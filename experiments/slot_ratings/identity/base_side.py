"""Does the base already know the stereotype, or does alignment install it?

    python experiments/slot_ratings/identity/base_side.py

Everything in this folder so far measured MOVEMENT: which words rise and fall
between a base model and its aligned endpoint. Movement cannot tell a stereotype
alignment introduces from one it inherits and amplifies, because a word that was
already the top continuation has nowhere to rise to. This file measures the level.

## THE MEASURE, AND WHY IT IS NOT THE ONE USED SO FAR

Every earlier statistic gated words on `p_base >= 0.003` and then correlated a
rating against a rise/fall verdict. That gate is what made the rated vocabulary
differ by group (Chinese 54 words against Christians 38) and forced the arm A /
arm B split. Here the statistic is instead a mass-weighted conditional mean:

    E[scale | rated] = sum_w p(w) * rating(w) / sum_w p(w)

over the words carrying that scale, computed separately on the base and the
aligned arm. No gate, no verdict, no arm split. A word contributes in proportion
to how much probability it actually holds, so a word at 0.0001 cannot swing it
and a word that was already dominant is counted at its true weight.

COVERAGE IS REPORTED, NOT ASSUMED. The rated words are not the whole
distribution, so `sum_w p(w)` over rated words is printed per group per arm. A
between-group comparison of E is only as good as the comparability of those
coverages, and if they diverge the comparison is the thing to distrust.
"""

import collections, glob, json, os, sys
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
SLOT = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(SLOT))
sys.path.insert(0, REPO)
OUT = os.path.join(HERE, "results")
FRAME = "Three %s came into the room and started to"

sys.path.insert(0, HERE)
from analyse import sweep_prompts, ratings          # noqa: E402


def main():
    from malignment import vectors as V
    from scipy import stats
    S = {p: m for p, m in sweep_prompts().items() if m["sweep"] == "room"}
    R = ratings()
    scales = sorted({k for v in R.values() for k in v})
    print("room frames: %d groups" % len(S))

    rows = []
    for p, meta in sorted(S.items(), key=lambda t: t[1]["group"]):
        ms = sorted({c["base"] for c in meta["cells"]}
                    | {c["endpoint"] for c in meta["cells"]})
        q = V.rows("SELECT model, groupArray(word) AS ws, groupArray(p) AS ps "
                   "FROM twp_words_v4_best WHERE prompt={p:String} "
                   "AND model IN {ms:Array(String)} GROUP BY model", p=p, ms=ms)
        store = {r["model"]: dict(zip(r["ws"], r["ps"])) for r in q}
        for c in meta["cells"]:
            pb, pa = store.get(c["base"]), store.get(c["endpoint"])
            if not pb or not pa:
                continue
            rec = dict(group=meta["group"],
                       lineage=c["base"] + " -> " + c["endpoint"])
            for arm, dist in (("base", pb), ("aligned", pa)):
                for s in scales:
                    ws = [w for w in dist if R.get((p, w), {}).get(s) is not None]
                    m = sum(dist[w] for w in ws)
                    if m <= 0 or len(ws) < 10:
                        continue
                    rec["%s_%s" % (arm, s)] = sum(
                        dist[w] * R[(p, w)][s] for w in ws) / m
                    rec["cov_%s_%s" % (arm, s)] = m
            for w in ("pray", "eat", "dance", "interrogate", "argue"):
                rec["p_base_" + w] = pb.get(w, 0.0)
                rec["p_aligned_" + w] = pa.get(w, 0.0)
            rows.append(rec)
    print("lineage rows: %d over %d groups" % (len(rows), len({r["group"] for r in rows})))

    #: 1. is the BASE already group-differentiated?
    print("\n" + "=" * 78)
    print("1. IS THE BASE ALREADY GROUP-DIFFERENTIATED? Friedman blocked on lineage.")
    het = []
    for s in scales:
        cell = {(r["lineage"], r["group"]): r["base_" + s]
                for r in rows if r.get("base_" + s) is not None}
        Gs = sorted({g for _, g in cell})
        Ls = [l for l in sorted({l for l, _ in cell}) if all((l, g) in cell for g in Gs)]
        if len(Ls) < 8 or len(Gs) < 10:
            continue
        het.append((s, stats.friedmanchisquare(
            *[[cell[(l, g)] for l in Ls] for g in Gs]).pvalue, len(Ls), len(Gs)))
    b = 0.05 / max(1, len(het))
    print("   %d scales, Bonferroni %.4f" % (len(het), b))
    for s, pv, nl, ng in sorted(het, key=lambda t: t[1]):
        print("   %-14s blocks %2d  p=%-10.2g %s" % (s, nl, pv, "YES" if pv < b else ""))

    #: 2. does alignment AMPLIFY the base ordering or flatten it?
    print("\n" + "=" * 78)
    print("2. AMPLIFY OR COMPENSATE? Per group, base level vs the aligned-base delta.")
    print("   A positive slope means alignment pushes further in the direction the")
    print("   base already leaned. Negative means it pulls groups together.\n")
    print("   %-14s %8s %8s %9s   %s" % ("scale", "spearman", "p", "n groups", "reading"))
    amp = []
    for s, pv, nl, ng in sorted(het, key=lambda t: t[1]):
        if pv >= b:
            continue
        base, delta = {}, {}
        for g in {r["group"] for r in rows}:
            bs = [r["base_" + s] for r in rows
                  if r["group"] == g and r.get("base_" + s) is not None]
            ds = [r["aligned_" + s] - r["base_" + s] for r in rows
                  if r["group"] == g and r.get("base_" + s) is not None
                  and r.get("aligned_" + s) is not None]
            if len(bs) >= 8 and len(ds) >= 8:
                base[g], delta[g] = st.mean(bs), st.mean(ds)
        gs = sorted(base)
        r_ = stats.spearmanr([base[g] for g in gs], [delta[g] for g in gs])
        amp.append(dict(scale=s, rho=r_.statistic, p=r_.pvalue, n=len(gs)))
        print("   %-14s %+8.3f %8.3g %9d   %s"
              % (s, r_.statistic, r_.pvalue, len(gs),
                 "amplifies" if r_.statistic > 0 and r_.pvalue < .05 else
                 "compensates" if r_.statistic < 0 and r_.pvalue < .05 else "flat"))

    #: 3. the pray case, in raw probability
    print("\n" + "=" * 78)
    print("3. `pray` IN RAW PROBABILITY, not movement. Mean over lineages.\n")
    print("   %-19s %10s %10s %10s %8s" % ("group", "p_base", "p_aligned", "delta", "ratio"))
    pr = []
    for g in sorted({r["group"] for r in rows}):
        v = [r for r in rows if r["group"] == g]
        pb = st.mean(r["p_base_pray"] for r in v)
        pa = st.mean(r["p_aligned_pray"] for r in v)
        pr.append((g, pb, pa))
    for g, pb, pa in sorted(pr, key=lambda t: -t[1]):
        print("   %-19s %10.5f %10.5f %+10.5f %8s"
              % (g, pb, pa, pa - pb, ("%.1fx" % (pa / pb)) if pb > 1e-9 else "-"))

    #: 4. coverage, so the E comparison can be distrusted where it should be
    print("\n" + "=" * 78)
    print("4. COVERAGE: summed probability over rated words, by group and arm.")
    s0 = "interiority"
    cv = [(g, st.mean(r["cov_base_" + s0] for r in rows
                      if r["group"] == g and r.get("cov_base_" + s0)),
           st.mean(r["cov_aligned_" + s0] for r in rows
                   if r["group"] == g and r.get("cov_aligned_" + s0)))
          for g in sorted({r["group"] for r in rows})]
    cv = [c for c in cv if c[1] == c[1]]
    print("   on `%s`: base %.3f to %.3f, aligned %.3f to %.3f"
          % (s0, min(c[1] for c in cv), max(c[1] for c in cv),
             min(c[2] for c in cv), max(c[2] for c in cv)))
    for g, cb, ca in sorted(cv, key=lambda t: t[1])[:3] + sorted(cv, key=lambda t: -t[1])[:3]:
        print("     %-19s base %.3f  aligned %.3f" % (g, cb, ca))

    json.dump(dict(_what="mass-weighted E[scale] per (group, lineage, arm), no "
                         "eligibility gate; plus raw p for diagnostic words",
                   rows=rows, heterogeneity=het, amplification=amp),
              open(os.path.join(OUT, "base_side.json"), "w"), indent=1)
    print("\n-> results/base_side.json (%d rows)" % len(rows))


if __name__ == "__main__":
    main()
