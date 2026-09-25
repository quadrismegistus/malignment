"""Interiority over arc_fiction with the vetted lists, drawn as Figure 5 draws its history. (RH, 2026-09-25)

    .venv/bin/python -u arc_interiority_fig5.py      -> figures/arc_interiority_vetted_lowess.{png,pdf,caption.txt}
    .venv/bin/python -u arc_interiority_fig5.py v2   -> ..._lowess_v2.*: RH, the lists are "cognitive (and emotional)
        language", not interiority as the coder reads it; vetted clean X's tokens are 68% cognition, the vetted
        candidates' 67% emotion (kind of each form's base word, INTERIORITY_VETTING.md), so the panels say so

Figure 5's recipe (literary_history.decades / smooth, literary_history_v2.panel): per decade the MEDIAN
over texts, decades with fewer than 3 texts dropped, gray points, a black lowess at span 0.3, thin
century lines. Here the texts are the book's arc_fiction set pooled over every source (no split into
transcribed / OCR / modern), from arc_interiority_precision.py --vetted's per-text counts: share of
alphabetic non-stopword tokens on the list, texts with at least 2,000 such tokens (arc_interiority's
floor), 1600-2009. No model arms: model prose has not been counted under this rule.
"""
import os, sys, textwrap

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, REPO)
from malignment import figure as F                              # noqa: E402

DATA = os.path.join(os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data")), "novel_arc")
SRC = os.path.join(DATA, "arc_interiority_texts_precision_vetted.parquet")
V2 = "v2" in sys.argv[1:]
OUT = os.path.join(HERE, "figures", "arc_interiority_vetted_lowess" + ("_v2" if V2 else ""))
MIN_CONTENT, MIN_DECADE = 2000, 3
PANELS = (("n_cleanx_p", "Interiority in fiction: clean X, vetted", "Interiority\n(word list frequency)"),
          ("n_comb_p", "Clean X + period candidates, vetted", "Interiority\n(word list frequency)"))
if V2:
    PANELS = (("n_cleanx_p", "Cognitive language in fiction", "Cognitive words\n(share of words)"),
              ("n_comb_p", "Cognitive and emotional language in fiction", "Cognitive + emotional\n(share of words)"))


def decades(T, col):
    rows = []
    for yr in range(1600, 2010, 10):
        t = T[(T.year >= yr) & (T.year < yr + 10)]
        if len(t) >= MIN_DECADE:
            rows.append({"year": yr + 5, "value": float((t[col] / t.n_content).median()), "n": len(t)})
    return pd.DataFrame(rows)


def smooth(h):
    from statsmodels.nonparametric.smoothers_lowess import lowess
    return lowess(h.value.values, h.year.values, frac=0.3, return_sorted=True)


def panel(h, curve, title, ylab, show_x):
    from plotnine import (ggplot, aes, geom_point, geom_line, geom_vline, labs, scale_x_continuous,
                          scale_y_continuous, theme, element_text)
    fnt = F.pub_font()
    cv = pd.DataFrame(curve, columns=["year", "value"])
    return (ggplot()
            + geom_vline(xintercept=[1700, 1800, 1900], color="#e9ecef", size=F.PUB_RULE_PT)
            + geom_point(aes("year", "value"), data=h, color=F.PUB_GRAY, size=0.9)
            + geom_line(aes("year", "value"), data=cv, color=F.PUB_INK, size=F.PUB_LINE_PT)
            + scale_y_continuous(labels=lambda v: ["%g%%" % round(100 * x, 6) for x in v])
            + scale_x_continuous(limits=(1595, 2010), breaks=list(range(1600, 2001, 50)), expand=(0, 0),
                                 labels=(lambda v: ["%d" % x for x in v]) if show_x else (lambda v: [""] * len(v)))
            + labs(x="", y=ylab, title=title)
            + F.pub_theme(grid="y")
            + theme(axis_title_y=element_text(family=fnt, size=F.PUB_FONT_PT),
                    plot_title=element_text(family=fnt, size=F.PUB_FONT_PT, weight="bold", ha="left")))


def main():
    for ext in (".png", ".pdf", ".caption.txt"):
        assert not os.path.exists(OUT + ext), "refusing to overwrite " + OUT + ext
    F.check_halftones({"history": F.PUB_INK, "points": F.PUB_GRAY})
    T = pd.read_parquet(SRC)
    assert len(T) == 82080, len(T)
    T = T[(T.n_content >= MIN_CONTENT) & T.year.between(1600, 2009)]
    #: the population ARC_INTERIORITY_PRECISION_VETTED.md reports
    assert len(T) == 75974, len(T)
    H = {col: decades(T, col) for col, _, _ in PANELS}
    C = {col: smooth(h) for col, h in H.items()}
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["pdf.fonttype"] = 42
    from plotnine.composition import Stack
    ps = [panel(H[col], C[col], t, yl, i == len(PANELS) - 1) for i, (col, t, yl) in enumerate(PANELS)]
    fig = Stack(ps).draw()
    fig.set_size_inches(F.PUB_SIZE[0], 4.2)
    fig.savefig(OUT + ".png", dpi=300)
    fig.savefig(OUT + ".pdf")
    h = H["n_cleanx_p"]
    wrap = lambda s: textwrap.wrap(s, 100)
    L = wrap(("COGNITIVE AND EMOTIONAL LANGUAGE IN FICTION, 1600-2000" if V2 else
              "INTERIORITY IN FICTION, 1600-2000, with the vetted interiority word lists") +
             ", drawn as Figure 5 draws its history.") + [""] + wrap(
        "Gray points: per decade, the median over texts of the share of a text's alphabetic non-stopword tokens "
        "that are on the list; black line: their lowess smooth (span 0.3). Texts: the book's arc_fiction set "
        "(abstraction.scores_rep, deduplicated), every source pooled, counted from lltk.text_freqs as surface "
        "forms with MorphAdorner and long-s spelling variants of kept words; %s texts with at least %s such tokens; "
        "decades under %d texts dropped. Top: clean X, the USAS X words an LLM rater kept as interior under a "
        "precision-first rule, then hand-vetted (872 base words). Bottom: the same plus the period-model candidates "
        "that passed the same rating and vetting (1,949 base words). No model arms: model prose has not been counted "
        "under this rule." % (format(len(T), ","), format(MIN_CONTENT, ","), MIN_DECADE) + (
        " By token mass the top list is 68% cognition words (10% emotion, 10% volition, 8% perception); the "
        "candidates it adds are 67% emotion." if V2 else "")) + ["",
        "  texts per decade: " + ", ".join("%d:%d" % (r.year - 5, r.n) for r in h.itertuples())]
    open(OUT + ".caption.txt", "w").write("\n".join(L) + "\n")
    print("\n".join(L))
    for col, h in H.items():
        print(col, "decades %d, median range %.2f%%-%.2f%%" % (len(h), 100 * h.value.min(), 100 * h.value.max()))


if __name__ == "__main__":
    main()
