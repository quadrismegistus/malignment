# displacement_reference

**How far training moves a model, per phase, per token.** Not a hypothesis;
nothing here can fail.

    run.py             # OLMo phase profile, twp
    run.py --curve     # 83 consecutive-rung intervals (plottable)
    run.py --fullvocab # 84 intervals at 100,278 vocab, from the archive .f16 tier
    plot.py            # -> figures/mass_movement_speed.png

## What was learned

**twp is accurate on pretraining and inflates post-training by ~50%.**

    stage1 x1.05   stage2 x1.08   stage3 x0.96   |   base->SFT x0.65   SFT x0.64

A clean split at the phase boundary, and the direction is the opposite of what
was predicted. Alignment concentrates its changes on exactly the high-probability
words twp keeps, so truncating to them AMPLIFIES it; the untouched tail dilutes
it at full vocabulary. Pretraining moves the whole distribution, so truncation
costs it nothing. **Any twp-derived post-training MAGNITUDE is overstated by
about a third.** Ratios computed within twp on both arms — `excess_C`, the pole
projections — are unaffected.

**Tokens, not steps, and the batch sizes derive exactly.**

    stage1  1,413,814 steps  5.93T  ->  2^22     stage2  47,684  100B -> 2^21 (HALF)
    stage3     11,921 steps   50B   ->  2^22     SFT     43,000 rungs -> 2^20

The first three divide the card's stated tokens by our own measured ladder and
land on powers of two, reconstructing 6.080T against the card's 6.080T. The
fourth is STATED: `--global_batch_size=1048576` in allenai/open-instruct
`scripts/train/olmo3/7b_think_sft.sh`, whose base checkpoint path ends
`/step11921/` — the exact rung this ladder ends on.

**The init transient is 3.3x.** `stage1-step0 -> step1000` is 0.8644 against
0.2652 for the next interval, so early rungs are a network leaving random
initialisation, not training efficiency. Any comparison that puts stage 1's
early rungs against SFT's early rungs is comparing init noise to fine-tuning.

**And no magnitude statistic separates alignment from pretraining** — JS total,
JS fall/rise, directional KL smoothed, directional KL with the tail as reserve
mass, at truncated and at full vocabulary. Five attempts, all flat. JS per token
measures the OPTIMISER, not the intervention: same loss, same parameters,
different text. The measures that do separate are anchored to a declared
vocabulary, and they work because a subset can lose mass to the rest of the
vocabulary while a full-vocabulary divergence is forced to balance.

## The comparator that was abandoned

Between two independently pretrained models. RH: *"why would we expect alignment
to have a stronger effect than all the many differences between separately
pretrained models?"* We would not — and the same number got read as "alignment is
modest" and "alignment is startling" in consecutive messages, which is the
signature of a statistic anchored to nothing. Kept at
`_superseded_between_bases.md`, because its `difference_in_differences` centres
at zero and that validates the `neither` reference vocabulary as MATCHED to the
lexicon — an assumption `removal_rates`' `excess_C` rests on that had never been
checked.

## Custody

`--fullvocab` reads the archive's parked `.f16` tier IN PLACE via the
`logit_row`/`logit_dim` pointers in each dump's own `.jsonl`. **Nothing is
ingested, `logit_dir_resolution.json` is untouched, the tier stays parked per
docket [5886].** CH's `logit_probs` is not the route: it is itself top-k
truncated (~6.6k of 100,278) and would reintroduce the very truncation being
measured. Four refusals guard the memmap join — absent volume, differing prompt
order between rungs, varying `logit_dim`, and `filesize != rows x dim x 2`.
