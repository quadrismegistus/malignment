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
REPO = os.path.dirname(os.path.dirname(HERE))
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


def population(prompts, min_pairs=3):
    """Eligible content words per prompt, with each pair's verdict."""
    from malignment import roster, vectors as V
    from malignment.pos import get_pos
    ep = sorted(roster.endpoints()[0].items())
    rows = V.rows(
        "SELECT prompt, word, base, aligned, cls, p_base FROM movement "
        "WHERE prompt IN {ps:Array(String)} "
        "AND (base, aligned) IN {bs:Array(Tuple(String,String))} "
        "AND p_base >= {mp:Float64}",
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


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", default="m03_N1")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args(argv)
    cells = kernel(a.scenario)
    if not cells:
        raise SystemExit("no cells for %r" % a.scenario)
    pop = population([c["prompt"] for c in cells])
    print("scenario %s (%s): %d cells" % (a.scenario, cells[0]["domain"], len(cells)))
    for c in cells:
        p = pop[c["prompt"]]
        print("  %-20s %4d content words, %2d pairs"
              % (c["cell"], len(p["words"]), len(p["verdicts"])))
    if a.dry:
        return

    from task import SlotRatingENv6, SCALES_V6, render
    from scipy import stats
    t = SlotRatingENv6()
    jobs = [(c["prompt"], w) for c in cells for w in pop[c["prompt"]]["words"]]
    print("\nrating %d (prompt, word) pairs" % len(jobs))
    errs = {}
    res = t.map([render(p, w) for p, w in jobs],
                metadata_list=[{"prompt": p, "word": w} for p, w in jobs],
                num_workers=32, errors=errs)
    print("errors: %d" % len(errs))
    rat = collections.defaultdict(dict)
    for (p, w), r in zip(jobs, res):
        if r is not None and r.ratable:
            rat[p][w] = {s: getattr(r, s) for s in SCALES_V6}
    os.makedirs(RESULTS, exist_ok=True)
    json.dump({"scenario": a.scenario,
               "cells": [dict(c, ratings=rat[c["prompt"]]) for c in cells]},
              open(os.path.join(RESULTS, "rated_%s.json" % a.scenario), "w"), indent=1)

    print("\nPER-PAIR rho(rating, verdict), Wilcoxon across pairs")
    print("  %-20s %s" % ("cell", " ".join("%6s" % s[:6] for s in SCALES_V6)))
    for c in cells:
        p = c["prompt"]
        per = collections.defaultdict(list)
        for pk, vd in pop[p]["verdicts"].items():
            e = [w for w in rat[p] if w in vd]
            if len(e) < 10:
                continue
            mv = [vd[w] for w in e]
            if len(set(mv)) < 2:
                continue
            for s in SCALES_V6:
                xs = [rat[p][w][s] for w in e]
                if len(set(xs)) < 2:
                    continue
                r = stats.spearmanr(xs, mv).correlation
                if r == r:
                    per[s].append(r)
        row = []
        for s in SCALES_V6:
            v = per[s]
            if len(v) < 6:
                row.append("%6s" % "--"); continue
            pv = stats.wilcoxon(v).pvalue
            row.append("%+6.2f%s" % (st.median(v), "*" if pv < 0.05 else " "))
        print("  %-20s %s   (%d pairs)" % (c["cell"], " ".join(row),
                                           max((len(v) for v in per.values()), default=0)))


if __name__ == "__main__":
    main()
