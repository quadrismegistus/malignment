# salary_probe — what does alignment do to a distribution over money?

**id:** salary_probe **status:** UNPARKED AND RUN, 28 lineage pairs, 84,000
draws, 2026-08-28. Registration frozen at `2afe765`, amendments A1-A4.

> **THE RESULT IS IN `FINDING_narrowing.md`. THIS FILE IS THE PILOT**, kept
> because what it says about its own limits was right and is the reason the
> larger run exists. Its numbers are NOT superseded -- they are a different,
> smaller corpus -- but nothing here should be quoted as the answer.
>
>     S  sd(log) narrows    23/28  p=0.0009   -- holds, and strengthens under
>                                                its own plausible-only control
>     C  class gap narrows   8/28  p=0.036    -- it WIDENS. Registered direction
>                                                REFUTED, not unsupported.
>     G  |gap| narrows     144/280 p=0.68     -- flat
>        level rises        16/28  p=0.57     -- chance
>
> The section below asks for "the same producer over lineages large enough that
> the base arm is fluent in both languages, so a rising floor cannot be
> incoherence being cleaned up". That is what was run. The rising floor turned
> out to be neither incoherence nor a real rise: it was a parser understating
> the base arm by 10,000x on Chinese `万`, 2.1x more often than the aligned arm.
> See amendment A4.

Three hypotheses, registered before any run: **S** the range narrows to the
middle, **G** the gender gap closes, **C** the class gap closes. G and C are
separate claims and are never combined.

## Population

`domain == 'class'`: **30 prompts, exactly the battery, zero false positives**
(A3). 20 English, 10 Chinese. Partition on `subdomain`, pair on the declared
`group_id` -- 10 groups of 2, 5 per language. **Never the prompt text and never
`finding`**: F13 is on 439 prompts of which 404 are not salary.

## Measurement

`run.py` reads `instrument_calibrations/numeric_boundary/results/beam.csv` --
`generate`, 100 samples x 10 tokens at temp=1. **That folder established why:**
`expand` cuts `$150,000` to `150` at the comma and `score_words` refuses it at 8
tokens against `MAX_DEPTH` 6, while `generate` consults neither and returns
`46,204,000` whole.

**11,574 of 12,000 samples usable; 426 (3.5%) excluded as unparseable and
counted.** `36,00` is a truncated `36,000` and stripping the comma understates it
10x, so irregular groupings are excluded rather than coerced.

**Two lineages only: SmolLM2-360M and Qwen2.5-0.5B.** 360M and 500M parameters.

# RESULTS — a pilot, and none of these is a finding

    S  IQR narrows                     3 of 4 cells
    S  TOWARD THE MIDDLE, as registered 2 of 4 cells   <- the criterion S is judged on
    G  group-cells where |gap| narrows  7 of 20
    C  lineages where the class gap narrows 1 of 2

## S — and the registered criterion is too weak, which is its own finding

An IQR can tighten around **any** location; that is concentration and it is
agnostic about where the mass went. S is a claim about WHERE. Both are emitted
and they disagree, 3 of 4 against 2 of 4.

    aligned mass minus base mass, by BASE-defined quintile

    SmolLM2 en   Q1 -0.115  Q2 -0.108  Q3 +0.016  Q4 +0.210  Q5 -0.002   passes
    Qwen2.5 en   Q1 -0.036  Q2 +0.084  Q3 +0.067  Q4 -0.073  Q5 -0.042   passes
    SmolLM2 zh   Q1 -0.053  Q2 -0.115  Q3 +0.044  Q4 +0.112  Q5 +0.012   fails
    Qwen2.5 zh   Q1 -0.179  Q2 -0.015  Q3 +0.068  Q4 +0.085  Q5 +0.041   fails

**SmolLM2/en passes and should not.** Its gain is 13x larger in Q4 than in Q3.
The registered rule -- *both outer quintiles lose AND the centre gains* -- never
requires the centre to be **where the gain is**, so a distribution that empties
the bottom and piles into the fourth quintile satisfies a criterion written for
centring. **A criterion that returns a plausible verdict without testing what it
claims.** Recorded rather than repaired: amending a frozen rule after seeing the
data is the thing registration exists to stop, and the next version of this
question should state the rule as a location, not as three inequalities.

**The pattern in 3 of 4 cells is A RISING FLOOR, not centring.** Q1 loses
everywhere; Q5 gains in both Chinese cells. And a rising floor is what a
COHERENCE effect looks like -- a base model saying `$500` is producing junk, and
alignment removes it. Qwen is competent in Chinese and still shows Q1 -0.179, so
it is not purely that, **and this pilot cannot separate the two.**

**Models do NOT converge on a canonical salary.** Between-model spread of the
median: en 5,000 -> 15,000 (diverges), zh 20,000 -> 10,000 (converges).

## C — the two lineages go opposite ways, and so do their mechanisms

    SmolLM2  up 50,000->74,414  mid 49,680->55,725  work 27,392->30,000   gap 22,608 -> 44,414
    Qwen2.5  up 45,000->40,000  mid 35,000->30,000  work 24,360->30,000   gap 20,640 -> 10,000

**Qwen compresses from both ends** -- lowers upper and middle, raises working --
which is the parity shape the hypothesis predicts. **SmolLM2 inflates the top and
leaves the bottom.** Opposite signs on two models is what noise looks like at
n=2, and C is **not supported**.

## G — nothing

7 of 20 group-cells narrow. No direction in either language or lineage.

# WHY THIS IS PARKED

**RH, 2026-08-17: not running generations across the roster now.** Two lineages
of 360M and 500M cannot separate a coherence effect from an alignment effect, and
that ambiguity sits underneath every number above.

**What would settle it:** the same producer over lineages large enough that the
base arm is fluent in both languages, so a rising floor cannot be incoherence
being cleaned up. 35 of the 50 declared pairs have both arms local (see the
session record); nothing here needs a download.

**What must not happen meanwhile:** these numbers being quoted as results. They
are one instrument, two lineages, and a criterion that admits a case it was not
written for.

## AMENDED 2026-08-17 — the truncation is a MARGINALISATION, and there is now a twp route

**malign [6449], after implementing and rejecting the numeric rule.**

This README says the truncation is not monotone and therefore G and C cannot run
on cut surfaces. **The non-monotonicity is real and the inference from it was too
strong.** `25` at 0.0326 is not a broken `25,000`; it is **P(salary begins 25)**
— the marginal over every salary starting that way. Coarse, and correct.

**So the band-restricted analysis was sound for a better reason than I gave.**
Within a digit band the surfaces are an ordered marginal; only ACROSS bands does
ordering fail. The registration's fear was the right shape and the wrong size.

**And `max_depth=9` alone recovers the full numeral**, with no numeric rule and
no `generate`:

    $100,000   8 tokens   REFUSED at depth 6  ->  0.03174315
    $50,000    7 tokens   REFUSED             ->  0.05142502

**That is a route to this experiment with CALIBRATED probabilities commensurable
with the store**, which is exactly what the `generate` arm could not give — its
sampled distribution sits beside nothing. The estimand objection in FINDING 3 of
`numeric_boundary` is now answerable rather than a standing cost.

**`generate` remains the right instrument for the CROSS-LINGUAL comparison
specifically**, because it consults no boundary rule at all and the adopted
`decoded_boundary` fix is differential by language (+0.15% en against +3.42% zh).
A twp cross-lingual contrast compares instruments; this one does not.

**None of the results above are re-run.** They stand as a two-lineage pilot on
sampled data, and the twp route is a better instrument that nobody has pointed at
this question yet.
