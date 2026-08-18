# Registration — is there a lexical axis in preference data, is it the SAME axis, and can it be named?

**Frozen 2026-08-18, before `run.py` exists.** RH's design: one prediction pass
over every preference corpus we hold, with dataset identity handled as a unit of
analysis rather than as a nuisance.

## Why this and not more per-corpus studies

Four corpora have now been studied with four different populations and four
different tests, which is why their results cannot be set against each other
except by argument. **One instrument, applied identically, makes the corpora
comparable by construction.**

And it recovers something already fitted and thrown away: `pku-safe-rlhf/run.py
--h3` fits a 13,820-term model on `safer` across 73,907 pairs, reports AUC 0.6831
and **discards the coefficient vector**. That vector is the object of this study.

## THE PRINCIPLE FOR HANDLING DATASET AS A CONFOUND

**Rows are NEVER pooled across corpora.** Each corpus is fitted on its own
vocabulary and its own split. What is compared is the resulting COEFFICIENT
VECTORS. Dataset identity therefore cannot leak into a model as a feature,
because no model ever sees two datasets.

## POPULATIONS -- five, stated by column, never pooled

    hh-harmless   Anthropic/hh-rlhf default-52e03caf22ec705f   42,537 pairs
    hh-helpful    Anthropic/hh-rlhf default-cfba128a0ab1b99f   43,835
    pku-unsafe    PKU both-unsafe (is_response_N_safe both False)  32,656
    pku-mixed     PKU is_response_0_safe != is_response_1_safe    10,813
    ultrafeedback HuggingFaceH4/ultrafeedback_binarized train_prefs 61,135

Three source corpora, THREE ANNOTATION REGIMES: human (hh), human+AI undisclosed
(PKU), GPT-4 against a rubric (UltraFeedback). That spread is the point.

CoCoNot `pref` is EXCLUDED: `chosen_model` is gpt-4 on 927 of 927 rows, so its
label is generator identity. Recorded so the absence is not read as an oversight.

## THE INSTRUMENT, IDENTICAL EVERYWHERE

    features   count(chosen) - count(rejected) over a min_df=20 vocabulary fit
               on that corpus's TRAIN split only
    label      which response the column names, SIGN-RANDOMISED at seed 20260818
               so a constant cannot beat 0.5
    model      logistic regression, liblinear, C=1.0
    outputs    AUC on the held-out split, and the coefficient vector w

## THE FOUR QUESTIONS

    A  IS THERE AN AXIS      AUC_match per corpus, |len diff| <= 5
    B  IS IT THE SAME AXIS   spearman(w_i, w_j) over vocabulary shared by both
    C  CAN IT BE NAMED       do K's seven rated norms predict w, HELD OUT BY WORD?
                             This is P_unnamed_axis.md's test, run on corpora
                             instead of models. P found NONE of eighteen norms
                             predicts movement direction in models.
    D  IS IT DISPLACEMENT    spearman(w, M01's signed `lean`) over shared tokens

**D is a comparison of two vectors over words, NOT a claim that one produced the
other.** It needs no model to have trained on any of these corpora, which is why
it survives A9's category objection when yesterday's model-level attempt did not.
**And the confound that barred it on hh-rlhf is controlled on `pku-unsafe` by
construction**: transgressive words appear when a response ENGAGES, and there both
responses engage.

## CONFOUNDS, EACH WITH ITS HANDLING STATED

**LENGTH. It has killed two findings in two days and is assumed guilty.**
Every corpus reports AUC_words, AUC_len, AUC_match, and **w is refit on the
length-matched subset**. If the matched and unmatched vectors disagree
(spearman < 0.5), the axis is length and is reported as such.

**GENERATOR.** Recoverable at 100% for UltraFeedback by joining
`openbmb/UltraFeedback` on completion text; PKU names `response_N_source`;
hh-rlhf does not name a generator at all. **Where recoverable, w is refit within
generator strata. Where not, it is declared UNHANDLED for that corpus** rather
than assumed absent.

**ENGAGE vs DEFLECT.** hh-rlhf's axis is engage-versus-deflect and INVERTS
between its arms. That is a property of those two populations and is reported
with every hh number, never controlled away.

**FORMATTING ARTEFACTS.** hh-rlhf's top chosen-side features were `https, http,
html`. **The top 30 features per corpus are printed VERBATIM before any
interpretation**, with markup, URL and whitespace tokens flagged.

## DECISION RULES -- and every raw value is reported whatever the verdict

Thresholds are for the headline only. Today two registered bars were set without
any estimate of plausible effect size and returned UNDECIDED on live data; these
are anchored to observed values instead -- hh-rlhf reached AUC 0.624-0.668, and P
recovered 18-21% of its headroom with GloVe against the rated norms' 7%.

    AXIS PRESENT    AUC_match >= 0.60 held out
    SAME AXIS       spearman(w_i, w_j) >= 0.30, p < 0.01
    NAMEABLE        any single K norm reaches spearman >= 0.20 with w, held out
                    by word. **If none does, that is P's result on corpora.**
    IS DISPLACEMENT spearman(w, lean) >= 0.20, p < 0.01

## WHAT THIS CANNOT SAY

Nothing about models (A9). Seventeen checkpoints cite UltraFeedback and two cite
PKU; that is why the corpora matter, not evidence about the checkpoints. **D, if
positive, says the same lexical axis is legible in both places -- not that the
corpus put it there.** U_ladder's ablation is the standing reason to expect it
did not.
