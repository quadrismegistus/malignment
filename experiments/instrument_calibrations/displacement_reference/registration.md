# Registration — displacement_reference

**INSTRUMENT REGISTRATION. It declares how a reference is BUILT, not what will be found.**

**DRAFT, NOT FROZEN. Awaiting RH's read.**

---

## 0. What is being tested: NOTHING. What can be wrong: the construction.

This produces a **scale**, not a result. No hypothesis, no direction, no decision rule, because no outcome could contradict it. A reference cannot be false; it can only be **built wrongly**, and this file exists so the building is arguable.

The question: **when we say alignment displaces a model by JS 0.10, is that a lot?** The answer requires a comparator, and choosing one is the entire design.

## 1. THE COMPARATOR THAT WAS ABANDONED, AND WHY — read this first

The first version compared alignment against **the distance between two independently pretrained models**. RH: *"why would we expect alignment to have a stronger effect than all the many differences between separately pretrained models?"*

We would not. Two models differing in corpus, tokenizer, architecture and scale should differ enormously; a light post-training pass on a fixed base reaching 82% of that gap is **alignment doing a startling amount**, not alignment being modest. I read the same number in both directions across two messages, which is the signature of a statistic anchored to nothing.

**A reference means something only if it is a comparison someone would have made anyway.** Nobody was ever going to ask whether alignment exceeds the Llama–Qwen gap. That version is kept at `_superseded_between_bases.md` with its results, because the base↔base table still does one real job — §5 below.

## 2. The comparator that survives: the model's own training history

Same lab, same weights, same tokenizer, same prompts. **OLMo 3 is the only family in the roster that admits it**, because it released ladders on *both* sides.

**Pythia does not**, and this was checked rather than assumed: 154 pretraining rungs, **zero** measured post-training rungs, and one aligned edge (`lomahony/eleuther-pythia6.9b-hh-sft`) which is a third-party HH finetune rather than the lab's own pipeline. It can offer an endpoint against a ladder — the mismatch this producer exists to avoid.

## 3. The population, and the prompt tier

**The OLMo checkpoints do NOT share a prompt set.** Across all 104, the universal intersection is **one** prompt; the base ladder alone spans 3, 1,199, 2,272 and 4,428 prompts, because prompt sets are fleet-defined and do not nest. Assuming otherwise was the last error here.

**The 2,272 tier is where both ladders live and it crosses fully:** 41 pretraining rungs, 43 SFT rungs, 2,272 prompts held by every one of them. That is the declared panel and no sampling is applied.

## 4. TOKENS, NOT STEPS — what is stated and what is derived

**STATED**, https://huggingface.co/allenai/Olmo-3-1025-7B: "5.93T tokens" (stage 1), "100B tokens" (stage 2), "50B tokens" (stage 3), and the naming convention `stage1-stepXXX` / `stage2-stepXXX` / `stage3-stepXXX`. Batch size, sequence length and steps per stage are **not stated**.

**DERIVED**, by dividing the stated tokens by the final step of our own measured ladder:

    stage1  1,413,814 steps  5.93T  ->  4,194,328/step   2^22 = 4,194,304
    stage2     47,684 steps   100B  ->  2,097,140/step   2^21 = 2,097,152
    stage3     11,921 steps    50B  ->  4,194,279/step   2^22 = 4,194,304
                                   reconstructed 6.080T vs card 6.080T

Three independent divisions each landing on a power of two to five significant figures is the batch size revealing itself, not a fit. **The 24-token gap on stage 1 is the card's rounding** — 1,413,814 × 2²² = 5.93003T — and is recorded so it is not later read as a discrepancy.

**Midtraining runs at HALF the batch of the stages either side of it.** Invisible in step counts, and it would silently corrupt any per-step comparison across stages.

**`SFT_TOKENS_PER_STEP` IS NOT SOURCED and is `None`.** While it is None the SFT rows carry JS and steps and **no per-token figure**. An unsourced denominator is worse than a missing column, because a missing column is visibly missing.

## 5. What the superseded base↔base table is still for

Its `difference_in_differences` centres at zero (median +0.0000, IQR −0.113..+0.097), which says the 3,812-word `neither` reference vocabulary is **matched** to the 1,063-word lexicon — two unrelated models do not diverge more on one than the other. That is the assumption every excess-over-neutral statistic in this project rests on, `removal_rates`' `excess_C` included, and it had never been checked. Kept for that alone.

## 6. IT EMITS A PROFILE, NOT A RATIO

Both phases are front-loaded, and unequally. **So "alignment is N times pretraining" has no single value** — 1.39× against the late stretch of pretraining, 0.31× against the full released ladder. A producer emitting one number would be choosing the answer by choosing the denominator, which is the class of derived value this repository keeps having to withdraw. A reader picks their own stretch and can see what it rests on.

## 7. Declared limits

- **Released rungs are not training boundaries.** `stage1-step1413814` is the last *released* rung, not provably the last *trained* step. The card's "97.53%+ of total pretraining budget" corroborates it (5.93/6.08 = 97.5%) but does not prove it.
- **The SFT ladder starts at step1000**, so `base → SFT@step1000` is outside it and must be measured separately. It is 12.7% of SFT's total.
- **A phase boundary is not a terminus, and this cost a wrong number.** An earlier run measured the SFT jump from `stage2-step47684` — but **stage 3 comes after stage 2**, so that was a midtraining rung, not the final base. It gave 43%; from `stage3-step11921` the figure is **12.7%**. Every ratio quoted before that correction was wrong.
- **n = 1 family.** Nothing here generalises past OLMo 3 7B, and the roster contains no second family that could test whether it does.
