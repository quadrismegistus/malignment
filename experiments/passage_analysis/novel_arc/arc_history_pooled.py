"""Cognitive and emotional language POOLED, as drawn and with concreteness regressed out. (RH, 2026-09-25)

    .venv/bin/python -u arc_history_pooled.py   -> figures/arc_history_pooled_v4.{png,pdf,caption.txt}

RH: "Can we try Cognitive + Emotional pooled, one facet for normal, one facet for residualized -- the
non-residual ones in arc_history_three_arms_v4 are similar enough to pool." Under the v4 lists they are:
decade series rho +0.64 over 1600-2009 (+0.79 before 1800, +0.36 after). Under v2, without volition in the
cognitive list, they had diverged after 1800 (-0.56), which is why pooling waited for v4.

A text's POOLED share: (cognitive + emotional list tokens) / content tokens, v4 lists (arc_history_arms.py
v4; the lists are disjoint, so the sum counts no token twice). Top: as drawn. Bottom: one OLS across texts
of the pooled share on concreteness (the book's Abs-Conc.Median.median, bias-corrected), residual plus the
mean share, as arc_history_resid.py does per list. Figure 5's recipe for both: decade median over texts,
lowess 0.3. Arms: TEMPLATE_ARM, per passage cognitive + emotional share (bottom: adjusted with the
HISTORY's slope), per model the median over passages, then the median over lineages -- Figure 5's
statistic. The residual caveat carries over: the list words are abstract content words and enter the
concreteness mean themselves, so part of the fitted slope is mechanical. EXPLORATORY.
"""
import os, sys, textwrap

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.argv = [sys.argv[0], "v4"]                         # arc_history_arms reads its version at import
import arc_history_arms as H                           # noqa: E402
from malignment import figure as F                     # noqa: E402

OUT = os.path.join(HERE, "figures", "arc_history_pooled_v4")


def main():
    from scipy.stats import spearmanr
    for ext in (".png", ".pdf", ".caption.txt"):
        assert not os.path.exists(OUT + ext), "refusing to overwrite " + OUT + ext
    assert H.V4 and not H.PAST
    C = H.concreteness_texts()[["_id", "conc_corr"]]
    T = pd.read_parquet(H.COUNTS)
    T = T[(T.n_content >= H.MIN_CONTENT) & T.year.between(1600, 2009)]
    assert len(T) == 75974, len(T)                     # the population every v4 panel draws
    T["share"] = (T.n_cog + T.n_emo) / T.n_content
    raw = H.decades(T.year, T.share)
    Tc = T.merge(C, on="_id", how="inner")
    Tc = Tc[Tc.conc_corr.notna()]
    b, a = np.polyfit(Tc.conc_corr, Tc.share, 1)
    cm = Tc.conc_corr.mean()
    adj = H.decades(Tc.year, Tc.share - b * (Tc.conc_corr - cm))
    A = pd.read_parquet(H.ARM_OUT)
    A["share"] = A.cog + A.emo
    arms_raw = {x: v for x, v in (lambda per: {x: float(per[x].median()) for x in ("base", "raw")})(
        A.groupby(["base", "arm"]).share.median().unstack()).items()}
    Ac = A.dropna(subset=["conc", "share"]).assign(adj=lambda d: d.share - b * (d.conc - cm))
    per = Ac.groupby(["base", "arm"]).adj.median().unstack()
    arms_adj = {x: float(per[x].median()) for x in ("base", "raw")}
    dconc = H.decades(Tc.year, Tc.conc_corr)
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["pdf.fonttype"] = 42
    from plotnine.composition import Stack
    ps = [H.panel(raw, H.smooth(raw), arms_raw, "Cognitive and emotional language in fiction",
                  "Cognitive + emotional\n(share of words)", False, True),
          H.panel(adj, H.smooth(adj), arms_adj, "The same, concreteness regressed out",
                  "Cognitive + emotional,\nadjusted (share)", True, True)]
    fig = Stack(ps).draw()
    fig.set_size_inches(F.PUB_SIZE[0], 4.2)
    fig.savefig(OUT + ".png", dpi=300)
    fig.savefig(OUT + ".pdf")
    wrap = lambda s: textwrap.wrap(s, 100)
    L = wrap("COGNITIVE AND EMOTIONAL LANGUAGE IN FICTION, POOLED, 1600-2000, as drawn (top) and with concreteness "
             "regressed out (bottom).") + [""] + wrap(
        "Per text, the share of content words on either list (v4: cognition, attention, perception and volition "
        "words; emotion words; USAS X and E with period-model neighbours, LLM-rated for precision and hand-vetted). "
        "Gray points: decade medians over %s arc_fiction texts; black line: lowess (span 0.3). Bottom: the share "
        "minus a linear fit on the text's concreteness (Abs-Conc.Median.median, corpus-bias corrected; %s texts "
        "with both), plus the mean share; part of that fit is mechanical, since the list words are abstract and "
        "enter the concreteness mean. Model arms: TEMPLATE_ARM, %d lineages, coherent narrative passages; per model "
        "the median over passages (bottom: adjusted with the history's slope), then the median over lineages." % (
            format(len(T), ","), format(len(Tc), ","), A.base.nunique())) + ["",
        "  slope %.4f per concreteness unit; text-level r %.3f; decade rho raw vs adjusted %.2f; decade rho with "
        "concreteness raw %.2f, adjusted %.2f" % (b, np.corrcoef(Tc.conc_corr, Tc.share)[0, 1],
                                                 spearmanr(raw.value, adj.value)[0], spearmanr(raw.value, dconc.value)[0],
                                                 spearmanr(adj.value, dconc.value)[0]),
        "  arms raw %s; adjusted %s" % ({x: round(100 * v, 2) for x, v in arms_raw.items()},
                                         {x: round(100 * v, 2) for x, v in arms_adj.items()})]
    open(OUT + ".caption.txt", "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
