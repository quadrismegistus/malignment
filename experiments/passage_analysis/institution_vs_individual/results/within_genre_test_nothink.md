# Within-genre widening at the lineage and dispute unit

Producer `within_genre_test.py`, declared before any per-unit number was computed (pooled numbers had been seen; see docstring). Floors: >= 5 passages per cell per lineage, >= 10 per cell per dispute.

## Within advice

| outcome | role | expected | lineages +/- | p | median widening | dropped by floor | base cell n min/median/max | disputes +/- | p | median widening | dropped |
|---|---|---|---|---|---|---|---|---|---|---|---|
| channel | PRIMARY | > 0 | 25/0 | 5.96e-08 | +0.317 | 17 | 5/18/119 | 16/1 | 0.000275 | +0.280 | 1 |
| move_voice_direct | secondary | < 0 | 2/23 | 1.94e-05 | -0.181 | 17 | 5/18/119 | 5/12 | 0.143 | -0.125 | 1 |
| outward | secondary | > 0 | 20/5 | 0.00408 | +0.114 | 17 | 5/18/119 | 12/5 | 0.143 | +0.056 | 1 |
| authority | secondary | > 0 | 20/5 | 0.00408 | +0.120 | 17 | 5/18/119 | 13/4 | 0.049 | +0.050 | 1 |

## Within continuation

| outcome | role | expected | lineages +/- | p | median widening | dropped by floor | base cell n min/median/max | disputes +/- | p | median widening | dropped |
|---|---|---|---|---|---|---|---|---|---|---|---|
| channel | PRIMARY | > 0 | 9/2 | 0.0654 | +0.067 | 31 | 7/29/93 | 12/3 | 0.0352 | +0.060 | 2 |
| move_voice_direct | secondary | < 0 | 4/7 | 0.549 | -0.044 | 31 | 7/29/93 | 6/10 | 0.454 | -0.119 | 2 |
| outward | secondary | > 0 | 3/7 | 0.344 | -0.023 | 31 | 7/29/93 | 11/4 | 0.118 | +0.023 | 2 |
| authority | secondary | > 0 | 6/4 | 0.754 | +0.036 | 31 | 7/29/93 | 10/5 | 0.302 | +0.030 | 2 |

## Decision

Channel widening within advice: lineages 25/0 (p=5.96e-08), disputes 16/1 (p=0.000275). **HOLDS on both units: the within-advice widening is the sentence's evidence.**

## Context, not the test: pooled shares within advice (post hoc)

`decompose.table` over the rows above (both arms, kept, advice). The paper quotes the channel row (individual base -> aligned) and the institution's.

| outcome | base indiv | base inst | base gap | aligned indiv | aligned inst | aligned gap | change in gap |
|---|---|---|---|---|---|---|---|
| any | 0.619 | 0.359 | +0.259 | 0.784 | 0.334 | +0.450 | +0.191 |
| outward | 0.274 | 0.087 | +0.187 | 0.330 | 0.048 | +0.282 | +0.096 |
| authority | 0.267 | 0.089 | +0.178 | 0.318 | 0.056 | +0.262 | +0.084 |
| channel | 0.221 | 0.028 | +0.192 | 0.478 | 0.024 | +0.454 | +0.262 |
| inward | 0.253 | 0.246 | +0.008 | 0.360 | 0.263 | +0.096 | +0.089 |
| move_voice_direct | 0.289 | 0.488 | -0.199 | 0.470 | 0.844 | -0.374 | -0.176 |
| move_third_party | 0.515 | 0.249 | +0.266 | 0.478 | 0.097 | +0.381 | +0.115 |
| move_self_help | 0.025 | 0.071 | -0.046 | 0.007 | 0.018 | -0.011 | +0.035 |
| move_exit | 0.031 | 0.005 | +0.026 | 0.004 | 0.000 | +0.004 | -0.022 |

n: base 679 / 562, aligned 5616 / 4658 (individual / institution).

