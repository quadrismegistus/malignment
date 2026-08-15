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
