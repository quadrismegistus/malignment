#!/usr/bin/env python
"""Figure 2 with a third tick: the aligned model in its chat template, sentence prefilled.

    python -u prefill_tick.py

RH, 2026-09-24: "add a third x-axis tick, extending same points and CIs, for
aligned-prefilled and/or aligned-chat, whichever we have". Writes NEW files only
and refuses to overwrite anything (RH: "Don't overwrite any files"); Figure 2's
own producer (`plot.py`) and its outputs are not touched.

## WHAT FIGURE 2 IS

`paper/figures/fig2-kill-scream-v2.{png,pdf}` is byte-identical to this folder's
`figures/slope_she_was_so_angry_she_wanted_to_endpoints_median_top5p_pub.*`
(16 Sep 10:27): `plot.py "She was so angry she wanted to" --top 5 --select
pooled --pub`, endpoints, median. Its arithmetic is `plot.build` over
`movement.contrast`, and this file IMPORTS both rather than re-deriving them.

## WHICH CHAT CONDITION

Only one exists at a next-word slot: `frame='prefill'` in `twp_words_v4` -- the
model's chat template, a user turn ("Hi."), and the sentence prefilled at the
start of the assistant's turn, so the next token continues the sentence. A plain
chat answer would start the assistant's reply, not continue the sentence, and is
not stored as a word-slot condition.

`system_mode` splits the prefilled cells into `empty` and `default` (the model's
own default system prompt), which [6557] rules NON-POOLABLE
(`instrument_calibrations/frame_prefill`). This file uses `empty`, the
calibration's own choice. For this prompt that is 31 of the 50 aligned models.

## TWO VARIANTS, BECAUSE THE SUPPORT DIFFERS

- MATCHED: all three ticks on the lineages that have all three cells. The first
  two ticks then differ slightly from Figure 2's, which stand on 50.
- EXTENDED: Figure 2's two ticks exactly as printed (50 lineages, asserted
  identical to plot.build's output), and the third on its own support, stated.

The raw-frame best view's de-duplication (argMax over (topup, prompt_cache,
mtime)) is mirrored for the prefilled cells, which have no view of their own.
"""
import importlib.util
import os
import re
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, REPO)
from malignment import ch, movement  # noqa: E402

_spec = importlib.util.spec_from_file_location("prompt_slopes_plot", os.path.join(HERE, "plot.py"))
PS = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(PS)

PROMPT = "She was so angry she wanted to"
MODE = "empty"
#: Figure 2's caption, to the printed digit: the paired within-lineage change
#: base -> aligned, median [bootstrap 95%], in points, and the lineage counts
BOOKED = {"kill": (-5.5, -7.1, -2.8, 44), "scream": (+5.0, +1.5, +8.6, 42)}
RUNGS = ["Base models", "Aligned models", "Aligned, chat\n(prefilled)"]
GRAYLABEL = "cluster"


def prefill(models, words):
    """{model: {word: p}} for aligned models with an `empty`-mode prefilled cell."""
    lit = ch._lit                       # the store module's own quoter, as movement uses it
    inl = ",".join(lit(m) for m in models)
    got = ch.query(
        "SELECT model, word, argMax(p, (topup, prompt_cache, mtime)) AS p "
        "FROM {db}.twp_words_v4 WHERE frame='prefill' AND system_mode=%s "
        "AND prompt=%s AND model IN (%s) GROUP BY model, word"
        % (lit(MODE), lit(PROMPT), inl))
    by = {}
    for r in got:
        by.setdefault(r["model"], {})[r["word"]] = float(r["p"])
    #: a model with a cell but without one of the words gets 0, as contrast() does
    return {m: {w: d.get(w, 0.0) for w in words} for m, d in by.items()}


#: THE RIGHT EDGE. plot.draw's pub render ends the x axis at last_pos + 0.34, sized
#: for two ticks; at three the cluster label "throw, cry, hit" (~0.95 in at 9 pt)
#: ran past the panel and was clipped -- a defect only the image showed. plot.py
#: is not to be edited (RH: no overwriting), so plotnine's scale_x_continuous is
#: wrapped for the duration of the call and ONLY that limit is replaced. Solved
#: for the label: start 2.04, 0.95 in at (U + 0.08) / 4.3 units per inch -> U >= 2.71.
RIGHT_EDGE = 2.75


class wider_right:
    def __init__(self, edge):
        self.edge = edge

    def __enter__(self):
        import plotnine
        self.orig = plotnine.scale_x_continuous
        orig, edge = self.orig, self.edge

        def patched(*a, **k):
            lim = k.get("limits")
            if lim is not None and abs(lim[0] + 0.08) < 1e-9:
                k["limits"] = (lim[0], edge)
            return orig(*a, **k)
        plotnine.scale_x_continuous = patched

    def __exit__(self, *exc):
        import plotnine
        plotnine.scale_x_continuous = self.orig


def pairs_of(lev_rows, a, b, stat="median"):
    """Paired within-lineage change from position a to b, per word, with plot.boot_ci."""
    df = pd.DataFrame(lev_rows)
    x = df[df.position == a].set_index(["unit", "word"])["p"]
    y = df[df.position == b].set_index(["unit", "word"])["p"]
    d = (y - x).dropna().reset_index(name="d")
    rng = np.random.default_rng(PS.SEED)
    out = {}
    for w, g in d.groupby("word", sort=False):
        lo, hi = PS.boot_ci(g["d"].tolist(), stat, rng=rng)
        out[w] = dict(d=float(np.median(g["d"])), lo=lo, hi=hi, up=int((g["d"] > 0).sum()),
                      down=int((g["d"] < 0).sum()), n=len(g))
    return out


def embedded_face(pdf, want):
    """The face the PDF actually embeds, asserted against the one asked for.

    The caption states the face, and at 20423046 it stated one the file did not
    carry. Read it back from /BaseFont so the sentence cannot outrun the file.
    """
    names = set(re.findall(rb"/BaseFont\s*/(?:[A-Z]{6}\+)?([A-Za-z-]+)", open(pdf, "rb").read()))
    names = sorted(n.decode() for n in names)
    assert names and all(n.lower().startswith(want) for n in names), \
        "asked for %s, PDF embeds %s" % (want, names)
    return ", ".join(names)


def out_path(tag):
    p = os.path.join(PS.FIGURES, "slope_%s_endpoints_median_top5p_prefill_%s_pub.png" % (PS.slug(PROMPT), tag))
    for ext in (".png", ".pdf", ".caption.txt"):
        q = p[:-4] + ext
        #: RH: "Don't overwrite any files"
        assert not os.path.exists(q), "refusing to overwrite %s" % q
    return p


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("variants", nargs="*", default=["extended", "matched"],
                    help="extended and/or matched")
    ap.add_argument("--graylabel", default="cluster", choices=["cluster", "each"],
                    help="cluster (Figure 2's): one label for the flat words; each: one per word")
    ap.add_argument("--suffix", default="", help="appended to the filename tag, e.g. _v2")
    ap.add_argument("--face", default="helvetica", choices=["helvetica", "arial"],
                    help="helvetica: plot.py's own _pub_font, as Figure 2 and 20423046 were set; "
                         "arial: the house face, malignment.figure.pub_font (since 21 Sep)")
    args = ap.parse_args()
    global GRAYLABEL
    GRAYLABEL = args.graylabel
    if args.face == "arial":
        #: plot.py resolves its OWN font, Helvetica first, so this plate shipped in
        #: Helvetica at 20423046 while its caption said Arial (paper seat, pdffonts,
        #: 2026-09-24). Swap the resolver on the imported module; plot.py is untouched.
        from malignment.figure import pub_font
        PS._pub_font = pub_font
    seq, _ = PS.units_for("endpoints")
    rows, meta = movement.contrast(PROMPT, seq, top=5, select_pooled=True)
    words = list(meta["words"])
    assert sorted(words) == sorted(["scream", "kill", "hit", "cry", "throw"]), words

    #: FIGURE 2 FIRST: its own build(), and its caption's numbers, reproduced
    lev2, pairs2 = PS.build(rows, meta, "median")
    #: THE MEDIAN IS EXACT; A BOOTSTRAP BOUND IS NOT. Figure 2's caption quotes
    #: kill's interval as [-7.1, -2.8], which is the footer of the TOP-3 render
    #: (-0.0709). The top-5 run that drew Figure 2 consumes the bootstrap stream
    #: over five words and gets -7.0 (-0.07006) on the same, unchanged data (no
    #: store row newer than 12 Sep). So: medians to the digit, bounds within the
    #: Monte Carlo spread, 0.15 point.
    for w, (d, lo, hi, n) in BOOKED.items():
        r = pairs2[pairs2.word == w].iloc[0]
        assert round(100 * r.d, 1) == d, "Figure 2 %s median: caption %+.1f, derived %+.2f" % (w, d, 100 * r.d)
        assert abs(100 * r.lo - lo) <= 0.15 and abs(100 * r.hi - hi) <= 0.15, \
            "Figure 2 %s interval: caption [%+.1f, %+.1f], derived [%+.2f, %+.2f]" % (w, lo, hi, 100 * r.lo, 100 * r.hi)
    p2 = pairs_of(rows, 0, 1)
    assert p2["kill"]["down"] == 44 and p2["scream"]["up"] == 42, (p2["kill"], p2["scream"])
    print("   Figure 2 reproduced: words %s, kill %+.1f, scream %+.1f" % (
        words, 100 * p2["kill"]["d"], 100 * p2["scream"]["d"]))

    unit_aligned = {u: rungs[1] for u, rungs in seq}
    pf = prefill(sorted(set(unit_aligned.values())), words)
    has = [u for u in dict(seq) if u in {r["unit"] for r in rows} and unit_aligned[u] in pf]
    print("   prefilled (%s) cells: %d of %d lineages" % (MODE, len(has), meta["n_units"]))
    extra = [dict(unit=u, word=w, position=2, p=pf[unit_aligned[u]][w]) for u in has for w in words]
    below = sum(1 for r in extra if r["p"] <= 0.001)

    variants = {
        "extended": (rows + extra, meta["n_units"]),
        "matched": ([r for r in rows if r["unit"] in set(has)] + extra, len(has)),
    }
    for tag, (rr, n0) in [(k, v) for k, v in variants.items() if k in args.variants]:
        m = dict(meta, n_rungs=3, n_units=n0, n_cells=len(rr),
                 below_theta=meta["below_theta"] + below)
        lev, pairs = PS.build(rr, m, "median")
        if tag == "extended":
            #: the first two ticks must be Figure 2's own points and intervals
            a = lev[lev.position < 2].sort_values(["word", "position"]).reset_index(drop=True)
            b = lev2.sort_values(["word", "position"]).reset_index(drop=True)
            assert np.allclose(a[["central", "lo", "hi"]].values, b[["central", "lo", "hi"]].values), \
                "extended variant's first two ticks differ from Figure 2"
        path = out_path(tag + args.suffix)
        #: graylabel="cluster" is Figure 2's own: the flat words share one label,
        #: "hit, throw, cry", at the bundle's median (RH, 2026-09-24)
        with wider_right(RIGHT_EDGE):
            PS.draw(lev, pairs, m, "median", path, RUNGS, pub=True, intervals="named",
                    yfloor="zero", graylabel=GRAYLABEL)
        face = embedded_face(path[:-4] + ".pdf", args.face)
        steps = {k: pairs_of(rr, a_, b_) for k, (a_, b_) in
                 {"base -> aligned": (0, 1), "aligned -> prefilled": (1, 2), "base -> prefilled": (0, 2)}.items()}
        L = ["FIGURE 2 WITH A THIRD TICK (%s). \"%s\" at the blank." % (tag.upper(), PROMPT), "",
             "Ticks: base model (raw); aligned model (raw); aligned model in its chat template with the sentence",
             "prefilled at the start of the assistant's turn after a user turn \"Hi.\" (frame='prefill',",
             "system_mode='%s'; the 'default' mode is ruled non-poolable, [6557])." % MODE,
             "Points: median over lineages of each word's probability; error bars: bootstrap 95% intervals on",
             "that median, lineage as unit, for the two named words (plot.build, as Figure 2).", "",
             ("SUPPORT: ticks 1-2 are Figure 2's %d lineages exactly (asserted); tick 3 is the %d of them whose "
              "aligned model has a prefilled cell in this mode." % (meta["n_units"], len(has))) if tag == "extended"
             else ("SUPPORT: all three ticks on the same %d lineages (those with a prefilled cell in this mode); "
                   "Figure 2's first two ticks stand on %d, so they differ slightly here." % (len(has), meta["n_units"])),
             "Words: Figure 2's five (top 5 by pooled mass over base and aligned, raw). %d of the %d prefilled "
             "cells are at or below 0.001 and drawn at the floor." % (below, len(extra)), "",
             "Median within-lineage change, points [bootstrap 95%], lineages up/down:"]
        for k, st in steps.items():
            for w in ("kill", "scream"):
                s = st[w]
                L.append("  %-22s %-7s %+5.1f [%+5.1f, %+5.1f]  %2d up / %2d down of %d" % (
                    k, w, 100 * s["d"], 100 * s["lo"], 100 * s["hi"], s["up"], s["down"], s["n"]))
        L += ["", "Levels, median probability per tick (lo, hi):"]
        for w in words:
            L.append("  %-7s " % w + "   ".join("%.3f (%.3f, %.3f)" % tuple(
                lev[(lev.word == w) & (lev.position == i)][["central", "lo", "hi"]].iloc[0]) for i in range(3)))
        L += ["", "Producer: experiments/exploratory/prompt_slopes/prefill_tick.py (imports plot.build/draw and "
              "movement.contrast). Type: %s, read back from the PDF's embedded fonts%s."
              % (face, "" if face.startswith("Arial") else "; Figure 2's face, not the house Arial of Figures 3-6")]
        open(path[:-4] + ".caption.txt", "w").write("\n".join(L) + "\n")
        print("   ->", os.path.relpath(path, HERE), "(+ .pdf, .caption.txt)")


if __name__ == "__main__":
    main()
