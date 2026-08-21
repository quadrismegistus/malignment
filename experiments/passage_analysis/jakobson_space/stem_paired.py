"""Category contrasts PAIRED BY STEM: API vs aligned vs base on 97 shared stems.

    python .../stem_paired.py
    python .../stem_paired.py --min-per-cell 5

## WHY THE STEM AND NOT THE LINEAGE

`arm_paired.py` pairs an aligned checkpoint with its own base, which is the right
unit for an ARM claim and is unavailable for the API models -- they ship no base,
which is the same structural fact that keeps them out of the `arm` column.

What they DO share with the open models is the prompt. 97 of the ~100 narrative
stems carry passages from all three categories, so the scene is held constant and
only the generator varies. That is a real paired design for a question the
lineage design cannot ask: **given this scene, does a commodity endpoint write it
differently from an open aligned checkpoint?**

## THIS IS A DIFFERENT UNIT AND THEREFORE A DIFFERENT CLAIM

Within a stem, a category's value is the median over ALL its models' passages, so
models are pooled inside the cell. That is fine for "does category A differ from
category B on this scene" and WRONG for "does alignment move a model" -- the
second needs the lineage, and `arm_paired.py` is where it lives. The
aligned-vs-base row is printed here for comparability with the other two and is
NOT the arm result; where the two designs disagree, the lineage one governs.

Eleven commodity endpoints from three vendors are still not a sample of anything.
A significant API row says these eleven differ from the open aligned checkpoints
on these stems; it does not generalise to "API models".

## THE TEST

Sign test on the 97 per-stem differences, median beside it, means printed and
never quoted. Exact two-sided binomial. A stem needs `--min-per-cell` passages in
BOTH categories of a contrast or it is dropped from that contrast only -- so the
three contrasts can have different n, and each prints its own.
"""

import argparse, collections, csv, math, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "results", "quadrants.csv")
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))

QS = ["(+surp +drift)", "(+surp -drift)", "(-surp +drift)", "(-surp -drift)"]
NAME = {"(-surp +drift)": "metonymic", "(+surp -drift)": "metaphoric",
        "(+surp +drift)": "breakdown", "(-surp -drift)": "unmarked"}
CONTRASTS = [("API", "aligned"), ("API", "base"), ("aligned", "base")]


def sign_test(diffs):
    v = [d for d in diffs if d != 0]
    n, up = len(v), sum(1 for d in v if d > 0)
    if not n:
        return 0, 0, 0, float("nan"), float("nan")
    k = max(up, n - up)
    p = min(1.0, 2 * sum(math.comb(n, i) for i in range(k, n + 1)) / 2 ** n)
    return n, up, n - up, statistics.median(v), p


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=SRC)
    ap.add_argument("--min-per-cell", type=int, default=3)
    a = ap.parse_args(argv)

    csv.field_size_limit(10 ** 7)
    cell = collections.defaultdict(list)
    for r in csv.DictReader(open(a.src, newline="")):
        if r["category"] in ("base", "aligned", "API") and r["prompt"]:
            cell[(r["prompt"], r["category"])].append(r)

    def val(rows, what):
        if what == "surprisal":
            return statistics.median(float(x["surprisal"]) for x in rows)
        if what == "drift":
            return statistics.median(float(x["drift"]) for x in rows)
        c = collections.Counter(x["quadrant"] for x in rows)
        return c[what] / len(rows)

    stems = sorted({p for p, _ in cell})
    print("stems seen: %d" % len(stems))
    for A, B in CONTRASTS:
        ok = [s for s in stems
              if len(cell.get((s, A), [])) >= a.min_per_cell
              and len(cell.get((s, B), [])) >= a.min_per_cell]
        print("\n%s - %s   paired over %d stems (>= %d passages in both)"
              % (A, B, len(ok), a.min_per_cell))
        if not ok:
            continue
        print("  %-28s %10s %5s %5s %12s" % ("", "median", "up", "dn", "p"))
        for lab, what in ([("surprisal (bits/token)", "surprisal"),
                           ("drift (mean_drift)", "drift")]
                          + [("%s  %s" % (q, NAME[q]), q) for q in QS]):
            d = [val(cell[(s, A)], what) - val(cell[(s, B)], what) for s in ok]
            n, up, dn, med, p = sign_test(d)
            print("  %-28s %+10.4f %5d %5d %12.3g" % (lab, med, up, dn, p))
    #: the unit, on the way out, because a p-value over 97 stems reads as a
    #: p-value over 97 independent things and the models inside are pooled.
    print("\nn is STEMS, not models or passages. Within a stem each category is the")
    print("median over all its models' passages, so models are POOLED inside the")
    print("cell -- see the docstring for what that does and does not license.")


if __name__ == "__main__":
    main()
