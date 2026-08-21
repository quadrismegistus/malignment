"""The SAME axis construction in three spaces. Head to head, not scale by scale.

    python experiments/displacement_axis/axis_spaces.py

`compare_scorers.py` compared one bge DIRECTION against individual named SCALES,
which is not a fair fight in either direction: bge gets a per-frame axis fitted
to that frame's poles, while a named scale is one global dimension. RH's fix is
to build the axis the same way in every space:

    u = centroid(naughty) - centroid(nice),  unit length
    origin = the midpoint of the two centroids
    s(w) = (v(w) - origin) . u

changing only what v(w) is:

    bge            1024-dim embedding      `s` in words.jsonl, already computed
    contextual     12-dim slot_ratings     rated per (prompt, word)
    type-level      7-dim k_ratings        rated out of context, one per word

Now every space contributes ONE direction per frame, chosen by the same rule from
the same declared poles, and the comparison is between SPACES rather than between
a space and a list of scales.

## WHAT THIS CAN AND CANNOT SETTLE

It can say which space carries the frame's own naughty/nice distinction in a form
that predicts which words move. It CANNOT say a space is better in general: the
poles are author-declared and a space that happens to align with how this author
wrote poles is flattered. Every frame's axis is a different direction in each
space, so 255 frames is 255 separate fits and the comparison is a paired one.

Pole coverage: the contextual ratings cover a median 10 of 11 pole words per
frame and at least 6 on 244 of 255 frames. Frames below that are dropped rather
than fitted on three points.

## SEPARATION IS REPORTED, NOT ASSUMED

A direction only means something if the poles it was built from actually separate
along it. `slot_axis.Axis` reports `separates` and `purity` for bge; the same
leave-one-out purity is computed here for each space, so a frame where the rating
space cannot tell naughty from nice is visible rather than silently contributing
a random direction.
"""

import collections, glob, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
#: The root, found by walking up from `malignment` itself, so this file does
#: not encode how deep under `experiments/` it sits. A wrong root makes the
#: globs below return [] instead of raising; `repo_root` refuses instead.
from malignment.paths import REPO
sys.path.insert(0, REPO)
RES = os.path.join(HERE, "results", "pilot3")
SLOT = os.path.join(REPO, "experiments", "slot_ratings")
NORMS = os.path.join(REPO, "lexicons", "norms")
DROP = {"n_eligible", "n_present", "rise", "fall", "net", "ratable"}
MIN_POLE = 3          #: per side, below which no direction is fitted


def load_poles():
    import yaml
    out = {}
    for f in glob.glob(os.path.join(REPO, "roster", "prompts", "slots", "*.yaml")):
        for it in (yaml.safe_load(open(f, encoding="utf-8")) or []):
            if isinstance(it, dict) and it.get("prompt") and it.get("naughty") \
                    and it.get("nice"):
                out[it["prompt"]] = (list(it["naughty"]), list(it["nice"]))
    return out


def axis_scores(vec, naughty, nice, words):
    """u = centroid(naughty) - centroid(nice); s = (v - origin) . u. Plus purity."""
    import numpy as np
    N = [vec[w] for w in naughty if w in vec]
    P = [vec[w] for w in nice if w in vec]
    if len(N) < MIN_POLE or len(P) < MIN_POLE:
        return None, None, None
    cn, cp = np.mean(N, 0), np.mean(P, 0)
    u = cn - cp
    n = np.linalg.norm(u)
    if n == 0:
        return None, None, None
    u = u / n
    origin = (cn + cp) / 2.0
    s = {w: float((vec[w] - origin) @ u) for w in words if w in vec}
    #: LEAVE-ONE-OUT PURITY: refit without each pole word, then check it still
    #: lands on its own side. A direction whose own poles do not separate is a
    #: random direction with a name.
    ok = 0
    tot = 0
    for side, other, sign in ((N, P, +1), (P, N, -1)):
        if len(side) <= MIN_POLE:
            continue
        for i in range(len(side)):
            rest = [v for j, v in enumerate(side) if j != i]
            c1, c2 = np.mean(rest, 0), np.mean(other, 0)
            uu = (c1 - c2) if sign > 0 else (c2 - c1)
            nn = np.linalg.norm(uu)
            if nn == 0:
                continue
            uu = uu / nn
            org = (c1 + c2) / 2.0
            tot += 1
            ok += (float((side[i] - org) @ uu) > 0) == (sign > 0)
    return s, (ok / tot if tot else None), float(np.linalg.norm(cn - cp))


def main():
    import numpy as np
    from scipy import stats
    poles = load_poles()
    ctx = collections.defaultdict(dict)
    for f in glob.glob(os.path.join(SLOT, "results", "v6", "rated_v6_*.json")):
        for x in json.load(open(f)):
            if x.get("ratable"):
                ctx[x["prompt"]][x["word"]] = {
                    k: v for k, v in x.items()
                    if isinstance(v, int) and not isinstance(v, bool) and k not in DROP}
    CSC = sorted({s for p in ctx.values() for v in p.values() for s in v})
    k = json.load(open(os.path.join(NORMS, "k_ratings_en.json")))
    KSC = k["_meta"]["scales"]
    KR = {w.lower(): np.array(v, float) for w, v in k["ratings"].items()}
    print("spaces: bge 1024-dim | contextual %d-dim %s | k_ratings %d-dim"
          % (len(CSC), CSC, len(KSC)))

    #: bge scores and net movement, straight from words.jsonl
    acc = collections.defaultdict(lambda: {"s": None, "net": 0})
    for line in open(os.path.join(RES, "words.jsonl")):
        d = json.loads(line)
        a = acc[(d["item_id"], d["word"])]
        a["s"] = d["s"]
        a["net"] += 1 if d["dP"] > 0 else (-1 if d["dP"] < 0 else 0)
    prompt_of = {c["item_id"]: c["prompt"]
                 for c in (json.loads(l) for l in open(os.path.join(RES, "cells.jsonl")))}
    by = collections.defaultdict(list)
    for (item, w), a in acc.items():
        if a["s"] is not None:
            by[item].append((w, a["s"], a["net"]))

    rows = []
    for item, ws in by.items():
        p = prompt_of.get(item)
        if not p or p not in poles:
            continue
        nau, nic = poles[p]
        words = [w for w, _, _ in ws]
        cv = {w: np.array([ctx[p][w][s] for s in CSC], float)
              for w in words if w in ctx.get(p, {}) and all(s in ctx[p][w] for s in CSC)}
        kv = {w: KR[w.lower()] for w in words if w.lower() in KR}
        s_ctx, pur_ctx, gap_ctx = axis_scores(cv, nau, nic, words)
        s_k, pur_k, gap_k = axis_scores(kv, nau, nic, words)
        if not s_ctx or not s_k:
            continue
        keep = [(w, sb, n) for w, sb, n in ws if w in s_ctx and w in s_k]
        if len(keep) < 15 or len({n for _, _, n in keep}) < 2:
            continue
        net = [n for _, _, n in keep]
        rows.append(dict(
            item_id=item, prompt=p, n_words=len(keep),
            rho_bge=stats.spearmanr([sb for _, sb, _ in keep], net).statistic,
            rho_ctx=stats.spearmanr([s_ctx[w] for w, _, _ in keep], net).statistic,
            rho_k=stats.spearmanr([s_k[w] for w, _, _ in keep], net).statistic,
            purity_ctx=pur_ctx, purity_k=pur_k, gap_ctx=gap_ctx, gap_k=gap_k))
    print("frames fitted in all three spaces: %d\n" % len(rows))

    print("%-34s %8s %8s %9s %9s"
          % ("space (one axis per frame)", "median", "mean", "|rho|>0.3", "pole purity"))
    for lab, key, pk in (("bge, 1024-dim embedding", "rho_bge", None),
                         ("contextual, %d-dim ratings" % len(CSC), "rho_ctx", "purity_ctx"),
                         ("k_ratings, %d-dim type-level" % len(KSC), "rho_k", "purity_k")):
        v = [abs(r[key]) for r in rows if r[key] == r[key]]
        pu = [r[pk] for r in rows if pk and r.get(pk) is not None]
        print("%-34s %8.3f %8.3f %8.0f%% %9s"
              % (lab, float(np.median(v)), float(np.mean(v)),
                 100 * sum(1 for x in v if x > .3) / len(v),
                 "%.3f" % float(np.median(pu)) if pu else "n/a"))

    print("\nPAIRED, per frame -- which space wins, and by how much")
    for a, b in (("rho_ctx", "rho_bge"), ("rho_ctx", "rho_k"), ("rho_bge", "rho_k")):
        d = [abs(r[a]) - abs(r[b]) for r in rows if r[a] == r[a] and r[b] == r[b]]
        w = stats.wilcoxon(d)
        print("   %-12s minus %-10s median %+.3f | %s wins %d of %d | p=%.2g"
              % (a[4:], b[4:], float(np.median(d)), a[4:],
                 sum(1 for x in d if x > 0), len(d), w.pvalue))

    json.dump(dict(_what="one axis per frame in each of three spaces, built by the "
                         "same centroid rule from the same declared poles",
                   scales_contextual=CSC, scales_k=KSC, rows=rows),
              open(os.path.join(RES, "axis_spaces.json"), "w"))
    print("\n-> results/pilot3/axis_spaces.json")


if __name__ == "__main__":
    main()
