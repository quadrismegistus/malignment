"""twp jsonl on disk -> ClickHouse. The rule is the stamp, not a list.

    python -m malignment.ingest --scan            what would be ingested
    python -m malignment.ingest --create          make the database and tables
    python -m malignment.ingest --run [--limit N] ingest

## WHAT IS INCLUDABLE, AND WHY IT IS NOT A HAND-MAINTAINED LIST

RH, 2026-08-15: *"why don't we declare any twp file with explicit rule version 3
as includable in sources. Take union of most recent data for a cell."*

    INCLUDE   a record carrying rule_version == 3, `rows`, and `residual`
    EXCLUDE   anything else -- including rule_version NULL (see below)
    EXCLUDE   paths marked QUARANTINE / RETIRED- / _SUPERSEDED

**The old repo declared sources in a hand-written registry, and the registry went
stale in the direction that hides work.** Measured 2026-08-15: 32 entries
declared, 51 directories on disk carrying real twp. `twp_grid_v3` (95 models) and
`f11_twp_bf` (41) had never been listed -- not retired, not refused, simply
absent, which is the state that registry existed to prevent. A list an operator
maintains diverges the first time two operators remember differently; a stamp
the producer wrote cannot.

So inclusion is DERIVED from the payload. A new fleet directory is includable the
moment it lands, without anyone remembering to add it.

## rule_version NULL IS NOT INGESTED, AND IT COSTS SOMETHING KNOWN

`data/twp_cloud` (103 files) predates the rule stamp. It is also the SOLE source
of **104 catalogue prompts that exist nowhere else** -- roughly 9,900 cells --
including whole markedness families:

    'He held her underwater until she stopped'   249 models in the old store
    'He held her underwater until she started'     0 models, 95 in twp_cloud

**So the marked/unmarked contrast cannot presently be computed at all**, and the
missing arm has been on disk since 30 July. Ingesting it anyway would make the
pair computable as a CROSS-RULE comparison -- one arm stamped 3, one arm
unstamped -- which is the shape that voided a registration on 2026-08-15: two
checkpoints carrying identical stamps and incompatible normalisations, found
only because a pre-registration put a reference `n` beside its result.

RH: *"not sure I trust the ruleVersionNone data."* Agreed, and the cost is
recorded here rather than discovered later: **the fix is to re-measure those 104
prompts under rule 3**, ~9,900 cells and one small fleet job, not to widen the
gate. A gap you can name and price is better than a corpus you cannot trust.

## UNION, NOT PRECEDENCE -- MEASURED, NOT ASSUMED

The directories are COMPLEMENTARY, not redundant. For `Olmo-3-1025-7B`: nine
files, union 4,531 prompts, **intersection 0**. Each fleet extended coverage
rather than repeating it, so "most recent wins" has almost nothing to decide.

Where a genuine (model, prompt) collision does occur, the newest file wins and
the collision is COUNTED, so we learn whether the rule ever fires instead of
trusting that it does the right thing.

**THE GRAIN IS THE CELL, NOT THE WORD.** A twp cell is one prefix-tree walk whose
rows plus residual sum to 1. Resolving word-by-word across two runs would build a
distribution no forward pass produced and the residual would stop reconciling.
One file supplies a cell entirely, or not at all.

## THE GATE IS THE PAYLOAD'S OWN ARITHMETIC

Every record carries `conservation`. A cell that does not conserve is REFUSED and
counted by class -- never dropped silently. Ported from the old `twp_ingest`,
whose docstring is right: *"it validates before it writes, which is the whole
point of a separate step."*
"""
import argparse
import glob
import json
import os
import sys
from collections import defaultdict

from . import ch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#: The corpus lives in the archive repo; this reads it in place and copies
#: nothing. 22 GB of jsonl, 1,896 files.
CORPUS = os.environ.get("MALIGNMENT_CORPUS",
                        "/Users/rj416/github/malign-logits/data")
RULE_VERSION = 3
TOL = 1e-4          #: conservation is exact to ~4e-7 in practice; 1e-4 is loose
#: A path component that disqualifies a directory however good its records are.
#: These are markers the producers already wrote; this honours them rather than
#: re-deciding. `_SUPERSEDED_shard_names/` and four QUARANTINE dirs exist today.
BAD_PATH = ("QUARANTINE", "RETIRED-", "_SUPERSEDED")

DDL = ["""
CREATE TABLE IF NOT EXISTS {db}.twp_words (
    model String, prompt String, word String,
    t1 UInt32, p Float32,
    source LowCardinality(String), mtime DateTime
) ENGINE = ReplacingMergeTree(mtime) ORDER BY (model, prompt, word)
""", """
CREATE TABLE IF NOT EXISTS {db}.twp_cells (
    model String, prompt String,
    n_words UInt32, conservation Float64,
    tail Float32, drop Float32, open Float32, mojibake Float32, total Float32,
    theta Float32, rule_version UInt16, dict_sha LowCardinality(String),
    revision LowCardinality(String), bos_policy LowCardinality(String),
    device LowCardinality(String), compute_dtype LowCardinality(String),
    torch_version LowCardinality(String), transformers_version LowCardinality(String),
    source LowCardinality(String), mtime DateTime
) ENGINE = ReplacingMergeTree(mtime) ORDER BY (model, prompt)
"""]


def scan():
    """Every includable file, with its source label and mtime.

    The label is the directory relative to the corpus root. **It is part of the
    data's identity** -- it lands in the `source` column, so renaming a directory
    re-partitions the store.
    """
    out = []
    for p in sorted(glob.glob(os.path.join(CORPUS, "**", "*.jsonl"), recursive=True)):
        rel = os.path.relpath(p, CORPUS)
        if any(b in rel for b in BAD_PATH):
            continue
        try:
            with open(p, encoding="utf-8") as fh:
                first = fh.readline()
            if not first:
                continue
            r = json.loads(first)
        except Exception:
            continue
        if r.get("rule_version") != RULE_VERSION:
            continue
        if "rows" not in r or "residual" not in r:
            continue
        out.append({"path": p, "source": os.path.dirname(rel) or ".",
                    "mtime": os.path.getmtime(p)})
    return out


def _cells(path):
    """(model, prompt) -> record, last write winning WITHIN a file.

    A shard re-run after a kill re-emits prompts; the old ingester dedups the
    same way and counts it rather than hiding it.
    """
    seen, dups = {}, 0
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            try:
                d = json.loads(line)
            except Exception:
                continue
            k = (d.get("model"), d.get("prompt"))
            if k[0] is None or k[1] is None:
                continue
            if k in seen:
                dups += 1
            seen[k] = d
    return seen, dups


def plan(files):
    """(model, prompt) -> the winning file. Newest mtime wins; collisions counted.

    Returns (winner, stats). A collision is two DIFFERENT files offering the same
    cell -- the thing precedence exists for, and measured at ~0 because the
    fleets ran complementary prompt sets.
    """
    winner, collide = {}, 0
    for f in sorted(files, key=lambda x: x["mtime"]):
        seen, _ = _cells(f["path"])
        for k in seen:
            if k in winner:
                collide += 1
            winner[k] = f          # later mtime overwrites
    return winner, {"collisions": collide}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scan", action="store_true")
    ap.add_argument("--create", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()

    files = scan()
    by_src = defaultdict(int)
    for f in files:
        by_src[f["source"]] += 1
    print("  corpus: %s" % CORPUS)
    print("  includable (rule_version == %d): %d files across %d directories\n"
          % (RULE_VERSION, len(files), len(by_src)))
    for s, n in sorted(by_src.items(), key=lambda x: -x[1])[:14]:
        print("     %-46s %4d" % (s[:46], n))
    if a.scan:
        return 0

    if a.create:
        for d in DDL:
            ch.execute(d)
        print("\n  created %s.twp_words, %s.twp_cells" % (ch.DB, ch.DB))
    if not a.run:
        return 0

    if a.limit:
        files = files[:a.limit]
    words, cells = [], []
    rej = defaultdict(int)
    n_dup = 0
    win, stats = plan(files)
    print("\n  planned %s cells | collisions needing precedence: %s"
          % (format(len(win), ","), format(stats["collisions"], ",")))
    for f in files:
        seen, dups = _cells(f["path"])
        n_dup += dups
        import datetime
        mt = datetime.datetime.fromtimestamp(f["mtime"]).strftime("%Y-%m-%d %H:%M:%S")
        for k, d in seen.items():
            if win.get(k) is not f:
                rej["superseded_by_newer"] += 1
                continue
            rows = d.get("rows") or []
            res = d.get("residual") or {}
            cons = d.get("conservation")
            #: THE PAYLOAD'S OWN ARITHMETIC IS THE GATE. Refused, not dropped.
            if cons is None or abs(cons - 1.0) > TOL:
                rej["conservation"] += 1
                continue
            m, pr = k
            for w in rows:
                words.append({"model": m, "prompt": pr, "word": w["word"],
                              "t1": int(w.get("t1") or 0), "p": float(w["p"]),
                              "source": f["source"], "mtime": mt})
            cells.append({"model": m, "prompt": pr, "n_words": len(rows),
                          "conservation": float(cons),
                          "tail": float(res.get("tail") or 0),
                          "drop": float(res.get("drop") or 0),
                          "open": float(res.get("open") or 0),
                          "mojibake": float(res.get("mojibake") or 0),
                          "total": float(res.get("total") or 0),
                          "theta": float(d.get("theta") or 0),
                          "rule_version": int(d.get("rule_version") or 0),
                          "dict_sha": d.get("dict_sha") or "",
                          "revision": d.get("revision") or "",
                          "bos_policy": d.get("bos_policy") or "",
                          "device": d.get("device") or "",
                          "compute_dtype": d.get("compute_dtype") or "",
                          "torch_version": d.get("torch_version") or "",
                          "transformers_version": d.get("transformers_version") or "",
                          "source": f["source"], "mtime": mt})
        if len(words) > 400_000:
            ch.insert("twp_words", words); words = []
            ch.insert("twp_cells", cells); cells = []
            print("     ... %s cells written" % format(
                ch.scalar("SELECT count() FROM {db}.twp_cells"), ","))
    if words:
        ch.insert("twp_words", words)
    if cells:
        ch.insert("twp_cells", cells)
    print("\n  duplicates WITHIN files (last write won): %s" % format(n_dup, ","))
    print("  refused / skipped, by class:")
    for k, v in sorted(rej.items(), key=lambda x: -x[1]):
        print("     %-24s %s" % (k, format(v, ",")))
    print("\n  %s.twp_cells: %s | twp_words: %s"
          % (ch.DB, format(ch.scalar("SELECT count() FROM {db}.twp_cells"), ","),
             format(ch.scalar("SELECT count() FROM {db}.twp_words"), ",")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
