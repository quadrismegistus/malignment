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


def draw(lev, pairs, meta, stat, out_path, rung_labels):
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
                          geom_text, labs, scale_x_continuous, theme_minimal,
                          theme, element_text, scale_color_manual)

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
    gap = span * 0.028
    ends = ends.sort_values("central", ascending=False).reset_index(drop=True)
    ly = ends["central"].tolist()
    for i in range(1, len(ly)):
        if ly[i - 1] - ly[i] < gap:
            ly[i] = ly[i - 1] - gap
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

    p = (ggplot(lev, aes("position", "central"))
         + geom_segment(aes(x="x", y="y", xend="xend", yend="yend",
                            color="role"), data=seg, size=0.7, alpha=0.9)
         + geom_errorbar(aes(ymin="lo", ymax="hi", color="role"), width=0.04,
                         size=0.4, alpha=0.7)
         + geom_point(aes(color="role"), size=2.0)
         + geom_text(aes(x="position", y="label_y", label="word", color="role"),
                     data=ends, ha="left", nudge_x=0.06, size=8)
         + scale_color_manual({"faller": "#c92a2a", "riser": "#1c7ed6",
                               "other": "#868e96"}, guide=None)
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
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    p.save(out_path, dpi=300, verbose=False)
    return out_path


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
        {"name": "top", "type": "int", "default": 12, "min": 3, "max": 30,
         "label": "top N words",
         "help": "declared rule: top N by mass at the base rung, blind to movement"},
        {"name": "stat", "type": "choice", "default": "median",
         "choices": ["median", "mean"], "label": "central tendency",
         "help": "median by default: probabilities are heavy-tailed across "
                 "families and a mean can be one family's obsession"},
        {"name": "words", "type": "text", "default": "", "label": "words",
         "help": "optional comma-separated list; LABELLED as curated, because "
                 "intervals on words picked because they moved are conditioned "
                 "on that selection"},
    ],
}


def render(prompt, units="endpoints", top=12, stat="median", words=""):
    """Run the whole thing and return `(path, info)`. The app's entry point.

    Shares every line of its arithmetic with the CLI below -- there is no second
    implementation of the figure, which is the divergence this repo keeps paying
    for. The CLI is a thin argument parser over this.
    """
    wl = [w.strip() for w in words.split(",") if w.strip()] if words else None
    seq, unit_label = units_for(units, None)
    rows, meta = movement.contrast(prompt, seq, top=int(top), words=wl)
    lev, pairs = build(rows, meta, stat)
    rung_labels = (["base", "aligned"] if meta["n_rungs"] == 2 else
                   ["base", "sft", "pref"] if meta["n_rungs"] == 3 else
                   ["rung %d" % i for i in range(meta["n_rungs"])])
    out = os.path.join(FIGURES, "slope_%s_%s_%s%s.png"
                       % (slug(prompt), units, stat,
                          "_curated" if wl else "_top%d" % int(top)))
    draw(lev, pairs, meta, stat, out, rung_labels)
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
    ap.add_argument("--words", default=None,
                    help="comma-separated; LABELLED as a curated list")
    ap.add_argument("--top", type=int, default=12,
                    help="declared rule: top-N by mass at the base rung")
    ap.add_argument("--stat", default="median", choices=["median", "mean"])
    ap.add_argument("--units", default="endpoints",
                    choices=["endpoints", "chains"])
    ap.add_argument("--pair", action="append", default=None,
                    help="explicit unit, `base>aligned` or `base>sft>dpo`; repeatable")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    units, unit_label = units_for(args.units, args.pair)
    words = [w.strip() for w in args.words.split(",")] if args.words else None
    rows, meta = movement.contrast(args.prompt, units, top=args.top, words=words)
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

    rung_labels = (["base", "aligned"] if meta["n_rungs"] == 2 else
                   ["base", "sft", "pref"] if meta["n_rungs"] == 3 else
                   ["rung %d" % i for i in range(meta["n_rungs"])])
    #: DETERMINISTIC FILENAME FROM THE PARAMETERS, so asking the same question
    #: twice OVERWRITES rather than accumulating a folder of near-duplicates
    #: nobody can tell apart. The parameters that change the picture are in the
    #: name; the ones that do not are not.
    name = args.out or os.path.join(
        FIGURES, "slope_%s_%s_%s%s.png"
        % (slug(args.prompt), args.units if not args.pair else "custom",
           args.stat, "_curated" if words else "_top%d" % args.top))
    out = draw(lev, pairs, meta, args.stat, name, rung_labels)
    print("\nwrote %s" % out)
    print("largest faller %-10s %+.4f   largest riser %-10s %+.4f"
          % (pairs.iloc[0]["word"], pairs.iloc[0]["d"],
             pairs.iloc[-1]["word"], pairs.iloc[-1]["d"]))


if __name__ == "__main__":
    main()
