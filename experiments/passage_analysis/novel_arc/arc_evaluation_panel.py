"""Evaluative word share alone, Figure 5 style, with RH's arm labels. (RH, 2026-09-26: "the strongest panel is Evaluative
word share"; labels "Base models / Aligned models (raw) / Aligned models (prefilled) / Aligned models (chat)")

    .venv/bin/python -u arc_evaluation_panel.py   -> figures/arc_evaluation_share_v1.{png,pdf,caption.txt}

The top panel of arc_evaluation_reference.py, unchanged in data: evaluative (positive + negative) words per content word
from the symmetric cleaned lexicon; Chadwyck and Chicago novels, decade medians, lowess 0.3; national-story arms, one
meta-text per model-condition, median over lineages. "chat" is the condition prompted "Write a 1500 word potential
story." in the model's chat template. EXPLORATORY.
"""
import os, sys, textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.argv = [sys.argv[0], "v2"]
import arc_valence_clean_components as V                   # noqa: E402
H, F = V.H, V.F

OUT = os.path.join(HERE, "figures", "arc_evaluation_share_v1")
LEX = "+vector"
NAME = {"base": "Base models", "raw": "Aligned models (raw)", "prefill": "Aligned models (prefilled)", "continue": "Aligned models (chat)"}


def label_positions(vals, gap):
    """Labels in value order, spaced by >= gap, each cluster CENTRED on its lines' mean (so no label sits beside a
    neighbour's line, as the generic spreader let happen)."""
    order = sorted(vals, key=vals.get)
    groups = [[order[0]]]
    for k in order[1:]:
        if vals[k] - vals[groups[-1][-1]] < gap:
            groups[-1].append(k)
        else:
            groups.append([k])
    pos = {}
    for g in groups:
        c = sum(vals[k] for k in g) / len(g)
        for i, k in enumerate(g):
            pos[k] = c + (i - (len(g) - 1) / 2) * gap
    return pos


def panel(hist, curve, arms):
    import pandas as pd
    from plotnine import (ggplot, aes, geom_point, geom_line, geom_segment, geom_text, geom_vline, labs,
                          scale_x_continuous, scale_y_continuous, scale_linetype_manual, theme, element_text)
    fnt = F.pub_font()
    cv = pd.DataFrame(curve, columns=["year", "value"])
    A = pd.DataFrame([{"arm": NAME[k], "value": v} for k, v in arms.items()])
    lo = min(cv.value.min(), hist.value.min(), A.value.min()); hi = max(cv.value.max(), hist.value.max(), A.value.max())
    pos = label_positions({NAME[k]: v for k, v in arms.items()}, 0.075 * (hi - lo))
    A["ly"] = A.arm.map(pos)
    X0, X1, XL, XMAX = 1600, 2005, 2040, 2325   # "Aligned models (prefilled)" at 9 pt ended ~12 px inside 2290
    return (ggplot()
            + geom_vline(xintercept=[1700, 1800, 1900], color="#e9ecef", size=F.PUB_RULE_PT)
            + geom_point(aes("year", "value"), data=hist, color=F.PUB_GRAY, size=0.9)
            + geom_line(aes("year", "value"), data=cv, color=F.PUB_INK, size=F.PUB_LINE_PT)
            + geom_segment(aes(x=X0, xend=X1, y="value", yend="value", linetype="arm"), data=A, color=F.PUB_MID, size=F.PUB_RULE_PT * 1.4)
            #: leaders from each line's end to its label, so the pairing is drawn rather than inferred
            + geom_segment(aes(x=X1, xend=XL - 4, y="value", yend="ly"), data=A, color=F.PUB_MID, size=F.PUB_RULE_PT * 0.8)
            + geom_text(aes(x=XL, y="ly", label="arm"), data=A, ha="left", va="center", size=F.PUB_FONT_PT, family=fnt, color=F.PUB_INK)
            + scale_linetype_manual({NAME["base"]: "dotted", NAME["raw"]: "dashed", NAME["prefill"]: "dashdot", NAME["continue"]: "solid"}, guide=None)
            + scale_y_continuous(labels=lambda v: ["%g%%" % round(100 * x, 6) for x in v])
            + scale_x_continuous(limits=(X0 - 5, XMAX), breaks=[1600, 1700, 1800, 1900, 2000], expand=(0, 0))
            + labs(x="", y="Evaluative words\n(per content word)", title="Evaluative words in fiction")
            + F.pub_theme(grid="y")
            + theme(axis_title_y=element_text(family=fnt, size=F.PUB_FONT_PT),
                    plot_title=element_text(family=fnt, size=F.PUB_FONT_PT, weight="bold", ha="left")))


def main():
    for ext in (".png", ".pdf", ".caption.txt"):
        assert not os.path.exists(OUT + ext), "refusing to overwrite " + OUT + ext
    L = V.lexicons()
    Th = V.history(L).merge(H.concreteness_texts()[["_id", "year"]], on="_id")
    Th = Th[(Th.lexicon == LEX) & Th.year.between(1600, 2009) & (Th.n_content >= H.MIN_CONTENT)]
    Mm = V.meta(L)
    Mm = Mm[Mm.lexicon == LEX]
    med = Mm.pivot_table(index="lineage", columns="cond", values="eval_rate").median()
    cond = {"base": "base", "raw": "aligned_raw", "prefill": "aligned_prefill", "continue": "aligned_rettberg"}
    arms = {k: float(med[c]) for k, c in cond.items()}
    #: RH's labels live in this file's NAME only; arc_history_arms.NAME stays as every other plate uses it
    h = H.decades(Th.year, Th.eval_rate)
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["pdf.fonttype"] = 42
    p = panel(h, H.smooth(h), arms)
    fig = p.draw()
    fig.set_size_inches(F.PUB_SIZE[0], 2.9)
    fig.savefig(OUT + ".png", dpi=300)
    fig.savefig(OUT + ".pdf")
    cap = textwrap.wrap(
        "EVALUATIVE WORDS IN FICTION, 1600-2000. Per text, words of clear positive or negative valence per content word, "
        "from a cleaned valence lexicon (Warriner et al. 2013 lemmas and forms kept under an ambiguity standard, plus "
        "period vocabulary proposed by a Warriner-seeded vector norm and confirmed by an LLM rater; positive above 6, "
        "negative below 4 on Warriner's 1-9 scale). Gray points: decade medians over %s Chadwyck and Chicago novels; black "
        "line: lowess (span 0.3). Lines: model fiction, national stories from a neutral prompt (judged proper stories), "
        "each model-condition as one text, median over %d lineages -- base models; aligned models given the raw prompt; "
        "aligned models in their chat template with the reply prefilled; aligned models asked in chat to write the story."
        % (format(Th._id.nunique(), ","), Mm.lineage.nunique()), 100) + ["", "  arms: " + ", ".join("%s %.4f" % (NAME[k], v) for k, v in arms.items())]
    open(OUT + ".caption.txt", "w").write("\n".join(cap) + "\n")
    print("\n".join(cap))


if __name__ == "__main__":
    main()
