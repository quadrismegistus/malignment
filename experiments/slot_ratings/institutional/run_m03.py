"""Rate M03/F21 speaker-kernel prompts, using the PRECOMPUTED `movement` table.

    python experiments/slot_ratings/run_m03.py --scenario m03_N1
    python experiments/slot_ratings/run_m03.py --scenario m03_N1 --dry

## WHY A SEPARATE RUNNER FROM run.py

`run.py` reads `displacement_axis/results/pilot3/cells.jsonl` for its pairs and
calls `movement.movement()` per cell. Neither applies here:

  - **The pairs come from `roster.endpoints()`, 50 of them** (RH, 2026-08-19),
    not from pilot3's 21. The `movement` table holds 153 pairs on these prompts;
    153 includes intermediate checkpoints and cross-family pairings, and the
    declared endpoint set is the population.
  - **Movement is already computed.** `movement` is 56.3M rows at rule
    `canonical`, theta 0.001, with `cls` in still/faller/riser. Computing it
    again on the fly would be a second implementation of the same rule.
  - **v4 does not cover these prompts at pair depth.** All 252 M03 prompts are in
    `twp_words_v4_best`, but only 22 models -- so very few endpoint PAIRS have
    both arms. `twp_words` has 406 models and `movement` has all 50 endpoint
    pairs on all 252 prompts. Prompt presence is not pair presence.

## THE DESIGN THIS BUYS

M03's kernel is 18 scenarios x 14 cells, crossing:

    POSITION  indiv | inst        the same scene from the other side
    PERSON    I | we
    MODAL     absent | final | final_ought | medial

and `medial` == final + " probably" (m03_kernel.py:25-27, asserted not inferred).
So `final` against `medial` is one added word at the same grammatical site, while
`absent` sits at a FINITE VERB slot rather than a bare infinitive -- an
absent-vs-modal difference is partly a fact about English and is not the hedge
contrast.

M03 finding A: the hedge moves alignment's valence shift by **+0.207** against
**+0.077** for the whole individual/institutional contrast. The larger factor is
the one nobody reported, so any position result here must be read beside it.

## THE UNIT IS THE PAIR

rho(rating, verdict) within each pair over that pair's eligible words, then
Wilcoxon across pairs. Verdict is the table's own `cls`: +1 riser, -1 faller,
0 still. Not a raw delta -- that would discard the renormalisation null that
makes a riser a riser, and `movement.py` states that nothing downstream may
describe fallers as "beyond renormalisation" since a faller is a bare ratio.
"""

import argparse, collections, json, os, sys
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
SLOT = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(SLOT))
sys.path.insert(0, HERE); sys.path.insert(0, REPO)
RESULTS = os.path.join(HERE, "results", "m03")
KERNEL = ("/Users/rj416/github/malign-logits/meta/M03_proceduralization/"
          "m03_kernel_full.json")
MIN_PROB = 0.003          # CANONICAL's faller gate; below it net is censored
CONTENT_POS = ("NOUN", "VERB", "ADJ", "ADV")


def kernel(scenario=None):
    k = json.load(open(KERNEL))
    items = k if isinstance(k, list) else list(k.values())[0]
    out = []
    for sc in items:
        if scenario and sc["scenario_id"] != scenario:
            continue
        cells = sc["cells"]
        for cid, txt in (cells if isinstance(cells, list) else cells.items()):
            out.append(dict(scenario=sc["scenario_id"], domain=sc.get("domain"),
                            cell=cid, prompt=txt))
    return out


def population(prompts, min_pairs=3, arm="A"):
    """Content words per prompt with each pair's verdict, for ONE arm.

    **THE TWO ARMS ARE DIFFERENTLY GATED AND ARE NEVER POOLED.**

        arm A   p_base >= MIN_PROB                    a word can FALL
        arm B   p_base < MIN_PROB, p_aligned >= MIN_PROB   a word can only RISE

    CANONICAL gates FALLERS on base mass (min_prob 0.003); risers have no such
    condition, being tested against the renormalisation null instead. Gating the
    population on p_base alone therefore imposes the faller condition on both
    directions -- symmetric, and wrong for a corpus whose effect is words
    ARRIVING from nothing.

    Measured on m03_N1 before this was added: M03 finding E's 21 managerial
    risers have mean p_base 0.00040 and clear min_prob in **6%** of cells, while
    its concrete fallers sit at 0.00397 and clear it in 47%. `assess`, `ensure`,
    `communicate`, `initiate` and `establish` clear it in ZERO cells -- yet
    `document` is called a riser 112 times, `inform` 74, `prioritize` 53. **The
    symmetric gate could not see the effect M03 found at all.**

    Arm B's gate is the MIRROR of arm A's, not a relaxation: each word is gated
    on the arm where it must carry mass for the movement to be detectable. It is
    not selection on the outcome -- `cls` is never consulted. On m03_N1 it yields
    529 words, 3,388 riser calls and **0 fallers**, which is the gate proving
    itself, and recovers 10 of the 21 M03 risers.

    Arm B's outcome is BINARY (riser / not), so its statistic is a
    riser-vs-still correlation and is not comparable to arm A's signed one.
    Report them side by side, never summed.
    """
    from malignment import roster, vectors as V
    from malignment.pos import get_pos
    ep = sorted(roster.endpoints()[0].items())
    gate = ("p_base >= {mp:Float64}" if arm == "A" else
            "p_base < {mp:Float64} AND p_aligned >= {mp:Float64}")
    rows = V.rows(
        "SELECT prompt, word, base, aligned, cls, p_base FROM movement "
        "WHERE prompt IN {ps:Array(String)} "
        "AND (base, aligned) IN {bs:Array(Tuple(String,String))} AND " + gate,
        ps=sorted(prompts), bs=ep, mp=MIN_PROB)
    by = collections.defaultdict(lambda: collections.defaultdict(dict))
    npairs = collections.defaultdict(collections.Counter)
    for r in rows:
        pk = (r["base"], r["aligned"])
        by[r["prompt"]][pk][r["word"]] = (
            1 if r["cls"] == "riser" else -1 if r["cls"] == "faller" else 0)
        npairs[r["prompt"]][r["word"]] += 1
    out = {}
    for p in prompts:
        words = sorted(w for w, n in npairs[p].items() if n >= min_pairs)
        pos = get_pos(words, p) if words else {}
        out[p] = dict(words=[w for w in words if pos.get(w) in CONTENT_POS],
                      pos=pos, verdicts=by[p])
    return out


def rate(task, render, scales, cells, pop, workers=32):
    jobs = [(c["prompt"], w) for c in cells for w in pop[c["prompt"]]["words"]]
    if not jobs:
        return {}, 0
    errs = {}
    res = task.map([render(p, w) for p, w in jobs],
                   metadata_list=[{"prompt": p, "word": w} for p, w in jobs],
                   num_workers=workers, errors=errs)
    rat = collections.defaultdict(dict)
    for (p, w), r in zip(jobs, res):
        if r is not None and r.ratable:
            rat[p][w] = {s: getattr(r, s) for s in scales}
    return rat, len(errs)


def per_pair_rho(cells, pop, rat, scales, arm):
    """rho(rating, outcome) within each pair. Arm A signed, arm B binary."""
    from scipy import stats
    out = {}
    for c in cells:
        p = c["prompt"]
        per = collections.defaultdict(list)
        for pk, vd in pop[p]["verdicts"].items():
            e = [w for w in rat.get(p, {}) if w in vd]
            if len(e) < 10:
                continue
            mv = [vd[w] for w in e]          # arm B is already {0, 1} by its gate
            if len(set(mv)) < 2:
                continue
            for s in scales:
                xs = [rat[p][w][s] for w in e]
                if len(set(xs)) < 2:
                    continue
                r = stats.spearmanr(xs, mv).correlation
                if r == r:
                    per[s].append(r)
        out[c["cell"]] = per
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", default="m03_N1")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--v6", action="store_true",
                    help="the fiction instrument instead of the institutional "
                         "one. Smoked and largely inert here: harm 1 for all 18 "
                         "words, fit 6-7, interiority 2-3, mundanity 4-5.")
    a = ap.parse_args(argv)
    cells = kernel(a.scenario)
    if not cells:
        raise SystemExit("no cells for %r" % a.scenario)

    pops = {arm: population([c["prompt"] for c in cells], arm=arm)
            for arm in ("A", "B")}
    print("scenario %s (%s): %d cells, %d pairs"
          % (a.scenario, cells[0]["domain"], len(cells),
             len(pops["A"][cells[0]["prompt"]]["verdicts"])))
    print("  %-20s %8s %8s" % ("cell", "arm A", "arm B"))
    for c in cells:
        print("  %-20s %8d %8d"
              % (c["cell"], len(pops["A"][c["prompt"]]["words"]),
                 len(pops["B"][c["prompt"]]["words"])))
    tot = sum(len(pops[x][c["prompt"]]["words"]) for x in "AB" for c in cells)
    print("  total to rate: %d" % tot)
    if a.dry:
        return

    if a.v6:
        from task import SlotRatingENv6 as T, SCALES_V6 as SCALES, render as R
    else:
        if os.environ.get("INST_V3"):
            from task import (InstitutionalSupplementENv3 as T,
                              SCALES_INST_V3 as SCALES, render as R)
        else:
            from task import (InstitutionalSupplementEN as T,
                              SCALES_INST as SCALES, render as R)
    task = T()
    os.makedirs(RESULTS, exist_ok=True)
    for arm in ("A", "B"):
        rat, nerr = rate(task, R, SCALES, cells, pops[arm])
        print("\narm %s: rated %d cells, errors %d"
              % (arm, len(rat), nerr))
        json.dump({"scenario": a.scenario, "arm": arm, "instrument": task.name,
                   "cells": [dict(c, ratings=rat.get(c["prompt"], {})) for c in cells]},
                  open(os.path.join(RESULTS, "rated_%s_%s_arm%s.json"
                                    % (task.name, a.scenario, arm)), "w"), indent=1)
        rho = per_pair_rho(cells, pops[arm], rat, SCALES, arm)
        head = "signed verdict (+1 riser / -1 faller / 0)" if arm == "A" else \
               "BINARY riser-vs-still -- NOT comparable to arm A"
        print("  per-pair rho against %s" % head)
        print("  %-20s %s" % ("cell", " ".join("%5s" % s[:5] for s in SCALES)))
        for c in cells:
            per = rho[c["cell"]]
            row = []
            for s in SCALES:
                v = per[s]
                if len(v) < 6:
                    row.append("%5s" % "--"); continue
                from scipy import stats as _st
                pv = _st.wilcoxon(v).pvalue
                row.append("%+5.2f%s" % (st.median(v), "*" if pv < 0.05 else " "))
            print("  %-20s %s" % (c["cell"], " ".join(row)))


if __name__ == "__main__":
    main()
