# Registration — does PKU's disclaimer finding replicate on UltraFeedback?

**Frozen 2026-08-18, before the outcome test is run.** Availability was measured
first and is reported below; the paired test is NOT run. Population chosen by RH.

## The question

PKU: where two responses both comply and one appends a moral or legal frame, the
disclaiming one is judged safer 68.4% of the time, and the frame's content does
not matter (OPERATIONAL at chance). **Is that a property of one dataset, or of
how preference annotation works?** UltraFeedback is the strongest available test:
61,135 pairs, 17 roster checkpoints across 11 distinct bases, 12 rated `high`
confidence -- against PKU's 2 checkpoints and 2 bases.

**AND THE ANNOTATOR IS DIFFERENT IN KIND.** PKU is human + AI in an undisclosed
mix. UltraFeedback is GPT-4 against a written rubric. If the effect appears in
both, it is not about crowdworkers; if it appears in neither, PKU's is local.

## AVAILABILITY, measured before the design was fixed

    marker      chosen   rejected   DIFFERS on
    E-ASSIST     7.32%      8.96%   8,130 of 61,135  (13.30%)
    REFUSAL      0.99%      1.55%   1,482            ( 2.42%)

    PKU both-unsafe:                  550 of 32,656  ( 1.68%)  E-ASSIST
                                        7            ( 0.02%)  REFUSAL

**REFUSAL HAS VARIANCE HERE AND DID NOT IN PKU.** RH's H1 -- safety clusters on
declining rather than mildness -- died on PKU as a scope fact at n=7. At n=1,482
it is askable, on a helpfulness corpus rather than a safety one. Reported
SEPARATELY from E-ASSIST and never pooled (M02's rule).

## POPULATION (RH): ALL PAIRS. CONTROL: GENERATOR-STRATIFIED.

    PRIMARY   train_prefs, pairs where exactly ONE response matches E-ASSIST
              n = 8,130.  Test split reported separately, never pooled.
    QUESTION  is the disclaiming response the CHOSEN one?
    TEST      two-sided binomial against 0.5

**The control is stratification, not matching.** Each prompt has four completions
from four DIFFERENT models, so chosen and rejected are never the same generator
and a matched design is impossible. Join to `openbmb/UltraFeedback` on completion
text recovers the model for both sides at **100% coverage on a 4,000-row sample**,
17 distinct generators.

    CONTROL   for each ordered generator pair (M1,M2) with n >= 100, compute the
              same statistic. Report the MEDIAN across pairs and how many run
              each way. If the pooled figure is generator identity wearing a
              disclaimer costume, the per-pair medians will not agree with it.

Declared because CoCoNot's `pref` was voided by exactly this: `chosen_model` was
gpt-4 on 927 of 927 rows, so its 10.4% measured which generator hedges, not what
was preferred.

## DECISION RULES, AS ARITHMETIC, AND TWO-SIDED

PKU's rules were one-sided in conception and CoCoNot produced a reversal that had
no home in them. Not repeated:

    REPLICATES     disclaiming chosen >= 0.60, binomial p < 0.01
    REVERSES       disclaiming chosen <= 0.40, binomial p < 0.01
    NULL           0.45 to 0.55, quoted with the MDE
    UNDECIDED      anything else

    SURVIVES CONTROL   the generator-pair median falls in the same band as the
                       pooled figure. Otherwise the finding is about generators.

## CONFOUNDS DECLARED NOW, BECAUSE LENGTH HAS BITTEN TWICE TODAY

    LENGTH   report the effect on pairs matched to |len diff| <= 20 words, and
             report whether the longer response is the chosen one. PKU's mildness
             arm survived every check except this and then died on it.
    SCORE    `score_chosen - score_rejected` is available. Report the effect
             within score-margin bands; a disclaimer effect that is really a
             quality effect will track the margin.

## WHAT THIS CANNOT SAY

**Nothing about models.** A9 stands: a dataset and a model are different objects,
and 17 checkpoints citing this corpus does not make their behaviour derivable
from it. The checkpoint count is why the corpus MATTERS, not evidence about them.

**And nothing about safety.** UltraFeedback is a quality corpus with no harm
labels. A replication here says the preference is general to preference
annotation; it does not say PKU's safety finding was really a quality finding.
