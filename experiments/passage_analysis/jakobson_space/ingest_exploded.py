"""Load the passage, word and sentence grains into ClickHouse.

    python .../ingest_exploded.py --dry-run     # counts and DDL, writes nothing
    python .../ingest_exploded.py

Three tables in the `malignment` database, one per grain:

    passage_axes        14,414   one row per passage: both axes, both z-scores,
                                 the quadrant, and the text
    passage_words      ~2.9M     one row per word, with its deepseek surprisal
    passage_sentences   ~216k    one row per sentence, with its drift step

## THE DATABASE IS `malignment`, AND THAT IS THE POINT OF NAMING IT

RH's other project has live tables in this ClickHouse. They are in `abstraction`,
`lltk` and `llmtasks`; `malignment` is ours and already holds `twp_words` at 94M
rows, against which 2.9M is small. Every statement here is qualified with `{db}`
so it cannot land anywhere else, and the only DDL is CREATE and (with --replace)
DROP of the three names above.

## THE PASSAGE KEYS ARE DENORMALISED ONTO EVERY WORD AND SENTENCE

`category`, `model` and `quadrant` are copied onto all 2.9M word rows. That is
redundant and deliberate: the use for this table is colouring a plot by arm or by
quadrant, and a reader who has to remember to join 2.9M rows back to 14k to get
`category` will eventually forget, or will join on the wrong key, and the result
of a wrong join here is a plot that looks right. One table, one query, no join.

## WHAT IS NOT COPIED DOWN

`passage_sentences.mean_bits` is the ONE exception and is not a copy: it is the
word grain aggregated to the sentence it falls in, computed once in `explode.py`
so that "do the surprising words sit in the sentences that move?" is a single
query. `n_words` travels with it, because a mean whose population is not stated
invites being averaged again over the wrong denominator.

`surprisal` and `drift` stay on `passage_axes` only. They are aggregates OF the
word and sentence rows, and a passage-level mean sitting on every word row is an
invitation to average it again over a different denominator -- the count that
looks like a rate. `passage_sentences.reproduces` is the check that the two
grains agree; it is carried because it is a property of the decomposition, not a
copy of the value.
"""

import argparse, collections, csv, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data"))
EXPLODED = os.path.join(DATA, "jakobson_space", "exploded")
QUAD = os.path.join(HERE, "results", "quadrants.csv")
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))

DB = "malignment"
BATCH = 200_000

DDL = {
    "passage_axes": """
CREATE TABLE IF NOT EXISTS %(db)s.passage_axes (
  id String, human_or_ai LowCardinality(String), category LowCardinality(String),
  model LowCardinality(String), prompt String, text String, text_sha String,
  surprisal Float64, drift Float64, drift_residual Float64,
  z_surprisal Float64, z_drift Float64, z_drift_residual Float64,
  quadrant LowCardinality(String), quadrant_raw LowCardinality(String)
) ENGINE = MergeTree ORDER BY (category, model, id)""",
    "passage_words": """
CREATE TABLE IF NOT EXISTS %(db)s.passage_words (
  id String, word_index UInt32, word String, bits Float32, partial UInt8,
  category LowCardinality(String), model LowCardinality(String),
  quadrant LowCardinality(String)
) ENGINE = MergeTree ORDER BY (category, id, word_index)""",
    "passage_sentences": """
CREATE TABLE IF NOT EXISTS %(db)s.passage_sentences (
  id String, sent_index UInt32, sentence String,
  step Nullable(Float64), dist_from_first Float64,
  is_furthest UInt8, reproduces UInt8,
  mean_bits Nullable(Float64), n_words UInt32,
  category LowCardinality(String), model LowCardinality(String),
  quadrant LowCardinality(String)
) ENGINE = MergeTree ORDER BY (category, id, sent_index)""",
}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--replace", action="store_true",
                    help="DROP the three tables first. Only these three names.")
    ap.add_argument("--exploded", default=EXPLODED)
    a = ap.parse_args(argv)
    import pyarrow.parquet as pq
    from malignment import ch

    csv.field_size_limit(10 ** 7)
    #: the passage grain first -- it supplies the keys the other two carry.
    #: `newline=""` -- see explode.py; without it two passages lose their \r.
    passages = list(csv.DictReader(open(QUAD, newline="")))
    key = {r["id"]: (r["category"], r["model"], r["quadrant"]) for r in passages}
    FL = ("surprisal drift drift_residual z_surprisal z_drift "
          "z_drift_residual").split()
    prows = [{**{k: r[k] for k in ("id", "human_or_ai", "category", "model",
                                   "prompt", "text", "text_sha", "quadrant",
                                   "quadrant_raw")},
              **{k: float(r[k]) for k in FL}} for r in passages]

    def parquet_rows(name, cast):
        fp = os.path.join(a.exploded, name)
        if not os.path.exists(fp):
            raise SystemExit("missing %s -- run explode.py first" % fp)
        t = pq.read_table(fp)
        d = {c: t.column(c).to_pylist() for c in t.column_names}
        n, lost = t.num_rows, 0
        for i in range(n):
            r = {c: d[c][i] for c in d}
            k = key.get(r["id"])
            if not k:
                #: a grain row whose passage is absent would be uncolourable and
                #: would silently widen every denominator. Counted, not carried.
                lost += 1
                continue
            r["category"], r["model"], r["quadrant"] = k
            yield cast(r)
        if lost:
            print("  %s: %d rows had no passage row and were NOT loaded"
                  % (name, lost))

    def w(r):
        r["partial"] = int(bool(r["partial"])); return r

    def s(r):
        r["is_furthest"] = int(bool(r["is_furthest"]))
        r["reproduces"] = int(bool(r["reproduces"])); return r

    jobs = [("passage_axes", prows),
            ("passage_words", parquet_rows("words.parquet", w)),
            ("passage_sentences", parquet_rows("sentences.parquet", s))]

    if a.dry_run:
        print("DRY RUN -- nothing written. Target database: %s\n" % DB)
        for name, rows in jobs:
            rows = list(rows)
            print("%-20s %9d rows" % (name, len(rows)))
            if rows:
                print("   sample keys: %s" % ", ".join(sorted(rows[0])[:6]))
        print("\nDDL that would run:")
        for name in DDL:
            print(DDL[name] % {"db": DB})
        return

    for name, rows in jobs:
        if a.replace:
            ch.execute("DROP TABLE IF EXISTS %s.%s" % (DB, name))
        ch.execute(DDL[name] % {"db": DB})
        before = ch.scalar("SELECT count() FROM %s.%s" % (DB, name), 0)
        n, buf = 0, []
        for r in rows:
            buf.append(r)
            if len(buf) >= BATCH:
                n += ch.insert("%s.%s" % (DB, name), buf); buf = []
                print("  %s: %d ..." % (name, n), flush=True)
        if buf:
            n += ch.insert("%s.%s" % (DB, name), buf)
        after = ch.scalar("SELECT count() FROM %s.%s" % (DB, name), 0)
        #: the accounting identity, stated. An insert that reports a count is
        #: not evidence the rows landed; the table's own count is.
        print("%-20s sent %8d | table %8d -> %8d | delta %8d%s"
              % (name, n, before, after, after - before,
                 "" if after - before == n else "   <-- DELTA != SENT"))


if __name__ == "__main__":
    main()
