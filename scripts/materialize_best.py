#!/usr/bin/env python
"""Materialize twp_*_v4_best from views into tables.

The views do argMax GROUP BY over ~10M rows on every query, which takes
minutes. Now that topup is complete across the roster, the dedup result is
stable and should be a table. Rebuild after any new ingest by re-running
this script.

    python scripts/materialize_best.py          # build both
    python scripts/materialize_best.py --check  # compare table vs view (slow)

The view DDL stays in views.py as documentation of the merge logic.
"""
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from malignment import ch

WORDS_DDL = """
CREATE TABLE IF NOT EXISTS {db}.twp_words_v4_best (
    model       String,
    prompt      String,
    word        String,
    p           Float64,
    n_paths     UInt32,
    merged      UInt8
) ENGINE = MergeTree
ORDER BY (model, prompt, word)
COMMENT 'Materialized from twp_words_v4. Raw frame only, topup merged via argMax(p, (topup, prompt_cache, mtime)). Rebuild with scripts/materialize_best.py after ingest.'
"""

WORDS_INSERT = """
INSERT INTO {db}.twp_words_v4_best
SELECT model, prompt, word,
       argMax(p,        (topup, prompt_cache, mtime)) AS p,
       argMax(n_paths,  (topup, prompt_cache, mtime)) AS n_paths,
       max(topup)                                     AS merged
FROM {db}.twp_words_v4
WHERE frame = ''
GROUP BY model, prompt, word
"""

CELLS_DDL = """
CREATE TABLE IF NOT EXISTS {db}.twp_cells_v4_best (
    model          String,
    prompt         String,
    total          Float64,
    tail           Float64,
    conservation   Float64,
    merged         UInt8
) ENGINE = MergeTree
ORDER BY (model, prompt)
COMMENT 'Materialized from twp_cells_v4. Raw frame only, topup merged via argMax(total, (topup, prompt_cache, mtime)). Rebuild with scripts/materialize_best.py after ingest.'
"""

CELLS_INSERT = """
INSERT INTO {db}.twp_cells_v4_best
SELECT model, prompt,
       argMax(total,        (topup, prompt_cache, mtime)) AS total,
       argMax(tail,         (topup, prompt_cache, mtime)) AS tail,
       argMax(conservation, (topup, prompt_cache, mtime)) AS conservation,
       max(topup)                                         AS merged
FROM {db}.twp_cells_v4
WHERE frame = ''
GROUP BY model, prompt
"""


def build(name, ddl, insert):
    print("  %s:" % name)
    t0 = time.time()
    ch.execute("DROP VIEW IF EXISTS {db}.%s" % name)
    ch.execute("DROP TABLE IF EXISTS {db}.%s" % name)
    ch.execute(ddl)
    ch.execute(insert)
    n = ch.scalar("SELECT count() FROM {db}.%s" % name)
    print("    %s rows in %.1fs" % (format(n, ","), time.time() - t0))
    return n


def check():
    """Rebuild the views temporarily and compare against tables."""
    from malignment import views
    print("\n  checking words...")
    ch.execute("DROP VIEW IF EXISTS {db}.twp_words_v4_best_check")
    ch.execute(views.VIEWS["twp_words_v4_best"].replace(
        "twp_words_v4_best", "twp_words_v4_best_check"))
    n_tbl = ch.scalar("SELECT count() FROM {db}.twp_words_v4_best")
    n_view = ch.scalar("SELECT count() FROM {db}.twp_words_v4_best_check")
    print("    table: %s  view: %s  match: %s" % (
        format(n_tbl, ","), format(n_view, ","), n_tbl == n_view))
    if n_tbl == n_view and n_tbl > 0:
        diff = ch.scalar("""
            SELECT count() FROM (
                SELECT model, prompt, word, p FROM {db}.twp_words_v4_best
                EXCEPT
                SELECT model, prompt, word, p FROM {db}.twp_words_v4_best_check
            )""")
        print("    differing rows: %s" % format(diff, ","))
    ch.execute("DROP VIEW IF EXISTS {db}.twp_words_v4_best_check")

    print("  checking cells...")
    ch.execute("DROP VIEW IF EXISTS {db}.twp_cells_v4_best_check")
    ch.execute(views.VIEWS["twp_cells_v4_best"].replace(
        "twp_cells_v4_best", "twp_cells_v4_best_check"))
    n_tbl = ch.scalar("SELECT count() FROM {db}.twp_cells_v4_best")
    n_view = ch.scalar("SELECT count() FROM {db}.twp_cells_v4_best_check")
    print("    table: %s  view: %s  match: %s" % (
        format(n_tbl, ","), format(n_view, ","), n_tbl == n_view))
    ch.execute("DROP VIEW IF EXISTS {db}.twp_cells_v4_best_check")


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true",
                    help="after building, compare table vs view (slow)")
    a = ap.parse_args()

    print("materializing twp_*_v4_best into tables...")
    build("twp_words_v4_best", WORDS_DDL, WORDS_INSERT)
    build("twp_cells_v4_best", CELLS_DDL, CELLS_INSERT)
    print("  done.")

    if a.check:
        check()

    return 0


if __name__ == "__main__":
    sys.exit(main())
