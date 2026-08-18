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

---

## A1 — 2026-08-18. `lean` needs a count floor, and step D as written would find a spurious correlation. Amended before running.

`meta/M01_displacement/results/m01_token_counts.csv`, 685 tokens:

    lean = (as_riser - as_faller) / total          range [-1, +1]

    total: median 2, p25 1, p75 8, max 1228
    241 of 685 tokens have total == 1     -> lean is +/-1 BY CONSTRUCTION
    423 of 685 sit at exactly +/-1.0
    spearman(|lean|, total) = -0.632      -> THE EXTREME LEANS ARE THE RARE WORDS

**A logistic coefficient vector has the same pathology** -- unstable extremes on
low-count features. Correlating the two unfiltered would find agreement produced
by shared rarity in both vectors, not by shared direction. **That is a
correlation this design would have reported as a finding.**

    AMENDED D   spearman(w, lean) restricted to tokens with M01 `total` >= 10
                AND corpus count >= 100, and REPORTED AS A FUNCTION of the
                M01 floor (>=1, >=5, >=10, >=20) so the artefact stays visible.
                A correlation that only appears at low floors is the artefact.

    n at total>=10: 153 tokens (19 still at +/-1); at >=20: 94 (7 at +/-1)

**Also available and not previously used: the `vv` flag** (lexical verb, True on
448 of 685). P's own population is "English lexical verbs only, so part of speech
is not a confound", so `vv=True AND total>=10` (n=112) is the population closest
to P's and is reported alongside the unrestricted one.

**Sanity check on that population, recorded because it is the reason to trust the
vector at all:** its content matches V.6's caption independently.

    most falling  punched -1.00, stabbed -1.00, smashed -0.96, told -0.92,
                  cut -0.89, dropped -0.89, pushed -0.88, poured -0.83
    most rising   examined, whispered, stepped, submitted, used, scattered

Contact, motion and force on the falling side; perception, cognition and speech
on the rising side. That is `V_embedding_regions.md`'s axis caption, arrived at by
a different instrument. **`shattered` and `scattered` rise and are force verbs, so
it is not clean, and both sit at lean 1.00 i.e. low count.** Not over-read.

---

## A2 — 2026-08-18. Step D replaced: PREDICT preference from the model-side vector. RH's expectation recorded before the run.

RH's design, and it is stronger than the correlation it replaces: instead of
correlating two vectors, **use the model-side word vector as a zero-parameter
predictor of corpus preference.**

## RH'S RECORDED EXPECTATION, 2026-08-18, BEFORE ANY FIT

> **RH expects this to FAIL, or to PASS NARROWLY.**

Recorded as RH's because a prediction's author is part of its evidential status,
and because this seat's standing bias is inflationary.

**lacan's expectation: agrees, and for a specific reason with precedent.** The
model-side vector is built on the twp corpus -- FICTION CONTINUATIONS -- and the
preference corpora are assistant prose about laundering money. `pku-safe-rlhf`
A2 already recorded exactly this failure once: three bge refusal centroids scored
PKU responses further from themselves than generic English did, because "the
spans are erotic-fiction refusals, the responses are assistant prose about
bribery, and **the genre gap swamps the speech act**."

## THE INSTRUMENT REPLACING D, AND IT FITS NOTHING ON THE CORPUS

Source: `meta/M01_displacement/results/k/word_auc_en.tsv`, 4,106 words, producer
`meta/M01_displacement/scripts/k_word_auc.py`. **Chosen over `m01_token_counts.csv`
because that file has NO PRODUCER anywhere in the archive** (A1).

    weight(w) = (auc - 0.5) * sign(aligned_share - base_share)
                zeroed where auc <= 0.568   (the flipnull's own p90)
                n_models available as a reliability weight

    score(pair) = SUM over w of  weight(w) * [count(chosen) - count(rejected)]
    PREDICTION  the response with the higher score is the CHOSEN one

**No vocabulary selection, no tuning, no fitting on any corpus. Zero free
parameters**, so the held-out/train distinction does not arise and overfitting is
not available as an explanation of a hit.

`auc` IS A MAGNITUDE, NOT A DIRECTION -- the entire high-AUC tail is
aligned-leaning and the top "base-leaning" words sit at 0.50-0.51, i.e. noise.
The zeroing threshold exists to stop that noise entering as strong base-lean.

## THE CONFOUND THAT WOULD MAKE A HIT WORTHLESS

The strongest aligned-leaning words are `provide, provided, inform, express,
discuss, focus, avoid` -- **assistant register.** Those occur in assistant prose
by definition. **A hit driven by them is not "the same axis"; it is two
instruments both detecting formality.** So:

    REPORTED ALWAYS  the 20 words contributing most of the score, per corpus
    AND              the same test with the assistant-register words removed
                     (declared now: provide, provided, inform, express, discuss,
                     focus, avoid, ensure, assist, note, important, help)
    A hit that does not survive the removal is reported as REGISTER, not as axis.

## DECISION RULES

Applied to all five populations separately, never pooled.

    PASSES        >= 0.58 accuracy, binomial p < 0.01, AND survives the
                  register-word removal within 0.02
    NARROW PASS   0.53 to 0.58 with p < 0.01
    FAILS         < 0.53, quoted with the MDE

**RH predicted FAIL or NARROW PASS. This seat concurs. A clear PASS would be the
surprise, and it is the outcome to check hardest.**

---

## A3 — 2026-08-18. WITHDRAWN: "the vector has no negative pole". It was a one-tailed filter on a two-tailed statistic.

RH asked how there could be no base-leaning counts. There are 2,013.

`k_word_auc.py:227` is `roc_auc_score(y, C[:, j])` -- **auc is DIRECTIONAL**, and
the script's own effect form is `abs(auc - .5) > .15`. I filtered `auc > 0.568`,
deleting the whole base-leaning half, then **reported the absence as independent
corroboration of U_ladder's removal-stops gradient.** A filtering artifact
promoted to evidence for another finding, in the direction that flattered it.

`kill` is at auc 0.1115 on 92 models. Corrected weight is `auc - 0.5` two-sided;
`run.py:vector()` now carries a refusing assert, since the one-sided form
produced completely plausible output.

**The verdict is unchanged** -- 4 FAIL, 1 NARROW, RH's prediction holds -- but two
raw figures flip sign, so no number from the first run is citable.

**Also recorded, per RH:** everything until now ran through shell heredocs and was
not reproducible. All of it is in `run.py`. And the substrate is `twp_words`,
next-token probabilities at fixed sites, NOT generations -- so this test crosses
two grains and its null is weaker than a within-grain null would be.

---

## A4 — 2026-08-18. A3's grain objection is withdrawn: M06 measured the grain transfer and it holds. The limit is GENRE.

RH asked whether M06 ran a prediction pass over generations. It did.
`M06_generation/findings/p_on_passages.md`, 232,384 passages, 41 pairs: the
distributional ranking transfers to running text at Spearman **+0.500** (n=600)
and +0.444 (n=3,613), and a page classifier reaches 0.85-0.97 with a
real-minus-null-mean of 0.39-0.50 against a 200-flip null distribution.

**So `twp` -> running text is a solved transfer, and A3's "two grains" caveat was
wrong.** What this test crossed is genre: fiction continuations to assistant
prose. `pku-safe-rlhf` A2 recorded the identical boundary with a different
instrument -- bge refusal centroids sat further from PKU responses than generic
English did, "the genre gap swamps the speech act."

Restated null: **the alignment axis is legible across grains WITHIN a genre and
does not reach assistant prose.** It predicts where a transfer would work -- a
preference corpus of narrative text -- and none of the five populations is one.

M06's finding is draft/ungraded/single-pass and is quoted with that fence.
