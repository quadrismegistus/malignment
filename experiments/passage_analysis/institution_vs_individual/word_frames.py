"""Plate A's words across four conditions: base raw, aligned raw, aligned chat, API.

    python -u word_frames.py     -> results/word_frames.{csv,md}, figures/word_frames.png

EXPLORATORY (RH, 2026-09-24: "can we see them in base, aligned-raw, aligned-chat,
and API"). No LLM anywhere: passage text only, every passage unfiltered, the
share of passages CONTAINING the word, as `word_did.py` counts it.

WHICH WORDS: plate A's twelve, from `plot.word_frame()`, so the list is the
plate's own rule and cannot drift from it.

WHICH MODELS: the lineages with both arms in `coded_regen.jsonl`, less
`analyse_regen.BROKEN_LINEAGES` (internlm2: word salad in every cell), which is
42. The aligned-raw cell is malign's full run (`aligned_raw.md`, 459f6c97;
`run_araw.py`), so all three open conditions stand on the SAME 42 lineages and
the x axis changes nothing but the condition. (Until 2026-09-24 this used the
frame pilot's six lineages, the only ones that then had a raw cell.)

API: the four vendor models of `frontier_generate.py` (the prompt as the user
message, no system message, t=1.0, 256 tokens, 10 draws), pooled, and per model
in the table. It has no base, so it is an endpoint, and it is drawn unjoined.
"""
import collections, csv, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
for p in (HERE, REPO):
    if p not in sys.path:
        sys.path.insert(0, p)
import analyse_regen as A     # noqa: E402  SRC, BROKEN_LINEAGES
import word_did as W          # noqa: E402  TOK

FRONTIER = os.path.expanduser("~/malignment-data/institution_vs_individual/coded_frontier.jsonl")
ARAW = os.path.expanduser("~/malignment-data/institution_vs_individual/coded_aligned_raw.jsonl")
COND = ["Base, raw", "Aligned, raw", "Aligned, chat", "API"]
SIDES = ["individual", "institution"]
N_LINEAGES = 42


def lineages():
    """The 42: both arms in coded_regen, less the broken ones. Asserted, not assumed."""
    arms = collections.defaultdict(set)
    for r in map(json.loads, open(A.SRC)):
        arms[r["lineage"]].add(r["arm"])
    ls = sorted(l for l, a in arms.items() if a == {"base", "aligned"} and l not in A.BROKEN_LINEAGES)
    assert len(ls) == N_LINEAGES, "expected %d usable lineages, found %d" % (N_LINEAGES, len(ls))
    return ls


def passages():
    """(condition, unit, side, text) for every passage in the comparison."""
    ls = set(lineages())
    out = [("Base, raw" if r["arm"] == "base" else "Aligned, chat", r["lineage"], r["side"], r["text"])
           for r in map(json.loads, open(A.SRC)) if r["lineage"] in ls]
    raw = [r for r in map(json.loads, open(ARAW)) if r["lineage"] in ls]
    assert {r["lineage"] for r in raw} == ls, "aligned-raw is missing a lineage"
    out += [("Aligned, raw", r["lineage"], r["side"], r["text"]) for r in raw]
    out += [("API", r["model"], r["side"], r["text"]) for r in map(json.loads, open(FRONTIER))]
    return out


def all_data(words):
    """Pooled share per (condition, side), plus per (condition, side, unit). -> (share, n, units)"""
    n = collections.Counter()
    hit = collections.Counter()
    for c, u, s, t in passages():
        d = set(W.TOK.findall((t or "").lower()))
        for k in ((c, s), (c, s, u)):
            n[k] += 1
            for w in words:
                if w in d:
                    hit[k + (w,)] += 1
    share = {k: {w: hit[k + (w,)] / n[k] for w in words} for k in n}
    units = {c: len({k[2] for k in n if len(k) == 3 and k[0] == c}) for c in COND}
    assert units["Base, raw"] == units["Aligned, raw"] == units["Aligned, chat"] == N_LINEAGES, units
    return share, n, units


def main():
    import plot as PL          # plate A's selection rule
    sel, _meta = PL.word_frame()
    words = [s["word"] for s in sel]
    grp = {s["word"]: s["grp"] for s in sel}
    share, n, units = all_data(words)
    api_models = sorted({k[2] for k in n if len(k) == 3 and k[0] == "API"})

    out = [dict(word=w, group=grp[w], condition=c, side=s, share=share[(c, s)][w], n=n[(c, s)], units=units[c])
           for w in words for c in COND for s in SIDES]
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    with open(os.path.join(HERE, "results", "word_frames.csv"), "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(out[0]))
        wr.writeheader()
        wr.writerows(out)

    L = ["# Plate A's words by condition (EXPLORATORY)", "",
         "Producer `word_frames.py`. Share of passages containing the word, every passage unfiltered, "
         "individual / institution. Open models: the same %d lineages in all three conditions (%s passages "
         "per condition and side). API: %s, pooled (%s per side)." % (
             N_LINEAGES, format(n[("Base, raw", "individual")], ","), ", ".join(m.split("/")[-1] for m in api_models),
             format(n[("API", "individual")], ",")), "",
         "| word | base raw | aligned raw | aligned chat | API |", "|---|---|---|---|---|"]
    for w in words:
        L.append("| %s | %s |" % (w, " | ".join("%.3f / %.3f" % (share[(c, "individual")][w], share[(c, "institution")][w])
                                                for c in COND)))
    L += ["", "## API by model (individual / institution)", "",
          "| word | " + " | ".join(m.split("/")[-1] for m in api_models) + " |", "|---|" + "---|" * len(api_models)]
    for w in words:
        L.append("| %s | %s |" % (w, " | ".join("%.2f / %.2f" % (share[("API", "individual", m)][w],
                                                                    share[("API", "institution", m)][w])
                                                   for m in api_models)))
    open(os.path.join(HERE, "results", "word_frames.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L[:len(words) + 6]))
    draw(out, words)


def draw(out, words):
    import textwrap
    import matplotlib
    matplotlib.use("Agg")
    import pandas as pd
    from plotnine import (ggplot, aes, geom_line, geom_point, facet_wrap, labs, scale_color_manual,
                          scale_x_discrete, scale_y_continuous, theme_minimal, theme, element_text,
                          element_blank)
    d = pd.DataFrame(out)
    d["pct"] = 100 * d.share
    d["side"] = d.side.map({"individual": "The aggrieved individual", "institution": "The institution"})
    d["word"] = pd.Categorical(d.word, categories=words)
    d["condition"] = pd.Categorical(d.condition, categories=COND)
    p = (ggplot(d, aes("condition", "pct", color="side"))
         + geom_line(aes(group="side"), data=d[d.condition != "API"], size=0.8)
         + geom_point(size=1.8)
         + facet_wrap("~word", ncol=4, scales="free_y")
         + scale_color_manual({"The aggrieved individual": "#000000", "The institution": "#9a9a9a"}, name="")
         + scale_x_discrete(labels=["Base\nraw", "Aligned\nraw", "Aligned\nchat", "API"])
         + scale_y_continuous(labels=lambda v: ["%g%%" % x for x in v])
         + labs(x="", y="Passages containing the word",
                title="Plate A's words: base, aligned without chat, aligned in chat, and the API models",
                subtitle="\n".join(textwrap.wrap(
                    "Open models: the same %d lineages in all three conditions. API: Sonnet 4.6, Haiku 4.5, "
                    "GPT-4o-mini, DeepSeek v4, pooled, drawn unjoined because it has no base. Each panel has its "
                    "own y scale. Base to aligned raw is the weights; aligned raw to chat is the frame. Exploratory."
                    % N_LINEAGES, 150)))
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
