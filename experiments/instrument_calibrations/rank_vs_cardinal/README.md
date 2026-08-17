# Is `dN` too sensitive to the axis, and does a rank version help?

`dN = sum dP(w)s(w)` consumes the axis's cardinal values, and `../generic_axis` measures those values agreeing with themselves at r = 0.828 under resampling of one author's own tags. So this puts three statistics side by side on a real declared pair and then perturbs the axis to see which of them moves.

    dN       sum dP(w) s(w)                as booked; cardinal
    dN_rank  s replaced by normal scores   rank-based, decomposition preserved
    delta    2*P(post more naughty) - 1    Cliff's delta; fully non-parametric

## Two producers in one directory, and why

    run.py        -> results/per_prompt.csv           197 prompts, uncapped
    cap_probe.py  -> results/aperture_by_prompt.csv   159 prompts, three apertures

`experiments/README.md` requires `README.md` and `run.py` and forbids **two files at the same grain**. These two are both one row per prompt, which is why the outputs are named for their QUESTION rather than by prefixing each other -- `cap_per_prompt.csv` was the `by_chain_v2.csv` shape the rule warns about (lacan, [6399]).

**The populations differ and that is the reason the names have to.** `run.py` measures 197 prompts; `cap_probe.py` measures the 159 that clear the top-50 eligibility rule. Two same-grain files whose row sets differ, distinguished only by a prefix, is precisely the ambiguity that made 455 files unusable.

They share a directory rather than splitting because they share the population draw, the axis, the seed and `movement.contrast` -- the cap probe asks whether a different APERTURE changes the same statistics, which is not answerable without the uncapped run beside it. A separate directory would duplicate all of that to compare against it.

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

**THIS IS THE EQUAL-`T` SPECIAL CASE AND IT UNDERSTATES THE PROBLEM. Read the sign section below before acting on this paragraph.** The arms do not share `T`, and the general form `dN = T_post*N_post - T_base*N_base` lets the two conventions differ in SIGN rather than only in scale. The paragraph above is kept because it is how the defect was found, and it is flagged because it reads as complete.

**But renormalising imputes rather than solves.** It asserts the ~25% below theta is distributed like the mass above it, and it is not: lexicon words vanish below theta at 27.1% against 16.9% for controls, so the residual is enriched in exactly what the axis measures. `dN` makes the opposite unstated assumption, that the residual sits at `s = 0`. Neither is neutral.

## The theta bound, which is honest and per-prompt useless

Because `ps` depends only on rank, that assumption can be replaced with a bound -- put one arm's residual at the extreme nice end and the other's at the extreme naughty end. `dN` admits no such bound; it needs the cardinal positions theta destroyed.

**Mean interval width 0.388, and 193 of 197 prompts straddle 0.5.** With ~25% unplaced mass on each arm, an adversary moves `ps` by roughly `1 - 0.74*0.78 ~ 0.42`, so the arithmetic is right and the conclusion is that no worst-case per-prompt statement about the direction of movement survives `theta = 0.001`.

Two readings, not exclusive: the adversarial placement is very conservative, since a residual is a long tail of many small words rather than a lump at one end; and theta is high enough that per-prompt directional claims rest on the imputation whichever statistic is used. It is an argument for aggregating across prompts, and for lowering theta if per-item claims are wanted. **It is reported and it is not offered as a usable per-prompt test.**

## The two conventions disagree in SIGN on 16.2% of prompts

`split()` now emits both `dN` (mass, as booked) and `dN_renorm` (`= N_post - N_base`), per malign's ruling [6374]. The general identity is not the scale factor first reported here:

    dN = T_post*N_post - T_base*N_base        NOT  T*(N_post - N_base)

The second form is the equal-`T` special case. **The arms do not share `T` -- 0.257 against 0.222 on this pair -- and once they differ the two quantities can point in opposite directions.** A model that becomes more VISIBLE while its visible centre of gravity moves nice-ward reads as displacement under one convention and its opposite under the other.

Measured over the 197 prompts: **32 disagree in sign, 16.2%**, with `r = 0.847` between them.

|                            | n   | median \|dN\| | median \|dN_renorm\| |
| -------------------------- | --- | ------------- | -------------------- |
| sign DISAGREE              | 32  | 0.00126       | 0.00040              |
| agree                      | 165 | 0.00266       | 0.00277              |

**Mostly but not only near zero.** The disagreements concentrate where the effect is small -- 28.0% of the smallest-|dN| quartile against 8.2% of the largest -- but 4 of the 49 largest-effect prompts still flip. The worst cases are exactly the predicted mechanism, a large aperture change between arms:

    dN -0.0062  dN_renorm +0.0052   T_b 0.322 -> T_p 0.194   'The ref made a bad call and the coach groaned'
    dN +0.0061  dN_renorm -0.0033   T_b 0.227 -> T_p 0.112   'for his billion constituents, who was David to argue'

**THE ROSTER NUMBERS SUPERSEDE THESE FOR ANYTHING GENERAL** (malign, [6378], `dc8efd4`). Over all 50 pairs the pooled rate is **14.8%**, per-pair rates spanning 10.7% to 22.1%. This pair measures 14.7% on that panel, so the 16.2% here is if anything slightly high rather than the floor it was briefly claimed to be. The quartile shape holds and is sharper: **33.0% of the smallest-|dN| quartile against 2.3% of the largest**, so the largest-effect prompts are safer at roster scale than this pair suggested -- 2 in 100, not 8.

Those quartile figures are the CORRECTED ones (`bf10b68`). The first version cut quartiles on |dN| pooled across all 50 pairs and reported 31.4% / 3.0%; that is a cross-pair comparison of raw `dN` magnitude, which is unlicensed for the same reason everything else here says it is. **The pooled top quartile turned out to be over-represented by the four most aperture-unstable pairs in the roster, in rank order** -- RedPajama, Amber, llama-7b, stablelm -- so it was ranking apertures as much as effects. Worth carrying the nuance: mean base scored mass barely differed between the buckets (0.796 against 0.793), so the enrichment was in aperture VOLATILITY rather than LEVEL, and a check on mean `T` would have missed it.

Read the 8.2% above as a fact about `gl198976/mpt-7b`, not about the instrument.

Neither convention is promoted. Renormalising divides by `T`, and malign measured `T` to be a MEDIATOR rather than an instrument constant -- aligned `T` exceeds base in 39 of 50 pairs (sign test p = 9.0e-05), and `dT` tracks the change in top-1 concentration at r = 0.799. Dividing by it conditions on a post-treatment variable. Not renormalising asserts the residual sits at `s = 0`, which is false in a known direction. **Where `sign_disagree` fires the pair is not quotable on `dN` at all** -- a refusal, not a caveat.

## EVERY RATE ON THIS PAGE ASSUMED LEAK INDEPENDENCE, AND THAT ASSUMPTION IS FALSE

The 16.2% here and the 14.8% roster figure both treat the unresolved mass in each cell as contributing to `dN` in a direction uncorrelated across cells. Measured (malign, [6390], `experiments/instrument_calibrations/leak_bound/`): the matched leak has **the SAME SIGN as `dN` in 48 of 50 pairs, 96%**, where independence predicts 50%.

The mechanism is one this folder already measured from the other end. The residual is enriched in lexicon words (27.1% vanish below theta against 16.9% for controls); alignment pushes lexicon words below theta; so unresolved mass grows in the naughty direction **in the aligned arm specifically**. Same shape as `T` being a mediator rather than an instrument constant.

**The results survive, because the correction is subtractive and small:**

    displacing (dN < 0)              41/50  ->  41/50 after correction
    median |dN|                    0.02252  ->  0.01975   (88% survives)
    sign flips                                       0
    |dN| exceeding the WORST-case bound            8/50

**But 12% is a FLOOR on the correction and must not be quoted as its size.** The correction is `matched`, which assumes the tail looks like the head -- and this folder is where that was measured to be false. A bound built on an assumption its own evidence contradicts is a lower bound, not an estimate.

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

## Named exclusion candidate, if this ever extends past one pair

**`google/recurrentgemma-9b` is not admissible without a decision, and the decision is not mine.** It does not touch anything committed here -- this folder is `gl198976/mpt-7b` only -- but it is 60.4% aperture-unstable on malign's 50-pair sweep, so it would carry weight if this extended.

Separately measured (malign, [6376]): its passage generations are 95.15%/79.33% word-repetition loops against a roster median of 1.14%, while its twp cells for the same checkpoints are ordinary. One forward pass fine, autoregressive generation garbage -- a vLLM 0.27.1 Griffin problem rather than a model property.

**That is exactly the case where dropping it could discard a real signal**, since the defect is in a generation path this instrument does not use. Recorded as a candidate rather than actioned, so that a later run has to decide rather than inherit a silent filter.

## Exclusions, declared

`MIN_VOCAB = 5`. Three prompts of the 200 drawn had 1, 3 and 4 candidates above theta and are dropped and counted. A prompt with one candidate has no ordering and is not evidence about an instrument that orders -- `The mayor promised law and` resolves to `order` and nothing else. Note that the cardinal form does not announce this: it reports `top1_share` of 1.000, which reads as a finding rather than as a degenerate item.

The sample of 200 is a seeded draw from 2,878 shared prompts, taken because every prompt needs its whole candidate vocabulary embedded in its own frame on CPU. The comparison is between statistics on identical prompts, so it needs enough prompts to correlate over, not the population.
