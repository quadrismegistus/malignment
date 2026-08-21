"""Figures for jakobson_space. One function per figure.

    python experiments/passage_analysis/jakobson_space/plot.py          # all
    python experiments/passage_analysis/jakobson_space/plot.py --list

The passage map is a DATA artifact drawn live by a LayerChart-era component, not
a raster: 14,414 points that a reader is meant to scan, filter and open. The
grains behind the points -- 3,040,970 words and 196,349 sentences -- stay in
ClickHouse and are fetched one passage at a time through `/passage`.
"""

import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
FIGDIR = os.path.join(HERE, "figures")

#: The four quadrants, named as the store names them. `(+surp -drift)` and
#: `(-surp +drift)` are F15's metaphoric and metonymic cells; the two diagonal
#: cells are not given a reading here because the finding is about the
#: off-diagonal ones.
CELLS = ["(+surp +drift)", "(+surp -drift)", "(-surp +drift)", "(-surp -drift)"]
READING = {"(+surp -drift)": "metaphoric", "(-surp +drift)": "metonymic"}

#: AI arms warm to cool along the axis the finding runs on -- base, aligned, API
#: -- and the human corpora in one muted family, because they are the reference
#: the three arms are placed against and not a fourth arm.
CATS = {
    "base":    ("#fa5252", "ai"),
    "aligned": ("#b197fc", "ai"),
    "API":     ("#4dabf7", "ai"),
    "arxiv_abstracts":    ("#8d9b6a", "human"),
    "philosophy":         ("#a08b5c", "human"),
    "dreams":             ("#9b7b8a", "human"),
    "c20_fiction":        ("#6f8f8a", "human"),
    "literary_criticism": ("#8a8f6f", "human"),
    "waking_narrative":   ("#7d8ba0", "human"),
}

#: lacan's [6521] table, re-derived below and refused if it moves. Percentages
#: are of that category over the four quadrants, in CELLS order.
BOOKED_PCT = {
    "base":    (43.2, 44.0, 7.8, 5.0),
    "aligned": (15.6, 23.4, 27.6, 33.5),
    "API":     (13.6, 14.2, 41.1, 31.1),
}
#: (metaphoric, metonymic) enrichment against the pooled rate.
BOOKED_ENRICH = {
    "base": (1.88, 0.28), "aligned": (1.00, 0.98), "API": (0.60, 1.46),
    "arxiv_abstracts": (1.92, None), "dreams": (1.59, None),
    "philosophy": (1.58, None), "waking_narrative": (None, 1.00),
}
BOOKED_R = 0.348


def fig_passage_map_data():
    """14,414 passages on the surprisal x drift plane, addressable (LayerChart)."""
    from malignment import vectors as V
    from malignment.chartdata import quadrants, write

    rows = V.rows("SELECT id, category, human_or_ai, model, quadrant, "
                  "z_surprisal, z_drift FROM malignment.passage_axes")
    assert len(rows) == 14414, "expected 14,414 passages, got %d" % len(rows)
    assert len({r["id"] for r in rows}) == len(rows), "passage ids are not unique"

    #: A CATEGORICAL ASSERT, worth more than a fourth decimal: this exact set of
    #: nine categories. A count is reproduced by any table of the right size.
    cats_seen = {r["category"] for r in rows}
    assert cats_seen == set(CATS), "category set moved: %s" % sorted(cats_seen ^ set(CATS))
    assert {r["quadrant"] for r in rows} == set(CELLS), "quadrant labels moved"

    #: The step z parameters the reader is shown, re-derived and refused if they
    #: move. A z printed against a stale mean is wrong in a way nothing on the
    #: panel can reveal.
    st = V.rows("SELECT avg(step) mu, stddevPop(step) sd FROM malignment.passage_sentences "
                "WHERE step IS NOT NULL")[0]
    assert abs(round(st["mu"], 4) - 0.4468) < 1e-9 and abs(round(st["sd"], 4) - 0.0921) < 1e-9, \
        "the sentence-step distribution moved: mean %.4f sd %.4f" % (st["mu"], st["sd"])

    r_pooled = V.rows("SELECT corr(z_surprisal, z_drift) c FROM malignment.passage_axes")[0]["c"]
    assert abs(round(r_pooled, 3) - BOOKED_R) < 1e-9, \
        "passage-grain r moved: booked %.3f, got %.4f" % (BOOKED_R, r_pooled)

    #: ── THE TABLE, RE-DERIVED AND REFUSED IF IT MOVES ───────────────────────
    n_by, rate, pct = {}, {}, {}
    for c in CATS:
        sub = [r for r in rows if r["category"] == c]
        n_by[c] = len(sub)
        rate[c] = {q: sum(1 for r in sub if r["quadrant"] == q) / len(sub) for q in CELLS}
        pct[c] = {q: round(100 * rate[c][q], 1) for q in CELLS}
    pooled = {q: sum(1 for r in rows if r["quadrant"] == q) / len(rows) for q in CELLS}

    #: FROM THE UNROUNDED RATE, and the assert below is what found that it had
    #: not been. Dividing the DISPLAY value -- 14.2% rather than 0.141670... --
    #: put API's metaphoric enrichment at 0.61 against a booked 0.60. One cell in
    #: nine, off by one in the second decimal, from a rounding meant for the
    #: table and never for the arithmetic. A booked value is the only thing that
    #: catches this: nothing about 0.61 looks wrong.
    enrich = {c: {q: round(rate[c][q] / pooled[q], 2) for q in CELLS} for c in CATS}

    for c, want in BOOKED_PCT.items():
        got = tuple(pct[c][q] for q in CELLS)
        assert got == want, "occupancy moved for %s: booked %s, got %s" % (c, want, got)
    for c, (met, mto) in BOOKED_ENRICH.items():
        if met is not None:
            assert abs(enrich[c]["(+surp -drift)"] - met) < 0.005, \
                "metaphoric enrichment moved for %s: booked %.2f, got %.2f" % (
                    c, met, enrich[c]["(+surp -drift)"])
        if mto is not None:
            assert abs(enrich[c]["(-surp +drift)"] - mto) < 0.005, \
                "metonymic enrichment moved for %s: booked %.2f, got %.2f" % (
                    c, mto, enrich[c]["(-surp +drift)"])

    #: ── THE DOMAIN IS THE DATA, ROUNDED OUT ─────────────────────────────────
    #: `z_drift` reaches -8.38 against a top of +4.26, so a symmetric axis would
    #: spend half its extent on an empty tail. Asymmetric and declared.
    #: ── THE PLANE IS WINDOWED AT +-4.5 AND THE COST IS COUNTED ──────────────
    #:
    #: `z_drift` reaches -8.38 against a top of +4.26, and RH read the far tail:
    #: those are models repeating themselves, so the axis was spending a third of
    #: its extent on degenerate output. **13 passages of 14,414 fall outside
    #: +-4.5 -- 11 below on drift, 2 above on surprisal -- and every one of the 11
    #: is an `aligned` checkpoint** (Qwen3-8B, granite-3.0-instruct, beaver,
    #: CT-LLM-SFT-DPO, RedPajama-Chat).
    #:
    #: The window is applied to what is DRAWN. The occupancy table below is
    #: unchanged and still counts all 14,414, so the panel carries a windowed
    #: picture beside an unwindowed statistic -- which is only honest because it
    #: is said out loud, here and on the panel.
    WINDOW = 4.5
    inside = [r for r in rows
              if abs(r["z_drift"]) <= WINDOW and abs(r["z_surprisal"]) <= WINDOW]
    n_outside = len(rows) - len(inside)
    assert n_outside == 13, "the +-4.5 window now excludes %d passages, not 13" % n_outside
    dom = [-WINDOW, WINDOW]

    cat_keys = sorted(CATS, key=lambda c: (CATS[c][1] != "ai", -n_by[c]))
    models = sorted({r["model"] for r in rows})
    ci = {c: i for i, c in enumerate(cat_keys)}
    mi = {m: i for i, m in enumerate(models)}

    #: ── WHAT IS DRAWN IS A CAPPED SAMPLE; WHAT IS COUNTED IS EVERYTHING ──────
    #:
    #: The 14,414 are not evenly spread over the 71 models. Eleven API endpoints
    #: carry 514 to 600 passages each and the six human corpora 476 to 500, while
    #: the 54 open checkpoints average 91 and go as low as 2 -- so at full
    #: population the plane is three fifths API and human, and the arms the
    #: figure is about are the thin ones.
    #:
    #: A per-model cap of 150 is where that stops costing anything. It draws
    #: 7,403 of 14,414 and **loses 78 open-model passages of 4,931**: API falls
    #: 6,508 to 1,650 and human 2,975 to 900, while base keeps 2,184 of 2,195 and
    #: aligned 2,669 of 2,736. A smaller cap starts eating the open models (452
    #: lost at 120, 934 at 100) and a larger one leaves the imbalance.
    #:
    #: **THE TABLE BELOW IS OVER ALL 14,414 AND SAYS SO.** Windowing the view is
    #: a drawing decision; windowing the statistic would be a different study.
    #: The two populations are named on the panel so a reader cannot take the
    #: count of ink for the count of passages.
    CAP = 150
    SEED = 20260821
    from random import Random
    #: KEYED BY (category, model), NOT BY MODEL. All six human corpora share one
    #: `model` value, so a cap on `model` alone capped the six of them TOGETHER at
    #: 150 rather than at 150 each -- 750 passages, and the panel would have shown
    #: one twentieth of the human anchor while the legend counted all of it. The
    #: booked total is what caught it; nothing about 6,653 looks wrong.
    by_model = {}
    for r in inside:
        by_model.setdefault((r["category"], r["model"]), []).append(r)
    drawn = []
    for m in sorted(by_model):
        sub = sorted(by_model[m], key=lambda r: r["id"])
        #: Seeded and taken from an ID-SORTED list, so the sample is a function of
        #: the data and not of the order ClickHouse happened to return. A store
        #: read without ORDER BY is not stable between runs.
        drawn.extend(sub if len(sub) <= CAP else Random(SEED).sample(sub, CAP))
    #: ── DRAW ORDER IS ROUND-ROBIN OVER THE CATEGORIES ───────────────────────
    #:
    #: Sorted by id, the categories arrive in blocks and the last one painted
    #: sits on top of the others everywhere they overlap -- which on a 7,403-point
    #: cloud is most of it. Capping made this worse rather than better: `base`
    #: went from 15% of 14,414 to 29% of what is drawn, so the brightest colour
    #: is now also one of the most numerous, and the human corpora underneath it
    #: were invisible.
    #:
    #: Round-robin rather than a shuffle, because the order must be identical on
    #: every run: the artifact is committed and a re-render has to be comparable
    #: with the one before it.
    by_cat = {}
    for r in sorted(drawn, key=lambda r: r["id"]):
        by_cat.setdefault(r["category"], []).append(r)
    queues = [by_cat[c] for c in cat_keys if c in by_cat]
    drawn = []
    for k in range(max(len(q) for q in queues)):
        for q in queues:
            if k < len(q):
                drawn.append(q[k])
    assert len(drawn) == 7396, "the cap-150 sample moved: expected 7,396, got %d" % len(drawn)
    lost_open = sum(len(v) - CAP for (cat, _), v in by_model.items()
                    if len(v) > CAP and cat in ("base", "aligned"))
    #: 74, not the 78 measured before the window: four of the passages a capped
    #: open model would have lost were among the 13 the window already removed.
    #: Two windows compose, and the cost of the second is not independent of the
    #: first -- which is why this is a booked number and not a subtraction.
    assert lost_open == 74, "open-model passages dropped by the cap moved: %d" % lost_open

    art = quadrants(
        title="Every passage on the surprisal and drift plane",
        subtitle=("14,414 passages, z-scored on both axes. The quadrant "
                  "verdict was a verdict on ONE GRAIN: over 70 entity medians the two axes "
                  "correlate at +0.749 and the plane is a diagonal; over these passages it "
                  "is +%.3f and all four cells are occupied. Collapsing a model's passages "
                  "to one point removes the within-model scatter, and that scatter is where "
                  "the axes are close to independent. DRAWN: %s of them, capped at %d per "
                  "model so eleven API endpoints at ~600 passages each do not bury 54 open "
                  "checkpoints averaging 91. The table below counts all 14,414."
                  % (r_pooled, format(len(drawn), ","), CAP)),
        x={"key": "z_drift", "label": "drift (z)", "domain": dom,
           "note": "mean sentence-to-sentence step in bge space"},
        y={"key": "z_surprisal", "label": "surprisal (z)", "domain": dom,
           "note": "deepseek bits per token, at a fixed token prefix"},
        cats=[{"key": c, "label": c.replace("_", " "), "colour": CATS[c][0],
               "kind": CATS[c][1], "n": n_by[c]} for c in cat_keys],
        models=models,
        points={"ids": [r["id"] for r in drawn],
                "x": [round(r["z_drift"], 3) for r in drawn],
                "y": [round(r["z_surprisal"], 3) for r in drawn],
                "cat": [ci[r["category"]] for r in drawn],
                "model": [mi[r["model"]] for r in drawn]},
        #: THE CORNER EACH CELL OCCUPIES IS DERIVED FROM ITS OWN NAME, not from
        #: which axis is which. The axes were swapped once already -- surprisal
        #: was x -- and a corner assignment written as "top left" would have
        #: survived that swap silently, putting `metaphoric` where `metonymic`
        #: belongs while every number on the panel stayed right.
        cells=[{"key": q, "label": READING.get(q, ""), "pooled": round(pooled[q], 4),
                "surp": 1 if "+surp" in q else -1,
                "drift": 1 if "+drift" in q else -1}
               for q in CELLS],
        table=[{"cat": c, "n": n_by[c], "pct": pct[c], "enrich": enrich[c]} for c in cat_keys],
        #: THE DETAIL SCALES ARE THE PRODUCER'S, NOT THE COMPONENT'S. Both are
        #: clamped and both say so. Per-word bits have a median of 3.57 and a
        #: p99 of 18.43 against a MAX OF 158.36, so a scale reaching the maximum
        #: paints every ordinary word the same pale colour and hands the whole
        #: range to a handful of tokens. 16 bits is just under the p99.
        n_total=len(rows),
        detail={"url": "/passage",
                #: DIVERGING, CENTRED ON THE MEDIAN. `mid` is the median over the
                #: 3,031,498 non-partial words, so the tint reads "more or less
                #: surprising than a typical word HERE" and passages stay
                #: comparable with each other.
                #:
                #: One bit was the other candidate and it is not the floor: the
                #: minimum is 0.00, 0.14% of words are exactly 0 and 19.5% fall
                #: below one bit, which sits near the 21st percentile. Centring
                #: there would put four words in five on the high side and paint
                #: most of every passage one colour.
                "scales": {"bits": {"domain": [0, 16], "mid": 3.44,
                                    "note": "bits per word, diverging about the median 3.44 "
                                            "and clamped at 16. Over 3,031,498 non-partial "
                                            "words: min 0.00, p25 1.38, p75 6.60, p99 17.90, "
                                            "max 158.36"},
                           #: NOT clamped: 0.794 is the observed maximum and 0
                           #: the minimum, so the domain contains every step.
                           #: The first version of this note said "155 sit above
                           #: 0.8" -- a number I had not measured, in a note whose
                           #: whole job is to say what a scale hides. It hides
                           #: nothing, and that is worth saying too.
                           #: `mean` and `sd` so the reader can be shown a z rather
                           #: than a raw cosine step, which is uninterpretable on
                           #: its own. The distribution supports it: skew -0.322
                           #: and kurtosis 3.889 over 181,935 sentences.
                           #:
                           #: **THESE ARE NOT THE PASSAGE'S z_drift PARAMETERS AND
                           #: THE NOTE SAYS SO.** A passage's drift is the MEAN of
                           #: its steps, and averaging shrinks the spread: the
                           #: sentence sd is 0.0921 against the passage sd of
                           #: 0.0434, so the same z means a different thing on each.
                           #: The panel shows both -- `z 1.02` in the header is a
                           #: passage among passages -- and two numbers spelled the
                           #: same way on one screen is exactly the mismatch a
                           #: reader has no way to suspect.
                           "step": {"domain": [0, 0.8], "mean": 0.4468, "sd": 0.0921,
                                    "note": "sentence-to-sentence step, shown as a z over the "
                                            "181,935 SENTENCE steps (mean 0.4468, sd 0.0921); "
                                            "raw on hover. NOT the same scale as the passage "
                                            "z_drift above, whose sd is 0.0434 because a "
                                            "passage's drift is the mean of its steps"}}},
        notes=[
            "Enrichment is against the pooled rate over all 14,414 passages, printed under "
            "each quadrant. The two off-diagonal cells are enriched monotonically in "
            "OPPOSITE directions across base, aligned and API, and aligned sits at almost "
            "exactly the pooled rate on both: it is the crossing point.",
            "The human corpora are not noise around that. Metaphoric is enriched in "
            "arxiv_abstracts, dreams and philosophy, three corpora sharing little except "
            "that none narrates a sequence of events; the metonymic cell has exactly one "
            "human corpus at parity, waking_narrative, which is people recounting what "
            "happened next.",
        ])
    write(art, FIGDIR, "fig_passage_map")
    print("   %-38s %d cats (%d AI, %d human), %d models, r=%.3f"
          % ("", len(cat_keys), sum(1 for c in cat_keys if CATS[c][1] == "ai"),
             sum(1 for c in cat_keys if CATS[c][1] == "human"), len(models), r_pooled))


FIGURES = {"passage_map": fig_passage_map_data}


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
