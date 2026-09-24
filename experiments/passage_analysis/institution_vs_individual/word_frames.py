"""Plate A's words across four conditions: base raw, aligned raw, aligned chat, API.

    python -u word_frames.py     -> results/word_frames.{csv,md}, figures/word_frames.png

EXPLORATORY (RH, 2026-09-24: "can we see them in base, aligned-raw, aligned-chat,
and API"). No LLM anywhere: passage text only, every passage unfiltered, the
share of passages CONTAINING the word, as `word_did.py` counts it.

WHICH WORDS: plate A's twelve, taken from `plot.word_frame()` so the list is the
plate's own rule and cannot drift from it.

WHICH MODELS, AND WHY ONLY SIX: aligned-raw exists only for the models the first
fleet accidentally ran raw (`frame_pilot.md`). Six of them also have a chat
cell. Comparing base, raw and chat on DIFFERENT model sets would put a
population change on the x axis, so the three open conditions use those six
lineages and nothing else. The 43-lineage base and chat shares (plate A's own
numbers) are in the table for reference, not on the figure.

API: the four vendor models of `frontier_generate.py` (the prompt as the user
message, no system message, t=1.0, 256 tokens, 10 draws), pooled, and per model
in the table. It has no base, so it is an endpoint, and it is drawn unjoined.
"""
import collections, csv, json, os, sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
for p in (HERE, REPO):
    if p not in sys.path:
        sys.path.insert(0, p)
import analyse_regen as A     # noqa: E402  SRC
import frame_pilot as FP      # noqa: E402  OUT, EIGHT, NO_CHAT
import plot as PL             # noqa: E402  word_frame (the plate's selection)
import word_did as W          # noqa: E402  TOK

FRONTIER = os.path.expanduser("~/malignment-data/institution_vs_individual/coded_frontier.jsonl")
COND = ["Base, raw", "Aligned, raw", "Aligned, chat", "API"]
SIDES = ["individual", "institution"]


def load():
    main = [json.loads(l) for l in open(A.SRC)]
    pilot = [json.loads(l) for l in open(FP.OUT)]
    api = [json.loads(l) for l in open(FRONTIER)]
    three = sorted({r["lineage"] for r in pilot if r["model"].split("/")[-1] not in FP.NO_CHAT})
    assert len(three) == 6, three
    arms = collections.defaultdict(set)
    for r in main:
        arms[r["lineage"]].add(r["arm"])
    both = {l for l, a in arms.items() if a == {"base", "aligned"}}
    assert set(three) <= both, "a pilot lineage lacks a base or chat arm in coded_regen"
    rows = []
    for r in main:
        if r["lineage"] in three:
            rows.append(("six", "Base, raw" if r["arm"] == "base" else "Aligned, chat", r["lineage"], r["side"], r["text"]))
        if r["lineage"] in both:
            rows.append(("all43", "Base, raw" if r["arm"] == "base" else "Aligned, chat", r["lineage"], r["side"], r["text"]))
    for r in pilot:
        if r["lineage"] in three:
            rows.append(("six", "Aligned, raw", r["lineage"], r["side"], r["text"]))
    for r in api:
        rows.append(("api", "API", r["model"], r["side"], r["text"]))
    return rows, three, len(both)


def main():
    sel, _meta = PL.word_frame()
    words = [s["word"] for s in sel]
    grp = {s["word"]: s["grp"] for s in sel}
    rows, three, n43 = load()
    #: name a lineage by its ALIGNED model: "pythia-2.8b" says nothing about archangel
    ALN = {json.loads(l)["lineage"]: json.loads(l)["model"].split("/")[-1] for l in open(FP.OUT)}
    toks = [set(W.TOK.findall((t or "").lower())) for *_x, t in rows]
    n = collections.Counter()
    hit = collections.Counter()
    for (pop, cond, unit, side, _t), d in zip(rows, toks):
        for key in ((pop, cond, side), (pop, cond, side, unit)):
            n[key] += 1
            for w in words:
                if w in d:
                    hit[key + (w,)] += 1
    #: every open cell of the six-lineage comparison holds 6 x 180 passages
    for c in COND[:3]:
        for s in SIDES:
            assert n[("six", c, s)] == 6 * 180, (c, s, n[("six", c, s)])
    share = lambda k, w: hit[k + (w,)] / n[k]

    out = []
    for w in words:
        for c in COND:
            pop = "api" if c == "API" else "six"
            for s in SIDES:
                out.append(dict(word=w, group=grp[w], condition=c, side=s,
                                share=share((pop, c, s), w), n=n[(pop, c, s)]))
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    with open(os.path.join(HERE, "results", "word_frames.csv"), "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(out[0]))
        wr.writeheader()
        wr.writerows(out)

    api_models = sorted({u for (pop, _c, _s, *rest) in n if pop == "api" for u in rest[:1]} - {None})
    L = ["# Plate A's words by condition (EXPLORATORY)", "",
         "Producer `word_frames.py`. Share of passages containing the word, every passage unfiltered, "
         "individual / institution. Open models: the six lineages with base-raw, aligned-raw and aligned-chat "
         "cells (%s). API: %s, pooled." % (", ".join(ALN[l] for l in three),
                                           ", ".join(m.split("/")[-1] for m in api_models)), "",
         "| word | base raw (6) | aligned raw (6) | aligned chat (6) | API (4) | base raw (all %d) | aligned chat (all %d) |" % (n43, n43),
         "|---|---|---|---|---|---|---|"]
    for w in words:
        cells = []
        for pop, c in (("six", "Base, raw"), ("six", "Aligned, raw"), ("six", "Aligned, chat"), ("api", "API"),
                       ("all43", "Base, raw"), ("all43", "Aligned, chat")):
            cells.append("%.2f / %.2f" % (share((pop, c, "individual"), w), share((pop, c, "institution"), w)))
        L.append("| %s | %s |" % (w, " | ".join(cells)))
    L += ["", "## API by model (individual / institution)", "",
          "| word | " + " | ".join(m.split("/")[-1] for m in api_models) + " |", "|---|" + "---|" * len(api_models)]
    for w in words:
        L.append("| %s | %s |" % (w, " | ".join("%.2f / %.2f" % (share(("api", "API", "individual", m), w),
                                                                    share(("api", "API", "institution", m), w))
                                                   for m in api_models)))
    L += ["", "## Per lineage, the six (individual / institution)", "",
          "| word | lineage | base raw | aligned raw | aligned chat |", "|---|---|---|---|---|"]
    for w in words:
        for l in three:
            L.append("| %s | %s | %s |" % (w, ALN[l], " | ".join(
                "%.2f / %.2f" % (share(("six", c, "individual", l), w), share(("six", c, "institution", l), w))
                for c in COND[:3])))
    open(os.path.join(HERE, "results", "word_frames.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L[:len(words) + 6]))
    draw(out, words, [ALN[l] for l in three])


def draw(out, words, names):
    import matplotlib
    matplotlib.use("Agg")
    import pandas as pd
    import textwrap
    from plotnine import (ggplot, aes, geom_line, geom_point, facet_wrap, labs, scale_color_manual,
                          scale_x_discrete, scale_y_continuous, theme_minimal, theme, element_text,
                          element_blank)
    d = pd.DataFrame(out)
    d["pct"] = 100 * d.share
    d["side"] = d.side.map({"individual": "The aggrieved individual", "institution": "The institution"})
    d["word"] = pd.Categorical(d.word, categories=words)
    d["condition"] = pd.Categorical(d.condition, categories=COND)
    openc = d[d.condition != "API"]
    p = (ggplot(d, aes("condition", "pct", color="side"))
         + geom_line(aes(group="side"), data=openc, size=0.8)
         + geom_point(size=1.8)
         + facet_wrap("~word", ncol=4, scales="free_y")
         + scale_color_manual({"The aggrieved individual": "#000000", "The institution": "#9a9a9a"}, name="")
         + scale_x_discrete(labels=["Base\nraw", "Aligned\nraw", "Aligned\nchat", "API"])
         + scale_y_continuous(labels=lambda v: ["%g%%" % x for x in v])
         + labs(x="", y="Passages containing the word",
                title="Plate A's words: base, aligned without chat, aligned in chat, and the API models",
                #: WRAPPED: the first render cut this line at the canvas edge
                subtitle="\n".join(textwrap.wrap(
                    "Open models: the six lineages that have all three conditions, named by their aligned "
                    "model (%s). API: Sonnet 4.6, Haiku 4.5, GPT-4o-mini, DeepSeek v4, pooled, drawn "
                    "unjoined because it has no base. Each panel has its own y scale. Base to aligned raw "
                    "is the weights; aligned raw to chat is the frame. Exploratory; six atypical lineages."
                    % ", ".join(names), 150)))
         + theme_minimal(base_size=9)
         + theme(figure_size=(11, 8), legend_position="top", legend_title=element_blank(),
                 plot_title=element_text(size=11, weight="bold", ha="left"),
                 plot_subtitle=element_text(size=8, color="#555555", ha="left"),
                 strip_text=element_text(size=9, weight="bold")))
    path = os.path.join(HERE, "figures", "word_frames.png")
    p.save(path, dpi=300, verbose=False)
    print("  ->", os.path.relpath(path, HERE))


if __name__ == "__main__":
    main()
