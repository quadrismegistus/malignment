---
kind: question
id: corpus_predicts_movement
question: Does the direction a preference corpus rewards predict the direction alignment actually moved the model it trained?
status: "RUN 2026-09-07. NULL: the norm-space direction PKU rewards does not predict how alignment moved the model PKU trained -- treated indistinguishable from a placebo stage and from 49 untouched lineages. BUT the channel is narrow: the 7 norm dims reach AUC 0.581 where unigram reaches 0.714, so the null bounds little."
headline: "beta is real and length-independent (AUC 0.581 vs null 0.500) and its largest term is CONCRETENESS, which this folder predicted would be absent. The projection onto it is null at every rung. The ablation is the finding: unigram reaches 0.714, so PKU's preference signal is lexical rather than norm-shaped and the transfer ran through the wrong channel."
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
