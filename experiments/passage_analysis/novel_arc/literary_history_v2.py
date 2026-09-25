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
#: v4 (RH): v3 with the metricality label reordered, "(stress pattern)" on its own line
#: v5 (RH): v4 with the right margin trimmed nearer the end of "Aligned models", and
#: the aligned arm dashed (base stays dotted)
#: v6 (RH): v5 plus a short leader from each crossing to a small year label
VERSION = next((a for a in sys.argv[1:] if a in ("v2", "v3", "v4", "v5", "v6", "v7", "v8")), "v2")
LATER = VERSION in ("v3", "v4", "v5", "v6", "v7", "v8")    # the v3 corrections, carried forward
V5ON = VERSION in ("v5", "v6", "v7", "v8")                 # v5's margin and dashed aligned arm
V6ON = VERSION in ("v6", "v7", "v8")                       # v6's year leaders
PAIRED = VERSION in ("v7", "v8")                           # v7's matched-pair arms
#: v8 (RH, 2026-09-25): v7 without the verse/prose panel, titles "... in fiction", axis labels
#: that name the statistic (a passage's concreteness is the MEAN of its words' norms, measure_lltk)
TWO = VERSION == "v8"
#: v7 (RH via the paper seat, 2026-09-25): panels 1 and 2 re-aggregate their arms over MATCHED
#: PAIRS -- per model the median over its passages, then the median over the pairs' models --
#: instead of the median over pooled passages. --floor N keeps a pair only if both of its models
#: have at least N passages (malign: in a median of per-model medians a 2-passage model weighs as
#: much as a 174-passage one).
FLOOR = int(sys.argv[sys.argv.index("--floor") + 1]) if "--floor" in sys.argv else 0
assert PAIRED or FLOOR == 0, "--floor is a v7/v8 option"
OUT = os.path.join(os.environ.get("LH_OUT_DIR", os.path.join(HERE, "figures")),
                   "ci_literary_history_" + VERSION + ("_floor%d" % FLOOR if FLOOR else ""))
REPARSE = os.environ.get("ANTIMETRICALITY_REPARSE", os.path.expanduser(
    "~/Dropbox/Prof/Articles/Antimetricality/data/data.2026.reparse.big_data.parquet"))
NAME = {"base": "Base models", "aligned": "Aligned models"}
LINETYPE = {"Base models": "dotted", "Aligned models": "dashed" if V5ON else "solid"}
#: "Aligned models" is ~0.95 in at 9 pt; at ~140 data units per inch on this panel it
#: needs ~135 units past XLAB. 2105 clipped it at the panel edge (an image-only defect).
X0, X1, XLAB, XMAX = 1600, 2005, 2011, (2150 if V5ON else 2165)


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


def year_leaders(cross, arms, lo, hi):
    """(leaders, labels) for the crossings. A leader runs 13% of the panel's range from
    the circle, away from the other arm's line. Two crossings closer than 45
    years splay their labels apart (earlier to the left, later to the right), since a
    year at 7.5 pt is about 35 years wide on this axis."""
    span, L, T = hi - lo, [], []
    pts = sorted((y, arms[a], a) for a, ys in cross.items() for y in ys)
    for i, (y, v, arm) in enumerate(pts):
        #: AWAY FROM THE OTHER ARM'S LINE: a label drawn toward it sat on it (v6's first
        #: render put "1920" on the base line). With no other arm on one side, go up.
        others = [w for b, w in arms.items() if b != arm]
        up = not (others and all(w > v for w in others))
        end = v + (1 if up else -1) * 0.13 * span
        near_prev = i > 0 and y - pts[i - 1][0] < 45 and abs(v - pts[i - 1][1]) < 0.05 * span
        near_next = i + 1 < len(pts) and pts[i + 1][0] - y < 45 and abs(v - pts[i + 1][1]) < 0.05 * span
        ha = "right" if near_next else "left" if near_prev else "center"
        L.append(dict(x=y, xend=y, y=v + (1 if up else -1) * 0.025 * span, yend=end))
        T.append(dict(x=y + {"right": 2, "left": -2, "center": 0}[ha], y=end + (1 if up else -1) * 0.012 * span,
                      label="%d" % round(y), ha=ha, va="bottom" if up else "top"))
    return pd.DataFrame(L), pd.DataFrame(T)


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
    if len(X) and V6ON:
        vlo, vhi = ylim if ylim is not None else (lo, hi)
        Ld, Td = year_leaders(cross, arms, vlo, vhi)
        p = p + geom_segment(aes(x="x", xend="xend", y="y", yend="yend"), data=Ld,
                             color=F.PUB_INK, size=F.PUB_RULE_PT)
        #: the scale trains on a label's ANCHOR, not its extent, so a label above the data
        #: was clipped at the panel edge ("1972"); an invisible point one label-height
        #: beyond each anchor makes the panel hold the text too
        from plotnine import geom_blank
        span_ = vhi - vlo
        Td2 = Td.assign(yb=[y + (0.10 if va == "bottom" else -0.10) * span_ for y, va in zip(Td.y, Td.va)])
        p = p + geom_blank(aes(x="x", y="yb"), data=Td2)
        for ha in ("left", "right", "center"):
            for va in ("bottom", "top"):
                sub = Td[(Td.ha == ha) & (Td.va == va)]
                if len(sub):
                    p = p + geom_text(aes(x="x", y="y", label="label"), data=sub, ha=ha, va=va,
                                      size=7.5, family=fnt, color=F.PUB_INK)
    if len(X):
        p = p + geom_point(aes("year", "value"), data=X, shape="o", fill="#ffffff", color=F.PUB_INK,
                           size=1.8, stroke=0.7)
    return p


def paired_arms(mod, col, floor=0):
    """v7's arms. -> ({arm: value}, info)

    Pairs: roster.lineages() roots holding exactly one base and one aligned model among
    model_placement's base/aligned rows. A pair is kept only if both models have >= floor passages.
    Per model: the median over its passages (NaN skipped). Per arm: the median over the kept pairs'
    models. `info` carries the counts the caption states and the per-pair aligned-minus-base deltas."""
    from malignment import roster
    lin = roster.lineages()
    root = {m: r for r, ms in lin.items() for m in ms}
    for r in lin:
        root.setdefault(r, r)
    d = mod[mod.category.isin(["base", "aligned"])]
    assert set(d.model) <= set(root), sorted(set(d.model) - set(root))
    per = d.groupby(["model", "category"]).agg(v=(col, "median"), n=(col, "size")).reset_index()
    per["root"] = per.model.map(root)
    pairs, unpaired = [], []
    for r, g in per.groupby("root"):
        if set(g.category) == {"base", "aligned"}:
            assert len(g) == 2, (r, g.model.tolist())         # one of each per lineage
            pairs.append((g[g.category == "base"].iloc[0], g[g.category == "aligned"].iloc[0]))
        else:
            unpaired += list(g.model)
    keep = [b.n >= floor and a.n >= floor for b, a in pairs]
    kept = [pr for pr, k in zip(pairs, keep) if k]
    #: the models BELOW the floor, not their partners, are what the caption names
    dropped = sorted(x.model for (b, a), k in zip(pairs, keep) if not k for x in (b, a) if x.n < floor)
    arms = {"base": float(np.median([b.v for b, a in kept])), "aligned": float(np.median([a.v for b, a in kept]))}
    info = dict(n_pairs=len(kept), n_pairs_all=len(pairs), unpaired=sorted(unpaired), dropped=dropped,
                n_models={"base": int((per.category == "base").sum()), "aligned": int((per.category == "aligned").sum())},
                passages={"base": int(sum(b.n for b, a in kept)), "aligned": int(sum(a.n for b, a in kept))},
                deltas=[float(a.v - b.v) for b, a in kept], aligned_models=[a.model for b, a in kept])
    return arms, info


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
    assert {k: round(v, 4) for k, (v, n) in a1.items()} == LH.BOOKED_ABS      # the data v6 was drawn on
    h1 = LH.decades(chad, chi, "rh_absconc_median", "text")
    c1 = LH.smooth(h1)
    if PAIRED:
        arms1, info1 = paired_arms(mod, "rh_absconc_median", FLOOR)
        #: booked (the paper seat's specification): 25 pairs, 26 base and 28 aligned before pairing,
        #: 2,140 and 2,490 passages in the pairs; the floor of 10 drops exactly three models
        assert (info1["n_pairs_all"], info1["n_models"]["base"], info1["n_models"]["aligned"]) == (25, 26, 28), info1
        if FLOOR == 0:
            assert (info1["n_pairs"], info1["passages"]["base"], info1["passages"]["aligned"]) == (25, 2140, 2490), info1
        if FLOOR == 10:
            assert info1["n_pairs"] == 22 and info1["dropped"] == [
                "OpenLLM-France/Lucie-7B", "Qwen/Qwen2.5-0.5B-Instruct", "openbmb/MiniCPM5-1B"], info1
    else:
        arms1 = {a: a1[a][0] for a in ("base", "aligned")}          # no API (RH)
    x1 = {a: LH.crossings(c1, v) for a, v in arms1.items()}
    if not PAIRED:
        assert {a: [round(y) for y in ys] for a, ys in x1.items()} == {"base": [1972], "aligned": [1920]}, x1
    print("   panel 1 arms %s crossings %s" % ({a: round(v, 4) for a, v in arms1.items()},
                                               {a: [round(y) for y in ys] for a, ys in x1.items()}))

    # panel 2
    h2 = LH.decades(chad, chi, "usas_x", "text")
    a2 = LH.arm_values(mod, "usas_x")
    assert {k: round(v, 4) for k, (v, n) in a2.items()} == LH.BOOKED_INT
    c2 = LH.smooth(h2)
    if PAIRED:
        arms2, info2 = paired_arms(mod, "usas_x", FLOOR)
        assert info2["n_pairs"] == info1["n_pairs"] and info2["passages"] == info1["passages"]
    else:
        arms2 = {a: a2[a][0] for a in ("base", "aligned")}
    print("   panel 2 arms %s (history max %.4f)" % ({a: round(100 * v, 2) for a, v in arms2.items()},
                                                    100 * max(h2.value.max(), c2[:, 1].max())))
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
    VG = (1700, 1800, 1900) if LATER else ()
    if TWO:
        p1 = panel(h1, c1, arms1, x1, "Concreteness in fiction", "Concreteness\n(word norm mean)", False, vgrid=VG)
        p2 = panel(h2, c2, arms2, x2, "Interiority in fiction", "Interiority\n(semantic field frequency)", True,
                   ypct=True, vgrid=VG)
    else:
        p1 = panel(h1, c1, arms1, x1, "Concreteness", "Concreteness (word norm)", False, vgrid=VG)
        p2 = panel(h2, c2, arms2, x2, "Interiority", "Interiority (semantic field)", False,
                   ypct=LATER, vgrid=VG)
    p3 = panel(h3, c3, a3, x3, "Rhythmic distinctiveness of verse from prose",
               {"v2": "Metricality (stress pattern),\nprose \u2212 verse",
                "v3": "Metricality (stress pattern),\nverse \u2212 prose",
                "v4": "Metricality, verse \u2212 prose\n(stress pattern)",
                "v5": "Metricality, verse \u2212 prose\n(stress pattern)",
                "v6": "Metricality, verse \u2212 prose\n(stress pattern)",
                "v7": "Metricality, verse \u2212 prose\n(stress pattern)",
                "v8": "Metricality, verse \u2212 prose\n(stress pattern)"}[VERSION],
               True, ylim=(bot3, top3), vgrid=VG)
    W_IN, H_IN = F.PUB_SIZE[0], (4.2 if TWO else 6.0)
    fig = Stack([p1, p2] if TWO else [p1, p2, p3]).draw()
    fig.set_size_inches(W_IN, H_IN)
    fig.savefig(OUT + ".png", dpi=300)
    fig.savefig(OUT + ".pdf")
    from PIL import Image
    Image.open(OUT + ".png").save(OUT + ".tif", dpi=(300, 300), compression="tiff_lzw")

    fmt_x = lambda d: "; ".join("%s %s" % (NAME[a], ", ".join("%d" % round(y) for y in ys) or "none")
                                for a, ys in d.items())
    sm, n80c, n80i = LH.seam(chad, chi, "rh_absconc_median")
    wrap = lambda s: textwrap.wrap(s, 100)
    #: committed v2/v3 captions say "(version 2)"; kept for them so they still reproduce
    L = ["REWINDING LITERARY HISTORY (version %s). %s measures of English %s, 1600-2000, with the"
         % ("2" if VERSION in ("v2", "v3", "v4") else VERSION[1:], "Two" if TWO else "Three",
            "fiction" if TWO else "writing"),
         "base and aligned model arms as horizontal lines.", "",
         #: the line styles come from LINETYPE, the mapping that draws them (v5's first caption said
         #: "solid" for a dashed line)
         *wrap(("Lines: base models %s, aligned models %s, labelled at the right. Gray points: decade "
                % (LINETYPE["Base models"], LINETYPE["Aligned models"])) +
               "values of the human history; black line: their lowess smooth (span 0.3). Open circle: where "
               "an arm's line crosses the smooth" + (", with a short leader to the year" if V6ON else "")
               + ". No API arm is drawn (RH)."), "",
         *wrap("CONCRETENESS (rh_absconc_median, z; up = more concrete). Per text the median over its "
               "passages; per decade the median over texts; Chadwyck 1600-1879 (1,333 texts), Chicago from "
               "1880 (9,089 texts); decades under 3 texts dropped. " + (
                   "Arms: median over each arm's passages (model_placement.parquet)." if not PAIRED else
                   "Arms, as in the interiority panel: see ARMS below.")),
         ("  arms: " + ", ".join("%s %+.4f (n=%d passages)" % (NAME[a], a1[a][0], a1[a][1]) for a in arms1))
         if not PAIRED else
         ("  arms: " + ", ".join("%s %+.4f" % (NAME[a], arms1[a]) for a in arms1) +
          "; paired, aligned minus base: more abstract in %d of %d, median %+.3f."
          % (sum(x < 0 for x in info1["deltas"]), info1["n_pairs"], float(np.median(info1["deltas"])))),
         "  crossings: " + fmt_x(x1),
         "  texts per decade: " + ", ".join("%d:%d" % (r.year - 5, r.n) for r in h1.itertuples()), "",
         *(wrap("INTERIORITY (usas_x: share of a passage's tokens in USAS field X, psychological actions, "
                "states and processes), same recipe.") if VERSION == "v2" else
           wrap("INTERIORITY (usas_x: the percentage of a passage's content words tagged in USAS field X, "
                "psychological actions, states and processes; measure_lltk.py), same recipe.")),
         ("  arms: " + ", ".join("%s %.4f (n=%d)" % (NAME[a], a2[a][0], a2[a][1]) for a in arms2)) if VERSION == "v2"
         else ("  arms: " + ", ".join("%s %.2f%% (n=%d)" % (NAME[a], 100 * a2[a][0], a2[a][1]) for a in arms2))
         if not PAIRED else
         ("  arms: " + ", ".join("%s %.2f%%" % (NAME[a], 100 * arms2[a]) for a in arms2) +
          "; paired, aligned minus base: up in %d of %d, median %+.1f points."
          % (sum(x > 0 for x in info2["deltas"]), info2["n_pairs"], 100 * float(np.median(info2["deltas"])))),
         ("  crossings: none; both arms sit above the whole history (max %.4f)." % max(h2.value.max(), c2[:, 1].max()))
         if VERSION == "v2" else
         ("  crossings: none; both arms sit above the whole history (max %.2f%%)." % (100 * max(h2.value.max(), c2[:, 1].max()))),
         "",
         *([] if TWO else [*wrap("RHYTHMIC DISTINCTIVENESS OF VERSE FROM PROSE: the gap in scansion uncertainty (viable parses "
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
             "%d:%d/%d" % (r.year - 5, r.n, r.n_poetry) for r in h3.itertuples()), ""]),
         *(wrap("ARMS (panels 1 and 2): each model's median over its own passages, then the median over "
                "the %d matched pairs' models -- lineages (roster.lineages()) holding both a base and an aligned "
                "model in model_placement.parquet, one of each per lineage; %d base and %d aligned models before "
                "pairing, so %s drop out unpartnered. %d base and %d aligned passages within the pairs. %s The "
                "v6 plate took the median over pooled passages, which lets a model with many passages outweigh "
                "one with few; this counts each model once." % (
                    info1["n_pairs"], info1["n_models"]["base"], info1["n_models"]["aligned"],
                    ", ".join(m.split("/")[-1] for m in info1["unpaired"]),
                    info1["passages"]["base"], info1["passages"]["aligned"],
                    ("FLOOR: a pair is kept only if both of its models have at least %d passages, which drops "
                     "%d of the %d pairs (%s); in a median of per-model medians a model with 2 passages would "
                     "otherwise weigh as much as one with 174." % (
                         FLOOR, info1["n_pairs_all"] - info1["n_pairs"], info1["n_pairs_all"],
                         ", ".join(m.split("/")[-1] for m in info1["dropped"])) if FLOOR else
                     "No floor on passages per model."))) + [""] if PAIRED else []),
         "CAVEATS",
         *wrap("- The concreteness and interiority years are Chicago years. Where the two corpora overlap, in "
               "the 1880s, Chicago sits %.2f z %s abstract than Chadwyck (%d Chadwyck texts, %d Chicago)."
               % (abs(sm), "more" if sm < 0 else "less", n80c, n80i)),
         *wrap("- The interiority history rests on the lexicon alone; the arm effect was also established, and "
               "more strongly, by an LLM coder reading passages blind for degree of interiority "
               "(interiority_in_passages)."),
         *([] if TWO else [
             *wrap("- The rhythm arms set prose from 34 lineages against verse from two model families; early "
                   "decades hold few fiction texts (see the counts)."),
             *wrap("- One rhythm decade is not drawn: the %ds, at %.2f, from %d fiction texts, lies above the "
                   "panel's window. It is in the data and in the smooth; the axis only stops short of it."
                   % (int(off.year.iloc[0]) - 5, float(off.value.iloc[0]), int(off.n.iloc[0])))]),
         *wrap("- API models are not drawn (RH)." if TWO else
               "- API models are not drawn: there is no API prose for the rhythm panel, and RH removed the arm "
               "from all three."),
         *(wrap("- The verse/prose rhythm panel of earlier versions is left out (RH).") if TWO else []), "",
         "Producer: experiments/passage_analysis/novel_arc/literary_history_v2.py (reuses literary_history.py)."]
    open(OUT + ".caption.txt", "w").write("\n".join(L) + "\n")
    for ext in (".png", ".pdf", ".tif", ".caption.txt"):
        print("   ->", os.path.relpath(OUT + ext, HERE))


if __name__ == "__main__":
    main()
