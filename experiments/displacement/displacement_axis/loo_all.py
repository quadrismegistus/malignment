"""All three instruments through leave-one-out, on identical words.

    python experiments/displacement_axis/loo_all.py

`loo.py` ran v6 alone and found the named scales recover about 43% of what a
word's own empirical history recovers (67% with base probability). RH's question:
did that include the sexual and institutional norms? It did not. The sexual set
was only ever scored under the broken half-split protocol, where everything read
as negative, and the institutional set has never been through this at all.

WHAT EXISTS.

  v6            12 scales, every pilot3 frame
  inst v3       13 scales, 186 frames (identity 72, institutional 62,
                violence 52), stored in two arms that are DIFFERENT WORD SETS
                with the same scales, merged here by union
  sexual v2      9 scales, 14 frames

So there are two nested comparisons, not one, and they must be reported apart:
a wide one over the 186 v6+inst frames, and a narrow one over the 14 frames that
carry all three.

THE RULE THAT MATTERS. Within each comparison every model sees the SAME WORDS --
the intersection of the sets being compared -- and the same folds. Scoring 12
scales over their words against 13 over theirs is the error that has already cost
this campaign three false comparisons in one day.

MORE SCALES IS NOT FREE. v6+inst is 25 columns on a median 68 words. Ridge
absorbs some of that, but a combined set losing to its parts is evidence about
parameters, not about meaning, so `emp_mean` stays in every table as the
reachable benchmark and the parts are always reported beside the whole.
"""

import argparse, collections, glob, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
#: The root, found by walking up from `malignment` itself, so this file does
#: not encode how deep under `experiments/` it sits. A wrong root makes the
#: globs below return [] instead of raising; `repo_root` refuses instead.
from malignment.paths import REPO
sys.path.insert(0, REPO); sys.path.insert(0, HERE)
RES = os.path.join(HERE, "results", "pilot3")
SR = os.path.join(REPO, "experiments", "slot_ratings")

S2 = ["orality", "tactility", "genitality", "incorporation", "body_distance",
      "exposure", "charge", "euphemism", "explicitness"]


def load_inst():
    """prompt -> word -> {scale: value}, unioned over the two arms.

    The arms hold different word populations with the same instrument, so union
    is the right merge. Where a word appears in both, arm A wins; they agreed on
    every scale in the frames spot-checked, and a disagreement would be a rating
    instability worth finding rather than averaging away.
    """
    out = collections.defaultdict(dict)
    scales = set()
    for f in sorted(glob.glob(os.path.join(
            SR, "institutional", "results", "slotdomain", "*_v3_arm*.json"))):
        for fr in json.load(open(f))["frames"]:
            p = fr.get("prompt")
            r = fr.get("ratings") or {}
            if not p or not isinstance(r, dict):
                continue
            for w, d in r.items():
                if not isinstance(d, dict):
                    continue
                if w not in out[p]:
                    out[p][w] = {k: float(v) for k, v in d.items()
                                 if isinstance(v, (int, float))}
                    scales |= set(out[p][w])
    return out, sorted(scales)


def load_sex():
    out = collections.defaultdict(dict)
    path = os.path.join(SR, "sexual", "results", "rated_gender_pairs_v2.json")
    for r in json.load(open(path))["rows"]:
        if r.get("ratable") is False:
            continue
        if all(isinstance(r.get(s), (int, float)) for s in S2):
            out[r["prompt"]][r["word"]] = {s: float(r[s]) for s in S2}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-lineages", type=int, default=10)
    ap.add_argument("--min-words", type=int, default=30)
    a = ap.parse_args(argv)
    import numpy as np
    from scipy import stats
    from malignment import slot_axis as SA
    from axis_variants import ratings

    v6, _ = ratings()
    S6 = sorted({s for p in v6.values() for w in p.values() for s in w})
    inst, SI = load_inst()
    sex = load_sex()
    print("instruments: v6 %d scales / %d frames | inst %d scales / %d frames "
          "| sexual %d scales / %d frames\n"
          % (len(S6), len(v6), len(SI), len(inst), len(S2), len(sex)))

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

    def fitpred(X, y, Xt):
        Xd = np.c_[np.ones(len(X)), X]
        lam = 1e-3 * np.trace(Xd.T @ Xd) / Xd.shape[1]
        b = np.linalg.solve(Xd.T @ Xd + lam * np.eye(Xd.shape[1]), Xd.T @ y)
        return np.c_[np.ones(len(Xt)), Xt] @ b

    import dedupe
    KEEP = dedupe.report(prompt_of, dedupe.keep(prompt_of))

    def run(need, label):
        """LOO over frames carrying every instrument in `need`, identical words."""
        rows = []
        for item, lins in dp.items():
            if item not in KEEP:
                continue
            p = prompt_of.get(item)
            if not p or len(lins) < a.min_lineages:
                continue
            src = {"v6": v6.get(p), "inst": inst.get(p), "sex": sex.get(p)}
            if any(not src[k] for k in need):
                continue
            SC = {"v6": S6, "inst": SI, "sex": S2}
            ok = []
            for w in sorted({w for l in lins for w in lins[l]}):
                if all(w in src[k] and all(s in src[k][w] for s in SC[k])
                       for k in need):
                    ok.append(w)
            if len(ok) < a.min_words:
                continue
            ix = {w: i for i, w in enumerate(ok)}
            L = sorted(lins)
            V = np.full((len(L), len(ok)), np.nan)
            B = np.full((len(L), len(ok)), np.nan)
            for r_, l in enumerate(L):
                for w, d_ in lins[l].items():
                    if w in ix:
                        V[r_, ix[w]] = 1 if d_ > 0 else (-1 if d_ < 0 else 0)
                        B[r_, ix[w]] = pb[item][l][w]
            X = {k: np.array([[src[k][w][s] for s in SC[k]] for w in ok], float)
                 for k in need}
            blocks = {k: X[k] for k in need}
            allnamed = np.concatenate([X[k] for k in need], 1)
            if len(need) > 1:
                blocks["+".join(need)] = allnamed
            #: the embedding, on THESE words, at two sizes: its own default and
            #: one matched to the named column count, so a win cannot be a win on
            #: free parameters alone
            try:
                E = SA.embed_cached(p, ok)
            except Exception:
                E = None
            if E is not None:
                Ec = E - E.mean(0)
                U = np.linalg.svd(Ec, full_matrices=False)[2]
                npc = allnamed.shape[1]
                blocks["bge_pc10"] = Ec @ U[:10].T
                blocks["bge_pc%d" % npc] = Ec @ U[:npc].T
                blocks["named+bge"] = np.c_[allnamed, Ec @ U[:10].T]

            pred = collections.defaultdict(list); actual = []
            for i in range(len(L)):
                tr = [j for j in range(len(L)) if j != i]
                with np.errstate(invalid="ignore"):
                    ytr = np.nanmean(V[tr], 0)
                    lp = np.log10(np.nanmean(B[tr], 0))
                good = np.where(np.isfinite(ytr))[0]
                keep = np.array([k for k in np.where(np.isfinite(V[i]))[0]
                                 if k in set(good.tolist())])
                if len(keep) < 8 or len(good) < 10 or np.nanstd(ytr[good]) == 0:
                    continue
                yb = V[i, keep]
                if yb.std() == 0:
                    continue
                fin = np.isfinite(lp)
                lp = np.where(fin, lp, np.nanmedian(lp[fin]) if fin.any() else 0.0)
                lp = lp.reshape(-1, 1)
                actual.append(yb)
                pred["emp_mean"].append(ytr[keep])
                for nm, M in blocks.items():
                    pred[nm].append(fitpred(M[good], ytr[good], M[keep]))
                    pred[nm + "+p"].append(
                        fitpred(np.c_[M, lp][good], ytr[good], np.c_[M, lp][keep]))
            if len(actual) < 5:
                continue
            y = np.concatenate(actual)
            tot = ((y - y.mean()) ** 2).sum()
            if tot <= 0:
                continue
            r = dict(prompt=p, domain=domain_of.get(item), n_words=len(ok),
                     n_lineages=len(L), n_folds=len(actual))
            for nm, v in pred.items():
                if len(v) == len(actual):
                    r["r2_" + nm] = float(
                        1 - ((y - np.concatenate(v)) ** 2).sum() / tot)
            rows.append(r)
        if not rows:
            print("%s: no qualifying frames\n" % label); return rows
        names = ["emp_mean"] + [k for k in rows[0] if k.startswith("r2_")]
        names = ["emp_mean"] + sorted(
            {k[3:] for r in rows for k in r if k.startswith("r2_")} - {"emp_mean"},
            key=lambda s: (s.count("+"), len(s)))
        base = float(np.median([r["r2_emp_mean"] for r in rows]))
        print("%s  --  %d frames, median %d words, %d lineages"
              % (label, len(rows), int(np.median([r["n_words"] for r in rows])),
                 int(np.median([r["n_lineages"] for r in rows]))))
        print("  %-18s %10s %10s %11s   %s"
              % ("model", "median R2", "% of bench", "frames > 0", "vs emp_mean"))
        for nm in names:
            v = [r["r2_" + nm] for r in rows if "r2_" + nm in r]
            if len(v) < 3:
                continue
            extra = ""
            if nm != "emp_mean":
                d = [r["r2_" + nm] - r["r2_emp_mean"] for r in rows
                     if "r2_" + nm in r and "r2_emp_mean" in r]
                extra = "%+.4f  wins %d/%d  p=%.2g" % (
                    float(np.median(d)), sum(1 for x in d if x > 0), len(d),
                    stats.wilcoxon(d).pvalue if len(d) >= 6 else float("nan"))
            print("  %-18s %10.4f %9.0f%% %8d/%-4d   %s"
                  % (nm, float(np.median(v)), 100 * float(np.median(v)) / base
                     if base else float("nan"),
                     sum(1 for x in v if x > 0), len(v), extra))
        doms = collections.defaultdict(list)
        for r in rows:
            doms[r["domain"] or "?"].append(r)
        if len(doms) > 1:
            print("\n  by domain")
            cols = [n for n in names if "+p" not in n]
            print("    %-14s %5s" % ("domain", "n")
                  + "".join("%12s" % c[:11] for c in cols))
            for d in sorted(doms, key=lambda d: -len(doms[d])):
                F = doms[d]
                if len(F) < 5:
                    continue
                print("    %-14s %5d" % (d, len(F)) + "".join(
                    "%12.4f" % float(np.median([f["r2_" + c] for f in F
                                                if "r2_" + c in f]))
                    if len([f for f in F if "r2_" + c in f]) >= 3 else "%12s" % "--"
                    for c in cols))
        print()
        return rows

    out = {}
    out["v6_inst"] = run(["v6", "inst"], "V6 + INSTITUTIONAL")
    out["all3"] = run(["v6", "inst", "sex"], "V6 + INSTITUTIONAL + SEXUAL")
    out["v6_sex"] = run(["v6", "sex"], "V6 + SEXUAL")
    json.dump(dict(_what="leave-one-lineage-out with the three instruments, "
                         "identical words within each comparison", **out),
              open(os.path.join(RES, "loo_all.json"), "w"), indent=1)
    print("-> results/pilot3/loo_all.json")


if __name__ == "__main__":
    main()
