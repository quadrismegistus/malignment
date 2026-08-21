"""SUPERSEDED 2026-08-20. Use `loo.py` / `loo_all.py`. Kept for the record.

WHY IT IS WRONG, not merely improved on. Models here are fit on half A and scored
on half B, while the "ceiling" is `np.polyfit(ya, yb, 1)` -- a slope fitted USING
yb, the target. Two different rules under one label. `protocol_check.py`
regenerates the consequence: a PERFECT predictor of half A, scored by the models'
own rule, earns -0.018, not the +0.264 printed here as the ceiling. With the
eight fitting lineages every split actually had, perfection earns -0.071.

So the band every model occupied, -0.09 to +0.08, was at or above flawless, and
the conclusions drawn from it -- "sexual is unexplained", "every model explains
something in identity and nothing anywhere else", a purpose-built sexual
instrument tying the wrong one at p=0.97 -- were artifacts of the benchmark. Under
leave-one-out all of them reverse.

The `% ceiling` column is REMOVED rather than caveated: it divided by a number no
model could reach, and a caveated ratio still gets read as a ratio. Frames here
are also NOT deduplicated -- 24 prompts carry three item_ids each -- so its counts
and p-values over-state n in `identity` by about 1.8x. See `dedupe.py`.

The original docstring follows.

The same decomposition over MANY random lineage splits, not one.

    python experiments/displacement_axis/variance_repeated.py --splits 20

`variance_decomp.py` splits each frame's lineages once, odd against even. That is
one arbitrary partition of 16 to 25 lineages, and every number it reports carries
whatever that particular draw happened to do. RH's question: do it repeatedly.

Two things this buys that one split cannot:

  a STABLE ESTIMATE   averaging R2 over K random half-splits removes the
                      split-to-split noise from the point estimate
  A SCALE FOR THE     the spread of a model's R2 ACROSS splits of the same frame
  DIFFERENCES         says whether the gap between two models is larger than the
                      noise in measuring either. If `best single` beats `all 12`
                      by 0.015 and either varies by 0.06 across splits, the
                      comparison was never resolvable at one split.

The ceiling -- half A's net movement predicting half B's -- is recomputed per
split for the same reason.

Splits are balanced (equal halves, or off by one for odd counts) and drawn
without replacement from that frame's lineages.
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
    ap.add_argument("--splits", type=int, default=20)
    ap.add_argument("--wide", action="store_true")
    ap.add_argument("--seed", type=int, default=20260820)
    a = ap.parse_args(argv)
    import numpy as np, random, yaml
    from malignment import slot_axis as SA
    from axis_variants import ratings
    poles = {}
    for f in glob.glob(os.path.join(REPO, "roster", "prompts", "slots", "*.yaml")):
        for it in (yaml.safe_load(open(f, encoding="utf-8")) or []):
            if isinstance(it, dict) and it.get("prompt") and it.get("naughty"):
                poles[it["prompt"]] = (list(it["naughty"]), list(it["nice"]))
    v6, _ = ratings(wide=a.wide)
    S6 = sorted({s for p in v6.values() for w in p.values() for s in w})
    cells = collections.defaultdict(lambda: collections.defaultdict(dict))
    for line in open(os.path.join(RES, "words.jsonl")):
        d = json.loads(line)
        cells[d["item_id"]][d["base"] + " -> " + d["endpoint"]][d["word"]] = d["dP"]
    _cl = [json.loads(l) for l in open(os.path.join(RES, "cells.jsonl"))]
    prompt_of = {c["item_id"]: c["prompt"] for c in _cl}
    domain_of = {c["item_id"]: c.get("domain") for c in _cl}

    def r2(X, ya, yb):
        Xd = np.c_[np.ones(len(X)), X]
        lam = 1e-3 * np.trace(Xd.T @ Xd) / Xd.shape[1]
        b = np.linalg.solve(Xd.T @ Xd + lam * np.eye(Xd.shape[1]), Xd.T @ ya)
        pr = Xd @ b
        tot = ((yb - yb.mean()) ** 2).sum()
        return 1 - ((yb - pr) ** 2).sum() / tot if tot > 0 else np.nan

    rng = random.Random(a.seed)
    MODELS = ["bge_axis", "bge_pcs", "best_single", "named_all",
              "named_plus_axis", "named_plus_pcs", "ceiling"]
    rows = []
    for item, lins in cells.items():
        p = prompt_of.get(item)
        if not p or p not in v6 or p not in poles or len(lins) < 8:
            continue
        L = sorted(lins)
        allw = sorted({w for l in L for w in lins[l]})
        ok = [w for w in allw if w in v6[p] and all(s in v6[p][w] for s in S6)]
        if len(ok) < 40:
            continue
        try:
            E = SA.embed_cached(p, ok)
        except Exception:
            continue
        idx = {w: i for i, w in enumerate(ok)}
        nau, nic = poles[p]
        P1 = [E[idx[w]] for w in nau if w in idx]
        P2 = [E[idx[w]] for w in nic if w in idx]
        if len(P1) < 2 or len(P2) < 2:
            continue
        u = np.mean(P1, 0) - np.mean(P2, 0)
        u = u / (np.linalg.norm(u) or 1)
        ax = (E @ u).reshape(-1, 1)
        Ec = E - E.mean(0)
        PC = Ec @ np.linalg.svd(Ec, full_matrices=False)[2][:10].T
        R = np.array([[v6[p][w][s] for s in S6] for w in ok], float)

        per = collections.defaultdict(list)
        for _ in range(a.splits):
            sh = list(L)
            rng.shuffle(sh)
            h = len(sh) // 2
            A, B = sh[:h], sh[h:]
            def net(sub):
                n = collections.Counter()
                for l in sub:
                    for w, dp in lins[l].items():
                        n[w] += 1 if dp > 0 else (-1 if dp < 0 else 0)
                return n
            na, nb = net(A), net(B)
            ya = np.array([na[w] for w in ok], float)
            yb = np.array([nb[w] for w in ok], float)
            if ya.std() == 0 or yb.std() == 0:
                continue
            per["bge_axis"].append(r2(ax, ya, yb))
            per["bge_pcs"].append(r2(PC, ya, yb))
            per["named_all"].append(r2(R, ya, yb))
            per["named_plus_axis"].append(r2(np.c_[R, ax], ya, yb))
            per["named_plus_pcs"].append(r2(np.c_[R, PC], ya, yb))
            singles = [r2(R[:, [i]], ya, yb) for i in range(R.shape[1])]
            bi = int(np.nanargmax(singles))
            per["best_single"].append(singles[bi])
            #: WHICH name won, per split. Recorded so the winner can be reported
            #: per frame and per domain, and so a name that wins on one split and
            #: not the next is visible as unstable rather than quoted as the name.
            per.setdefault("_names", []).append(S6[bi])
            b = np.polyfit(ya, yb, 1)
            pr = np.polyval(b, ya)
            per["ceiling"].append(1 - ((yb - pr) ** 2).sum() / ((yb - yb.mean()) ** 2).sum())
        if len(per["ceiling"]) < a.splits // 2:
            continue
        names = collections.Counter(per.get("_names", []))
        r = dict(item=item, prompt=p, domain=domain_of.get(item),
                 n_words=len(ok), n_lineages=len(L), n_splits=len(per["ceiling"]),
                 best_name=(names.most_common(1)[0][0] if names else None),
                 best_name_share=(names.most_common(1)[0][1] / sum(names.values())
                                  if names else None))
        for m in MODELS:
            v = [x for x in per[m] if x == x]
            if v:
                r["mean_" + m] = float(np.mean(v))
                r["sd_" + m] = float(np.std(v))
        rows.append(r)

    print("frames: %d | %d random splits each | median lineages %d, words %d\n"
          % (len(rows), a.splits, int(np.median([r["n_lineages"] for r in rows])),
             int(np.median([r["n_words"] for r in rows]))))
    ceil = float(np.median([r["mean_ceiling"] for r in rows if "mean_ceiling" in r]))
    print("NOT-A-CEILING (slope fitted on the target; unreachable by any model "
          "here): %.3f" % ceil)
    print("  its SPREAD across splits of one frame: median sd %.3f\n"
          % float(np.median([r["sd_ceiling"] for r in rows if "sd_ceiling" in r])))
    print("  %-22s %9s %9s %11s"
          % ("model", "mean R2", "sd/split", "one-split R2"))
    ONE = {"bge_axis": -0.009, "bge_pcs": 0.023, "best_single": 0.049,
           "named_all": 0.034, "named_plus_axis": 0.051, "named_plus_pcs": 0.101}
    for m in MODELS[:-1]:
        v = [r["mean_" + m] for r in rows if "mean_" + m in r]
        sd = [r["sd_" + m] for r in rows if "sd_" + m in r]
        #: the "% of ceiling" column that stood here is gone: it divided by a
        #: quantity scored under a different rule. See this file's header.
        print("  %-22s %9.3f %9.3f %11.3f"
              % (m, float(np.median(v)), float(np.median(sd)),
                 ONE.get(m, float("nan"))))
    print("\nIS THE GAP BIGGER THAN THE SPLIT NOISE?")
    for x, y in (("best_single", "named_all"), ("named_plus_pcs", "named_all"),
                 ("named_plus_pcs", "bge_pcs"), ("bge_pcs", "bge_axis")):
        d = [r["mean_" + x] - r["mean_" + y] for r in rows
             if "mean_" + x in r and "mean_" + y in r]
        noise = float(np.median([r["sd_" + x] for r in rows if "sd_" + x in r]))
        from scipy import stats
        w = stats.wilcoxon(d)
        print("   %-16s - %-16s  %+.3f   split sd %.3f   %s wins %d/%d  p=%.2g"
              % (x, y, float(np.median(d)), noise, x,
                 sum(1 for z in d if z > 0), len(d), w.pvalue))
    json.dump(dict(_what="held-out R2 averaged over %d random lineage splits per "
                         "frame, with the across-split sd" % a.splits, rows=rows),
              open(os.path.join(RES, "variance_repeated.json"), "w"))
    print("\n-> results/pilot3/variance_repeated.json")


if __name__ == "__main__":
    main()
