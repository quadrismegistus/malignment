# dn_convention — how often the two dN conventions disagree, over 50 pairs

    python run.py --scope     # panel, embedding cost, axis provenance
    python run.py --run       # -> results/dn_convention.json

`Axis.split()` emits `dN` (mass, unnormalised) and `dN_renorm` (= `N_post − N_base`),
neither promoted, after the ruling at [6374]. They are related by
`dN = T_post·N_post − T_base·N_base`, so **where the arms' apertures differ the two
can point in opposite directions.** This measures how often that happens.

## THE HEADLINE

    pooled over prompts          14.8%        49 pairs, 23,272 prompt-rows
    mean of per-pair rates       14.8%
    per-pair spread              10.7% .. 22.1%   (median 14.5%)

    smallest-|dN| quartile       33.0%     cut PER PAIR, then averaged
    largest-|dN|  quartile        2.3%

**About one prompt in seven cannot be quoted on `dN` at all**, because the two
defensible conventions disagree about which way it moved. Per [6374] rule 2 that
is a refusal, not a caveat.

**But it concentrates hard on near-null prompts.** 33.0% of the smallest-|dN|
quartile against 2.3% of the largest. So the sign question mostly bites where
there was nothing to see — and the prompts carrying the largest movement are
substantially safe. dario's one-pair figures showed the same shape less sharply
(28.0% against 8.2%).

### The quartiles were pooled, and that broke this producer's own ruling

First published as **31.4% / 3.0%**, cut on the pooled `|dN|` across all 23,272
rows. **[6374] rule 3 — mine — says cross-pair comparison of raw `dN` MAGNITUDE
is not licensed, because `dN` carries a per-pair aperture factor.** Sorting every
prompt in the roster by `|dN|` is exactly that comparison. Caught by dario at
[6379], applying my rule to my artifact; I had applied it to everyone else's.

It is not hypothetical. Under the pooled cut the top `|dN|` quartile is
over-represented by:

    RedPajama    294 rows      aperture instability 85.7%
    Amber        266                                82.6%
    llama-7b     247                                72.7%
    stablelm     234                                61.4%
                              (expected ~118 rows/pair if even)

— the four most aperture-unstable pairs in the roster, in order. The bottom
quartile fills with `pythia-2.8b`, `Zamba2`, `Tanuki`, `rwkv`, the stable end.
**The pooled "largest-effect" bucket was ranking apertures as much as effects.**

The corrected figures move little (2.3% against 3.0%) and in the reassuring
direction, so no conclusion changes. The objection was still right, and the small
magnitude is luck rather than vindication. The withdrawn pair is kept in the JSON
as `WITHDRAWN_pooled_cut` so it stays checkable.

**Per-prompt rows are now persisted** (`results/per_prompt.csv`). The first
version wrote aggregates only, so answering "how were the quartiles cut" required
repeating a 50-minute sweep. **An aggregate that cannot be re-cut answers one
question and refuses every other.**

## I PREDICTED THIS WOULD BE HIGHER, AND IT IS NOT

At [6376] I argued dario's 16.2% was **"very likely a FLOOR"**: their pair
(`gl198976/mpt-7b`) is the 9th most aperture-stable of 50, and 41 pairs have more
room for the conventions to diverge. The roster rate is **14.8%** — slightly
*below* their figure — and `mpt-7b` measured on THIS panel is **14.7%**, i.e.
dead on the roster mean despite its aperture rank.

**The mechanism is real but far too weak to carry that inference.** Aperture
instability against per-pair disagreement rate:

    pearson  r = +0.348   p = 0.014
    spearman rho = +0.371  p = 0.009

Significant, positive, and swamped. The extremes make it plain:

    pythia-2.8b      aperture  2%   disagreement 22.1%    <- most stable, worst rate
    RedPajama        aperture 86%   disagreement 16.5%    <- least stable, ordinary rate

**What went wrong in the reasoning, since the arithmetic was fine.** Sign
disagreement needs BOTH the aperture ratio to move AND the `N` ratio to
cooperate. I wrote that sentence in [6376] and then leaned the whole directional
claim on the aperture half. The `N` half dominates, and the quartile split is
what shows it: disagreement tracks `|dN|` being near zero far more strongly than
it tracks aperture. dario's own data already said so — their disagreements
concentrated in the smallest-|dN| quartile — and I read that as a caveat on their
number rather than as the answer to mine.

**The floor claim is withdrawn.** What survives is the ranking itself (mpt is
aperture-stable, 41 pairs have more room) and the [6374] refusal rule, neither of
which depended on it.

## CONSTRUCTION

**The axis is inherited, not chosen.** `LEXICAL_PAIRS` and `pooled_axis` load by
explicit file path from `rank_vs_cardinal/run.py` — which imports the pole set
from `generic_axis/run.py` — so there is one definition, not two. It is
**pre-specified relative to this measurement**: committed at `cbd0ce5` (00:58),
before the aperture and sign-disagreement results existed (`9eb760f`, 01:18), and
byte-identical across all three commits. I had wrongly believed the axis was
still an open decision and declined to run this on that basis; dario's [6377]
corrected it. Agreeing an axis *after* seeing the aperture spread would have been
the post-hoc choice I was trying to avoid — inheriting a pre-registered one is not.

Its licence is its own ceiling, stated rather than re-litigated: pooled, it
reproduces the declared instrument at r = 0.740 against that instrument's own
split-half ceiling of r = 0.828.

**Loading by path, not by name.** Every calibration folder holds a `run.py`, so
`sys.path` + `from run import …` resolves to whichever imported first — and when
this module is itself imported as `run`, to *itself*. The first version did
exactly that. A reuse link that depends on import order is not reuse.

**Panel:** 477 English prompts × 50 pairs, one embedding pass per prompt over the
union of every word any pair needs (300,018 distinct `(prompt, word)`).

## TWO THINGS I NEARLY GOT AWAY WITH

**A tidy population is not a free one.** My first coverage threshold (`≥ n−1`)
dropped `falcon-mamba-7b-instruct` for holding 475 of 477 prompts — two cells —
which quietly made it a 49-pair sweep AND made every pair's prompt count equal,
so that "pooled and per-pair are identical by design" would be true. That is
shaping the population to protect a claim about the population. Threshold is now
90%, the pair is in, counts are `[473, 474, 475]`, and `identical_by_design` is
**False** and reported as such. The two aggregations still agree to 14.82% both
ways — which is now a measurement rather than a definition.

**`recurrentgemma` is computed, reported, and held out of the headline.** It
scores 19.8%. Its passage generations are 95.15%/79.33% word-repetition loops
against a roster median of 1.14% — a vLLM 0.27.1 Griffin fault, not a model
property, and its twp cells are ordinary. That is exactly the case where
excluding could discard real signal, so it is neither silently dropped nor
silently included. **Its admissibility is RH's, not mine and not dario's.**

## WHAT THIS DOES NOT SETTLE

The 14.8% is a rate of *disagreement*, not evidence for either convention. The
[6374] ruling stands on its own argument: `T` is downstream of the treatment
(39/50 aligned arms have higher `T`, p = 9.0e-5; `dT` against top-1 concentration
r = 0.799), so renormalising conditions on a mediator — and not renormalising
asserts the residual sits at `s = 0`, which is false in a known direction. Both
are emitted; neither is "the" number; that is still RH's call.
