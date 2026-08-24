# The lineage as the unit, and the dose response this folder never ran

Producer: `lineage_dose.py`. Reads `results/pilot3/` only -- no rescoring, no fleet
work. Long output at `~/malignment-data/displacement_axis/lineage_dose_long.csv`,
one row per (domain, scale, lineage).

Population: 4,402 cells, 253 prompts, **21 lineages, all 21 in `roster.endpoints()`
out of 50 declared**. Gate `sd >= 0.5` per (cell, scale), identical to
`mass_direction.py`. Ties excluded from every sign test.

**Structural floor, before any number is read.** With 21 lineages a sign test cannot
go below `p = 2 * 0.5^21 = 9.5e-07`. The frame-unit e-18s and e-34s in `README.md`
do not survive translation and their disappearance is arithmetic, not a failure to
replicate. Perfect agreement across all 21 lineages reads as `9.5e-07`.

## 1. THE UNIT: 23 of 48 direction results hold under both, and every loss is in one domain

`mass_direction.py:173` collapses a frame's lineages to their median and signs across
FRAMES. That generalises over stimuli with the models pooled inside. The rest of
`experiments/displacement/` uses the LINEAGE, because the models are what is sampled
and the claim is about what alignment does. Both are computed here, side by side.

    significant under BOTH units       23
    frame-unit only, LOST on lineages   4    identity aggression   0.0018  -> 1.0
                                             identity directedness 0.043   -> 0.5
                                             identity harm         1.2e-07 -> 0.26
                                             identity interiority  2.7e-07 -> 0.12
    lineage-unit only, NEW              4    institutional deliberation 0.13 -> 0.00022
                                             institutional hedged       0.51 -> 0.0072
                                             violence directedness      0.11 -> 0.027
                                             sexual interiority         0.15 -> 0.027
    neither                            17

**The headline direction claims survive.** `institutional fit` is 21/21 at the floor
(9.5e-07), `violence harm` 0/21 at the floor, `sexual mundanity` 20/21 (2.1e-05),
`identity fit` 19/20 (4e-05), `identity vocalisation` 16/20 (0.012). The
mass-direction result is not an artifact of the frame collapse.

**But identity is the only domain that loses anything, and it loses half of what it
had.** Four of its eight significant scales fail on the lineage unit; institutional,
violence and sexual lose none. Power cannot be the whole story -- the same power drop
hits all four domains -- and the gated cell matrix is no more ragged in identity
(66-86% filled) than elsewhere (80-91%).

### What the frame collapse cannot see, with the worked example

Medianing a frame's lineages BEFORE testing makes model heterogeneity invisible by
construction. `harm`, per-lineage median dN:

    violence harm     0 of 21 lineages positive     unanimous
                      -0.0018 (pythia-2.8b) to -0.5453 (Llama-3.1-8B)

    identity harm     7 of 20 lineages positive     split
                      +0.3608 bloom-7b1   +0.1652 llm-jp-3-7.2b   +0.1147 CT-LLM-Base
                      +0.0826 Qwen2.5-7B  +0.0757 Qwen3-8B-Base
                      ... -0.3808 Yi-1.5-9B  -0.4165 gemma-2-9b  -0.4388 Amber

`identity harm` is reported in `README.md` as **23/23 frames, p=2.4e-07** -- which
reads as unanimity. Seven of twenty models move it the other way, one of them by
+0.36. The frame test is not wrong about frames; it is silent about models, and the
silence is not visible in its output.

**So: the direction findings hold, and `identity harm` is not a corpus-wide claim.**
The distinction matters most exactly where the README leans hardest on identity as
the domain of unlegislated corpus residue.

## 2. THE DOSE CROSS: naming works, and it does not work better under load

The README's conditional section (displacement rate 2%/11%/28%/38% across
`base_naughty_mass` quartiles) is a crosstab over 5,595 cells with no slope and no
p-value, and it sits 170 lines above the naming section without ever meeting it.
Crossed here, with the lineage as the unit and the dose measured on the BASE arm
before alignment, so the predictor cannot be selected on the outcome.

`|dN| / shuffled |dN|` -- how much further the centroid travels along a named
dimension than along a reshuffle of that same dimension's values within the frame's
own vocabulary. Each lineage split at its OWN median dose; one number per lineage,
so twelve correlated scales cannot each cast a vote.

    |dN| / shuffled, LOW-dose half     +0.1289   19/21   p=0.00022   (vs 1.00x)
    |dN| / shuffled, HIGH-dose half    +0.1924   18/21   p=0.0015    (vs 1.00x)
    GAIN, high minus low               +0.0309   12/21   p=0.66

**Named dimensions beat their own permutation in both halves and by statistically
indistinguishable amounts.** 1.13x where the base arm is quiet, 1.19x where it is
loaded, and the difference is a null at 12/21.

This is the opposite of what the dose section predicts. **Transgressive mass governs
WHETHER the distribution moves -- 2% to 38% -- and not how nameable the movement is
once it does.** Rate and nameability are separate functions of dose, and only the
first one has any.

### What is significant under dose, and it is not a wash

DOSE slope, pooled over domains, lineage unit:

    scale          MARGINAL                    DOSE                     shape
    mundanity      +0.0463 16/21   0.027       +0.1987 17/21  0.0072    both
    fit            +0.0432 21/21   9.5e-07     -0.1162  3/21  0.0015    both, opposed
    makes_better   +0.0265 20/21   2.1e-05     -0.1018  5/21  0.027     both, opposed
    directedness   -0.0347  5/21   0.027       -0.3805  5/21  0.027     both
    harm           -0.0616  1/21   2.1e-05     -0.4544  8/21  0.38      marginal only
    interiority    +0.0172 18/21   0.0015      +0.0304 11/21  1.0       marginal only

**`mundanity` is the one scale that both rises and rises MORE where the base arm is
transgressive.** The more transgressive mass a frame carries at base, the further the
centre of what the model will say moves toward the ordinary. That is the shape
`X_metonymy` describes -- down the ladder and into an ordinary vocabulary -- now with
a slope rather than a contrast.

**`fit` and `makes_better` rise everywhere and rise LESS under load.** Both are
near-unanimous marginally (21/21, 20/21) with negative dose slopes. Alignment applies
them as a constant, not as a response to what it finds.

**`harm` falls hard and flat.** 1/21 marginally at 2.1e-05, dose slope 8/21 at 0.38.
It falls the same amount whether or not the frame was loaded.

### Per-domain, exploratory

At the (domain, scale) level, 12 of 48 naming-gain cells reach p<0.05 against 2.4
expected by chance, 9 positive and 3 negative; dose slopes 15 of 48, 7 positive and
8 negative. **There is structure below the pooled null, and it does not compose**,
which is why the pooled test is the answer and these are candidates:

    identity      hedged       +0.6895 15/16 0.00052      institutional superego     -0.2877  4/20 0.012
    violence      harm         +0.4918 16/20 0.012        institutional deliberation -0.2736  2/20 0.0004
    identity      fit          +0.4661 16/20 0.012        violence      fit          -0.3378  2/20 0.0004
    institutional makes_worse  +0.3563 16/20 0.012
    violence      makes_worse  +0.2729 16/21 0.027
    institutional directedness +0.2278 16/20 0.012
    violence      mundanity    +0.2203 16/20 0.012
    institutional aggression   +0.2035 16/20 0.012

None is corrected across 48 cells and none should be quoted alone.

## What this does and does not change in README.md

- **Does not change** the mass-direction finding. 23 of 48 hold under both units,
  including every scale the README leads with.
- **Changes `identity harm`.** Quote it as 13/20 lineages, p=0.26, seven models
  moving the other way -- never as 23/23.
- **Changes the three other identity scales** (`aggression`, `directedness`,
  `interiority`): frame-unit results that do not generalise over models.
- **Adds four** the frame collapse missed, two of them institutional.
- **Answers the crossed question with a null.** "Displacement is conditional on
  transgressive mass" is a claim about the RATE. It does not extend to nameability.
- **Every p-value in README.md's mass tables is over frames.** They cannot be read
  next to `norm_change` or `rate_and_magnitude`, which are over 50 lineages.

## Fences

- **21 lineages of 50.** pilot3 predates the roster; a rerun would change the
  population, not just the n. Nothing here is a 50-lineage result.
- **The floor is 9.5e-07** and three results sit on it. They mean "unanimous", not
  "overwhelming".
- **`base_naughty_mass` is not `k_transgressiveness`.** This folder's dose is mass on
  a per-item declared naughty pole set; `norm_change` and `rate_and_magnitude` use a
  rated scale. Nobody has checked that the two agree, so the dose results here and
  there are not yet the same axis.
- **The naming gain is a ratio of medians per (lineage, scale).** A lineage
  contributing few gated cells in a domain contributes as much as one contributing
  many, which is the correct weighting for a claim about models and the wrong one for
  a claim about cells.
- **`dN` still scores the two arms on different word sets** (median Jaccard 0.575,
  README "Known gap"). Everything above inherits that, and it is in the direction
  that inflates apparent displacement.
- **The per-domain tables are exploratory.** 48 cells, uncorrected, both signs.
