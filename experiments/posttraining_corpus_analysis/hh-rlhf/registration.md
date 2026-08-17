# Registration — hh-rlhf, is preference lexically predictable?

**Frozen 2026-08-17, before `run.py` exists.** Mini, per RH. Amendments append
below, dated, never edited in place.

## The question

**Can a bag-of-words model tell `chosen` from `rejected`?** And is it better at
it on the HARMLESS half than the HELPFUL half?

If it can, alignment's preference signal is partly a word list, and M01's
displacement has a source in the data rather than only in the optimisation. If it
cannot, displacement is something the optimisation produces from data that does
not look lexical at all. **Both answers are worth having and the null is the more
interesting one.**

## Population, and the two arms are cached separately

Verified by content, not by matching row counts against a card:

    harmless-base   42,537 pairs   18.1% harm-word in the opening turn
                    `default-52e03caf22ec705f`
    helpful-base    43,835 pairs    1.3%
                    `default-cfba128a0ab1b99f`

**The contrast is the design.** A single pooled number would answer a weaker
question, and the pooled config (`default/`, 160,800) concatenates harmless
FIRST — so its head is not a sample of it, which is how I misread the harm rate
once already.

`helpful-online` and `helpful-rejection-sampled` complete the 160,800 and are NOT
cached separately. Out of scope, and named so the absence is not read as a
choice.

## THE UNIT IS THE PAIR, AND POOLING IS NOT A WEAKER OPTION BUT A WRONG ONE

    shared prefix, % of chosen    median 74.4%   p10 36.2   p90 92.9

Both columns carry the whole dialogue, so chosen and rejected share three
quarters of their characters. **A model on raw text would learn the prompt
distribution and score well while measuring nothing.** The within-pair difference
cancels the shared prefix exactly.

    features   delta = word counts(chosen) - word counts(rejected)
    label      SIGN-RANDOMISED: half the pairs presented reversed, label 0
    null       AUC 0.500 -- and it is a true null, because a constant cannot
               beat it once the sign is randomised

## LENGTH IS THE CONFOUND AND IT RUNS THE OPPOSITE WAY TO THE OBVIOUS GUESS

    chars, median      chosen 481   rejected 519
    chosen - rejected  median -21   chosen longer in only 42.1% of pairs

**Chosen is SHORTER.** I asserted the opposite before measuring it. So "shorter
wins" is a real and available signal that is not lexical, and it must be
separated rather than assumed away.

    REPORTED ALWAYS   AUC with length as a covariate, and AUC without
    AND               AUC on a length-matched subset

**If AUC collapses to chance once length is controlled, the answer is that the
signal is length and not vocabulary**, and that is the result rather than a
failed run.

## Executable decision rules

    SUPPORTED       AUC >= 0.60 on held-out pairs, length-controlled, in BOTH
                    arms. Test split only; the train/test division is the
                    dataset's own, never a re-split.
    LEXICAL GAP     harmless AUC - helpful AUC >= 0.05, same features, same
                    pipeline, both length-controlled
    NULL QUOTABLE   only with the MDE. An AUC near 0.5 on 42k pairs is a tight
                    bound and worth stating as one; on a small subset it is not.
    STOPPING        one specification. If it fails, that is the answer and a
                    second operationalisation is a new question with a line
                    saying why.

## The outcome I would rather not see

**I want the transgressive lexicon to carry the weight** — a high harmless AUC
whose top features are the M01 vocabulary would connect the corpus to the
displacement finding directly, and it is the result this project would use.

**So the thing to guard is a high AUC driven by something boring**: politeness
formulae, refusal templates ("I can't help with that"), the assistant's own
register, or length leaking through word counts. **Top features get read and
reported whatever they are**, and a refusal-template result is reported as a
refusal-template result rather than as evidence about vocabulary.

**And the honest second-worst outcome: harmless > helpful for the wrong reason.**
Harmless-base contains adversarial prompts, so its responses may differ in FORM
(refusal versus compliance) rather than in vocabulary. A gap driven by refusal
templates is a finding about templates.

## What this cannot answer

- **Whether the model learned it.** This is a property of the corpus. That a
  signal is present says nothing about whether DPO used it.
- **Anything causal about displacement.** M01 measured models; this measures
  text. A lexical signal here and displacement there is a correspondence, not a
  mechanism.
- **Other corpora.** hh-rlhf is one dataset with one annotation protocol. PKU and
  ultrafeedback are separate questions and are named in the subject README.
