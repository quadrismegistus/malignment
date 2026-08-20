---
subject: jakobson_space
question: What do F15 and F16's axes look like when rebuilt on OUR corpus?
status: surprisal axis BUILT; drift axis inherited; external axis NOT YET (needs BLT)
grain: page
---

# jakobson_space

F15 and F16 place passages in a space of **surprisal x drift** and read Jakobsonian quadrants off it. The point here is **not to audit their parquet** -- `../drift_geometry/` already did that -- but to **rebuild the axes on our own corpus**, where we control the instrument and can measure its reliability rather than inherit it.

    axis         source                                       status
    drift        ../drift_geometry/ over 13,557 f11_l2         BUILT (bge-m3, stanza,
                 passages                                      cpu; ICC 0.32 on
                                                               mean_drift, 3.3x F15's)
    surprisal    malign_logits.gen_scores, self and cross      BUILT, no new compute
    external     one reference model scoring everything        NOT YET -- needs BLT

## The surprisal axis needed no compute at all

`gen_scores` already held it, for exactly our passages:

    our drift-measured passages   13,557
    found in gen_scores           13,557   100.0%
      with BOTH self and cross    13,316    98.2%
    with BOTH axes                12,801

`surprisal = -logprob` per continuation token, the definition asserted in
`../selection_and_combination/scripts/m06_mediation.py`. `token_ids` is the
continuation and `plen` is stored separately, so no prompt tokens enter the mean --
which matters because prompt tokens are identical across arms and would dilute
every contrast.

## What it already reproduces

**F15's headline, on our corpus, unanimously.** Self-surprisal, aligned minus base,
per lineage pair:

    median -0.7684 nats/token | 29 of 29 pairs NEGATIVE | sign p=3.7e-09
    range -2.130 to -0.093

**And the off-policy effect is MUTUAL**, which the pooled number hides. Each arm
finds the other's text more surprising than its own, by almost the same amount:

    base text costs the ALIGNED model   +0.1785   28/28 pairs
    aligned text costs the BASE model   +0.2026   28/28 pairs

Pooled across arms these cancel to +0.004, so `s_aligned_minus_base` looks like
nothing until it is split. `composition_not_level.md` saw only the first of these,
because its instrument scored base-generated text; the symmetry is what says the
effect is off-policy distance and not something alignment does.

## SELF-SURPRISAL IS NOT A COMMON YARDSTICK, and this file does not pretend it is

A passage's self-score is its own generator's opinion, so base and aligned passages
are measured by DIFFERENT models. F15 avoided this with an external reference
(Pythia 1B-deduped): one yardstick for everything. **We do not have that yet.** BLT
is the plan for it, and until then every cross-arm surprisal comparison here rests
on a yardstick that moves with the passage.

What IS available is a fixed scorer WITHIN a pair, since both arms score both
texts. Every row carries four numbers:

    s_self         its own generator's surprisal
    s_cross        the other arm's, on the same tokens
    s_by_base      the pair's BASE model's opinion      <- fixed within pair
    s_by_aligned   the pair's ALIGNED model's opinion   <- fixed within pair

`s_by_aligned - s_by_base` is `composition_not_level.md`'s CROSS-SCORER level and
is the only within-corpus yardstick available before BLT.

## The two axes are correlated, and that bears on the quadrants

    spearman(self-surprisal, mean_drift)   +0.392 overall
                              base arm     +0.207
                              aligned arm  +0.424

The quadrant scheme treats drift and surprisal as two dimensions to cross. They are
not independent here, and the dependence is TWICE AS STRONG in the aligned arm --
so a median split produces quadrants whose populations differ by arm for reasons
that have nothing to do with the quadrant names. Not yet analysed; recorded because
any quadrant claim has to deal with it first.

## Why the quadrants are not simply ported

`../drift_geometry/` measured the reliability F15's quadrants rest on, on F15's own
population and with F15's own embedder: **ICC 0.066 for bge-m3 drift**, worse than
the MiniLM 0.082 the audit reported. A median split at that reliability classifies
near-randomly. On OUR corpus `mean_drift` reaches ICC 0.324 -- 3.3x -- which is why
rebuilding rather than porting was the right call.

    F15 corpus   total_drift 0.070   mean_drift 0.098   median 5 sentences
    f11_l2       total_drift 0.162   mean_drift 0.324   median 14 sentences

The mechanism is not isolated: f11_l2 also has ~200 prompts against F15's 47, so
between-cell variance differs by prompt diversity as well as by length. Both are
consistent with the audit's own corrected claim that reliability belongs to the
(corpus, embedder, truncation) triple and must be measured per instrument.

## Outputs

    results/jakobson_by_passage.csv   13,557 rows x 26 columns. Every drift column
                                      from ../drift_geometry/ plus the four
                                      surprisal columns and two contrasts, keyed on
                                      pid / model / arm / pair / prompt / sample_idx.
