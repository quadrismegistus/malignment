"""Is "alignment compensates" real, or regression to the mean?

    python experiments/slot_ratings/identity/base_checks.py

Reads results/base_side.json, so it is cheap and does not re-query ClickHouse.

base_side.py correlates a group's BASE level against its aligned-minus-base
DELTA and finds negatives on ten scales, which reads as "alignment pulls the
groups together". That correlation is also exactly what measurement noise
produces on its own: the base term appears on both axes with opposite signs, so
a group whose base was overestimated gets an underestimated delta for free. Ten
significant negatives is what regression to the mean looks like when you have not
checked for it.

TWO CHECKS, both of which a real compensation effect passes and an artifact does
not:

  SPLIT-HALF. Base level from the odd lineages, delta from the even ones. The
  noise in the two terms is now independent, so the artifact cannot arise. Only
  harm, directedness and hedged survive; deference, procedural, arousal,
  assertiveness, aggression, mundanity, makes_better and agency do not.

  BETWEEN-GROUP SD. "Pulls together" is a claim about dispersion, so measure
  dispersion directly: sd of the group means on the base arm against the aligned
  arm. No change scores, no shared term. harm compresses most (ratio 0.73).
"""

import json, math, os
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results")
CANDIDATES = ["harm", "makes_worse", "deference", "procedural", "arousal",
              "directedness", "assertiveness", "aggression", "mundanity",
              "makes_better", "agency", "hedged"]


def main():
    from scipy import stats
    rows = json.load(open(os.path.join(OUT, "base_side.json")))["rows"]
    G = sorted({r["group"] for r in rows})
    saved = {"split_half": [], "dispersion": [], "pray": {}}

    print("A. SPLIT-HALF: base level from ODD lineages, delta from EVEN.")
    print("   %-14s %10s %10s   %10s %10s" % ("scale", "full rho", "p", "split rho", "p"))
    for s in CANDIDATES:
        ba, da, bo, de = [], [], [], []
        for g in G:
            v = sorted([r for r in rows if r["group"] == g
                        and r.get("base_" + s) is not None
                        and r.get("aligned_" + s) is not None],
                       key=lambda r: r["lineage"])
            if len(v) < 8:
                continue
            ba.append(st.mean(r["base_" + s] for r in v))
            da.append(st.mean(r["aligned_" + s] - r["base_" + s] for r in v))
            bo.append(st.mean(r["base_" + s] for r in v[0::2]))
            de.append(st.mean(r["aligned_" + s] - r["base_" + s] for r in v[1::2]))
        f, sp = stats.spearmanr(ba, da), stats.spearmanr(bo, de)
        ok = bool(sp.pvalue < 0.05 and sp.statistic < 0)
        print("   %-14s %+10.3f %10.2g   %+10.3f %10.2g %s"
              % (s, f.statistic, f.pvalue, sp.statistic, sp.pvalue,
                 "SURVIVES" if ok else ""))
        saved["split_half"].append(dict(scale=s, full_rho=f.statistic, full_p=f.pvalue,
                                        split_rho=sp.statistic, split_p=sp.pvalue,
                                        survives=ok))

    print("\nB. BETWEEN-GROUP SD, base arm against aligned arm.")
    print("   %-14s %10s %10s %8s" % ("scale", "sd base", "sd aligned", "ratio"))
    for s in CANDIDATES[:6]:
        bb = [st.mean(r["base_" + s] for r in rows if r["group"] == g
                      and r.get("base_" + s) is not None) for g in G]
        aa = [st.mean(r["aligned_" + s] for r in rows if r["group"] == g
                      and r.get("aligned_" + s) is not None) for g in G]
        print("   %-14s %10.4f %10.4f %8.2f"
              % (s, st.pstdev(bb), st.pstdev(aa), st.pstdev(aa) / st.pstdev(bb)))
        saved["dispersion"].append(dict(scale=s, sd_base=st.pstdev(bb),
                                        sd_aligned=st.pstdev(aa),
                                        ratio=st.pstdev(aa) / st.pstdev(bb)))

    print("\nC. `pray`: alignment AMPLIFIES the base ordering.")
    pb = [st.mean(r["p_base_pray"] for r in rows if r["group"] == g) for g in G]
    pa = [st.mean(r["p_aligned_pray"] for r in rows if r["group"] == g) for g in G]
    lr = [math.log((a + 1e-6) / (b + 1e-6)) for a, b in zip(pa, pb)]
    r1, r2 = stats.spearmanr(pb, lr), stats.spearmanr(pb, pa)
    top = [g for g, b in zip(G, pb) if b > 0.05]
    rest = [g for g, b in zip(G, pb) if b <= 0.05]
    mw = stats.mannwhitneyu([lr[G.index(g)] for g in top],
                            [lr[G.index(g)] for g in rest])
    print("   spearman(p_base, log ratio) %+.3f p=%.2g" % (r1.statistic, r1.pvalue))
    print("   spearman(p_base, p_aligned) %+.3f p=%.2g" % (r2.statistic, r2.pvalue))
    print("   between-group SD base %.5f -> aligned %.5f, ratio %.2f"
          % (st.pstdev(pb), st.pstdev(pa), st.pstdev(pa) / st.pstdev(pb)))
    print("   p_base>0.05 (%s): x%.2f    other %d groups: x%.2f    mannwhitney p=%.4g"
          % (", ".join(top), math.exp(st.mean(lr[G.index(g)] for g in top)),
             len(rest), math.exp(st.mean(lr[G.index(g)] for g in rest)), mw.pvalue))
    saved["pray"] = dict(rho_amplify=r1.statistic, p_amplify=r1.pvalue,
                         rho_order=r2.statistic, sd_ratio=st.pstdev(pa) / st.pstdev(pb),
                         top_groups=top, mannwhitney_p=mw.pvalue,
                         by_group={g: dict(base=b, aligned=a) for g, b, a in zip(G, pb, pa)})
    json.dump(json.loads(json.dumps(saved, default=float)), open(os.path.join(OUT, "base_checks.json"), "w"), indent=1)
    print("\n-> results/base_checks.json")


if __name__ == "__main__":
    main()
