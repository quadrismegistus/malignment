"""Reference plate: the fall of evaluation in the novel, and where model fiction sits on it. (RH, 2026-09-26: "Can you
plot all this as reference")

    .venv/bin/python -u arc_evaluation_reference.py   -> figures/arc_evaluation_reference_v1.{png,pdf,caption.txt}, ARC_EVALUATION_REFERENCE.md

Everything from arc_valence_clean_components.py v2 (the SYMMETRIC cleaned lexicon, "+vector": kept Warriner lemmas and
forms plus the vector negative- and positive-pole words the rater confirmed; per content word). Panels, Figure 5 style
(decade medians, lowess 0.3, four labelled arms):
  1 evaluative words per content word (positive + negative)
  2 positive words per content word
  3 negative words per content word
  4 POSITIVITY: positive words as a share of evaluative words -- one number for how lopsided the evaluation is
  5 negative intensity: mean (5 - valence) over negative words
History: Chadwyck and Chicago arc_fiction, 1600-2009, >= 2,000 content words. Arms: judged no-demonym national
stories, one meta-text per model-condition, median over lineages. EXPLORATORY.
"""
import os, sys, textwrap

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.argv = [sys.argv[0], "v2"]
import arc_valence_clean_components as V                   # noqa: E402  (reads v2 at import; sets its own argv for H)
H, F = V.H, V.F

OUT = os.path.join(HERE, "figures", "arc_evaluation_reference_v1")
LEX = "+vector"


def main():
    for ext in (".png", ".pdf", ".caption.txt"):
        assert not os.path.exists(OUT + ext), "refusing to overwrite " + OUT + ext
    assert V.V2
    L = V.lexicons()
    Th = V.history(L).merge(H.concreteness_texts()[["_id", "year"]], on="_id")
    Th = Th[(Th.lexicon == LEX) & Th.year.between(1600, 2009) & (Th.n_content >= H.MIN_CONTENT)].copy()
    Th["positivity"] = Th.pos_rate / Th.eval_rate
    Mm = V.meta(L)
    Mm = Mm[Mm.lexicon == LEX].copy()
    Mm["positivity"] = Mm.pos_rate / Mm.eval_rate
    arm = {"base": "base", "aligned_raw": "raw", "aligned_prefill": "prefill", "aligned_rettberg": "continue"}
    spec = [("eval_rate", "Evaluative words in fiction", "Evaluative words\n(per content word)", True),
            ("pos_rate", "Positive words in fiction", "Positive words\n(per content word)", True),
            ("neg_rate", "Negative words in fiction", "Negative words\n(per content word)", True),
            ("positivity", "Positivity of evaluation", "Positive share of\nevaluative words", True),
            ("neg_int", "Intensity of negative words", "Mean distance\nbelow neutral", False)]
    hist, arms, rows = {}, {}, []
    for c, *_ in spec:
        hist[c] = H.decades(Th.year, Th[c])
        med = Mm.pivot_table(index="lineage", columns="cond", values=c).median()
        arms[c] = {arm[k]: float(med[k]) for k in arm}
        cv = H.smooth(hist[c])
        lo, hi = cv[:, 1].min(), cv[:, 1].max()
        for k, v in arms[c].items():
            xs = [int(round(y0 + (v - v0) / (v1 - v0) * (y1 - y0))) for (y0, v0), (y1, v1) in zip(cv[:-1], cv[1:]) if (v0 - v) * (v1 - v) < 0]
            rows.append((c, H.NAME[k], v, "above every decade" if v > hi else "below every decade" if v < lo else ", ".join(map(str, xs))))
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["pdf.fonttype"] = 42
    from plotnine.composition import Stack
    H.XMAX = 2250
    ps = [H.panel(hist[c], H.smooth(hist[c]), arms[c], t, yl, i == len(spec) - 1, pct) for i, (c, t, yl, pct) in enumerate(spec)]
    fig = Stack(ps).draw()
    fig.set_size_inches(F.PUB_SIZE[0], 10.0)
    fig.savefig(OUT + ".png", dpi=300)
    fig.savefig(OUT + ".pdf")
    cap = textwrap.wrap(
        "THE FALL OF EVALUATION IN THE NOVEL, 1600-2000, and where model fiction sits on it. Per text, words of clear "
        "positive or negative valence per content word, from a cleaned valence lexicon (Warriner et al. 2013 lemmas and "
        "forms kept under an ambiguity standard, plus period vocabulary proposed by a Warriner-seeded vector norm and "
        "confirmed by an LLM rater; positive above 6, negative below 4 on Warriner's 1-9 scale). Positivity = positive "
        "share of evaluative words; negative intensity = mean distance below neutral (5) of negative words. Gray points: "
        "decade medians over %s Chadwyck and Chicago novels; black line: lowess (span 0.3). Model arms: national stories "
        "(no-demonym prompt, judged proper stories), each model-condition as one text, median over lineages: base models "
        "(dotted); aligned models given raw text (dashed); aligned models in their chat template, reply prefilled "
        "(dash-dot) or asked (solid)." % format(Th._id.nunique(), ","), 100)
    open(OUT + ".caption.txt", "w").write("\n".join(cap) + "\n")
    R = ["# The fall of evaluation: reference numbers (EXPLORATORY)", "",
         "Producer `arc_evaluation_reference.py`. Plate: figures/arc_evaluation_reference_v1.png. Placement = crossing years "
         "of the smoothed history.", "", "| measure | arm | value | placement |", "|---|---|---|---|"]
    R += ["| %s | %s | %.4f | %s |" % r for r in rows]
    open(os.path.join(HERE, "ARC_EVALUATION_REFERENCE.md"), "w").write("\n".join(R) + "\n")
    print("\n".join(R))


if __name__ == "__main__":
    main()
