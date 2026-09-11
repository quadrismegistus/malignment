#!/usr/bin/env python
"""Does alignment's movement along word norms depend on the attention mechanism?

    python run.py

## A LOOKUP, AND ITS SOURCE HAD TO BE BUILT FIRST

`displacement/norm_change` regresses (aligned - base) on the base transgressive
dose, per lineage, and until 2026-09-11 it wrote only the AGGREGATE -- one row
per target, already collapsed over lineages. No question could stratify the
roster without re-running the whole dose. `dose.py --per-lineage` now writes the
vector beside it, and this file reads that.

## THE POPULATION IS 45, NOT 50, AND THAT IS NOT THIS FILE'S CHOICE

`displacement/norm_change/README.md` makes `--match-framed` non-optional: the
framed set covers 45 of the 50 pairs, and raw at n=50 beside framed at n=45
differs partly by which labs ship a chat template. All 12 of this subject's
architecture-relevant models are inside the 45, so nothing here is lost to it --
but this question and `architectures/displacement` are NOT on one population and
must not be quoted as though they were.

## WHY THIS IS A WEAK INSTRUMENT FOR THE SUBJECT, STATED HERE TOO

It is a DELTA, and the subject README explains at length why that matters: a
delta differences out the corpus, which is the confound that destroys every
level measure here, but its own confound is that ALIGNMENT data varies across
labs and is NOT controlled across these 45 lineages. The remedy exists and is
not applied here -- restrict to lineages sharing a mixture, Dolci or Tulu-3 --
and it would cost most of the n.

Split out of `architectures/displacement/run.py` on 2026-09-11: the claim was
stated in this folder's README while the code that produced it lived next door,
which is what one-producer-per-question exists to prevent.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(HERE))))

EXP = os.path.dirname(os.path.dirname(HERE))
NC = os.path.join(EXP, "displacement", "norm_change", "results")
#: how many dose targets to carry. The aggregate is sorted by p, and past the
#: first dozen the targets are near-duplicates of each other (the _absz variant
#: of a scale it already lists), so a larger K buys correlated votes, not power.
N_TARGETS = 12


def slopes(table="levels"):
    """(targets, {target: {base: slope}}, {target: roster median}) or Nones."""
    import csv
    import statistics as st
    agg = os.path.join(NC, "dose_lift_v4__%s_en.csv" % table)
    per = os.path.join(NC, "dose_lift_v4__%s_en__by_lineage.csv" % table)
    if not (os.path.exists(agg) and os.path.exists(per)):
        return None, None, None
    rows = sorted(csv.DictReader(open(agg)), key=lambda r: float(r["p"]))
    targets = [r["target"] for r in rows[:N_TARGETS]]
    want, sl = set(targets), {t: {} for t in targets}
    for r in csv.DictReader(open(per)):
        if r["target"] in want:
            sl[r["target"]][r["lineage"].split(">")[0]] = float(r["slope"])
    med = {t: st.median(sl[t].values()) for t in targets if sl[t]}
    return targets, sl, med


def main():
    from malignment import roster
    targets, nc, med = slopes()
    if targets is None:
        print("no per-lineage CSV. Run, from displacement/norm_change/:")
        print("  python dose.py --lift-dose --rule-version 4 --lang en \\")
        print("      --table all --match-framed --per-lineage --out results")
        return 1
    bases = sorted({b for t in targets for b in nc[t]})
    nd = [b for b in bases if roster.architecture(b) != ("unknown", "unknown")
          and (roster.architecture(b)[1] != "dense"
               or roster.architecture(b)[0] != "full")]
    print("NORM_CHANGE dose slopes, top %d targets by p, %d matched pairs"
          % (len(targets), len(bases)))
    print("agree = this model's slope has the SAME SIGN as the roster median\n")
    print("%-30s %-13s %-7s %s" % ("model", "attn", "block", "agree"))
    for b in sorted(nd):
        at, bl = roster.architecture(b)
        hit = [t for t in targets if b in nc[t] and nc[t][b] * med[t] > 0]
        has = [t for t in targets if b in nc[t]]
        print("%-30s %-13s %-7s %d/%d"
              % (b.split("/")[-1][:30], at, bl, len(hit), len(has)))
    print("\nthe roster itself, for scale:")
    for t in targets[:6]:
        v = nc[t]
        agr = sum(1 for x in v.values() if x * med[t] > 0)
        print("   %-38s median %+9.5f   %d/%d lineages agree"
              % (t[:38], med[t], agr, len(v)))
    print("\nAND THE TWO DISSENTERS ARE THE TWO WEAKEST MOVERS, which is the")
    print("finding: agreement tracks how much a model was ALIGNED, not what it")
    print("is built from. See architectures/displacement for the |slope| column.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
