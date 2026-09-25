"""Which Figure 5 measure separates the four TEMPLATE_ARM arms once the others are partialled out? (RH, 2026-09-25)

    .venv/bin/python -u arc_fig5_partials.py   -> ARC_FIG5_PARTIALS.md

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

    def test(col, on=None):
        y = M[col] - (np.polyval(np.polyfit(M[on], M[col], 1), M[on]) if on else 0)
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
    open(os.path.join(HERE, "ARC_FIG5_PARTIALS.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
