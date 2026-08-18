# UltraFeedback — does the disclaimer finding generalise?

**id:** ultrafeedback_disclaimer **status:** primary run; PKU does NOT replicate.
Aspect decomposition UNDECIDED by its own rule. Registration `4ca8323`, A1.

# 1. PKU DOES NOT REPLICATE, AND IT IS NOT A WEAKER VERSION

    TRAIN  all pairs          n=8,130   43.9%  [0.428, 0.449]  p=1.7e-28
    TEST   all pairs          n=  260   46.2%  [0.400, 0.524]  p=0.24
    |len diff| <= 20 words    n=  982   43.7%  [0.406, 0.469]  p=8.5e-05

    PKU, for comparison:      n=  550   68.4%   disclaiming judged SAFER

**68.4% against 43.9% is the other side of chance, not a smaller version of the
same effect.** The band label is UNDECIDED because 43.9% sits between the NULL
band and the REVERSES bar; *does PKU replicate* is answered NO without ambiguity.

**So the appended-frame preference is NOT general to preference annotation.** It
is a property of PKU, or of safety annotation, or of harmful-request contexts --
this cannot say which, only that it does not survive the move to a quality corpus
judged by GPT-4 against a written rubric.

## IT TRACKS THE SCORE MARGIN

    margin 0.0        n=1,007   46.6%
    margin 0.5-1.0    n=3,125   47.7%
    margin 1.5-3.0    n=2,608   43.4%
    margin 3.5-10     n=1,390   34.2%

## AND THE GENERATOR CONTROL PASSES -- AFTER THE THRESHOLD I DECLARED FAILED IT

    thresh   pairs   coverage   median   weighted
    n>=100       9     13.7%     20.9%     21.8%
    n>=50       48     45.9%     37.1%     36.0%
    n>=30      107     74.2%     40.9%     42.4%
    n>=10      209     97.7%     44.8%     43.7%
    n>=1       252    100.0%     47.1%     43.9%

The registration fixed `n>=100`, which selected 13.7% of the data, 38% of it
`gpt-4`/`gpt-3.5` against llama-2 variants -- the configuration guaranteed to
produce a low figure. **At n>=30 the weighted mean is 42.4% against a pooled
43.9%: the control passes.** Consistent with the model-level correlation between
win rate and E-ASSIST rate, which is +0.007, p=0.98 over 17 generators.

Real heterogeneity survives underneath: at n>=30 the per-pair spread runs min 0%,
p25 25.3%, median 40.9%, p75 69.1%, max 100%, and the disclaimer wins in 44 of
107 generator pairs.

# 2. THE ASPECT DECOMPOSITION: UNDECIDED, AND THE TWO ANALYSES DISAGREE

255,864 completions, 8.80% carrying E-ASSIST, four aspects rated separately.

                            WITHIN-MODEL      WITHIN-PROMPT     RAW
                            (registered)      17,462 prompts    255,864
    helpfulness               +0.075            -0.250          -0.087
    honesty                   +0.096            -0.110          -0.006
    instruction_following     -0.101            -0.522          -0.317
    truthfulness              +0.049            -0.317          -0.150

**Nothing clears the registered +/-0.15 on 12 of 17 models, so the rule returns
UNDECIDED.** Reported because the disagreement is the informative part.

**Within-prompt compares four completions from four DIFFERENT models**, so it
carries generator identity; within-model removes it. Control for the generator and
three of four aspects flip positive. Do not, and all four go down. Same defect
class as the `n>=100` threshold above and as CoCoNot's generator-fixed `pref`:
**third time today a stratification choice moved a sign.**

## THE ONE ROBUST ELEMENT

**`instruction_following` is negative in every specification and the largest
effect in every one.** A disclaimer is a departure from what was asked, and that
is the aspect the rubric docks. Nothing else survives the choice of control.

# WHAT THIS CANNOT SAY

- **Nothing about models.** 17 checkpoints cite this corpus across 11 bases; that
  is why it MATTERS, not evidence about their behaviour (A9).
- **Nothing about safety.** No harm labels here. That PKU's effect vanishes on a
  quality corpus does not make PKU's a quality effect.
- **The honesty result is not the humility story.** +0.096 within-model, -0.006
  raw. Essentially nothing, either way.
