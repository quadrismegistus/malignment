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

Bar to the right: the base words sit at the LEFT pole, so alignment pushes
toward the right one. Length is the mean of a probability-weighted position on
a five-level scale, so |1.0| would be every relation placing the two lists
cleanly at opposite poles.
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


def short(s, n=22):
    s = s.split("—")[0].split(",")[0].strip()
    return s if len(s) <= n else s[:n - 1].rstrip() + "…"


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
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    M, L, V, ax = load(a.seed)
    mu = M.mean(0)
    q = np.quantile(L, [1 / 3, 2 / 3])
    lowm = M[L <= q[0]].mean(0)
    topm = M[L > q[1]].mean(0)

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
    fig, axx = plt.subplots(figsize=(PUB_SIZE[0], 0.155 * n + 1.0))
    y = np.arange(n)
    if a.dose:
        axx.barh(y + 0.20, lowm[o], height=0.36, color="white",
                 edgecolor=PUB_MID, linewidth=PUB_RULE_PT, zorder=3)
        axx.barh(y - 0.20, topm[o], height=0.36, color=PUB_INK,
                 edgecolor="none", zorder=3)
    else:
        axx.barh(y, mu[o], height=0.62, color=PUB_INK, edgecolor="none",
                 zorder=3)
    axx.axvline(0, color=PUB_INK, linewidth=PUB_RULE_PT, zorder=4)
    #: the label is the CONTRAST, not the movement: the bar supplies the
    #: direction, and a directional label plus a signed bar states it twice
    #: and disagrees with itself whenever the mean is near zero
    axx.set_yticks(y)
    axx.set_yticklabels(["%s  /  %s" % (short(V[i]["pole_x"]),
                                        short(V[i]["pole_y"])) for i in o],
                        fontsize=PUB_FONT_PT - 2.5, fontfamily=pub_font())
    axx.set_ylim(-0.8, n - 0.2)
    axx.tick_params(axis="both", length=2, labelsize=PUB_FONT_PT - 2)
    for s in ("top", "right", "left"):
        axx.spines[s].set_visible(False)
    axx.spines["bottom"].set_linewidth(PUB_RULE_PT)
    axx.grid(axis="x", color=PUB_GRAY, linewidth=PUB_RULE_PT * 0.6, zorder=0)
    axx.set_axisbelow(True)
    #: **NO ARROW GLYPHS.** The publication font has no U+2190/2192 and
    #: matplotlib silently substituted a tofu box, which reads as a stray
    #: symbol rather than a missing one. Words instead.
    axx.set_xlabel("mean position of the base words\n"
                   "left pole  <<  0  >>  right pole",
                   fontsize=PUB_FONT_PT - 1, fontfamily=pub_font())
    if a.dose:
        axx.legend(handles=[
            plt.Rectangle((0, 0), 1, 1, facecolor="white", edgecolor=PUB_MID,
                          linewidth=PUB_RULE_PT, label="lowest third of lift"),
            plt.Rectangle((0, 0), 1, 1, facecolor=PUB_INK, edgecolor="none",
                          label="highest third")],
            fontsize=PUB_FONT_PT - 2, frameon=False, loc="lower right")
    fig.tight_layout(pad=0.4)
    out = a.out or os.path.join(HERE, "figures",
                                "axis_bars%s.png" % ("_dose" if a.dose else ""))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    print("wrote %s" % save(fig, out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
