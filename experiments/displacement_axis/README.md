# displacement_axis

dN and its decomposition, per (lineage, item), with the words that carried it.

    python experiments/displacement_axis/run.py

Reads `twp_words_v4` / `twp_cells_v4` and imports `slot_axis.Axis`. Runs no
checkpoint and needs no server.

## The pilot population: 8 of 50 declared pairs

Pairs come from `roster.endpoints()`, never from the model names in the store.
As of 2026-08-18, 20 models hold slot-corpus prompts in v4 and 8 of them form a
declared base -> endpoint pair with both arms present:

    Qwen/Qwen2.5-0.5B                 -> Qwen/Qwen2.5-0.5B-Instruct
    Qwen/Qwen2.5-7B                   -> Qwen/Qwen2.5-7B-Instruct
    Qwen/Qwen3-8B-Base                -> Qwen/Qwen3-8B
    baichuan-inc/Baichuan2-7B-Base    -> baichuan-inc/Baichuan2-7B-Chat
    google/gemma-2-9b                 -> google/gemma-2-9b-it
    llm-jp/llm-jp-3-7.2b              -> llm-jp/llm-jp-3-7.2b-instruct3
    m-a-p/CT-LLM-Base                 -> m-a-p/CT-LLM-SFT-DPO
    m-a-p/neo_7b                      -> m-a-p/neo_7b_instruct_v0.1

**This is not a sample of the roster and should not be read as one.** It is
whichever pairs a local pass happened to reach first, and it is heavily skewed:
six of eight are China-origin lineages (Qwen x3, Baichuan, CT-LLM, neo), one
Japanese, one US. Any cross-lineage claim from this pilot is a claim about that
skew as much as about alignment.

Four more models hold the prompts and cannot pair:

    deepseek-ai/DeepSeek-R1-Distill-Qwen-7B   not in endpoints() at all
    m-a-p/CT-LLM-SFT                          not in endpoints() at all
    m-a-p/neo_7b_sft_v0.1                     not in endpoints() at all
    internlm/internlm2-base-7b                base whose endpoint is unmeasured

The two SFT arms are the interesting exclusion. `endpoints()` maps one base to
exactly ONE endpoint, so `CT-LLM-Base -> SFT` and `CT-LLM-Base -> SFT-DPO` are
two STAGES of one lineage rather than two lineages. An earlier draft paired them
by hand and produced "ten lineages" of which two were stage comparisons wearing
lineage clothes. If the SFT stage is wanted it is a separate question with its
own design, not an extra row here.

`DeepSeek-R1-Distill` is also worth keeping out on its own merits: it is a
reasoning distillation and returns both poles on only 64% of items against
88-99% for every other model in the store, because its distribution at a
mid-sentence slot is shaped by thinking-trace behaviour rather than direct
continuation.

## What each row carries, and why it is three measurements not one

**Alignment does more than one thing at once, and the columns keep them apart**
(RH, 2026-08-18).

    dT              T_aligned - T_base      how much the distribution CONCENTRATED
    dN_position     N_aligned - N_base      WHERE the mass sits on the axis
    dN, dN_renorm                           the combined conventions, kept for comparison
    signature                               displacement / suppression / arrival / churn / flat

`dN` is `T_post*N_post - T_base*N_base`, so it multiplies concentration by
position and a cell can read as displacement or its opposite depending on which
convention is used. Measured here: aligned scored mass exceeds base in 79% of
cells, median dT +0.0442, and the two conventions disagree in sign on 5%.

The standing objection to renormalising is that T is post-treatment. That is
correct and is not a reason to avoid it: concentration is an EFFECT to report,
not a nuisance to divide away, and asking where a distribution concentrates
requires normalising out how much it concentrated. So both are reported and
neither is derived from the other.

## Read `signature` before `dN`

The two components of `split` have signs that separate cases dN conflates.
Verified on synthetic distributions, moving known mass:

    kill 0.05->0.01, scream 0.05->0.09   dN -0.0170  supp -0.0087  subs -0.0083
    kill 0.05->0.01, nothing else        dN -0.0087  supp -0.0087  subs  0
    scream 0.05->0.09, nothing else      dN -0.0083  supp  0       subs -0.0083
    scream -> cry, INSIDE the nice pole  dN -0.0001  supp +0.0083  subs -0.0084

**Displacement puts both negative. Churn within one pole puts them opposite.**
A three-item probe found churn on the item whose dN looked strongest.

## The leak columns are recorded and DO NOT bind

`leak_worst = (residual_base + residual_endpoint) * max|s|` assumes the entire
unreturned mass sits at the axis extreme. The residual is ~0.21 of the
distribution spread over words each below theta=0.001, so it contains a MINIMUM
of ~206 distinct words; the bound requires all of them to sit at one extreme in
the same direction. That is an arithmetic ceiling with no physical reading, and
it is roughly 16x `leak_matched_floor`. Scored words are near-symmetric about
zero (mean -0.0037, sd 0.107), so a tail distributed like the body contributes
about -0.0008.

Reported because the bound must travel with the number (`_leak`'s own reasoning:
a `None` field is a passive guard). NOT used as a filter. `leak_matched_floor`
is the operative figure.

## Known gap: the arms are scored on DIFFERENT word sets

`N_base` averages over the words base returned, `N_aligned` over the words
aligned returned, and those sets share a median Jaccard of only **0.575**. Base
returns ~35 words aligned does not; aligned returns ~11 base does not. A median
**7.5%** of base mass sits on words aligned never surfaced, against **1.8%** the
other way -- asymmetric, and in the direction that inflates apparent
displacement.

So `dN_position` currently conflates movement along the axis with the two arms
having different supports. The fix is `twp_v4.score_words_paths` over the UNION
of both arms' vocabularies, which is fleet work rather than a query and has not
been run. `dT` should NOT move to the union: concentration is about each model's
own aperture, and fixing the word set would turn it into a different quantity.

## Outputs

    results/cells.jsonl    one row per (base, endpoint, item_id)
    results/words.jsonl    one row per word, with p_base, p_aligned, dP, s,
                           contribution -- contributions sum to dN EXACTLY, so a
                           cell resting on one word is visible rather than inferred
    results/skipped.jsonl  every pair, item or cell not measured, with the reason
