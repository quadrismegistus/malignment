# Is the base → aligned difference one thing?

**The 38 axes cannot be factored.** Each relation sits on exactly one, so a relation × axis matrix is a partition and its components recover the partition. The question is put to the two matrices that exist.

## A — 50 alignment lineages × norm scales, dose slopes

_do alignment regimes differ along one dimension?_

50 × 13. **PC1 60.4%, PC2 16.2%, PC3 8.9% — first two 76.6%.**

- **PC1 −** `warriner_valence` -0.33, `k_valence` -0.33, `warriner_dominance` -0.30, `k_register_level` -0.09
- **PC1 +** `k_bodily_harm` +0.33, `warriner_arousal` +0.33, `k_charge` +0.34, `k_transgressiveness` +0.34
- **PC2 −** `k_vulgarity` -0.63, `k_charge` -0.12, `warriner_arousal` -0.06, `warriner_dominance` -0.05
- **PC2 +** `k_bodily_harm` +0.10, `brooke_formality` +0.27, `warriner_valence_extremity` +0.35, `k_register_level` +0.61

## B — frames × scales, base → aligned deltas

_is the movement itself one or two things?_

77 × 25. **PC1 28.2%, PC2 15.9%, PC3 9.8% — first two 44.1%.**

- **PC1 −** `slot_institutional_en_v3_assertiveness` -0.31, `slot_institutional_en_v3_agency` -0.31, `v6_makes_worse` -0.29, `v6_harm` -0.27
- **PC1 +** `v6_mundanity` +0.22, `v6_vocalisation` +0.23, `slot_institutional_en_v3_vocalisation` +0.24, `slot_institutional_en_v3_deference` +0.26
- **PC2 −** `v6_deliberation` -0.38, `v6_superego` -0.36, `slot_institutional_en_v3_abstraction` -0.34, `v6_fit` -0.32
- **PC2 +** `v6_vocalisation` +0.03, `slot_institutional_en_v3_deference` +0.03, `slot_institutional_en_v3_collective` +0.03, `slot_institutional_en_v3_termination` +0.15

### Where each axis sits on PC1 and PC2

The 77 frames that carry both a norm profile and an axis. Small cells: read the ORDER, not the values.

| axis | frames | PC1 | PC2 |
|---|---|---|---|
| `force_and_abruptness` | 4 | +1.79 | +0.28 |
| `argument_structure` | 5 | +1.42 | +0.71 |
| `speech_vs_physical_act` | 10 | +1.15 | +0.02 |
| `act_vs_state` | 3 | +0.82 | +1.68 |
| `deliberation_vs_decisive_act` | 3 | +0.73 | -1.51 |
| `co_member_of_same_field` | 6 | +0.04 | +0.71 |
| `body_referent` | 3 | -0.06 | +1.45 |
| `sexual_or_transgressive_content` | 6 | -0.42 | +0.55 |
| `same_event_vs_new_event` | 4 | -0.51 | -0.13 |
| `specificity_vs_generality` | 5 | -1.10 | +0.78 |
| `institutional_vs_personal` | 3 | -1.33 | -3.22 |


## C — the axes themselves, from the annotations alone

_is there a factor or two behind the 38 axes?_

**The single-choice prompt is what blocks the direct answer, and that was my design decision.** Each agent was asked for "the single best-fitting axis", so every relation has one non-zero and a relation × axis matrix is a partition. Ask instead for *all axes that apply*, or a score per relation per axis, and it is an ordinary loading matrix. Nothing about the data prevents it.

What the existing annotations do support: the two runs assigned **the same 2,466 relations** under **two independently built vocabularies** (28 and 38 axes, different prompts, different shuffles). That 29 × 39 contingency table is a real matrix, and correspondence analysis on it asks whether both readers were tracking a small number of underlying dimensions.

> **dim1 9.0%, dim2 8.6%, dim3 7.6%, dim4 7.0% — first two 17.5%.**
> **Seven dimensions for half the inertia, fourteen for 80%, of 29 possible.**

**That is a flat spectrum, and it is a clear no.** Two vocabularies built from the same corpus share no two-dimensional structure; the association between them is spread almost evenly across dimensions, which is what near-independent partitions look like. It is the same finding as ARI 0.311 seen from the other side.

The leading dimension is nevertheless interpretable, and both vocabularies order onto it the same way:

| | run 1 | run 2 |
|---|---|---|
| **dim1 low** | `granularity`, `referent_substitution`, `explicitness_charge`, `entity_vs_event` | `spatial_configuration`, `body_referent`, `bluntness_vs_euphemism`, `sexual_or_transgressive_content` |
| **dim1 high** | `act_channel`, `deliberation_vs_action`, `interiority`, `affective_vs_cognitive` | `deliberation_vs_decisive_act`, `inner_state_vs_outward_act`, `realis_vs_irrealis`, `kind_of_inner_state` |

Concrete, bodily, referential contrasts at one end; inner-state, deliberative, communicative ones at the other. Both readers found that split without sharing a vocabulary — **but it is 9% of the inertia**, so it is a tendency in how relations get sorted, not a factor the 38 axes reduce to.

### What would answer the question properly

A multi-label pass: every relation scored on every axis rather than assigned to one. 16 agents × 154 relations × 38 axes, which is a loading matrix and factors without argument. Until that exists, "is there a factor or two" has been asked of a partition and answered no by default, which is not the same as answered.

## D — the dense graded matrix, and the answer

The multi-label pass section C called for, run. `axis_survey.py` on `jev-1.13.0`: **2,244 English relations × 38 axes = 85,272 graded judgements, 65 seconds, 0 failures, 22.74M input tokens ≈ $0.96.** Every relation scored on every axis as a `Score` — a probability-weighted position between five levels, centre meaning "these two lists do not separate on this contrast".

**Missing cells: 0.00%.** The 2.6%-filled partition is gone; `Survey`'s per-item question set makes the key set a contract rather than a hope.

> **PC1 21.6%, PC2 12.4% — first two 34.1%.**
> **Four components for half the variance, twelve for 80%, of 38.**

**So the answer is no.** What alignment does to a frame is not one or two things. It is not the forced-choice prompt hiding the structure either — this is the dense graded matrix the question actually needs, and it gives four dimensions for half.

**But it is not the 9% the correspondence analysis gave**, and the difference is the measurement, not the corpus. Asking every axis and grading the answer more than doubles the leading component. The partition was hiding real structure; there just isn't a *small* amount of it.

**PC1 is not a salience artefact**, which was the obvious worry given its one-sided loadings (negative end −0.25, positive end +0.10 — the shape of a general factor). Correlation between PC1 score and a relation's mean |value| is **−0.202**, and removing the per-relation salience component leaves PC1 at 22.7% rather than collapsing it. It is a contrast, not a count of how many axes fired.

| | negative end | positive end |
|---|---|---|
| **PC1** | `orientation_toward_other_party`, `specificity_vs_generality`, `handling_vs_no_contact`, `means_vs_end` | `argument_structure`, `inner_state_vs_outward_act`, `deliberation_vs_decisive_act` |
| **PC2** | `inner_state_vs_outward_act`, `kind_of_inner_state`, `evaluative_polarity`, `bluntness_vs_euphemism` | `volition_and_agency`, `act_vs_outcome`, `act_vs_state`, `transfer_vs_own_handling` |
| **PC3** | `deliberation_vs_decisive_act`, `creation_vs_destruction`, `compliance_vs_resistance` | `force_and_abruptness`, `evaluative_polarity`, `bluntness_vs_euphemism` |

**And the sparsity is real rather than structural.** Only **27.0%** of the 85,272 cells exceed 0.35 from centre. The rater was asked about all 38 and declined on three-quarters — zeros from a reader that considered the question, which is what the partition could never supply and what makes the covariance meaningful.

## E — two vocabularies, and the one dimension they share

**CORRECTION TO SECTION D's READING.** The loadings there were reported against the raw signed columns, but each axis was *named* from its own mean direction — and 18 of 38 axes have a negative mean. So for those the named arrow corresponded to negative values and for the other 20 to positive ones, and the ends of each component were half-right. Variance is unaffected (a column flip is a reflection); the interpretation was not. Every column is now oriented so **positive = more of the named movement**. The claim "pure charge-drain, isolated on PC3" was an artefact of exactly this and is withdrawn.

Corrected, and with the 28-axis vocabulary run as well (2,244 × 28 = 62,832 judgements, 78 s, $0.74):

| | PC1 | PC2 | PC3 | PC4 |
|---|---|---|---|---|
| 38 axes | 21.6% | 12.4% | 11.5% | 7.0% |
| 28 axes | 22.8% | 12.6% | 11.3% | 7.2% |

**The amount of structure replicates almost exactly.** Two vocabularies built by different readers under different prompts, of different sizes, give the same eigenvalue spectrum. Dimensionality is a property of the corpus.

**The content of the structure does not.** Canonical correlations between the two four-dimensional score subspaces: **0.80, 0.08, 0.02, 0.01.** One shared direction and nothing else. Regressing seed-1's components on all four of seed-0's: PC1 R²=0.34, **PC2 R²=0.10, PC3 R²=0.13**. So the de-agenting-versus-softening reading of PC2, and whatever PC3 is, are properties of a vocabulary, not of the corpus, and must not be cited.

Two things do replicate, and they are different from each other:

**Salience, r = 0.86.** How much a relation separates on anything at all is a robust property of the relation. But it is *not* the shared factor direction (correlation with the first canonical variate: +0.14 and −0.01).

**One substantive dimension, canonical r = 0.80 — and it is the same-field reshuffle.** The strongest loader at one pole in each vocabulary is that vocabulary's name for it:

| | 38-axis | 28-axis |
|---|---|---|
| **negative pole** | `one member of a field → another` **−0.83**, `one word class → another` −0.74, `starting a new event → continuing this one` −0.73 | `one member of the referent class → another` **−0.70**, `the event continued → a separate one` −0.62, `bounded part → encompassing whole` −0.53 |
| **positive pole** | `a bounded place → an open extent` +0.52, `an intimate part → a whole region` +0.48, `what it is → how it seems` +0.47 | `onset → completion` +0.55, `stands in the slot → needs another form` +0.54, `felt emotion → cognitive stance` +0.46 |

**The single replicable dimension of the base → aligned difference is whether the movement leaves its field at all.** Lateral substitution within one class at one pole; going somewhere else at the other. That is `referent_substitution` / `co_member_of_same_field` — the axis that came back 41-unclear of 44 in the assignment run because both word groups sat on the same pole, and the operation `TAXONOMY.md` already names *same-field reshuffle*.

Two independent vocabularies, a graded dense matrix, and a canonical correlation analysis recover the distinction that folder's ten meta-relations arrived at by hand.

## F — pooling the two vocabularies, and the diagnostic that would have over-claimed

RH asked whether, given that the two solutions' *content* differs, the 66 columns could be pooled into one analysis. I had refused earlier on the grounds that `act_channel` and `speech_vs_physical_act` are near-duplicates and would inflate the shared factor — the `warriner_valence`/`_z` problem from section A, reintroduced deliberately.

**THAT OBJECTION WAS AN ASSERTION AND IT IS FALSE.** Cross-vocabulary column correlations, all 38 × 28 = 1,064 pairs:

> **max 0.72; exactly one pair above 0.7; mean best-match per 38-axis column 0.23.**

And the one pair is `co_member_of_same_field` ~ `referent_substitution` — the shared dimension itself. The two vocabularies' *names* overlap heavily; their *measurements* barely do. Pooling is safe.

Pooled, 2,244 × 66: PC1 16.1%, PC2 8.9%, PC3 7.6%, PC4 6.9%, seven components for half.

**A BALANCE DIAGNOSTIC LOOKED LIKE THREE SHARED COMPONENTS AND WAS WRONG.** Share of squared loading from each vocabulary gave PC1 67/33, PC2 43/57, PC3 56/44 — three components drawing on both, which reads as shared structure. It is not. Project each component onto only the 38 columns and only the 28, and correlate the halves:

| PC | variance | 38 / 28 loading | half-correlation | |
|---|---|---|---|---|
| PC1 | 16.1% | 67 / 33 | **0.58** | **shared** |
| PC2 | 8.9% | 43 / 57 | −0.06 | not shared |
| PC3 | 7.6% | 56 / 44 | 0.07 | not shared |
| PC4 | 6.9% | 97 / 3 | 0.06 | not shared |
| PC5 | 5.0% | 4 / 96 | −0.01 | not shared |

**A pooled PCA maximises total variance, so it will assemble a component out of UNRELATED variance from both halves.** Balanced loadings are not evidence of shared structure; co-varying halves are. Had the balance column been the last check, this file would report three shared components instead of one.

Pooling therefore confirms the canonical analysis rather than extending it: **one shared component, and its top loaders are `one member of a field → another`, `starting a new event → continuing this one`, `one word class → another`, `a general term → a specific one`.** The same-field reshuffle, arrived at now by a third method.

## What is canonical

**The 38-axis run (seed 1) is the run of record** — it is the leak-fixed vocabulary, and it supplies the axes, their directions and their dose behaviour. The 28-axis run is confirmation.

**But confirmation succeeded for only two things**, and the distinction has to travel with any citation:

| | replicates | cite |
|---|---|---|
| dimensionality (21.6/12.4/11.5 vs 22.8/12.6/11.3) | yes | yes |
| the same-field-reshuffle dimension (canonical r 0.80, pooled half-corr 0.58) | yes | yes |
| per-relation salience (r 0.86) | yes | yes, as a separate property |
| PC2, PC3 and their readings | **no** (R² 0.10, 0.13) | **no** |
| any individual axis's membership | not tested here; ARI 0.311 in `AXIS_RUN.md` says no | no |

So the 38-axis solution is canonical as a **source of named, dosed movements** — `plain naming → euphemism`, `forceful → gentle`, `the deed becomes an utterance` — and is **not** canonical as a factor solution. Exactly one factor is a property of the corpus rather than of a vocabulary.

## G — two checks paper-claude asked for before anything is cited

**THE REVERSAL IS NOT THE INSTITUTIONAL BATTERY.** His hypothesis: low lift *is* the advice battery by construction, and its frames (`say, mention → file, report, sue`) code as speaking → non-verbal for a reason that has nothing to do with the scream.

| `speech_vs_physical_act` | bottom | middle | top |
|---|---|---|---|
| all frames | 44/29 p=0.1 | 42/37 p=0.7 | **7/81 p=4e-17** |
| advice/institutional excluded | 38/28 p=0.3 | 28/35 p=0.4 | **7/79 p=2e-16** |
| affect-NONE excluded | 6/8 p=0.8 | 3/10 p=0.09 | **2/46 p=8e-12** |

The advice battery is 30 of 290 relations on this axis and sits mostly in the **middle** band (18 of 30), not the bottom (8). The bottom tertile is **90 distinct template families over 90 relations** — every frame unique.

So the bottom lean was never significant and survives neither exclusion; the top survives both. The finding is **the deed becomes an utterance only under high lift**, and the bottom lean is not claimed.

**The denominator moves a lot under the affect gate**: 290 relations become 75, and "7 against 81" becomes "2 against 46". Same finding at two population definitions; only one may be quoted in a given sentence.

**EUPHEMISM RISES WITH LIFT, STEEPLY.** His test: if `plain naming → euphemism` is the largest mean movement but flat on lift, it is the "of course alignment euphemizes" objection made measurable and should not lead.

| movement | slope / unit lift | r | bottom → middle → top | top vs bottom |
|---|---|---|---|---|
| plain naming → euphemism | **+0.216** | +0.399 | +0.135 → +0.221 → **+0.448** | t=+16.7, p=9e-58 |
| forceful → gentle | +0.324 | +0.459 | **+0.004** → +0.153 → **+0.546** | t=+23.8, p=3e-106 |
| speaking → bodily action | **−0.167** | −0.220 | +0.122 → +0.067 → **−0.167** | t=−10.7, p=9e-26 |

Euphemism is strongly dose-dependent, so it is a response to charge rather than a constant register effect.

**And `forceful → gentle` starts at +0.004** — indistinguishable from zero in the bottom tertile — reaching +0.546 in the top. The softening of force does not exist at low lift at all.

**The third row is the reversal again, measured continuously** on the graded matrix instead of by counting poles: a negative slope that crosses zero between the middle and top tertiles. The assignment run and the survey are independent instruments and both find this axis changing sign with dose.

### Figures: none of A–F is drawn

paper-claude's call, recorded so it is not relitigated. The article is at ~8,350 of 9,500 words with V–VIII undrafted and four figures placed; a figure about method cannot be paid for. `(b)` and `(d)` would read as noise at 4.8 inches, and `(c)` invites the PC1 × PC2 misreading it exists to avoid, since readers assume both biplot axes are real.

**`(a)` is kept for the book's methods chapter** and its spec is recorded here rather than rebuilt: two scatters, each relation's shared-dimension score under the 38-axis vocabulary against the 28-axis one (r=0.80, a diagonal cloud), beside PC2 against PC2 (r≈0.1, a round blob), 2,244 points each. A negative control drawn as a panel.
