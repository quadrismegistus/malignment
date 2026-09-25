"""Check the Figure 5 candidate's Warriner panels against the k lexicon: k_valence, and k_charge where k has
no arousal. (RH, 2026-09-25: "Is that k_valence and k_arousal" -- no, Warriner; "Yes" to running k.)

    .venv/bin/python -u arc_fig5_kcheck.py   -> ARC_FIG5_KCHECK.md, figures/arc_fig5_kcheck_v1.{png,pdf,caption.txt}

Same history (arc_type_norms texts), same 120 meta-texts (arc_fig5_candidate: 30 lineages x base, aligned
raw, chat prefilled, chat asked), same statistics (median over lineages; crossings of the smoothed history;
lineages whose aligned arm moves from base in the median's direction), with the k lexicon's map in place of
Warriner's. k is one model's out-of-context ratings (deepseek-v4-flash), 1-7; charge agrees with human
arousal at r 0.60 in the lexicon's own calibration, so it is a neighbour of arousal, not a stand-in. EXPLORATORY.
"""
import os, re, sys, textwrap

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import arc_fig5_candidate as C5                            # noqa: E402  (sets arms4 argv for arc_history_arms)
H, N, A = C5.H, C5.N, C5.A
from malignment import figure as F                         # noqa: E402

OUT = os.path.join(HERE, "figures", "arc_fig5_kcheck_v1")
K_OUT = os.path.join(H.DATA, "arc_fig5_meta_k_arms4.parquet")
SC = {"k_valence": "valence", "k_charge": "charge"}


def meta_k():
    if os.path.exists(K_OUT):
        return pd.read_parquet(K_OUT)
    P = pd.read_parquet(H.ARM_OUT)
    S_ = pd.concat([pd.read_parquet(os.path.join(H.TA, "selection.parquet")),
                    pd.read_parquet(os.path.join(H.TA, "selection_2.parquet"))]).set_index("id")
    L = N.lexicons()["k"]
    Mf = pd.read_parquet(N.MAP)
    fmap = dict(zip(Mf[Mf.source == "k"].form, Mf[Mf.source == "k"].entry))
    core = N.mapper(L)
    _, sw, _ = A.lists_expanded()
    rows = []
    for (base, arm, model), g in P.groupby(["base", "arm", "model"]):
        toks = [w for w in re.findall(r"[a-z]+", "\n\n".join(S_.loc[i, "text"] or "" for i in g.id).lower()) if w not in sw]
        es = [e for e in (fmap.get(w) or core(w)[0] for w in toks) if e]
        rows.append(dict(base=base, arm=arm, model=model, cov=len(es) / len(toks),
                         **{s: float(np.mean([L[e][s] for e in es])) for s in SC}))
    D = pd.DataFrame(rows)
    D.to_parquet(K_OUT, index=False)
    return D


def main():
    for ext in (".png", ".pdf", ".caption.txt"):
        assert not os.path.exists(OUT + ext), "refusing to overwrite " + OUT + ext
    W = pd.read_parquet(N.TEXTS)
    W = W[(W.n_content >= H.MIN_CONTENT) & W.year.between(1600, 2009)]
    assert len(W) == 75974, len(W)
    K = meta_k()
    V = C5.meta_warriner()
    assert K.base.nunique() == 30 and set(K.arm) == set(C5.ARMS)
    rows = {}
    L = ["# Figure 5 candidate: Warriner against the k lexicon, four arms (EXPLORATORY)", "",
         "Producer `arc_fig5_kcheck.py` (method in its docstring). Placement = crossing years of the smoothed "
         "history; agreement = lineages (of 30) whose aligned arm moves from base in the median's direction.", "",
         "| scale | " + " | ".join(H.NAME[a] for a in C5.ARMS) + " | agreement raw / prefill / asked |", "|---|" + "---|" * (len(C5.ARMS) + 1)]
    for col, src, lab in (("warriner_valence", V.rename(columns={"valence": "warriner_valence"}), "Warriner valence"),
                          ("k_valence", K, "k valence"),
                          ("warriner_arousal", V.rename(columns={"arousal": "warriner_arousal"}), "Warriner arousal"),
                          ("k_charge", K, "k charge")):
        h = H.decades(W.year, W[col])
        cv = H.smooth(h)
        lo, hi = cv[:, 1].min(), cv[:, 1].max()
        arms = {a: float(src[src.arm == a][col].median()) for a in C5.ARMS}
        piv = src.pivot_table(index="base", columns="arm", values=col)
        agree = [int((np.sign(piv[a] - piv["base"]) == np.sign(arms[a] - arms["base"])).sum()) for a in ("raw", "prefill", "continue")]
        cells = ["%.3f (%s)" % (arms[a], "above all" if arms[a] > hi else "below all" if arms[a] < lo else
                                ", ".join(map(str, C5.crossings(cv, arms[a])))) for a in C5.ARMS]
        L.append("| %s | %s | %s |" % (lab, " | ".join(cells), " / ".join(map(str, agree))))
        rows[col] = (h, cv, arms, lab)
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["pdf.fonttype"] = 42
    from plotnine.composition import Stack
    H.XMAX = 2250
    ps = [H.panel(rows[c][0], rows[c][1], rows[c][2], rows[c][3] + " in fiction", rows[c][3].replace(" ", "\n", 1), i == 1, False)
          for i, c in enumerate(("k_valence", "k_charge"))]
    fig = Stack(ps).draw()
    fig.set_size_inches(F.PUB_SIZE[0], 4.2)
    fig.savefig(OUT + ".png", dpi=300)
    fig.savefig(OUT + ".pdf")
    cap = textwrap.wrap("K-LEXICON CHECK of the Figure 5 candidate: k valence and k charge (one model's 1-7 ratings; k has "
                        "no arousal, and charge agrees with human arousal at r 0.60) over the arc_fiction history, with the "
                        "four TEMPLATE_ARM arms as in arc_fig5_candidate_v1. Not human norms.", 100)
    open(OUT + ".caption.txt", "w").write("\n".join(cap) + "\n")
    open(os.path.join(HERE, "ARC_FIG5_KCHECK.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
