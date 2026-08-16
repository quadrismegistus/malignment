# Registration — displacement_reference

**INSTRUMENT REGISTRATION. It declares how a reference is BUILT, not what will be found.**

**DRAFT, NOT FROZEN. Awaiting RH's read.**

---

## What is being tested: NOTHING. What can be wrong: the construction.

This produces a **scale**, not a result. There is no hypothesis, no direction, no p-value and no decision rule, because there is no outcome that could contradict it. A reference cannot be false; it can only be **built wrongly**, and this file exists so the building is arguable.

The question it answers is one the project has asked implicitly for months and never answered: **when we say alignment displaces a model by JS 0.176, is that a lot?** Nothing in the repository says. This measures what the same statistic reads between two models where **no alignment relation exists on either side**, so any displacement figure can be quoted as a fraction of it.

**FOUR WAYS THIS COULD BE BUILT WRONG, which is what the rest of this file pins down:**

1. the pairs might not actually be alignment-free
2. the statistic might not be the same one the numbers it calibrates were computed with
3. the panel might differ from the panel those numbers used
4. the pairwise count might be read as an independent sample size

Only (2) is currently unresolved, and it is declared in §4 rather than rounded past.

## 1. The population — and why it is bases only

**Every pair is two INDEPENDENTLY PRETRAINED models.** The 50 declared bases from `roster.endpoints()`, restricted to those with cells (49 at the last run). Ordered pairs, `i != j`.

**Verified, not assumed: 0 of the 50 is derived from another checkpoint by any `DERIVING` edge.** Falcon3-10B is upscaled from 7B and Yi-1.5 is continual-pretrained, but neither is in `endpoints()` — the terminal-under-DERIVING rule already excludes them. A reference built on a pair where one was upscaled from the other would understate the very distance it exists to measure.

**The aligned models are not used.** Not as a second arm, not as a comparison. This is the whole point: a reference containing an aligned model would contain some alignment.

## 2. The panel

Prompts held by all 154 models in the pairs population AND declared live: **2,189**.

**JS IS COMPUTED ON A SAMPLE OF 30 AND THE OTHERS ARE POOLED OVER ALL 2,189.** JS needs the full word distribution per (model, prompt), so its cost is `n_bases^2 x n_prompts` rather than a single grouped sum. `--js-prompts` controls it and the value used is recorded in the output. **The sample is a cost decision and it is the one number here most worth increasing** if the reference is ever leaned on hard.

## 3. The statistics, and what each is for

    js_divergence                   the one the published family numbers use
    transgressive_mass_difference   lexicon mass, base_i minus base_j
    transgressive_removal_rate      the same as a fraction of base_i's own mass
    difference_in_differences       lexicon rate minus reference-vocabulary rate

**THE FIRST THREE ARE CENTRED BY CONSTRUCTION AND THE SPREAD IS THE REFERENCE.** Over ordered pairs, `mass(i) - mass(j)` sums to zero by symmetry. Reporting the median as if it were a finding would be reporting arithmetic. **Only the IQR, sd and range carry information.**

**`difference_in_differences` is doing a second job and it is worth stating separately.** Its centre tests whether the 3,812-word `neither` vocabulary is MATCHED to the 1,063-word lexicon — whether two unrelated models diverge more on one than the other. That is the assumption every excess-over-neutral statistic in this project rests on, `removal_rates`' `excess_C` included, and it had never been checked. If this comes out systematically non-zero, that is a defect in the *lexicon build*, discovered here.

## 4. THE UNRESOLVED ONE — a tail convention, declared before use

**This producer normalises JS over the union of observed words. `movement_cells.js_total` carries a separate `js_tail` term for residual mass.** They share a name and may not share a value.

**So the comparison this reference exists to license is INDICATIVE and not yet exact.** At the first run: real base→endpoint edges median 0.1153 against a no-alignment reference of 0.1688. That ratio is the headline and **it must not be quoted until the conventions are reconciled** — by computing the reference through the same producer that builds `movement_cells`, run on shuffled pairs.

Recorded here rather than in a footnote because comparing two statistics that share a name and differ in the tail is precisely the failure this repository keeps paying for, and a reference that gets it wrong poisons everything that cites it.

## 5. THE COUNT IS NOT A SAMPLE SIZE

49 bases produce 2,352 ordered pairs and 35,280 JS values. **Those are not 35,280 independent observations — they are 49 models compared to each other.** Each base appears in 48 pairs and every value shares a model with many others.

**Therefore: median, IQR, sd and range only. No confidence interval, no standard error, no significance test may be computed on this object, and none is.** A CI on 35,280 pairwise values would be narrower than the truth by roughly an order of magnitude, and it would look entirely respectable.

## 6. Custody

`results/reference.json` carries `n_bases`, `n_pairs`, `n_panel_prompts`, `n_js_prompts`, `lexicon_words`, `reference_words` and a `note` per statistic. **A citation of this reference must name the panel and the JS sample size**, because both move the numbers and neither is visible in a quoted median.

## 7. What this registration does NOT cover

Any claim about what alignment does. This directory produces a ruler. `alignment_specificity`'s A1 was drafted here and parked — see `_parked_A1_draft.md` — on finding it was a replication of `removal_rates`' hypothesis A (same statistic, same lexicon, same reference set), which has already run and is SUPPORTED at +0.0894. **A hypothesis must not live in this folder**; that is the whole reason the folder exists.
