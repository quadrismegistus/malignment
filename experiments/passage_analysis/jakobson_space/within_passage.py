"""Inside one passage: do the surprising words sit in the sentences that move?

    python .../within_passage.py
    python .../within_passage.py --min-sents 6

The two axes are measured on the same passages but on different grains, so at
the passage level they can only be correlated. Joined onto the sentence row,
they can be asked a question no passage-level correlation can answer: **within a
single passage, is the sentence that steps furthest also the sentence carrying
deepseek's most unexpected words?**

## THE UNIT IS THE PASSAGE, AND THEN THE MODEL

One `r` per passage, over its own sentences. Then a median per model, then a
median of those. A passage contributes one number however many sentences it has,
and a model one number however many passages -- otherwise a 40-sentence passage
outvotes ten short ones and a model with more passages outvotes the arm.

## THE LENGTH CONFOUND IS MEASURED, NOT ASSUMED

`mean_bits` is a mean over `n_words`, and short sentences have noisier means AND
may take larger steps in bge space. That would manufacture a correlation with no
lexical content at all. So three numbers are reported per stratum, not one:

    r(mean_bits, step)      the claim
    r(n_words, step)        the confound, on its own
    partial r               the claim with n_words held out

If the raw and partial r differ materially, the raw one was measuring length.

## SENTENCE 0 HAS NO STEP AND IS EXCLUDED

It has no predecessor, so `step` is null there. Including it as zero would put a
floor point in every passage at the same place and bend every correlation the
same way.
"""

import argparse, collections, csv, math, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data"))
EXPLODED = os.path.join(DATA, "jakobson_space", "exploded")
QUAD = os.path.join(HERE, "results", "quadrants.csv")

CATS = ["base", "aligned", "API"]


def pearson(x, y):
    n = len(x)
    if n < 3:
        return None
    mx, my = sum(x) / n, sum(y) / n
    sx = math.sqrt(sum((v - mx) ** 2 for v in x))
    sy = math.sqrt(sum((v - my) ** 2 for v in y))
    if sx == 0 or sy == 0:
        return None
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy)


def partial(x, y, z):
    """r(x,y) with z held out. None if any component is undefined."""
    rxy, rxz, ryz = pearson(x, y), pearson(x, z), pearson(y, z)
    if None in (rxy, rxz, ryz):
        return None
    d = math.sqrt((1 - rxz ** 2) * (1 - ryz ** 2))
    return None if d == 0 else (rxy - rxz * ryz) / d


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-sents", type=int, default=5,
                    help="a within-passage r needs enough sentences to mean anything")
    a = ap.parse_args(argv)
    import pyarrow.parquet as pq

    csv.field_size_limit(10 ** 7)
    meta = {r["id"]: r for r in csv.DictReader(open(QUAD, newline=""))}
    t = pq.read_table(os.path.join(EXPLODED, "sentences.parquet"))
    d = {c: t.column(c).to_pylist() for c in t.column_names}
    by = collections.defaultdict(list)
    for i, pid in enumerate(d["id"]):
        if d["step"][i] is None or d["mean_bits"][i] is None:
            continue
        by[pid].append((d["mean_bits"][i], d["step"][i], float(d["n_words"][i]),
                        d["is_furthest"][i], d["dist_from_first"][i]))

    #: per passage: the three correlations, and whether the furthest sentence is
    #: above this passage's own median sentence bits (a sign test needs no
    #: distributional assumption and no length control).
    rows = []
    for pid, v in by.items():
        if len(v) < a.min_sents:
            continue
        m = meta.get(pid)
        if not m:
            continue
        b = [x[0] for x in v]; s = [x[1] for x in v]; n = [x[2] for x in v]
        r1, r2, rp = pearson(b, s), pearson(n, s), partial(b, s, n)
        if r1 is None:
            continue
        med = statistics.median(b)
        far = [x[0] for x in v if x[3]]
        rows.append(dict(id=pid, cat=m["category"], model=m["model"] or m["category"],
                         quad=m["quadrant"], r=r1, rn=r2, rp=rp,
                         far_hi=(far[0] > med) if far else None))

    def block(title, groups):
        print("\n%s" % title)
        print("%-26s %7s %8s %8s %8s %9s %7s"
              % ("", "n", "r(bits,", "r(words,", "partial", "furthest", "unit"))
        print("%-26s %7s %8s %8s %8s %9s %7s"
              % ("", "", "step)", "step)", "r", "hi-bits", ""))
        for label, sub, unit in groups:
            if not sub:
                continue
            if unit == "models":
                per = collections.defaultdict(list)
                for x in sub:
                    per[x["model"]].append(x)
                vals = [(statistics.median(y["r"] for y in v),
                         statistics.median(y["rn"] for y in v),
                         statistics.median(y["rp"] for y in v if y["rp"] is not None)
                         if any(y["rp"] is not None for y in v) else 0.0,
                         sum(1 for y in v if y["far_hi"] is True)
                         / max(sum(1 for y in v if y["far_hi"] is not None), 1))
                        for v in per.values() if len(v) >= 3]
                if not vals:
                    continue
                n = len(vals)
                r1 = statistics.median(x[0] for x in vals)
                r2 = statistics.median(x[1] for x in vals)
                rp = statistics.median(x[2] for x in vals)
                fh = statistics.median(x[3] for x in vals)
            else:
                n = len(sub)
                r1 = statistics.median(x["r"] for x in sub)
                r2 = statistics.median(x["rn"] for x in sub)
                pv = [x["rp"] for x in sub if x["rp"] is not None]
                rp = statistics.median(pv) if pv else float("nan")
                #: `far_hi is None` means the furthest sentence had no scored
                #: words, which is not evidence either way -- excluded from the
                #: denominator rather than counted as a failure.
                dn = sum(1 for x in sub if x["far_hi"] is not None)
                fh = sum(1 for x in sub if x["far_hi"] is True) / max(dn, 1)
            print("%-26s %7d %+8.3f %+8.3f %+8.3f %8.0f%% %7s"
                  % (label, n, r1, r2, rp, 100 * fh, unit))

    print("passages with >= %d usable sentences: %d of %d"
          % (a.min_sents, len(rows), len(by)))
    block("BY CATEGORY   (the unit is the model where there is a population of them)",
          [(c, [x for x in rows if x["cat"] == c], "models" if c != "API" else "models")
           for c in CATS]
          + [(c, [x for x in rows if x["cat"] == c], "passages")
             for c in sorted({x["cat"] for x in rows} - set(CATS))])
    block("BY QUADRANT   (pooled over passages: a quadrant is not a population "
          "of models)",
          [(q, [x for x in rows if x["quad"] == q], "passages")
           for q in ("(+surp +drift)", "(+surp -drift)",
                     "(-surp +drift)", "(-surp -drift)")])
    #: SAY WHAT A NULL WOULD LOOK LIKE. `furthest hi-bits` is a proportion whose
    #: chance value is 50%, and a column with no stated null is a column whose
    #: top row looks meaningful whatever it says.
    print("\n`furthest hi-bits` = the sentence furthest from the opening also "
          "sits above\nthat passage's median sentence bits. Chance is 50%.")


if __name__ == "__main__":
    main()
