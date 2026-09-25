"""Which type-norm histories survive regressing out concreteness? (RH, 2026-09-25)

    .venv/bin/python -u arc_type_norms_resid.py   -> ARC_TYPE_NORMS_RESID.md, figures/arc_type_norms_resid.{png,pdf,caption.txt}

For each scale of arc_type_norms.py (Warriner, Brysbaert, k): one OLS across texts of the scale on the
book's concreteness (Abs-Conc.Median.median, corpus-bias corrected -- the Figure 5 panel, not Brysbaert),
over texts carrying both; adjusted value = scale - slope * (concreteness - mean concreteness). Decade
medians and lowess (0.3) as everywhere else. Two numbers per scale decide "killed" vs "survives":
  shape   Spearman rho between the raw and the adjusted decade series;
  size    the adjusted lowess's range over the raw lowess's range.
Arms adjusted with the history's slope, from each model's meta-text: its scale value (arc_type_norms
meta) and its concreteness (arc_history_arms meta, measure_lltk, on scores_rep's scale).
Brysbaert and k concreteness are near-duplicates of the regressor, so their "adjustment" mostly removes
themselves; they are kept as a check that the method kills what it should. For every scale some of the
fit is shared vocabulary, since the same content words enter both means. EXPLORATORY.
"""
import os, sys, textwrap

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.argv = [sys.argv[0], "v4", "meta", "sel12"]
import arc_history_arms as H                               # noqa: E402
import arc_type_norms as N                                 # noqa: E402
from malignment import figure as F                         # noqa: E402

OUT = os.path.join(HERE, "figures", "arc_type_norms_resid")


def main():
    from scipy.stats import spearmanr
    from statsmodels.nonparametric.smoothers_lowess import lowess
    for ext in (".png", ".pdf", ".caption.txt"):
        assert not os.path.exists(OUT + ext), "refusing to overwrite " + OUT + ext
    T = pd.read_parquet(N.TEXTS)
    T = T[(T.n_content >= H.MIN_CONTENT) & T.year.between(1600, 2009)]
    assert len(T) == 75974, len(T)
    C = H.concreteness_texts()[["_id", "conc_corr"]]
    T = T.merge(C, on="_id").dropna(subset=["conc_corr"])
    Mn = pd.read_parquet(N.META)
    Mc = pd.read_parquet(H.META_OUT)[["model", "arm", "conc"]]
    Mm = Mn.merge(Mc, on=["model", "arm"], validate="1:1")
    assert len(Mm) == len(Mn) == 60, (len(Mm), len(Mn))
    scales = [c for c in T.columns if c.startswith(("warriner_", "brysbaert_", "k_"))]
    cm = T.conc_corr.mean()
    dconc = H.decades(T.year, T.conc_corr).set_index("year").value
    rows, pts, curves, arms = [], [], [], []
    for s in scales:
        d = T[[s, "year", "conc_corr"]].dropna()
        b, a = np.polyfit(d.conc_corr, d[s], 1)
        adj = d[s] - b * (d.conc_corr - cm)
        hr, ha = H.decades(d.year, d[s]), H.decades(d.year, adj)
        lr = lowess(hr.value.values, hr.year.values, frac=0.3, return_sorted=True)
        la = lowess(ha.value.values, ha.year.values, frac=0.3, return_sorted=True)
        shape = spearmanr(hr.value, ha.value)[0]
        size = np.ptp(la[:, 1]) / np.ptp(lr[:, 1])
        verdict = "survives" if shape >= 0.7 and size >= 0.5 else "killed" if shape < 0.3 or size < 0.3 else "partly"
        arm = {x: float(Mm[Mm.arm == x][s].median()) for x in ("base", "raw")}
        armj = {x: float((Mm[Mm.arm == x][s] - b * (Mm[Mm.arm == x].conc - cm)).median()) for x in ("base", "raw")}
        rows.append(dict(scale=s, r_text=float(np.corrcoef(d.conc_corr, d[s])[0, 1]), slope=b,
                         rho_raw_conc=spearmanr(hr.value, dconc.loc[hr.year])[0], rho_adj_conc=spearmanr(ha.value, dconc.loc[ha.year])[0],
                         shape=shape, size=size, verdict=verdict,
                         adj_min=la[:, 1].min(), adj_max=la[:, 1].max(), base_adj=armj["base"], aligned_adj=armj["raw"],
                         base_raw=arm["base"], aligned_raw=arm["raw"]))
        lab = s.replace("warriner_", "Warriner ").replace("brysbaert_", "Brysbaert ").replace("k_", "k: ").replace("_", " ")
        pts += [dict(scale=lab, year=y, value=v) for y, v in zip(ha.year, ha.value)]
        curves += [dict(scale=lab, year=x, value=y, curve="raw") for x, y in lr] + [dict(scale=lab, year=x, value=y, curve="adjusted") for x, y in la]
        arms += [dict(scale=lab, arm=n, value=armj[x]) for x, n in (("base", "Base models"), ("raw", "Aligned models"))]
    R = pd.DataFrame(rows)
    order = [r.scale.replace("warriner_", "Warriner ").replace("brysbaert_", "Brysbaert ").replace("k_", "k: ").replace("_", " ")
             for r in R.sort_values(["verdict", "shape"], ascending=[False, False]).itertuples()]
    P_, C_, A_ = pd.DataFrame(pts), pd.DataFrame(curves), pd.DataFrame(arms)
    for df in (P_, C_, A_):
        df["scale"] = pd.Categorical(df.scale, categories=order)
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["pdf.fonttype"] = 42
    from plotnine import (ggplot, aes, geom_point, geom_line, geom_hline, facet_wrap, labs, scale_color_manual,
                          scale_linetype_manual, scale_x_continuous, theme, element_text, guides, guide_legend)
    nrow = (len(order) + 2) // 3
    p = (ggplot()
         + geom_point(aes("year", "value"), data=P_, color=F.PUB_GRAY, size=0.5)
         + geom_line(aes("year", "value", color="curve"), data=C_, size=F.PUB_LINE_PT)
         + geom_hline(aes(yintercept="value", linetype="arm"), data=A_, color=F.PUB_MID, size=F.PUB_RULE_PT * 1.2)
         + scale_color_manual({"raw": F.PUB_GRAY, "adjusted": F.PUB_INK})
         + scale_linetype_manual({"Base models": "dotted", "Aligned models": "dashed"})
         + facet_wrap("~scale", ncol=3, scales="free_y")
         + scale_x_continuous(breaks=[1600, 1800, 2000])
         + labs(x="", y="Token-weighted mean rating", color="", linetype="")
         + guides(color=guide_legend(nrow=1), linetype=guide_legend(nrow=1))
         + F.pub_theme(height=1.45 * nrow + 0.9)
         + theme(legend_position="bottom", legend_box="vertical", figure_size=(F.PUB_SIZE[0], 1.45 * nrow + 0.9),
                 strip_text=element_text(family=F.pub_font(), size=F.PUB_FONT_PT - 1)))
    F.save(p, OUT + ".png")
    cap = textwrap.wrap("TYPE-NORM HISTORIES WITH CONCRETENESS REGRESSED OUT. Gray line: the raw lowess; black line: "
                        "the lowess of the adjusted decade medians (gray points) -- the scale minus a text-level linear "
                        "fit on the book's concreteness, plus its mean; %s arc_fiction texts. Panels ordered survivors "
                        "first. Arms: 30 lineages' meta-texts adjusted with the history's slope. Brysbaert and k "
                        "concreteness are near-duplicates of the regressor and serve as a check; shared vocabulary makes "
                        "part of every fit mechanical." % format(len(T), ","), 100)
    open(OUT + ".caption.txt", "w").write("\n".join(cap) + "\n")
    L = ["# Type-norm histories: which survive regressing out concreteness? (EXPLORATORY)", "",
         "Producer `arc_type_norms_resid.py` (method in its docstring). Verdict: survives if shape >= 0.7 and size >= "
         "0.5; killed if shape < 0.3 or size < 0.3; otherwise partly. Plate: figures/arc_type_norms_resid.png.", "",
         "| scale | verdict | shape (rho raw vs adjusted) | size (adjusted / raw range) | r with concreteness (texts) | decade rho with concreteness raw / adjusted | adjusted range | base adj | aligned adj |",
         "|---|---|---|---|---|---|---|---|---|"]
    for r in R.sort_values(["verdict", "shape"], ascending=[False, False]).itertuples():
        L.append("| %s | %s | %+.2f | %.2f | %+.2f | %+.2f / %+.2f | %.3f-%.3f | %.3f | %.3f |" % (
            r.scale, r.verdict, r.shape, r.size, r.r_text, r.rho_raw_conc, r.rho_adj_conc, r.adj_min, r.adj_max, r.base_adj, r.aligned_adj))
    open(os.path.join(HERE, "ARC_TYPE_NORMS_RESID.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
