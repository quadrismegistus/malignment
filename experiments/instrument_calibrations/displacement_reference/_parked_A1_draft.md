# Registration — alignment_specificity

**DRAFT, NOT FROZEN. Awaiting RH's read.** Nothing in the real arm has been computed. Freeze by changing this line, dated; amendments append below and are never edited in place.

**Drafted with RH across 2026-08-16.** Two of the design decisions below are RH's and neither is cosmetic: the shuffle direction in §4 (I proposed a null that preserved the property under test) and the refusal in §3 to build this on scalar structure statistics.

## 0. WHAT THIS IS — ONE question, and what was removed from it

**A1.** Alignment removes transgressive mass **at a higher rate than it removes a matched neutral vocabulary**, within lineage. One-sided. That is the whole experiment.

**A SECOND OBJECT WAS DRAFTED HERE AND HAS BEEN REMOVED — RH: *"aren't these 2 very different questions".*** A calibration (`C1`: how far apart are two unrelated pretraining runs) was bundled in because both grew out of one shuffle idea. They share only the panel: C1 needs no lexicon, A1 needs no shuffle.

**It was removed because REGISTRATION IS FOR THINGS THAT CAN BE WRONG.** C1 has no decision rule it could violate, so registering it would put a row in the hypothesis register that cannot fail — the exact shape that lets a null be read as a finding. C1 is now a **reported reference**, produced and cited, registered nowhere. It still matters: every displacement number this project quotes (OLMo 0.176, Qwen 0.044, Amber 0.181) has never had a *compared to what*.

**The part of C1 that was genuinely A1's has stayed**, as §3b: the base-to-base DiD centring check, which tests whether the reference vocabulary is matched. That is A1's internal validity, not a second question.

**A1 WAS ITSELF WEAKER AND WAS REPLACED BEFORE THE FREEZE.** It first read *"an endpoint removes more transgressive mass than an unrelated base differs"*. That is nearly free: alignment removes mass from most things, and a base-to-base null rules out "any two models differ this way" without ruling out **generic smoothing**. RH's objection — *"obviously alignment exists, what are we trying to prove here?"* — is what the difference-in-differences answers. **A stage that strips everything equally scores exactly zero on it, by construction.**

## 1. WHAT WAS ALREADY LOOKED AT — disclosures

**The real arm is unspent.** Transgressive mass has been computed for the 50 BASES only. No endpoint's transgressive mass has been computed, by me or anyone, at any point in this design.

**The null arm has been fully inspected and that is deliberate**, since it is a calibration and its properties had to be checked before it could be used:

    transgressive mass per base, 48 measured bases x 120 sampled panel prompts
      median 1.4025 | IQR 1.2721-1.5438 | range 0.6354-2.2935
    base_i - base_j over 2,256 ordered pairs: mean +0.00000, sd 0.4284
    corr(params_b, transgressive mass) = +0.060  (n=48)

**A DIRECTIONALLY-PREDICTED RESULT IS BEING REGISTERED ON THE STRENGTH OF A PRIOR FINDING.** The archive records that transgressive token mass separates categories where scalar metrics do not, on a 62-token list. This registration uses the same anchoring idea on the same corpus with a 1,063-word lexicon. So A1 is not a blind prediction; it is an extension of a result that has already worked once, and it should be read as a confirmation attempt rather than a discovery.

**No pilot was run on the real arm and none may be.** If one is wanted, it must be on a subset declared spent and excluded from the final n, before the freeze.

## 2. THE MEASUREMENT

**Transgressive mass** = summed probability on the 1,063 admitted words of `experiments/sex_violence_lexicon` (sha `d542e7e2bb86bd00`, 655 violent / 394 sexual / 14 both), over the declared panel.

**Reference vocabulary** = the **3,812** words rated `neither` by >=2 of 3 blind raters in that same build and admitted to nothing. Matched by construction: every one went through the identical rating instrument. *Not* "all other words", which would be the 225k vocabulary, most of which no rater ever saw.

**THE STATISTIC IS A DIFFERENCE-IN-DIFFERENCES**, one value per lineage:

    rate_C   = (mass_C(base) - mass_C(endpoint)) / mass_C(base)
    DiD      = rate_transgressive - rate_reference

Positive means alignment stripped the lexicon proportionally harder than the neutral set.

**Paired within base, never pooled across.** Bases span 0.6354 to 2.2935 — a 3.6x range — so a raw comparison of levels across bases is meaningless. Every observation is a within-base difference.

## 3. WHY NOT SCALAR STRUCTURE STATISTICS — a design that was tried and abandoned before the freeze

An earlier version tested `n_rise/n_fall`, `arrived/total moved` and arrival concentration, real versus shuffled. **Abandoned on RH's objection, which the record confirms**: scalar metrics — JS, entropy drop, top-50 overlap, rank correlation — are already known not to separate transgressive from neutral prompts in this corpus (Mann-Whitney p > 0.05 for all families; OLMo's neutrals show HIGHER mean JS, 0.224, than its transgressive prompts, 0.167). A stratum hypothesis built on that class would have produced an uninterpretable null.

A pilot of the abandoned version was run (24 pairs, 40 prompts, one shuffle draw): structure statistics agreed within 3-14% between real and shuffled while magnitude ran 1.65x LARGER for shuffled. **That pilot is reported here as the reason for the abandonment and is not part of this registration's evidence.**

## 3b. WHERE THE SHUFFLE WENT, AND THE ASSUMPTION IT NOW TESTS

**RH asked whether A1's second arm is another base or an aligned model. It is the lineage's OWN ALIGNED ENDPOINT, and A1 contains no shuffle at all.**

    A1   base_i -> its own endpoint   an ALIGNED model. The control is the
                                       VOCABULARY (lexicon vs reference), not a model.
    §3b  base_i -> base_j             another BASE. Not a hypothesis: a check
                                       that the reference vocabulary is matched.

That is a drift from the design this experiment started as — a cross-lineage shuffle — and it happened when A1 became a difference-in-differences: uniform smoothing is now cancelled by the reference arm, so no shuffle is needed to cancel it. **Recorded rather than quietly absorbed**, because the shuffle is what motivated the experiment and a reader will look for it.

**THE SHUFFLE DOES RETURN, AS THE NULL FOR THE DiD ITSELF.** The difference-in-differences assumes the reference set is MATCHED — if lexicon words differ from `neither` words in any way two arbitrary models differ on (frequency being the obvious candidate, §7), then base-to-base would show a non-zero DiD and A1's positive result would be confounded. Measured, null arm only:

    BASE-TO-BASE DiD, 288 pseudo-pairs over 48 bases
      mean -0.0115   median +0.0134   sd 0.1781
      positive 155/288 = 53.8%
      one-sample t vs 0: p = 0.2760

**Mean and median straddle zero and neither differs from it significantly, so the reference set is adequately matched and §7's frequency confound is not detectable at this resolution.** The 288 pairs are not independent (each base appears six times) so the p-value is optimistic; the check is the centring, not the test.

## 4. WHY THE NULL FOR §3b IS BASE-TO-BASE AND NOT BASE-TO-OTHER-ENDPOINT

    REAL   base_i -> its own endpoint      an alignment relation exists
    NULL   base_i -> base_j,  j != i       no alignment anywhere in the comparison

**THE NULL MAY NOT BE ANOTHER ENDPOINT.** An earlier draft shuffled `base_i -> endpoint_j`. RH's objection: every endpoint has low transgressive mass regardless of lineage, so the shuffled arm would show removal too — the control would have preserved the exact property under test and returned a null meaning "both arms are aligned". **A control that cannot distinguish its own treatment is not a control.**

`base_i -> base_j` has no alignment relation on either side. Its centring is tautological over ordered pairs; what it supplies is the **spread**, sd 0.4284 against a typical level of 1.4025 — between-run variation is ~30% of the level.

**Free shuffling is legitimate on the size axis**: r = +0.060 between parameters and transgressive mass across 48 bases, so `base_j` needs no matching on scale.

**THE NULL IS CONSERVATIVE AND THIS IS A STATED LIMIT, NOT A CAVEAT.** The real arm is size-matched by construction (an endpoint is its own base post-trained; median |Δparams| = 0.00B) while the null is not (median 1.96B) and additionally carries architecture and tokenizer differences the real arm never has. Its spread is therefore wider than the true no-alignment spread for a same-architecture comparison. **An effect clearing it clears it with room; an effect failing to clear it is not thereby null.**

## 5. UNIT, POPULATION, POWER

**Unit: the base. n = 50, and there is no clustering to correct.** `roster.endpoints()` returns one endpoint per base, so no base contributes two rows — llama/tulu/tulu-no-safety cannot appear as three, because Tulu is in `chains()` and not a second llama endpoint. Verified: **0 of the 50 bases is derived from another checkpoint** by any DERIVING edge, so all 50 are independent pretraining runs. (This was checked because the campaign's standing rule is that the unit is the lineage; here the population already is one per lineage.)

**Panel**: prompts held by all 154 models in the pairs population AND declared live (2,189).

**MDE, from BLINDED variance estimation — `run.py --variance`, which emits an sd and nothing else.**

    statistic                          sd       MDE 80%      MDE 90%
    absolute difference            5.6792     2.0386        2.3988     (= 6.7% of level)
    removal rate                   0.1757     0.0630        0.0742     (= 6.30 pp)
    DIFFERENCE-IN-DIFFERENCES      0.1474     0.0529        0.0623     (= 5.29 pp)

    sign test, n=48: needs 31/48 positive (p=0.0297); 30/48 gives p=0.0557

**THREE THINGS WERE LEARNED WHILE BLINDED AND ALL THREE CHANGED THE DESIGN.**

1. **The conservative bound was miscomputed.** The 0.4284 / MDE 0.1506 / "10.7% of level" figures came from a 120-prompt sample and were compared against a full-panel level. On the 2,189-prompt panel the unpaired sd is 6.3768 and the bound is 7.5%, not 10.7%.
2. **Pairing barely helps: 1.12x, not the 3-10x predicted.** Between-base LEVEL is not what makes this noisy; how much each family removes is. `sd(rate) = 0.1757` means removal rates vary by ~±17.6 percentage points across lineages, which is the known order-of-magnitude alignment-intensity variation appearing as the binding constraint.
3. **The rate did not help either** (6.30 pp against 6.7% of level) — the heterogeneity is proportional, so dividing by level does not remove it. **The DiD does help**, to 5.29 pp, because differencing against the reference removes the family's overall smoothing intensity.

**STATISTICS WERE CHOSEN ON VARIANCE WHILE BLIND TO EFFECT, AND THAT IS DECLARED.** Selecting for power is legitimate only if the chooser cannot see the effect; `run.py` enforces that by call graph — `_paired_differences`, `_paired_rates` and `_paired_did` are private, nothing outside consumes a list, and the CLI prints an sd and counts. No mean, no sign, no count of positives, and no individual lineage value has been computed at any point.

## 6. DECISION RULES — executable, fixed now

**PRIMARY: the sign test on the DiD.** SUPPORTED iff **>= 32 of 48** lineages have DiD > 0.

**32, NOT 31, BECAUSE THE NULL IS NOT A FAIR COIN.** The measured base-to-base DiD is positive 53.8% of the time, not 50%. Against p0=0.500 the threshold is 31/48 (p=0.0297); against the measured p0=0.538 it is **32/48 (p=0.0490)**. The lean is not itself significant (binomial p≈0.21 on non-independent pairs), and 31/48 would have been defensible — **the stricter threshold is taken because a null measured at 53.8% should not be tested against an assumed 50%.** It costs power: 0.75 rather than 0.84 at a true P(positive) of 0.70, 0.93 at 0.75.

**Sign test primary because the variance structure says so.** `sd(DiD) = 0.1474` against an unknown mean is the signature of heterogeneous magnitude; where direction is consistent but amount is not, a sign test is better powered and a few large negative lineages cannot defeat it. Making the paired t co-primary would have made the weaker instrument binding. (Power at the 32/48 threshold: 0.75 if the true P(positive) is 0.70, 0.93 at 0.75, 0.99 at 0.80.)

- **Paired one-sided t is REPORTED BESIDE IT and decides nothing.** Its MDE is 5.29 pp at 80%.
- **NOT SUPPORTED** is quotable only as a bound: *"at n=48 the sign test needed 32/48 and had 75% power against P(positive)=0.70; the paired t could have detected 5.29 percentage points."*
- **Ties dropped, never split.**
- **Both component rates are reported** beside the DiD. A DiD near zero because neither rate moved is a different world from one where both moved together, and the DiD alone cannot tell them apart.

## 7. WHAT WOULD MAKE THIS EXPERIMENT WRONG RATHER THAN NEGATIVE

If the lexicon words are systematically rarer than the corpus average, alignment could strip them as a side effect of any distributional smoothing. The lexicon build's reference set (3,812 `neither`-rated words) exists for exactly this and **frequency matching is NOT part of this registration** — it is named here as the first amendment anyone should propose if A1 comes out positive.
