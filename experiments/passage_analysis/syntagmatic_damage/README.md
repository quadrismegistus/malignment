---
id: syntagmatic_damage
status: PORTED, not re-run. Nine archived measurements synthesised here; one gap named and sized.
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
