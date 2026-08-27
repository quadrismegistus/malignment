---
subject: norm_change
status: FIRST RESULT, corrected 2026-08-24. 50 endpoint lineages, en and zh separately.
headline: Register rises and valence rises in BOTH languages. Concreteness falls in Chinese only.
data: ~/malignment-data/norm_change (3.0 GB, outside the checkout)
---

# norm_change

**Does alignment move the continuation distribution along word norms and
semantic fields, across every endpoint pair there is?** The *whether* question.
`emergence/capacities` and M05's B and H ask *when*, on the few lineages with
checkpoints; this asks whether, at the endpoint.

Design in `registration.md` — a LIGHT registration, seven directional
hypotheses, everything else explicitly exploratory. `run.py` builds the long
tables, `analyse.py` does the statistics, `dose.py` the conditional version.

    UNIT      the lineage: 50 base->endpoint pairs from `roster.endpoints()`
    TEST      per lineage the median over its prompts of (aligned - base),
              then a sign test over lineages, TIES EXCLUDED AND REPORTED
    LANGS     en and zh separately, never pooled

## THE UNIT WAS WRONG IN THE FIRST VERSION, AND IT CHANGED TWO CONCLUSIONS

Every number first published from this folder used **n=153**, the count of
distinct `(base, aligned)` pairs in `movement`. That table is not a roster: it
holds RUNGS (base->SFT, SFT->DPO) and TRANSITIVE pairs as well as endpoints,
because `produce_movement` builds both on purpose — a word can fall at SFT and
rise at DPO, so base->DPO is not recoverable from the rungs.

153 edges sit over **85 base models**. `Llama-3.1-8B` alone contributes 11. So
one pretrained model was voting eleven times in a test whose unit is the
lineage. RH caught it: *"153 lineages? We have 50."*

`roster.endpoints()` resolves **50**, all present in `movement`; the other 103
edges are dropped. It exists precisely so this rule is not retyped per
experiment — its own docstring records four shell heredocs that each filtered
differently, one matching `"lmo" in base` and so finding 4 of 6 OLMo lineages.

**What the inflation had manufactured:**

    H1 concreteness, ENGLISH   n=153  p=0.003   SUPPORTED
                               n= 50  p=0.119   not supported
    H5 |valence|, CHINESE      n=153  p=2e-5    REVERSED (widening)
                               n= 50  p=0.135   not supported

The Chinese "widening" was the previous headline of this file. It does not
survive the correct unit. **Neither claim should be cited from any earlier
version.**

## THE RESULT, 50 ENDPOINT LINEAGES

### English

    H2  k_register_level         +0.006298   45 up/ 4 dn/ 1 tie  p<1e-5    SUPPORTED
    H2  k_register_level_z       +0.007063   45 up/ 5 dn/ 0 tie  p<1e-5    SUPPORTED
    H4  warriner_valence         +0.009693   32 up/16 dn/ 2 tie  p=0.029   SUPPORTED
    H4  k_valence                +0.002638   32 up/11 dn/ 7 tie  p=0.002   SUPPORTED
    H5  warriner_valence_absz    -0.007682   16 up/34 dn/ 0 tie  p=0.015   SUPPORTED
    H6  euphemism                +0.003428   38 up/ 6 dn/ 6 tie  p<1e-5    SUPPORTED
    H7  mediation                +0.026846   33 up/16 dn/ 1 tie  p=0.021   SUPPORTED
    H1  k_concreteness           -0.024823   19 up/31 dn/ 0 tie  p=0.119   not supported
    H1  brysbaert_concreteness   -0.002776   21 up/27 dn/ 2 tie  p=0.471   not supported
    H3  X1 (interiority field)    0.000000    2 up/ 1 dn/47 tie  p=1.000   not supported
    H5  k_valence_absz           -0.000166   22 up/25 dn/ 3 tie  p=0.771   not supported

### Chinese

    H1  concreteness_zh          -0.032509    8 up/40 dn/ 0 tie  p<1e-5    SUPPORTED
    H1  concreteness_zh_z        -0.040895    8 up/40 dn/ 0 tie  p<1e-5    SUPPORTED
    H2  k_register_level         +0.006170   38 up/ 5 dn/ 7 tie  p<1e-5    SUPPORTED
    H4  k_valence                +0.002547   33 up/10 dn/ 7 tie  p=0.0006  SUPPORTED
    H1  k_concreteness           -0.009366   18 up/29 dn/ 3 tie  p=0.144   not supported
    H3  X1 (interiority field)    0.000000   12 up/ 6 dn/30 tie  p=0.238   not supported
    H5  warriner_valence_absz     0.000000    6 up/12 dn/13 tie  p=0.238   not supported
    H5  k_valence_absz           +0.005072   28 up/17 dn/ 5 tie  p=0.135   not supported
    H6/H7                        no rated (prompt, word) overlap in zh

## WHAT LANDED

**H2 REGISTER RISES IN BOTH LANGUAGES, and it is the strongest result here.**
45 of 49 signed English lineages, 38 of 43 Chinese, p<1e-5 both. On
`k_register_level`, the instrument built for it.

**H4 VALENCE RISES IN BOTH LANGUAGES, and it had never been tested.** M01's
`C_deextremification` records that its sweetening hypothesis "was never
emitted" — it confirmed the flattening and never measured the shift. English
`warriner_valence` +0.0097 (p=0.029) and `k_valence` +0.0026 (p=0.002); Chinese
`k_valence` +0.0025 (p=0.0006).

**H5 NARROWING SURVIVES IN ENGLISH ONLY**, on Warriner (16 up/34 dn, p=0.015) —
M01's de-extremification on a different instrument and roster. `k_valence_absz`
is flat in English and in Chinese. **The Chinese REVERSAL reported earlier was
an artefact of the wrong unit and is withdrawn.**

**H1 CONCRETENESS FALLS IN CHINESE AND NOT IN ENGLISH.** `concreteness_zh`
-0.0325, 8 up/40 dn, p<1e-5 — one of the cleanest splits in the folder. English
`k_concreteness` moves the right way (-0.0248, 19 up/31 dn) but does not clear
the bar at n=50. So the cross-lingual asymmetry is real but the OPPOSITE way
round from the earlier version: Chinese de-concretizes, English does not.

**And the instrument still has to match the language.** The English lexicons are
flat under Chinese prompts and vice versa; only the lexicon built for the
language answers.

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

    EN levels, n=153 -- WITHDRAWN, awaiting recomputation on 50
                                    med slope     up/dn        p
      warriner_dominance_z           +0.05831   117/ 36     <1e-5
      warriner_valence_z             +0.06457   114/ 39     <1e-5
      k_bodily_harm_z                -0.12738    31/122     <1e-5
      k_transgressiveness_z          -0.10448    31/122     <1e-5
      warriner_arousal_z             -0.05705    37/116     <1e-5

**SUPERSEDED by the `summary.py` table above, which is on 50 lineages. The
numbers in this section are the old n=153 ones and are NOT to be cited.** They inherit the same pseudo-replication the declared tests did;
`dose.py` now restricts to `endpoint_pairs()` but has not been re-run.
The DESIGN is unaffected -- the predictor is still measured before
alignment and still does not select on the outcome.

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


## MARGINAL vs DOSE, ONE TABLE (`summary.py`)

Two questions about every scale on the same 50 lineages. MARGINAL: does it move
under alignment on average? DOSE: does it move MORE where the base arm was more
transgressive? They can disagree in every combination, which is why they print
together.

### English levels

    scale                       MARGINAL          DOSE              reading
    k_register_level          +0.0063 p<1e-5*   +0.0025 p=0.67    MARGINAL ONLY
    k_register_level_z        +0.0071 p<1e-5*   +0.0028 p=0.67    MARGINAL ONLY
    k_bodily_harm_z           -0.0043 p<1e-5*   -0.2125 p<1e-5*   both
    k_transgressiveness_z     -0.0033 p<1e-5*   -0.1687 p<1e-5*   both
    warriner_arousal_z        -0.0185 p<1e-5*   -0.0773 p=9e-5*   both
    k_vulgarity_z             -0.0000 p=2e-5*   -0.0577 p<1e-5*   both
    warriner_valence          +0.0102 p=0.029*  +0.1200 p=2e-5*   both
    k_valence                 +0.0040 p=0.002*  +0.0806 p=3e-4*   both
    k_concreteness            -0.0248 p=0.119   -0.1105 p=1e-5*   DOSE ONLY
    brysbaert_concreteness    -0.0042 p=0.471   -0.0291 p=3e-4*   DOSE ONLY
    warriner_dominance_z      +0.0061 p=0.085   +0.0922 p=9e-5*   DOSE ONLY
    k_charge                  +0.0034 p=0.533   -0.0986 p=2e-5*   DOSE ONLY

### THREE SHAPES, AND THE SHAPE IS THE RESULT

**MARGINAL ONLY — moves everywhere alike.** `k_register_level` is the clearest
thing in this folder marginally (45 up/4 dn, p<1e-5) and has NO dose slope at
all (p=0.67). **Register rises across the board and not as a response to
transgression.** It is a global stylistic shift, not a safety behaviour.

**DOSE ONLY — moves only where the frame is loaded.** Concreteness, dominance
and charge are flat on average and steep under dose. **H1 is rescued in a
specific form: concreteness does fall, but only at transgressive prompts.**

**And `warriner_dominance` is the case M01 got marginally and missed.**
`C_deextremification` reports "H3 dominance dead". Marginally here it is dead
too (p=0.085). Under dose it is +0.092, p=9e-5. A marginal test cannot see it;
the finding is not wrong, it is incomplete.

**BOTH — falls generally and falls harder where loaded.** The transgression
cluster: bodily_harm, transgressiveness, vulgarity, arousal. Valence rises both
ways.

### THE SPEECH ANSWER, EXACTLY

    Q2.2 Speech acts   MARGINAL -0.0130 p=0.003*   DOSE +0.0079 p=0.015*

**Opposite signs, both significant.** Speech mass falls on average across all
prompts and RISES where the base arm was transgressive. That is why the marginal
sweep and M01's kill->scream direction looked like a contradiction: they are
different conditions, and only the dose version is about displacement.

### Chinese levels — a DIFFERENT structure, not a weaker one

    concreteness_zh           -0.0325 p<1e-5*   +0.0049 p=0.56    MARGINAL ONLY
    k_register_level          +0.0075 p<1e-5*   +0.0057 p=0.56    MARGINAL ONLY
    k_bodily_harm_z           -0.0009 p<1e-5*   -0.1148 p=0.003*  both
    k_valence                 +0.0038 p=6e-4*   +0.0646 p=0.008*  both
    k_concreteness            -0.0160 p=0.144   -0.1088 p=0.001*  DOSE ONLY

**Concreteness is MARGINAL ONLY in Chinese and DOSE ONLY in English**, on each
language's own instrument. Chinese de-concretizes everywhere; English does it
only under transgressive load. Same direction, different trigger — which is a
sharper cross-lingual claim than "the signature does not travel".


## "FEW LARGE FALLERS, MANY SMALL RISERS" — REPLICATES MARGINALLY, INVERTS UNDER DOSE

M01 `T_category_flow.md` §14, *displacement along a chain*: **206 risers against
36 fallers, fallers 3.8x larger each** (-0.01267 vs +0.00334), Mann-Whitney
p=5.8e-09, "the ratio exceeds one in every lexicon". USAS specifically: 41
risers, 4 fallers, 5.0x.

That section's own discipline, which is followed here: **"Quote the magnitude;
quote the count with its resolution."** The 206/36 count is carried by the
fine-grained lexicons and is partly a statement about granularity; the magnitude
ratio is what travels.

Tested on this folder's USAS fields, 50 endpoint lineages, categories that clear
p<0.05:

    condition        risers  fallers   mean riser   mean faller   ratio    MW p
    en MARGINAL           6        3     +0.00436      -0.00860   1.97x   0.197
    zh MARGINAL          27       73     +0.00068      -0.00183   2.70x   1.4e-05
    en DOSE              25       40     +0.01448      -0.00751   0.52x   0.034
    zh DOSE              20       23     +0.00418      -0.00341   0.81x   0.061

**MARGINALLY, THE MAGNITUDE RATIO REPLICATES.** English 1.97x and Chinese 2.70x
against M01's 3.8x, same direction, and Chinese reaches p=1.4e-05. Fallers are
individually larger than risers, which is the chain shape.

**THE COUNT DOES NOT, AND M01 SAID IT WOULD NOT.** Chinese gives 73 fallers to
27 risers — inverted. English has only 9 surviving categories against M01's 45
for USAS, so its p=0.197 is a power statement, not a refutation. Both are the
granularity caveat M01 recorded, arriving as predicted.

**UNDER DOSE THE ASYMMETRY REVERSES, and that is new.** Where the base arm was
transgressive the ratio is 0.52x in English (p=0.034): **few large RISERS, many
small fallers** — the mirror image of the marginal shape. Mass does not drain
from a few categories into many; it concentrates into a few.

Read with the speech result that is the same shape: `Q2.2` falls marginally and
rises under dose. **The chain-displacement picture is a property of the average
prompt. At a transgressive prompt the model is not spreading mass down a chain,
it is moving it somewhere in particular.**

### What this comparison is NOT

M01 counted **Bonferroni survivors** — categories whose delta is consistent
across 43 edges by a one-sample t. This counts categories clearing p<0.05 on a
sign test over 50 lineages. Different selection rules on different rosters with
different lexicon coverage, so **the ratios are comparable in direction and not
in value**, and none of these four rows is a replication in the strict sense.


## THE CONTEXTUAL RATINGS, SAME TREATMENT

`summary.py --table contextual`. 115 scales over the prompts where
`slot_ratings` and the endpoint roster overlap. English only — the contextual
instruments have no Chinese counterpart.

    scale                                MARGINAL            DOSE            shape
    slot_institutional_v3:vocalisation  -0.0099 p=0.480   +0.3862 p=9e-5*   DOSE ONLY
    slot_institutional_v2:vocalisation  -0.0119 p=0.253   +0.3369 p=2e-5*   DOSE ONLY
    slot_rating_v6:makes_better         +0.0512 p<1e-5*   +0.2718 p<1e-5*   both
    slot_rating_v6:makes_worse          -0.0247 p<1e-5*   -0.2566 p<1e-5*   both
    slot_institutional_v3:termination   -0.1270 p<1e-5*   -0.3142 p=2e-5*   both
    slot_institutional_v3:deference     +0.0477 p<1e-5*   +0.2277 p=0.033*  both
    slot_rating_v6:deliberation         +0.0212 p=1e-5*   +0.1725 p=0.003*  both
    slot_institutional_v3:abstraction   +0.1077 p<1e-5*   +0.0798 p=0.480   marginal only
    slot_institutional_v3:procedural    +0.0925 p<1e-5*   +0.0906 p=0.119   marginal only
    slot_rating_v6:fit                  +0.0918 p<1e-5*   -0.0259 p=0.203   marginal only
    results:euphemism                   +0.0043 p<1e-5*        --           marginal only

### VOCALISATION IS DOSE ONLY, AND TWO INSTRUMENT VERSIONS AGREE

`vocalisation` is **flat marginally and among the steepest slopes in the folder
under dose** — +0.386 (p=9e-5) on `slot_institutional_en_v3` and +0.337
(p=2e-5) on v2, two instrument versions rating independently.

**This is the same finding as the USAS fields, from an unrelated instrument.**
The lexicon route gave `Q2.2 Speech acts` +0.0079 and `X3.2 Sensory: Sound`
+0.0179 under dose; the LLM-coded contextual route gives `vocalisation` +0.386.
One is a word list, the other is a model rating a word in its frame. **Where the
base arm was transgressive, alignment moves toward speaking.** Two instruments,
one direction, and neither was built to test the other.

### PROCEDURALISATION IS MARGINAL, DEFERENCE IS BOTH

`abstraction` and `procedural` rise marginally with no dose slope: alignment
proceduralises **everywhere**, not as a transgression response. `deference`
rises both ways, harder under load. And `termination` FALLS on both — the
aligned model is less likely to reach for quitting, and much less so at a loaded
prompt.

That is F21's shape arriving through a different door: the individual is
proceduralised and made deferent, and the exit is closed.

### makes_better UP, makes_worse DOWN, BOTH WAYS

+0.272 and -0.257 under dose, both p<1e-5, and both significant marginally too.
The most direct statement of the alignment objective in the whole folder, and it
is dose-dependent: the worse the base frame, the harder the model steers toward
making it better.

### H6 EUPHEMISM IS MARGINAL ONLY

+0.0043, p<1e-5 marginal, no dose slope resolvable. Euphemism rises across the
rated prompts generally rather than specifically where transgression sits — the
same shape as register.


## WHAT THE DOSE EFFECTS LOOK LIKE AS WORDS (`examples.py`)

A slope over 50 lineages cannot be checked by reading. `examples.py` ranks
prompts by BASE-arm transgressive level — outcome-blind, the same discipline
`dose.py` rests on — and prints the words whose movement contributes most to the
target scale, ranked by `(p_aligned - p_base) * value` rather than by how far
they moved.

### English, `k_concreteness` — a DOSE ONLY scale

    prompt: 'He was so furious with the prisoner he wanted to'
    rank 1 of 2,245 en prompts, base transgressive level 3.520

    FALLING                          RISING
      kill      -7.45  delta -1.490    strangle  +3.06  delta +0.510
      shoot     -2.26        -0.377    take      +2.04        +0.681
      cut       -0.99        -0.165    tear      +1.44        +0.240
      hang      -0.57        -0.094    break     +1.16        +0.233
      murder    -0.40        -0.100    throw     +0.99        +0.165
      kick      -0.39        -0.056    shake     +0.86        +0.171
      burn      -0.26        -0.043    punish    +0.84        +0.280

### Chinese, `concreteness_zh` — a MARGINAL ONLY scale

    prompt: '她拔出刀，她想要'   ("She drew the knife, she wanted to")
    rank 1 of 416 zh prompts, base transgressive level 2.771

    FALLING                          RISING
      报仇 revenge     -0.065         结束 to end        +0.823
      自己 oneself     -0.038         保护 to protect    +0.290
      干掉 to finish off -0.035       伤害 to harm       +0.237
      结果 to kill     -0.025         离开 to leave      +0.180
      抓住 to seize    -0.023         自杀 suicide       +0.163
      解剖 to dissect  -0.014         证明 to prove      +0.161
      反击 to strike back -0.003      刺杀 to assassinate +0.086

### THE DISPLACEMENT IS LATERAL IN BOTH LANGUAGES, AND THAT IS THE POINT

The specific lethal verb drains — `kill`, `shoot`, `murder`; 干掉, 报仇 — and
the mass does NOT simply go to safety. `strangle` RISES in English. 自杀
(suicide) and 刺杀 (assassinate) RISE in Chinese. Alongside them: `punish`,
`break`, `throw`; 保护 (protect), 结束 (to end).

**So it is not suppression and it is not sweetening. One word is removed and
its neighbours absorb the mass**, some of them no less violent than the word
that left. That is chain displacement seen at word grain, in two languages, and
it is what a scale-level mean necessarily hides.

It also matches what `malign` reported independently at [6559] on the
cross-frame contrast: `kill` falling into `break`, `cry`, `hit`, `punch`,
`smash` — semantic neighbours inside the field of anger-and-violence.

## RAW->RAW, AND WHY THAT IS A NOTE RATHER THAN A CAVEAT

`movement` is a raw -> raw contrast, and malign reports at [6559] that on OLMo-3
some displaced mass lands on exam-template blanks rather than on words. That is
worth knowing and it is NOT a confound for these numbers:

- **Blank-fill is rare store-wide and concentrated** -- measured previously as
  74% of a single Olmo-DPO cell, not a corpus-wide property.
- **Blanks carry no rating**, so they leave both the numerator and the
  denominator of every mean here. Rated-mass coverage is HIGHER in the aligned
  arm (median 0.6225 against 0.5730; aligned lower in only 32.2% of 110,767 en
  cells).
- The effects above are measured over 50 lineages and hundreds of scales, and
  are an order of magnitude larger than anything one model's formatting could
  carry.

The cross-frame contrast is a better instrument for WHERE the mass goes, and is
worth having for that reason rather than as a repair to this.


## MAGNITUDE MOVED OUT

"Does more mass move where the base is transgressive?" is now its own folder:
`../rate_and_magnitude/`. It confirms M01's magnitude result in English
(+0.0111 departed, 41 of 50 lineages), does NOT reproduce M01's rate null
(n_movers +1.81, 44 of 50), and INVERTS in Chinese — less mass moving while more
words move, a dispersal. It shares this folder's dose predictor and lineage
roster and is not a copy of either.

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

## THE AGGREGATE / INDIVIDUAL DISTINCTION, AND named_under_dose

This folder's dose slopes are large and highly significant -- `k_concreteness`
MARGINAL p=0.119 against DOSE p=1e-5, and so on. `experiments/displacement/
named_under_dose/` asks a dose question too and finds a flat NULL. Both are right,
and the pair is more informative than either alone.

    here                  x = base-arm k_transgressiveness at the prompt
                          y = aligned - base on the TARGET scale, a LEVEL SHIFT of
                              the mass-weighted mean
                          OLS slope, sign test over 50 lineages, nothing held out

    named_under_dose      outcome = which way an INDIVIDUAL word moved, +1/-1
                          held out by WORD, AUC in a low- against a high-dose stratum

**This folder asks how far the distribution slides along a named scale. That one
asks how well a word's ratings say which way that word goes.** Dose can scale the
AMOUNT of movement without changing its SORTABILITY: if a loaded frame pushes every
word further down concreteness, the mean moves much more while which particular
words rise stays exactly as predictable. Turning up the volume does not make the
signal easier to classify.

Three differences push the same way -- unit (50 lineages against held-out words),
fitted against held-out, aggregate against individual. The last is what Findings P's
ICC of 0.131 names: 82-87% of the fall/rise variance is WITHIN a word across sites,
which an aggregate averages away and an individual test cannot.

**So a dose slope here is not evidence that a named scale predicts displacement**,
and the absence of one there is not evidence that dose does nothing. They are
different questions about the same data.

### MEASURED, not just argued: `dose.py --contextual`

The flag runs all three tables -- word norms, USAS fields, contextual slot ratings --
on the SHARED PROMPT SET, i.e. only prompts carrying contextual ratings (2,344 of
2,717, 86%; before 2026-08-25 it would have been 279, about 10%). Subsetting every
table is what makes it a GRAIN comparison: the rated prompts were chosen by whoever
built the instrument and are not a random sample, so word-level-on-everything against
contextual-on-the-rated-subset would be a population difference in a grain costume.

`harm` is the one construct measured both ways, and the aggregate dose slopes are
indistinguishable:

    word-level  k_bodily_harm   -0.18702   7/43   p<1e-5
    contextual  v6:harm         -0.16747   8/42   p<1e-5

Set against the held-out individual-direction result from `named_under_dose` on the
same day:

                        aggregate dose slope   individual direction (held out)
    word-level norms         -0.187                 +0.0340 .. +0.0609
    contextual, same 12      -0.167                 +0.0875 .. +0.0964  disjoint

**Grain matters for predicting WHICH WORD MOVES and not at all for HOW FAR THE
DISTRIBUTION SLIDES.** That is what Findings P's ICC of 0.131 implies: 82-87% of the
fall/rise variance is WITHIN a word across sites, which a site-level rating can see
and an aggregate averages away before the statistic is computed.

Caveats: ONE construct pair, and `k_bodily_harm` ("does this word denote bodily
harm", out of context) and `v6:harm` ("how much harm does this action cause in this
scene") are close but not identical constructs. The raw significance counts (levels
31/38, contextual 23/48) are NOT the test -- they compare different target sets.

### KNOWN DEFECT IN THE CONTEXTUAL TARGET SET

`contextual()` excludes only `scale == "ratable"` and admits every other numeric
field, so the pre-existing v6 files' movement bookkeeping is carried in AS DOSE
TARGETS: `v6` reports 18 scales where the instrument has 12, the extras being
`net`, `rise`, `fall`, `net_rate`, `n_eligible`, `n_present`. Same root cause as the
leak fixed in `named_under_dose/predict.py` -- a denylist of known bookkeeping names
admits every new one.

Bounded, not harmless: none of them reached any significant list, and a dose SLOPE on
`net` is a real if uninteresting quantity rather than the circular PREDICTION the
predict.py leak produced. But they inflate the tested-target denominator and a reader
would reasonably assume every row is a rating. Three strays covering 2 prompts each
(`v6full`, `v6_wide`, `results`) are also in the table. Fix is to name the twelve v6
scales explicitly and rebuild; NOT done at time of writing.

## THE DOSE IS NOT MEASURING WHAT IT IS NAMED FOR

Examined 2026-08-26, on RH's question of whether `k_transgressiveness` is enough.
It is not, and the problem is the construct rather than the statistic.

### 1. THE RANGE IS ALMOST ALL FLOOR

    scale                     min     p50     p90     max    IQR/range
    k_transgressiveness     1.000   1.025   1.307   6.000       0.02
    k_vulgarity             1.000   1.000   1.015   4.762       0.00
    k_bodily_harm           1.000   1.019   1.331   5.717       0.02
    k_charge                1.000   1.354   2.223   6.205       0.11
    k_concreteness          1.000   3.038   4.966   7.000       0.28

**63.4% of 4,055 en prompts sit within 5% of the floor**, and the median split this
folder has used cuts at 1.0558 -- INSIDE the floor cluster. So "low dose" has been
pure floor and "high dose" everything from barely-above-floor upward. That is the
range restriction this campaign documented against M01's minimal pairs
(`M01_RECONSIDERED.md`: two arms differing by 3% of the available range), and it
means **any null from this dose may be attenuated rather than absent.**

### 2. AND IT IS NOT THE AVERAGING

    mass3_transgressiveness   p50 = 0.0025      mass5_transgressiveness  p50 = 0.0000
    max_transgressiveness     p50 = 5.0000, IQR/range 0.500 -- 12x the mean's spread

The median prompt genuinely has 0.25% of its base-arm mass on transgressive words.
A tail statistic buys spread (`max` most of all) but does not manufacture content
the corpus does not have. `k_vulgarity` is unusable under every definition.

### 3. WHAT THE SPOT-CHECK SHOWED, WHICH IS THE REAL PROBLEM

Under all three definitions, quid-pro-quo coercion sits at the FLOOR and physical
violence at the TOP:

    LOW   'The student was told her recommendation letter would depend on whether...'
    LOW   'The floor manager explained that the promotion hinged on the cashier not...'
    MED   'He held the pillow down on the mattress in the dark and'
    HIGH  'He swung the broken bottle at his coworker outside the bar and'

**So the "dose" contrast has substantially been a VIOLENCE-versus-INSTITUTIONAL
contrast, not transgressive-versus-neutral** -- and the institutional material is
exactly what the F21 argument runs on.

`max` exposes the mechanism: `'He grabbed her by the arm and dragged her toward
the'` scores 2.0, LOW. It is an assault, but the slot solicits a NOUN, so no
candidate is lexically transgressive. The dose conflates three things and only the
first is what it names:

    1. how transgressive the SCENE is
    2. whether the SLOT solicits transgressive vocabulary
    3. what the BASE MODEL happened to offer there

### 4. AND A PROMPT-LEVEL RATING WOULD NOT FIX IT EITHER

RH's objection, and it is the binding one: **there is no guarantee that what a
lexicon calls transgressive is transgressive TO THE MODELS.** Rating frames instead
of words replaces one imposed notion with another. It is not a calibration problem.

Defining dose by what alignment suppresses is circular -- precisely the trap
`dose.py`'s own docstring is written against, "conditioning on words that MOVED,
and then reporting that moved words moved".

**The way out is to split the MODELS, not the words.** Derive the dose from movement
in one half of the 50 lineages, test the dose-response on the held-out half. Within
a fold nothing is circular, because the models supplying the dose are not the models
supplying the outcome, and the dose is then in the models' own terms. The
disagreement between a lexical dose and a model-derived one becomes the measurement:
if institutional coercion is floor on `k_transgressiveness` and high on a
model-derived dose, that is direct evidence that **what alignment polices is not
what a transgressiveness lexicon names.**

Two cautions: aligned models share training signal, so this BOUNDS circularity
rather than removing it -- "held out across models", never "independent"; and the
split must be declared before looking, or it is a garden of forking paths over which
half defines the dose.

**Until that is run, results in this folder should be described as a lexical-proxy
contrast, not a dose-response.**

## THREE DOSES, AND WHAT SURVIVES ALL THREE

The dose examined above is a global word lexicon and it is floor-bound. Two
replacements were built and `dose.py` now runs any of them, each writing FULL tables
under its own filename so no run can silently overwrite another:

    --dose k_transgressiveness   global lexicon, ~2,700 prompts   (default)
    --slot-dose                  loaded words tagged per prompt from a 200-word
                                 union list, 1,944 prompts
                                 (instrument_calibrations/dose_response)
    --v6-dose                    base-arm mass on words at contextual v6_harm >= 4,
                                 744 prompts, COSTS NOTHING -- the ratings exist

All three are per (lineage, prompt): the tags are prompt-level in every case, but
the MASS WEIGHTING is per lineage, because models put different probability on the
loaded words. RH's point, and it is why a prompt-level rating still yields a
lineage-varying dose.

### THE CONVERGENCE, WHICH IS THE RESULT

    levels          lexical vs slot     n=38   corr +0.948   sig both 24 (of 31/27)
                    lexical vs v6_harm  n=38   corr +0.952   sig both 26 (of 31/27)
                    slot    vs v6_harm  n=39   corr +0.862   sig both 20 (of 28/28)

    significant under ALL THREE: 19 of 38, and all 19 agree in SIGN.
      k_bodily_harm, k_charge, k_transgressiveness_z, k_valence_absz,
      warriner_arousal, warriner_arousal_absz, and 13 more

**Three doses built from three unrelated instruments** -- a type-level lexicon, an
LLM tagging loaded completions, and contextual harm ratings made months earlier for
another purpose -- **agree at +0.86 to +0.95 on which word-level norms respond, with
no sign disagreement among the 19.** That makes the levels dose-response robust to
how the dose is constructed, which no single run could establish.

It also retires a suspicion raised earlier in this file: the floor-bound lexicon
ranks prompts well enough to reproduce the answer, so its compression is a power
problem and not a validity one.

### DE-CONCRETISATION SURVIVES

                              LEXICAL              SLOT               V6_HARM
    brysbaert_concreteness  -0.0257 12/50 *   -0.0099 21/50     -0.0288 16/50 *
    k_concreteness          -0.1023  9/50 *   -0.0417 21/50     -0.0529 13/50 *

Same sign in all three, significant in two, and the v6 dose is INDEPENDENT of the
lexical one -- different instrument, contextual rather than type-level. So the
effect is not `k_transgressiveness` regressing against its own lexicon, which was
the leading suspicion when the slot dose nulled it. The within-domain test points
the same way: restricted to institutional prompts the lexical slope STRENGTHENS to
-0.214, which is the opposite of what a between-domain artifact does.

The slot dose is the outlier at exactly 21/50 on every variant, and it is the least
trustworthy of the three -- see `dose_response/README.md` for its two failure modes.

### WHAT DOES NOT SURVIVE

    contextual   lexical vs v6_harm  corr +0.359   significant in all three: 2 of 34
    fields       lexical vs slot     corr +0.508   77 of 267 targets FLIP SIGN

The institutional and sexual slopes reported above rest on ONE dose. And `fields` was
never testable in this form -- see the next section.

### THE FIELDS TABLE IS MEASURING A CONSTANT

A USAS field is categorical: a word carries it or does not, weight 1. So the
"mass-weighted mean over rated words" is the mean of 1.0 over words whose value is
1.0 -- **every field's level is exactly 1.000 in both arms**, and 69.1% of
level-deltas are EXACTLY ZERO. The informative column was beside it all along:
`base_cov`, the share of mass the field holds, whose deltas are 0.0% zero.

    field    med level   p90 level   med coverage
    I3.1-      1.00000     1.00000       0.003
    T2+        1.00000     1.00000       0.010

Every `fields` number in this folder regresses that constant. RH found it by asking
why the slopes were so small. NOT YET FIXED: `contextual()` and the dose path need to
read coverage rather than level, and the table rebuilt.

## ROBUST UNDER 2 OF 3 DOSES: THE FEATURE TABLE

`dose_agreement.py` -> `dose_agreement.csv`. **A feature significant on >=2 of the
three doses WITH CONSISTENT SIGN is ROBUST**; on 3 of 3 it is unanimous. One dose is
not enough because each has a known and DIFFERENT defect -- the lexicon is
floor-bound and ranks coercion below knife attacks, the slot tagging collapses where
the loaded option is rare and saturates where the transgression is in the setup, and
v6_harm shares the second while covering 744 prompts against 1,944 and ~2,700.
Because the defects differ, agreement is evidence about alignment rather than about
how loadedness was measured.

    table         targets    3 of 3    2 of 3    ROBUST   contradictory
    levels             38        19        12        31        0
    fields            278        12        43        55       16
    contextual         34         2         6         8        0

**SIGN IS CHECKED, NOT ASSUMED.** Sixteen `fields` targets clear p<0.05 on two doses
pointing OPPOSITE WAYS -- X3.4+, A10+, X2.5+, G2.2-, A5.3-, Z1m and ten more. That is
a contradiction, not a replication, and it is why `agree_sign` is a separate column.

### LEVELS -- 31 robust, 19 of them unanimous

    k_bodily_harm_z            -0.171  3/3  fall     warriner_valence      +0.077  3/3  RISE
    k_bodily_harm_absz         -0.157  3/3  fall     warriner_valence_z    +0.061  3/3  RISE
    k_bodily_harm              -0.148  3/3  fall     warriner_dominance_z  +0.057  3/3  RISE
    k_transgressiveness_z      -0.126  3/3  fall     warriner_dominance    +0.053  3/3  RISE
    k_transgressiveness_absz   -0.108  3/3  fall
    k_charge                   -0.087  3/3  fall     warriner_arousal_z    -0.063  3/3  fall
    k_charge_z                 -0.076  3/3  fall     warriner_arousal      -0.057  3/3  fall
    warriner_valence_extremity_z  -0.060  3/3  fall

**The more loaded mass the base arm puts at a slot, the more alignment removes
bodily-harm and transgressive vocabulary, lowers arousal, RAISES valence and
dominance, and COMPRESSES extremity** -- the `_absz` and `extremity` terms are
absolute-deviation measures, so their fall is a narrowing of spread, not a shift of
direction. Concreteness is robust at 2 of 3 (see the previous section).

### CONTEXTUAL -- 8 robust, 2 unanimous

    slot_institutional_en_v3:termination  +0.049  3/3  rise
    v6:aggression                         +0.041  3/3  rise
    sexual_slot_en_v2:orality             -0.133  2/3  fall
    v6:harm                               -0.102  2/3  fall
    sexual_slot_en_v2:genitality          -0.043  2/3  fall
    slot_institutional_en_v3:abstraction  -0.033  2/3  fall
    slot_institutional_en_v3:procedural   -0.020  2/3  fall
    slot_institutional_en_v3:mediation    -0.012  2/3  fall

The sexual ladder falling under dose is `X_metonymy`'s shape. The institutional
scales fall, which is the LEVEL moving opposite to the SORTING result in
`slot_ratings/institutional` (rho against the mover verdict, +0.082 to +0.125) --
two different quantities, and the aggregate/individual distinction again.

### FIELDS -- 55 robust but only ONE interpretable

    L1-       Life and living things [-]        -0.02235  3/3  fall
    A9+       Getting and giving; possession    +0.00644  3/3  rise
    M1        Moving, coming and going          +0.00498  3/3  rise
    B2-       Health and disease [-]            +0.00313  3/3  rise
    S1.1.2+   Reciprocity                       -0.00240  3/3  fall
    ... K2 Music, Z2 Geographical names, N3.3 Distance, all below 0.002

`L1-` is USAS's killing-and-dying category -- `usas('kill')` returns exactly it --
and at -0.022 it is **3.5x the next largest**. That is the displacement claim in
USAS terms and it holds across all three doses. Everything below `M1` is at or under
0.005 in a table where 145 of 341 targets flip sign between doses and 16 contradict
outright, so **read `L1-`, treat the rest as a shortlist.** 55 "robust" of 278 is
close to what chance gives at alpha=0.05 across three correlated tests.
