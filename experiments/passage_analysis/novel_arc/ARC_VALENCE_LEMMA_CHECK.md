# Surface vs lemma-mapped Warriner lookup: valence components (EXPLORATORY)

Producer `arc_valence_lemma_check.py` (method in its docstring). Coverage = scored tokens per text relative to the mapped version's.

History: surface scores 68% of the tokens the mapped lookup scores (median over texts). Model meta-texts: 68%.

| component | lookup | history range (smoothed) | base | aligned raw / prefill / asked | lineages, base -> raw / prefill / asked |
|---|---|---|---|---|---|
| Positive share | surface | 0.413 to 0.454 | 0.483 | 0.547 / 0.545 / 0.537 | up 27/32 (p 0.000) / up 21/23 (p 0.000) / up 16/20 (p 0.012) |
| Positive share | mapped | 0.388 to 0.445 | 0.459 | 0.515 / 0.501 / 0.489 | up 27/32 (p 0.000) / up 20/23 (p 0.000) / up 16/20 (p 0.012) |
| Negative share | surface | 0.100 to 0.125 | 0.084 | 0.063 / 0.064 / 0.068 | down 27/32 (p 0.000) / down 19/23 (p 0.003) / down 18/20 (p 0.000) |
| Negative share | mapped | 0.094 to 0.137 | 0.079 | 0.059 / 0.064 / 0.063 | down 28/32 (p 0.000) / down 19/23 (p 0.003) / down 17/20 (p 0.003) |
| Positive intensity | surface | 1.753 to 1.871 | 1.793 | 1.834 / 1.816 / 1.797 | up 27/32 (p 0.000) / up 14/23 (p 0.405) / up 12/20 (p 0.503) |
| Positive intensity | mapped | 1.714 to 1.853 | 1.758 | 1.796 / 1.782 / 1.760 | up 25/32 (p 0.002) / up 17/23 (p 0.035) / up 14/20 (p 0.115) |
| Negative intensity | surface | 1.931 to 2.083 | 2.008 | 1.873 / 1.866 / 1.877 | down 24/32 (p 0.007) / down 18/23 (p 0.011) / down 15/20 (p 0.041) |
| Negative intensity | mapped | 1.923 to 2.018 | 1.999 | 1.864 / 1.845 / 1.868 | down 26/32 (p 0.001) / down 19/23 (p 0.003) / down 18/20 (p 0.000) |
