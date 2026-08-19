"""Each scenario alone, LINEAGE as the unit, sign test. The check never run.

    python experiments/slot_ratings/institutional/per_scenario.py

Section 11 tested the position gap two ways: with the lineage as the unit and
prompts averaged away (p as low as 1.8e-15), and with a crossed lineage-x-cluster
bootstrap that accounts for prompt variance too (`procedural` fell from 8e-10 to
0.314). I reported the crossed version as the truth.

The sexual study then showed why that is not enough on its own. There, pooling
across scenes produced numbers that were averages over scenes DISAGREEING IN
SIGN -- `charge` +0.422 at one scene and -0.660 at another -- and only the
per-scene table made it visible. A pooled null can be cancellation and a pooled
significance can be one scene carrying four.

So: each matched cluster ALONE, its own lineages as the unit, two-sided sign
test, and then COUNT HOW MANY AGREE. Unanimity across independently written
scenarios is stronger evidence than any pooled p, and disagreement in sign is
information the pooled statistic destroys.

    F21       12 matched pairs   x 50 lineages
    M03      126 matched pairs   x 50 lineages   (18 scenarios x 7 person/modal strata)
    slotpov    6 matched sets    x 31 lineages
"""

import collections, json, os, sys
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results", "base_side")
SCALES = ["procedural", "deference", "mediation", "agency", "arousal", "abstraction",
          "specificity", "termination", "collective", "assertiveness", "target"]


def main():
    from scipy import stats
    saved = {}
    for corpus in ("f21", "m03", "slotpov"):
        p = os.path.join(OUT, "%s.json" % corpus)
        if not os.path.exists(p):
            continue
        rows = json.load(open(p))["rows"]
        by = collections.defaultdict(dict)
        for r in rows:
            by[(r["cluster"], r["lineage"])][r["position"]] = r
        clusters = sorted({c for c, _ in by})
        print("\n" + "=" * 100)
        print("%s: %d matched clusters, %d lineages"
              % (corpus.upper(), len(clusters), len({l for _, l in by})))
        print("  %-14s %8s %26s | %26s"
              % ("scale", "clusters", "BASE gap (inst - indiv)", "DELTA gap"))
        print("  %-14s %8s %6s %6s %6s %5s | %6s %6s %6s %5s"
              % ("", "tested", "sig", "pos", "neg", "unan", "sig", "pos", "neg", "unan"))
        res = []
        for s in SCALES:
            bsig = bpos = bneg = 0
            dsig = dpos = dneg = 0
            n = 0
            detail = []
            for c in clusters:
                gb, gd = [], []
                for (cc, l), d in by.items():
                    if cc != c or "indiv" not in d or "inst" not in d:
                        continue
                    a, b = d["inst"], d["indiv"]
                    kb, ka = "base_" + s, "aligned_" + s
                    if a.get(kb) is not None and b.get(kb) is not None:
                        gb.append(a[kb] - b[kb])
                        if a.get(ka) is not None and b.get(ka) is not None:
                            gd.append((a[ka] - b[ka]) - (a[kb] - b[kb]))
                if len(gb) < 8:
                    continue
                n += 1
                def sg(v):
                    if not v or all(abs(x) < 1e-12 for x in v):
                        return None
                    pos = sum(1 for x in v if x > 0)
                    nn = sum(1 for x in v if abs(x) > 1e-12)
                    return pos, nn, stats.binomtest(pos, nn, .5).pvalue, st.mean(v)
                tb, td = sg(gb), sg(gd)
                if tb and tb[2] < .05:
                    bsig += 1
                    bpos += tb[3] > 0; bneg += tb[3] < 0
                if td and td[2] < .05:
                    dsig += 1
                    dpos += td[3] > 0; dneg += td[3] < 0
                detail.append(dict(cluster=c, base_mean=tb[3] if tb else None,
                                   base_p=tb[2] if tb else None,
                                   delta_mean=td[3] if td else None,
                                   delta_p=td[2] if td else None))
            if not n:
                continue
            bu = "YES" if bsig and (bpos == bsig or bneg == bsig) else ""
            du = "YES" if dsig and (dpos == dsig or dneg == dsig) else ""
            print("  %-14s %8d %6d %6d %6d %5s | %6d %6d %6d %5s"
                  % (s, n, bsig, bpos, bneg, bu, dsig, dpos, dneg, du))
            res.append(dict(scale=s, n_clusters=n, base_sig=bsig, base_pos=bpos,
                            base_neg=bneg, base_unanimous=bool(bu),
                            delta_sig=dsig, delta_pos=dpos, delta_neg=dneg,
                            delta_unanimous=bool(du), clusters=detail))
        saved[corpus] = res
    json.dump(dict(_what="each matched cluster alone, lineage as unit, two-sided "
                         "sign test; counts of how many clusters agree",
                   results=saved), open(os.path.join(OUT, "per_scenario.json"), "w"),
              indent=1)
    print("\n-> results/base_side/per_scenario.json")


if __name__ == "__main__":
    main()
