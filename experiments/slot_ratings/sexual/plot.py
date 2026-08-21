"""Figures for the sexual study. One function per figure.

    python experiments/slot_ratings/sexual/plot.py            # all
    python experiments/slot_ratings/sexual/plot.py --list
    python experiments/slot_ratings/sexual/plot.py gender_slopes

Same shape as `institutional/plot.py`: a producer computes and asserts, and a
LayerChart component in the app draws the artifact. NO app change was needed for
this figure -- it declares `chart: "slopes"` and the existing component draws it,
which is the property `malignment/chartdata.py` exists to make true.
"""

import argparse, collections, json, os, statistics as st, sys

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
FIGDIR = os.path.join(HERE, "figures")

#: The same two-colour convention as the institutional slopegraph. The contrast
#: is different -- male slot against female slot rather than individual against
#: institution -- and keeping one palette across the study lets a reader carry
#: the habit from one figure to the next.
MALE, FEMALE = "#e67e22", "#2980b9"


def _gender_frame():
    """Levels per (gender, arm, scale), on EXACTLY the population `within` uses.

    `gender_pairs.json` books per-gender deltas but not the levels behind them, so
    the levels are recomputed here -- and the recomputation is only trustworthy if
    it lands on the same population, which is why it asserts.

    THREE THINGS HAD TO MATCH, and each was found by the numbers not matching:

      1. the pairs are those matched sets carrying BOTH genders, `full` in
         `gender_pairs.py:232`
      2. the unit is the (lineage, pair) CELL, averaged before the mean over
         cells -- not a flat mean over rows
      3. a row counts only if BOTH arms are present for that scale

    (3) is the one that looks pedantic and is not. Coverage differs by arm, so
    rows exist with one arm and not the other; include them and MEAN-OF-DIFFERENCES
    stops equalling DIFFERENCE-OF-MEANS. With all three the reconstruction lands
    on the booked deltas to 5.6e-16; with only the first two it is out by up to
    5.8e-3, which is small enough to look like rounding and is not.
    """
    with open(os.path.join(RES, "gender_pairs.json")) as fh:
        d = json.load(fh)
    rows, within = d["rows"], {r["scale"]: r for r in d["within"]}
    gaps = {r["scale"]: r for r in d["gaps"]}

    bypair = collections.defaultdict(set)
    for r in rows:
        bypair[r["pair"]].add(r["gender"])
    keep = {p for p, g in bypair.items() if {"male", "female"} <= g}

    lv, meta = {}, {}
    for s in sorted(within):
        for g in ("male", "female"):
            cb, ca = collections.defaultdict(list), collections.defaultdict(list)
            for r in rows:
                if r["gender"] != g or r["pair"] not in keep:
                    continue
                b, a = r.get("base_" + s), r.get("aligned_" + s)
                if b is None or a is None:
                    continue
                k = (r["lineage"], r["pair"])
                cb[k].append(b)
                ca[k].append(a)
            lv[(s, g, "base")] = st.mean([st.mean(v) for v in cb.values()])
            lv[(s, g, "aligned")] = st.mean([st.mean(v) for v in ca.values()])
        #: THE BOOKED-VALUE GUARD. If the population drifts, these stop matching
        #: and the figure refuses rather than drawing levels from a different set.
        for g, key in (("male", "male_delta"), ("female", "female_delta")):
            got = lv[(s, g, "aligned")] - lv[(s, g, "base")]
            assert abs(got - within[s][key]) < 1e-9, (
                "%s %s: recomputed %+.6f, booked %+.6f -- population drift"
                % (s, g, got, within[s][key]))
        four = [lv[(s, g, a)] for g in ("male", "female") for a in ("base", "aligned")]
        meta[s] = dict(mid=(min(four) + max(four)) / 2, lo=min(four), hi=max(four),
                       span=max(four) - min(four),
                       delta_gap=gaps[s]["delta_gap"], delta_p=gaps[s]["delta_p"],
                       base_gap=gaps[s]["base_gap"], base_p=gaps[s]["base_p"])
    order = sorted(meta, key=lambda s: -abs(meta[s]["delta_gap"]))
    return lv, meta, order, len({r["lineage"] for r in rows}), len(keep)


def fig_gender_slopes():
    """Base to aligned, two lines per scale, coloured by whose body is in the slot."""
    from malignment.chartdata import slopes, write

    lv, meta, order, n_lin, n_pairs = _gender_frame()
    span = max(m["span"] for m in meta.values())
    #: Chosen FROM the data and asserted, as in the institutional figure: a
    #: window that clips a line makes a panel understate the movement it exists
    #: to show, and a scale-free auto-domain per panel makes tiny movements draw
    #: as steep as large ones.
    dom = 0.25
    assert span <= 2 * dom, "widest scale spans %.3f, past the +-%.2f window" % (span, dom)

    #: NO SIGNIFICANCE MARK. `gaps` books `delta_p` and no interval, and a binary
    #: star on a bootstrap p is a coin flip wherever the value sits near the cut
    #: -- the failure this seat corrected on the institutional figure. The p is
    #: printed instead, so the reader judges rather than inherits a threshold.
    lab = lambda s: "%s  %+.3f  p %.3f" % (s, meta[s]["delta_gap"], meta[s]["delta_p"])
    art = slopes(
        title="Alignment moves both genders the same way, and the gap it found stays put",
        subtitle="Parallel lines are a null; the asymmetry is the fanning.",
        stat_label="change in gap (male − female)",
        note_label="absolute range across all four points",
        x_order=["base", "aligned"],
        series=[{"key": "male slot", "colour": MALE},
                {"key": "female slot", "colour": FEMALE}],
        y_domain=[-dom, dom],
        panels=[{"key": s, "label": lab(s),
                 "note": "%.2f-%.2f" % (meta[s]["lo"], meta[s]["hi"]),
                 "did": round(meta[s]["delta_gap"], 6), "mark": ""}
                for s in order],
        rows=[{"panel": s, "series": g + " slot", "x": a,
               "y": round(lv[(s, g, a)] - meta[s]["mid"], 6),
               "level": round(lv[(s, g, a)], 6)}
              for s in order for g in ("male", "female") for a in ("base", "aligned")],
    )
    assert len(art["panels"]) == 12, "12 v6 scales expected, got %d" % len(art["panels"])
    write(art, FIGDIR, "gender_slopes")

    #: Sidecar caption, per the protocol: ONE LINE on the figure, the reasoning
    #: beneath it. The figure must not be misleading standing alone; everything
    #: that only says HOW it was made lives here.
    with open(os.path.join(FIGDIR, "gender_slopes.caption.md"), "w") as fh:
        fh.write("""`slot_ratings/sexual`. Produced by `plot.py gender_slopes` from
`results/gender_pairs.json`.

Eight gender-swapped matched pairs -- the same scene with the gender swapped --
over %d lineages and %d matched sets carrying both genders. Gender is WHOSE BODY
THE SLOT CONTENT ATTACHES TO, not the grammatical subject: `She unzipped his ___`
is a male slot.

## What it shows

Alignment moves the two genders the same way. The lines run near-parallel on
every scale, so the gap alignment found is the gap it leaves: the base is
asymmetric and the change in that asymmetry is not. `hedged` is the only panel
whose change clears p<0.05 (+0.010, p=0.032), and it is one result among twelve
scales tested, so it is a lead rather than a finding.

## Why the p and not a star

`gender_pairs.json` books `delta_p` and no interval. A binary mark on a bootstrap
p is a coin flip wherever the value sits near the cut, so the p is printed and
the reader judges. The institutional slopegraph can distinguish a boundary case
because its artifact carries intervals; this one cannot, and says so rather than
implying a cleanliness it has not measured.

## The estimator, because the levels are recomputed

The artifact books per-gender DELTAS and not the levels behind them, so the
levels are recomputed and asserted against those deltas -- they reproduce to
5.6e-16. Three things had to match: the pairs are the matched sets carrying both
genders, the unit is the (lineage, pair) cell averaged before the mean over
cells, and a row counts only if BOTH arms are present for that scale. The last
looks pedantic and is not: coverage differs by arm, and including one-armed rows
stops mean-of-differences equalling difference-of-means. With only the first two
the reconstruction is out by up to 5.8e-3 -- small enough to look like rounding.

## Fences

- v6 scales only. The institutional scales that carried the sharpest results
  elsewhere (`mediation`, `procedural`, `deference`) are not measured on these
  frames.
- Eight pairs and %d lineages is modest power; a null here bounds an effect
  rather than excluding it.
- The gender contrast averages over five role types (object, agent, target,
  experiencer, patient). At this n there is no room to test role by gender.
""" % (n_lin, n_pairs, n_lin))
    print("   %-38s %d lineages, %d matched pairs, widest span %.3f"
          % ("", n_lin, n_pairs, span))


FIGURES = {"gender_slopes": fig_gender_slopes}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("names", nargs="*", help="figures to draw (default: all)")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args(argv)
    if a.list:
        for k, f in sorted(FIGURES.items()):
            print("  %-18s %s" % (k, (f.__doc__ or "").strip().splitlines()[0]))
        return
    todo = a.names or sorted(FIGURES)
    unknown = [n for n in todo if n not in FIGURES]
    if unknown:
        raise SystemExit("unknown: %s (see --list)" % ", ".join(unknown))
    for n in todo:
        print(n)
        FIGURES[n]()


if __name__ == "__main__":
    main()
