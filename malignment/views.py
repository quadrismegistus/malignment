"""Rollups of `movement`, as VIEWS. Materialise only on a measured reason.

    python -m malignment.views          create/replace them
    python -m malignment.views --time   time them, which is the only argument
                                        for turning one into a table

## WHY VIEWS AND NOT TABLES

The archive stores `movement`, `movement_cells` and `movement_edges` as three
tables. They are not three datasets — they are one dataset at three grains:

    movement         (pair, prompt, word)
    movement_cells   (pair, prompt)
    movement_edges   (pair)

**A stored rollup can disagree with its source.** That is the failure this
repository is a response to, and the archive has paid for it repeatedly: a
declared `same_base_as` holding 84 of 175 derivable pairs, a `landed` glob
covering 95 of 401 models, a `grid_roster` stamping status from a July run. Every
one is a derived thing stored beside its source and left to drift.

ClickHouse aggregates tens of millions of rows in well under a second, so the
rollups cost nothing to recompute. If one is ever measured as too slow for
something real, materialise it THEN and put the timing in the commit — a
materialisation justified by a number is maintainable; one justified by a habit
is the thing that drifts.

## THE LEDGER CLOSES, AND IT DID NOT BEFORE

`mass_out` and `mass_in` are NOT two sides of one balance sheet, and printed
adjacent they read as if they were. Amber -> AmberSafe shows 662 out and 1202 in,
which looks like a conservation failure and is not: words classified `still` also
carry delta, and so does the RESIDUAL — the untruncated tail that `twp_cells`
holds and `movement` has no row for.

So `mass_still` and `resid_delta` are in the view. With them the four terms sum
to zero up to float error, and a reader can see that rather than take it on
faith. A quantity that looks like a balance sheet and is not is how a wrong
sentence gets into a paper.

## JS IS DECOMPOSED, BECAUSE IT PARTITIONS EXACTLY

The archive's `movement_cells` carries `js_fall`, `js_rise` and `js_tail` beside
`js_total`, and that is the point rather than a convenience. `decompose_steps.py`
states it: *"`js()` answers 'how much did this move' and that conflates two
opposite events: mass passing between identifiable words, and mass draining into
an unresolved tail. Because JS is a SUM over words it partitions exactly, so the
two can be told apart."*

**Without `js_tail` a displacement and a drainage are the same number.** A cell
whose mass moved from `kill` to `scream` and a cell whose mass fell below theta
can report identical `js_total`, and only the split says which happened. That
distinction is the difference between the campaign's displacement finding and an
artefact of truncation.

## JS INCLUDES THE RESIDUAL AS A BUCKET

Jensen-Shannon over the scored words alone is a divergence between two
truncations, not between two distributions. The residual is one undifferentiated
mass in each arm, so it enters the sum as one more bucket:

    js = SUM over words  js_term(p_base, p_aligned)
       +                 js_term(resid_base, resid_aligned)

    js_term(p,q) = 0.5*(p*log2(2p/(p+q)) + q*log2(2q/(p+q)))

Omitting it would understate divergence exactly where the tail moved most, which
is the cross-language case — a Chinese cell carries more of its mass below theta.


## THESE VIEWS ARE BUILT OVER v3 AND ONLY v3

Every `{db}.twp_cells` below is the v3 table. A view is a NAMED OBJECT other code
selects from, so this file is deliberately NOT switchable the way
`similarity.RULE_VERSION` is: flipping a module constant would silently redefine
what `movement_cells` means for every existing caller, which is a worse failure
than the one it fixes.

Serving v4 needs `_v4`-suffixed views built alongside these, so both corpora are
addressable at once and a query names which it wants. Not done here because it is
a change to shared objects rather than to a caller's own read -- flagged
2026-08-18 when `corpus.retable` made the other read surfaces version-aware.
"""
import argparse
import sys
import time

from . import ch

#: js_term with the 0*log(0) branches guarded. `if(p>0, ...)` rather than a
#: nullif: a zero contributes zero, and NaN from log2(0) would propagate through
#: the whole sum silently -- the defect that stopped the first movement build.
_JSTERM = ("0.5 * (if({p} > 0, {p} * log2(2 * {p} / ({p} + {q})), 0)"
           "     + if({q} > 0, {q} * log2(2 * {q} / ({p} + {q})), 0))")

VIEWS = {
    #: `relation` and `depth` JOIN from `{db}.pairs` rather than being read off
    #: `movement`. They describe the EDGE, not the measurement, and storing them
    #: beside 52.9M measurement rows meant every models.yaml relabel cost a
    #: 25-minute recompute to change a string -- and could not even be done by
    #: re-running, because `relation` sat in the ORDER BY, so a ReplacingMergeTree
    #: appended the new label beside the old one instead of replacing it.
    "movement_cells": """
CREATE OR REPLACE VIEW {db}.movement_cells AS
SELECT m.base AS base, m.aligned AS aligned, pr.relation AS relation,
       pr.depth AS depth, m.rule AS rule, m.prompt AS prompt,
       countIf(m.cls = 'faller')                        AS n_fall,
       countIf(m.cls = 'riser')                         AS n_rise,
       countIf(m.cls = 'still')                         AS n_still,
       sumIf(-m.delta, m.cls = 'faller')                AS departed,
       sumIf(m.delta,  m.cls = 'riser')                 AS arrived,
       sumIf(m.delta,  m.cls = 'still')                 AS mass_still,
       any(rp.total)                                    AS resid_base,
       any(rq.total)                                    AS resid_aligned,
       any(rq.total) - any(rp.total)                    AS resid_delta,
       sumIf(%(t)s, m.cls = 'faller')                   AS js_fall,
       sumIf(%(t)s, m.cls = 'riser')                    AS js_rise,
       sumIf(%(t)s, m.cls = 'still')                    AS js_still,
       %(r)s                                            AS js_tail,
       sum(%(t)s) + %(r)s                               AS js_total
FROM {db}.movement m
INNER JOIN {db}.pairs pr
        ON pr.base = m.base AND pr.aligned = m.aligned
INNER JOIN (SELECT model, prompt, total FROM {db}.twp_cells) rp
        ON rp.model = m.base    AND rp.prompt = m.prompt
INNER JOIN (SELECT model, prompt, total FROM {db}.twp_cells) rq
        ON rq.model = m.aligned AND rq.prompt = m.prompt
GROUP BY base, aligned, relation, depth, rule, prompt
""" % {"t": _JSTERM.format(p="m.p_base", q="m.p_aligned"),
       "r": _JSTERM.format(p="any(rp.total)", q="any(rq.total)")},

    #: ── PER PROMPT, ACROSS THE DECLARED ENDPOINTS (RH, 2026-08-17).
    #:
    #: `movement_edges` groups the same cells by EDGE; this groups them by
    #: PROMPT. Same source, same definitions, different question: which frames
    #: move, rather than which lineages move.
    #:
    #: **RESTRICTED TO `{db}.endpoints` BY JOIN, NOT BY A LIST.** `movement`
    #: holds every measured pair, and "across endpoints" is a POPULATION CHOICE
    #: -- one made in a hardcoded list is one nobody reports. The join means the
    #: population is whatever the roster currently declares, and a roster
    #: correction propagates rather than needing this file edited.
    #:
    #: MEDIAN, not mean, and for the reason the slopegraph gives: these are
    #: heavy-tailed across families and a mean can be one family's obsession.
    #: `n_pairs` travels beside every median so a prompt measured on 9 lineages
    #: cannot be read as one measured on 50.
    "prompt_movement": """
CREATE OR REPLACE VIEW {db}.prompt_movement AS
SELECT mc.prompt                       AS prompt,
       mc.rule                         AS rule,
       count()                         AS n_pairs,
       median(mc.js_total)             AS js_median,
       median(mc.departed)             AS departed_median,
       median(mc.arrived)              AS arrived_median,
       median(mc.arrived - mc.departed) AS net_median,
       median(mc.n_fall)               AS n_fall_median,
       median(mc.n_rise)               AS n_rise_median,
       median(mc.resid_base)           AS resid_base_median,
       median(mc.resid_aligned)        AS resid_aligned_median
FROM {db}.movement_cells mc
INNER JOIN {db}.endpoints e
        ON e.base = mc.base AND e.endpoint = mc.aligned
GROUP BY prompt, rule
""",

    #: How many checkpoints have a twp cell at this prompt. **NOT the same as
    #: `n_pairs` above**: a cell is one arm, a pair needs both, so a prompt can
    #: be widely measured and thinly paired. Both are shown because the gap is
    #: the interesting case.
    "prompt_coverage": """
CREATE OR REPLACE VIEW {db}.prompt_coverage AS
SELECT prompt,
       uniqExact(model) AS n_models,
       median(total)    AS resid_median
FROM {db}.twp_cells
GROUP BY prompt
""",

    "movement_edges": """
CREATE OR REPLACE VIEW {db}.movement_edges AS
SELECT base, aligned, relation, depth, rule,
       count()                       AS n_prompts,
       avg(js_total)                 AS js_mean,
       median(js_total)              AS js_median,
       avg(js_fall)                  AS js_fall_mean,
       avg(js_rise)                  AS js_rise_mean,
       avg(js_tail)                  AS js_tail_mean,
       avg(js_tail) / nullIf(avg(js_total), 0) AS tail_share,
       avg(n_fall)                   AS faller_mean,
       avg(n_rise)                   AS riser_mean,
       avg(departed)                 AS departed_mean,
       avg(arrived)                  AS arrived_mean,
       avg(resid_delta)              AS resid_delta_mean
FROM {db}.movement_cells
GROUP BY base, aligned, relation, depth, rule
""",

    #: **THESE TWO EXISTED ONLY IN THE LIVE DATABASE UNTIL 2026-08-21.** Four
    #: consumers read them -- displacement_taxonomy/{run,crosslineage,coverage}.py
    #: and scripts/cell_screen.py -- and nothing in the repository created them,
    #: so a rebuilt ClickHouse would have come back without them and every one of
    #: those producers would have failed on a missing table. Added here, which is
    #: where every other view already lived.
    #:
    #: ## THE TIE THE OLD DEFINITION COULD NOT BREAK
    #:
    #: The previous form was `argMax(total, topup)` grouped by (model, prompt).
    #: That is a total order ONLY when at most one row exists per (key, topup).
    #: It does not hold: 3,790 cell keys and 495,624 word keys carry two rows at
    #: the SAME topup, differing on `prompt_cache`. For those, `argMax` broke the
    #: tie arbitrarily -- stable in practice, guaranteed by nothing, and across a
    #: merge it can change. lacan found the symptom on 2026-08-19 (canonical
    #: min_prob flipped on 14 word keys) and it was recorded in the view's own
    #: COMMENT as "a correctness bug, not a results bug" without the cause being
    #: named. The cause is that the ordering expression is not a total order.
    #:
    #: ## WHY prompt_cache=1 WINS, AND WHY NOT device
    #:
    #: `prompt_cache=1` is 657,523 cells across 120 models (80.2%); `=0` is
    #: 162,723 across 40. For four cells in five there is no choice at all, so
    #: preferring the cached arm makes the canonical column HOMOGENEOUS with the
    #: unreplicated majority instead of mixing two paths inside one column.
    #: RH's call, 2026-08-21.
    #:
    #: `device` was considered as a tiebreak (prefer cuda, put mps last) and
    #: REJECTED: it distinguishes only 529 of the 3,790 cell pairs, and it does
    #: not exist as a column on `twp_words_v4` at all. Using it for cells alone
    #: would let the two views select DIFFERENT underlying runs for one cell.
    #: `mtime` is shared by both tables and comes from the file that produced
    #: both rows, so the two views stay in step.
    #:
    #: (topup, prompt_cache, mtime) leaves 0 tied keys in either table -- checked,
    #: not assumed.
    #:
    #: The replicates are NOT deleted. They agree to 3.2e-05 median on `total`
    #: (p90 8.1e-04, max 8.8e-03), conservation matches to <1e-6 on all 3,790,
    #: and n_words differs on 565 -- 283 down, 282 up, i.e. unbiased theta-boundary
    #: jitter. That is an accidental replicate experiment and it is the only
    #: measurement of this instrument's noise floor we have.
    "twp_cells_v4_best": """
CREATE OR REPLACE VIEW {db}.twp_cells_v4_best AS
SELECT model, prompt,
       argMax(total,        (topup, prompt_cache, mtime)) AS total,
       argMax(tail,         (topup, prompt_cache, mtime)) AS tail,
       argMax(conservation, (topup, prompt_cache, mtime)) AS conservation,
       max(topup)                                         AS merged
FROM {db}.twp_cells_v4
GROUP BY model, prompt
COMMENT 'BOTH source rows are legitimate and neither is a repair of the other. A pass-1 cell and its topup cell are TWO MEASUREMENTS OF ONE SURFACE -- beam-accumulated (expand4) and single-path lower bound (score_words4, n_paths=1) -- and they must not be merged. This view takes the merged value where a topup cell exists and the pass-1 value where it does not, one row per key. The merged COLUMN is PROVENANCE, not a quality mark. ORDERING FIXED 2026-08-21: was argMax(.., topup), which is not a total order -- 3,790 cell keys carry two rows at the same topup differing on prompt_cache, and the tie was broken arbitrarily (this is the cause of the canonical min_prob flip lacan found 2026-08-19). Now (topup, prompt_cache, mtime), which leaves 0 tied keys. prompt_cache=1 wins because it is 80.2 percent of the corpus and 4 cells in 5 have no replicate at all. Replicates are retained, not deleted: they agree to 3.2e-05 median on total and give the instrument its only noise floor.'
""",

    "twp_words_v4_best": """
CREATE OR REPLACE VIEW {db}.twp_words_v4_best AS
SELECT model, prompt, word,
       argMax(p,        (topup, prompt_cache, mtime)) AS p,
       argMax(n_paths,  (topup, prompt_cache, mtime)) AS n_paths,
       max(topup)                                     AS merged
FROM {db}.twp_words_v4
GROUP BY model, prompt, word
COMMENT 'BOTH source rows are legitimate and neither is a repair of the other. A pass-1 cell and its topup cell are TWO MEASUREMENTS OF ONE SURFACE -- beam-accumulated (expand4) and single-path lower bound (score_words4, n_paths=1) -- and they must not be merged. A topup cell carries pass 1 rows byte-identically PLUS words scored below theta, which is why the same (model,prompt,word) appears twice in twp_words_v4. This view takes the merged value where a topup cell exists and the pass-1 value where it does not, one row per key. The merged COLUMN is PROVENANCE, not a quality mark. ORDERING FIXED 2026-08-21: was argMax(.., topup), which is not a total order -- 495,624 word keys carry two rows at the same topup differing on prompt_cache, and the tie was broken arbitrarily. That is the cause of the canonical min_prob flip on 14 keys of 9,993,876 found by lacan 2026-08-19, recorded then as a correctness bug without its cause named. Now (topup, prompt_cache, mtime), which leaves 0 tied keys. device was rejected as a tiebreak: it is not a column on this table, so cells and words could have selected different runs for one cell.'
""",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--time", action="store_true")
    a = ap.parse_args()
    for name, sql in VIEWS.items():
        ch.execute(sql)
        print("  view %s.%s" % (ch.DB, name))
    #: THE LEDGER CHECK, run at creation rather than documented. If the four
    #: terms plus the residual do not sum to ~0 the view is wrong, and a view
    #: that is wrong about conservation is worse than no view.
    bad = ch.scalar("""SELECT count() FROM {db}.movement_cells
                       WHERE abs(arrived - departed + mass_still + resid_delta) > 1e-3""")
    tot = ch.scalar("SELECT count() FROM {db}.movement_cells")
    part = ch.scalar("""SELECT count() FROM {db}.movement_cells
                        WHERE abs(js_fall + js_rise + js_still + js_tail - js_total) > 1e-4""")
    print("  partition: cells where js_fall+js_rise+js_still+js_tail != js_total: %s"
          % format(part or 0, ","))
    print("\n  ledger: cells where in - out + still + resid != 0 (1e-3): %s of %s"
          % (format(bad or 0, ","), format(tot or 0, ",")))
    if a.time:
        for q, label in ((("SELECT count() FROM {db}.movement_cells"), "movement_cells"),
                         (("SELECT count() FROM {db}.movement_edges"), "movement_edges")):
            t = time.time(); n = ch.scalar(q); dt = time.time() - t
            print("  %-16s %10s rows  %5.2f s" % (label, format(n or 0, ","), dt))
        print("\n  Materialise ONLY if one of these is too slow for something real,"
              "\n  and put the timing in the commit.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
