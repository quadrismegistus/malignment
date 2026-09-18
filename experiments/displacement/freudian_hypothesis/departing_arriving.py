"""Follow the mass twice: what leaves, and what arrives. -> results/departing_arriving.json

    python -u departing_arriving.py            print it
    python -u departing_arriving.py --write    write the JSON

## THE TEST IS FREUD'S OWN INSTRUCTION, NOT AN ANALOGY IMPOSED ON THE DATA

"Repression" (1915) requires a case to be followed twice, for what "becomes of
the idea, and what becomes of the drive energy linked to it": the idea acquires a
substitute by displacement, while the "quantitative portion has not vanished, but
has been transformed." That is two predictions with opposite signs on the same
population of words, and they are separable because this corpus rates the IDEA
(harm, transgressiveness, directedness, aggression) and the AFFECT (charge,
arousal) on different scales.

    THE IDEA IS REPRESSED       harm, bodily_harm, transgressiveness,
                                directedness, aggression, makes_worse  -> DOWN
    THE AFFECT IS CONSERVED     k_charge, warriner_arousal             -> ~ZERO
    AND TRANSFORMED             vocalisation, interiority              -> UP

**THE MIDDLE ROW IS THE ONE THAT CAN KILL THE READING**, and it is a null, so it
is reported as a FRACTION of the first row rather than as a p-value. "Arousal did
not move" is unfalsifiable at any n; "arousal moved 9% as far as harm did, on the
same words, in the same units" is a bound. A quota of affect that fell as far as
the idea did would refute the transformation claim outright.

## THE STATISTIC: A MASS-WEIGHTED PROFILE OF EACH SIDE OF THE LEDGER

Per lineage, over every English prompt, each word contributes its own |change| as
weight:

    departing   sum(|d| * norm) / sum(|d|)   over words with d < 0
    arriving    sum( d  * norm) / sum( d )   over words with d > 0

so the profile is of the MASS that moved, not of the word types that moved. A
word losing 8 points counts eight times a word losing one, which is what an
economic claim about quantity requires.

The two sides are then differenced WITHIN a lineage, which is what makes the
comparison safe: both profiles are built from the same prompts, the same
candidate lists and the same rater, so an instrument's floor or ceiling sits on
both sides and cancels. Nothing here compares a base arm to an aligned arm
directly; the unit is the movement.

## WHAT ALREADY ANSWERS THE OTHER HALF, AND WHY THIS EXISTS ANYWAY

`experiments/displacement/existence/` has the prior claim on where the mass GOES
and this file does not supersede any of it:

    adjacency.py        do risers share the top faller's `kind`? Per lineage,
                        same-kind against none-kind.
    adjacency.py --flow the USAS field-to-field channels, with word pairs;
                        `channel_table.py` joins them readably.
    channel_graph.py    those channels laid out by BFS depth from high-charge
                        seeds. Its result bears on the "chain of connections"
                        claim: charge 4.92 at the seeds, 2.67 at depth 1, 2.59
                        at depth 2 -- the whole descent is the FIRST move, so
                        the chain is one link, not a ladder.
    metonymy/run.py     within ONE scene, is the riser further out on the
                        scene's own scale than the faller?

All four ask about the RELATION between a faller and a riser. This file asks a
different question that none of them can answer: what are the mass-weighted
PROPERTIES of each side of the ledger, on scales that separate the idea from the
affect. `kind` and USAS are categorical and cannot say that harm fell while
aggression did not; a field-to-field channel cannot say that the arriving mass is
no less charged than the departing.

**So: relation there, profile here.** If a reader wants "where did it go", go to
`existence/`. If they want "what left and what arrived", this is it. Neither
settles the disjunction in the argument's own sentence -- substitutes OR
displaced affect -- which needs both halves at once.

## WHAT THIS CANNOT SHOW

**Substitution is the other half of the sentence and is NOT tested here.** "The
idea acquires a substitute by displacement along a chain of connections" is a
claim about the relation between a particular departing word and a particular
arriving one, which needs a similarity measure over (prompt, word) -- the
`bge` slot-word space in `slot_axis.py` -- and not a profile of each side. A
profile can show the arriving mass is less harmful and no less aroused; it cannot
show that `scream` is the substitute FOR `kill` rather than an unrelated riser.
"""
import argparse, collections, gzip, csv, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)
SRC = os.path.expanduser("~/malignment-data/norm_change/words_long_v4.csv.gz")
OUT = os.path.join(HERE, "results", "departing_arriving.json")

#: grouped by what the argument predicts, so a table cannot be read without its
#: prediction attached. `SAME` is the null that bounds the claim.
PREDICT = [
    ("DOWN -- the idea is repressed",
     ["v6:harm", "v6:aggression", "v6:directedness", "v6:makes_worse",
      "k_bodily_harm", "k_transgressiveness"]),
    ("~ZERO -- the quota of affect is conserved",
     ["k_charge", "warriner_arousal"]),
    ("UP -- transformed into affect and speech",
     ["v6:vocalisation", "v6:interiority", "v6:deliberation", "v6:superego"]),
    #: **`hedged` WAS MINE AND IT CAME BACK THE OTHER WAY.** I grouped it with
    #: the affect-transformation scales on the guess that displaced speech would
    #: be tentative speech. It falls (-0.118, 36/50, p=0.0026): the arriving
    #: mass is MORE committed than the departing, not less. Left in its own row
    #: rather than moved quietly into "no prediction", because a prediction that
    #: failed is evidence and a prediction relabelled after the fact is not.
    ("PREDICTED UP BY ME, CAME BACK DOWN", ["v6:hedged"]),
    ("no prediction, reported for context",
     ["warriner_valence", "warriner_dominance", "k_valence", "k_concreteness",
      "k_register_level", "v6:makes_better", "v6:fit", "v6:mundanity"]),
]
SCALES = [s for _lab, ss in PREDICT for s in ss]
#: the scale the nulls are quoted as a fraction OF -- the largest declared
#: repression effect, named here rather than picked after seeing the numbers
ANCHOR = "v6:harm"


def norms():
    """(per-word dict, per-(prompt,word) dict) for every scale above."""
    from malignment import fields as F
    idx = F._slot_index()
    ctx = {}
    for (pr, w), by in idx.items():
        v6 = by.get("v6")
        if v6:
            ctx[(pr, w)] = {"v6:" + k: float(x) for k, x in v6.items()
                            if isinstance(x, (int, float))
                            and not isinstance(x, bool)}
    return F, ctx


def compute():
    import statistics as st
    from math import comb
    from malignment import roster
    pairs = {(b, a) for b, a in roster.endpoints()[0].items()}
    F, ctx = norms()
    #: lineage -> scale -> [dep_wsum, dep_w, arr_wsum, arr_w]
    acc = collections.defaultdict(lambda: collections.defaultdict(
        lambda: [0.0, 0.0, 0.0, 0.0]))
    mass = collections.defaultdict(lambda: [0.0, 0.0])
    seen, n = set(), 0
    with gzip.open(SRC, "rt") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            if row["lang"] != "en":
                continue
            key = (row["base"], row["aligned"])
            if key not in pairs:
                continue
            d = float(row["delta"])
            if d == 0:
                continue
            n += 1
            seen.add(key)
            lin, w, pr = row["base"], row["word"], row["prompt"]
            side = 0 if d < 0 else 2
            mass[lin][0 if d < 0 else 1] += abs(d)
            vals = dict(ctx.get((pr, w), {}))
            k = F.k(w)
            if k:
                vals.update({"k_" + s: float(v) for s, v in k.items()})
            wn = F.word_norms(w)
            if wn:
                vals.update({("brysbaert_concreteness" if s == "concreteness"
                              else "warriner_" + s): float(v)
                             for s, v in wn.items()})
            a = acc[lin]
            for s in SCALES:
                if s in vals:
                    a[s][side] += abs(d) * vals[s]
                    a[s][side + 1] += abs(d)
    if len(seen) != 50:
        raise SystemExit("expected 50 endpoint lineages, matched %d" % len(seen))
    print("%s non-zero English movements over %d lineages"
          % (format(n, ","), len(seen)), file=sys.stderr)

    def test(vals):
        v = [x for x in vals if x is not None]
        nn = len(v)
        below = sum(1 for x in v if x < 0)
        kk = min(below, nn - below)
        return {"median": st.median(v), "below_0": below, "n_lineages": nn,
                "p_sign": min(1.0, sum(comb(nn, i) for i in range(kk + 1))
                              * 2 / 2 ** nn)}

    res = {}
    for s in SCALES:
        diffs = []
        for lin, a in acc.items():
            dw, dn, aw, an = a[s]
            if dn > 0 and an > 0:
                diffs.append(aw / an - dw / dn)
        if len(diffs) >= 25:
            res[s] = test(diffs)
    #: **NOT A TEST OF CONSERVATION, AND IT MUST NOT BE PRINTED AS ONE.** Each
    #: distribution sums to 1 by construction, so the quantity is conserved by
    #: definition and nothing here could falsify it. What this ratio measures is
    #: the OBSERVATION WINDOW: `twp` stores only words above theta, the aligned
    #: arm is more peaked, and so a larger share of its distribution sits inside
    #: the window. Checked directly -- among words present in BOTH arms the
    #: ratio is still 1.247, which cannot be movement into or out of the corpus
    #: and can only be the window. Reported as a diagnostic of how asymmetric
    #: the window is, which any mass-weighted profile above should be read
    #: against.
    cons = {"median_ratio": st.median([m[1] / m[0] for m in mass.values()]),
            "n_lineages": len(mass),
            "IS_NOT": "a test of conservation; see the comment at this line"}
    return res, cons


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    res, cons = compute()
    anchor = abs(res[ANCHOR]["median"]) if ANCHOR in res else None
    print("\nARRIVING MINUS DEPARTING, mass-weighted, per lineage then median\n")
    for lab, ss in PREDICT:
        print("  %s" % lab)
        for s in ss:
            r = res.get(s)
            if not r:
                print("    %-26s (not carried)" % s)
                continue
            frac = ("%6.0f%%" % (100 * abs(r["median"]) / anchor)) if anchor else "    --"
            print("    %-26s %+7.4f  %2d/%d below 0  p=%-9.2g %s of |%s|"
                  % (s, r["median"], r["below_0"], r["n_lineages"],
                     r["p_sign"], frac, ANCHOR))
        print()
    print("  WINDOW ASYMMETRY -- a diagnostic, NOT a test of conservation")
    print("    arriving / departing observed mass   %.3f over %d lineages"
          % (cons["median_ratio"], cons["n_lineages"]))
    print("    Each distribution sums to 1, so conservation cannot be falsified")
    print("    here. This is how much more of the ALIGNED arm sits above theta:")
    print("    among words present in both arms it is still 1.247.")
    if a.write:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        json.dump({"anchor": ANCHOR, "predictions": PREDICT, "scales": res,
                   "conservation": cons}, open(OUT, "w"), indent=1)
        print("\nwrote %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
