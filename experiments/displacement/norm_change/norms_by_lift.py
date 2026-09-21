"""The marginal norm change, split by charge lift. -> results/levels_by_lift_en.json

    python -u norms_by_lift.py

## WHY THIS EXISTS AND WHY IT IS NOT A REDRAW

Figure 3's scatter carries one number per scale per lineage: the median over
prompts of `(aligned - base)`, gated on coverage. The Osgood remake wants that
median computed separately WITHIN LIFT TERTILES, so a row can show where
alignment takes a scale on the least charged prompts and on the most.

**THAT QUANTITY IS IN NO STORED ARTIFACT.** `norm_stats.json` and
`levels_gated_en.json` both hold `per_lineage: {lineage -> value}`, already
collapsed over prompts -- 127,232 rows seen, one number out per lineage. So the
triangles are a NEW STATISTIC over the 938 MB source, not a reshuffle, and they
want the scrutiny a new number gets.

## THE OVERALL MEDIAN IS RECOMPUTED AS A CHECK, NOT REUSED

Everything here repeats `gated_levels.build` exactly -- same gate on
`min(base_cov, aligned_cov)`, same `SPARSE` exclusion, same endpoint filter,
same median-over-prompts-per-lineage aggregator -- and then ALSO splits by
band. The ungrouped result must therefore equal `levels_gated_en.json` scale
for scale. It is asserted rather than assumed: if the two disagree, this file
has drifted from the one whose numbers are published, and the triangles would
be drawn against a square nobody can reproduce.

## THE BANDS ARE CUT ON PROMPTS, ONCE, ACROSS EVERYTHING

Tertiles of `charge.lift_per_lineage` -- `T_base - frame` for a (prompt, base)
pair, the dose the displacement work uses -- taken over every rated row rather
than within a scale. Cutting within a scale would give every scale the same
three bands by construction, which is the comparison the figure is for.

**ENGLISH ONLY**, because `charge` rates English prompts; rows with no lift are
counted and reported, not dropped silently.
"""
import collections, gzip, json, os, statistics as st, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
from gated_levels import GATE, SPARSE, SRC, sign_p  # noqa: E402


def build(table, lpl, keep):
    """One table, gated, with a lift band per row. -> (scales, n_all, n_nolift)"""
    import statistics as st
    rows = []
    n_all = n_nolift = 0
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
                cov = min(float(f[ix["base_cov"]]), float(f[ix["aligned_cov"]]))
            except ValueError:
                continue
            if cov < GATE:
                continue
            n_all += 1
            lift = lpl.get((f[ix["prompt"]], f[ix["base"]]))
            if lift is None:
                n_nolift += 1
            rows.append((sc, lin, d, lift))
    print("  %-11s gated rows %d, no lift %d (%.1f%%)"
          % (table, n_all, n_nolift, 100.0 * n_nolift / max(1, n_all)))

    #: **THE CUTS COME FROM `levels` AND ARE REUSED FOR `contextual`.** Two
    #: tables cut on their own quantiles would put the same prompt in
    #: different bands, and the figure draws rows from both on one axis.
    global CUTS, LIFT_MEAN, LIFT_BAND_MEAN, LIFT_MEDIAN, LIFT_BAND_MEDIAN
    if CUTS is None:
        vals = sorted(r[3] for r in rows if r[3] is not None)
        k = len(vals) // 3
        CUTS = (vals[k], vals[2 * k])
        #: **WHERE EACH BAND SITS ON THE LIFT AXIS, not just where it is cut.**
        #: A tertile cut says which rows are in a band; it does not say how far
        #: apart the bands are, and a fitted slope cannot be turned into a
        #: position without that distance. Computed from the SAME `vals` that
        #: produced the cuts -- gated rows, `levels`, row-weighted -- so the
        #: three means and the three bands are the same partition of the same
        #: population, not two descriptions that happen to share a name.
        parts = (vals[:k], vals[k:2 * k], vals[2 * k:])
        LIFT_MEAN = sum(vals) / len(vals)
        LIFT_BAND_MEAN = [sum(v) / len(v) for v in parts]
        #: **AND THE MEDIANS, BECAUSE THE OUTCOME IS A MEDIAN.** Comparing a
        #: band MEAN lift against a band MEDIAN outcome mixes two estimators
        #: on opposite sides of one ratio, and lift is right-skewed enough for
        #: that to matter: the top band is cut at +0.360 and has a mean of
        #: +0.952, which only happens with a long tail. The fitted triangles
        #: use the MEAN (an OLS slope is a mean-based fit, so the mean lift is
        #: where it is evaluated); the under-reporting diagnostic uses the
        #: MEDIAN against the median outcome.
        LIFT_MEDIAN = st.median(vals)
        LIFT_BAND_MEDIAN = [st.median(v) for v in parts]
        print("  lift tertile cuts (from %s, reused): %+.3f and %+.3f"
              % (table, *CUTS))
        print("  lift band means:   low %+.3f  mid %+.3f  high %+.3f  (all %+.3f)"
              % (*LIFT_BAND_MEAN, LIFT_MEAN))
        print("  lift band medians: low %+.3f  mid %+.3f  high %+.3f  (all %+.3f)"
              % (*LIFT_BAND_MEDIAN, LIFT_MEDIAN))
    lo, hi = CUTS

    def band(v):
        return None if v is None else (0 if v <= lo else (1 if v <= hi else 2))

    acc = collections.defaultdict(lambda: collections.defaultdict(list))
    bacc = collections.defaultdict(
        lambda: [collections.defaultdict(list) for _ in range(3)])
    for sc, lin, d, lift in rows:
        acc[sc][lin].append(d)
        b = band(lift)
        if b is not None:
            bacc[sc][b][lin].append(d)

    out = []
    for sc in sorted(acc):
        per = {l: st.median(v) for l, v in acc[sc].items() if v}
        v = list(per.values())
        up = sum(1 for x in v if x > 0)
        dn = sum(1 for x in v if x < 0)
        rec = {"scale": sc, "n_lineages": len(v), "up": up, "down": dn,
               "ties": len(v) - up - dn, "effective_n": up + dn,
               "median": st.median(v) if v else None,
               "p_sign": sign_p(min(up, dn), up + dn), "bands": []}
        for b in range(3):
            pb = {l: st.median(x) for l, x in bacc[sc][b].items() if x}
            vb = list(pb.values())
            rec["bands"].append(
                {"band": ("low", "mid", "high")[b], "n_lineages": len(vb),
                 "median": st.median(vb) if vb else None,
                 "up": sum(1 for x in vb if x > 0),
                 "down": sum(1 for x in vb if x < 0)})
        out.append(rec)

    #: **THE ASSERTION IS THE POINT OF RECOMPUTING IT.**
    ref = {s["scale"]: s for s in json.load(
        open(os.path.join(HERE, "results",
                          "%s_gated_en.json" % table)))["scales"]}
    bad = []
    for r in out:
        g = ref.get(r["scale"])
        if g is None:
            continue
        if abs((g["median"] or 0) - (r["median"] or 0)) > 1e-9 \
                or g["effective_n"] != r["effective_n"]:
            bad.append("%s: stored median %s n %s, here %s n %s"
                       % (r["scale"], g["median"], g["effective_n"],
                          r["median"], r["effective_n"]))
    print("  REPRODUCTION OF %s_gated_en.json: %s" % (table,
          ("%d scales match" % sum(1 for r in out if r["scale"] in ref)
           if not bad else "MISMATCH on %d" % len(bad))))
    for b in bad[:6]:
        print("  " + b)
    if bad:
        raise SystemExit("refusing to write: the ungrouped result must equal "
                         "the published artifact or the bands are drawn "
                         "against a square nobody can reproduce")

    return out, n_all, n_nolift


CUTS = None
#: set beside CUTS, from the same vals. See the comment there.
LIFT_MEAN = None
LIFT_BAND_MEAN = None
LIFT_MEDIAN = None
LIFT_BAND_MEDIAN = None


def main():
    from malignment import roster, charge
    eps, _ = roster.endpoints()
    keep = {"%s>%s" % (b, a) for b, a in eps.items()}
    lpl = charge.lifts_per_lineage()
    print("lift cells: %d" % len(lpl))
    allsc, tot, nol = [], 0, 0
    for table in ("levels", "contextual"):
        out, n, nn = build(table, lpl, keep)
        for r in out:
            r["table"] = table
        allsc += out; tot += n; nol += nn
    p = os.path.join(HERE, "results", "norms_by_lift_en.json")
    json.dump({"gate": GATE, "gate_on": "min(base_cov, aligned_cov)",
               "aggregator": "median over prompts, per lineage, per band",
               "lift": "charge.lift_per_lineage (T_base - frame)",
               "cuts": list(CUTS), "lift_mean": LIFT_MEAN,
               "lift_band_mean": LIFT_BAND_MEAN,
               "lift_median": LIFT_MEDIAN,
               "lift_band_median": LIFT_BAND_MEDIAN,
               "rows_gated": tot, "rows_no_lift": nol,
               "excluded_by_name": sorted(SPARSE),
               "built": time.strftime("%Y-%m-%d %H:%M"), "scales": allsc},
              open(p, "w"), indent=1)
    print("wrote %s  (%d scales)" % (p, len(allsc)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
