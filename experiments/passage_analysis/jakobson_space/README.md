---
subject: jakobson_space
question: What do F15 and F16's axes look like when rebuilt on OUR corpus?
status: all three axes BUILT; external axis twice (BLT bytes, then deepseek tokens); human anchor placed
grain: page
---

# jakobson_space

F15 and F16 place passages in a space of **surprisal x drift** and read Jakobsonian quadrants off it. The point here is **not to audit their parquet** -- `../drift_geometry/` already did that -- but to **rebuild the axes on our own corpus**, where we control the instrument and can measure its reliability rather than inherit it.

    axis         source                                       status
    drift        ../drift_geometry/ over 13,557 f11_l2         BUILT (bge-m3, stanza,
                 passages                                      cpu; ICC 0.32 on
                                                               mean_drift, 3.3x F15's)
    surprisal    malign_logits.gen_scores, self and cross      BUILT, no new compute
    external     BLT (itazap/blt-1b-hf), per BYTE              BUILT
    external     deepseek-llm-7b-base, per TOKEN               BUILT -- the one to use
    anchor       3,000 human passages, 6 corpora, 193 words    BUILT and PLACED

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

## SELF-SURPRISAL IS NOT A COMMON YARDSTICK -- SUPERSEDED, THERE IS ONE NOW

**The section below described the state before an external reference existed.
There are now two, and `deepseek-llm-7b-base` is the one to use.** It is kept
because every self/cross number above it still rests on the moving yardstick it
describes, and a reader needs to know which claims are which. Anything wanting a
common scale should use the deepseek axis and the anchor, both below.

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

## THE EXTERNAL AXIS AND THE HUMAN ANCHOR -- the finding this folder now carries

**Alignment moves a model down a human range it already sat inside.** Both axes
on one row for 8,145 passages, `results/two_axes.csv`, built by `two_axes.py`.
Surprisal at M=200 tokens under `deepseek-llm-7b-base`; drift uncontrolled
because `mean_drift` is length-free. Model rows are medians of per-model medians
over 26 base and 27 aligned checkpoints, human rows over passages.

    group                       bits/token   mean_drift        n
    MODEL base                      4.4958       0.4617       26 models
    human literary_criticism        4.4543       0.4963      499 passages
    human c20_fiction               4.3558       0.4833      500 passages
    human arxiv_abstracts           4.1581       0.4496      500 passages
    human philosophy                4.0397       0.4521      500 passages
    human dreams                    3.8457       0.4369      476 passages
    MODEL aligned                   3.7298       0.4394       27 models
    human waking_narrative          3.2884       0.4211      500 passages

**The arm effect is on BOTH axes, lineage-paired with the model as the unit:**

    surprisal   aligned lower in 24 of 24 lineages   sign p = 1.19e-07
    drift       aligned lower in 23 of 24            sign p = 2.98e-06

**The two arms of one technology span nearly the whole human spread** on
surprisal -- 4.4958 to 3.7298 against a human 4.4543 to 3.2884 -- so alignment
moves a model 65% of the distance from literary criticism to a diary.

**And where the axes DISAGREE is the point of the joint table.** Base is FIRST in
surprisal and THIRD in drift: locally unpredictable, globally static. Literary
criticism and fiction invert it -- more predictable word to word, further
travelled across the passage. A single entropy number hides that.

Not claimable: base against the two literary corpora, +0.0414 and +0.1400, which
flip below M=175 and M=150 (`ref_anchor.py --sweep`). Everything else is stable
at every prefix from 60 to 200 tokens.

**Reading the surprisal axis in BYTES gets it wrong.** arXiv abstracts run 5.53
bytes/token against dreams' 4.28, so a per-byte reading credits them for packing
more characters into each decision and puts them second-most-predictable; per
token they are mid-range. **M=200 is not an eyeball either**: it is the largest
prefix at which every human corpus retains 100%, and at 220 waking narrative is
already 54% and length-selected. An earlier per-byte version quoted K=1000, where
dreams was 27% of its sample; that number is withdrawn.

**The model population is narrative-coded.** All 5,687 are `narrative_A == True`
from `../interiority_in_passages/results/passC/codings/`, 28 shards, verified
cell by cell -- a filter that removes 54% of the coded corpus (6,174 against
7,383). This is a claim about NARRATIVE continuations, not model output at large.
(`ANNOTATIONS.md` there claims to list every annotation run and has no passC
entry, though passC's `narrative` field defines this population.)

## The two axes are correlated, and that bears on the quadrants

    r(deepseek surprisal, mean_drift)   +0.869 over the 8 GROUPS
                                        +0.414 over the 8,145 PASSAGES

So they rank a CORPUS almost interchangeably and cannot substitute for one
another on a PASSAGE. On the older self-surprisal axis:

    spearman(self-surprisal, mean_drift)   +0.392 overall
                              base arm     +0.207
                              aligned arm  +0.424

The quadrant scheme treats drift and surprisal as two dimensions to cross. They are
not independent here, and the dependence is TWICE AS STRONG in the aligned arm --
so a median split produces quadrants whose populations differ by arm for reasons
that have nothing to do with the quadrant names.

### ANALYSED NOW, AND THE QUADRANTS DO NOT SURVIVE IT

70 entities on the plane -- 53 open models, 6 human corpora, 11 API models, each
a median of its own passages. **r(surprisal, drift) = +0.749.** Z-scoring both
axes and crossing them at zero:

    reference              HH    Hl    lH    ll    off-diagonal
    six human corpora      24    16     2    28    18 of 70 = 26%
    53 open models         32     3    11    24    14 of 70 = 20%
    all 70 entities        36     4     7    23    11 of 70 = 16%

**Under independence the off-diagonal cells would hold 50%. They hold 16-26%.**
So this is not four populations, it is a diagonal with scatter, and the two
off-diagonal quadrants -- the ones whose NAMES carry the Jakobsonian content --
hold 11 of 70 entities at best.

**AND THE REFERENCE CHOICES DISAGREE ABOUT WHO IS WHERE.** `salamandra-7b` is
HIGH/low against the human corpora and HIGH/HIGH against the open models;
`arxiv_abstracts` moves the same way. Off-diagonal membership swings from 18 to
11 depending on which population defines zero, so "which quadrant is X in" has no
answer until the reference is declared -- and the six-corpus reference is the
weakest of the three, an sd estimated from six points.

**What the plane does separate is the arm, and almost perfectly:**

    kind        HH    Hl    lH    ll
    base        25     1     0     0
    aligned      6     3     3    15
    api          1     0     4     6
    human        4     0     0     2

25 of 26 base models sit in HIGH/HIGH. Aligned models are mostly `ll` but occupy
all four cells; API models are 10 of 11 in the low-surprisal half. So the
contrast this corpus supports is ONE DIAGONAL, and the quadrant names do no work
beyond it. A four-quadrant reading needs a corpus where the axes are closer to
independent than +0.749.

Reproduce: `two_axes.py --csv results/two_axes.csv`, then z-score the per-entity
medians. `api_placement.py` carries the CIs.

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
    results/two_axes.csv              8,145 rows, deepseek surprisal x bge drift,
                                      models AND the human anchor on one scale
    results/population_manifest.json  what build_population.py wrote, and its drops
    alignment_smooths.md              the BLT-axis finding, 42/46 lineages

    two_axes.py      builds results/two_axes.csv and the summary above
    ref_anchor.py    the anchor on the deepseek axis, with --sweep for stability
    ref_surprisal.py scores any text with deepseek; roundtrip-guarded
    build_human_pool.py / normalise_task.py / finalise_human.py   the anchor

### Where the anchor came from

3,000 passages, 500 each from six corpora, **all cut to exactly 193 words** and
orthographically normalised by an LLM pass so the measurement is of syntax and
semantics rather than of how fast somebody typed. `normalise_spec.md` is the
task text and is read from disk by `normalise_task.py` with an assert that the
curly characters survive -- because transcribing the rule into a Python string
turned it into an ASCII-to-ASCII no-op once already.

Byte lengths still differ by corpus at fixed words (abstracts 1,406 median
against dreams' 970), which is why the surprisal axis is taken at a fixed TOKEN
prefix and not at fixed words or bytes.
