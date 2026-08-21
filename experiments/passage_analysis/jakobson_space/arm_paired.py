"""The base->aligned contrast, PAIRED WITHIN LINEAGE, on both axes and the quadrants.

    python .../arm_paired.py
    python .../arm_paired.py --min-passages 20
    python .../arm_paired.py --human        # and the toward/away test per corpus

Everything else in this folder reports the quadrant plane DESCRIPTIVELY: shares,
enrichments, medians of per-model medians. None of it is a test, and a table of
percentages cannot say whether alignment MOVES a lineage -- only that the two
populations differ, which they would also do if the arms held different models.

This pairs each aligned checkpoint with its own base and tests the difference.

## WHY THE PAIR AND NOT THE ARM

`base` and `aligned` are not two samples from one population. Every aligned model
has a specific base it was trained from, they share a pretraining corpus and a
tokenizer, and the between-lineage variance is far larger than the arm effect --
`../../..`'s F31 puts family at 97.8% of variance. Comparing arm medians throws
that pairing away and tests against the wrong noise.

The unit is the LINEAGE, not the checkpoint: where a lineage ships several
aligned children of one base they are averaged into one difference first, so a
family with four instruct variants does not get four votes.

## THE TEST IS A SIGN TEST AND THAT IS DELIBERATE

Sign test on the per-lineage differences, plus the median difference. No
normality assumption, no variance estimate from n=25, and it is what the M06
passage-corpus run used (38 pairs) -- so the two are directly comparable rather
than merely both significant. Means are printed beside the medians and are never
the quoted statistic.

## THE DENOMINATOR IS 22 LINEAGES OF 59, AND THAT IS A COVERAGE LIMIT

`quadrants.csv` holds 54 models; the roster has 59 lineages. 29 lineages have at
least one arm present and **22 have BOTH** at 10+ passages, which is what a
paired test can use. The loss is not a filter applied here -- it is which models
reached the narrative pool upstream -- but it is the population every p-value
below is about, and a reader should not infer the roster.

## THE HUMAN TEST IS PER CORPUS, NOT AGAINST "HUMAN"

`--human` asks whether alignment moves a lineage TOWARD or AWAY from human
writing, lineage-paired: euclidean distance on the (z_surprisal, z_drift) plane
from each arm's median to a corpus median, differenced aligned-minus-base, sign
test over the same lineages.

**It is run against each of the six corpora separately and never against their
centroid.** The corpora occupy opposite corners of this plane -- literary
criticism is 66.7% `(+surp +drift)` and waking narrative 61.2% `(-surp -drift)`
-- so their pooled centroid sits in the middle of a region none of them occupies,
and "distance from human" computed against it would be a distance from nowhere.
Six answers is the honest shape of the question, and they are not expected to
agree in sign.

## WHAT IS TESTED

    surprisal      median bits/token, per model, aligned - base
    drift          median mean_drift, per model, aligned - base
    quadrant share for each of the four cells, aligned share - base share

The quadrant shares are the four M06 predictions: their Q1 metonymic is our
`(-surp +drift)` and their Q3 metaphoric is our `(+surp -drift)`. Their run found
Q1 up, Q2 down, Q3 down, Q4 up on 38 pairs under two embedders. **Those
directions were declared before their data and are therefore predictions for
this corpus**, which is a different corpus, a different rung and a different
reference model -- so agreement extends them and disagreement localises them.
"""

import argparse, collections, csv, math, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "results", "quadrants.csv")
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))

QS = ["(+surp +drift)", "(+surp -drift)", "(-surp +drift)", "(-surp -drift)"]
#: M06's names for the same cells, and the direction its plan declared for the
#: aligned-minus-base difference BEFORE its run.
M06 = {"(-surp +drift)": ("Q1 metonymic", "+"), "(+surp +drift)": ("Q2 breakdown", "-"),
       "(+surp -drift)": ("Q3 metaphoric", "-"), "(-surp -drift)": ("Q4 unmarked", "+")}


def sign_test(diffs):
    """-> (n, up, dn, median, mean, p). Ties are dropped and counted by the caller."""
    v = [d for d in diffs if d != 0]
    n, up = len(v), sum(1 for d in v if d > 0)
    if not n:
        return 0, 0, 0, float("nan"), float("nan"), float("nan")
    k = max(up, n - up)
    #: two-sided exact binomial against 0.5
    p = min(1.0, 2 * sum(math.comb(n, i) for i in range(k, n + 1)) / 2 ** n)
    return n, up, n - up, statistics.median(v), statistics.mean(v), p


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=SRC)
    ap.add_argument("--min-passages", type=int, default=10,
                    help="a model median needs enough passages to be one")
    ap.add_argument("--human", action="store_true",
                    help="also run the toward/away test against each corpus")
    a = ap.parse_args(argv)
    from malignment import roster

    csv.field_size_limit(10 ** 7)
    per = collections.defaultdict(list)
    corp = collections.defaultdict(list)
    for r in csv.DictReader(open(a.src, newline="")):
        if r["category"] in ("base", "aligned"):
            per[r["model"]].append(r)
        elif r["human_or_ai"] == "human":
            corp[r["category"]].append(r)

    def zmed(rows):
        """(median z_surprisal, median z_drift) -- the plane the quadrants cut."""
        return (statistics.median(float(x["z_surprisal"]) for x in rows),
                statistics.median(float(x["z_drift"]) for x in rows))

    def stats_for(m):
        v = per[m]
        s = statistics.median(float(x["surprisal"]) for x in v)
        d = statistics.median(float(x["drift"]) for x in v)
        c = collections.Counter(x["quadrant"] for x in v)
        return s, d, {q: c[q] / len(v) for q in QS}, len(v)

    #: lineage -> [base, children...]. A lineage contributes ONE difference
    #: however many aligned children it ships.
    lin = roster.lineages()
    rows, skipped = [], collections.Counter()
    for base, members in sorted(lin.items()):
        kids = [m for m in members if m != base and m in per
                and len(per[m]) >= a.min_passages]
        if base not in per or len(per[base]) < a.min_passages:
            skipped["base absent or under %d passages" % a.min_passages] += 1
            continue
        if not kids:
            skipped["no aligned child with >= %d passages" % a.min_passages] += 1
            continue
        bs, bd, bq, bn = stats_for(base)
        ks = [stats_for(k) for k in kids]
        bz = zmed(per[base])
        kz = [zmed(per[k]) for k in kids]
        rows.append(dict(
            base=base, n_kids=len(kids), n_base=bn, base_z=bz, kid_z=kz,
            d_surp=statistics.mean(x[0] for x in ks) - bs,
            d_drift=statistics.mean(x[1] for x in ks) - bd,
            d_quad={q: statistics.mean(x[2][q] for x in ks) - bq[q] for q in QS}))

    print("lineages tested: %d  (%d aligned children in total)"
          % (len(rows), sum(r["n_kids"] for r in rows)))
    for k, v in sorted(skipped.items()):
        print("  skipped %-46s %d" % (k, v))
    if not rows:
        return

    print("\nALIGNED - BASE, paired within lineage, sign test on %d lineages\n" % len(rows))
    print("%-30s %9s %9s %5s %5s %11s"
          % ("", "median", "mean", "up", "dn", "p"))
    for lab, key in (("surprisal (bits/token)", "d_surp"), ("drift (mean_drift)", "d_drift")):
        n, up, dn, med, mean, p = sign_test([r[key] for r in rows])
        print("%-30s %+9.4f %+9.4f %5d %5d %11.3g" % (lab, med, mean, up, dn, p))

    print("\nQUADRANT SHARE, aligned - base                    M06 predicted")
    print("%-30s %9s %5s %5s %11s   %-14s %s"
          % ("", "median", "up", "dn", "p", "cell", "dir"))
    for q in QS:
        n, up, dn, med, mean, p = sign_test([r["d_quad"][q] for r in rows])
        name, direction = M06[q]
        got = "+" if med > 0 else "-" if med < 0 else "0"
        mark = "  AGREES" if got == direction else "  DISAGREES"
        print("%-30s %+9.4f %5d %5d %11.3g   %-14s %s%s"
              % (q, med, up, dn, p, name, direction, mark))
    #: SAY THE DENOMINATOR AND THE INDEPENDENCE UNIT ON THE WAY OUT. A p-value
    #: whose n is a checkpoint count and not a lineage count is the defect this
    #: file was written to avoid, and the reader cannot see the difference.
    if a.human:
        print("\n\nTOWARD OR AWAY FROM EACH HUMAN CORPUS, lineage-paired")
        print("distance on the (z_surprisal, z_drift) plane; NEGATIVE = alignment")
        print("moves the lineage TOWARD that corpus\n")
        print("%-24s %10s %5s %5s %11s %s"
              % ("corpus", "median", "twd", "awy", "p", "direction"))
        for c in sorted(corp):
            cz = zmed(corp[c])
            d = []
            for r in rows:
                db = math.dist(r["base_z"], cz)
                dk = statistics.mean(math.dist(z, cz) for z in r["kid_z"])
                d.append(dk - db)
            n, up, dn, med, mean, p = sign_test(d)
            #: `up` is AWAY (distance grew); name the columns for the reader
            #: rather than leaving them to infer the sign convention.
            print("%-24s %+10.4f %5d %5d %11.3g %s"
                  % (c, med, dn, up, p, "TOWARD" if med < 0 else "away"))

    print("\nn is LINEAGES (%d), not checkpoints (%d). A lineage with several"
          % (len(rows), sum(r["n_kids"] for r in rows) + len(rows)))
    print("aligned children contributes one difference, its children averaged first.")


if __name__ == "__main__":
    main()
