"""Leave-one-lineage-out, with a benchmark the models are allowed to reach.

    python experiments/displacement_axis/loo.py --scales v6

WHY THE HALF-SPLIT VERSION HAD TO GO. `variance_repeated.py` scored every model
against a "ceiling" of 0.261 computed by fitting the slope ON THE TARGET, a rule
no model was permitted to use. Under the models' own rule a PERFECT predictor of
half A scores -0.017, and with eight fitting lineages -- what every half-split
had -- a perfect predictor scores -0.067. So the wall of small negatives that
made me write "sexual is unexplained" and "nothing anywhere else" was the price
of estimating from ten lineages, not a fact about meaning.

Growing the fitting half, scale-matched, predicting a fixed held-out block:

      lineages to fit    1       2       4       8      12      16
      median R2       -2.548  -1.124  -0.418  -0.067  +0.052  +0.113

Still climbing at 16. Leave-one-out sits as far right on that curve as the data
allows, so it is the design the growth curve argues for.

WHAT LOO FIXES BESIDES SAMPLE SIZE.

  SCALE MATCHES BY CONSTRUCTION. Train on the MEAN net over n-1 lineages; test on
  the held-out lineage. The mean estimates the per-word tendency the held-out
  lineage is a draw from, so predictions and target are on one scale and there is
  no variance mismatch to pay for. The old sum-vs-sum design had none of this.

  THE BENCHMARK IS REACHABLE. The n-1 mean is itself a predictor of the held-out
  lineage -- the best purely empirical one available -- and it is scored by the
  identical rule. A model BEATING it has done something the data alone cannot:
  smoothed the mean's own sampling noise using structure the words share.

WHAT THE NUMBERS WILL LOOK LIKE, said before running so it cannot be narrated
afterwards. A single held-out lineage is a noisy target, so the achievable
maximum is single-lineage reliability, which Spearman-Brown puts near 0.11 from
rho=0.557 at ten lineages. Everything here will be small. `emp_mean` is what
separates small-and-real from failed; 0 is what separates failed from harmful.
"""

import argparse, collections, glob, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
#: The root, found by walking up from `malignment` itself, so this file does
#: not encode how deep under `experiments/` it sits. A wrong root makes the
#: globs below return [] instead of raising; `repo_root` refuses instead.
from malignment.paths import REPO
sys.path.insert(0, REPO); sys.path.insert(0, HERE)
RES = os.path.join(HERE, "results", "pilot3")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-lineages", type=int, default=10)
    ap.add_argument("--min-words", type=int, default=40)
    ap.add_argument("--out", default="loo.json")
    a = ap.parse_args(argv)
    import numpy as np, yaml
    from scipy import stats
    from malignment import slot_axis as SA
    from axis_variants import ratings

    v6, _ = ratings()
    S6 = sorted({s for p in v6.values() for w in p.values() for s in w})
    poles = {}
    for f in glob.glob(os.path.join(REPO, "roster", "prompts", "slots", "*.yaml")):
        for it in (yaml.safe_load(open(f, encoding="utf-8")) or []):
            if isinstance(it, dict) and it.get("prompt") and it.get("naughty"):
                poles[it["prompt"]] = (list(it["naughty"]), list(it["nice"]))

    dp = collections.defaultdict(lambda: collections.defaultdict(dict))
    pbase = collections.defaultdict(lambda: collections.defaultdict(dict))
    for line in open(os.path.join(RES, "words.jsonl")):
        d = json.loads(line)
        k = d["base"] + " -> " + d["endpoint"]
        dp[d["item_id"]][k][d["word"]] = d["dP"]
        pbase[d["item_id"]][k][d["word"]] = d["p_base"]
    cl = [json.loads(l) for l in open(os.path.join(RES, "cells.jsonl"))]
    prompt_of = {c["item_id"]: c["prompt"] for c in cl}
    domain_of = {c["item_id"]: c.get("domain") for c in cl}

    def fitpred(X, y, Xt):
        """Ridge on the training mean, applied to the held-out lineage's rows."""
        Xd = np.c_[np.ones(len(X)), X]
        lam = 1e-3 * np.trace(Xd.T @ Xd) / Xd.shape[1]
        b = np.linalg.solve(Xd.T @ Xd + lam * np.eye(Xd.shape[1]), Xd.T @ y)
        return np.c_[np.ones(len(Xt)), Xt] @ b

    import dedupe
    KEEP = dedupe.report(prompt_of, dedupe.keep(prompt_of))
    ck, bad = dedupe.check(dp, prompt_of)
    print("dedupe: %d copy-pairs checked, %d differ" % (ck, bad))
    rows = []
    for item, lins in dp.items():
        if item not in KEEP:
            continue
        p = prompt_of.get(item)
        if not p or p not in v6 or len(lins) < a.min_lineages:
            continue
        L = sorted(lins)
        ok = [w for w in sorted({w for l in L for w in lins[l]})
              if w in v6[p] and all(s in v6[p][w] for s in S6)]
        if len(ok) < a.min_words:
            continue
        ix = {w: i for i, w in enumerate(ok)}
        V = np.full((len(L), len(ok)), np.nan)
        B = np.full((len(L), len(ok)), np.nan)
        for r_, l in enumerate(L):
            for w, d_ in lins[l].items():
                if w in ix:
                    V[r_, ix[w]] = 1 if d_ > 0 else (-1 if d_ < 0 else 0)
                    B[r_, ix[w]] = pbase[item][l][w]
        R = np.array([[v6[p][w][s] for s in S6] for w in ok], float)
        try:
            E = SA.embed_cached(p, ok)
        except Exception:
            continue
        Ec = E - E.mean(0)
        PC = Ec @ np.linalg.svd(Ec, full_matrices=False)[2][:10].T
        ax = None
        if p in poles:
            P1 = [E[ix[w]] for w in poles[p][0] if w in ix]
            P2 = [E[ix[w]] for w in poles[p][1] if w in ix]
            if len(P1) >= 2 and len(P2) >= 2:
                u = np.mean(P1, 0) - np.mean(P2, 0)
                ax = (E @ (u / (np.linalg.norm(u) or 1))).reshape(-1, 1)

        #: pooled over held-out lineages: every (word, lineage) prediction goes
        #: into one R2, which is the standard LOO-CV quantity and keeps the
        #: target's full variance in the denominator
        pred = collections.defaultdict(list)
        actual = []
        for i in range(len(L)):
            tr = [j for j in range(len(L)) if j != i]
            keep = np.where(np.isfinite(V[i]))[0]
            if len(keep) < 8:
                continue
            with np.errstate(invalid="ignore"):
                ytr = np.nanmean(V[tr], 0)
            good = np.where(np.isfinite(ytr))[0]
            keep = np.array([k for k in keep if k in set(good.tolist())])
            if len(keep) < 8 or np.nanstd(ytr[good]) == 0:
                continue
            yb = V[i, keep]
            if yb.std() == 0:
                continue
            actual.append(yb)
            pred["emp_mean"].append(ytr[keep])
            pred["names12"].append(fitpred(R[good], ytr[good], R[keep]))
            pred["bge_pcs"].append(fitpred(PC[good], ytr[good], PC[keep]))
            if ax is not None:
                pred["bge_axis"].append(fitpred(ax[good], ytr[good], ax[keep]))
            with np.errstate(divide="ignore", invalid="ignore"):
                lp = np.log10(np.nanmean(B[tr], 0))
            lp = np.where(np.isfinite(lp), lp, np.nanmedian(lp[np.isfinite(lp)]))
            lp = lp.reshape(-1, 1)
            pred["logp"].append(fitpred(lp[good], ytr[good], lp[keep]))
            pred["names_logp"].append(
                fitpred(np.c_[R, lp][good], ytr[good], np.c_[R, lp][keep]))
            for j, s in enumerate(S6):
                pred["1:" + s].append(
                    fitpred(R[good][:, [j]], ytr[good], R[keep][:, [j]]))
        if len(actual) < 5:
            continue
        y = np.concatenate(actual)
        tot = ((y - y.mean()) ** 2).sum()
        if tot <= 0:
            continue
        r = dict(item=item, prompt=p, domain=domain_of.get(item),
                 n_words=len(ok), n_lineages=len(L), n_folds=len(actual))
        for m, v in pred.items():
            if len(v) == len(actual):
                r["r2_" + m] = float(1 - ((y - np.concatenate(v)) ** 2).sum() / tot)
        rows.append(r)

    MODELS = ["emp_mean", "names12", "names_logp", "logp", "bge_pcs", "bge_axis"]
    print("LEAVE-ONE-LINEAGE-OUT, pooled over folds")
    print("%d frames | median %d lineages, %d words\n"
          % (len(rows), int(np.median([r["n_lineages"] for r in rows])),
             int(np.median([r["n_words"] for r in rows]))))
    print("  %-14s %10s %11s   %s"
          % ("model", "median R2", "frames > 0", "vs emp_mean (sign test)"))
    for m in MODELS:
        v = [r["r2_" + m] for r in rows if "r2_" + m in r]
        if not v:
            continue
        extra = ""
        if m != "emp_mean":
            d = [r["r2_" + m] - r["r2_emp_mean"] for r in rows
                 if "r2_" + m in r and "r2_emp_mean" in r]
            extra = ("%+.4f  wins %d/%d  p=%.2g"
                     % (float(np.median(d)), sum(1 for x in d if x > 0), len(d),
                        stats.wilcoxon(d).pvalue))
        print("  %-14s %10.4f %8d/%-4d   %s"
              % (m, float(np.median(v)), sum(1 for x in v if x > 0), len(v), extra))

    print("\nSINGLE NAMED SCALES (one column, no selection)")
    sing = []
    for s in S6:
        v = [r["r2_1:" + s] for r in rows if "r2_1:" + s in r]
        if len(v) >= 20:
            sing.append((float(np.median(v)), s, sum(1 for x in v if x > 0), len(v)))
    for m, s, k, n in sorted(sing, reverse=True):
        print("  %-14s %10.4f %8d/%-4d" % (s, m, k, n))

    print("\nBY DOMAIN")
    doms = collections.defaultdict(list)
    for r in rows:
        doms[r["domain"] or "?"].append(r)
    cols = ["emp_mean", "names12", "names_logp", "bge_pcs"]
    print("  %-14s %5s" % ("domain", "n") + "".join("%12s" % c for c in cols)
          + "%14s" % "best 1 scale")
    for d in sorted(doms, key=lambda d: -len(doms[d])):
        F = doms[d]
        if len(F) < 5:
            continue
        best = max(((float(np.median([f["r2_1:" + s] for f in F if "r2_1:" + s in f])), s)
                    for s in S6
                    if len([f for f in F if "r2_1:" + s in f]) >= 5), default=(0, "-"))
        print("  %-14s %5d" % (d, len(F))
              + "".join("%12.4f" % float(np.median([f["r2_" + c] for f in F
                                                    if "r2_" + c in f])) for c in cols)
              + "%14s" % ("%s %.3f" % (best[1][:9], best[0])))
    json.dump(dict(_what="leave-one-lineage-out pooled R2; emp_mean is the n-1 "
                         "mean scored by the same rule and is the reachable "
                         "benchmark", rows=rows),
              open(os.path.join(RES, a.out), "w"), indent=1)
    print("\n-> results/pilot3/%s" % a.out)


if __name__ == "__main__":
    main()
