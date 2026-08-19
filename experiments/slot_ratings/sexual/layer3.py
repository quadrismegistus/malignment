"""LAYER 3: the 5 sets as one, LINEAGE as the unit, sign test over 33.

    python experiments/slot_ratings/sexual/layer3.py

Layer 2 pooled the sets by making the SET one of two bootstrap dimensions, so
the delta test had n=5 scenes. Layer 2b tested each set alone at n=33 lineages.
This is the third option and the one that keeps the lineage as the unit while
still using all five sets:

    for each lineage    gap = mean over the 5 sets of [ level(M->F) - level(F->M) ]
    then                two-sided sign test over the 33 lineages

The added assumption over layer 2b is that the five sets are comparable enough to
AVERAGE within a lineage. That is a real assumption -- `charge` is +0.422 in
`grabbed` and -0.660 in `unzip`, so averaging it mixes scenes that disagree in
sign -- and it is why this layer is reported beside 2b rather than replacing it.
Where a scale is unanimous across the five (genitality) the average is a fair
summary; where it is not (charge, explicitness) the average is a number without
a referent and the per-set table is the honest one.

The Wilcoxon is printed beside the sign test since the sign test discards
magnitude.
"""

import collections, json, os, sys
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, HERE); sys.path.insert(0, REPO)
OUT = os.path.join(HERE, "results")
SCALES = ["genitality", "charge", "explicitness", "body_distance", "euphemism",
          "orality", "tactility", "incorporation", "exposure"]


def cell(lv, prompts, meta, DIRECTION, sets, a, b, label):
    from scipy import stats
    print("\n  %s  (%d sets averaged within each lineage)" % (label, len(sets)))
    print("     %-14s %10s %8s %10s %10s | %10s %8s %10s %10s"
          % ("scale", "BASE gap", "signs", "sign p", "wilcox",
             "DELTA gap", "signs", "sign p", "wilcox"))
    out = []
    for s in SCALES:
        gb, gd = collections.defaultdict(list), collections.defaultdict(list)
        for pr in sets:
            ap = [p for p in prompts if meta[p][0] == pr and DIRECTION[p] == a]
            bp = [p for p in prompts if meta[p][0] == pr and DIRECTION[p] == b]
            if not ap or not bp:
                continue
            for l in {l for (t, l) in lv if t == ap[0]}:
                va, vb = lv.get((ap[0], l), {}), lv.get((bp[0], l), {})
                kb, ka = "base_" + s, "aligned_" + s
                if kb in va and kb in vb:
                    gb[l].append(va[kb] - vb[kb])
                    if ka in va and ka in vb:
                        gd[l].append((va[ka] - vb[ka]) - (va[kb] - vb[kb]))
        B = [st.mean(v) for l, v in sorted(gb.items()) if v]
        D = [st.mean(v) for l, v in sorted(gd.items()) if v]
        if len(B) < 8:
            print("     %-14s %10s" % (s, "(too few)")); continue
        def t(v):
            if not v or all(abs(x) < 1e-12 for x in v):
                return None
            pos = sum(1 for x in v if x > 0); n = sum(1 for x in v if abs(x) > 1e-12)
            return (st.mean(v), pos, n, stats.binomtest(pos, n, 0.5).pvalue,
                    stats.wilcoxon(v).pvalue)
        tb, td = t(B), t(D)
        if tb is None:
            print("     %-14s %10s" % (s, "no variation")); continue
        row = ("     %-14s %+10.3f %4d/%-3d %10.2g%s %10.2g"
               % (s, tb[0], tb[1], tb[2], tb[3], "*" if tb[3] < .05 else " ", tb[4]))
        if td:
            row += (" | %+10.3f %4d/%-3d %10.2g%s %10.2g"
                    % (td[0], td[1], td[2], td[3], "*" if td[3] < .05 else " ", td[4]))
        print(row)
        out.append(dict(scale=s, base_gap=tb[0], base_pos=tb[1], base_n=tb[2],
                        base_sign_p=tb[3], base_wilcox_p=tb[4],
                        delta_gap=td[0] if td else None,
                        delta_pos=td[1] if td else None,
                        delta_n=td[2] if td else None,
                        delta_sign_p=td[3] if td else None,
                        delta_wilcox_p=td[4] if td else None))
    return out


def main():
    from analyse import load, masses
    from gender_pairs import DIRECTION, DIRECTIONAL, PAIRS
    from layer2 import levels
    R = load()
    prompts = sorted({k[0] for k in R})
    meta = {p: (PAIRS[p][0],) for p in prompts}
    lv = levels(R, masses(prompts), meta, None)
    nond = sorted({PAIRS[p][0] for p in prompts if PAIRS[p][0] not in DIRECTIONAL})
    print("=" * 108)
    r1 = cell(lv, prompts, meta, DIRECTION, sorted(DIRECTIONAL), "M->F", "F->M",
              "M->F minus F->M   (slot = the other person's body)")
    r2 = cell(lv, prompts, meta, DIRECTION, nond, "F", "M",
              "F minus M   (slot = own action or state)")
    json.dump(dict(_what="LAYER 3: sets averaged within lineage, sign test over "
                         "lineages", directional=r1, nondirectional=r2),
              open(os.path.join(OUT, "layer3.json"), "w"), indent=1)
    print("\n-> results/layer3.json")


if __name__ == "__main__":
    main()
