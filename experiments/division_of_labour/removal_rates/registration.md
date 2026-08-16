# Registration — removal_rates

**FROZEN 2026-08-16, before any removal rate was computed.** Amendments append below, dated, never edited in place.

**Written WITH RH rather than drafted and reviewed** — the first registration in this project to be. Every earlier one was frozen solo and each cost a full run before its operationalisation was found wanting: `sft_share`'s H3 decided on a p-value its producer never printed, `lexical_domains`' L1 differenced two quantities computed on different prompt sets using a "share" that is not a share. The design decisions below that came from RH and not from me are: §1 accepted (*"misoperationalisation shows us nothing relating to hypothesis so not a null"*), §5's separation of sexual from violent into two independent hypotheses, and §5's inclusion of `both` in both sets.

---

## 1. This is the THIRD test of a claim that has failed twice. Stated first.

*"SFT handles sex, DPO handles violence"* has returned null twice:

- **H3** (`sft_share`), prompt-domain labels, SFT share of total JS: base level +0.0086, p=0.077.
- **L1** (`lexical_domains`), word-level via the blind lexicon: +0.0024, CI [−0.047, +0.047].

L1's registration pre-committed that a second null **withdraws** the claim. It was withdrawn. **Changing the statistic and trying again is exactly what a stopping rule exists to prevent**, so this document has to justify itself or not exist.

The justification is that L1 measured the wrong quantity, which was established *after* it ran, by adversarial review, and is recorded in its README:

- **`share` is not a share.** JS is not additive along a path, so `js(base→sft)/js(base→endpoint)` is a ratio of two path lengths sharing an endpoint. It exceeds 1 when the endpoint sits closer to base than the SFT rung (internlm2, 1.237).
- **JS is symmetric.** A sexual word that *rises* contributed exactly as much as one that *falls*. For a claim about repression that is backwards: L1 measured **movement**, not **removal**.
- **The preference step never entered the statistic.** `sft→pref` is measured for all 18 chains and appeared nowhere in the test. "SFT or DPO?" was asked without measuring DPO.
- **Violence was used as sexual's baseline**, so the test was structurally blind to "SFT handles both" and imported violence's noise into sexual's estimate.

**A test that measured the wrong quantity is not evidence about the claim.** Two nulls of which one is mis-operationalised are one null. That is the argument; if it does not hold, this experiment should not run.

## 2. DISCLOSURES — things that are true and inconvenient

**I have already seen 3 of 16 lineages.** `Olmo-3-1025-7B`, `Amber` and `pythia-2.8b` were computed as a worked example *while designing this statistic*, and they are what convinced me the statistic was better. The OLMo numbers are **favourable to hypothesis A** (SFT removes 66.5% of sexual mass against a 37.1% all-words baseline; at the preference stage sexual falls to baseline). Amber is unfavourable; pythia is null-ish. **This design was chosen with partial outcome data visible.** No amount of pre-commitment undoes that, and it is the reason the OLMo family must not be reported as a confirmation here.

**Effective n is ~40 prompts, not 2,189.** 82% of the sexual mass departed at SFT sits in 40 prompts; 92% in 81. Whatever panel is declared, that is the real denominator, and every interval should be read against it.

**The OLMo subgroup is already known to be the strong one** from `lexical_domains`' post-hoc split (+0.0535, 4/5). Any family-level reporting here is descriptive and inherits that contamination.

## 3. The measurement

**Falls only.** `removed_C(stage)` = summed mass of *negative* deltas on category-C words. Rises are not netted off. The claim is about repression: what a stage takes away, not where the balance lands. Net is reported separately and decides nothing.

**Rate, not amount — because the stages are sequential.** The preference stage inherits a distribution SFT already stripped, so a raw comparison of amounts punishes it for arriving second:

    rate_C(stage) = removed_C(stage) / inherited_C(stage)

where `inherited_C` is the category's mass in the distribution the stage *started from* (`p_base` of that edge) — **each stage against its OWN starting mass, not against the base model's.**

**Why own-starting-mass, decisively.** The neutral reference absorbs depletion only if depletion is equal across categories, and it is not: if SFT strips sexual harder than neutral — which is what hypothesis A asserts — then by the preference stage sexual has proportionally less left than neutral does. Under base-mass denominators that **mechanically suppresses sexual's preference-stage rate**, which is the very quantity B compares. The hypotheses would be biased against by their own denominator. Own-starting-mass scores each stage on what it still had.

The cost is interpretive: this answers *"of what you inherited, what fraction did you strip"* rather than *"what share of the original work did you do"*. That is accepted, and is arguably the better reading of "handles" — a stage that removes half of what remains is handling it whatever the absolute amount. The base-mass version appears in the §5 C table as the intuitive decomposition, **labelled depletion-confounded**.

**Pooled over the full declared panel**, not averaged per prompt. Pooling is self-weighting: a prompt carrying no sexual mass contributes nothing to numerator or denominator, so it cannot dilute. This is why the panel choice is not load-bearing, and why the panel is *not* restricted to transgressive prompts — the weighting does that job without a hand-picked subset.

**Sensitivity check: per-prompt averaging.** Not a restriction to the high-mass prompts. Pooling is already dominated by them — 82% of sexual departed mass sits in 40 prompts — so restricting to those would reproduce the pooled result by construction, and **a check that cannot fail is not a check**. Per-prompt averaging is the genuine alternative: it downweights exactly those 40 and gives the other 772 mass-bearing prompts equal say. Agreement between the two says the result does not rest on a handful of prompts; disagreement says it does, and that would be worth knowing.

**Panel**: the prompts held by all 154 models in the pairs population AND declared live (2,189). **Unit: the LINEAGE** (16), per the campaign rule.

## 4. The reference set — and why not `k_`

**Reference = the 3,812 words rated `neither` by ≥2 of 3 blind raters in the lexicon build, excluding admitted lexicon words.**

    854  hidden controls (random vocabulary)
    594  audit words (random remainder)
  1,606  rejected expansions   } proposed as transgressive by the
    758  rejected candidates   } generators, refused by the panel
  median corpus cells 24, against the lexicon's 20

Two reasons this rather than anything else. It is **positively rated neutral**, not merely absent from the lexicon — absence and rated-neutral are different claims. And it comes from the **same protocol, same raters, same session**, so rater idiosyncrasy applies equally to both sides of the comparison.

**A THIRD REASON WAS CLAIMED AND IS WITHDRAWN.** An earlier draft said the reference was already frequency-comparable, so no matching was needed. That rested on the lexicon's `cells` field, which was **wrong**: the builder keyed a dict on `w.lower()`, so a case collision overwrote rather than summed and `rape` was booked at 4 cells (the count for `Rape`) against a true 3,130. Corrected, case-summed:

    neutral reference   median 52 cells
    violent             median 50   <- matched
    sexual              median 30   <- NOT matched

So the confound is handled by construction for **B** and not for **A** — and A is already the arm estimated from a seventh of the mass. **The reference is therefore frequency-matched to each category separately**: for each lexicon word, draw neutral words whose corpus cell count is within ±25%, sampled with a recorded seed, and use that matched reference for that category's excess. The unmatched reference is reported alongside so the size of the correction is visible rather than assumed small.

**`k_ratings` is refused as a definition of neutrality, on its own evidence.** Its scales are floors, not measurements: `vulgarity` has variance on **1.7%** of words, `bodily_harm` 6.6%, `transgressiveness` 11.7%. "Low vulgarity" therefore includes essentially the entire dictionary, `cock` among it — which is the exact instrument failure that motivated building the lexicon. Reintroducing it on the reference side would be the same error facing the other way. (`register_level` 92%, `valence` 99% and `concreteness` 78% do carry real variance and are usable for *matching*, if matching is later wanted.)

## 5. Hypotheses — SEXUAL and VIOLENT ARE NEVER COMPARED TO EACH OTHER

Each category is compared only to neutral, at the same stage, in the same lineage. "SFT handles both" and "neither stage specialises" are therefore sayable outcomes rather than quantities that cancel.

    excess_C(stage) = rate_C(stage) − rate_neutral(stage)

**A — SEXUAL IS AN SFT SPECIALITY.**
Predicts `excess_sexual(SFT) > excess_sexual(PREF)`, paired within lineage.

**B — VIOLENT IS A PREFERENCE-STAGE SPECIALITY.**
Predicts `excess_violent(PREF) > excess_violent(SFT)`, paired within lineage.

**`both` WORDS ARE IN BOTH SETS.** RH, 2026-08-16: they are important sexual words and holding them out attenuates A in exactly the place alignment is most likely to act. The 14 are `rape, raped, rapes, raping, rapist, rapy, molest, molestation, molested, castrate, castrated, castrates, ravish, ravished`.

    sexual set  = sexual ∪ both
    violent set = violent ∪ both

**This is only legitimate because A and B are never compared.** A word in two sets would be double-counting in a contrast; in two independent tests it is simply the true statement that `rape` is sexual content and is violent content. The `both` category exists in the lexicon because raters were asked to name it; it was never a claim that such words belong to neither.

Effect is asymmetric, and declared before the run: sexual's share of departed transgressive mass goes **11.9% → 13.3%** (a 12% gain, in the most marked vocabulary it has), violent's **86.7% → 88.1%** (negligible).

**KNOWN FALSE POSITIVE, disclosed:** `rapy` is not a word. It is a stage-C expansion artefact (`rape` → `rap` + `y`, since the suffix list includes `y`) that scraped in at 2 of 3 votes, one rater calling it `neither`. It is retained because the admission rule is ≥2 of 3 and substituting my judgement for the blind panel's is the move the design exists to prevent — but it carries 17 corpus cells against ~3,500 for the `rape` family, so its influence is nil.

**C — descriptive, no threshold, no claim.** Raw rates for every category and stage, plus the base-mass decomposition (depletion-confounded, labelled).

**PRECISION IS VERY UNEQUAL BETWEEN A AND B, and this is declared before the intervals exist.** Of departed transgressive mass: **violent 86.7%, sexual 11.9%, both 1.4%.** Sexual's rate is estimated from roughly a seventh of the mass violent's is, so **A is the much noisier hypothesis** and will have the wider interval for reasons that have nothing to do with whether it is true. Read A's bound against that, not against B's.

**A and B are reported separately and are NOT summarised into a single verdict.** The original claim is one sentence with two halves; if A passes and B fails, the sentence is false and something real has still been found, and that must be sayable.

## 6. Executable decision rules

1. **Unit is the lineage; the paired difference across 16 lineages decides.** Primary test is magnitude-using with a bootstrap 95% CI. The sign test is reported for continuity with H3/L1 but **its MDE is computed and printed before any p-value is read** — L1's sign test had an MDE of 0.10 against a real CI of ±0.05, and a null from a test that cannot see the effect is not evidence of absence.
2. **A null is reported as a BOUND.** "Not supported" is never written without the interval that says what is excluded.
3. **Direction is fixed here.** A significant result in the opposite direction is a *surprise to be reported as such*, never confirmation.
4. **The lexicon is cited by sha `d542e7e2bb86bd00`.** A rebuild means re-run or withdraw.
5. **STOPPING RULE. If A and B both fail, the claim is dead.** No fourth instrument, no fifth statistic. It is recorded as not supported at prompt level, at word level, and at removal-rate level, and this project stops asking.
6. **Family-level reporting is descriptive only** and must carry the disclosure in §2.

## 7. The outcome I would rather not see

That A passes because SFT over-removes *everything* and the neutral reference fails to absorb it. H1 puts SFT at ~82% of all displacement, so a stage-level asymmetry is the default state of the world, not a finding. **If `excess_sexual(SFT)` is large but `excess_neutral` is also large in the same direction, A is measuring thoroughness, not specificity** — and the raw-rate table in C is what makes that visible rather than hidden inside a difference.

Second: that A passes on the strength of the OLMo lineages I have already seen, and the honest conclusion is a family-specific effect that the aggregate cannot support.

---

## Open questions for RH — these are the marks I want on the draft

- ~~Is §1's justification good enough?~~ **ACCEPTED, RH 2026-08-16.**
- ~~own-starting-mass or base mass?~~ **RESOLVED: own-starting-mass** (§3), because category-specific depletion would otherwise bias B's denominator.
- ~~is `both` worth reporting?~~ **RESOLVED: reported, no hypothesis, 1.4% stated** (§5 C).
- ~~which sensitivity check?~~ **RESOLVED: per-prompt averaging** (§3); the high-mass restriction cannot fail and so checks nothing.

**Still open, and the only thing left before freezing:** nothing. If RH is content with the four resolutions above, this is ready to date and freeze.
