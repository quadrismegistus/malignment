# Interiority word lists from the LLM consensus ratings, against the blind coder (EXPLORATORY)

Producer `interiority_xe.py --lists`. The abstraction seat's 13564 coded English passages, 12536 with at least 20 content words (5860 narrative); coder degree 0-3, mean over coders A and B; control the plate's concreteness. Each list: share of content words whose surface form or lemma is on the list, each word counted once. Lists from interiority_candidates.py's consensus ratings (interior >= 2 and a mental kind; INTERIORITY_TIEBREAK.md): CLEAN X is the USAS X words that pass; NEW CANDIDATES are period-model neighbours of X from outside X that pass. The FULL X LIST is every X word under the same rule, so clean X against it isolates the cleaning from the counting rule. The coder is an LLM and so is the rater that made these lists: agreement here is not independent validation.

| measure | raw | partial (concreteness) | partial within prompt | partial narrative | rho with concreteness | median share |
|---|---|---|---|---|---|---|
| usas_x (panel now) | +0.368 | +0.370 | +0.339 | +0.300 | -0.198 | 0.147 |
| full X list (3,225) | +0.356 | +0.359 | +0.326 | +0.275 | -0.209 | 0.148 |
| clean X (1,526) | +0.376 | +0.388 | +0.355 | +0.313 | -0.324 | 0.092 |
| new candidates (2,161) | +0.172 | +0.176 | +0.126 | +0.004 | -0.414 | 0.097 |
| clean X + candidates (3,687) | +0.332 | +0.359 | +0.308 | +0.206 | -0.459 | 0.188 |

Sampling error of each coefficient is about 0.009 overall and 0.013 in the narrative subset; gaps smaller than ~0.03 between measures on the same passages are not differences without a dependent-correlation test.
