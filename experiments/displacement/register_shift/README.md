---
id: register_shift
status: "RUN. G NOT SUPPORTED, G1 supported, G2 REVERSED. Lift-stratified check added 2026-09-05 (descriptive, outside the registration): G null at every dose, G2 still below the base mean everywhere, G1 decaying to null at high lift."
kind: question
headline: "This is substitution WITHIN the low register, not movement up it."
grain: distribution
question: Does alignment shift REGISTER -- vulgar to clinical, plain to euphemistic -- rather than only lowering transgressive mass?
---

# register_shift

Runs the design frozen in `registration.md` **amendment A1**. R1-R4 in that file
were superseded before any run and are not what this executes; the hypotheses are
G, G1 and G2.

    INSTRUMENT   k_register_level, English + Chinese, 1-7 continuous
    STATISTIC    mass-weighted mean register, sum(mass x register) / sum(mass)
    EDGE         base -> endpoint, the commodity form
    UNIT         the lineage, n=50

# THE RESULT

    SIGN-TEST MDE at alpha=.05: 33 of 50 (66%)  -- printed before any p

    G   reg_end - reg_base         30/50   median +0.0029   [-0.0410, +0.0247]   p=0.203
    G1  reg_removed - reg_base      4/50   median -0.0221   [-0.0661, +0.0086]   p<1e-5
    G2  reg_arrived - reg_base     12/50   median -0.0193   [-0.0736, +0.0300]   p=0.0003
        SIGNATURE arrived-removed  31/50   median +0.0147   [-0.0877, +0.0951]   p=0.119

    sensitivity, pre-committed, 43 pairs at coverage shift <=2pp
    G                              24/43   median +0.0012                        p=0.542
    SIGNATURE                      25/43   median +0.0082                        p=0.360

**G is NOT SUPPORTED.** 30 of 50 against an MDE of 33, and per decision rule 2
the null is a BOUND rather than a bare non-significance: the mean-register change
base->endpoint lies in **[-0.0410, +0.0247]** on a 1-7 scale.

**G1 IS SUPPORTED.** What leaves is low-register: 46 of 50 lineages, median
-0.0221.

**G2 IS REVERSED, significantly.** The registration predicted arriving mass would
sit ABOVE the distribution mean. It sits **below** it -- 38 of 50 lineages,
median -0.0193, p=0.0003. Direction was fixed in advance (rule 3), so this is
reported as a surprise rather than absorbed.

**The displacement signature does not clear.** `arrived > removed` is the
registration's stated criterion, and arrived is indeed less low than removed
(+0.0147), but at p=0.119 unadjusted and p=0.360 under the pre-committed
coverage sensitivity.

## What this means, stated at the strength the design allows

Both what leaves and what arrives are below the distribution's mean register.
**This is substitution WITHIN the low register, not movement up it.** The
registration's decision rule 6 says G1/G2 are required for the word
"displacement" and G alone licenses only "the register rises"; here G does not
even license that, at this edge and this grain.

Note this is the same shape R2 predicted for VIOLENCE -- "substitute within
register (plain->plain) rather than across it" -- arriving as the whole-vocabulary
result rather than as a domain contrast. R2 itself is not tested here.

## LIFT-STRATIFIED (2026-09-05): G IS NULL AT EVERY DOSE, AND G1 DECAYS WITH IT

`run.py --lift`. DESCRIPTIVE, outside the registration, bands not pre-declared,
English only because charge ratings are. The frozen numbers are untouched.

The reason to run it: `norm_change` shows this same scale behaving differently
under different doses -- MARGINAL ONLY on the level dose (+0.0025, p=0.67) but
rising under LIFT at 34/16, p=0.015, and 40/5 framed. So G's null here might have
been a marginal-only null on a quantity that moves under load, which is the shape
that caught `DISPLACEMENT_EVIDENCE` §197.

    band     n     MDE          G        p    SIGNATURE        p
    L-lo    50   33/50   +0.00240   0.4799     +0.01184   0.4799
    L-mid   50   33/50   +0.00126   0.8877     +0.00755   0.6718
    L-hi    50   33/50   -0.00132   0.8877     -0.00242   1.0000

    band     n  G1 removed        p   G2 arrived        p
    L-lo    50    -0.01554   0.0000     -0.00519   0.1189
    L-mid   50    -0.01319   0.0009     -0.00391   0.4799
    L-hi    50    -0.00542   0.4799     -0.01166   0.6718

**IT IS NOT A MARGINAL-ONLY NULL.** G is null in all three bands and its point
estimate goes NEGATIVE at high lift. The headline stands with a dose check behind
it, and the disagreement with `norm_change` localises entirely in the
aggregation -- pooled mass against per-prompt -- with no dose component.

MDE stays 33/50 in every band because the bands split PROMPTS WITHIN a lineage,
not lineages; the unit is untouched and no power is lost.

**AND THE EUPHEMISM PREDICTION IS NOT RESCUED AT HIGH CHARGE.** G2 is null in
every band and negative in all three point estimates. The registration predicted
arriving mass above the base mean; it is below it everywhere, loaded or not. That
was the most plausible way this run could have overturned the frozen reversal and
it did not.

### G1 DECAYS WITH LIFT, WHICH IS NEW

    what LEAVES, vs the base mean    L-lo -0.01554 p<1e-4
                                     L-mid -0.01319 p=0.0009
                                     L-hi  -0.00542 p=0.48

**"What leaves is low-register" is a LOW-LIFT phenomenon.** At charged sites the
removed mass sits at the base mean rather than below it -- alignment is not
register-selective about what it takes there. Which is readable: at a loaded
prompt the transgressive candidates run from clinical to vulgar, so removal
cannot be picking on register.

**THE TREND ITSELF IS NOT TESTED.** Three bands are reported separately and the
monotone decay is eyeballed across them; a per-lineage slope of G1 against lift
would be the test and has not been run. Cite the three bands, not the trend.

## THE DISAGREEMENT WITH `norm_change`, AND ITS CAUSE

**`displacement/norm_change` H2 reports `k_register_level` RISING at 45 up / 4 dn,
p<1e-5 -- its strongest result and its headline -- where this folder's G is 30/50
at p=0.203, NOT SUPPORTED.** Neither folder cited the other until 2026-09-05.

It is not the lexicon (both `k_register_level`), not the unit (both
`roster.endpoints()`, n=50), not the statistic (both a level shift of the
mass-weighted mean), and not the edge (both base -> endpoint). **It is how prompts
are combined WITHIN a lineage.**

    norm_change      computes a level per (base, aligned, PROMPT) -- its SQL
                     groups by prompt -- then combines across prompts
    register_shift   pools mass across prompts, so high-mass prompts dominate

**This folder already measured the gap without knowing it was a disagreement.**
Its own off-spec note records that *"aggregating medians over prompts rather than
pooling mass, gave 44/50 rises"* against the frozen spec's 30/50 -- and
norm_change's 45/4 sits on top of that 44/50. The off-spec run also changed the
edge, so the attribution is not airtight; norm_change uses endpoints, which
removes that difference and leaves aggregation as the remaining one.

**NEITHER IS WRONG. They are different populations.** Pooled mass asks whether
the average word the model would emit rises in register, weighting by the mass
actually at stake. Per-prompt asks whether register rises at the typical prompt,
counting a prompt where three words hold all the mass the same as one with sixty
live candidates.

**What each licenses.** norm_change's H2 licenses "register rises at the typical
prompt". This folder's G bounds the pooled quantity to [-0.0410, +0.0247] and
licenses nothing about a rise. And the G1/G2 decomposition is unaffected by the
disagreement -- it is a within-arm comparison that norm_change does not run at
all.

**A NOTE ON WHAT THIS FOLDER FORBADE.** The text above says the 44/50 *"is not a
second result and must not be quoted as one"*. That instruction is about running
it here off-spec. norm_change's H2 is the same quantity arrived at independently,
registered separately, on the correct endpoint population -- so it is quotable as
norm_change's result. What must not happen is either number being cited as
settling the other.

# THE GRAIN DISAGREEMENT, WHICH IS THE INTERESTING PART

The same instrument on generated PASSAGES gives the opposite answer.
`passage_analysis/passage_norms`, `norms_quadrants.parquet`, 25 lineage pairs
with both arms, paired by lineage:

    k_register_level   20 rise / 5 fall   median +0.0209   p=0.004
    k_vulgarity         3 rise / 20 fall  median -0.0021   p=0.0005
    brooke_formality   13 rise / 9 fall   median +0.0215   p=0.523

So **register rises in generated text and does not rise at the next-word slot.**
Same lexicon, same statistic, different grain: a bag of words over 200 generated
tokens against a distribution over one position.

**And within twp the answer depends on the EDGE.** An off-spec run comparing base
against the median of ALL its aligned rungs, aggregating medians over prompts
rather than pooling mass, gave 44/50 rises. The frozen spec -- base->ENDPOINT,
pooled mass-weighted over shared prompts -- gives 30/50. Recorded because it says
this quantity is edge-sensitive, and the registration fixed one edge in advance;
the 44/50 is not a second result and must not be quoted as one.

Three readings, none tested here:

1. Register accumulates over a passage. A per-position effect too small to clear
   at one slot could compound over 200 tokens.
2. The endpoint is not the rung where it happens. Per-stage decomposition is
   descriptive under the registration and has not been run.
3. The two measure different things: what the model would say next given a stem,
   against what it actually produces when sampling freely.

Deciding between them is a per-stage decomposition on the twp side, which the
registration permits as description.

# WHAT IS CONFIRMATORY AND MUST BE LABELLED SO

**S (the sexual subset) is not run here.** The registration discloses that
vulgar-out/clinical-retained was observed in `removal_rates` exemplars
(`cleavage +0.45, tits +0.40, fucking +0.35` stripped against `cock -0.20,
wank -0.21` retained) BEFORE freezing, so S is a confirmatory test of an
already-seen pattern and can never be reported as a discovery.

A contextual version of the same contrast exists and was not built for this
registration: `slot_ratings/sexual`'s `sexual_slot_en_v2` rates a word IN ITS
SLOT on `euphemism`, `explicitness` and `genitality` over 2,599 (prompt, word)
pairs covering 96.7% of base+aligned mass at the median prompt, and finds
euphemism significant in 13 of 16 prompts (12 up, 1 down) against explicitness
9/16 (0 up, 9 down) and genitality 8/16 (0 up, 8 down). That is a different
population and a different instrument; it is not G, S, or a test of this
registration, and it is cited here so the two are not conflated.

# COVERAGE, the declared covariate

    k-covered mass   base median 0.928   endpoint median 0.919
    |within-pair shift|   median 0.53pp   max 6.81pp   pairs >2pp: 7

Within the range amendment A1 anticipated. The pre-committed sensitivity drops
those 7 and is reported above; it weakens both G and the signature.

# WHAT IS NOT TESTED HERE

R2 (the sexual-vs-violent interaction), R3 (archaic escape hatch), and R4's
frequency-matched control. R4 was declared a GATE rather than a robustness check,
so **no R1-style claim can be made from this run at all** -- but R1 is superseded,
and G/G1/G2 carry no frequency gate in amendment A1. Whether they should is an
open question this run does not settle.
