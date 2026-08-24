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

    lang  outcome      n   med slope    up/dn        p
    en    departed    50   +0.01107    41/ 9     6e-6
    en    arrived     50   +0.01092    36/14     0.003
    en    n_movers    50   +1.81360    44/ 6    <1e-6
    zh    departed    47   -0.01010    10/37     1e-4
    zh    arrived     47   -0.01882     6/41    <1e-6
    zh    n_movers    47   +1.13203    31/16     0.040

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

## WHAT IS SHARED, AND NOT COPIED

The dose is the base-arm mass-weighted mean of `k_transgressiveness`, read from
`norm_change`'s `levels_long` — the same predictor, measured before alignment,
so it does not select on the outcome. The lineage roster is
`roster.endpoints()`: 50 pairs, NOT the 153 edges in `movement`, which include
rungs and transitive pairs and would let one base model vote eleven times.

## NOT CLAIMED

- **Direction.** Where the departed mass goes is `tail_excess`'s question and
  this instrument is silent on it.
- **That the Chinese inversion is understood.** It is measured, twice, on two
  outcomes that agree. Why a language would disperse where the other
  concentrates is not established here.
- **A rate/magnitude contradiction with M01.** Binary twin contrast against
  continuous slope, 33 pair-sites against 50 lineages. Different tests.
