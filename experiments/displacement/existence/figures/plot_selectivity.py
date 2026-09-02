"""Content selectivity by lift: per-lineage slopes across lift bands.

    python experiments/displacement/existence/figures/plot_selectivity.py

Reads results/selectivity.json (from run.py --save). Draws per-lineage median
slopes (one dot per lineage) in each lift band, with the grand median and sign
count annotated. The gradient steepening from NULL at lift < 0 to p < 1e-5 at
lift > 0.5 IS the finding.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..", "..")))

DATA = os.path.join(HERE, "..", "results", "selectivity.json")
OUT = os.path.join(HERE, "selectivity_by_lift.png")


def main():
    import pandas as pd
    from plotnine import (ggplot, aes, geom_jitter, geom_hline, geom_segment,
                          geom_text, theme_minimal, labs, scale_color_manual,
                          scale_x_discrete, theme, element_text, element_blank,
                          coord_flip)

    d = json.load(open(DATA))
    rows = []
    for band in d["by_lift"]:
        if not band["per_lineage"]:
            continue
        for lin in band["per_lineage"]:
            rows.append({
                "band": band["band"],
                "slope": lin["slope"],
                "lineage": lin["lineage"],
            })
    df = pd.DataFrame(rows)

    band_order = ["< 0 (no lift)", "0-0.5 (low)", "0.5-1 (moderate)", "1-2 (high)"]
    df["band"] = pd.Categorical(df["band"], categories=band_order, ordered=True)
    df = df.dropna(subset=["band"])

    meds = df.groupby("band", observed=True)["slope"].median().reset_index()
    meds.columns = ["band", "med"]

    labels = []
    for band in d["by_lift"]:
        if band["band"] not in band_order:
            continue
        sig = "**" if band["p"] < 0.001 else ("*" if band["p"] < 0.05 else "")
        labels.append({
            "band": band["band"],
            "label": "%d/%d %s" % (band["neg"], band["pos"], sig),
            "p": band["p"],
        })
    ldf = pd.DataFrame(labels)
    ldf["band"] = pd.Categorical(ldf["band"], categories=band_order, ordered=True)

    from plotnine import geom_boxplot

    fig = (
        ggplot(df, aes(x="band", y="slope"))
        + geom_boxplot(width=0.5, fill="#2a2a3e", color="#555555",
                       outlier_shape="", alpha=0.6)
        + geom_jitter(width=0.2, size=1.2, alpha=0.5, color="#4e79a7")
        + geom_hline(yintercept=0, linetype="dashed", color="#888888", size=0.4)
        + geom_text(data=ldf, mapping=aes(x="band", label="label"),
                    y=df["slope"].max() * 1.05, size=8, color="#cccccc",
                    inherit_aes=False)
        + labs(
            title="Content selectivity by lift",
            subtitle="per-lineage median slope of delta ~ scene, 50 lineages\n"
                     "red bar = grand median · neg/pos = sign count · ** p < 0.001",
            x="lift band (dose - frame)",
            y="median within-cell slope (delta ~ scene)",
        )
        + theme_minimal()
        + theme(
            figure_size=(8, 4.5),
            plot_background=element_blank(),
            panel_grid_major_x=element_blank(),
            axis_text=element_text(size=9),
            plot_title=element_text(size=13, weight="bold"),
            plot_subtitle=element_text(size=9, color="#888888"),
        )
    )

    fig.save(OUT, dpi=300)
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
