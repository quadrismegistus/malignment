"""Simplified 2D density: base, aligned, fiction, dreams, waking narrative.

    python experiments/passage_analysis/jakobson_space/figures/plot_density_simple.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "fig_passage_map.data.json")
OUT = os.path.join(HERE, "jakobson_density_simple.png")


def main():
    import pandas as pd
    from plotnine import (ggplot, aes, geom_density_2d, geom_point,
                          theme_minimal, labs, theme, element_text,
                          element_blank, scale_color_manual, guides,
                          guide_legend, geom_vline, geom_hline,
                          scale_fill_manual)

    d = json.load(open(DATA))
    pts = d["points"]
    cats = d["cats"]

    keep = {"base", "aligned", "API", "c20 fiction", "dreams", "waking narrative"}
    colors = {
        "base": "#fa5252",
        "aligned": "#b197fc",
        "API": "#4dabf7",
        "c20 fiction": "#59a14f",
        "dreams": "#edc949",
        "waking narrative": "#4e79a7",
    }

    rows = []
    for j in range(len(pts["x"])):
        c = cats[pts["cat"][j]]
        if c["label"] in keep:
            rows.append({
                "drift": pts["x"][j],
                "surprisal": pts["y"][j],
                "source": c["label"],
            })
    df = pd.DataFrame(rows)

    from plotnine import facet_wrap

    order = ["base", "aligned", "API", "c20 fiction", "dreams", "waking narrative"]
    sampled = []
    for src in order:
        sub = df[df["source"] == src]
        sampled.append(sub.sample(n=min(500, len(sub)), random_state=42))
    df = pd.concat(sampled, ignore_index=True)
    df["source"] = pd.Categorical(df["source"], categories=order, ordered=True)

    fig = (
        ggplot(df, aes(x="drift", y="surprisal"))
        + geom_point(aes(color="source"), alpha=0.3, size=0.4, show_legend=False)
        + geom_density_2d(aes(color="source"), alpha=0.8, size=0.6, show_legend=False)
        + geom_vline(xintercept=0, linetype="dashed", color="#444444", size=0.3)
        + geom_hline(yintercept=0, linetype="dashed", color="#444444", size=0.3)
        + scale_color_manual(values=colors)
        + facet_wrap("source", ncol=3)
        + labs(
            title="Jakobson space",
            subtitle="base and aligned models against human registers and API (ordered by mean surprisal)",
            x="drift (z)",
            y="surprisal (z)",
        )
        + theme_minimal()
        + theme(
            figure_size=(11, 7),
            plot_background=element_blank(),
            strip_text=element_text(size=11, weight="bold"),
            axis_text=element_text(size=8),
            axis_title=element_text(size=10),
            plot_title=element_text(size=14, weight="bold"),
            plot_subtitle=element_text(size=9, color="#888888"),
        )
    )

    fig.save(OUT, dpi=300)
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
