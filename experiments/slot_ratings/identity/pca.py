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
"""
import collections
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
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


if __name__ == "__main__":
    main()
