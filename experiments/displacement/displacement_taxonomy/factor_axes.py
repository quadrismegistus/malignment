"""Is the base -> aligned difference one thing? Two matrices, two answers.

    python -u factor_axes.py        -> results/factor_axes.md

## THE 38 AXES CANNOT BE FACTORED AND THAT IS NOT A LIMITATION OF THE DATA

Each relation is assigned to exactly ONE axis. A relation x axis matrix is a
PARTITION -- one 1 per row, zeros elsewhere -- and its principal components
recover the partition, nothing more. Factor analysis needs every observation to
carry a value on every variable, and the axes are a classification.

So the question "is there a factor or two behind all this" has to be asked of
something that IS a matrix. Two exist, they are different questions, and they
give different answers.

    A   50 lineages x 13 norm scales, DOSE SLOPES
        "do alignment regimes differ along one dimension?"
    B   77 frames x 25 scales, BASE -> ALIGNED DELTAS
        "is the movement itself one or two things?"

**A IS THE EASIER QUESTION AND IT IS NOT RH'S.** A high PC1 there says the
fifty alignment recipes vary mostly along one axis -- a fact about the roster.
B asks whether what happens to a frame is one thing, which is the displacement
claim, and it is the harder one.

`_z` and `_absz` columns are dropped. `warriner_valence` and
`warriner_valence_z` are the same construct twice; left in, they inflate PC1 by
giving one factor duplicate columns to load on. Undeduplicated, A's PC1 reads
55.3% over 39 columns against 60.4% over 13 -- the share rises when the
duplicates go, which is the opposite of what a reader would guess, because the
duplicates also add variance they explain.
"""
import collections, csv, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
SKIP = ("_z", "_absz")


def _pca(M):
    import numpy as np
    M = np.where(np.isnan(M), np.nanmean(M, axis=0), M)
    Z = (M - M.mean(0)) / (M.std(0) + 1e-12)
    u, s, vt = np.linalg.svd(Z, full_matrices=False)
    return u, s, vt, s ** 2 / (s ** 2).sum()


def lineage_matrix():
    import numpy as np
    p = os.path.join(HERE, "..", "norm_change", "results", "dose_lift_v4_cov20",
                     "dose_lift_v4__levels_en__by_lineage.csv")
    r = list(csv.DictReader(open(p, encoding="utf-8")))
    keep = lambda t: not t.endswith(SKIP)
    lin = sorted({x["lineage"] for x in r})
    tgt = sorted({x["target"] for x in r if keep(x["target"])})
    li = {l: i for i, l in enumerate(lin)}
    ti = {t: i for i, t in enumerate(tgt)}
    M = np.full((len(lin), len(tgt)), np.nan)
    for x in r:
        if keep(x["target"]):
            try:
                M[li[x["lineage"]], ti[x["target"]]] = float(x["slope"])
            except ValueError:
                pass
    return M, lin, tgt


def frame_matrix(min_cov=0.15):
    import numpy as np
    p = os.path.join(HERE, "results", "norm_shift_contextual.csv")
    r = list(csv.DictReader(open(p, encoding="utf-8")))
    skip = lambda s: s.startswith(("v6_wide", "v6full")) or s.endswith(SKIP)
    fr = sorted({x["frame"] for x in r})
    sc = sorted({x["scale"] for x in r if not skip(x["scale"])})
    fi = {f: i for i, f in enumerate(fr)}
    si = {s: i for i, s in enumerate(sc)}
    M = np.full((len(fr), len(sc)), np.nan)
    for x in r:
        if not skip(x["scale"]):
            try:
                M[fi[x["frame"]], si[x["scale"]]] = float(x["delta"])
            except ValueError:
                pass
    #: drop sparse columns then sparse rows, in that order: a scale rated on a
    #: third of the frames would otherwise evict the frames that carry it
    cols = [j for j in range(len(sc)) if np.isnan(M[:, j]).mean() < min_cov]
    M, sc = M[:, cols], [sc[j] for j in cols]
    rows = [i for i in range(M.shape[0]) if np.isnan(M[i]).mean() < min_cov]
    return M[rows], [fr[i] for i in rows], sc


def main():
    import numpy as np
    L = ["# Is the base → aligned difference one thing?", "",
         "**The 38 axes cannot be factored.** Each relation sits on exactly one, "
         "so a relation × axis matrix is a partition and its components recover "
         "the partition. The question is put to the two matrices that exist.", ""]

    for tag, (M, obs, var), q in (
            ("A — 50 alignment lineages × norm scales, dose slopes",
             lineage_matrix(), "do alignment regimes differ along one dimension?"),
            ("B — frames × scales, base → aligned deltas",
             frame_matrix(), "is the movement itself one or two things?")):
        u, s, vt, ev = _pca(M)
        L += ["## %s" % tag, "", "_%s_" % q, "",
              "%d × %d. **PC1 %.1f%%, PC2 %.1f%%, PC3 %.1f%% — first two %.1f%%.**"
              % (M.shape[0], M.shape[1], 100 * ev[0], 100 * ev[1], 100 * ev[2],
                 100 * (ev[0] + ev[1])), ""]
        for k in (0, 1):
            o = np.argsort(vt[k])
            L.append("- **PC%d −** %s" % (k + 1, ", ".join(
                "`%s` %+.2f" % (var[i], vt[k][i]) for i in o[:4])))
            L.append("- **PC%d +** %s" % (k + 1, ", ".join(
                "`%s` %+.2f" % (var[i], vt[k][i]) for i in o[-4:])))
        L.append("")
        if tag.startswith("B"):
            from relation_group_report import load
            rel, _v, got, _b = load(1)
            byf = {rel[g["id"]]["frame"]: g for g in got}
            s1, s2 = u[:, 0] * s[0], u[:, 1] * s[1]
            agg = collections.defaultdict(list)
            for i, f in enumerate(obs):
                g = byf.get(f)
                if g:
                    agg[g["axis"]].append((s1[i], s2[i]))
            L += ["### Where each axis sits on PC1 and PC2", "",
                  "The %d frames that carry both a norm profile and an axis. "
                  "Small cells: read the ORDER, not the values." % len(obs), "",
                  "| axis | frames | PC1 | PC2 |", "|---|---|---|---|"]
            for a, v in sorted(agg.items(),
                               key=lambda kv: -float(np.mean([x[0] for x in kv[1]]))):
                if len(v) >= 3:
                    L.append("| `%s` | %d | %+.2f | %+.2f |"
                             % (a, len(v), np.mean([x[0] for x in v]),
                                np.mean([x[1] for x in v])))
            L.append("")
    out = os.path.join(HERE, "results", "factor_axes.md")
    open(out, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L))
    print("\nwrote %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
