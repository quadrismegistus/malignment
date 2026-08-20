"""Figures for the three studies, from the saved artifacts only.

    python experiments/slot_ratings/plot.py            # all
    python experiments/slot_ratings/plot.py --only did

Every figure reads `results/long/levels_long.csv.gz` or a per-study results JSON
and computes nothing that a README does not already report. If a figure and a
README disagree, the figure is wrong.

## WHY THESE SHAPES

The difference-in-differences results are the hardest thing in the three READMEs
to read as numbers, and the reason is that a DiD is a DISTRIBUTION over lineages
while the tables give its mean and a p. The same row can be 21/33 with sign
p=0.16 and Wilcoxon p=0.028 -- magnitudes agreeing while directions do not --
which is unreadable as a bar and obvious as a strip. So the DiD figures plot the
points, one per lineage, with zero marked, and let the reader see whether a
significant mean is a consistent shift or two outliers.

Written into `<study>/figures/`, 300 dpi.

Institutional figures live in `institutional/plot.py`, not here.
"""

import argparse, json, os, sys
import warnings

HERE = os.path.dirname(os.path.abspath(__file__))
LONG = os.path.join(HERE, "results", "long", "levels_long.csv.gz")
warnings.filterwarnings("ignore")

BASE = None  # set in main once plotnine is imported


def theme():
    from plotnine import theme_minimal, theme, element_text, element_rect, element_line
    return (theme_minimal(base_size=9)
            + theme(figure_size=(9, 6),
                    plot_title=element_text(size=11, weight="bold", ha="left"),
                    plot_subtitle=element_text(size=8, color="#555555", ha="left"),
                    plot_caption=element_text(size=7, color="#777777", ha="left"),
                    strip_text=element_text(size=8, weight="bold"),
                    panel_grid_minor=element_line(size=0.2),
                    plot_background=element_rect(fill="white", color="white")))


def save(p, path, w=9, h=6):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    p.save(path, dpi=300, width=w, height=h, verbose=False)
    print("   %-58s %6.0f KB" % (os.path.relpath(path, HERE), os.path.getsize(path) / 1024))


# ---------------------------------------------------------------- DiD strips
def fig_did_identity():
    """The four named group contrasts: every lineage a point, zero marked."""
    import pandas as pd
    from plotnine import (ggplot, aes, geom_vline, geom_jitter, geom_point,
                          facet_grid, labs, scale_color_manual)
    rows = json.load(open(os.path.join(HERE, "identity/results/group_pairs.json")))["rows"]
    recs = []
    for r in rows:
        if not r.get("did_values"):
            continue
        for l, v in zip(r["lineages"], r["did_values"]):
            recs.append(dict(contrast="%s - %s" % (r["a"], r["b"]), scale=r["scale"],
                             lineage=l, did=v, sig=r["did_p"] < .05 if r["did_p"] else False))
    d = pd.DataFrame(recs)
    keep = ["interiority", "deliberation", "harm", "aggression", "directedness",
            "makes_worse", "vocalisation", "superego"]
    d = d[d.scale.isin(keep)]
    d["scale"] = pd.Categorical(d.scale, categories=keep[::-1])
    mu = d.groupby(["contrast", "scale"], observed=True).did.mean().reset_index()
    p = (ggplot(d, aes("did", "scale", color="sig"))
         + geom_vline(xintercept=0, color="#bbbbbb", size=0.5)
         + geom_jitter(height=0.18, width=0, alpha=0.35, size=0.9)
         #: THE MEAN IS COMPUTED HERE, not by stat_summary. stat_summary inherits
         #: the colour aesthetic and so grouped by (scale, sig) AND by x, drawing
         #: one marker per POINT rather than one per row -- which buried the
         #: cloud under a line of diamonds and looked like a dense result.
         + geom_point(mu, aes("did", "scale"), inherit_aes=False,
                      shape="D", size=2.6, color="black")
         + facet_grid("~contrast")
         + scale_color_manual({True: "#c0392b", False: "#7f8c8d"},
                              name="sign test p<0.05")
         + labs(title="Identity: does alignment change the gap between two groups?",
                subtitle="One point per lineage. Positive = the first group gained "
                         "relative to the second. Black diamond = the mean.",
                x="difference-in-differences  (aligned gap minus base gap)", y="",
                caption="identity/results/group_pairs.json. 14-20 lineages per "
                        "contrast. A significant mean with points either side of "
                        "zero is magnitude without consistency.")
         + theme())
    save(p, os.path.join(HERE, "identity/figures/did_group_contrasts.png"), 11, 5.5)


def fig_did_sexual():
    """The 5 directional sexual sets: base gap and its change, per lineage."""
    import pandas as pd
    from plotnine import (ggplot, aes, geom_vline, geom_jitter, geom_point,
                          facet_grid, labs, scale_color_manual)
    rows = json.load(open(os.path.join(HERE, "sexual/results/layer2b.json")))["rows"]
    recs = []
    for r in rows:
        for lab, vals, pv in (("base gap", r.get("base_values"), r.get("base_p")),
                              ("change in gap", r.get("delta_values"), r.get("delta_p"))):
            for v in (vals or []):
                recs.append(dict(pair=r["pair"], scale=r["scale"], quantity=lab,
                                 value=v, sig=(pv or 1) < .05))
    d = pd.DataFrame(recs)
    keep = ["genitality", "charge", "explicitness", "body_distance", "euphemism"]
    d = d[d.scale.isin(keep)]
    d["scale"] = pd.Categorical(d.scale, categories=keep[::-1])
    d["quantity"] = pd.Categorical(d.quantity, categories=["base gap", "change in gap"])
    mu = d.groupby(["pair", "quantity", "scale"], observed=True).value.mean().reset_index()
    p = (ggplot(d, aes("value", "scale", color="sig"))
         + geom_vline(xintercept=0, color="#bbbbbb", size=0.5)
         + geom_jitter(height=0.18, width=0, alpha=0.3, size=0.8)
         + geom_point(mu, aes("value", "scale"), inherit_aes=False,
                      shape="D", size=2.2, color="black")
         + facet_grid("quantity~pair", scales="free_x")
         + scale_color_manual({True: "#c0392b", False: "#7f8c8d"},
                              name="sign test p<0.05")
         + labs(title="Sexual: the male-object / female-object gap, and whether "
                      "alignment moves it",
                subtitle="M->F minus F->M. Negative = the female-object slot scores "
                         "lower. One point per lineage, 33 per set. Black diamond = mean.",
                x="scale points", y="",
                #: facet_grid(scales="free_x") varies x by COLUMN, so a pair's
                #: two rows SHARE a scale. That is the point: the change row is
                #: visibly small against the base row above it rather than
                #: rescaled to look comparable.
                caption="sexual/results/layer2b.json. Each pair's two rows share "
                        "an x scale, so the change is drawn against the base gap "
                        "it is a change in. Base gaps reach 2 scale points; the "
                        "changes sit on zero.")
         + theme())
    save(p, os.path.join(HERE, "sexual/figures/did_directional_sets.png"), 12, 6)


# ------------------------------------------------------- amplification scatter
def fig_amplification():
    """pray: base against aligned, one point per group. The diagonal is 'no change'."""
    import pandas as pd
    from plotnine import (ggplot, aes, geom_abline, geom_point, geom_text, labs,
                          scale_x_log10, scale_y_log10, scale_color_manual)
    rows = json.load(open(os.path.join(HERE, "identity/results/base_side.json")))["rows"]
    d = pd.DataFrame(rows).groupby("group")[["p_base_pray", "p_aligned_pray"]].mean()
    d = d.reset_index()
    d = d[d.p_base_pray > 0]
    d["moved"] = (d.p_aligned_pray > d.p_base_pray).map(
        {True: "alignment raised it", False: "alignment lowered it"})
    #: label everything: the unlabelled lower-left cluster is where the
    #: "the low get lower" half of the claim lives, and leaving it anonymous
    #: made the figure look like a story about three religions.
    d["label"] = d.group
    d = d.sort_values("p_base_pray").reset_index(drop=True)
    step = d.index % 4
    d["lab_y"] = d.p_aligned_pray * step.map({0: 1.28, 1: 0.78, 2: 1.28, 3: 0.78})
    d["lab_ha"] = step.map({0: "right", 1: "right", 2: "left", 3: "left"})
    p = (ggplot(d, aes("p_base_pray", "p_aligned_pray"))
         + geom_abline(slope=1, intercept=0, color="#bbbbbb", size=0.5)
         + geom_point(aes(color="moved"), size=2.4, alpha=0.9)
         #: labels staggered by rank rather than by adjustText, which is not
         #: installed and is not worth a new dependency for one figure. The
         #: middle of this cloud is dense, so alternating the offset is the
         #: difference between four readable labels and four overlapping ones.
         + geom_text(aes(label="label", y="lab_y", ha="lab_ha"), size=6,
                     color="#34495e")
         + scale_color_manual({"alignment raised it": "#c0392b",
                               "alignment lowered it": "#2980b9"}, name="")
         #: expand the panel: "Christians" and "Russians" sit at the extremes and
         #: their labels were clipped by the default 5% margin.
         + scale_x_log10(expand=(0.14, 0)) + scale_y_log10(expand=(0.10, 0))
         + labs(title="Identity: alignment sharpens an ordering the base already has",
                subtitle="`pray` in the frame 'Three <group> came into the room and "
                         "started to ___'. One point per group, mean over lineages.",
                x="p(pray), base model   [log]", y="p(pray), aligned model   [log]",
                caption="identity/results/base_side.json. The diagonal is 'no "
                        "change'. Base-to-aligned rank correlation is 0.970: the "
                        "aligned ordering IS the base ordering, moved apart.")
         + theme())
    save(p, os.path.join(HERE, "identity/figures/pray_amplification.png"), 7.5, 6)


# ------------------------------------------------------ per-scenario sign counts
# --------------------------------------------------------- layer 1, sexual
def fig_sexual_layer1():
    """Every prompt moves the same way. 16 prompts, 9 scales."""
    import pandas as pd
    from plotnine import (ggplot, aes, geom_vline, geom_point, labs, facet_wrap,
                          scale_color_manual, scale_shape_manual)
    d = pd.DataFrame(json.load(open(os.path.join(
        HERE, "sexual/results/levels.json")))["rows"])
    d = d[d.p.notna()]
    d["sig"] = d.p < .05
    d["label"] = d.pair + " / " + d.gender.str[0]
    order = ["euphemism", "explicitness", "genitality", "charge", "body_distance",
             "orality", "tactility", "exposure", "incorporation"]
    d = d[d.scale.isin(order)]
    d["scale"] = pd.Categorical(d.scale, categories=order)
    p = (ggplot(d, aes("delta", "label", color="sig"))
         + geom_vline(xintercept=0, color="#bbbbbb", size=0.5)
         + geom_point(size=1.6, alpha=0.9)
         + facet_wrap("~scale", scales="free_x", ncol=3)
         + scale_color_manual({True: "#c0392b", False: "#bdc3c7"},
                              name="Wilcoxon p<0.05")
         + labs(title="Sexual: alignment moves all 16 frames the same way",
                subtitle="Base-to-aligned change per prompt, tested against that "
                         "prompt's 33 lineages. Nothing pooled, nothing paired.",
                x="change in mass-weighted level (scale points)", y="",
                caption="sexual/results/levels.json. Every scale that reaches "
                        "significance does so in one direction: euphemism 12 up of "
                        "13, explicitness 9 down of 9, genitality 8 down of 8.")
         + theme())
    save(p, os.path.join(HERE, "sexual/figures/layer1_all_prompts.png"), 11, 8)


#: `fig_per_scenario` MOVED to institutional/plot.py on 2026-08-20 (RH), so the
#: institutional figures are produced inside the institutional folder. Its output
#: was byte-identical across the move. This file now draws identity and sexual.
FIGS = {"did": [fig_did_identity, fig_did_sexual],
        "amplification": [fig_amplification],
        "layer1": [fig_sexual_layer1]}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=sorted(FIGS))
    a = ap.parse_args(argv)
    todo = FIGS[a.only] if a.only else [f for v in FIGS.values() for f in v]
    for fn in todo:
        print("%s" % fn.__name__)
        try:
            fn()
        except Exception as e:
            print("   FAILED %s: %s" % (type(e).__name__, str(e)[:160]))


if __name__ == "__main__":
    main()
