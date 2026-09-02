# The lineage as the unit, and the dose response this folder never ran

Producer: `lineage_dose.py`. Run: **`pilot4`, all 50 endpoint pairs**. Long output at
`~/malignment-data/displacement_axis/pilot4/lineage_dose_long.csv`, one row per
(domain, scale, lineage).

    pilot4   50 of 50 declared pairs, 0 not run, 0 cells skipped
             303 items, 255 prompts, 15,150 cells; 11,859 rated cells after the gate
    pilot3   21 of 50 pairs, superseded by this. Its shortfall was DATA, not design:
             the manifest records 25 `base absent` and 4 `endpoint absent` against
             twp_words_v4 as it then stood. All 50 pairs now carry all 255 axis
             prompts on both arms.

Gate `sd >= 0.5` per (cell, scale), as `mass_direction.py`. Ties excluded throughout.
Sign-test floor at 50 lineages: `p = 2 * 0.5^50 = 1.8e-15`.

## A CORRECTION TO THE pilot3 VERSION OF THIS FILE

The 21-lineage run reported **"4 direction results lost on the lineage unit and all
four are in identity"**, and argued power was not the explanation because the same
power drop hit all four domains. **That was wrong.** At 50 lineages the identity
concentration disappears:

    LOST at 21 lineages          what 50 lineages say
    identity harm                significant under BOTH   (lineage 16/50, p=0.015)
    identity interiority         significant under BOTH   (lineage 34/50, p=0.015)
    identity aggression          the FRAME result did not replicate (0.0018 -> 0.40)
    identity directedness        the FRAME result did not replicate (0.043  -> 0.31)

Two of the four were underpowered on the lineage side and are now significant. The
other two failed on the *frame* side, which is a different fact: a frame's value is a
median over lineages, so adding 29 lineages moves the frame numbers too. Neither is
"identity's results do not generalise over models."

**What survives from that reading** is the narrower mechanism, which the larger run
sharpens rather than removes -- see the `harm` block below.

## 1. THE UNIT: 25 of 48 hold under both, and the two collapses now largely agree

`mass_direction.py:173` collapses a frame's lineages to their median and signs across
FRAMES: it generalises over stimuli with the models pooled inside. Everywhere else in
`experiments/displacement/` the LINEAGE is the unit. Both computed on the same cells.

    significant under BOTH units       25
    frame-unit only, LOST               2    identity makes_better  0.044 -> 0.12
                                             violence hedged        0.020 -> 0.065
    lineage-unit only, NEW              5    institutional vocalisation 0.19  -> 0.0066
                                             violence superego          0.21  -> 0.015
                                             sexual directedness        0.065 -> 0.015
                                             sexual hedged              0.057 -> 0.015
                                             sexual interiority         0.15  -> 0.0026
    neither                            16

Both losses are borderline on both sides. **The mass-direction finding is not an
artifact of the frame collapse**, and at full roster the two units mostly agree.

### What the frame collapse still cannot see

Medianing a frame's lineages before testing makes model heterogeneity invisible by
construction. That remains true and is worth quoting with `harm`:

    violence harm     5 of 50 lineages positive    lineage 5/50, p=4.2e-09
                                                   frame   2/47, p=1.6e-11
    identity harm    16 of 50 lineages positive    lineage 16/50, p=0.015
                                                   frame    0/24, p=1.2e-07
                      +0.3500 bloom-7b1   +0.2601 falcon-mamba-7b
                      +0.1232 llm-jp-3-7.2b   +0.0841 OLMo-2-0425-1B

`identity harm` is reported in `README.md` as **0 of 24 frames**, which reads as
unanimity. **Nearly a third of models move it the other way.** The direction claim is
real -- it now clears the lineage test -- but the frame collapse says nothing about
how consistently models do it, and the two domains differ sharply on exactly that:
violence 5/50 against identity 16/50.

## 2. THE DOSE CROSS: naming works, and it does not work better under load

The README's conditional section (displacement rate 2%/11%/28%/38% across
`base_naughty_mass` quartiles) is a crosstab over cells with no slope and no p-value,
sitting 170 lines above the naming section without ever meeting it. Crossed here,
lineage unit, dose measured on the BASE arm so the predictor cannot be selected on
the outcome. Each lineage split at its OWN median dose; one number per lineage, so
twelve correlated scales cannot each cast a vote.

    |dN| / shuffled |dN|, LOW-dose half     +0.1306   42/50   p=1.2e-06   (vs 1.00x)
    |dN| / shuffled |dN|, HIGH-dose half    +0.1385   45/50   p=4.2e-09   (vs 1.00x)
    GAIN, high minus low                    +0.0146   27/50   p=0.67

**Named dimensions beat their own permutation in both halves, by indistinguishable
amounts.** 1.13x where the base arm is quiet, 1.14x where it is loaded. The pilot3
null replicates at more than twice the n and both halves gain significance while the
gap does not.

**Transgressive mass governs WHETHER the distribution moves -- 2% to 38% -- and not
how nameable the movement is once it does.** Rate and nameability are separate
functions of dose and only the first one has any.

### `mundanity` is significant on all three quantities

Pooled over domains, lineage unit:

    scale          MARGINAL              DOSE                  NAMING GAIN
    mundanity      +0.0287 36/50 0.0026  +0.2467 41/50 5.6e-06  +0.1982 38/50 0.00031
    fit            +0.0352 46/50 4.5e-10 -0.0922 12/50 0.00031  -0.0940 15/50 0.0066
    harm           -0.0791  7/50 2.1e-07 -0.4731 15/50 0.0066   +0.2217 31/50 0.12
    interiority    +0.0197 38/50 0.00031 +0.1452 35/50 0.0066   -0.1333 17/50 0.033
    directedness   -0.0235 14/50 0.0026  -0.4271 11/50 9e-05    -0.0106 24/50 0.89
    vocalisation   +0.0163 33/50 0.033   -0.1663 16/50 0.015    -0.2437  7/50 2.1e-07

**`mundanity` rises, rises MORE where the base arm is transgressive, and is BETTER
named there.** The only scale positive and significant on all three. The more
transgressive mass a frame carries at base, the further the centre of what the model
will say moves toward the ordinary, and the more of that movement the named dimension
accounts for. That is `X_metonymy`'s shape -- down the ladder, into an ordinary
vocabulary -- with a slope instead of a contrast.

**`harm` falls hard and falls harder under load.** 7/50 marginally at 2.1e-07, dose
slope 15/50 at 0.0066. (At 21 lineages the dose slope was p=0.38; the extra models
resolved it.)

**`fit` rises everywhere and rises LESS under load.** 46/50 marginally at 4.5e-10
with a negative dose slope. Applied as a constant, not as a response to what is
found.

### Per-domain, exploratory

22 of 48 dose slopes (8 positive, 14 negative) and 24 of 48 naming-gain cells
(13 positive, 11 negative) reach p<0.05 against 2.4 expected by chance. **There is
much more structure below the pooled null than chance allows, and it does not
compose** -- which is why the pooled test is the answer and these are candidates.
The largest, uncorrected:

    identity      hedged       +0.7709 45/50 4.2e-09    institutional vocalisation -0.2714 14/50 0.0026
    identity      deliberation +0.8645 37/50 0.00094    institutional deliberation -0.1975  9/50 5.6e-06
    institutional makes_worse  +0.2715 42/50 1.2e-06    violence      fit          -0.3506  5/50 4.2e-09
    institutional aggression   +0.3218 38/50 0.00031    violence      makes_better -0.2500 15/50 0.0066
    identity      makes_better +0.3058 34/50 0.015      institutional superego     -0.1439 17/50 0.033

Note that identity, whose scales the pilot3 file suspected of not generalising, has
the two largest positive naming gains in the table.

## What this does and does not change in README.md

- **Does not change** the mass-direction finding. 25 of 48 hold under both units.
- **Changes the reading of `identity harm`.** Quote the frame result with the model
  split: 0/24 frames, and 16 of 50 lineages moving the other way.
- **Retires** `identity aggression` and `identity directedness`: their frame-unit
  significance at 21 lineages does not hold at 50.
- **Adds five** the frame collapse missed, three of them sexual.
- **Answers the crossed question with a null.** "Displacement is conditional on
  transgressive mass" is a claim about the RATE and does not extend to nameability.
- **Every p-value in README.md's mass tables is over frames**, and those were
  computed on pilot3's 21 pairs. They are not comparable with `norm_change` or
  `rate_and_magnitude` without this translation.

## Fences

- **The floor is 1.8e-15.** Nothing here reaches it; `fit` frame-unit at 1.1e-35 is a
  frame count, not a model count.
- **THE DOSE IS LIST MEMBERSHIP, NOT A RATING OR A PROJECTION.**
  `base_naughty_mass` is `sum(p_base(w) for w in item["naughty"])` -- the base arm's
  mass on the words the author hand-tagged, nothing else. Pole lists run **median 5
  naughty words** (29 items have 2, 68 have 3 or fewer), and the resulting dose has
  median 0.0494 against a `base_scored_mass` of 0.8132, with 2.2% of cells at exactly
  zero. **So the dose regression is partly a regression on how much of a frame's
  transgressive vocabulary the tagger wrote down.** `norm_change` and
  `rate_and_magnitude` use `k_transgressiveness`, a rated continuum over every word;
  the two have never been compared and are not the same construct.

- **The declared pole axis is a bge quantity and this file does not use it.**
  `slot_axis.Axis` is `centroid(embed(naughty)) - centroid(embed(nice))` in
  prompt-conditioned bge-m3, unit length -- a rank-1 direction through two
  median-5-word centroids. Everything above is computed from `dN_<scale>` and
  `nullabs_<scale>`, the rated scales and permutations of those ratings, so the
  results here are independent of how the axis was built. Purity is median 1.000
  (0.7% of cells below, min 0.941): the tagging is consistent, it is thin.

- **README.md's "the named scales see what the geometry cannot" is against that thin
  axis**, not against the 25-component bge construct its own per-word section uses,
  where the named scales tie rather than win.
- **The naming gain is a ratio of medians per (lineage, scale).** A lineage with few
  gated cells in a domain counts as much as one with many -- correct for a claim
  about models, wrong for a claim about cells.
- **`dN` still scores the two arms on different word sets** (median Jaccard 0.575,
  README "Known gap"), in the direction that inflates apparent displacement.
- **pilot4's `words.jsonl` is 772 MB and gitignored.** Regenerating it is only
  reproducible while the store holds still; the population is discovered, so a later
  ingest gives a different one.
- **The per-domain tables are exploratory**, 48 cells, uncorrected, both signs.


## 3. LIFT DOSE REVERSES THE NAMING-GAIN NULL (2026-08-30, lacan [6565])

`python -u lineage_dose.py --run pilot4 --lift-dose`

The dose above is `base_naughty_mass` -- sum of base-arm probability on
hand-tagged "naughty" words, median 5 words per item, partly a regression on how
much vocabulary the tagger wrote down. Lacan's [6565] showed that
`charge.lift_per_lineage()` -- T_base minus frame, per (prompt, base) -- predicts
displacement 3x better than the level (r = -0.261 vs -0.091), because the level
saturates above frame 5.

98% of pilot4's cells carry a lift value (12,490 of 12,750). 194 dropped, all
from prompts outside the 2,400 charge-rated English set.

### THE NAMING GAIN FLIPPED

    DOSE = base_naughty_mass (old)
      |dN| / shuffled |dN|, LOW-dose half    +0.131  42/50   p=1.2e-6
      |dN| / shuffled |dN|, HIGH-dose half   +0.139  45/50   p=4.2e-9
      GAIN, high minus low                   +0.015  27/50   p=0.67     NULL

    DOSE = lift (T_base - frame)
      |dN| / shuffled |dN|, LOW-dose half    +0.116  44/50   p=3.2e-8
      |dN| / shuffled |dN|, HIGH-dose half   +0.175  47/50   p=3.7e-11
      GAIN, high minus low                   +0.060  34/50   p=0.015    SIGNIFICANT

**Named dimensions beat their own permutation by MORE where the candidate words
add transgressiveness over the setup.** The headline from section 2 -- "naming
works, and it does not work better under load" -- was a property of the dose, not
of the data. The naughty-mass dose split the population at the wrong place
(median 5 hand-tagged words, partly floor), and lift splits it at the right
place (how much this model's distribution exceeds the frame).

The gain is not large (0.060 median, 34/50 lineages positive). But the old null
was the single strongest argument that the rate and nameability of displacement
were independent functions of dose, and it no longer holds.

### MUNDANITY IS NOW THE STRONGEST DOSE SLOPE

Pooled over all domains:

                            base_naughty_mass         lift
    mundanity               +0.247  41/50  5.6e-6    +0.055  45/50  4.2e-9
    harm                    -0.473  15/50  0.0066     -0.090   6/50  3.2e-8
    directedness            -0.427  11/50  9e-5       -0.078   7/50  2.1e-7
    fit                     -0.094  12/50  3.1e-4     -0.013   9/50  5.6e-6
    superego                        --                -0.052   9/50  5.6e-6
    deliberation                    --                -0.012  12/50  3.1e-4

The median slopes are smaller under lift because the predictor has a wider range
(lift spans -1.0 to +1.9 vs naughty-mass's 0 to 0.38), so the per-unit-dose
effect is compressed. **The SIGN COUNTS are larger**: mundanity 45/50 vs 41/50,
harm 6/50 vs 15/50. The signal-to-noise improved.

**`superego` and `deliberation` are now significant pooled**, at p=5.6e-6 and
3.1e-4. Both are negative: more lift, less superego-like and less deliberate
language. Neither reached significance under naughty-mass.

### PER-DOMAIN HIGHLIGHTS

**Identity harm** gains significance on the dose slope (14/50, p=0.0026) and has
the largest naming gain in any cell (0.610, 40/50, p=2.4e-5). Lift separates
what naughty-mass could not: how much the model's own candidates add, weighed by
this base arm's probabilities.

**Identity deliberation** shows the largest naming gain of any domain-scale pair
(+0.564, 37/50, p=0.00094), up from the old dose's +0.865 at 37/50 where the
sign count was the same. The hedged-deliberation-harm cluster in identity is
consistently the locus of dose-dependent naming.

**Sexual mundanity** is the strongest per-domain dose slope (+0.053, 39/50,
p=9e-5). In sexual frames, the more the candidates exceed the setup, the further
alignment moves toward the ordinary.

**Violence fit** has a negative dose slope under lift (-0.021, 11/50, p=9e-5)
AND a negative naming gain (-0.220, 9/50, p=5.6e-6). Fit is applied as a
constant -- it rises everywhere and rises LESS under load, and the named
dimension accounts for LESS of the travel where load is high. That is the same
shape as under the old dose and the only scale where both quantities are
significant and negative.

### WHAT THIS CHANGES IN THE READING

1. **The naming-gain null is withdrawn.** Under lift, gain is positive and
   significant at p=0.015. The rate and nameability of displacement are NOT
   independent functions of dose -- they co-vary, weakly but reliably.

2. **The "naming works everywhere alike" claim weakens but does not vanish.**
   Both halves still beat their permutation, and the gain (0.06) is a tenth of
   the baseline (0.12-0.18). So naming works in both halves, and works somewhat
   better in the high-lift half.

3. **mundanity's three-quantity significance (marginal, dose, naming gain)
   strengthens.** It was the one scale positive on all three under the old dose
   and it remains so under lift, now at 45/50 (p=4.2e-9) on the dose slope.

### WHAT THIS DOES NOT CHANGE

The mass-direction finding (25 of 48 hold under both units) is unaffected --
those are marginal results that do not depend on how dose is measured. The
translation table (which directions survive the change of unit) is also
unaffected.


## 4. CHARGE SCENE AS A MAGNITUDE PREDICTOR: NO (2026-08-30)

`loo_all.py --run pilot4 --charge-only`. Does the contextual charge continuum
(1-7 per word per prompt, from `charge.scene`) predict HOW FAR a word moves,
not just which way?

### The question and why it was worth asking

`charge.scene` is the first predictor in this folder that is (a) contextual --
a word's rating depends on the frame it appears in -- and (b) continuous -- not
a category or a binary pole membership. The naming-gain result in section 3
shows the named dimensions account for MORE of the displacement under high lift.
If that "more" comes from the scene continuum specifically, it could close the
gap with bge.

Additionally, `charge.cell(prompt, base)` gives per-lineage scene ratings -- each
base arm's own annotation of each word. That is a per-(prompt, word, model)
quantity, which is exactly the within-site variation that Findings P's ICC of
0.131 says carries 82-87% of the magnitude variance.

### Three versions tested

    charge           cross-lineage mean scene (1 col, same for all folds)
    scene_perlin     per-lineage scene (1 col, varies by held-out fold --
                     training uses mean of n-1 lineages' ratings, test uses
                     the held-out lineage's own ratings)
    bge_pc1          first PC of bge-m3 embedding (1 col, the matched control)

### Result

    CHARGE SCENE (1 column), 249 frames, 50 lineages

                                        median R2    % of benchmark
    emp_mean (benchmark)                0.0674       100%
    charge (cross-lineage, 1 col)      -0.0026        -4%
    bge_pc1 (1 col)                    -0.0025        -4%
    scene_perlin (per-lineage, 1 col)  -0.0079       -12%
    bge_pc10 (10 cols)                  0.0200        30%

**One column predicts nothing on magnitude**, regardless of whether it is charge,
bge_pc1, or anything else. This is structural: predicting which of 82 words
moves further from one number per word is underdetermined.

**Per-lineage scene is worse than the cross-lineage mean.** Each per-lineage
rating is one rater's judgment on one base arm's candidates. The cross-lineage
mean denoises by averaging over 50 raters, but even the denoised version scores
zero. The per-lineage version adds noise that ridge regression cannot absorb.

### In ensemble

    CHARGE + V6 + INST (166 frames, identical words)

                                        median R2    % of benchmark
    emp_mean                            0.0582       100%
    v6+inst (25 cols)                   0.0373        64%
    bge_pc26 (26 cols)                  0.0458        79%
    scene_perlin+named (26 cols)        0.0321        55%     WORSE than named alone
    scene_perlin+bge (11 cols)          0.0223        38%     WORSE than bge alone
    scene_perlin+all (36 cols)          0.0364        63%     WORSE than named+bge
    charge+v6+inst (27 cols)            0.0373        64%     NO GAIN over v6+inst

**Adding scene to any ensemble degrades or does not help.** The scene column is
collinear with the v6 decomposition (it is a composite of those scales) and adds
noise without adding information the decomposition does not already carry. The
per-lineage version is worse because it adds noise on top of collinearity.

### What this means for the direction/magnitude split

The finding from Findings P holds at full roster with a new instrument:

> **There is a word-level direction alignment sorts on, it is not in our
> descriptive vocabulary, and the unnamed residual outpredicts every name we
> have tried.**

Charge is a BETTER name for direction than any previous one -- it is contextual,
continuous, and it correctly predicts which words fall (high-scene) and which
rise (low-scene). But direction and magnitude are different objects, and
magnitude is where the embeddings win. The gap between named scales (62% of
benchmark) and bge (73%) is not a gap in how transgressiveness is measured; it
is a gap in what kind of information predicts how far mass travels.

The embedding encodes distributional neighborhood structure -- how many similar
words are nearby to absorb mass -- which is a magnitude-relevant property that
no single charge number can carry. The ICC result says the same thing from the
other direction: 82-87% of the fall/rise variance is within a word across sites,
which means what determines how far a word moves is its local competitive
environment, not its rating on any scale.

### Also fixed: `_build` indentation bug

The multi-source refactor (commit `d58815a`) placed the per-cell aggregation
loop body outside the inner `for raw in open(src, "rb")` loop. The index was
built from only the last cell of each source file: 2 prompts instead of 2,793.
Fixed here. The lift and dose results earlier in this file were computed from
`lifts_per_lineage()`, which reads the JSONL directly and was unaffected.
