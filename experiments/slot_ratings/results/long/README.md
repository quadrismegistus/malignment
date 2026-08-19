# long/

Tidy exports, one row per observation. Written by `../tidy.py`. Gzipped;
`pandas.read_csv` opens them directly.

`levels_long.csv.gz` is the atomic table: a mass-weighted level for one
(study, corpus, prompt, lineage, arm, scale). **Every gap, delta and
difference-in-differences in the three READMEs derives from this table and from
nothing else**, so any of them can be recomputed or disputed without reading the
producers.

`cov` is the share of that arm's probability mass held by the rated words. A
level is only as good as its coverage, which runs from about 0.24 to 0.82 across
studies, so it belongs in an analysis rather than in a footnote.

`units_long.csv` is the design: which prompt sits in which matched set and cell,
and how many lineages cover it.

`words_long.csv.gz` is the rating layer: one row per (prompt, word, scale) with
the net movement across lineages.

Nothing is aggregated and no test is run in these files.

## The order of reduction matters, and the READMEs use one order

Every published figure averages **within a lineage first, then across lineages**.
A flat mean over all (prompt, lineage) rows is NOT the same number when prompts
have unequal lineage coverage: F21 `mediation` base for the individual position
is 2.87 the first way and 2.89 the second. Neither is wrong; they weight prompts
differently. Anyone reproducing a README figure should reduce in that order, and
anyone doing something else should say so.

## Which corpus is which

    f21, m03, slotpov     institutional, the three position corpora
    room                  identity, the "Three <group> came into the room" sweep
    gender_pairs_v2       sexual, the 8 gender pairs on sexual_slot_en_v2
                          -- this is the one the sexual README reports
    gender_pairs_v6       the earlier v6 pass over the same prompts, kept
                          because it is the only saved source for those scales
