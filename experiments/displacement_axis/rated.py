"""The same measurement on RATED scales instead of a bge direction.

    python experiments/displacement_axis/rated.py --run pilot3

## THE QUESTION (RH, 2026-08-18): is bge the bottleneck?

Everything in this folder measures position as a projection onto one direction in
a 1024-dimensional embedding space. Two costs follow from that and neither is a
property of the phenomenon:

  - **A geometric ceiling.** A single word's vector is mostly orthogonal to any
    one line, so a perfectly tagged word-to-word movement reaches only |cos| 0.669
    and the measured value is 0.375. Chasing the remainder produced three
    retracted claims in one evening; the residual was never a place where
    phenomena hid.
  - **An unnameable residual.** A direction in bge is named only by the words at
    its extremes, so "what did the axis miss" has no answer in words.

**A RATED SCALE HAS NEITHER.** It is one-dimensional by construction, so there is
no orthogonal component to account for, no ceiling below 1.0, and the axis has a
NAME rather than a neighbourhood. `k_ratings_en.json` carries seven of them over
27,242 words, and coverage of this corpus is 99.5% of moved mass and 100% of pole
words -- better powered than the embedding it would replace.

The statistic is unchanged: `N = sum p(w) r(w) / sum p(w)` per arm, `dN = N_post -
N_base`, so the comparison to `dN_position` is like for like.

## THE INSTRUMENT, AND THE BANDS THAT MUST TRAVEL WITH EVERY NUMBER

The producer is NOT missing, as an earlier version of this docstring claimed. It is
`meta/M01_displacement/scripts/k_bulk.py` in the malign-logits repo, the instrument
is frozen at `results/k/INSTRUMENT.txt` (`k_charge_en_v2`, deepseek-v4-flash,
temperature 0.0, sha 5b59a44c..., git b9f122bb), and `results/k/iaa.json` carries a
cross-model reliability study over 475 words (coder A deepseek-v4-flash, coder B
claude-haiku-4-5).

**`iaa.json` says in its own `_what` that the band travels with every drafted
number, at the point of use and not in a limits section.** So:

    scale               pearson   exact   vs human norm
    vulgarity             0.879   97.5%
    transgressiveness     0.828   77.9%
    bodily_harm           0.879   91.4%
    valence               0.901   72.6%   0.862 vs human valence
    charge                0.873   57.0%   0.597 vs arousal
    concreteness          0.834   39.4%   0.875 vs Brysbaert
    register_level        0.597   62.9%

**AND THE SCALES ARE NOT INDEPENDENT, WHICH CHANGES WHAT MAY BE CLAIMED.**
`iaa.json`'s collinearity block gives transgressiveness~charge +0.646,
transgressiveness~valence -0.643, transgressiveness~bodily_harm +0.518,
valence~bodily_harm -0.471, charge~bodily_harm +0.464. Those four scales are
largely ONE DIMENSION. An earlier reading of this file's output reported five
separately significant effects; four of them were that one dimension counted four
times, which is the same headcount error the campaign has booked twice already.

The defensible reading is THREE independent effects, because vulgarity,
register_level and concreteness are near-orthogonal to everything (max |r| 0.24):

    one transgression dimension  DOWN   (transg / bodily_harm / valence / charge together)
    register_level               UP     (independent; WEAKEST agreement, r 0.597 -- band matters most here)
    concreteness                 DOWN   (independent; largest effect; exact agreement only 39.4%
                                         but calibrates to Brysbaert at r 0.875, so the scale tracks
                                         a human norm even where two coders split on integers)

One confound is ruled out rather than assumed: every scale correlates below |0.17|
with log10 COCA frequency, so none of this is a frequency proxy.

**A rating is a property of the INSTRUMENT VERSION.** `k_bulk.py` records that
adding three scales once moved `penis` vulgarity 2->4 and `defenestrate` charge
2->4 at temperature 0. Outputs from different versions must never be pooled, and
that includes any in-context re-rating done with different anchors or a different
scale set: it is a different instrument, comparable on SEPARATIONS and RANKS but
never on absolute level.

## WHAT THIS IS NOT

**These are not human norms and the file says so in capitals.** They are one
aligned model's out-of-context judgements at one frozen version
(`deepseek/deepseek-v4-flash`), with an inter-annotator band and no established
scale comparability. The `k_` prefix exists to keep that visible at the call site
and this module does not launder it. Nothing here may be presented beside
Warriner or Brysbaert as the same kind of object.

**And the rater is an aligned model, which is the instrument's own hazard.** We
are measuring what alignment does to word choice using a ruler an aligned model
produced, so a rating scheme that compresses exactly the distinctions alignment
compresses would hide the effect. Out-of-context rating is a partial protection:
the ratings cannot have been fitted to these frames because they never saw them.

## THE PREDICTION, REGISTERED BEFORE RUNNING

k_ratings should beat bge where transgression is LEXICAL and fail where it is
CONTEXTUAL, because the ratings are type-level:

    kill -> scream      transgressiveness 6 -> 1     should work
    cock -> name        vulgarity 7 -> 1, transgressiveness only 2 -> 1
                        so the SCALE MATTERS, not just the instrument
    fired -> laid       register_level 3 -> 4 (more formal), the euphemism
    pants -> backpack   IDENTICAL on all seven scales

That last is the "She unzipped his ___" family, where the transgression is
entirely positional: out of context `pants` is a garment and rates as one. If
those frames come out flat on every scale while bge sees them, that is not a
failure of the rated approach, it is a MEASUREMENT OF WHICH FRAMES CARRY LEXICAL
transgression and which carry contextual transgression -- a distinction the
corpus has never had.

## THE NULL

A rated scale gets no random-bisection null, so it gets a permutation one:
`--null-draws` shuffles the ratings ACROSS the frame's vocabulary, preserving the
marginal distribution exactly and destroying only the word-to-rating link. The
declared scale must beat that.
"""

import argparse
import collections
import json
import math
import os
import re
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")
#: The root, found by walking up from `malignment` itself, so this file does
#: not encode how deep under `experiments/` it sits. A wrong root makes the
#: globs below return [] instead of raising; `repo_root` refuses instead.
from malignment.paths import REPO
NORMS = os.path.join(os.path.dirname(os.path.dirname(HERE)), "lexicons", "norms")
TABLE = "twp_words_v4"


def z_binom(k, n):
    return (k - n / 2.0) / math.sqrt(n * 0.25) if n > 0 else float("nan")


def pearson(x, y):
    n = len(x)
    if n < 3:
        return None
    mx, my = sum(x) / n, sum(y) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    if sxx <= 0 or syy <= 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def wmean(words, probs, rate):
    tot = sum(probs.get(w, 0.0) for w in words if w in rate)
    if tot <= 0:
        return None, 0.0
    return (sum(probs.get(w, 0.0) * rate[w] for w in words if w in rate) / tot, tot)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--run", default="pilot3")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--null-draws", type=int, default=12,
                    help="rating permutations per cell (0 disables)")
    ap.add_argument("--seed", type=int, default=20260818)
    a = ap.parse_args(argv)

    import numpy as np
    k = json.load(open(os.path.join(NORMS, "k_ratings_en.json")))
    SCALES = k["_meta"]["scales"]
    RAT = {w.lower(): v for w, v in k["ratings"].items()}
    print("k_ratings: %d words, %d scales, model %s"
          % (len(RAT), len(SCALES), k["_meta"]["model"]))
    print("NOT HUMAN NORMS -- one aligned model's out-of-context judgements.")

    rundir = os.path.join(RESULTS, a.run)
    cells = [json.loads(l) for l in open(os.path.join(rundir, "cells.jsonl"))]
    if a.limit:
        cells = cells[:a.limit]
    from malignment import vectors as V
    prompts = sorted({c["prompt"] for c in cells})
    rows = V.rows("SELECT prompt, model, groupArray(word) AS ws, groupArray(p) AS ps "
                  "FROM %s WHERE prompt IN {ps:Array(String)} GROUP BY prompt, model"
                  % TABLE, ps=prompts)
    store = collections.defaultdict(dict)
    for r in rows:
        store[r["prompt"]][r["model"]] = dict(zip(r["ws"], r["ps"]))

    rng = np.random.default_rng(a.seed)
    out = []
    for c in cells:
        per = store.get(c["prompt"]) or {}
        pb, pa = per.get(c["base"]), per.get(c["endpoint"])
        if not pb or not pa:
            continue
        words = sorted(set(pb) | set(pa))
        lw = {w: w.lower() for w in words}
        have = [w for w in words if lw[w] in RAT]
        if len(have) < 5:
            continue
        cov_mass = (sum(abs(pa.get(w, 0.0) - pb.get(w, 0.0)) for w in have)
                    / max(sum(abs(pa.get(w, 0.0) - pb.get(w, 0.0)) for w in words), 1e-12))
        rec = {"item_id": c["item_id"], "prompt": c["prompt"], "domain": c.get("domain"),
               "base": c["base"], "endpoint": c["endpoint"], "signature": c["signature"],
               "dN_position": c.get("dN_position"), "n_rated": len(have),
               "n_words": len(words), "coverage_mass": cov_mass}
        for si, sname in enumerate(SCALES):
            rate = {w: float(RAT[lw[w]][si]) for w in have}
            nb, tb = wmean(have, pb, rate)
            na, ta = wmean(have, pa, rate)
            if nb is None or na is None:
                continue
            rec["dN_" + sname] = na - nb
            rec["Nbase_" + sname] = nb
            #: PERMUTATION NULL. Shuffling ratings across the frame's vocabulary
            #: preserves the marginal distribution exactly and destroys only the
            #: word-to-rating link, which is the thing under test. A rated scale
            #: cannot take the random-bisection null the bge axis takes.
            if a.null_draws:
                vals = np.array([rate[w] for w in have])
                beat = 0
                for _ in range(a.null_draws):
                    perm = rng.permutation(vals)
                    r2 = {w: float(perm[i]) for i, w in enumerate(have)}
                    n2b, _ = wmean(have, pb, r2)
                    n2a, _ = wmean(have, pa, r2)
                    if n2b is not None and n2a is not None and abs(na - nb) > abs(n2a - n2b):
                        beat += 1
                rec["beats_" + sname] = beat / a.null_draws
        out.append(rec)

    path = os.path.join(rundir, "rated.jsonl")
    with open(path, "w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r) + "\n")
    print("\nwrote %s (%d rows)\n" % (path, len(out)))

    print("=" * 92)
    print("COVERAGE: rated words carry %.1f%% of moved mass (median), %d of %d word types"
          % (100 * st.median(r["coverage_mass"] for r in out),
             int(st.median(r["n_rated"] for r in out)), int(st.median(r["n_words"] for r in out))))
    print()
    print("SIGN TEST PER SCALE. Negative dN = moved DOWN the scale.")
    print("bge dN_position for the same cells: %.1f%% negative, z=%+.1f"
          % (100 * sum(1 for r in out if (r.get("dN_position") or 0) < 0) / len(out),
             z_binom(sum(1 for r in out if (r.get("dN_position") or 0) < 0), len(out))))
    print()
    print("   %-18s %6s %8s %8s %11s %9s %8s"
          % ("scale", "cells", "down%", "z", "median dN", "beats null", "r(bge)"))
    for sname in SCALES:
        v = [r for r in out if r.get("dN_" + sname) is not None]
        if not v:
            continue
        kn = sum(1 for r in v if r["dN_" + sname] < 0)
        bt = [r["beats_" + sname] for r in v if r.get("beats_" + sname) is not None]
        pr = [(r["dN_position"], r["dN_" + sname]) for r in v if r.get("dN_position") is not None]
        rr = pearson([x for x, _ in pr], [y for _, y in pr]) if pr else None
        print("   %-18s %6d %7.1f%% %+8.1f %+11.5f %8.0f%% %8s"
              % (sname, len(v), 100 * kn / len(v), z_binom(kn, len(v)),
                 st.median(r["dN_" + sname] for r in v),
                 100 * st.median(bt) if bt else float("nan"),
                 ("%+.3f" % rr) if rr is not None else "n/a"))

    print()
    print("=" * 92)
    print("BY DOMAIN -- the registered prediction is that LEXICAL transgression rates")
    print("and CONTEXTUAL transgression does not. down%% per scale, bge for comparison.")
    byd = collections.defaultdict(list)
    for r in out:
        byd[r["domain"]].append(r)
    keys = [s for s in SCALES]
    print("   %-14s %6s %7s %s" % ("domain", "cells", "bge", " ".join("%7s" % s[:7] for s in keys)))
    for dd, g in sorted(byd.items(), key=lambda kv: -len(kv[1])):
        if len(g) < 40:
            continue
        bge = 100 * sum(1 for r in g if (r.get("dN_position") or 0) < 0) / len(g)
        cols = []
        for sname in keys:
            v = [r for r in g if r.get("dN_" + sname) is not None]
            cols.append("%6.0f%%" % (100 * sum(1 for r in v if r["dN_" + sname] < 0) / len(v)) if v else "    n/a")
        print("   %-14s %6d %6.0f%% %s" % (dd, len(g), bge, " ".join(cols)))

    print()
    print("=" * 92)
    print("THE FRAMES THE PREDICTION SAYS SHOULD BE FLAT ON EVERY SCALE")
    flat = []
    for r in out:
        ds = [abs(r.get("dN_" + s) or 0.0) for s in SCALES]
        if max(ds) < 0.01 and abs(r.get("dN_position") or 0) > 0.01:
            flat.append(r)
    print("   cells where every rated scale moves <0.01 while bge moves >0.01: %d of %d (%.1f%%)"
          % (len(flat), len(out), 100 * len(flat) / len(out)))
    if flat:
        cnt = collections.Counter(r["prompt"][:78] for r in flat)
        for pr, n in cnt.most_common(8):
            print("      %3d cells  %s" % (n, pr))
    return 0


if __name__ == "__main__":
    sys.exit(main())
