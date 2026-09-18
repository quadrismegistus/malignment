"""Does alignment act less on lightly-invested words, at the same lift?

    python -u cathexis.py             print it
    python -u cathexis.py --write     -> results/cathexis.json

Cathexis is analogised to probability: how much the base model has invested in a
word. The question is whether a high-lift word that carries little mass is left
alone, where the same lift on a heavily-invested word is punished.

## THE STATISTIC IS SCALE-FREE, BECAUSE THE OBVIOUS ONE IS NOT

`p_aligned - p_base` is mechanically larger for large `p_base`, so a difference
of differences would answer "are big numbers bigger". Everything here is

    r = log10(p_aligned / p_base)

which asks what FRACTION of its investment a word kept. A word going 0.40 -> 0.20
and one going 0.02 -> 0.01 both score -0.30.

## TWO ARTEFACTS, BOTH OF WHICH FAKE THE ANSWER WE ARE LOOKING FOR

**1. THE GATE SELECTS UPWARD AT LOW p_base.** A candidate is listed if it
clears 1% in EITHER arm, so a word with `p_base` of 0.002 appears ONLY when it
rose enough to clear 1% in the aligned arm -- a 5x rise or better. 23.7% of the
deposit's rows are in this condition. Include them and the low-cathexis band
fills with guaranteed risers and "alignment spares the lightly invested" falls
out of the sampling frame alone. **Everything below is restricted to
`p_base >= 0.01`**, words that stood on their own in the base arm, which removes
the base-side selection completely.

**2. REGRESSION TO THE MEAN IS PRESENT AND ITS SIGN IS NOT KNOWN HERE.** The two
arms are correlated and not identical, so conditioning on `p_base` mixes real
movement with the tendency of an extreme value to be less extreme on a second
measurement. An earlier version of this docstring asserted the direction -- that
it would fake "low-probability words are spared" -- and **the data contradict
that**: the naive gradient runs the other way, low-cathexis words losing a larger
FRACTION than heavily-invested ones at every lift band, which is what peaking
predicts (alignment concentrates mass on the top candidates and drains the
marginal ones). Whether that gradient is peaking, regression, or both is not
separable with one base and one aligned measurement per lineage, so no claim is
made from it.

**So the headline table below is NOT the answer** -- it is the contaminated view,
printed because a reader will otherwise compute it. The answer is the contrast
UNDER it: the size of the LIFT effect within each cathexis band. Any artefact
that depends on `p_base` ALONE -- regression, peaking, the gate -- falls equally
on the high-lift and low-lift words sharing a band, so differencing them cancels
it whatever its sign. If alignment really spares the lightly invested, the lift
effect must SHRINK as investment falls.
"""
import argparse, collections, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)
DEPOSIT = os.path.expanduser("~/malignment-data/dose_response/charge_en50_flash.jsonl")
OUT = os.path.join(HERE, "results", "cathexis.json")

GATE = 0.01
#: quartiles of `p_base` among words that cleared the gate in the base arm.
#: Fixed rather than computed per lineage so a band means the same investment
#: everywhere; the roster's models differ in how peaked they are and a
#: per-lineage quartile would make the bands incomparable across the sign test.
BINS = [("0.010-0.015", 0.010, 0.015), ("0.015-0.025", 0.015, 0.025),
        ("0.025-0.050", 0.025, 0.050), ("0.050+", 0.050, 1.01)]
LIFTS = [("lift <= 0", lambda L: L <= 0), ("lift 1-2", lambda L: 1 <= L <= 2),
         ("lift >= 3", lambda L: L >= 3)]


def rows():
    """-> (lineage, cathexis bin, lift band, r) for words that stood in base."""
    kept = dropped_gate = dropped_zero = 0
    for line in open(DEPOSIT, encoding="utf-8"):
        d = json.loads(line)
        fr, lin = d["frame"], d["base"]
        for w in d["words"]:
            b, a = w["p_base"], w["p_aligned"]
            if b < GATE:
                dropped_gate += 1
                continue
            if a <= 0:
                #: censored, not zero: `twp` stores nothing below 0.001, so the
                #: word's aligned mass is somewhere in [0, 0.001) and the log is
                #: undefined. 0.2% of rows, dropped rather than floored -- a
                #: floor would put them all at one value and that value would
                #: set the low tail of every median.
                dropped_zero += 1
                continue
            L = w["scene"] - fr
            cb = next((n for n, lo, hi in BINS if lo <= b < hi), None)
            lb = next((n for n, fn in LIFTS if fn(L)), None)
            if cb and lb:
                kept += 1
                yield lin, cb, lb, math.log10(a / b)
    print("%s rows used; dropped %s below the base gate (upward-selected) and "
          "%s with zero aligned mass (censored)"
          % (format(kept, ","), format(dropped_gate, ","),
             format(dropped_zero, ",")), file=sys.stderr)


def compute():
    import statistics as st
    from math import comb
    acc = collections.defaultdict(list)
    for lin, cb, lb, r in rows():
        acc[(lin, cb, lb)].append(r)
    lins = sorted({k[0] for k in acc})

    def med(l, cb, lb):
        v = acc.get((l, cb, lb))
        return st.median(v) if v and len(v) >= 20 else None

    def test(vals, name, asks, need=25):
        v = [x for x in vals if x is not None]
        if len(v) < need:
            return {"test": name, "asks": asks, "n_lineages": len(v),
                    "SKIPPED": "only %d lineages carry both cells" % len(v)}
        n = len(v)
        below = sum(1 for x in v if x < 0)
        k = min(below, n - below)
        return {"test": name, "asks": asks, "median": st.median(v),
                "below_0": below, "n_lineages": n,
                "p_sign": min(1.0, sum(comb(n, i) for i in range(k + 1))
                              * 2 / 2 ** n)}

    #: the contaminated view, printed so it is not recomputed in innocence
    naive = []
    for cb, _lo, _hi in BINS:
        for lb, _fn in LIFTS:
            v = [med(l, cb, lb) for l in lins]
            v = [x for x in v if x is not None]
            if len(v) < 25:
                continue
            naive.append({"cathexis": cb, "band": lb, "n_lineages": len(v),
                          "median_r": st.median(v),
                          "rows": sum(len(acc[(l, cb, lb)]) for l in lins
                                      if (l, cb, lb) in acc)})
    #: THE ANSWER: the lift effect within each cathexis band, which cancels
    #: regression to the mean because that depends on p_base alone
    eff = []
    for cb, _lo, _hi in BINS:
        eff.append(test([(med(l, cb, "lift >= 3") - med(l, cb, "lift <= 0"))
                         if med(l, cb, "lift >= 3") is not None
                         and med(l, cb, "lift <= 0") is not None else None
                         for l in lins],
                        "lift effect within %s" % cb,
                        "how much does a lift of 3+ cost, in log10 mass kept, "
                        "at this level of investment?"))
    #: and does the effect itself differ between the extreme bands?
    diff = test([(med(l, BINS[0][0], "lift >= 3") - med(l, BINS[0][0], "lift <= 0"))
                 - (med(l, BINS[-1][0], "lift >= 3") - med(l, BINS[-1][0], "lift <= 0"))
                 if all(med(l, c, b) is not None
                        for c in (BINS[0][0], BINS[-1][0])
                        for b in ("lift >= 3", "lift <= 0")) else None
                 for l in lins],
                "lift effect: lowest band MINUS highest band",
                "is the lift effect SMALLER for lightly-invested words? "
                "negative = the lightly invested are punished MORE, "
                "positive = spared")
    return naive, eff, diff


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    naive, eff, diff = compute()
    print("\nCONTAMINATED VIEW -- median log10(p_aligned/p_base). Peaking and "
          "regression to\nthe mean both act on p_base alone and are not "
          "separable here. Do not read down it.\n")
    print("  %-12s %-11s %10s %10s" % ("cathexis", "lift band", "rows", "median r"))
    for r in naive:
        print("  %-12s %-11s %10s %+10.4f"
              % (r["cathexis"], r["band"], format(r["rows"], ","), r["median_r"]))
    print("\nTHE ANSWER -- the lift effect WITHIN a band, which cancels it\n")
    for e in eff:
        if "SKIPPED" in e:
            print("  %-34s SKIPPED: %s" % (e["test"], e["SKIPPED"]))
        else:
            print("  %-34s %+.4f  %2d/%d below 0  p=%.2g"
                  % (e["test"], e["median"], e["below_0"], e["n_lineages"],
                     e["p_sign"]))
    print()
    if "SKIPPED" in diff:
        print("  %-34s SKIPPED: %s" % (diff["test"], diff["SKIPPED"]))
    else:
        print("  %-34s %+.4f  %2d/%d below 0  p=%.2g"
              % (diff["test"], diff["median"], diff["below_0"],
                 diff["n_lineages"], diff["p_sign"]))
    if a.write:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        json.dump({"gate": GATE, "bins": [b[0] for b in BINS], "naive": naive,
                   "lift_effect": eff, "difference": diff}, open(OUT, "w"),
                  indent=1)
        print("\nwrote %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
