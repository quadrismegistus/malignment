"""Named group contrasts, paired within lineage: base gap, aligned gap, and DiD.

    python experiments/slot_ratings/identity/group_pairs.py

Four contrasts RH named, each a pair of groups that share a frame and a scene and
differ in the way the question is about:

    men          vs women
    Israelis     vs Palestinians
    Muslims      vs Jews
    Americans    vs African-Americans

The same lineage sees BOTH groups, so the pair is blocked on the lineage and the
test is a two-sided sign test over the lineages the two share. Three quantities,
reported together because the third is meaningless without the first two:

    base gap      A minus B on the base arm
    aligned gap   the same on the aligned arm
    DiD           how much alignment CHANGED that gap

POWER IS THE BINDING CONSTRAINT and is printed per contrast. With n shared
lineages the smallest attainable two-sided sign p is 2/2^n, so at n=14 a
unanimous result reaches 0.00012 and 12 of 14 reaches 0.013, while at n=16 a
12/16 reaches 0.077. A null here bounds the effect at that n; it does not
exclude it. The identity panel is 14-20 lineages, the thinnest of the three
studies, and will resolve much more at the full 50-pair roster.
"""

import collections, json, os, sys
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results")
CONTRASTS = [("men", "women"), ("Israelis", "Palestinians"),
             ("Muslims", "Jews"), ("Americans", "African-Americans")]
SCALES = ["interiority", "deliberation", "harm", "aggression", "directedness",
          "vocalisation", "mundanity", "superego", "makes_better", "makes_worse",
          "fit", "hedged"]


def main():
    from scipy import stats
    rows = json.load(open(os.path.join(OUT, "base_side.json")))["rows"]
    by = collections.defaultdict(dict)
    for r in rows:
        by[r["lineage"]][r["group"]] = r
    saved = []
    for A, B in CONTRASTS:
        shared = sorted(l for l in by if A in by[l] and B in by[l])
        print("\n" + "=" * 100)
        print("  %s  vs  %s   -- %d shared lineages" % (A, B, len(shared)))
        if len(shared) >= 2:
            print("     smallest attainable two-sided sign p at n=%d: %.2g"
                  % (len(shared), 2 / 2 ** len(shared)))
        print("     %-14s %20s %20s | %20s"
              % ("scale", "BASE gap  %s-%s" % (A[:4], B[:4]), "ALIGNED gap", "DiD"))
        for s in SCALES:
            gb, ga, gd = [], [], []
            for l in shared:
                a, b = by[l][A], by[l][B]
                kb, ka = "base_" + s, "aligned_" + s
                if a.get(kb) is not None and b.get(kb) is not None:
                    gb.append(a[kb] - b[kb])
                    if a.get(ka) is not None and b.get(ka) is not None:
                        ga.append(a[ka] - b[ka])
                        gd.append((a[ka] - b[ka]) - (a[kb] - b[kb]))
            if len(gb) < 8:
                continue

            def sg(v):
                if not v or all(abs(x) < 1e-12 for x in v):
                    return None
                pos = sum(1 for x in v if x > 0)
                n = sum(1 for x in v if abs(x) > 1e-12)
                return st.mean(v), pos, n, stats.binomtest(pos, n, .5).pvalue
            tb, ta, td = sg(gb), sg(ga), sg(gd)
            if not tb:
                continue
            def f(t):
                return ("%+7.3f %3d/%-2d %6.3g%s"
                        % (t[0], t[1], t[2], t[3], "*" if t[3] < .05 else " ")) if t else "%20s" % "-"
            print("     %-14s %s %s | %s" % (s, f(tb), f(ta), f(td)))
            saved.append(dict(a=A, b=B, scale=s, n_lineages=len(shared),
                              base_gap=tb[0], base_pos=tb[1], base_p=tb[3],
                              aligned_gap=ta[0] if ta else None,
                              aligned_p=ta[3] if ta else None,
                              did=td[0] if td else None,
                              did_pos=td[1] if td else None,
                              did_p=td[3] if td else None))
    json.dump(dict(_what="four named group contrasts, blocked on lineage: base gap, "
                         "aligned gap, and the change in the gap", rows=saved),
              open(os.path.join(OUT, "group_pairs.json"), "w"), indent=1)
    print("\n-> results/group_pairs.json")


if __name__ == "__main__":
    main()
