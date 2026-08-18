"""What fraction of the distribution's actual movement is the naughty-nice axis?

    python experiments/displacement_axis/axis_share.py --run pilot2

Writes `<run>/axis_share.jsonl`. This is the measurement the pilot was missing.

## THE QUESTION (RH, 2026-08-18)

Everything reported so far is a PROJECTION. `dN_position` is the movement of the
distribution's centroid, in embedding space, projected onto one chosen direction:
the naughty-nice axis `u = centroid(naughty) - centroid(nice)`.

A projection cannot tell you whether it caught the movement. Writing

    c_b = sum p_b(w) e(w) / T_b      base centroid in embedding space
    c_a = sum p_a(w) e(w) / T_a      aligned centroid
    D   = c_a - c_b                  what the distribution ACTUALLY did

we have been reporting `D . u` and never `|D|`. So a cell where the centroid
moves a long way in some direction that has little to do with transgression, and
a cell where it barely moves but moves along `u`, are indistinguishable in every
number in `cells.jsonl`. **Statistical significance of `D . u` is not evidence
that `u` is the relevant direction**, and with 3,758 cells a small consistent
projection will be significant whatever the rest of the movement is doing.

So:

    cos_theta = (D . u) / |D|          how much of the DIRECTION is ours
    r2        = cos_theta ** 2         how much of the MOVEMENT is ours
    orth      = |D| * sqrt(1 - cos^2)  the part going somewhere else

`cos_theta` is signed on the same convention as everything else: NEGATIVE means
the centroid moved toward the nice pole.

## WHAT THIS CAN DO TO THE CHURN CLASS

Churn was characterised as mass leaving and arriving at the same end of the axis.
That is a statement about the projection, and it has two very different possible
causes which the projection cannot separate:

    the centroid barely moves at all                    -> genuinely little happens
    the centroid moves a LOT, orthogonal to u            -> a lot happens, elsewhere

The second would mean churn cells are not quiet cells; they are cells where
alignment is doing something large that the naughty-nice axis is not built to
see. That is a decomposition of churn into two kinds, and it is the direct answer
to "can we decompose churn".

## THE VALIDATION THAT MAKES THIS TRUSTWORTHY

`s(w) = (e(w) - origin) . u`, so `D . u` computed from the full vectors must
equal `dN_position` computed from the scores, EXACTLY up to floating point. The
origin cancels because `D` is a difference of two centroids and both centroids
are affine in the same origin. The script asserts this per cell and refuses the
whole run on the first failure, naming the cell.

An assert that ties a new quantity to an old one through an identity is worth
more than a plausibility check on the new quantity alone: it cannot pass by being
approximately right.
"""

import argparse
import collections
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")
TABLE = "twp_words_v4"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--run", default="pilot2")
    #: **1e-9 REFUSED A CORRECT RUN AND THE REFUSAL WAS THE TOLERANCE, NOT A BUG.**
    #: First run stopped at |D.u - dN| = 1.311e-09. The embeddings are float32
    #: (verified: `embed_cached(...).dtype` is float32, eps 1.19e-07), so a
    #: quantity of order 1e-2 accumulated over ~100 terms carries absolute error
    #: around 1e-9 by construction. 1e-6 is still three orders tighter than any
    #: disagreement that would mean something -- the projections being compared
    #: are order 1e-2 -- so the guard keeps its power while not asserting float64
    #: precision of a float32 pipeline.
    ap.add_argument("--tol", type=float, default=1e-6,
                    help="max |D.u - dN_position| tolerated before refusing")
    #: **cos_theta IS UNINTERPRETABLE WITHOUT THIS.** A random direction in 1024
    #: dimensions scores |cos| about 0.03 against anything, but D lives in the
    #: span of the frame's ~100 word vectors and bge-m3 is strongly anisotropic,
    #: so the real null is unknown and could plausibly reach 0.1 -- which is
    #: where the churn class sits. Assuming 0.03 would convert "churn is
    #: orthogonal" into "churn is a weak real effect" by arithmetic nobody
    #: performed.
    #:
    #: The null is built by the SAME CONSTRUCTION as the real axis -- a centroid
    #: difference between two disjoint word sets, size-matched to the declared
    #: poles -- drawn from the frame's own vocabulary. Two draws, because they
    #: answer different objections:
    #:
    #:   uniform   any words from the union vocabulary. Asks whether the axis is
    #:             special at all.
    #:   head      only words carrying the top `--head-mass` of base probability.
    #:             Asks whether it is special BEYOND being made of words the
    #:             model actually emits, which the declared poles are and a
    #:             uniform draw mostly is not. This is the harder test and the
    #:             one the question deserves.
    ap.add_argument("--null-draws", type=int, default=24,
                    help="random size-matched axes per item (0 disables)")
    ap.add_argument("--head-mass", type=float, default=0.90,
                    help="mass fraction defining the 'words the model uses' pool")
    ap.add_argument("--seed", type=int, default=20260818)
    a = ap.parse_args(argv)

    import numpy as np
    rundir = os.path.join(RESULTS, a.run)
    cells = [json.loads(l) for l in open(os.path.join(rundir, "cells.jsonl"))]
    print("run %s | %d cells" % (a.run, len(cells)), flush=True)

    from malignment import vectors as V
    from malignment.slots import read_items, corpora
    from malignment.slot_axis import Axis, embed_cached

    items = {d["item_id"]: d for _, p in corpora() for d in read_items(p)}
    prompts = sorted({c["prompt"] for c in cells})
    rows = V.rows("SELECT prompt, model, groupArray(word) AS ws, groupArray(p) AS ps "
                  "FROM %s WHERE prompt IN {ps:Array(String)} GROUP BY prompt, model"
                  % TABLE, ps=prompts)
    store = collections.defaultdict(dict)
    for r in rows:
        store[r["prompt"]][r["model"]] = dict(zip(r["ws"], r["ps"]))

    by_item = collections.defaultdict(list)
    for c in cells:
        by_item[c["item_id"]].append(c)

    rng = np.random.default_rng(a.seed)
    out, done, worst = [], 0, 0.0
    for item_id, group in by_item.items():
        d = items.get(item_id)
        if not d:
            continue
        ax = Axis(d["prompt"], list(d["naughty"]), list(d["nice"]))
        if not ax.ok:
            continue
        per = store.get(d["prompt"]) or {}
        #: One embedding matrix per ITEM over the union of every arm's vocabulary,
        #: so the per-cell work is arithmetic on rows already in memory.
        vocab = sorted({w for m in per for w in per[m]})
        if not vocab:
            continue
        E = embed_cached(d["prompt"], vocab, True)
        idx = {w: i for i, w in enumerate(vocab)}
        u = ax.axis
        S = (E - ax.origin) @ u

        #: NULL AXES, built once per item and shared by all its cells, because
        #: they depend on the frame's vocabulary and on nothing a checkpoint
        #: supplies -- exactly like the real axis. Sharing them across the item's
        #: cells is also what makes the comparison paired: real and null are
        #: scored against the SAME D.
        n_g, n_n = len(d["naughty"]), len(d["nice"])
        #: Pool of words the model actually emits, by base mass pooled over arms.
        #: The declared poles are made of such words; a uniform draw over the
        #: union is mostly tail, so without this pool the null would be beaten by
        #: a real axis for the uninteresting reason that its words carry mass.
        pooled = collections.Counter()
        for m in per:
            for w, q in per[m].items():
                pooled[w] += q
        tot_pool = sum(pooled.values()) or 1.0
        run, head_pool = 0.0, []
        for w, q in pooled.most_common():
            head_pool.append(idx[w])
            run += q
            if run / tot_pool >= a.head_mass:
                break
        nulls = {"uniform": [], "head": []}
        if a.null_draws and n_g + n_n <= len(vocab):
            for _ in range(a.null_draws):
                for kind, pool in (("uniform", range(len(vocab))), ("head", head_pool)):
                    pool = list(pool)
                    if len(pool) < n_g + n_n:
                        continue
                    pick = rng.choice(len(pool), n_g + n_n, replace=False)
                    A = E[[pool[i] for i in pick[:n_g]]].mean(0)
                    B = E[[pool[i] for i in pick[n_g:]]].mean(0)
                    v = A - B
                    nv = float(np.linalg.norm(v))
                    if nv > 1e-8:
                        nulls[kind].append(v / nv)

        for c in group:
            pbm, pam = per.get(c["base"]), per.get(c["endpoint"])
            if pbm is None or pam is None:
                continue
            pb = np.zeros(len(vocab))
            pa = np.zeros(len(vocab))
            for w, q in pbm.items():
                pb[idx[w]] = q
            for w, q in pam.items():
                pa[idx[w]] = q
            tb, ta = pb.sum(), pa.sum()
            if tb <= 0 or ta <= 0:
                continue
            cb = (pb @ E) / tb
            ca = (pa @ E) / ta
            D = ca - cb
            nrm = float(np.linalg.norm(D))
            proj = float(D @ u)

            #: THE IDENTITY. Same quantity by two routes; the origin cancels
            #: because D is a difference of centroids affine in one origin.
            check = float((pa @ S) / ta - (pb @ S) / tb)
            err = abs(proj - check)
            worst = max(worst, err)
            if err > a.tol:
                print("REFUSING: %s %s -> %s  |D.u - dN| = %.3e exceeds %.1e"
                      % (item_id, c["base"], c["endpoint"], err, a.tol), file=sys.stderr)
                return 1

            cos = (proj / nrm) if nrm > 0 else None
            #: **COMPARE MAGNITUDES.** A random axis has an arbitrary sign, so its
            #: cos is symmetric about zero and its MEDIAN is ~0 by construction.
            #: Comparing the real signed cos against that would show the real axis
            #: winning on every draw and would be measuring the sign convention.
            #: `beats` is the paired quantity that matters: the fraction of null
            #: axes through this frame's own words that the declared axis
            #: out-aligns on THIS cell's movement.
            nullstats = {}
            if cos is not None and nrm > 0:
                for kind, axes in nulls.items():
                    if not axes:
                        continue
                    signed = [float(D @ v) / nrm for v in axes]
                    cs = sorted(abs(x) for x in signed)
                    nullstats["null_%s_med" % kind] = cs[len(cs) // 2]
                    nullstats["null_%s_p95" % kind] = cs[int(0.95 * (len(cs) - 1))]
                    nullstats["beats_%s" % kind] = sum(
                        1 for x in cs if abs(cos) > x) / len(cs)
                    #: **THE SIGNS, KEPT, AND THE FIRST VERSION THREW THEM AWAY.**
                    #: Summaries of |cos| answer the MAGNITUDE question and cannot
                    #: answer the direction one. "63% of cells move nice-ward"
                    #: has null 50% only if the axis orientation is arbitrary, and
                    #: ours is fixed by the author's labels -- so the real null is
                    #: whether an arbitrary bisection of the same words produces
                    #: comparable CONSISTENCY of sign across an item's checkpoints.
                    #: A null axis carries an arbitrary orientation, held fixed
                    #: across the item's cells by being built once per item, which
                    #: is what makes the per-item fraction meaningful.
                    if kind == "head":
                        nullstats["null_head_signed"] = [round(x, 6) for x in signed]
            out.append({
                "item_id": item_id, "base": c["base"], "endpoint": c["endpoint"],
                "domain": c.get("domain"), "signature": c["signature"],
                "dN_position": c.get("dN_position"),
                **nullstats,
                "proj": proj, "norm": nrm,
                "cos_theta": cos,
                "r2": (cos * cos) if cos is not None else None,
                "orth": (nrm * math.sqrt(max(0.0, 1.0 - cos * cos))) if cos is not None else None,
                "dT": c.get("dT"),
            })
            done += 1
            if done % 400 == 0:
                print("  %d cells" % done, flush=True)

    print("\nidentity check: largest |D.u - dN_position| = %.2e over %d cells" % (worst, done))
    path = os.path.join(rundir, "axis_share.jsonl")
    with open(path, "w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r) + "\n")
    print("wrote %s (%d rows)" % (path, len(out)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
