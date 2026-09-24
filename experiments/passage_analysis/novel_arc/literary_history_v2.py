#!/usr/bin/env python
"""Rewinding literary history, version 2: the verse/prose panel as a scatter with a smooth.

    python -u literary_history_v2.py     -> figures/ci_literary_history_v2.{png,pdf,tif,caption.txt}

RH, 2026-09-24, against ci_literary_history (8f3c7ed2, Figure 5), in a NEW file with a
NEW filename (no existing file is touched):

- panel 3 as decade points plus a lowess, like panels 1-2, instead of eight periods;
- concreteness the right way up again (up = more concrete);
- y labels "Concreteness", "Interiority", "Rhythmic distinctiveness of verse from prose",
  and no panel titles;
- no API line anywhere;
- the arms labelled "Base models" and "Aligned models".

Panels 1-2 reuse literary_history.py's functions (the recovered recipe, per text),
and its assertion that the recovery reproduces novel_arc.data.json is re-run here.

## PANEL 3, PER DECADE

The Antimetricality reparse (`~/Dropbox/Prof/Articles/Antimetricality/data/
data.2026.reparse.big_data.parquet`): 10-syllable lines, scansion uncertainty = the
number of viable parses per line. Fiction is dated by publication year; poetry by
the reparse's `year`, which for poetry is author_dob + 30 (syntax_and_rhythm/plot.py).
Per decade: mean over Fiction lines minus mean over Poetry lines, decades with at
least 3 texts in each genre. Pooled to 50-year periods the same arithmetic gives
syntax_and_rhythm/results/verse_prose_gap.csv's eight human values exactly, which
is asserted. The arms (base 1.188, aligned 1.727: prose from 34 lineages against
verse from two model families) are that csv's, asserted by literary_history.gap_panel.
"""
import os
import sys
import textwrap

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import literary_history as LH  # noqa: E402
from literary_history import F  # noqa: E402

#: VERSIONS. v2 is the committed plate (c37a86ed) and must keep reproducing it; v3 (RH,
#: 2026-09-24) fixes two things v2 got wrong or left loose:
#:   - the rhythm label's SIGN: the quantity is prose uncertainty minus verse uncertainty,
#:     and uncertainty (viable parses per line) is INVERSE metricality, so as metricality
#:     it reads verse - prose, not prose - verse;
#:   - interiority is a proportion of content words (measure_lltk.py: USAS-X content words
#:     / content words), so its axis reads in percent.
#: Select with `python literary_history_v2.py v3`; LH_OUT_DIR redirects output (checks).
VERSION = next((a for a in sys.argv[1:] if a in ("v2", "v3")), "v2")
OUT = os.path.join(os.environ.get("LH_OUT_DIR", os.path.join(HERE, "figures")),
                   "ci_literary_history_" + VERSION)
REPARSE = os.environ.get("ANTIMETRICALITY_REPARSE", os.path.expanduser(
    "~/Dropbox/Prof/Articles/Antimetricality/data/data.2026.reparse.big_data.parquet"))
NAME = {"base": "Base models", "aligned": "Aligned models"}
LINETYPE = {"Base models": "dotted", "Aligned models": "solid"}
#: "Aligned models" is ~0.95 in at 9 pt; at ~140 data units per inch on this panel it
#: needs ~135 units past XLAB. 2105 clipped it at the panel edge (an image-only defect).
X0, X1, XLAB, XMAX = 1600, 2005, 2011, 2165


def gap_decades():
    b = pd.read_parquet(REPARSE, columns=["metagenre", "year", "num_sylls_canonical", "num_parses", "id"])
    b = b[(b.num_sylls_canonical == 10) & b.year.notna() & (b.year < 2000)]
    #: the booked 50-year values first: the same lines, pooled per period
    b["period"] = (b.year // 50 * 50).astype(int)
    m = b.groupby(["metagenre", "period"]).num_parses.mean().unstack(0)
    got = [round(float(x), 3) for x in (m["Fiction"] - m["Poetry"]).values]
    assert got == LH.BOOKED_GAP_HUMAN, "50-year gap %s does not reproduce verse_prose_gap.csv" % got
    b["decade"] = (b.year // 10 * 10).astype(int)
    g = b[b.metagenre.isin(["Fiction", "Poetry"])].groupby(["decade", "metagenre"]).agg(
        u=("num_parses", "mean"), lines=("num_parses", "size"), texts=("id", "nunique")).unstack(1)
    rows = []
    for dec, r in g.iterrows():
        ft, pt = r[("texts", "Fiction")], r[("texts", "Poetry")]
        if pd.isna(ft) or pd.isna(pt) or ft < 3 or pt < 3:
            continue
        rows.append({"year": int(dec) + 5, "value": float(r[("u", "Fiction")] - r[("u", "Poetry")]),
                     "n": int(ft), "n_poetry": int(pt), "lines_f": int(r[("lines", "Fiction")]),
                     "lines_p": int(r[("lines", "Poetry")])})
    return pd.DataFrame(rows)


def panel(hist, curve, arms, cross, title, ylab, show_x, ylim=None, ypct=False, vgrid=()):
    """ylim, when given, is a VIEW window (coord_cartesian): points beyond it stay in the
    data and in the lowess, they are only not drawn inside the panel."""
    from plotnine import coord_cartesian
    from plotnine import (ggplot, aes, geom_point, geom_line, geom_segment, geom_text, labs,
                          scale_x_continuous, scale_y_continuous, scale_linetype_manual, theme, element_text)
    fnt = F.pub_font()
    cv = pd.DataFrame(curve, columns=["year", "value"])
    A = pd.DataFrame([{"arm": NAME[a], "value": v} for a, v in arms.items()])
    lo = float(min(cv.value.min(), A.value.min(), hist.value.min()))
    hi = float(max(cv.value.max(), A.value.max(), hist.value.max()))
    order = A.sort_values("value").reset_index(drop=True)
    order["ly"] = order.value
    for i in range(1, len(order)):
        order.loc[i, "ly"] = max(order.loc[i, "ly"], order.loc[i - 1, "ly"] + 0.11 * (hi - lo))
    X = pd.DataFrame([{"year": y, "value": arms[a]} for a, ys in cross.items() for y in ys])
    from plotnine import geom_vline
    p = (ggplot()
         #: RH (v3): thin century lines, drawn first so everything else sits on top;
         #: the house grid colour and rule weight, so they read as grid and not data
         + (geom_vline(xintercept=list(vgrid), color="#e9ecef", size=F.PUB_RULE_PT) if vgrid
            else geom_point(aes("year", "value"), data=hist.iloc[:0]))
         + geom_point(aes("year", "value"), data=hist, color=F.PUB_GRAY, size=0.9)
         + geom_line(aes("year", "value"), data=cv, color=F.PUB_INK, size=F.PUB_LINE_PT)
         + geom_segment(aes(x=X0, xend=X1, y="value", yend="value", linetype="arm"), data=A,
                        color=F.PUB_MID, size=F.PUB_RULE_PT * 1.4)
         + geom_text(aes(x=XLAB, y="ly", label="arm"), data=order, ha="left", va="center",
                     size=F.PUB_FONT_PT, family=fnt, color=F.PUB_INK)
         + scale_linetype_manual(LINETYPE, guide=None)
         + (scale_y_continuous(labels=lambda v: ["%g%%" % round(100 * x, 6) for x in v]) if ypct
            else scale_y_continuous())
         + scale_x_continuous(limits=(X0 - 5, XMAX), breaks=list(range(1600, 2001, 50)), expand=(0, 0),
                              labels=(lambda v: ["%d" % x for x in v]) if show_x else (lambda v: [""] * len(v)))
         + labs(x="", y=ylab, title=title)
         + F.pub_theme(grid="y")
         + theme(axis_title_y=element_text(family=fnt, size=F.PUB_FONT_PT),
                 plot_title=element_text(family=fnt, size=F.PUB_FONT_PT, weight="bold", ha="left")))
    if ylim is not None:
        p = p + coord_cartesian(ylim=ylim)
    if len(X):
        p = p + geom_point(aes("year", "value"), data=X, shape="o", fill="#ffffff", color=F.PUB_INK,
                           size=1.8, stroke=0.7)
    return p


def main():
    for ext in (".png", ".pdf", ".tif", ".caption.txt"):
        assert not os.path.exists(OUT + ext), "refusing to overwrite %s" % (OUT + ext)
    F.check_halftones({"history": F.PUB_INK, "points": F.PUB_GRAY, "arms": F.PUB_MID})
    import json
    art = json.load(open(LH.ART))
    chad, chi, mod = LH.load()

    # panel 1: the recovery re-proved on the committed artifact, then per text
    hp = LH.decades(chad, chi, "rh_absconc_median", "passage")
    booked = pd.DataFrame(art["abstraction"]["history"])
    assert (hp.n.values == booked.n.values).all() and np.allclose(hp.value.values, booked.value.values, atol=1e-12)
    a1 = LH.arm_values(mod, "rh_absconc_median")
    assert {k: round(v, 4) for k, (v, n) in a1.items()} == LH.BOOKED_ABS
    h1 = LH.decades(chad, chi, "rh_absconc_median", "text")
    c1 = LH.smooth(h1)
    arms1 = {a: a1[a][0] for a in ("base", "aligned")}          # no API (RH)
    x1 = {a: LH.crossings(c1, v) for a, v in arms1.items()}
    assert {a: [round(y) for y in ys] for a, ys in x1.items()} == {"base": [1972], "aligned": [1920]}, x1

    # panel 2
    h2 = LH.decades(chad, chi, "usas_x", "text")
    a2 = LH.arm_values(mod, "usas_x")
    assert {k: round(v, 4) for k, (v, n) in a2.items()} == LH.BOOKED_INT
    c2 = LH.smooth(h2)
    arms2 = {a: a2[a][0] for a in ("base", "aligned")}
    x2 = {a: LH.crossings(c2, v) for a, v in arms2.items()}
    assert not any(x2.values())

    # panel 3: decade gap, lowess, the csv's arms
    h3 = gap_decades()
    _, a3, base_label = LH.gap_panel()
    c3 = LH.smooth(h3)
    x3 = {a: LH.crossings(c3, v) for a, v in a3.items()}
    print("   panel 3: %d decades; lowess crossings %s" % (len(h3), {a: [round(y) for y in ys] for a, ys in x3.items()}))

    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["pdf.fonttype"] = 42
    from plotnine.composition import Stack
    #: RH: the 1700s decade (gap ~2.96, few fiction texts) stays in the data and the
    #: smooth; the axis stops short of it. The window is set from the REST of the panel,
    #: and exactly one point may fall outside it, asserted, so a data change that moves
    #: another point out cannot hide silently.
    rest = h3.sort_values("value").iloc[:-1]
    top3 = max(float(rest.value.max()), float(c3[:, 1].max()), max(a3.values())) + 0.12
    bot3 = min(float(h3.value.min()), float(c3[:, 1].min())) - 0.08
    off = h3[(h3.value > top3) | (h3.value < bot3)]
    assert len(off) == 1 and int(off.year.iloc[0]) == 1705, off
    print("   panel 3: one decade outside the view window: %d at %.3f (in the smooth)" % (
        int(off.year.iloc[0]) - 5, float(off.value.iloc[0])))
    VG = (1700, 1800, 1900) if VERSION == "v3" else ()
    p1 = panel(h1, c1, arms1, x1, "Concreteness", "Concreteness (word norm)", False, vgrid=VG)
    p2 = panel(h2, c2, arms2, x2, "Interiority", "Interiority (semantic field)", False,
               ypct=(VERSION == "v3"), vgrid=VG)
    p3 = panel(h3, c3, a3, x3, "Rhythmic distinctiveness of verse from prose",
               "Metricality (stress pattern),\n" + ("verse \u2212 prose" if VERSION == "v3" else "prose \u2212 verse"),
               True, ylim=(bot3, top3), vgrid=VG)
    W_IN, H_IN = F.PUB_SIZE[0], 6.0
    fig = Stack([p1, p2, p3]).draw()
    fig.set_size_inches(W_IN, H_IN)
    fig.savefig(OUT + ".png", dpi=300)
    fig.savefig(OUT + ".pdf")
    from PIL import Image
    Image.open(OUT + ".png").save(OUT + ".tif", dpi=(300, 300), compression="tiff_lzw")

    fmt_x = lambda d: "; ".join("%s %s" % (NAME[a], ", ".join("%d" % round(y) for y in ys) or "none")
                                for a, ys in d.items())
    sm, n80c, n80i = LH.seam(chad, chi, "rh_absconc_median")
    wrap = lambda s: textwrap.wrap(s, 100)
    L = ["REWINDING LITERARY HISTORY (version 2). Three measures of English writing, 1600-2000, with the",
         "base and aligned model arms as horizontal lines.", "",
         *wrap("Lines: base models dotted, aligned models solid, labelled at the right. Gray points: decade "
               "values of the human history; black line: their lowess smooth (span 0.3). Open circle: where "
               "an arm's line crosses the smooth. No API arm is drawn (RH)."), "",
         *wrap("CONCRETENESS (rh_absconc_median, z; up = more concrete). Per text the median over its "
               "passages; per decade the median over texts; Chadwyck 1600-1879 (1,333 texts), Chicago from "
               "1880 (9,089 texts); decades under 3 texts dropped. Arms: median over each arm's passages "
               "(model_placement.parquet)."),
         "  arms: " + ", ".join("%s %+.4f (n=%d passages)" % (NAME[a], a1[a][0], a1[a][1]) for a in arms1),
         "  crossings: " + fmt_x(x1),
         "  texts per decade: " + ", ".join("%d:%d" % (r.year - 5, r.n) for r in h1.itertuples()), "",
         *(wrap("INTERIORITY (usas_x: share of a passage's tokens in USAS field X, psychological actions, "
                "states and processes), same recipe.") if VERSION == "v2" else
           wrap("INTERIORITY (usas_x: the percentage of a passage's content words tagged in USAS field X, "
                "psychological actions, states and processes; measure_lltk.py), same recipe.")),
         ("  arms: " + ", ".join("%s %.4f (n=%d)" % (NAME[a], a2[a][0], a2[a][1]) for a in arms2)) if VERSION == "v2"
         else ("  arms: " + ", ".join("%s %.2f%% (n=%d)" % (NAME[a], 100 * a2[a][0], a2[a][1]) for a in arms2)),
         ("  crossings: none; both arms sit above the whole history (max %.4f)." % max(h2.value.max(), c2[:, 1].max()))
         if VERSION == "v2" else
         ("  crossings: none; both arms sit above the whole history (max %.2f%%)." % (100 * max(h2.value.max(), c2[:, 1].max()))),
         "",
         *wrap("RHYTHMIC DISTINCTIVENESS OF VERSE FROM PROSE: the gap in scansion uncertainty (viable parses "
               "per 10-syllable line), prose fiction minus poetry, from the Antimetricality reparse. Fiction "
               "dated by publication year, poetry by author's birth + 30. Per decade: mean over lines, decades "
               "with at least 3 texts in each genre. Pooled to 50-year periods this reproduces "
               "verse_prose_gap.csv exactly. Arms: that csv's LLM rows, prose from 34 lineages against verse "
               "from two model families."),
         *([] if VERSION == "v2" else wrap(
             "  Direction: uncertainty is the number of viable scansions of a line, so fewer means MORE "
             "metrical. Prose uncertainty minus verse uncertainty is therefore how much more metrical verse "
             "is than prose: as metricality, verse minus prose, and the higher, the more distinct the two.")),
         "  arms: Base models %.3f, Aligned models %.3f." % (a3["base"], a3["aligned"]),
         "  crossings of the smooth: " + fmt_x(x3),
         "  decades (fiction texts / poetry texts): " + ", ".join(
             "%d:%d/%d" % (r.year - 5, r.n, r.n_poetry) for r in h3.itertuples()), "",
         "CAVEATS",
         *wrap("- The concreteness and interiority years are Chicago years. Where the two corpora overlap, in "
               "the 1880s, Chicago sits %.2f z %s abstract than Chadwyck (%d Chadwyck texts, %d Chicago)."
               % (abs(sm), "more" if sm < 0 else "less", n80c, n80i)),
         *wrap("- The interiority history rests on the lexicon alone; the arm effect was also established, and "
               "more strongly, by an LLM coder reading passages blind for degree of interiority "
               "(interiority_in_passages)."),
         *wrap("- The rhythm arms set prose from 34 lineages against verse from two model families; early "
               "decades hold few fiction texts (see the counts)."),
         *wrap("- One rhythm decade is not drawn: the %ds, at %.2f, from %d fiction texts, lies above the "
               "panel's window. It is in the data and in the smooth; the axis only stops short of it."
               % (int(off.year.iloc[0]) - 5, float(off.value.iloc[0]), int(off.n.iloc[0]))),
         *wrap("- API models are not drawn: there is no API prose for the rhythm panel, and RH removed the arm "
               "from all three."), "",
         "Producer: experiments/passage_analysis/novel_arc/literary_history_v2.py (reuses literary_history.py)."]
    open(OUT + ".caption.txt", "w").write("\n".join(L) + "\n")
    for ext in (".png", ".pdf", ".tif", ".caption.txt"):
        print("   ->", os.path.relpath(OUT + ext, HERE))


if __name__ == "__main__":
    main()
