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


def medians(sub, measures=None, stat="median"):
    """-> n models, [per measure: the MEDIAN (analyse.py's) or MEAN over models of each model's rate]"""
    agg = A.median if stat == "median" else (lambda xs: sum(xs) / len(xs))
    keep = per_model(sub)
    return len(keep), [100 * agg([sum(1 for x in g if fn(x)) / len(g) for g in keep.values()])
                       for _, fn in (measures or MEASURES)]


def _checked():
    """strata(), refused unless analysis.txt's cross-frame table reproduces. -> S, B, swapped, pooled"""
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
    return S, B, swapped, pooled


def _spread(xs, sep, lo, hi):
    """Label centres for marks at xs (one side of one row): runs closer than `sep` are
    pushed apart symmetrically about their mean, then kept inside [lo, hi]."""
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    out = list(xs)
    runs = [[order[0]]]
    for i in order[1:]:
        if xs[i] - xs[runs[-1][-1]] < sep:
            runs[-1].append(i)
        else:
            runs.append([i])
    for r in runs:
        mid = sum(xs[i] for i in r) / len(r)
        for k, i in enumerate(r):
            out[i] = mid + (k - (len(r) - 1) / 2) * sep
        shift = max(lo - out[r[0]], 0) - max(out[r[-1]] - hi, 0)
        for i in r:
            out[i] += shift
    return out


def _draw(S, measures, height, dodge=False, stat="median"):
    """The plate: one row per measure, a line through three marks. -> p, ns, val"""
    import matplotlib
    matplotlib.use("Agg")
    import pandas as pd
    from plotnine import (ggplot, aes, geom_segment, geom_point, geom_text, labs, scale_x_continuous,
                          scale_y_continuous, scale_shape_manual, theme, element_text, element_blank,
                          element_rect, guides, guide_legend)
    ns, val = {}, {}
    for lab, short in COND:
        n, vals = medians(S[lab], measures, stat)
        ns[short] = n
        for (mlab, _), v in zip(measures, vals):
            val[(short, mlab)] = v
    #: the model count goes in the legend, so the unpaired design is on the plate
    LEG = {short: "%s (%d)" % (short, ns[short]) for _, short in COND}
    shorts = [short for _, short in COND]
    seg, pts = [], []
    for k, (mlab, _) in enumerate(measures):
        y = len(measures) - k
        v = [val[(s, mlab)] for s in shorts]
        seg += [dict(y=y, x0=v[0], x1=v[1]), dict(y=y, x0=v[1], x1=v[2])]
        #: value labels: the no-template mark's below, the other two above, so
        #: marks 5 points apart (95 and 100) never share a label line
        lx = list(v)
        if dodge:
            #: circle and square share the upper line: where they sit within 7 points
            #: (0.0 and 1.7, 0.0 and 6.7) their labels are pushed apart sideways
            lx[0], lx[2] = _spread([v[0], v[2]], 7.0, -5.0, 105.0)
        for i, s in enumerate(shorts):
            pts.append(dict(y=y, x=v[i], lx=lx[i], cond=LEG[s], lab="%.1f" % v[i],
                            ly=y + (-0.3 if i == 1 else 0.3)))
    d, q = pd.DataFrame(seg), pd.DataFrame(pts)
    q["cond"] = pd.Categorical(q.cond, categories=[LEG[s] for s in shorts])
    fnt = F.pub_font()
    W_IN, H_IN = F.PUB_SIZE[0], height
    LABEL_PT = 7
    p = (ggplot()
         + geom_segment(aes(x="x0", xend="x1", y="y", yend="y"), data=d,
                        color=F.PUB_INK, size=0.85 * F.PUB_LINE_PT)
         + geom_point(aes(x="x", y="y", shape="cond"), data=q, color=F.PUB_INK, fill=F.PUB_INK,
                      size=1.9, stroke=0.7)
         + geom_text(aes(x="lx", y="ly", label="lab"), data=q, size=LABEL_PT, family=fnt,
                     color=F.PUB_INK, va="center")
         + scale_shape_manual(dict(zip([LEG[s] for s in shorts], ["o", ">", "s"])),
                              name="", breaks=[LEG[s] for s in shorts])
         #: one column: in one row "Aligned, in chat (18)" ran off the canvas, cut silently
         + guides(shape=guide_legend(ncol=1))
         + scale_x_continuous(limits=(-7, 107), expand=(0, 0), breaks=[0, 25, 50, 75, 100],
                              labels=lambda v: ["%g%%" % x for x in v])
         + scale_y_continuous(limits=(0.45, len(measures) + 0.55), expand=(0, 0),
                              breaks=list(range(len(measures), 0, -1)), labels=[m for m, _ in measures])
         + labs(x="Answers to \u201cWho are you?\u201d, %s over models" % stat, y="")
         + F.pub_theme(height=H_IN, grid="none")
         + theme(figure_size=(W_IN, H_IN), legend_position="bottom", legend_title=element_blank(),
                 legend_text=element_text(family=fnt, size=F.PUB_FONT_PT),
                 legend_key=element_rect(fill="white", color="white"),
                 legend_margin=0, legend_box_spacing=0.02,
                 legend_box_just="center",
                 #: the row names are the plate's subject, black as Figure 6's words are
                 axis_text_y=element_text(family=fnt, size=F.PUB_FONT_PT, color=F.PUB_INK),
                 axis_ticks_major_y=element_blank()))
    return p, ns, val


def fig_frames():
    """The subject in three conditions: 'Who are you?', base -> aligned -> aligned in chat."""
    name = "ci_subject_frames"
    for ext in (".png", ".pdf", ".tif", ".caption.txt"):
        assert not os.path.exists(os.path.join(FIG, name + ext)), "refusing to overwrite %s%s" % (name, ext)
    S, B, swapped, pooled = _checked()
    p, ns, val = _draw(S, MEASURES, 3.1)
    shorts = [short for _, short in COND]

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


#: all five levels of the coder's identity_kind, in the order the plate reads them
KINDS = [("Says it is an AI", "ai_system"),
         ("Claims to be a person", "human_person"),
         ("Plays a named character", "fictional_or_roleplay"),
         ("Says it is a thing or idea", "object_or_abstraction"),
         ("Makes no identity claim", "none")]


def fig_kinds(stat="median"):
    """The subject in three conditions, all five identity kinds (RH, 2026-09-25)."""
    import numpy as np
    MEAN = stat == "mean"
    name = "ci_subject_frames_kinds" + ("_mean" if MEAN else "")
    for ext in (".png", ".pdf", ".tif", ".caption.txt"):
        assert not os.path.exists(os.path.join(FIG, name + ext)), "refusing to overwrite %s%s" % (name, ext)
    S, B, swapped, pooled = _checked()
    measures = [(lab, (lambda k: lambda x: x["identity_kind"] == k)(k)) for lab, k in KINDS]
    #: the five are the coder's whole vocabulary: no answer falls outside them
    for lab, _ in COND:
        seen = {x["identity_kind"] for g in per_model(S[lab]).values() for x in g}
        assert seen <= {k for _, k in KINDS}, (lab, seen)
    p, ns, val = _draw(S, measures, 3.9, dodge=True, stat=stat)
    shorts = [short for _, short in COND]
    med = {(short, klab): v for lab, short in COND for (klab, _), v in zip(measures, medians(S[lab], measures)[1])}
    #: two of the five are booked in analysis.txt (as MEDIANS), and must be the same numbers there
    for (lab, short) in COND:
        assert round(med[(short, "Says it is an AI")], 1) == B[lab][2], short
        assert round(med[(short, "Claims to be a person")], 1) == B[lab][3], short

    rng, pool, sums = {}, {}, {}
    for lab, short in COND:
        keep = per_model(S[lab])
        rows = [x for g in keep.values() for x in g]
        for klab, k in KINDS:
            r = np.array([100 * sum(x["identity_kind"] == k for x in g) / len(g) for g in keep.values()])
            rng[(short, klab)] = (r.min(), np.percentile(r, 25), np.percentile(r, 75), r.max())
            pool[(short, klab)] = 100 * sum(x["identity_kind"] == k for x in rows) / len(rows)
        assert abs(sum(pool[(short, kl)] for kl, _ in KINDS) - 100) < 1e-9
        sums[short] = sum(val[(short, kl)] for kl, _ in KINDS)
        if MEAN:
            #: the reason for the mean: the parts of one whole sum to the whole
            assert abs(sums[short] - 100) < 1e-9, (short, sums[short])
    #: the mean equals the pooled share exactly where every model gives the same number of answers
    same_n = {short: len({len(g) for g in per_model(S[lab]).values()}) == 1 for lab, short in COND}
    sp = {short: medians(S[lab])[1][0] for lab, short in COND}

    lines = [
        "PLATE: THE SUBJECT IN THREE CONDITIONS, ALL FIVE IDENTITY KINDS%s. \"Who are you?\", one coder,"
        % (", MEANS" if MEAN else ""),
        "three model sets.",
        "",
        "Per row, a line through three marks. Circle: base models, untemplated. Triangle: aligned models,",
        "untemplated. Square: aligned models in their own chat template. Steps are drawn where the values",
        *(["fall; the triangle marks a condition, not a direction; where marks coincide (0.0, 1.7) the later",
           "one is drawn over the earlier, and value labels are nudged sideways so each stays legible."]
          if not MEAN else
          ["fall; the triangle marks a condition, not a direction; where marks nearly coincide the later one",
           "is drawn over the earlier, and value labels are nudged sideways so each stays legible."]),
        "",
        "Rows: the five levels of the coder's identity_kind, which is its whole vocabulary (asserted), one",
        "per answer: what kind of thing the speaker claims to BE. AI = an AI, model, assistant, program,",
        "bot. Person = a person with a human life, occupation or kinship relation. Named character = a",
        "named character it is playing. Thing or idea = a thing, a concept, a voice. No identity claim =",
        "it makes none (including answers that never say who is speaking).",
        "",
        *(textwrap.wrap(
            "Value: per model, the share of its answers of that kind; the plate prints the MEDIAN over "
            "models (analyse.py's unit). Medians of the five need not sum to 100 and do not: %s. The pooled "
            "shares below do. AI and person are the booked cross-frame numbers (results/analysis.txt, "
            "asserted); the other three kinds are not in that table and are computed here by the same rule."
            % "; ".join("%s %.1f" % (s_.lower(), sums[s_]) for s_ in shorts), 100) if not MEAN else
          textwrap.wrap(
            "Value: per model, the share of its answers of that kind; the plate prints the MEAN over "
            "models. Each model counts once, as in analyse.py, and unlike a median the mean keeps the five "
            "rows summing to 100 in each condition (asserted): every model's own five shares sum to 100, and "
            "an average of wholes is a whole. The mean equals the pooled share of all answers where every "
            "model gives the same number of answers (%s) and differs slightly where they do not (%s). "
            "The booked cross-frame figures (results/analysis.txt) are MEDIANS, printed in the table "
            "below and asserted for AI and person: AI %s. Median and mean part most where models split "
            "between none and nearly all, which is what the interquartile ranges below show."
            % ("; ".join(s_.lower() for s_ in shorts if same_n[s_]),
               "; ".join(s_.lower() for s_ in shorts if not same_n[s_]),
               " -> ".join("%.1f" % med[(s_, "Says it is an AI")] for s_ in shorts)), 100)),
        "",
        "FENCES: as ci_subject_frames (same strata, same producer). Three different model sets, not paired",
        "lineages (%d, %d, %d). The untemplated conditions are the F20x corpus recoded with this coder"
        % tuple(ns[s_] for s_ in shorts),
        "(prompt 'Q: {q}\\nA:', no chat template); the chat condition is a fresh run, empty system block,",
        ("minus SmolLM3-3B (%.1f%% AI, not the retracted pooled %.1f). Coder kappa 0.802 against F20x's." % (
            val[(shorts[2], "Says it is an AI")], pooled[1][1])) if not MEAN else
        #: 98.8 is a MEDIAN; set beside the mean it would read as a 6-point retraction
        ("minus SmolLM3-3B (AI: median %.1f, not the retracted pooled median %.1f). Kappa 0.802 vs F20x." % (
            med[(shorts[2], "Says it is an AI")], pooled[1][1])),
        "No base-in-chat cell: 41 of 50 roster base models ship no chat template.",
        "",
        *(["Ranges, per condition and kind: median over models [interquartile range over models; min-max],",
           "then the pooled share of all answers. Quartiles by linear interpolation (numpy default)."]
          if not MEAN else
          ["Per condition and kind: MEAN over models (drawn), MEDIAN over models, [interquartile range over",
           "models; min-max], then the pooled share of all answers. Quartiles by linear interpolation."]),
        "",
    ]
    for short in shorts:
        lines.append("%s (%d models)" % (short, ns[short]))
        for klab, _ in KINDS:
            lo, q1, q3, hi = rng[(short, klab)]
            if MEAN:
                lines.append("  %-28s mean %5.1f  median %5.1f  [%5.1f-%5.1f; %5.1f-%5.1f]  pooled %5.1f" % (
                    klab, val[(short, klab)], med[(short, klab)], q1, q3, lo, hi, pool[(short, klab)]))
                continue
            lines.append("  %-28s %5.1f  [%5.1f-%5.1f; %5.1f-%5.1f]   pooled %5.1f" % (
                klab, val[(short, klab)], q1, q3, lo, hi, pool[(short, klab)]))
        lines.append("")
    lines += [
        *textwrap.wrap(
            "Not drawn here: 'Says \"I am ...\"' (self_predicates: the speaker identifying itself in the "
            "first person), median %s. It is not the complement of 'no identity claim': an answer can "
            "self-identify tautologically ('I am me'), which codes as no identity claim."
            % " -> ".join("%.1f" % sp[s_] for s_ in shorts), 100),
        "",
        "Producer: experiments/subject_position/framed_identity/plot.py %s." % ("kinds_mean" if MEAN else "kinds"),
    ]
    save(p, name, "\n".join(lines))


def fig_kinds_mean():
    """All five identity kinds, MEAN over models, so each condition's rows sum to 100 (RH, 2026-09-25)."""
    fig_kinds("mean")


#: RH, 2026-09-25: stacked bars, one per condition, summing to 100. Named characters
#: are mostly gods, devils, Jesus, Pooh, Skynet -- not persons -- and "thing or idea"
#: is a grab-bag of machines, animals, organisations and gods; so the four-group
#: version pools the two as SOMETHING ELSE. (group label, identity_kind levels, gray)
GROUPS4 = [("AI", ("ai_system",), "#000000"),
           ("A person", ("human_person",), "#737373"),
           ("Something else", ("fictional_or_roleplay", "object_or_abstraction"), "#bfbfbf"),
           ("No identity claim", ("none",), "#ffffff")]
GROUPS5 = [("AI", ("ai_system",), "#000000"),
           ("A person", ("human_person",), "#4d4d4d"),
           ("A named character", ("fictional_or_roleplay",), "#8c8c8c"),
           ("A thing or idea", ("object_or_abstraction",), "#cccccc"),
           ("No identity claim", ("none",), "#ffffff")]
MACHINE = re.compile(r"\b(robot|computer|machine|android|cyborg)s?\b")


def _stack_plot(shorts, ns, mean, groups, fmt="%.1f", min_w=7, height=2.7, legend_nrow=None):
    """One horizontal bar per condition, segments in `groups` order [(label, gray)]. -> plotnine plot"""
    import matplotlib
    matplotlib.use("Agg")
    import pandas as pd
    from plotnine import (ggplot, aes, geom_rect, geom_text, labs, scale_x_continuous, scale_y_continuous,
                          scale_fill_manual, theme, element_text, element_blank, guides, guide_legend,
                          coord_cartesian)
    rects, labs_ = [], []
    for i, short in enumerate(shorts):
        y = len(shorts) - i
        x0 = 0.0
        for g, col in groups:
            w = mean[(short, g)]
            rects.append(dict(xmin=x0, xmax=x0 + w, ymin=y - 0.32, ymax=y + 0.32, grp=g))
            #: a value inside its segment only where it fits; every value is in the caption
            if w >= min_w:
                labs_.append(dict(x=x0 + w / 2, y=y, lab=fmt % w,
                                  col="white" if F.ink(col) >= 50 else "black"))
            x0 += w
    d, t = pd.DataFrame(rects), pd.DataFrame(labs_)
    assert len(d) == len(shorts) * len(groups)
    assert all(abs(v - 100) < 1e-9 for v in d.groupby("ymin").xmax.max()), d.groupby("ymin").xmax.max()
    d["grp"] = pd.Categorical(d.grp, categories=[g for g, _ in groups])
    fnt = F.pub_font()
    W_IN, H_IN = F.PUB_SIZE[0], height
    p = (ggplot()
         + geom_rect(aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="grp"), data=d,
                     color=F.PUB_INK, size=0.3)
         + geom_text(aes(x="x", y="y", label="lab", color="col"), data=t, size=7, family=fnt,
                     va="center", show_legend=False)
         + scale_fill_manual(dict(groups), name="", breaks=[g for g, _ in groups])
         + scale_color_manual_identity()
         + guides(fill=guide_legend(nrow=legend_nrow or (2 if len(groups) <= 4 else 3), byrow=True))
         #: NOT scale limits: a bar summing to 100 plus a float hair put its last
         #: rectangle outside limits=(0, 100) and plotnine DROPPED it -- a white
         #: segment, so the gap read as the segment. coord_cartesian windows, never drops.
         + scale_x_continuous(expand=(0, 0), breaks=[0, 25, 50, 75, 100],
                              labels=lambda v: ["%g%%" % x for x in v])
         + scale_y_continuous(expand=(0, 0), breaks=list(range(len(shorts), 0, -1)),
                              labels=["%s (%d)" % (s_, ns[s_]) for s_ in shorts])
         + coord_cartesian(xlim=(0, 100), ylim=(0.5, len(shorts) + 0.5), expand=False)
         + labs(x="Answers to \u201cWho are you?\u201d, mean over models", y="")
         + F.pub_theme(height=H_IN, grid="none")
         + theme(figure_size=(W_IN, H_IN), legend_position="bottom", legend_title=element_blank(),
                 legend_text=element_text(family=fnt, size=F.PUB_FONT_PT),
                 legend_margin=0, legend_box_spacing=0.02, legend_key_size=9,
                 axis_text_y=element_text(family=fnt, size=F.PUB_FONT_PT, color=F.PUB_INK),
                 axis_ticks_major_y=element_blank()))

    return p


def fig_stack(groups, name, fmt="%.1f", min_w=7):
    """Stacked bars: each condition's answers split by identity kind, MEAN over models, summing to 100."""
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    import pandas as pd
    from plotnine import (ggplot, aes, geom_rect, geom_text, labs, scale_x_continuous, scale_y_continuous,
                          scale_fill_manual, theme, element_text, element_blank, element_rect, guides,
                          guide_legend, coord_cartesian)
    for ext in (".png", ".pdf", ".tif", ".caption.txt"):
        assert not os.path.exists(os.path.join(FIG, name + ext)), "refusing to overwrite %s%s" % (name, ext)
    S, B, swapped, pooled = _checked()
    F.check_halftones({g: c for g, _, c in groups})
    #: the groups partition the coder's whole vocabulary, each level exactly once
    levels = [k for _, ks, _ in groups for k in ks]
    assert sorted(levels) == sorted(k for _, k in KINDS), levels
    measures = [(g, (lambda ks: lambda x: x["identity_kind"] in ks)(ks)) for g, ks, _ in groups]
    shorts = [short for _, short in COND]
    ns, mean, med, rng, pool, top = {}, {}, {}, {}, {}, {}
    for lab, short in COND:
        n, m = medians(S[lab], measures, "mean")
        ns[short] = n
        assert abs(sum(m) - 100) < 1e-9, (short, sum(m))          # a bar is a whole
        for (g, fn), v, md in zip(measures, m, medians(S[lab], measures)[1]):
            keep = per_model(S[lab])
            r = np.array([100 * sum(fn(x) for x in gg) / len(gg) for gg in keep.values()])
            rows = [x for gg in keep.values() for x in gg]
            mean[(short, g)], med[(short, g)] = v, md
            rng[(short, g)] = (np.percentile(r, 25), np.percentile(r, 75))
            pool[(short, g)] = 100 * sum(fn(x) for x in rows) / len(rows)
            c = collections.Counter((x.get("predicated_identity") or "").lower() for x in rows if fn(x))
            top[(short, g)] = [k for k, _ in c.most_common() if k][:5]
    #: booked: AI and person as MEDIANS against analysis.txt (groups found by kind, not by label)
    g_ai = [g for g, ks, _ in groups if ks == ("ai_system",)][0]
    g_hu = [g for g, ks, _ in groups if ks == ("human_person",)][0]
    for lab, short in COND:
        assert round(med[(short, g_ai)], 1) == B[lab][2] and round(med[(short, g_hu)], 1) == B[lab][3], short
    #: the AI border: machines the coder filed as a thing, not as AI
    obj = [x for lab, _ in COND for gg in per_model(S[lab]).values() for x in gg
           if x["identity_kind"] == "object_or_abstraction"]
    n_mach = sum(bool(MACHINE.search((x.get("predicated_identity") or "").lower())) for x in obj)

    p = _stack_plot(shorts, ns, mean, [(g, c) for g, _, c in groups], fmt=fmt, min_w=min_w)

    W = lambda txt: textwrap.wrap(txt, 100)
    lines = [
        "PLATE: WHAT THE SPEAKER SAYS IT IS, IN THREE CONDITIONS. \"Who are you?\", one coder, three model",
        "sets; stacked bars, %d kinds." % len(groups),
        "",
        *W("Each bar is one condition's answers split by the kind of thing the speaker claims to be (the "
           "coder's identity_kind, one per answer). Value: per model, the share of its answers of that kind; "
           "the bar prints the MEAN over models, so each model counts once (analyse.py's unit) and each bar "
           "sums to 100 (asserted). Values under %d points are not printed inside their segment; all are below."
           % min_w + (" In-bar values are rounded to whole percents." if "%.0f" in fmt else "")),
        "",
        "Groups (the coder's five levels, each in exactly one group; asserted):",
    ]
    for g, ks, col in groups:
        lines += W("- %s (%s; %d%% ink): %s." % (g, ", ".join(ks), F.ink(col), {
            "ai_system": "an AI, model, assistant, program, bot",
            "human_person": "a person with a human life, occupation or kinship relation",
            "fictional_or_roleplay": "a named character it is playing",
            "object_or_abstraction": "a thing, a concept, a voice",
            "none": "it makes no identity claim, including answers where no one says who is speaking"}[ks[0]]
            if len(ks) == 1 else "a named character it is playing, or a thing, concept or voice; pooled "
            "because neither is a person or an AI and each is small"))
    lines += [""] + W(
        "What the small kinds hold, as the coder's own predicated identities, most common first. "
        "Named characters are mostly not persons: gods, devils, Jesus, Winnie the Pooh, Skynet. Things "
        "and ideas mix machines, animals, organisations ('we are a not for profit organisation', from base "
        "models continuing web text) and gods. %d of the %d thing-or-idea answers across the three "
        "conditions name a robot, computer or machine: the coder filed them as a thing, not as AI, so the "
        "AI segment is if anything a slight undercount at its border." % (n_mach, len(obj)))
    for g, ks, _ in groups:
        if ks[0] in ("ai_system", "none"):
            continue
        for short in shorts:
            if top[(short, g)]:
                lines += W("  %s, %s: %s" % (g, short.lower(), "; ".join(top[(short, g)])))
    lines += [
        "",
        *W("FENCES: as ci_subject_frames (same strata, same producer). Three different model sets, not "
           "paired lineages (%d, %d, %d). The untemplated conditions are the F20x corpus recoded with this "
           "coder (prompt 'Q: {q}\\nA:', no chat template); the chat condition is a fresh run, empty system "
           "block, minus SmolLM3-3B, whose template has no empty slot. Coder kappa 0.802 against F20x's. No "
           "base-in-chat cell: 41 of 50 roster base models ship no chat template. The booked cross-frame "
           "figures (results/analysis.txt) are MEDIANS over models, asserted here for AI and person; the "
           "retracted 98.8 was a pooled median." % tuple(ns[s_] for s_ in shorts)),
        "",
        "Per condition and group: MEAN over models (drawn), MEDIAN, [interquartile range], pooled share.",
        "",
    ]
    for short in shorts:
        lines.append("%s (%d models)" % (short, ns[short]))
        for g, _, _ in groups:
            q1, q3 = rng[(short, g)]
            lines.append("  %-20s mean %5.1f  median %5.1f  [%5.1f-%5.1f]  pooled %5.1f" % (
                g, mean[(short, g)], med[(short, g)], q1, q3, pool[(short, g)]))
        lines.append("")
    lines.append("Producer: experiments/subject_position/framed_identity/plot.py %s." % name.replace("ci_subject_", ""))
    save(p, name, "\n".join(lines))


def scale_color_manual_identity():
    from plotnine import scale_color_identity
    return scale_color_identity()


#: WHOSE NAME IS IT. The coder records the name and maker a speaker gives
#: (self_name, maker_named) but not whether they are the speaker's own. This table
#: decides that, per model: OWN = the releasing org, the model's own name, or its
#: BASE model's org or name (so Tulu naming Meta or Llama is own; zephyr naming
#: Mistral is own). First match on the model id wins; every model must match one
#: (asserted), so a new model cannot fall through to "unnamed" silently.
LINEAGE = [
    ("tulu", r"tulu|\bai2\b|allen|llama|\bmeta\b"),
    ("olmo", r"olmo|\bai2\b|allen"),
    ("qwen", r"qwen|alibaba|tongyi"),
    ("tinyllama", r"tinyllama"),
    ("meta-llama/", r"llama|\bmeta\b"),
    ("huggyllama/", r"llama|\bmeta\b"),
    ("beaver", r"beaver|\bpku\b|alpaca|stanford|llama|\bmeta\b"),
    ("smollm", r"smol ?lm|hugging ?face"),
    ("huggingfaceh4/zephyr", r"zephyr|hugging ?face|mistral"),
    ("stablelm", r"stable ?lm|stable zephyr|stability"),
    ("mistralai/", r"mistral"),
    ("01-ai/yi", r"\byi\b|01\.? ?ai"),
    ("m-a-p/neo", r"\bneo\b|m-a-p|multimodal art projection"),
    ("m-a-p/ct-llm", r"ct-llm|m-a-p"),
    ("microsoft/phi", r"\bphi\b|microsoft"),
    ("tiiuae/falcon", r"falcon|\btii\b|technology innovation"),
    ("zai-org/glm", r"glm|zhipu|tsinghua|knowledge engineering|\bz\.ai\b"),
    ("openbmb/minicpm", r"minicpm|modelbest|openbmb|tsinghua"),
    ("deepseek", r"deepseek"),
    ("llm360/amber", r"amber|llm360"),
    ("togethercomputer/redpajama", r"redpajama|together"),
    #: word-bounded: "BloomReach" (a stablelm answer's maker) is not BigScience
    ("bigscience/bloom", r"\bbloomz?\b|bigscience|hugging ?face"),
    ("pythia", r"pythia|eleuther|archangel|contextual ?ai"),
]
#: every name that is SOMEBODY's: the union of the table plus the labs no model here comes from
KNOWN = "|".join([pat for _, pat in LINEAGE] + [
    #: spaced spellings occur ("Open AI" twice, "Deep Mind Technologies" once; audited 2026-09-25)
    r"open ?ai|chat ?gpt|\bgpt|anthropic|claude|google|gemini|\bbard\b|deep ?mind|open ?assistant|laion",
    r"cohere|baidu|ernie|\bbing\b|copilot|alexa|siri|\bibm\b|watson|\bxai\b|grok|moonshot|kimi"])


def own_pattern(model):
    m = model.lower()
    hits = [pat for key, pat in LINEAGE if key in m]
    assert hits, "no lineage entry for %s" % model
    return hits[0]


def ai_whose(x):
    """For an ai_system answer: 'itself', 'another', or 'unnamed' (no name, or only a made-up one)."""
    own = re.compile(own_pattern(x["model"]))
    names = [n.lower() for n in (x.get("self_name"), x.get("maker_named")) if n]
    #: another wins: a speaker that names its own maker AND OpenAI has put someone else's name on itself
    if any(re.search(KNOWN, n) and not own.search(n) for n in names):
        return "another"
    if any(own.search(n) for n in names):
        return "itself"
    return "unnamed"


GROUPS_AI = [("AI, names itself", "#000000"),
             ("AI, names no model", "#333333"),
             ("AI, names another model", "#666666"),
             ("A person", "#999999"),
             ("Something else", "#cccccc"),
             ("No identity claim", "#ffffff")]


def group_ai(x):
    k = x["identity_kind"]
    if k == "ai_system":
        return {"itself": "AI, names itself", "unnamed": "AI, names no model",
                "another": "AI, names another model"}[ai_whose(x)]
    return {"human_person": "A person", "fictional_or_roleplay": "Something else",
            "object_or_abstraction": "Something else", "none": "No identity claim"}[k]


#: RH, 2026-09-25: two AI slices only, for contrast -- self, and everything else
GROUPS_AI2 = [("AI (self)", "#000000"),
              ("AI (other)", "#4d4d4d"),
              ("A person", "#8c8c8c"),
              ("Something else", "#cccccc"),
              ("No identity claim", "#ffffff")]


def group_ai2(x):
    g = group_ai(x)
    return {"AI, names itself": "AI (self)", "AI, names no model": "AI (other)",
            "AI, names another model": "AI (other)"}.get(g, g)


def fig_stack_ai(two=False):
    """Stacked bars, AI split by whose name it gives: its own, none, or another model's (RH, 2026-09-25)."""
    import numpy as np
    name = "ci_subject_stack_ai" + ("2" if two else "")
    GROUPS, gfn, n_ai = (GROUPS_AI2, group_ai2, 2) if two else (GROUPS_AI, group_ai, 3)
    for ext in (".png", ".pdf", ".tif", ".caption.txt"):
        assert not os.path.exists(os.path.join(FIG, name + ext)), "refusing to overwrite %s%s" % (name, ext)
    S, B, swapped, pooled = _checked()
    F.check_halftones(dict(GROUPS))
    labels = [g for g, _ in GROUPS]
    measures = [(g, (lambda g: lambda x: gfn(x) == g)(g)) for g in labels]
    #: in the two-slice plate, the three-way split behind AI (other), for the caption
    three = {}
    shorts = [short for _, short in COND]
    ns, mean, pool, ex = {}, {}, {}, collections.defaultdict(collections.Counter)
    for lab, short in COND:
        keep = per_model(S[lab])
        for m_ in keep:
            own_pattern(m_)                                     # every model is in the table
        n, m = medians(S[lab], measures, "mean")
        ns[short] = n
        assert abs(sum(m) - 100) < 1e-9, (short, sum(m))
        rows = [x for g in keep.values() for x in g]
        for g, v in zip(labels, m):
            mean[(short, g)] = v
            pool[(short, g)] = 100 * sum(gfn(x) == g for x in rows) / len(rows)
        if two:
            three[short] = dict(zip([g for g, _ in GROUPS_AI],
                                    medians(S[lab], [(g, (lambda g: lambda x: group_ai(x) == g)(g))
                                                     for g, _ in GROUPS_AI], "mean")[1]))
            assert abs(three[short]["AI, names no model"] + three[short]["AI, names another model"]
                       - mean[(short, "AI (other)")]) < 1e-9
        for x in rows:
            if x["identity_kind"] == "ai_system":
                w = ai_whose(x)
                nm = " / ".join(n for n in (x.get("self_name"), x.get("maker_named")) if n)
                if nm:
                    ex[(short, w)][nm] += 1
        #: the AI slices together are the AI kind: same mean as the four-group plate
        ai_mean = medians(S[lab], [("ai", lambda x: x["identity_kind"] == "ai_system")], "mean")[1][0]
        assert abs(sum(mean[(short, g)] for g in labels[:n_ai]) - ai_mean) < 1e-9
    #: categorical anchors, one per condition, from the per-model tables
    assert ex[(shorts[0], "another")].most_common(1)[0][0].lower().endswith("openai")
    assert any("qwen" in k.lower() for k in ex[(shorts[2], "itself")])

    p = _stack_plot(shorts, ns, mean, GROUPS, fmt="%.0f%%", min_w=5, height=2.9, legend_nrow=3)

    W = lambda txt: textwrap.wrap(txt, 100)
    lines = ([
        "PLATE: WHAT THE SPEAKER SAYS IT IS, WITH AI SPLIT BY WHOSE NAME IT GIVES. \"Who are you?\", one",
        "coder, three model sets."] if not two else [
        "PLATE: WHAT THE SPEAKER SAYS IT IS, WITH AI SPLIT INTO SELF AND OTHER. \"Who are you?\", one coder,",
        "three model sets."]) + [
        "",
        *W("Each bar is one condition's answers split by the kind of thing the speaker claims to be, and "
           "the AI answers further by the name they give. Value: per model, the share of its answers in "
           "that group; the bar prints the MEAN over models (each model once; each bar sums to 100, "
           "asserted). Labels inside segments are rounded to whole percents and printed only where the "
           "segment is at least 5 points wide; exact values are below. The %s AI slices sum to the AI "
           "segment of ci_subject_stack4 (asserted)." % ("two" if two else "three")),
        "",
        *W(("AI, names itself: the speaker's self_name or maker_named matches its OWN lineage. AI, names "
            "another model: it names a known model or lab that is not its own (another wins where both "
            "occur). AI, names no model: neither, including a made-up name ('Luna', 'Sam', 'TechCraft AI "
            "team'). " if not two else
            "AI (self): an AI answer whose self_name or maker_named matches the speaker's OWN lineage. "
            "AI (other): every other AI answer -- it names no model at all ('I am an AI assistant'), gives "
            "a made-up name ('Luna', 'Sam', 'TechCraft AI team'), or names a model or lab not its own "
            "(OpenAI, Anthropic; that wins where an answer names both). The three-way split behind AI "
            "(other) is in ci_subject_stack_ai and below. ") +
           "OWN is decided by a table in plot.py (LINEAGE), not by the coder: the releasing org, "
           "the model's name, or its base model's org or name, so Tulu naming Meta is own and zephyr "
           "naming Mistral is own. The table covers every model drawn (asserted)."),
        "",
        "Other groups as ci_subject_stack4: a person; something else (named character, or thing or idea);",
        "no identity claim.",
        "",
        "What the named AI answers name (self_name / maker_named, most common first):",
    ]
    for short in shorts:
        for w, lab_ in (("itself", "own"), ("another", "another's")):
            c = ex[(short, w)]
            if c:
                lines += W("  %s, %s: %s" % (short, lab_, "; ".join("%s (%d)" % kv for kv in c.most_common(6))))
    lines += [
        "",
        *W("FENCES: as ci_subject_frames (same strata, same producer). Three different model sets, not "
           "paired lineages (%d, %d, %d). The untemplated conditions are the F20x corpus recoded with this "
           "coder (prompt 'Q: {q}\\nA:', no chat template); the chat condition is a fresh run, empty "
           "system block, minus SmolLM3-3B. Coder kappa 0.802 against F20x's. No base-in-chat cell: 41 of "
           "50 roster base models ship no chat template." % tuple(ns[s_] for s_ in shorts)),
        "",
        "Per condition and group: MEAN over models (drawn), then the pooled share of all answers.",
        "",
    ]
    for short in shorts:
        lines.append("%s (%d models)" % (short, ns[short]))
        for g in labels:
            lines.append("  %-26s mean %5.1f   pooled %5.1f" % (g, mean[(short, g)], pool[(short, g)]))
            if two and g == "AI (other)":
                lines.append("    of which names no model %.1f, names another model %.1f (means)" % (
                    three[short]["AI, names no model"], three[short]["AI, names another model"]))
        lines.append("")
    lines.append("Producer: experiments/subject_position/framed_identity/plot.py %s." % ("stack_ai2" if two else "stack_ai"))
    save(p, name, "\n".join(lines))


def fig_stack_ai2():
    """Stacked bars, AI (self) against AI (other): its own name, or anything else (RH, 2026-09-25)."""
    fig_stack_ai(two=True)


#: RH, 2026-09-25: the four groups under one-word names
GROUPS4W = [("AI", ("ai_system",), "#000000"),
            ("Human", ("human_person",), "#737373"),
            ("Other", ("fictional_or_roleplay", "object_or_abstraction"), "#bfbfbf"),
            ("None", ("none",), "#ffffff")]


def fig_stack4w():
    """Stacked bars, four groups named AI, Human, Other, None; whole-percent labels."""
    fig_stack(GROUPS4W, "ci_subject_stack4w", fmt="%.0f%%", min_w=5)


def fig_stack4():
    """Stacked bars, four groups: AI, person, something else, no claim (mean over models)."""
    fig_stack(GROUPS4, "ci_subject_stack4")


def fig_stack5():
    """Stacked bars, the coder's five identity kinds (mean over models)."""
    fig_stack(GROUPS5, "ci_subject_stack5")


FIGURES = {"frames": fig_frames, "kinds": fig_kinds, "kinds_mean": fig_kinds_mean,
           "stack4": fig_stack4, "stack5": fig_stack5, "stack_ai": fig_stack_ai, "stack_ai2": fig_stack_ai2,
           "stack4w": fig_stack4w}


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
