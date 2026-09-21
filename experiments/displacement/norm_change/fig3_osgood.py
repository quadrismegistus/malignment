"""Figure 3 as a semantic differential. -> figures/fig3_norms_osgood_en.{png,pdf,caption.txt}

Replaces the dose-vs-marginal scatter. One row per scale; three markers a row:
down-triangle for the lowest third of charge lift, square for all prompts,
up-triangle for the highest third. Position is the median within-lineage change
base -> aligned in SD units, so **the square reproduces the scatter's vertical
coordinate exactly** -- checked at 18 of 18 scales -- and the triangle spread
stands in for its dose slope.

## POLES ARE NOT REORIENTED, AND THAT IS THE POINT

Each scale keeps its native direction, low pole left and high pole right. The
axis figure orients every row by its high-lift destination, which makes the
side of a marker a definition; here the side of every marker is a RESULT and
the caption needs no ordering sentence.

## ONE SD PER SCALE, FOR ALL THREE MARKERS

The between-lineage POPULATION stdev of the per-lineage medians -- sample stdev
misses the scatter by exactly sqrt(50/49). Dividing each band by its own SD
would put the three markers on three different rulers, which is the comparison
the row exists to make.
"""
import json, os, statistics as st, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

#: low pole, high pole. Warriner scales keep Warriner's names; ours keep the
#: scatter's. `v6:fit` reads "fits less well" because the scale runs 3.73-7.00
#: among movers and has no low end -- paper-claude, and the caption says so.
POLES = {
    "k_bodily_harm": ("No harm", "Bodily harm"),
    "k_transgressiveness": ("Unmarked", "Transgressive"),
    "k_concreteness": ("Abstract", "Concrete"),
    "k_register_level": ("Low register", "High register"),
    "k_vulgarity": ("Not vulgar", "Vulgar"),
    "warriner_arousal": ("Calm", "Aroused"),
    "warriner_valence": ("Unpleasant", "Pleasant"),
    "warriner_dominance": ("Submissive", "Dominant"),
    "v6:fit": ("Fits less well", "Fits the frame"),
    "v6:directedness": ("Undirected", "Directed"),
    "v6:makes_better": ("Does not improve", "Makes better"),
    "v6:makes_worse": ("Does not worsen", "Makes worse"),
    "v6:mundanity": ("Charged", "Mundane"),
    "v6:vocalisation": ("Silent", "Vocalized"),
}
#: paper-claude's picks, low pole then high
PICKS = {
    "k_bodily_harm": (("began", "gave"), ("kill", "stabbed")),
    "k_transgressiveness": (("asked", "started"), ("murder", "rape")),
    "k_concreteness": (("know", "thought"), ("needle", "horse")),
    "k_register_level": (("whacked", "chat"), ("rescind", "subsequently")),
    "k_vulgarity": (("made", "took"), ("fuck", "shit")),
    "warriner_arousal": (("rested", "quiet"), ("attack", "assault")),
    "warriner_valence": (("die", "hate"), ("smiled", "hugged")),
    "warriner_dominance": (("cry", "afraid"), ("laughed", "win")),
    "v6:fit": (("became", "flew"), ("whip", "clung")),
    "v6:directedness": (("noticed", "prayed"), ("harass", "abuse")),
    "v6:makes_better": (("stole", "hurt"), ("save", "forgive")),
    "v6:makes_worse": (("clean", "thank"), ("beat", "shot")),
    "v6:mundanity": (("strangle", "torture"), ("work", "sit")),
    "v6:vocalisation": (("pulled", "stared"), ("said", "screamed")),
}
_FAM = [("kill", "killed"), ("say", "said"), ("take", "took"),
        ("make", "made"), ("begin", "began"), ("give", "gave"),
        ("start", "started"), ("think", "thought"), ("know", "knew")]


def check_picks():
    """No word twice, no inflectional pair. -> the stem map, or raises."""
    import collections
    def stem(w):
        for f in _FAM:
            if w in f:
                return f[0]
        return w
    allw = [w for p in PICKS.values() for side in p for w in side]
    dup = [w for w, n in collections.Counter(stem(w) for w in allw).items()
           if n > 1]
    if dup:
        raise SystemExit("repeated pole words (by stem): %s" % ", ".join(dup))
    return len(allw)


def rows():
    """-> [(scale, square, low, high, sd)] in SD units, ordered by square."""
    byl = {s["scale"]: s for s in json.load(
        open(os.path.join(HERE, "results", "norms_by_lift_en.json")))["scales"]}
    ref = {}
    for t in ("levels", "contextual"):
        for s in json.load(open(os.path.join(
                HERE, "results", "%s_gated_en.json" % t)))["scales"]:
            ref[s["scale"]] = s
    out = []
    for sc in POLES:
        s, g = byl[sc], ref[sc]
        sd = st.pstdev(list(g["per_lineage"].values()))
        b = {x["band"]: x for x in s["bands"]}
        out.append((sc, g["median"] / sd,
                    b["low"]["median"] / sd, b["high"]["median"] / sd, sd))
    #: **DESCENDING, BECAUSE MATPLOTLIB'S y GROWS UPWARD.** Sorted ascending,
    #: the most negative row lands at y=0 and therefore at the BOTTOM -- the
    #: opposite of "most negative at top", and the kind of inversion that looks
    #: deliberate on the plate. Row 0 is drawn lowest, so the top row must be
    #: last in the list.
    out.sort(key=lambda r: -r[1])
    return out


def v6_frames():
    """{word: frames rated} for the v6 picks, so the caption can carry f."""
    import fig3_candidates as C
    v6 = C.v6_ratings()
    fr = {}
    for by in v6.values():
        for w, (_m, f) in by.items():
            fr[w] = max(fr.get(w, 0), f)
    return fr


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.font_manager import FontProperties
    from malignment.figure import (PUB_SIZE, PUB_FONT_PT, PUB_INK, PUB_MID,
                                   PUB_GRAY, PUB_FAINT, PUB_RULE_PT, pub_font,
                                   save)
    matplotlib.rcParams["font.family"] = pub_font()
    matplotlib.rcParams["font.sans-serif"] = [pub_font(), "DejaVu Sans"]
    matplotlib.rcParams["axes.unicode_minus"] = False

    n_words = check_picks()
    rs = rows()
    n = len(rs)
    fr = v6_frames()

    def lab(sc, side):
        name = POLES[sc][side]
        ws = PICKS[sc][side]
        if sc.startswith("v6:"):
            ws = ["%s (%d)" % (w, fr.get(w, 0)) for w in ws]
        return "%s\n(%s)" % (name, ", ".join(ws))

    fig, ax = plt.subplots(figsize=(PUB_SIZE[0], 0.30 * n + 1.05),
                           layout="constrained")
    y = np.arange(n)
    sq = np.array([r[1] for r in rs])
    lo = np.array([r[2] for r in rs])
    hi = np.array([r[3] for r in rs])
    e = np.concatenate([sq, lo, hi])
    pad = 0.06 * (e.max() - e.min())
    for i in range(n):
        ax.plot([e.min() - pad, e.max() + pad], [i, i], color=PUB_FAINT,
                linewidth=PUB_RULE_PT * 0.7, zorder=1, solid_capstyle="butt")
        ax.plot([lo[i], hi[i]], [i, i], color=PUB_GRAY,
                linewidth=PUB_RULE_PT * 1.6, zorder=2, solid_capstyle="butt")
    ax.scatter(lo, y, marker="v", s=17, facecolor=PUB_GRAY, edgecolor="none",
               zorder=3, label="lowest third of charge lift")
    ax.scatter(sq, y, marker="s", s=13, facecolor=PUB_MID, edgecolor="none",
               zorder=4, label="all prompts")
    ax.scatter(hi, y, marker="^", s=19, facecolor=PUB_INK, edgecolor="none",
               zorder=5, label="highest third")
    ax.axvline(0, color=PUB_INK, linewidth=PUB_RULE_PT, zorder=6)
    ax.set_yticks(y)
    ax.set_yticklabels([lab(r[0], 0) for r in rs],
                       fontsize=PUB_FONT_PT - 2.5, fontfamily=pub_font())
    r2 = ax.secondary_yaxis("right")
    r2.set_yticks(y)
    r2.set_yticklabels([lab(r[0], 1) for r in rs],
                       fontsize=PUB_FONT_PT - 2.5, fontfamily=pub_font())
    r2.tick_params(length=0)
    r2.spines["right"].set_visible(False)
    ax.set_ylim(-0.75, n - 0.25)
    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", length=2, labelsize=PUB_FONT_PT - 2)
    for t in ax.get_xticklabels():
        t.set_fontfamily(pub_font())
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_linewidth(PUB_RULE_PT)
    ax.grid(axis="x", color=PUB_GRAY, linewidth=PUB_RULE_PT * 0.6, zorder=0)
    ax.set_axisbelow(True)
    ax.set_xlabel("Median change from base to aligned, in SDs of the scale\n"
                  "Toward the left pole  <<  0  >>  Toward the right pole",
                  fontsize=PUB_FONT_PT - 1, fontfamily=pub_font())
    fig.legend(prop=FontProperties(family=pub_font(), size=PUB_FONT_PT - 2),
               frameon=False, handlelength=0.9, loc="outside lower center",
               ncol=3, scatterpoints=1, columnspacing=1.4, handletextpad=0.35)

    import collections as _c
    seen = _c.Counter()
    for t in fig.findobj(matplotlib.text.Text):
        if t.get_text().strip():
            seen[(t.get_fontname(), round(t.get_fontsize(), 1))] += 1
    print("  FONT AUDIT")
    for (fam, pt), k in sorted(seen.items()):
        print("    %-14s %4.1f pt x%-3d%s" % (fam, pt, k,
                                              "  <-- BELOW 6" if pt < 6 else ""))

    out = os.path.join(HERE, "figures", "fig3_norms_osgood_en.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    print("  wrote %s" % save(fig, out))

    meta = json.load(open(os.path.join(HERE, "results",
                                       "norms_by_lift_en.json")))
    cap = [
        "Figure 3. What alignment does to fourteen norm scales, and how it "
        "changes with charge.",
        "",
        "Each row is one scale, its two ends labelled on their own sides. "
        "Position is the median within-lineage change from base to aligned "
        "over 50 endpoint lineages, in standard deviations of that scale's "
        "between-lineage distribution. The square is all prompts and "
        "reproduces the vertical coordinate of the scatter it replaces; the "
        "triangles are the same median computed on the lowest and highest "
        "third of charge lift (T_base minus the frame's own rating), cut at "
        "%+.3f and %+.3f over %s gated prompt-lineage rows."
        % (meta["cuts"][0], meta["cuts"][1], format(meta["rows_gated"], ",")),
        "",
        "Scales keep their native direction, low pole left and high pole "
        "right, so the side of every marker is a result. Rows are ordered by "
        "the square, most negative at the top, so the figure reads from what "
        "alignment removes down to what it adds.",
        "",
        "Pole words illustrate each end among the words alignment moved: a "
        "word appears only if it moved in at least 50 prompt-lineage cells. "
        "For the six v6 scales, which rate a word in a particular frame "
        "rather than as a type, the number in brackets is how many frames the "
        "word was rated in.",
        "",
        "Coverage gate and population as in the scatter: minimum of the two "
        "arms' coverage at 0.20, the same 50 lineages, selection by "
        "Benjamini-Hochberg at 5 percent on both quantities over the "
        "eighteen-scale family, from which the four dispersion scales are "
        "omitted here as not independent of their parents.",
        "",
        "v6:fit runs 3.73 to 7.00 among moved words, so it has no true low "
        "end; its left pole is labelled 'fits less well' rather than 'does "
        "not fit'.",
        "",
        "%d pole words, none repeated and no inflectional pairs." % n_words,
    ]
    cp = out.replace(".png", ".caption.txt")
    open(cp, "w", encoding="utf-8").write("\n".join(cap) + "\n")
    print("  wrote %s" % cp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
