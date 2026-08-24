---
subject: rate_and_magnitude
status: RUN 2026-08-24. 50 endpoint lineages, en and zh separately.
question: How MUCH mass moves under alignment, how OFTEN, and does either scale with the frame?
headline: English moves more mass AND more words at transgressive prompts. Chinese moves MORE WORDS but LESS MASS.
---

# rate_and_magnitude

**Named for both quantities because the finding is that they come apart.**

M01 `F_G_rate_magnitude` separated them first and found:

    RATE       does alignment displace MORE OFTEN at transgressive sites?
               NULL -- n=33 pair-sites, p=0.148
    MAGNITUDE  does it displace HARDER?
               CONFIRMED -- d=0.748, p=6e-5

*"Alignment does not displace more often at transgressive sites; it displaces
harder."* `Q_bridge` names the magnitude quantity: `departed`, "how much mass
leaves words at all" — against `tail_excess` for DIRECTION, whether freed mass
"re-lands on nameable substitute words or disperses into the unresolved tail".

**This folder does not measure direction**, and nothing else in
`experiments/displacement/` measured plain magnitude: `displacement_axis` does
magnitude and direction along author-declared pole axes, `displacement_taxonomy`
asks what KIND of movement, `register_shift` asks about one scale.

## WHAT IS NEW: THE CONTINUOUS VERSION

M01 asked it as a BINARY contrast — a transgressive twin against its matched
neutral twin. This regresses three outcomes on a CONTINUOUS base-arm
transgressive level, per lineage, across prompts, unit = the lineage,
sign test over 50 endpoints from `roster.endpoints()`.

    lang  outcome          n   med slope    up/dn        p
    en    departed        50   +0.01107    41/ 9     6e-6
    en    arrived         50   +0.01092    36/14     0.003
    en    n_movers        50   +1.81360    44/ 6    <1e-6
    en    n_fallers       50   +0.77315    39/11     9e-5
    en    n_risers        50   +0.86678    44/ 6    <1e-6
    en    n_fall-n_rise   50   -0.12651    24/26     0.888   NULL
    en    mass/faller     50   -0.00000    25/25     1.000   NULL
    en    mass/riser      50   -0.00189    16/34     0.015
    en    tail_excess     50   -0.00875    12/38     3e-4
    zh    departed        47   -0.01010    10/37     1e-4
    zh    arrived         47   -0.01882     6/41    <1e-6
    zh    n_movers        47   +1.13203    31/16     0.040
    zh    n_fallers       47   -0.22221    20/27     0.382   NULL
    zh    n_risers        47   +1.21460    35/12     0.001
    zh    n_fall-n_rise   47   -1.06453    17/30     0.079
    zh    mass/faller     46   -0.00167     4/42    <1e-6
    zh    mass/riser      47   -0.00745     3/44    <1e-6
    zh    tail_excess     47   +0.01633    38/ 9     2.5e-5

`n_fallers` / `n_risers` are the RATE SPLIT BY DIRECTION. Not `tail_excess`,
which asks WHERE the freed mass lands; this asks whether the extra movement at a
loaded prompt is words LEAVING or words ARRIVING, and what each one carries.

## ENGLISH CONFIRMS M01'S MAGNITUDE AND BREAKS ITS RATE NULL

More mass departs where the base is more transgressive (+0.0111, 41 of 50
lineages). `departed` and `arrived` agree to three decimals (+0.01107 /
+0.01092) — mass conservation, and a check that the statistic behaves.

**But `n_movers` rises steeply too** (+1.81, 44 of 50, p<1e-6). At a
transgressive prompt MORE WORDS move as well as more mass. M01's rate null was
33 pair-sites as a binary twin contrast; this is a continuous slope over 50
lineages and thousands of prompts. **They are not the same test, so this is not
evidence against M01** — but the continuous version does not reproduce the null
and that is stated rather than smoothed.

## CHINESE INVERTS THE MASS AND KEEPS THE RATE

Less mass moves at transgressive prompts (-0.0101 departed, -0.0188 arrived)
while MORE WORDS move (+1.13). **That is a DISPERSAL: many small movements
instead of few large ones.**

It agrees with the asymmetry test in `norm_change`, where M01's "few large
fallers, many small risers" replicates marginally and INVERTS under dose. English
concentrates displacement at loaded prompts; Chinese spreads it.

**Reporting all three outcomes is what makes that legible.** A departed-only
reading would have called the Chinese result a smaller effect rather than a
differently-shaped one.



## SPLITTING THE RATE BY DIRECTION IS WHERE THE TWO LANGUAGES SEPARATE

**ENGLISH: the counts rise TOGETHER and the risers thin out.** `n_fallers`
+0.773 and `n_risers` +0.867 both rise steeply, and their DIFFERENCE is null
(-0.127, 24 up/26 dn, p=0.888) — symmetric. Meanwhile `mass/faller` is exactly
null (25/25, p=1.000) while `mass/riser` FALLS (-0.0019, p=0.015).

So at a transgressive English prompt: more words leave and more words arrive, in
step; **each departing word carries the same mass it always did, and each
arriving word carries less.** The extra mass is spread over more, smaller
risers.

**That is "few large fallers, many small risers" as a DOSE EFFECT.** M01 T §14
found the shape marginally; here the transgressive frame is what produces it —
fallers hold their size while risers multiply and thin.

**CHINESE: only the arrivals increase, and everything shrinks.** `n_fallers` is
null (-0.222, p=0.382) while `n_risers` rises (+1.215, p=0.001), and BOTH
per-word masses fall hard (`mass/faller` -0.0017 at 4 up/42 dn; `mass/riser`
-0.0075 at 3 up/44 dn, both p<1e-6).

So a loaded Chinese prompt does not recruit more departures at all. The same
words leave, each carrying less, and the mass they release is scattered across
more and much smaller arrivals. **Dispersal on both sides of the ledger.**

### WHY THIS IS THE INFORMATIVE CUT

`n_movers` alone said "more words move" in both languages and looked like a
shared effect. Split by direction it is not shared: English recruits departures
AND arrivals symmetrically; Chinese recruits only arrivals. The aggregate hid a
difference in kind.



## DIRECTION: `tail_excess`, AND THE SHARPENING QUESTION IT ANSWERS BY CONSTRUCTION

M01 `N_mass_migration` defines it: does freed mass "re-land on nameable words
above the resolution floor (substitution) or disperse into the unresolvable tail
(diffusion)?" **The comparison is against a proportional-renormalisation null**
— what the distribution would look like if the freed mass were simply spread
over the survivors in proportion to what they already held.

    tail_base   = 1 - sum(p_base)           the theta-censored remainder
    survivors   = 1 - faller_base           what the freed mass could land on
    expected    = tail_base * (1 + departed / survivors)
    tail_excess = tail_aligned - expected

**THAT NULL IS THE CONTROL FOR GENERAL SHARPENING, and it is why the null is a
null rather than a raw difference.** If alignment merely rescaled the
distribution, freed mass would reach every survivor -- the tail included -- in
proportion to its existing share. Subtracting that expectation leaves only the
part that is NOT rescaling. A raw `tail_aligned - tail_base` would confound the
two and is deliberately not computed here. The dose slope adds a second and
independent layer: whether the excess is specific to transgressive frames.

### THE LEVEL REPLICATES M01 IN BOTH LANGUAGES, UNANIMOUSLY

    MARGINAL tail_excess LEVEL   en  -0.170276   0 up/50 dn   p<1e-15
                                 zh  -0.133729   0 up/50 dn   p<1e-15

Negative everywhere, all 50 lineages in each language. That is `O_crosslingual`'s
**"the substitution travels"** — freed mass concentrates on nameable words
rather than dispersing, in English and Chinese alike.

### BUT THE DOSE SLOPE INVERTS BY LANGUAGE

    en  tail_excess  -0.00875   12 up/38 dn   p=3e-4
    zh  tail_excess  +0.01633   38 up/ 9 dn   p=2.5e-5

**English becomes MORE substitutional as the frame loads** — the more
transgressive the base, the further below the proportional null the tail sits.
**Chinese becomes LESS so**, moving toward diffusion.

**The sign of the slope is not the sign of the level.** Chinese remains
net-substitutional throughout (level -0.134); the slope says only that
transgressive frames push it toward the tail relative to neutral ones. Nothing
here shows Chinese crossing into net diffusion, and it should not be read that
way.

### THIS IS THE SAME SPLIT THE OTHER OUTCOMES SHOW

    ENGLISH under load   more mass moves, more words both ways, risers thin,
                         and the mass lands on NAMEABLE WORDS
    CHINESE under load   less mass moves, only arrivals recruit, everything
                         shrinks, and the mass goes to the TAIL

Both languages substitute. Under transgressive load English substitutes harder
and Chinese disperses. Every outcome in this folder tells that story, and
`tail_excess` is the one that says where the mass actually went.

## WHAT IS SHARED, AND NOT COPIED

The dose is the base-arm mass-weighted mean of `k_transgressiveness`, read from
`norm_change`'s `levels_long` — the same predictor, measured before alignment,
so it does not select on the outcome. The lineage roster is
`roster.endpoints()`: 50 pairs, NOT the 153 edges in `movement`, which include
rungs and transitive pairs and would let one base model vote eleven times.

## NOT CLAIMED

- **Direction beyond the tail split.** `tail_excess` says whether mass reached
  nameable words or the tail. It does NOT say WHICH nameable words -- that is
  `displacement_axis`'s and `norm_change`'s question.
- **That the Chinese inversion is understood.** It is measured, twice, on two
  outcomes that agree. Why a language would disperse where the other
  concentrates is not established here.
- **A rate/magnitude contradiction with M01.** Binary twin contrast against
  continuous slope, 33 pair-sites against 50 lineages. Different tests.
