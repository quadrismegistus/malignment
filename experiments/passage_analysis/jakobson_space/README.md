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

**This verdict is about the ENTITY grain and the next section qualifies it.** At
the passage grain the same measurements give `r = +0.348` and four occupied
quadrants; nothing above is withdrawn, but "the quadrants do not survive" is true
of medians-of-models and false of passages.

### THE GRAIN WAS THE PROBLEM. AT PASSAGE LEVEL THE QUADRANTS ARE OCCUPIED

Everything above stands as written. At the ENTITY grain -- one median per model
or corpus -- `r(surprisal, drift)` is `+0.749` and the off-diagonal holds 16% of
70 entities, and that remains the right description of the entity plane. What it
could not see is that most of the correlation was made by the averaging.

    grain      n         r(surprisal, drift)   surprisal explains
    entity     70        +0.749                56% of drift variance
    passage    14,414    +0.348                12%

Collapsing a model's passages to one point removes the within-model scatter, and
the within-model scatter is where the two axes are close to independent. The
entity plane is a diagonal; the passage plane is not; both are true of the same
measurements. **A quadrant claim therefore has to name its grain**, and the
earlier verdict was a verdict on the entity grain only.

At the passage grain all four cells are substantively occupied. The reference is
all 14,414 passages pooled, which the manifest beside `quadrants.csv` records:

    all passages         23.0%  (+s+d)   23.4%  (+s-d)   28.1%  (-s+d)   25.4%  (-s-d)

    category         n   (+surp +drift)  (+surp -drift)  (-surp +drift)  (-surp -drift)
    base          2,195      43.2%           44.0%            7.8%            5.0%
    aligned       2,736      15.6%           23.4%           27.6%           33.5%
    API           6,508      13.6%           14.2%           41.1%           31.1%
    literary_crit   499      66.7%           23.0%            8.8%            1.4%
    c20_fiction     500      62.2%           22.2%           11.2%            4.4%
    philosophy      500      33.6%           37.0%           14.0%           15.4%
    arxiv_abstr     500      28.0%           45.0%           12.0%           15.0%
    dreams          476      18.9%           37.4%           15.3%           28.4%
    waking_narr     500       3.0%            7.6%           28.2%           61.2%

**The three AI categories are ordered along the diagonal and the human corpora
are not.** Base models put 87.2% of their passages in the high-surprisal half;
aligned models spread across all four; API models put 72.2% in the low-surprisal
half. The human corpora meanwhile occupy the plane's corners -- literary
criticism 66.7% in `(+s+d)`, waking narrative 61.2% in `(-s-d)` -- so the axes
are not measuring "human vs machine" in either direction. They separate kinds of
writing, and the arms move through them.

#### The off-diagonal cells are F15's metaphoric and metonymic quadrants

Enrichment against the pooled rate, `1.00x` meaning "the same share as all
passages":

                        (+surp -drift)      (-surp +drift)
                         METAPHORIC          METONYMIC
    base                    1.88x              0.28x
    aligned                 1.00x              0.98x
    API                     0.60x              1.46x

    arxiv_abstracts         1.92x              0.43x
    dreams                  1.59x              0.55x
    philosophy              1.58x              0.50x
    literary_criticism      0.98x              0.31x
    c20_fiction             0.95x              0.40x
    waking_narrative        0.32x              1.00x
    all human               1.22x              0.53x

**Monotone across the three arms, in opposite directions.** Metaphoric
1.88 -> 1.00 -> 0.60; metonymic 0.28 -> 0.98 -> 1.46. Alignment sits at
almost exactly the pooled rate on both, which is the least interesting position
on the axis and the easiest to state: the aligned arm is the crossing point.

Both off-diagonal cells are more AI than human in absolute share, and they are
so for different reasons. The metaphoric cell is enriched in base models AND in
`arxiv_abstracts`, `dreams` and `philosophy` -- three human corpora with little
else in common except that none of them narrate a sequence of events. The
metonymic cell has exactly one human corpus at parity, `waking_narrative`, and
that is the corpus made of people recounting what happened next.

So the human occupancy is not noise around an AI effect. It is the register
distinction the quadrant names were always about, and the API models sit at the
`waking_narrative` end of it while base models sit at the `arxiv_abstracts` end.

#### Everything above is descriptive. Here it is tested, three ways.

Shares and enrichments say two populations differ. They cannot say alignment
MOVES anything -- the arms hold different models, and between-lineage variance
dominates the arm effect. Three paired designs, three units, each answering a
question the others cannot.

**`arm_paired.py` -- the lineage.** Each aligned checkpoint against its own base,
children averaged first so a family with four instruct variants gets one vote.
22 lineages of 59 (54 models are in `quadrants.csv`; 22 lineages have both arms
at 10+ passages). Sign test, exact two-sided:

    ALIGNED - BASE            median      up    dn        p
    surprisal                -0.8435       0    22   4.8e-07
    drift                    -0.0254       1    21   1.1e-05
    (+surp +drift) breakdown -0.2911       1    21   1.1e-05
    (+surp -drift) metaphoric -0.1581      3    19   8.6e-04
    (-surp +drift) metonymic +0.2134      20     1   2.1e-05
    (-surp -drift) unmarked  +0.2173      21     0   9.5e-07

**`stem_paired.py` -- the stem.** The API models ship no base, so the lineage
design cannot reach them; what they share with the open models is the prompt. 97
of ~100 narrative stems carry all three categories, so the scene is pinned and
only the generator varies. Within a stem a category is the median over all its
models' passages, so models are POOLED inside the cell -- right for "does
category A differ from B on this scene", wrong for "does alignment move a model",
and where the two disagree the lineage design governs.

    API - ALIGNED, 89 stems   median      up    dn        p
    metonymic                +0.1569      72    16   1.2e-09
    metaphoric               -0.0923      20    68   2.8e-07
    drift                    +0.0085      64    25   4.3e-05
    surprisal                -0.0852      33    56   0.019
    unmarked                 -0.0084      42    47   0.67   NULL

**The API step is not a continuation of the alignment step.** base->aligned
drains breakdown and metaphoric into metonymic AND unmarked (+0.2619, 79/1,
p=1.3e-22). aligned->API drains them into metonymic ONLY, and unmarked is flat.
Same direction on one axis, different on the other, and the null is the
informative half.

The `aligned - base` row of the stem design lands at -0.8444 surprisal and
-0.0243 drift against the lineage design's -0.8435 and -0.0254. Two different
units agreeing to three decimals is a consistency check on the pipeline, not a
second result, and it is not quoted as one.

**`arm_paired.py --human` -- toward or away from each human corpus.** Euclidean
distance on the (z_surprisal, z_drift) plane from each arm's median to a corpus
median, differenced aligned-minus-base, same 22 lineages.

    corpus                   median     twd   awy        p
    waking_narrative        -0.9004      22     0   4.8e-07   TOWARD
    dreams                  -0.5077      15     7   0.134
    philosophy              -0.0110      11    11   1.0
    arxiv_abstracts         +0.1691       9    13   0.523
    c20_fiction             +0.8377       1    21   1.1e-05   away
    literary_criticism      +0.9150       1    21   1.1e-05   away

**Alignment moves every one of 22 lineages toward people recounting what happened
next, and away from literary fiction and criticism.** That is the same fact as
the metonymic enrichment, seen from the human side: waking narrative is the one
human corpus at parity in the metonymic cell, and it is the one every lineage
approaches.

This is run per corpus and NEVER against a pooled human centroid. The six corpora
occupy opposite corners of this plane, the six answers disagree in sign, and
their centre sits in a region none of them occupies -- a distance from nowhere.

#### The four directions were predicted, on a different corpus, before that data

`~/github/malign-logits/meta/M06_generation/plans/plan_f15_on_passages.md`
declared all four before its run and its producer confirmed all four on the M06
passage corpus: 38 matched pairs, GPT-2 reference, forced-continuation rung on
the M01 sites, under TWO embedders.

    aligned - base       M06 MiniLM       M06 bge-m3        HERE (22 lineages)
    surprisal            -0.53  35/38     -0.62  33/38      -0.84   22/22 dn
    drift                -0.023 34/38     -0.030 34/38      -0.025  21/22 dn
    Q2 breakdown         -0.211 35/38     -0.335 36/38      -0.291  21/22 dn
    Q3 metaphoric        -0.157 34/38     -0.123 32/38      -0.158  19/22 dn
    Q1 metonymic         +0.137 34/38     +0.114 31/38      +0.213  20/22 up
    Q4 unmarked          +0.224 35/38     +0.299 35/38      +0.217  21/22 up

Their Q1 is our `(-surp +drift)` and their Q3 our `(+surp -drift)`; the
definitions match. **Four for four, across a different corpus, a different rung,
a different reference model and a different embedder.** M06's numbers are the
prediction and these are the test, because theirs were written down first.

The API arm has no counterpart there and is new here.

#### Read on two passages that continue almost the same stem

The corpus supplies a near-controlled pair: `granite-3.0-8b-base` continuing
"He was ugly and misshapen and she wanted to", and `gemini-3.5-flash` continuing
"He was ugly and she wanted to". Same scene, opposite quadrants, opposite arms.
Both are drawn at the 85th percentile of distance from the origin rather than
from the tips, because the tip of a two-axis plane is usually a malformed
passage and quoting it would be an illustration sampled on its own effect size.

`read_passage.py --id mode-b708426d81badd` -- METAPHORIC, `+2.45` surprisal:

    most surprising   Jacint, 29.1   bodin 26.8   red-head's 21.3   rivulets 20.2
    concentration     4% of 172 words cost under 0.5 bits

    +0.509 | 0.589 |  8.87  Two.
    +0.375 | 0.547 |  6.54  Did they wear shoes?
    +0.410 | 0.572 |  2.63  One did, the other did not.
    +0.528 | 0.651 |  8.12  <-- Yes, before the Count, the Countess and their tall,
                                shy friend, Mad Jacint, ...

The expensive words are names and substitutions -- `Jacint`, `bodin`,
`rivulets` -- arriving in place of words that would have cost nothing. The
passage circles one scene; it does not go anywhere.

`read_passage.py --id google_gemini_3_5_flash-v5-031-0` -- METONYMIC, `-1.25`:

    most surprising   outward 21.2   draft. 16.1   "Don't 13.9   harsh, 13.4
    concentration     20% of 229 words cost under 0.5 bits

    +0.444 | 0.444 |  4.20  She stared at his crooked nose, the uneven spacing of
                            his eyes, and the harsh ...
    +0.478 | 0.398 |  3.22  She wanted to look away, to find comfort in the familiar
                            shadows of the alley ...
    +0.413 | 0.593 |  4.47  In his palm rested a small, glowing glass vial, pulsing
                            with a soft violet ...

Nose to eyes to jaw to voice to alley to streetlamp to vial: contiguity, each
detail handing off to the one beside it. **Five times as many words cost under
half a bit** -- 20% against 4% -- on a passage that travels further.

#### Does the surprisal sit in the sentences that move? Weakly yes, and never at the furthest one

Joining the two grains on the sentence row makes this a query rather than an
inference. Per passage, the correlation between a sentence's mean bits and its
step from the previous sentence; then a median per model; then per arm.
`within_passage.py`, 14,249 passages with at least 5 usable sentences:

                    n   r(bits, step)   r(n_words, step)   partial r   furthest hi-bits
    base           26      +0.216           +0.022          +0.212          56.4%
    aligned        27      +0.214           -0.051          +0.210          50.7%
    API            11      +0.130           -0.020          +0.137          47.7%

**The relation is positive everywhere and it is not length.** The partial
correlation holding `n_words` out is within 0.01 of the raw one in every arm, so
this is not short sentences taking big steps. It is small -- `+0.13` to `+0.22`
explains 2-5% of the variance in a step -- but it is consistent across 64 models
and across all four quadrants (`+0.123` to `+0.215`).

**The furthest sentence is NOT the surprising one.** Whether a passage's
furthest-from-opening sentence also sits above that passage's median sentence
bits is at chance in every arm: 56.4% for base (sign test over 26 models,
p=0.076), 50.7% aligned, 47.7% API. Only API clears p<0.05 (1 of 11 models above
half, p=0.012) and eleven commodity endpoints from three vendors are not a
sample of anything, so that is an observation and not a result -- and it was not
registered in advance.

So the two axes touch each other locally and not cumulatively. Surprisal travels
with the STEP, the move from one sentence to the next, and carries no
information about total displacement. That is the shape you would want if
selection and combination were separable, and it is the first thing in this
folder measured WITHIN a passage rather than across a population.

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

    results/quadrants.csv             14,414 passages: both axes, the residual,
                                      three z-scores, the quadrant, and the TEXT
    $MALIGNMENT_DATA/jakobson_space/exploded/
      words.parquet                   3,040,970 rows, one per word, with the bits
                                      deepseek spent on it
      sentences.parquet                 196,349 rows, one per sentence, with its
                                      step, its displacement, and mean_bits

    quadrants.py       builds results/quadrants.csv and the occupancy tables
    arm_paired.py      base->aligned, paired within LINEAGE; --human for the
                       toward/away test against each corpus
    stem_paired.py     API vs aligned vs base, paired within STEM (the API
                       models have no base, so the lineage design cannot reach
                       them)
    explode.py         builds the two parquets above from the existing sidecars
    read_passage.py    renders one passage with both decompositions marked on it
    within_passage.py  the within-passage bits-vs-step correlation, length-controlled
    ingest_exploded.py loads all three grains into ClickHouse

### The three grains are queryable in ClickHouse

`malignment.passage_axes` (14,414), `passage_words` (3,040,970) and
`passage_sentences` (196,349), loaded by `ingest_exploded.py --replace`. The
database is `malignment`, ours; RH's other project lives in `abstraction`, `lltk`
and `llmtasks` and no statement here is unqualified.

`category`, `model` and `quadrant` are denormalised onto every word and sentence
row. That is redundant on purpose: the use for these tables is colouring a plot
by arm or by quadrant, and a reader who must remember to join 3M rows back to 14k
to get `category` will eventually join on the wrong key -- and a wrong join here
produces a plot that looks right.

    -- the words alignment finds cheap that base models do not
    SELECT word, count() n, round(avg(bits),2) b
    FROM malignment.passage_words WHERE category='aligned' AND partial=0
    GROUP BY word HAVING n > 200 ORDER BY b ASC LIMIT 40

    -- does surprisal ride the step, per arm
    SELECT category, round(corr(mean_bits, step),3) FROM malignment.passage_sentences
    WHERE step IS NOT NULL AND mean_bits IS NOT NULL GROUP BY category

That second query POOLS sentences and so answers a different question from
`within_passage.py`, which takes one correlation per passage and then a median
per model. Pooled it gives aligned `+0.270` against base `+0.218`; per model it
gives `+0.214` against `+0.216`, a tie. The pooled version lets a model with more
passages, and a passage with more sentences, count more -- so it is the right
query for "how do these two columns covary in this table" and the wrong one for
any claim about an arm. Both are correct about what they measure.

**Every sentence row carries `reproduces`**: whether `mean(step)` reproduces that
passage's own `drift` to 1e-6. It is true for 14,414 of 14,414 passages, which is
worth nothing until it isn't -- it is the one defect a re-grained table can have,
and it is a stored column rather than a claim in a README.

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
