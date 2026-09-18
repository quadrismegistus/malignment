"""Freud's quantitative factor, as a cross: out-of-context objectionableness x in-context lift.

    python -u lexicon_by_lift.py              print the cross
    python -u lexicon_by_lift.py --write      -> results/lexicon_by_lift.json

## THE QUESTION, AND WHY IT NEEDS TWO INSTRUMENTS AND NOT ONE

Freud separates an idea's CONTENT from its QUANTITY of energy: a derivative can
be "calculated to give rise to a conflict" by what it means and still go
unrepressed because it carries little cathexis. Read on one instrument that
sentence is a contradiction -- `charge` is the rated transgressiveness of the
SCENE, which is content in context, so "objectionable content but little charge"
says the same thing twice.

The two measures exist and they are independent by construction:

    OUT OF CONTEXT   `k_transgressiveness`, `k_bodily_harm` -- the word alone,
                     rated once for the whole corpus. `kill` is 7 wherever it
                     appears, in a murder scene or a kill-switch manual.
    IN CONTEXT       `lift` = scene - frame, from `task_charge`. What this word
                     ADDS to this scene. On `He raised the knife and stabbed him
                     in the ___` the frame is already 7 and no body part adds
                     anything, so every candidate sits at lift 0 however the
                     lexicon rates it.

So the prediction is a cross, not a gradient: among words the lexicon calls
objectionable, mass loss should track LIFT, and the high-lexicon / zero-lift
cell should stay put.

## THE STATISTIC IS A PER-LINEAGE MASS RATIO, NOT A POOLED ONE

Within a cell of the cross, `sum(p_aligned) / sum(p_base)` over one lineage's
rows. Pooling the fifty would let the largest-vocabulary lineages set the answer
and would hide the between-lineage variance the sign test needs; the roster's
unit is the lineage everywhere else in this campaign and it is the unit here.

Both arms are measured on the SAME candidate rows -- the union list `rank.py`
builds -- so a ratio cannot move because one arm had words the other lacked.

## WHAT THIS CANNOT SETTLE

The lexicon and the rater are BOTH `deepseek-v4-flash`. They are different
calls with different prompts at different grains, and the out-of-context task
never sees a frame, but they are not independent instruments and a correlation
between them is not two witnesses agreeing.
"""
import argparse, collections, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)
DEPOSIT = os.path.expanduser("~/malignment-data/dose_response/charge_en50_flash.jsonl")
OUT = os.path.join(HERE, "results", "lexicon_by_lift.json")

#: **THE CUT IS PAPER-CLAUDE'S, STATED RATHER THAN TUNED.** "transgressiveness
#: or bodily harm at 5 or above" -- the max of the two, so a word qualifies on
#: either. 2.5% of word-ratings clear it; the k scales are floored (93% of the
#: vocabulary sits at 1) and a percentile cut here would return `stone` and
#: `have` as objectionable words, which is how this was got wrong once already.
LEX_CUT = 5

#: lift bands. `<=0` carries 79.5% of base mass and is the cell Freud's sentence
#: is about; it absorbs the negatives (a word that LOWERS the scene) because
#: they are 3.9% of mass and splitting them buys a cell of noise.
BANDS = [("lift <= 0", lambda L: L <= 0),
         ("lift 1-2", lambda L: 1 <= L <= 2),
         ("lift >= 3", lambda L: L >= 3)]

#: **TWO READINGS OF "CONTENT", AND THEY ARE NOT THE SAME CLAIM.**
#:
#:   lexicon  the word rated ALONE, by a separate out-of-context call. Brings a
#:            third instrument in, and is what Freud's "content" most nearly
#:            means: `kill` is objectionable wherever it stands.
#:   scene    the completed scene's own rating, frame NOT subtracted. Stays
#:            inside one instrument, and is the quantity `lift` is derived from.
#:
#: **THE SECOND IS CONFOUNDED WITH LIFT BY CONSTRUCTION and the first is not.**
#: `lift = scene - frame`, so a low scene cannot carry a high lift: at scene 1,
#: 98% of frames are also 1 and lift is 0 by arithmetic. Only at scene 5-7 do
#: frames spread widely enough (scene 7: frames 3 through 7) for the two to
#: vary independently, so the scene reading is tested THERE and the triangular
#: cells are reported empty rather than filled with a number the design cannot
#: produce.
def _lex(*scales):
    """A two-level content factor: does ANY of these k scales reach the cut?"""
    return ("max(%s) >= %d" % (", ".join("k_" + x for x in scales), LEX_CUT),
            [("low", lambda sc, k, _s=scales: max(k[x] for x in _s) < LEX_CUT),
             ("high", lambda sc, k, _s=scales: max(k[x] for x in _s) >= LEX_CUT)])


#: **EACH SCALE ON ITS OWN, AND THE THREE TOGETHER.** They are not the same
#: question. `k_charge` is affective INTENSITY in either direction (`ecstasy`
#: and `agony` both 7) and is the only one of the three that is not a content
#: category; `k_transgressiveness` asks whether a rule is broken;
#: `k_bodily_harm` whether a body is damaged. Running the max of several hides
#: which one carries the effect, so the max is offered as a fifth factor rather
#: than as the default.
#:
#: **THE THREE ARE NOT INDEPENDENT INSTRUMENTS**: one rater, one call, seven
#: scales returned together, so a word rated high on one is rated in the same
#: breath as the others. Agreement between them is not corroboration.
FACTOR = {
    "charge": _lex("charge"),
    "transgressiveness": _lex("transgressiveness"),
    "bodily_harm": _lex("bodily_harm"),
    #: kept under its own name so the first run's numbers stay reproducible
    "harm_or_transg": _lex("transgressiveness", "bodily_harm"),
    "any3": _lex("charge", "transgressiveness", "bodily_harm"),
    "scene": ("the completed scene's own 1-7 rating, frame not subtracted",
              [("scene 1-2", lambda sc, k: sc <= 2),
               ("scene 3-4", lambda sc, k: 3 <= sc <= 4),
               ("scene 5-7", lambda sc, k: sc >= 5)]),
}


def rows():
    """Stream the deposit -> (lineage, k ratings, scene, lift, p_base, p_aligned).

    Yields the whole k dict rather than a precomputed flag, so one pass feeds
    every content factor and the factors cannot silently disagree about which
    rows they saw.
    """
    from malignment import fields as F
    n = miss = 0
    for line in open(DEPOSIT, encoding="utf-8"):
        d = json.loads(line)
        fr, lin = d["frame"], d["base"]
        for w in d["words"]:
            k = F.k(w["word"])
            if not k:
                miss += 1
                continue
            n += 1
            yield (lin, k, w["scene"], w["scene"] - fr,
                   w["p_base"], w["p_aligned"])
    print("%s word-ratings used, %s dropped for no lexicon entry (%.1f%%)"
          % (format(n, ","), format(miss, ","), 100 * miss / (n + miss)),
          file=sys.stderr)


def tally(factor):
    """(lineage, content band, lift band) -> [base mass, aligned mass, rows]."""
    _desc, levels = FACTOR[factor]
    acc = collections.defaultdict(lambda: [0.0, 0.0, 0])
    for lin, k, sc, L, pb, pa in rows():
        cb = next((n for n, fn in levels if fn(sc, k)), None)
        lb = next((n for n, fn in BANDS if fn(L)), None)
        if cb is None or lb is None:
            continue
        c = acc[(lin, cb, lb)]
        c[0] += pb
        c[1] += pa
        c[2] += 1
    return acc


def cross(factor="harm_or_transg", acc=None):
    import statistics as st
    acc = tally(factor) if acc is None else acc
    _desc, levels = FACTOR[factor]
    #: **THE NULL IS NOT 1.0, AND READING IT AS 1.0 INVERTS THE SENTENCE.**
    #: The candidate list is the union of both arms, and the aligned arm clears
    #: the 1% gate on more words than the base does -- peaking lifts tail mass
    #: across the threshold (`task_charge`: 175,638 base pairs against 260,775
    #: aligned). So total rated mass GROWS from base to aligned in almost every
    #: lineage, and a cell sitting at ratio 1.00 has lost ground against its own
    #: lineage rather than held still. Each cell is therefore reported twice:
    #: raw, and divided by that lineage's ratio over ALL its rows.
    drift = collections.defaultdict(lambda: [0.0, 0.0])
    for (lin, _cb, _lb), (b, a_, _n) in acc.items():
        drift[lin][0] += b
        drift[lin][1] += a_
    dr = {lin: a_ / b for lin, (b, a_) in drift.items() if b > 0}
    out = []
    for cb, _fn in levels:
        for lb, _f2 in BANDS:
            per = {lin: v for (lin, c, l), v in acc.items()
                   if c == cb and l == lb and v[0] > 0}
            if not per:
                continue
            rat = [a / b for b, a, _n in per.values()]
            rel = [(a / b) / dr[lin] for lin, (b, a, _n) in per.items()
                   if dr.get(lin)]
            out.append({
                "content": cb, "band": lb, "n_lineages": len(rat),
                "median_ratio": st.median(rat),
                "median_relative": st.median(rel),
                "falls_relative": sum(1 for r in rel if r < 1.0),
                "base_mass": sum(b for b, _a, _n in per.values()),
                "rows": sum(n for _b, _a, n in per.values())})
    tot = sum(r["base_mass"] for r in out)
    for r in out:
        r["share_of_base_mass"] = r["base_mass"] / tot
    return out, st.median(dr.values())


def contrasts(factor="harm_or_transg", acc=None):
    """The paired within-lineage tests. -> [dict]

    **PAIRED CONTRASTS NEED NO NULL.** The cross table's raw column has to be
    read against the lineage's own drift, and choosing that baseline is a
    judgement. A ratio of two cells measured on the SAME lineage cancels the
    drift exactly, whatever it was -- and the interaction test, which is the one
    that decides whether the two quantities are one filter or two, is a ratio of
    ratios and cancels it twice.

    **A CONTRAST IS SKIPPED WHERE THE DESIGN CANNOT SUPPORT IT**, rather than
    reported thin. With `scene` as the content factor, `scene 1-2 x lift >= 3`
    is empty by arithmetic, not by outcome.
    """
    import statistics as st
    from math import comb
    acc = tally(factor) if acc is None else acc
    _desc, levels = FACTOR[factor]
    lins = sorted({k[0] for k in acc})
    names = [n for n, _f in levels]

    def R(l, cb, lb):
        x = acc.get((l, cb, lb))
        return x[1] / x[0] if x and x[0] > 0 else None

    def test(vals, name, what, need=25):
        v = [x for x in vals if x]
        if len(v) < need:
            return {"test": name, "asks": what, "n_lineages": len(v),
                    "SKIPPED": "only %d lineages carry both cells" % len(v)}
        n = len(v)
        below = sum(1 for x in v if x < 1.0)
        k = min(below, n - below)
        return {"test": name, "asks": what, "median": st.median(v),
                "below_1": below, "n_lineages": n,
                "p_sign": min(1.0, sum(comb(n, i) for i in range(k + 1))
                              * 2 / 2 ** n)}

    lo, hi_ = names[0], names[-1]
    out = []
    for lb, _fn in BANDS:
        out.append(test([R(l, hi_, lb) / R(l, lo, lb)
                         if R(l, hi_, lb) and R(l, lo, lb) else None
                         for l in lins],
                        "A: %s / %s  within %s" % (hi_, lo, lb),
                        "at a FIXED lift, does more content cost mass?"))
    for cb in names:
        out.append(test([R(l, cb, "lift >= 3") / R(l, cb, "lift <= 0")
                         if R(l, cb, "lift >= 3") and R(l, cb, "lift <= 0")
                         else None for l in lins],
                        "B: lift>=3 / lift<=0  within %s" % cb,
                        "at FIXED content, does more lift cost mass?"))
    inter = []
    for l in lins:
        a, b = R(l, hi_, "lift >= 3"), R(l, hi_, "lift <= 0")
        c, d = R(l, lo, "lift >= 3"), R(l, lo, "lift <= 0")
        if all((a, b, c, d)):
            inter.append((a / b) / (c / d))
    out.append(test(inter, "C: INTERACTION",
                    "is the lift effect DIFFERENT at high content? 1.000 = two "
                    "independent filters"))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--factor", default="harm_or_transg", choices=sorted(FACTOR),
                    help="what plays the role of CONTENT against lift")
    ap.add_argument("--all", action="store_true",
                    help="run every content factor")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    doc = {}
    for factor in (sorted(FACTOR) if a.all else [a.factor]):
        acc = tally(factor)
        res, drift = cross(factor, acc)
        con = contrasts(factor, acc)
        print("\n=== CONTENT = %s" % factor.upper())
        print("    %s" % FACTOR[factor][0])
        print("\n    lineage's OWN drift over all rated mass: median %.3f "
              "-- the null for `raw`, not 1.000" % drift)
        print("\n    %-11s %-11s %10s %8s %8s %8s %9s"
              % ("content", "lift band", "rows", "mass sh.", "raw", "vs drift",
                 "falls"))
        for r in res:
            print("    %-11s %-11s %10s %7.1f%% %8.3f %8.3f %5d/%-3d"
                  % (r["content"], r["band"], format(r["rows"], ","),
                     100 * r["share_of_base_mass"], r["median_ratio"],
                     r["median_relative"], r["falls_relative"],
                     r["n_lineages"]))
        print("\n    PAIRED CONTRASTS -- each cancels the drift, no baseline chosen\n")
        for c in con:
            if "SKIPPED" in c:
                print("    %-40s SKIPPED: %s" % (c["test"], c["SKIPPED"]))
            else:
                print("    %-40s %.3f  %2d/%d below 1  p=%.2g"
                      % (c["test"], c["median"], c["below_1"],
                         c["n_lineages"], c["p_sign"]))
        doc[factor] = {"describes": FACTOR[factor][0], "median_drift": drift,
                       "cells": res, "contrasts": con}
    if a.write:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        json.dump({"lex_cut": LEX_CUT, "factors": doc}, open(OUT, "w"), indent=1)
        print("\nwrote %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
