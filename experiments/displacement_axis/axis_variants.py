"""Normalisation, origin, and dimensionality: what the rating axis needs.

    python experiments/displacement_axis/axis_variants.py

`poles_from_data.py` left three things unexamined, all raised by RH.

## 1. THE DIMENSIONS WERE NOT NORMALISED, AND THEY ARE NOT COMPARABLE

Within-frame SD, median over frames: `directedness` 1.923, `vocalisation` 1.598,
down to `harm` 0.281. A **6.8x** spread. A centroid difference in raw units is
therefore dominated by whichever scales happen to vary most in that frame, and
the direction is partly an artifact of that. bge does not have this problem --
its dimensions are commensurable by construction -- so the comparison was unfair
to the rating space in a way I did not check.

`z` standardises each dimension WITHIN THE FRAME, over that frame's own rated
vocabulary, before any centroid is taken.

## 2. rho IS ORIGIN-INDEPENDENT; MASS IS NOT

s(w) = (v(w) - origin) . u is a constant shift of v(w).u, so RANKS -- and
therefore Spearman -- are untouched by the origin. Only the mass metric, which
asks which SIDE of zero a word falls, depends on it. So the tables are split:
rho varies with space, normalisation and pole source; mass additionally with
origin. Three origins:

    midpoint    the two pole centroids' midpoint. displacement_axis's own rule,
                and the one its README warns about: "a fact about WHERE THE
                MIDPOINT FALLS, and the midpoint is defined by the pole choices".
    basemass    the base arm's mass-weighted mean position. Where the model
                actually sits before alignment, not where the poles imply.
    centroid    the unweighted mean over the frame's rated vocabulary.

## 3. MORE DIMENSIONS, WHERE THE VOCABULARY SUPPORTS IT

    v6      12 scales, 255 of 255 pilot3 frames
    v6+v3   25 scales, 186 frames (violence 52, identity 72, institutional 62)
    sexual  9 scales, 14 frames -- TOO FEW, excluded rather than reported thin

Every comparison is run on the frames where all its columns exist.
"""

import collections, glob, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, REPO)
RES = os.path.join(HERE, "results", "pilot3")
SLOT = os.path.join(REPO, "experiments", "slot_ratings")
DROP = {"n_eligible", "n_present", "rise", "fall", "net", "ratable"}
K_POLE = 3


def ratings():
    v6 = collections.defaultdict(dict)
    for f in glob.glob(os.path.join(SLOT, "results", "v6", "rated_v6_*.json")):
        for x in json.load(open(f)):
            if x.get("ratable"):
                v6[x["prompt"]][x["word"]] = {
                    k: v for k, v in x.items() if isinstance(v, int)
                    and not isinstance(v, bool) and k not in DROP}
    v3 = collections.defaultdict(dict)
    for f in glob.glob(os.path.join(SLOT, "institutional", "results", "**", "*.json"),
                       recursive=True):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        def walk(o):
            if isinstance(o, dict):
                if "prompt" in o and isinstance(o.get("ratings"), dict):
                    for w, r in o["ratings"].items():
                        v3[o["prompt"]][w] = dict(r)
                    return
                for v in o.values():
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
        walk(d)
    return v6, v3


def main():
    import numpy as np, random, yaml
    from scipy import stats
    from malignment import slot_axis as SA
    poles = {}
    for f in glob.glob(os.path.join(REPO, "roster", "prompts", "slots", "*.yaml")):
        for it in (yaml.safe_load(open(f, encoding="utf-8")) or []):
            if isinstance(it, dict) and it.get("prompt") and it.get("naughty"):
                poles[it["prompt"]] = (list(it["naughty"]), list(it["nice"]))
    v6, v3 = ratings()
    S6 = sorted({s for p in v6.values() for w in p.values() for s in w})
    S3 = sorted({s for p in v3.values() for w in p.values() for s in w
                 if s not in ("ratable",)})
    print("v6 %d dims over %d prompts | v3 %d dims over %d prompts"
          % (len(S6), len(v6), len(S3), len(v3)))

    cells = collections.defaultdict(lambda: collections.defaultdict(dict))
    for line in open(os.path.join(RES, "words.jsonl")):
        d = json.loads(line)
        cells[d["item_id"]][d["base"] + " -> " + d["endpoint"]][d["word"]] = d["dP"]
    prompt_of = {c["item_id"]: c["prompt"]
                 for c in (json.loads(l) for l in open(os.path.join(RES, "cells.jsonl")))}
    rng = random.Random(20260820)

    SPACES = [("bge", None), ("v6 (12d)", (v6, S6)), ("v6+v3 (25d)", (None, None))]
    out = []
    for item, lins in cells.items():
        p = prompt_of.get(item)
        if not p or p not in poles or len(lins) < 6:
            continue
        L = sorted(lins)
        A, B = L[0::2], L[1::2]
        def net(sub):
            n = collections.Counter()
            for l in sub:
                for w, dp in lins[l].items():
                    n[w] += 1 if dp > 0 else (-1 if dp < 0 else 0)
            return n
        na, nb = net(A), net(B)
        words = sorted(set(na) | set(nb))
        if len(words) < 20 or len({nb[w] for w in words}) < 2:
            continue
        hi = [w for w, _ in na.most_common()[:K_POLE]]
        lo = [w for w, _ in na.most_common()[-K_POLE:]]
        dpB = {w: sum(lins[l].get(w, 0.0) for l in B) for w in words}
        absmass = sum(abs(v) for v in dpB.values()) or 1.0
        up = sum(abs(v) for v in dpB.values() if v > 0)
        trivial = max(up, absmass - up) / absmass
        pmass = {w: 0.0 for w in words}
        for l in A:
            for w in words:
                pmass[w] += max(lins[l].get(w, 0.0), 0.0)

        vecs = {}
        try:
            V = SA.embed_cached(p, words)
            vecs["bge"] = ({w: V[i] for i, w in enumerate(words)}, None)
        except Exception:
            pass
        if p in v6:
            ok = [w for w in words if w in v6[p] and all(s in v6[p][w] for s in S6)]
            if len(ok) >= 20:
                vecs["v6 (12d)"] = ({w: np.array([v6[p][w][s] for s in S6], float)
                                     for w in ok}, None)
        if p in v6 and p in v3:
            ok = [w for w in words if w in v6[p] and w in v3[p]
                  and all(s in v6[p][w] for s in S6) and all(s in v3[p][w] for s in S3)]
            if len(ok) >= 20:
                vecs["v6+v3 (25d)"] = (
                    {w: np.array([v6[p][w][s] for s in S6] + [v3[p][w][s] for s in S3],
                                 float) for w in ok}, None)

        r = dict(item_id=item, prompt=p, trivial=trivial, n_words=len(words))
        for sname, (vec, _) in vecs.items():
            M = np.array([vec[w] for w in sorted(vec)])
            keys = sorted(vec)
            for norm in ("raw", "z"):
                X = M.copy()
                if norm == "z":
                    sd = X.std(0)
                    sd[sd == 0] = 1.0
                    X = (X - X.mean(0)) / sd
                V2 = {w: X[i] for i, w in enumerate(keys)}
                for src, (h, ll) in (("data", (hi, lo)), ("author", poles[p])):
                    P1 = [V2[w] for w in h if w in V2]
                    P2 = [V2[w] for w in ll if w in V2]
                    if len(P1) < 2 or len(P2) < 2:
                        continue
                    u = np.mean(P1, 0) - np.mean(P2, 0)
                    n = np.linalg.norm(u)
                    if n == 0:
                        continue
                    u = u / n
                    common = [w for w in words if w in V2]
                    proj = {w: float(V2[w] @ u) for w in common}
                    if len({nb[w] for w in common}) < 2:
                        continue
                    key = "%s|%s|%s" % (sname, norm, src)
                    r["rho|" + key] = stats.spearmanr(
                        [proj[w] for w in common], [nb[w] for w in common]).statistic
                    origins = {
                        "midpoint": float((np.mean(P1, 0) + np.mean(P2, 0)) / 2 @ u),
                        "centroid": float(np.mean([V2[w] for w in common], 0) @ u),
                        "basemass": (sum(pmass[w] * proj[w] for w in common)
                                     / (sum(pmass[w] for w in common) or 1.0)),
                    }
                    for oname, o in origins.items():
                        cap = sum(abs(dpB[w]) for w in common
                                  if (proj[w] - o > 0) == (dpB[w] > 0)) / absmass
                        r["mass|%s|%s" % (key, oname)] = cap - trivial
        out.append(r)

    print("frames: %d | constant-predictor floor, median %.3f\n"
          % (len(out), float(np.median([r["trivial"] for r in out]))))
    print("RHO -- origin-independent. Held-out half B.")
    print("  %-16s %-6s %-8s %8s %8s %7s" % ("space", "norm", "poles", "median", "mean", "n"))
    for sname in ("bge", "v6 (12d)", "v6+v3 (25d)"):
        for norm in ("raw", "z"):
            for src in ("data", "author"):
                k = "rho|%s|%s|%s" % (sname, norm, src)
                v = [abs(r[k]) for r in out if k in r and r[k] == r[k]]
                if len(v) < 30:
                    continue
                print("  %-16s %-6s %-8s %8.3f %8.3f %7d"
                      % (sname, norm, src, float(np.median(v)), float(np.mean(v)), len(v)))
    print("\nMASS LIFT over the constant-predictor floor, by origin. data poles.")
    print("  %-16s %-6s %10s %10s %10s" % ("space", "norm", "midpoint", "basemass", "centroid"))
    for sname in ("bge", "v6 (12d)", "v6+v3 (25d)"):
        for norm in ("raw", "z"):
            cells_ = []
            for oname in ("midpoint", "basemass", "centroid"):
                k = "mass|%s|%s|data|%s" % (sname, norm, oname)
                v = [r[k] for r in out if k in r]
                cells_.append(("%+10.3f" % float(np.median(v))) if len(v) >= 30 else "%10s" % "-")
            print("  %-16s %-6s %s" % (sname, norm, " ".join(cells_)))
    json.dump(dict(_what="normalisation x origin x dimensionality, held-out halves",
                   rows=out), open(os.path.join(RES, "axis_variants.json"), "w"))
    print("\n-> results/pilot3/axis_variants.json")


if __name__ == "__main__":
    main()
