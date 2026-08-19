"""Identity's claims re-tested with the LINEAGE as the unit, not the group.

    python experiments/slot_ratings/identity/per_lineage.py

`base_side.py` established three things by computing a statistic ACROSS THE 24
GROUPS with lineages pooled inside it:

    the base carries the ordering    spearman(base order, aligned order) = 0.970
    alignment amplifies              spearman(p_base, log ratio) = +0.811
    alignment compresses harm        between-group SD 0.300 -> 0.218, ratio 0.73

Each is a single number over 24 points, so **the lineage was never the unit** and
none of them says whether the models agree. A cross-group correlation can be
produced by a handful of lineages and nothing in the output would show it.

So: compute each statistic WITHIN a lineage, over its own 24 groups, then sign
test across lineages. The question becomes "in how many of the 33 models does
alignment amplify", which is the identity analogue of the per-scenario test the
institutional and sexual studies needed.

    amplification   spearman(p_base, log(p_aligned/p_base)) over 24 groups, per lineage
    dispersion      SD across groups on the aligned arm / SD on the base arm
    order stability spearman(base ranking, aligned ranking) over 24 groups
"""

import collections, json, math, os, sys
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results")
SCALES = ["harm", "aggression", "directedness", "interiority", "vocalisation",
          "mundanity", "fit", "makes_better", "makes_worse", "superego",
          "deliberation", "hedged"]


def main():
    from scipy import stats
    rows = json.load(open(os.path.join(OUT, "base_side.json")))["rows"]
    by = collections.defaultdict(dict)
    for r in rows:
        by[r["lineage"]][r["group"]] = r
    lins = sorted(by)
    print("identity `room` sweep: %d lineages, %d groups\n"
          % (len(lins), len({r["group"] for r in rows})))

    def sg(v, null=0.0):
        v = [x for x in v if x == x]
        if not v:
            return None
        pos = sum(1 for x in v if x > null); n = sum(1 for x in v if abs(x - null) > 1e-12)
        return (st.median(v), pos, n, stats.binomtest(pos, n, .5).pvalue)

    print("=" * 92)
    print("1. `pray` -- does alignment AMPLIFY the base ordering, within each lineage?")
    amp, ordr, sdr = [], [], []
    for l in lins:
        g = by[l]
        pb = [g[k]["p_base_pray"] for k in sorted(g)]
        pa = [g[k]["p_aligned_pray"] for k in sorted(g)]
        if len(pb) < 10 or len(set(pb)) < 3:
            continue
        lr = [math.log((a + 1e-6) / (b + 1e-6)) for a, b in zip(pa, pb)]
        amp.append(stats.spearmanr(pb, lr).statistic)
        ordr.append(stats.spearmanr(pb, pa).statistic)
        sdr.append(st.pstdev(pa) / st.pstdev(pb) if st.pstdev(pb) > 0 else float("nan"))
    t = sg(amp)
    print("   spearman(p_base, log ratio) per lineage:")
    print("     median %+.3f | POSITIVE in %d of %d | sign p=%.3g%s"
          % (t[0], t[1], t[2], t[3], " *" if t[3] < .05 else ""))
    print("     pooled-across-groups value reported earlier: +0.811")
    t2 = sg(ordr)
    print("   spearman(base order, aligned order) per lineage:")
    print("     median %+.3f | min %+.3f | max %+.3f   (pooled: +0.970)"
          % (t2[0], min(ordr), max(ordr)))
    t3 = sg(sdr, null=1.0)
    print("   between-group SD ratio aligned/base per lineage:")
    print("     median %.3f | ABOVE 1 in %d of %d | sign p=%.3g%s   (pooled: 1.47)"
          % (t3[0], t3[1], t3[2], t3[3], " *" if t3[3] < .05 else ""))

    print("\n" + "=" * 92)
    print("2. DISPERSION per scale: does alignment compress or expand the groups?")
    print("   %-14s %8s %10s %8s %10s   %s"
          % ("scale", "median", "below 1", "sign p", "pooled", "verdict"))
    saved = []
    for s in SCALES:
        rat = []
        for l in lins:
            g = by[l]
            b = [g[k].get("base_" + s) for k in sorted(g)]
            a = [g[k].get("aligned_" + s) for k in sorted(g)]
            b = [x for x in b if x is not None]; a = [x for x in a if x is not None]
            if len(b) < 10 or len(a) < 10 or st.pstdev(b) <= 0:
                continue
            rat.append(st.pstdev(a) / st.pstdev(b))
        if len(rat) < 8:
            continue
        below = sum(1 for x in rat if x < 1)
        p = stats.binomtest(below, len(rat), .5).pvalue
        pooled = None
        print("   %-14s %8.3f %6d/%-3d %8.3g%s %10s   %s"
              % (s, st.median(rat), below, len(rat), p, " *" if p < .05 else " ",
                 "-", "COMPRESSES" if below > len(rat) * .7 and p < .05 else
                 "EXPANDS" if below < len(rat) * .3 and p < .05 else ""))
        saved.append(dict(scale=s, median_ratio=st.median(rat), below_one=below,
                          n_lineages=len(rat), p=p))
    json.dump(dict(_what="identity claims with the LINEAGE as the unit: "
                         "amplification, order stability and dispersion computed "
                         "within each lineage over its 24 groups, then sign-tested",
                   amplification=dict(median=sg(amp)[0], positive=sg(amp)[1],
                                      n=sg(amp)[2], p=sg(amp)[3], values=amp),
                   order=dict(median=sg(ordr)[0], values=ordr),
                   pray_sd_ratio=dict(median=sg(sdr, 1.0)[0], above_one=sg(sdr, 1.0)[1],
                                      n=sg(sdr, 1.0)[2], p=sg(sdr, 1.0)[3], values=sdr),
                   dispersion=saved),
              open(os.path.join(OUT, "per_lineage.json"), "w"), indent=1)
    print("\n-> results/per_lineage.json")


if __name__ == "__main__":
    main()
