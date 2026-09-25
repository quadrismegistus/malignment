"""Figure 5 candidate: concreteness, valence, arousal and emotional language, with all four TEMPLATE_ARM arms.
(RH, 2026-09-25: "settled on Concreteness, Valence, and Arousal and maybe Emotion-words ... the big thing to
check: malign gave you new data -- which has prefilled and chat-template aligned as well as aligned-raw")

    .venv/bin/python -u arc_fig5_candidate.py   -> figures/arc_fig5_candidate_v1.{png,pdf,caption.txt}, ARC_FIG5_CANDIDATE.md

HISTORY over the book's arc_fiction set, Figure 5's recipe (decade median over texts, lowess 0.3):
  concreteness   the book's Abs-Conc.Median.median, corpus-bias corrected (arc_history_arms.concreteness_texts)
  valence        Warriner, token-weighted mean over mapped content words (arc_type_norms.py)
  arousal        Warriner, likewise
  emotional      share of content words on the v4 emotional list (arc_history_arms v4)
ARMS: TEMPLATE_ARM (TEMPLATE_ARM.md), 30 lineages with >= 10 coherent narrative passages in all four arms
(sel12, RWKV excluded): base; aligned raw (no template); aligned prefill (chat template, "Hi.", the reply
opening on the stem); aligned continue (chat template, "Continue this text: " + stem). Each model-arm's
passages concatenated into one meta-text and scored as a novel is; the median over lineages. Concreteness
and emotional from arc_history_arms.arm_meta (arms4); valence and arousal from the same meta-texts with
arc_type_norms' map (cached here). Model concreteness is not bias-corrected. EXPLORATORY.
"""
import os, re, sys, textwrap

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.argv = [sys.argv[0], "v4", "meta", "sel12", "arms4"]
import arc_history_arms as H                               # noqa: E402
import arc_type_norms as N                                 # noqa: E402
import arc_interiority as A                                # noqa: E402
from malignment import figure as F                         # noqa: E402

OUT = os.path.join(HERE, "figures", "arc_fig5_candidate_v1")
VA_OUT = os.path.join(H.DATA, "arc_fig5_meta_warriner_arms4.parquet")
ARMS = ("base", "raw", "prefill", "continue")


def meta_warriner():
    """Warriner valence and arousal of each model-arm meta-text (the same passages as arm_meta)."""
    if os.path.exists(VA_OUT):
        return pd.read_parquet(VA_OUT)
    P = pd.read_parquet(H.ARM_OUT)
    S_ = pd.concat([pd.read_parquet(os.path.join(H.TA, "selection.parquet")),
                    pd.read_parquet(os.path.join(H.TA, "selection_2.parquet"))]).set_index("id")
    L = N.lexicons()["warriner"]
    Mf = pd.read_parquet(N.MAP)
    fmap = dict(zip(Mf[Mf.source == "warriner"].form, Mf[Mf.source == "warriner"].entry))
    core = N.mapper(L)
    _, sw, _ = A.lists_expanded()
    rows = []
    for (base, arm, model), g in P.groupby(["base", "arm", "model"]):
        toks = [w for w in re.findall(r"[a-z]+", "\n\n".join(S_.loc[i, "text"] or "" for i in g.id).lower()) if w not in sw]
        es = [fmap.get(w) or core(w)[0] for w in toks]
        es = [e for e in es if e]
        rows.append(dict(base=base, arm=arm, model=model, n_content=len(toks), cov=len(es) / len(toks),
                         valence=float(np.mean([L[e]["warriner_valence"] for e in es])),
                         arousal=float(np.mean([L[e]["warriner_arousal"] for e in es]))))
    D = pd.DataFrame(rows)
    D.to_parquet(VA_OUT, index=False)
    return D


def crossings(curve, t):
    out = []
    for (y0, v0), (y1, v1) in zip(curve[:-1], curve[1:]):
        if (v0 - t) * (v1 - t) < 0:
            out.append(int(round(y0 + (t - v0) / (v1 - v0) * (y1 - y0))))
    return out


def main():
    for ext in (".png", ".pdf", ".caption.txt"):
        assert not os.path.exists(OUT + ext), "refusing to overwrite " + OUT + ext
    assert H.ALL4 and H.META and H.UNION and H.V4
    F.check_halftones({"history": F.PUB_INK, "points": F.PUB_GRAY, "arms": F.PUB_MID})
    C = H.concreteness_texts()
    C = C[C.year.between(1600, 2009) & C.conc_corr.notna()]
    assert len(C) == 81555, len(C)
    T = pd.read_parquet(H.COUNTS)
    T = T[(T.n_content >= H.MIN_CONTENT) & T.year.between(1600, 2009)]
    assert len(T) == 75974, len(T)
    W = pd.read_parquet(N.TEXTS)
    W = W[(W.n_content >= H.MIN_CONTENT) & W.year.between(1600, 2009)]
    assert len(W) == 75974, len(W)
    M = pd.read_parquet(H.META_OUT)
    V = meta_warriner()
    assert M.base.nunique() == V.base.nunique() == 30 and set(M.arm) == set(V.arm) == set(ARMS), (M.base.nunique(), set(M.arm))
    hist = {"conc": H.decades(C.year, C.conc_corr), "valence": H.decades(W.year, W.warriner_valence),
            "arousal": H.decades(W.year, W.warriner_arousal), "emo": H.decades(T.year, T.n_emo / T.n_content)}
    arms = {"conc": {a: float(M[M.arm == a].conc.median()) for a in ARMS},
            "emo": {a: float(M[M.arm == a].emo.median()) for a in ARMS},
            "valence": {a: float(V[V.arm == a].valence.median()) for a in ARMS},
            "arousal": {a: float(V[V.arm == a].arousal.median()) for a in ARMS}}
    spec = (("conc", "Concreteness in fiction", "Concreteness\n(word norm mean)", False),
            ("valence", "Valence in fiction", "Valence\n(Warriner, 1-9)", False),
            ("arousal", "Arousal in fiction", "Arousal\n(Warriner, 1-9)", False),
            ("emo", "Emotional language in fiction", "Emotional words\n(share of words)", True))
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["pdf.fonttype"] = 42
    from plotnine.composition import Stack
    #: the right margin holds "Aligned, chat, prefilled" at 9 pt; Figure 5's XMAX fits only "Aligned models"
    H.XMAX = 2250
    ps = [H.panel(hist[k], H.smooth(hist[k]), arms[k], t, yl, i == len(spec) - 1, pct) for i, (k, t, yl, pct) in enumerate(spec)]
    fig = Stack(ps).draw()
    fig.set_size_inches(F.PUB_SIZE[0], 7.6)
    fig.savefig(OUT + ".png", dpi=300)
    fig.savefig(OUT + ".pdf")
    L = ["# Figure 5 candidate: four measures, four arms (EXPLORATORY)", "",
         "Producer `arc_fig5_candidate.py` (method in its docstring). Plate: figures/arc_fig5_candidate_v1.png. Arms are "
         "medians over 30 lineages of per-model meta-texts. Crossing years: where an arm's level crosses the smoothed "
         "history (several where the curve is not monotone; 'above'/'below' where it clears every decade).", "",
         "| measure | " + " | ".join(H.NAME[a] for a in ARMS) + " |", "|---|" + "---|" * len(ARMS)]
    for k, *_ in spec:
        cv = H.smooth(hist[k])
        lo, hi = cv[:, 1].min(), cv[:, 1].max()
        cells = []
        for a in ARMS:
            v = arms[k][a]
            where = "above all" if v > hi else "below all" if v < lo else ", ".join(map(str, crossings(cv, v)))
            cells.append(("%.2f%%" % (100 * v) if k == "emo" else "%.3f" % v) + " (" + where + ")")
        L.append("| %s | %s |" % (k, " | ".join(cells)))
    L += ["", "Per-lineage agreement with the median ordering (share of the 30 lineages where the aligned arm moves from "
          "base in the median's direction):", ""]
    for k in ("conc", "valence", "arousal", "emo"):
        src = M if k in ("conc", "emo") else V
        col = k
        piv = src.pivot_table(index="base", columns="arm", values=col)
        cells = []
        for a in ("raw", "prefill", "continue"):
            sgn = np.sign(arms[k][a] - arms[k]["base"])
            cells.append("%s %d/30" % (a, int((np.sign(piv[a] - piv["base"]) == sgn).sum())))
        L.append("- %s: %s" % (k, ", ".join(cells)))
    open(os.path.join(HERE, "ARC_FIG5_CANDIDATE.md"), "w").write("\n".join(L) + "\n")
    wrap = lambda s: textwrap.wrap(s, 100)
    cap = wrap("FIGURE 5 CANDIDATE: concreteness, valence, arousal and emotional language in English fiction, "
               "1600-2000, with four model arms.") + [""] + wrap(
        "Gray points: decade medians over the book's arc_fiction texts (concreteness %s texts; the rest %s with at "
        "least 2,000 content words); black line: lowess (span 0.3). Concreteness: Abs-Conc.Median.median, "
        "corpus-bias corrected. Valence, arousal: Warriner norms, token-weighted over content words mapped to the "
        "lexicon (inflections, British and old spellings, long-s). Emotional: share of words on a vetted emotion list "
        "(USAS E and emotion-rated X words with period-model neighbours, 1,121 base words). Arms: 30 model lineages "
        "(TEMPLATE_ARM), each model-arm's coherent narrative passages as one meta-text; median over lineages. Base "
        "models (dotted); aligned models given raw text (dashed); aligned models in their chat template with the "
        "reply prefilled with the story's opening (dash-dot) or asked to continue it (solid). Model concreteness is "
        "not bias-corrected (clean digital text)." % (format(len(C), ","), format(len(T), ",")))
    open(OUT + ".caption.txt", "w").write("\n".join(cap) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
