# Partial tests of the Figure 5 measures across the four arms (EXPLORATORY)

Producer `arc_fig5_partials.py` (method in its docstring). Cells: lineages (of 30) whose raw / prefill / continue arm moves from base in the direction of the unpartialled continue effect, with the two-sided sign test p. Bonferroni over the 30 partialled tests below puts the bar near p 0.001.

Meta-text Spearman with concreteness: emotional words -0.78, cognitive words -0.83, valence (vector) -0.06, arousal (vector) -0.84, dominance (vector) -0.46

| measure | unpartialled | partialled on concreteness | concreteness partialled on it |
|---|---|---|---|
| concreteness | 27 (p 0.000) / 29 (p 0.000) / 30 (p 0.000) | -- | -- |
| emotional words | 23 (p 0.005) / 27 (p 0.000) / 30 (p 0.000) | 13 (p 0.585) / 9 (p 0.043) / 17 (p 0.585) | 26 (p 0.000) / 26 (p 0.000) / 23 (p 0.005) |
| cognitive words | 22 (p 0.016) / 28 (p 0.000) / 29 (p 0.000) | 13 (p 0.585) / 17 (p 0.585) / 14 (p 0.856) | 20 (p 0.099) / 19 (p 0.200) / 24 (p 0.001) |
| valence (vector) | 16 (p 0.856) / 10 (p 0.099) / 19 (p 0.200) | 15 (p 1.000) / 10 (p 0.099) / 19 (p 0.200) | 28 (p 0.000) / 29 (p 0.000) / 30 (p 0.000) |
| arousal (vector) | 26 (p 0.000) / 25 (p 0.000) / 29 (p 0.000) | 17 (p 0.585) / 9 (p 0.043) / 16 (p 0.856) | 22 (p 0.016) / 28 (p 0.000) / 24 (p 0.001) |
| dominance (vector) | 22 (p 0.016) / 27 (p 0.000) / 18 (p 0.362) | 17 (p 0.585) / 22 (p 0.016) / 11 (p 0.200) | 28 (p 0.000) / 25 (p 0.000) / 29 (p 0.000) |
| cognitive + emotional | 25 (p 0.000) / 28 (p 0.000) / 30 (p 0.000) | 15 (p 1.000) / 15 (p 1.000) / 17 (p 0.585) | 20 (p 0.099) / 24 (p 0.001) / 19 (p 0.200) |
