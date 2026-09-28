# The fates of the barred affect in a continuous feeling space

Producer `feeling_space.py` (declared before the full Jev run and the second-rater check). Jev `type_survey.py` v2, words alone.

## `doer`

Reliability gate: PASS (argmax agreement 0.87, kappa 0.71, n=400; `none` boundary 0.89; fear/anger 1.00)

29968 gated cells.

- CARRY  JS(B,S) - JS(B,A): -0.0244 [-0.0353, -0.0180] +0/-49 of 49, p=3.6e-15
- SUPPRESSION  A[none] - S[none]: -0.0159 [-0.0355, -0.0049] +11/-38 of 49, p=0.00014
- KEPT  A[X] - S[X]: -0.0060 [-0.0141, +0.0018] +15/-34 of 49, p=0.0094
- ANXIETY  A[fear] - S[fear], X != fear: +0.0086 [+0.0013, +0.0162] +42/-7 of 49, p=3.6e-07

Mean levels: P(none) barred 0.33 / scene 0.75 / arriving 0.73; P(fear) barred 0.06 / scene 0.03 / arriving 0.04

## `evoked`

Reliability gate: **FAIL -- instrument not validated; fates below are not to be quoted** (argmax agreement 0.79, kappa 0.54, n=400; `none` boundary 0.85; fear/anger 0.59)

29968 gated cells.

- CARRY  JS(B,S) - JS(B,A): -0.0228 [-0.0352, -0.0118] +4/-45 of 49, p=8.2e-10
- SUPPRESSION  A[none] - S[none]: -0.0214 [-0.0456, +0.0010] +13/-36 of 49, p=0.0014
- KEPT  A[X] - S[X]: -0.0007 [-0.0108, +0.0048] +21/-28 of 49, p=0.39
- ANXIETY  A[fear] - S[fear], X != fear: +0.0103 [-0.0020, +0.0204] +34/-15 of 49, p=0.0094

Mean levels: P(none) barred 0.06 / scene 0.62 / arriving 0.59; P(fear) barred 0.37 / scene 0.07 / arriving 0.08

## BY DOSE (doer), within-lineage terciles, top minus bottom

### LIFT of the barred words (primary) (10752 cells, 47 lineages)

| fate | low | mid | high | high - low |
|---|---|---|---|---|
| carry | -0.0294 | -0.0317 | -0.0282 | +0.0018 [-0.0123, +0.0105] +26/-21 of 47, p=0.56 |
| kept | -0.0094 | -0.0097 | -0.0060 | +0.0005 [-0.0164, +0.0053] +24/-23 of 47, p=1 |
| anxiety | +0.0068 | +0.0105 | +0.0096 | +0.0059 [-0.0078, +0.0251] +30/-17 of 47, p=0.079 |
| suppression | -0.0143 | -0.0094 | -0.0218 | -0.0112 [-0.0261, +0.0234] +22/-25 of 47, p=0.77 |

### prompt CHARGE (separate) (26570 cells, 49 lineages)

| fate | low | mid | high | high - low |
|---|---|---|---|---|
| carry | -0.0254 | -0.0236 | -0.0285 | -0.0019 [-0.0143, +0.0084] +20/-29 of 49, p=0.25 |
| kept | -0.0077 | -0.0011 | -0.0084 | -0.0030 [-0.0166, +0.0141] +23/-26 of 49, p=0.78 |
| anxiety | +0.0052 | +0.0128 | +0.0059 | -0.0025 [-0.0070, +0.0051] +20/-29 of 49, p=0.25 |
| suppression | -0.0202 | -0.0182 | -0.0163 | +0.0025 [-0.0211, +0.0299] +26/-23 of 49, p=0.78 |

