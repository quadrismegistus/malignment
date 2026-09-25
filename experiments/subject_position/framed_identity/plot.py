#!/usr/bin/env python
"""Critical Inquiry plate for the coda: the subject in three conditions.

    python plot.py              # all figures
    python plot.py frames       # ci_subject_frames
    python plot.py --list

Writes `figures/<name>.{png,pdf,tif}` and `figures/<name>.caption.txt`, and
refuses to overwrite. House rules as Figure 6 (institution_vs_individual/plot.py):
4.8 in wide, Arial, no type under 7 pt, grayscale inside CI's halftone band, no
title or caption on the plate, every number on it in the caption file.

## THE PLATE COMPUTES NOTHING NEW

It re-derives three rows of `analyse.py`'s CROSS-FRAME table ("Who are you?",
one instrument) and refuses to draw unless they reproduce `results/analysis.txt`
to its printed precision. `analyse.py` builds that table inline in `main()`, so
the loaders are imported (`load`, `substitute_recovered`, `median`, the
reasoning gate) and the three stratum filters and the >= 5 rows-per-model rule
are restated here; the booked asserts are what fail if the two ever disagree.

## WHICH CHAT ROW, AND WHY NOT 98.8

The chat condition is `system=""` minus SmolLM3-3B (18 models), whose template
hard-codes its persona so it has no empty system slot. The 98.8% this README
carried until 2026-09-14 pooled the `system=DEFAULT` draws, and 5 of the 19
shipped default blocks state the answer. The DEFAULT row is re-derived below
ONLY to assert that it is not the one drawn.

## THE FIRST ROW IS NOT "USES I"

The column `analyse.py` prints as `any I` is the coder's `self_predicates`: the
SPEAKER identifies itself in the first person ('I am X', 'My name is X'), and an
'I' inside quoted speech, a list or a template slot does not count. The row is
labelled for what the coder read.
"""
import argparse
import collections
import os
import re
import sys
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
for p in (HERE, REPO):
    if p not in sys.path:
        sys.path.insert(0, p)

import analyse as A                           # noqa: E402  load, substitute_recovered, median
from malignment import figure as F            # noqa: E402

FIG = os.path.join(HERE, "figures")
SMOLLM3 = "HuggingFaceTB/SmolLM3-3B"
REASONING_SWAPPED = ["HuggingFaceTB/SmolLM3-3B", "Qwen/Qwen3-8B", "openbmb/MiniCPM5-1B"]

#: the analysis.txt row label for each drawn condition, and the plate's name for it
COND = [("base, untemplated", "Base models"),
        ("aligned, untemplated", "Aligned, no chat template"),
        ("   ... minus SmolLM3 (no empty slot exists)", "Aligned, in chat")]
#: measure -> (plate row label, per-answer predicate)
MEASURES = [("Says “I am …”", lambda x: x["self_predicates"]),
            ("Says it is an AI", lambda x: x["identity_kind"] == "ai_system"),
            ("Claims to be a person", lambda x: x["identity_kind"] == "human_person")]


def save(p, name, caption):
    """PNG + PDF (house `save`), a 300 dpi TIF from the PNG, and the caption file."""
    from PIL import Image
    os.makedirs(FIG, exist_ok=True)
    png, pdf = F.save(p, os.path.join(FIG, name + ".png"))
    tif = os.path.join(FIG, name + ".tif")
    Image.open(png).save(tif, dpi=(300, 300), compression="tiff_lzw")
    cap = os.path.join(FIG, name + ".caption.txt")
    open(cap, "w").write(caption.rstrip() + "\n")
    for f in (png, pdf, tif, cap):
        print("   %-40s %7.0f KB" % (os.path.relpath(f, HERE), os.path.getsize(f) / 1024))


def booked():
    """analysis.txt's cross-frame table -> {row label: (n models, any I, ai_system, human)}."""
    out = {}
    pat = re.compile(r"^  (.+?)\s+(\d+)\s+([\d.]+)%\s+([\d.]+)%\s+([\d.]+)%\s+([\d.]+)%$")
    for line in open(os.path.join(HERE, "results", "analysis.txt")):
        m = pat.match(line.rstrip("\n"))
        if m:
            out[m.group(1).rstrip()] = (int(m.group(2)), float(m.group(3)), float(m.group(4)), float(m.group(5)))
    return out


def strata():
    """The cross-frame strata as analyse.main() builds them. -> {label: rows}, swapped models"""
    import json
    f20 = [json.loads(l) for l in open(A.F20X_OUT)]
    rows = [r for r in A.load() if not r["truncated_think"]]       # the reasoning gate
    tmpl, swapped = A.substitute_recovered(rows)
    who_empty = [r for r in tmpl if r["qid"] == "who" and r.get("system") == "empty"]
    return {
        "base, untemplated": [r for r in f20 if r["qid"] == "who" and r["arm"] == "base"],
        "aligned, untemplated": [r for r in f20 if r["qid"] == "who" and r["arm"] == "superego"],
        "aligned, TEMPLATED, system=\"\"": who_empty,
        "   ... minus SmolLM3 (no empty slot exists)": [r for r in who_empty if r["model"] != SMOLLM3],
        "aligned, TEMPLATED, system=DEFAULT": [r for r in tmpl if r["qid"] == "who" and r.get("system") == "default"],
    }, swapped


def per_model(sub):
    """Models with >= 5 answers (analyse.py's rule) -> {model: [answers]}."""
    by = collections.defaultdict(list)
    for x in sub:
        by[x["model"]].append(x)
    return {m: g for m, g in by.items() if len(g) >= 5}


def medians(sub):
    keep = per_model(sub)
    return len(keep), [100 * A.median([sum(1 for x in g if fn(x)) / len(g) for g in keep.values()])
                       for _, fn in MEASURES]


def fig_frames():
    """The subject in three conditions: 'Who are you?', base -> aligned -> aligned in chat."""
    name = "ci_subject_frames"
    for ext in (".png", ".pdf", ".tif", ".caption.txt"):
        assert not os.path.exists(os.path.join(FIG, name + ext)), "refusing to overwrite %s%s" % (name, ext)

    S, swapped = strata()
    B = booked()
    #: THE BOOKED TABLE: every row of it, n models and all three columns, to the printed 0.1
    for lab, sub in S.items():
        n, vals = medians(sub)
        got = (n,) + tuple(round(v, 1) for v in vals)
        assert got == B[lab][:4], "analysis.txt %r: booked %s, derived %s" % (lab.strip(), B[lab][:4], got)
    #: categorical: the three reasoning models are the 1024-token substitutes, and
    #: SmolLM3 is present in the empty cell and absent from the drawn one
    assert sorted(swapped) == REASONING_SWAPPED, swapped
    assert SMOLLM3 in per_model(S["aligned, TEMPLATED, system=\"\""])
    assert SMOLLM3 not in per_model(S[COND[2][0]])
    #: the plate draws 96.2; the retracted 98.8 is BOTH system conditions pooled per
    #: model, re-derived here so the caption names what it was rather than a
    #: row that merely prints the same digits ("DEFAULT minus the 5" is also 98.8)
    assert B[COND[2][0]][2] == 96.2
    pooled = medians(S['aligned, TEMPLATED, system=""'] + S["aligned, TEMPLATED, system=DEFAULT"])
    assert (pooled[0], round(pooled[1][1], 1)) == (19, 98.8), pooled
    print("   analysis.txt reproduced: %d rows; drawn chat row is system=\"\" minus SmolLM3" % len(S))

    import matplotlib
    matplotlib.use("Agg")
    import pandas as pd
    from plotnine import (ggplot, aes, geom_segment, geom_point, geom_text, labs, scale_x_continuous,
                          scale_y_continuous, scale_shape_manual, theme, element_text, element_blank,
                          element_rect, guides, guide_legend)
    ns, val = {}, {}
    for lab, short in COND:
        n, vals = medians(S[lab])
        ns[short] = n
        for (mlab, _), v in zip(MEASURES, vals):
            val[(short, mlab)] = v
    #: the model count goes in the legend, so the unpaired design is on the plate
    LEG = {short: "%s (%d)" % (short, ns[short]) for _, short in COND}
    shorts = [short for _, short in COND]
    seg, pts = [], []
    for k, (mlab, _) in enumerate(MEASURES):
        y = len(MEASURES) - k
        v = [val[(s, mlab)] for s in shorts]
        seg += [dict(y=y, x0=v[0], x1=v[1]), dict(y=y, x0=v[1], x1=v[2])]
        for i, s in enumerate(shorts):
            #: value labels: the no-template mark's below, the other two above, so
            #: marks 5 points apart (95 and 100) never share a label line
            pts.append(dict(y=y, x=v[i], cond=LEG[s], lab="%.1f" % v[i],
                            ly=y + (-0.3 if i == 1 else 0.3)))
    d, q = pd.DataFrame(seg), pd.DataFrame(pts)
    q["cond"] = pd.Categorical(q.cond, categories=[LEG[s] for s in shorts])
    fnt = F.pub_font()
    W_IN, H_IN = F.PUB_SIZE[0], 3.1
    LABEL_PT = 7
    p = (ggplot()
         + geom_segment(aes(x="x0", xend="x1", y="y", yend="y"), data=d,
                        color=F.PUB_INK, size=0.85 * F.PUB_LINE_PT)
         + geom_point(aes(x="x", y="y", shape="cond"), data=q, color=F.PUB_INK, fill=F.PUB_INK,
                      size=1.9, stroke=0.7)
         + geom_text(aes(x="x", y="ly", label="lab"), data=q, size=LABEL_PT, family=fnt,
                     color=F.PUB_INK, va="center")
         + scale_shape_manual(dict(zip([LEG[s] for s in shorts], ["o", ">", "s"])),
                              name="", breaks=[LEG[s] for s in shorts])
         #: one column: in one row "Aligned, in chat (18)" ran off the canvas, cut silently
         + guides(shape=guide_legend(ncol=1))
         + scale_x_continuous(limits=(-7, 107), expand=(0, 0), breaks=[0, 25, 50, 75, 100],
                              labels=lambda v: ["%g%%" % x for x in v])
         + scale_y_continuous(limits=(0.45, len(MEASURES) + 0.55), expand=(0, 0),
                              breaks=list(range(len(MEASURES), 0, -1)), labels=[m for m, _ in MEASURES])
         + labs(x="Answers to “Who are you?”, median over models", y="")
         + F.pub_theme(height=H_IN, grid="none")
         + theme(figure_size=(W_IN, H_IN), legend_position="bottom", legend_title=element_blank(),
                 legend_text=element_text(family=fnt, size=F.PUB_FONT_PT),
                 legend_key=element_rect(fill="white", color="white"),
                 legend_margin=0, legend_box_spacing=0.02,
                 legend_box_just="center",
                 #: the row names are the plate's subject, black as Figure 6's words are
                 axis_text_y=element_text(family=fnt, size=F.PUB_FONT_PT, color=F.PUB_INK),
                 axis_ticks_major_y=element_blank()))

    lines = [
        "PLATE: THE SUBJECT IN THREE CONDITIONS. \"Who are you?\", one coder, three model sets.",
        "",
        "Per row, a line through three marks. Circle: base models, untemplated. Triangle: aligned models,",
        "untemplated. Square: aligned models in their own chat template. Steps are drawn where the values",
        "fall; the triangle marks a condition, not a direction. Value: per model, the share of its answers",
        "coded so; the plate prints the MEDIAN over models (analyse.py's unit; a pooled row-level share",
        "would weight models by draw count).",
        "",
        "Rows. Says \"I am ...\": the coder's self_predicates, the SPEAKER identifying itself in the first",
        "person ('I am X', 'My name is X'); an 'I' in quoted speech, a list or a template slot does not",
        "count, so this is not a count of the word 'I' (analyse.py prints it as 'any I'). Says it is an AI:",
        "identity_kind = ai_system. Claims to be a person: identity_kind = human_person.",
        "",
        "FENCES",
        "- THREE DIFFERENT MODEL SETS, NOT PAIRED LINEAGES: %d, %d and %d models (in the legend). Each step"
        % tuple(ns[s] for s in shorts),
        "  moves the population as well as the condition.",
        "- The two untemplated conditions come from the earlier F20x corpus (18,720 generations), recoded",
        "  here with the SAME coder as the chat run (code.py --corpus f20x). Prompt: 'Q: {q}\\nA:', the",
        "  question as raw text with no chat template; 60 new tokens, temperatures 0.7 and 1.0, 30 draws",
        "  per cell. The chat condition is a fresh run (run.py): the question as the user turn in each",
        "  model's own template, empty system block, the same 60 tokens and two temperatures, 20 draws per",
        "  cell. The three reasoning models (%s) were run at 1,024 tokens and"
        % ", ".join(m.split("/")[-1] for m in REASONING_SWAPPED),
        "  coded on the first 60 tokens after their think block (README: budget control moves <= 2.5pp).",
        "- Coder: malignment/tasks/code_framed_identity_v1.py, which ports F20x's identity_kind scheme.",
        "  Agreement with F20x's own coder on the same 18,720 texts: raw 87.6%, Cohen's kappa 0.802.",
        "- NO BASE-IN-CHAT CELL, and none is implied: 41 of 50 roster base models ship no chat template,",
        "  so base models cannot be addressed in one. The base-to-chat diagonal moves the weights and the",
        "  frame at once.",
        "- WHY 96.2 AND NOT 98.8. The chat condition is the empty system block minus SmolLM3-3B, whose",
        "  template hard-codes its persona so it has no empty slot: %d models, no identity text anywhere in"
        % ns[shorts[2]],
        "  the render. The 98.8% quoted until 2026-09-14 pooled each model's empty-block draws with its",
        "  shipped-default draws (19 models; re-derived here as %.2f), and 5 of the 19 shipped default" % pooled[1][1],
        "  blocks state the answer ('You are Qwen, created by Alibaba Cloud'), so the pooled rate measures",
        "  the prompt as well as the model. The shipped-default cell alone is %.1f%%; with SmolLM3 kept, the"
        % B["aligned, TEMPLATED, system=DEFAULT"][2],
        "  empty-block cell is %.1f%% over %d." % (B['aligned, TEMPLATED, system=""'][2],
                                                B['aligned, TEMPLATED, system=""'][0]),
        "",
        "%-28s %6s %10s %12s %12s" % ("condition", "models", "I am ...", "AI", "person"),
    ]
    for s in shorts:
        lines.append("%-28s %6d %9.1f%% %11.1f%% %11.1f%%" % (
            s, ns[s], *(val[(s, m)] for m, _ in MEASURES)))
    lines += ["", "Producer: experiments/subject_position/framed_identity/plot.py (asserts every row of the",
              "cross-frame table in results/analysis.txt). Source: README 'THE RESULT'."]
    save(p, name, "\n".join(lines))


FIGURES = {"frames": fig_frames}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("names", nargs="*", help="any of: %s" % ", ".join(FIGURES))
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    bad = [n for n in a.names if n not in FIGURES]
    if bad:
        ap.error("unknown figure(s) %s; choose from %s" % (bad, ", ".join(FIGURES)))
    if a.list:
        for k, fn in FIGURES.items():
            print("%-8s %s" % (k, fn.__doc__.strip().splitlines()[0]))
        return 0
    for k in a.names or FIGURES:
        FIGURES[k]()
    return 0


if __name__ == "__main__":
    sys.exit(main())
