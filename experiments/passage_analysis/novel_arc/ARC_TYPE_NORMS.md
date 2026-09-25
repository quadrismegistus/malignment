# Type-based norms over arc_fiction, with TEMPLATE_ARM meta-text arms (EXPLORATORY)

Producer `arc_type_norms.py` (method in its docstring). 75,974 texts; 30 lineages. Coverage after the map, decade medians, and each scale's decade range with the arms.

Mapped forms by rule: brysbaert: self 33530, lemma 25122, morph+self 13464, morph+lemma 3561, long_s+self 1949, long_s+lemma 675, british 537, lemma+british 353, long_s+morph+self 323, morph+british 94, long_s+morph+lemma 57, morph+lemma+british 27, long_s+british 24, long_s+lemma+british 3, long_s+morph+british 1; k: self 22269, morph+self 13111, lemma 12202, long_s+self 2035, morph+lemma 1205, british 350, long_s+morph+self 329, long_s+lemma 279, lemma+british 75, morph+british 38, long_s+morph+lemma 23, long_s+british 18, morph+lemma+british 10, long_s+lemma+british 1; warriner: lemma 20035, self 13768, morph+self 9808, morph+lemma 4654, long_s+self 1395, long_s+lemma 849, british 259, long_s+morph+self 229, lemma+british 176, long_s+morph+lemma 118, morph+british 78, morph+lemma+british 37, long_s+british 17, long_s+lemma+british 3, long_s+morph+british 1

## human norms

| scale | decade min | decade max | base | aligned | aligned - base |
|---|---|---|---|---|---|
| brysbaert_concreteness | 2.815 | 3.249 | 3.205 | 3.081 | -0.125 |
| warriner_arousal | 4.037 | 4.204 | 4.166 | 4.159 | -0.006 |
| warriner_dominance | 5.551 | 5.622 | 5.553 | 5.568 | +0.016 |
| warriner_valence | 5.635 | 5.731 | 5.646 | 5.690 | +0.044 |

## k lexicon (one model's ratings, not human norms)

| scale | decade min | decade max | base | aligned | aligned - base |
|---|---|---|---|---|---|
| k_bodily_harm | 1.070 | 1.122 | 1.134 | 1.114 | -0.021 |
| k_charge | 1.531 | 1.836 | 1.749 | 1.782 | +0.033 |
| k_concreteness | 2.681 | 3.435 | 3.506 | 3.318 | -0.187 |
| k_register_level | 3.855 | 4.047 | 3.888 | 3.913 | +0.025 |
| k_transgressiveness | 1.083 | 1.145 | 1.122 | 1.105 | -0.018 |
| k_valence | 4.067 | 4.192 | 4.054 | 4.083 | +0.028 |
| k_vulgarity | 1.010 | 1.017 | 1.034 | 1.018 | -0.016 |

## Coverage after the map (share of content tokens scored), decade medians at 1650, 1750, 1850, 1950

- warriner: 1650 73.5%, 1750 74.6%, 1850 73.8%, 1950 75.4%; model meta-texts median 80.4%
- brysbaert: 1650 91.2%, 1750 90.4%, 1850 90.0%, 1950 90.9%; model meta-texts median 96.1%
- k: 1650 84.1%, 1750 85.3%, 1850 87.2%, 1950 89.9%; model meta-texts median 95.0%
