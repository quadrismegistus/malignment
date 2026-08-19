"""LAYER 2b: each matched set on its own, LINEAGE as the unit, sign test.

    python experiments/slot_ratings/sexual/layer2b.py

Layer 2 pooled the five directional sets and tested with the SET as one of two
bootstrap dimensions, so the delta-gap test effectively had n=5 scenes. That is
few enough that a null there is uninformative about whether alignment changes the
gap. Here each set is tested alone against its own 33 lineages:

    gap        = level(M->F prompt) - level(F->M prompt), computed per lineage
    delta gap  = that gap on the aligned arm minus on the base arm, per lineage

and the test is a two-sided sign test over the 33 lineages, which assumes only
that the lineages are exchangeable observations of that scene. The Wilcoxon is
printed beside it because the sign test throws away magnitude.

Five independent tests, so the evidence is CONSISTENCY ACROSS THEM rather than
any single p, in the same way layer 1's direction unanimity was the result.
"""

import collections, json, os, sys
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, HERE); sys.path.insert(0, REPO)
OUT = os.path.join(HERE, "results")
SCALES = ["genitality", "charge", "explicitness", "body_distance", "euphemism",
          "orality", "tactility", "incorporation", "exposure"]


def main():
    from scipy import stats
    from analyse import load, masses
    from gender_pairs import DIRECTION, DIRECTIONAL, PAIRS
    from layer2 import levels
    R = load()
    prompts = sorted({k[0] for k in R})
    meta = {p: (PAIRS[p][0],) for p in prompts}
    M = masses(prompts)
    lv = levels(R, M, meta, None)
    saved = []
    for pr in sorted(DIRECTIONAL):
        a = [p for p in prompts if meta[p][0] == pr and DIRECTION[p] == "M->F"][0]
        b = [p for p in prompts if meta[p][0] == pr and DIRECTION[p] == "F->M"][0]
        lins = sorted({l for (t, l) in lv if t in (a, b)})
        print("=" * 100)
        print("  %s   M->F: %s ___" % (pr, a))
        print("  %s   F->M: %s ___" % (" " * len(pr), b))
        print("     %-14s %20s %6s %9s | %20s %6s %9s"
              % ("scale", "BASE gap (M->F - F->M)", "signs", "p", "DELTA gap", "signs", "p"))
        for s in SCALES:
            gb, gd = [], []
            for l in lins:
                va, vb = lv.get((a, l), {}), lv.get((b, l), {})
                kb, ka = "base_" + s, "aligned_" + s
                if kb in va and kb in vb:
                    gb.append(va[kb] - vb[kb])
                    if ka in va and ka in vb:
                        gd.append((va[ka] - vb[ka]) - (va[kb] - vb[kb]))
            if len(gb) < 8:
                print("     %-14s %20s" % (s, "(too few lineages)")); continue
            def sgn(v):
                pos = sum(1 for x in v if x > 0); n = sum(1 for x in v if abs(x) > 1e-12)
                if n == 0:
                    return pos, 0, float("nan")
                return pos, n, stats.binomtest(pos, n, 0.5).pvalue
            pb, nb, sb = sgn(gb)
            row = "     %-14s %+20.3f %3d/%-2d %9.2g%s" % (
                s, st.mean(gb), pb, nb, sb, "*" if sb == sb and sb < .05 else " ")
            if len(gd) >= 8:
                pd_, nd, sd = sgn(gd)
                row += " | %+20.3f %3d/%-2d %9.2g%s" % (
                    st.mean(gd), pd_, nd, sd, "*" if sd == sd and sd < .05 else "")
            print(row)
            saved.append(dict(pair=pr, scale=s, base_gap=st.mean(gb),
                              base_pos=pb, base_n=nb, base_p=sb,
                              delta_gap=st.mean(gd) if gd else None,
                              delta_pos=(sgn(gd)[0] if len(gd) >= 8 else None),
                              delta_n=(sgn(gd)[1] if len(gd) >= 8 else None),
                              delta_p=(sgn(gd)[2] if len(gd) >= 8 else None)))
    print("\n  CONSISTENCY across the 5 sets (sign test, p<0.05):")
    print("     %-14s %10s %10s" % ("scale", "base gap", "delta gap"))
    for s in SCALES:
        rs = [r for r in saved if r["scale"] == s]
        nb = sum(1 for r in rs if r["base_p"] == r["base_p"] and r["base_p"] < .05)
        bd = sum(1 for r in rs if r["base_p"] == r["base_p"] and r["base_p"] < .05
                 and r["base_gap"] < 0)
        nd = sum(1 for r in rs if r["delta_p"] is not None and r["delta_p"] == r["delta_p"]
                 and r["delta_p"] < .05)
        dd = sum(1 for r in rs if r["delta_p"] is not None and r["delta_p"] == r["delta_p"]
                 and r["delta_p"] < .05 and r["delta_gap"] < 0)
        print("     %-14s %2d/5  (%d neg)  %2d/5  (%d neg)" % (s, nb, bd, nd, dd))
    json.dump(dict(_what="LAYER 2b: each directional matched set alone, lineage as "
                         "unit, two-sided sign test over 33 lineages", rows=saved),
              open(os.path.join(OUT, "layer2b.json"), "w"), indent=1)
    print("\n-> results/layer2b.json")


if __name__ == "__main__":
    main()
