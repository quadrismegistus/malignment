"""Rate enough of each frame's vocabulary to cover 99% of its mass.

    python experiments/slot_ratings/corpus_full.py            # all 303, resumable
    python experiments/slot_ratings/corpus_full.py --sizing   # what it would cost

## WHY MASS COVERAGE, NOT "THE FULL VOCABULARY"

The point of this run is to let a rated scale stand where the bge axis stands in
`displacement_axis`. That statistic is MASS-WEIGHTED --
`N = sum p(w) r(w) / sum p(w)` -- so an unrated word costs coverage in
proportion to its probability, and the tail costs almost nothing. Measured on a
40-frame sample, words needed per frame:

     90% of mass   179   ->  54,320 words   $2.72
     95% of mass   262   ->  79,310 words   $3.97
     99% of mass   373   -> 112,981 words   $5.65
    100% of mass   545   -> 165,097 words   $8.25

The last 1% costs another 172 words per frame for nothing a mass-weighted mean
can feel. **99% is the stopping point and it is a declared choice, not a
budget.**

The population here is DELIBERATELY not the eligibility population used by
`run.py`. That one exists so a word could have moved either way under CANONICAL
and is right for a correlation against the mover verdict. This one exists to
cover mass and is right for a centroid. Same corpus, two populations, different
statistics -- do not read a rho from one against an N from the other.

## WHAT THIS BUYS, MEASURED BEFORE RUNNING

On the eligible-word ratings alone (median 59.4% of arm mass), the named scales
already track the bge axis across 5,579 cells:

    dN_mundanity    vs dN_position   rho -0.673
    dN_makes_worse  vs dN_position   rho +0.648
    dN_harm         vs dN_position   rho +0.475

against +0.545 for `rated.py`'s type-level `transgressiveness`. So a CONTEXTUAL
scale at 59% coverage beats a type-level one at 99.5% coverage, and the axis
acquires a name: the declared naughty/nice direction is mostly mundanity,
makes_worse and harm.

**And `dN_fit` is -0.030 -- orthogonal.** `fit` is the most consistent effect in
the corpus (21 of 21 pairs, p=9.5e-07) and the bge axis cannot see it at all.
displacement_axis records `r2` at 0.369 and says two thirds of the movement in
displacement cells is uncharacterised; this is a candidate for part of it, and it
only appeared because the scale was NAMED rather than derived from the poles.

## NO POS FILTER HERE

`run.py` keeps NOUN/VERB/ADJ/ADV because a correlation over function words is
noise. A centroid needs the mass wherever it sits, so everything is rated and
`ratable: false` rows are reported as uncovered rather than dropped silently.
POS is still tagged, as metadata.
"""

import argparse, collections, json, os, sys, time
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
OUT = os.path.join(HERE, "results", "v6full")
CELLS = os.path.join(os.path.dirname(HERE), "displacement_axis",
                     "results", "pilot3", "cells.jsonl")
TARGET = 0.99


def frames():
    cells = [json.loads(l) for l in open(CELLS, encoding="utf-8")]
    by = collections.defaultdict(list)
    for c in cells:
        by[c["item_id"]].append(c)
    return sorted(by.items(), key=lambda kv: -len(kv[1]))


def vocab(mine, target=TARGET):
    """Words carrying `target` of the union mass, biggest first."""
    from malignment import vectors as V
    ms = sorted({c["base"] for c in mine} | {c["endpoint"] for c in mine})
    q = V.rows("SELECT model, groupArray(word) AS ws, groupArray(p) AS ps "
               "FROM twp_words_v4_best WHERE prompt={p:String} "
               "AND model IN {ms:Array(String)} GROUP BY model",
               p=mine[0]["prompt"], ms=ms)
    mass = collections.defaultdict(float)
    for r in q:
        for w, p in zip(r["ws"], r["ps"]):
            mass[w] = max(mass[w], p)          # union mass: the arm that holds it most
    tot = sum(mass.values()) or 1.0
    out, run = [], 0.0
    for w, p in sorted(mass.items(), key=lambda kv: -kv[1]):
        out.append(w); run += p
        if run / tot >= target:
            break
    return out, len(mass)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizing", action="store_true")
    ap.add_argument("--limit", type=int)
    a = ap.parse_args(argv)
    os.makedirs(OUT, exist_ok=True)
    fs = frames()
    todo = [(i, m) for i, m in fs
            if not os.path.exists(os.path.join(OUT, "rated_%s.json" % i))]
    print("frames: %d total, %d done, %d to run" % (len(fs), len(fs) - len(todo), len(todo)))
    if a.limit:
        todo = todo[:a.limit]
    if a.sizing:
        n = [len(vocab(m)[0]) for _, m in todo[:20]]
        print("  median %d words/frame -> ~%d words, $%.2f"
              % (st.median(n), st.mean(n) * len(todo), st.mean(n) * len(todo) * 0.00005))
        return

    from task import SlotRatingENv6, SCALES_V6, render
    from malignment.pos import get_pos
    t = SlotRatingENv6()
    t0 = time.time()
    for n, (iid, mine) in enumerate(todo, 1):
        try:
            words, total = vocab(mine)
            pos = get_pos(words, mine[0]["prompt"])
            errs = {}
            res = t.map([render(mine[0]["prompt"], w) for w in words],
                        metadata_list=[{"prompt": mine[0]["prompt"], "word": w}
                                       for w in words],
                        num_workers=32, errors=errs)
            out = []
            for w, r in zip(words, res):
                d = dict(word=w, pos=pos.get(w, "X"), prompt=mine[0]["prompt"],
                         item_id=iid)
                if r is not None:
                    d["ratable"], d["reading"] = r.ratable, r.reading
                    for s in SCALES_V6:
                        d[s] = getattr(r, s)
                out.append(d)
            json.dump(out, open(os.path.join(OUT, "rated_%s.json" % iid), "w"))
            el = time.time() - t0
            print("  [%d/%d] %-30s %4d of %4d words, %d err  (%.0fs, %.0fs/frame)"
                  % (n, len(todo), iid[:30], len(words), total, len(errs), el, el / n),
                  flush=True)
        except Exception as e:
            print("  [%d/%d] %-30s FAILED %s: %s"
                  % (n, len(todo), iid[:30], type(e).__name__, str(e)[:70]), flush=True)


if __name__ == "__main__":
    main()
