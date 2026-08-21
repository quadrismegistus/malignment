---
status: draft
date: 2026-08-20
role: finding
seat: lacan
topics: [surprisal, alignment, blt, cross-lingual, F15]
producers: [build_population.py, population.py, smoothing.py]
description: "Alignment lowers BLT bits-per-byte and compresses its spread: 42 of 46 contrasts, p=5.1e-09, on a fixed byte-level scorer across 94 models and two scripts. Survives degeneracy, script and fluency controls, each of which SHARPENS it. One model is the exception -- Llama-3.1-8B-Instruct is the highest-surprisal aligned model of 45. No human anchor yet, so the claim is model-relative."
---
# Alignment smooths, and compresses

**Aligned models produce lower-surprisal text than their base models, and cluster more tightly while doing it.**

    42 of 46 contrasts lower | median -0.2274 bits/byte | sign test p=5.1e-09

The unit is the ALIGNED MODEL -- each has exactly one base, so one contrast each, and a base with several aligned children contributes several rather than being collapsed. Population: `$MALIGNMENT_DATA/jakobson_space/passages.parquet` under `population.standard()`.

## Why this is not F15 again

F15 (2026-05-17, grade C, unaudited) reported the same direction on 10 families with Pythia-1B-deduped as reference. Four things differ:

- **47 contrasts, not 10 families**, over 94 models and 76 lineages.
- **A byte-level scorer.** `itazap/blt-1b-hf` gives bits per BYTE, so one scale spans 94 models with different tokenizers and both scripts. No roster model can score another family's `token_ids` without re-tokenising, which is why cross-scoring in `gen_scores` only ever worked within a lineage.
- **Chinese, which F15 never touched**, and which only a byte-level scale makes legitimate.
- **Controls F15 did not run**: degeneracy, script purity, and blind fluency grade.

## The controls SHARPEN it, which is the point

    all                              39/47 lower | -0.2146 | p=5.5e-06
    non-degenerate                   40/46       | -0.2154 | p=3.1e-07
    non-degenerate + single-script   42/46       | -0.2310 | p=5.1e-09
    STANDARD (population.standard)   42/46       | -0.2274 | p=5.1e-09

Degeneracy contaminates `bits_per_byte` in BOTH directions -- a repetition loop is trivially predictable and reads as maximal smoothing, token salad reads as maximal roughening -- so it had to be removed before the number meant anything. It was, and the effect grew. **The confounds were dampening the result, not creating it.**

## The distributional form is the stronger statement

    base models     n=45   median 1.389   IQR 1.329-1.467
    aligned models  n=45   median 1.135   IQR 1.044-1.255

English, standard population. **Alignment lowers surprisal AND compresses its spread**: aligned models converge on a narrower band where base models scatter. The 0.25 gap between medians is the same effect as the -0.23 contrast median, arriving as two distributions instead of 46 paired differences.

## Chinese

    zh, all                          27/29 lower | -0.2992 | p=1.6e-06
    zh, non-degenerate + pure        26/28       | -0.3408 | p=3e-06
    zh, BOTH arms Chinese-fluent      5/5        | -0.2032 | p=0.062

**The last line is unanimous and its p is a FLOOR**: a two-sided sign test with 5 of 5 agreeing gives exactly 2/2^5 = 0.0625 and can go no lower. Quote the count.

Both arms must be fluent because otherwise the contrast measures CAPABILITY. `bloomz` loses Chinese entirely (25% fluent -> 0%) and `MiniCPM5` gains it (0% -> 45%); either would read as a register effect. Five lineages qualify at a 20% threshold.

## It survives conditioning on fluency, which is what licenses reading it as register

Blind Opus judges, kappa 0.776, from `zh_fluency_and_ordering.md`:

    verdict          n   base b/B   aligned b/B      diff         p
    fluent         120     1.9836        1.7933   -0.1902     0.036
    flawed         348     2.2713        1.7952   -0.4760   1.1e-11
    broken         275     2.3005        2.1175   -0.1830   2.4e-05
    not_chinese    128     1.4502        1.3110   -0.1392     0.16

Aligned is lower even among passages a blind judge called **equally fluent**. Since alignment independently improves fluency (20 pairs to 5), quality and register were not separable a priori; conditioning separates them. **These p-values pool passages across models and are therefore optimistic** -- the direction holding in every grade is the robust part.

## THE EXCEPTION, and it is one model

    Llama-3.1-8B            base    1.351   rank 17 of 45   (36th pct)  ORDINARY
    Llama-3.1-8B-Instruct   aligned 1.854   rank 45 of 45  (100th pct)  THE HIGHEST

Llama-3.1-8B-Instruct is more surprising than **every base model** except CroissantLLM, CT-LLM and Teuken. Its base is unremarkable, so this is not a degenerate base making an ordinary aligned model look rough: it is **an aligned model that failed to smooth**, by 0.6 above the top of its own arm's IQR.

Three other contrasts are positive and none is substantial: `phi-4-reasoning` +0.096 (n=231, 5 shared prompts), `internlm2-chat-7b` +0.093, `SmolLM2-360M-Instruct` +0.007.

## Fences

- **NO HUMAN ANCHOR IN THIS DOCUMENT, AND THE FENCE IS NOW DISCHARGED ELSEWHERE.** This is a claim about model output relative to other model output. "Aligned prose is smoother than base prose" is established; "smoother than human writing" is not askable *here*. The anchor was built 2026-08-21 and placed -- 3,000 passages, six corpora, on a per-TOKEN deepseek axis -- see `README.md`. **That answer does not transfer to the numbers in this file**: different scorer (deepseek tokens, not BLT bytes), different population (narrative-coded only), English only. Every BLT level below remains model-relative.
- **Degeneracy filtering cannot reach incoherence.** The rules catch repetition, near-empty output and script mixing. They do not catch single-script non-repetitive incoherence, which the judges called broken in 71% of Chinese continuations that the rules clear at 99.5%.
- **10.5% of the corpus has no sentence vector** -- the `mixed` script stratum that `--mixed-policy refuse` declined. Not missing at random: these are the breakdown passages, and f11_l2 loses 16% of itself.
- **The within-fluency-grade p-values pool passages across models.**
- **The zh both-arms-fluent test is n=5** and its p sits on the floor.
- **`bits_per_byte` is not comparable across scripts**: zh runs 1.63x en (2.12 vs 1.30). Within-script contrasts are safe; pooled cross-script levels are not.
- Single pass, one seat, not second-seated.
