"""Let the FRAME pick its poles, without letting it mark its own homework.

    python experiments/displacement_axis/poles_from_data.py

`axis_spaces.py` builds one direction per frame from the AUTHOR'S declared
naughty/nice words. That direction turned out to be a poor guide in rating space:
0.181, against 0.344 for simply choosing the best-fitting named scale per frame.
So the obvious question is whether poles chosen FROM THE DATA do better -- and the
obvious hazard is that fitting a direction to the movement and then scoring it on
that movement is circular.

## THE SPLIT THAT MAKES IT HONEST

Split each frame's LINEAGES in half.

    poles       from half A: the 3 words that rise most and the 3 that fall most
    direction   u = centroid(risers) - centroid(fallers), in each space
    evaluation  against half B's movement, which the direction never saw

The author-pole direction is evaluated on the SAME half B, so the two pole
choices meet on identical ground and the only difference is where the poles came
from.

**What survives is not circular; what remains is worth naming.** A word that
rises in half A tends to rise in half B, because the effect is real and the two
halves are the same frame. That is the thing being measured, not a leak: the
question is whether a data-chosen direction generalises ACROSS MODELS better than
an author-chosen one, and half B is a different set of models.

Two evaluations, because they answer different questions:

    rho        does the direction ORDER the words by how much they move
    mass       what share of half B's total absolute mass shift, sum|dP|, sits on
               words the direction ranks on the correct side of its own origin.
               This is RH's question -- whether the vector captures more of the
               ENTIRE vocabulary's probability shift, not just its ranking.

**THE MASS COLUMN NEEDS A NULL AND NOW HAS TWO.** A direction that places nearly
every word on one side of its origin scores well automatically whenever most mass
moves that way, so the raw share is uninterpretable on its own:

    mass_trivial   the best CONSTANT predictor: put every word on one side and
                   take whichever side holds more of sum|dP|. This is the floor
                   any direction must clear, and it is high -- most frames move
                   most of their mass one way.
    mass_perm      permute s across the frame's words, preserving the marginal
                   distribution of scores exactly and destroying only the
                   word-to-score link. rated.py's null, applied to this metric.

`lift` is the raw share minus the trivial floor. A direction that has genuinely
sorted the vocabulary beats the constant predictor; one that has only discovered
which way the frame moves does not.
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
K_POLE = 3


def direction(vec, hi, lo):
    import numpy as np
    A = [vec[w] for w in hi if w in vec]
    B = [vec[w] for w in lo if w in vec]
    if len(A) < 2 or len(B) < 2:
        return None
    ca, cb = np.mean(A, 0), np.mean(B, 0)
    u = ca - cb
    n = np.linalg.norm(u)
    if n == 0:
        return None
    return u / n, (ca + cb) / 2.0


def score(vec, d, words):
    if d is None:
        return None
    u, org = d
    return {w: float((vec[w] - org) @ u) for w in words if w in vec}


def main():
    import numpy as np
    import yaml
    from scipy import stats
    from malignment import slot_axis as SA
    poles = {}
    for f in glob.glob(os.path.join(REPO, "roster", "prompts", "slots", "*.yaml")):
        for it in (yaml.safe_load(open(f, encoding="utf-8")) or []):
            if isinstance(it, dict) and it.get("prompt") and it.get("naughty"):
                poles[it["prompt"]] = (list(it["naughty"]), list(it["nice"]))
    ctx = collections.defaultdict(dict)
    for f in glob.glob(os.path.join(SLOT, "results", "v6", "rated_v6_*.json")):
        for x in json.load(open(f)):
            if x.get("ratable"):
                ctx[x["prompt"]][x["word"]] = {
                    kk: v for kk, v in x.items()
                    if isinstance(v, int) and not isinstance(v, bool) and kk not in DROP}
    CSC = sorted({s for p in ctx.values() for v in p.values() for s in v})
    kj = json.load(open(os.path.join(NORMS, "k_ratings_en.json")))
    KR = {w.lower(): np.array(v, float) for w, v in kj["ratings"].items()}

    #: per (item, lineage, word): the bge score and dP
    cells = collections.defaultdict(lambda: collections.defaultdict(dict))
    sbge = collections.defaultdict(dict)
    for line in open(os.path.join(RES, "words.jsonl")):
        d = json.loads(line)
        lin = d["base"] + " -> " + d["endpoint"]
        cells[d["item_id"]][lin][d["word"]] = d["dP"]
        sbge[d["item_id"]][d["word"]] = d["s"]
    prompt_of = {c["item_id"]: c["prompt"]
                 for c in (json.loads(l) for l in open(os.path.join(RES, "cells.jsonl")))}

    import random
    rngp = random.Random(20260820)
    rows = []
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
        #: THE REAL 1024-dim VECTORS, from the on-disk cache (0.07s for 40 words,
        #: measured). An earlier version of this file built the bge "data pole"
        #: direction from the SCALAR `s` in words.jsonl, which is a 1-dimensional
        #: space: the direction collapses to +/-1, rho is unchanged by
        #: construction, and the run reported "data wins 0 of 303, p=nan" as
        #: though the two pole choices tied.
        try:
            V = SA.embed_cached(p, words)
            bge_vec = {w: V[i] for i, w in enumerate(words)}
        except Exception:
            bge_vec = {}
        spaces = {
            "bge": bge_vec,
            "ctx": {w: np.array([ctx[p][w][s] for s in CSC], float)
                    for w in words if w in ctx.get(p, {}) and all(s in ctx[p][w] for s in CSC)},
            "k": {w: KR[w.lower()] for w in words if w.lower() in KR}}
        y = [nb[w] for w in words]
        r = dict(item_id=item, prompt=p, n_words=len(words),
                 n_lin_a=len(A), n_lin_b=len(B))
        dpB = {w: sum(lins[l].get(w, 0.0) for l in B) for w in words}
        absmass = sum(abs(v) for v in dpB.values()) or 1.0
        #: the constant-predictor floor, computed once per frame
        up = sum(abs(v) for v in dpB.values() if v > 0)
        r["mass_trivial"] = max(up, absmass - up) / absmass
        for space in ("bge", "ctx", "k"):
            vec = spaces[space]
            for src, (h, ll) in (("data", (hi, lo)), ("author", poles[p])):
                s = score(vec, direction(vec, h, ll), words)
                if not s:
                    continue
                common = [w for w in words if w in s]
                if len(common) < 15 or len({nb[w] for w in common}) < 2:
                    continue
                rr = stats.spearmanr([s[w] for w in common],
                                     [nb[w] for w in common]).statistic
                #: MASS CAPTURED: share of half B's |dP| on words the direction
                #: puts on the side its own sign predicts.
                def captured(sc):
                    c = 0.0
                    for w in common:
                        if (sc[w] > 0) == (dpB[w] > 0):
                            c += abs(dpB[w])
                    return c / absmass
                cap = captured(s)
                #: permutation null: same score marginal, no word-to-score link
                vals = [s[w] for w in common]
                perms = []
                for _ in range(24):
                    pm = list(vals)
                    rngp.shuffle(pm)
                    perms.append(captured(dict(zip(common, pm))))
                r["rho_%s_%s" % (space, src)] = rr
                r["mass_%s_%s" % (space, src)] = cap
                r["massperm_%s_%s" % (space, src)] = float(np.mean(perms))
                r["masslift_%s_%s" % (space, src)] = cap - r["mass_trivial"]
        rows.append(r)
    #: RESTRICT TO THE COMMON FRAME SET. An earlier version printed bge over 302
    #: frames beside contextual over 165 -- the contextual space needs every one
    #: of its 12 scales present for a word, so it covers fewer frames -- and the
    #: two columns were read as a comparison. They were not paired.
    need = ["rho_%s_%s" % (sp, sr) for sp in ("bge", "ctx", "k")
            for sr in ("author", "data")]
    allrows = rows
    rows = [r for r in rows if all(k2 in r and r[k2] == r[k2] for k2 in need)]
    print("frames with >=6 lineages, split in half: %d" % len(allrows))
    print("frames scored in ALL THREE spaces by BOTH pole rules: %d" % len(rows))
    print("(the contextual space needs all 12 scales present per word, which is "
          "what bounds it)\n")
    triv = [r["mass_trivial"] for r in rows if "mass_trivial" in r]
    print("THE FLOOR: the best CONSTANT predictor captures a median %.3f of "
          "half B's |dP|" % float(np.median(triv)))
    print("(most frames move most of their mass one way, which is why the raw")
    print(" mass share cannot be read on its own)\n")
    print("%-30s %9s %9s %9s %9s %9s"
          % ("direction", "median rho", "mean rho", "mass", "vs perm", "LIFT"))
    for space, lab in (("bge", "bge (the s already computed)"),
                       ("ctx", "contextual %d-dim" % len(CSC)),
                       ("k", "k_ratings 7-dim")):
        for src in ("author", "data"):
            key, mk = "rho_%s_%s" % (space, src), "mass_%s_%s" % (space, src)
            v = [abs(r[key]) for r in rows if r.get(key) == r.get(key) and key in r]
            m = [r[mk] for r in rows if mk in r]
            if len(v) < 30:
                continue
            pm = [r["massperm_%s_%s" % (space, src)] for r in rows
                  if "massperm_%s_%s" % (space, src) in r]
            lf = [r["masslift_%s_%s" % (space, src)] for r in rows
                  if "masslift_%s_%s" % (space, src) in r]
            w = stats.wilcoxon(lf) if len(lf) > 8 else None
            print("%-30s %9.3f %9.3f %9.3f %9.3f %+9.3f%s"
                  % ("%s, %s poles" % (lab, src), float(np.median(v)),
                     float(np.mean(v)), float(np.median(m)),
                     float(np.median(pm)) if pm else float("nan"),
                     float(np.median(lf)) if lf else float("nan"),
                     " *" if w and w.pvalue < .05 else "  "))
    print("\nPAIRED, data-chosen poles minus author-declared, same frames")
    for space in ("bge", "ctx", "k"):
        a, b = "rho_%s_data" % space, "rho_%s_author" % space
        d = [abs(r[a]) - abs(r[b]) for r in rows if a in r and b in r
             and r[a] == r[a] and r[b] == r[b]]
        if len(d) < 30:
            continue
        w = stats.wilcoxon(d)
        print("   %-6s median %+.3f | data wins %d of %d | p=%.2g"
              % (space, float(np.median(d)), sum(1 for x in d if x > 0), len(d), w.pvalue))
    json.dump(dict(_what="poles chosen from half the lineages, evaluated on the "
                         "other half; author-declared poles on the same half B",
                   k_pole=K_POLE, rows=rows),
              open(os.path.join(RES, "poles_from_data.json"), "w"))
    print("\n-> results/pilot3/poles_from_data.json")


if __name__ == "__main__":
    main()
