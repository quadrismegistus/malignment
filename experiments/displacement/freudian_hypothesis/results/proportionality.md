# Does the affect that arrives scale with the charge that left?

Producer `proportionality.py` (spec in its docstring). Per (lineage, English prompt): W = charge withdrawn from barred departing words (act >= 4), A = intensity of arriving mass, B = the frame's own base-weighted level. Per lineage (>= 15 prompts past an 80% coverage gate), Spearman rho across prompts; median over lineages, two-sided sign test. **Freud: rho(A-B, W) > 0. Cooling: <= 0.**

| scale | cells (charged / past gate) | lineages | rho(A-B, W) | rho(A, W), no control | rho(B, W), the scene | rho(A-B, M), mass only | rho(A-B', W): coupled all-word B (type scales) / non-barred-word B (affect arm) |
|---|---|---|---|---|---|---|---|
| `k_charge` | 30878 / 30195 | 49 | +0.010 [-0.04, +0.04] +27/-22 of 49 p=0.57 | +0.165 [+0.11, +0.20] +46/-3 of 49 p=7e-11 | +0.228 [+0.16, +0.27] +48/-1 of 49 p=1.8e-13 | +0.004 [-0.05, +0.05] +26/-23 of 49 p=0.78 | -0.345 [-0.43, -0.31] +0/-49 of 49 p=3.6e-15 |
| `inst:arousal` | 30878 / 4296 | 47 | -0.073 [-0.26, +0.05] +19/-28 of 47 p=0.24 | +0.463 [+0.38, +0.52] +47/-0 of 47 p=1.4e-14 | +0.497 [+0.42, +0.58] +47/-0 of 47 p=1.4e-14 | -0.058 [-0.24, +0.03] +17/-30 of 47 p=0.079 | -0.261 [-0.39, -0.14] +2/-45 of 47 p=1.6e-11 |
| `affect:scene_intensity` | 30878 / 12113 | 49 | +0.044 [-0.01, +0.09] +33/-16 of 49 p=0.021 | +0.396 [+0.32, +0.45] +49/-0 of 49 p=3.6e-15 | +0.365 [+0.29, +0.43] +48/-1 of 49 p=1.8e-13 | +0.041 [-0.01, +0.10] +34/-15 of 49 p=0.0094 | -0.020 [-0.05, +0.07] +21/-28 of 49 p=0.39 |
| `affect:intensity` | 30878 / 12113 | 49 | +0.006 [-0.06, +0.06] +25/-24 of 49 p=1 | +0.408 [+0.34, +0.45] +49/-0 of 49 p=3.6e-15 | +0.424 [+0.34, +0.46] +49/-0 of 49 p=3.6e-15 | -0.022 [-0.06, +0.04] +19/-30 of 49 p=0.15 | -0.032 [-0.06, +0.04] +21/-28 of 49 p=0.39 |

**Levels** (per lineage the median over prompts, then median over lineages [IQR]; positive/n is lineages with arrivals ABOVE the scene):

| scale | barred departing | scene (B: non-barred words; FRAME for affect:) | arriving (A) | A - B |
|---|---|---|---|---|
| `k_charge` | 4.00 | 1.39 | 1.48 | +0.074 [+0.02, +0.14] +39/-9 of 49 p=1.5e-05 |
| `inst:arousal` | 6.00 | 3.11 | 3.00 | -0.000 [-0.11, +0.05] +20/-24 of 47 p=0.65 |
| `affect:scene_intensity` | 5.12 | 4.00 | 4.03 | +0.000 [-0.05, +0.00] +0/-23 of 49 p=2.4e-07 |
| `affect:intensity` | 5.00 | 4.00 | 4.02 | -0.010 [-0.08, +0.00] +1/-31 of 49 p=1.5e-08 |

Each cell: median rho [interquartile range over lineages], lineages positive / lineages, sign-test p.

Coverage of rated words (median over charged cells, share of mass): `k_charge` barred 1.00, arriving 1.00, base 1.00; `inst:arousal` barred 0.00, arriving 0.05, base 0.09; `affect:scene_intensity` barred 1.00, arriving 0.81, base 0.70; `affect:intensity` barred 1.00, arriving 0.81, base 0.70
