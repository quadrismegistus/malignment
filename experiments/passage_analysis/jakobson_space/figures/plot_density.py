"""2D density contours by category on the surprisal x drift plane.

    python experiments/passage_analysis/jakobson_space/figures/plot_density.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "fig_passage_map.data.json")
OUT = os.path.join(HERE, "jakobson_density.png")


def main():
    import pandas as pd
    from plotnine import (ggplot, aes, geom_density_2d, geom_point,
                          theme_minimal, labs, theme, element_text,
                          element_blank, scale_color_manual, guides,
                          guide_legend, facet_wrap, geom_vline, geom_hline)

    d = json.load(open(DATA))
    pts = d["points"]
    cats = d["cats"]

    rows = []
    for j in range(len(pts["x"])):
        c = cats[pts["cat"][j]]
        rows.append({
            "drift": pts["x"][j],
            "surprisal": pts["y"][j],
            "category": c["label"],
            "kind": c["kind"],
            "colour": c["colour"],
        })
    df = pd.DataFrame(rows)

    groups = [
        ("base", "#fa5252"),
        ("aligned", "#b197fc"),
        ("API", "#4dabf7"),
        ("c20 fiction", "#6f8f8a"),
        ("waking narrative", "#7d8ba0"),
        ("literary criticism", "#8a8f6f"),
        ("dreams", "#9b7b8a"),
        ("arxiv abstracts", "#8d9b6a"),
        ("philosophy", "#a08b5c"),
    ]
    color_map = {g: c for g, c in groups}
    import statistics as st
    cat_mean_y = {}
    for g, _ in groups:
        vals = df.loc[df["category"] == g, "surprisal"]
        if len(vals):
            cat_mean_y[g] = st.mean(vals)
    order = sorted([g for g, _ in groups], key=lambda g: -cat_mean_y.get(g, 0))
    df["category"] = pd.Categorical(df["category"], categories=order, ordered=True)
    df = df.dropna(subset=["category"])

    fig = (
        ggplot(df, aes(x="drift", y="surprisal"))
        + geom_point(alpha=0.15, size=0.4, color="#4e79a7")
        + geom_density_2d(alpha=0.8, size=0.5, color="#ff9da7")
        + geom_vline(xintercept=0, linetype="dashed", color="#444444", size=0.3)
        + geom_hline(yintercept=0, linetype="dashed", color="#444444", size=0.3)
        + facet_wrap("category", ncol=3)
        + labs(
            title="Jakobson space: density by source",
            subtitle="z-scored surprisal (y) x drift (x), faceted by category",
            x="drift (z) -- metonymic",
            y="surprisal (z) -- metaphoric",
        )
        + theme_minimal()
        + theme(
            figure_size=(12, 10),
            plot_background=element_blank(),
            strip_text=element_text(size=10, weight="bold"),
            axis_text=element_text(size=8),
            plot_title=element_text(size=14, weight="bold"),
            plot_subtitle=element_text(size=10, color="#888888"),
        )
    )

    fig.save(OUT, dpi=300)
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
