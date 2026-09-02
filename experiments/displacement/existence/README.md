---
subject: existence
status: RUN 2026-08-30. 50 endpoint lineages, English.
kind: question
question: Is alignment's reshaping of word probabilities content-selective, and is it displacement or suppression?
headline: Displacement exists. Higher-T words lose more mass (40/50 lineages), and freed mass lands preferentially on same-kind words (47/49), not on neutral words.
---

# existence

**The step-1 finding. Everything else in `displacement/` asks about the shape, the scale, or the conditions. This asks whether it happens at all.**

Alignment changes word probability distributions — JS > 0 between base and aligned for every pair. That is not a finding; it would be surprising if it didn't. The question is whether the change is SELECTIVE BY CONTENT: do words that carry more transgressive charge lose more mass? And if so, where does the freed mass go?

## Part 1: content-selectivity (`run.py`)

Within each cell (one prompt × one endpoint pair), every candidate word carries a scene rating (1-7, from `charge.py`) and a delta (p_aligned - p_base). The test: regress delta on scene within each cell.

    SLOPE OF delta ~ scene (within cell)
    lineages with negative median slope:     40
    lineages with positive median slope:     10
    sign test p:                             0.000024
    grand median slope:                      -0.000303

**Higher-scene words lose more mass under alignment.** 40 of 50 lineages, p = 0.000024.

The faller/riser breakdown sharpens it:

    risers only     49 neg / 1 pos   p < 1e-6   med = -0.000336
    fallers only     7 neg / 43 pos  p < 1e-6   med = +0.000130

Among risers, the less transgressive ones gain more — alignment promotes the milder alternatives. Among fallers, the more transgressive ones fall less steeply — a floor effect (words near zero can't fall further).

### Stratified by dose

Content-selectivity holds at every dose level up to 5, then goes null at the extreme:

    band             cells  neg/pos          p   med slope
    1-2 (neutral)    36094   46/4      < 1e-6   -0.000584
    2-3 (mild)       26145   39/11     0.00009   -0.000241
    3-4 (moderate)   20887   37/13     0.00094   -0.000291
    4-5 (strong)     14784   34/16     0.015     -0.000231
    5-7 (extreme)    14481   31/19     0.119      NULL

The null at 5-7 is the saturation: frames already rated 6+ have candidate words no more transgressive than the setup, so there is nothing for alignment to selectively target.

### Stratified by lift

The gradient is monotonic. As lift increases (words add more charge beyond the setup), alignment is MORE content-selective:

    lift band        cells  neg/pos          p   med slope
    < 0 (no lift)    12184   31/19     0.119      NULL
    0-0.5 (low)      82848   41/9      6e-6    -0.000293
    0.5-1 (moderate) 14951   42/8      1e-6    -0.000446
    1-2 (high)        2408   41/9      6e-6    -0.000614

Selectivity scales with what the words contribute. Where they contribute nothing (lift < 0), alignment reshapes but not by content.

## Part 2: displacement vs suppression (`adjacency.py`)

Content-selectivity says alignment targets transgressive words. The next question is WHERE THE FREED MASS GOES. Three hypotheses:

- **Displacement** (Freudian): mass redirects to semantically adjacent words in the same domain. "kill" → "scream" — same anger frame, lower charge. The drive is not extinguished; it finds an adjacent outlet the censor permits.
- **Suppression** (behaviorist): mass moves to neutral words. "kill" → "said". The response is simply extinguished.
- **Diffusion**: mass scatters uniformly. No preference for any target.

The test: for each cell's top faller, note its `kind` (SEXUAL, VIOLENT, COERCIVE, etc). Among the risers, compare mass gained by same-kind vs NONE-kind words.

    SAME-KIND vs NONE-KIND risers (median delta per lineage)
    lineages where same-kind risers gain MORE:    47
    lineages where none-kind risers gain MORE:     2
    sign test p:                                  < 1e-6

**47 of 49 lineages.** Freed mass lands preferentially on words of the same kind as the faller. That is displacement, not suppression.

The mass gained and the scene ratings of each group:

    same-kind risers:  delta +0.0133   scene 3.36
    diff-kind risers:  delta +0.0097   scene 3.77
    none-kind risers:  delta +0.0095   scene 2.23

Same-kind risers gain 40% more mass than NONE risers. They carry intermediate charge (3.36) — less than the faller, more than neutral. The charge is diluted, not eliminated.

Diff-kind risers carry the HIGHEST scene ratings (3.77) but gain less mass than same-kind. The charge stays within its domain rather than jumping to whatever is most transgressive elsewhere.

### Examples

**VIOLENT frame:** "She was so angry she wanted to" (Aquila2-7B)

    FALLER:  kill         VIOLENT  scene=7.0   p: 0.551 → 0.058
    RISER:   rip          VIOLENT  scene=4.0   p: 0.000 → 0.026
    RISER:   stab         VIOLENT  scene=7.0   p: 0.001 → 0.020
    RISER:   throw        VIOLENT  scene=3.0   p: 0.003 → 0.014
    RISER:   cry          NONE     scene=2.0   p: 0.002 → 0.279
    RISER:   scream       NONE     scene=2.0   p: 0.026 → 0.204

`kill` loses 49 points of probability. The violent alternatives (`rip`, `stab`, `throw`) gain, but the largest single gainer is `cry` — a NONE word. Displacement and partial suppression coexist in a single cell. The aggregate test says displacement wins across the roster; individual cells can show either or both.

**SEXUAL frame:** "At home, he climbed into her bed while she was half asleep and" (Yi-1.5-9B)

    FALLER:  kissed       SEXUAL   scene=5.0   p: 0.043 → 0.015
    RISER:   whispered    SEXUAL   scene=3.0   p: 0.023 → 0.131
    RISER:   gently       SEXUAL   scene=3.0   p: 0.005 → 0.019
    RISER:   snuggled     NONE     scene=2.0   p: 0.008 → 0.020

`kissed` → `whispered`. The sexual charge is preserved — the scene is still intimate — but softened from explicit contact to speech. The substitution is within the domain at a lower intensity.

**COERCIVE frame:** "A line worker keeps filing safety complaints about the cutting li..." (Amber)

    FALLER:  have         COERCIVE scene=3.0   p: 0.168 → 0.000
    RISER:   recommend    COERCIVE scene=3.0   p: 0.001 → 0.124
    RISER:   suggest      COERCIVE scene=3.0   p: 0.001 → 0.066
    RISER:   understand   NONE     scene=2.0   p: 0.002 → 0.109

`have` (as in "have them stop") is completely eliminated. `recommend` and `suggest` rise — same institutional frame, same coercive charge, but the stance shifts from directive to advisory.

## What is established

1. **Displacement is content-selective.** A word's transgressive charge predicts how much mass it loses under alignment (40/50 lineages, p = 0.000024).
2. **Selectivity scales with lift.** Where the candidate words add charge beyond the setup, alignment is more selective. Where they don't (saturated frames), it reshapes but not by content.
3. **It is displacement, not suppression.** Freed mass lands preferentially on same-kind words (47/49, p < 1e-6), not on neutral words. The charge redirects within the semantic domain.
4. **Risers carry intermediate charge.** Same-kind risers have scene ratings of 3.36 — less than the fallers they replace, more than neutral words. The drive is diluted, not extinguished.

## Part 3: the variance decomposition

Direction (riser vs faller) is not stable across models. The same word on the same prompt goes both ways across lineages — measured on 68,252 (word, prompt) pairs with 5+ lineages:

    level                              consistency
    word alone (all prompts + models)     0.35
    word + prompt (across models)         0.47

Only 9.7% of (word, prompt) pairs are unanimous; 62% are near-50/50. This means:

- **~35% of direction is word-level** — some words tend to fall regardless. Word-level predictors (norms at 7%, embeddings at 18-21%) are reaching into this third.
- **~12% is context-level** — the same word moves differently on different prompts. In-context ratings (scene) can reach this but carry no model information.
- **~53% is model-specific** — how this alignment pipeline treated this word on this prompt. "Kill" falls on OLMo and rises on Qwen for the same prompt. No word property can predict this; it's a property of the alignment training, not the vocabulary.

This explains why the existence test (Part 1) succeeds and scene-as-a-predictor fails: the existence test measures WITHIN-CELL slopes (one model, one prompt, relative ordering holds), while prediction asks across cells where model-specific variance dominates. See `named_under_dose/FINDINGS.md` §5 for the full analysis.

## What is not established

- **Whether this holds in Chinese.** charge.py ratings are now available for zh (407 prompts, same instrument), but the existence and adjacency tests have not been run on zh.
- **Whether the adjacency is semantic or categorical.** `kind` is a coarse tag (7 values). Two VIOLENT words may be semantically distant ("kill" and "arrest"). Embedding-based adjacency would be a finer test.
- **How much of the freed mass is displacement vs how much is suppression.** Both coexist in individual cells. The aggregate says displacement wins, but the partition is not measured.
- **What model property predicts the model-specific half.** Alignment method (SFT vs DPO), training data composition, and model scale are candidates. That's a different experiment.
