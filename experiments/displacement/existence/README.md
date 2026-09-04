---
subject: existence
status: RUN 2026-08-30. 50 endpoint lineages, English.
kind: question
question: Is alignment's reshaping of word probabilities content-selective, and is it displacement or suppression?
headline: "Displacement exists. Higher-T words lose more mass (43/50 lineages). Freed mass lands preferentially on same-kind words (47/49) -- but ONLY where the prompt's field is at least a third one kind; where the scene is mostly neutral that is exactly null (24/24). It holds under the deployment frame and is 2.8x larger there."
---

# existence

**The step-1 finding. Everything else in `displacement/` asks about the shape, the scale, or the conditions. This asks whether it happens at all.**

Alignment changes word probability distributions — JS > 0 between base and aligned for every pair. That is not a finding; it would be surprising if it didn't. The question is whether the change is SELECTIVE BY CONTENT: do words that carry more transgressive charge lose more mass? And if so, where does the freed mass go?

## Part 1: content-selectivity (`run.py`)

Within each cell (one prompt × one endpoint pair), every candidate word carries a scene rating (1-7, from `charge.py`) and a delta (p_aligned - p_base). The test: regress delta on scene within each cell.

    SLOPE OF delta ~ scene (within cell)
    lineages with negative median slope:     43
    lineages with positive median slope:      7
    sign test p:                             2.1e-07
    grand median slope:                      -0.000295

**Higher-scene words lose more mass under alignment.** 43 of 50 lineages, p = 2.1e-07.

**This block said 40/10 and p=0.000024 until 2026-09-03.** Those were the numbers
of a run before the one that wrote `results/selectivity.json` on 31 Aug, and the
prose was never brought forward with the artifact. Re-run to settle it rather
than to choose between them: 43/7 exactly, reproducing the stored JSON to the
digit. The direction never moved; the sign count and the p-value did.

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

## THE DEPLOYMENT FRAME: it survives, 2.8x larger

`run.py --frame prefill`. The aligned arm measured inside its chat template
rather than bare, against the same raw base -- `base_raw -> aligned_framed`.

    same 45 pairs              RAW          FRAMED
    lineages negative          39 / 45      41 / 45
    grand median slope         -0.000276    -0.000780
    sign test p                1e-6         < 1e-6

**Content-selectivity is not an artifact of measuring the aligned arm bare.**
Putting it in the frame a user actually meets strengthens the effect, in the same
direction `instrument_calibrations/frame_prefill` finding 15 reports for the arm
contrast at large, where raw understates by 1.74x.

### Three things that make this readable, and none is optional

**THE CONTRAST IS ASYMMETRIC.** 43 of 50 bases ship no chat template, so there is
no framed base to compare against. This is not the same test conducted inside the
frame; it is the DEPLOYED arm against the BARE one, and it changes two things at
once by design, because in deployment they are never separate.

**THE POPULATION IS 45, NOT 50, AND THE RAW COLUMN ABOVE IS RUN ON THE SAME 45.**
`--match-framed` exists for exactly that: read against the 50-pair raw headline,
a framed difference would be partly which labs ship a template. Two pairs are
excluded because their system slot carries text no empty message can remove
(SmolLM3-3B's metadata block, Llama-3.1-8B-Instruct's `Cutting Knowledge Date`),
and three because they are unframed.

**`frame_aligned='prefill'` ALONE IS NOT THE FILTER.** `system_mode` records the
argument passed to the producer, not the treatment the model received, and the
two disagree in both directions -- Qwen at `system_mode='empty'` still renders a
151-character persona, gemma at `default` renders no system turn at all. The
population comes from `movement.clean_frame_pairs()`, which reads what each
template actually RENDERED into the system slot
(`roster/models/chat_renders.json`).

    results/selectivity_framed.json      the framed run
    results/selectivity_raw_on45.json    raw on the same pairs
    results/selectivity.json             the 50-pair raw headline, unchanged

## THE FRAME WITH THE WEIGHTS HELD FIXED (`--frame self`)

Self-edges: `base == aligned`, unframed against framed. Nothing changes but
whether the prompt is wrapped in a chat template. 45 aligned models -- every one
in the framed population, so this column spans the same models as the other two
-- and 8 base models as the control.

    contrast                        content-selective   same-kind landing
    base_raw    -> aligned_raw       43/50   p=2e-7      42/44   p<1e-6
    base_raw    -> aligned_framed    41/45   p<1e-6      45/45   p<1e-6
    aligned_raw -> aligned_framed    40/45   p<1e-6      45/45   p<1e-6
    base_raw    -> base_framed        4/4    p=1.000      8/8    p=0.0078

### What the four rows say, without interpretation

**Alignment displaces on its own** -- row 1, no frame anywhere.
**The chat frame displaces too** -- row 3, no weight change anywhere.
**But only on weights alignment has touched** -- row 4 is null on content.
**Together they displace more** -- row 2, about 2.8x row 1.

Neither effect is a weakened version of the other. If raw displacement were the
same pattern at lower gain, per-word `delta` would correlate near 1 between the
raw and framed conditions. It correlates at **median r = 0.574** over 20
lineages (range 0.009 to 0.79), so about two thirds of the variance is not
shared: the frame changes WHICH words move, not only how far.

The precise form is an INTERACTION. The frame's effect on displacement is
conditional on aligned weights; alignment's effect is present without the frame.

### THE DISSOCIATION, which is the result

    frame alone            content-selective?   same-kind landing?
      aligned  n=45        40/45  p<1e-6        45/45  p<1e-6
      base     n= 8         4/4   p=1.000        8/8   p=0.0078

**Content-selectivity needs aligned weights. Same-kind landing does not.**

Base models reproduce the same-kind pattern perfectly -- 8 of 8 -- while showing
no content-selectivity whatever. Semantically adjacent words are substitutes in
any language model, so any perturbation redistributes mass among them. Adjacency
is a property of the LEXICON. What alignment supplies is the DIRECTION: that the
words losing mass are the higher-charge ones.

This qualifies Part 2 below. `47/49 same-kind` is real and is less diagnostic
than it looks, because a base model under a template it never saw reproduces it
without any alignment involved.

### NEVER POOLED, and why the producer prints the split

Pooled, content-selectivity reads 44/9 at p=1e-6 and would have been written up
as "the frame displaces by content". The 8 base models were being carried by the
45. RH ruled against pooling before the run; the arm split is printed by `run.py`
and `adjacency.py` rather than left to whoever opens the JSON, because a pooled
number that has assumed its own conclusion does not announce itself.

### Fences on the control

**n=8 is permanent.** A base self-edge needs a base with a chat template and only
8 exist in the roster.

**Those 8 are the strangest template cases there are.** Qwen ships base templates
deliberately; `neo_7b` and `Tanuki-8B-base` carry templates byte-identical to
their aligned siblings; `llama-7b` renders Llama-2 format on a Llama-1 model that
never saw it. Three of eight arguably measure "the wrong template applied".

**The cells are valid but narrower.** Checked, not assumed: `conservation` 1.0
and `mojibake` ~0 on all 8, so no leakage or garbage. But every base loses 10-26%
of its candidate words under the frame, so the control is a narrower distribution
and not a clean null. Read it beside its own `n_words`.

**So 4/4 is a WEAK null** -- consistent with no effect and with an effect too
small to see at n=8. The 8/8 same-kind result is the stronger of the two control
readings, since a unanimous sign test at n=8 is p=0.0078 on its own.

## Part 2: displacement vs suppression (`adjacency.py`)

**Also run framed.** `adjacency.py --frame prefill` and `--match-framed`, the
same two flags and the same three fences as Part 1 above:

    same 45 pairs                 RAW          FRAMED
    same-kind gains more          42 / 44      45 / 45
    none-kind gains more           2            0
    same-kind median delta        +0.013634    +0.017398
    none-kind median delta        +0.009593    +0.010550
    same/none ratio                1.42x        1.65x

Unanimous under the frame, and the gap widens. Both lineages that ran the wrong
way raw flip to same-kind.

**Read the 45/45 with its denominator.** Qualifying cells fall from 13,049 to
6,227, because a cell needs a rated non-NONE top faller AND both a same-kind and
a none-kind riser, and the framed arm supplies that combination less often. So
this is unanimity on half the data, not unanimity on more of it.

**AND THE RAW COLUMN IS 44 LINEAGES, NOT 45.** `archangel_sft-dpo_pythia2-8b`
has ONE qualifying cell raw and clears the threshold framed, so the
`n_cells < 10` guard drops it from one column and keeps it in the other:

    archangel_sft-dpo_pythia2-8b   raw n=1 cell   framed n>=10

`--match-framed` matches the PAIRS and cannot match which lineages survive a
per-lineage minimum, because that depends on how many cells each arm supplies.
The 42+2 in the table sums to 44 for this reason and not because a lineage tied
-- there are no exact ties in either column, checked. It is one lineage on one
cell either way, so it moves nothing; it is recorded because a sign count that
silently changes its denominator between two columns is the thing a reader would
otherwise take as given.


### THE SAME-KIND RESULT IS CONDITIONAL ON WHAT THE PROMPT MAKES AVAILABLE

`saturation.py`. The population guard above requires that a cell have BOTH a
same-kind and a none-kind riser, so a fully saturated prompt never enters the
comparison. **But that is a test of PRESENCE, not BALANCE** -- a prompt with 60
VIOLENT candidates and 3 NONE ones qualifies. Stratifying the same comparison by
`saturation`, the share of a prompt's rated words carried by its top non-NONE
kind:

    sat band       lineages   cells   same med   none med   up/dn        p
    lo <0.33             48    2825    0.00797    0.00804   24/24   1.00000
    mid .33-.66          49    5068    0.00828    0.00747    45/4   0.00000
    hi >=0.66            49    6783    0.00789    0.00640    46/3   0.00000

**Where the scene is mostly neutral, the effect is exactly absent** -- 24/24, and
the two medians agree to three significant figures. It is absence rather than low
power: 48 lineages and 2,825 cells is not a thin cell, and a real effect at the
mid band's size would show at that n. Where the field is at least a third one
kind, same-kind landing is strong and gets stronger.

So freed mass does not seek same-kind targets. **It lands on whatever the prompt
makes abundant**, and when same-kind material is scarce the behaviour is
indistinguishable from suppression. That is a second reason the 47/49 is less
diagnostic than it reads, independent of the first one recorded above (base
models reproduce it 8/8 with no content-selectivity at all).

**This is not the dose cut in disguise.** Saturation is a FRAME property:
`corr(saturation, frame) = +0.826` against `corr(saturation, lift) = -0.025`.
Selecting on lift does not select saturated prompts, so nothing that selects on
lift inherits this.

AND IT PROBABLY EXPLAINS THE RESPONSE SATURATION `charge.py` RECORDS. That file
documents dose as the wrong selector because frames rated 5-7 show essentially
zero response, and `readout_share` §208 puts headroom at -0.05 by frame 6-7. By
frame band, the share of prompts that are >=75% one kind runs 1%, 33%, 73%, 76%,
**92%**. A prompt whose whole candidate field is one kind has nothing of another
kind to move toward. Two descriptions of one fact, reached from opposite ends.

EXPLORATORY. Not registered. The saturation bands are equal-width thirds chosen
before the numbers were read, but nothing about the cut was pre-declared.

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
