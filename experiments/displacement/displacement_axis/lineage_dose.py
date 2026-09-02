"""The lineage as the unit, and the dose response this folder never ran.

    python -u lineage_dose.py                    # pilot3, all tables
    python -u lineage_dose.py --domain identity
    python -u lineage_dose.py --run pilot3 --out ~/malignment-data/displacement_axis

Two jobs, one pass, because they need the same join and the same gate.

## 1. THE UNIT

`mass_direction.py:173` collapses a frame's lineages to their median and signs
across FRAMES. That is deliberate and its reason is sound -- twenty lineages of
one prompt are not twenty observations of a domain -- but it generalises over
STIMULI with the models pooled inside, and `identity fit 69/71 p=2.2e-18` is a
statement about this prompt corpus, not about alignment. Everywhere else in
`experiments/displacement/` the LINEAGE is the unit, because the models are the
sampled thing and the claim is about what alignment does. `norm_change` and
`rate_and_magnitude` both report on 50 endpoint pairs.

**Neither collapse is wrong and they answer different questions**, so this file
prints both side by side rather than replacing one. What it refuses to do is let
a frame-unit p-value stand next to a lineage-unit one without saying which is
which.

A structural consequence worth stating before any number is read: pilot3 holds
21 lineages, so a lineage-unit sign test CANNOT go below p = 2 * 0.5^21 = 9.5e-07
however perfect the agreement. The e-18s do not survive translation and their
disappearance is arithmetic, not a failure to replicate.

## 2. THE DOSE

The README's own conditional section -- `base_naughty_mass` quartiles, displacement
rate 2%/11%/28%/38% -- is a crosstab over 5,595 CELLS with no slope, no
lineage-level test and no p-value. It is 170 lines above the naming section and
the two are never crossed, so the folder holds both halves of the obvious
question and never asks it:

    does the named-scale signal STRENGTHEN where the base arm is transgressive?

Three quantities, all with the lineage as the unit and ties excluded:

    MARGINAL     per lineage, median dN over its gated cells
    DOSE         per lineage, OLS slope of dN on base_naughty_mass across cells
    NAMING GAIN  per lineage, median |dN|/nullabs in the high-dose half minus the
                 low-dose half, split at that lineage's OWN median dose

`base_naughty_mass` is measured on the BASE arm, before alignment touches it, so
the predictor cannot be selected on the outcome: a frame loaded with
transgressive mass at base is free to move up, down or not at all.

NAMING GAIN is the one that answers the crossed question. `nullabs` is the median
absolute dN over permutations that shuffle the word-to-rating link within the
frame's own vocabulary, so the ratio asks how much further the centroid travels
along a named dimension than along a reshuffle of that same dimension's values.
If naming works better under load, the ratio rises with dose.

## THE GATE COMES ACROSS UNCHANGED

Where a scale is near-constant over a frame's vocabulary, dN and every
permutation of it are both ~0 and the ratio pins at 1.00x. `sd_<scale> >= 0.5`,
identical to `mass_direction.py`, applied per (cell, scale). It is not optional
here: an ungated ratio is a ratio of two noise floors and the dose split would
sort cells by how many rated words they had.
"""

import argparse, collections, csv, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))

SCALES = ["aggression", "deliberation", "directedness", "fit", "harm", "hedged",
          "interiority", "makes_better", "makes_worse", "mundanity", "superego",
          "vocalisation"]
DOMAINS = ["identity", "institutional", "violence", "sexual"]
DOSE = "base_naughty_mass"
GATE = 0.5
MIN_CELLS = 12          # per lineage, for a slope or a dose split
MIN_UNITS = 6           # signed units below which a sign test is not printed


def binom(k, n):
    """Two-sided exact sign-test p."""
    if not n:
        return float("nan")
    lo = min(k, n - k)
    return min(1.0, 2.0 * sum(math.comb(n, j) for j in range(lo + 1)) / 2.0 ** n)


def sign(vals):
    """-> (n, up, dn, ties, median_nonzero, p) or None."""
    import statistics as st
    up = sum(1 for x in vals if x > 0)
    dn = sum(1 for x in vals if x < 0)
    ties = len(vals) - up - dn
    if up + dn < MIN_UNITS:
        return None
    nz = [x for x in vals if x != 0]
    return (len(vals), up, dn, ties, st.median(nz), binom(up, up + dn))


def ols(xs, ys):
    """Slope of y on x, or None if x is constant."""
    n = len(xs)
    mx = sum(xs) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx <= 0:
        return None
    my = sum(ys) / n
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx


def load(run, use_lift=False):
    """-> rows with dN/sd/nullabs per scale plus the dose, joined and checked."""
    d = os.path.join(HERE, "results", run)
    dose_of = {}
    lift_of = {}
    with open(os.path.join(d, "cells.jsonl")) as fh:
        for line in fh:
            r = json.loads(line)
            dose_of[(r["base"], r["endpoint"], r["item_id"])] = r.get(DOSE)
    if use_lift:
        from malignment import charge
        lpl = charge.lifts_per_lineage()
        prompts_by_item = {}
        with open(os.path.join(d, "cells.jsonl")) as fh:
            for line in fh:
                r = json.loads(line)
                prompts_by_item[r["item_id"]] = r.get("prompt", "")
    rows, missing = [], 0
    with open(os.path.join(d, "long", "mass_cells.csv")) as fh:
        for r in csv.DictReader(fh):
            k = (r["base"], r["endpoint"], r["item"])
            if use_lift:
                pr = prompts_by_item.get(r["item"], r.get("prompt", ""))
                v = lpl.get((pr, r["base"]))
            else:
                v = dose_of.get(k)
            if v is None:
                missing += 1
                continue
            r["_dose"] = float(v)
            r["_lin"] = "%s>%s" % (r["base"], r["endpoint"])
            rows.append(r)
    dose_name = "lift (T_base - frame)" if use_lift else DOSE
    if missing:
        print("WARNING: %d cells had no %s and were dropped" % (missing, dose_name))

    #: mass_cells is written post-dedupe; assert it rather than trust it, since
    #: a triplicated prompt would inflate every per-lineage median silently.
    items = {r["item"] for r in rows}
    prompts = {r["prompt"] for r in rows}
    if len(items) != len(prompts):
        print("WARNING: %d items over %d prompts -- dedupe NOT applied"
              % (len(items), len(prompts)))

    #: and the population must be endpoint pairs, not the movement roster
    try:
        from malignment import roster
        #: endpoints() returns (mapping, ...) -- the first element is base -> aligned
        m = roster.endpoints()
        m = m[0] if isinstance(m, tuple) else m
        ep = {"%s>%s" % (b, a) for b, a in m.items()}
        seen = {r["_lin"] for r in rows}
        off = seen - ep
        print("population: %d lineages, %d of them in roster.endpoints() (%d declared)"
              % (len(seen), len(seen & ep), len(ep)))
        if off:
            print("  NOT endpoints: %s" % sorted(off)[:5])
    except Exception as e:
        print("roster check skipped: %s" % e)
    return rows


def gated(rows, scale, domain):
    """Cells where this scale actually varies, in this domain (None = pooled)."""
    out = []
    for r in rows:
        if domain and r["domain"] != domain:
            continue
        sd = r.get("sd_" + scale)
        dn = r.get("dN_" + scale)
        if not sd or not dn or sd == "" or dn == "":
            continue
        try:
            if float(sd) < GATE:
                continue
            out.append((r["_lin"], float(dn), r["_dose"],
                        float(r.get("nullabs_" + scale) or 0.0)))
        except ValueError:
            continue
    return out


def per_lineage(cells):
    d = collections.defaultdict(list)
    for lin, dn, dose, nul in cells:
        d[lin].append((dn, dose, nul))
    return d


def analyse(rows, domain, writer=None):
    import statistics as st
    cellrows = []
    for sc in SCALES:
        cells = gated(rows, sc, domain)
        if len(cells) < MIN_CELLS:
            continue
        by = per_lineage(cells)

        #: MARGINAL, lineage unit
        marg = sign([st.median([x[0] for x in v]) for v in by.values() if v])

        #: MARGINAL, frame unit -- mass_direction.py's own collapse, recomputed
        #: here so the two appear in one table and cannot be misread as one
        byfr = collections.defaultdict(list)
        for r in rows:
            if domain and r["domain"] != domain:
                continue
            sd, dn = r.get("sd_" + sc), r.get("dN_" + sc)
            if not sd or not dn:
                continue
            try:
                if float(sd) < GATE:
                    continue
                byfr[r["prompt"]].append(float(dn))
            except ValueError:
                continue
        frame = sign([st.median(v) for v in byfr.values() if v])

        #: DOSE, lineage unit
        slopes = {}
        for lin, v in by.items():
            if len(v) < MIN_CELLS:
                continue
            s = ols([x[1] for x in v], [x[0] for x in v])
            if s is not None:
                slopes[lin] = s
        dose = sign(list(slopes.values())) if slopes else None

        #: NAMING GAIN, lineage unit. |dN|/nullabs in the high-dose half minus
        #: the low-dose half, each lineage split at its own median dose.
        gains = {}
        for lin, v in by.items():
            if len(v) < MIN_CELLS:
                continue
            med = st.median([x[1] for x in v])
            hi = [abs(dn) / nul for dn, ds, nul in v if ds > med and nul > 0]
            lo = [abs(dn) / nul for dn, ds, nul in v if ds <= med and nul > 0]
            if len(hi) < 3 or len(lo) < 3:
                continue
            gains[lin] = st.median(hi) - st.median(lo)
        gain = sign(list(gains.values())) if gains else None

        cellrows.append((sc, len(cells), len(by), marg, frame, dose, gain))
        if writer:
            for lin in sorted(set(list(slopes) + list(gains))):
                writer.writerow({
                    "domain": domain or "POOLED", "scale": sc, "lineage": lin,
                    "n_cells": len(by.get(lin, [])),
                    "median_dN": st.median([x[0] for x in by[lin]]) if by.get(lin) else "",
                    "dose_slope": slopes.get(lin, ""),
                    "naming_gain": gains.get(lin, ""),
                })
    return cellrows


def fmt(s, star=True):
    if not s:
        return "        --        "
    n, up, dn, ties, med, p = s
    return "%+8.4f %2d/%-2d %8.2g%s" % (med, up, up + dn, p,
                                        "*" if (star and p < 0.05) else " ")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="pilot3")
    ap.add_argument("--domain", default=None)
    ap.add_argument("--lift-dose", action="store_true",
                    help="use per-lineage lift (T_base - frame) from charge instead "
                         "of base_naughty_mass. Lacan [6565]: lift predicts 3x better.")
    ap.add_argument("--out", default=None, help="dir for the long CSV")
    a = ap.parse_args(argv)

    rows = load(a.run, use_lift=a.lift_dose)
    dose_name = "lift (T_base - frame)" if a.lift_dose else DOSE
    print("%d cells joined, gate sd >= %.2f, ties excluded, min %d signed units"
          % (len(rows), GATE, MIN_UNITS))
    print("DOSE: %s" % dose_name)
    nlin = len({r["_lin"] for r in rows})
    print("FLOOR: with %d lineages a sign test cannot go below p = %.2g\n"
          % (nlin, 2.0 * 0.5 ** nlin))

    w = fh = None
    if a.out:
        os.makedirs(os.path.expanduser(a.out), exist_ok=True)
        p = os.path.join(os.path.expanduser(a.out), "lineage_dose_long.csv")
        fh = open(p, "w", newline="")
        w = csv.DictWriter(fh, fieldnames=["domain", "scale", "lineage", "n_cells",
                                           "median_dN", "dose_slope", "naming_gain"])
        w.writeheader()

    doms = [a.domain] if a.domain else DOMAINS + [None]
    for dom in doms:
        out = analyse(rows, dom, w)
        if not out:
            continue
        out.sort(key=lambda r: (r[5][5] if r[5] else 1.0))
        print("=" * 108)
        print("%s   (%d cells)" % ((dom or "POOLED, all domains").upper(),
                                   sum(r[1] for r in out) // max(1, len(out))))
        print("=" * 108)
        print("  %-13s %20s %20s %20s %20s"
              % ("scale", "MARGINAL lineage", "MARGINAL frame", "DOSE slope",
                 "NAMING GAIN hi-lo"))
        for sc, nc, nl, marg, frame, dose, gain in out:
            print("  %-13s %20s %20s %20s %20s"
                  % (sc, fmt(marg), fmt(frame), fmt(dose), fmt(gain)))
        print()

    #: THE CROSSED QUESTION, at the level the folder never asked it. One number
    #: per lineage -- its median naming gain over every (domain, scale) cell it
    #: contributes to -- so the 12 scales, which share cells and are anything but
    #: independent, cannot each cast a vote.
    import statistics as st
    glo = collections.defaultdict(list)
    ratio = {"hi": collections.defaultdict(list), "lo": collections.defaultdict(list)}
    for dom in DOMAINS:
        for sc in SCALES:
            cells = gated(rows, sc, dom)
            if len(cells) < MIN_CELLS:
                continue
            for lin, v in per_lineage(cells).items():
                if len(v) < MIN_CELLS:
                    continue
                med = st.median([x[1] for x in v])
                hi = [abs(dn) / nul for dn, ds, nul in v if ds > med and nul > 0]
                lo = [abs(dn) / nul for dn, ds, nul in v if ds <= med and nul > 0]
                if len(hi) < 3 or len(lo) < 3:
                    continue
                glo[lin].append(st.median(hi) - st.median(lo))
                ratio["hi"][lin].append(st.median(hi))
                ratio["lo"][lin].append(st.median(lo))
    print("=" * 108)
    print("DOES NAMING WORK BETTER UNDER DOSE? unit = lineage, one median per lineage")
    print("=" * 108)
    g = sign([st.median(v) for v in glo.values() if v])
    hi = sign([st.median(v) - 1.0 for v in ratio["hi"].values() if v])
    lo = sign([st.median(v) - 1.0 for v in ratio["lo"].values() if v])
    print("  |dN| / shuffled |dN|, LOW-dose half   %s   (vs 1.00x)" % fmt(lo))
    print("  |dN| / shuffled |dN|, HIGH-dose half  %s   (vs 1.00x)" % fmt(hi))
    print("  GAIN, high minus low                  %s" % fmt(g))
    print("  A named dimension beats a reshuffle of its own values by this much.")
    print("  1.00x = the scale explains no more of the travel than its permutation.")
    print()

    #: THE TRANSLATION, which is the point of printing both collapses. A result
    #: that holds under one unit and not the other is not a replication failure;
    #: it says which population the effect generalises over.
    print("=" * 108)
    print("TRANSLATION: what the change of unit does to the direction results")
    print("=" * 108)
    keep = drop = gain_ = both_ns = 0
    lost, found = [], []
    for dom in DOMAINS:
        for sc, nc, nl, marg, frame, dose, g in analyse(rows, dom):
            fs = bool(frame) and frame[5] < 0.05
            ls = bool(marg) and marg[5] < 0.05
            if fs and ls:
                keep += 1
            elif fs and not ls:
                drop += 1
                lost.append("%s %s (frame %.2g -> lineage %.2g)"
                            % (dom, sc, frame[5], marg[5] if marg else float("nan")))
            elif ls and not fs:
                gain_ += 1
                found.append("%s %s (frame %.2g -> lineage %.2g)"
                             % (dom, sc, frame[5] if frame else float("nan"), marg[5]))
            else:
                both_ns += 1
    print("  significant under BOTH units      %3d" % keep)
    print("  frame-unit only, LOST on lineages %3d" % drop)
    for s in lost:
        print("      %s" % s)
    print("  lineage-unit only, NEW            %3d" % gain_)
    for s in found:
        print("      %s" % s)
    print("  neither                           %3d" % both_ns)
    print()

    if fh:
        fh.close()
        print("wrote %s" % p)
    print("MARGINAL lineage/frame: median over units of the per-unit median dN.")
    print("DOSE: median per-lineage OLS slope of dN on %s." % DOSE)
    print("NAMING GAIN: median per-lineage (|dN|/nullabs high-dose half minus low).")
    print("Positive GAIN = the named dimension explains MORE of the travel where")
    print("the base arm carried transgressive mass. * = p < 0.05, uncorrected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
