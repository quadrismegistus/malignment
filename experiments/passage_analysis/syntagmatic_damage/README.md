---
id: syntagmatic_damage
status: RUN. The archived nulls were window-limited. With a 30-token window and probability controlled, movement predicts downstream surprisal in the ALIGNED arm only.
question: When a model is forced to utter a word alignment demoted, what happens to the sentence around it?
---

# syntagmatic_damage

**The finding lives here.** Nine measurements across four archived campaigns,
two substrates and two instrument families. They read as contradictory in
sequence and are not: they decompose.

    ARCHIVE SOURCES, all read in full 2026-08-23
      M01  W_forced_continuation.md
      M02  exit_markers_first_look.md sec. 3
      M04  A_post_utterance_shock.md
      M06  composition_not_level.md, f15_on_passages.md F3,
           self_surprisal.md S3/S4, propagation.md, offset_repair.md

# THE CLAIM

**Alignment installs a standing disposition about WHICH word to reach for. That
disposition is legible wherever the word appears, it is paid at the moment of
utterance, and it does not propagate into the chain.**

Selection is changed; combination is not. Both halves are measured.

## 1. The passage effect is composition, not level

`composition_not_level` Result 1, 36 pairs, self-surprisal, nats per word:

    Delta (aligned - base)   -1.2849
      composition            -1.3098      WHICH words appear
      level                  +0.0249      what they cost in context
      GATE R residual         0.0000

And the composition change IS M01's displacement, not a co-occurrence:

    net_fall        rho -0.285   36/36 negative   partial -0.276
    dir_when_moved  rho -0.269   36/36
    pct_moved       rho +0.008   18/36            NULL, exact chance

Direction predicts, volatility does not. `the` disqualifies itself
arithmetically rather than by hand.

## 2. The demoted word carries a charge, measured at matched probability

`composition_not_level` Result 4. 848,453 cells, 36 pairs, 203 prompts,
restricted to the band where fallers and risers coexist (log p_aligned
-2.464 .. -1.465):

    median(level | fall) - median(level | rise)
      base-generated      +0.3471   34/35 pairs   p 1.2e-10
      aligned-generated   +0.4435   35/35         p 5.8e-11

This is the separation `A_post_utterance_shock` declared impossible for want of
a matched corpus. It is obtained observationally: `p_aligned` is a continuous
covariate and the common-support band supplies the match. **45,901 fall cells
sit in bins holding zero risers**, so the contrast on common support is the
claim and the partial correlations are the weaker, extrapolating version.

Enabled by the `prompt_full` repair (560e44a2), which restored the join the
60-character prompt truncation had destroyed.

**The obvious deflation was tested and refuted.** If demotion generalised across
contexts while promotion did not, matching at one slot would leave the demoted
word lower everywhere else. Promotion is in fact the MORE consistent operation
(-0.0361, n=152 pairs, p 0.0027).

## 3. The charge is local -- four measurements, two substrates, one answer

    propagation             ~99% of an imposed word absorbed within a few tokens
                            slope ~+0.008 nats-per-bit
    A_post_utterance_shock  -0.04066 at +1, p 0.0018; NULL at every other index
    W damage family         four bounded nulls with stated MDEs
    wave-3 cost channel     dd +0.0144 p 0.0043, 19/24
    repair channel          flat

W's null and wave-3's small positive are a size disagreement, not a direction
one: both put the cost of forcing at about a twentieth of the resist asymmetry.

## 4. The result that looks like a contradiction, and is the decomposition

`f15_on_passages` F3b, third-party surprisal on the CONTINUATION:

    aligned  faller - matched          -0.0213  p 0.066   (n 4,198)
    base     faller - matched          -0.0337  p 0.0014  (n 4,263)
    aligned  riser_matched - matched   +0.0089  p 0.42
    base     riser_matched - matched   -0.0073  p 0.37
    drift, all four contrasts                   p 0.25 to 0.94

A forced faller makes what follows LESS surprising, and it is faller-SPECIFIC:
`riser_matched`, forced at the same aligned probability, is null in both arms.

**Set beside sec. 2 this is not a contradiction.** Two quantities at two places:

    THE WORD          costly to the aligned model     a standing disposition
    THE CONTINUATION  cheaper to everyone             corpus-typical context

A faller is a word the base prefers, hence corpus-typical, hence good context.
The charge sits on the signifier, not on the sequence.

## 5. Each arm is at home in the vocabulary it promoted

`self_surprisal` S3/S4, pair grain:

                 faller (base-preferred)      riser_matched (alignment-promoted)
    base         -0.0199  8/31  p 0.00029      +0.0012  21/18  p 0.749
    aligned      -0.0053 15/25  p 0.154        -0.0077  13/27  p 0.0385
    DiD          +0.0133        p 0.636        -0.0150         p 0.0166

A clean diagonal with both off-diagonal cells null. The riser half is
established as arm-specific and survived the typicality attack at [5796]; the
faller half's DiD is null at the pair grain, so "the base is soothed by fallen
words" is solid while its mirror is not.

**The first non-null DiD in the forced series after four nulls, and it is on the
PROMOTED side.**

# THE MEASUREMENT THIS FOLDER EXISTS FOR

Producer `run.py`, archive corpus `passage`, 42 lineage pairs, self-surprisal
only (`scorer = model`). Two models, both fitted WITHIN each lineage and
summarised across pairs with a sign test -- never pooled over rows, because row
counts differ several-fold between pairs and a pooled fit weights by data volume.

    M1  all rows       surprisal(w) ~ log p_gen            forced AND unforced
    M2  forced only    surprisal(w) ~ log p_gen + delta

`log p_gen` is the opening word's probability UNDER THE MODEL THAT WROTE IT
(`faller_q` etc. for aligned, `faller_p` for base). `delta = q - p`, the signed
movement. Unforced rows enter M1 with their own opening logprob as the dose and
scoring from the second word, which is `offset_repair`'s k=1 alignment; k=2 was
run as the sensitivity and agrees throughout.

## THE RESULT: two effects with different shapes, and only one is alignment-specific

M2, ALIGNED arm, median coefficient over 42 lineages:

    window     log p_gen                       delta
    +1      -0.04965  7/35  p=2e-5      -0.34843  20/22  p=0.88   <- NULL
    +10     -0.02479  3/39  p<1e-5      -0.38464   8/34  p=7e-5
    +20     -0.02257  3/39  p<1e-5      -0.34986  10/32  p=9e-4
    +30     -0.02312  3/39  p<1e-5      -0.34223  10/32  p=9e-4
    all     -0.01428  8/34  p=7e-5      -0.16595  11/31  p=0.003

**`delta` survives beside `log p_gen` in the same fit.** Direction is not
improbability under another name, and the effect is obtained WITHOUT discarding
the range where fallers and risers do not overlap.

**The two localise oppositely.** `log p_gen` is strongest at +1 (-0.0497) and
halves thereafter: an improbable opening costs you at the very next token.
`delta` is ABSENT at +1 (20/22, p=0.88) and appears from +10 through +30. How far
a word MOVED does nothing at the joint and everything in the clause that follows.

**And in the base arm `delta` is null everywhere:**

    +1   +0.05224  21/21  p=1.00      +20  -0.06450  16/26  p=0.16
    +10  -0.09791  17/25  p=0.28      +30  -0.05511  14/28  p=0.044
                                      all  -0.02117  18/24  p=0.44

`log p_gen` behaves the same in both arms (-0.02 to -0.10, significant
throughout). So the base model is sensitive to how improbable a word was and
INDIFFERENT to whether alignment moved it; the aligned model is sensitive to
both. The interaction is alignment-specific.

## WHY THE ARCHIVE FOUND NULLS HERE, AND WHY THAT IS NOT A CONTRADICTION

Each earlier instrument was blind to this region by construction:

    W damage family     10-token beams; bounded nulls with stated MDEs
    A_post_utterance    10 tokens IS the whole window -- "ten tokens is the
                        whole window; a repair or a return at token 30 is
                        invisible" (its own limits section)
    composition_not_level  the chain is held constant BY CONSTRUCTION, same
                        tokens scored twice; it says outright that it "could
                        not show damage if there were any"
    f15 F3b             faller vs matched, pooled over the whole passage,
                        third-party scorer, no probability term

**`delta` lives at +10 to +30 and is null at +1.** An instrument with a ten-token
window measures the one place the effect is not, and a whole-passage mean dilutes
it -- which is visible here as the `all` row being the weakest non-null in the
table (-0.166 against -0.385 at +10).

## MAGNITUDE, stated plainly

The coefficient is nats per unit of `delta`, and `delta` is a probability
difference. At the observed medians -- faller -0.0299, riser +0.0879 -- the
+10-token effect is:

    a typical FALLER   +0.0115 nats added to the following ten tokens
    a typical RISER    -0.0338 nats removed

Small in absolute terms and consistent in sign across 34 of 42 lineages. This is
a real effect at a scale the campaign's earlier MDEs could not have resolved on
ten tokens.

## WHAT THIS IS AND IS NOT

**It IS syntagmatic**: the outcome is the surprisal of the tokens that FOLLOW,
the chain is free to vary, and the effect is absent at the joint and present
downstream. That is the definition the charter used.

**It is not yet audited.** Single pass, one seat, OLS per lineage, no
second-seat reproduction. `delta` and `log p_gen` are correlated by construction
-- a word that fell has a low `q` -- so the two coefficients are not cleanly
separable in principle even though both survive here; a collinearity diagnostic
is owed before either magnitude travels.

**And the third-party question is untouched.** Everything above is
self-surprisal. Whether an outside reader (deepseek) sees the same downstream
effect is the fork this folder already names, and it is now a sharper question:
not "is the demoted word costly" but "does the clause after it read as
disturbed to someone who never trained on either arm".

# THE GAP, AND IT IS ONE GAP

**Every reference position used so far is inside the lineage or is GPT-2.**

`composition_not_level`'s level is `s_aligned(T) - s_base(T)` -- the parent as
comparison scorer. `gen_scores` holds 106 scorers and every one is a roster
model scoring its own pair's texts; there is no universal third party in it.
`f15` F3b used GPT-2 deliberately, as *"the only reference still independent of
the roster -- Pythia joined it"*, and GPT-2 is a 2019 124M model.

**Deepseek has never scored a forced passage.** `~/malignment-data/ref_pool/`
carries 13,124 deepseek-scored passages -- 3,000 human anchor, 5,687 model
narrative, 4,437 wrapper -- and no `forced_word` field.

**What a third-party pass would settle, and it is a real fork:**

    if the fall-vs-rise contrast at matched probability SURVIVES under deepseek
        the charge is in the TEXT: any competent reader registers it
    if it VANISHES
        the charge is a RELATION between a model and its own parent

Both are results. The second is the more interesting one for the argument and
neither is currently distinguishable.

## What it needs

    corpus      904,544 forced sequences in the archive's `gen_sequences`,
                1,457 distinct forced words, 198 prompts, 84 models,
                `prompt_full` present
    band        the common-support band is already characterised
    scale       F3b's GPT-2 contrast ran on ~4,200 cells per arm
    producer    `jakobson_space/ref_surprisal.py` writes the shard format
                the reference pool already uses

Not started. Sizing is the next step, not the run.

# WHAT MUST NOT BE CLAIMED FROM WHAT IS HERE

- **Damage to the chain.** sec. 2's instrument holds the chain constant by
  construction -- the same tokens scored twice -- so it registers DISAGREEMENT,
  not injury, and could not show damage if there were any. `propagation` is the
  instrument for that question.
- **A faller-side arm difference.** sec. 5's faller DiD is null at the pair
  grain. Only the riser half is established as arm-specific.
- **Forced versus undisturbed.** Ruled out twice independently ([5026] and
  Finding A) on two grounds: a commitment boundary and a one-token position
  offset. `offset_repair` measured that offset at 0.04-0.09 nats -- larger than
  the effect the affected finding reported -- and repairing it reversed every
  sign.
- **A p-value as a magnitude.** Four headline values across the M06 documents
  sit exactly on the sign test's floor, `p = 2/2^n`. Quote the sign counts.
