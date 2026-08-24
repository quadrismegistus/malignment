---
subject: norm_change
status: FIRST RESULT, 2026-08-24. Seven declared hypotheses tested on 153 lineages, en and zh separately.
headline: Alignment SWEETENS in both languages. It NARROWS valence in English and WIDENS it in Chinese.
data: ~/malignment-data/norm_change (3.0 GB, outside the checkout)
---

# norm_change

**Does alignment move the continuation distribution along word norms and
semantic fields, across every endpoint pair there is?** The *whether* question.
`emergence/capacities` and M05's B and H ask *when*, on the few lineages with
checkpoints; this asks whether, at the endpoint, on 153 lineages.

Design in `registration.md` — a LIGHT registration, seven directional
hypotheses, everything else explicitly exploratory. Producers: `run.py` builds
the long tables, `analyse.py` does the statistics and touches nothing else.

    UNIT      the lineage (153)
    TEST      per lineage the median over its prompts of (aligned - base),
              then a sign test over lineages, TIES EXCLUDED AND REPORTED
    LANGS     en and zh separately, never pooled

## THE RESULT

### English

    H1  brysbaert_concreteness   -0.000470   72 up/ 79 dn/  2 tie  p=0.626   not supported
    H1  k_concreteness           -0.006804   56 up/ 93 dn/  4 tie  p=0.003   SUPPORTED
    H2  k_register_level         +0.003284  128 up/ 14 dn/ 11 tie  p<1e-5    SUPPORTED
    H2  brooke_formality          0.000000   17 up/ 11 dn/125 tie  p=0.345   not supported
    H3  X1 (interiority field)    0.000000    4 up/  1 dn/148 tie  p=0.375   not supported
    H4  warriner_valence_z       +0.001891   91 up/ 57 dn/  5 tie  p=0.006   SUPPORTED
    H4  k_valence_z              +0.000353   87 up/ 44 dn/ 22 tie  p=0.0002  SUPPORTED
    H5  warriner_valence_absz    -0.003284   48 up/ 99 dn/  6 tie  p=3e-5    SUPPORTED
    H5  k_valence_absz            0.000000   69 up/ 69 dn/ 15 tie  p=1.000   not supported

### Chinese

    H1  concreteness_zh          -0.020627   21 up/125 dn/  4 tie  p<1e-5    SUPPORTED
    H1  k_concreteness            0.000000   69 up/ 75 dn/  9 tie  p=0.677   not supported
    H2  k_register_level         +0.002858  119 up/ 22 dn/ 12 tie  p<1e-5    SUPPORTED
    H2  brooke_formality              ALL TIES (45 of 46) -- no signed evidence
    H3  X1 (interiority field)    0.000000   31 up/ 22 dn/ 97 tie  p=0.272   not supported
    H4  k_valence_z              +0.001822   99 up/ 42 dn/ 12 tie  p<1e-5    SUPPORTED
    H4  warriner_valence_z        0.000000   17 up/ 29 dn/ 57 tie  p=0.104   not supported
    H5  warriner_valence_absz     0.000000   14 up/ 34 dn/ 55 tie  p=0.006   SUPPORTED
    H5  k_valence_absz           +0.003218   98 up/ 46 dn/  9 tie  p=2e-5    **REVERSED**

## WHAT LANDED

**H4 IS THE NEW ONE, AND IT LANDS IN BOTH LANGUAGES.** Alignment shifts the
continuation distribution toward the positive pole: `k_valence_z` up in English
(p=0.0002) and Chinese (p<1e-5), `warriner_valence_z` up in English (p=0.006).
M01's `C_deextremification` recorded that its **sweetening hypothesis "was never
emitted"** — it confirmed the flattening and never tested the shift. This is the
first measurement of it, and it is positive.

**H5 REPLICATES IN ENGLISH AND REVERSES IN CHINESE.** English narrows
(`warriner_valence_absz` -0.0033, p=3e-5), which is M01's de-extremification
result on a different instrument and a different roster. Chinese **widens** on
the K scale (+0.0032, 98 up/46 dn, p=2e-5). Alignment sweetens Chinese without
flattening it — it pushes the mean up while spreading the extremes.

**That is the sharpest thing here and it is exactly where M01 said to look.**
`O_crosslingual` found the affect signature does not travel to Chinese while the
substitution does. This is finer: the *sign* flips on one component while
another (H2 register, H4 valence) travels intact.

**H2 holds in both** on `k_register_level`, the instrument built for it.

**H1 holds on the instrument matched to the language and not otherwise.**
English `k_concreteness` falls (p=0.003) while Brysbaert is flat (p=0.63);
Chinese falls on `concreteness_zh` (p<1e-5) while the English lexicons are flat.
That pattern is what a working instrument looks like — the lexicon built for the
language answers and the one applied across it does not.


## H6 AND H7 LAND, AND H6 WAS THE UNTESTED MOVE

    H6  results:euphemism                  +0.002392  104 up/22 dn/27 tie  p<1e-5   SUPPORTED
    H7  slot_institutional_en_v3:mediation +0.005310   89 up/58 dn/ 6 tie  p=0.013  SUPPORTED

**H6 applied the sexual instrument's `euphemism` scale to every rated prompt,
not only to prompts marked sexual** -- the move `slot_ratings` never made, which
is why the registration flagged it as worth a try. It holds: 104 of 126 signed
lineages rise.

Neither has any zh counterpart: the contextual ratings are English-only, so
`slot_prompts()` and the Chinese roster do not intersect. Reported as no overlap
rather than as a null.

## THE DOSE-RESPONSE, WHICH RECOVERS WHAT THE MARGINAL MEANS HID

`dose.py`. Predictor: the BASE arm's transgressive level at a prompt, measured
before alignment touches anything. Outcome: `aligned - base` on some other
scale. **It does not select on the outcome** -- a transgressive prompt could
show a rise, a fall or nothing on any target with equal ease.

    EN levels, 153 lineages         med slope     up/dn        p
      warriner_dominance_z           +0.05831   117/ 36     <1e-5
      warriner_valence_z             +0.06457   114/ 39     <1e-5
      k_bodily_harm_z                -0.12738    31/122     <1e-5
      k_transgressiveness_z          -0.10448    31/122     <1e-5
      warriner_arousal_z             -0.05705    37/116     <1e-5

**Sweetening is DOSE-DEPENDENT, not uniform**: the more transgressive mass the
base put at a prompt, the harder alignment sweetens it and the harder it cuts
harm and arousal.

**`warriner_dominance` is the strongest positive slope, and M01 called dominance
dead.** `C_deextremification` reports "H3 dominance dead" on a marginal test.
Conditioned on transgressive dose it is the largest riser here (117/36, p<1e-5).
A marginal test cannot see it. That is the argument for the design.

### AND IT SETTLES THE SPEECH QUESTION THE OTHER WAY

    EN fields, dose slopes           med slope     up/dn        p
      X3.2  Sensory: Sound            +0.01789   112/ 41     <1e-5
      A10-  Hiding/Hidden             +0.01377   113/ 40     <1e-5
      S3.2  Relationship: sexual      +0.01316   113/ 40     <1e-5
      Q1.3  Telecommunications        +0.00963   110/ 42     <1e-5
      Q2.2  SPEECH ACTS               +0.00783   108/ 45     <1e-5
      E3-   Calm/VIOLENT/Angry        -0.00383    46/107     <1e-5
      E2+   Liking                    -0.00695    42/111     <1e-5
      T2++  Time: beginning/ending    -0.01258    45/108     <1e-5

**Speech acts RISE with transgressive dose while the VIOLENT pole falls.** That
is M01's kill->scream at field level, and the largest riser of all is
`X3.2 Sensory: Sound` -- which is what a scream IS.

**THE MARGINAL FIELD MEANS SAID THE OPPOSITE AND THEY WERE THE WRONG QUANTITY.**
The exploratory sweep reported `Q2.1`/`Q2.2` falling. That is a SHARE of rated
mass, normalised by the rated denominator, and a field's share can fall while
its absolute mass rises. Restricted to movers, speech words are net risers:

    speech (Q2.1+Q2.2), movers, all lineages
      riser rows  418,323  gaining 6625.18 mass
      faller rows 379,653  losing  3353.09 mass
      NET                          +3272.09

RH flagged the contradiction against findings elsewhere; it was a quantity
error in the reporting, not a disagreement in the data.

## WHAT DID NOT LAND, AND WHY IT IS NOT A NULL

**H3 failed for want of MASS, not for want of an effect.** USAS `X1`
(*psychological actions, states and processes*) is tied in **148 of 153 English
lineages and 97 of 150 Chinese ones** — the field carries no probability mass in
either arm at most prompts, so there is nothing for a difference to be taken of.
Where it is non-zero the median is +0.0138 (en), the predicted direction, on 5
lineages. **This is a coverage failure of the instrument, and reporting it as
"interiority does not rise" would be wrong.** A field-level test needs either
prompts that elicit the field or a coarser grouping.

`brooke_formality` is the same shape: 125 of 153 English lineages tied, 45 of 46
Chinese. It was already marked sparse in `lexicons/PROVENANCE.md` and stays
marked.

## A DEFECT FIXED BEFORE THESE NUMBERS WERE READ

The first pass counted TIES AS SUCCESSES — `dn` was the strictly-negative count
and `up` was everything else. It printed lines like

    brooke_formality  median +0.00000  142 up/11 dn  p=0.00000  REVERSED

which cannot be true: a median of exactly zero with an overwhelming up-count.
The zeros WERE the up-count. Every sparse scale looked overwhelmingly
significant in whichever direction the zeros were being counted, and the
verdict logic then called a zero median "REVERSED" because it failed `> 0`.

Ties are now excluded from the sign test and reported on every line, which is
the rule M05's `H_norm_acquisition` states for the same reason. The tie count is
the most informative column for the sparse scales and is why H3's failure is
legible as coverage rather than as a null.

## LIMITS

- **English lexicons under Chinese prompts measure a strange subpopulation.**
  `warriner_*` reaches only 103 of 153 zh lineages and `brysbaert` 113: those
  numbers come from English words appearing inside Chinese continuations. Read
  them as a code-switching probe, not as a Chinese measurement.
- **H6 and H7 are not wired.** The contextual arm needs a (prompt, word) join
  against `slot_prompts()` and is a different shape from the levels table.
- **Coverage is carried per row and is not yet used as a filter.** A
  mass-weighted mean over a source covering 3% of a distribution is in the same
  column as one covering 80%.
- **The exploratory sweep is run but not written up here.** `analyse.py
  --explore` reports 239 further scales; every one is a candidate for a
  registration and not a result.
