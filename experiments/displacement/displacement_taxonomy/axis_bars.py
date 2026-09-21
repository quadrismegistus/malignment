"""The 38 axes as signed bars: which way alignment pushes, and how far.

    python -u axis_bars.py            -> figures/axis_bars.{png,pdf}
    python -u axis_bars.py --dose     split each bar by lift tertile

## WHY THE MEAN AND NOT A LOADING (RH)

The first figures proposed for this material plotted PC loadings. Those do not
replicate: two independently built vocabularies share ONE component (canonical
r=0.80) and nothing after it, so a loading plot draws a quantity that is a
property of a vocabulary. The per-axis MEAN MOVEMENT does replicate -- it is
the directions table, measured -- and it is what a reader can check against the
word lists.

## IT IS A MOVEMENT, NOT A PROPERTY OF THE BASE SIDE

The Survey asks where the two word lists sit RELATIVE TO EACH OTHER on an axis:
its lowest level is "LIST 1 is wholly at the first pole, LIST 2 at the second".
So a single value already carries both sides, and orienting it to "which pole
the base sits on" leaves the aligned side implied at the other end. **There is
no separate aligned score to plot; there is one displacement with a sign.**

Marker to the right: alignment moves the sentence toward the RIGHT pole.
Magnitude is the mean of a probability-weighted position on five levels, so
|1.0| would be every relation placing the two lists cleanly at opposite ends.

## THE SOURCE IS THE GRADED SURVEY, NOT THE ASSIGNMENT RUN

`results/axis_survey_en_seed1.jsonl` — 2,244 relations x 38 axes on
`jev-1.13.0`, every relation scored on every axis. NOT
`grouping_seed1/axis_*.json`, which is the single-best-fitting-axis assignment
and carries one value per relation.
"""
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.path.join(HERE, "..", "..", "..")):
    if p not in sys.path:
        sys.path.insert(0, p)
SCRATCH = ("/private/tmp/claude-502/-Users-rj416-github-malign-logits/"
           "412328a9-b178-4724-9c75-eca7f1f0e80b/scratchpad")


def load(seed=1):
    import numpy as np
    from relation_group_input import flip
    from relation_group_report import load as _l, dose_values
    from axis_survey import vocabulary
    rel, _v, _g, _b = _l(seed)
    V = vocabulary(seed)["axes"]
    ax = [a["id"] for a in V]
    lift = dose_values(rel, "shown_lift")
    rows = [json.loads(x) for x in
            open(os.path.join(HERE, "results",
                              "axis_survey_en_seed%d.jsonl" % seed),
                 encoding="utf-8")]
    rows = [r for r in rows if rel[r["id"]]["frame"] in lift]
    M = np.zeros((len(rows), len(ax)))
    L = np.zeros(len(rows))
    for i, r in enumerate(rows):
        L[i] = lift[rel[r["id"]]["frame"]]
        fl = flip(r["id"], seed)
        for j, k in enumerate(ax):
            v = r.get(k)
            s = 0.0 if v is None else 2.0 - v
            M[i, j] = -s if fl else s
    return M, L, V, ax


def short(s, n=21):
    """Shorten a pole description to something that fits the label column.

    **STRIP BEFORE TRUNCATING.** Cutting at a character count spent the budget
    on articles and dangling clauses -- "another action or event that follows"
    became "another action o…" when "another action" says it. Drop the leading
    article and everything after the first comma or dash first; truncate at a
    WORD boundary only if it still does not fit.
    """
    import re as _re
    s = s.split("—")[0].split(",")[0].split(" — ")[0].strip()
    s = _re.sub(r"^(a|an|the) ", "", s)
    s = _re.sub(r" (that|which|already|typically) .*$", "", s)
    if len(s) <= n:
        return s
    cut = s[:n].rsplit(" ", 1)[0]
    return (cut if len(cut) >= n - 8 else s[:n - 1]).rstrip() + "…"


def main(argv=None):
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from malignment.figure import (PUB_SIZE, PUB_FONT_PT, PUB_INK, PUB_MID,
                                   PUB_GRAY, PUB_RULE_PT, pub_font, save)
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--dose", action="store_true")
    ap.add_argument("--top", type=int, default=0, help="keep only the N largest")
    ap.add_argument("--dots", action="store_true",
                    help="three markers a row on one scale instead of bars")
    ap.add_argument("--facet", action="store_true",
                    help="two panels: marginal on the left, lift split on the right")
    ap.add_argument("--sig", action="store_true",
                    help="keep only axes with a direction worth drawing")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    M, L, V, ax = load(a.seed)
    mu = M.mean(0)
    q = np.quantile(L, [1 / 3, 2 / 3])
    lowm = M[L <= q[0]].mean(0)
    topm = M[L > q[1]].mean(0)

    if a.sig:
        #: **SIGNIFICANCE IS THE GATE, EFFECT SIZE IS THE SELECTOR.** At
        #: n=2,225 a per-axis Wilcoxon against zero passes 31 of 38, including
        #: an axis whose mean is +0.007 -- the test cannot discriminate at this
        #: n and filtering on it alone would keep almost everything.
        #:
        #: **AND A MARGINAL FILTER DROPS EXACTLY THE REVERSALS.**
        #: `specificity_vs_generality` is marginal q=0.12 and dose q=8e-57;
        #: `argument_structure` q=0.07 and 1e-06. An axis with no overall
        #: direction and a large dose effect is the most interesting kind here,
        #: so the dose test is a second entry route rather than an extra hurdle.
        from scipy import stats
        m = M.shape[1]
        def _bh(pv):
            o_ = np.argsort(pv); q = np.empty(m); prev = 1.0
            for r, i in enumerate(o_[::-1], 1):
                prev = min(prev, pv[i] * m / (m - r + 1)); q[i] = prev
            return q
        qm = _bh(np.array([stats.wilcoxon(M[:, j])[1] if np.any(M[:, j]) else 1.0
                           for j in range(m)]))
        qd = _bh(np.array([stats.mannwhitneyu(M[L > q[1], j],
                                              M[L <= q[0], j])[1]
                           for j in range(m)]))
        ok = ((qm < 0.05) & (np.abs(mu) >= 0.05)) | \
             ((qd < 0.05) & (np.abs(topm - lowm) >= 0.10))
        print("  --sig keeps %d of %d axes (%d on a marginal direction, "
              "%d on a dose difference)"
              % (int(ok.sum()), m, int(((qm < 0.05) & (np.abs(mu) >= 0.05)).sum()),
                 int(((qd < 0.05) & (np.abs(topm - lowm) >= 0.10)).sum())))
        M = M[:, ok]; mu = mu[ok]; lowm = lowm[ok]; topm = topm[ok]
        V = [v for v, k in zip(V, ok) if k]; ax = [x for x, k in zip(ax, ok) if k]
    o = np.argsort(mu)
    if a.top:
        #: **RANKING BY THE MEAN EXCLUDES EXACTLY THE AXES THAT REVERSE.** An
        #: axis that runs one way at low lift and the other at high averages to
        #: zero, so `--top 20` on |mean| dropped `speaking / bodily` -- the
        #: reversal this whole thread turns on. It is the same defect as the
        #: marginal binomial reporting the residue of a cancellation (see
        #: `relation_group_report`), reappearing in a figure's selection rule.
        #: Rank on the LARGER of the two tertile means instead, so an axis
        #: enters if it is big at either end.
        rank = np.maximum(np.abs(lowm), np.abs(topm)) if a.dose else np.abs(mu)
        keep = set(np.argsort(-rank)[:a.top].tolist())
        o = np.array([i for i in o if i in keep])
    n = len(o)
    #: 0.19 in a row put the full 38 on an 8-inch plate. `--top` is the plate
    #: version and the full one is the appendix.
    y = np.arange(n)
    if a.dots:
        fig, axx = plt.subplots(figsize=(PUB_SIZE[0], 0.165 * n + 1.05),
                                layout="constrained")
        axm = None
        #: **THE SEGMENT IS THE POINT, NOT THE MARKERS.** Three markers a row
        #: on one scale is compact but the eye reads them as three unrelated
        #: dots; the thin rule joining the two tertiles makes the dose shift a
        #: LENGTH, which is the quantity the figure is about, and its direction
        #: is legible before any of the labels are read.
        for i, j in enumerate(o):
            axx.plot([lowm[j], topm[j]], [i, i], color=PUB_GRAY,
                     linewidth=PUB_RULE_PT * 1.6, zorder=2,
                     solid_capstyle="butt")
        axx.scatter(lowm[o], y, marker="v", s=17, facecolor=PUB_GRAY,
                    edgecolor="none", zorder=3, label="lowest third of lift")
        axx.scatter(mu[o], y, marker="s", s=13, facecolor=PUB_MID,
                    edgecolor="none", zorder=4, label="all frames")
        axx.scatter(topm[o], y, marker="^", s=19, facecolor=PUB_INK,
                    edgecolor="none", zorder=5, label="highest third")
    elif a.facet:
        fig, (axm, axx) = plt.subplots(
            1, 2, sharey=True, figsize=(PUB_SIZE[0], 0.155 * n + 1.1),
            layout="constrained",
            gridspec_kw={"width_ratios": [1, 1]})
    else:
        fig, axx = plt.subplots(figsize=(PUB_SIZE[0], 0.155 * n + 1.0))
        axm = None
    if axm is not None and not a.dots:
        axm.barh(y, mu[o], height=0.62, color=PUB_MID, edgecolor="none", zorder=3)
        axm.axvline(0, color=PUB_INK, linewidth=PUB_RULE_PT, zorder=4)
        axm.set_title("all frames", fontsize=PUB_FONT_PT - 1,
                      fontfamily=pub_font())
        axm.set_xlabel("where alignment\nmoves the sentence",
                       fontsize=PUB_FONT_PT - 1.5, fontfamily=pub_font())
        for sp in ("top", "right", "left"):
            axm.spines[sp].set_visible(False)
        axm.spines["bottom"].set_linewidth(PUB_RULE_PT)
        axm.grid(axis="x", color=PUB_GRAY, linewidth=PUB_RULE_PT * 0.6, zorder=0)
        axm.set_axisbelow(True)
        axm.tick_params(axis="both", length=2, labelsize=PUB_FONT_PT - 2.5)
        axx.set_title("by charge lift", fontsize=PUB_FONT_PT - 1,
                      fontfamily=pub_font())
        #: the shared axis still draws its own ticks and they read as a second
        #: column of marks between the panels
        axx.tick_params(axis="y", length=0, labelleft=False)
    if a.dose and not a.dots:
        axx.barh(y + 0.20, lowm[o], height=0.36, color="white",
                 edgecolor=PUB_MID, linewidth=PUB_RULE_PT, zorder=3)
        axx.barh(y - 0.20, topm[o], height=0.36, color=PUB_INK,
                 edgecolor="none", zorder=3)
    elif not a.dots:
        axx.barh(y, mu[o], height=0.62, color=PUB_INK, edgecolor="none",
                 zorder=3)
    axx.axvline(0, color=PUB_INK, linewidth=PUB_RULE_PT, zorder=4)
    #: the label is the CONTRAST, not the movement: the bar supplies the
    #: direction, and a directional label plus a signed bar states it twice
    #: and disagrees with itself whenever the mean is near zero
    (axm or axx).set_yticks(y)
    #: **THE LABEL IS BIDIRECTIONAL** (RH). "X / Y" reads as a ratio or a
    #: heading; "X <-> Y" says the row is an axis with two ends and that the
    #: marker's position on it is the answer.
    (axm or axx).set_yticklabels(["%s  <->  %s" % (short(V[i]["pole_x"]),
                                        short(V[i]["pole_y"])) for i in o],
                        fontsize=PUB_FONT_PT - 2.5, fontfamily=pub_font())
    (axm or axx).set_ylim(-0.8, n - 0.2)
    axx.tick_params(axis="both", length=2, labelsize=PUB_FONT_PT - 2)
    for s in ("top", "right", "left"):
        axx.spines[s].set_visible(False)
    axx.spines["bottom"].set_linewidth(PUB_RULE_PT)
    axx.grid(axis="x", color=PUB_GRAY, linewidth=PUB_RULE_PT * 0.6, zorder=0)
    axx.set_axisbelow(True)
    #: **NO ARROW GLYPHS.** The publication font has no U+2190/2192 and
    #: matplotlib silently substituted a tofu box, which reads as a stray
    #: symbol rather than a missing one. Words instead.
    #: **THE QUANTITY IS A MOVEMENT, NOT A POSITION** (RH). The Survey asked
    #: where the TWO lists sit relative to each other -- level 0 is "LIST 1
    #: wholly at pole_x, LIST 2 at pole_y" -- so every value already encodes
    #: both sides. Oriented to "which pole the base sits on", the aligned side
    #: is implied at the other end, which makes the number what ALIGNMENT DID.
    #: Labelling it "mean position of the base words" described one half of a
    #: relational measure as though the other half were absent, and invited a
    #: reader to ask what the aligned words scored. There is no separate
    #: aligned score; there is one displacement with a sign.
    axx.set_xlabel(("lowest vs highest\nthird of lift" if a.facet else
                    "where alignment moves the sentence\n"
                    "toward the left pole  <<  0  >>  toward the right pole"),
                   fontsize=PUB_FONT_PT - (1.5 if a.facet else 1),
                   fontfamily=pub_font())
    if a.dots:
        axx.legend(fontsize=PUB_FONT_PT - 2, frameon=False, handlelength=0.8,
                   loc="lower right", scatterpoints=1, borderpad=0.2)
    elif a.dose:
        (fig if a.facet else axx).legend(handles=[
            plt.Rectangle((0, 0), 1, 1, facecolor="white", edgecolor=PUB_MID,
                          linewidth=PUB_RULE_PT, label="lowest third of lift"),
            plt.Rectangle((0, 0), 1, 1, facecolor=PUB_INK, edgecolor="none",
                          label="highest third")],
            fontsize=PUB_FONT_PT - 2, frameon=False, handlelength=1.2,
            **({"loc": "outside lower center", "ncol": 2} if a.facet
               else {"loc": "lower right"}))
    #: **`tight_layout` DOES NOT RESERVE THE LABEL COLUMN UNDER `sharey`** --
    #: the 26 axis labels hang off the left edge of the plate and are simply
    #: cut. The label column is budgeted explicitly instead: at 4.8 in it wants
    #: about 1.35, which leaves ~1.6 per panel and is readable. Width is not
    #: the constraint; the labels are.
    #: `constrained` measures the rendered labels and reserves the column;
    #: hand-set margins were guesses and both of mine were wrong (labels still
    #: clipped at left=0.29, and an invented bottom formula left an inch of
    #: white). The legend goes OUTSIDE the axes for the same reason -- inside,
    #: it sat on top of the bars it was describing.
    if not (a.facet or a.dots):
        fig.tight_layout(pad=0.4)
    out = a.out or os.path.join(HERE, "figures",
                                "axis_bars%s%s%s%s.png"
                                % ("_dose" if a.dose else "",
                                   "_dots" if a.dots else "",
                                   "_facet" if a.facet else "",
                                   "_sig" if a.sig else ""))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    print("wrote %s" % save(fig, out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
