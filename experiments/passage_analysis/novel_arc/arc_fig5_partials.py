"""Which Figure 5 measure separates the four TEMPLATE_ARM arms once the others are partialled out? (RH, 2026-09-25)

    .venv/bin/python -u arc_fig5_partials.py      -> ARC_FIG5_PARTIALS.md     (pooled slope; as committed at 32924f93)
    .venv/bin/python -u arc_fig5_partials.py v2   -> ARC_FIG5_PARTIALS_v2.md  (abstraction's two objections answered)

v2 (abstraction, 2026-09-25). (1) The POOLED slope is fitted partly on the between-arm shift it is meant to
adjust for; v2 fits it WITHIN ARM (both variables demeaned by arm, slope from the lineage-to-lineage variation)
and applies it to the raw values, beside the pooled slope. (2) An asymmetry between "X partialled on
concreteness" and the reverse follows from a reliability gap alone -- a noisy measure loses its shared signal
when partialled on a precise one, a noisy regressor removes little -- so v2 MEASURES reliability: split-half
over each model-arm's passages (odd vs even), correlated across the 120 meta-texts and stepped up by
Spearman-Brown. The earlier sentence "the asymmetry, not an assumption, puts the arm shift on concreteness" is
withdrawn pending these numbers.

The abstraction seat found (3e47a7b) that no VAD dimension separates the arms once text-level concreteness is
partialled out of it within the 120 meta-texts, and read the apparent arousal effect as "concreteness counted
twice". That reading assumes concreteness is the prior variable. The test here runs the partial BOTH ways, and
on our own emotional and cognitive lists too: a measure X partialled on Y is X minus its OLS fit on Y over the
120 model-arm meta-texts; per lineage, whether each aligned arm moves from base in the direction of the raw
effect; two-sided sign test over 30 lineages. If alignment moved one dimension that both measures read,
partialling either on the other would kill both; an asymmetry says which one carries the arm effect.

Inputs: abstraction's fig5_meta_texts_arms4_scored.parquet (Abs-Conc, VAD) and arc_history_arms' arms4 meta
(emo, cog: v4 lists), joined on model and arm. EXPLORATORY.
"""
import os

import numpy as np
import pandas as pd
from scipy.stats import binomtest, spearmanr

HERE = os.path.dirname(os.path.abspath(__file__))
SH = os.path.expanduser("~/malignment-data/interiority_norms")
DATA = os.path.expanduser("~/malignment-data/novel_arc")
C = "Abs-Conc.Median.median"
import sys                                                  # noqa: E402
V2 = "v2" in sys.argv[1:]
WITHIN = V2
MEAS = {C: "concreteness", "emo": "emotional words", "cog": "cognitive words",
        "VAD-Valence.Warriner.median": "valence (vector)", "VAD-Arousal.Warriner.median": "arousal (vector)",
        "VAD-Dominance.Warriner.median": "dominance (vector)"}


def main():
    M = pd.read_parquet(os.path.join(SH, "fig5_meta_texts_arms4_scored.parquet"))
    E = pd.read_parquet(os.path.join(DATA, "arc_history_arm_meta_v4_sel12_arms4.parquet"))[["model", "arm", "emo", "cog", "conc"]]
    M = M.merge(E, on=["model", "arm"], validate="1:1")
    assert len(M) == 120 and M.base.nunique() == 30
    #: the two concreteness scorings are one quantity (abstraction's identity check); assert it here too
    assert np.allclose(M.groupby("arm")[C].median(), M.groupby("arm").conc.median(), atol=0.002)
    base = M.pivot_table(index="base", columns="arm", values=C)
    direction = {col: np.sign(M.pivot_table(index="base", columns="arm", values=col).median().loc["continue"]
                              - M.pivot_table(index="base", columns="arm", values=col).median().loc["base"]) for col in MEAS}

    def slope(col, on):
        if WITHIN:
            d = M[[col, on, "arm"]].copy()
            d[col] -= d.groupby("arm")[col].transform("mean")
            d[on] -= d.groupby("arm")[on].transform("mean")
            return np.polyfit(d[on], d[col], 1)[0]
        return np.polyfit(M[on], M[col], 1)[0]

    def test(col, on=None):
        y = M[col] - (slope(col, on) * M[on] if on else 0)
        piv = M.assign(y=y).pivot_table(index="base", columns="arm", values="y")
        cells = []
        for a in ("raw", "prefill", "continue"):
            k = int((np.sign(piv[a] - piv["base"]) == direction[col]).sum())
            cells.append("%d (p %.3f)" % (k, binomtest(k, 30).pvalue))
        return " / ".join(cells)

    L = ["# Partial tests of the Figure 5 measures across the four arms (EXPLORATORY)", "",
         "Producer `arc_fig5_partials.py` (method in its docstring). Cells: lineages (of 30) whose raw / prefill / "
         "continue arm moves from base in the direction of the unpartialled continue effect, with the two-sided sign "
         "test p. Bonferroni over the %d partialled tests below puts the bar near p 0.001." % (3 * (len(MEAS) - 1) * 2), "",
         "Meta-text Spearman with concreteness: " + ", ".join("%s %+.2f" % (MEAS[c], spearmanr(M[c], M[C])[0]) for c in MEAS if c != C), "",
         "| measure | unpartialled | partialled on concreteness | concreteness partialled on it |", "|---|---|---|---|"]
    for col in MEAS:
        if col == C:
            L.append("| %s | %s | -- | -- |" % (MEAS[col], test(col)))
        else:
            L.append("| %s | %s | %s | %s |" % (MEAS[col], test(col), test(col, C), test(C, col)))
    M["pool"] = M.emo + M.cog
    MEAS["pool"] = "cognitive + emotional"
    direction["pool"] = 1.0
    L.append("| %s | %s | %s | %s |" % (MEAS["pool"], test("pool"), test("pool", C), test(C, "pool")))
    if V2:
        L = L[:2] + ["Producer `arc_fig5_partials.py v2`: the SLOPE IS FITTED WITHIN ARM (both variables demeaned by "
                     "arm), then applied to the raw values. Pooled-slope version: ARC_FIG5_PARTIALS.md."] + L[2:]
        L += ["", "## Split-half reliability across the 120 meta-texts (odd vs even passages; Spearman-Brown)", ""]
        L += reliability()
    open(os.path.join(HERE, "ARC_FIG5_PARTIALS%s.md" % ("_v2" if V2 else "")), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


def reliability():
    """Split-half reliability of the list shares and of concreteness across model-arm meta-texts: each
    meta-text's passages split odd/even by passage order, each half pooled (list tokens over content tokens;
    concreteness as the content-token-weighted mean of passage scores), halves correlated over the 120."""
    P = pd.read_parquet(os.path.join(DATA, "arc_history_arm_passages_v4_sel12_arms4.parquet"))
    P = P.sort_values(["model", "arm", "id"]).assign(half=lambda d: d.groupby(["model", "arm"]).cumcount() % 2)
    out = []
    for col, lab in (("emo", "emotional words"), ("cog", "cognitive words"), ("conc", "concreteness (measure_lltk, passage-weighted)")):
        d = P.dropna(subset=[col]).assign(w=lambda x: x[col] * x.n_content)
        h = d.groupby(["model", "arm", "half"]).agg(w=("w", "sum"), n=("n_content", "sum"))
        v = (h.w / h.n).unstack("half")
        r = float(np.corrcoef(v[0], v[1])[0, 1])
        out.append("- %s: split-half r %.3f, Spearman-Brown %.3f (n %d meta-texts)" % (lab, r, 2 * r / (1 + r), len(v)))
    return out


if __name__ == "__main__":
    main()
