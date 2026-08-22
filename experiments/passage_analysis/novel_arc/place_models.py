"""Place model passages on the historical abstraction axis.

    python .../place_models.py

Scores the `jakobson_space` quadrant corpus -- base, aligned, API and the six
human anchor corpora, 14,414 passages with text -- on the SAME instruments the
chadwyck series uses, so the two tables share an axis and can be read together.

## WHY THIS CORPUS AND NOT THE LARGER ONE

`gen_sequences` has 490,882 free passages over 94 models, but no human anchor
and no API arm. `quadrants.csv` carries all four populations in one file
WITH the passage text: 2,195 base, 2,736 aligned, 6,508 API, 2,975 human across
six reference corpora. Placement needs the human end of the scale more than it
needs model count, because the question is where model prose sits relative to
prose people actually wrote.

## DIRECTION IS NOT POSITION

The chadwyck series establishes that alignment moves prose along the axis whose
rise constitutes the novel's emergence. That is a claim about DIRECTION. Whether
aligned output SITS anywhere near eighteenth-century fiction is a different
question, and the base model's starting point is set by a training corpus that
is overwhelmingly post-1800 -- so a large move in the C18 direction can still
land nowhere near the C18, and a small one can already be past it.

Sign, again: RH's scale is HIGH = CONCRETE, so **more abstract is more
negative**.
"""

import argparse, collections, csv, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
#: RESULTS GO TO $MALIGNMENT_DATA, NOT THE REPO. The chadwyck table is 128 MB
#: and chicago is ~760 MB; `results/` here is untracked but was not ignored, so
#: a single careless `git add` on the folder would have swept them in.
DATA = os.path.join(os.environ.get("MALIGNMENT_DATA",
                                   os.path.expanduser("~/malignment-data")),
                    "novel_arc")
sys.path.insert(0, HERE)
JAK = "/Users/rj416/github/malignment/experiments/passage_analysis/jakobson_space"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=os.path.join(JAK, "results", "quadrants.csv"))
    ap.add_argument("--out", default=os.path.join(DATA,
                                                  "model_placement.parquet"))
    ap.add_argument("--limit", type=int)
    a = ap.parse_args(argv)
    import pyarrow as pa, pyarrow.parquet as pq
    from measure_lltk import Scorer

    csv.field_size_limit(10 ** 7)
    S = Scorer()
    rows = []
    for i, r in enumerate(csv.DictReader(open(a.src, newline=""))):
        if a.limit and i >= a.limit:
            break
        txt = r.get("text") or ""
        if len(txt.split()) < 40:
            continue
        v = S.score(txt)
        if not v:
            continue
        v.update(id=r["id"], category=r["category"], model=r.get("model") or "",
                 human_or_ai=r["human_or_ai"])
        rows.append(v)
        if len(rows) % 2000 == 0:
            print("  %d scored" % len(rows), flush=True)
    keys = sorted({k for r in rows for k in r})
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    pq.write_table(pa.table({k: [r.get(k) for r in rows] for k in keys}),
                   a.out, compression="zstd")
    c = collections.Counter(r["category"] for r in rows)
    print("-> %s  (%s passages)" % (a.out, "{:,}".format(len(rows))))
    for k, n in c.most_common():
        print("   %-22s %6d" % (k, n))


if __name__ == "__main__":
    main()
