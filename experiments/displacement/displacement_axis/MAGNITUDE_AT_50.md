# The magnitude stack at 50 lineages: direction holds, the horse race reverses

The README frontmatter carried `status: awaiting more lineages`,
`blocked_on: more base->aligned lineages in twp_words_v4 / movement`, and said which
results were waiting:

> the named-vs-embedding comparison in particular should be re-run before it is
> quoted: it already flipped once, from bge-ahead to a dead tie, on a bookkeeping fix.
> The DIRECTION results (rho, sign tests across frames) are not waiting on this.

**Both halves of that prediction are correct.** pilot4 (50 pairs, 49 fitting under
leave-one-out, against pilot3's 21 and 20) leaves direction where it was and reverses
every magnitude claim in the README.

Producers rerun on pilot4: `rated.py`, `rated_contextual.py`, `protocol_check.py`,
`loo.py`, `loo_all.py`, `rho_domains.py`. All six now take `--run` (default pilot3).

## DIRECTION SURVIVES, essentially unmoved

`rho_domains.py`, per-frame rho against the mover verdict, sign test across frames.
Frame counts are identical to pilot3 by construction -- the frame set did not change,
only the lineages inside each -- so this is a clean like-for-like.

    IDENTITY (59)              INSTITUTIONAL (55)         VIOLENCE (47)
    vocalisation +0.103 48/48  fit          +0.088 52/55  harm        -0.106 44/46
    harm         -0.086 47/47  harm         -0.079 33/36  makes_worse -0.075 38/47
    fit          +0.086 55/59  makes_better +0.059 39/55  makes_better+0.069 33/45
    interiority  +0.078 53/59  deliberation +0.035 40/53  interiority +0.055 32/44

    SEXUAL (42)   mundanity +0.091 38/42   harm -0.083 19/20   makes_better +0.067 32/42

Every domain signature the README names holds: `vocalisation` for identity, `fit` for
institutional, `harm` for violence, `mundanity` for sexual. `identity harm` is 47/47
at p=1.4e-14, exactly as quoted. Effect sizes are uniformly a shade smaller (identity
`fit` +0.096 -> +0.086) and no sign changes.

## MAGNITUDE REVERSES

`loo_all.py`, leave-one-lineage-out, identical words within each comparison,
`emp_mean` (the n-1 mean scored by the same rule) as the reachable benchmark.

    V6 + INSTITUTIONAL          pilot3, 173 frames, 20 fitting   pilot4, 174 frames, 49 fitting
    emp_mean                    0.0243  100%                     0.0592  100%
    v6                          0.0101   41%                     0.0207   35%
    inst                        0.0130   54%                     0.0247   42%
    v6+inst                     0.0191   79%                     0.0351   59%
    v6+inst+p                   0.0226   93%   p=0.93            0.0366   62%   p=7.9e-29
    bge_pc10                    0.0152   62%                     0.0259   44%
    bge_pc25                    0.0226   93%   p=0.76            0.0431   73%   p=6.2e-29
    named+bge                   0.0243  100%   p=0.15            0.0411   69%
    bge_pc25+p                  0.0272  112%                     0.0442   75%
    named+bge+p                 0.0261  108%                     0.0438   74%

Three README claims fall:

- **"Magnitude is named too, at the level of the data itself. 25 named scales plus
  base probability reach 93% of the benchmark and are statistically indistinguishable
  from it (p=0.93)."** At 49 fitting lineages `v6+inst+p` reaches **62%** and is
  separated from the benchmark at **p=7.9e-29**. **Nothing reaches the benchmark**;
  the best model is at 75%.
- **"At matched parameters the named set and the embedding are exactly level, 0.0226
  apiece."** 0.0366 against 0.0431 -- **the embedding is ahead by 18%**. The dead tie
  was a 20-lineage artifact.
- **"Only base-probability-augmented bge is ahead."** bge is now ahead in every
  parameter-matched comparison.

The benchmark itself rose 2.4x (0.0243 -> 0.0592) while the models rose less, which is
why percentages fall even though every absolute R2 roughly doubled.

### The domain split reverses, and with it the legislated/unlegislated reading

                    pilot3  bge_pc25 / v6+inst        pilot4  bge_pc25 / v6+inst
    identity        0.0351 / 0.0278   embedding       0.0539 / 0.0417   embedding
    institutional   0.0155 / 0.0173   NAMES WIN       0.0399 / 0.0357   embedding
    violence        0.0192 / 0.0197   NAMES WIN       0.0395 / 0.0325   embedding

**There is no longer any domain in which the named scales beat the embedding.** The
README's reading -- "alignment's institutional operation runs along dimensions
somebody wrote down... while what happens to identity words is corpus residue that was
never legislated" -- rested on those two NAMES WIN cells and does not survive.

The purpose-built instrument does still do its job locally: `inst` alone (0.0247)
beats `v6` alone (0.0207) overall and by more inside institutional (0.0258 vs 0.0170).
It is not enough to reach the embedding.

### The declared pole axis is a near-null predictor

`loo.py`, 222 frames, median 50 lineages:

    emp_mean     0.0561      names12    0.0181      bge_pcs   0.0224
    names_logp   0.0222      logp       0.0002      bge_axis  0.0013

**`bge_axis` -- `dN_position`'s own direction, the quantity this folder is named
for -- predicts magnitude at 0.0013 against principal components of the same
embedding at 0.0224.** A ~17x gap. That is the quantitative form of the structural
point: the axis is `centroid(embed(naughty)) - centroid(embed(nice))` over pole lists
with a median of 5 words each, and it is a very thin read of bge. All twelve single
named scales remain negative alone, as at pilot3.

## THE BROKEN-BENCHMARK FINDING IS n-DEPENDENT

`protocol_check.py`, section A:

                                                  pilot3     pilot4
    ceiling AS REPORTED (slope fitted on target)   +0.260     +0.518
    a PERFECT predictor, scored by the models rule -0.020     +0.407
    median corr(half A net, half B net)            +0.508     +0.718
    frames where the perfect predictor beats 0        --      255/255

The README's most-quoted methodological result is **"A perfect predictor of half A
earns -0.020 under the rule every model was scored by"**, from which "the band every
model occupied, -0.09 to +0.08, was at or above flawless".

**At 50 lineages a perfect predictor earns +0.407 and beats zero on all 255 frames.**

**The diagnosis is not retracted** -- `np.polyfit(ya, yb, 1)` fits a slope using the
target, which is the wrong quantity at any n, and the four conclusions the README
reversed were correctly reversed for pilot3's numbers. What was n-specific is the
*severity*: at 21 lineages the half-splits correlated at 0.508 and the rule pushed
perfection below zero; at 50 they correlate at 0.718 and it does not. **Do not carry
"a perfect predictor scores negative" forward as a property of the rule.**

## THE GROWTH CURVE NOW REACHES THE DATA

`protocol_check.py`'s sweep was fixed at `[1, 2, 4, 8, 12, 16]`, which was honest on
pilot3's 20 fitting lineages and, run unchanged on 49, printed the same
"still climbing at 16" while saying nothing about lineages 17-49. Extended:

    fit lineages   1       2       4       8      12      16      24      32      40      45
    median R2  -2.735  -1.243  -0.490  -0.120  +0.006  +0.072  +0.135  +0.163  +0.184  +0.191
    frames>0     0/255   0/255   3/255  28/255 133/255 202/255 250/255 255/255 255/255 255/255

    step size          16->24 +0.063   24->32 +0.028   32->40 +0.021   40->45 +0.0074

**Still climbing at 45, but decelerating hard.** R2 at 16 fitting lineages is +0.072
and at 45 it is +0.191 -- **2.6x** -- so pilot3's horse race ran at roughly a third of
the achievable R2, which is why it reverses. The magnitude numbers are still bounded
by lineage count, but far less tightly than before, and the folder's `status:` can
move from "awaiting more lineages" to "bounded, and the bound is now visible".

## What to do with README.md

- **Keep** the direction sections. They replicate.
- **Strike** "Magnitude is named too", the "exactly level" tie, and "Only
  base-probability-augmented bge is ahead". Replace with: named scales reach 62% of a
  reachable benchmark, the embedding 73-75%, and nothing reaches it.
- **Strike** the legislated/unlegislated domain reading. The confound the README
  itself flagged (institutional gets a purpose-built instrument, identity a general
  one) no longer even needs to be invoked -- the finding is gone.
- **Qualify** the broken-benchmark section with the n it was measured at.
- **Keep** the fence that bge is a ceiling on naming rather than a neutral contest.
  It matters more now, not less.
