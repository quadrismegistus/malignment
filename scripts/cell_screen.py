#!/usr/bin/env python
"""Screen the v4 corpus for cells that measured nothing, and for models whose
distributions sit at an extreme.

    python scripts/cell_screen.py              # both screens
    python scripts/cell_screen.py --dead       # the empty-cell screen only
    python scripts/cell_screen.py --shape      # the distribution screen only
    python scripts/cell_screen.py --json out.json

## WHY THIS EXISTS

`tiiuae/Falcon-H1-7B-Base` and `-Instruct` wrote 2,981 cells each with 100% of
the probability mass in `tail`: no token cleared theta as a word start, the beam
expanded nothing, and zero word rows were emitted. Every guard passed.

**`conservation == 1.0` held exactly on all 2,981 cells, because a cell that
measured nothing sums perfectly.** The check that exists to catch a bad cell is a
SUM, and 100% tail satisfies `words + tail + drop + open + mojibake == 1.0` as
well as any healthy cell does. Byte verification passed, the DONE marker was
written, and `topup_todo` returned 0 prompts -- which reads as "complete" and
meant "empty". An empty union and an identical union are the same number.

Docket [6479] [6480] [6481] [6486] [6488]. Cause: `Falcon-H1 7B x mamba kernels`,
established across a 2x2 and awaiting a reproduction on a second box.

## THE TWO SCREENS ANSWER DIFFERENT QUESTIONS AND ONLY ONE IS A VERDICT

**`--dead` is a verdict.** A cell at `tail >= 0.999` measured nothing. The
separation is not a tuned threshold: over 400,786 healthy cells the worst is
0.994748 and every dead cell is exactly 1.000000, a margin of 0.005252.

**`--shape` is a POINTER, never a verdict.** It ranks models by mean entropy and
top-1 mass over their word distributions. It has NO power to prove a distribution
correct; it says where to point a load. It exists because `--dead` catches an
EMPTY distribution and cannot see a subtly wrong one, which is the limit @malign
named, and because four models documented as requiring bf16 were measured at
float16 and "looks fine" was a state nobody had checked.

**Read the shape screen against the base->aligned change, not against the raw
rank.** Alignment lowers slot entropy and that is established, so an aligned arm
sitting low is the expected result and not a finding. The screen prints the
per-lineage change for exactly this reason.

## What it does not do

It does not read `twp_cells_v4` or the v3 tables. On 2026-08-21 three seats in
one day reached for the wrong store and two had a correction half written before
noticing, so every table this touches is named in its own output.
"""

import argparse, json, os, sys
import statistics as S

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CELLS = "twp_cells_v4_best"
WORDS = "twp_words_v4_best"
#: Pass 1 only. Kept as a named constant because the `--fill` screen prints both
#: populations side by side; see the docstring on `fill()` for why that is not
#: redundancy.
WORDS_P1 = "twp_words_v4"
#: A surface that is nothing but form punctuation. Stored surfaces carry NO
#: leading space -- `'kill'`, not `' kill'` -- and a pattern written for the
#: spaced form matches nothing and returns a confident zero.
FILL_RE = r"^[_\\-.=]+$"
#: A cell at or above this measured nothing. Not tuned: the worst healthy cell in
#: a 400,786-cell corpus sits at 0.994748 and every dead one is exactly 1.0.
DEAD = 0.999


def _rows(q):
    from malignment import ch
    r = ch.query(q)
    rows = r.result_rows if hasattr(r, "result_rows") else r
    return [dict(x) if not isinstance(x, dict) else x for x in rows]


def dead():
    """Models and cells whose mass went entirely to tail."""
    per_model = _rows(
        "SELECT model, count() AS cells, round(avg(tail),4) AS mean_tail, "
        "countIf(tail >= %s) AS dead_cells FROM %s GROUP BY model ORDER BY mean_tail DESC"
        % (DEAD, CELLS))
    bad = [r for r in per_model if r["dead_cells"]]
    ok = [r for r in per_model if not r["dead_cells"]]
    print("EMPTY-CELL SCREEN  [%s]  tail >= %s" % (CELLS, DEAD))
    print("  %d models, %d cells" % (len(per_model), sum(r["cells"] for r in per_model)))
    if bad:
        print("  DEAD -- these measured nothing and every sum-based guard passes them:")
        for r in bad:
            print("    %-42s %5d of %5d cells  mean_tail %.4f"
                  % (r["model"], r["dead_cells"], r["cells"], r["mean_tail"]))
    else:
        print("  no dead cells anywhere")
    if ok:
        t = [r["mean_tail"] for r in ok]
        print("  healthy population: mean_tail %.4f (min %.4f, max %.4f) over %d models"
              % (S.mean(t), min(t), max(t), len(ok)))
    return {"dead_models": [r["model"] for r in bad], "per_model": per_model}


def shape(top=6):
    """Entropy and top-1 mass per model, and the base->aligned change per lineage."""
    from malignment import roster
    #: `p > 0` because log2(0) is -inf and one such row makes a model's whole
    #: mean null -- which reads as a missing model rather than as a bad row.
    per = _rows(
        "SELECT model, count() AS cells, round(avg(top1),4) AS top1, "
        "round(avg(H),4) AS H FROM (SELECT model, prompt, max(p) AS top1, "
        "-sum(p*log2(p)) AS H FROM %s WHERE p > 0 GROUP BY model, prompt) "
        "GROUP BY model ORDER BY H ASC" % WORDS)
    per = [r for r in per if r["H"] is not None]
    H = [r["H"] for r in per]
    mH, sH = S.mean(H), S.pstdev(H)
    print("\nDISTRIBUTION SHAPE  [%s]  -- A POINTER, NOT A VERDICT" % WORDS)
    print("  %d models with words | entropy %.3f +- %.3f" % (len(per), mH, sH))
    print("  lowest entropy (most peaked):")
    for r in per[:top // 2]:
        print("    %-42s H %.3f  top1 %.3f" % (r["model"], r["H"], r["top1"]))
    print("  highest entropy (flattest):")
    for r in per[-(top // 2):]:
        print("    %-42s H %.3f  top1 %.3f" % (r["model"], r["H"], r["top1"]))

    E = {r["model"]: r["H"] for r in per}
    ep, _ = roster.endpoints()
    pairs = sorted(((b, a, E[b], E[a], E[a] - E[b]) for b, a in ep.items()
                    if b in E and a in E), key=lambda t: t[4])
    d = [t[4] for t in pairs]
    print("\n  base -> aligned entropy change, %d complete lineages" % len(pairs))
    print("    mean %+.3f  median %+.3f  sd %.3f  falls in %d of %d"
          % (S.mean(d), S.median(d), S.pstdev(d), sum(1 for x in d if x < 0), len(d)))
    print("    largest falls:")
    for b, a, eb, ea, dd in pairs[:top // 2]:
        print("      %-40s %.3f -> %.3f  %+.3f" % (a, eb, ea, dd))
    print("\n  A LOW ALIGNED ARM IS THE EXPECTED RESULT, not a finding. Read a model")
    print("  against this distribution, and treat any rank as a place to point a")
    print("  load rather than as evidence the distribution is wrong.")
    return {"per_model": per, "entropy_change": [
        {"base": b, "aligned": a, "H_base": eb, "H_aligned": ea, "delta": dd}
        for b, a, eb, ea, dd in pairs]}


def fill(threshold=0.25, top=8):
    """Cells where the model answers with a BLANK TO FILL rather than a word.

    `She was so angry she wanted to` puts 72% of Olmo-3-DPO's word mass on
    underscores; its base puts 0.6%. The model is reading the fragment as a
    fill-in-the-blank exercise. Docket [6495] [6496] [6497] [6498] [6499] [6500].

    THE TRIGGER IS STEM SHAPE, NOT CONTENT. `The capital of France is` draws the
    same response from 8 models and has no transgressive content at all, while
    `Let's kill these` is at 0.0000 on every arm of the Olmo-3 ladder. Base arms
    are as exposed as aligned ones -- the largest single carrier in the corpus is
    `Qwen/Qwen2.5-7B`, a base model.

    ## Why both populations are printed

    A displacement ratio computed on pass 1 alone reads the suppressed word as
    0.00000, because PASS 2 EXISTS TO SCORE THE WORDS A MODEL'S LINEAGE CLEARED
    THAT IT DID NOT -- which for an aligned arm is the transgressive term, every
    time. Filtering `topup=0` therefore does not sample unevenly, it deletes the
    measurement whose whole purpose is to give the suppressed word a number, and
    the result is a clean-looking value with the sign reversed. That happened in
    this thread. Printing both is a rule that fires; a comment saying "use _best"
    is one somebody has to recall while writing a WHERE clause.
    """
    print("\nFILL-PARADIGM SCREEN  threshold %.2f" % threshold)
    for tbl, label, extra in ((WORDS, WORDS, ""),
                              (WORDS_P1, WORDS_P1 + " (topup=0, PASS 1 ONLY)", "WHERE topup=0")):
        r = _rows(
            "SELECT countIf(fs >= %s) AS flagged, count() AS cells, "
            "round(avg(fs),5) AS mean_fs, uniqExactIf(model, fs >= %s) AS models, "
            "uniqExactIf(prompt, fs >= %s) AS prompts FROM "
            "(SELECT model, prompt, sumIf(p, match(word, '%s'))/sum(p) AS fs "
            "FROM %s %s GROUP BY model, prompt)"
            % (threshold, threshold, threshold, FILL_RE, tbl, extra))[0]
        print("  [%s]" % label)
        print("    %d flagged of %d cells (%.3f%%)  mean fill %.5f  %d models  %d prompts"
              % (r["flagged"], r["cells"], 100 * r["flagged"] / r["cells"],
                 r["mean_fs"], r["models"], r["prompts"]))

    car = _rows("SELECT model, count() AS n FROM (SELECT model, prompt, "
                "sumIf(p, match(word, '%s'))/sum(p) AS fs FROM %s GROUP BY model, prompt) "
                "WHERE fs >= %s GROUP BY model ORDER BY n DESC LIMIT %d"
                % (FILL_RE, WORDS, threshold, top))
    print("  largest carriers [%s]:" % WORDS)
    for r in car:
        print("    %-44s %4d cells" % (r["model"], r["n"]))

    con = _rows("SELECT prompt, count() AS models, round(max(fs),3) AS mx FROM "
                "(SELECT model, prompt, sumIf(p, match(word, '%s'))/sum(p) AS fs "
                "FROM %s GROUP BY model, prompt) WHERE fs >= %s "
                "GROUP BY prompt ORDER BY models DESC LIMIT %d"
                % (FILL_RE, WORDS, threshold, top))
    print("  prompts drawing the most agreement across unrelated models:")
    for r in con:
        print("    %2d models  max %.3f  %s" % (r["models"], r["mx"], r["prompt"][:52]))
    print("  A prompt many models flag is a STEM-SHAPE result. A prompt one model")
    print("  flags is a fact about that model. The screen does not distinguish them;")
    print("  the count in the first column does.")
    return {"threshold": threshold, "carriers": car, "concentration": con}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dead", action="store_true", help="empty-cell screen only")
    ap.add_argument("--shape", action="store_true", help="distribution screen only")
    ap.add_argument("--fill", action="store_true", help="fill-paradigm screen only")
    ap.add_argument("--threshold", type=float, default=0.25)
    ap.add_argument("--json", help="write both results to this path")
    a = ap.parse_args()
    both = not (a.dead or a.shape or a.fill)
    out = {}
    if both or a.dead:
        out["dead"] = dead()
    if both or a.shape:
        out["shape"] = shape()
    if both or a.fill:
        out["fill"] = fill(a.threshold)
    if a.json:
        json.dump(out, open(a.json, "w"), indent=1, default=float)
        print("\n-> %s" % a.json)


if __name__ == "__main__":
    main()
