"""Is alignment's reshaping of word probabilities content-selective?

    python -u run.py

## THE QUESTION

Alignment changes word probability distributions — JS > 0 between base and
aligned for every pair. That is not a finding; it would be surprising if it
didn't. The question is whether the change is SELECTIVE BY CONTENT: do words
that carry more transgressive charge lose more mass?

## THE TEST

Within each cell (one prompt × one endpoint pair), every candidate word has:

    scene_w     how transgressive the completed sentence is if the model
                says this word (1-7, from charge.py, rated by task_charge)
    delta_w     p_aligned - p_base (from movement_v4)

The test: regress delta on scene within each cell. If displacement is
content-selective, the slope is NEGATIVE — higher-scene words lose more mass.

    unit        the lineage (50 endpoints from roster.endpoints())
    per-cell    OLS slope of delta ~ scene, one per (lineage, prompt)
    aggregate   median slope across prompts, per lineage
    test        sign test: do more lineages have negative median slope?

A null result would mean: alignment reshapes distributions, but which words
move is unrelated to their transgressive content. The reshaping might be
instruction-following, sharpening, or some other non-content-selective process.

## WHAT IS NOT TESTED HERE

- Whether the displacement is LARGE (that's rate_and_magnitude)
- Whether it scales with the frame's transgressiveness (that's dose-response)
- WHERE the freed mass goes (that's tail_excess in rate_and_magnitude)
- What KIND of substitution occurs (that's displacement_taxonomy)

This is the step-1 finding: content predicts which words move.
"""

import argparse
import collections
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))


def binom(k, n):
    if not n:
        return float("nan")
    return min(1.0, 2 * sum(math.comb(n, j)
               for j in range(0, min(k, n - k) + 1)) / 2.0 ** n)


def slope(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx = sum(xs) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx <= 0:
        return None
    my = sum(ys) / n
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx


def measure():
    import statistics as st
    from malignment import ch, charge, roster

    eps, unresolved = roster.endpoints()
    if unresolved:
        raise SystemExit("unresolved lineages: %s" % sorted(unresolved)[:3])

    ep_set = set()
    base_of = {}
    for b, a in eps.items():
        key = b + ">" + a
        ep_set.add(key)
        base_of[key] = b

    print("EXISTENCE: does a word's transgressive charge predict its displacement?")
    print("50 endpoint lineages, per-cell slope of delta ~ scene")
    print()

    by_cell = collections.defaultdict(list)
    for b, a in sorted(eps.items()):
        lin = b + ">" + a
        rows = ch.query(
            "SELECT prompt, word, (p_aligned - p_base) AS delta "
            "FROM {db}.movement_v4 "
            "WHERE base='%s' AND aligned='%s' "
            "AND frame_base = '' AND frame_aligned = ''"
            % (b.replace("'", "\\'"), a.replace("'", "\\'")),
            limit_bytes=None)
        for r in rows:
            by_cell[(lin, r["prompt"])].append((r["word"], float(r["delta"])))

    print("  %d cells across %d lineages" % (len(by_cell), len(ep_set)))

    scenes_cache = {}
    def get_scene(prompt):
        if prompt not in scenes_cache:
            scenes_cache[prompt] = charge.scene(prompt)
        return scenes_cache[prompt]

    slopes_by_lin = collections.defaultdict(list)
    n_cells_rated = 0
    n_words_rated = 0

    for (lin, prompt), word_deltas in by_cell.items():
        sc = get_scene(prompt)
        if not sc:
            continue
        xs, ys = [], []
        for word, delta in word_deltas:
            s = sc.get(word)
            if s is not None:
                xs.append(s)
                ys.append(delta)
        if len(xs) < 3:
            continue
        s = slope(xs, ys)
        if s is not None:
            slopes_by_lin[lin].append(s)
            n_cells_rated += 1
            n_words_rated += len(xs)

    print("  %d cells with >= 3 rated words, %d total word-level observations"
          % (n_cells_rated, n_words_rated))
    print()

    # --- per-lineage median slope ---
    med_slopes = {}
    for lin, ss in slopes_by_lin.items():
        if len(ss) >= 25:
            med_slopes[lin] = st.median(ss)

    neg = sum(1 for v in med_slopes.values() if v < 0)
    pos = sum(1 for v in med_slopes.values() if v > 0)
    n = neg + pos
    p = binom(min(neg, pos), n)
    grand_med = st.median(list(med_slopes.values())) if med_slopes else float("nan")

    print("  SLOPE OF delta ~ scene (within cell)")
    print("  %-40s %s" % ("lineages with negative median slope:", neg))
    print("  %-40s %s" % ("lineages with positive median slope:", pos))
    print("  %-40s %.6f" % ("sign test p:", p))
    print("  %-40s %+.6f" % ("grand median slope:", grand_med))
    print()

    if neg > pos:
        print("  NEGATIVE: higher-scene words lose more mass under alignment.")
        print("  Displacement is content-selective.")
    elif pos > neg:
        print("  POSITIVE: higher-scene words GAIN mass — unexpected.")
    else:
        print("  NULL: no directional relationship between scene and delta.")

    # --- breakdown: fallers vs risers ---
    print()
    print("  --- breakdown by faller/riser status ---")

    for cls_label, cls_filter in [("fallers only", lambda d: d < 0),
                                  ("risers only", lambda d: d > 0)]:
        cls_slopes = collections.defaultdict(list)
        for (lin, prompt), word_deltas in by_cell.items():
            sc = get_scene(prompt)
            if not sc:
                continue
            xs, ys = [], []
            for word, delta in word_deltas:
                if not cls_filter(delta):
                    continue
                s = sc.get(word)
                if s is not None:
                    xs.append(s)
                    ys.append(delta)
            if len(xs) < 3:
                continue
            s = slope(xs, ys)
            if s is not None:
                cls_slopes[lin].append(s)

        cls_meds = {}
        for lin, ss in cls_slopes.items():
            if len(ss) >= 25:
                cls_meds[lin] = st.median(ss)

        cn = sum(1 for v in cls_meds.values() if v < 0)
        cp = sum(1 for v in cls_meds.values() if v > 0)
        ct = cn + cp
        cp_val = binom(min(cn, cp), ct)
        cm = st.median(list(cls_meds.values())) if cls_meds else float("nan")
        print("  %-14s  n=%d  %d neg / %d pos  p=%.6f  med=%+.6f"
              % (cls_label, ct, cn, cp, cp_val, cm))

    # --- effect size: per-word correlation ---
    print()
    all_sc, all_delta = [], []
    for (lin, prompt), word_deltas in by_cell.items():
        sc = get_scene(prompt)
        if not sc:
            continue
        for word, delta in word_deltas:
            s = sc.get(word)
            if s is not None:
                all_sc.append(s)
                all_delta.append(delta)
    if len(all_sc) > 10:
        mx = sum(all_sc) / len(all_sc)
        my = sum(all_delta) / len(all_delta)
        sxx = sum((x - mx) ** 2 for x in all_sc)
        syy = sum((y - my) ** 2 for y in all_delta)
        sxy = sum((x - mx) * (y - my) for x, y in zip(all_sc, all_delta))
        r = sxy / (sxx * syy) ** 0.5 if sxx > 0 and syy > 0 else 0
        print("  pooled word-level correlation(scene, delta): r = %+.4f  n = %s"
              % (r, format(len(all_sc), ",")))
        print("  (pooled across cells; within-cell slopes are the proper test)")

    # --- stratified by dose ---
    print()
    print("  --- stratified by dose (charge.dose) ---")
    print()
    doses = charge.doses()
    dose_bands = [(1, 2, "1-2 (neutral)"),
                  (2, 3, "2-3 (mild)"),
                  (3, 4, "3-4 (moderate)"),
                  (4, 5, "4-5 (strong)"),
                  (5, 7, "5-7 (extreme)")]
    print("  %-16s %5s %6s %8s %10s %10s"
          % ("band", "cells", "lins", "neg/pos", "p", "med slope"))
    for lo, hi, label in dose_bands:
        band_prompts = {p for p, d in doses.items() if lo <= d < hi}
        band_slopes = collections.defaultdict(list)
        band_cells = 0
        for (lin, prompt), word_deltas in by_cell.items():
            if prompt not in band_prompts:
                continue
            sc = get_scene(prompt)
            if not sc:
                continue
            xs, ys = [], []
            for word, delta in word_deltas:
                s = sc.get(word)
                if s is not None:
                    xs.append(s)
                    ys.append(delta)
            if len(xs) < 3:
                continue
            s = slope(xs, ys)
            if s is not None:
                band_slopes[lin].append(s)
                band_cells += 1
        band_meds = {}
        for lin, ss in band_slopes.items():
            if len(ss) >= 10:
                band_meds[lin] = st.median(ss)
        bn = sum(1 for v in band_meds.values() if v < 0)
        bp = sum(1 for v in band_meds.values() if v > 0)
        bt = bn + bp
        bp_val = binom(min(bn, bp), bt) if bt else float("nan")
        bm = st.median(list(band_meds.values())) if band_meds else float("nan")
        print("  %-16s %5d %6d %4d/%-4d %10.6f %+10.6f%s"
              % (label, band_cells, bt, bn, bp, bp_val, bm,
                 "  <-" if bp_val < 0.05 else ""))

    # --- stratified by lift ---
    print()
    print("  --- stratified by lift (charge.lift) ---")
    print()
    all_lifts = charge.lifts()
    lift_bands = [(-2, 0, "< 0 (no lift)"),
                  (0, 0.5, "0-0.5 (low)"),
                  (0.5, 1, "0.5-1 (moderate)"),
                  (1, 2, "1-2 (high)"),
                  (2, 7, "2+ (very high)")]
    print("  %-16s %5s %6s %8s %10s %10s"
          % ("band", "cells", "lins", "neg/pos", "p", "med slope"))
    for lo, hi, label in lift_bands:
        band_prompts = {p for p, lf in all_lifts.items() if lo <= lf < hi}
        band_slopes = collections.defaultdict(list)
        band_cells = 0
        for (lin, prompt), word_deltas in by_cell.items():
            if prompt not in band_prompts:
                continue
            sc = get_scene(prompt)
            if not sc:
                continue
            xs, ys = [], []
            for word, delta in word_deltas:
                s = sc.get(word)
                if s is not None:
                    xs.append(s)
                    ys.append(delta)
            if len(xs) < 3:
                continue
            s = slope(xs, ys)
            if s is not None:
                band_slopes[lin].append(s)
                band_cells += 1
        band_meds = {}
        for lin, ss in band_slopes.items():
            if len(ss) >= 10:
                band_meds[lin] = st.median(ss)
        bn = sum(1 for v in band_meds.values() if v < 0)
        bp = sum(1 for v in band_meds.values() if v > 0)
        bt = bn + bp
        bp_val = binom(min(bn, bp), bt) if bt else float("nan")
        bm = st.median(list(band_meds.values())) if band_meds else float("nan")
        print("  %-16s %5d %6d %4d/%-4d %10.6f %+10.6f%s"
              % (label, band_cells, bt, bn, bp, bp_val, bm,
                 "  <-" if bp_val < 0.05 else ""))

    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.parse_args(argv)
    return measure()


if __name__ == "__main__":
    sys.exit(main())
