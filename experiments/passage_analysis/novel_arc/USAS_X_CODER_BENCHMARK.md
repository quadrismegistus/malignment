# USAS X against the blind interiority coder (EXPLORATORY)

Producer `usas_x_coder_benchmark.py`. The 13564 English passages the abstraction seat evaluated its seeded interiority norms on, scored with `measure_lltk.Scorer` (Figure 5's instrument). 12536 have at least 20 content words and enter (5860 narrative). Coder degree 0-3, mean over coders A and B. Control: `rh_absconc_median`, the plate's concreteness. Per-passage scores: /Users/rj416/malignment-data/interiority_norms/usas_x_passages_dario.parquet.

| statistic | value |
|---|---|
| rho(coder degree, concreteness) | -0.027 |
| rho(usas_x, concreteness) | -0.198 |
| rho(usas_x, coder degree), raw | +0.368 |
| raw, within prompt | +0.348 |
| partial, controlling concreteness | +0.370 |
| partial, within prompt | +0.339 |
| partial, narrative passages only | +0.300 |

For comparison, the seat's seeded norms on its own tokenisation and concreteness control (eval_passage_coder.csv): raw / partial / within prompt / narrative -- A_ALL +0.04 / +0.06 / +0.08 / +0.13; B_ALL +0.18 / +0.31 / +0.24 / +0.17; B_NOUN +0.22 / +0.35 / +0.29 / +0.23; C_ALL +0.09 / +0.20 / +0.17 / +0.17; C_NOUN +0.13 / +0.30 / +0.26 / +0.28. Populations and controls are close, not identical (see the docstring); the seat can rerun its exact controls on the per-passage file.
