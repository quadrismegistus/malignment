"""Do the 24 identity groups form groups-of-groups, and does alignment move them together?

RH's design: one point per {group} x {base, aligned}, the 25 slot scales as
features, PCA.

## WHAT IS CENTRED, AND WHY IT HAS TO BE

The raw `E[scale]` for a (group, lineage, arm) cell carries three things at once:
the SCALE's own level, the LINEAGE's level, and the group's deviation. Only the
third is the object here. So each scale is centred WITHIN (lineage, arm) across
the 24 groups before averaging over lineages.

**Without that, PC1 is which model you are.** With it, a group's coordinate is
its deviation from the other 23 in the same model and the same arm, which is the
same quantity `group_contrast.py` sign-tests.

## THE QUESTION THE ARROWS ANSWER

Every group appears twice, so each has a base->aligned displacement. If alignment
applies ONE operation to identity terms, those 24 vectors point the same way and
their pairwise cosines are near 1. If it does something different per group, they
do not. **That is a measurement, not a picture**, and it is printed.

Scales are z-scored across the 48 points so a wide scale does not dominate the
covariance by having wide units.

    python -m experiments.slot_ratings.identity.pca
    python -m experiments.slot_ratings.identity.pca --plot

## THE FIGURE READS THE SAVED ARTIFACT

`plot.py` in the parent folder sets the rule: *"Every figure reads a saved
artifact and computes nothing that a README does not already report. If a figure
and a README disagree, the figure is wrong."* So `--plot` recomputes nothing --
it reads `results/pca.json`, which this producer writes on every run.
"""
import collections
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def main(plot=False):
    import numpy as np
    rows = json.load(open(os.path.join(HERE, "results", "base_side.json")))["rows"]
    scales = sorted({k[5:] for k in rows[0] if k.startswith("base_")})
    groups = sorted({r["group"] for r in rows})
    gi = {g: i for i, g in enumerate(groups)}

    #: centre within (lineage, arm) across groups, then average over lineages
    acc = {a: np.zeros((len(groups), len(scales))) for a in ("base", "aligned")}
    cnt = {a: np.zeros(len(groups)) for a in ("base", "aligned")}
    byl = collections.defaultdict(list)
    for r in rows:
        byl[r["lineage"]].append(r)
    for lin, rs in byl.items():
        for arm in ("base", "aligned"):
            M = np.full((len(rs), len(scales)), np.nan)
            for i, r in enumerate(rs):
                for j, s in enumerate(scales):
                    v = r.get("%s_%s" % (arm, s))
                    if v is not None:
                        M[i, j] = v
            M = M - np.nanmean(M, axis=0)          # centre across the 24 groups
            for i, r in enumerate(rs):
                k = gi[r["group"]]
                ok = ~np.isnan(M[i])
                acc[arm][k][ok] += M[i][ok]
                cnt[arm][k] += 1
    P = {a: acc[a] / np.maximum(cnt[a][:, None], 1) for a in acc}

    X = np.vstack([P["base"], P["aligned"]])       # 48 x 25
    X = np.nan_to_num(X)
    X = (X - X.mean(0)) / np.where(X.std(0) > 0, X.std(0), 1)
    U, S, Vt = np.linalg.svd(X - X.mean(0), full_matrices=False)
    var = S ** 2 / (S ** 2).sum()
    Y = U * S

    print("PCA over %d points (%d groups x 2 arms), %d scales"
          % (len(X), len(groups), len(scales)))
    print("variance explained: PC1 %.1f%%  PC2 %.1f%%  PC3 %.1f%%  (top3 %.1f%%)"
          % (100 * var[0], 100 * var[1], 100 * var[2], 100 * var[:3].sum()))

    print("\nPC1 loadings, both ends")
    o = np.argsort(Vt[0])
    print("   negative: " + ", ".join("%s %+.2f" % (scales[i], Vt[0][i]) for i in o[:5]))
    print("   positive: " + ", ".join("%s %+.2f" % (scales[i], Vt[0][i]) for i in o[-5:]))
    print("PC2 loadings, both ends")
    o = np.argsort(Vt[1])
    print("   negative: " + ", ".join("%s %+.2f" % (scales[i], Vt[1][i]) for i in o[:5]))
    print("   positive: " + ", ".join("%s %+.2f" % (scales[i], Vt[1][i]) for i in o[-5:]))

    n = len(groups)
    print("\n%-20s %8s %8s   %8s %8s   %8s" %
          ("group", "PC1 base", "PC1 algn", "PC2 base", "PC2 algn", "|move|"))
    D = Y[n:, :2] - Y[:n, :2]
    order = np.argsort(-np.hypot(D[:, 0], D[:, 1]))
    for k in order:
        print("%-20s %8.2f %8.2f   %8.2f %8.2f   %8.2f"
              % (groups[k], Y[k, 0], Y[n + k, 0], Y[k, 1], Y[n + k, 1],
                 math.hypot(D[k, 0], D[k, 1])))

    #: DO THE ARROWS AGREE? full-dimensional displacement, pairwise cosine.
    F = X[n:] - X[:n]
    Fn = F / np.maximum(np.linalg.norm(F, axis=1, keepdims=True), 1e-12)
    C = Fn @ Fn.T
    iu = np.triu_indices(n, 1)
    cos = C[iu]
    print("\nDO THE 24 DISPLACEMENTS POINT THE SAME WAY? (full 25-dim, cosine)")
    print("   median pairwise cosine %.3f   mean %.3f" % (np.median(cos), cos.mean()))
    print("   pairs above +0.5: %d of %d      below -0.5: %d"
          % ((cos > 0.5).sum(), len(cos), (cos < -0.5).sum()))
    m = Fn.mean(0)
    print("   norm of the MEAN unit displacement: %.3f" % np.linalg.norm(m))
    print("   (1.0 = all groups move identically, 0.0 = no common direction)")

    out = dict(
        _what="PCA over {group} x {base,aligned}; scales centred within "
              "(lineage, arm) across the 24 groups, then z-scored across the 48 "
              "points. Coordinates are PC scores; loadings are the right "
              "singular vectors.",
        n_points=int(len(X)), n_scales=len(scales), groups=groups, scales=scales,
        var_explained=[float(v) for v in var[:5]],
        points=[dict(group=groups[k], arm=arm,
                     PC1=float(Y[k + (0 if arm == "base" else n), 0]),
                     PC2=float(Y[k + (0 if arm == "base" else n), 1]))
                for k in range(n) for arm in ("base", "aligned")],
        loadings=[dict(scale=scales[j], PC1=float(Vt[0][j]), PC2=float(Vt[1][j]))
                  for j in range(len(scales))],
        cosine=dict(median=float(np.median(cos)), mean=float(cos.mean()),
                    above_half=int((cos > 0.5).sum()),
                    below_half=int((cos < -0.5).sum()), n_pairs=int(len(cos)),
                    mean_unit_norm=float(np.linalg.norm(m))))
    path = os.path.join(HERE, "results", "pca.json")
    json.dump(out, open(path, "w"), indent=1)
    print("\n-> results/pca.json")
    if plot:
        _plot(path)


def _plot(path):
    """Biplot from `results/pca.json`. Computes nothing."""
    import pandas as pd
    from plotnine import (ggplot, aes, geom_segment, geom_point, geom_text,
                          labs, theme_minimal, theme, element_text, arrow,
                          scale_colour_manual, guides, element_blank,
                          coord_cartesian)
    d = json.load(open(path))
    P = pd.DataFrame(d["points"])
    L = pd.DataFrame(d["loadings"])
    v = d["var_explained"]

    #: base -> aligned as one row per group, so the arrow is a segment
    b = P[P.arm == "base"].set_index("group")
    a = P[P.arm == "aligned"].set_index("group")
    M = pd.DataFrame(dict(group=b.index, x=b.PC1, y=b.PC2,
                          xend=a.PC1.reindex(b.index), yend=a.PC2.reindex(b.index)))
    M["move"] = ((M.xend - M.x) ** 2 + (M.yend - M.y) ** 2) ** 0.5

    #: LOADINGS SCALED TO THE POINT CLOUD, which is what makes a biplot readable.
    #: The scale factor is cosmetic and is stated on the axis label so nobody
    #: reads an arrow length as a coordinate.
    pad = 0.10 * (P.PC1.max() - P.PC1.min())
    span = max(P.PC1.abs().max(), P.PC2.abs().max())
    lmax = max(L.PC1.abs().max(), L.PC2.abs().max())
    k = 0.85 * span / lmax
    L = L.assign(x=0.0, y=0.0, xend=L.PC1 * k, yend=L.PC2 * k)
    L["mag"] = (L.PC1 ** 2 + L.PC2 ** 2) ** 0.5
    L = L.sort_values("mag", ascending=False).head(12)

    g = (ggplot()
         + geom_segment(L, aes(x="x", y="y", xend="xend", yend="yend"),
                        colour="#b0b0b0", size=0.4,
                        arrow=arrow(length=0.10, type="closed"))
         + geom_text(L, aes(x="xend", y="yend", label="scale"),
                     colour="#7a7a7a", size=7, ha="left", va="bottom")
         + geom_segment(M, aes(x="x", y="y", xend="xend", yend="yend"),
                        colour="#2b6cb0", size=0.6, alpha=0.9,
                        arrow=arrow(length=0.09, type="closed"))
         + geom_point(P, aes("PC1", "PC2", colour="arm", shape="arm"), size=2.2)
         + geom_text(M, aes(x="xend", y="yend", label="group"),
                     size=7, ha="left", va="top", nudge_x=0.18)
         + scale_colour_manual({"base": "#c05050", "aligned": "#2b6cb0"})
         #: DIRECTION CHECKED AGAINST THE DATA, NOT ASSUMED. `harm` loads +0.27
         #: on PC1 and Palestinians -- the highest-harm group -- sits at +9.6, so
         #: POSITIVE PC1 IS THE HARM END. The first version of this label had it
         #: the other way round and a reader would have read the axis backwards.
         + labs(x="PC1  %.1f%%      deference / procedural  <-->  harm / assertiveness"
                  % (100 * v[0]),
                y="PC2  %.1f%%   interiority, superego, vocalisation" % (100 * v[1]),
                title="Identity groups in slot-norm space, base -> aligned",
                subtitle="arrows: base to aligned, one per group.  grey: scale "
                         "loadings, length cosmetic (x%.1f)" % k)
         + coord_cartesian(xlim=(P.PC1.min() - pad, P.PC1.max() + 2.2 * pad))
         + theme_minimal()
         + theme(figure_size=(11, 8.5), plot_title=element_text(size=12),
                 plot_subtitle=element_text(size=8, colour="#666666"),
                 panel_grid_minor=element_blank()))
    out = os.path.join(HERE, "figures", "pca_biplot.png")
    g.save(out, dpi=300, verbose=False)
    print("-> figures/pca_biplot.png")


if __name__ == "__main__":
    import sys
    main(plot="--plot" in sys.argv)
