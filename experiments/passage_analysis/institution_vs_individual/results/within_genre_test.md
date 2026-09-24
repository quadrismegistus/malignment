# Within-genre widening at the lineage and dispute unit

Producer `within_genre_test.py`, declared before any per-unit number was computed (pooled numbers had been seen; see docstring). Floors: >= 5 passages per cell per lineage, >= 10 per cell per dispute.

## Within advice

| outcome | role | expected | lineages +/- | p | median widening | dropped by floor | base cell n min/median/max | disputes +/- | p | median widening | dropped |
|---|---|---|---|---|---|---|---|---|---|---|---|
| channel | PRIMARY | > 0 | 25/0 | 5.96e-08 | +0.305 | 17 | 5/18/119 | 16/1 | 0.000275 | +0.265 | 1 |
| move_voice_direct | secondary | < 0 | 2/23 | 1.94e-05 | -0.247 | 17 | 5/18/119 | 4/13 | 0.049 | -0.126 | 1 |
| outward | secondary | > 0 | 20/5 | 0.00408 | +0.094 | 17 | 5/18/119 | 12/5 | 0.143 | +0.050 | 1 |
| authority | secondary | > 0 | 20/5 | 0.00408 | +0.119 | 17 | 5/18/119 | 12/5 | 0.143 | +0.045 | 1 |

## Within continuation

| outcome | role | expected | lineages +/- | p | median widening | dropped by floor | base cell n min/median/max | disputes +/- | p | median widening | dropped |
|---|---|---|---|---|---|---|---|---|---|---|---|
| channel | PRIMARY | > 0 | 11/2 | 0.0225 | +0.088 | 29 | 7/28/93 | 15/2 | 0.00235 | +0.065 | 0 |
| move_voice_direct | secondary | < 0 | 5/8 | 0.581 | -0.044 | 29 | 7/28/93 | 5/13 | 0.0963 | -0.103 | 0 |
| outward | secondary | > 0 | 4/8 | 0.388 | -0.015 | 29 | 7/28/93 | 11/6 | 0.332 | +0.035 | 0 |
| authority | secondary | > 0 | 8/4 | 0.388 | +0.036 | 29 | 7/28/93 | 9/8 | 1 | +0.018 | 0 |

## Decision

Channel widening within advice: lineages 25/0 (p=5.96e-08), disputes 16/1 (p=0.000275). **HOLDS on both units: the within-advice widening is the sentence's evidence.**
