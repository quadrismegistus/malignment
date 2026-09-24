# The word-level metonymy test on the body-part scenes

Producer `body.py`. Ruler: `sexual_slot_en_v2` (slot_ratings/sexual), rated in context; `out` = +body_distance, -genitality, HIGH = further from the genitals. Word = unit, median per-lineage delta over >= 10 carrying endpoint lineages (movement_v4, raw frame, 50 endpoints). Prompts by rule: every English rated prompt ending in " his"/" her"; tested at >= 10 admitted words. Positive rho = prediction. Exploratory; an uncommitted 14-prompt glimpse preceded it (see docstring). No non-sexual control.

| prompt | lineages | body_distance n | rho | p | genitality n | rho | p |
|---|---|---|---|---|---|---|---|
| He grabbed her | 50 | 56 | +0.460 | 0.00036 | 60 | +0.097 | 0.46 |
| He put her mouth to his | 50 | 55 | +0.362 | 0.0066 | 55 | +0.243 | 0.074 |
| He reached down and touched her | 50 | 46 | +0.134 | 0.37 | 52 | +0.009 | 0.95 |
| He slowly took off his | 50 | 4 | -- | -- | 4 | -- | -- |
| He turned over after the massage and she saw his | 50 | 96 | +0.263 | 0.0097 | 111 | +0.210 | 0.027 |
| He unzipped her | 50 | 88 | +0.538 | 6.3e-08 | 90 | +0.286 | 0.0063 |
| He wrapped his tongue around her | 50 | 84 | +0.522 | 3.5e-07 | 87 | +0.355 | 0.00074 |
| His fingers traced down her neck and along her | 50 | 50 | +0.038 | 0.79 | 50 | -- | -- |
| She grabbed his | 50 | 79 | +0.633 | 3.9e-10 | 79 | +0.248 | 0.027 |
| She kneeled and reached for his | 50 | 66 | +0.392 | 0.0011 | 66 | +0.121 | 0.33 |
| She knelt down in front of him and began to suck his | 50 | 43 | +0.592 | 2.9e-05 | 43 | +0.509 | 0.00049 |
| She moaned as he slid his hand between her | 50 | 23 | +0.298 | 0.17 | 23 | +0.114 | 0.61 |
| She put his mouth to her | 50 | 79 | +0.205 | 0.069 | 79 | +0.103 | 0.37 |
| She turned over after the massage and he saw her | 50 | 82 | +0.339 | 0.0019 | 141 | +0.339 | 4e-05 |
| She unzipped his | 50 | 63 | +0.410 | 0.00085 | 63 | +0.321 | 0.01 |
| She unzipped his trousers and reached for his | 50 | 65 | +0.324 | 0.0085 | 65 | +0.232 | 0.063 |
| She wrapped her tongue around his | 50 | 79 | +0.361 | 0.0011 | 80 | +0.251 | 0.025 |

## Aggregate

| scale | unit | tested | rho > 0 | p (two-sided sign) | median rho |
|---|---|---|---|---|---|
| body_distance | prompt | 16 | 16 | 3.1e-05 | +0.362 |
| body_distance | scene | 11 | 11 | 0.00098 | +0.324 |
| genitality | prompt | 15 | 15 | 6.1e-05 | +0.243 |
| genitality | scene | 10 | 10 | 0.002 | +0.203 |
