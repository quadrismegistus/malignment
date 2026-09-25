"""Cognitive and emotional language with concreteness regressed out: a diagnostic, not a replacement. (RH, 2026-09-25)

    .venv/bin/python -u arc_history_resid.py   -> figures/arc_history_resid_v3.{png,pdf,caption.txt}

QUESTION (RH: "does it make sense to try residualizing cognitive and emotion away from tracking
concreteness? not as replacement, just curious"). Concreteness bottoms out near 1770 where both word
lists peak. Is each list's history more than the mirror of concreteness?

METHOD. Over the texts carrying both measures (arc_history_arms.py v3 counts and concreteness, same
floors), one OLS per list across TEXTS: share = a + b * concreteness. The adjusted share of a text is its
residual plus the list's mean share, so the axis stays in percent. Drawn as the history is: decade median
over texts, lowess 0.3. Model passages get the SAME fitted b (the history's, not their own):
adjusted = share - b * (conc - mean text conc), then per model the median, then the median over lineages.

A CAVEAT THAT IS PART OF THE ANSWER. The concreteness score is a mean over a text's content words' norms,
and the cognitive and emotional words are among the most abstract content words, so part of the
correlation is built in: a text with more of them scores lower on concreteness by that fact alone. The
residual therefore removes some of the lists' own signal along with the shared history. A cleaner test
would score concreteness without the list words; scores_rep does not carry that. EXPLORATORY.
"""
import json, os, sys, textwrap

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.argv = [sys.argv[0], "v3"] + sys.argv[1:]          # arc_history_arms reads its version at import
import arc_history_arms as H                           # noqa: E402
from malignment import figure as F                     # noqa: E402

OUT = os.path.join(HERE, "figures", "arc_history_resid_v3")


def main():
    for ext in (".png", ".pdf", ".caption.txt"):
        assert not os.path.exists(OUT + ext), "refusing to overwrite " + OUT + ext
    assert H.V3
    from scipy.stats import spearmanr
    C = H.concreteness_texts()[["_id", "conc_corr"]]
    T = pd.read_parquet(H.COUNTS)
    T = T[(T.n_content >= H.MIN_CONTENT) & T.year.between(1600, 2009)].merge(C, on="_id", how="inner")
    T = T[T.conc_corr.notna()]
    A = pd.read_parquet(H.ARM_OUT)
    fits, hist, arms, stats = {}, {}, {}, {}
    for k, col in (("cog", H.COG_COL), ("emo", H.EMO_COL)):
        y = T[col] / T.n_content
        b, a = np.polyfit(T.conc_corr, y, 1)
        adj = y - b * (T.conc_corr - T.conc_corr.mean())
        hist[k] = H.decades(T.year, adj)
        raw = H.decades(T.year, y)
        ca = A.dropna(subset=["conc", k]).copy()
        ca["adj"] = ca[k] - b * (ca.conc - T.conc_corr.mean())
        per = ca.groupby(["base", "arm"]).adj.median().unstack()
        arms[k] = {x: float(per[x].median()) for x in ("base", "raw")}
        dconc = H.decades(T.year, T.conc_corr)
        stats[k] = dict(slope=float(b), r_text=float(np.corrcoef(T.conc_corr, y)[0, 1]),
                        rho_decade_raw_conc=float(spearmanr(raw.value, dconc.value)[0]),
                        rho_decade_adj_conc=float(spearmanr(hist[k].value, dconc.value)[0]),
                        rho_decade_raw_adj=float(spearmanr(raw.value, hist[k].value)[0]))
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["pdf.fonttype"] = 42
    from plotnine.composition import Stack
    ps = [H.panel(hist["cog"], H.smooth(hist["cog"]), arms["cog"], "Cognitive language, concreteness regressed out",
                  "Cognitive words,\nadjusted (share)", False, True),
          H.panel(hist["emo"], H.smooth(hist["emo"]), arms["emo"], "Emotional language, concreteness regressed out",
                  "Emotional words,\nadjusted (share)", True, True)]
    fig = Stack(ps).draw()
    fig.set_size_inches(F.PUB_SIZE[0], 4.2)
    fig.savefig(OUT + ".png", dpi=300)
    fig.savefig(OUT + ".pdf")
    wrap = lambda s: textwrap.wrap(s, 100)
    L = wrap("COGNITIVE AND EMOTIONAL LANGUAGE WITH CONCRETENESS REGRESSED OUT (diagnostic; v3 lists).") + [""] + wrap(
        "Per text, the list share minus what a linear fit on the text's concreteness predicts, plus the list's mean "
        "share; one fit per list over %s arc_fiction texts carrying both measures. Gray points: decade medians; black "
        "line: lowess (span 0.3). Model arms adjusted with the history's slope, then per model the median over "
        "coherent narrative passages and the median over %d lineages. Part of the text-level correlation is "
        "mechanical: the list words are abstract content words and enter the concreteness mean themselves, so the "
        "adjustment removes some of the lists' own signal." % (format(len(T), ","), A.base.nunique())) + [""] + [
        "  %s: slope %.4f per concreteness unit, text-level r %.3f; decade rho with concreteness raw %.2f, adjusted "
        "%.2f; decade rho raw vs adjusted %.2f; arms adjusted %s" % (
            k, s["slope"], s["r_text"], s["rho_decade_raw_conc"], s["rho_decade_adj_conc"], s["rho_decade_raw_adj"],
            {x: round(100 * v, 2) for x, v in arms[k].items()}) for k, s in stats.items()]
    open(OUT + ".caption.txt", "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
