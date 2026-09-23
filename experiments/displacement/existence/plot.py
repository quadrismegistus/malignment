"""Does selectivity grow with LIFT? The dose-response curve behind Part 1.

    python -u plot.py                      # the figure, screen render
    python -u plot.py --pub                # publication render
    python -u plot.py --json results/selectivity.json

## WHAT IT SHOWS, AND WHY THIS IS THE STEP UP FROM A SLOPEGRAPH

`exploratory/prompt_slopes` draws ONE prompt: what 50 lineages put at one blank
before and after alignment. This draws the whole battery with CHARGE as the
line identity -- the quantity Part 1 regresses on, banded.

The y value is the WITHIN-CELL SLOPE of `delta ~ scene`, one number per lineage
per band. **Negative means higher-charge words lose more mass**, so DOWN is more
selective and the zero rule is "alignment reshapes, but not by content".

`lift` = dose - frame, a property of the PROMPT: how much the candidate words
add beyond the setup. Where they add nothing there is nothing to select on, and
the claim under test is that selectivity grows as they add more.

## THE UNIT IS THE LINEAGE AND THE FIGURE SHOWS ALL 50

A median with an interval hides that some lineages go the other way, and seven
of them do overall. Every lineage is drawn, faintly; the median rides on top.
A band's n is printed on the axis because it is not constant -- the high band
rests on 2,562 cells against 94,424 in the low one, and a reader comparing two
medians should see that before they compare them.

## IT READS A CACHED ARTIFACT, AND THE ARTIFACT IS OLDER THAN ITS PRODUCER

`results/selectivity.json` was written 2026-09-03; `run.py` was modified
2026-09-11. **And the README's Part 1 lift table disagrees with this file on
every row** -- 12,184 cells against 13,811 at the `<0` band, 31/19 against
32/18, and a fifth band the prose does not mention. The monotonic gradient
survives in both; no individual number does.

So this producer prints the artifact's mtime in its own output and the figure
is only as current as that file. Re-run `run.py` before quoting anything from
here. It reads rather than recomputes ON PURPOSE: recomputing would give a
third set of numbers and no way to tell which of the three the prose meant.
"""
import argparse
import json
import statistics as st
import textwrap
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, ROOT)
FIGURES = os.path.join(HERE, "figures")
DEFAULT_JSON = os.path.join(HERE, "results", "selectivity.json")

PLOT = {
    "id": "lift_gradient",
    "name": "selectivity by lift",
    "blurb": "Does alignment get more content-selective as the candidate words "
             "add more charge beyond the setup? One line per lineage, median "
             "on top. Down is more selective.",
    "requires": ["plotnine"],
    "params": [
        {"name": "pub", "type": "choice", "default": "no",
         "choices": ["no", "yes"], "label": "publication render",
         "help": "strips the title and note (they are typeset as the legend), "
                 "encloses the panel, one sans-serif at one size, final size "
                 "4.8 x 3.36 in"},
        {"name": "show", "type": "choice", "default": "both",
         "choices": ["both", "median", "lineages"], "label": "show",
         "help": "both = 50 faint lineage lines with the median over them. "
                 "median alone hides that seven lineages run the other way"},
    ],
}


def load(path):
    """-> (bands, meta). Bands with no lineages are DROPPED and counted."""
    d = json.load(open(path))
    bands, dropped = [], []
    for b in d["by_lift"]:
        per = [r for r in b.get("per_lineage", []) if r.get("slope") is not None]
        #: **A BAND WITH 14 CELLS IS NOT A BAND.** `2+ (very high)` carries 14
        #: cells and 0 lineages that clear the per-cell minimum, so it has no
        #: median to draw. Dropped and NAMED -- silently omitting it would make
        #: the axis look like the whole range of lift, which it is not.
        if len(per) < 2:
            dropped.append((b["band"], b.get("n_cells", 0), len(per)))
            continue
        bands.append({"band": b["band"], "n_cells": b["n_cells"],
                      "neg": b["neg"], "pos": b["pos"], "p": b["p"],
                      "med": b["med_slope"], "per": per})
    return bands, {"dropped": dropped, "path": path,
                   "mtime": time.strftime("%Y-%m-%d %H:%M",
                                          time.localtime(os.path.getmtime(path))),
                   "overall": d.get("overall", {})}


def draw(bands, meta, out_path, pub=False, show="both"):
    import matplotlib
    matplotlib.use("Agg")
    import pandas as pd
    from plotnine import (ggplot, aes, geom_line, geom_point, geom_hline,
                          labs, scale_x_continuous, theme_minimal, theme,
                          element_text, ggtitle)
    from malignment.figure import (PUB_GRAY, PUB_INK, PUB_LINE_PT, PUB_RULE_PT,
                                   PUB_FONT_PT, pub_theme, pub_font)

    order = {b["band"]: i for i, b in enumerate(bands)}
    rows = []
    for b in bands:
        for r in b["per"]:
            rows.append({"x": order[b["band"]], "lineage": r["lineage"],
                         "slope": r["slope"]})
    lin = pd.DataFrame(rows)
    med = pd.DataFrame([{"x": order[b["band"]], "slope": b["med"]}
                        for b in bands])
    #: n on the tick, because the bands are not the same size and a reader
    #: comparing two medians should see that before they compare them
    labels = ["%s\nn=%s" % (b["band"].split(" (")[0],
                            format(b["n_cells"], ",")) for b in bands]

    p = ggplot(lin, aes("x", "slope"))
    #: ZERO IS THE CLAIM'S BOUNDARY, so it gets a rule: above it alignment
    #: favours the charged word, below it the charged word loses more.
    p = p + geom_hline(yintercept=0.0, color="black", size=PUB_RULE_PT)
    if show in ("both", "lineages"):
        p = p + geom_line(aes(group="lineage"), color=PUB_GRAY,
                          size=PUB_RULE_PT, alpha=0.55)
    if show in ("both", "median"):
        p = (p + geom_line(data=med, color=PUB_INK, size=PUB_LINE_PT)
             + geom_point(data=med, color=PUB_INK, size=1.6))
    p = (p + scale_x_continuous(breaks=list(range(len(bands))), labels=labels,
                                limits=(-0.15, len(bands) - 0.85))
         #: the x axis needs its own name: the tick labels are band EDGES and
         #: a reader who does not already know what lift is cannot recover it
         #: from "< 0" and "0-0.5"
         + labs(x="Lift (prompt dose − frame): what the candidate words add",
                y="Slope of Δp on word charge, within cell"))
    if pub:
        p = p + pub_theme()
    else:
        p = (p + ggtitle("Selectivity by lift — %d lineages, artifact %s"
                         % (len(lin['lineage'].unique()), meta["mtime"]))
             + theme_minimal()
             + theme(figure_size=(9, 6),
                     plot_title=element_text(size=11, weight="bold")))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    #: PNG and PDF together -- see malignment.figure.save
    from malignment.figure import save as _save
    return _save(p, out_path)[0]


def draw_mass(d, out_path, pub=False, scale="absolute", drop=()):
    """Seven levels, base to aligned. RH's design, 2026-09-15.

    The annotated rating is an INTEGER 1-7 inside a cell, so the seven lines are
    the seven levels and no banding is chosen. y is probability mass, NOT a
    within-cell share: a share moves when the covered mass moves and would fold
    two changes into one line.

    **EVERY LEVEL GAINS, WHICH IS THE FIRST THING TO SAY ABOUT THIS FIGURE.**
    Alignment concentrates probability, so all seven rise and the question is
    by how much. Reading a rising line here as "alignment likes level 7 more"
    is the error the figure invites; the ramp and the right-hand numbers are
    there so a reader compares SLOPES rather than heights.
    """
    import matplotlib
    matplotlib.use("Agg")
    import pandas as pd, random
    from plotnine import (ggplot, aes, geom_line, geom_point, geom_errorbar,
                          geom_text, labs, scale_x_continuous,
                          scale_y_continuous, scale_color_manual,
                          theme_minimal, theme, element_text, ggtitle)
    from malignment.figure import PUB_FONT_PT, PUB_RULE_PT, pub_theme, pub_font

    rng = random.Random(11)
    def ci(vals):
        med = st.median(vals)
        bs = sorted(st.median([vals[rng.randrange(len(vals))]
                               for _ in vals]) for _ in range(2000))
        return med, bs[int(0.025 * len(bs))], bs[int(0.975 * len(bs)) - 1]

    #: **INDEXED, BECAUSE ONE LEVEL OWNS THE AXIS.** On lift, level 0 carries
    #: 28-34% of the mass and the other five lines are pressed into the floor
    #: with their labels overprinting -- the figure becomes a picture of how
    #: common lift 0 is, which nobody asked. `indexed` divides each line by its
    #: own base value so every line starts at 100% and the picture is the
    #: CHANGE. It is a different quantity and the axis says so; the absolute
    #: masses stay one flag away and in the JSON.
    per = d["per_lineage"]
    #: **A DROPPED LEVEL IS A LEVEL, NOT A GAP.** Lift 0 holds 28-34% of the
    #: mass and squashes the rest; removing it lets the other five use the axis.
    #: But the drawn lines then no longer sum to the rated mass, so what was
    #: removed and how big it was has to reach the caption -- an axis that
    #: silently omits three quarters of the quantity it names is the more
    #: dangerous kind of clean figure.
    drop = {int(x) for x in drop}
    levels = [k for k in d["levels"] if k not in drop]
    rows, ends = [], []
    #: light -> dark with the level. ORDINAL data wants an ordinal ramp, and a
    #: ramp survives a grayscale plate where seven hues do not.
    #: indexed BY POSITION, not by level value -- lift levels start at -1 and
    #: `ramp[k-1]` would wrap to the dark end for the lowest band
    ramp = ["#c3c9ce", "#a9b1b7", "#8e979f", "#737e87", "#58646e", "#3d4a55", "#1f2933"]
    nlev = len(levels) if False else len(d["levels"])
    ramp = [ramp[int(round(i * (len(ramp) - 1) / max(1, nlev - 1)))]
            for i in range(nlev)]
    pos_of = {k: i for i, k in enumerate(d["levels"])}
    fmt = (lambda k: str(k)) if min(d["levels"]) >= 1 else (
        lambda k: ("%+d" % k) if k else "0")
    for k in levels:
        for pos, arm in ((0, "base"), (1, "aligned")):
            vals = [r["%s_%d" % (arm, k)] for r in per]
            if scale == "indexed":
                base = [r["base_%d" % k] for r in per]
                vals = [v / b for v, b in zip(vals, base) if b > 0]
            m, lo, hi = ci(vals)
            rows.append({"x": pos, "mass": m, "lo": lo, "hi": hi,
                         "level": fmt(k)})
            if pos == 1:
                ends.append({"x": pos, "mass": m, "level": fmt(k)})
    lev = pd.DataFrame(rows)
    end = pd.DataFrame(ends)
    colors = {fmt(k): ramp[pos_of[k]] for k in levels}
    what = ("charge level" if d.get("by", "scene") == "scene"
            else "lift (word charge − frame charge)")
    ytitle = ("Probability mass on words at each %s" % what
              if scale == "absolute" else
              "Mass at each %s, indexed to its own base = 100%%" % what)
    p = (ggplot(lev, aes("x", "mass", color="level"))
         + geom_line(aes(group="level"), size=1.0)
         + geom_errorbar(aes(ymin="lo", ymax="hi"), width=0.03,
                         size=PUB_RULE_PT)
         + geom_point(size=1.2)
         + geom_text(aes(label="level"), data=end, ha="left", nudge_x=0.05,
                     size=PUB_FONT_PT, family=pub_font())
         + scale_color_manual(colors, guide=None)
         + scale_x_continuous(breaks=[0, 1],
                              labels=["Base models", "Aligned models"],
                              limits=(-0.08, 1.22))
         + scale_y_continuous(
             labels=lambda v: ["%g%%" % round(x * 100, 6) for x in v])
         #: WRAPPED. One line of this title is longer than the panel is tall,
         #: and matplotlib does not wrap an axis title -- it draws it off the
         #: canvas, where it reads as a cropping error rather than a text that
         #: did not fit.
         + labs(x="", y="\n".join(textwrap.wrap(ytitle, 34))))
    if pub:
        p = p + pub_theme()
    else:
        p = (p + ggtitle("Mass by charge level, %d lineages, %s cells"
                         % (d["n_lineages"], format(d["n_cells"], ",")))
             + theme_minimal() + theme(figure_size=(9, 6),
                                       plot_title=element_text(size=11, weight="bold")))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    #: PNG and PDF together -- see malignment.figure.save
    from malignment.figure import save as _save
    return _save(p, out_path)[0]


def draw_wlift(d, out_path, pub=False):
    """ONE LINE: the mass-weighted mean lift of the next word, base to aligned.

    For each cell, `sum(p * lift) / sum(p)` -- the expected lift of whatever the
    model says next, weighted by how likely it is to say it. Then the mean over
    that lineage's cells, then a median and a bootstrap interval over the 50
    lineages, which is this folder's unit throughout.

    **LIFT IS UNCLAMPED HERE.** The seven-line figures pool below -1 and above
    +4 because those bands are too thin to carry a median; a MEAN has no such
    problem and clamping would pull exactly the tails where alignment acts.

    **THE INTERVAL ON THE ARMS IS NOT THE INTERVAL ON THE MOVEMENT.** The two
    end intervals overlap heavily, because lineages differ a lot in level; the
    paired within-lineage difference is what the claim rests on and it is
    printed by the producer for the caption. Reading non-overlap off this
    figure would understate the result, not overstate it.
    """
    import matplotlib
    matplotlib.use("Agg")
    import pandas as pd, random
    from plotnine import (ggplot, aes, geom_line, geom_point, geom_errorbar,
                          labs, scale_x_continuous, theme_minimal, theme,
                          element_text, ggtitle)
    from malignment.figure import PUB_RULE_PT, PUB_INK, pub_theme

    rng = random.Random(13)
    def ci(vals):
        bs = sorted(st.median([vals[rng.randrange(len(vals))] for _ in vals])
                    for _ in range(4000))
        return st.median(vals), bs[int(0.025 * len(bs))], bs[int(0.975 * len(bs)) - 1]

    per = d["per_lineage"]
    rows = []
    for pos, arm in ((0, "base"), (1, "aligned")):
        m, lo, hi = ci([r[arm] for r in per])
        rows.append({"x": pos, "y": m, "lo": lo, "hi": hi})
    lev = pd.DataFrame(rows)
    p = (ggplot(lev, aes("x", "y"))
         + geom_line(size=1.0, color=PUB_INK)
         + geom_errorbar(aes(ymin="lo", ymax="hi"), width=0.03,
                         size=PUB_RULE_PT, color=PUB_INK)
         + geom_point(size=1.6, color=PUB_INK)
         + scale_x_continuous(breaks=[0, 1],
                              labels=["Base models", "Aligned models"],
                              limits=(-0.12, 1.12))
         + labs(x="", y="Mass-weighted mean lift of the next word\n"
                        "(word charge − frame charge)"))
    if pub:
        p = p + pub_theme()
    else:
        p = (p + ggtitle("Weighted lift, %d lineages, %s cells"
                         % (d["n_lineages"], format(d["n_cells"], ",")))
             + theme_minimal() + theme(figure_size=(9, 6),
                                       plot_title=element_text(size=11, weight="bold")))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    #: PNG and PDF together -- see malignment.figure.save
    from malignment.figure import save as _save
    return _save(p, out_path)[0]


def render(pub="no", show="both"):
    bands, meta = load(DEFAULT_JSON)
    out = os.path.join(FIGURES, "lift_gradient%s.png"
                       % ("_pub" if str(pub) in ("yes", "True", "1") else ""))
    draw(bands, meta, out, pub=str(pub) in ("yes", "True", "1"), show=str(show))
    return out, {"bands": [b["band"] for b in bands],
                 "dropped": meta["dropped"], "artifact": meta["mtime"],
                 "n_lineages": len(bands[0]["per"]) if bands else 0}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", default=DEFAULT_JSON)
    ap.add_argument("--pub", action="store_true")
    ap.add_argument("--show", default="both",
                    choices=["both", "median", "lineages"])
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    bands, meta = load(a.json)
    print("artifact  %s  (written %s)" % (a.json, meta["mtime"]))
    print("%-20s %9s %8s %11s %11s" % ("band", "cells", "neg/pos", "p", "median"))
    for b in bands:
        print("%-20s %9s %8s %11.4g %11.6f"
              % (b["band"], format(b["n_cells"], ","),
                 "%d/%d" % (b["neg"], b["pos"]), b["p"], b["med"]))
    for name, n_cells, n_lin in meta["dropped"]:
        print("DROPPED %-12s %d cells, %d lineages -- no median to draw"
              % (name, n_cells, n_lin))
    out = a.out or os.path.join(
        FIGURES, "lift_gradient%s.png" % ("_pub" if a.pub else ""))
    print("\nwrote %s" % draw(bands, meta, out, pub=a.pub, show=a.show))


if __name__ == "__main__":
    main()
