---
kind: question
id: corpus_predicts_movement
question: Does the direction a preference corpus rewards predict the direction alignment actually moved the model it trained?
status: "RUN 2026-09-07, both channels. The per-word transfer is the result: a PKU-learned word score predicts alignment movement in 47 of 49 lineages PKU NEVER TOUCHED (p=4.4e-12) and predicts the PKU-trained model least well (percentile 10), which is not movement magnitude (checked). The direction is generic to alignment, not transmitted from this corpus."
headline: "A direction learned from PKU is recovered by essentially every aligned model and LEAST by the one PKU trained -- a model tuned on a different preference corpus scores eight times higher on PKU's own direction. The refusal/disclaimer register is convergent across alignment procedures, not an echo of one dataset. Within the ladder the move sits at SFT, where U_ladder puts the cutting."
grain: lineage
---

# corpus_predicts_movement

**Nothing has been measured.** This file states a design and the machinery it
reuses, so that a run starts from what is already built.

## THE QUESTION

`displacement/norm_change` finds that alignment moves the continuation
distribution along word norms, and its own MARGINAL/DOSE split sorts those moves
into two shapes: **MARGINAL ONLY** (`k_register_level`, +0.0063 p<1e-5, dose
p=0.67 -- "a global stylistic shift, not a safety behaviour") and **DOSE ONLY**
(`k_concreteness`, `warriner_dominance`, `k_charge` -- flat on average, steep
where the frame is loaded).

RH, 2026-09-07: which of those are **direct echoes of the posttraining data**,
and which are **emergent**?

**That is not answerable by inspecting model behaviour alone**, and it is not
answerable by comparing vendors, which confounds data with family, size and
recipe. It needs a lineage where the posttraining corpus is KNOWN, and a
contrast that varies the corpus while holding the model fixed.

## WHY IT IS ANSWERABLE HERE AND ESSENTIALLY NOWHERE ELSE

`../README.md` already says it: *"PKU is the one that matters, because it is the
only cached corpus that TRAINED MODELS WE MEASURE."* This is that sentence's
experiment.

**And the intermediate rung is in the store**, which turns a single contrast into
a placebo design:

    huggyllama/llama-7b
        |  SFT on Alpaca data -- PKU IS NOT INVOLVED      430,735 rows
        v                                                  <- PLACEBO STAGE
    PKU-Alignment/alpaca-7b-reproduced
        |  Safe RLHF on PKU-SafeRLHF                      548,577 rows
        v                                                  <- TREATED STAGE
    PKU-Alignment/beaver-7b-v1.0

    llama-7b -> beaver-7b-v1.0 (the declared endpoint pair) 548,831 rows

All three are in `movement_v4` at 2,983 prompts each, verified 2026-09-07. The
placebo stage holds family, size, tokenizer and prompt set fixed and varies only
WHICH CORPUS WAS APPLIED. Nothing else in this campaign offers that.

## THE DESIGN

**1. Learn the direction the corpus rewards.**

`../pku-safe-rlhf/run.py` already builds it. `k_ranks()` gives every K dimension
as a percentile rank over the lexicon (never a level -- see its docstring), and
`features()` returns `kA - kB`, the difference in mean K-rank profile between the
two responses of a pair. Fit `auc()`'s logistic regression on that with
`safer_response_id` as the label. **The coefficient vector is beta: the direction
in norm-space that this annotation regime rewards.**

**2. Project each stage's movement onto beta.**

`norm_change` computes, per (lineage, prompt), a mass-weighted mean of each norm
over the rated words -- a norm profile of a distribution. The PKU feature is a
norm profile of a text. **Same functional form, differenced between two arms in
both cases**, which is what makes the transfer legitimate rather than a
re-description.

**3. The contrast.**

    TREATED   alpaca-7b-reproduced -> beaver-7b-v1.0    trained on PKU
    PLACEBO   llama-7b -> alpaca-7b-reproduced          not trained on PKU
    SPAN      llama-7b -> beaver-7b-v1.0                both stages
    CONTROL   the other 49 endpoint pairs               PKU never touched them

**An echo predicts the treated stage projects onto beta and the placebo stage
does not.** If both project equally, beta is a generic alignment direction and
there is no PKU-specific echo. If neither does, the corpus's preference direction
does not reach the continuation distribution at all, which is also a result.

## PREDICTIONS, TO BE RECORDED BEFORE THE RUN AND NOT AFTER

From `norm_change`'s three shapes:

- **MARGINAL ONLY effects are the echo candidates.** beta should load on
  `k_register_level`, and the treated stage should project positively.
- **DOSE ONLY effects are the emergent candidates.** beta should NOT load on
  `k_concreteness`, `warriner_dominance` or `k_charge`, and the projection should
  show **no dose slope** against `charge.lift_per_lineage`.
- If beta loads on the DOSE ONLY scales, the emergent reading is WRONG and this
  file should say so.

## FEATURES

    PRIMARY     the K-rank profile (`kvec` in ../pku-safe-rlhf/run.py).
                Already implemented. This is "word counts x norms": the mean
                percentile rank over the lexicon-covered words of a text.
    COVARIATE   LENGTH, never a feature. That folder's own finding is
                "helpfulness is length"; as a feature it leaks the label.
    ABLATION    unigram bag-of-words. If unigram beats the norm profile
                substantially, the corpus's signal is NOT norm-shaped and the
                transfer into norm_change's currency is lossy. That is worth
                knowing whichever way the main test lands.
    AVAILABLE   `refusal` and `eassist` marker counts, already built.

**A SHARED-INSTRUMENT HAZARD, STATED BEFORE IT BITES.** Both sides use the same K
lexicon. A blind spot in it fails on both sides at once and would look like
agreement. The unigram ablation is a partial guard; a second lexicon would be a
better one and is not budgeted.

## CHARACTERISE THE NULL BEFORE READING ANY NUMBER

`passage_analysis/predicting_aligned_text` records what happens otherwise:
`p_on_passages`'s I2 **was wrong in its first two versions** because the flip
assignment iterated an unsorted set -- one seed gave 0.52-0.63, the next
0.40-0.49, and both were quoted as findings when neither an elevation nor a
depression existed. **A one-flip null at 41 lineages wobbles +-0.15.** The same
defect independently cost `displacement/displacement_axis` a full day.

`randomise()` in the sibling folder is the null generator. Run it first, report
real-minus-null, and never quote a raw AUC.

---

# THE RESULT (2026-09-07): NULL, AND THE CHANNEL IS TOO NARROW TO CLOSE IT

## PHASE 1 -- BETA IS REAL, AND IT IS NOT LENGTH

    safer_response_id, n=73,907 pairs, 70/30 split
      AUC real 0.5811 | null mean 0.5000 sd 0.0041 | REAL MINUS NULL +0.0811

The null was characterised first (200 label permutations) and the effect is ~20
null-sds. The direction:

    concreteness        -4.198        bodily_harm        -1.398
    register_level      +2.735 [rep]  valence            +1.372
    charge              +1.856        transgressiveness  +0.758
    vulgarity           -1.658 [rep]

`[rep]` = REPORTED ONLY, never evidence, per `../pku-safe-rlhf/`'s fence on
`register_level` (IAA 0.597) and `vulgarity`.

**And it is not the length confound**, which had to be checked because this
README made length a covariate and then phase 1 fitted without it:

    length only                  AUC 0.5651
    K profile only               AUC 0.5811
    K + length                   AUC 0.6040
    K RESIDUALISED on length     AUC 0.5805    <- costs 0.0006

Residualising K on length costs essentially nothing and the coefficients are
unchanged, so beta is a length-independent direction.

## THE PREDICTIONS, AND ONE IS REFUTED

Recorded above before the run:

- **"beta should load on `k_register_level`"** -- it does, +2.735, second
  largest. But `register_level` is REPORTED-ONLY here, so this is an
  observation and not a result. Scored as neither.
- **"beta should NOT load on `k_concreteness`"** -- **REFUTED.**
  `concreteness` is beta's LARGEST coefficient at -4.198, and the sign agrees
  with `norm_change` (the corpus prefers less concrete; alignment reduces
  concreteness under dose). On the corpus side concreteness is the most
  echo-shaped dimension there is, and it is the one this file predicted would
  be absent because `norm_change` classes it DOSE ONLY.

## PHASE 2 AND 3 -- THE PROJECTION IS NULL

700 prompts, projection of each stage's norm-profile movement onto beta:

    stage      edge                                    n   median     up/dn      p
    PLACEBO    llama-7b -> alpaca-7b-reproduced      700  -0.0152   329/371   0.12
    TREATED    alpaca-7b-reproduced -> beaver-7b     700  -0.0079   327/373   0.089
    SPAN       llama-7b -> beaver-7b-v1.0            700  -0.0242   326/374   0.076

    PAIRED DiD, TREATED minus PLACEBO, per prompt
      n=700  median +0.0074  mean +0.0004  367/333  sign p=0.212  Wilcoxon p=0.715

    CONTROL   49 endpoint pairs PKU never touched
      median-of-medians +0.0002, 25 up / 24 dn, p=1
      TREATED sits at percentile 35 -- BELOW the median untouched lineage

**The direction PKU rewards does not predict how alignment moved the model PKU
trained.** The treated stage is not distinguishable from the placebo stage that
never saw PKU, and it is not distinguishable from lineages PKU never touched.
All three rungs drift slightly AGAINST beta and none significantly.

## BUT THE CHANNEL IS TOO NARROW FOR THAT NULL TO CLOSE THE QUESTION

    K-rank profile (7 dims)      AUC 0.5811
    UNIGRAM tf-idf difference    AUC 0.7135

**The ablation this README specified is the most important number here.** A bag
of words recovers far more of PKU's preference structure than the seven norm
dimensions do. So the corpus's signal is substantially LEXICAL and not
norm-shaped, and the transfer was carried through a channel that explains a
minority of it.

**The correct reading is therefore narrow: the NORM-SPACE COMPONENT of PKU's
preference direction does not reach the continuation distribution.** It is not
"the corpus does not predict the movement", and it must not be quoted that way.
A null through a channel this narrow bounds very little.

## THE FOLLOW-UP THIS POINTS AT, NOT RUN

Learn a **per-word log-odds** from PKU -- the unigram model's coefficients --
and correlate it with the per-word `delta` in `movement_v4` on the same three
rungs. That uses the 0.71 channel instead of the 0.58 one, and it matches grain
exactly: a per-word corpus score against a per-word mass change. The word-level
movement data is already there and needs no new rating.

That is the version of this test worth believing, and this one is its
underpowered first pass.

---

# THE PER-WORD TRANSFER (2026-09-07): THE DIRECTION IS GENERIC, NOT TRANSMITTED

`word_transfer.py`. The follow-up the section above specified, run: a word's PKU
preference score against that same word's mass change in `movement_v4`. One
grain, no profile averaging on either side, and the 0.71 channel instead of 0.58.

## THE SCORE

Z-scored log-odds of appearing in the SAFER response, 14,117 words at count>=20.
**Raw log-odds was tried first and discarded**: its extremes were all rare
technical nouns (`sumac`, `digitalis`, `hellebore` one way; `eyedropper`,
`dichromate` the other), because a log-odds at count 20 is mostly sampling
noise. Dividing by the standard error fixes it, and the result is legible:

    SAFER : cannot, serious, is, not, advisable, unfortunately, we, instead,
            legal, result, consequences, sorry, health, respect
    OTHER : them, fake, using, false, then, use, include, by, trioxide,
            accounts, tag, like, create, one

That is the disclaimer register `../pku-safe-rlhf/` established, recovered
independently at word grain.

## THE RESULT

Per-prompt Spearman between a word's PKU score and its delta, 900 prompts:

    rung           n    med rho      up/dn           p   med resid
    PLACEBO      890    +0.0390   595/295     4.5e-24     +0.0266
    TREATED      890    +0.0155   506/384     4.9e-05     +0.0103
    SPAN         890    +0.0419   604/285     4.1e-27     +0.0276

    CONTROL   49 endpoint pairs PKU never touched
      median-of-medians +0.0497, 47 up / 2 dn, p=4.4e-12
      TREATED +0.0155 is above only 5 of 49 -- percentile 10

**The PKU score predicts alignment movement almost everywhere, and predicts the
PKU-trained model least well.** 47 of 49 lineages that never saw this corpus
move in its direction. The one it actually trained sits in the bottom decile.

`med resid` is the same statistic after regressing `log p_base` out of both
sides: the effect keeps about two thirds of its size, so it is not word
frequency read twice.

## AND IT IS NOT THE MOVEMENT MAGNITUDE

The TREATED rung is much the smallest move -- `sum|delta|` 743 against PLACEBO's
1551, median |delta| 0.00023 against 0.00094 -- so its lower rho had to be
checked against attenuation before anything was claimed:

    Spearman(sum|delta|, rho) over the 49 controls = +0.159, p=0.275
    controls with sum|delta| < 1200 (matched to TREATED's 743):
        n=22, median rho +0.0496      TREATED +0.0155

**Magnitude does not predict rho, and among magnitude-matched lineages TREATED
is still far below the median.** The check strengthened the reading instead of
dissolving it.

One case makes the point on its own: `pythia-6.9b -> eleuther-pythia6.9b-hh-dpo`
moves HALF as far as the treated rung (`sum|delta|` 376) and scores rho +0.1244,
the highest in the low-magnitude group. **A model tuned on a DIFFERENT preference
corpus scores eight times higher on PKU's own direction than the model PKU
trained.**

## THE TARGET WAS WRONG AND THE CORRECTION MAKES IT BIGGER

RH, 2026-09-07: *"Why are we predicting labelled UNSAFE?"* The first run scored
on `safer_response_id` pooled over all 73,907 pairs, and that is a RELATIVE
preference:

    both UNSAFE   32,656   44.2%   "safer" = the LESS BAD harmful response
    both safe     30,438   41.2%   "safer" = style, not safety
    mixed         10,813   14.6%   "safer" = the safe one

**85% of the signal was within-safety-class comparison**, which is why reading
the passages found harmful compliances on the "safer" side -- a cyberbullying
manual scoring on `consent` because it says *"without their consent"*, a drug
distribution plan scoring on `illegal`.

Three targets were built and compared (`--score`):

    A pooled    cannot, serious, not, advisable, unfortunately, legal, sorry
    B absolute  waste, i, local, animal, health, food, energy, medical, pet
    C mixed     cannot, is, not, illegal, unfortunately, serious, instead, sorry

    corr  A vs C +0.739 | A vs B +0.565 | B vs C +0.650

**B, the obvious fix, is the worst of the three.** Pooling responses by their
absolute label compares answers to DIFFERENT PROMPTS, so it learns subject
matter: pets, recycling, food, energy. It is kept selectable only so that defect
can be reproduced.

**C is the clean target and is now the default**: the two responses answer the
SAME prompt and exactly one is labelled safe, so topic is controlled by
construction.

### THE RESULT UNDER THE CLEAN TARGET

    rung           n    med rho      up/dn           p
    PLACEBO      890    +0.0690   662/228     9.8e-50
    TREATED      889    +0.0191   507/382     3.1e-05
    SPAN         890    +0.0690   648/242     1.7e-43

    CONTROL  49 lineages, median-of-medians +0.0612, 46 up / 3 dn, p=7e-11
             TREATED is above 5 of 49 -- percentile 10, unchanged

Every effect grows (placebo +0.0390 -> +0.0690, control median +0.0497 ->
+0.0612) and the conclusion is unchanged: **the score predicts alignment
movement broadly and predicts the PKU-trained model least well.** The
mis-specified target was costing power, not manufacturing the result.

## WHAT THIS ANSWERS, AND WHAT IT DOES NOT

**Answers RH's question for this trend: it is not an echo of the specific
posttraining data.** A direction learned from PKU is recovered by essentially
every aligned model in the roster, including 47 that never saw it. Whatever
installs the refusal/disclaimer register is convergent across alignment
procedures, not transmitted from one corpus.

**It does NOT show the direction is uninherited from data in general.** The
score is close to "disclaimer register versus instrumental register", which is
plausibly what EVERY alignment corpus shares. "Not traceable to THIS corpus" and
"not learned from data" are different claims and only the first is supported.

**And within the ladder the move sits at SFT, not at the PKU stage** -- PLACEBO
+0.0390 against TREATED +0.0155, with SPAN (+0.0419) barely above PLACEBO. That
is the same place `U_ladder` puts the cutting.

## WHAT THIS CANNOT ESTABLISH

- **n = 1 lineage.** It tests the MECHANISM, not its prevalence. The other 49
  pairs are a control on beta's genericness, not four dozen replications.
- **ONE ANNOTATION REGIME.** `../pku-safe-rlhf/` establishes what PKU's labels
  actually reward -- the disclaimer effect at 68%, helpfulness is length, the
  mildness bundle. beta inherits every one of those properties. A positive result
  says the model moved toward what THESE annotators rewarded, not toward
  "safety".
- **Preference data is one stage.** PKU is the Safe RLHF corpus. The Alpaca SFT
  data that made the placebo stage is not analysed here, so a null on the placebo
  stage means "not PKU's direction", not "no corpus echo".
- **`AmberSafe` is not a second case.** Its card says DPO on PKU-SafeRLHF alone
  and the paper says ShareGPT-90K SFT plus a SafeRLHF DPO stage;
  `roster/models/attestations.json` records the contradiction. Do not treat
  `Amber -> AmberSafe` as a replication without resolving that first.

## WHAT WOULD MAKE THIS FOLDER STALE

Written because `instrument_calibrations/frame_pilot` sat at "DESIGNED, NOT RUN"
for weeks while its question was answered elsewhere, and its status read as an
opportunity.

**This folder is superseded if** anyone establishes, by any route, whether the
norm-space direction alignment moves in is recoverable from its training corpus.
If that happens, retire this and point at it. The design is not precious; the
placebo rung is the only part hard to come by.
