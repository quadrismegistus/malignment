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


def exemplars(seed, M, ax, mu, L=None, top=25, k=2):
    """Two words a pole, from the relations that separate most cleanly on it.

    Taken from the top `top` relations by ORIENTED value on that axis, so the
    left-pole words are base words from pairs the rater placed firmly at the
    left end and the right-pole words are their aligned counterparts. Frequency
    over the head of each list, which is agreement rank.

    **WHERE THE MARGINAL MEAN IS NOISE, THE WORDS COME FROM THE HIGH-LIFT
    TERTILE** (RH: "find 2 for each even if they're high lift"). An axis whose
    overall mean is near zero is in the figure because its DOSE difference
    earned it a place, so the population that justified the row is the one the
    exemplars should come from. Previously such rows got no words at all, which
    left the reversals -- the most interesting rows on the plate -- looking
    identical to flat ones.

    The words are illustrations, not evidence: the evidence is the marker
    positions, and no claim rests on which two words appear.
    """
    import collections, json
    import numpy as np
    from relation_group_report import load as _l, dose_values
    rel, _v, _g, _b = _l(seed)
    lift = dose_values(rel, "shown_lift")
    rows = [json.loads(x) for x in
            open(os.path.join(HERE, "results",
                              "axis_survey_en_seed%d.jsonl" % seed),
                 encoding="utf-8")]
    rows = [r for r in rows if rel[r["id"]]["frame"] in lift]
    out = {}
    #: **POOL WORDS BY WHICH POLE THEY LANDED ON, NOT BY A CHOSEN DIRECTION.**
    #: Orienting the search by a mean and then reading base words as the
    #: left-pole exemplar is right only when every relation on the axis runs
    #: the same way. On a REVERSAL it is wrong for half of them, and it made
    #: `Speech | Bodily act` -- a row whose poles are ordered by its marginal
    #: -- carry `hit, threw -> said, whispered`, which is that row backwards.
    #:
    #: For each relation, the SIGN of its value says which pole its base words
    #: sit on and its aligned words the other. Count each word toward the pole
    #: it actually occupied. Direction-free, and correct on every axis rather
    #: than on the ones that do not reverse.
    hi_mask = (L > np.quantile(L, 2 / 3.0)) if L is not None else None
    for j, a in enumerate(ax):
        v = M[:, j]
        #: where the marginal is noise the axis is drawn for its DOSE
        #: difference, so the high-lift end is the population that earned the
        #: row and the words come from there (RH)
        pool = np.where(hi_mask)[0] if (abs(mu[j]) < 0.03 and hi_mask is not None) \
            else np.arange(M.shape[0])
        pool = [i for i in pool if abs(v[i]) >= 0.35]
        pool.sort(key=lambda i: -abs(v[i]))
        x_side, y_side = collections.Counter(), collections.Counter()
        for i in pool[:top]:
            bw = rel[rows[i]["id"]]["base"][:4]
            aw = rel[rows[i]["id"]]["aligned"][:4]
            if v[i] > 0:          # base at pole_x
                x_side.update(bw); y_side.update(aw)
            else:                 # base at pole_y
                y_side.update(bw); x_side.update(aw)
        b, g = x_side, y_side
        out[a] = (", ".join(w for w, _ in b.most_common(k)),
                  ", ".join(w for w, _ in g.most_common(k)))
    return out


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
                                   PUB_GRAY, PUB_FAINT, PUB_RULE_PT, pub_font,
                                   save)
    #: **SET THE FAMILY GLOBALLY, NOT PER ARTIST.** Setting it on each Text
    #: misses whatever matplotlib builds later: the numeric x ticks came out
    #: DejaVu Sans even after `set_fontfamily` on `get_xticklabels()`, because
    #: the formatter regenerates them during layout. rcParams is the only
    #: place that reaches every default.
    #:
    #: **AND `unicode_minus` OFF.** matplotlib writes U+2212 MINUS for negative
    #: ticks; Helvetica does not carry it, so matplotlib falls back PER GLYPH
    #: and a tick reading "-0.2" ships in two faces. ASCII hyphen instead.
    matplotlib.rcParams["font.family"] = pub_font()
    matplotlib.rcParams["font.sans-serif"] = [pub_font(), "DejaVu Sans"]
    matplotlib.rcParams["axes.unicode_minus"] = False
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--dose", action="store_true")
    ap.add_argument("--top", type=int, default=0, help="keep only the N largest")
    ap.add_argument("--examples", action="store_true",
                    help="a word pair under each pole, from the relations that "
                         "separate most cleanly on that axis")
    ap.add_argument("--orient", choices=("highlift", "marginal", "raw"),
                    default="highlift",
                    help="which end goes on the right: where the top lift "
                         "tertile points (default), where the corpus mean "
                         "points, or the vocabulary's own arbitrary order")
    ap.add_argument("--osgood", action="store_true",
                    help="semantic-differential layout: each pole labelled on "
                         "its own side of the scale")
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
    #: **THE VOCABULARY'S POLE ORDER IS ARBITRARY AND THE SIGN INHERITED IT**
    #: (RH). `pole_x` and `pole_y` are whichever order the consolidator wrote
    #: them in, so an axis was "negative" only because of a word order, and a
    #: plot sorted by the signed mean put `Inner state -> Outward act` at the
    #: bottom as though it were the opposite of `Plain -> Euphemistic` at the
    #: top. It is not the opposite of anything; it is the same statement with
    #: the poles typed the other way round.
    #:
    #: Oriented so the BASE end is on the left of every row. The left column
    #: then reads as what the base says and the right as what alignment makes
    #: of it, and the length is a magnitude rather than a direction plus an
    #: accident. `--raw-poles` keeps the vocabulary's order.
    #:
    #: **ORIENTED ON THE MARGINAL MEAN, INCLUDING WHERE THAT MEAN IS NOISE.**
    #: `Speech / Bodily act` averages +0.007, so which way it is typed is
    #: effectively a coin toss -- and the figure SHOWS that, because its two
    #: tertile markers straddle zero whichever way the row is drawn. Orienting
    #: such a row on its high-lift mean instead would be choosing the tertile
    #: that makes the story, which is the thing every check tonight was for.
    #: **THE RIGHT POLE IS WHERE HIGH LIFT TAKES IT** (RH, default). Applied
    #: uniformly to all 38, which is what makes it a convention rather than a
    #: choice: the objection to orienting on a tertile is cherry-picking, and
    #: cherry-picking is one rule for most rows and another for the awkward
    #: ones.
    #:
    #: **SO THE BLACK TRIANGLES BEING POSITIVE CARRIES NO INFORMATION.** It is
    #: the definition of the axis, not a result, and a caption has to say so or
    #: a reader will read "alignment always moves right at high lift" off a
    #: tautology. What carries information is where the GREY triangle and the
    #: SQUARE fall relative to it -- and a grey triangle on the far side of
    #: zero is a reversal, which is the thing the plate is for.
    q3 = np.quantile(L, 2 / 3.0)
    key = {"highlift": M[L > q3].mean(0), "marginal": mu,
           "raw": np.ones(len(ax))}[a.orient]
    flip_ax = np.where(key < 0, -1.0, 1.0)
    if a.orient != "raw":
        M = M * flip_ax
        mu = mu * flip_ax
        V = [dict(v, pole_x=v["pole_y"], pole_y=v["pole_x"]) if f < 0 else v
             for v, f in zip(V, flip_ax)]
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
        #: **`flip_ax` MUST BE FILTERED WITH EVERYTHING ELSE.** It was not,
        #: and `zip(ax_filtered, flip_ax_unfiltered)` silently misaligned every
        #: pair after the first dropped axis -- the plate came out reading
        #: "Gentle -> Forceful", which is the finding backwards. Two sequences
        #: of different lengths zipped without complaint, which is the same
        #: shape as the `imap` pairing bug in `axis_survey` earlier today.
        M = M[:, ok]; mu = mu[ok]; lowm = lowm[ok]; topm = topm[ok]
        flip_ax = flip_ax[ok]
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
        fig, axx = plt.subplots(figsize=(PUB_SIZE[0],
                                         (0.25 if a.examples else 0.165) * n + 1.05),
                                layout="constrained")
        axm = None
        #: **THE SEGMENT IS THE POINT, NOT THE MARKERS.** Three markers a row
        #: on one scale is compact but the eye reads them as three unrelated
        #: dots; the thin rule joining the two tertiles makes the dose shift a
        #: LENGTH, which is the quantity the figure is about, and its direction
        #: is legible before any of the labels are read.
        #: **A THIN RULE ACROSS EACH ROW** (RH): Osgood draws a scale between
        #: the two poles and the marker sits ON it. Without it the markers
        #: float and the reader has to supply the axis mentally.
        #: the rule spans the MARKERS, not the per-relation values: M runs to
        #: +-2 by construction and using it put every marker in a pinch at the
        #: centre of a rule four units wide
        e = np.concatenate([mu, lowm, topm])
        pad = 0.06 * (e.max() - e.min())
        xlo, xhi = e.min() - pad, e.max() + pad
        for i in range(n):
            axx.plot([xlo, xhi], [i, i], color=PUB_FAINT,
                     linewidth=PUB_RULE_PT * 0.7, zorder=1,
                     solid_capstyle="butt")
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
        axm.set_xlabel("Where alignment\nmoves the sentence",
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
    #: **OSGOOD LAYOUT: EACH POLE ON ITS OWN SIDE** (RH). A semantic
    #: differential puts one pole at the left of the scale and the other at the
    #: right, so the reader's eye travels from a named end, through the
    #: marker, to the other named end -- the position IS the answer to "which
    #: of these two". Stacking both names on the left ("X <-> Y") makes the
    #: reader map a label pair onto a direction, which is the work the layout
    #: exists to remove.
    #:
    #: Labels come from `axis_poles.POLES`, written by hand and capped at 16
    #: characters, and `check()` REFUSES an axis it has no pair for rather than
    #: falling back to a truncated description.
    from axis_poles import POLES
    pairs = [(POLES[k][1], POLES[k][0]) if f < 0 else POLES[k]
             for k, f in zip(ax, flip_ax)]
    if a.examples:
        #: **HAND-PICKED WHERE THEY EXIST, DERIVED OTHERWISE.** The frequency
        #: ranking returns the corpus head, so `said`/`told`/`went` repeated
        #: across rows; `axis_examples.PICKS` is paper-claude's 52 choices,
        #: verified here on load: no word twice by stem, every word n>=2 on its
        #: own pole.
        #:
        #: **PICKS ARE STORED IN THE HIGH-LIFT ORIENTATION AND SWAPPED IF THE
        #: ROW IS DRAWN THE OTHER WAY.** Under `--orient marginal` or `raw` a
        #: row can flip, and a pair attached without checking would put the
        #: left pole's words under the right pole -- the same defect as the
        #: exemplar pooling before it was made orientation-free.
        from axis_examples import PICKS
        hl = np.where(M[L > q3].mean(0) < 0, -1.0, 1.0) if a.orient != "highlift" \
            else np.ones(len(ax))
        ex = exemplars(a.seed, M, ax, mu, L)
        for j, k in enumerate(ax):
            if k in PICKS:
                lft, rgt = PICKS[k]
                if hl[j] < 0:
                    lft, rgt = rgt, lft
                ex[k] = (", ".join(lft), ", ".join(rgt))
        pairs = [("%s\n(%s)" % (p[0], ex[k][0]),
                  "%s\n(%s)" % (p[1], ex[k][1]))
                 for p, k in zip(pairs, ax)]
    (axm or axx).set_yticklabels([pairs[i][0] for i in o] if a.osgood else
                                 ["%s  <->  %s" % (short(V[i]["pole_x"]),
                                                   short(V[i]["pole_y"]))
                                  for i in o],
                        fontsize=PUB_FONT_PT - 2.5, fontfamily=pub_font())
    if a.osgood:
        r = axx.secondary_yaxis("right")
        r.set_yticks(y)
        r.set_yticklabels([pairs[i][1] for i in o],
                          fontsize=PUB_FONT_PT - 2.5, fontfamily=pub_font())
        r.tick_params(length=0)
        r.spines["right"].set_visible(False)
    (axm or axx).set_ylim(-0.8, n - 0.2)
    axx.tick_params(axis="both", length=2, labelsize=PUB_FONT_PT - 2)
    #: `tick_params` sets a size and never a family
    for t in axx.get_xticklabels() + axx.get_yticklabels():
        t.set_fontfamily(pub_font())
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
                    "Where alignment moves the sentence\n"
                    "Toward the left pole  <<  0  >>  Toward the right pole"),
                   fontsize=PUB_FONT_PT - (1.5 if a.facet else 1),
                   fontfamily=pub_font())
    if a.dots:
        #: **plotnine's LEGEND LOOK, DRAWN BY MATPLOTLIB.** This producer is
        #: matplotlib -- plotnine cannot put a second labelled axis on the
        #: right of a discrete scale, which is what the Osgood layout needs --
        #: so the legend is matplotlib's with plotnine's conventions: below the
        #: panel, horizontal, no frame, no title. Moving it out of the panel
        #: also frees the lower-right corner, where it had been sitting on the
        #: two longest segments in the figure.
        #: `prop`, not `fontsize`: a legend built with `fontsize` alone keeps
        #: matplotlib's default FAMILY, so three labels shipped in DejaVu Sans
        #: on a plate declared Helvetica. Caught by the audit below, not by
        #: reading the code -- the code said `pub_font()` four times.
        from matplotlib.font_manager import FontProperties
        fig.legend(prop=FontProperties(family=pub_font(),
                                       size=PUB_FONT_PT - 2),
                   frameon=False, handlelength=0.9,
                   loc="outside lower center", ncol=3, scatterpoints=1,
                   columnspacing=1.6, handletextpad=0.35)
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
    #: **EVERY TEXT OBJECT AUDITED BEFORE SAVING.** `pub_font()` resolves the
    #: family but nothing applies it to TICK labels -- `tick_params` takes a
    #: size and no family -- so the numeric axis can ship in matplotlib's
    #: default while every declaration in the code reads as true. Same failure
    #: `pub_font`'s own docstring warns about, one level up: the font is named
    #: correctly and then not used.
    import collections as _c
    seen = _c.Counter()
    for t in fig.findobj(matplotlib.text.Text):
        if t.get_text().strip():
            seen[(t.get_fontname(), round(t.get_fontsize(), 1))] += 1
    print("  FONT AUDIT")
    off = [t.get_text() for t in fig.findobj(matplotlib.text.Text)
           if t.get_text().strip() and t.get_fontname() != pub_font()]
    if off:
        print("    NOT %s: %s" % (pub_font(), "; ".join(repr(x)[:24] for x in off)))
    for (fam, pt), k in sorted(seen.items()):
        flag = "  <-- BELOW 6 pt" if pt < 6 else ""
        print("    %-22s %4.1f pt  x%-3d%s" % (fam, pt, k, flag))
    out = a.out or os.path.join(HERE, "figures",
                                "axis_bars%s%s%s%s%s%s.png"
                                % ("_dose" if a.dose else "",
                                   "_dots" if a.dots else "",
                                   "_osgood" if a.osgood else "",
                                   "_ex" if a.examples else "",
                                   "_facet" if a.facet else "",
                                   "_sig" if a.sig else ""))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    print("wrote %s" % save(fig, out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
