---
subject: M01_reconsidered
status: NOTE, 2026-08-24. What today's displacement work bears on in the archive's M01 findings.
question: After norm_change and rate_and_magnitude, what in M01 needs revisiting?
---

# What M01 findings today's work touches

A pass over `~/github/malign-logits/meta/M01_displacement/findings/` after
`norm_change` and `rate_and_magnitude`. Four things need reconsidering, three
are corroborated from a new direction, and one design lesson turns out to have
been followed without knowing it.

## 1. THE AROUSAL NULL — THE SHARPEST TENSION, AND PROBABLY NOT A CONTRADICTION

`D_site_suite`: **"The arousal null is strong enough to be QUOTABLE as a null
(D −0.02841, p 0.9967): whatever alignment is doing at these sites, it is not
selecting calmer words."**

`rate_and_magnitude` / `norm_change`, English, 50 endpoint lineages:

    warriner_arousal    MARGINAL -0.0168 p<1e-5    DOSE -0.0701 p=9e-5
    warriner_arousal_z  MARGINAL -0.0185 p<1e-5    DOSE -0.0773 p=9e-5

Arousal falls, marginally and under dose, on one of the largest effects in the
folder. **These are different quantities and the difference is instructive.**

D asks a per-swap question at minimal-pair SITES: *is the replacement word
calmer than the word it replaced?* No. This asks a distribution question: *is
the whole continuation distribution calmer?* Yes.

Both can hold, and the reconciliation is the same one that caught me on speech:
**a distribution can become calmer without any individual swap selecting a
calmer word**, if the calming comes from mass redistribution across many words
rather than from the identity of the substitute. D's null is about SELECTION.
This is about COMPOSITION.

**What to reconsider:** D's null is quotable as stated and should keep its
scope. But "alignment is not selecting calmer words" and "alignment does not
calm the distribution" are different claims, and the second is now measured and
false in English. Anyone citing the arousal null for the second reading is
citing it past its population.

## 2. O_CROSSLINGUAL — REFINED, NOT CONTRADICTED

`O_crosslingual`: the substitution travels to Chinese; **the affect signature
does not** — "both extremity and arousal come out English-confirming with the
Chinese arms at clean coin-flip nulls (648/650 and 652/646). Not reversals:
nulls."

Today, Chinese, 50 lineages:

    tail_excess LEVEL   -0.1337, 0 up/50 dn, p<1e-15    substitution travels -- CONFIRMED
    H5 |valence|        not supported                    extremity does not -- CONFIRMED
    H4 k_valence        +0.0025, 33/10, p=6e-4           the MEAN travels -- NEW
    H2 k_register_level +0.0062, 38/5,  p<1e-5           register travels -- NEW

**O tested extremity and arousal. It did not test the valence MEAN.** So the
refinement is: the affect signature that fails to travel is EXTREMITY; the
central tendency travels, and so does register. "The affect signature does not
travel" is too broad as a summary of O's own result and should be stated as
"extremity and arousal do not travel".

## 3. F/G's RATE NULL — NOT REPRODUCED CONTINUOUSLY

`F_G_rate_magnitude`: rate null (n=33 pair-sites, p=0.148), magnitude confirmed
(d=0.748, p=6e-5). *"Alignment does not displace more often at transgressive
sites; it displaces harder."*

`rate_and_magnitude`, English: magnitude CONFIRMED (departed +0.0111, 41/50,
p=6e-6) and **the rate is not null** (`n_movers` +1.81, 44/50, p<1e-6;
`n_fallers` +0.77, `n_risers` +0.87, both p<1e-4).

**Not evidence against F.** A binary twin contrast on 33 pair-sites and a
continuous slope over 50 lineages and thousands of prompts are different tests
with different power. But the headline "does not displace more often" does not
survive the continuous version, and should travel with its design.

## 4. T §14's ASYMMETRY — REPLICATES IN MAGNITUDE, INVERTS UNDER DOSE

`T_category_flow` §14: 206 risers to 36 fallers, fallers 3.8x larger each,
p=5.8e-09, with its own instruction: *"Quote the magnitude; quote the count with
its resolution."*

Marginally the magnitude ratio replicates (en 1.97x, zh 2.70x p=1.4e-05) and the
count does not (zh inverts, 73 fallers to 27 risers) — exactly the granularity
caveat T recorded. **Under dose the ratio reverses** (en 0.52x, p=0.034): few
large RISERS, many small fallers.

And `rate_and_magnitude` gives the mechanism: under load English fallers hold
their size (`mass/faller` null, 25/25) while risers multiply and thin
(`mass/riser` -0.0019). **T's shape is what a transgressive frame produces**,
not a constant of alignment.


## 5. THE MINIMAL-PAIR DESIGN SPANS ALMOST NONE OF THE TRANSGRESSIVE RANGE

RH, 2026-08-24, on why the dose design is the sounder foundation: the M01
minimal pairs are weak because **(a) the transgressive prompts were hardly
transgressive** and **(b) the minimal pair changed the scene entirely.**

(a) is checkable and it holds. Scoring M01's declared minimal-pair prompts on
`k_transgressiveness` — the same base-arm dose this folder uses — against the
corpus distribution of 2,245 English prompts:

    transgression   declared level    n   med dose   corpus percentile
    violence        4                 6      1.463         93%
    profanity       2                 3      1.461         93%
    substance       4                 1      1.172         79%
    sexual          4                 3      1.086         67%
    sexual          3                 5      1.060         59%
    substance       3                 1      1.052         55%
    sexual          2                 1      1.048         53%
    substance       2                 2      1.011         24%
    substance       5                 1      1.008         21%
    violence        5                 1      1.000          0%

    corpus range 1.000 - 3.520      top decile begins at 1.378

**M01's most transgressive site scores 1.463. The corpus reaches 3.520.** Its
maximum sits at **18% of the available range** measured from the floor, and
pooled across all 79 of its prompts the median percentile is **42%** — below the
middle of the corpus it was meant to probe the top of.

**And the declared levels do not track the measured charge.** The single
`violence` level-5 prompt sits at the corpus FLOOR (0th percentile) while a
`profanity` level-2 prompt sits at the 93rd. Several cells are n=1 and should
not be read individually, but the ordering failure is visible across the table.

### WHY THIS MATTERS FOR F's RATE NULL

A design confined to the bottom fifth of a gradient has little leverage on that
gradient. `F_G_rate_magnitude` found the rate null on 33 pair-sites; the
continuous version over 50 lineages and 2,245 prompts does not reproduce it
(`n_movers` +1.81, 44/50, p<1e-6). **That is what a range restriction predicts**,
and it is a better explanation than either result being wrong.

The same reasoning applies to D's arousal null: a per-swap test at sites that
are, on measurement, ordinary prompts.

### (b) IS NOT TESTED HERE

"The minimal pair changed the scene entirely" is a claim about how much the twin
differs beyond its transgressive element. It is measurable — vocabulary overlap
between the twins' base distributions would do it — and is not measured here.
Recorded so the claim is not cited as though it had been.

### WHAT THE DOSE DESIGN BUYS, STATED PLAINLY

    RANGE       the full 1.000-3.520 spread rather than its bottom fifth
    N           2,245 en prompts x 50 lineages against 33 pair-sites
    NO TWIN     nothing has to be matched, so nothing can be mismatched --
                and R_decoy_negative is the registered negative that happened to
    CONTINUOUS  a gradient, so range restriction is visible rather than silent

## CORROBORATED FROM A NEW DIRECTION

**`V_embedding_regions`.** Its defensible axis caption, in T's words, is *"off
contact, motion and force onto perception, cognition and speech"*. Under
transgressive dose the USAS fields give `X3.2 Sensory: Sound` +0.0179 and
`Q2.2 Speech acts` +0.0078 rising while `E3-` (the violent pole) falls. The
second half of V's caption is reproduced by a lexicon route V never used.

**`E_gap_stratum`.** C's H2 (de-extremification) replicated on the blind gap
stratum, 19 of 25 lineages, p=0.0073. `norm_change` H5 replicates it a third
time on 50 endpoints with a different instrument
(`warriner_valence_absz` -0.0077, 16/34, p=0.015).

**`N_mass_migration` / `Q_bridge`.** `tail_excess` negative in both languages,
**0 up / 50 down in each**, p<1e-15. The substitution result is now on three
rosters.

## A DESIGN LESSON FOLLOWED WITHOUT KNOWING IT

`R_decoy_negative`: *"every matched control population carried its own lexical
character, and that character was the effect."* A fully registered negative with
a mechanical cause.

`norm_change`'s dose design constructs **no matched control at all** — the
predictor is a continuous base-arm level measured before alignment, so there is
no control population to carry a character. That was chosen for a different
reason (not selecting on the outcome) and happens to be immune to R's failure
mode. Worth stating so the next matched-control design is proposed knowingly.

## NOT TOUCHED, AND WHY

    B_frozen              froze and never fired; no result to reconsider
    H1/H2_alignment_depth  the depth instrument; nothing here bears on it
    J_arch_displacement    architecture, not norms
    S_annotation           the order-reversal design that replaced R
    Y_* superego cluster   theory-facing; a different question
    Z_ladders_regimes      the ladder, which is `emergence/`'s subject
    zh_sites_unit_limited  unit-limited by construction; analysis cannot fill it
