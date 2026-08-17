# Is `dN` too sensitive to the axis, and does a rank version help?

`dN = sum dP(w)s(w)` consumes the axis's cardinal values, and `../generic_axis` measures those values agreeing with themselves at r = 0.828 under resampling of one author's own tags. So this puts three statistics side by side on a real declared pair and then perturbs the axis to see which of them moves.

    dN       sum dP(w) s(w)                as booked; cardinal
    dN_rank  s replaced by normal scores   rank-based, decomposition preserved
    delta    2*P(post more naughty) - 1    Cliff's delta; fully non-parametric

All three live in `malignment.slot_axis`; their invariances are asserted by `python -m malignment.slot_axis`, not claimed here. Run: `python run.py`. Pair `gl198976/mpt-7b -> gl198976/mpt-7b-instruct`, 197 of a 200-prompt sample from 2,878 shared `CDH0050` prompts, pooled 12-pair lexical axis.

## The answer, and it is not the one the question expects

**The pole set matters far more than the statistic.** Going from a pooled 12-pair axis to a single-pair axis drops every statistic from ~0.99 to ~0.62, and it does so to all three about equally. Whichever statistic you pick, the axis is where the variance is.

| | LOO (mild: 11 of 12 pairs) | | SINGLE (strong: one pair) | | |
| --- | --- | --- | --- | --- | --- |
| | rho mean | sign agree | rho mean | **rho min** | sign agree |
| `dN` | 0.992 | 0.962 | 0.615 | **-0.026** | 0.708 |
| `dN_rank` | 0.992 | 0.963 | 0.650 | **0.240** | 0.758 |
| `delta` | 0.976 | 0.962 | 0.612 | **0.213** | 0.751 |

**The rank forms do not improve the typical case. They improve the worst case.** On mean rank correlation the three are within 0.04 of each other. The separation is in `rho min`: under its worst single-pair axis `dN` loses essentially all ordering information (-0.026), while the rank forms retain 0.21-0.24. Directional agreement follows the same pattern, 0.708 against 0.75-0.76.

So the honest summary is: *if your axis is pooled, the statistic barely matters; the rank forms are insurance against a bad axis, not an upgrade on a good one.*

## The perturbation had to be run at two sizes, and the first size was useless

The first version of this experiment used leave-one-out alone and reported all three between 0.974 and 0.992. That is a result about the perturbation. Dropping one pair from a twelve-pair pool barely moves the pooled direction, so nothing could have separated -- the same defect as judging a guard vacuous on a subsample too small to discriminate. Both families are kept and reported, because the gap between them is itself informative about how much pooling buys.

## What the rank form does NOT fix

**Concentration is identical: 0.225 cardinal, 0.222 rank.** One word carries about 22% of the total absolute contribution either way. That is not a defect of the transform, it is where the concentration comes from: `dP` is untouched by re-scoring `s`, and mass movement is the phenomenon rather than an artefact of it. Nothing rank-based can remove sensitivity to `p` magnitude without removing the thing being measured.

## Two defects in `dN` found while running this

**`dN` is not `N_post - N_base`.** `stats()` divides by the scored mass and `split()` does not, so where both arms share a scored mass `T` the identity is `dN = T * (N_post - N_base)`, verified at 0.017098 / 0.028029 = 0.610. `T = 1 - residual` runs from 0.712 to 0.929 across the nine checkpoints with `CDH0050` records, so **`dN` carries a hidden per-model scale factor varying by 1.31x**, and two `dN` values from different pairs are not on one scale. `ps` and `N` both renormalise and are immune.

**But renormalising imputes rather than solves.** It asserts the ~25% below theta is distributed like the mass above it, and it is not: lexicon words vanish below theta at 27.1% against 16.9% for controls, so the residual is enriched in exactly what the axis measures. `dN` makes the opposite unstated assumption, that the residual sits at `s = 0`. Neither is neutral.

## The theta bound, which is honest and per-prompt useless

Because `ps` depends only on rank, that assumption can be replaced with a bound -- put one arm's residual at the extreme nice end and the other's at the extreme naughty end. `dN` admits no such bound; it needs the cardinal positions theta destroyed.

**Mean interval width 0.388, and 193 of 197 prompts straddle 0.5.** With ~25% unplaced mass on each arm, an adversary moves `ps` by roughly `1 - 0.74*0.78 ~ 0.42`, so the arithmetic is right and the conclusion is that no worst-case per-prompt statement about the direction of movement survives `theta = 0.001`.

Two readings, not exclusive: the adversarial placement is very conservative, since a residual is a long tail of many small words rather than a lump at one end; and theta is high enough that per-prompt directional claims rest on the imputation whichever statistic is used. It is an argument for aggregating across prompts, and for lowering theta if per-item claims are wanted. **It is reported and it is not offered as a usable per-prompt test.**

## The top-N rank cap, tested (`cap_probe.py`)

RH's proposal: take the top 50 words from each arm, and refuse the comparison where an arm has fewer than 50 candidates. Measured over the same sample, 159 eligible of 200 drawn.

| regime | words | mass base | mass post | aperture gap | one-arm-only |
| --- | --- | --- | --- | --- | --- |
| `UNION` (theta, as now)          | 153.8 | 0.729 | 0.771 | **+0.0414** | 49.5 |
| `CAP_UNION` (top-50 each arm)    | 59.4  | 0.642 | 0.702 | **+0.0596** | 4.1 |
| `CAP_INTER` (top-50 in both)     | 49.8  | 0.622 | 0.683 | **+0.0609** | 0.0 |

**It fixes set membership and worsens mass.** One-arm-only words fall from 49.5 per prompt to 4.1 -- a real gain, that being the asymmetry that biases `dN`. But the mass aperture gap grows ~44%.

The reason is that **theta was partially self-correcting and a rank cap removes the correction**. A probability floor gives a FLAT distribution more words, which claws back some of what a peaked distribution keeps for free. A fixed rank gives both the same count, so the peakier arm -- the aligned one -- simply keeps more mass: top-50 captures 0.702 of post against 0.642 of base. Equalising rank de-equalises mass, and mass is what every statistic here weights by.

**The eligibility rule should not be adopted.** The 41 refused prompts have mean base residual 0.186 against 0.271 for the eligible: it discards the peaked, confident prompts the instrument measures best and keeps the diffuse ones. A filter whose bias runs along the same axis as the treatment cannot be applied silently, and this one runs the wrong way.

**And none of it matters much.** Capped statistics correlate with uncapped at 0.96-0.99, sign agreement 0.87-0.94. The aperture question moves the answer far less than the pole set does. What the cap's one genuine win is really arguing for is UNION RESCORING at production time -- score each arm on the other arm's words -- which removes one-arm-only words without touching the mass aperture and without a selection rule.

**What this probe cannot test:** a real v4 would expand BY RANK and so reach words theta never entered. Those were never measured and no downstream analysis can invent them. Applying a cap to existing records tests the aperture half of the proposal, not the depth half.

## Exclusions, declared

`MIN_VOCAB = 5`. Three prompts of the 200 drawn had 1, 3 and 4 candidates above theta and are dropped and counted. A prompt with one candidate has no ordering and is not evidence about an instrument that orders -- `The mayor promised law and` resolves to `order` and nothing else. Note that the cardinal form does not announce this: it reports `top1_share` of 1.000, which reads as a finding rather than as a degenerate item.

The sample of 200 is a seeded draw from 2,878 shared prompts, taken because every prompt needs its whole candidate vocabulary embedded in its own frame on CPU. The comparison is between statistics on identical prompts, so it needs enough prompts to correlate over, not the population.
