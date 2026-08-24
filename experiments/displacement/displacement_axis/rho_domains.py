"""The domain comparison again, on an estimator with the power to make it.

    python experiments/displacement_axis/rho_domains.py --splits 40

WHAT THIS REPAIRS. `variance_repeated.py` produced a domain table -- identity
+0.077, institutional -0.007, violence -0.011, sexual -0.007 -- and I reported
"every model explains something in identity and nothing anywhere else". Then the
sexual frames turned out to carry a highly consistent effect (genitality 12/12
frames, p=0.0005) that the same table scored at zero. The table was reading its
own noise.

TWO THINGS WERE WRONG WITH IT, both about power, neither about domains:

  a TOO MANY PARAMETERS. Fitting 12 to 21 columns on 41 to 82 words costs about
    p/n in held-out R2 -- roughly 0.16 -- against a true signal near 0.01. The
    penalty is an order of magnitude larger than the thing being measured, so
    every frame returns a negative number whose size is set by its word count.

  b MEDIAN ACROSS FRAMES ACCUMULATES NOTHING. Twelve noisy near-zero numbers have
    a noisy near-zero median. rho got its p=0.0005 from twelve frames agreeing in
    SIGN, evidence the median throws away.

SO THIS FILE DOES BOTH PROPERLY. Per-scale rho with a sign test across frames,
and per-scale held-out R2 with ONE column at a time. No scale is ever chosen on
the data that scores it: all 12 are reported for every domain, and the reader
picks. `best_single` in the old file took a nanmax over the evaluation split,
which is selection on the test set and biased upward -- that number should not
be quoted, including by me.
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


def load():
    cells = collections.defaultdict(lambda: collections.defaultdict(dict))
    for line in open(os.path.join(RES, "words.jsonl")):
        d = json.loads(line)
        cells[d["item_id"]][d["base"] + " -> " + d["endpoint"]][d["word"]] = d["dP"]
    cl = [json.loads(l) for l in open(os.path.join(RES, "cells.jsonl"))]
    return (cells, {c["item_id"]: c["prompt"] for c in cl},
            {c["item_id"]: c.get("domain") for c in cl})


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default=RUN, help="run directory under results/")
    ap.add_argument("--splits", type=int, default=40)
    ap.add_argument("--seed", type=int, default=20260820)
    ap.add_argument("--min-lineages", type=int, default=8)
    ap.add_argument("--min-words", type=int, default=40)
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
    cells, prompt_of, domain_of = load()
    rng = random.Random(a.seed)

    def rank(v):
        return stats.rankdata(v)

    def corr(x, y):
        x = x - x.mean(); y = y - y.mean()
        d = (np.sqrt((x * x).sum()) * np.sqrt((y * y).sum()))
        return float((x * y).sum() / d) if d > 0 else np.nan

    def r2_1(x, ya, yb):
        #: one predictor plus intercept, ordinary least squares, no shrinkage.
        #: With p=1 the honest out-of-sample penalty is ~1/n, so no ridge is
        #: needed and adding one would make the comparison to the 12-column
        #: version unfair in the other direction.
        X = np.c_[np.ones(len(x)), x]
        b = np.linalg.lstsq(X, ya, rcond=None)[0]
        pr = X @ b
        tot = ((yb - yb.mean()) ** 2).sum()
        return 1 - ((yb - pr) ** 2).sum() / tot if tot > 0 else np.nan

    import dedupe
    KEEP = dedupe.report(prompt_of, dedupe.keep(prompt_of))
    frames = []
    for item, lins in cells.items():
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
        idx = {w: i for i, w in enumerate(ok)}
        R = np.array([[v6[p][w][s] for s in S6] for w in ok], float)
        Rr = np.array([rank(R[:, j]) for j in range(R.shape[1])]).T

        #: --- rho, per lineage, per scale ---
        rhos = collections.defaultdict(list)
        for l in L:
            d = lins[l]
            pres = [idx[w] for w in ok if w in d]
            if len(pres) < 8:
                continue
            y = np.array([1 if d[ok[i]] > 0 else (-1 if d[ok[i]] < 0 else 0)
                          for i in pres], float)
            if y.std() == 0:
                continue
            yr = rank(y)
            for j, s in enumerate(S6):
                xr = Rr[pres, j]
                if xr.std() > 0:
                    rhos[s].append(corr(xr, yr))

        #: --- held-out R2, ONE scale at a time, same splits for every scale ---
        r2s = collections.defaultdict(list)
        ceil = []
        for _ in range(a.splits):
            sh = list(L); rng.shuffle(sh); h = len(sh) // 2
            def net(sub):
                n = collections.Counter()
                for l in sub:
                    for w, dp in lins[l].items():
                        n[w] += 1 if dp > 0 else (-1 if dp < 0 else 0)
                return n
            na, nb = net(sh[:h]), net(sh[h:])
            ya = np.array([na[w] for w in ok], float)
            yb = np.array([nb[w] for w in ok], float)
            if ya.std() == 0 or yb.std() == 0:
                continue
            for j, s in enumerate(S6):
                if R[:, j].std() > 0:
                    r2s[s].append(r2_1(R[:, j], ya, yb))
            b = np.polyfit(ya, yb, 1)
            ceil.append(1 - ((yb - np.polyval(b, ya)) ** 2).sum()
                        / ((yb - yb.mean()) ** 2).sum())
        if not ceil:
            continue
        fr = dict(item=item, prompt=p, domain=domain_of.get(item),
                  n_words=len(ok), n_lineages=len(L),
                  ceiling=float(np.mean(ceil)))
        for s in S6:
            if len(rhos[s]) >= 5:
                fr["rho_" + s] = float(np.median(rhos[s]))
                fr["rhon_" + s] = len(rhos[s])
            v = [x for x in r2s[s] if x == x]
            if v:
                fr["r2_" + s] = float(np.mean(v))
        frames.append(fr)

    doms = collections.defaultdict(list)
    for f in frames:
        doms[f["domain"] or "?"].append(f)
    order = sorted(doms, key=lambda d: -len(doms[d]))

    print("%d frames | %d splits | min %d lineages, %d words | v6 12 scales\n"
          % (len(frames), a.splits, a.min_lineages, a.min_words))
    print("DOMAIN SIZES AND CEILINGS")
    for d in order:
        F = doms[d]
        print("  %-14s %4d frames   median %3d words, %2d lineages   ceiling %.3f"
              % (d, len(F), int(np.median([f["n_words"] for f in F])),
                 int(np.median([f["n_lineages"] for f in F])),
                 float(np.median([f["ceiling"] for f in F]))))

    def signtest(v):
        k = max(sum(1 for x in v if x > 0), sum(1 for x in v if x < 0))
        return k, len(v), stats.binomtest(k, len(v), 0.5).pvalue

    print("\nRHO: does the scale ORDER the movers? (median of per-frame medians;")
    print("     'agree' is how many frames share the majority sign; p is a sign test)")
    for d in order:
        F = doms[d]
        print("\n  %s  (n=%d frames)" % (d.upper(), len(F)))
        rank_ = []
        for s in S6:
            v = [f["rho_" + s] for f in F if "rho_" + s in f]
            if len(v) < 6:
                continue
            k, n, p = signtest(v)
            rank_.append((abs(np.median(v)), s, float(np.median(v)), k, n, p))
        for _, s, m, k, n, p in sorted(rank_, reverse=True)[:6]:
            print("     %-14s %+.3f   agree %3d/%-3d   p=%-9.2g %s"
                  % (s, m, k, n, p, "*" if p < 0.05 / len(S6) else ""))

    print("\nHELD-OUT R2, ONE SCALE AT A TIME (median over frames; frames>0)")
    print("  the same 12 scales, no selection, so these are directly comparable")
    hdr = "  %-14s" + " %8s" * len(order)
    print(hdr % tuple(["scale"] + [d[:8] for d in order]))
    for s in S6:
        cells_ = []
        for d in order:
            v = [f["r2_" + s] for f in doms[d] if "r2_" + s in f]
            cells_.append("%+.3f" % float(np.median(v)) if len(v) >= 6 else "--")
        print(hdr % tuple([s] + cells_))
    print(hdr % tuple(["CEILING"] + ["%+.3f" % float(np.median(
        [f["ceiling"] for f in doms[d]])) for d in order]))
    print("  BEST-OF-12 (median over frames of that frame's best a-priori scale")
    print("  is NOT reported: choosing on the score is selection on the test set.)")

    print("\nDOES THE DOMAIN RANKING SURVIVE? strongest rho per domain, and")
    print("whether the domains differ on it (Kruskal over per-frame values)")
    for d in order:
        F = doms[d]
        best = None
        for s in S6:
            v = [f["rho_" + s] for f in F if "rho_" + s in f]
            if len(v) >= 6:
                k, n, p = signtest(v)
                sc = abs(float(np.median(v)))
                if best is None or sc > best[0]:
                    best = (sc, s, float(np.median(v)), k, n, p)
        if best:
            print("  %-14s %-14s %+.3f   agree %d/%d  p=%.2g"
                  % (d, best[1], best[2], best[3], best[4], best[5]))
    for s in S6:
        groups = [[f["rho_" + s] for f in doms[d] if "rho_" + s in f] for d in order]
        groups = [g for g in groups if len(g) >= 6]
        if len(groups) >= 3:
            p = stats.kruskal(*groups).pvalue
            if p < 0.05:
                print("   domains DIFFER on %-14s p=%.3g   (%s)"
                      % (s, p, "  ".join("%s %+.3f" % (d[:6], float(np.median(g)))
                                         for d, g in zip(order, groups))))

    json.dump(dict(_what="per-frame median rho and per-scale one-column held-out "
                         "R2 over %d splits, all 12 v6 scales, no selection"
                         % a.splits, rows=frames),
              open(os.path.join(RES, "rho_domains.json"), "w"), indent=1)
    print("\n-> results/%s/rho_domains.json" % a.run)


if __name__ == "__main__":
    main()
