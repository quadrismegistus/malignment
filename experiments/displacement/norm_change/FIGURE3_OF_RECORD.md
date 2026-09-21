# Which Figure 3 the article prints

RH's decision, relayed through the paper seat (`TheoryMachines`), 21 Sep 2026. Recorded here because it is a choice about which of four correct artifacts gets cited, and nothing in the code says so on its own.

## The scatter stays, and nothing further is built for the article

`figures/dose_vs_marginal_gated_both_bh05_pub.png` remains the article's Figure 3. The two Osgood plates and the fitted diagnostic go to the book, where the tie-rate problem can have the paragraph it needs.

**What decided it:** the row plate's whole purpose was cross-row comparability, and ties remove exactly that. On tie-heavy rows a median of per-lineage medians recovers about a **seventh** of the movement an OLS fit on the same rows finds — 21 of 50 lineages sit exactly on zero for `v6:vocalisation` — so a row with few ties is drawn near its true size and a tie-heavy row near zero. The plate's visual ordering is therefore partly an ordering of tie rates, which is not a thing a caption can repair.

## Built, committed, and NOT the article's figure

| artifact | what it is |
|---|---|
| `fig3_norms_osgood_en.*` | band medians, native poles, most negative at top. The spec as written. |
| `fig3_norms_osgood_en_oriented.*` | `--orient`: aligned pole on the right of every row. RH asked for it and reverted it — orienting flips the pole NAMES with the row, so `k_bodily_harm` draws as "Bodily harm -> No harm". |
| `fig3_norms_osgood_en_fitted.*` | `--fitted`: triangles from the slope. **A DIAGNOSTIC, NOT A FIGURE** — five of fourteen fitted low triangles sit on the opposite side of zero from the data, and `k_vulgarity` lands at +17.5/-23.1 SD on a denominator of 0.0004. See `fig3_osgood.fitted_vs_observed`. |
| `fig3_dose_osgood_en.*` | the one-ruler companion, the scatter's x only, ruler named on the plate. |
| `fig3_norms_osgood_en_z.*` | `--z`: the move in SDs of **the norm's own spread**, so one unit means the same thing on every row. RH's, 21 Sep. Mean within lineage by default; `--z-median` restores the median. |

The 56 pole words in `fig3_osgood.PICKS` are on file for whenever the row plate is drawn for the book.

## NEITHER SCATTER AXIS IS A DISTANCE, AND BOTH HAVE THE SAME FORM

This is the sentence the v6 caption needed and the one that is easiest to get half-right. Both coordinates are a median divided by the between-lineage SD **of that same quantity**:

    vertical    median per-lineage marginal change / SD of those changes
    horizontal  median per-lineage slope on lift   / SD of those slopes

So a scale scores high by moving far, or by moving consistently, or both, and **the coordinate alone cannot separate the two**. Do not write that either axis "measures agreement rather than distance": that is the same error as calling it a distance, with the sign reversed. Two illustrations, both on the vertical axis and both from the gated `levels` table:

- `k_bodily_harm` and `k_register_level` move by 0.0062 and 0.0058 scale points — within 7 percent of each other — and sit at y = -1.11 and +0.64. Here the gap is almost entirely spread.
- `k_concreteness` moves 0.0241, **3.9 times** `k_bodily_harm`, and sits at y = -0.34 against -1.11 — a third of the distance from zero. Here the ordering inverts the movement outright.

**BOTH PAIRS ARE `k_` SCALES ON PURPOSE, AND THE FIRST VERSION OF THIS SECTION WAS NOT.** It illustrated the inversion with `warriner_arousal` against `k_bodily_harm` at "four and a half times", which compares rating points on a 1-9 scale against rating points on a 1-7 scale. A point is not the same size on the two, and correcting for range the factor is 3.4, not 4.5 — inflated by a third by the unit mismatch. The direction survived; the number did not. **This is the thread's own error one level down**: a comparison whose two sides have different denominators, inside the note warning that the axes have different denominators. `k_concreteness` against `k_bodily_harm` is the same illustration with the objection removed, both 1-7, and it is the pair to quote.

On the horizontal axis the same pair works: `k_register_level` and `k_bodily_harm` have raw median slopes of +0.0082 and -0.0387, a factor of 4.7 apart, at |x| of 0.66 and 0.70.

## Two numbers withdrawn on the way here

- **"The band medians recover a tenth of the fit"** compared a band MEAN lift against a band MEDIAN outcome, one estimator on each side of one ratio. Band median lifts are -0.060 and +0.794, a gap of 0.854: it is a **seventh**. Both means and medians are now in `results/norms_by_lift_en.json`.
- **"The marginal on vocalisation is null"** was read off a median of exactly 0.000 one paragraph after diagnosing that this scale's medians are tie-clipped. The sign test on the same data is 22 down against 7 up of 29 untied, **p=0.008**. Alignment makes the typical completion less vocal and spends that as charge rises.

## THE ESTIMATOR IS A SECOND DEFECT, SEPARATE FROM THE RULER

The z plate fixes the ruler and NOT the clipping, and those were always two problems rather than one. Changing a denominator cannot move a statistic pinned to a tie.

The median over prompts within a lineage lands on exactly 0.000 for up to 42 of the 50 lineages (`k_vulgarity` 42, `v6:makes_worse` 22, `v6:vocalisation` 21, `v6:directedness` 19, `v6:makes_better` 14). The mean ties on **none** of the fourteen, so every row uses all 50 lineages rather than conditioning on the untied subset, and the usual objection to a mean has a ceiling here because the scales are bounded (1–7, 1–9) and so are the differences.

**AND THE TWO SEND `v6:vocalisation` IN OPPOSITE DIRECTIONS, BOTH SIGNIFICANT.**

    mean within lineage, median over lineages   +0.0311 z   33 up / 17 down / 0 tied   p = 0.033   TOWARD speech
    median within lineage                        0.0000 z    7 up / 22 down / 21 tied   p = 0.008   AWAY from speech

Most prompts inside a lineage move slightly toward silence; a minority move a long way toward speech, so the typical prompt and the net mass go opposite ways. **"Alignment makes the typical completion less vocal" is withdrawn as a headline** — it is a claim about the median prompt, and "charge is talked, not deleted" rests on the mass. `v6:makes_worse` and `v6:directedness` are the cost: decisive on the median (p=2.7e-05, 4.6e-07) and null on the mean over all 50 (p=0.89, 0.20), so if either is cited the conditioning has to be stated.

## THREE WRONG STATISTICS RENDERED CLEANLY BEFORE THIS ONE WAS RIGHT

The move between the two marginal medians; then the median across lineages of (lineage median aligned − lineage median base); then the per-row difference medianed within the lineage. **A median does not commute with a difference** — the first two differ by 63 percent on `warriner_valence` — and only the third reproduces the published marginal. `norms_levels_z.py` now gates on it: `move_z × sd` must equal `*_gated_en.json` exactly, 173 of 173 scales. Each of the three drew a plausible plate.
