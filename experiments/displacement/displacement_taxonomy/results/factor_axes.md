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
