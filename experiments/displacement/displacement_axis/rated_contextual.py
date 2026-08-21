"""The same measurement again, on CONTEXTUAL ratings. Three scorers compared.

    python experiments/displacement_axis/rated_contextual.py --run pilot3
    python experiments/displacement_axis/rated_contextual.py --limit 200 --null-draws 0

## WHAT THIS ADDS TO rated.py

`rated.py` replaced the bge projection with `k_ratings_en.json`, which is
TYPE-LEVEL: one number per word, rated out of context. Its docstring registers
the prediction that follows from that, before it was run:

    k_ratings should beat bge where transgression is LEXICAL and fail where it
    is CONTEXTUAL ... `pants -> backpack` IDENTICAL on all seven scales. If those
    frames come out flat on every scale while bge sees them, that is a
    MEASUREMENT OF WHICH FRAMES CARRY LEXICAL transgression and which carry
    CONTEXTUAL transgression.

`experiments/slot_ratings` produced exactly the instrument that prediction
implies is missing: the same kind of named scale, rated PER (prompt, word), so
`pants` in "She unzipped his ___" and `pants` in a laundry frame are two
different numbers. This file runs the identical statistic a third time with those
ratings, so the three scorers can be compared on the same cells:

    bge            geometric, per-frame axis, unnameable residual   `dN_position`
    k_ratings      named, type-level, 27,242 words                  `rated.jsonl`
    slot_ratings   named, contextual, 303 frames                    here

THE STATISTIC IS UNCHANGED, which is the point:

    N = sum p(w) r(w) / sum p(w)   per arm,   dN = N_aligned - N_base

so `dN` here, `dN_<scale>` in rated.jsonl and `dN_position` in cells.jsonl are
like for like and differ only in what r(w) is.

## THE SAME HAZARD, AND IT IS WORSE HERE

rated.py records it: we measure what alignment does to word choice with a ruler
an aligned model produced. Out-of-context rating is a partial protection because
the ratings cannot have been fitted to frames they never saw. **Contextual rating
gives that protection up** -- the rater saw the frame. That is the price of the
sensitivity and it belongs beside every number this file produces, not in a
limits section.

## THE NULL

The same permutation as rated.py: shuffle the ratings ACROSS the frame's
vocabulary, preserving the marginal distribution exactly and destroying only the
word-to-rating link. A contextual scale that beats bge but not its own
permutation has measured nothing.
"""

import argparse, collections, glob, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
#: The root, found by walking up from `malignment` itself, so this file does
#: not encode how deep under `experiments/` it sits. A wrong root makes the
#: globs below return [] instead of raising; `repo_root` refuses instead.
from malignment.paths import REPO
sys.path.insert(0, REPO)
RESULTS = os.path.join(HERE, "results")
SLOT = os.path.join(REPO, "experiments", "slot_ratings")
TABLE = "twp_words_v4_best"
DROP = {"n_eligible", "n_present", "rise", "fall", "net", "ratable"}


def contextual():
    """(prompt, word) -> {scale: value}, from the v6 corpus run."""
    R = collections.defaultdict(dict)
    for f in glob.glob(os.path.join(SLOT, "results", "v6", "rated_v6_*.json")):
        for x in json.load(open(f)):
            if x.get("ratable"):
                R[(x["prompt"], x["word"])].update(
                    {k: v for k, v in x.items()
                     if isinstance(v, int) and not isinstance(v, bool) and k not in DROP})
    return R


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--run", default="pilot3")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--null-draws", type=int, default=12)
    ap.add_argument("--seed", type=int, default=20260820)
    a = ap.parse_args(argv)
    import numpy as np
    from scipy import stats
    from malignment import vectors as V

    R = contextual()
    scales = sorted({k for v in R.values() for k in v})
    print("contextual ratings: %d (prompt, word) pairs over %d prompts, %d scales"
          % (len(R), len({p for p, _ in R}), len(scales)))
    print("RATED IN CONTEXT, so the rater saw the frame. rated.py's out-of-context")
    print("protection does not apply here; that is the price of the sensitivity.\n")

    rundir = os.path.join(RESULTS, a.run)
    cells = [json.loads(l) for l in open(os.path.join(rundir, "cells.jsonl"))]
    if a.limit:
        cells = cells[:a.limit]
    prompts = sorted({c["prompt"] for c in cells})
    rows = V.rows("SELECT prompt, model, groupArray(word) AS ws, groupArray(p) AS ps "
                  "FROM %s WHERE prompt IN {ps:Array(String)} GROUP BY prompt, model"
                  % TABLE, ps=prompts)
    store = collections.defaultdict(dict)
    for r in rows:
        store[r["prompt"]][r["model"]] = dict(zip(r["ws"], r["ps"]))

    #: k_ratings, for the three-way, keyed by the same (item, base, endpoint)
    kr = {}
    p = os.path.join(rundir, "rated.jsonl")
    if os.path.exists(p):
        for l in open(p):
            d = json.loads(l)
            kr[(d["item_id"], d["base"], d["endpoint"])] = d

    rng = np.random.default_rng(a.seed)
    out = []
    for c in cells:
        per = store.get(c["prompt"]) or {}
        pb, pa = per.get(c["base"]), per.get(c["endpoint"])
        if not pb or not pa:
            continue
        words = sorted(set(pb) | set(pa))
        have = [w for w in words if (c["prompt"], w) in R]
        if len(have) < 5:
            continue
        mb = sum(pb.get(w, 0.0) for w in have)
        ma = sum(pa.get(w, 0.0) for w in have)
        if mb <= 0 or ma <= 0:
            continue
        rec = dict(item_id=c["item_id"], prompt=c["prompt"], domain=c.get("domain"),
                   base=c["base"], endpoint=c["endpoint"],
                   signature=c.get("signature"), dN_position=c.get("dN_position"),
                   n_rated=len(have), n_words=len(words),
                   coverage_mass=mb / sum(pb.values()) if sum(pb.values()) else None)
        k = kr.get((c["item_id"], c["base"], c["endpoint"]))
        for s in scales:
            vals = [R[(c["prompt"], w)].get(s) for w in have]
            if any(v is None for v in vals):
                continue
            nb = sum(pb.get(w, 0.0) * v for w, v in zip(have, vals)) / mb
            na = sum(pa.get(w, 0.0) * v for w, v in zip(have, vals)) / ma
            rec["dN_" + s] = na - nb
            rec["Nbase_" + s] = nb
            if a.null_draws:
                arr = np.array(vals, float)
                beat = 0
                for _ in range(a.null_draws):
                    pm = rng.permutation(arr)
                    n0 = sum(pb.get(w, 0.0) * v for w, v in zip(have, pm)) / mb
                    n1 = sum(pa.get(w, 0.0) * v for w, v in zip(have, pm)) / ma
                    beat += abs(na - nb) > abs(n1 - n0)
                rec["beats_" + s] = beat / a.null_draws
        if k:
            for s in ("transgressiveness", "vulgarity", "concreteness", "charge"):
                if "dN_" + s in k:
                    rec["k_dN_" + s] = k["dN_" + s]
        out.append(rec)

    print("cells scored: %d of %d" % (len(out), len(cells)))
    print("median rated coverage of base mass: %.3f"
          % np.median([r["coverage_mass"] for r in out if r["coverage_mass"]]))

    print("\n%-14s %7s %7s %9s %10s %9s"
          % ("scale", "cells", "down%", "median dN", "beats null", "r(bge dN)"))
    summary = []
    for s in scales:
        v = [r for r in out if r.get("dN_" + s) is not None]
        if len(v) < 30:
            continue
        d = [r["dN_" + s] for r in v]
        bt = [r["beats_" + s] for r in v if r.get("beats_" + s) is not None]
        bg = [(r["dN_position"], r["dN_" + s]) for r in v
              if r.get("dN_position") is not None]
        rr = stats.spearmanr([x for x, _ in bg], [y for _, y in bg]).statistic if bg else float("nan")
        print("%-14s %7d %6.0f%% %+9.4f %10.2f %9.3f"
              % (s, len(v), 100 * sum(1 for x in d if x < 0) / len(d),
                 float(np.median(d)), float(np.mean(bt)) if bt else float("nan"), rr))
        summary.append(dict(scale=s, cells=len(v),
                            down_frac=sum(1 for x in d if x < 0) / len(d),
                            median_dN=float(np.median(d)),
                            beats_null=float(np.mean(bt)) if bt else None,
                            spearman_vs_bge=float(rr)))
    os.makedirs(rundir, exist_ok=True)
    with open(os.path.join(rundir, "rated_contextual.jsonl"), "w") as fh:
        for r in out:
            fh.write(json.dumps(r) + "\n")
    json.dump(dict(_what="contextual slot_ratings run through displacement_axis's "
                         "own statistic, for comparison with bge (dN_position) and "
                         "k_ratings (rated.jsonl)", summary=summary),
              open(os.path.join(rundir, "rated_contextual_summary.json"), "w"), indent=1)
    print("\n-> results/%s/rated_contextual.jsonl (%d cells)" % (a.run, len(out)))


if __name__ == "__main__":
    main()
