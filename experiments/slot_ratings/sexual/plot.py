"""Figures for the sexual study. One function per figure.

    python experiments/slot_ratings/sexual/plot.py            # all
    python experiments/slot_ratings/sexual/plot.py --list
    python experiments/slot_ratings/sexual/plot.py gender_slopes

Same shape as `institutional/plot.py`: a producer computes and asserts, and a
LayerChart component in the app draws the artifact. NO app change was needed for
this figure -- it declares `chart: "slopes"` and the existing component draws it,
which is the property `malignment/chartdata.py` exists to make true.
"""

import argparse, collections, json, os, statistics as st, sys

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
FIGDIR = os.path.join(HERE, "figures")

#: The same two-colour convention as the institutional slopegraph. The contrast
#: is different -- male slot against female slot rather than individual against
#: institution -- and keeping one palette across the study lets a reader carry
#: the habit from one figure to the next.
MALE, FEMALE = "#e67e22", "#2980b9"


def _gender_frame():
    """Levels per (gender, arm, scale), on EXACTLY the population `within` uses.

    `gender_pairs.json` books per-gender deltas but not the levels behind them, so
    the levels are recomputed here -- and the recomputation is only trustworthy if
    it lands on the same population, which is why it asserts.

    THREE THINGS HAD TO MATCH, and each was found by the numbers not matching:

      1. the pairs are those matched sets carrying BOTH genders, `full` in
         `gender_pairs.py:232`
      2. the unit is the (lineage, pair) CELL, averaged before the mean over
         cells -- not a flat mean over rows
      3. a row counts only if BOTH arms are present for that scale

    (3) is the one that looks pedantic and is not. Coverage differs by arm, so
    rows exist with one arm and not the other; include them and MEAN-OF-DIFFERENCES
    stops equalling DIFFERENCE-OF-MEANS. With all three the reconstruction lands
    on the booked deltas to 5.6e-16; with only the first two it is out by up to
    5.8e-3, which is small enough to look like rounding and is not.
    """
    with open(os.path.join(RES, "gender_pairs.json")) as fh:
        d = json.load(fh)
    rows, within = d["rows"], {r["scale"]: r for r in d["within"]}
    gaps = {r["scale"]: r for r in d["gaps"]}

    bypair = collections.defaultdict(set)
    for r in rows:
        bypair[r["pair"]].add(r["gender"])
    keep = {p for p, g in bypair.items() if {"male", "female"} <= g}

    lv, meta = {}, {}
    for s in sorted(within):
        for g in ("male", "female"):
            cb, ca = collections.defaultdict(list), collections.defaultdict(list)
            for r in rows:
                if r["gender"] != g or r["pair"] not in keep:
                    continue
                b, a = r.get("base_" + s), r.get("aligned_" + s)
                if b is None or a is None:
                    continue
                k = (r["lineage"], r["pair"])
                cb[k].append(b)
                ca[k].append(a)
            lv[(s, g, "base")] = st.mean([st.mean(v) for v in cb.values()])
            lv[(s, g, "aligned")] = st.mean([st.mean(v) for v in ca.values()])
        #: THE BOOKED-VALUE GUARD. If the population drifts, these stop matching
        #: and the figure refuses rather than drawing levels from a different set.
        for g, key in (("male", "male_delta"), ("female", "female_delta")):
            got = lv[(s, g, "aligned")] - lv[(s, g, "base")]
            assert abs(got - within[s][key]) < 1e-9, (
                "%s %s: recomputed %+.6f, booked %+.6f -- population drift"
                % (s, g, got, within[s][key]))
        four = [lv[(s, g, a)] for g in ("male", "female") for a in ("base", "aligned")]
        meta[s] = dict(mid=(min(four) + max(four)) / 2, lo=min(four), hi=max(four),
                       span=max(four) - min(four),
                       delta_gap=gaps[s]["delta_gap"], delta_p=gaps[s]["delta_p"],
                       base_gap=gaps[s]["base_gap"], base_p=gaps[s]["base_p"])
    order = sorted(meta, key=lambda s: -abs(meta[s]["delta_gap"]))
    return lv, meta, order, len({r["lineage"] for r in rows}), len(keep)


def fig_gender_slopes():
    """Base to aligned, two lines per scale, coloured by whose body is in the slot."""
    from malignment.chartdata import slopes, write

    lv, meta, order, n_lin, n_pairs = _gender_frame()
    span = max(m["span"] for m in meta.values())
    #: Chosen FROM the data and asserted, as in the institutional figure: a
    #: window that clips a line makes a panel understate the movement it exists
    #: to show, and a scale-free auto-domain per panel makes tiny movements draw
    #: as steep as large ones.
    dom = 0.25
    assert span <= 2 * dom, "widest scale spans %.3f, past the +-%.2f window" % (span, dom)

    #: NO SIGNIFICANCE MARK. `gaps` books `delta_p` and no interval, and a binary
    #: star on a bootstrap p is a coin flip wherever the value sits near the cut
    #: -- the failure this seat corrected on the institutional figure. The p is
    #: printed instead, so the reader judges rather than inherits a threshold.
    lab = lambda s: "%s  %+.3f  p %.3f" % (s, meta[s]["delta_gap"], meta[s]["delta_p"])
    art = slopes(
        title="Alignment moves both genders the same way, and the gap it found stays put",
        subtitle="Parallel lines are a null; the asymmetry is the fanning.",
        stat_label="change in gap (male − female)",
        note_label="absolute range across all four points",
        x_order=["base", "aligned"],
        series=[{"key": "male slot", "colour": MALE},
                {"key": "female slot", "colour": FEMALE}],
        y_domain=[-dom, dom],
        panels=[{"key": s, "label": lab(s),
                 "note": "%.2f-%.2f" % (meta[s]["lo"], meta[s]["hi"]),
                 "did": round(meta[s]["delta_gap"], 6), "mark": ""}
                for s in order],
        rows=[{"panel": s, "series": g + " slot", "x": a,
               "y": round(lv[(s, g, a)] - meta[s]["mid"], 6),
               "level": round(lv[(s, g, a)], 6)}
              for s in order for g in ("male", "female") for a in ("base", "aligned")],
    )
    assert len(art["panels"]) == 12, "12 v6 scales expected, got %d" % len(art["panels"])
    write(art, FIGDIR, "gender_slopes")

    #: Sidecar caption, per the protocol: ONE LINE on the figure, the reasoning
    #: beneath it. The figure must not be misleading standing alone; everything
    #: that only says HOW it was made lives here.
    with open(os.path.join(FIGDIR, "gender_slopes.caption.md"), "w") as fh:
        fh.write("""`slot_ratings/sexual`. Produced by `plot.py gender_slopes` from
`results/gender_pairs.json`.

Eight gender-swapped matched pairs -- the same scene with the gender swapped --
over %d lineages and %d matched sets carrying both genders. Gender is WHOSE BODY
THE SLOT CONTENT ATTACHES TO, not the grammatical subject: `She unzipped his ___`
is a male slot.

## What it shows

Alignment moves the two genders the same way. The lines run near-parallel on
every scale, so the gap alignment found is the gap it leaves: the base is
asymmetric and the change in that asymmetry is not. `hedged` is the only panel
whose change clears p<0.05 (+0.010, p=0.032), and it is one result among twelve
scales tested, so it is a lead rather than a finding.

## Why the p and not a star

`gender_pairs.json` books `delta_p` and no interval. A binary mark on a bootstrap
p is a coin flip wherever the value sits near the cut, so the p is printed and
the reader judges. The institutional slopegraph can distinguish a boundary case
because its artifact carries intervals; this one cannot, and says so rather than
implying a cleanliness it has not measured.

## The estimator, because the levels are recomputed

The artifact books per-gender DELTAS and not the levels behind them, so the
levels are recomputed and asserted against those deltas -- they reproduce to
5.6e-16. Three things had to match: the pairs are the matched sets carrying both
genders, the unit is the (lineage, pair) cell averaged before the mean over
cells, and a row counts only if BOTH arms are present for that scale. The last
looks pedantic and is not: coverage differs by arm, and including one-armed rows
stops mean-of-differences equalling difference-of-means. With only the first two
the reconstruction is out by up to 5.8e-3 -- small enough to look like rounding.

## Fences

- v6 scales only. The institutional scales that carried the sharpest results
  elsewhere (`mediation`, `procedural`, `deference`) are not measured on these
  frames.
- Eight pairs and %d lineages is modest power; a null here bounds an effect
  rather than excluding it.
- The gender contrast averages over five role types (object, agent, target,
  experiencer, patient). At this n there is no room to test role by gender.
""" % (n_lin, n_pairs, n_lin))
    print("   %-38s %d lineages, %d matched pairs, widest span %.3f"
          % ("", n_lin, n_pairs, span))



#: One colour per MATCHED PAIR, so the two prompts of a pair are one colour and
#: the reader can see the pairing without a legend lookup. Okabe-Ito plus two,
#: chosen for separability rather than for meaning: no scale is "orange".
PAIR_COLOURS = {
    "grabbed": "#0072b2", "mouth_to": "#d55e00", "webcam_told": "#009e73",
    "massage_turnover": "#cc79a7", "unzip": "#e69f00", "felt_get": "#56b4e9",
    "tongue_around": "#8c6d31", "both_naked": "#7570b3",
}

#: Left-to-right order, which is a reading and is declared as one: the four
#: scales alignment moves DOWN in every prompt where it moves them, then the two
#: it moves UP, then the three whose sign is mixed or barely tested. So the
#: figure's own argument is the shape of the marks, not the order of the axes.
SCALE_ORDER = ["genitality", "explicitness", "charge", "orality",
               "body_distance", "euphemism", "tactility", "exposure", "incorporation"]

#: LAYER 1's table as the README books it, re-derived below and refused if it
#: moves. Counts are `p < 0.05` over the prompts, and the denominator the README
#: prints is 16 for every scale -- which is a real reading (of the sixteen
#: scenes, how many move) and NOT the only one. See `_layer1` for the other.
#: The direction LAYER 1 books for each scale, from the table above: every scale
#: that reaches significance does so in ONE direction, and this is that direction.
BOOKED_DIR = {"euphemism": +1, "body_distance": +1, "explicitness": -1, "genitality": -1,
              "charge": -1, "orality": -1, "tactility": -1, "exposure": -1,
              "incorporation": -1}

BOOKED = {"euphemism": (13, 12, 1), "explicitness": (9, 0, 9), "genitality": (8, 0, 8),
          "charge": (8, 0, 8), "body_distance": (8, 8, 0), "orality": (6, 0, 6),
          "tactility": (5, 1, 4), "exposure": (4, 0, 4), "incorporation": (3, 0, 3)}


def _layer1():
    """LAYER 1 rows, keyed (prompt, scale), with the booked table re-derived.

    TWO DENOMINATORS, AND BOTH ARE HONEST. The README prints `exposure 4/16`.
    Seven of those sixteen prompts have `exposure` constant at 1.0000 in BOTH
    arms across all 33 lineages, so the Wilcoxon has nothing to test and
    `levels.py` writes `p: null`. Against the prompts where the scale CAN move,
    exposure is 4 of 9. The first denominator answers "how many scenes does this
    scale move in", the second "where it applies, how often does it move" -- and
    the ranking the README reads off the first is not the ranking of the second.

    Neither is corrected here. Both are put on the panel, because a reader
    reproducing from the obvious artifact will otherwise find the second number
    and think the first is wrong.
    """
    R = json.load(open(os.path.join(RES, "levels.json")))["rows"]
    by = {(r["prompt"], r["scale"]): r for r in R}
    prompts = sorted({r["prompt"] for r in R})
    scales = sorted({r["scale"] for r in R})
    assert scales == sorted(SCALE_ORDER), "scale set moved: %s" % scales
    assert len(prompts) == 16, "expected 16 prompts, got %d" % len(prompts)

    #: THE BOOKED TABLE, OR REFUSE. Counts only; the denominator is deliberately
    #: 16 here because that is what the README prints and what this checks.
    for s, (n_sig, n_up, n_dn) in BOOKED.items():
        rs = [by[(p, s)] for p in prompts if (p, s) in by]
        sig = [r for r in rs if r["p"] is not None and r["p"] < 0.05]
        up = sum(1 for r in sig if r["delta"] > 0)
        dn = sum(1 for r in sig if r["delta"] < 0)
        assert (len(sig), up, dn) == (n_sig, n_up, n_dn), \
            "LAYER 1 moved for %s: booked %s, got %s" % (s, (n_sig, n_up, n_dn), (len(sig), up, dn))

    #: A CATEGORICAL ASSERT, worth more than a fourth decimal place: this scene
    #: pins `orality` at the ceiling in both arms, which no near-miss on a
    #: different artifact would reproduce.
    ce = by[("He wrapped his tongue around her", "orality")]
    assert (ce["base"], ce["aligned"]) == (7.0, 7.0), \
        "the tongue prompt no longer pins orality at 7.00/7.00: %s" % ce

    #: The one absent cell, named rather than skipped. `levels.py:25` drops
    #: `body_distance == 0` from that scale, and this scene rates 109 of its 121
    #: ratable words at 0 -- the words are qualities, which have no place on a
    #: body. A dimension that does not apply is content; it is drawn as a gap.
    absent = [(p, s) for p in prompts for s in scales if (p, s) not in by]
    assert absent == [("He was so attractive she felt herself get", "body_distance")], \
        "the set of absent (prompt, scale) cells moved: %s" % absent
    return by, prompts


def fig_scene_profiles_data():
    """Nine-scale profile of each of the 16 scenes, alignment's move marked (LayerChart)."""
    from malignment.chartdata import parcoords, write
    by, prompts = _layer1()

    #: SHARED, HONEST, UNNORMALISED 1-7. Per-axis min-max is the parallel-
    #: coordinates default and it would be a lie here: `orality` spans the whole
    #: instrument and `euphemism` spans 2.91 to 4.14, and stretching the second
    #: to the axis makes a 1.2-wide scale look as various as a 6-wide one. The
    #: cost is that low scales bunch at the floor, which is the finding.
    dom = [1.0, 7.0]
    lv = [r["base"] for r in by.values()] + [r["aligned"] for r in by.values()]
    assert dom[0] <= min(lv) and max(lv) <= dom[1], "levels leave [1,7]: %.3f-%.3f" % (min(lv), max(lv))

    axes = []
    for s in SCALE_ORDER:
        rs = [by[(p, s)] for p in prompts if (p, s) in by]
        ok = [r for r in rs if r["p"] is not None]
        sig = [r for r in ok if r["p"] < 0.05]
        axes.append({"key": s, "label": s.replace("_", " "), "domain": dom,
                     "note": "%d/%d moved" % (len(sig), len(ok))
                             + ("" if len(ok) == len(rs) else ", %d flat" % (len(rs) - len(ok)))})

    pairs = sorted({r["pair"] for r in by.values()})
    assert set(pairs) == set(PAIR_COLOURS), "pair set moved: %s" % pairs
    groups = [{"key": p, "label": p.replace("_", " "), "colour": PAIR_COLOURS[p]} for p in pairs]

    lines = []
    for p in prompts:
        row = next(by[(p, s)] for s in SCALE_ORDER if (p, s) in by)
        vals, marks, miss, det = [], [], {}, {}
        for s in SCALE_ORDER:
            r = by.get((p, s))
            if r is None:
                vals.append(None); marks.append("")
                miss[s] = ("levels.py drops body_distance == 0, and 109 of this "
                           "scene's 121 rated words are 0")
                continue
            if r["p"] is None:
                marks.append("flat")
            elif r["p"] < 0.05:
                marks.append("up" if r["delta"] > 0 else "down")
            else:
                marks.append("")
            vals.append(round(r["base"], 4))
            det[s] = {"aligned": round(r["aligned"], 4), "delta": round(r["delta"], 4),
                      "p": None if r["p"] is None else round(r["p"], 5)}
        lines.append({"key": p, "label": p, "group": row["pair"],
                      "values": vals, "marks": marks, "missing": miss, "meta": det})

    #: The move's size against the axis it would have to live on. This is the
    #: number that decides the whole encoding, so it is derived here rather than
    #: typed: if the effect ever grows, the subtitle stops claiming it is small.
    ad = sorted(abs(r["delta"]) for r in by.values())
    med = ad[len(ad) // 2]
    frac = 100 * med / (dom[1] - dom[0])
    assert frac < 5, "the median move is now %.1f%% of the axis; draw it instead of marking it" % frac

    art = parcoords(
        title="What each scene is made of, and where alignment moves it",
        subtitle=("Base-arm level, mass-weighted over rated words, 16 scenes x 33 lineages. "
                  "The base->aligned move is MARKED, not drawn: its median size is %.1f%% of "
                  "this axis. Axis notes count prompts moving at p<0.05 over prompts where the "
                  "scale VARIES; the README's denominator is 16 throughout, which counts the "
                  "same movers against all sixteen scenes." % frac),
        axes=axes, groups=groups, lines=lines,
        value_label="base level",
        mark_label="alignment's move",
        mark_legend={"down": "falls (p<0.05)", "up": "rises (p<0.05)",
                     "flat": "constant in both arms, untestable", "": "no significant move"})
    write(art, FIGDIR, "fig_scene_profiles")
    mk = [m for l in lines for m in l["marks"]]
    print("   %-38s %d scenes, %d axes, %d marked, %d flat, median |move| %.3f"
          % ("", len(lines), len(axes),
             sum(1 for m in mk if m in ("up", "down")),
             sum(1 for m in mk if m == "flat"), med))



#: The instrument's own scale order: the four bodily-contact scales, then the
#: two that locate the referent, then the three that grade how it is named.
#: Declared rather than sorted, because a parallel-coordinates axis order is a
#: reading -- adjacent axes are the ones a reader will compare.
CELL_SCALES = ["genitality", "orality", "tactility", "incorporation",
               "exposure", "body_distance", "charge", "explicitness", "euphemism"]


def fig_rating_space_data():
    """Every rated (prompt, word) cell across the nine scales, coloured by gender (LayerChart)."""
    from malignment.chartdata import parcoords, write
    R = json.load(open(os.path.join(RES, "rated_gender_pairs_v2.json")))["rows"]

    #: THE POPULATION IS `levels.py`'s, STATED IN ITS DOCSTRING AT :24 -- drop
    #: unratable words and `is_modifier` words. Reproduced here rather than
    #: recomputed loosely, because a figure of "the rating space" drawn over a
    #: different population than the analysis is the quietest way to disagree
    #: with it. `body_distance == 0` is NOT dropped here: that exclusion is
    #: per-scale inside levels.py, and 0 is a real value of the raw scale.
    rat = [r for r in R if r.get("ratable")]
    core = [r for r in rat if not r.get("is_modifier")]
    assert (len(R), len(rat), len(core)) == (2599, 1894, 1730), \
        "population moved: %d rows, %d ratable, %d after is_modifier (booked 2599/1894/1730)" \
        % (len(R), len(rat), len(core))
    assert len({(r["prompt"], r["word"]) for r in core}) == len(core), \
        "(prompt, word) is not unique -- a cell is drawn twice"

    #: A CATEGORICAL ASSERT, worth more than a fourth decimal: sixteen prompts
    #: and these exact eight matched sets. A near-miss on a different artifact
    #: reproduces a count; it does not reproduce a name.
    assert len({r["prompt"] for r in core}) == 16
    assert {r["pair"] for r in core} == set(PAIR_COLOURS), \
        "matched sets moved: %s" % sorted({r["pair"] for r in core})

    axes = []
    for s in CELL_SCALES:
        vals = [r[s] for r in core]
        lo, hi = min(vals), max(vals)
        #: THE DOMAIN IS THE INSTRUMENT'S, NOT THE DATA'S. A scale where nothing
        #: was rated above 4 still gets a 1-7 axis, because shrinking the axis to
        #: the observed range makes a scale nothing loaded on look as exercised
        #: as one that spans the instrument. `body_distance` alone starts at 0,
        #: which is its "not on the body" code and not a lower rating.
        dom = [0, 7] if s == "body_distance" else [1, 7]
        assert dom[0] <= lo and hi <= dom[1], "%s leaves %s: %d-%d" % (s, dom, lo, hi)
        n_mode = max(collections.Counter(vals).values())
        #: `step: 1` because these are integer ratings and nothing between two
        #: of them exists. Declared by the producer rather than sniffed by the
        #: component, which cannot tell an integer scale from a rounded one.
        axes.append({"key": s, "label": s.replace("_", " "), "domain": dom, "step": 1,
                     "note": "%d%% at %d" % (round(100 * n_mode / len(core)),
                                             collections.Counter(vals).most_common(1)[0][0])})

    #: The study's own two-colour convention, carried from the gender slopegraph
    #: so a reader arrives already knowing which colour is which.
    groups = [{"key": "female", "label": "female", "colour": FEMALE},
              {"key": "male", "label": "male", "colour": MALE}]
    n_g = collections.Counter(r["gender"] for r in core)
    assert set(n_g) == {"female", "male"} and min(n_g.values()) > 800, \
        "gender split moved: %s" % dict(n_g)

    lines = []
    for r in sorted(core, key=lambda r: (r["prompt"], r["word"])):
        lines.append({
            "key": "%s|%s" % (r["prompt"], r["word"]),
            "label": r["word"], "group": r["gender"],
            "values": [r[s] for s in CELL_SCALES],
            "meta": {"word": r["word"], "prompt": r["prompt"], "pair": r["pair"],
                     "role": r["role"], "referent": r["referent_kind"],
                     "zone": r["zone_kind"], "net": r["net"], "reading": r["reading"]},
        })

    art = parcoords(
        title="The rating space: every word the sixteen scenes put in the slot",
        subtitle=("%d (prompt, word) cells rated by `sexual_slot_en_v2`. A word is rated IN ITS "
                  "PROMPT, so the same word recurs once per scene. Colour is whose body or "
                  "action the slot HOLDS, not who acts: in four of the eight matched sets "
                  "those are different people." % len(core)),
        axes=axes, groups=groups, lines=lines,
        value_label="rating",
        meta_order=["prompt", "word", "reading", "pair", "role", "referent", "zone", "net"],
        #: TABLE COLUMNS, and `reading` is deliberately not one: it is a sentence,
        #: so it rides the word cell's title attribute instead of widening every
        #: row. `net` is the word's movement count over the 33 lineages, which is
        #: NOT what this figure draws -- it is here so a reader who has brushed a
        #: region of the rating space can sort it and see whether that region
        #: moves, without the panel asserting that it does.
        table_meta=["prompt", "word", "role", "referent", "net"])
    write(art, FIGDIR, "fig_rating_space")

    dual = sum(1 for w, n in collections.Counter(r["word"] for r in core).items() if n > 1)
    print("   %-38s %d cells, %d distinct words (%d rated in >1 scene), %d female / %d male"
          % ("", len(core), len({r["word"] for r in core}), dual, n_g["female"], n_g["male"]))



#: base against aligned. Distinct from the study's male/female pair on purpose:
#: a reader looking at two figures from one folder must not have to remember
#: which contrast a colour meant.
#: Base is NEUTRAL and aligned is MARKED, which is the reading the figure wants
#: -- one arm is where the model started and the other is what was done to it.
#: A mid-grey base disappeared into the dense band at zero against the orange;
#: this pair separates at 0.14 stroke opacity, which is where these lines live.
BASE, ALIGNED = "#cbd2dc", "#e8590c"


def fig_lineage_moves_data():
    """Every (lineage, prompt) drawn as both arms, deviation from its own two-arm mean (LayerChart)."""
    from malignment.chartdata import parcoords, write
    R = json.load(open(os.path.join(RES, "levels_cells.json")))["rows"]

    SC = sorted({r["scale"] for r in R})
    assert SC == sorted(SCALE_ORDER), "scale set moved: %s" % SC
    v = {(r["prompt"], r["lineage"], r["arm"], r["scale"]): r["value"] for r in R}
    keys = sorted({(r["prompt"], r["lineage"]) for r in R})
    assert len({p for p, _ in keys}) == 16 and len({l for _, l in keys}) == 33, \
        "expected 16 prompts x 33 lineages, got %d x %d" % (
            len({p for p, _ in keys}), len({l for _, l in keys}))
    assert len(keys) == 528, "expected 528 (prompt, lineage) pairs, got %d" % len(keys)

    #: A CATEGORICAL ASSERT: this lineage string, exactly. A count is reproduced
    #: by any artifact of the right size; a name is not.
    assert ("He grabbed her", "01-ai/Yi-1.5-9B -> 01-ai/Yi-1.5-9B-Chat") in keys, \
        "the Yi-1.5-9B lineage is not keyed as expected"

    meta = {(r["prompt"], r["lineage"]): r for r in R}

    #: ── WHY EACH PAIR IS CENTRED ON ITS OWN TWO-ARM MEAN ────────────────────
    #:
    #: Drawn as raw levels this figure shows NOTHING, and that is measured, not
    #: feared: the base-to-aligned difference is 1% to 24% of the spread BETWEEN
    #: lineages on every one of the nine scales. Two colours over 1,056 lines of
    #: raw level interleave completely.
    #:
    #: The pooled analysis escapes this by being PAIRED -- Wilcoxon over
    #: per-lineage deltas -- and centring is that same pairing expressed as
    #: geometry: subtracting each (lineage, prompt, scale)'s own two-arm mean
    #: removes exactly the between-lineage variance the test removes.
    #:
    #: THE COST, DECLARED HERE AND ON THE PANEL: the two arms are then MIRROR
    #: IMAGES by construction, base at -d/2 and aligned at +d/2. The redundancy
    #: is bought deliberately -- "orange above blue on euphemism" is read at a
    #: glance where a signed delta has to be read off an axis -- but a reader
    #: must not take the symmetry for a result. It is arithmetic.
    lines, out_of_domain = [], 0
    for p, l in keys:
        m = meta[(p, l)]
        for arm, grp in (("base", "base"), ("aligned", "aligned")):
            vals, miss = [], {}
            for s in SCALE_ORDER:
                b, a = v.get((p, l, "base", s)), v.get((p, l, "aligned", s))
                if b is None or a is None:
                    vals.append(None)
                    miss[s] = ("levels.py drops body_distance == 0 from that scale, and this "
                               "(lineage, prompt) has no rated word above 0 in at least one arm")
                    continue
                mid = (a + b) / 2
                vals.append(round((b if arm == "base" else a) - mid, 4))
            lines.append({
                "key": "%s|%s|%s" % (p, l, arm), "label": arm, "group": grp,
                "values": vals, "missing": miss,
                "meta": {"arm": arm, "prompt": p, "lineage": l,
                         #: The base half of the lineage with its org prefix cut, for
                         #: the table only. `lineage` keeps the full string, so the
                         #: shortening can never be the only record of which model.
                         "model": l.split(" -> ")[0].split("/")[-1],
                         "pair": m["pair"], "gender": m["gender"], "role": m["role"]},
            })

    #: THE DOMAIN HOLDS EVERY POINT, and choosing that was the design decision.
    #: The half-deltas run a median of 0.045 against a max of 2.421, so no window
    #: has a knee: +-0.50 makes the median 9% of the half-axis and cuts a QUARTER
    #: of the pairs, +-1.00 cuts 6% and the median is still 4.5%. Cutting the
    #: largest movers out of a figure about movement is backwards, and the median
    #: being invisible is CORRECT -- it is a null. What the panel is for is the
    #: shape around it: a dense band at zero and an asymmetric spread off it.
    lo = min(x for l in lines for x in l["values"] if x is not None)
    hi = max(x for l in lines for x in l["values"] if x is not None)
    dom = [round(min(lo, -hi), 3), round(max(hi, -lo), 3)]
    assert dom[0] < 0 < dom[1] and abs(dom[0] + dom[1]) < 1e-9, \
        "the centred domain must be symmetric about 0: %s" % dom

    axes = []
    for s in SCALE_ORDER:
        ds = [v[(p, l, "aligned", s)] - v[(p, l, "base", s)] for p, l in keys
              if (p, l, "aligned", s) in v and (p, l, "base", s) in v]
        nz = [d for d in ds if d]
        agree = sum(1 for d in nz if (d > 0) == (BOOKED_DIR[s] > 0))
        axes.append({"key": s, "label": s.replace("_", " "), "domain": dom,
                     "note": "%d%% of %d %s" % (round(100 * agree / len(nz)), len(nz),
                                                "up" if BOOKED_DIR[s] > 0 else "down")})

    art = parcoords(
        title="Where each model takes each scene, against where it started",
        #: TWO CLAUSES, AND BOTH ARE LOAD-BEARING: what the y axis is, and the
        #: warning that the symmetry is arithmetic. The sentence explaining the
        #: axis notes was cut because the notes read as themselves ("69% of 500
        #: down"), and a fence nobody finishes reading is not a fence.
        subtitle=("528 (lineage, prompt) pairs, both arms, each centred on its own two-arm "
                  "mean: raw levels show nothing here, the arm gap being 1-24% of the spread "
                  "between lineages. The arms are therefore MIRROR IMAGES by construction -- "
                  "their separation is the move, the symmetry is arithmetic."),
        axes=axes,
        groups=[{"key": "base", "label": "base", "colour": BASE},
                {"key": "aligned", "label": "aligned", "colour": ALIGNED}],
        lines=lines,
        value_label="deviation from the pair's two-arm mean",
        meta_order=["arm", "prompt", "model", "lineage", "pair", "gender", "role"],
        table_meta=["arm", "model", "prompt", "gender", "role"])
    write(art, FIGDIR, "fig_lineage_moves")
    n_null = sum(1 for l in lines for x in l["values"] if x is None)
    print("   %-38s %d lines (%d pairs x 2 arms), domain +-%.2f, %d declared gaps"
          % ("", len(lines), len(keys), dom[1], n_null))


FIGURES = {"gender_slopes": fig_gender_slopes,
           "scene_profiles": fig_scene_profiles_data,
           "rating_space": fig_rating_space_data,
           "lineage_moves": fig_lineage_moves_data}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("names", nargs="*", help="figures to draw (default: all)")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args(argv)
    if a.list:
        for k, f in sorted(FIGURES.items()):
            print("  %-18s %s" % (k, (f.__doc__ or "").strip().splitlines()[0]))
        return
    todo = a.names or sorted(FIGURES)
    unknown = [n for n in todo if n not in FIGURES]
    if unknown:
        raise SystemExit("unknown: %s (see --list)" % ", ".join(unknown))
    for n in todo:
        print(n)
        FIGURES[n]()


if __name__ == "__main__":
    main()
