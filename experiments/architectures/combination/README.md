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
