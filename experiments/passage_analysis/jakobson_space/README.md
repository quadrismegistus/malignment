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

## THE POPULATION FILE

    $MALIGNMENT_DATA/jakobson_space/passages.parquet
    432,064 rows | 38 columns | 228 MB | 94 models | 76 lineages

Both axes for the whole generated corpus, with the text and every key needed to
reach anything else. Built by `build_population.py`; a manifest sits beside it.

    corpus    passage 223,053 | f11_l2 192,119 | y 16,892
    script    en 357,236 | zh 74,828
    arm       base 217,667 | aligned 214,397

    identity    text_sha  prompt  TEXT  corpus  corpora  script
    ClickHouse  model  sample_idx  role  pair  prompt_id  temp  seed
                gen_n_tokens  finish_reason
    arms        arm  arm_src  lineage
    BLT         bits_per_byte  blt_ref  blt_box  blt_shard  blt_row  blt_n
                n_bytes  n_chars  blt_n_tokens
    bge         bge_embedder  splitter  n_sents
    drift       mean_drift  max_drift  std_drift  total_drift  path_length
                directedness  mean_pairwise  ordering

**One row per passage, with pointers down to the finer grains rather than copies.**
`bge_embedder + prompt + text` IS the sentence-vector stash key;
`blt_box + blt_shard + blt_row + blt_n` locates the per-byte float32 block. A
per-sentence table is not built: 4.4M sentences at 1024 float32 is ~18 GB and the
step distances are recomputable in seconds.

**`arm` had to be derived for f11_l2 and the file says so.** ClickHouse carries
`role` and `pair` for `passage` and `y` and leaves BOTH EMPTY on all 192,119
f11_l2 rows -- which would have made base-vs-aligned unrecoverable on the one
corpus the drift axis was validated against. `roster.lineages()` fills it;
`arm_src` records whether ClickHouse or the roster answered, so a disagreement
stays visible and anyone who distrusts the derivation can restrict to
`arm_src == 'clickhouse'`.

### Two fences on this file

**50,896 passages dropped (10.5%) for having no sentence vector** -- the `mixed`
script stratum that `--mixed-policy refuse` declined to embed. **Not missing at
random**: these are the code-switched passages, and f11_l2 loses 16% of itself
that way. A cross-lingual question asked of this file is asked of the non-mixed
corpus.

**24,648 rows carry null drift** (n_sents < 2). Present rather than dropped, so
absence reads as absence, but any mean over a drift column must exclude them.

## Outputs

    results/jakobson_by_passage.csv   13,557 rows x 26 columns, the f11_l2 sample
                                      with self/cross surprisal from gen_scores
    results/population_manifest.json  what build_population.py wrote, and its drops
