"""Read a run's mechanism.jsonl and say what carried the axis shift.

    python experiments/displacement_axis/mechanism_report.py --run pilot2

Six blocks:

  0. CONSISTENCY   dN_total recomputed here against dN_position from run.py.
                   Two code paths for one quantity; if they disagree, nothing
                   below is worth reading and the block says so rather than
                   printing a table on top of it.
  1. IS IT SHARPENING AT ALL   entropy change and dT. The decomposition
                   attributes a shift; this asks whether the premise holds --
                   a model that does not concentrate cannot be shifting by
                   concentrating, whatever the attribution says.
  2. HEADLINE      dN_sharpen, dN_reorder, interaction over all cells, plus the
                   share of cells where each dominates.
  3. BY SIGNATURE  the same, split by the mass decomposition's own classes.
  4. RANKS         d_rho and d_auc against dN_total. **Read this THROUGH block
                   2**: if sharpening dominates, ranks disagreeing with mass is
                   the predicted result and not a fault in either.
  5. BY PAIR       per lineage, because a mechanism that holds on average can
                   reverse inside one checkpoint -- and bloomz, whose alignment
                   is multitask prompting rather than RLHF, is in this set
                   precisely as the case where it might.
"""

import argparse
import collections
import json
import math
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")


def pearson(x, y):
    n = len(x)
    if n < 3:
        return None
    mx, my = sum(x) / n, sum(y) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    if sxx <= 0 or syy <= 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def med(rows, k):
    v = [r[k] for r in rows if r.get(k) is not None]
    return st.median(v) if v else None


def f(v, w=9, p=4):
    return ("%+*.*f" % (w, p, v)) if v is not None else " " * (w - 3) + "n/a"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--run", default="pilot2")
    ap.add_argument("--file", default="mechanism.jsonl")
    a = ap.parse_args(argv)
    rundir = os.path.join(RESULTS, a.run)
    rows = [json.loads(l) for l in open(os.path.join(rundir, a.file))]
    print("run %s | %s | %d cells\n" % (a.run, a.file, len(rows)))

    print("0. CONSISTENCY with run.py")
    pair = [(r["dN_total"], r["dN_position_from_run"]) for r in rows
            if r.get("dN_total") is not None and r.get("dN_position_from_run") is not None]
    if pair:
        worst = max(abs(u - v) for u, v in pair)
        print("   n=%d  largest |dN_total - dN_position| = %.2e  %s"
              % (len(pair), worst, "OK" if worst < 1e-9 else "*** DISAGREE ***"))
        if worst >= 1e-9:
            print("   The two code paths do not agree. Stopping: everything below\n"
                  "   would be a reading of an unreconciled quantity.")
            return 1

    print("\n1. IS THE PREMISE TRUE -- does alignment concentrate here?")
    de = [r["d_entropy"] for r in rows if r.get("d_entropy") is not None]
    dt = [r["dT"] for r in rows if r.get("dT") is not None]
    if de:
        print("   entropy change   median %s   fell in %3.0f%% of cells"
              % (f(st.median(de)), 100 * sum(1 for v in de if v < 0) / len(de)))
    if dt:
        print("   scored mass dT   median %s   rose in %3.0f%% of cells"
              % (f(st.median(dt)), 100 * sum(1 for v in dt if v > 0) / len(dt)))

    def block(rows, label):
        n = len(rows)
        sh = [r["dN_sharpen"] for r in rows if r.get("dN_sharpen") is not None]
        re = [r["dN_reorder"] for r in rows if r.get("dN_reorder") is not None]
        ix = [r["interaction"] for r in rows if r.get("interaction") is not None]
        both = [(r["dN_sharpen"], r["dN_reorder"]) for r in rows
                if r.get("dN_sharpen") is not None and r.get("dN_reorder") is not None]
        dom = (sum(1 for s, q in both if abs(s) > abs(q)) / len(both)) if both else None
        print("   %-14s %5d %s %s %s %s %8s"
              % (label, n, f(med(rows, "dN_total")), f(st.median(sh) if sh else None),
                 f(st.median(re) if re else None), f(st.median(ix) if ix else None),
                 ("%.0f%%" % (100 * dom)) if dom is not None else "n/a"))

    hdr = "   %-14s %5s %9s %9s %9s %9s %8s" % (
        "", "cells", "total", "sharpen", "reorder", "interact", "sharp>ord")
    print("\n2. HEADLINE (medians; negative = toward the NICE pole)")
    print(hdr)
    block(rows, "all cells")

    print("\n3. BY SIGNATURE (classes defined by the mass decomposition)")
    print(hdr)
    bysig = collections.defaultdict(list)
    for r in rows:
        bysig[r["signature"]].append(r)
    for s in ("displacement", "churn", "reverse", "arrival"):
        if bysig.get(s):
            block(bysig[s], s)

    print("\n4. RANK STATISTICS against dN_total")
    #: **THE TWO FAMILIES POINT NICE-WARD IN OPPOSITE SIGNS AND THE FIRST DRAFT
    #: OF THIS BLOCK DID NOT.** `d_rho` was built to share the mass convention
    #: (negative = nice) by correlating against `-rank`. `d_auc` was not: it is
    #: P(nice outranks naughty), so nice-ward is POSITIVE. Comparing them with
    #: one rule reported AUC at pearson -0.549 and 24% agreement -- which is
    #: -0.549 and 76% AGREEING, printed as the sharpest clash in the table.
    #:
    #: This is the failure the docstring warns about for rho, committed on the
    #: line below it. `orient` makes the convention a property of the statistic
    #: rather than of my memory at the moment of writing the comparison.
    for k, lab, orient in (("d_rho", "rank rho", +1), ("d_auc", "pole AUC", -1)):
        p = [(r["dN_total"], r[k] * orient) for r in rows
             if r.get("dN_total") is not None and r.get(k) is not None]
        if not p:
            continue
        x = [u for u, _ in p]
        y = [v for _, v in p]
        agree = sum(1 for u, v in p if (u < 0) == (v < 0)) / len(p)
        r = pearson(x, y)
        print("   %-18s %6d %9s %10.0f%%%s"
              % (lab, len(p), ("%+.3f" % r) if r is not None else "n/a", 100 * agree,
                 "   [sign flipped to the mass convention]" if orient < 0 else ""))
        print("      median %s   (mass median %s)" % (f(st.median(y)), f(st.median(x))))

    print("\n5. BY PAIR")
    print("   %-42s %5s %9s %9s %9s %8s"
          % ("pair", "cells", "total", "sharpen", "reorder", "sharp>ord"))
    bypair = collections.defaultdict(list)
    for r in rows:
        bypair[(r["base"], r["endpoint"])].append(r)
    scored = []
    for (b, e), g in bypair.items():
        both = [(r["dN_sharpen"], r["dN_reorder"]) for r in g
                if r.get("dN_sharpen") is not None and r.get("dN_reorder") is not None]
        dom = (sum(1 for s, q in both if abs(s) > abs(q)) / len(both)) if both else 0.0
        scored.append((dom, b, e, g))
    for dom, b, e, g in sorted(scored, reverse=True):
        short = (b.split("/")[-1] + " -> " + e.split("/")[-1])[:42]
        print("   %-42s %5d %s %s %s %7.0f%%"
              % (short, len(g), f(med(g, "dN_total")), f(med(g, "dN_sharpen")),
                 f(med(g, "dN_reorder")), 100 * dom))
    return 0


if __name__ == "__main__":
    sys.exit(main())
