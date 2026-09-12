---
subject: architectures
kind: question
status: "RUN 2026-09-11 on the BLT axis, which is SUPERSEDED -- deepseek is the campaign's surprisal reference and covers only 3 of this subject's models, so the fluency-orthogonal drift_residual that would settle this question cannot be computed for the architectures it is about. ENGLISH ONLY (script=en; the 48 zh rows in this slice go through stanza-zh segmentation and the zh bge variant, so a sentence is not the same unit -- excluding them moved nothing, falcon-mamba stayed 17/37 and the fluency correlation went +0.734 to +0.726). Mined from ~/malignment-data/jakobson_space/passages_std.parquet (358,633 passages, 92 models). No generation, no GPU. Base arm, corpus=passage, n_sents>=3, 6 models paired on 147 prompts held by all of them. NOT REGISTERED. The declared population is 6 models because the parquet covers only three non-dense architectures; recurrentgemma-9b is present but UNUSABLE at 38 rows and a median of one sentence."
question: Does the syntagmatic axis -- how the chain coheres from sentence to sentence -- depend on the attention mechanism?
headline: "NO, AND THIS IS THE ONE THAT SHOULD HAVE GONE THE OTHER WAY. Ranked against the WHOLE spread (37 base models, 181 common-core prompts): the two pure-SSM models sit at 6/37 and 17/37 on sentence drift and 14/37 and 8/37 on cohesion, and BOTH ENDS of the range are dense full-attention transformers (gemma-2-9b lowest at 1/37, Amber highest at 37/37). Attention is a COMBINATION mechanism, so the syntagmatic axis is the one place this subject had a reason to expect a difference; the paradigmatic nulls elsewhere are cheap because selection lives in the softmax, which every model has. falcon-mamba-7b, computing no attention at all, sits mid-pack on every metric that clears its own noise (mean_drift 3/6, mean_pairwise 2/6, bits_per_byte 2/6). The one robust between-model effect is gemma-2-9b, a DENSE full-attention transformer, which every other model exceeds on mean_drift on 95-98% of 147 paired prompts. Two of the five metrics sit BELOW their own noise floor and are not interpreted."
---

# combination

**The syntagmatic test, and the prediction it refuted.**

Every other question in this subject reads the paradigmatic axis: which word goes in a slot. That is the unembedding matrix and the output softmax, which every model here has, transformer or not, so those nulls are cheap by construction.

**Attention is a combination mechanism.** It relates positions within a sequence -- items present together in the chain, *in praesentia* -- which is the syntagmatic axis by definition. It is the one place this census had an actual reason to expect architecture to show. It does not.

## What was mined

`jakobson_space`'s `passages_std.parquet`: 358,633 passages over 92 models, already carrying bge sentence-drift geometry. No generation and no GPU; this question is a read.

    model                  attn        block      drift  pairwise  bits/byte
    gemma-2-9b             full        dense     0.4642    0.4987     1.1233
    Falcon3-7B-Base        full        dense     0.4953    0.5290     1.3996
    falcon-mamba-7b        none        ssm       0.4968    0.5234     1.2990
    Falcon-H1-7B-Base      full+ssm    hybrid    0.4969    0.5245     1.3529
    Olmo-3-1025-7B         full+local  dense     0.5001    0.5318     1.4019
    OLMoE-1B-7B-0125       full        moe       0.5003    0.5365     1.3268

**`falcon-mamba-7b`, with no attention of any kind, is third of six on drift and second on cohesion -- inside the dense transformers, not beside them.** The model that stands out is `gemma-2-9b`, and every other model exceeds it on `mean_drift` on 95-98% of the 147 paired prompts. It is a dense transformer with full attention.

## THE LONG-CONTEXT REGIME, AND THE SIGNAL THAT WAS RANGE RESTRICTION

    python run.py --long

**Why this regime exists as a separate question.** Attention's distinctive technical contribution is exact long-range recall: it keeps every past position and can re-read any of them, where a recurrent state keeps a fixed-size summary. The passage corpus is 188 words median -- far too short to exercise that, which is a reason to expect the nulls above rather than to be surprised by them. `national_story` generations are **1,503 words median, eight times longer**, and `story_drift.jsonl` already carries drift on them.

**THE FIRST PASS FOUND A SIGNAL AND IT WAS AN ARTIFACT. Kept, because it is the warning.** Regressing `mean_drift` on `n_words` per model put the attention-free models at the top: `falcon-mamba-7b-instruct` had the HIGHEST slope of 56 models, +0.0866 against a roster median of +0.0007. In the predicted direction, in the regime where the prediction says it should appear, and it survived a first artifact check (short-output models have higher slopes generally at Spearman -0.229, but length-matched dense models sat at +0.0057 against non-dense +0.0224).

Binning by length instead of fitting a slope reverses it:

    length bin      attention-free           has attention          gap
                 median  mdl  texts      median  mdl  texts
    200-600      0.4247    2     80      0.4353   43    882      -0.0106
    600-1200     0.4372    2     52      0.4413   63   1666      -0.0041
    1200-2000       --     0      0      0.4543   51    926          --
    2000-9999       --     0      0      0.4535   38    811          --

**Attention-free drift is LOWER wherever the two groups overlap, and the group is absent from the long bins** -- but read that carefully. `falcon-mamba` writes 557 words median and **2 of its 57 raw generations exceed 1,200 words, the longest 2,362.** It is this file's `MIN_IN_BIN = 5` that drops them, not the model. An earlier version of this section said the model produced NONE, which is false, and the difference is the difference between a claim about a capability and a claim about a sample size. Its slope had been fitted inside 200-1200 and compared against slopes fitted over 200-2500. **So this corpus cannot MEASURE an attention-free model at length. That is not evidence that it fails at length.**

Two further corrections the first pass needed. The unit is the MODEL, not the text, because one model contributing 900 texts to a bin would otherwise set that bin's median. And the split is by ATTENTION, not by block: the first pass counted `OLMoE` as non-dense when it is a mixture with FULL attention, which took the apparent n from one lineage to three.

**n is one lineage.** `Zamba2-7B` is in `national_story` (23 and 27 raw rows) but is a `full+ssm` hybrid; `recurrentgemma-9b` has ONE base row. The corpus that could have answered this does not contain the models it needs.

## ON THE CORRECT SURPRISAL AXIS: deepseek, scored here

    python run.py --score      # deepseek via malignment.score, cached

The jakobson deepseek axis cannot reach these architectures -- its pool is gated on a 58-model blind narrative coding over `f11_l2`, and `f11_l2` holds only three of this subject's models, all dense or MoE. So it was rebuilt here: 5,200 passages over 13 models, both arms, scored through `malignment.score.surprisal` so the result lands in the shared sha-keyed store (96,305 entries) rather than a private sidecar.

    BASE arms, deepseek bits/token, M=50
    gemma-2-9b            4.2818   full / dense
    falcon-mamba-7b       4.7879   none / ssm
    Falcon3-Mamba-7B      5.0093   none / ssm
    OLMoE-1B-7B-0125      5.1042   full / moe
    Falcon-H1-7B-Base     5.1387   full+ssm / hybrid
    Falcon3-7B-Base       5.1773   full / dense
    Olmo-3-1025-7B        5.2287   full+local / dense

**Bracketed at both ends by dense transformers, with every non-dense model inside the range.** The same shape the drift axis gave, now on the campaign's own reference instead of the superseded byte-level one. Incidentally the arm effect reproduces F15: every aligned model sits 0.7 to 0.8 bits/token below its base, which is larger than the whole architecture spread.

### THE PREFIX IS 50 BECAUSE M=200 SELECTS ON LENGTH

`score.surprisal` returns None when a passage has FEWER than M scored tokens -- it drops the passage rather than shortening the window. So the prefix selects on length, and length differs by model. Measured retention over 400 sampled passages each:

    model                      M=50  M=100  M=150  M=200
    falcon-mamba-7b-instruct    96%    80%    67%    56%
    OLMoE-1B-7B-0125-DPO        96%    87%    80%    74%
    gemma-2-9b-it              100%   100%   100%   100%
    falcon-mamba-7b             99%    94%    92%    89%

**A 44-point differential at M=200, on the one model that has already failed two other screens** (3.4% to the degeneracy filter, 1.4% sub-threshold repetition). M=200 is right for `jakobson_space`, whose human corpora all clear it; it is wrong for a cross-MODEL comparison. At M=50 the spread is 4 points and overall retention goes 85.9% to 98.6%.

## Where no-attention falls in the whole spread

    python run.py --spread

The six-model set answers "are these six alike"; it cannot say whether a rank is unusual, because six models have no distribution. This ranks every base model with >= 150 prompts on the prompts held by >= 90% of them: **37 models, 181 common-core prompts, 94,401 passages.**

    model                      attn       block      drift  rank  pairwise  rank
    Falcon3-Mamba-7B-Base      none       ssm       0.4920  6/37    0.5265  14/37
    Falcon-H1-7B-Base          full+ssm   hybrid    0.4964 14/37    0.5240  10/37
    falcon-mamba-7b            none       ssm       0.4975 17/37    0.5235   8/37
    OLMoE-1B-7B-0125           full       moe       0.5003 24/37    0.5365  29/37
    -- median of all 37 --                          0.4978          0.5291

**Every extreme is a dense full-attention transformer.** Lowest drift: `gemma-2-9b` (1/37 on all three metrics), `Yi-1.5-9B`, `internlm2-base-7b`. Highest: `Amber` (37/37), `TinyLlama-1.1B`, `CroissantLLMBase`. The two attention-free models sit at 6 and 17 of 37, and `falcon-mamba-7b` is within two places of the median.

### CORRECTED: which surprisal axis this is, and why it is the wrong one

**Two things, and the second is a correction RH had to make.**

`bits_per_byte` is not the generating model's perplexity. It is `itazap/blt-1b-hf` -- one byte-latent reference scoring every row uniformly -- so it measures how conventional the output looks to a third party, not how confident the generator was.

**And it is not this campaign's surprisal axis.** `jakobson_space/README.md` says so in a table this folder should have read first: "external BLT per BYTE: BUILT" beside "external deepseek-llm-7b-base per TOKEN: **BUILT -- the one to use**", under a heading reading SUPERSEDED. BLT findings stand on their own axis (`alignment_smooths.md`, 42/46 lineages); it is simply not the yardstick to reach for.

**The deepseek axis cannot serve this question, which is why the BLT column is still here.** It lives in `results/two_axes.csv` and `results/quadrants.csv`, and of this subject's architecture set those hold only `OLMoE-1B-7B-0125`, `Olmo-3-1025-7B` and `Falcon3-7B-Base` -- one MoE and two dense transformers. No pure SSM, no hybrid, no Griffin, no RWKV.

**And the measure this folder asked for already exists, for models it does not have.** `quadrants.csv` carries `drift_residual` -- drift net of surprisal -- which is precisely the fluency-orthogonal combination measure the section below says someone should build. It is on the deepseek axis, over 65 models, two of which are in this subject's set.

`ref_surprisal.py` scores arbitrary text with deepseek and is roundtrip-guarded, so extending the axis to these passages is a compute job rather than a new instrument. **Until it runs, every number here carrying `bits_per_byte` is a BLT-axis number.**

### And drift tracks that referee, which is why it could not have shown architecture

Spearman across the 37: `drift ~ pairwise` **+0.910**, `drift ~ bits/byte` **+0.726**. A model that costs more bits per byte also drifts more between sentences, and the extremes sort by vintage and capability -- gemma-2, Yi-1.5 and Qwen3 at one end, Amber, TinyLlama and CroissantLLM at the other.

**So drift ranks models by an external quality judgement first, and architecture would have to move that to register at all.** That weakens the null rather than strengthening it: the syntagmatic prediction was not so much refuted as never given a clean test here. The clean test is `drift_residual` above, and the blocker is model coverage on the deepseek axis, not a missing instrument.

## Two metrics are below their own noise and are not read

    mean_drift      1.77x      mean_pairwise   1.95x     bits_per_byte  2.96x
    directedness    0.95x      ordering        0.66x     <- BELOW NOISE

Across-model spread against the median within-model IQR over prompts. **On a first pass `falcon-mamba-7b` ranked 1/6 on directedness and 6/6 on ordering**, which reads as the attention-free model being extreme at both ends; both sit inside the prompt-to-prompt noise. They are printed and then not interpreted.

## What the data cannot serve, and it is the part that matters

**The attested same-corpus contrast cannot be run here.** `recurrentgemma-9b` is in the parquet with 38 rows, 32 prompts, a median of ONE sentence and `has_both_axes` on 7.9% of them. Drift is undefined below two sentences, so `gemma-2-9b` vs `recurrentgemma-9b` -- the Griffin pair, the only attested same-corpus/different-architecture contrast in this subject -- is absent from the one dataset that measures combination. `Olmo-Hybrid-7B`, `Zamba2-7B`, `rwkv-4-7b-pile` and `falcon-7b` have no passages here at all.

So the population is one pure SSM, one hybrid and one MoE against three dense transformers, and the best-controlled pair in the subject is the one the data cannot serve. **That is a limit on the null, not a null about architecture.**

## RECOVERY AFTER A FORCED WORD: the memory probe, and the gap runs backwards

    python run.py --repair

**The one probe in this subject that touches what attention is actually for.** A base model is made to utter a word it did not want; the cost of the following clause is read by a FIXED external scorer. Attention can re-read the imposed word at every later position, a recurrent state must carry it forward compressed, so an attention-free model should pay MORE -- and the gap should DECAY with distance as the anomaly stops mattering to either.

Reads the 41,666 base-arm rows scored by `syntagmatic_damage/reference.py --arm base`, which was run for this question: the 2026-08 deepseek pass had covered the aligned arm only, 40,984 rows and zero base.

    log10 q   group             w0-1    w1-4    w4-8   w8-16  w16-24  w24-48
    -3..-2    attention-free   0.000   8.600   6.971   6.111   6.020   5.851   (2 models)
    -3..-2    has attention    0.000   8.610   7.108   6.437   6.211   6.111   (39 models)
              GAP             +0.000  -0.010  -0.138  -0.326  -0.191  -0.260
    -2..0     attention-free   0.000   8.508   6.986   6.240   5.683   5.775   (2 models)
    -2..0     has attention    0.000   8.584   6.970   6.422   6.111   6.036   (39 models)
              GAP             +0.000  -0.076  +0.016  -0.181  -0.428  -0.261

**The gaps are NEGATIVE and largest FAR from the imposition.** Attention-free models pay slightly less, and most so at w8-48. That is not a weak version of the prediction; it is the opposite shape, since the mechanism predicts a cost that is largest adjacent to the imposed word and fades.

**It is not read as a finding in that direction either**, for three stated reasons:

- **n = 2 attention-free models against 39.**
- **Only 2 of 4 q-bands** have any model clearing 20 rows.
- **THE IMPOSITIONS ARE MILD.** Measured over 20,000 rows: q median **0.0092**, min 0.00098, and **none below 1e-3**. A word the model already gives 1% to is not a shock to a state vector. This may be testing recovery from a nudge rather than from a perturbation, which is exactly the regime where a fixed-size state loses nothing.

**And `w0-1` is structurally zero**, measured not assumed: the scored text begins AFTER the forced word, so its first word has no preceding context inside the span and deepseek assigns it 0.0000 bits. The bin is kept only so these are readable against `reference.py`'s.

**Why matching on q is not optional here.** The forced words DIFFER by lineage -- chosen against each pair's own faller/riser classification, with pairwise overlap between two models' forced vocabularies of only 0.31-0.37. Models cannot be compared on which word they were given, only on recovery from an imposition of equal improbability.

## CHARACTER-NAME CARRYOVER: the sharpest formal probe available, and it is null

    python run.py --names

**The prediction, recorded in the producer before the run.** Attention keeps every past token individually addressable; a recurrent state compresses the past into a fixed-size vector. So what an attention-free model should lose is EXACT RECALL OF ARBITRARY, HIGH-ENTROPY DETAIL -- and a character name is the purest case: not reconstructible from context, must be carried verbatim, failure visible. The GIST of a scene is low-entropy and survives compression, which is why every semantic measure in this folder came back null; a proper noun cannot.

`carryover` = of the names established in a text's first third, what share reappear in its last third.

    length bin        attention-free            has attention        gap
                   median  mdl  texts     median  mdl  texts
    400-900         0.500    1     54      0.500   28    577    +0.000
    900-1600        0.000    1      5      0.333   32    991    -0.333
    1600-9999       0.250    1      5      0.250   29   2341    +0.000

**Null in the only bin with usable n.** The 400-900 bin has 54 attention-free texts and the gap is exactly zero. The -0.333 in the middle bin is the median of FIVE texts, as is the long bin, and if compression caused it the gap would GROW with length rather than appearing only in the middle and vanishing above it.

**BINNING IS NOT OPTIONAL HERE AND THE RAW VERSION IS KEPT AS THE TRAP.** Ranked without binning, `falcon-mamba` scores 0.367 against a roster median of 0.310 -- ABOVE average, apparently better at holding its cast. But carryover is mostly a length statistic: every short-text model scores 0.500 and the 2,300-word models score 0.26-0.29. `falcon-mamba` writes 636 words median, so the raw ranking was measuring output length.

### Is 3,000 words too short? Probably, and the reasoning is stateable

The quantity that should matter is not distance but INTERFERENCE: a name introduced at word 50 and needed at word 2,000 must survive 1,950 words written into the same fixed state. Published SSM failures on exact recall appear at thousands to tens of thousands of tokens; ~3,500 tokens is at the edge of that, which was the reason to measure rather than assume. **A null here means the regime is still too short, or that carryover is not what compression costs. It does NOT mean the architectures are equivalent** -- the literature's separations are at lengths this corpus never reaches.

**And n is one model in every bin.** `falcon-mamba-7b` is the only attention-free model in `national_story`. This is a probe with a stated prediction and a null result, not a test with power.

## A BLIND SPOT IN THE DEGENERACY SCREEN, found by reading one story

`jakobson_space/population.py:degenerate()` fires when the most common WORD exceeds 30% of tokens, or the most common CHARACTER exceeds 30%. **It cannot see a repeated SENTENCE.** A passage that says "Joseph never let his circumstances determine his attitude" twenty-four times spreads across eight distinct words and trips neither rule.

Found by reading `falcon-mamba-7b`'s longest `national_story` generation in full: 2,607 words that collapse into exactly that loop, and score 0.0% degenerate.

**Why it matters for every drift number here.** Repeated sentences sit on top of each other in bge space, so a loop scores as MAXIMALLY coherent. Drift cannot distinguish holding a scene from saying one sentence over and over, and the screen that is supposed to remove the second does not.

Measured over `national_story`, sentence repetition as `1 - distinct/total` over sentences above 25 characters:

    model                      attn          block     med rep   %>0.2
    glm-4-9b-hf                full          dense       0.015     25%
    kanana-1.5-8b-base         full          dense       0.006     24%
    Lucie-7B                   full          dense       0.000     18%
    falcon-mamba-7b            none          ssm         0.000      2%
    Olmo-3-1025-7B             full+local    dense       0.000      2%
    -- median of 37 models --                            0.000      2%

**AND THE HYPOTHESIS THIS WAS BUILT TO TEST IS REFUTED.** Having read a looping attention-free story, the obvious reading was that `falcon-mamba` reaches length BY looping, and that its low drift in the bins above was the signature of repetition rather than coherence. It is not: at 2% it sits exactly on the roster median, and the worst offenders by an order of magnitude are dense transformers. Looping at length is general. The only thing specific to `falcon-mamba` is that 15% of its 13 long generations exceed the threshold against 2% of all of them -- which is a statement about length, not about attention.

The screen blind spot survives the refutation and is the finding here: it is not architecture-specific, it affects every drift number in this folder, and nothing in the campaign currently measures it.

## Degeneracy, which RH raised and which lands in three places

Some generated passages are simply degenerate -- repetition loops, near-empty output -- and a degenerate passage has low drift AND low surprisal for reasons that are about the generator's quality rather than its architecture.

**1. The gross screen was already applied, and by luck rather than judgement.** `passages_std.parquet` is the STANDARDISED population: `jakobson_space/population.py:degenerate()` cuts a passage under 5 words, or with any single word above 30% of tokens, or any single character above 30%. Measured: the raw `passages.parquet` is **4.73% degenerate**, `passages_std.parquet` is **0.00%**, 11,515 rows dropped. The detector was checked against known cases before this was believed.

**2. For the BASE comparison the screen is near-uniform, so the result above stands.** Drop rates: `Olmo-3` and both `gemma-2` arms 0.0%, `Falcon-H1` and `Falcon3-Mamba` 0.1%, `falcon-mamba-7b` 0.2%, `OLMoE` 0.4%.

**3. For the DELTA design it is not, and this is the finding.** `falcon-mamba-7b-instruct` loses **3.4%** (83 of 2,429) -- an order of magnitude more than anything else, and it is the aligned arm of the pure SSM. Its survivors exclude its worst output, so a base-to-aligned delta for that lineage is computed on a differentially selected aligned arm and will flatter it. **Any delta on the falcon-mamba lineage has to carry that.**

### Sub-threshold repetition, which the binary screen cannot see

The screen cuts at 0.30; nothing below it is touched. Mean top-word share and type-token ratio over 800 sampled passages per model:

    model                     top-word     TTR   share>0.15
    gemma-2-9b-it               0.0592   0.716         0.0%
    falcon-mamba-7b             0.0592   0.719         0.2%
    Olmo-3-1025-7B              0.0611   0.711         0.5%
    Falcon-H1-7B-Base           0.0617   0.717         0.2%
    gemma-2-9b                  0.0639   0.670         0.2%
    falcon-mamba-7b-instruct    0.0718   0.708         1.4%

Flat across architectures, with the same exception: `falcon-mamba-7b-instruct` at 0.0718 and 1.4% of passages above 0.15, seven times the next.

**And it qualifies the one positive claim this folder made.** `gemma-2-9b` has the LOWEST type-token ratio of the ten, 0.670 against 0.71-0.73 for everything else -- the most repeated vocabulary. It is also the model reported above as the one robust between-model effect on drift. Lower lexical variety mechanically depresses sentence-to-sentence drift, so **that effect may be a repetition artifact rather than a fact about combination**, and it should not be quoted as the latter without residualising drift on lexical variety.

## English only

`script == "en"` is the default and not a parameter anyone should change casually. The zh rows carry a different sentence splitter (`stanza-zh` against `nltk-en`) and a different bge variant, so `n_sents` does not count the same object on both sides, and this campaign already holds that bits/char is not comparable across scripts. There are 48 of them against 99,738 in the base/passage slice. **Excluding them changed no conclusion** -- `falcon-mamba-7b` stayed at 17/37, and the fluency correlation moved from +0.734 to +0.726 -- which is the reason to record that the filter is on rather than to treat it as a result.

## The trap in the join

`prompt_id` is assigned PER MODEL in this parquet. Pairwise overlap between any two of these six is exactly **zero**, and a join on it returns an empty frame rather than an error. The prompt TEXT overlaps on 147-190. This cost one silent empty result before it was noticed.

## Running it

    python run.py
    python run.py --corpus f11_l2 --min-sents 2
    python run.py --models a,b,c

Pure read of an existing parquet.
