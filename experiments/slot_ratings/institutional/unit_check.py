"""Does the position gap survive with the PROMPT as unit, not the lineage?

    python experiments/slot_ratings/institutional/unit_check.py

`base_side_positions.py` uses the lineage as the significance unit: prompts are
averaged within a lineage, then Wilcoxon over 50 (F21, M03) or 32 (slotpov)
lineages. That is the right unit for "does this hold across models", and it is
not pooling -- n is the lineage count.

But averaging prompts inside the unit means the test cannot see whether one
prompt or twelve carry the effect. A gap driven by a single prompt can still be
unanimous across 50 lineages, because every lineage sees that same prompt.

So this runs the ORTHOGONAL test: average over lineages first, then treat the
PROMPT (F21), the matched SET (slotpov) or the SCENARIO (M03) as the unit. An
effect present on both units is carried by the corpus. An effect present only on
the lineage unit is carried by a few prompts and generalises to models, not to
prompts.

The two tests are not nested and neither dominates. Both are reported.
"""

import collections, json, os
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results", "base_side")


def main():
    from scipy import stats
    summary = {}
    for c in ("f21", "m03", "slotpov"):
        p = os.path.join(OUT, "%s.json" % c)
        if not os.path.exists(p):
            print("%s: not built yet" % c)
            continue
        d = json.load(open(p))
        rows, res = d["rows"], d["results"]
        scales = [r["scale"] for r in res]
        nlin = len({r["lineage"] for r in rows})
        print("\n" + "=" * 92)
        print("%s: lineage unit n=%d | prompt-side unit below" % (c.upper(), nlin))
        out = []
        for s in scales:
            #: average over LINEAGES first, so the prompt is the unit
            per = collections.defaultdict(list)
            for r in rows:
                if r.get("base_" + s) is not None:
                    per[(r["prompt"], r["position"], r["stratum"])].append(
                        (r["base_" + s], r["aligned_" + s]
                         if r.get("aligned_" + s) is not None else None))
            lvl = {k: st.mean(x[0] for x in v) for k, v in per.items()}
            strata = sorted({k[2] for k in lvl})
            if len(strata) > 1:
                #: M03 and slotpov: pair WITHIN stratum, so the unit is the
                #: stratum-level contrast and the site is still held fixed
                gaps = []
                for stx in strata:
                    a = [v for k, v in lvl.items() if k[2] == stx and k[1] == "inst"]
                    b = [v for k, v in lvl.items() if k[2] == stx and k[1] == "indiv"]
                    if a and b:
                        gaps.append(st.mean(a) - st.mean(b))
                if len(gaps) < 5:
                    out.append((s, len(gaps), st.mean(gaps) if gaps else float("nan"),
                                float("nan"), "n<5"))
                    continue
                pv = stats.wilcoxon(gaps).pvalue
                out.append((s, len(gaps), st.median(gaps), pv,
                            "%d/%d" % (sum(1 for g in gaps if g > 0), len(gaps))))
            else:
                a = [v for k, v in lvl.items() if k[1] == "inst"]
                b = [v for k, v in lvl.items() if k[1] == "indiv"]
                if len(a) < 4 or len(b) < 4:
                    continue
                pv = stats.mannwhitneyu(a, b).pvalue
                out.append((s, len(a) + len(b), st.median(a) - st.median(b), pv,
                            "%d v %d" % (len(a), len(b))))
        byscale = {r["scale"]: r for r in res}
        print("   %-14s | %9s %9s | %9s %9s %9s | %s"
              % ("scale", "lin gap", "p (n=%d)" % nlin, "unit gap", "p", "n", "both?"))
        for s, n, gap, pv, note in sorted(out, key=lambda t: t[3]):
            L = byscale[s]
            both = (L["p_base"] < .05) and (pv < .05) and (L["base_gap"] > 0) == (gap > 0)
            print("   %-14s | %+9.3f %9.1e | %+9.3f %9.2g %9s | %s"
                  % (s, L["base_gap"], L["p_base"], gap, pv, note,
                     "BOTH" if both else ("lineage only" if L["p_base"] < .05 else "")))
        summary[c] = dict(n_lineages=nlin, prompt_unit=[
            dict(scale=s, n=n, gap=gap, p=pv, note=note) for s, n, gap, pv, note in out])
    json.dump(summary, open(os.path.join(OUT, "unit_check.json"), "w"), indent=1)
    print("\n-> results/base_side/unit_check.json")


if __name__ == "__main__":
    main()
