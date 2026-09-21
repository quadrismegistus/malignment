"""The norm LEVEL by lift band, z-scored, instead of the change. -> results/norms_levels_z_en.json

    python -u norms_levels_z.py

## WHY A LEVEL AND NOT A CHANGE

Every earlier plate drew `aligned - base` divided by the between-lineage SD of
those per-lineage differences. That denominator is a different number for every
row -- 0.0004 on `k_vulgarity`, 0.0966 on `v6:fit`, a factor of 250 -- so the
rows are not on a common ruler and the plate's visual ordering is partly an
ordering of tie rates. See `FIGURE3_OF_RECORD.md`.

**THE Z HERE IS THE SPREAD OF THE NORM ITSELF**, pooled over the base and
aligned values of every gated row for that scale, so one SD means the same kind
of thing on every row: how far apart the words on this scale actually are. A
movement of 0.2 is then a fifth of the spread of concreteness among the words
alignment touched, which is sayable, and comparable down the column.

**NEITHER ARM IS THE ANCHOR.** z over the POOLED values, not over base alone.
Centring on base would put every base marker at 0.000 by construction and make
the base side of the plate a definition again -- the same defect as orienting
rows by their destination.

## MEDIANS SURVIVE THE TRANSFORM, WHICH IS WHY THIS IS CHEAP

z is monotone linear, so median(z) == (median(raw) - mu) / sigma. The medians
are taken on raw values and transformed once at the end; nothing is stored twice
and no second pass is needed.

## THE UNIT IS STILL THE LINEAGE

Median over prompts within a lineage, then median over the 50 lineages, exactly
as `norms_by_lift`. A per-row median over pooled prompts would weight a lineage
by how many prompts cleared its coverage gate.
"""
import collections, gzip, json, os, statistics as st, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
from gated_levels import GATE, SPARSE, SRC  # noqa: E402

CUTS = None


def build(table, lpl, keep):
    global CUTS
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
                b = float(f[ix["base_level"]])
                a = float(f[ix["aligned_level"]])
                cov = min(float(f[ix["base_cov"]]), float(f[ix["aligned_cov"]]))
            except ValueError:
                continue
            if cov < GATE:
                continue
            n_all += 1
            lift = lpl.get((f[ix["prompt"]], f[ix["base"]]))
            if lift is None:
                n_nolift += 1
            rows.append((sc, lin, b, a, lift))
    print("  %-11s gated rows %d, no lift %d (%.1f%%)"
          % (table, n_all, n_nolift, 100.0 * n_nolift / max(1, n_all)))

    #: cuts from `levels`, reused -- same rule as norms_by_lift, and asserted
    #: equal to its stored cuts below so the two plates band identically.
    if CUTS is None:
        vals = sorted(r[4] for r in rows if r[4] is not None)
        CUTS = (vals[len(vals) // 3], vals[2 * len(vals) // 3])
        print("  lift tertile cuts: %+.3f and %+.3f" % CUTS)
    lo, hi = CUTS

    def band(v):
        return None if v is None else (0 if v <= lo else (1 if v <= hi else 2))

    #: z parameters from the POOLED base and aligned values, running sums
    agg = collections.defaultdict(lambda: [0, 0.0, 0.0])
    #: [band][lineage] -> ([base], [aligned]); band 3 is ALL prompts
    acc = collections.defaultdict(
        lambda: [collections.defaultdict(lambda: ([], [], []))
                 for _ in range(4)])
    for sc, lin, b, a, lift in rows:
        g = agg[sc]
        g[0] += 2; g[1] += b + a; g[2] += b * b + a * a
        for k in (3,) + ((band(lift),) if band(lift) is not None else ()):
            p = acc[sc][k][lin]
            #: **THE MOVE IS PER ROW, AND IT IS KEPT SEPARATELY.** A median
            #: does not commute with a difference, so `median(a) - median(b)`
            #: is not the median move -- on `warriner_valence` the two differ
            #: by 63 percent. Only the per-row difference, medianed within the
            #: lineage, reproduces the published marginal.
            p[0].append(b); p[1].append(a); p[2].append(a - b)

    out = []
    for sc in sorted(acc):
        n, s1, s2 = agg[sc]
        mu = s1 / n
        var = max(0.0, s2 / n - mu * mu)
        sd = var ** 0.5
        if sd <= 0:
            print("  SKIP %s: the scale has no spread (sd=0)" % sc)
            continue
        rec = {"scale": sc, "table": table, "mu": mu, "sd": sd, "n_values": n,
               "bands": []}
        for k, name in enumerate(("low", "mid", "high", "all")):
            per_b, per_a, d, dm = [], [], [], []
            for lin, (bs, asg, ds) in acc[sc][k].items():
                if bs:
                    per_b.append(st.median(bs)); per_a.append(st.median(asg))
                    d.append(st.median(ds))
                    #: **THE MEAN WITHIN THE LINEAGE IS WHERE THE TIE PILE
                    #: LIVES OR DIES.** A median over prompts lands on exactly
                    #: 0.000 whenever most prompts in that lineage did not
                    #: move; a mean over the same prompts does not, because one
                    #: moved prompt is enough. The scales are bounded (1-7,
                    #: 1-9) and so are the differences, so the usual objection
                    #: to a mean -- one outlier carries it -- has a ceiling
                    #: here that it does not have on an unbounded quantity.
                    dm.append(st.fmean(ds))
            if not per_b:
                rec["bands"].append({"band": name, "n_lineages": 0})
                continue
            mb, ma = st.median(per_b), st.median(per_a)
            #: **`move_z` IS THE MEDIAN OF THE MOVES, NOT THE MOVE BETWEEN THE
            #: MEDIANS.** The two differ -- on `k_register_level` by nearly a
            #: factor of two -- because a median does not commute with a
            #: difference. The unit of this whole folder is the LINEAGE, so
            #: the per-lineage move is the thing to summarise; the difference
            #: of the two marginal medians is a property of two separately
            #: ranked columns and no lineage need exhibit it. `spread_z`
            #: keeps the other one, because the base and aligned PROFILES are
            #: worth drawing and they are built from `base_z`/`aligned_z`,
            #: whose difference is exactly it.
            rec["bands"].append({
                "band": name, "n_lineages": len(per_b),
                "base_z": (mb - mu) / sd, "aligned_z": (ma - mu) / sd,
                "move_z": st.median(d) / sd,
                "move_mean_z": st.median(dm) / sd,
                "move_meanmean_z": st.fmean(dm) / sd,
                "spread_z": (ma - mb) / sd,
                "tied_median": sum(1 for x in d if x == 0.0),
                "tied_mean": sum(1 for x in dm if x == 0.0),
                "up_mean": sum(1 for x in dm if x > 0),
                "down_mean": sum(1 for x in dm if x < 0),
                "up": sum(1 for x in d if x > 0),
                "down": sum(1 for x in d if x < 0)})
        out.append(rec)
    return out, n_all, n_nolift


def main():
    from malignment import roster, charge
    eps, _ = roster.endpoints()
    keep = {"%s>%s" % (b, a) for b, a in eps.items()}
    lpl = charge.lifts_per_lineage()
    print("lift cells: %d" % len(lpl))
    allsc, tot, nol = [], 0, 0
    for table in ("levels", "contextual"):
        o, n, nn = build(table, lpl, keep)
        allsc += o; tot += n; nol += nn
    #: **THE BANDS MUST BE THE SAME BANDS.** A plate drawn beside the change
    #: plate with different cuts is two populations wearing one set of labels.
    ref = json.load(open(os.path.join(HERE, "results",
                                      "norms_by_lift_en.json")))["cuts"]
    if [round(c, 9) for c in CUTS] != [round(c, 9) for c in ref]:
        raise SystemExit("refusing to write: cuts %s != norms_by_lift %s"
                         % (list(CUTS), ref))
    print("  cuts match norms_by_lift_en.json: %s" % (list(CUTS),))
    #: **AND THE ALL-PROMPT MOVE MUST REPRODUCE THE PUBLISHED MARGINAL.**
    #: `move_z` differs from it only by the divisor, so multiplying back has
    #: to land on `*_gated_en.json` exactly. This is the gate that would have
    #: caught the two wrong statistics this file shipped before it: a
    #: difference of medians across lineages, then a difference of per-lineage
    #: medians. Both looked right and neither reproduced anything.
    pub = {}
    for t in ("levels", "contextual"):
        for x in json.load(open(os.path.join(
                HERE, "results", "%s_gated_en.json" % t)))["scales"]:
            pub[(t, x["scale"])] = x["median"]
    bad = []
    for r in allsc:
        want = pub.get((r["table"], r["scale"]))
        got = [b for b in r["bands"] if b["band"] == "all"]
        if want is None or not got or "move_z" not in got[0]:
            continue
        if abs(got[0]["move_z"] * r["sd"] - want) > 1e-9:
            bad.append("%s/%s: published %s, here %s"
                       % (r["table"], r["scale"], want,
                          got[0]["move_z"] * r["sd"]))
    print("  REPRODUCTION of the published marginal: %s"
          % ("%d scales match" % (len(allsc) - len(bad)) if not bad
             else "MISMATCH on %d" % len(bad)))
    for b in bad[:6]:
        print("  " + b)
    if bad:
        raise SystemExit("refusing to write: move_z x sd must equal the "
                         "published median or the plate is drawn against a "
                         "quantity nobody can reproduce")
    p = os.path.join(HERE, "results", "norms_levels_z_en.json")
    json.dump({"gate": GATE, "cuts": list(CUTS),
               "z": "pooled base and aligned values of that scale, all gated "
                    "en rows; median(z) == (median(raw)-mu)/sd",
               "aggregator": "median over prompts per lineage, then over "
                             "lineages", "rows_gated": tot,
               "rows_no_lift": nol, "built": time.strftime("%Y-%m-%d %H:%M"),
               "scales": allsc}, open(p, "w"), indent=1)
    print("wrote %s  (%d scales)" % (p, len(allsc)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
