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


## 5. THE TRANSGRESSIVE MANIPULATION SPANS 3% OF THE AVAILABLE RANGE

RH, 2026-08-24, on why the dose design is the sounder foundation: the M01
minimal pairs are weak because **(a) the transgressive prompts were hardly
transgressive** and **(b) the minimal pair changed the scene entirely.**

(a) is checkable. D's population is the 684 pair_ids with
`contrast_type == transgressive_swap` (`results/population_d_684.json`), and the
full set in `data/prompt_categorisation.json` is 1,509 prompts split
`pair_role` MARKED / UNMARKED. Scoring them on `k_transgressiveness` — the same
base-arm dose this folder uses — against 2,245 English corpus prompts:

    pair_role     n in corpus   med dose   corpus percentile   max
    MARKED            496         1.105          70%          2.373
    UNMARKED          628         1.023          37%          1.657

    corpus range 1.000 - 3.520      top decile begins at 1.378

**THE MANIPULATION WORKS AND IT IS SMALL.** MARKED sits above UNMARKED, 70th
percentile against 37th, so the design does what it says. But the gap between
the arms is **0.082 on a corpus range of 2.520 — about 3% of the available
range.** And the transgressive arm's MEDIAN sits below the corpus top decile
threshold (1.105 against 1.378): **30% of ordinary corpus prompts are more
transgressive than M01's typical transgressive site.**

Its most transgressive prompt reaches 2.373 where the corpus reaches 3.520.

### WHY THIS MATTERS FOR THE NULLS

A two-level contrast separated by 3% of a gradient has little leverage on that
gradient. Two M01 nulls sit exactly there:

    F's RATE null      33 pair-sites, p=0.148
                       continuous: n_movers +1.81, 44/50, p<1e-6
    D's AROUSAL null   D -0.02841, p=0.9967, "quotable"
                       continuous: warriner_arousal -0.0701 under dose, p=9e-5

**Range restriction predicts both**, and it is a better explanation than either
result being wrong. Neither null is retracted by this; both should travel with
the span of the manipulation that produced them.

### A CORRECTION TO THIS SECTION'S OWN FIRST VERSION

The first version of this section scored `data/f36_minimal_pairs.csv`, which
carries a `trans_level` column — and RH pointed out that the transgressive_swap
prompts *do not have a transgression level*, so that was a different design
being measured under M01's name. Its numbers (median 42nd percentile, "18% of
the range") described the wrong population and are withdrawn. The MARKED/UNMARKED
figures above are the right ones, and they make a weaker but sounder version of
the same point.

### (b) IS NOT TESTED HERE

"The minimal pair changed the scene entirely" is a claim about how much the twin
differs beyond its transgressive element. It is measurable — vocabulary overlap
between the twins' base distributions would do it — and is not measured here.
Recorded so it is not cited as though it had been.

### WHAT THE DOSE DESIGN BUYS, STATED PLAINLY

    RANGE       the full 1.000-3.520 spread rather than a 3% contrast inside it
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

## WHAT IS STILL WORTH REDOING: P's UNNAMED AXIS, CONDITIONALLY

`P_unnamed_axis` is the one M01 finding today's work gives a new handle on.

Its claim: **"none of the eighteen rated norms predicts which way alignment
moves a word"**, held out by word. Word identity carries +0.121 AUC of headroom
over base probability; 300 unsupervised GloVe dimensions recover 18-21% of that
headroom while the rated norms recover **7%**. Every named component — register,
concreteness, length — is a minority share, and the unnamed residual outpredicts
all of them. Its nameable face has the provisional name INTERIORITY,
enacted -> represented.

**P tested MARGINAL prediction. Today's central result is that many named norms
are DOSE ONLY** — flat on average, steep where the frame is transgressive:

    k_concreteness       MARGINAL p=0.119   DOSE p=1e-5
    warriner_dominance   MARGINAL p=0.085   DOSE p=9e-5
    k_charge             MARGINAL p=0.533   DOSE p=2e-5
    vocalisation         MARGINAL p=0.480   DOSE p=9e-5

**So P's failure may be the same marginal/conditional split, and its 7% may be a
marginal 7%.** The question worth asking is P's own, conditioned:

> Held out by word, do the rated norms predict direction BETTER at prompts where
> the base arm carries transgressive charge than at neutral ones?

If yes, the named vocabulary is not inadequate — it is context-dependent, and P's
ceiling was measured in the wrong condition. If no, P stands harder than before,
because the most favourable condition has been tried.

**This is a real re-do, not a re-read.** It needs P's held-out-by-word protocol
and its measured ceiling, not this folder's lineage-level sign tests, and the
ceiling has to be recomputed within dose strata or the comparison is against the
wrong baseline. `K_word_properties`'s instrument facts stand and are reusable.

## AND ONE CELL M01 DECLARED UNFILLABLE IS PARTLY FILLED

`zh_sites_unit_limited`: *"The Chinese site question is unit-limited... the test
has 17 independent units where it needs between 235 and 428. No amount of
reanalysis fixes that, and the ceiling is set by how many Chinese-competent base
checkpoints exist in the world."*

That was correct **about that unit**. The dose design does not use it: 50
lineages over 416 Chinese prompts, a continuous predictor, no twin to match. It
returns Chinese results at p<1e-15 (`tail_excess` level, 0 up/50 dn) and p<1e-5
(register, valence mean).

**The finding said reanalysis could not fix it, and reanalysis did not — a
different instrument did.** The bounded negative was a statement about the
minimal-pair unit, not about Chinese, and it should be cited that way.

## NOT WORTH REDOING, AND WHY

    B_frozen               froze and never fired; nothing to redo
    H1/H2_alignment_depth  a different instrument; nothing here bears on it
    J_arch_displacement    architecture, not norms
    S_annotation           the order-reversal design that replaced R; intact
    X_metonymy             live in the X campaign, not superseded here
    Y_* superego cluster   theory-facing; a different question
    Z_ladders_regimes      the ladder, which is `emergence/`'s subject
    L_M_found_prose        adjacent to tail_excess but a different mechanism
                           claim (BOUNDARY BLUR, not tail contraction) and not
                           tested by anything here
