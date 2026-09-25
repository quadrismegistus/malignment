"""Concreteness above emotional language: the Figure 5 candidate. (RH, 2026-09-25: "is the best plate
Concreteness | Emotion-over-concreteness?")

    .venv/bin/python -u arc_history_conc_emo.py         -> figures/arc_history_conc_emo_v4.{png,pdf,caption.txt}
    .venv/bin/python -u arc_history_conc_emo.py resid   -> figures/arc_history_conc_emo_resid_v4.*

Two panels over arc_fiction, Figure 5's recipe (decade median over texts, lowess 0.3), model arms from
per-model meta-texts (arc_history_arms.arm_meta; median over lineages). Top: concreteness, the book's
Abs-Conc.Median.median, corpus-bias corrected. Bottom: the v4 emotional list's share; with `resid`, that
share minus a text-level linear fit on concreteness plus the mean (arc_history_resid.py's adjustment; the
arms adjusted with the history's slope). Why emotion and not cognition or the pool: the emotional arc
survives the adjustment (decade rho raw vs adjusted ~0.95) where the cognitive and pooled arcs do not
(~0.14). EXPLORATORY.
"""
import os, sys, textwrap

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
RESID = "resid" in sys.argv[1:]
sys.argv = [sys.argv[0], "v4", "meta", "sel12"]         # arc_history_arms reads its version at import; sel12 adds internlm2
import arc_history_arms as H                            # noqa: E402
from malignment import figure as F                      # noqa: E402

OUT = os.path.join(HERE, "figures", "arc_history_conc_emo" + ("_resid" if RESID else "") + "_v4_sel12")


def main():
    from scipy.stats import spearmanr
    for ext in (".png", ".pdf", ".caption.txt"):
        assert not os.path.exists(OUT + ext), "refusing to overwrite " + OUT + ext
    assert H.V4 and H.META and not H.PAST
    C = H.concreteness_texts()
    Cy = C[C.year.between(1600, 2009) & C.conc_corr.notna()]
    assert len(Cy) == 81555, len(Cy)
    T = pd.read_parquet(H.COUNTS)
    T = T[(T.n_content >= H.MIN_CONTENT) & T.year.between(1600, 2009)]
    assert len(T) == 75974, len(T)
    T["share"] = T.n_emo / T.n_content
    M = pd.read_parquet(H.META_OUT)
    arms_c = {a: float(M[M.arm == a].conc.median()) for a in ("base", "raw")}
    hc = H.decades(Cy.year, Cy.conc_corr)
    if RESID:
        Tc = T.merge(C[["_id", "conc_corr"]], on="_id").dropna(subset=["conc_corr"])
        b, a = np.polyfit(Tc.conc_corr, Tc.share, 1)
        cm = Tc.conc_corr.mean()
        he = H.decades(Tc.year, Tc.share - b * (Tc.conc_corr - cm))
        arms_e = {x: float((M[M.arm == x].emo - b * (M[M.arm == x].conc - cm)).median()) for x in ("base", "raw")}
        n_e, note = len(Tc), "slope %.4f per concreteness unit over %s texts" % (b, format(len(Tc), ","))
    else:
        he = H.decades(T.year, T.share)
        arms_e = {x: float(M[M.arm == x].emo.median()) for x in ("base", "raw")}
        n_e, note = len(T), ""
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["pdf.fonttype"] = 42
    from plotnine.composition import Stack
    ps = [H.panel(hc, H.smooth(hc), arms_c, "Concreteness in fiction", "Concreteness\n(word norm mean)", False, False),
          H.panel(he, H.smooth(he), arms_e,
                  "Emotional language in fiction, concreteness regressed out" if RESID else "Emotional language in fiction",
                  "Emotional words,\nadjusted (share)" if RESID else "Emotional words\n(share of words)", True, True)]
    fig = Stack(ps).draw()
    fig.set_size_inches(F.PUB_SIZE[0], 4.2)
    fig.savefig(OUT + ".png", dpi=300)
    fig.savefig(OUT + ".pdf")
    wrap = lambda s: textwrap.wrap(s, 100)
    L = wrap("CONCRETENESS AND EMOTIONAL LANGUAGE IN FICTION, 1600-2000" + (", emotion with concreteness regressed out"
             if RESID else "") + ", with base and aligned model arms.") + [""] + wrap(
        "Gray points: decade medians over the book's arc_fiction texts; black line: lowess (span 0.3). Top: "
        "concreteness (Abs-Conc.Median.median, corpus-bias corrected; %s texts). Bottom: share of content words "
        "on the emotional list (USAS E and emotion-rated USAS X words with period-model neighbours, LLM-rated for "
        "precision and hand-vetted, 1,121 base words; %s texts)%s. Model arms: TEMPLATE_ARM, %d lineages; each model's "
        "coherent narrative passages concatenated into one meta-text and scored as a novel is; the median over "
        "lineages. Model concreteness is not bias-corrected (clean digital text)." % (
            format(len(Cy), ","), format(n_e, ","),
            ", minus a text-level linear fit on concreteness plus the mean share, arms adjusted with the history's "
            "slope (part of the fit is mechanical: emotion words are abstract and enter the concreteness mean)"
            if RESID else "", M.base.nunique())) + ["",
        "  arms: concreteness %s; emotional %s%s; decade rho(emotional, concreteness) %.2f" % (
            {a: round(v, 3) for a, v in arms_c.items()}, {a: round(100 * v, 2) for a, v in arms_e.items()},
            ("; " + note) if note else "",
            spearmanr(he.value, hc.set_index("year").loc[he.year].value)[0])]
    open(OUT + ".caption.txt", "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
