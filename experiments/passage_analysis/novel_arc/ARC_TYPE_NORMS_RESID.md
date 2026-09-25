# Type-norm histories: which survive regressing out concreteness? (EXPLORATORY)

Producer `arc_type_norms_resid.py` (method in its docstring). Verdict: survives if shape >= 0.7 and size >= 0.5; killed if shape < 0.3 or size < 0.3; otherwise partly. Plate: figures/arc_type_norms_resid.png.

| scale | verdict | shape (rho raw vs adjusted) | size (adjusted / raw range) | r with concreteness (texts) | decade rho with concreteness raw / adjusted | adjusted range | base adj | aligned adj |
|---|---|---|---|---|---|---|---|---|
| k_transgressiveness | survives | +0.97 | 0.90 | -0.13 | -0.63 / -0.50 | 1.087-1.128 | 1.126 | 1.108 |
| warriner_arousal | survives | +0.95 | 0.55 | -0.40 | -0.76 / -0.66 | 4.064-4.135 | 4.198 | 4.171 |
| warriner_valence | survives | +0.92 | 0.82 | -0.08 | -0.33 / -0.06 | 5.669-5.711 | 5.655 | 5.694 |
| k_vulgarity | survives | +0.79 | 1.07 | +0.23 | +0.05 / -0.50 | 1.010-1.017 | 1.032 | 1.017 |
| k_bodily_harm | survives | +0.74 | 1.34 | +0.24 | +0.07 / -0.58 | 1.079-1.112 | 1.125 | 1.107 |
| k_charge | partly | +0.95 | 0.50 | -0.44 | -0.81 / -0.69 | 1.587-1.694 | 1.799 | 1.809 |
| k_valence | partly | +0.82 | 0.43 | -0.34 | -0.84 / -0.55 | 4.093-4.139 | 4.081 | 4.091 |
| k_register_level | partly | +0.56 | 0.68 | -0.43 | -0.64 / +0.18 | 3.894-3.987 | 3.926 | 3.926 |
| warriner_dominance | partly | +0.34 | 0.67 | -0.25 | -0.64 / +0.32 | 5.565-5.587 | 5.568 | 5.580 |
| k_concreteness | killed | +0.51 | 0.22 | +0.88 | +0.96 / +0.33 | 3.048-3.202 | 3.260 | 3.222 |
| brysbaert_concreteness | killed | +0.49 | 0.18 | +0.91 | +0.96 / +0.31 | 3.031-3.103 | 3.041 | 3.027 |
