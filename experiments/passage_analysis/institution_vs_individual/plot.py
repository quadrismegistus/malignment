#!/usr/bin/env python
"""Critical Inquiry plates for the Political economy section: two candidates.

    python plot.py              # both
    python plot.py words        # plate A, the words of the capture
    python plot.py channel      # plate B, where the complaint is sent
    python plot.py --list

Writes `figures/<name>.{png,pdf,tif}` and `figures/<name>.caption.txt`. House
rules (paper seat, 2026-09-24): 4.8 in wide, at most 6.5 in tall, Arial, no type
under 7 pt, grayscale inside CI's halftone band (asserted), no title or caption
on the plate; every number the plate carries is in the caption file.

## NEITHER PLATE COMPUTES ITS OWN STATISTIC

Both re-derive a table another producer in this folder already booked, and
refuse to draw unless they reproduce it:

    words    word_did.py   -> results/word_did.md     no LLM; passage text only
    channel  by_dispute.py -> results/by_dispute.md   the LLM coder's `channel`

The helpers are IMPORTED from those producers and from `analyse_regen.py` (the
tokeniser, BH, the sign test, the keep filter, the domain map), not retyped, so
a change there reaches the plate. The arithmetic around them is repeated here
because neither producer exposes it as a function, and the booked-table asserts
are what keeps the two copies from drifting apart.

## PLATE A DRAWS POOLED SHARES; ITS STATISTIC IS A MEDIAN OVER LINEAGES

The arrows are the share of ALL passages on that side and arm containing the
word, exactly the four columns word_did.md prints. The test behind the word's
selection is the per-lineage difference-in-differences, and its median and
sign counts go in the caption file, not on the plate.

## WORD SELECTION IS A RULE, NOT A READING

From words in >= 300 passages, surviving BH over lineages AND p < 0.05 by
dispute (the set word_did.md tables), drop closed-class words (STOP, printed in
the caption file), then take the top N_IND by median DiD and the bottom N_INST.
Ties are broken by the unrounded median, then alphabetically.
"""
import argparse
import collections
import json
import os
import sys
import textwrap

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
for p in (HERE, REPO):
    if p not in sys.path:
        sys.path.insert(0, p)

import analyse_regen as A                     # noqa: E402  SRC, keep, outcomes, sign
import by_dispute as BD                       # noqa: E402  DOM
import word_did as W                          # noqa: E402  TOK, MIN_DOCS, bh
from malignment import figure as F            # noqa: E402

FIG = os.path.join(HERE, "figures")
SEED = 20260924
N_IND, N_INST = 8, 4

#: Closed-class words: pronouns, determiners, modal and auxiliary verbs,
#: prepositions, conjunctions, negation, and quantifier or degree adverbs. The
#: test is the word's CLASS, not whether it moved: `their` and `my` are the two
#: largest institution-side movers and both go, because a pronoun's movement is
#: the change of genre (continuation to advice), which README names as genre.
STOP = set("""
a an the this that these those some any all each every many much more most few
i me my mine we us our you your yours he him his she her it its they them their
can could may might must shall should will would do does did have has had be is
are was were been being am
if or and but so because as than then not no nor never
of to in on at by for from with about into over under out up down off
also now only just even still again very too here there when where how why what
which who whom whose
""".split())


def save(p, name, w, h, caption):
    """PNG + PDF (house `save`), a 300 dpi TIF from the PNG, and the caption file."""
    from PIL import Image
    os.makedirs(FIG, exist_ok=True)
    png, pdf = F.save(p, os.path.join(FIG, name + ".png"))
    tif = os.path.join(FIG, name + ".tif")
    Image.open(png).save(tif, dpi=(300, 300), compression="tiff_lzw")
    cap = os.path.join(FIG, name + ".caption.txt")
    open(cap, "w").write(caption.rstrip() + "\n")
    for f in (png, pdf, tif, cap):
        print("   %-44s %7.0f KB" % (os.path.relpath(f, HERE), os.path.getsize(f) / 1024))


def booked_table(path, header_prefix):
    """Rows of the markdown table that follows `## <header_prefix>...`, as lists."""
    out, on = [], False
    for line in open(path):
        if line.startswith("## "):
            on = line[3:].startswith(header_prefix)
            continue
        if on and line.startswith("| ") and not line.startswith("| word") \
                and not line.startswith("|---"):
            out.append([c.strip() for c in line.strip().strip("|").split("|")])
    return out


# ───────────────────────────────────────────────────────────── plate A, words
def word_frame():
    """Recompute word_did.md for every word, assert it, apply the selection rule."""
    rows = [json.loads(l) for l in open(A.SRC)]
    arms = collections.defaultdict(set)
    for r in rows:
        arms[r["lineage"]].add(r["arm"])
    rows = [r for r in rows if arms[r["lineage"]] == {"base", "aligned"}]
    docs = [set(W.TOK.findall((r["text"] or "").lower())) for r in rows]
    df = collections.Counter(w for d in docs for w in d)
    vocab = sorted(w for w, n in df.items() if n >= W.MIN_DOCS)
    idx = {w: i for i, w in enumerate(vocab)}

    def tally(unit):
        n = collections.Counter()
        c = collections.defaultdict(lambda: np.zeros(len(vocab)))
        for r, d in zip(rows, docs):
            k = (r[unit], r["arm"], r["side"])
            n[k] += 1
            for w in d:
                if w in idx:
                    c[k][idx[w]] += 1
        out = []
        for u in sorted({k[0] for k in n}):
            ks = [(u, a, s) for a in ("base", "aligned") for s in ("individual", "institution")]
            if min(n[k] for k in ks) == 0:
                continue
            f = {k: c[k] / n[k] for k in ks}
            out.append((f[(u, "aligned", "individual")] - f[(u, "base", "individual")])
                       - (f[(u, "aligned", "institution")] - f[(u, "base", "institution")]))
        return np.array(out)

    L_, D_ = tally("lineage"), tally("scenario")
    res = {}
    for w, i in idx.items():
        lu, ld, lp = A.sign(list(L_[:, i]))
        du, dd, dp = A.sign(list(D_[:, i]))
        res[w] = dict(lu=lu, ld=ld, lp=lp, du=du, dd=dd, dp=dp, med=float(np.median(L_[:, i])))
    sig = dict(zip(res, W.bh([res[w]["lp"] for w in res])))
    both = {w for w in res if sig[w] and res[w]["dp"] < 0.05}

    share = {}
    for a in ("base", "aligned"):
        for s in ("individual", "institution"):
            sub = [d for r, d in zip(rows, docs) if r["arm"] == a and r["side"] == s]
            share[(a, s)] = {w: sum(1 for d in sub if w in d) / len(sub) for w in vocab}

    #: THE BOOKED TABLE, every row of both halves, to its printed precision.
    booked = 0
    for half in ("Gains MORE on the individual", "Gains MORE on the institution"):
        for c in booked_table(os.path.join(HERE, "results", "word_did.md"), half):
            w = c[0]
            got = ["%.3f" % share[("base", "individual")][w], "%.3f" % share[("base", "institution")][w],
                   "%.3f" % share[("aligned", "individual")][w], "%.3f" % share[("aligned", "institution")][w],
                   "%+.3f" % res[w]["med"], "%d/%d" % (res[w]["lu"], res[w]["ld"]),
                   "%d/%d" % (res[w]["du"], res[w]["dd"])]
            assert got == c[1:] and w in both, "word_did.md row %s: booked %s, derived %s" % (w, c[1:], got)
            booked += 1
    #: and the README's own headline word, categorically
    assert (res["contact"]["lu"], res["contact"]["ld"], res["contact"]["du"], res["contact"]["dd"]) == (41, 1, 18, 0)
    print("   word_did.md reproduced: %d booked rows, %d passages, %d words, %d in both tests"
          % (booked, len(rows), len(vocab), len(both)))

    content = [w for w in both if w not in STOP]
    ind = sorted([w for w in content if res[w]["med"] > 0], key=lambda w: (-res[w]["med"], w))[:N_IND]
    inst = sorted([w for w in content if res[w]["med"] < 0], key=lambda w: (res[w]["med"], w))[:N_INST]
    sel = []
    for grp, ws in (("ind", ind), ("inst", inst)):
        for w in ws:
            sel.append(dict(word=w, grp=grp, **res[w],
                            b_ind=share[("base", "individual")][w], b_inst=share[("base", "institution")][w],
                            a_ind=share[("aligned", "individual")][w], a_inst=share[("aligned", "institution")][w]))
    meta = dict(n_pass=len(rows), n_vocab=len(vocab), n_both=len(both),
                n_lin=len(L_), n_disp=len(D_),
                dropped=sorted((w for w in both if w in STOP), key=lambda w: -abs(res[w]["med"])))
    return sel, meta


def fig_words():
    """Plate A: base -> aligned share per word, individual dark, institution light."""
    import matplotlib
    matplotlib.use("Agg")
    import pandas as pd
    from plotnine import (ggplot, aes, geom_segment, geom_point, geom_text, geom_vline, facet_grid, labs, arrow,
                          scale_x_continuous, scale_y_continuous, scale_color_manual, theme,
                          element_text, element_blank, element_rect)
    sel, meta = word_frame()
    TONE = {"The aggrieved individual": F.PUB_INK, "The institution": F.PUB_GRAY}
    F.check_halftones(TONE)
    GRP = {"ind": "Gains more for the individual", "inst": "Gains more for the institution"}
    rows, n_ind = [], sum(s["grp"] == "ind" for s in sel)
    for k, s in enumerate(sel):
        y0 = len(sel) - k                                  # top row first
        for side, b, a, dy in (("The aggrieved individual", s["b_ind"], s["a_ind"], +0.17),
                               ("The institution", s["b_inst"], s["a_inst"], -0.17)):
            rows.append(dict(word=s["word"], grp=GRP[s["grp"]], side=side, y=y0 + dy, ypos=y0,
                             b=100 * b, a=100 * a))
    d = pd.DataFrame(rows)
    d["grp"] = pd.Categorical(d.grp, categories=list(GRP.values()))
    #: GROUP HEADINGS AS TEXT INSIDE EACH PANEL, above its first word. As
    #: rotated strips the institution's ran longer than its four-row panel and
    #: was cut at the canvas edge -- a pixel-only defect.
    head = (d.groupby("grp", observed=True).ypos.max() + 0.85).reset_index()
    head["label"] = list(head.grp)
    head["grp"] = pd.Categorical(head.grp, categories=list(GRP.values()))
    d["side"] = pd.Categorical(d.side, categories=list(TONE))
    ticks = d.drop_duplicates("word")
    xmax = float(max(d.a.max(), d.b.max()))
    fnt = F.pub_font()
    W_IN, H_IN = F.PUB_SIZE[0], 4.6
    p = (ggplot(d)
         + geom_segment(aes(x="b", xend="a", y="y", yend="y", color="side"),
                        size=F.PUB_LINE_PT, arrow=arrow(length=0.05, type="closed", angle=25))
         + geom_point(aes(x="b", y="y", color="side"), size=1.1)
         + geom_text(aes(x=0.4, y="ypos", label="label"), data=head, ha="left", va="center",
                     size=F.PUB_FONT_PT, family=fnt, fontweight="bold")
         #: WORDS AS TEXT FROM THE DATA, per facet. As axis labels they were a
         #: positional labeller over free_y facets, and the lower panel printed
         #: `department` -- a word from the upper one -- at a break its range
         #: happened to reach. The trap is in this seat's notes; the image caught it.
         + geom_text(aes(x=-0.8, y="ypos", label="word"), data=ticks, ha="right", va="center",
                     size=F.PUB_FONT_PT, family=fnt)
         + facet_grid("grp ~ .", scales="free_y", space="free")
         + scale_color_manual(TONE, name="")
         #: the left 9 points of the x range hold the words
         + scale_x_continuous(limits=(-9.5, xmax * 1.04), expand=(0, 0),
                              breaks=[0, 10, 20, 30, 40],
                              labels=lambda v: ["%g%%" % x for x in v])
         + geom_vline(xintercept=0, color=F.PUB_GRAY, size=F.PUB_RULE_PT)
         + scale_y_continuous(breaks=[], expand=(0, 0.5))
         + labs(x="Passages containing the word, base model → aligned model", y="")
         + F.pub_theme(height=H_IN, grid="none")
         + theme(figure_size=(W_IN, H_IN),
                 legend_position="top", legend_direction="horizontal",
                 legend_title=element_blank(),
                 legend_text=element_text(family=fnt, size=F.PUB_FONT_PT),
                 legend_key=element_rect(fill="white", color="white"),
                 strip_text_y=element_blank(),
                 strip_background=element_blank(),
                 axis_ticks_major_y=element_blank()))

    lines = [
        "PLATE A. The words of the capture. What alignment adds to advice, by side of the dispute.",
        "",
        "Each word has two arrows, base model to aligned model: the aggrieved individual (black, upper)",
        "and the institution (gray, lower). Arrow ends are the share of ALL passages on that side and arm",
        "that contain the word (document frequency: a passage counts once however often it repeats it).",
        "",
        "Corpus: experiments/passage_analysis/institution_vs_individual, the 256-token regeneration.",
        "%s passages from %d lineages with both arms, 18 disputes, each written from both sides." % (
            format(meta["n_pass"], ","), meta["n_lin"]),
        "Base model raw, aligned model in chat. No LLM in the measurement or the selection: passage text",
        "only, lower-cased [a-z']+ tokens. Producer word_did.py; table results/word_did.md; this plate plot.py.",
        "",
        "SELECTION RULE. Of the %d words in at least %d passages, those whose per-lineage difference-in-" % (
            meta["n_vocab"], W.MIN_DOCS),
        "differences (individual change minus institution change) survives a sign test over lineages under",
        "Benjamini-Hochberg across all %d words AND a sign test over the 18 disputes at p < 0.05 (%d words)." % (
            meta["n_vocab"], meta["n_both"]),
        "Closed-class words removed (pronouns, determiners, modals and auxiliaries, prepositions,",
        "conjunctions, negation, quantifier and degree adverbs; full list in plot.py STOP). Then the top %d" % N_IND,
        "by median DiD (gains more for the individual) and the bottom %d (gains more for the institution)." % N_INST,
        "Largest movers removed as closed-class: %s." % ", ".join(meta["dropped"][:12]),
        "",
        "EXPLORATORY: many words tested, nothing declared in advance.",
        "",
        "%-12s %8s %8s   %8s %8s   %8s  %9s  %9s" % ("word", "ind base", "ind alig", "ins base", "ins alig",
                                                      "med DiD", "lineages", "disputes"),
    ]
    for s in sel:
        lines.append("%-12s %8.3f %8.3f   %8.3f %8.3f   %+8.3f  %4d/%-4d  %4d/%-4d" % (
            s["word"], s["b_ind"], s["a_ind"], s["b_inst"], s["a_inst"], s["med"],
            s["lu"], s["ld"], s["du"], s["dd"]))
    lines += ["", "Lineages and disputes: counts with DiD > 0 / DiD < 0 (ties omitted). Shares are proportions (0.36 = 36%)."]
    save(p, "ci_word_did", W_IN, H_IN, "\n".join(lines))


# ────────────────────────────────────────────────────────── plate B, channel
LABEL = {"housing_repairs": "Repairs", "housing_rent": "Rent", "housing_deposit": "Deposit",
         "labor_credit": "Credit for work", "labor_safety": "Workplace safety",
         "labor_layoff": "Layoff", "labor_benefits_cut": "Benefits cut",
         "medical_bill": "Hospital bill", "medical_referral": "Referral refused",
         "police_search": "Police search", "benefits_denial": "Benefits denied",
         "civic_highway": "Highway demolition", "immigration_visa": "Visa refused",
         "consumer_charge": "Disputed charge", "banking_fee": "Bank fee",
         "utilities_bill": "Utility bill", "insurance_denial": "Insurance denied",
         "education_removal": "University removal"}


def channel_frame():
    """Recompute by_dispute.md's `channel` column, assert it, add a lineage bootstrap."""
    rows = [json.loads(l) for l in open(A.SRC)]
    rows = [r for r in rows if r.get("coded") and A.keep(r["coded"])]
    arms = collections.defaultdict(set)
    for r in rows:
        arms[r["lineage"]].add(r["arm"])
    rows = [r for r in rows if arms[r["lineage"]] == {"base", "aligned"}]
    design = json.load(open(os.path.join(HERE, "prompts", "design.json")))
    #: by_dispute.md's one table sits under an H1, so rows are picked by dispute id
    booked = {}
    for line in open(os.path.join(HERE, "results", "by_dispute.md")):
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) == 6 and c[1] in LABEL:
            booked[c[1]] = c[2]
    assert set(booked) == set(LABEL), "by_dispute.md rows %s" % sorted(set(LABEL) ^ set(booked))
    rng = np.random.default_rng(SEED)
    out = []
    for dom, ss in BD.DOM.items():
        for s in ss:
            c = collections.defaultdict(list)
            for r in rows:
                if r["scenario"] == s:
                    c[(r["lineage"], r["arm"], r["side"])].append(A.outcomes(r["coded"])["channel"])
            dd = []
            for l in sorted({k[0] for k in c}):
                v = [c.get((l, a, sd)) for a in ("base", "aligned") for sd in ("individual", "institution")]
                if all(v):
                    bi, bs, ai, as_ = (np.mean(x) for x in v)
                    dd.append((ai - bi) - (as_ - bs))
            dd = np.array(dd)
            got = "%+.2f (%d/%d)" % (dd.mean(), (dd > 0).sum(), (dd < 0).sum())
            assert booked[s].startswith(got), "by_dispute.md %s: booked %r, derived %r" % (s, booked[s], got)
            boots = dd[rng.integers(0, len(dd), size=(4000, len(dd)))].mean(axis=1)
            src = design["%s__individual" % s]["source"]
            out.append(dict(domain=dom, scenario=s, label=LABEL[s], mean=float(dd.mean()),
                            lo=float(np.percentile(boots, 2.5)), hi=float(np.percentile(boots, 97.5)),
                            n=len(dd), up=int((dd > 0).sum()), dn=int((dd < 0).sum()),
                            original=src.startswith("F21"), source=src,
                            prompt_ind=design["%s__individual" % s]["prompt"],
                            prompt_inst=design["%s__institution" % s]["prompt"]))
    assert len(out) == 18 and sum(o["original"] for o in out) == 6, "expected 18 disputes, 6 F21 originals"
    #: the README's named extremes, categorically
    by = {o["scenario"]: o for o in out}
    assert max(out, key=lambda o: o["mean"])["scenario"] in ("banking_fee", "education_removal")
    assert (by["education_removal"]["up"], by["education_removal"]["dn"]) == (22, 0)
    print("   by_dispute.md channel reproduced: 18 disputes, %s coded passages kept" % format(len(rows), ","))
    return out


def fig_channel():
    """Plate B: channel DiD per dispute with a lineage bootstrap, grouped by domain."""
    import matplotlib
    matplotlib.use("Agg")
    import pandas as pd
    from plotnine import (ggplot, aes, geom_segment, geom_point, geom_vline, facet_grid, labs,
                          scale_x_continuous, scale_y_continuous, scale_shape_manual,
                          scale_fill_manual, theme, element_text, element_blank, element_rect)
    out = channel_frame()
    F.check_halftones({"ink": F.PUB_INK, "zero": F.PUB_GRAY})
    d = pd.DataFrame(out)
    DOMS = list(BD.DOM)
    d["domain"] = pd.Categorical([x.capitalize() for x in d.domain],
                                 categories=[x.capitalize() for x in DOMS])
    #: within a domain, largest shift on top
    d["y"] = 0
    for dom, g in d.groupby("domain", observed=True):
        for k, i in enumerate(g.sort_values("mean").index):
            d.loc[i, "y"] = k + 1
    d["prompt"] = np.where(d.original, "F21 original prompt", "Rewritten prompt, not yet reviewed")
    d["prompt"] = pd.Categorical(d.prompt, categories=["F21 original prompt",
                                                       "Rewritten prompt, not yet reviewed"])
    fnt = F.pub_font()
    W_IN, H_IN = F.PUB_SIZE[0], 5.6
    lo = min(-0.1, float(d.lo.min()))
    hi = max(1.0, float(d.hi.max()))
    p = (ggplot(d, aes(y="y"))
         + geom_vline(xintercept=0, color=F.PUB_GRAY, size=F.PUB_RULE_PT)
         + geom_segment(aes(x="lo", xend="hi", yend="y"), color=F.PUB_INK, size=F.PUB_RULE_PT)
         + geom_point(aes(x="mean", shape="prompt", fill="prompt"), color=F.PUB_INK,
                      size=2.0, stroke=0.6)
         + facet_grid("domain ~ .", scales="free_y", space="free")
         + scale_shape_manual({"F21 original prompt": "o", "Rewritten prompt, not yet reviewed": "o"}, name="")
         + scale_fill_manual({"F21 original prompt": F.PUB_INK,
                              "Rewritten prompt, not yet reviewed": "#ffffff"}, name="")
         #: the left 0.62 of the x range holds the dispute names, drawn as text
         + scale_x_continuous(limits=(lo - 0.62, hi), breaks=[0, 0.25, 0.5, 0.75, 1.0])
         + scale_y_continuous(breaks=[], expand=(0, 0.7))   # names are geom_text, per facet
         + labs(x="Change in how often the individual, more than the institution,\n"
                  "is sent to the other side's own channel, base → aligned", y="")
         + F.pub_theme(height=H_IN, grid="none")
         + theme(figure_size=(W_IN, H_IN), legend_position="top", legend_direction="vertical",
                 plot_margin_right=0.03,
                 legend_title=element_blank(),
                 legend_text=element_text(family=fnt, size=F.PUB_FONT_PT),
                 legend_key=element_rect(fill="white", color="white"),
                 strip_text_y=element_text(family=fnt, size=F.PUB_FONT_PT, angle=0, ha="left"),
                 strip_background=element_blank(),
                 axis_ticks_major_y=element_blank()))
    #: y labels are per facet: a positional labeller cannot see its facet, so
    #: the dispute names are drawn from the data as text at the left margin.
    from plotnine import geom_text
    p = p + geom_text(aes(x=lo, y="y", label="label"), ha="right", nudge_x=-0.03,
                      size=F.PUB_FONT_PT, family=fnt)

    lines = [
        "PLATE B. Where the complaint is sent. The counterparty-channel shift, dispute by dispute.",
        "",
        "Marker: the mean over lineages of a per-lineage difference-in-differences, base model to aligned",
        "model: (aligned - base, individual) - (aligned - base, institution), where the outcome is the share",
        "of passages that recommend taking the matter to the COUNTERPARTY'S OWN side (its HR, billing office,",
        "management, internal affairs). Line: bootstrap 95%% interval over lineages (4,000 resamples, seed %d)." % SEED,
        "Filled marker: the dispute's prompts are F21 originals used verbatim. Open marker: rewritten from",
        "M03 by the malign seat and not yet reviewed (12 of 18 disputes, 24 of 36 prompts).",
        "",
        "Outcome coded by an LLM (deepseek-flash, one pass, blind to side, model and arm); one coder, no",
        "second-coder agreement yet. Passages kept: continuation or advice form, coherent, perspective kept;",
        "lineages with both arms. One prompt pair per dispute, so a dispute's value is partly its prompt.",
        "EXPLORATORY: domains are described, not tested. Producer by_dispute.py; table results/by_dispute.md.",
        "",
        "%-18s %-20s %6s  %-15s %8s  %-4s %s" % ("domain", "dispute", "mean", "95% CI", "+/-", "n", "prompt"),
    ]
    for o in out:
        lines.append("%-18s %-20s %+6.2f  [%+.2f, %+.2f] %4d/%-3d  %-4d %s" % (
            o["domain"], o["label"], o["mean"], o["lo"], o["hi"], o["up"], o["dn"], o["n"],
            "F21 original" if o["original"] else "rewrite, unreviewed"))
    lines += ["", "+/-: lineages with DiD > 0 / < 0; n: lineages with all four cells (ties are the rest).",
              "", "INDIVIDUAL-SIDE PROMPTS (the institution's mirror prompt in brackets):", ""]
    for o in out:
        lines.append("%s (%s; source: %s)" % (o["label"], o["scenario"], o["source"]))
        lines += textwrap.wrap('  "%s"' % o["prompt_ind"], 100, subsequent_indent="   ")
        lines += textwrap.wrap('  ["%s"]' % o["prompt_inst"], 100, subsequent_indent="   ")
    save(p, "ci_channel_by_dispute", W_IN, H_IN, "\n".join(lines))


FIGURES = {"words": fig_words, "channel": fig_channel}


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
