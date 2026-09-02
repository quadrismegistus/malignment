---
kind: question
subject: selection_and_combination
question: Does alignment change WHICH words appear, or what they COST in context?
status: "COMPLETE (migrated 2026-08-20 from malign-logits M06)"
headline: "Alignment changes which signifiers appear. It does not change how the chain coheres."
grain: "page, joined to the distribution grain"
---

# selection_and_combination

**Alignment changes which signifiers appear. It does not change how the chain coheres.**

Migrated from `malign-logits meta/M06_generation/findings/composition_not_level.md` (2026-08-13), which is here verbatim along with its pre-registered plan, its five producers, and its results. `PROVENANCE.md` pins every file by sha256.

## Why the folder is not called `mediation`

Every producer here is `m06_mediation*.py` and the plan is `plan_mediation.md` — that is the archive's internal name for this work. It is not used because **`mediation` is already an institutional v3 scale in this repo** (`SCALES_INST_V3`, and it appears by that name throughout `experiments/displacement/displacement_axis/`). Nor is the finding's own name used for the folder: `composition_not_level` is named after the term the finding itself found broken — "level" meant two different quantities and an earlier draft conflated them. The file keeps that name; the folder does not.

## The decomposition, which is the reason to have this

Mean surprisal per word is `Σ_w f(w)·s(w)`. There are exactly two ways aligned passages can be cheaper than base ones, and they exhaust the possibilities:

    COMPOSITION   Σ_w (f_a − f_b)·s̄(w)     different words are used
    LEVEL         Σ_w f̄(w)·(s_a − s_b)     the same words cost less

**Composition is SELECTION and level is COMBINATION** — the paradigmatic and syntagmatic axes, as an arithmetic partition that sums exactly. Residual 0.0000.

    Δ (aligned self − base self)   -1.2849 nats/word
      composition (symmetric)      -1.3098
      level       (symmetric)      +0.0249

Both decomposition orders are reported in the finding and **neither is the headline** — they disagree substantially (level swings +0.49 to −0.44), so the terms are entangled and the symmetric mean is a summary, not a fact.

**This is what makes the Jakobson mapping a measurement rather than a metaphor.** The theory-return wave asserts correspondences of this kind and does not test them. Here the correspondence is decomposable, exhaustive, and the split is lopsided.

## Direction predicts; volatility does not

No classification and no threshold, because every mover flag admitted `the` — which is not a threshold defect: **`the` moves constantly and goes nowhere**, non-still in 30.5% of its cells with a direction of −3.3%. Volatility and direction are two dimensions and a binary flag multiplies them into one.

    against the composition change (f_aligned − f_base), 36 pairs
    net_fall          rho -0.285   36/36     partial -0.276
    dir_when_moved    rho -0.269   36/36
    pct_moved         rho +0.008   18/36     NULL, exact chance

## The trap in Result 3, and why it is our trap too

The story one wants is that displaced words cost the aligned model more — displacement showing up as surprise. The class table refuses it:

    class         tokens   share   mean level
    fall         1293354    7.6%     +0.3806
    rise          596374    3.5%     +0.1443
    still        2948340   17.3%     +0.2574
    unmeasured  12242204   71.7%     +0.6137     <- the largest

**The words M01 never measured are the costliest of all**, so fallers sit BELOW the corpus average. "Displaced words cost more" is true, significant, correctly signed, and **not evidence of displacement** — base text is simply foreign to the aligned model, and a whole-distribution fact was being credited to a specific mechanism. The correlations once reported as the result are WITHDRAWN for inheriting it.

The repair is to compare fallers to RISERS on a fixed text, where the generic shift applies equally to both and cancels:

    median(level | fall) − median(level | rise), common support only
      base-generated      +0.3471    34/35 pairs
      aligned-generated   +0.4435    35/35

**At matched aligned probability, a word alignment pushed DOWN costs ~0.35–0.44 nats more in context than one it pushed UP to the same place.**

**That defect is the same shape as the one that cost this repo a day on 2026-08-20.** `experiments/displacement/displacement_axis/` compared every model against a "ceiling" computed by a rule no model could use, and read the resulting wall of small negatives as absence. Here a real measurement was read against an implicit zero when the right reference was what an average token costs. Both times the number was fine and **the baseline was doing the work**; both times the fix was a reference the comparison is entitled to.

## Disagreement, not injury

Surprisal is two models' opinions about ONE fixed sequence. Nothing about the text changes; only the reader does. So at each position where a displaced word sits, the aligned model's distribution says *this is not the word I would have reached for*.

**The design could not show chain damage even if there were any** — the chain is held constant by construction. Two measurements say there is none: decomposition level is +0.0249 (aligned passages are not less coherent to their own author), and the propagation slope is ~+0.008 nats-per-bit (an imposed improbable word is absorbed within a few tokens, ~99% of it).

## What this connects to here

- **`../predicting_aligned_text/`** inherits `p_on_passages`'s I6: the page-grain signature is TONIC, *"site-specificity lives only at the distribution grain."* That is the same claim from the other side — alignment reaches selection and not combination, so what survives sampling is a constant disposition rather than a site-conditional response.
- **`experiments/displacement/displacement_axis/`** found, on 2026-08-20 and at the distribution grain, that **direction is nameable and magnitude is not** — `harm` at 44/47 frames, every named scale negative alone. This finding reports the same asymmetry from the page: `net_fall` 36/36, `pct_moved` 18/36 at exact chance. Two instruments, two grains, one shape.
- **`../diegetic_superego/`** and this folder's one untested speculation point at each other. Y finds alignment moralising INSIDE the scene it keeps writing; this finding, having measured and REFUTED the obvious mechanism (promotion turns out to be the MORE consistent operation, 0.580 vs 0.533), speculates that **the scope of a demotion may be the SCENE rather than the site or the lexicon**. Read together they suggest a prohibition that is situational rather than lexical — not that `kill` is forbidden, but that it is forbidden HERE, for as long as one stays in the scene that raised it. **Neither of these is a tested claim and the speculation is flagged as speculation in its own document.**
- **`experiments/slot_ratings/`** asks which NAMED dimension orders the words that move. Composition asks which words appear at all. Same object, different question, and the named-scale work is the one that could say what the composition change is made of.

## Fences carried from the original

- **Single pass, one seat, not audit-grade.** Nothing here has been second-seated.
- **Selection on the outcome, and this is THE limitation to carry.** Level is measured only where the word was emitted. Displaced words appear less often, so the occasions where they do surface may be contexts that demand them unusually strongly. No amount of data fixes this; the forced ladder is the instrument that does not have the problem.
- CANONICAL's fallers are **not null-tested**; risers are. Nothing here may describe fallers as though they were.
- `p_aligned` is floored at theta before log — an epsilon of 1e-9 once turned `murder`'s 44 zero cells into a fabricated 10.5 nats.
- **The sign-test p-values are FLOORS.** With every pair agreeing, `p = 2/2^n` exactly; n=36 floors at 2.91e-11. Four headline values across M06 sit exactly on it. **Quote the sign counts**, which say the same thing without implying a precision the test does not have.
- Superseded en route and not to be quoted: every classified-mover number (a bare majority gave movers 72% of all tokens), the 33-pair figures, and a premature "the tautology objection fails".
