# Precision and vetted interiority lists against the blind coder (EXPLORATORY)

Producer `interiority_vetted_benchmark.py`. Same 13564 coded English passages as INTERIORITY_LISTS_BENCHMARK.md, 12536 with at least 20 content words (5860 narrative); coder degree 0-3; control the plate's concreteness; counting rule `interiority_xe.list_shares`. Base words only (modern prose, modernised before lookup). The first three rows reproduce the earlier readout.

| measure | raw | partial (concreteness) | partial within prompt | partial narrative | rho with concreteness | median share |
|---|---|---|---|---|---|---|
| usas_x (panel now) | +0.368 | +0.370 | +0.339 | +0.300 | -0.198 | 0.147 |
| clean X (1,526) | +0.376 | +0.388 | +0.355 | +0.313 | -0.324 | 0.092 |
| clean X + candidates (3,687) | +0.332 | +0.359 | +0.308 | +0.206 | -0.459 | 0.188 |
| clean X, precision (1,054) | +0.366 | +0.380 | +0.350 | +0.305 | -0.342 | 0.075 |
| candidates, precision (1,243) | +0.232 | +0.239 | +0.195 | +0.134 | -0.373 | 0.026 |
| clean X + candidates, precision (2,297) | +0.393 | +0.423 | +0.381 | +0.321 | -0.433 | 0.100 |
| clean X, vetted (872) | +0.295 | +0.307 | +0.298 | +0.230 | -0.374 | 0.040 |
| candidates, vetted (1,077) | +0.260 | +0.264 | +0.215 | +0.166 | -0.304 | 0.016 |
| clean X + candidates, vetted (1,949) | +0.346 | +0.374 | +0.339 | +0.271 | -0.447 | 0.059 |

## Paired differences in the partial (95% paired bootstrap over passages, 1000 draws)

| comparison | difference | 95% interval |
|---|---|---|
| clean X, vetted (872) minus clean X (1,526) | -0.081 | -0.095 to -0.067 |
| clean X, vetted (872) minus usas_x (panel now) | -0.063 | -0.078 to -0.048 |
| clean X, precision (1,054) minus clean X (1,526) | -0.009 | -0.015 to -0.002 |
| clean X, vetted (872) minus clean X, precision (1,054) | -0.072 | -0.085 to -0.060 |
| clean X + candidates, vetted (1,949) minus clean X, vetted (872) | +0.066 | +0.056 to +0.076 |
