"""What share of the movement can each space explain, and can we NAME it?

    python experiments/displacement_axis/variance_decomp.py

The comparisons so far asked which single direction ranks words best. This asks
the question a name is actually for: how much of a frame's word movement is
accounted for by named scales, by the embedding, by both, and how much by
neither.

## THE DESIGN

Outcome is net movement per word. Every model is FITTED ON HALF THE LINEAGES and
scored on the other half, because a 12-predictor regression will fit anything on
its own data. Held-out R2 can be negative and is reported as it comes.

    each named scale alone        1 predictor, 12 of them
    all named scales              12 predictors, the whole rating vector
    bge axis (author poles)       1 predictor -- the axis as displacement_axis uses it
    bge top-10 PCs                10 predictors, fitted per frame -- what the
                                  embedding could do if allowed more than one line
    named + bge axis              13 -- does the embedding add anything the names miss
    named + bge PCs               22 -- the ceiling of the two together

## WHAT A NAME BUYS

If `all named` approaches `bge PCs`, the phenomenon is nameable at the cost of
nothing. If a single named scale approaches `all named` on some frames, those
frames have a name, not just a direction -- and which name it is, per frame, is
the output that no embedding can produce.

Unexplained is 1 - R2 of the best model, and it is expected to be large: net
movement over 33 lineages is a noisy outcome and no model here should reach 1.
"""

import collections, glob, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, REPO); sys.path.insert(0, HERE)
RES = os.path.join(HERE, "results", "pilot3")


def main():
    import numpy as np, yaml
    wide = "--wide" in sys.argv
    from malignment import slot_axis as SA
    from axis_variants import ratings
    poles = {}
    for f in glob.glob(os.path.join(REPO, "roster", "prompts", "slots", "*.yaml")):
        for it in (yaml.safe_load(open(f, encoding="utf-8")) or []):
            if isinstance(it, dict) and it.get("prompt") and it.get("naughty"):
                poles[it["prompt"]] = (list(it["naughty"]), list(it["nice"]))
    v6, _ = ratings(wide=wide)
    print("rating set: %s\n" % ("v6_wide (n_eligible>=1)" if wide else "v6 (n_eligible>=3)"))
    S6 = sorted({s for p in v6.values() for w in p.values() for s in w})

    cells = collections.defaultdict(lambda: collections.defaultdict(dict))
    for line in open(os.path.join(RES, "words.jsonl")):
        d = json.loads(line)
        cells[d["item_id"]][d["base"] + " -> " + d["endpoint"]][d["word"]] = d["dP"]
    prompt_of = {c["item_id"]: c["prompt"]
                 for c in (json.loads(l) for l in open(os.path.join(RES, "cells.jsonl")))}

    def r2(Xa, ya, Xb, yb):
        """Least squares on half A, R2 on half B. Ridge-stabilised."""
        Xa = np.c_[np.ones(len(Xa)), Xa]
        Xb = np.c_[np.ones(len(Xb)), Xb]
        lam = 1e-3 * np.trace(Xa.T @ Xa) / Xa.shape[1]
        beta = np.linalg.solve(Xa.T @ Xa + lam * np.eye(Xa.shape[1]), Xa.T @ ya)
        pred = Xb @ beta
        ss = ((yb - pred) ** 2).sum()
        tot = ((yb - yb.mean()) ** 2).sum()
        return 1 - ss / tot if tot > 0 else float("nan")

    rows = []
    for item, lins in cells.items():
        p = prompt_of.get(item)
        if not p or p not in v6 or p not in poles or len(lins) < 8:
            continue
        L = sorted(lins); A, B = L[0::2], L[1::2]
        def net(sub):
            n = collections.Counter()
            for l in sub:
                for w, dp in lins[l].items():
                    n[w] += 1 if dp > 0 else (-1 if dp < 0 else 0)
            return n
        na, nb = net(A), net(B)
        words = sorted(set(na) | set(nb))
        ok = [w for w in words if w in v6[p] and all(s in v6[p][w] for s in S6)]
        if len(ok) < 40:
            continue
        ya = np.array([na[w] for w in ok], float)
        yb = np.array([nb[w] for w in ok], float)
        if ya.std() == 0 or yb.std() == 0:
            continue
        R = np.array([[v6[p][w][s] for s in S6] for w in ok], float)
        try:
            E = SA.embed_cached(p, ok)
        except Exception:
            continue
        nau, nic = poles[p]
        idx = {w: i for i, w in enumerate(ok)}
        P1 = [E[idx[w]] for w in nau if w in idx]
        P2 = [E[idx[w]] for w in nic if w in idx]
        if len(P1) < 2 or len(P2) < 2:
            continue
        u = np.mean(P1, 0) - np.mean(P2, 0)
        u = u / (np.linalg.norm(u) or 1)
        ax = (E @ u).reshape(-1, 1)
        Ec = E - E.mean(0)
        U, S, Vt = np.linalg.svd(Ec, full_matrices=False)
        PC = Ec @ Vt[:10].T

        r = dict(item=item, prompt=p, domain=None, n_words=len(ok))
        r["r2_bge_axis"] = r2(ax, ya, ax, yb)
        r["r2_bge_pcs"] = r2(PC, ya, PC, yb)
        r["r2_named_all"] = r2(R, ya, R, yb)
        r["r2_named_plus_axis"] = r2(np.c_[R, ax], ya, np.c_[R, ax], yb)
        r["r2_named_plus_pcs"] = r2(np.c_[R, PC], ya, np.c_[R, PC], yb)
        best, bestn = -9e9, None
        for i, s in enumerate(S6):
            v = r2(R[:, [i]], ya, R[:, [i]], yb)
            r["r2_" + s] = v
            if v == v and v > best:
                best, bestn = v, s
        r["r2_best_single"] = best
        r["best_single"] = bestn
        rows.append(r)

    med = lambda k: float(np.median([x[k] for x in rows if x.get(k) == x.get(k)]))
    print("frames: %d | median words per frame: %d\n"
          % (len(rows), int(np.median([r["n_words"] for r in rows]))))
    print("HELD-OUT R2, fit on half the lineages, scored on the other half")
    print("  %-28s %8s %8s %8s" % ("model", "median", "mean", ">0.1"))
    for k, lab in (("r2_bge_axis", "bge axis (author poles), 1"),
                   ("r2_bge_pcs", "bge top-10 PCs, 10"),
                   ("r2_best_single", "best single named scale, 1"),
                   ("r2_named_all", "all 12 named scales, 12"),
                   ("r2_named_plus_axis", "named + bge axis, 13"),
                   ("r2_named_plus_pcs", "named + bge PCs, 22")):
        v = [r[k] for r in rows if r.get(k) == r.get(k)]
        print("  %-28s %8.3f %8.3f %7.0f%%"
              % (lab, float(np.median(v)), float(np.mean(v)),
                 100 * sum(1 for x in v if x > .1) / len(v)))
    print("\n  unexplained by the best model (named + bge PCs): %.0f%%"
          % (100 * (1 - med("r2_named_plus_pcs"))))

    print("\nWHICH NAME, WHERE. Frames whose best single named scale reaches R2>0.1:")
    good = [r for r in rows if r.get("r2_best_single", 0) > .1]
    cnt = collections.Counter(r["best_single"] for r in good)
    print("  %d of %d frames" % (len(good), len(rows)))
    for n, c in cnt.most_common():
        ex = [r["prompt"] for r in good if r["best_single"] == n][:1]
        print("   %-14s %3d frames   e.g. %s" % (n, c, (ex[0][:52] + " ___") if ex else ""))
    print("\n  how much of `all named` a SINGLE name recovers, on those frames: %.2f"
          % float(np.median([r["r2_best_single"] / r["r2_named_all"]
                             for r in good if r.get("r2_named_all", 0) > .05])))
    json.dump(dict(_what="held-out R2 by predictor set, per frame", rows=rows),
              open(os.path.join(RES, "variance_decomp.json"), "w"))
    print("\n-> results/pilot3/variance_decomp.json")


if __name__ == "__main__":
    main()
