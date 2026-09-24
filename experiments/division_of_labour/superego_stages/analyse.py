"""The registered analysis (README.md, 47f22c0a). -> results/superego_stages.md, results/per_model.csv

    python -u analyse.py

Per model: SUPEREGO_IN_SCENE given sexual_scene, pass A -- the share of pass-A
passages coded sexual_scene YES that carry a superego tag (Y's composite, stored
on every row). Y's base and aligned rows come from Y's store (re-used: the drift
gate passed 40/40); the new rungs and llama-7b/beaver from `code_ss.py`'s output.

Per ladder, exactly as declared:

    step1 = first rung - base              (SFT; chat SFT for Amber)
    step2 = second rung - first rung        (DPO / preference / safety)
    step3 = RLVR - DPO                      (OLMo ladders only)
    total = second rung - base;  SFT share = step1 / total where total > 0

Readings fixed in the registration: Wilcoxon signed-rank and sign test over the
10 ladders on step1 and on step2; the median SFT share with a bootstrap interval
over ladders; the verdict rule; per-ladder readings on AmberSafe, OLMo-2-1B,
CT-LLM and pythia-6.9b-hh with per-model SEs; RLVR descriptive.

SANITY CHECK FIRST: Y's own headline (SUPEREGO_IN_SCENE given sexual_scene
15.18 -> 21.60) is recomputed from Y's store with this file's per-model rule
and printed beside the result, so a wrong reading of the store cannot pass as a
finding.
"""
import collections, json, math, os, random, statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
Y = os.path.expanduser("~/malignment-data/y_diegetic/y_confirmatory_coded.jsonl")
SS = os.path.expanduser("~/malignment-data/superego_stages/coded.jsonl")
BOOT, SEED = 10000, 20260924

#: (ladder, [rungs in order: base, first rung, second rung], RLVR or None, step labels)
LADDERS = [
    ("pythia-2.8b", ["EleutherAI/pythia-2.8b", "ContextualAI/archangel_sft_pythia2-8b", "ContextualAI/archangel_sft-dpo_pythia2-8b"], None, "SFT, DPO"),
    ("pythia-6.9b", ["EleutherAI/pythia-6.9b", "lomahony/eleuther-pythia6.9b-hh-sft", "lomahony/eleuther-pythia6.9b-hh-dpo"], None, "SFT, DPO"),
    ("Amber", ["LLM360/Amber", "LLM360/AmberChat", "LLM360/AmberSafe"], None, "chat SFT, safety SFT"),
    ("OLMo-2-1B", ["allenai/OLMo-2-0425-1B", "allenai/OLMo-2-0425-1B-SFT", "allenai/OLMo-2-0425-1B-DPO"], "allenai/OLMo-2-0425-1B-Instruct", "SFT, DPO, RLVR"),
    ("OLMoE", ["allenai/OLMoE-1B-7B-0125", "allenai/OLMoE-1B-7B-0125-SFT", "allenai/OLMoE-1B-7B-0125-DPO"], "allenai/OLMoE-1B-7B-0125-Instruct", "SFT, DPO, RLVR"),
    ("Olmo-3-7B", ["allenai/Olmo-3-1025-7B", "allenai/Olmo-3-7B-Instruct-SFT", "allenai/Olmo-3-7B-Instruct-DPO"], "allenai/Olmo-3-7B-Instruct", "SFT, DPO, RLVR"),
    ("CT-LLM", ["m-a-p/CT-LLM-Base", "m-a-p/CT-LLM-SFT", "m-a-p/CT-LLM-SFT-DPO"], None, "SFT, DPO"),
    ("neo", ["m-a-p/neo_7b", "m-a-p/neo_7b_sft_v0.1", "m-a-p/neo_7b_instruct_v0.1"], None, "SFT, preference"),
    ("Tulu", ["meta-llama/Llama-3.1-8B", "allenai/Llama-3.1-Tulu-3-8B-SFT", "allenai/Llama-3.1-Tulu-3-8B-DPO"], None, "SFT, DPO"),
    ("beaver", ["huggyllama/llama-7b", "PKU-Alignment/alpaca-7b-reproduced", "PKU-Alignment/beaver-7b-v1.0"], None, "SFT, safe-RLHF"),
]
READ = {"Amber", "OLMo-2-1B", "CT-LLM", "pythia-6.9b"}


def rows():
    out = collections.defaultdict(list)
    for path, src in ((Y, "Y"), (SS, "superego_stages")):
        for line in open(path):
            r = json.loads(line)
            if r.get("pass") != "A" or not r.get("parsed"):
                continue
            out[r["model"]].append((r.get("sexual_scene") == "YES", bool(r.get("SUPEREGO_IN_SCENE")), src))
    return out


def rate(rs):
    """(rate in points, SE in points, n scenes, n passages, source)."""
    sc = [s for sex, s, _ in rs if sex]
    if not sc:
        return None
    p = sum(sc) / len(sc)
    return 100 * p, 100 * math.sqrt(p * (1 - p) / len(sc)), len(sc), len(rs), rs[0][2]


def sign_p(k, n):
    from scipy.stats import binomtest
    return binomtest(k, n).pvalue if n else float("nan")


def wilcoxon(v):
    from scipy.stats import wilcoxon as W
    v = [x for x in v if x != 0]
    return W(v).pvalue if len(v) >= 2 else float("nan")


def main():
    R = rows()
    rate_of = {m: rate(v) for m, v in R.items()}
    #: SANITY: Y's headline from Y's store with this file's rule.
    yrows = [json.loads(l) for l in open(Y)]
    pairs = collections.defaultdict(dict)
    for r in yrows:
        if r.get("pass") == "A" and r.get("parsed"):
            pairs[r["pair"]].setdefault(r["role"], r["model"])
    yb = [rate_of[p["base"]][0] for p in pairs.values() if "base" in p and "aligned" in p and rate_of.get(p["base"]) and rate_of.get(p["aligned"])]
    ya = [rate_of[p["aligned"]][0] for p in pairs.values() if "base" in p and "aligned" in p and rate_of.get(p["base"]) and rate_of.get(p["aligned"])]
    L = ["# superego_stages: which stage installs the in-scene superego?", "",
         "Producer `analyse.py`, the analysis registered in README.md (47f22c0a) before any new rung was generated. "
         "Measure: SUPEREGO_IN_SCENE given sexual_scene, pass A, in points.", "",
         "**Sanity check against Y's headline** (15.18 -> 21.60): this file's per-model rule on Y's store gives "
         "mean %.2f -> %.2f over %d pairs." % (st.mean(yb), st.mean(ya), len(yb)), ""]
    missing = [m for _l, rungs, rl, _s in LADDERS for m in rungs + ([rl] if rl else []) if not rate_of.get(m)]
    if missing:
        raise SystemExit("REFUSED, no coded scenes for %s" % missing)
    L += ["## Per model", "", "| ladder | rung | model | superego given scene | SE | scenes | passages | source |", "|---|---|---|---|---|---|---|---|"]
    csv = ["ladder,rung,model,rate,se,scenes,passages,source"]
    lad = []
    for name, rungs, rl, steps in LADDERS:
        tags = ["base", "rung 1", "rung 2"] + (["RLVR"] if rl else [])
        for tag, m in zip(tags, rungs + ([rl] if rl else [])):
            r, se, ns, n, src = rate_of[m]
            L.append("| %s | %s | `%s` | %.1f | %.1f | %d | %d | %s |" % (name, tag, m, r, se, ns, n, src))
            csv.append("%s,%s,%s,%.3f,%.3f,%d,%d,%s" % (name, tag, m, r, se, ns, n, src))
        b, s1, s2 = (rate_of[m][0] for m in rungs)
        e = [rate_of[m][1] for m in rungs]
        lad.append(dict(name=name, steps=steps, base=b, r1=s1, r2=s2, step1=s1 - b, step2=s2 - s1, total=s2 - b,
                        se1=math.hypot(e[0], e[1]), se2=math.hypot(e[1], e[2]), setot=math.hypot(e[0], e[2]),
                        step3=(rate_of[rl][0] - s2) if rl else None, se3=math.hypot(e[2], rate_of[rl][1]) if rl else None))
    L += ["", "## Per ladder", "", "| ladder | steps | base | rung 1 | rung 2 | step1 | step2 | total | SFT share | step3 (RLVR) |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for d in lad:
        d["share"] = d["step1"] / d["total"] if d["total"] > 0 else None
        L.append("| %s | %s | %.1f | %.1f | %.1f | %+.1f | %+.1f | %+.1f | %s | %s |" % (
            d["name"], d["steps"], d["base"], d["r1"], d["r2"], d["step1"], d["step2"], d["total"],
            "%.2f" % d["share"] if d["share"] is not None else "-- (total <= 0)",
            "%+.1f (SE %.1f)" % (d["step3"], d["se3"]) if d["step3"] is not None else ""))
    s1 = [d["step1"] for d in lad]
    s2 = [d["step2"] for d in lad]
    sh = [d["share"] for d in lad if d["share"] is not None]
    rng = random.Random(SEED)
    boots = []
    for _ in range(BOOT):
        smp = [rng.choice(sh) for _ in sh]
        boots.append(st.median(smp))
    boots.sort()
    lo, hi = boots[int(0.025 * BOOT)], boots[int(0.975 * BOOT) - 1]
    k1, n1 = sum(x > 0 for x in s1), sum(x != 0 for x in s1)
    k2, n2 = sum(x > 0 for x in s2), sum(x != 0 for x in s2)
    p1w, p2w = wilcoxon(s1), wilcoxon(s2)
    L += ["", "## The registered readings", "",
          "- **SFT step (step1 > 0):** %d of %d ladders positive, median %+.1f, mean %+.1f; Wilcoxon p = %.3g, sign p = %.3g."
          % (k1, n1, st.median(s1), st.mean(s1), p1w, sign_p(k1, n1)),
          "- **Second step (step2 > 0):** %d of %d positive, median %+.1f, mean %+.1f; Wilcoxon p = %.3g, sign p = %.3g."
          % (k2, n2, st.median(s2), st.mean(s2), p2w, sign_p(k2, n2)),
          "- **SFT share** over the %d ladders with total > 0: median %.2f, bootstrap 95%% interval [%.2f, %.2f] (%d resamples of ladders, seed %d)."
          % (len(sh), st.median(sh), lo, hi, BOOT, SEED)]
    one = p1w < 0.05 and k1 > n1 / 2
    two = p2w < 0.05 and k2 > n2 / 2
    if one and st.median(sh) >= 0.5:
        verdict = "**SFT installs it**: step1 is significant and the median SFT share is >= 0.5."
    elif two and st.median(sh) < 0.5:
        verdict = "**The later stage installs it**: step2 is significant and the median SFT share is < 0.5."
    else:
        verdict = ("**Neither condition of the verdict rule is met**; reported as the interval: median SFT share %.2f [%.2f, %.2f]."
                   % (st.median(sh), lo, hi))
    L += ["- **Verdict (rule fixed in the registration):** " + verdict, "",
          "## Per-ladder readings (declared: Amber, OLMo-2-1B, CT-LLM, pythia-6.9b-hh)", "",
          "| ladder | step1 (SE) | step2 (SE) | total (SE) |", "|---|---|---|---|"]
    for d in lad:
        if d["name"] in READ:
            L.append("| %s | %+.1f (%.1f) | %+.1f (%.1f) | %+.1f (%.1f) |" % (d["name"], d["step1"], d["se1"], d["step2"], d["se2"], d["total"], d["setot"]))
    L += ["", "Amber's split is chat SFT (AmberChat) against safety SFT (AmberSafe), as declared.", "",
          "## RLVR (step3), descriptive, three OLMo ladders", ""]
    L += ["- %s: %+.1f (SE %.1f)" % (d["name"], d["step3"], d["se3"]) for d in lad if d["step3"] is not None]
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    open(os.path.join(HERE, "results", "superego_stages.md"), "w").write("\n".join(L) + "\n")
    open(os.path.join(HERE, "results", "per_model.csv"), "w").write("\n".join(csv) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
