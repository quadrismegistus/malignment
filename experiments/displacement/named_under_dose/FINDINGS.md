# P's question conditioned on dose: the answer is no, and the reason is grain

**Read this file rather than the run logs.** Three earlier versions of these numbers
were confounded or leaking and are listed at the bottom with what was wrong. The
table below is the first uncontaminated, uniformly-covered run.

    POPULATION   `movement` over roster.endpoints() (50 pairs), cls != 'still',
                 CONTENT words at the slot via pos.get_pos -- not verbs-only.
    RATINGS      108,575 contextual pairs commissioned this session, coverage
                 UNIFORM in dose (low 67.8%, high 68.9%).
    UNIT         the word. GroupKFold, so no word is in both fit and test.
    METRIC       P's: each model minus ITS OWN SHUFFLE. 5 tree draws, range shown.

## 1. THE DOSE ANSWER IS NULL, FOR EVERYTHING

                       LOW dose                  HIGH dose
    ctx_v6/trees   +0.0964 [.0871,.1065]    +0.0875 [.0801,.0974]    overlap
    norms/trees    +0.0340 [.0151,.0551]    +0.0609 [.0392,.0733]    overlap
    glove/trees    +0.0716 [.0516,.0993]    +0.0858 [.0699,.0999]    overlap
    bge/trees      +0.0907 [.0729,.1056]    +0.0813 [.0688,.1011]    overlap
    shared cells      57,204                   62,502

**The named vocabulary does not predict direction better or worse where the frame
carries transgressive mass.** No model's draw ranges separate between strata.

This folder was built to ask whether P's 7% was a MARGINAL 7% concealing a
conditional effect. It was not. P's result stands as measured.

## 2. WHAT DOES HOLD: GRAIN, NOT VOCABULARY

    ctx_v6 vs word-level norms      LOW 2.8x [disjoint]   HIGH 1.4x [disjoint]
    ctx_v6 vs embeddings            LOW  ctx .0964  glove .0716  bge .0907
                                    HIGH ctx .0875  glove .0858  bge .0813

Word-level norms sit near the floor. **The SAME twelve scales asked AT THE SITE
reach 1.4-2.8x that, ranges disjoint at both strata** -- and match GloVe and bge
rather than trailing them.

So P's **"the unnamed residual outpredicts every name we have tried"** is true at
WORD grain and dissolves at SITE grain. The names catch the embeddings; they never
overtake. The descriptive vocabulary was not inadequate -- it was being asked one
question per word when the phenomenon is one question per site, which is exactly
what P's own ICC of 0.131 predicts: 82-87% of the fall/rise variance is WITHIN a
word across the sites it appears at, and no constant-per-word feature can reach any
of it.

Chinese replicates the grain finding on its own instrument (`v6zh`): pooled ctx
+0.0889 [.0843,.0952] against word-level +0.0348 [.0136,.0664], 2.6x, disjoint.

## 3. WHY norm_change FINDS A HUGE DOSE EFFECT AND THIS FINDS NONE

They measure different quantities and both are right.

    norm_change/dose.py   x = base-arm k_transgressiveness at the prompt
                          y = aligned - base on the TARGET scale, a LEVEL SHIFT of
                              the mass-weighted mean
                          OLS slope, sign test over 50 lineages, nothing held out

    here                  outcome = which way an INDIVIDUAL word moved, +1/-1
                          held-out AUC, low stratum against high

**`norm_change` asks how far the distribution slides along a named scale. This asks
how well a word's ratings say which way that word goes.** Dose can scale the AMOUNT
of movement without changing its SORTABILITY: if a loaded frame pushes every word
further down concreteness, the mean moves much more (p=1e-5) while which particular
words rise stays exactly as predictable (AUC flat). Turning up the volume does not
make the signal easier to classify.

Three differences all push the same way: unit (50 lineages vs held-out words),
fitted vs held-out, and aggregate vs individual -- the last being the same
distinction P's ICC names.

## 4. THREE EARLIER VERSIONS, AND WHAT WAS WRONG WITH EACH

- **"norms 8% -> 40% under dose".** Unoriented `log p_base` floor: scored raw it
  returns AUC 0.4151, ANTI-predictive, which inflated the headroom 2.8x. Also an
  all-words population where the norms partly proxy POS. Both fixed; the effect
  did not survive either.
- **"ctx beats bge at low dose" (Chinese).** LEAKAGE. `consistency` -- the share of
  a pair's lineages agreeing on direction, a function of the outcome -- was written
  as a numeric field, and `_slot_index` treats every numeric field as a scale, so it
  became a predictor. Worth ~+0.018, which was the whole apparent win. Clean it is
  a tie.
- **"ctx gets WORSE under dose".** Coverage was correlated with dose, because tier 2
  commissioned 34,304 pairs at top-quartile dose and coverage became 21.8% low
  against 63.6% high. Selecting on the variable you then condition on. The uniform
  63,815-pair pass removed it and the effect vanished.

A fourth, structural: **`--verbs-only` deleted prompts rather than thinning them.**
451 of 2,612 en prompts and 56 of 407 zh are under 20% verbs -- the salary probes,
the Chinese anatomical slots -- and 111 already-rated en prompts were in that group.
It also destroyed a diagnostic: restricting to prompts rated before any dose-based
selection kept 2 of 1,815.

## 5. WHY THE CEILING IS LOW: DIRECTION IS MOSTLY MODEL-SPECIFIC

Added 2026-08-30. The existence test (`experiments/displacement/existence/`) shows
higher-scene words lose more mass (40/50 lineages, p=2e-5). But scene as a
predictor of DIRECTION (riser vs faller) returns AUC 0.52 — near chance. These
are not contradictory: the first measures within-cell slopes; the second asks
whether a word's absolute scene predicts its direction across cells.

The reason is that **direction is not a property of the word or even of the
word-in-context. It is mostly a property of the word-in-context-on-THIS-MODEL.**

    level                         consistency     interpretation
    word alone (all prompts+models)    0.35       word properties predict ~35%
    word + prompt (across models)      0.47       in-context gets ~47%
    word + prompt + model              1.00       deterministic

Consistency = |mean direction| across the instances at that level, where 1.0 is
unanimous and 0.0 is exactly 50/50. Measured on 68,252 (word, prompt) pairs with
5+ lineages and 2,862 words with 20+ cells.

**62% of (word, prompt) pairs are near-50/50 across lineages.** Only 9.7% are
unanimous. "Kill" falls on OLMo and rises on Qwen for the same prompt.

This decomposes the variance into thirds:

- **~35% word-level.** Some words tend to fall regardless. Embeddings recover
  18-21% of this, norms recover 7%. Neither is failing — they are measuring
  different fractions of a signal that is only one-third word-level.
- **~12% context-level.** The same word moves differently in different frames.
  Scene ratings (in-context charge) should reach this, but as a single number
  against embeddings' 300 dimensions it gets AUC 0.52.
- **~53% model-specific.** How each alignment pipeline decided to treat this
  word on this prompt. No word property can reach it; the right question here
  is what MODEL property predicts direction — alignment training data, method,
  scale.

**P's unnamed axis is partly vocabulary (embeddings see it, norms don't) and
partly not a vocabulary property at all.** The ctx_v6 contextual ratings reach
the ceiling that word-level features cannot because they measure a (word ×
prompt)-level property, adding the context third. But the model third is out
of reach for any instrument that scores words rather than models.

## FENCES

- **The `% headr` column is not quotable.** Increments are measured up from the
  shuffle (~0.49), the headroom from `log p_base` (~0.58), so the ratio routinely
  exceeds 100%.
- **The pooled row mixes POS**, where norms partly proxy part of speech. Read the
  per-stratum contrast.
- **Tree draws are OpenMP-nondeterministic**; every tree row is a mean of 5 with its
  range printed, per P's own record of five identical runs spanning 0.0040.
- **P's headline was a COMPARISON**, named against GloVe/bge. Both halves are run
  here, but on our corpus and our norm set (12 en, 7 zh), not P's eighteen.
- **Chinese `interiority` (+1.03) and `deliberation` (+0.72) sit above English.** No
  cross-language LEVEL comparison on those scales.
