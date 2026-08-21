"""Two questions the centroid cannot answer (RH, 2026-08-18).

    python experiments/displacement_axis/movers.py --run pilot3

## 1. WHERE DOES THE MASS THAT MOVED COME FROM, AND WHERE DOES IT GO?

`dN_position` is a centroid over EVERY scored word, and most words barely move.
So the statistic is diluted by a large still population: a median cell carries
~140 scored words and CANONICAL finds movement in a handful. A 1.6%-of-pole-gap
shift in the centroid is compatible with a large shift in the mass that actually
moved, and the centroid cannot distinguish those.

So restrict to movers, using `malignment.movement` rather than a local threshold.
That module exists because fourteen scripts had disagreed about what a riser is
-- "1,650 cells against 3,366 on the same question" -- and it ships three NAMED
rules. This takes CANONICAL and says so, per its own instruction.

    s_fall   axis position of departing mass, weighted by |Q - P| over fallers
    s_rise   axis position of arriving mass, weighted by EXCESS over risers
    travel   s_rise - s_fall     negative = mass moved toward the permitted pole

**THE ASYMMETRY IS THE MODULE'S AND IS PRESERVED, NOT PATCHED.** Risers are
tested against the renormalisation null; FALLERS ARE NOT -- a faller is a bare
ratio rule, and a word can halve purely because mass left the system elsewhere.
`movement.py` states that nothing downstream may describe fallers as "beyond
renormalisation", so `s_fall` is a position of mass that fell, NOT of mass that
fell for a reason. `s_rise` is weighted by `excess` (Q - null) precisely because
that quantity IS null-tested; weighting risers by raw `Q - P` would import the
bookkeeping the null exists to remove, and both are reported so the difference
is visible rather than argued.

**AND THE NULL HERE IS APPROXIMATE.** `true_word_probs` is truncated at theta, so
R and S cannot be computed over the full vocabulary. The residuals from
`twp_cells_v4.total` are passed in as explicit non-faller mass, which is the
module's honest compromise, and `residual_share` is reported: on this instrument
the tail is about a quarter of the distribution, larger than most single words.

## 2. WHAT IS THE ACTUAL DIRECTION OF THE MOVEMENT?

`D = c_aligned - c_base` is the movement of the distribution's centroid in bge
space. We have only ever reported its projection onto the declared axis. This
asks what D IS.

    consistency   mean pairwise cos between unit D from DIFFERENT items.
                  High => one global direction wearing 300 local descriptions.
                  Near zero => the locality is real and each frame moves its own way.
    Dbar          the mean unit D. If consistency is near zero this is near zero
                  too and means nothing, which is why it is reported second.
    cos(Dbar, u)  how much of each frame's declared axis lies along the global
                  direction, if there is one.

**THE TRAP THIS IS BUILT TO AVOID.** bge-m3 is severely anisotropic -- mean
pairwise cosine 0.87 between raw word vectors -- so a "consistency" measured on
raw vectors would come back high for every pair of anything. D is a DIFFERENCE of
two centroids with equal total weight, so the shared mean component cancels
exactly (verified: global centering changes cos_theta by at most 1.4e-09). The
consistency below is therefore a fact about movement and not about the embedding
space's mean. A comparable figure computed on raw centroids rather than their
difference is printed alongside, as the thing this is NOT measuring.
"""

import argparse
import collections
import json
import math
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")
TABLE = "twp_words_v4"


def wmean(pairs):
    """Weighted mean of (value, weight). None if no positive weight."""
    tot = sum(w for _, w in pairs)
    if tot <= 0:
        return None
    return sum(v * w for v, w in pairs) / tot


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--run", default="pilot3")
    ap.add_argument("--limit", type=int, default=None, help="first N cells, for a quick look")
    ap.add_argument("--pairs", type=int, default=4000,
                    help="max item pairs sampled for the consistency figure")
    a = ap.parse_args(argv)

    import numpy as np
    rundir = os.path.join(RESULTS, a.run)
    cells = [json.loads(l) for l in open(os.path.join(rundir, "cells.jsonl"))]
    if a.limit:
        cells = cells[:a.limit]
    print("run %s | %d cells" % (a.run, len(cells)), flush=True)

    from malignment import vectors as V
    from malignment.slots import read_items, corpora
    from malignment.slot_axis import Axis, embed_cached
    from malignment.movement import movement, CANONICAL

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

    out = []
    #: Unit D per cell, kept with its item so the consistency figure can be
    #: restricted to CROSS-ITEM pairs. Within one item the cells share a prompt
    #: and correlated base models, so a within-item cos is not evidence of a
    #: global direction -- it is the same defect as the per-item consistency null.
    Ds, Ditem, Uaxis, Craw = [], [], {}, []
    done = 0
    for item_id, group in by_item.items():
        d = items.get(item_id)
        if not d:
            continue
        ax = Axis(d["prompt"], list(d["naughty"]), list(d["nice"]))
        if not ax.ok:
            continue
        per = store.get(d["prompt"]) or {}
        vocab = sorted({w for m in per for w in per[m]})
        if not vocab:
            continue
        E = embed_cached(d["prompt"], vocab, True)
        idx = {w: i for i, w in enumerate(vocab)}
        u = ax.axis
        Sarr = (E - ax.origin) @ u
        S = {w: float(Sarr[i]) for i, w in enumerate(vocab)}
        Uaxis[item_id] = u

        for c in group:
            pbm, pam = per.get(c["base"]), per.get(c["endpoint"])
            if pbm is None or pam is None:
                continue
            m = movement(pbm, pam, CANONICAL,
                         residual_pre=c.get("residual_base"),
                         residual_post=c.get("residual_endpoint"))
            fall = [(S[w], -m.delta[w]) for w in m.fallers
                    if w in S and m.delta.get(w, 0.0) < 0]
            rise_x = [(S[w], m.excess[w]) for w in m.risers
                      if w in S and m.excess.get(w, 0.0) > 0]
            rise_d = [(S[w], m.delta[w]) for w in m.risers
                      if w in S and m.delta.get(w, 0.0) > 0]
            nm = m.nonmovers()
            still = [(S[w], pbm.get(w, 0.0)) for w in nm if w in S]

            s_fall = wmean(fall)
            s_rise = wmean(rise_x)
            s_rise_d = wmean(rise_d)
            s_still = wmean(still)
            rec = {"item_id": item_id, "base": c["base"], "endpoint": c["endpoint"],
                   "domain": c.get("domain"), "signature": c["signature"],
                   "gap": c.get("gap"), "dN_position": c.get("dN_position"),
                   "n_fallers": len(m.fallers), "n_risers": len(m.risers),
                   "n_still": len(nm), "n_scored": len(set(pbm) | set(pam)),
                   "s_fall": s_fall, "s_rise": s_rise, "s_rise_delta": s_rise_d,
                   "s_still": s_still,
                   "travel": (s_rise - s_fall) if (s_fall is not None and s_rise is not None) else None,
                   "travel_delta": (s_rise_d - s_fall) if (s_fall is not None and s_rise_d is not None) else None,
                   "mass_fell": sum(w for _, w in fall),
                   "mass_rose_excess": sum(w for _, w in rise_x),
                   "residual_share": m.diagnostics.get("residual_share"),
                   "exact_null": m.diagnostics.get("exact_null"),
                   "inflation": m.inflation}
            out.append(rec)

            pb = np.zeros(len(vocab))
            pa = np.zeros(len(vocab))
            for w, q in pbm.items():
                pb[idx[w]] = q
            for w, q in pam.items():
                pa[idx[w]] = q
            if pb.sum() > 0 and pa.sum() > 0:
                cb = (pb @ E) / pb.sum()
                ca = (pa @ E) / pa.sum()
                D = ca - cb
                nD = float(np.linalg.norm(D))
                if nD > 0:
                    Ds.append(D / nD)
                    Ditem.append(item_id)
                    #: The thing this is NOT measuring: a raw centroid, which
                    #: carries the anisotropic mean and will look consistent
                    #: whatever the movement does.
                    Craw.append(ca / float(np.linalg.norm(ca)))
            done += 1
            if done % 500 == 0:
                print("  %d cells" % done, flush=True)

    path = os.path.join(rundir, "movers.jsonl")
    with open(path, "w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r) + "\n")
    print("\nwrote %s (%d rows)\n" % (path, len(out)))

    # ------------------------------------------------------------------ report
    print("=" * 84)
    print("1. RISERS AND FALLERS -- restricting to the mass that actually moved")
    print("   rule: CANONICAL (min_prob 0.003, fall_ratio 0.5, delta 0.003, null test ON)")
    rs = [r for r in out if r.get("residual_share") is not None]
    if rs:
        print("   residual share median %.3f -- the null is APPROXIMATE on this instrument"
              % st.median(r["residual_share"] for r in rs))
        ex = sum(1 for r in rs if r.get("exact_null"))
        print("   exact_null true on %d of %d cells" % (ex, len(rs)))
    print()
    print("   set sizes per cell (medians): %d scored, %d fallers, %d risers, %d still"
          % tuple(int(st.median([r[k] for r in out])) for k in
                  ("n_scored", "n_fallers", "n_risers", "n_still")))
    print()
    hdr = "   %-14s %6s %9s %9s %9s %10s %9s"
    print(hdr % ("", "cells", "s_fall", "s_rise", "s_still", "travel", "dN_pos"))

    def row(lab, g):
        g2 = [r for r in g if r.get("travel") is not None]
        if not g2:
            return
        print(hdr % (lab, len(g2),
                     "%+.4f" % st.median(r["s_fall"] for r in g2),
                     "%+.4f" % st.median(r["s_rise"] for r in g2),
                     ("%+.4f" % st.median(r["s_still"] for r in g2 if r["s_still"] is not None))
                     if any(r["s_still"] is not None for r in g2) else "n/a",
                     "%+.4f" % st.median(r["travel"] for r in g2),
                     "%+.4f" % st.median(r["dN_position"] for r in g2
                                         if r["dN_position"] is not None)))
    row("all cells", out)
    by = collections.defaultdict(list)
    for r in out:
        by[r["signature"]].append(r)
    for s in ("displacement", "churn", "reverse"):
        row("  " + s, by.get(s, []))
    g2 = [r for r in out if r.get("travel") is not None]
    if g2:
        k = sum(1 for r in g2 if r["travel"] < 0)
        print("\n   travel is NEGATIVE (mass moved toward the permitted pole) in"
              " %d of %d cells = %.1f%%  z=%+.1f"
              % (k, len(g2), 100 * k / len(g2), (k - len(g2) / 2) / math.sqrt(len(g2) * 0.25)))
        gg = [r for r in g2 if r.get("gap")]
        if gg:
            print("   travel as a fraction of the pole gap: median %.1f%%"
                  % (100 * abs(st.median(r["travel"] / r["gap"] for r in gg))))
            print("   (compare dN_position at 1.6%% of the pole gap over all cells)")
        d2 = [r for r in out if r.get("travel_delta") is not None]
        print("\n   risers weighted by EXCESS (null-tested) vs by raw Q-P:")
        print("      travel        median %+.4f" % st.median(r["travel"] for r in g2))
        print("      travel_delta  median %+.4f   <- includes renormalisation bookkeeping"
              % st.median(r["travel_delta"] for r in d2))

    print()
    print("=" * 84)
    print("2. THE ACTUAL DIRECTION OF MOVEMENT")
    if len(Ds) < 50:
        print("   too few cells")
        return 0
    M = np.array(Ds)
    R = np.array(Craw)
    rng = np.random.default_rng(20260818)
    n = len(M)
    #: CROSS-ITEM pairs only. Within an item the cells share a prompt and
    #: correlated base checkpoints, so their D vectors are not independent.
    picks = rng.integers(0, n, size=(a.pairs, 2))
    cross = [(i, j) for i, j in picks if Ditem[i] != Ditem[j]]
    cd = [float(M[i] @ M[j]) for i, j in cross]
    cr = [float(R[i] @ R[j]) for i, j in cross]
    print("   mean pairwise cos between unit MOVEMENT vectors, cross-item pairs (n=%d):" % len(cd))
    print("      %+.4f   (sd %.4f)" % (sum(cd) / len(cd), st.stdev(cd)))
    print("   the same figure on raw ALIGNED CENTROIDS, which is what this is NOT measuring:")
    print("      %+.4f   -- the anisotropic mean, present there and cancelled in D"
          % (sum(cr) / len(cr)))
    Dbar = M.mean(0)
    nb = float(np.linalg.norm(Dbar))
    print("\n   |mean unit D| = %.4f" % nb)
    print("      1.0 would mean every cell moves the same way; 0.0 that directions cancel.")
    print("      For %d independent random unit vectors in %d effective dims, expect ~%.4f"
          % (n, 68, (1.0 / n * 68 / 68) ** 0.5 if n else 0))
    if nb > 1e-9:
        Dhat = Dbar / nb
        cu = [float(Dhat @ Uaxis[i]) for i in Uaxis]
        print("\n   cos(global movement direction, each frame's DECLARED axis):")
        print("      median %+.4f   mean %+.4f   |median| %.4f over %d frames"
              % (st.median(cu), sum(cu) / len(cu), abs(st.median(cu)), len(cu)))
        neg = sum(1 for v in cu if v < 0)
        print("      negative (declared axis points AGAINST the global drift) on %d of %d"
              % (neg, len(cu)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
