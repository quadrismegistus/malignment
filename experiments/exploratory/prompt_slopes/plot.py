#!/usr/bin/env python
"""One prompt, every lineage: the site slopegraph.

    python experiments/exploratory/prompt_slopes/plot.py "She was so angry she wanted to"
    ... "prompt" --words kill,scream,hit      # curated list, LABELLED as such
    ... "prompt" --top 12                     # declared rule: top-N by base mass
    ... "prompt" --stat mean                  # median is the default
    ... "prompt" --units chains               # rungs instead of endpoints

PORTED FROM `malign-logits/meta/M01_displacement/scripts/plot_prompt_words.py`
(RH's design, 2026-08-14). **Rewritten in plotnine rather than copied**: the
original is matplotlib, and the convention of record here is plotnine at 300 dpi.
Nothing in a slopegraph with paired intervals needs matplotlib -- it is
`geom_segment` plus `geom_point` plus `geom_errorbar`.

## WHY THIS FIGURE FIRST

**It plots LEVELS, not derived statistics.** `p` at each rung, per lineage. So it
is unblocked by the two rulings that currently stop a displacement panel: the
`dN` convention (two conventions, neither canonical, disagreeing in sign on 14.8%
of prompts) and the leak correction (96% co-signed, so `dN` needs a subtractive
bound). Neither touches a level. A figure that shows what the models do, rather
than a statistic computed from what they do, is the one that can be drawn today.

## THE THREE DISCIPLINES, CARRIED OVER RATHER THAN REINVENTED

1. **Word selection is DECLARED and blind to movement.** Default is top-N by mass
   at the base rung. `--words` prints `curated list` in the subtitle, because
   intervals on words picked BECAUSE they moved are conditioned on the selection.
2. **The paired difference is the error bar of the movement.** Marginal intervals
   can overlap while the within-lineage change is tight, so the two largest
   movers are annotated with the paired-difference interval rather than leaving
   the reader to eyeball two overlapping bars.
3. **Median by default**, because probabilities are heavy-tailed across families
   and a mean can be one family's obsession. `--stat mean` is available and the
   choice is stated in the subtitle either way.

## WHAT THIS DOES NOT DO

It does not compute the contrast. `movement.contrast` reads the store and returns
tidy rows; this file turns rows into a picture. That split is the repo's rule --
arithmetic in the module or in a producer, never smuggled into a renderer -- and
it is what lets the app ask for the same figure without a second implementation.
"""
import argparse
import os
import re
import sys
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

import numpy as np                                          # noqa: E402
import pandas as pd                                         # noqa: E402

from malignment import movement, roster                     # noqa: E402

FIGURES = os.path.join(HERE, "figures")
#: Fixed, so a re-run reproduces the intervals rather than jittering them.
SEED = 20260817
#: The wrap widths are in CHARACTERS and they exist because plotnine neither
#: wraps a title nor widens the canvas for one: a long line is cut at the edge,
#: mid-word, silently -- not in the code, not in stdout, not in any assert. The
#: loss exists only in the rendered PNG, and what goes is always the end of the
#: line, which is where the quantification lives.
WRAP_TITLE, WRAP_SUB, WRAP_CAP = 78, 104, 116

#: ── PUBLICATION MODE ──────────────────────────────────────────────────────
#: **A JOURNAL FIGURE CARRIES NO TEXT THE LEGEND WILL CARRY.** Critical
#: Inquiry typesets the number, title, legend and notes itself, and forbids a
#: figure repeating them. So `--pub` drops the title, the method note and the
#: faller/riser footer -- NOT because they are wrong but because they belong in
#: the manuscript, and a figure that duplicates its own legend is the defect
#: the rule names. Everything that is the figure's OWN labelling stays: the y
#: axis title, the tick labels, the rung labels, and the word labels at the
#: right, which double as the key the same rules require to sit inside the
#: figure.
#:
#: **RENDERED AT FINAL SIZE, WHICH IS THE WHOLE POINT.** The screen figure is
#: 10 inches wide and the text block is 4.5, so a 12 pt label prints at about
#: 5 pt. Rendering at 4.5 in means the size set here IS the size on the page,
#: and no reduction happens to undo it. 4.5 x 3.15 keeps the screen aspect.
#: **4.8 IN, MEASURED, NOT THE 4.5 EVERYONE QUOTES.** RH measured Critical
#: Inquiry's text block on the page; 4.5 was the received figure and it was
#: wrong. Height follows at the same 10:7 aspect. `--height` overrides it.
PUB_SIZE = (4.8, 3.36)      # inches; 1440 x 1008 px at 300 dpi
PUB_FONT_PT = 9             # ONE size for every piece of text in the figure
#: at final size, so this is the printed weight. Below ~0.5 pt a rule can
#: drop out of the plate entirely.
PUB_RULE_PT = 0.5
PUB_LINE_PT = 1.0
#: **HUE IS NOT THE ONLY CHANNEL.** Colour is permitted for a line chart, but
#: some copies print grayscale, where #c92a2a and #1c7ed6 are two similar mid
#: grays. The two named words therefore differ in DASH as well, and the eight
#: unnamed words go lighter so the figure reads at 4.5 inches.
PUB_GRAY = "#9aa1a7"


def _pub_font():
    """One sans-serif, resolved once, with a fallback that actually exists.

    Naming a font matplotlib cannot find is not an error -- it substitutes
    DejaVu Sans and warns into a stream nobody reads, so the figure silently
    ships in a different face than the one declared.
    """
    from matplotlib import font_manager
    have = {f.name for f in font_manager.fontManager.ttflist}
    for fam in ("Helvetica", "Arial", "Helvetica Neue", "DejaVu Sans"):
        if fam in have:
            return fam
    return "sans-serif"


def wrap(s, n):
    return "\n".join(textwrap.wrap(s, n)) if s else s


def units_for(kind, pairs=None):
    """(units, label). A unit is a lineage; its rungs are the x positions."""
    if pairs:
        seq = []
        for spec in pairs:
            rungs = [m.strip() for m in spec.split(">") if m.strip()]
            if len(rungs) < 2:
                raise SystemExit("--pair wants base>aligned, got %r" % spec)
            seq.append((rungs[0].split("/")[-1], rungs))
        return seq, "%d passed unit%s" % (len(seq), "" if len(seq) == 1 else "s")
    if kind == "endpoints":
        ep, unresolved = roster.endpoints()
        #: **`unresolved` IS CHECKED, NOT IGNORED.** `docs/HOWTO.md`: a caller
        #: that ignores it is choosing by accident.
        if unresolved:
            print("note: %d unresolved lineage(s) excluded: %s"
                  % (len(unresolved), ", ".join(sorted(unresolved))))
        return ([(b.split("/")[-1], [b, a]) for b, a in ep.items()],
                "%d declared endpoint pairs" % len(ep))
    if kind == "chains":
        ch = roster.chains()
        seq = [(c["base"].split("/")[-1], [c["base"], c["sft"], c["pref"]])
               for c in ch]
        return seq, "%d declared chains (base, sft, pref)" % len(seq)
    raise SystemExit("--units wants endpoints or chains")


def boot_ci(v, stat, reps=2000, rng=None):
    """Bootstrap interval for the central tendency. The UNIT is the lineage."""
    v = np.asarray([x for x in v if x is not None], dtype=float)
    if len(v) < 3:
        return float("nan"), float("nan")
    rng = rng or np.random.default_rng(SEED)
    f = np.median if stat == "median" else np.mean
    draws = f(rng.choice(v, size=(reps, len(v)), replace=True), axis=1)
    return float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))


def build(rows, meta, stat):
    """Tidy rows -> (per-word-per-position frame, paired-difference frame)."""
    df = pd.DataFrame(rows)
    f = np.median if stat == "median" else np.mean
    rng = np.random.default_rng(SEED)
    out = []
    for (w, pos), g in df.groupby(["word", "position"], sort=False):
        lo, hi = boot_ci(g["p"].tolist(), stat, rng=rng)
        out.append({"word": w, "position": pos, "central": float(f(g["p"])),
                    "lo": lo, "hi": hi, "n": len(g)})
    lev = pd.DataFrame(out)

    #: THE PAIRED DIFFERENCE, first rung to last, WITHIN each lineage. This is
    #: the quantity the figure is about, and it is not the difference of the two
    #: marginal intervals -- those can overlap while every unit moved the same
    #: way. Computed here so the annotation cannot drift from the panel.
    first, last = 0, meta["n_rungs"] - 1
    a = df[df.position == first].set_index(["unit", "word"])["p"]
    b = df[df.position == last].set_index(["unit", "word"])["p"]
    d = (b - a).dropna().reset_index().rename(columns={0: "d", "p": "d"})
    pairs = []
    for w, g in d.groupby("word", sort=False):
        lo, hi = boot_ci(g["d"].tolist(), stat, rng=rng)
        pairs.append({"word": w, "d": float(f(g["d"])), "lo": lo, "hi": hi,
                      "n": len(g)})
    return lev, pd.DataFrame(pairs).sort_values("d")


def draw(lev, pairs, meta, stat, out_path, rung_labels, pub=False,
         intervals="all", repel="auto", yfloor="auto", height=None,
         graylabel="each"):
    #: **`Agg` BEFORE PLOTNINE IMPORTS ANYTHING.** plotnine draws through
    #: matplotlib, whose default backend on macOS is the GUI one, and a GUI
    #: FigureManager cannot be created off the main thread: called from the
    #: app's threaded HTTP server this raises rather than drawing. Setting it
    #: here rather than at module import keeps the CLI's startup cheap, and it
    #: must precede the plotnine import because the backend is fixed at first
    #: use. The archive's script did the same thing for the same reason.
    import matplotlib
    matplotlib.use("Agg")
    from plotnine import (ggplot, aes, geom_segment, geom_point, geom_errorbar,
                          geom_text, labs, scale_x_continuous, scale_y_continuous,
                          theme_minimal,
                          theme, element_text, element_rect, element_blank,
                          element_line, scale_color_manual,
                          scale_linetype_manual, coord_cartesian,
                          geom_blank)

    #: plotnine has no "add nothing" object, and `+ None` raises. `geom_blank`
    #: with no aesthetics draws nothing and composes, so the conditional layers
    #: above stay expressions rather than becoming an imperative build.
    def _noop():
        return geom_blank()

    #: Largest faller red, largest riser blue, everything else grey -- the
    #: archive's scheme. The two named words are the ones the annotation covers,
    #: so colour and text agree by construction rather than by editing.
    faller = pairs.iloc[0]["word"] if len(pairs) else None
    riser = pairs.iloc[-1]["word"] if len(pairs) else None
    role = {w: ("faller" if w == faller else "riser" if w == riser else "other")
            for w in lev["word"].unique()}
    lev = lev.assign(role=lev["word"].map(role))

    seg = []
    for w, g in lev.groupby("word", sort=False):
        g = g.sort_values("position")
        for i in range(len(g) - 1):
            seg.append({"word": w, "role": role[w],
                        "x": g.iloc[i]["position"], "y": g.iloc[i]["central"],
                        "xend": g.iloc[i + 1]["position"],
                        "yend": g.iloc[i + 1]["central"]})
    seg = pd.DataFrame(seg)

    last_pos = meta["n_rungs"] - 1
    ends = lev[lev.position == last_pos].copy()
    #: **ONE LABEL FOR THE BUNDLE.** The gray lines exist to show `nearly
    #: flat`, not to be told apart, and labelling them individually is what
    #: forced the repelling that put `cry` at 1.8% against a true 2.97%. A
    #: single label beside the cluster carries no false position at all: it
    #: names a group and sits at the group's own centre, so there is no
    #: implied reading of an individual height. Which line is which goes in
    #: the caption, where a reader who cares can find it. Paper-claude's
    #: first option, 2026-09-15, and it costs no leader lines.
    if graylabel == "cluster" and (ends["role"] == "other").any():
        g = ends[ends["role"] == "other"].sort_values("central", ascending=False)
        keep = ends[ends["role"] != "other"].copy()
        one = g.iloc[[0]].copy()
        one["word"] = ", ".join(g["word"].tolist())
        #: the MIDPOINT of the bundle, not its top: a label level with the
        #: highest member would read as that member's value
        one["central"] = float(g["central"].median())
        ends = pd.concat([keep, one], ignore_index=True)

    #: ── LABELS DO NOT OVERPRINT, AND THE FIRST RENDER PROVED THEY WOULD.
    #:
    #: The end labels sit where the lines CONVERGE -- flat words pile into a
    #: band a few thousandths wide -- so `punch` printed on `cry` and `go` on
    #: `slap`. `geom_text` overlap is invisible to every check that is not the
    #: rendered image: no assert sees it, and the text-width audits measure
    #: against the panel edge, not against each other.
    #:
    #: A greedy push-apart in DATA UNITS, working outward from the top. The
    #: minimum gap is a fraction of the drawn range rather than a constant,
    #: because the range is whatever this prompt's probabilities happen to span.
    #: The POINTS stay where they are and only the text moves, so nothing about
    #: the geometry is falsified -- a label is a name, not a measurement.
    span = float(lev["hi"].max() - min(0.0, lev["lo"].min()))
    #: **THE GAP IS PHYSICAL, NOT A FRACTION OF THE DATA.** 0.028 of the span
    #: separates 12 labels on a 7-inch canvas and COLLIDES them on a 3.15-inch
    #: one, because the same fraction of data is now half the paper. Derived
    #: from the type size and the panel height instead: a 9 pt line is 0.125 in
    #: tall, the panel is about 2.6 in, so one line-height plus leading is
    #: ~0.055 of the span. Carrying the screen constant into the publication
    #: render is exactly how a figure passes every check and arrives unreadable.
    #: scales with the panel: a taller figure really does have room for more
    gap = span * ((0.055 * PUB_SIZE[1] / float(height or PUB_SIZE[1]))
                  if pub else 0.028)
    ends = ends.sort_values("central", ascending=False).reset_index(drop=True)
    ly = ends["central"].tolist()
    #: **REPELLING IS A COST, NOT A FEATURE.** Every pixel a label moves off its
    #: line end is a pixel of false position, and a reader takes label height
    #: for value. With six words there is usually room to set them AT the line
    #: ends and pay nothing. `auto` repels only when two labels would actually
    #: collide; `off` never repels and accepts overlap; `on` always repels.
    _do_repel = (repel == "on") or (
        repel == "auto" and any(ly[i - 1] - ly[i] < gap
                                for i in range(1, len(ly))))
    for i in (range(1, len(ly)) if _do_repel else []):
        if ly[i - 1] - ly[i] < gap:
            ly[i] = ly[i - 1] - gap
    #: **THE LABELS MUST NOT DRAG THE AXIS BELOW ZERO.** The greedy pass above
    #: pushes each colliding label down, and with twelve words on a short panel
    #: the stack ran past 0 and plotnine extended the scale to accommodate it --
    #: printing `-0.05` on an axis of PROBABILITIES. That is not a cosmetic
    #: defect: it is the figure asserting a value the quantity cannot take, and
    #: nothing in the pipeline objected because the labels are just points.
    #: Bounded to the data's own range instead: push the stack back up off the
    #: floor, re-separate upward, and if it still will not fit, distribute the
    #: whole column evenly. Labels then sit further from their lines, which is
    #: the honest trade -- they are an ordered key, not a measurement.
    floor = min(0.0, float(lev["lo"].min()))
    ceiling = float(lev["hi"].max())
    if _do_repel and ly and min(ly) < floor:
        #: CLAMP THE BOTTOM AND RELAX UPWARD -- do NOT shift the column. The
        #: first version shifted every label by the deficit, which pushed the
        #: top one past the ceiling and triggered an even-spread fallback, and
        #: THAT put `kill` at 0.155 on a chart where kill is 0.04. A key whose
        #: height can be read as a value and is not one is worse than the
        #: negative axis it replaced: the axis error announces itself, this one
        #: reads as a measurement. Only the colliding tail moves; a label with
        #: room keeps its own height.
        ly[-1] = floor
        for i in range(len(ly) - 2, -1, -1):
            if ly[i] - ly[i + 1] < gap:
                ly[i] = ly[i + 1] + gap
    #: A HARD REFUSAL, NOT A SILENT SQUEEZE. If the column still does not fit,
    #: the panel is too short for this many words at this type size and no
    #: placement rule fixes it -- say so and name both numbers rather than
    #: shipping a figure whose key has quietly stopped meaning anything.
    if _do_repel and ly and max(ly) > ceiling:
        raise SystemExit(
            "%d labels at %.4f gap need %.4f of range; the data spans %.4f. "
            "Raise the panel height or cut --top; a fitted-by-force key stops "
            "being readable as position."
            % (len(ly), gap, (len(ly) - 1) * gap, ceiling - floor))
    ends["label_y"] = ly

    n = meta["n_units"]
    title = wrap("%s at the blank, across %d lineages" % (
        ("`%s`" % meta["prompt"]), n), WRAP_TITLE)
    sub = wrap(
        "%s of per-lineage word probability with bootstrap 95%% intervals; the "
        "unit is the LINEAGE. Words: %s. %d of %d cells sit at or below theta "
        "(0.001) and are drawn at the floor -- below theta means smaller than "
        "0.001, not absent."
        % (stat.capitalize(), meta["selection"], meta["below_theta"],
           meta["n_cells"]), WRAP_SUB)
    cap_bits = []
    if faller is not None:
        r = pairs.iloc[0]
        cap_bits.append("largest faller %s %+.4f [%+.4f, %+.4f]"
                        % (r["word"], r["d"], r["lo"], r["hi"]))
    if riser is not None and riser != faller:
        r = pairs.iloc[-1]
        cap_bits.append("largest riser %s %+.4f [%+.4f, %+.4f]"
                        % (r["word"], r["d"], r["lo"], r["hi"]))
    cap_bits.append("intervals on the PAIRED within-lineage difference, "
                    "which is the error bar of the movement")
    if meta["missing_units"]:
        cap_bits.append("%d unit(s) dropped for missing rungs"
                        % len(meta["missing_units"]))
    cap = wrap(" · ".join(cap_bits), WRAP_CAP)

    #: 40 characters is the measured fit: ~4.5 pt per character at 9 pt
    #: against a ~194 pt panel height.
    #: THE BREAK GOES BEFORE THE PROMPT, not wherever 40 characters happens to
    #: fall. Wrapping the whole string split the prompt itself across lines
    #: ("She was / so angry she wanted to"), which reads as two fragments
    #: rather than as the quoted stimulus. The prompt is still wrapped if it is
    #: long enough to need it -- some in this battery are multi-line verse.
    ytitle = "\n".join(
        ["Probability of word following"]
        + textwrap.wrap('\u201c%s\u201d' % meta["prompt"].replace("\n", " "), 40))
    #: **TWO TONES, NOT THREE. RH, 2026-09-16.** Both named words solid black
    #: -- points, lines, error bars and labels -- and the flat bundle at
    #: #808080 throughout. 100% against 49.8% ink: one separation of 50 points,
    #: well past CI's 20-point minimum, with the only halftone comfortably
    #: inside the 20-80% band.
    #:
    #: **kill AND scream ARE NOT DISTINGUISHED BY TONE, DELIBERATELY.** They
    #: cross, so each is traceable from either end, and the word sits at the
    #: end of its own line. A third grey to separate them would have bought a
    #: distinction the crossing already makes, at the cost of pushing one of
    #: them toward the flat bundle it is supposed to stand apart from.
    _GRAY_PUB = "#808080"
    COLORS = ({"faller": "#000000", "riser": "#000000", "other": _GRAY_PUB}
              if pub else
              {"faller": "#c92a2a", "riser": "#1c7ed6", "other": "#868e96"})
    #: every de-emphasised mark in the pub render uses the same value, so the
    #: bundle's line, point and label cannot drift apart from each other
    GRAY = _GRAY_PUB if pub else PUB_GRAY

    if not pub:
        p = (ggplot(lev, aes("position", "central"))
             + geom_segment(aes(x="x", y="y", xend="xend", yend="yend",
                                color="role"), data=seg, size=0.7, alpha=0.9)
             + geom_errorbar(aes(ymin="lo", ymax="hi", color="role"), width=0.04,
                             size=0.4, alpha=0.7)
             + geom_point(aes(color="role"), size=2.0)
             + geom_text(aes(x="position", y="label_y", label="word", color="role"),
                         data=ends, ha="left", nudge_x=0.06, size=8)
             + scale_color_manual(COLORS, guide=None)
             + scale_x_continuous(breaks=list(range(meta["n_rungs"])),
                                  labels=rung_labels,
                                  limits=(-0.12, last_pos + 0.55))
             + labs(title=title, subtitle=sub, caption=cap,
                    x="", y="word probability")
             + theme_minimal()
             + theme(figure_size=(10, 7),
                     plot_title=element_text(size=12, weight="bold"),
                     plot_subtitle=element_text(size=8),
                     plot_caption=element_text(size=7, ha="left")))
    else:
        #: **SPLIT BY ROLE INTO TWO LAYERS RATHER THAN SCALING SIZE.** The eight
        #: unnamed words need a lighter, thinner rule than the two named ones,
        #: and mapping `size` to a discrete aesthetic is the plotnine API that
        #: changed name between versions. Two layers cannot break that way.
        fnt = _pub_font()
        named = seg[seg["role"] != "other"]
        rest = seg[seg["role"] == "other"]
        e_named = lev[lev["role"] != "other"]
        e_rest = lev[lev["role"] == "other"]
        p = (ggplot(lev, aes("position", "central"))
             + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"),
                            data=rest, color=GRAY, size=PUB_RULE_PT)
             #: ALL SOLID, RH 2026-09-15. The dash was carrying the grayscale
             #: distinction; with it gone the two named lines differ from the
             #: gray ones by WEIGHT (1.0 pt against 0.5) and from each other by
             #: hue alone -- so a grayscale plate renders #c92a2a and #1c7ed6
             #: as two similar mid grays and the reader tells them apart by the
             #: word at the line end, which is why the key sits there.
             + geom_segment(aes(x="x", y="y", xend="xend", yend="yend",
                                color="role"),
                            data=named, size=PUB_LINE_PT)
             #: **INTERVALS ONLY WHERE A CLAIM RESTS ON THEM.** Ten gray
             #: whiskers on a 4.5-inch panel are ink that says "these did not
             #: move" in the least legible way available, and they crowd the
             #: two intervals a reader is meant to read. `named` draws them on
             #: the faller and riser alone. The gray words keep their POINTS,
             #: so their flatness is still visible -- what goes is the
             #: uncertainty on a quantity nothing in the text claims.
             + (geom_errorbar(aes(ymin="lo", ymax="hi"), data=e_rest,
                              color=GRAY, width=0.03, size=PUB_RULE_PT)
                if intervals == "all" else _noop())
             #: **THE GRAY POINTS GO UNDER THE NAMED ERROR BARS TOO.** Putting
             #: the gray POINT layer after the named ERRORBAR layer left gray
             #: dots sitting on the red whisker -- the z-order was fixed within
             #: each kind of mark and not across kinds, which looks fixed and
             #: is not. All gray, then all named. Nothing is hidden by it: a
             #: 0.5 pt whisker crossing a 1.2 pt dot still leaves the dot
             #: readable, so position survives the restacking.
             + geom_point(data=e_rest, color=GRAY, size=1.2)
             + (geom_errorbar(aes(ymin="lo", ymax="hi", color="role"),
                              data=e_named, width=0.03, size=PUB_RULE_PT)
                if intervals in ("all", "named") else _noop())
             #: **DRAW ORDER IS THE Z ORDER.** One layer holding every word
             #: leaves the stacking to row order, so a gray point could land on
             #: top of the red line. Gray first, named second, for points and
             #: for the key alike.
             + geom_point(aes(color="role"), data=e_named, size=1.2)
             + geom_text(aes(x="position", y="label_y", label="word"),
                         data=ends[ends["role"] == "other"], color=GRAY,
                         ha="left", nudge_x=0.04, size=PUB_FONT_PT, family=fnt)
             + geom_text(aes(x="position", y="label_y", label="word",
                             color="role"),
                         data=ends[ends["role"] != "other"], ha="left",
                         nudge_x=0.04, size=PUB_FONT_PT, family=fnt)
             + scale_color_manual(COLORS, guide=None)
             #: wider right margin than the screen render: the words are the
             #: key, and a key clipped by the panel edge is not one
             #: sized to the longest word at 9 pt, not guessed: a 6-character
             #: label is ~0.38 in, which is ~0.30 of a rung step on this panel.
             #: **`minor_breaks=[]` AT THE SCALE, NOT `axis_ticks_minor_x` IN
             #: THE THEME.** With majors at 0 and 1 the scale generates a minor
             #: break at 0.5, drawn as an unlabelled tick between "Base models"
             #: and "Aligned models" that reads as a third, nameless rung.
             #: Blanking the themeable did NOT remove it: `pub_theme` also sets
             #: `axis_ticks` explicitly and the parent wins over the child.
             #: Removing the BREAK removes the tick at source -- checked, the
             #: axis goes from minor ticks [0.5] to [].
             + scale_x_continuous(breaks=list(range(meta["n_rungs"])),
                                  minor_breaks=[],
                                  labels=rung_labels,
                                  limits=(-0.08, last_pos + 0.34))
             #: PER CENT, not a decimal fraction: `10%` reads at a glance where
             #: `0.10` needs a beat. Formatted from the same numbers -- this is
             #: a tick FORMAT and nothing about the data is rescaled.
             + scale_y_continuous(
                 labels=lambda v: ["%g%%" % round(x * 100, 6) for x in v])
             #: NO title, subtitle or caption. They are the legend's, and the
             #: rule forbids the figure repeating them.
             #: **THE Y TITLE NAMES THE PROMPT, AND IT HAS TO FIT.** At 9 pt
             #: the usable panel height is ~2.7 in = ~194 pt, about 43
             #: characters; `Probability of word following "<prompt>"` is
             #: longer than that for every prompt in the battery. Wrapped onto
             #: two lines rather than shrunk, because ONE SIZE THROUGHOUT is a
             #: rule of the journal and a second, smaller face to fit a long
             #: string is exactly what that rule forbids.
             + labs(x="", y=ytitle)
             #: **THE AXIS STOPS AT ZERO.** A probability cannot be negative,
             #: so an axis that runs below it is the figure asserting a value
             #: the quantity cannot take. `coord_cartesian` and not a scale
             #: limit: a scale limit DROPS rows outside it, which would
             #: silently delete a bootstrap low that came back slightly
             #: negative rather than showing it clipped.
             + (coord_cartesian(ylim=(0.0, ceiling * 1.03))
                if yfloor == "zero" else _noop())
             + theme_minimal()
             #: **HEIGHT IS THE ONLY DIAL THAT BUYS LABEL ROOM.** Width is
             #: fixed by the text block; type size is fixed by the rules. So
             #: when N words will not sit at their own heights, a taller panel
             #: is the honest fix and a tighter gap is not.
             + theme(figure_size=(PUB_SIZE[0], float(height or PUB_SIZE[1])),
                     #: ONE family, ONE size, everywhere -- set on `text`, which
                     #: every other text element inherits from.
                     text=element_text(family=fnt, size=PUB_FONT_PT),
                     axis_title=element_text(family=fnt, size=PUB_FONT_PT),
                     axis_text=element_text(family=fnt, size=PUB_FONT_PT),
                     #: the completely enclosed box the rules ask for
                     panel_border=element_rect(color="black",
                                               size=PUB_RULE_PT, fill=None),
                     axis_ticks=element_line(color="black", size=PUB_RULE_PT),
                     panel_grid_minor=element_blank(),
                     panel_grid_major_x=element_blank(),
                     panel_grid_major_y=element_line(color="#e9ecef",
                                                     size=PUB_RULE_PT)))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    #: PNG and PDF together -- see malignment.figure.save
    from malignment.figure import save as _save
    return _save(p, out_path)[0]


#: ── THE PRODUCER DECLARES ITSELF, AND THE APP READS THE DECLARATION.
#:
#: The alternative is a registry of plot types inside `serve.py`, which is a
#: second definition of what this producer accepts and drifts from it the first
#: time a parameter changes. The experiment declares; the app reads. Same shape
#: as the register itself.
#:
#: **`prompt` IS TYPE `prompt`, NOT `text`, AND THAT IS A SECURITY BOUNDARY
#: RATHER THAN A UI HINT.** `serve.py`'s rule is that nothing a client sends
#: reaches SQL, and a prompt goes straight into a ClickHouse query. The server
#: validates it by MEMBERSHIP in the set of prompts the store actually holds,
#: which is the same move as `/slot`'s pair dropdown -- and it is better anyway,
#: because a prompt with no cells can only ever produce an empty figure.
PLOT = {
    "id": "prompt_slopes",
    #: **DECLARED SO DISCOVERY CAN REFUSE BEFORE THE BUTTON IS PRESSED.** The
    #: plotnine import lives inside `draw()` -- deliberately, to keep the CLI's
    #: startup cheap and to set the Agg backend first -- and the side effect was
    #: that this module imports fine without it. So `/plots` listed a figure the
    #: environment could not draw and the failure arrived on click, as
    #: `ModuleNotFoundError: matplotlib`. A lazy import moves a failure later,
    #: which is usually the point and here made an unavailable plot look
    #: available. Install with `pip install -e '.[plots]'`.
    "requires": ["plotnine"],
    "name": "prompt slopes",
    "blurb": "One prompt, every lineage: what the models put at the blank, "
             "before and after. Levels, not derived statistics.",
    "params": [
        {"name": "prompt", "type": "prompt", "required": True,
         "label": "prompt",
         "help": "must be a prompt the store holds; type to search"},
        {"name": "units", "type": "choice", "default": "endpoints",
         "choices": ["endpoints", "chains"], "label": "units",
         "help": "endpoints = 50 declared pairs (2 rungs); "
                 "chains = 18 lineages at base, sft, pref (3 rungs)"},
        {"name": "top", "type": "int", "default": 6, "min": 2, "max": 30,
         "label": "top N words",
         "help": "declared rule: top N by mass, blind to movement. 5-6 is the "
                 "publication budget -- past that the right-hand key cannot be "
                 "placed at the words' own heights and stops being readable "
                 "as position"},
        {"name": "select", "type": "choice", "default": "pooled",
         "choices": ["pooled", "base", "union"], "label": "word selection",
         "help": "pooled = top N by mass summed across both rungs, which is the "
                 "publication default: a stable N however much the arms agree. "
                 "base = top N at the base rung only, so a word that ARRIVES is "
                 "invisible. union = top N at each rung unioned -- measured on "
                 "`She was so angry she wanted to` it returns 3 words at N=3, "
                 "because both arms lead with kill, scream, hit, and the flat "
                 "words that make a mover legible AS a mover drop out. All "
                 "three are blind to movement"},
        {"name": "intervals", "type": "choice", "default": "named",
         "choices": ["named", "all", "none"], "label": "error bars on",
         "help": "named = the faller and riser only. Intervals on words no "
                 "claim rests on are ink that crowds the two a reader must "
                 "read; the gray words keep their points, so flatness stays "
                 "visible"},
        {"name": "repel", "type": "choice", "default": "auto",
         "choices": ["auto", "on", "off"], "label": "repel labels",
         "help": "every pixel a label moves off its line end is false position, "
                 "and readers take label height for value. auto repels only on "
                 "an actual collision"},
        {"name": "graylabel", "type": "choice", "default": "cluster",
         "choices": ["cluster", "each", "none"], "label": "gray labels",
         "help": "cluster = one label for the flat bundle, which removes the "
                 "repelling that otherwise puts a gray label at a height that "
                 "is not its value; the caption says which line is which. "
                 "each = label every word (repelling may displace them)"},
        {"name": "height", "type": "int", "default": 0, "min": 0, "max": 9,
         "label": "panel height (in)",
         "help": "0 = the default 3.15 in. The only dial that buys label room: "
                 "width is set by the journal text block and type size by its "
                 "rules, so a taller panel is the honest fix when N words will "
                 "not sit at their own heights"},
        {"name": "yfloor", "type": "choice", "default": "zero",
         "choices": ["zero", "auto"], "label": "axis floor",
         "help": "zero stops the axis at 0: a probability cannot be negative"},
        {"name": "stat", "type": "choice", "default": "median",
         "choices": ["median", "mean"], "label": "central tendency",
         "help": "median by default: probabilities are heavy-tailed across "
                 "families and a mean can be one family's obsession"},
        {"name": "pub", "type": "choice", "default": "no",
         "choices": ["no", "yes"], "label": "publication render",
         "help": "strips the title, method note and footer (they are typeset "
                 "as the legend), encloses the panel, one sans-serif at one "
                 "size, dashes the riser so it survives grayscale, and draws "
                 "at FINAL size 4.5 x 3.15 in"},
        {"name": "plus_top", "type": "int", "default": 0, "min": 0, "max": 20,
         "label": "+ top N by mass",
         "help": "with `words`: keep the named ones AND add this many by mass. "
                 "A named pair is often the top of its own distribution, so a "
                 "curated figure can come back with two lines and no context -- "
                 "and the flat words are what make a mover legible AS a mover"},
        {"name": "words", "type": "text", "default": "", "label": "words",
         "help": "optional comma-separated list; LABELLED as curated, because "
                 "intervals on words picked because they moved are conditioned "
                 "on that selection"},
    ],
}


def render(prompt, units="endpoints", top=6, stat="median", words="",
           pub=False, select="pooled", intervals="named", repel="auto",
           yfloor="zero", height=None, graylabel="cluster", plus_top=0):
    """Run the whole thing and return `(path, info)`. The app's entry point.

    Shares every line of its arithmetic with the CLI below -- there is no second
    implementation of the figure, which is the divergence this repo keeps paying
    for. The CLI is a thin argument parser over this.
    """
    wl = [w.strip() for w in words.split(",") if w.strip()] if words else None
    seq, unit_label = units_for(units, None)
    rows, meta = movement.contrast(prompt, seq, top=int(top), words=wl,
                                   plus_top=int(plus_top or 0),
                                   select_union=(str(select) == "union"),
                                   select_pooled=(str(select) == "pooled"))
    lev, pairs = build(rows, meta, stat)
    rung_labels = (["Base models", "Aligned models"] if meta["n_rungs"] == 2 else
                   ["base", "sft", "pref"] if meta["n_rungs"] == 3 else
                   ["rung %d" % i for i in range(meta["n_rungs"])])
    #: `_pub` IN THE NAME. The two renders differ in what they are allowed to
    #: carry, so one must never overwrite the other -- a figure sent to a
    #: journal with a title burnt into it is the failure this mode exists for.
    out = os.path.join(FIGURES, "slope_%s_%s_%s%s%s.png"
                       % (slug(prompt), units, stat,
                          "_curated" if wl else "_top%d%s" % (
                              int(top), {"union": "u", "pooled": "p"}.get(
                                  str(select), "")),
                          "_pub" if pub else ""))
    draw(lev, pairs, meta, stat, out, rung_labels, pub=bool(pub),
         intervals=str(intervals), repel=str(repel), yfloor=str(yfloor),
         height=float(height) if height else None, graylabel=str(graylabel))
    return out, {
        "unit_label": unit_label,
        "n_units": meta["n_units"], "n_units_requested": meta["n_units_requested"],
        "n_rungs": meta["n_rungs"], "selection": meta["selection"],
        "words": meta["words"], "below_theta": meta["below_theta"],
        "n_cells": meta["n_cells"],
        "dropped": [d["unit"] for d in meta["missing_units"]],
        "faller": {"word": pairs.iloc[0]["word"], "d": float(pairs.iloc[0]["d"])},
        "riser": {"word": pairs.iloc[-1]["word"], "d": float(pairs.iloc[-1]["d"])},
    }


def slug(s, n=48):
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", s.lower())).strip("_")[:n]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("prompt")
    ap.add_argument("--plus-top", type=int, default=0,
                    help="with --words: keep the named words AND add this many "
                         "by mass, deduped. The named half is the caller's, the "
                         "rest is declared and blind to movement, and the "
                         "subtitle says `top N by mass + M named` so both "
                         "warrants travel. 0 (default) leaves --words curated.")
    ap.add_argument("--words", default=None,
                    help="comma-separated; LABELLED as a curated list")
    ap.add_argument("--intervals", default="all",
                    choices=["all", "named", "none"],
                    help="which words carry error bars. `named` is the faller "
                         "and riser only: intervals on words no claim rests on "
                         "are ink that crowds the two a reader must read.")
    ap.add_argument("--repel", default="auto", choices=["auto", "on", "off"],
                    help="push colliding word labels apart. Every pixel of "
                         "repelling is false position, so `auto` does it only "
                         "when two labels would actually overlap.")
    ap.add_argument("--graylabel", default="each",
                    choices=["each", "cluster", "none"],
                    help="`cluster` labels the gray bundle ONCE beside its end "
                         "instead of labelling each word, which removes the "
                         "repelling that otherwise puts a gray label at a "
                         "height that is not its value. Which line is which "
                         "then belongs in the caption.")
    ap.add_argument("--height", type=float, default=None,
                    help="panel height in inches (publication render; default "
                         "%.2f). The only dial that buys room for labels: width "
                         "is set by the text block and type size by the rules."
                         % PUB_SIZE[1])
    ap.add_argument("--yfloor", default="auto", choices=["auto", "zero"],
                    help="`zero` stops the axis at 0 -- a probability cannot be "
                         "negative and an axis that runs below it asserts a "
                         "value the quantity cannot take.")
    ap.add_argument("--select", default="base",
                    choices=["base", "union", "pooled"],
                    help="which rung's mass picks the words. `base` is top N at "
                         "position 0. `union` is top N at EVERY rung, unioned -- "
                         "still blind to movement, but it can show a word that "
                         "ARRIVES rather than only words the base already had. "
                         "Returns between N and N x rungs words.")
    ap.add_argument("--top", type=int, default=6,
                    help="declared rule: top-N by mass at the base rung")
    ap.add_argument("--stat", default="median", choices=["median", "mean"])
    ap.add_argument("--units", default="endpoints",
                    choices=["endpoints", "chains"])
    ap.add_argument("--pair", action="append", default=None,
                    help="explicit unit, `base>aligned` or `base>sft>dpo`; repeatable")
    ap.add_argument("--pub", action="store_true",
                    help="PUBLICATION RENDER: no title, method note or footer "
                         "(they are the legend's, and a figure may not repeat "
                         "its legend); enclosed axis box; one sans-serif at one "
                         "size; named lines differ in DASH as well as hue so "
                         "they survive a grayscale plate; drawn at FINAL SIZE "
                         "4.5 x 3.15 in at 300 dpi, so the type size set here "
                         "is the type size on the page.")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    units, unit_label = units_for(args.units, args.pair)
    words = [w.strip() for w in args.words.split(",")] if args.words else None
    rows, meta = movement.contrast(args.prompt, units, top=args.top,
                                   words=words, plus_top=args.plus_top,
                                   select_union=(args.select == "union"),
                                   select_pooled=(args.select == "pooled"))
    print("prompt    %r" % meta["prompt"])
    print("units     %d of %d (%s), %d rungs"
          % (meta["n_units"], meta["n_units_requested"], unit_label, meta["n_rungs"]))
    print("selection %s" % meta["selection"])
    print("words     %s" % ", ".join(meta["words"]))
    print("cells     %d, %d at or below theta" % (meta["n_cells"], meta["below_theta"]))
    if meta["missing_units"]:
        print("dropped   %d unit(s): %s"
              % (len(meta["missing_units"]),
                 ", ".join(d["unit"] for d in meta["missing_units"][:6])))

    lev, pairs = build(rows, meta, args.stat)
    #: **THE PANEL AND THE ANNOTATION COME FROM ONE FRAME.** An assert rather
    #: than a convention, because the failure is a caption naming a word the
    #: colours do not mark.
    assert set(pairs["word"]) == set(lev["word"]), \
        "the paired frame and the level frame disagree about which words exist"
    assert len(lev) == len(meta["words"]) * meta["n_rungs"], \
        "expected %d level rows, got %d" % (len(meta["words"]) * meta["n_rungs"], len(lev))

    rung_labels = (["Base models", "Aligned models"] if meta["n_rungs"] == 2 else
                   ["base", "sft", "pref"] if meta["n_rungs"] == 3 else
                   ["rung %d" % i for i in range(meta["n_rungs"])])
    #: DETERMINISTIC FILENAME FROM THE PARAMETERS, so asking the same question
    #: twice OVERWRITES rather than accumulating a folder of near-duplicates
    #: nobody can tell apart. The parameters that change the picture are in the
    #: name; the ones that do not are not.
    name = args.out or os.path.join(
        FIGURES, "slope_%s_%s_%s%s.png"
        % (slug(args.prompt), args.units if not args.pair else "custom",
           args.stat, "_curated" if words else "_top%d%s" % (
               args.top, {"union": "u", "pooled": "p"}.get(args.select, "")))
        + ("" if not args.pub else ""))
    if args.pub and not args.out:
        name = name[:-4] + "_pub.png"
    out = draw(lev, pairs, meta, args.stat, name, rung_labels, pub=args.pub,
               intervals=args.intervals, repel=args.repel, yfloor=args.yfloor,
               height=args.height, graylabel=args.graylabel)
    print("\nwrote %s" % out)
    print("largest faller %-10s %+.4f   largest riser %-10s %+.4f"
          % (pairs.iloc[0]["word"], pairs.iloc[0]["d"],
             pairs.iloc[-1]["word"], pairs.iloc[-1]["d"]))


if __name__ == "__main__":
    main()
