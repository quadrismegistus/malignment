"""Reference grid, not a figure draft: every version of valence, arousal and dominance over the arc_fiction history,
with the national-story arms. (RH, 2026-09-26: "Can you plot them all just for my reference")

    .venv/bin/python -u arc_vad_reference_grid.py           -> figures/arc_vad_reference_grid_v1.{png,pdf,caption.txt}
    .venv/bin/python -u arc_vad_reference_grid.py partial   -> figures/arc_vad_reference_grid_partial_v1.*
        (RH: "a new version of same fig that plots concreteness-partialed-out versions"): every panel's text scores
        minus a text-level OLS fit on concreteness (Abs-Conc.Median.median, uncorrected like the rest) over the
        1700-2009 novels, plus the mean; the arms adjusted with THAT history slope applied to their meta-texts'
        concreteness, so arm and history stay on one scale (the within-condition slope of the lineage tests
        answers a different question: whether the arms separate, not where they sit).

Rows: valence, arousal, dominance. Columns: the raw Warriner LOOKUP (human ratings, same scorer), and the
abstraction project's vector axes plain, orth, band, nnpair, wnpair (3013bcc). Recommended axis per row
(abstraction): valence plain, arousal nnpair, dominance nnpair -- marked * in the panel title.
History: vad_scores_arc_fiction.parquet, texts 1700-2009 (1600-2009 with `from1600`), decade medians (>= 3 texts), lowess 0.3. NOT corpus-bias
corrected, in every panel alike: coefficients exist only for the plain columns, and a grid mixing corrected and
uncorrected panels would compare unlike things. Arms: the no-demonym national stories (judged; one meta-text per
model-condition; median over lineages): base dotted, aligned raw dashed, chat prefilled dash-dot, chat asked
solid. Free y scale per panel: compare shapes and arm placement, not levels across panels. EXPLORATORY.
"""
import os, sys, textwrap

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
PARTIAL = "partial" in sys.argv[1:]                         # read before the argv rewrite below
#: from1600 (RH, 2026-09-26: "remake prev graphs adding back in c17 so history is year 1600+")
START = 1600 if "from1600" in sys.argv[1:] else 1700
sys.argv = [sys.argv[0], "v4", "meta", "sel12", "arms4"]
import arc_history_arms as H                               # noqa: E402
from malignment import figure as F                         # noqa: E402

SH = os.path.expanduser("~/malignment-data/interiority_norms")
OUT = os.path.join(HERE, "figures", "arc_vad_reference_grid" + ("_partial" if PARTIAL else "") + ("_1600" if START == 1600 else "") + "_v1")
CONC = "Abs-Conc.Median.median"
VERS = [("lookup", "human lookup"), ("", "plain"), ("_orth", "orth"), ("_band", "band"), ("_nnpair", "nnpair"), ("_wnpair", "wnpair")]
REC = {"Valence": "", "Arousal": "_nnpair", "Dominance": "_nnpair"}
ARMS = {"base": "Base models", "aligned_raw": "Aligned models", "aligned_prefill": "Aligned, chat, prefilled",
        "aligned_rettberg": "Aligned, chat, asked"}


def col(dim, v):
    return "Warriner-%s.lookup" % dim if v == "lookup" else "VAD-%s.Warriner%s.median" % (dim, v)


def main():
    from statsmodels.nonparametric.smoothers_lowess import lowess
    for ext in (".png", ".pdf", ".caption.txt"):
        assert not os.path.exists(OUT + ext), "refusing to overwrite " + OUT + ext
    V = pd.read_parquet(os.path.join(SH, "vad_scores_arc_fiction.parquet"))
    T = H.concreteness_texts()[["_id", "year"]].merge(V, on="_id", validate="1:1")
    T = T[T.year.between(START, 2009)]
    M = pd.read_parquet(os.path.join(H.DATA, "prompt_check_national_judged_meta_scored.parquet"))
    pts, cvs, arms, order, slopes = [], [], [], [], []
    for dim in ("Valence", "Arousal", "Dominance"):
        for v, lab in VERS:
            c = col(dim, v)
            name = "%s: %s%s" % (dim, lab, " *" if v == REC[dim] else "")
            order.append(name)
            d = T[["year", c, CONC]].dropna()
            y = d[c]
            if PARTIAL:
                b = float(np.polyfit(d[CONC], d[c], 1)[0])
                cm = float(d[CONC].mean())
                y = d[c] - b * (d[CONC] - cm)
                slopes.append("%s %+.3f" % (name.replace(" *", ""), b))
            h = H.decades(d.year, y)
            pts += [dict(panel=name, year=y, value=x) for y, x in zip(h.year, h.value)]
            cvs += [dict(panel=name, year=x, value=y) for x, y in lowess(h.value.values, h.year.values, frac=0.3, return_sorted=True)]
            if PARTIAL:
                adj = M[c] - b * (M[CONC] - cm)
                arms += [dict(panel=name, arm=ARMS[k], value=float(adj[M.cond == k].median())) for k in ARMS]
            else:
                arms += [dict(panel=name, arm=ARMS[k], value=float(M[M.cond == k][c].median())) for k in ARMS]
    P, C, A = pd.DataFrame(pts), pd.DataFrame(cvs), pd.DataFrame(arms)
    for df in (P, C, A):
        df["panel"] = pd.Categorical(df.panel, categories=order)
    A["arm"] = pd.Categorical(A.arm, categories=list(ARMS.values()))
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["pdf.fonttype"] = 42
    from plotnine import (ggplot, aes, geom_point, geom_line, geom_hline, facet_wrap, labs, scale_linetype_manual,
                          scale_x_continuous, theme, element_text)
    p = (ggplot()
         + geom_point(aes("year", "value"), data=P, color=F.PUB_GRAY, size=0.5)
         + geom_line(aes("year", "value"), data=C, color=F.PUB_INK, size=F.PUB_LINE_PT)
         + geom_hline(aes(yintercept="value", linetype="arm"), data=A, color=F.PUB_MID, size=F.PUB_RULE_PT * 1.2)
         + scale_linetype_manual(dict(zip(ARMS.values(), ["dotted", "dashed", "dashdot", "solid"])))
         + facet_wrap("~panel", ncol=6, scales="free_y")
         + scale_x_continuous(breaks=[1600, 1700, 1800, 1900, 2000] if START == 1600 else [1700, 1800, 1900, 2000])
         + labs(x="", y="Score, concreteness regressed out (own scale)" if PARTIAL else "Score (each panel on its own scale)", linetype="")
         + F.pub_theme(height=6.6)
         + theme(legend_position="bottom", figure_size=(13.0, 6.6),
                 strip_text=element_text(family=F.pub_font(), size=F.PUB_FONT_PT)))
    F.save(p, OUT + ".png")
    head = ("CONCRETENESS REGRESSED OUT (text-level OLS over the %d-2009 novels per panel; arms adjusted with the same "
            "slope). " % START) if PARTIAL else ""
    cap = textwrap.wrap(head + ("REFERENCE GRID: valence, arousal and dominance in English fiction %d-2000, every version -- the "
                                "human Warriner lookup and the vector axes plain, orth, band, nnpair, wnpair (* = recommended). "
                                "Decade medians over arc_fiction texts, lowess; not bias-corrected in any panel. Lines: the "
                                "national-story arms (judged no-demonym stories, median over lineages). Free y per panel. Working "
                                "reference, not a figure draft." % START), 110)
    if PARTIAL:
        cap += ["", "  slopes on concreteness: " + "; ".join(slopes)]
    open(OUT + ".caption.txt", "w").write("\n".join(cap) + "\n")
    print("\n".join(cap))


if __name__ == "__main__":
    main()
