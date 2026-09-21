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

**`--orient` PUTS THE ALIGNED POLE ON THE RIGHT OF EVERY ROW AND IS NOT THE
DEFAULT.** RH asked for it, looked at it, and reverted it himself: oriented,
`k_bodily_harm` draws as "Bodily harm -> No harm", which reads backwards,
because the scale's own high end IS harm and flipping the row flips the pole
NAMES with it. A row whose left label is the high end of its own scale costs
more than the tidy all-positive axis buys. The flag stays so the comparison is
reachable; the default is the native direction.

## --dose: THE SAME FOURTEEN ROWS IN THE SCATTER'S METRIC

`--dose` draws one marker per row at the scatter's x -- `med_slope / sd(slopes)`
over the 50 lineages -- because THIS PLATE CANNOT SHOW `v6:vocalisation` AND
THAT IS A PROPERTY OF THE ESTIMATOR, not of the norm. Vocalisation carries the
roster's most consistent dose response (45 of 50 lineages, p=4.2e-09) and lands
on this plate as a grey triangle at -0.27 against a square on zero, because a
median of per-lineage medians is clipped by ties: 21 of 50 lineages sit at
exactly 0.000 marginally and 27 of 50 do in the top band.

**THE TWO PLATES DO NOT AGREE IN RAW UNITS AND SHOULD NOT BE SAID TO.** The
observed low-to-high band-median difference is 0.0054 norm-points; the fitted
slope over the actual band separation (band mean lifts -0.203 and +0.952) says
0.052. The bands recover a TENTH of what the fit implies -- the median clipped
by ties at one end, OLS pulled by lift's long right tail at the other. The gap
is the finding about the instrument, and an earlier version of this file said
the two agreed.

**ONE RULER PER PLATE, AND IT IS NAMED ON THE PLATE.** `--dose` does not also
draw the marginal: that is the scatter's y, a different denominator, and this
whole line of work started from two plates whose denominators differed
silently. The marginal is named in words in the caption for the rows where it
is zero.

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


def slopes():
    """{scale: (med_slope, sd_slopes, ratio)} -- THE SCATTER'S OWN NUMBERS.

    Read from `plot_fields.load`, which is what draws the scatter, so the
    ratio here is its x coordinate by construction rather than by agreement.
    """
    import plot_fields as P
    out = {}
    for t in ("levels", "contextual"):
        d, _, _ = P.load(table=t, top=999, pmax=1.01, min_lin=0,
                         panel="v6", gated=True)
        for r in d:
            out[r["field"].split("  (")[0]] = (r["med"], r["sd"],
                                               r["med"] / r["sd"], r["p"])
    return out


def fitted_vs_observed():
    """The diagnostic table. -> [(scale, ties, sq, obs, fit, ratio, signflip)]

    **WHY THIS EXISTS AND WHY `--fitted` IS NOT THE DEFAULT.** theorymachines
    asked for the triangles to be drawn from the fit rather than from band
    medians -- square plus med_slope times (band mean lift minus all-prompt
    mean lift), in the scale's SD units -- so that the row plots the scatter's
    own two numbers. It is the right instinct and it does not survive contact
    with the denominator:

        k_vulgarity   42 of 50 lineages tied, sd of the per-lineage marginal
                      medians 0.0004, fitted triangles at +17.5 and -23.1 SD
        k_bodily_harm  3 ties, so tie clipping explains nothing, and the fit
                      puts the LOW triangle at +2.36 against an observed band
                      median of -0.75 -- OPPOSITE SIGN

    Five of the fourteen rows have a fitted low triangle whose sign disagrees
    with the observed one. On a plate whose whole virtue is that the side of
    every marker is a result, that is fatal: the fitted marker would put a
    result on the wrong side of zero.

    **THE STRUCTURAL REASON, WHICH IS THE ANSWER TO "WHY WAS IT A SCATTER".**
    The square is in SDs of the per-lineage MARGINAL MEDIANS. Any dose quantity
    is in slope units, whose between-lineage SD is a different number with no
    fixed relation to the first -- across these fourteen rows the ratio of the
    two spans a factor of about fifty. Dividing a lift-scaled slope by the
    marginal SD is therefore not a conversion, it is a collision. The scatter
    used two axes because two axes are what the quantities support, and any
    single-axis remake either keeps one statistic on all three markers (the
    default here, at the cost of tie clipping) or smuggles in a second ruler.

    The ratio column separates the two causes cleanly, which is the use this
    table has: rows with many ties (vocalisation 21, directedness 19,
    vulgarity 42) disagree because the MEDIAN is clipped, and the fit is the
    better estimate. Rows with almost none (bodily harm 3, transgressiveness 2,
    fit 2) disagree because the FIT overshoots, OLS being pulled by lift's long
    right tail and then evaluated at a band mean that sits outside where most
    of the band's rows are.
    """
    meta = json.load(open(os.path.join(HERE, "results",
                                       "norms_by_lift_en.json")))
    byl = {s["scale"]: s for s in meta["scales"]}
    ref = _ref()
    sl = slopes()
    LM, LB = meta["lift_mean"], meta["lift_band_mean"]
    out = []
    for sc in POLES:
        g, s, sd = ref[sc], byl[sc], _sd(ref[sc])
        b = {x["band"]: x for x in s["bands"]}
        sq = g["median"] / sd
        olo, ohi = b["low"]["median"] / sd, b["high"]["median"] / sd
        B = sl[sc][0]
        flo = sq + B * (LB[0] - LM) / sd
        fhi = sq + B * (LB[2] - LM) / sd
        obs = abs(b["high"]["median"] - b["low"]["median"])
        fit = abs(B * (LB[2] - LB[0]))
        out.append((sc, s["ties"], sq, (olo, ohi), (flo, fhi),
                    (fit / obs if obs > 1e-12 else float("inf")),
                    (olo < 0) != (flo < 0)))
    return out


def _ref():
    r = {}
    for t in ("levels", "contextual"):
        for s in json.load(open(os.path.join(
                HERE, "results", "%s_gated_en.json" % t)))["scales"]:
            r[s["scale"]] = s
    return r


def _sd(g):
    return st.pstdev(list(g["per_lineage"].values()))


def rows(orient=False, mode="bands"):
    """-> [(scale, square, low, high, sd, flipped)] in SD units.

    **`orient=True` PUTS THE ALIGNED SIDE ON THE RIGHT OF EVERY ROW** (RH), by
    flipping any scale whose median change is negative and swapping its pole
    names and pole words with it. The left pole is then where the base sits and
    the right is where alignment takes it, on all fourteen rows.

    **AND IT CHANGES WHAT THE AXIS MEANS.** Unoriented, a position is "which
    way did this scale move", and the side of every marker is a result.
    Oriented, the SQUARE is positive by construction -- that is the definition
    of the row -- and only its LENGTH is a result. The triangles keep both:
    a triangle left of zero means that lift band moved the scale the OTHER WAY
    from the corpus as a whole, which is a finding and the only thing on the
    plate whose side still carries information.

    `orient=False` restores paper-claude's specification, under which every
    marker's side is a result and no row is flipped.
    """
    meta = json.load(open(os.path.join(HERE, "results",
                                       "norms_by_lift_en.json")))
    byl = {s["scale"]: s for s in meta["scales"]}
    ref = _ref()
    if mode == "z":
        zz = {x["scale"]: x for x in json.load(open(os.path.join(
            HERE, "results", "norms_levels_z_en.json")))["scales"]}
        out = []
        for sc in POLES:
            b = {x["band"]: x for x in zz[sc]["bands"]}
            #: **MEAN WITHIN THE LINEAGE BY DEFAULT** (RH). `--z-median`
            #: restores the median. The two are different questions and on
            #: `v6:vocalisation` they answer in opposite directions, both
            #: significant -- see `_z_caption`.
            f_ = "move_z" if "--z-median" in sys.argv else "move_mean_z"
            sq, lo, hi = (b["all"][f_], b["low"][f_], b["high"][f_])
            f = orient and sq < 0
            if f:
                sq, lo, hi = -sq, -lo, -hi
            out.append((sc, sq, lo, hi, zz[sc]["sd"], f))
        out.sort(key=lambda r: r[1], reverse=not orient)
        return out
    sl = slopes() if mode == "fitted" else None
    LM, LB = meta["lift_mean"], meta["lift_band_mean"]
    out = []
    for sc in POLES:
        s, g = byl[sc], ref[sc]
        sd = _sd(g)
        b = {x["band"]: x for x in s["bands"]}
        sq = g["median"] / sd
        if mode == "fitted":
            B = sl[sc][0]
            lo = sq + B * (LB[0] - LM) / sd
            hi = sq + B * (LB[2] - LM) / sd
        else:
            lo, hi = b["low"]["median"] / sd, b["high"]["median"] / sd
        f = orient and sq < 0
        if f:
            sq, lo, hi = -sq, -lo, -hi
        out.append((sc, sq, lo, hi, sd, f))
    #: **MATPLOTLIB'S y GROWS UPWARD, SO ROW 0 IS DRAWN LOWEST** and whatever
    #: should sit at the top must come LAST. The two modes want opposite ends
    #: at the top, so the direction is not a constant:
    #:
    #:     native    most negative at top -- what alignment REMOVES read down
    #:               to what it adds, which is the ordering the spec asked for
    #:     oriented  every square is positive, so the ordering is by how far
    #:               alignment moves the scale, largest at top
    #:
    #: **THIS WAS ASCENDING IN BOTH MODES**, which put native's most negative
    #: row at the BOTTOM while the caption said top. It went unseen because
    #: every plate shipped in the interim was oriented, where ascending is
    #: right -- a defect parked in the branch nobody was rendering.
    out.sort(key=lambda r: r[1], reverse=not orient)
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


def draw_dose():
    """The companion plate, ONE RULER, named on the plate. -> figures/fig3_dose_osgood_en.*

    RH asked for a version of the row plate in the scatter's metric, because
    `v6:vocalisation` carries the roster's most consistent dose response and
    the band-median plate cannot render it (21 of 50 lineages tied at exactly
    zero; see `fitted_vs_observed`).

    **ONE MARKER PER ROW AND NO SECOND QUANTITY.** The marginal is the
    scatter's VERTICAL ruler and is not drawn here at any size, because this
    entire line of work began with two plates whose denominators differed
    without saying so. It is named in words in the caption for the rows where
    it is zero, which is the only place a reader needs it.

    **AND THE RULER IS ON THE PLATE, NOT IN THE CAPTION** (theorymachines).
    The x label says what the quantity is divided by. A reader who never opens
    the caption cannot mistake this axis for scale points.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.font_manager import FontProperties
    import plot_fields as P
    from malignment.figure import (PUB_SIZE, PUB_FONT_PT, PUB_INK, PUB_GRAY,
                                   PUB_FAINT, PUB_RULE_PT, pub_font, save)
    matplotlib.rcParams["font.family"] = pub_font()
    matplotlib.rcParams["font.sans-serif"] = [pub_font(), "DejaVu Sans"]
    matplotlib.rcParams["axes.unicode_minus"] = False

    n_words = check_picks()
    #: the published scatter's own selection: BH at 5% over the gated family,
    #: `either` axis. Intersected with POLES so the row set is Figure 3's.
    xy = {r["scale"]: r for r in P.load_xy(panel="v6", gated=True,
                                           sig="either", alpha=0.05,
                                           correct="bh")}
    ref = _ref()
    miss = [k for k in POLES if k not in xy]
    if miss:
        raise SystemExit("not on the scatter: %s" % ", ".join(miss))
    #: descending, so matplotlib's upward y puts the most negative at the TOP
    #: -- the same reading order as the band plate: what alignment pushes away
    #: from at high lift, read down to what it pushes toward.
    rs = sorted(POLES, key=lambda k: xy[k]["x"], reverse=True)
    n = len(rs)

    def lab(sc, side):
        return "%s\n(%s)" % (POLES[sc][side], ", ".join(PICKS[sc][side]))

    fig, ax = plt.subplots(figsize=(PUB_SIZE[0], 0.30 * n + 1.05),
                           layout="constrained")
    y = np.arange(n)
    x = np.array([xy[k]["x"] for k in rs])
    pad = 0.08 * (x.max() - x.min())
    for i in range(n):
        ax.plot([x.min() - pad, x.max() + pad], [i, i], color=PUB_FAINT,
                linewidth=PUB_RULE_PT * 0.7, zorder=1, solid_capstyle="butt")
        ax.plot([0, x[i]], [i, i], color=PUB_GRAY,
                linewidth=PUB_RULE_PT * 1.6, zorder=2, solid_capstyle="butt")
    ax.scatter(x, y, marker="o", s=16, facecolor=PUB_INK, edgecolor="none",
               zorder=4)
    ax.axvline(0, color=PUB_INK, linewidth=PUB_RULE_PT, zorder=6)
    ax.set_yticks(y)
    ax.set_yticklabels([lab(k, 0) for k in rs],
                       fontsize=PUB_FONT_PT - 2.5, fontfamily=pub_font())
    r2 = ax.secondary_yaxis("right")
    r2.set_yticks(y)
    r2.set_yticklabels([lab(k, 1) for k in rs],
                       fontsize=PUB_FONT_PT - 2.5, fontfamily=pub_font())
    r2.tick_params(length=0)
    r2.spines["right"].set_visible(False)
    ax.set_ylim(-0.75, n - 0.25)
    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", length=2, labelsize=PUB_FONT_PT - 2)
    for t in ax.get_xticklabels():
        t.set_fontfamily(pub_font())
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.spines["bottom"].set_linewidth(PUB_RULE_PT)
    ax.grid(axis="x", color=PUB_GRAY, linewidth=PUB_RULE_PT * 0.6, zorder=0)
    ax.set_axisbelow(True)
    ax.set_xlabel("Median lineage slope of the norm on charge lift, divided "
                  "by its own\nbetween-lineage SD -- the scatter\'s horizontal "
                  "ruler, and the only\nquantity on this plate\n"
                  "At high lift alignment pushes toward the left pole  <<  0 "
                  " >>  toward the right pole",
                  fontsize=PUB_FONT_PT - 2, fontfamily=pub_font())

    import collections as _c
    seen = _c.Counter()
    for t in fig.findobj(matplotlib.text.Text):
        if t.get_text().strip():
            seen[(t.get_fontname(), round(t.get_fontsize(), 1))] += 1
    print("  FONT AUDIT")
    for (fam, pt), k in sorted(seen.items()):
        print("    %-14s %4.1f pt x%-3d%s" % (fam, pt, k,
                                              "  <-- BELOW 6" if pt < 6 else ""))
    out = os.path.join(HERE, "figures", "fig3_dose_osgood_en.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    print("  wrote %s" % save(fig, out))

    zero = [POLES[k][1] for k in rs if abs(ref[k]["median"]) < 1e-12]
    cap = [
        "Figure 3b. How strongly each norm answers to charge, on the "
        "fourteen scales of Figure 3.",
        "",
        "One marker per scale. Position is the median per-lineage slope of the "
        "base-to-aligned change on charge lift over 50 endpoint lineages, "
        "divided by the between-lineage standard deviation of those slopes. "
        "It is the horizontal coordinate of the dose scatter, unchanged, and "
        "it is the ONLY quantity drawn here.",
        "",
        "IT IS NOT A SIZE. A scale whose fifty lineages agree scores high "
        "whether or not its slope is large: register level and bodily harm sit "
        "at 0.66 and -0.70 on raw median slopes of +0.0082 and -0.0387, a "
        "factor of 4.7 apart. Read the axis as how reliably a norm answers to "
        "charge, and the caption below for how far it moves.",
        "",
        "The marginal change -- whether the norm moves at all on the typical "
        "prompt -- is the scatter's VERTICAL ruler, a different denominator, "
        "and is deliberately not drawn on this plate. "
        + ("Its MEDIAN is exactly zero for %s -- which is not the same as "
           "no marginal movement, and should not be written as though it "
           "were: on vocalisation the sign test over the untied lineages is "
           "p=0.008. A median of zero on a tie-dominated scale is a "
           "quantized estimator landing on the tie pile."
           % ", ".join(zero) if zero else ""),
        "",
        "Vocalisation is the case this plate exists for. Its marginal median "
        "is zero and 21 of 50 lineages are tied there, so Figure 3 can only "
        "draw it at -0.27 SD and flat; the slope is +0.0448 scale points per "
        "unit of lift with 45 of 50 lineages positive, p=4.2e-09. The sign "
        "test on the marginal is not null either, 22 down against 7 up of 29 "
        "untied, p=0.008: alignment makes the typical completion less vocal, "
        "and spends that as charge rises.",
        "",
        "Selection, population and gate as in Figure 3 and the scatter: 50 "
        "lineages, English, coverage at 0.20 on the minimum of the two arms, "
        "Benjamini-Hochberg at 5 percent on either quantity over the "
        "eighteen-scale family, four dispersion scales omitted.",
        "",
        "Lineages with a positive slope, of 50: "
        + ", ".join("%s %d" % (POLES[k][1], _up(k)) for k in rs) + ".",
        "",
        "%d pole words, none repeated and no inflectional pairs." % n_words,
    ]
    cp = out.replace(".png", ".caption.txt")
    open(cp, "w", encoding="utf-8").write("\n".join(cap) + "\n")
    print("  wrote %s" % cp)
    return 0


def _up(k):
    """Lineages with a positive slope, from the dose table."""
    import plot_fields as P
    for t in ("levels", "contextual"):
        d, _, _ = P.load(table=t, top=999, pmax=1.01, min_lin=0,
                         panel="v6", gated=True)
        for r in d:
            if r["field"].split("  (")[0] == k:
                return r.get("up", 0)
    return 0


def _v6_min():
    """Fewest frames any v6 pole word was rated in. -> int

    Replaces the per-label "(1050)" decoration: the provenance fact that a v6
    rating is frame-specific is worth one clause in the caption, not a number
    on eight of the twenty-eight labels.
    """
    fr = v6_frames()
    return min(fr.get(w, 0) for sc in PICKS if sc.startswith("v6:")
               for side in PICKS[sc] for w in side)


def _zsd(scale):
    """The norm's own SD in rating points, for converting z back."""
    for x in json.load(open(os.path.join(
            HERE, "results", "norms_levels_z_en.json")))["scales"]:
        if x["scale"] == scale:
            return x["sd"]
    raise KeyError(scale)


def _zb(scale, band="all"):
    """One band record from the z artifact, for the caption."""
    z = json.load(open(os.path.join(HERE, "results",
                                    "norms_levels_z_en.json")))
    for x in z["scales"]:
        if x["scale"] == scale:
            for bb in x["bands"]:
                if bb["band"] == band:
                    return bb
    raise KeyError(scale)


def _z_caption(out, rs, meta, n_words):
    """Caption for `--z`. Its own function because almost nothing carries over.

    The band-median caption says the square reproduces the scatter's vertical
    coordinate and then spends a paragraph on tie counts. **NEITHER IS TRUE
    HERE**: the quantity is a different one, and medians of LEVELS are
    continuous, so the tie pile that clipped `v6:vocalisation` and
    `k_vulgarity` does not exist on this plate. Reusing the caption with the
    numbers swapped is how a convention dies crossing between two artifacts.
    """
    z = json.load(open(os.path.join(HERE, "results",
                                    "norms_levels_z_en.json")))
    zz = {x["scale"]: x for x in z["scales"]}
    big = max(rs, key=lambda r: abs(r[1]))
    span = max(max(abs(r[2]), abs(r[3])) for r in rs)
    cap = [
        "Figure 3z. What alignment does to fourteen norm scales, measured "
        "against the spread of each norm itself.",
        "",
        "Each row is one scale, its two ends labelled on their own sides. "
        "Position is the move from base to aligned -- averaged over the "
        "prompts of a lineage, then the median over the 50 endpoint "
        "lineages -- divided by the standard deviation of that "
        "norm's own values -- pooled over the base and aligned ratings of "
        "every gated row for the scale, so neither arm is the anchor. The "
        "square is all prompts; the triangles are the same quantity on the "
        "lowest and highest third of charge lift, cut at %+.3f and %+.3f."
        % (meta["cuts"][0], meta["cuts"][1]),
        "",
        "ONE RULER FOR EVERY ROW, WHICH IS THE POINT. The companion plate "
        "divides each row by the spread of its own CHANGES, a denominator "
        "that ranges over a factor of 250 across these fourteen scales, so "
        "its rows cannot be compared with each other. Here one unit means the "
        "same kind of thing on every row: how far apart the words on that "
        "scale actually are.",
        "",
        "THE MOVEMENTS ARE SMALL. On all prompts the largest is %s at %.3f, "
        "and nothing anywhere on the plate exceeds %.3f. Alignment moves "
        "these norms by under a seventh of their own spread -- which the "
        "companion plate cannot say, because its units do not carry that "
        "meaning."
        % (POLES[big[0]][1].lower(), abs(big[1]), span),
        "",
        "AND THE ORDER IS NOT THE COMPANION'S ORDER. Bodily harm is the "
        "largest mover there and fourth here; register level and fit are "
        "largest here. A scale whose changes are tightly agreed among "
        "lineages scores high on a per-change denominator whether or not it "
        "moved far.",
        "",
        "THE MOVE IS A MEAN OVER PROMPTS WITHIN EACH LINEAGE, THEN A MEDIAN "
        "OVER THE 50 LINEAGES. The median-over-prompts version is what every "
        "earlier plate drew, and on these scales it lands on an exact-zero "
        "tie for up to 42 of the 50 lineages, which does two things: it pins "
        "the marker at 0.000, and it makes the sign test a test on the untied "
        "SUBSET rather than on the roster. The mean has no ties on any of the "
        "fourteen, so every row here uses all 50 lineages. The scales are "
        "bounded (1 to 7, 1 to 9) and so are the differences, so the usual "
        "objection to a mean has a ceiling here it would not have on an "
        "unbounded quantity.",
        "",
        "AND THE TWO ESTIMATORS DISAGREE ABOUT VOCALISATION, IN OPPOSITE "
        "DIRECTIONS, BOTH SIGNIFICANT. Mean: %+.4f, 33 of 50 lineages up, "
        "p=0.033 -- alignment moves the completion TOWARD speech. Median: "
        "0.0000 with 21 lineages tied, 7 up against 22 down of the untied, "
        "p=0.008 -- away from it. Most prompts in a lineage move slightly "
        "toward silence and a minority move a long way toward speech, so the "
        "typical prompt and the net mass go opposite ways. That is a finding "
        "about the scale, not a defect in either statistic, and it should be "
        "reported as one."
        % _zb("v6:vocalisation")["move_mean_z"],
        "",
        "THE ORDER OF THE ROWS IS THE DENOMINATOR, and this plate uses a "
        "third one. Ranked by how far the highest lift band sits from the "
        "lowest, vocalisation is fourth here (%+.4f) behind bodily harm, "
        "transgressiveness and vulgarity -- while on the dose scatter it is "
        "FIRST. Neither is wrong. The scatter ranks by the slope divided by "
        "the spread OF THE SLOPES, so it measures how unanimous the roster "
        "is; this plate divides by the spread of the NORM, so a scale whose "
        "words are widely spread needs to move further to score. In raw "
        "rating points, which is a third ordering again, vocalisation is "
        "FIRST on both: %+.4f points from the lowest lift band to the "
        "highest, against bodily harm's %+.4f. It ranks fourth here only "
        "because its own spread is 2.5 times bodily harm's."
        % (_zb("v6:vocalisation", "high")["move_mean_z"]
           - _zb("v6:vocalisation", "low")["move_mean_z"],
           (_zb("v6:vocalisation", "high")["move_mean_z"]
            - _zb("v6:vocalisation", "low")["move_mean_z"]) * _zsd("v6:vocalisation"),
           (_zb("k_bodily_harm", "high")["move_mean_z"]
            - _zb("k_bodily_harm", "low")["move_mean_z"]) * _zsd("k_bodily_harm")),
        "",
        "Two rows move the other way. Makes worse and directedness are "
        "decisive on the median (p=2.7e-05 and 4.6e-07, on 28 and 31 untied "
        "lineages) and null on the mean over all 50 (p=0.89 and 0.20). "
        "Conditioning on the lineages that did not tie is what made them "
        "significant.",
        "",
        "Scales keep their native direction, low pole left and high pole "
        "right, so the side of every marker is a result. Rows are ordered by "
        "the square, most negative at the top.",
        "",
        "Charge deepens the movement in BOTH directions: at high lift "
        "arousal, concreteness, bodily harm and transgressiveness sit further "
        "left, and register level, dominance, valence and mundanity further "
        "right. Of the fourteen, %d have their high-lift triangle further "
        "from zero than their low-lift one."
        % sum(1 for r in rs if abs(r[3]) > abs(r[2])),
        "",
        "Pole words illustrate each end among the words alignment moved: a "
        "word appears only if it moved in at least 50 prompt-lineage cells, "
        "and for the six v6 scales, which rate a word in a frame rather than "
        "as a type, in at least %d frames. %d pole words, none repeated."
        % (_v6_min(), n_words),
        "",
        "Population and gate as elsewhere: 50 endpoint lineages, English, "
        "coverage at 0.20 on the minimum of the two arms, %s gated rows."
        % format(z["rows_gated"], ","),
    ]
    cp = out.replace(".png", ".caption.txt")
    open(cp, "w", encoding="utf-8").write("\n".join(cap) + "\n")
    print("  wrote %s" % cp)
    return 0


def main():
    if "--dose" in sys.argv:
        return draw_dose()
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
    mode = ("z" if "--z" in sys.argv else
            "fitted" if "--fitted" in sys.argv else "bands")
    rs = rows(orient="--orient" in sys.argv, mode=mode)
    n = len(rs)

    flipped = {r[0]: r[5] for r in rs}

    def lab(sc, side):
        #: **NO PER-WORD FRAME COUNT** (RH). The v6 labels used to read
        #: "said (1050), screamed (170)", the number being how many frames the
        #: word was rated in. It is a real provenance fact -- a v6 rating is of
        #: a word IN a frame, so a word rated in 7 frames is thinner evidence
        #: than one rated in 1,050 -- but it is a footnote riding on every
        #: label, and it made the six v6 rows read differently from the other
        #: eight for a reason no reader could infer. The caption carries the
        #: minimum instead; `v6_frames` still computes it.
        if flipped[sc]:
            side = 1 - side
        return "%s\n(%s)" % (POLES[sc][side], ", ".join(PICKS[sc][side]))

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
    h_lo = ax.scatter(lo, y, marker="v", s=17, facecolor=PUB_GRAY,
                      edgecolor="none", zorder=3,
                      label="Least charged prompts (lift)")
    h_sq = ax.scatter(sq, y, marker="s", s=13, facecolor=PUB_MID,
                      edgecolor="none", zorder=4, label="All prompts")
    h_hi = ax.scatter(hi, y, marker="^", s=19, facecolor=PUB_INK,
                      edgecolor="none", zorder=5,
                      label="Most charged prompts (lift)")
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
    native = "--orient" not in sys.argv
    #: **ONE PLAIN SENTENCE, UNITS TO THE CAPTION** (RH). This label carried
    #: the estimator, the denominator and a left/right gloss over three lines
    #: -- everything a reader needs to CHECK the plate and nothing they need
    #: to READ it. The poles are already named at both ends of every row and
    #: zero is already drawn, so the axis only has to say what a side means.
    #: The caption states the quantity, the units and the aggregation.
    ax.set_xlabel("Semantic pole toward which alignment moves",
                  fontsize=PUB_FONT_PT - 1, fontfamily=pub_font())
    #: **ORDER IS THE HANDLE LIST, NOT THE DRAW ORDER** (RH): all prompts
    #: first, then the two lift extremes most-charged before least. Drawing
    #: order is fixed by z-order (the pale down-triangle has to go down first
    #: or the black one hides under it), so the two cannot be the same list.
    fig.legend(handles=[h_sq, h_hi, h_lo],
               prop=FontProperties(family=pub_font(), size=PUB_FONT_PT - 2),
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

    out = os.path.join(HERE, "figures", "fig3_norms_osgood_en%s%s.png"
                       % ("" if native else "_oriented",
                          #: **THE ESTIMATOR IS PART OF THE NAME.** `--z` and
                          #: `--z --z-median` are different plates and both
                          #: used to write `_z`, so rendering the pair in one
                          #: command silently left the SECOND one under the
                          #: first one's name -- which is how the median plate
                          #: reached paper/figures labelled as the mean, with
                          #: vocalisation sitting on zero. A flag that changes
                          #: what is drawn has to change where it is written.
                          "" if mode == "bands" else
                          "_z_median" if mode == "z"
                          and "--z-median" in sys.argv else "_" + mode))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    print("  wrote %s" % save(fig, out))

    meta = json.load(open(os.path.join(HERE, "results",
                                       "norms_by_lift_en.json")))
    if mode == "z":
        return _z_caption(out, rs, meta, n_words)
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
        ("Scales keep their native direction, low pole left and high pole "
         "right, so the side of every marker is a result. Rows are ordered by "
         "the square, most negative at the top, so the eye reads what "
         "alignment removes down to what it adds."
         if native else
         "Every scale is oriented so the pole alignment moves TOWARD is on "
         "the right; seven of the fourteen are therefore drawn with their "
         "high end on the left. The square is positive by construction and "
         "only its length is a result. A TRIANGLE LEFT OF ZERO is the one "
         "thing on the plate whose side still carries information: that lift "
         "band moved the scale the opposite way from the corpus as a whole. "
         "Rows are ordered by the square, largest movement at the top."),
        "",
        "Pole words illustrate each end among the words alignment moved: a "
        "word appears only if it moved in at least 50 prompt-lineage cells. "
        "The six v6 scales rate a word IN a frame rather than as a type, so "
        "their pole words carry a second minimum: every one was rated in at "
        "least %d frames." % _v6_min(),
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
        "",
        "TIES PER ROW, and they are why the markers are not comparable across "
        "rows in the way the eye assumes. The marker is a median of "
        "per-lineage medians, so a lineage whose median change is exactly zero "
        "contributes a tie, and a row with many ties is drawn nearer zero than "
        "it moved. Of 50 lineages, tied: "
        + ", ".join("%s %d" % (POLES[sc][1], t)
                    for sc, t, *_ in sorted(fitted_vs_observed(),
                                            key=lambda r: -r[1]) if t)
        + ".",
        "",
        "The clearest case is vocalisation, 21 tied: its band medians differ "
        "by 0.0054 scale points across the lift range while an OLS fit on the "
        "same rows gives 0.038 over the same separation (band median lifts "
        "%+.3f to %+.3f), so the median recovers about a seventh of the "
        "movement the fit finds. Drawing the triangles from the fit instead "
        "was tried and rejected: it is reported in the file\'s docstring and "
        "reachable with --fitted, and it puts five of the fourteen low "
        "triangles on the opposite side of zero from the data, because the "
        "square\'s denominator and a slope\'s denominator are different "
        "numbers with no fixed ratio between them."
        % (meta["lift_band_median"][0], meta["lift_band_median"][2]),
    ]
    cp = out.replace(".png", ".caption.txt")
    open(cp, "w", encoding="utf-8").write("\n".join(cap) + "\n")
    print("  wrote %s" % cp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
