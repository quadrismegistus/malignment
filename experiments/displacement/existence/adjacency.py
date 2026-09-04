"""Does freed mass land on semantically adjacent words (displacement) or scatter?

    python -u adjacency.py

## THE TEST

For each cell, take the top faller and note its `kind` (SEXUAL, VIOLENT, etc).
Among the risers in the same cell, split them:

    same-kind     risers sharing the faller's kind (semantic neighbours)
    diff-kind     risers with a different non-NONE kind
    none-kind     risers tagged NONE (non-transgressive)

Displacement predicts same-kind risers gain MORE than diff/none risers —
the charge redirects within the same domain. Diffusion predicts no difference.
Suppression predicts none-kind risers gain most (mass moves to neutral words).

Unit is the lineage. Within each lineage, compare mean delta of same-kind
vs none-kind risers across prompts. Sign-test: do more lineages show
same-kind > none-kind?
"""

import collections
import math
import os
import sys
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))


def binom(k, n):
    if not n:
        return float("nan")
    return min(1.0, 2 * sum(math.comb(n, j)
               for j in range(0, min(k, n - k) + 1)) / 2.0 ** n)


def measure(frame="raw", match_framed=False):
    from malignment import ch, charge, roster

    eps, unresolved = roster.endpoints()
    if unresolved:
        raise SystemExit("unresolved lineages: %s" % sorted(unresolved)[:3])

    #: same two flags as `run.py`, same reasons. The framed contrast is
    #: base_raw -> aligned_framed and is ASYMMETRIC -- 43 of 50 bases ship no
    #: chat template, so it is the deployed arm against the bare one.
    #: `clean_slot` is not optional: `frame_aligned='prefill'` alone mixes empty
    #: system slots with personas and date blocks, because `system_mode` records
    #: the argument passed and not the treatment received.
    mode_of = {}
    if match_framed or frame != "raw":
        from malignment import movement as M
        mode_of = {(b, a): m for b, a, m in M.clean_frame_pairs()
                   if eps.get(b) == a}
        eps = {b: a for b, a in eps.items() if (b, a) in mode_of}

    print("ADJACENCY: does freed mass land on same-kind words (displacement)")
    print("           or scatter to unrelated words (diffusion/suppression)?")
    print("           %d lineages  [frame=%s]" % (len(eps), frame))
    if frame != "raw":
        print("           base_raw -> aligned_framed, clean system slot only")
    print()

    scenes_cache = {}
    kinds_cache = {}
    def get_ratings(prompt):
        if prompt not in scenes_cache:
            scenes_cache[prompt] = charge.scene(prompt)
            kinds_cache[prompt] = charge.kinds(prompt)
        return scenes_cache[prompt], kinds_cache[prompt]

    # per lineage: collect (same_kind_delta, none_kind_delta) pairs per cell
    by_lin = collections.defaultdict(lambda: {
        "same_deltas": [], "diff_deltas": [], "none_deltas": [],
        "same_scenes": [], "diff_scenes": [], "none_scenes": [],
        "n_cells": 0,
    })

    for b, a in sorted(eps.items()):
        lin = b + ">" + a
        rows = ch.query(
            "SELECT prompt, word, p_base, p_aligned, "
            "(p_aligned - p_base) AS delta, cls "
            "FROM {db}.movement_v4 "
            "WHERE base='%s' AND aligned='%s' "
            "AND frame_base = '' AND %s"
            % (b.replace("'", "\\'"), a.replace("'", "\\'"),
               "frame_aligned = ''" if frame == "raw" else
               ("frame_aligned = 'prefill' AND system_mode_aligned = '%s'"
                % mode_of[(b, a)])),
            limit_bytes=None)

        cells = collections.defaultdict(list)
        for r in rows:
            cells[r["prompt"]].append(r)

        for prompt, word_rows in cells.items():
            sc, kd = get_ratings(prompt)
            if not sc or not kd:
                continue

            fallers = [(r["word"], float(r["delta"]), float(r["p_base"]))
                       for r in word_rows if r["cls"] == "faller"
                       and r["word"] in kd]
            if not fallers:
                continue
            top_faller = max(fallers, key=lambda x: -x[1])
            faller_kind = kd.get(top_faller[0])
            if not faller_kind or faller_kind == "NONE":
                continue

            risers = [(r["word"], float(r["delta"]))
                      for r in word_rows if r["cls"] == "riser"
                      and r["word"] in kd]
            if not risers:
                continue

            same, diff, none = [], [], []
            same_sc, diff_sc, none_sc = [], [], []
            for w, d in risers:
                k = kd.get(w, "NONE")
                s = sc.get(w, 0)
                if k == faller_kind:
                    same.append(d)
                    same_sc.append(s)
                elif k == "NONE":
                    none.append(d)
                    none_sc.append(s)
                else:
                    diff.append(d)
                    diff_sc.append(s)

            if same and none:
                rec = by_lin[lin]
                rec["same_deltas"].append(sum(same) / len(same))
                rec["none_deltas"].append(sum(none) / len(none))
                rec["same_scenes"].append(sum(same_sc) / len(same_sc))
                rec["none_scenes"].append(sum(none_sc) / len(none_sc))
                rec["n_cells"] += 1
                if diff:
                    rec["diff_deltas"].append(sum(diff) / len(diff))
                    rec["diff_scenes"].append(sum(diff_sc) / len(diff_sc))

    # --- sign test: same-kind vs none-kind mean delta ---
    print("  cells with rated top-faller (non-NONE) + both same-kind and")
    print("  none-kind risers: %d across %d lineages"
          % (sum(r["n_cells"] for r in by_lin.values()), len(by_lin)))
    print()

    # same vs none: does same-kind gain more?
    same_wins = 0
    none_wins = 0
    for lin, rec in sorted(by_lin.items()):
        if rec["n_cells"] < 10:
            continue
        med_same = st.median(rec["same_deltas"])
        med_none = st.median(rec["none_deltas"])
        if med_same > med_none:
            same_wins += 1
        elif med_none > med_same:
            none_wins += 1

    n = same_wins + none_wins
    p = binom(min(same_wins, none_wins), n)
    print("  SAME-KIND vs NONE-KIND risers (median delta per lineage)")
    print("  %-45s %d" % ("lineages where same-kind risers gain MORE:", same_wins))
    print("  %-45s %d" % ("lineages where none-kind risers gain MORE:", none_wins))
    print("  %-45s %.6f" % ("sign test p:", p))
    print()

    if same_wins > none_wins:
        print("  DISPLACEMENT: freed mass preferentially lands on same-kind words.")
        print("  The charge redirects within the semantic domain.")
    elif none_wins > same_wins:
        print("  SUPPRESSION: freed mass preferentially lands on NONE words.")
        print("  The charge is extinguished, not redirected.")
    else:
        print("  NULL: no preference between same-kind and none-kind risers.")

    # --- scene ratings of the three groups ---
    print()
    print("  --- mean scene ratings of the three riser groups ---")
    all_same_sc = [s for r in by_lin.values() for s in r["same_scenes"]]
    all_diff_sc = [s for r in by_lin.values() for s in r["diff_scenes"]]
    all_none_sc = [s for r in by_lin.values() for s in r["none_scenes"]]
    if all_same_sc:
        print("  same-kind risers:  scene %.3f  (n=%d cells)"
              % (st.median(all_same_sc), len(all_same_sc)))
    if all_diff_sc:
        print("  diff-kind risers:  scene %.3f  (n=%d cells)"
              % (st.median(all_diff_sc), len(all_diff_sc)))
    if all_none_sc:
        print("  none-kind risers:  scene %.3f  (n=%d cells)"
              % (st.median(all_none_sc), len(all_none_sc)))

    # --- same vs none: delta magnitudes ---
    print()
    print("  --- median delta (mass gained) by riser group ---")
    all_same_d = [d for r in by_lin.values() for d in r["same_deltas"]]
    all_diff_d = [d for r in by_lin.values() for d in r["diff_deltas"]]
    all_none_d = [d for r in by_lin.values() for d in r["none_deltas"]]
    if all_same_d:
        print("  same-kind risers:  delta %+.6f  (n=%d)" % (st.median(all_same_d), len(all_same_d)))
    if all_diff_d:
        print("  diff-kind risers:  delta %+.6f  (n=%d)" % (st.median(all_diff_d), len(all_diff_d)))
    if all_none_d:
        print("  none-kind risers:  delta %+.6f  (n=%d)" % (st.median(all_none_d), len(all_none_d)))

    return 0


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--frame", default="raw", choices=("raw", "prefill"))
    ap.add_argument("--match-framed", action="store_true",
                    help="run RAW on the framed population, so the two are the "
                         "same pairs and a difference is not partly which labs "
                         "ship a chat template")
    a = ap.parse_args(argv)
    return measure(frame=a.frame, match_framed=a.match_framed)


if __name__ == "__main__":
    sys.exit(main())
