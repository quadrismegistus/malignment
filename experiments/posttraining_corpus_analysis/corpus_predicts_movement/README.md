---
kind: question
id: corpus_predicts_movement
question: Does the direction a preference corpus rewards predict the direction alignment actually moved the model it trained?
status: "DESIGNED, NOT RUN, 2026-09-07. Nothing measured. The three rungs and both feature paths are verified present; see FEASIBILITY."
headline: NONE STATED -- the design is written, nothing has been run.
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
