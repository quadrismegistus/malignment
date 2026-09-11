---
kind: question
id: acquisition_reversal
question: Is the order in which alignment removes words the reverse of the order in which pretraining acquired them?
status: "DESIGNED, NOT RUN, 2026-09-11. The join is verified (one lineage, 2,272/2,272 shared prompts, both rule_version 3) and a crude first look points in the predicted direction. Three design hazards are recorded, one of which tuning_order's own audit already solved."
headline: NONE STATED -- the design is written, nothing has been run.
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
