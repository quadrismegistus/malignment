"""Substitutes OR displaced affect? Split the arriving mass between the two.

    python -u disjunction.py              print it
    python -u disjunction.py --write      -> results/disjunction.json
    python -u disjunction.py --tol 0.5    sensitivity on the one free parameter

## THE SENTENCE THIS TESTS, AND THE WORD IN IT NOBODY HAS TESTED

The argument predicts that the words gaining mass "should be either substitutes
for these acts or displaced expressions of their affect." Both halves have
support -- `existence/adjacency.py` and `channel_graph.py` for the first,
`departing_arriving.py` for the second -- and **the disjunction itself has none**.
Nobody has asked whether those are the same words, different words, or what
share of the mass is neither.

"Neither" is not a rhetorical third option. It is what plain suppression looks
like: mass leaving `kill` for `said`, carrying neither the act nor the charge.
A sentence offering two channels is refuted not by either failing but by most of
the traffic using a third.

## THE 2x2, AND WHY BOTH AXES COME FROM ONE CALL

Freud's two fates are separable here because the lexicon rates both:

    ACT      max(k_bodily_harm, k_transgressiveness) -- the idea, what is done
    AFFECT   k_charge -- "affective intensity, in EITHER direction", the quota

Both are returned by the SAME rating call on the same word, so an arriving word's
act and affect are measured at one grain and one moment. Using v6 for the act and
`k` for the affect would put the two axes on different instruments and make every
quadrant boundary a comparison between rulers.

Per cell, the departing mass sets the reference: its own mass-weighted act A and
affect C. Each arriving word is then placed against THAT cell's departure, not
against a global constant, because a substitute is only a substitute for what
actually left.

    retains the act      act_w    >= A - tol
    retains the affect   charge_w >= C - tol

            affect kept          affect lost
  act kept  SUBSTITUTE           (rare; act without its charge)
  act lost  DISPLACED AFFECT     NEITHER -- plain suppression

## THE GATE: THE SENTENCE IS CONDITIONAL AND SO IS THE TEST

"...losing mass ought to be transgressive acts". Where nothing transgressive
left, "retains the act" is satisfied by any ordinary word and the quadrants are
meaningless. Cells enter only when the departing mass is itself charged
(`--min-act`, default 4 on the 1-7 scale, the cut `existence/channel_graph.py`
already uses for its seed set).

## THE ONE FREE PARAMETER IS NAMED AND SWEPT

`tol` decides how far below the departure a word may sit and still count as
keeping that property. There is no principled value, so `--tol` sweeps it and the
result is reported at three settings. A split that only holds at one tolerance is
not a finding.
"""
import argparse, collections, csv, gzip, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)
SRC = os.path.expanduser("~/malignment-data/norm_change/words_long_v4.csv.gz")
OUT = os.path.join(HERE, "results", "disjunction.json")
#: **THE ACT AXIS IS GRADED, BECAUSE A BINARY ONE PUTS `hurt` WHERE `scream` IS.**
#: The reference is what actually departed, so after `kill` (act 7) a word must
#: reach ~6 to count as keeping the act -- and `hurt` at 5 then lands in the same
#: cell as `scream` at 1, which is exactly the distinction the sentence turns on.
#: So: FULL (within tol of the departure), PARTIAL (still an act, but milder),
#: NONE (at the lexicon floor, no act at all).
ACT_FLOOR = 2.0
QUAD = ["SUBSTITUTE (full act, affect kept)",
        "MILDER ACT (partial act, affect kept)",
        "DISPLACED AFFECT (no act, affect kept)",
        "act kept, affect lost",
        "NEITHER -- content word",
        "NEITHER -- function word"]


def cells():
    """-> (lineage, [(word, delta, act, charge)]) per (prompt, lineage) cell."""
    from malignment import fields as F
    from malignment import roster
    pairs = {(b, a) for b, a in roster.endpoints()[0].items()}
    cur, key = [], None
    with gzip.open(SRC, "rt") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            if row["lang"] != "en" or (row["base"], row["aligned"]) not in pairs:
                continue
            k2 = (row["base"], row["prompt"])
            if k2 != key:
                if cur:
                    yield key[0], cur
                cur, key = [], k2
            d = float(row["delta"])
            if d == 0:
                continue
            kk = F.k(row["word"])
            if not kk:
                continue
            cur.append((row["word"], d,
                        max(kk["bodily_harm"], kk["transgressiveness"]),
                        float(kk["charge"]), row["is_function"] == "1"))
    if cur:
        yield key[0], cur


def compute(tol, min_act):
    import statistics as st
    #: lineage -> quadrant -> arriving mass
    acc = collections.defaultdict(collections.Counter)
    avail = collections.defaultdict(collections.Counter)
    seen, used, skipped = set(), 0, 0
    ex = collections.Counter()
    for lin, rows in cells():
        dep = [(w, -d, a, c, f) for w, d, a, c, f in rows if d < 0]
        arr = [(w, d, a, c, f) for w, d, a, c, f in rows if d > 0]
        if not dep or not arr:
            skipped += 1
            continue
        dm = sum(x[1] for x in dep)
        A = sum(x[1] * x[2] for x in dep) / dm
        C = sum(x[1] * x[3] for x in dep) / dm
        #: **THE CONDITIONAL IN THE SENTENCE, ENFORCED.** Where nothing charged
        #: departed there is no "these acts" for a substitute to substitute for.
        if A < min_act:
            skipped += 1
            continue
        used += 1
        seen.add(lin)
        for w, d, a, c, isfn in arr:
            keeps_aff = c >= C - tol
            if a >= A - tol:
                act = 2
            elif a >= ACT_FLOOR:
                act = 1
            else:
                act = 0
            if keeps_aff:
                q = QUAD[0] if act == 2 else QUAD[1] if act == 1 else QUAD[2]
            elif act > 0:
                q = QUAD[3]
            else:
                #: **FUNCTION WORDS SPLIT OUT RATHER THAN DROPPED.** They carry
                #: real mass and belong in the denominator, but "the arriving
                #: mass goes to `be` and `the`" and "it goes to ordinary content
                #: words" are different claims about the argument and a single
                #: NEITHER bucket says whichever the reader assumes.
                q = QUAD[5] if isfn else QUAD[4]
            acc[lin][q] += d
            ex[(q, w)] += d
        #: **WHAT WAS AVAILABLE, so a share can be read as a preference.** 54% of
        #: the arriving mass landing on ordinary content words says nothing on
        #: its own if ordinary content words are 54% of the candidate list. The
        #: null is this cell's own candidates, counted once each regardless of
        #: mass -- the set alignment had to choose from.
        for w, d, a, c, isfn in rows:
            keeps_aff = c >= C - tol
            act = 2 if a >= A - tol else (1 if a >= ACT_FLOOR else 0)
            if keeps_aff:
                q = QUAD[0] if act == 2 else QUAD[1] if act == 1 else QUAD[2]
            elif act > 0:
                q = QUAD[3]
            else:
                q = QUAD[5] if isfn else QUAD[4]
            avail[lin][q] += 1
    print("%s cells used, %s skipped (no movement on one side, or the departing "
          "mass was not charged)" % (format(used, ","), format(skipped, ",")),
          file=sys.stderr)
    out = {}
    for q in QUAD:
        shares, avs, enr = [], [], []
        for lin, c in acc.items():
            t, ta = sum(c.values()), sum(avail[lin].values())
            if t > 0 and ta > 0:
                shares.append(c[q] / t)
                avs.append(avail[lin][q] / ta)
                if avail[lin][q]:
                    enr.append((c[q] / t) / (avail[lin][q] / ta))
        #: **AN ENRICHMENT RATIO IS A MEDIAN OF FIFTY, SO IT GETS A SIGN TEST.**
        #: 1.28x across lineages that individually straddle 1 is not a
        #: preference, and a table of ratios alone cannot tell the two apart.
        from math import comb
        nn = len(enr)
        below = sum(1 for x in enr if x < 1.0)
        kk = min(below, nn - below)
        out[q] = {"below_1": below, "n_enr": nn,
                  "p_sign": (min(1.0, sum(comb(nn, i) for i in range(kk + 1))
                                 * 2 / 2 ** nn) if nn else None),
                  "median_share": st.median(shares),
                  "median_available": st.median(avs),
                  "median_enrichment": st.median(enr) if enr else None,
                  "n_lineages": len(shares),
                  "words": [w for (qq, w), _m in ex.most_common()
                            if qq == q][:10]}
    return out, len(seen), used


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tol", type=float, default=None)
    ap.add_argument("--min-act", type=float, default=4.0)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    tols = [a.tol] if a.tol is not None else [0.5, 1.0, 1.5]
    doc = {}
    for tol in tols:
        res, nlin, used = compute(tol, a.min_act)
        print("\n=== tol %.1f, departing act >= %.1f -- %s cells, %d lineages"
              % (tol, a.min_act, format(used, ","), nlin))
        print("    share of ARRIVING mass, median over lineages\n")
        print("    %-38s %8s %9s %7s %14s"
              % ("", "arriving", "available", "ratio", "below 1x     p"))
        for q in QUAD:
            r = res[q]
            print("    %-38s %7.1f%% %8.1f%% %7s   %2d/%-2d  %8.2g"
                  % (q, 100 * r["median_share"], 100 * r["median_available"],
                     ("%.2fx" % r["median_enrichment"])
                     if r["median_enrichment"] else "--",
                     r["below_1"], r["n_enr"], r["p_sign"]))
        print()
        for q in QUAD:
            print("      %-38s %s" % (q, ", ".join(res[q]["words"][:7])))
        doc["tol=%.1f" % tol] = {"min_act": a.min_act, "n_lineages": nlin,
                                 "n_cells": used, "quadrants": res}
    if a.write:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        json.dump(doc, open(OUT, "w"), indent=1)
        print("\nwrote %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
