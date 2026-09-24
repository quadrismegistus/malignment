#!/usr/bin/env python
"""Slopegraphs for Y_diegetic_superego §1 and §3: base -> aligned, per measure.

    python plot.py                 # all
    python plot.py --only slopes   # the headline
    python plot.py --list
    python plot.py --only ci_out ci_in          # prompt_slopes style, with intervals
    python plot.py --only ci_out ci_in --pub    # the same, journal render

Reads `data/y_confirmatory_coded.jsonl` only (pass A, parsed), the file
`scripts/y_diegetic.py` reads. Writes PNGs to `figures/`, 300 dpi.

## THE ARITHMETIC IS y_diegetic.py's, AND THE BOOKED TABLE IS ASSERTED

Unit is the PAIR: a rate inside each base>aligned pair (both arms >= 20
passages), then the mean over pairs for each arm's level, and the MEDIAN of the
per-pair differences for the change. Those are two different statistics and the
finding prints both, so mean(aligned) - mean(base) is NOT the booked delta
(CLEAN_SCENE: -8.04 by means, -6.12 by median pair). The figure draws the means
and labels the median, and the subtitle says so.

Every value in BOOKED is §1 or §3 of the finding to the printed digit. A figure
whose numbers no longer match that table refuses to draw.

## TWO DENOMINATORS, TWO PANELS

Leaving the scene is a rate over ALL passages (§1). What happens inside it is a
rate over passages where a sexual scene occurs (§3). Put on one axis they would
invite the reader to compare a refusal rate with a guilt rate as if they shared a
denominator. They share a y scale, linear and 0-90, because the argument is that
one panel is flat and the other moves, and only a common scale in percentage
points can show that. A log axis would turn refusal's +1pp into the steepest line
on the page.
"""

import argparse
import collections
import functools
import importlib.util
import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "data", "y_confirmatory_coded.jsonl")
FIG = os.path.join(HERE, "figures")
MIN_N = 20      #: passages per arm before a pair contributes (y_diegetic.py)

#: (field, label, panel). Order within a panel is irrelevant to the drawing;
#: labels are placed by value.
OUT = "Staying in the story or leaving it  (% of all passages)"
IN = "Inside the scene  (% of passages with a sexual scene)"
MEASURES = [
    ("continues_narrative", "Story continues", OUT),
    ("sexual_scene", "Sexual scene occurs", OUT),
    ("frame_exit", "Exits the frame", OUT),
    ("assistant_refusal", "Assistant refuses", OUT),
    ("CLEAN_SCENE", "Clean scene (none of the three below)", IN),
    ("SUPEREGO_IN_SCENE", "Any of the below", IN),
    ("consent_hesitation", "Consent hesitation", IN),
    ("guilt_or_shame", "Guilt or shame", IN),
    ("moralisation_in_scene", "Moralization", IN),
]

#: field -> (base %, aligned %, median delta pp, sign agreement), from
#: Y_diegetic_superego.md §1 / §3 and results/y_diegetic.log.
BOOKED = {
    "continues_narrative": (69.58, 69.52, +1.12, 18),
    "sexual_scene": (53.85, 50.01, -0.22, 16),
    "frame_exit": (26.43, 26.92, +0.66, 17),
    "assistant_refusal": (0.10, 1.14, +0.22, 18),
    "CLEAN_SCENE": (84.72, 76.68, -6.12, 27),
    "SUPEREGO_IN_SCENE": (15.18, 21.60, +4.30, 24),
    "consent_hesitation": (11.00, 16.34, +3.99, 24),
    "guilt_or_shame": (3.55, 5.79, +1.27, 23),
    "moralisation_in_scene": (2.37, 3.67, +0.81, 19),
}
N_PASSAGES, N_SEXUAL, N_PAIRS = 41596, 21858, 32

#: The one measure the finding's Limits say does not clear alone (p=0.056).
DOES_NOT_CLEAR = {"moralisation_in_scene"}

SLIVER = {}      #: refusals among sexual-scene passages, set by _frame()

COL = {OUT: "#8a8a8a", IN: "#b8322a"}


def hit(r, f):
    return (r.get(f) is True) if f.isupper() else (r.get(f) == "YES")


def per_pair(rows, f):
    """{pair: (base %, aligned %)} for pairs with >= MIN_N passages in each arm."""
    by = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in rows:
        by[r["pair"]][r["role"]].append(hit(r, f))
    out = {}
    for p, arms in by.items():
        b, a = arms.get("base", []), arms.get("aligned", [])
        if len(b) >= MIN_N and len(a) >= MIN_N:
            out[p] = (100.0 * sum(b) / len(b), 100.0 * sum(a) / len(a))
    return out


def frame():
    """Copies of the cached frames. fig_slopes_pairs rewrites `label` in place,
    and handing out the cached objects let that rewrite reach ci_in's lookup --
    found by running the whole registry, invisible running either alone."""
    s, d = _frame()
    return s.copy(), d.copy()


@functools.lru_cache(maxsize=1)
def _frame():
    """One row per (measure, pair), with the booked summary re-derived and asserted."""
    import pandas as pd
    rows = [json.loads(l) for l in open(SRC)]
    ok = [r for r in rows if r.get("pass") == "A" and r.get("parsed")]
    sx = [r for r in ok if r.get("sexual_scene") == "YES"]
    assert len(ok) == N_PASSAGES, "pass-A parsed passages %d, booked %d" % (len(ok), N_PASSAGES)
    assert len(sx) == N_SEXUAL, "sexual-scene passages %d, booked %d" % (len(sx), N_SEXUAL)
    #: GIVEN A SEXUAL SCENE, CLEAN / SUPEREGO / REFUSAL PARTITION THE PASSAGES:
    #: each passage is exactly one of the three. So CLEAN_SCENE is the mirror of
    #: SUPEREGO_IN_SCENE less the refusals, which is what licenses dropping it
    #: from `ci_in_moral` -- asserted, because the licence is only as good as
    #: the partition.
    part = [(r["CLEAN_SCENE"] is True) + (r["SUPEREGO_IN_SCENE"] is True)
            + (r.get("assistant_refusal") == "YES") for r in sx]
    assert all(k == 1 for k in part), "clean/superego/refusal no longer partition"
    SLIVER["n"] = sum(r.get("assistant_refusal") == "YES" for r in sx)
    #: Categorical: the corpus is Y's, not a near-miss. Five prompts, one coder.
    assert {r["prompt_id"] for r in ok} == {"sexual_explicit_1", "sexual_explicit_3",
                                            "sexual_explicit_5", "sexual_liminal_6",
                                            "sexual_liminal_7"}, "prompt set moved"
    assert {r["coder"] for r in ok} == {"deepseek/deepseek-v4-flash"}, "coder moved"

    recs, summ = [], []
    for f, label, panel in MEASURES:
        pp = per_pair(sx if panel == IN else ok, f)
        assert len(pp) == N_PAIRS, "%s: %d pairs, booked %d" % (f, len(pp), N_PAIRS)
        d = [a - b for b, a in pp.values()]
        mb = statistics.mean(b for b, _ in pp.values())
        ma = statistics.mean(a for _, a in pp.values())
        med = statistics.median(d)
        sign = sum(1 for x in d if (x > 0) == (med > 0))
        got = (round(mb, 2), round(ma, 2), round(med, 2), sign)
        assert got == BOOKED[f], "%s: derived %s, booked %s" % (f, got, BOOKED[f])
        summ.append(dict(field=f, label=label, panel=panel, base=mb, aligned=ma,
                         med=med, sign=sign, n=len(d)))
        for p, (b, a) in pp.items():
            recs.append(dict(field=f, label=label, panel=panel, pair=p, base=b, aligned=a))
    print("   booked §1/§3 reproduced: %d measures x %d pairs" % (len(MEASURES), N_PAIRS))
    return pd.DataFrame(summ), pd.DataFrame(recs)


def dodge(ys, gap):
    """Spread label positions so neighbours sit >= gap apart, keeping their order
    and staying as close to the data as the gap allows."""
    order = sorted(range(len(ys)), key=lambda i: ys[i])
    pos = [ys[i] for i in order]
    for k in range(1, len(pos)):
        pos[k] = max(pos[k], pos[k - 1] + gap)
    #: pushed-up labels drag the block's centre upward; recentre on the data.
    shift = (sum(pos) - sum(ys[i] for i in order)) / len(pos)
    pos = [p - shift for p in pos]
    for k in range(1, len(pos)):
        pos[k] = max(pos[k], pos[k - 1] + gap)
    out = [0.0] * len(ys)
    for k, i in enumerate(order):
        out[i] = pos[k]
    return out


def theme(w, h):
    from plotnine import theme_minimal, theme, element_text, element_rect, element_blank
    return (theme_minimal(base_size=9)
            + theme(figure_size=(w, h),
                    plot_title=element_text(size=11, weight="bold", ha="left"),
                    plot_subtitle=element_text(size=8, color="#555555", ha="left"),
                    plot_caption=element_text(size=7, color="#777777", ha="left"),
                    strip_text=element_text(size=9, weight="bold", ha="left"),
                    panel_grid_major_x=element_blank(),
                    panel_grid_minor=element_blank(),
                    legend_position="none",
                    plot_background=element_rect(fill="white", color="white")))


def save(p, name, w, h):
    os.makedirs(FIG, exist_ok=True)
    path = os.path.join(FIG, name + ".png")
    p.save(path, dpi=300, width=w, height=h, verbose=False)
    print("   %-40s %6.0f KB" % (os.path.relpath(path, HERE), os.path.getsize(path) / 1024))


def fig_slopes():
    """The headline: one line per measure, pair-mean levels, median-pair change."""
    import pandas as pd
    from plotnine import (ggplot, aes, geom_segment, geom_point, geom_text, facet_wrap,
                          scale_x_continuous, scale_y_continuous, scale_color_manual,
                          scale_linetype_manual, labs)
    s, _ = frame()
    s["style"] = ["dashed" if f in DOES_NOT_CLEAR else "solid" for f in s.field]
    s["ly_l"] = 0.0
    s["ly_r"] = 0.0
    for panel in (OUT, IN):
        m = s.panel == panel
        s.loc[m, "ly_l"] = dodge(list(s.loc[m, "base"]), 3.4)
        s.loc[m, "ly_r"] = dodge(list(s.loc[m, "aligned"]), 3.4)
    s["txt_l"] = ["%.1f" % v for v in s.base]
    s["txt_r"] = ["%.1f  %s  (%+.1f pp, %d/%d)" % (a, lab, med, sg, n)
                  for a, lab, med, sg, n in zip(s.aligned, s.label, s.med, s.sign, s.n)]
    s["panel"] = pd.Categorical(s.panel, categories=[OUT, IN])

    W, H = 11, 6.2
    p = (ggplot(s)
         + geom_segment(aes(x=0, xend=1, y="base", yend="aligned", color="panel",
                            linetype="style"), size=1.1)
         + geom_point(aes(x=0, y="base", color="panel"), size=2)
         + geom_point(aes(x=1, y="aligned", color="panel"), size=2)
         + geom_text(aes(x=-0.06, y="ly_l", label="txt_l"), ha="right", size=7.5,
                     color="#333333")
         + geom_text(aes(x=1.06, y="ly_r", label="txt_r"), ha="left", size=7.5,
                     color="#333333")
         + facet_wrap("~panel", ncol=2)
         + scale_x_continuous(breaks=[0, 1], labels=["base", "aligned"],
                              limits=[-0.3, 3.0], expand=(0, 0))
         + scale_y_continuous(limits=[-2, 90], breaks=[0, 25, 50, 75],
                              expand=(0, 0))
         + scale_color_manual(values=COL)
         + scale_linetype_manual(values={"solid": "solid", "dashed": "dashed"})
         + labs(x="", y="%",
                title="Aligned models rarely step out of the scene; "
                      "they stay in it and add hesitation and guilt",
                subtitle="Levels: mean over %d base>aligned pairs of each pair's rate. "
                         "Labels: median per-pair change, then pairs moving that way.\n"
                         "Left over all %s passages; right over the %s in which a sexual "
                         "scene occurs. Same linear scale in both panels."
                         % (N_PAIRS, format(N_PASSAGES, ","), format(N_SEXUAL, ",")),
                caption="Five sexual prompts, 256-token passages, one LLM coder "
                        "(deepseek-v4-flash). Dashed: moralization alone does not clear "
                        "(p=0.056); consent hesitation carries the composite.\n"
                        "Refusal rises elevenfold and stays near 1%. Per-pair spread is "
                        "large; the median is the claim. Y_diegetic_superego §1, §3.")
         + theme(W, H))
    save(p, "diegetic_slopes", W, H)


def fig_slopes_pairs():
    """The constituents: every pair a line, one panel per measure, mean on top."""
    import pandas as pd
    from plotnine import (ggplot, aes, geom_segment, facet_wrap, scale_x_continuous,
                          scale_y_continuous, scale_color_manual, labs)
    s, d = frame()
    #: "the three below" refers to the headline's layout and means nothing here.
    short = {m[1]: m[1].split(" (")[0] for m in MEASURES}
    order = [short[m[1]] for m in MEASURES]
    s["label"] = pd.Categorical(s.label.map(short), categories=order)
    d["label"] = pd.Categorical(d.label.map(short), categories=order)
    W, H = 11, 7.5
    p = (ggplot()
         + geom_segment(d, aes(x=0, xend=1, y="base", yend="aligned", color="panel"),
                        size=0.35, alpha=0.35)
         + geom_segment(s, aes(x=0, xend=1, y="base", yend="aligned", color="panel"),
                        size=1.4)
         + facet_wrap("~label", ncol=5, scales="free_y")
         + scale_x_continuous(breaks=[0, 1], labels=["base", "aligned"],
                              limits=[-0.15, 1.15])
         + scale_y_continuous()
         + scale_color_manual(values=COL)
         + labs(x="", y="%",
                title="Every pair behind the slopegraph",
                subtitle="One thin line per base>aligned pair (%d); thick line the mean over "
                         "pairs. Grey: %% of all passages. Red: %% of passages with a "
                         "sexual scene.\nEach panel has its own y scale, so compare "
                         "directions across panels, not steepness."
                         % N_PAIRS,
                caption="Y_diegetic_superego §1, §3. Pairs with < %d passages per arm "
                        "excluded (none are, for these measures)." % MIN_N)
         + theme(W, H))
    save(p, "diegetic_slopes_pairs", W, H)


# ─────────────────────────────────────────────── prompt_slopes style
#: THE STATISTICS ARE IMPORTED FROM `exploratory/prompt_slopes/plot.py`, not
#: reimplemented: `build()` (median per rung, lineage-unit bootstrap, and the
#: PAIRED within-lineage difference) and its fixed SEED. A second copy is the
#: one that drifts. Loaded by path because both files are called `plot.py`.
def _prompt_slopes():
    path = os.path.join(HERE, "..", "..", "exploratory", "prompt_slopes", "plot.py")
    spec = importlib.util.spec_from_file_location("prompt_slopes_plot", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def ci_frames(panel, drop=()):
    """-> (lev, pairs) from prompt_slopes.build, over one panel's measures.

    `word` is the measure's label, `position` 0 = base and 1 = aligned, the
    unit is the base>aligned pair and `p` is the pair's rate in percent. build()
    uses ONE statistic for both the levels and the paired difference; the
    median is its default and is the statistic the finding books for the
    difference, so the paired medians are asserted against BOOKED.
    """
    ps = _prompt_slopes()
    _, d = frame()
    d = d[(d.panel == panel) & ~d.field.isin(drop)]
    rows = []
    for r in d.itertuples():
        rows.append(dict(unit=r.pair, word=r.label, position=0, p=r.base))
        rows.append(dict(unit=r.pair, word=r.label, position=1, p=r.aligned))
    lev, pairs = ps.build(rows, {"n_rungs": 2}, "median")
    field = {m[1]: m[0] for m in MEASURES}
    for r in pairs.itertuples():
        booked = BOOKED[field[r.word]][2]
        assert round(r.d, 2) == booked and r.n == N_PAIRS, (
            "%s: build() median pair change %.2f over %d, booked %+.2f over %d"
            % (r.word, r.d, r.n, booked, N_PAIRS))
    #: A LINE IS COLOURED ONLY IF ITS PAIRED INTERVAL EXCLUDES ZERO. prompt_slopes
    #: colours the largest faller and riser whatever their size, which is right
    #: for words chosen blind to movement and wrong here: the largest "faller"
    #: in the left panel is sexual_scene at -0.22 [CI across zero], and red would
    #: say it fell.
    pairs["dir"] = ["rise" if lo > 0 else "fall" if hi < 0 else "flat"
                    for lo, hi in zip(pairs.lo, pairs.hi)]
    lev = lev.merge(pairs[["word", "dir"]], on="word")
    return lev, pairs


def _xmax(labels, size_pt, fig_w, pub, nudge=0.05, xmin=-0.1):
    """Right x limit that ends the panel just past the longest end label.

    A fixed limit left an inch of empty panel on some figures and would cut a
    long label on others. The label's width is MEASURED from the font's glyph
    outlines, not estimated from its character count. Then solve for the limit
    at which label end + pad = limit, given that the data-per-inch scale
    depends on the limit itself. The panel is the figure less the y-axis area,
    about 0.8 in in both modes.
    """
    from matplotlib.textpath import TextPath
    from matplotlib.font_manager import FontProperties
    from malignment import figure as F
    fp = FontProperties(family=F.pub_font() if pub else None, size=size_pt)
    w_in = max(TextPath((0, 0), t, prop=fp).get_extents().width for t in labels) / 72
    panel = fig_w - 0.8
    k = (w_in + 0.12) / panel          # 0.12 in of breathing room after the text
    return (1 + nudge + k * -xmin) / (1 - k)


COMPOSITES = {"SUPEREGO_IN_SCENE", "CLEAN_SCENE"}


def draw_ci(panel, name, title, pub=False, drop=(), note=""):
    import matplotlib
    matplotlib.use("Agg")
    from plotnine import (ggplot, aes, geom_segment, geom_point, geom_errorbar,
                          geom_text, labs, scale_x_continuous, scale_y_continuous,
                          scale_color_manual, theme_minimal, theme, element_text,
                          coord_cartesian)
    from malignment import figure as F
    lev, pairs = ci_frames(panel, drop)
    ps_mod = _prompt_slopes()
    if pub:
        #: IN GRAYSCALE THE TONE CARRIES THE ROLE, NOT THE DIRECTION: the slope
        #: already shows direction. Composites (Combined, and Clean scene, its
        #: inverse) in ink; the components that move in the mid gray; whatever
        #: does not move in the light gray. Tones are figure.py's ramp, and the
        #: journal's halftone rule is asserted on them below rather than trusted.
        field = {m[1]: m[0] for m in MEASURES}
        lev["dir"] = ["flat" if d_ == "flat" else
                      "composite" if field[w] in COMPOSITES else "component"
                      for w, d_ in zip(lev.word, lev.dir)]
    seg = (lev.pivot(index=["word", "dir"], columns="position", values="central")
              .reset_index().rename(columns={0: "y", 1: "yend"}))
    ends = lev[lev.position == 1].merge(pairs[["word", "d", "lo", "hi"]],
                                        on="word", suffixes=("", "_d"))
    ceiling = float(lev.hi.max())
    H = float(F.PUB_SIZE[1]) if pub else 6.0
    gap = ceiling * (0.055 * F.PUB_SIZE[1] / H if pub else 0.032)
    ends["label_y"] = dodge(list(ends.central), gap)
    #: a label pushed below zero would drag the probability axis negative
    lift = max(0.0, -min(ends.label_y))
    ends["label_y"] = ends.label_y + lift
    if pub:
        #: the parenthetical definitions ran off a 4.8 in panel; the legend
        #: carries them in the journal render
        ends["txt"] = [w.split(" (")[0] for w in ends.word]
        COL = {"composite": F.PUB_INK, "component": F.PUB_MID, "flat": F.PUB_GRAY}
        F.check_halftones({k: COL[k] for k in set(lev.dir)})   # malignment.figure
    else:
        ends["txt"] = ["%s  %+.1f [%+.1f, %+.1f]" % (w, d_, lo, hi) for w, d_, lo, hi
                       in zip(ends.word, ends.d, ends.lo_d, ends.hi_d)]
        COL = {"rise": "#1c7ed6", "fall": "#c92a2a", "flat": "#868e96"}
    W = float(F.PUB_SIZE[0]) if pub else 9.0
    lw, rw, ps_, ts = ((F.PUB_LINE_PT, F.PUB_RULE_PT, 1.2, F.PUB_FONT_PT) if pub
                       else (0.8, 0.45, 2.0, 8))
    p = (ggplot(lev, aes("position", "central"))
         + geom_segment(aes(x=0, xend=1, y="y", yend="yend", color="dir"),
                        data=seg, size=lw)
         + geom_errorbar(aes(ymin="lo", ymax="hi", color="dir"),
                         width=0.03 if pub else 0.04, size=rw)
         + geom_point(aes(color="dir"), size=ps_)
         + geom_text(aes(x=1, y="label_y", label="txt", color="dir"), data=ends,
                     ha="left", nudge_x=0.05, size=ts,
                     **({"family": F.pub_font()} if pub else {}))
         + scale_color_manual(COL, guide=None)
         + scale_x_continuous(breaks=[0, 1], minor_breaks=[],
                              labels=["Base models", "Aligned models"] if pub
                              else ["base", "aligned"],
                              limits=(-0.1, _xmax(ends.txt, ts, W, pub)))
         + scale_y_continuous(labels=lambda v: ["%g%%" % x for x in v])
         + coord_cartesian(ylim=(0, max(ceiling, float(ends.label_y.max())) * 1.04)))
    ylab = ("% of passages" if panel == OUT
            else "% of passages with a sexual scene")
    if pub:
        p = p + labs(x="", y=ylab) + F.pub_theme()
    else:
        #: WRAPPED, because plotnine cuts a long line at the figure edge
        #: silently and the first render lost both the subtitle's and the
        #: caption's ends. Widths are prompt_slopes' (10 in) scaled to 9 in.
        wr = ps_mod.wrap
        p = (p + labs(
                x="", y=ylab, title=title,
                subtitle=wr("Median over %d base>aligned pairs of each pair's rate, "
                          "bootstrap 95%% intervals; the unit is the PAIR. Labels: "
                          "median PAIRED change (pp) and its interval, which is the "
                          "error bar of the movement. Colored only where that "
                          "interval excludes zero: blue rises, red falls, gray does "
                          "not move." % N_PAIRS, 94),
                caption=wr("Y_diegetic_superego %s. Levels are medians, so they "
                         "differ from the finding's table, which prints means; the "
                         "changes are the finding's medians to the digit. Five "
                         "sexual prompts, one LLM coder (deepseek-v4-flash)."
                         % ("§1, over all %s passages" % format(N_PASSAGES, ",")
                            if panel == OUT else
                            "§3, over the %s with a sexual scene"
                            % format(N_SEXUAL, ",")) + note, 104))
             + theme_minimal()
             + theme(figure_size=(9, H),
                     plot_title=element_text(size=11, weight="bold", ha="left"),
                     plot_subtitle=element_text(size=8, ha="left"),
                     plot_caption=element_text(size=7, ha="left")))
    out = os.path.join(FIG, name + ("_pub" if pub else "") + ".png")
    os.makedirs(FIG, exist_ok=True)
    for path in F.save(p, out):
        print("   %-40s %6.0f KB" % (os.path.relpath(path, HERE),
                                      os.path.getsize(path) / 1024))


def fig_ci_out(pub=False):
    """Staying or leaving, % of all passages: the four flat-or-nearly lines."""
    draw_ci(OUT, "diegetic_ci_leaving", pub=pub,
            title="Whether the model stays in the story barely changes")


def fig_ci_in(pub=False):
    """Inside the scene, % of sexual scenes: the moral apparatus rises."""
    draw_ci(IN, "diegetic_ci_inside", pub=pub,
            title="Inside the scene, aligned models add hesitation and guilt")


def fig_ci_in_moral(pub=False):
    """Inside the scene without clean scene, so the axis fits the moral measures."""
    frame()      # sets SLIVER
    draw_ci(IN, "diegetic_ci_inside_moral", pub=pub, drop={"CLEAN_SCENE"},
            title="Inside the scene, aligned models add hesitation and guilt",
            note=(" Clean scene is omitted: among sexual scenes every passage is "
                  "clean, superego or refused, so clean is the superego line "
                  "inverted, less %d refusals." % SLIVER["n"]))


FIGURES = {"slopes": fig_slopes, "slopes_pairs": fig_slopes_pairs,
           "ci_out": fig_ci_out, "ci_in": fig_ci_in, "ci_in_moral": fig_ci_in_moral}
PUB = {"ci_out", "ci_in", "ci_in_moral"}      #: figures with a --pub render


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", choices=sorted(FIGURES))
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--pub", action="store_true",
                    help="journal render (grayscale, 4.8 in, no title) of the ci_* figures")
    a = ap.parse_args()
    if a.list:
        for k, fn in FIGURES.items():
            print("%-14s %s" % (k, fn.__doc__.strip().splitlines()[0]))
        return 0
    for k in a.only or FIGURES:
        if a.pub and k in PUB:
            FIGURES[k](pub=True)
        elif not a.pub:
            FIGURES[k]()
    return 0


if __name__ == "__main__":
    sys.exit(main())
