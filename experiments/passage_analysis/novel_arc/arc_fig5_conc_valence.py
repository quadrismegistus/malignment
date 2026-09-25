"""Concreteness and valence, 1700-2000, with national-story arms. (RH, 2026-09-25: "a 2 panel conc and valence,
starting at 1700 not 1600 (filter out c17)")

    .venv/bin/python -u arc_fig5_conc_valence.py [f11]   -> figures/arc_fig5_conc_valence_v1[_f11].{png,pdf,caption.txt}
    .venv/bin/python -u arc_fig5_conc_valence.py extremity -> figures/arc_fig5_conc_valence_extremity_v1.*: a third
        panel, valence EXTREMITY (arc_valence_extremity.py: each word's distance from Warriner-neutral valence,
        token-averaged; RH "could we plot abs val of valence"). No bias coefficients exist for it: uncorrected.

HISTORY: the abstraction project's vector norms over arc_fiction (vad_scores_arc_fiction.parquet):
Abs-Conc.Median.median, corrected with the book's corpus_bias_coefficients.json (abstraction's re-estimate awaits
RH), and VAD-Valence.Warriner.median (plain, not orth), corrected with vad_corpus_bias.json. Texts 1700-2009 only,
so the decade medians and the lowess (span 0.3) are fitted on that span. Decades with >= 3 texts.
ARMS (default): the no-demonym national stories -- every generation in judged_stories_v2, kept whole if a pure
story, else spliced before the judge's first non-story segment (arc_prompt_check.splice); endpoint lineages;
each model-condition as one meta-text; abstraction's scorer; median over lineages. Conditions: base (raw
paratext), aligned raw, aligned chat prefilled, aligned chat asked ("Write a 1500 word potential story.").
RH judged these the better model-fiction source: longer and neutrally prompted, where the F11 stems set the
valence level (ARC_PROMPT_CHECK.md). With `f11`: the TEMPLATE_ARM meta-texts instead. EXPLORATORY.
"""
import json, os, sys, textwrap

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
F11 = "f11" in sys.argv[1:]
EXT = "extremity" in sys.argv[1:]
sys.argv = [sys.argv[0], "v4", "meta", "sel12", "arms4"]
import arc_history_arms as H                               # noqa: E402
from malignment import figure as F                         # noqa: E402

SH = os.path.expanduser("~/malignment-data/interiority_norms")
OUT = os.path.join(HERE, "figures", "arc_fig5_conc_valence" + ("_extremity" if EXT else "") + "_v1" + ("_f11" if F11 else ""))
XC = "VAD-ValenceExtremity.Warriner.median"
COLS = {"conc": "Abs-Conc.Median.median", "valence": "VAD-Valence.Warriner.median"}
START = 1700


def main():
    for ext in (".png", ".pdf", ".caption.txt"):
        assert not os.path.exists(OUT + ext), "refusing to overwrite " + OUT + ext
    V = pd.read_parquet(os.path.join(SH, "vad_scores_arc_fiction.parquet"))
    T = H.concreteness_texts()[["_id", "year", "corpus", "conc"]].merge(V, on="_id", validate="1:1")
    ok = T.conc.notna() & T[COLS["conc"]].notna()
    assert np.allclose(T.conc[ok], T[COLS["conc"]][ok], atol=1e-4)
    book = json.load(open(H.BIAS))["coefficients"]
    vad = json.load(open(os.path.join(SH, "vad_corpus_bias.json")))["estimates"]
    T["c_conc"] = T[COLS["conc"]] - T.corpus.map(book).fillna(0.0)
    T["c_valence"] = T[COLS["valence"]] - T.corpus.map(vad[COLS["valence"]]["coefficients"]).fillna(0.0)
    if EXT:
        E = pd.read_parquet(os.path.join(H.DATA, "valence_extremity_arc.parquet"))[["_id", XC]]
        T = T.merge(E, on="_id", how="left", validate="1:1")
        T["c_extremity"] = T[XC]
        COLS["extremity"] = XC
    T = T[T.year.between(START, 2009)]
    if F11:
        M = pd.read_parquet(os.path.join(SH, "fig5_meta_texts_arms4_scored.parquet"))
        key, conds, lin = "arm", ["base", "raw", "prefill", "continue"], "base"
        src = "TEMPLATE_ARM F11 stems, 30 lineages, coherent narrative passages"
    else:
        M = pd.read_parquet(os.path.join(H.DATA, "prompt_check_national_judged_meta_scored.parquet"))
        M = M.assign(arm=M.cond.map({"base": "base", "aligned_raw": "raw", "aligned_prefill": "prefill", "aligned_rettberg": "continue"}))
        key, conds, lin = "arm", ["base", "raw", "prefill", "continue"], "lineage"
        src = "no-demonym national stories, judged proper stories, %d lineages" % M.lineage.nunique()
    if EXT:
        Mx = pd.read_parquet(os.path.join(H.DATA, "valence_extremity_meta_%s.parquet" % ("f11" if F11 else "national")))[["id", XC]]
        M = M.merge(Mx, on="id", how="left", validate="1:1")
    hist, arms, n = {}, {}, {}
    for k, c in COLS.items():
        d = T[["year", "c_" + k]].dropna()
        hist[k], n[k] = H.decades(d.year, d["c_" + k]), len(d)
        arms[k] = {a: float(M[M[key] == a][c].median()) for a in conds}
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["pdf.fonttype"] = 42
    from plotnine.composition import Stack
    #: "Aligned, chat, prefilled" at 9 pt ends a few pixels inside the panel border at 2150; the canvas-edge audit
    #: cannot see a cut at the PANEL edge, so the margin carries slack
    H.X0, H.XMAX = START, 2185
    spec = (("conc", "Concreteness in fiction", "Concreteness\n(vector norm)"),
            ("valence", "Valence in fiction", "Valence\n(vector norm)"))
    if EXT:
        spec += (("extremity", "Valence extremity in fiction", "Distance from\nneutral valence"),)
    ps = [H.panel(hist[k], H.smooth(hist[k]), arms[k], t, yl, i == len(spec) - 1, False) for i, (k, t, yl) in enumerate(spec)]
    fig = Stack(ps).draw()
    fig.set_size_inches(F.PUB_SIZE[0], 4.4 if not EXT else 6.4)
    fig.savefig(OUT + ".png", dpi=300)
    fig.savefig(OUT + ".pdf")
    rows = []
    for k, *_ in spec:
        cv = H.smooth(hist[k])
        lo, hi = cv[:, 1].min(), cv[:, 1].max()
        for a in conds:
            v = arms[k][a]
            where = "above all" if v > hi else "below all" if v < lo else ", ".join(
                str(int(round(y0 + (v - v0) / (v1 - v0) * (y1 - y0)))) for (y0, v0), (y1, v1) in zip(cv[:-1], cv[1:]) if (v0 - v) * (v1 - v) < 0)
            rows.append("  %s %s: %+.3f (%s)" % (k, H.NAME[a], v, where))
    cap = textwrap.wrap("CONCRETENESS AND VALENCE IN ENGLISH FICTION, 1700-2000, with four model arms. Vector norms from "
                        "period word2vec models seeded by human ratings (concreteness: the book's Abs-Conc; valence: "
                        "Warriner et al. 2013), median across periods; held-out agreement with the human ratings 0.68 and "
                        "0.66. Gray points: decade medians over %s arc_fiction texts (1700-2009, corpus-bias corrected); "
                        "black line: lowess (span 0.3). Arms: %s; each model-condition's texts as one meta-text scored the "
                        "same way; median over lineages. Base models (dotted); aligned models given raw text (dashed); "
                        "aligned models in their chat template, reply prefilled (dash-dot) or asked (solid)." % (
                            format(n["conc"], ","), src) + (
                        " Bottom: valence extremity, each word's distance from neutral valence (the point where Warriner's "
                        "midpoint, 5, falls on the vector axis) averaged over tokens -- emotional charge of either sign; "
                        "not corpus-bias corrected (no coefficients exist for it)." if EXT else ""), 100) + [""] + rows
    open(OUT + ".caption.txt", "w").write("\n".join(cap) + "\n")
    print("\n".join(cap))


if __name__ == "__main__":
    main()
