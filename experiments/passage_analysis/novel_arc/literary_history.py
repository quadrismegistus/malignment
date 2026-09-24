#!/usr/bin/env python
"""Rewinding literary history: a three-panel CI plate, and the producer the novel_arc figures lacked.

    python -u literary_history.py     -> figures/ci_literary_history.{png,pdf,tif,caption.txt}

Requested by the paper seat for RH (2026-09-24) to replace Figure 5. Writes NEW files
only and refuses to overwrite anything (RH, same day).

## PRODUCER DEBT THIS DISCHARGES

`figures/novel_arc_abstraction.png`, `novel_arc_interiority.png` and the abstraction
history, loess and intersections in `novel_arc.data.json` were made by the dario
seat on 2026-08-25 (commits 5d439623, 74d51377, f961d0df) from inline session code
that was never committed. The recipe below is RECOVERED from that session's log
(8690ed90, tool calls of 18:19 and 18:47 UTC), logic unedited:

    per text:    median of the column over the text's passages
    per decade:  median over texts; Chadwyck for 1600-1879, Chicago from 1880;
                 bins with fewer than 3 texts dropped; plotted at mid-decade
    smooth:      statsmodels lowess, frac=0.3, on the decade medians
    arm value:   median over the arm's passages in model_placement.parquet
    crossing:    linear interpolation on the lowess curve

and this file ASSERTS it reproduces the committed data file: every abstraction
decade (year, value, n), the three arm values, and the three crossing years.
Nothing in novel_arc.data.json or the two PNGs is rewritten.

## A DEFECT IN THE RECOVERED RECIPE, FOUND BY REPRODUCING IT

The recipe says "median per text, then median of texts", and does that for
Chadwyck (text_id). For Chicago it grouped on the ROW INDEX, which is one row per
PASSAGE (4,198,863 rows, 9,089 texts). So every Chicago decade was a median over
passages, not texts, and its "n" counted passages. Grouping Chicago by text_id,
as intended, moves the abstraction crossings from 1979 / 1922 / 1903 to
1972 / 1920 / 1901 and leaves the inner-life panel's reading unchanged. The plate
is drawn from the CORRECTED series (group="text"); the passage-grouped series is
still computed, only to prove the recovery reproduces the committed artifact.

## THE THIRD PANEL

The gap in scansion uncertainty, prose minus verse, from
`syntax_and_rhythm/results/verse_prose_gap.csv`: eight human 50-year periods and
two open-model arms. The csv's API row pairs API VERSE with open-model PROSE (there
is no API prose) and is refused by name, not merely skipped.

## ORIENTATION

Every panel puts the direction alignment moves UP: the concreteness scale is
reversed (up = more abstract); inner life and the gap run as measured.
"""
import csv
import json
import os
import sys
import textwrap

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, REPO)
from malignment import figure as F  # noqa: E402

DATA = os.path.join(os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data")), "novel_arc")
ART = os.path.join(HERE, "figures", "novel_arc.data.json")
GAP = os.path.join(HERE, "..", "syntax_and_rhythm", "results", "verse_prose_gap.csv")
OUT = os.path.join(HERE, "figures", "ci_literary_history")
ARMS = ["base", "aligned", "API"]
LINETYPE = {"base": "dotted", "aligned": "solid", "API": "dashed"}
#: the axis runs 1600-2000 as requested; the recipe's last decade sits at 2005, so the
#: arm lines run to it and their labels start just beyond
X0, X1, XLAB, XMAX = 1600, 2005, 2011, 2085

#: booked, from the paper seat's request and the committed data file
BOOKED_ABS = {"base": 0.0957, "aligned": -0.0407, "API": -0.1039}
BOOKED_ABS_X = {"base": 1979, "aligned": 1922, "API": 1903}
BOOKED_INT = {"base": 0.1461, "aligned": 0.1667, "API": 0.1491}
BOOKED_GAP_HUMAN = [1.479, 1.411, 1.951, 1.565, 1.027, 1.186, 0.842, 0.322]
BOOKED_GAP_ARMS = {"base": 1.188, "aligned": 1.727}


# ───────────────────────────────────────────── the recovered recipe
def load():
    chad = pd.read_parquet(os.path.join(DATA, "chadwyck_n200.parquet"))
    chi = pd.read_parquet(os.path.join(DATA, "chicago_n200.parquet"))
    mod = pd.read_parquet(os.path.join(DATA, "model_placement.parquet"))
    return chad, chi, mod


def per_text(chad, chi, col, group="text"):
    ct = chad.groupby("text_id").agg(year=("year", "first"), v=(col, "median")).dropna()
    #: group="passage" is the recovered August code, which grouped Chicago on its
    #: row index -- one row per PASSAGE. group="text" is what the recipe says.
    key = chi.index if group == "passage" else "text_id"
    it = chi.groupby(key).agg(year=("year", "first"), v=(col, "median")).dropna()
    return ct, it


def decades(chad, chi, col, group="text"):
    ct, it = per_text(chad, chi, col, group)
    rows = []
    for src, t_, lo, hi in (("chadwyck", ct, 1600, 1880), ("chicago", it, 1880, 2010)):
        for yr in range(lo, hi, 10):
            t = t_[(t_.year >= yr) & (t_.year < yr + 10)]
            if len(t) < 3:
                continue
            rows.append({"year": yr + 5, "value": float(t.v.median()), "n": len(t), "source": src})
    return pd.DataFrame(rows)


def arm_values(mod, col):
    return {c: (float(mod[mod.category == c][col].median()), int((mod.category == c).sum())) for c in ARMS}


def smooth(hist):
    from statsmodels.nonparametric.smoothers_lowess import lowess
    xy = hist[["year", "value"]].sort_values("year")
    return lowess(xy.value.values, xy.year.values, frac=0.3, return_sorted=True)


def crossings(curve, target):
    """EVERY year where a piecewise-linear curve crosses a level, by interpolation."""
    out = []
    for (y0, v0), (y1, v1) in zip(curve[:-1], curve[1:]):
        if (v0 - target) * (v1 - target) < 0 or (v0 == target and not out):
            out.append(y0 + (target - v0) / (v1 - v0) * (y1 - y0) if v1 != v0 else y0)
    return out


def seam(chad, chi, col):
    """Chicago minus Chadwyck in the 1880s, the first decade both hold (Chicago starts
    in 1880), per text. The splice uses Chadwyck to 1879 and Chicago from 1880."""
    ct, it = per_text(chad, chi, col, "text")
    a = ct[(ct.year >= 1880) & (ct.year < 1890)].v
    b = it[(it.year >= 1880) & (it.year < 1890)].v
    return float(b.median() - a.median()), len(a), len(b)


def gap_panel():
    rows = list(csv.DictReader(open(GAP, encoding="utf-8")))
    human = [r for r in rows if r["who"].startswith("human ")]
    assert [float(r["uncertainty"]) for r in human] == BOOKED_GAP_HUMAN, [r["uncertainty"] for r in human]
    mids = [int(r["who"].split()[1][:4]) + 25 for r in human]
    assert mids == list(range(1625, 2000, 50)), mids
    arm = {}
    for r in rows:
        if r["who"].startswith("LLM base"):
            arm["base"] = float(r["uncertainty"])
        elif r["who"].startswith("LLM open aligned"):
            arm["aligned"] = float(r["uncertainty"])
        elif r["who"].startswith("API"):
            #: API verse against open-model prose: not a gap of anything the API wrote
            assert "no API prose" in r["who"], r["who"]
    assert arm == BOOKED_GAP_ARMS, arm
    base_row = next(r["who"] for r in rows if r["who"].startswith("LLM base"))
    return pd.DataFrame({"year": mids, "value": BOOKED_GAP_HUMAN,
                         "n": [None] * len(mids)}), arm, base_row


# ───────────────────────────────────────────── the plate
def panel(hist, curve, arms, cross, title, ylab, reverse, show_x):
    from plotnine import (ggplot, aes, geom_point, geom_line, geom_segment, geom_text, labs,
                          scale_x_continuous, scale_y_continuous, scale_y_reverse, theme,
                          element_text, element_blank, scale_linetype_manual)
    fnt = F.pub_font()
    cv = pd.DataFrame(curve, columns=["year", "value"])
    A = pd.DataFrame([{"arm": a, "value": v} for a, v in arms.items()])
    #: labels at the right end, pushed apart where two arms sit close
    span = float(max(cv.value.max(), A.value.max(), hist.value.max()) -
                 min(cv.value.min(), A.value.min(), hist.value.min()))
    order = A.sort_values("value").reset_index(drop=True)
    ly = list(order.value)
    for i in range(1, len(ly)):
        ly[i] = max(ly[i], ly[i - 1] + 0.11 * span)
    shift = (sum(ly) - sum(order.value)) / len(ly)
    order["ly"] = [y - shift for y in ly]
    for i in range(1, len(order)):
        order.loc[i, "ly"] = max(order.loc[i, "ly"], order.loc[i - 1, "ly"] + 0.11 * span)
    X = pd.DataFrame([{"arm": a, "year": y, "value": arms[a]} for a, ys in cross.items() for y in ys])
    p = (ggplot()
         + geom_point(aes("year", "value"), data=hist, color=F.PUB_GRAY, size=0.9)
         + geom_line(aes("year", "value"), data=cv, color=F.PUB_INK, size=F.PUB_LINE_PT)
         + geom_segment(aes(x=X0, xend=X1, y="value", yend="value", linetype="arm"), data=A,
                        color=F.PUB_MID, size=F.PUB_RULE_PT * 1.4)
         + geom_text(aes(x=XLAB, y="ly", label="arm"), data=order, ha="left", va="center",
                     size=F.PUB_FONT_PT, family=fnt, color=F.PUB_INK)
         + scale_linetype_manual(LINETYPE, guide=None)
         + scale_x_continuous(limits=(X0 - 5, XMAX), breaks=list(range(1600, 2001, 50)), expand=(0, 0),
                              labels=(lambda v: ["%d" % x for x in v]) if show_x else (lambda v: [""] * len(v)))
         + (scale_y_reverse() if reverse else scale_y_continuous())
         + labs(x="", y=ylab, title=title)
         + F.pub_theme(grid="y")
         + theme(plot_title=element_text(family=fnt, size=F.PUB_FONT_PT, weight="bold", ha="left"),
                 axis_title_y=element_text(family=fnt, size=F.PUB_FONT_PT)))
    if len(X):
        p = p + geom_point(aes("year", "value"), data=X, shape="o", fill="#ffffff", color=F.PUB_INK,
                           size=1.8, stroke=0.7)
    return p


def main():
    for ext in (".png", ".pdf", ".tif", ".caption.txt"):
        assert not os.path.exists(OUT + ext), "refusing to overwrite %s" % (OUT + ext)
    F.check_halftones({"history": F.PUB_INK, "points": F.PUB_GRAY, "arms": F.PUB_MID})
    art = json.load(open(ART))
    chad, chi, mod = load()

    # ── panel 1: abstraction, reproduced against the committed artifact
    #: the recovery is proved on the PASSAGE-grouped series the August code made ...
    hp = decades(chad, chi, "rh_absconc_median", "passage")
    booked = pd.DataFrame(art["abstraction"]["history"])
    assert len(hp) == len(booked) and (hp.year.values == booked.year.values).all() and \
        (hp.n.values == booked.n.values).all() and np.allclose(hp.value.values, booked.value.values, atol=1e-12), \
        "abstraction decades do not reproduce novel_arc.data.json"
    a1 = arm_values(mod, "rh_absconc_median")
    assert {k: round(v, 4) for k, (v, n) in a1.items()} == BOOKED_ABS, a1
    assert {m["category"]: m["value"] for m in art["abstraction"]["models"]} == BOOKED_ABS
    xp = {a: crossings(smooth(hp), v) for a, (v, n) in a1.items()}
    assert {a: round(ys[0]) for a, ys in xp.items()} == BOOKED_ABS_X, xp
    print("   recovery proved: %d decades, arms and crossings %s reproduce the committed artifact"
          % (len(hp), BOOKED_ABS_X))
    #: ... and the plate is drawn from the TEXT-grouped series the recipe describes
    h1 = decades(chad, chi, "rh_absconc_median", "text")
    c1 = smooth(h1)
    x1 = {a: crossings(c1, v) for a, (v, n) in a1.items()}
    print("   panel 1 (per text): crossings %s" % {a: [round(y) for y in ys] for a, ys in x1.items()})

    # ── panel 2: inner life, the same recipe on usas_x
    h2 = decades(chad, chi, "usas_x", "text")
    a2 = arm_values(mod, "usas_x")
    assert {k: round(v, 4) for k, (v, n) in a2.items()} == BOOKED_INT, a2
    c2 = smooth(h2)
    x2 = {a: crossings(c2, v) for a, (v, n) in a2.items()}
    assert all(not ys for ys in x2.values()) and min(v for v, n in a2.values()) > max(h2.value.max(), c2[:, 1].max()), \
        "an inner-life arm is not above the whole history"
    print("   panel 2: %d decades, arms %s, no crossings (all above)" % (len(h2), BOOKED_INT))

    # ── panel 3: the verse/prose gap
    h3, a3, base_label = gap_panel()
    c3 = h3[["year", "value"]].values
    x3 = {a: crossings(c3, v) for a, v in a3.items()}
    print("   panel 3: crossings %s" % {a: [round(y) for y in ys] for a, ys in x3.items()})

    sm, n_chad80, n_chi80 = seam(chad, chi, "rh_absconc_median")
    print("   splice seam, 1880s: Chicago minus Chadwyck %+.3f z (texts %d / %d)" % (sm, n_chad80, n_chi80))

    from plotnine.composition import Stack
    p1 = panel(h1, c1, {a: v for a, (v, n) in a1.items()}, x1, "Abstraction",
               "Concreteness\n(↑ more abstract)", True, False)
    p2 = panel(h2, c2, {a: v for a, (v, n) in a2.items()}, x2, "Inner life",
               "Interior vocabulary\n(↑ more)", False, False)
    p3 = panel(h3, c3, a3, x3, "Verse against prose",
               "Prose minus verse,\nscansion uncertainty\n(↑ wider gap)", False, True)
    for t in ("↑",):
        assert not F.missing_glyphs(t), "house face lacks %r" % t
    W_IN, H_IN = F.PUB_SIZE[0], 6.0
    comp = Stack([p1, p2, p3])
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["pdf.fonttype"] = 42
    fig = comp.draw()
    fig.set_size_inches(W_IN, H_IN)
    fig.savefig(OUT + ".png", dpi=300)
    fig.savefig(OUT + ".pdf")
    from PIL import Image
    Image.open(OUT + ".png").save(OUT + ".tif", dpi=(300, 300), compression="tiff_lzw")

    fmt_x = lambda d: "; ".join("%s %s" % (a, ", ".join("%d" % round(y) for y in ys) or "none")
                                for a, ys in d.items())
    L = [
        "REWINDING LITERARY HISTORY. Three measures of English writing across four centuries, with the",
        "model arms as horizontal lines. Every panel puts up the direction alignment moves.",
        "",
        "Lines: base models dotted, open aligned models solid, API models dashed; each labelled at the right.",
        "Open circle: where an arm's line crosses the history. Gray points: the human series; black line:",
        "its smooth (panels 1-2, lowess span 0.3 on the decade medians) or its periods joined (panel 3).",
        "",
        "PANEL 1, ABSTRACTION. Concreteness (rh_absconc_median, z; axis reversed, up = more abstract).",
        "Per text the median over its passages; per decade the median over texts; Chadwyck 1600-1879 (1,333",
        "texts in all), then Chicago from 1880 (9,089 texts); decades with fewer than 3 texts dropped. Arms:",
        "median over each arm's passages (model_placement.parquet).",
        "  arms: " + ", ".join("%s %+.4f (n=%d passages)" % (a, v, n) for a, (v, n) in a1.items()),
        "  crossings (year the lowess reaches the arm): " + fmt_x(x1),
        "  NOTE: novel_arc.data.json and the August figure give %s. Their Chicago bins were medians over"
        % fmt_x({a: [ys[0]] for a, ys in xp.items()}),
        "  PASSAGES, not texts (a grouping error in that code, recovered and corrected here); per text, as",
        "  above, each crossing moves 1-7 years earlier. Any text quoting the old years should be updated.",
        "  texts per decade: " + ", ".join("%d:%d" % (r.year - 5, r.n) for r in h1.itertuples()),
        "",
        "PANEL 2, INNER LIFE. usas_x: the share of a passage's tokens tagged in USAS field X (psychological",
        "actions, states and processes; measure_lltk.py), same recipe.",
        "  arms: " + ", ".join("%s %.4f (n=%d)" % (a, v, n) for a, (v, n) in a2.items()),
        "  crossings: none; every arm sits above the whole history (history max %.4f)." % max(h2.value.max(),
                                                                                             c2[:, 1].max()),
        "  texts per decade: " + ", ".join("%d:%d" % (r.year - 5, r.n) for r in h2.itertuples()),
        "",
        "PANEL 3, VERSE AGAINST PROSE. The gap in scansion uncertainty, prose minus verse",
        "(syntax_and_rhythm/results/verse_prose_gap.csv), eight human 50-year periods plotted at their",
        "midpoints and joined by straight segments: " + ", ".join("%d %.3f" % (y, v) for y, v in zip(h3.year, h3.value)) + ".",
        "  arms: base %.3f, aligned %.3f (%s)." % (a3["base"], a3["aligned"], base_label),
        "  crossings: " + fmt_x(x3),
        "  No API line: there is no API prose, and the csv's API row pairs API verse with open-model prose.",
        "",
        "CAVEATS",
        "- The years are Chicago years. Where the two corpora overlap, in the 1880s, Chicago sits %.2f z"
        % abs(sm),
        "  %s abstract than Chadwyck (%d Chadwyck texts, %d Chicago), a step at the 1880 splice."
        % ("more" if sm < 0 else "less", n_chad80, n_chi80),
        "- The inner-life history rests on the lexicon alone; the arm effect was also established, and more",
        "  strongly, by an LLM coder reading passages blind for degree of interiority (interiority_in_passages).",
        "- The gap sets prose from 34 lineages against verse from two model families.",
        "- There is no API prose.",
        "",
        "Producer: experiments/passage_analysis/novel_arc/literary_history.py, which recovers and asserts the",
        "recipe behind novel_arc.data.json and the August novel_arc figures.",
    ]
    open(OUT + ".caption.txt", "w").write("\n".join(L) + "\n")
    for ext in (".png", ".pdf", ".tif", ".caption.txt"):
        print("   ->", os.path.relpath(OUT + ext, HERE))


if __name__ == "__main__":
    main()
