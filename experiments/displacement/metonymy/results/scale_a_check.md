# Scale A: two runs, two axes

Producer `scale_a_check.py`. Raw (un-negated) scores; median per-lineage delta from `results/words_D.csv`, >= 10 carriers. Spearman.

## Each run against the deltas

| column | frame | n | rho | p |
|---|---|---|---|---|
| A A_opus | her | 72 | +0.396 | 0.00058 |
| A A_sonnet | her | 72 | -0.354 | 0.0023 |
| A mean | her | 73 | +0.141 | 0.23 |
| B mean | her | 71 | -0.620 | 8e-09 |
| D mean | her | 72 | -0.726 | 5.3e-13 |
| A A_opus | his | 57 | +0.218 | 0.1 |
| A A_sonnet | his | 58 | -0.395 | 0.0022 |
| A mean | his | 58 | -0.056 | 0.68 |
| B mean | his | 56 | -0.432 | 0.00088 |
| D mean | his | 57 | -0.535 | 1.8e-05 |

## Each run against the other scales, on the 71 words all five ported scales share

| column | vs A other run | vs B | vs Cexp | vs Ccharge | vs D |
|---|---|---|---|---|---|
| A_opus | +0.064 | -0.846 | -0.414 | -0.568 | -0.564 |
| A_sonnet | +0.064 | +0.170 | +0.625 | +0.260 | +0.449 |

Ported scales B-D run 0 = off the body to 100 = against the skin; `run.py` negates them to `out`. A_opus runs the other way (100 = outermost), so a positive raw rho with the deltas is the PREDICTED direction for A_opus and the opposite for B and D.
