# Headline lineage counts at the cluster unit

Producer `test.py` (paper seat's check 1, 2026-09-24). Reanalysis only. Groupings from `clusters.py`: LINEAGE is the published test (50 independent units); PRETRAIN groups by base developer; SFT by dominant declared SFT source, developer where none is named; UNION joins any shared named source or developer into connected components.

- **PRETRAIN**: 33 clusters, sizes [5, 5, 3, 3, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
- **SFT**: 25 clusters, sizes [7, 7, 5, 3, 3, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
- **UNION**: 16 clusters, sizes [32, 3, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]

| test | predicted | grouping | clusters | cluster medians in predicted direction | p | one-per-cluster: median count | draws with p<0.05 |
|---|---|---|---|---|---|---|---|
| selectivity | < 0 | LINEAGE | 50 | 40/50 | 2.4e-05 | -- | -- |
| selectivity | < 0 | PRETRAIN | 33 | 27/33 | 0.00032 | 25 of 33 | 100.0% |
| selectivity | < 0 | SFT | 25 | 22/25 | 0.00016 | 20 of 25 | 99.7% |
| selectivity | < 0 | UNION | 16 | 13/16 | 0.021 | 12 of 16 | 27.9% |
| kill | < 0 | LINEAGE | 50 | 44/50 | 3.2e-08 | -- | -- |
| kill | < 0 | PRETRAIN | 33 | 29/33 | 1.1e-05 | 28 of 33 | 100.0% |
| kill | < 0 | SFT | 25 | 24/25 | 1.5e-06 | 23 of 25 | 100.0% |
| kill | < 0 | UNION | 16 | 15/16 | 0.00052 | 15 of 16 | 100.0% |
| scream | > 0 | LINEAGE | 50 | 42/50 | 1.2e-06 | -- | -- |
| scream | > 0 | PRETRAIN | 33 | 28/33 | 6.6e-05 | 28 of 33 | 100.0% |
| scream | > 0 | SFT | 25 | 21/25 | 0.00091 | 20 of 25 | 100.0% |
| scream | > 0 | UNION | 16 | 12/16 | 0.077 | 12 of 16 | 0.0% |

Cluster medians and draws are sign-flipped so the predicted direction always counts as a hit; ties (a median or a draw exactly zero) are dropped from the sign test.

**The fence.** 22 of 50 endpoints name no public SFT dataset; they are grouped by developer, so data shared ACROSS developers among them (e.g. undeclared ShareGPT-style distillation) is invisible to every grouping here, UNION included.
