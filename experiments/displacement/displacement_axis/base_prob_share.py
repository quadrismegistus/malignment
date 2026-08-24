"""Is the variance our axes miss even semantic? Or is it where the word started?

    python experiments/displacement_axis/base_prob_share.py --splits 40

THE SUSPICION. Twelve named scales, a 1024-dim embedding, a purpose-built sexual
instrument and a single column all fail at held-out R2 by about the same amount
(-0.02 to -0.09) against a ceiling of 0.285. When every candidate predictor fails
EQUALLY, the usual cause is not a missing name. It is that the target encodes
something none of them could carry.

Net movement is a count of +1/-1 verdicts, and how far a word can move is bounded
by where it started: a word at p_base 0.18 has room to fall, a word at 0.001 does
not. So the reliable half-to-half structure may be a probability gradient rather
than a meaning gradient -- arithmetic that no rating scale encodes and no
embedding should be expected to.

THE TEST. One predictor, log10 of the word's mean base probability, estimated ON
THE FITTING HALF ONLY, against the same splits, frames, words and ridge as
everything else. Then whether the twelve names add anything ON TOP of it.

WHAT EACH OUTCOME WOULD MEAN, written down before running so neither can be
narrated into a success:

  logp NEAR THE CEILING   the reliable variance is positional, not semantic. Our
                          axes were competing with arithmetic and the per-word
                          regression was the wrong question all along. Names then
                          belong to DIRECTION, which they already do at 95/95.
  logp NEAR ZERO TOO      the target is just noisy at this resolution and the
                          ceiling is measuring shared sampling error, not shared
                          structure. That would indict the ceiling, not the axes.
  NAMES ADD ON TOP        semantics has an independent share and it was being
                          masked. That is the one result that would rescue the
                          per-word framing.
"""

import argparse, collections, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
#: The root, found by walking up from `malignment` itself, so this file does
#: not encode how deep under `experiments/` it sits. A wrong root makes the
#: globs below return [] instead of raising; `repo_root` refuses instead.
from malignment.paths import REPO
sys.path.insert(0, REPO); sys.path.insert(0, HERE)
#: `--run` selects the run directory; pilot3 stays the default so every
#: command already written against this file keeps meaning what it meant.
RUN = "pilot3"
RES = os.path.join(HERE, "results", RUN)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default=RUN, help="run directory under results/")
    ap.add_argument("--splits", type=int, default=40)
    ap.add_argument("--seed", type=int, default=20260820)
    a = ap.parse_args(argv)
    global RES
    RES = os.path.join(HERE, "results", a.run)
    if not os.path.isdir(RES):
        ap.error("no such run: %s" % RES)
    print("run: %s" % a.run)
    import numpy as np, random
    from scipy import stats
    from axis_variants import ratings

    v6, _ = ratings()
    S6 = sorted({s for p in v6.values() for w in p.values() for s in w})

    #: keep p_base per (word, lineage) so the predictor can be rebuilt from
    #: whichever lineages land in the fitting half
    dp = collections.defaultdict(lambda: collections.defaultdict(dict))
    pb = collections.defaultdict(lambda: collections.defaultdict(dict))
    for line in open(os.path.join(RES, "words.jsonl")):
        d = json.loads(line)
        k = d["base"] + " -> " + d["endpoint"]
        dp[d["item_id"]][k][d["word"]] = d["dP"]
        pb[d["item_id"]][k][d["word"]] = d["p_base"]
    cl = [json.loads(l) for l in open(os.path.join(RES, "cells.jsonl"))]
    prompt_of = {c["item_id"]: c["prompt"] for c in cl}
    domain_of = {c["item_id"]: c.get("domain") for c in cl}

    def r2(X, ya, yb):
        Xd = np.c_[np.ones(len(X)), X]
        lam = 1e-3 * np.trace(Xd.T @ Xd) / Xd.shape[1]
        b = np.linalg.solve(Xd.T @ Xd + lam * np.eye(Xd.shape[1]), Xd.T @ ya)
        pr = Xd @ b
        tot = ((yb - yb.mean()) ** 2).sum()
        return 1 - ((yb - pr) ** 2).sum() / tot if tot > 0 else np.nan

    rng = random.Random(a.seed)
    MODELS = ["ceiling", "logp", "names12", "logp_names", "logp_sq"]
    import dedupe
    KEEP = dedupe.report(prompt_of, dedupe.keep(prompt_of))
    rows = []
    for item, lins in dp.items():
        if item not in KEEP:
            continue
        p = prompt_of.get(item)
        if not p or p not in v6 or len(lins) < 8:
            continue
        L = sorted(lins)
        ok = [w for w in sorted({w for l in L for w in lins[l]})
              if w in v6[p] and all(s in v6[p][w] for s in S6)]
        if len(ok) < 40:
            continue
        R = np.array([[v6[p][w][s] for s in S6] for w in ok], float)
        per = collections.defaultdict(list)
        for _ in range(a.splits):
            sh = list(L); rng.shuffle(sh); h = len(sh) // 2
            A, B = sh[:h], sh[h:]

            def net(sub):
                n = collections.Counter()
                for l in sub:
                    for w, d_ in dp[item][l].items():
                        n[w] += 1 if d_ > 0 else (-1 if d_ < 0 else 0)
                return n
            ya = np.array([net(A)[w] for w in ok], float)
            yb = np.array([net(B)[w] for w in ok], float)
            if ya.std() == 0 or yb.std() == 0:
                continue
            #: the predictor is built from the FITTING half only
            lp = []
            for w in ok:
                v = [pb[item][l][w] for l in A if w in pb[item][l]]
                lp.append(np.log10(np.mean(v)) if v else np.nan)
            lp = np.array(lp, float)
            m = np.nanmean(lp[np.isfinite(lp)]) if np.isfinite(lp).any() else 0.0
            lp = np.where(np.isfinite(lp), lp, m).reshape(-1, 1)
            if lp.std() == 0:
                continue
            per["logp"].append(r2(lp, ya, yb))
            per["logp_sq"].append(r2(np.c_[lp, lp ** 2], ya, yb))
            per["names12"].append(r2(R, ya, yb))
            per["logp_names"].append(r2(np.c_[lp, R], ya, yb))
            b = np.polyfit(ya, yb, 1)
            per["ceiling"].append(1 - ((yb - np.polyval(b, ya)) ** 2).sum()
                                  / ((yb - yb.mean()) ** 2).sum())
            #: how strongly does where it started order how far it moved?
            per["rho_lp"].append(stats.spearmanr(lp.ravel(), yb).statistic)
        if len(per["ceiling"]) < a.splits // 2:
            continue
        r = dict(item=item, prompt=p, domain=domain_of.get(item),
                 n_words=len(ok), n_lineages=len(L))
        for m_ in MODELS + ["rho_lp"]:
            v = [x for x in per[m_] if x == x]
            if v:
                r["mean_" + m_] = float(np.mean(v)); r["sd_" + m_] = float(np.std(v))
        rows.append(r)

    print("%d frames | %d splits | one column: log10 mean p_base on the fit half\n"
          % (len(rows), a.splits))
    ceil = float(np.median([r["mean_ceiling"] for r in rows]))
    print("  %-14s %10s %9s %11s   %s"
          % ("model", "median R2", "sd/split", "%% of ceiling", "frames > 0"))
    for m_ in MODELS:
        v = [r["mean_" + m_] for r in rows if "mean_" + m_ in r]
        sd = [r["sd_" + m_] for r in rows if "sd_" + m_ in r]
        print("  %-14s %10.3f %9.3f %10.0f%%   %d/%d"
              % (m_, float(np.median(v)), float(np.median(sd)),
                 100 * float(np.median(v)) / ceil, sum(1 for x in v if x > 0), len(v)))
    print("\n  rho(log p_base, held-out net movement): %+.3f   %d/%d frames same sign"
          % (float(np.median([r["mean_rho_lp"] for r in rows])),
             max(sum(1 for r in rows if r["mean_rho_lp"] > 0),
                 sum(1 for r in rows if r["mean_rho_lp"] < 0)), len(rows)))

    print("\nDO THE NAMES ADD ANYTHING ON TOP OF WHERE THE WORD STARTED?")
    for x, y in (("logp", "names12"), ("logp_names", "logp"), ("logp_sq", "logp")):
        d = [r["mean_" + x] - r["mean_" + y] for r in rows
             if "mean_" + x in r and "mean_" + y in r]
        print("   %-12s - %-12s %+.3f   %s wins %d/%d   p=%.3g"
              % (x, y, float(np.median(d)), x, sum(1 for z in d if z > 0), len(d),
                 stats.wilcoxon(d).pvalue))

    print("\nBY DOMAIN")
    doms = collections.defaultdict(list)
    for r in rows:
        doms[r["domain"] or "?"].append(r)
    print("  %-14s %6s %8s %8s %9s %10s"
          % ("domain", "n", "ceiling", "logp", "names12", "logp+names"))
    for d in sorted(doms, key=lambda d: -len(doms[d])):
        F = doms[d]
        if len(F) < 5:
            continue
        print("  %-14s %6d %+8.3f %+8.3f %+8.3f %+10.3f"
              % (d, len(F), float(np.median([f["mean_ceiling"] for f in F])),
                 float(np.median([f["mean_logp"] for f in F])),
                 float(np.median([f["mean_names12"] for f in F])),
                 float(np.median([f["mean_logp_names"] for f in F]))))
    json.dump(dict(_what="held-out R2 of log10 base probability against the named "
                         "scales, %d random lineage splits" % a.splits, rows=rows),
              open(os.path.join(RES, "base_prob_share.json"), "w"), indent=1)
    print("\n-> results/%s/base_prob_share.json" % a.run)


if __name__ == "__main__":
    main()
