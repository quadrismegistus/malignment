"""Concreteness, valence and arousal: the abstraction project's vector norms, history and four arms. (RH, 2026-09-25:
"can we just plot Concreteness, Valence, Arousal, all the vector versions produced from abstraction project")

    .venv/bin/python -u arc_fig5_vector.py   -> figures/arc_fig5_vector_v1.{png,pdf,caption.txt}, ARC_FIG5_VECTOR.md

HISTORY: abstraction's vad_scores_arc_fiction.parquet -- per arc_fiction rep, Abs-Conc.Median.median (identical to
scores_rep) and VAD-{Valence,Arousal}.Warriner.median (Warriner-seeded, period word2vec C16-C21, median over
runs, corpora, centuries; positive = concrete / pleasant / aroused). Year and corpus from lltk.texts via
arc_history_arms.concreteness_texts. Corpus-bias correction: concreteness with the book's
corpus_bias_coefficients.json, as every earlier plate (abstraction's re-estimate, about double, awaits RH);
valence and arousal with abstraction's vad_corpus_bias.json. Decade median over texts (>= 3), 1600-2009, lowess 0.3.
ARMS: abstraction's scoring of the 120 model-arm meta-texts (fig5_meta_texts_arms4_scored.parquet: 30 lineages x
base, aligned raw, chat prefilled, chat asked), identical scorer; median over lineages; not bias-corrected
(clean digital text). Held-out agreement with Warriner (vad_norms_validation.csv, median): valence 0.66, arousal
0.48, concreteness 0.68 against its own norms. EXPLORATORY.
"""
import json, os, sys, textwrap

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.argv = [sys.argv[0], "v4", "meta", "sel12", "arms4"]
import arc_history_arms as H                               # noqa: E402
import arc_fig5_candidate as C5                            # noqa: E402
from malignment import figure as F                         # noqa: E402

SH = os.path.expanduser("~/malignment-data/interiority_norms")
OUT = os.path.join(HERE, "figures", "arc_fig5_vector_v1")
COLS = {"conc": "Abs-Conc.Median.median", "valence": "VAD-Valence.Warriner.median", "arousal": "VAD-Arousal.Warriner.median"}
ARMS = C5.ARMS


def main():
    for ext in (".png", ".pdf", ".caption.txt"):
        assert not os.path.exists(OUT + ext), "refusing to overwrite " + OUT + ext
    V = pd.read_parquet(os.path.join(SH, "vad_scores_arc_fiction.parquet"))
    assert len(V) == 82080
    T = H.concreteness_texts()[["_id", "year", "corpus", "conc"]].merge(V, on="_id", validate="1:1")
    #: abstraction's Abs-Conc is scores_rep's; assert the identity rather than trust it
    ok = T.conc.notna() & T[COLS["conc"]].notna()
    assert np.allclose(T.conc[ok], T[COLS["conc"]][ok], atol=1e-4), "Abs-Conc differs from scores_rep"
    book = json.load(open(H.BIAS))["coefficients"]
    vad = json.load(open(os.path.join(SH, "vad_corpus_bias.json")))["estimates"]
    T["c_conc"] = T[COLS["conc"]] - T.corpus.map(book).fillna(0.0)
    for k in ("valence", "arousal"):
        T["c_" + k] = T[COLS[k]] - T.corpus.map(vad[COLS[k]]["coefficients"]).fillna(0.0)
    T = T[T.year.between(1600, 2009)]
    M = pd.read_parquet(os.path.join(SH, "fig5_meta_texts_arms4_scored.parquet"))
    assert len(M) == 120 and M.base.nunique() == 30 and set(M.arm) == set(ARMS)
    hist, arms, agree = {}, {}, {}
    for k in COLS:
        d = T[["year", "c_" + k]].dropna()
        hist[k] = (H.decades(d.year, d["c_" + k]), len(d))
        piv = M.pivot_table(index="base", columns="arm", values=COLS[k])
        arms[k] = {a: float(piv[a].median()) for a in ARMS}
        agree[k] = {a: int((np.sign(piv[a] - piv["base"]) == np.sign(arms[k][a] - arms[k]["base"])).sum()) for a in ARMS[1:]}
    spec = (("conc", "Concreteness in fiction", "Concreteness\n(vector norm)"),
            ("valence", "Valence in fiction", "Valence\n(vector norm)"),
            ("arousal", "Arousal in fiction", "Arousal\n(vector norm)"))
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["pdf.fonttype"] = 42
    from plotnine.composition import Stack
    H.XMAX = 2250
    ps = [H.panel(hist[k][0], H.smooth(hist[k][0]), arms[k], t, yl, i == 2, False) for i, (k, t, yl) in enumerate(spec)]
    fig = Stack(ps).draw()
    fig.set_size_inches(F.PUB_SIZE[0], 6.0)
    fig.savefig(OUT + ".png", dpi=300)
    fig.savefig(OUT + ".pdf")
    L = ["# Vector norms: concreteness, valence, arousal, with four arms (EXPLORATORY)", "",
         "Producer `arc_fig5_vector.py` (method in its docstring). Arm values are medians over 30 lineages of meta-text "
         "scores; placement = crossing years of the smoothed history; agreement = lineages (of 30) whose arm moves from "
         "base in the median's direction. No partial or adjustment here.", "",
         "| measure | " + " | ".join(H.NAME[a] for a in ARMS) + " | agreement raw / prefill / asked |", "|---|" + "---|" * (len(ARMS) + 1)]
    for k, *_ in spec:
        cv = H.smooth(hist[k][0])
        lo, hi = cv[:, 1].min(), cv[:, 1].max()
        cells = ["%+.3f (%s)" % (arms[k][a], "above all" if arms[k][a] > hi else "below all" if arms[k][a] < lo else
                                 ", ".join(map(str, C5.crossings(cv, arms[k][a])))) for a in ARMS]
        L.append("| %s | %s | %s |" % (k, " | ".join(cells), " / ".join(str(agree[k][a]) for a in ARMS[1:])))
    L += ["", "History ranges (smoothed): " + "; ".join("%s %.3f to %.3f" % (k, H.smooth(hist[k][0])[:, 1].min(), H.smooth(hist[k][0])[:, 1].max()) for k in COLS)]
    open(os.path.join(HERE, "ARC_FIG5_VECTOR.md"), "w").write("\n".join(L) + "\n")
    cap = textwrap.wrap("CONCRETENESS, VALENCE AND AROUSAL IN ENGLISH FICTION, 1600-2000, with four model arms. Vector "
                        "norms from period word2vec models (C16-C21), seeded by human ratings (concreteness: the book's "
                        "Abs-Conc; valence and arousal: Warriner et al. 2013), median across periods; held-out agreement "
                        "with the human ratings 0.68, 0.66 and 0.48. Gray points: decade medians over %s arc_fiction texts "
                        "(corpus-bias corrected); black line: lowess (span 0.3). Arms: 30 model lineages (TEMPLATE_ARM), "
                        "each model-arm's coherent narrative passages as one meta-text, same scorer; median over lineages; "
                        "base (dotted), aligned given raw text (dashed), aligned in its chat template with the reply "
                        "prefilled (dash-dot) or asked to continue (solid). Arousal's vector norm is strongly coupled to "
                        "concreteness at text level (Spearman -0.79 over texts)." % format(hist["conc"][1], ","), 100)
    open(OUT + ".caption.txt", "w").write("\n".join(cap) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
