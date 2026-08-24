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
- **`base_naughty_mass` is not `k_transgressiveness`.** This folder's dose is mass on
  a per-item declared naughty pole set; `norm_change` and `rate_and_magnitude` use a
  rated scale. Nobody has checked that the two agree, so the dose results here and
  there are not yet on the same axis.
- **The naming gain is a ratio of medians per (lineage, scale).** A lineage with few
  gated cells in a domain counts as much as one with many -- correct for a claim
  about models, wrong for a claim about cells.
- **`dN` still scores the two arms on different word sets** (median Jaccard 0.575,
  README "Known gap"), in the direction that inflates apparent displacement.
- **pilot4's `words.jsonl` is 772 MB and gitignored.** Regenerating it is only
  reproducible while the store holds still; the population is discovered, so a later
  ingest gives a different one.
- **The per-domain tables are exploratory**, 48 cells, uncorrected, both signs.
