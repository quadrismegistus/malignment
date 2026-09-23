"""The marginal norm change, GATED ON COVERAGE. -> results/levels_gated_en.json

    python -u gated_levels.py                 # the table
    python -u gated_levels.py --gate 0.0      # ungated, to see what the gate buys

## WHY A GATE AT ALL

`README.md` lists it as a live limit: *"Coverage is carried per row and is not
yet used as a filter. A mass-weighted mean over a source covering 3% of a
distribution is in the same column as one covering 80%."* This is that filter.

**AND THE ALTERNATIVE WAS TRIED FIRST AND REJECTED.** Switching the per-lineage
aggregator from MEDIAN to MEAN also removes every tie -- but it removes them by
letting a handful of low-coverage cells speak for the lineage. It turned
`brooke_formality` from 4/4 with 42 ties into 40/10 at p<1e-4, and
`k_vulgarity` from 0/4 with 46 ties into 8/42 at p<1e-4, while COSTING the two
declared results: `warriner_valence` 0.011 -> 0.203 and `warriner_dominance`
0.040 -> 0.203. A change that manufactures significance on the sparse scales
and destroys it on the dense ones is the wrong change. Median stays.

## WHAT A TIE ACTUALLY IS, SINCE IT IS NOT WHAT IT LOOKS LIKE

A tie is a per-lineage median of EXACTLY zero over ~2,400 prompts. That does
not require half the prompts to be identical. Measured on `brooke_formality` x
`Yi-1.5-9B`: 991 negative, 502 exactly zero, 933 positive -- the negatives end
at rank 991, the zero block runs 992-1,493, and the median sits at rank 1,213,
INSIDE the atom. A fat atom at zero straddles the median whenever up and down
are near-balanced. The zeros are the low-coverage cells: median `n_words` 10.4
on the zeros against 17.6 overall, and for `warriner_valence` 1.1 against 59.4,
i.e. one covered word that did not move.

## THE GATE IS 0.20 AND THAT IS A CHOICE, NOT A DISCOVERY

Sweeping 0 / 0.10 / 0.20 / 0.35, every declared result strengthens
monotonically -- valence p=0.011 -> 0.0000, dominance 0.040 -> 0.0003 -- and
`k_concreteness` crosses into significance at 0.20 (0.085 -> 0.033), which
matters because H1 was booked NOT SUPPORTED in English and the failure may have
been coverage rather than absence.

**But the gate discards very unequally, so a tighter one changes the
POPULATION, not just the noise.** At 0.35 `warriner_valence` is computed on 33%
of the battery and `brooke_formality` on 1%, and Warriner's median `n_words`
climbs 72 -> 90 as the gate tightens: those are not the same prompts. 0.20 keeps
61-81% of rows for the lexicons that carry the results. The producer prints the
surviving share per scale so the trade is visible rather than asserted.

## TWO THINGS THE GATE DOES NOT DO, WHICH IS HOW IT EARNS TRUST

`k_vulgarity` stays tied on 42 of 50 lineages at every gate. Its ties were never
a coverage artefact -- vulgarity has almost no mass anywhere in this battery --
and a filter that could rescue it would be a filter that manufactures results.
`k_charge` stays null at every gate (23/20, 25/25, 25/25, 22/26).

`brooke_formality` is excluded BY NAME, not by threshold: it is marked sparse in
`lexicons/PROVENANCE.md`, and across the sweep it flips direction (11/23, then
12/31, then 6/31) while its p falls. Letting a coverage number exclude it would
be luck; naming it is the claim.
"""
import argparse, collections, gzip, json, math, os, statistics as st, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, ROOT)
#: **EVERY TABLE THAT HAS COVERAGE COLUMNS, NOT JUST LEVELS.** The first
#: version built `levels` only, and `plot_fields.py --combine --marginal
#: --gated` then asked it for `contextual`, got nothing back, and rendered a
#: levels-only figure under a name that said `v6`. No error: an empty filter
#: returns an empty list, and a chart with fewer rows than expected looks like
#: a strict gate rather than a missing table.
SRC = os.path.expanduser("~/malignment-data/norm_change/%s_long_v4.csv.gz")
OUT = os.path.join(HERE, "results", "%s_gated_en.json")
TABLES = ("levels", "contextual")
GATE = 0.20
MIN_SIGNED = 40
#: marked sparse in lexicons/PROVENANCE.md -- excluded by NAME, see the docstring
SPARSE = {"brooke_formality", "brooke_formality_z", "brooke_formality_absz"}


def sign_p(k, n):
    return (min(1.0, 2 * sum(math.comb(n, j) for j in range(0, min(k, n - k) + 1))
                / 2.0 ** n) if n else float("nan"))


def build(gate=GATE, table="levels"):
    from malignment import roster
    eps, _ = roster.endpoints()
    keep = {"%s>%s" % (b, a) for b, a in eps.items()}
    acc = collections.defaultdict(lambda: collections.defaultdict(list))
    seen = collections.Counter()
    with gzip.open(SRC % table, "rt") as fh:
        head = fh.readline().rstrip("\n").split("\t")
        ix = {k: i for i, k in enumerate(head)}
        for line in fh:
            f = line.rstrip("\n").split("\t")
            if f[ix["lang"]] != "en":
                continue
            sc = f[ix["scale"]]
            if sc in SPARSE:
                continue
            lin = "%s>%s" % (f[ix["base"]], f[ix["aligned"]])
            if lin not in keep:
                continue
            try:
                d = float(f[ix["aligned_level"]]) - float(f[ix["base_level"]])
                #: the MINIMUM of the two arms: a mean computed over 80% of one
                #: distribution and 3% of the other is not a comparison, and
                #: gating on the base alone would let the aligned arm be thin
                cov = min(float(f[ix["base_cov"]]), float(f[ix["aligned_cov"]]))
            except ValueError:
                continue
            seen[sc] += 1
            if cov >= gate:
                acc[sc][lin].append(d)
    out = []
    for sc, by in sorted(acc.items()):
        per = {l: st.median(v) for l, v in by.items() if v}
        vals = list(per.values())
        up = sum(1 for x in vals if x > 0)
        dn = sum(1 for x in vals if x < 0)
        ties = len(vals) - up - dn
        kept = sum(len(v) for v in by.values())
        out.append({"scale": sc, "n_lineages": len(vals), "up": up, "down": dn,
                    "ties": ties, "effective_n": up + dn,
                    "median": st.median(vals) if vals else None,
                    "p_sign": sign_p(min(up, dn), up + dn),
                    "rows_kept": kept, "rows_seen": seen[sc],
                    "share_kept": (kept / seen[sc]) if seen[sc] else 0.0,
                    "per_lineage": per})
    return {"gate": gate, "table": table,
            "gate_on": "min(base_cov, aligned_cov)",
            "aggregator": "median over prompts, per lineage",
            "excluded_by_name": sorted(SPARSE), "min_signed": MIN_SIGNED,
            "built": time.strftime("%Y-%m-%d %H:%M"), "scales": out}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gate", type=float, default=GATE)
    ap.add_argument("--table", default="all",
                    choices=["all", "levels", "contextual"])
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    for table in (TABLES if a.table == "all" else (a.table,)):
        d = build(a.gate, table)
        out = a.out or (OUT % table)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        json.dump(d, open(out, "w"), indent=1)
        _report(d, out, table)


def _report(d, out, table):
    rows = [r for r in d["scales"] if not r["scale"].endswith("_z")]
    print("\n== %s ==  gate %.2f on %s | excluded by name: %s\n"
          % (table, d["gate"], d["gate_on"], ", ".join(sorted(SPARSE))))
    print("%-28s %8s %6s %9s %8s %8s" % ("scale", "up/dn", "ties", "median",
                                         "p", "rows kept"))
    for r in sorted(rows, key=lambda r: r["p_sign"]):
        flag = "" if r["effective_n"] >= MIN_SIGNED else "   <- under min_signed"
        print("%-28s %8s %6d %+9.5f %8.4f %7.0f%%%s"
              % (r["scale"], "%d/%d" % (r["up"], r["down"]), r["ties"],
                 r["median"], r["p_sign"], 100 * r["share_kept"], flag))
    print("\n-> %s" % out)


if __name__ == "__main__":
    main()
