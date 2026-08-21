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

## FOUR THINGS MOVE A MODEL ON THESE AXES, AND THIS IS HOW FAR EACH MOVES IT

`synthesis.py`. Raw units cannot be compared -- 0.02 of drift and 0.8 bits of
surprisal are not commensurable, so "alignment reduces both" says nothing about
which it reduces more. Each effect is divided by the PASSAGE-LEVEL sd of its own
axis (surprisal 0.6948, drift 0.0434, the same sd `quadrants.py` z-scored with),
which puts both in units of how spread out passages actually are.

                                  surprisal        drift    which moves more
    alignment (aligned - base)    -1.214 sd    -0.585 sd    surprisal 2.1x
    size (1.7B -> 10.3B)          -1.105 sd    -0.161 sd    surprisal 6.9x
    chat wrapper (cont - raw)     -0.734 sd    -0.864 sd    about equal
    API - aligned                 -0.123 sd    +0.196 sd    drift 1.6x

    alignment    arm_paired.py    22 lineages, paired within lineage, both p<1e-4
    size         scale_ladder.py  Falcon3 aligned arm, one lab, one recipe, 6x
    wrapper      run_wrapper.py   6 models, paired within (model, prompt), M=64
    API          stem_paired.py   89 stems, paired within stem

**These are not four steps of one process.** A model does not go base to aligned
to bigger to wrapped. They are four separate manipulations on overlapping
populations, and the table ranks their sizes.

### What the ordering says

**Alignment is primarily a predictability effect.** It moves surprisal about
twice as far as drift. Real trajectory effect, smaller.

**Size is the most lopsided of the four.** A six-fold parameter range moves
surprisal nearly as far as alignment does and barely touches drift -- 6.9x
apart. Measured on the controlled Falcon3 ladder, not the 47-model regression,
whose drift correlation is confounded with lab, recipe, data and release date.

**The wrapper is the only manipulation that is not lopsided**, and its ranking
differs by axis. On SURPRISAL it is the smallest of the three manipulations
(0.73 against alignment's 1.21 and size's 1.11). On DRIFT it is **the largest
single effect in the table** -- 0.86, against alignment's 0.59 and size's 0.16.
Asking a model to continue a text does less to its predictability than either
aligning it or growing it, and more to its trajectory than either.

### THE WRAPPER CANNOT EXPLAIN THE API MODELS' DRIFT, BECAUSE IT POINTS THE OTHER WAY

The API models drift MORE than open aligned models (+0.196 sd; +0.0085 raw,
64/25 stems, p=4.3e-05) and they were generated behind a continuation frame the
open models did not have. That looks like a confound until the frame is
measured: the measured wrapper effect on drift is **-0.864 sd**, the largest
downward drift force in this table.

So if the API models' frame behaved like the measured wrapper, they would drift
substantially LESS than open aligned models. They drift more. **The observed
direction is opposite to the mechanism proposed to explain it**, and the gap is
not marginal -- the frame effect is four times the size of the difference it
would have to produce, in the wrong direction.

The same reasoning does NOT rescue the surprisal row, where the wrapper (-0.734)
and the API difference (-0.123) share a sign, and where size shares it too.

**One thing this does not close.** The two frames are not identical: the measured
wrapper is a single user turn, `"Continue this text: " + stem`
(`malign-logits/malign_logits/core.py:231`), while the API models got a SYSTEM
message, `"Continue this text for 200-250 words. Do not repeat the text you are
given."` (`generate_task.py:135,280`), with the stem as a separate turn. That
last clause is an instruction to move away from the given text, and distance
from the opening is what the drift axis measures -- so OUR frame could raise
drift by a route the measured wrapper has no equivalent of.

What the table establishes is therefore precise: **a continuation wrapper as such
does not produce this**, and anyone attributing the API drift result to "they had
to be prompted to continue" is proposing a mechanism that runs backwards.
Whether the `do not repeat` clause specifically produces it is untested, and
testing it needs that clause run against a bare condition rather than this pool.

## ALIGNMENT IS NOT SIMPLIFICATION. IT IS THE REVERSE OF IT.

Every direction measured above is one of this campaign's own construction:
base-to-aligned, small-to-large, unframed-to-framed. **Ogden Basic English is a
direction someone else defined**, for reasons that had nothing to do with us --
a deliberate restriction to an 850-word vocabulary, carried out by editors in
the 1930s on stories they did not write. It is the only external, named
simplification available to put on these axes, and the comparison is the first
thing here that tests a direction of ours against a direction of somebody
else's.

`ogden_align.py`, `ogden_axes.py`. Source:
`malign-logits/data/texts/{basic,original}` -- Mansfield, Hemingway and
Andersen paired, plus Joyce in `original` ALONE, because *Finnegans Wake* has no
Basic rendering and that absence is the point it was collected to make.

### The pairing is computed, not assumed

Paragraph counts do not match (46/49, 185/179, 7/11), so pairing by index would
have worked for two texts and silently mispaired the third, whose Basic version
merges paragraphs so heavily that its second paragraph already describes a
different moment. Instead: **monotone alignment, Needleman-Wunsch over
paragraphs**, with merge and split as first-class moves. Both texts tell one
story in one order, so crossing pairings are not penalised but unreachable, and
the search is a shortest path.

Similarity is a bag-of-words Jaccard, deliberately crude. **A tf-idf scheme
would have been worse, not better:** a Basic rendering replaces exactly the rare
words, which are the ones such a scheme weights hardest, so it would score true
pairs LOWER the more Basic-ish they were. Function words and surviving nouns
carry the alignment; the substitutions this exists to find are the tokens the
metric ignores.

    text        matched   merges   jaccard median
    hemingway        46        3        0.82
    mansfield       177       10        0.65
    andersen          7        4        0.28

Andersen's 0.28 is rewriting, not mispairing -- its final pair is *"In the early
morning, there on the earth, was the poor little one"* against *"But in the
corner, leaning against the wall, sat the little girl"*: one moment, almost no
shared vocabulary. Consecutive pairs are then pooled until BOTH sides reach 120
words, giving **47 paired passages** whose correspondence survives pooling
because a group is a contiguous run of already-aligned pairs.

### BASIC ENGLISH IS LESS PREDICTABLE, ON EVERY PAIR

    basic - original       median      n    95% CI            negative
    surprisal (M=100)     +0.7804     47   [+0.632, +0.899]      0%
    surprisal (whole)     +0.6979     47   [+0.563, +0.756]      0%
    drift                 +0.0037     47   [-0.003, +0.011]     45%
    n_sents               +0.0000     47   [ 0, 0 ]              9%

    per text     andersen +1.0543    hemingway +0.4505    mansfield +0.8091

**Unanimous: 47 of 47 pairs positive, and all three texts agree.** Restricting
an author to 850 words makes the prose MARKEDLY LESS predictable. The
substitutions show why -- the constraint does not permit a plain synonym, it
forces circumlocution, and a circumlocution is common words in an arrangement
English does not use:

    "passed on the stairs"   ->  "went through on the flight of steps"
    "that kitty"             ->  "that young cat"
    "the padrone asked me"   ->  "the padrone requested me"

`young cat` is two frequent words in a bigram almost nothing uses. `requested`
is RARER than the `asked` it replaces -- Basic English going UP the frequency
scale, not down. The vocabulary gets simpler and the sentences do not.

### The comparison

                                    surprisal      drift
    alignment (aligned - base)        -0.8435     -0.0254
    simplification (basic - original) +0.7804     +0.0037

**Nearly equal and opposite on surprisal.** Alignment and deliberate
simplification move prose in opposite directions on predictability, at
comparable magnitude. Whatever alignment is doing when it makes text more
probable, it is not what an editor does when restricting vocabulary -- it is the
reverse. A model made more predictable and a story made simpler are not the same
operation and do not even point the same way.

### The drift null, and a mechanism refuted by its own control

Both predictions were registered before the scoring finished
(`results/ogden_prediction.md`): RH said lower drift and higher surprise, and
this seat agreed on both with the reasoning written down. Surprisal was right.
**Drift was wrong -- predicted lower, measured null** -- and the column that
refutes the stated mechanism is in the table.

The argument had been that Basic takes more words over the same ground, so more
sentences carry an unchanged path and the per-step mean falls. `n_sents` is
**identical pair for pair**: zero median difference, zero interval, in 47 pairs
where Basic runs 18% longer in words. The circumlocution happens INSIDE
sentences and never adds one. So the trajectory is untouched by construction and
a null is what a fixed trajectory gives. The prediction failed for a reason the
data names rather than for an unknown one.

### The fence

Three stories by three authors. **The effective n is nearer 3 than 47**, and the
per-text column is reported for that reason; no claim here rests on the pooled
interval alone. The surprisal result is a SIGN claim -- 47 of 47, three texts of
three -- and the magnitudes are not offered as an estimate of anything beyond
these texts. The drift result is a null, not a small effect.

## THE BLIND CODES ON THESE AXES

`../interiority_in_passages` coded 4,931 of these passages blind (rubric
`plans/passC_rubric.md`, kappa 0.904): `degree` 0-3 for how much of the passage
is given over to a character's mind, `mode` TOLD / SHOWN / NONE, and `drift_A`
HOLDS / SHIFTS / UNMOORED for whether it holds its topic. The codes ride on the
ref_pool rows, so all of this is a join and not a coding run.

Every contrast below is computed WITHIN a model and then aggregated to the
lineage, because the codes are arm-skewed -- base passages are coded SHIFTS at
10.3% against aligned's 5.1% -- and a pooled figure would carry the arm effect
inside it.

### Interiority reduces drift. It does not reduce surprisal.

`interiority_axis.py`. RH's hypothesis was that interiority reduces both.

    within model, lineage as the unit    median      neg   pos       p
    spearman(degree, drift)             -0.2207       29     0   3.7e-09
      the same, holding n_sents out     -0.2058       29     0   3.7e-09
    spearman(degree, surprisal)         +0.0486        9    20    0.061

Drift falls monotonically with degree in both arms -- base 0.4873, 0.4706,
0.4619, 0.4429 across degree 0 to 3; aligned 0.4561, 0.4475, 0.4378, 0.4118 --
and the relation survives every control: both arms separately (base -0.2025 at
25/25 models, aligned -0.2197 at 26/26), two-way demeaning by model AND stem
(-0.2183), and the length control.

**Length had to be tested rather than ticked, because it ran the same way as the
finding.** Interior passages carry slightly fewer sentences (-0.0518) and
passages with fewer sentences drift slightly less (+0.0439), so length alone
would produce a negative relation. It accounts for about 7% of it.

Surprisal does not move, and the direction it does not move in is upward.

### THE POOLED CORRELATION REVERSES THE SURPRISAL SIGN

Pooled over all 4,931 passages, `spearman(degree, surprisal)` is **-0.0417**.
Within model it is **+0.0486**. Alignment raises degree (mean 1.799 base against
1.940 aligned) and lowers both axes, so the pooled figure has the arm effect
inside it -- and reports the hypothesis as weakly supported when the within-model
answer points the other way. Both are printed and the pooled one is labelled,
because the gap between them IS the confound.

### The drift axis agrees with a reader who never saw it

`coded_axes.py`. `drift_A` is a human-grade judgment of topical drift; `drift` is
a cosine statistic over sentence embeddings. They share no machinery, so
agreement is the one kind of evidence a metric-versus-metric comparison cannot
give. This replicates `../drift_geometry`'s run on a different population
(narrative-only), a different splitter (the nltk-en stash against stanza) and a
different unit.

    SHIFTS - HOLDS            median      up    dn         p     drift_geometry
    surprisal                +0.1397      23     2   1.9e-05     not measured
    drift                    +0.0136      21     4   9.1e-04     +0.0208, 24/27
    n_sents                  +0.7500      12     7     0.359     +0.985, 22/27

Same direction and magnitude on drift. **Cleaner in one respect:** the original
carried a real length difference and had to argue past it; here `n_sents` is
null, so nothing needs arguing past.

**And the coded judgment tracks SURPRISAL more strongly than it tracks the drift
metric** -- p=1.9e-05 against p=9.1e-04. A passage a reader calls topic-shifting
is more unpredictable to deepseek than it is distant in bge space. The reader was
asked about trajectory and their answer lands harder on the other axis. That is
new; nothing had asked it.

### SHOWN drifts more than TOLD, and both controls were HIDING it

    SHOWN - TOLD        uncontrolled    + degree   + degree & length band
    drift               +0.0041 (.136)  +0.0161    +0.0126   22/2   3.6e-05
    surprisal           +0.0527 (.265)  +0.0428    +0.1155   19/5    0.0066
    n_sents             +1.50           +1.65      +0.67            0.383

Mode is confounded with degree -- TOLD holds 1,181 passages at degree 1 against
SHOWN's 119 -- and SHOWN runs 1.6 sentences longer, so both controls were needed.
Both were SUPPRESSING the effect, not inflating it: uncontrolled the drift
difference is null, and with degree and length held the residual length
difference goes null while both axes strengthen. Showing moves through more
semantic space and is less predictable than telling.

**It is not the arm's mechanism.** The arms produce SHOWN at the same rate
(lineage-paired, 10 up / 12 dn, p=0.83), so mode locates the axes without
explaining base->aligned. That check runs inside the producer, because a reader
who has just seen SHOWN drift more will reach for it as the explanation.

`NONE` is dropped as an alias for degree 0 -- all 146 NONE passages are degree 0
and the rubric mandates it. `UNMOORED` is dropped and counted: 16 of 4,931, too
thin for a per-model contrast, and folding it into SHIFTS would have changed the
construct being validated without saying so.

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
    interiority_axis.py  the `degree` code against both axes, within model
    coded_axes.py        `drift_A` and `mode_A` against both axes; the drift
                         validation against a reader who never saw the embedding
    checks.py            re-runs every provenance claim these docstrings make,
                         PASS/FAIL against the value the prose quotes

The observer-side work moved to `../surprisal_matrix/` -- the same text scored
by its own generator, its lineage partner and an external reference, which is
where the self-versus-external entropy question lives and where F18's "private
language" finding was retried.

The generation-side calibrations moved to
`../../instrument_calibrations/generation_provenance/` -- the deployment frame,
provider injection, decoder parameters and nucleus truncation. They ask whether
this folder's API-versus-open contrast is about the models or the apparatus, and
the short answer is that the frame and the truncation both point AWAY from the
observed effect while the sampling parameters were not what we asked for.
    synthesis.py         all four effects on one scale, in sd of each axis
    ogden_align.py       monotone paragraph alignment of Basic English against
                         its original; --group-words pools aligned pairs
    ogden_axes.py        the simplification direction on both axes, paired
    scale_axes.py        params_b against both axes across 47 models (the drift
                         rows are confounded -- see scale_ladder.py)
    scale_ladder.py      the Falcon3 ladder: one lab, one recipe, four sizes
    extrapolate.py       where the size trend predicts the API models should sit
    run_wrapper.py       the "Continue this text:" frame effect on both axes
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
