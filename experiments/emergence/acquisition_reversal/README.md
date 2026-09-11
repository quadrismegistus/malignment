---
kind: question
id: acquisition_reversal
question: Is the order in which alignment removes words the reverse of the order in which pretraining acquired them?
status: "RUN 2026-09-11. The prediction recorded before the run is MET: acquisition t_move and removal t_move correlate NEGATIVELY (median rho -0.0550, 235 of 383 prompts) and the sign survives partialling out log p (-0.0545). Small effect, consistently measured -- quote the rho with the 235/383, never the p-value alone."
headline: "What pretraining acquired later, SFT removes earlier. Jakobson's regression hypothesis holds of the cut on one Olmo-3 lineage -- median rho -0.055 across 383 prompts, unchanged by a frequency control. The effect is weak and consistent, and it is an analogy to a law about phonology, not an application of it."
grain: word
---

# acquisition_reversal

**Nothing has been measured.** This file states a design, its hazards, and the
predictions, so a run starts from them rather than from a fresh reading.

## THE QUESTION

Jakobson's regression hypothesis, from *Child Language, Aphasia and Phonological
Universals* (1941/1968): **dissolution reverses acquisition** -- what is learned
last is lost first, marked forms going before unmarked ones.

This campaign has both halves on one family:

    ACQUISITION   Olmo-3-1025-7B pretraining ladder, 43 rungs
                  stage1 step0..1,413,814 | stage2 | stage3
    REMOVAL       Olmo-3-7B-Think-SFT, 43 rungs, step1000..43000

**If the words that leave earliest in SFT are the ones pretraining acquired
latest, the regression hypothesis holds of the cut. If not, it fails.**

**CITATION NOT VERIFIED.** The statement above is a paraphrase and has NOT been
checked against Jakobson's text. Do not quote it, or attach a page number to it,
until someone has the book open. The design does not depend on the wording, but
the write-up will.

## WHY IT IS WORTH RUNNING

**It can come back negative.** Most theory-mapping in this area cannot: a
correlation is computed, a typology is fitted to it, and nothing in the design
could have failed. This one has a direction and a way to be wrong, which is rare
enough to be the main argument for doing it.

## THE JOIN IS VERIFIED

    roster: Olmo-3-1025-7B is the declared root of Olmo-3-7B-Think-SFT
    prompts: 2,272 shared of 2,272 on each side
    tables: BOTH rule_version 3 -- twp_words, NOT twp_words_v4, and `movement`
            holds no rows for either ladder, so deltas are computed not read

No cross-family assumption. That matters: `posttraining_corpus_analysis/
corpus_predicts_movement` drew a conclusion from a Pythia pretraining ladder
against a llama alignment edge and had to withdraw it when the same measurement
inside one Olmo family gave the opposite answer.

## A CRUDE FIRST LOOK, WHICH POINTS THE PREDICTED WAY

Olmo-3 pretrained-end (`stage3-step11921`) to Think-SFT-end (`step43000`),
400 prompts, words moving more than 0.001:

    words LOSING     16,191    median p at pretrained end 0.00250
    words GAINING     5,080    median p at pretrained end 0.00293

    losers present at stage1-step1000     31.7%
    gainers present at stage1-step1000    48.8%

**The words alignment removes were LESS likely to have been present early in
pretraining than the words it adds.** Learned last, lost first.

**This is a proxy, not the measurement.** "Present at step1000" is presence above
a theta floor, not acquisition, and these are pooled counts with no per-prompt
control. It is recorded because it points the OPPOSITE way from what this seat
expected -- the guess was that leavers would be the common, early-acquired words
-- and an expectation refuted by a crude look is a reason to run the careful one.

## THREE HAZARDS, AND THE FIRST IS ALREADY SOLVED NEXT DOOR

**1. THE ONSET-DEFINITION TRAP. Do not define acquisition by a threshold
crossing.** `tuning_order`'s cross-seat audit (docket [6648]) found that a
persistent-sign onset fires at the FIRST RUNG for 55% of sites, making a paired
lag 0 by construction: *"the statistic times when the sign settles, not when the
mass moves."* An acquisition-order measure built the same way will reproduce the
artifact exactly. **Use `t_move` -- centre of mass of per-step movement -- from
the start.** The producer is in `../tuning_order/`.

**2. THE THETA FLOOR CONFOUNDS "ACQUIRED LATE" WITH "NEVER SCORED."** A word
absent at an early rung may be below threshold rather than unacquired. The crude
look above inherits this. Restrict to words present at both ends, or define
acquisition on mass rather than presence.

**3. FREQUENCY IS CORRELATED WITH BOTH HALVES** and must be partialled out.
Frequent words are acquired early and are unmarked; rare words late and marked.
Without the control, a positive result may be Zipf's law wearing Jakobson's
clothes.

## PREDICTIONS, TO BE RECORDED BEFORE THE RUN AND NOT AFTER

- **HOLDS** if `t_move` in SFT correlates NEGATIVELY with `t_move` in
  pretraining -- late-acquired words leave early -- with frequency partialled
  out and the correlation surviving it.
- **FAILS** if the correlation is null or positive once frequency is controlled.
- **A positive result that vanishes under the frequency control is a NULL**, and
  is to be reported as one rather than as a weakened positive.

---

# THE RESULT (2026-09-11): IT HOLDS, AND IT IS SMALL

`run.py`, 400 prompts, 43 pretraining rungs against 43 SFT rungs, 41,148 words
carrying a `t_move` on both ladders.

    raw                     n=383   median rho -0.0550   148 up / 235 dn   p=1.02e-05
    log-p partialled out    n=383   median rho -0.0545   142 up / 241 dn   p=4.79e-07

**The prediction recorded above is met.** The correlation between acquisition
`t_move` and removal `t_move` is NEGATIVE -- words pretraining acquired later
leave earlier under SFT -- and it holds in 235 of 383 prompts.

**AND IT IS NOT FREQUENCY.** This was the hazard most likely to produce a false
positive, and the control costs almost nothing: -0.0550 raw against -0.0545 with
`log p` at the pretrained endpoint partialled out of both sides, with the sign
test improving rather than degrading. The README's own rule -- a result that does
not survive the control is a NULL -- does not fire.

## THE SIZE IS THE CAVEAT, AND THE p-VALUE MUST NOT CARRY IT

**Median rho -0.055, and 61% of prompts negative.** That is a weak correlation
measured consistently across many replicates, and the p-value is a statement
about the consistency, not the strength. Quote the rho and the 235/383 together
or neither; `p=4.79e-07` on its own would misrepresent this by an order of
magnitude.

## WHAT THE CLOCK DOES, SINCE IT COULD HAVE INVERTED THE RESULT

The pretraining stages restart their step numbering, so `stage2-step1000` comes
AFTER `stage1-step1413814`. Placed on a cumulative clock:

    stage1   23 rungs   cumulative        0 .. 1,413,814
    stage2    7 rungs           1,414,814 .. 1,461,498
    stage3   13 rungs           1,462,498 .. 1,473,419

Monotone, no overlap. A raw step number would have put nearly all of stage2 and
stage3 inside the first 3% of pretraining and inverted every late acquisition
into an early one.

## WHAT THIS CANNOT ESTABLISH

- **Jakobson's law is about PHONOLOGY** -- the order of phoneme acquisition and
  its mirror in aphasic dissolution. Extending it to lexical items in a language
  model is an ANALOGY, not an application, and the write-up must say so. A
  result here is evidence about word-level ordering in one model family, which
  is a smaller thing than the law it is named for.
- **n = 1 lineage.** Olmo-3 is the only family in this store with both ladders.
- **SFT only.** The removal ladder stops before DPO and RLVR.
- **And the disanalogy is the interesting part, not a caveat.** A lesion is
  uniform; it impairs selection wherever selection occurs. Alignment is
  content-selective -- 43 of 50 lineages, strongest where candidates add charge,
  null where they do not. So even a positive result describes a bar that
  produces aphasia's shape where it is drawn, not an induced aphasia.
