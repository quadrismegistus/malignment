# Interiority as X + E, POS-matched and once per word, against the blind coder (EXPLORATORY)

Producer `interiority_xe.py --benchmark`. The abstraction seat's 13564 coded English passages, 12536 with at least 20 content words (5860 narrative); coder degree 0-3, mean over coders A and B; control the plate's concreteness (`rh_absconc_median`). Rule: the USAS entry matching the word's tagged POS (surface, then lemma; any entry only if none matches), its primary tag, counted once per word per family.

| measure | raw | partial (concreteness) | partial within prompt | partial narrative | rho with concreteness | share > 1 |
|---|---|---|---|---|---|---|
| usas_x (panel now: every POS entry, counted per tag) | +0.368 | +0.370 | +0.339 | +0.300 | -0.198 | 0 |
| X | +0.338 | +0.344 | +0.312 | +0.273 | -0.280 | 0 |
| E | +0.252 | +0.251 | +0.181 | +0.081 | -0.116 | 0 |
| X + E | +0.391 | +0.403 | +0.348 | +0.276 | -0.309 | 0 |

The panel should cite the X + E row for the rule it uses. EXPLORATORY.
