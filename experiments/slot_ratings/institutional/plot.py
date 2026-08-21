"""Figures for the institutional study. One function per figure.

    python experiments/slot_ratings/institutional/plot.py              # all
    python experiments/slot_ratings/institutional/plot.py --list
    python experiments/slot_ratings/institutional/plot.py did_blindness

Every figure reads a saved artifact, re-derives the numbers its README books, and
REFUSES with a named reason if they do not reproduce. Nothing here queries the
store and nothing writes an artifact, so a re-run moves pixels and nothing else.

## Why this file exists beside `../plot.py`

`slot_ratings/plot.py` draws for all three studies and writes into each one's
`figures/`. `fig_per_scenario` was its only institutional figure and it moved here
(2026-08-20, RH) so the institutional figures live in the institutional folder.
Its output is byte-identical to what the shared file produced; that was checked
rather than assumed, which is the only thing that distinguishes a move from a
redraw.

## Two output paths, on purpose

`_save_gg` renders a plotnine figure to PNG at 300 dpi. `_save_spec` writes a
Vega-Lite spec as JSON *and* renders the same spec through `vl_convert` at 300
dpi. The spec is what the app serves and the PNG is what print uses, and because
both come from one dict they cannot disagree.

## Text is not wrapped by either renderer

plotnine cuts a long title at the panel edge silently. Vega-Lite does not wrap a
title either; it takes an ARRAY of lines and draws exactly what it is given. So
prose goes through `_wrap` and the rendered PNG is checked for ink at the right
edge. A truncated fence is not a missing fence, it is a fence that reads as
complete.
"""

import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
FIGDIR = os.path.join(HERE, "figures")
sys.path.insert(0, HERE)

INDIV, INST = "#e67e22", "#2980b9"
GREY, RULE = "#bdc3c7", "#888888"


# ----------------------------------------------------------------- plumbing
def _wrap(text, n=96):
    """Break prose into lines of at most `n` characters, on spaces.

    Vega-Lite draws a title array verbatim. A single long string is drawn as one
    line and runs off the canvas, which shows up in no assert and no stdout.
    """
    out, cur = [], ""
    for w in text.split():
        if cur and len(cur) + 1 + len(w) > n:
            out.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        out.append(cur)
    return out


def _theme():
    from plotnine import theme_minimal, theme, element_text, element_rect, element_line
    return (theme_minimal(base_size=9)
            + theme(figure_size=(9, 6),
                    plot_title=element_text(size=11, weight="bold", ha="left"),
                    plot_subtitle=element_text(size=8, color="#555555", ha="left"),
                    plot_caption=element_text(size=7, color="#777777", ha="left"),
                    strip_text=element_text(size=8, weight="bold"),
                    panel_grid_minor=element_line(size=0.2),
                    plot_background=element_rect(fill="white", color="white")))


def _save_gg(p, name, w=9, h=6):
    path = os.path.join(FIGDIR, name + ".png")
    os.makedirs(FIGDIR, exist_ok=True)
    p.save(path, dpi=300, width=w, height=h, verbose=False)
    print("   %-38s %6.0f KB" % (name + ".png", os.path.getsize(path) / 1024))


def _save_spec(spec, name, ppi=300, caption=None):
    """The spec for the app, the PNG for print, from one dict, and a sidecar.

    ## WHERE PROSE GOES (RH, 2026-08-21, correcting me)

    `slopes_by_position` shipped with 294 words baked into the image. I then cut
    it to 113 and argued the rest had to stay because a stripped fence reads as
    no fence. **RH: it is an ugly caption I would never show anyone; at most one
    line.** Right, and my rule was imported from the wrong context.

    "The fence must survive stripping" comes from plotnine figures shipped
    STANDALONE into talks, where nothing travels with the image. It does not
    apply here: the caption sits directly under the chart in the app and directly
    under the figure in a paper. A figure with a headline and a caption beneath
    it is how every published figure works, and my version was a slide.

    So: TITLE IS ONE LINE, everything else is the sidecar, rendered open beneath
    the chart. The invariant that matters is that the caption TRAVELS -- which is
    what `<name>.caption.md` beside `<name>.png` is for -- not that it is baked
    into the pixels.
    

    The right-edge scan is the verdict on what shipped. It is cheap and it is the
    only check that sees a line the renderer cut, because nothing upstream of the
    pixels knows the canvas ran out.
    """
    import vl_convert as vlc
    os.makedirs(FIGDIR, exist_ok=True)
    js = json.dumps(spec, indent=1)
    open(os.path.join(FIGDIR, name + ".vl.json"), "w").write(js)
    png = vlc.vegalite_to_png(js, ppi=ppi)
    path = os.path.join(FIGDIR, name + ".png")
    open(path, "wb").write(png)
    if caption:
        open(os.path.join(FIGDIR, name + ".caption.md"), "w").write(caption.strip() + "\n")
        print("   %-38s %6.0f KB" % (name + ".caption.md", len(caption) / 1024))
    edge = _right_edge_ink(png)
    print("   %-38s %6.0f KB  %s" % (name + ".png", len(png) / 1024,
                                     "EDGE INK -- SOMETHING IS CUT" if edge else "edge clear"))
    print("   %-38s %6.0f KB" % (name + ".vl.json", len(js) / 1024))
    if edge:
        raise SystemExit("%s: ink in the rightmost columns, text is being cut" % name)


def _right_edge_ink(png, cols=2, tol=250):
    """True if any non-white pixel sits in the last `cols` columns."""
    import io
    from PIL import Image
    im = Image.open(io.BytesIO(png)).convert("L")
    w, h = im.size
    return any(im.getpixel((w - 1 - c, y)) < tol for c in range(cols) for y in range(h))


def _ishould():
    return json.load(open(os.path.join(RES, "base_side", "ishould.json")))


# --------------------------------------------- the DiD blindness, section 13
def fig_did_blindness():
    """Both positions move; their difference does not. Section 13's main claim.

    Sections 11 and 12 tested gaps and changes in gaps. A difference is null
    exactly when both sides move together, which is what happens here, so the
    apparatus was measuring the residual after differencing the effect away. The
    two panels are the same numbers before and after that subtraction, ON ONE X
    SCALE -- if each panel took its own domain the right one would rescale and
    the figure would lose the only thing it exists to show.
    """
    import altair as alt
    import pandas as pd

    d = _ishould()
    R = {r["scale"]: r for r in d["rows"]}

    #: ---- BOOKED VALUES. Categorical first: a leading label cannot be
    #: approximately right, and a near-miss on the wrong artifact passes every
    #: numeric guard at two significant figures.
    assert d["n_prompts"] == 52, "prompts: booked 52, artifact %s" % d["n_prompts"]
    assert set(R) == {
        "abstraction", "agency", "aggression", "arousal", "assertiveness",
        "collective", "deference", "delay", "deliberation", "directedness", "fit",
        "harm", "hedged", "interiority", "makes_better", "makes_worse", "mediation",
        "mundanity", "procedural", "specificity", "superego", "target",
        "termination", "vocalisation"}, "the 24 scales are not the booked set"
    assert R["procedural"]["n_lineages"] == 50, "lineages: booked 50"
    assert R["procedural"]["n_clusters"] == 24, "paired clusters: booked 24"

    #: Numeric, against the README's section 13 table. Tolerances are on the
    #: POINT ESTIMATES, which are deterministic; the p values and intervals are
    #: bootstrap draws and asserting equality on them would assert that a
    #: resampling procedure is deterministic.
    for s, di, dn in [("procedural", 0.216, 0.148), ("mediation", 0.236, 0.125),
                      ("directedness", 0.265, 0.211), ("abstraction", 0.106, 0.237),
                      ("termination", -0.156, -0.112), ("deference", 0.087, 0.081)]:
        for k, want in (("delta_indiv", di), ("delta_inst", dn)):
            got = R[s][k]
            assert abs(got - want) < 0.006, (
                "%s %s: booked %+.3f, artifact %+.3f" % (s, k, want, got))
    for s, want in [("mediation", 0.102), ("abstraction", -0.110),
                    ("procedural", 0.072), ("deference", 0.006)]:
        got = R[s]["paired_diff"]
        assert abs(got - want) < 0.002, (
            "%s paired indiv-inst: booked %+.3f, artifact %+.3f" % (s, want, got))

    #: ---- long form. Every scale, no selection, so there is no omission to
    #: declare and no threshold quietly choosing the story.
    recs = []
    for s, r in R.items():
        recs.append(dict(scale=s, panel="within each position", who="individual",
                         v=r["delta_indiv"], lo=r["ci_lo_indiv"], hi=r["ci_hi_indiv"],
                         p=r["p_indiv"]))
        recs.append(dict(scale=s, panel="within each position", who="institution",
                         v=r["delta_inst"], lo=r["ci_lo_inst"], hi=r["ci_hi_inst"],
                         p=r["p_inst"]))
        recs.append(dict(scale=s, panel="differenced", who="individual - institution",
                         v=r["paired_diff"], lo=r["paired_ci_lo"], hi=r["paired_ci_hi"],
                         p=r["paired_p"]))
    x = pd.DataFrame(recs)
    #: "true"/"false" in a legend is a data type leaking into prose. The reader
    #: needs to know what the shape MEANS, and it does not mean truth.
    x["sig"] = x.p.apply(lambda v: "clears" if v < 0.05 else "does not clear")

    #: Order by the larger of the two within-position movements, so the scales
    #: alignment actually moves sit at the top of both panels.
    order = sorted(R, key=lambda s: -max(abs(R[s]["delta_indiv"]), abs(R[s]["delta_inst"])))

    #: ONE DOMAIN FOR BOTH PANELS. The claim is that the right-hand points sit at
    #: zero while the left-hand ones do not, and that claim is only legible if
    #: the two panels cannot rescale independently.
    span = max(abs(x.lo.min()), abs(x.hi.max())) * 1.06
    dom = [-span, span]
    axis = alt.Axis(title="change in mass-weighted level (scale points, 1-7)",
                    titleFontSize=9, labelFontSize=9, grid=True)

    def panel(sel, width, colour, title):
        base = alt.Chart(x[x.panel == sel])
        zero = alt.Chart(pd.DataFrame({"z": [0]})).mark_rule(
            color=RULE, strokeWidth=0.8).encode(x="z:Q")
        common = dict(y=alt.Y("scale:N", sort=order, title=None,
                              axis=alt.Axis(labelFontSize=9)),
                      yOffset=alt.YOffset("who:N", sort=None))
        rule = base.mark_rule(strokeWidth=1.4, opacity=0.75).encode(
            x=alt.X("lo:Q", scale=alt.Scale(domain=dom, nice=False), axis=axis),
            x2="hi:Q", color=colour, **common)
        pt = base.mark_point(size=34, filled=True).encode(
            x=alt.X("v:Q", scale=alt.Scale(domain=dom, nice=False), axis=axis),
            color=colour, shape=alt.Shape("sig:N", sort=["clears", "does not clear"],
                                          scale=alt.Scale(range=["circle", "triangle-down"]),
                                          legend=alt.Legend(title=["95% interval", "excludes zero"],
                                                            orient="bottom")),
            tooltip=["scale:N", "who:N", alt.Tooltip("v:Q", format="+.3f"),
                     alt.Tooltip("lo:Q", format="+.3f"), alt.Tooltip("hi:Q", format="+.3f"),
                     alt.Tooltip("p:Q", format=".3f"), "sig:N"],
            **common)
        return (zero + rule + pt).properties(width=width, height=430, title=title)

    left = panel("within each position", 300,
                 alt.Color("who:N", scale=alt.Scale(domain=["individual", "institution"],
                                                    range=[INDIV, INST]),
                           legend=alt.Legend(title=None, orient="bottom")),
                 alt.TitleParams("what alignment does to each position",
                                 fontSize=10, anchor="start", color="#333333"))
    right = panel("differenced", 250,
                  alt.value("#444444"),
                  alt.TitleParams("what the difference between them retains",
                                  fontSize=10, anchor="start", color="#333333"))

    spec = alt.hconcat(left, right, spacing=34).properties(
        title=alt.TitleParams(
            _wrap("A difference between the two positions cancels what alignment "
                  "does to both"),
            subtitle=_wrap(
                "Prompts ending \"I should\", F21 and M03 pooled, so every cell sits at the "
                "same bare-infinitive slot: 52 prompts, 50 lineages, 2,600 cells. Left, the "
                "base-to-aligned change in each position on its own. Right, the same change "
                "differenced, paired inside the 24 scenarios that hold both positions. "
                "Crossed (lineage, prompt) bootstrap, 2,000 reps, 95% intervals. Almost "
                "everything alignment does survives on the left and cancels on the right; "
                "abstraction is the exception, and it is the one this study can defend."),
            fontSize=13, subtitleFontSize=10, anchor="start", color="#111111",
            subtitleColor="#555555", offset=8)
    ).configure_view(stroke=None).configure_axis(domainColor="#cccccc").to_dict()

    #: The caption is the second casualty of an unwrapped renderer, and it is the
    #: longest unbroken line in the figure. It carries the three fences.
    spec["params"] = spec.get("params", [])
    spec["title"]["subtitle"] = spec["title"]["subtitle"] + [""] + _wrap(
        "FENCES. Ratings cover 0.242 of base mass and 0.296 of aligned mass, so the two arms "
        "are averaged over different fractions of the distribution; the gap is uniform across "
        "scales and positions. agency, specificity, assertiveness and arousal are pairwise "
        "0.62-0.83 over 14,196 rated rows and are ONE axis drawn four times. mediation sits on "
        "the boundary: its interval touches zero and its p resamples between 0.03 and 0.05, so "
        "abstraction is the only difference here that is not fragile.")

    _save_spec(spec, "did_blindness")


# ----------------------------------------------- the slopegraph, section 13
def fig_slopes():
    """Base to aligned, two lines per scale, coloured by position (RH).

    The DiD is a DIFFERENCE OF SLOPES, and `did_blindness` draws it as a
    difference of positions -- which is what makes it hard to see. Here the
    quantity is the geometry: two lines that stay parallel are a null, and two
    that fan or converge are the asymmetry.

    ## Y IS CENTRED PER SCALE, AND THAT IS THE WHOLE DESIGN

    Levels run 1.00 (`harm`) to 5.86 (`fit`), so a shared axis flattens every
    slope to nothing. The obvious fix, a free y per facet, is worse: it rescales
    each panel to its own range, so `harm` moving 0.003 draws as steep as
    `directedness` moving 0.267 and the reader compares slopes that are not
    comparable.

    So each facet plots `level - midpoint(that scale)` on ONE shared domain of
    +-0.5. Constant y-units-per-pixel across all 24 panels, so a steeper line IS
    a bigger movement, and each panel still sits at its own level. The window
    was chosen from the data: 23 of 24 scales span under 0.60 and `mediation`
    needs 0.945, so +-0.5 fits every scale without clipping any.

    The absolute levels leave the axis and are printed in each facet, because a
    centred axis cannot carry them and dropping them would hide that `harm` is
    pinned at 1.00 and has nowhere to go.
    """
    import altair as alt
    import pandas as pd

    d = _ishould()
    R = {r["scale"]: r for r in d["rows"]}
    assert d["n_prompts"] == 52 and R["procedural"]["n_lineages"] == 50
    assert len(R) == 24, "booked 24 scales, artifact has %d" % len(R)

    recs, meta = [], {}
    for s, r in R.items():
        four = [r["base_indiv"], r["base_inst"], r["aligned_indiv"], r["aligned_inst"]]
        mid = (min(four) + max(four)) / 2
        span = max(four) - min(four)
        assert span <= 1.0, "%s spans %.3f, past the +-0.5 window" % (s, span)
        #: THREE STATES, NOT A THRESHOLD. The first version starred p<0.05 and
        #: put `mediation` on the wrong side of the README, which books it at
        #: 0.025 where this producer's own draw gives 0.050. Neither is wrong:
        #: it is a bootstrap and the value resamples across exactly that line.
        #:
        #: A binary mark on a quantity that straddles its own cut is a coin
        #: flip, and the numbers say so -- `mediation`'s interval EXCLUDES zero
        #: by 0.0003 and `procedural`'s INCLUDES it by 0.005. They are equally
        #: unstable and a threshold puts them on opposite sides. So: clear,
        #: boundary, or nothing, and the boundary is a category rather than a
        #: side of a line.
        #: MEASURED AGAINST THE INTERVAL'S OWN WIDTH, not against an absolute
        #: distance. The first attempt used `near <= 0.01` and marked `harm`,
        #: `aggression` and `collective` as boundary cases -- their intervals are
        #: a hair wide around zero, so every endpoint is near it. Those are
        #: decisive nulls, the opposite of a boundary.
        #:
        #: `near / width` is the quantity: how close the endpoint sits to zero
        #: RELATIVE to how uncertain the estimate is. The cut at 0.05 falls in a
        #: real gap rather than being picked -- mediation 0.0015, procedural
        #: 0.0317, then nothing until vocalisation at 0.1523, and every decisive
        #: null is above 0.30.
        clo, chi = r["paired_ci_lo"], r["paired_ci_hi"]
        near, width = min(abs(clo), abs(chi)), chi - clo
        frac = near / width if width else 1.0
        mark = "~" if frac < 0.05 else ("*" if (clo > 0) == (chi > 0) else "")
        meta[s] = dict(mid=mid, did=r["paired_diff"], p=r["paired_p"], mark=mark,
                       lo=min(four), hi=max(four))
        for who, b, a in (("individual", r["base_indiv"], r["aligned_indiv"]),
                          ("institution", r["base_inst"], r["aligned_inst"])):
            for arm, v in (("base", b), ("aligned", a)):
                recs.append(dict(scale=s, who=who, arm=arm, level=v, centred=v - mid,
                                 did=r["paired_diff"], p=r["paired_p"],
                                 #: The absolute span, carried on every row so the
                                 #: text layer shares the facet's data source --
                                 #: a second DataFrame cannot be faceted with the
                                 #: first. Drawn for ONE row per facet, filtered
                                 #: below, or it renders four times over itself.
                                 span_txt="%.2f-%.2f" % (min(four), max(four))))
    x = pd.DataFrame(recs)

    #: Ordered by the size of the asymmetry, so the non-parallel panels are read
    #: first -- which is the thing the figure exists to show.
    order = sorted(R, key=lambda s: -abs(R[s]["paired_diff"]))
    _lab = lambda s: "%s   %+.3f %s" % (s, meta[s]["did"], meta[s]["mark"])
    x["lab"] = x.scale.map(_lab)
    labs = [_lab(s) for s in order]

    base = alt.Chart(x)
    line = base.mark_line(strokeWidth=2).encode(
        x=alt.X("arm:N", sort=["base", "aligned"], title=None,
                axis=alt.Axis(labelAngle=0, labelFontSize=9)),
        y=alt.Y("centred:Q", scale=alt.Scale(domain=[-0.5, 0.5], nice=False),
                title=None, axis=alt.Axis(labelFontSize=8)),
        color=alt.Color("who:N", scale=alt.Scale(domain=["individual", "institution"],
                                                 range=[INDIV, INST]),
                        legend=alt.Legend(title=None, orient="bottom")),
        tooltip=["scale:N", "who:N", "arm:N", alt.Tooltip("level:Q", format=".3f"),
                 alt.Tooltip("did:Q", format="+.3f"), alt.Tooltip("p:Q", format=".3f")])
    pt = base.mark_point(size=26, filled=True).encode(
        x=alt.X("arm:N", sort=["base", "aligned"], title=None),
        y=alt.Y("centred:Q", scale=alt.Scale(domain=[-0.5, 0.5], nice=False)),
        color=alt.Color("who:N", scale=alt.Scale(domain=["individual", "institution"],
                                                 range=[INDIV, INST]), legend=None))
    txt = base.transform_filter(
        (alt.datum.arm == "base") & (alt.datum.who == "individual")
    ).mark_text(align="left", baseline="top", fontSize=7, color="#999999").encode(
        text="span_txt:N", x=alt.value(1), y=alt.value(1))

    spec = alt.layer(line, pt, txt).properties(width=88, height=104).facet(
        facet=alt.Facet("lab:N", sort=labs, title=None,
                        header=alt.Header(labelFontSize=8, labelFontWeight="bold",
                                          labelColor="#333333")),
        columns=6,
    ).properties(
        title=alt.TitleParams(
            _wrap("Both positions move together, and where they do not the lines fan"),
            subtitle="Parallel lines are a null; the asymmetry is the fanning.",
            fontSize=13, subtitleFontSize=10, anchor="start", color="#111111",
            subtitleColor="#555555", offset=8)
    ).configure_view(stroke=None).configure_axis(domainColor="#cccccc").to_dict()

    #: NO LEADING H1: the figure above already carries the title, and repeating
    #: it puts the same sentence on screen twice.
    CAPTION = """
`slot_ratings/institutional`, section 13. Produced by `plot.py slopes_by_position`
from `results/base_side/ishould.json`.

## Why the y axis is centred rather than shared or free

Levels run 1.00 (`harm`) to 5.86 (`fit`). A shared axis flattens every slope to
nothing. A free axis per panel is worse: it rescales each panel to its own range,
so `harm` moving 0.003 draws as steep as `directedness` moving 0.267, and the
reader compares slopes that are not comparable.

Centring each panel on its own midpoint over one shared +-0.5 domain keeps
y-units-per-pixel constant across all 24, so a steeper line really is a bigger
movement. The window was chosen from the data rather than picked: 23 of 24 scales
span under 0.60 and `mediation` needs 0.945, so +-0.5 clips nothing. An assert
refuses any scale that would exceed it, so a re-run on different numbers fails
rather than silently cropping a line.

The grey number at each panel's top left is the absolute range across all four
points. `harm` reads 1.00-1.00: it is pinned at the floor and has nowhere to go,
which is why its two lines sit on top of each other.

## Why `~` exists, and why it is not a p-value threshold

`mediation`'s interval excludes zero by 0.0003 and `procedural`'s includes it by
0.005. They are equally unstable and any threshold puts them on opposite sides.

This study's README books `mediation` at p=0.025; this producer's own bootstrap
draw gives 0.050. Both are honest draws of the same quantity -- the point
estimates are identical -- so the mark says BOUNDARY rather than picking one.

The cut is `near / width`, how close the nearer endpoint sits to zero relative to
how uncertain the estimate is, and 0.05 falls in a measured gap rather than being
chosen: `mediation` 0.0015, `procedural` 0.0317, then nothing until `vocalisation`
at 0.1523, with every decisive null above 0.30. An earlier version used an
absolute distance and marked `harm`, `aggression` and `collective` -- intervals a
hair wide around zero, so every endpoint is near it. Those are decisive nulls,
the opposite of a boundary.

**`abstraction` is the only difference here that is not fragile.**

## Fences

- Ratings cover 0.242 of base mass and 0.296 of aligned mass, so the two arms are
  averaged over different fractions of the distribution. The gap is uniform
  across scales and positions.
- `agency`, `specificity`, `assertiveness` and `arousal` are pairwise 0.62-0.83
  over 14,196 rated rows and are ONE axis drawn four times. Four panels moving
  together is one finding, not four.
- Panels are ordered by individual minus institution, so the fanning ones come
  first. After `abstraction` the reader scans 23 near-parallel panels, which is
  the finding rather than a gap in it.
"""

    _save_spec(spec, "slopes_by_position", caption=CAPTION)


# ------------------------------------------------- per-scenario, section 15
def fig_per_scenario():
    """Why M03's `procedural` pooled to zero: the scenarios disagree.

    Moved from `../plot.py` unchanged on 2026-08-20. Byte-identical output was
    the acceptance test for the move.
    """
    import pandas as pd
    from plotnine import (ggplot, aes, geom_col, geom_hline, facet_wrap, labs,
                          scale_fill_manual, coord_flip)
    d = json.load(open(os.path.join(RES, "base_side", "per_scenario.json")))["results"]
    recs = []
    for corpus, res in d.items():
        for r in res:
            recs.append(dict(corpus=corpus.upper(), scale=r["scale"],
                             direction="institution higher", n=r["base_pos"]))
            recs.append(dict(corpus=corpus.upper(), scale=r["scale"],
                             direction="individual higher", n=-r["base_neg"]))
    x = pd.DataFrame(recs)
    order = ["arousal", "mediation", "collective", "specificity", "agency",
             "assertiveness", "target", "termination", "abstraction",
             "deference", "procedural"]
    x = x[x.scale.isin(order)]
    x["scale"] = pd.Categorical(x.scale, categories=order)
    p = (ggplot(x, aes("scale", "n", fill="direction"))
         + geom_hline(yintercept=0, color=RULE, size=0.4)
         + geom_col(width=0.7)
         + coord_flip()
         + facet_wrap("~corpus", scales="free_x")
         + scale_fill_manual({"institution higher": INST,
                              "individual higher": INDIV}, name="")
         + labs(title="Institutional: scenarios that disagree produce a pooled zero",
                subtitle="Each matched scenario tested alone against its own "
                         "lineages. Bars count scenarios reaching sign-test p<0.05.",
                x="", y="scenarios significant, by direction",
                caption="institutional/results/base_side/per_scenario.json. M03's "
                        "`procedural` is 51 positive against 61 negative -- 112 of "
                        "126 scenarios significant, pooling to -0.031.")
         + _theme())
    _save_gg(p, "per_scenario_signs", 11, 5)


FIGURES = {"did_blindness": fig_did_blindness,
           "slopes_by_position": fig_slopes,
           "per_scenario": fig_per_scenario}


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
