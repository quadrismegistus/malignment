# Does the affect that arrives scale with the charge that left?

Producer `proportionality.py` (spec in its docstring). Per (lineage, English prompt): W = charge withdrawn from barred departing words (act >= 4), A = intensity of arriving mass, B = the frame's own base-weighted level. Per lineage (>= 15 prompts past an 80% coverage gate), Spearman rho across prompts; median over lineages, two-sided sign test. **Freud: rho(A-B, W) > 0. Cooling: <= 0.**

| scale | cells (charged / past gate) | lineages | rho(A-B, W) | rho(A, W), no control | rho(B, W), the scene | rho(A-B, M), mass only | rho(A-B_all, W), coupled control |
|---|---|---|---|---|---|---|---|
| `k_charge` | 30878 / 30195 | 49 | +0.010 [-0.04, +0.04] 27/49 p=0.57 | +0.165 [+0.11, +0.20] 46/49 p=7e-11 | +0.228 [+0.16, +0.27] 48/49 p=1.8e-13 | +0.004 [-0.05, +0.05] 26/49 p=0.78 | -0.345 [-0.43, -0.31] 0/49 p=3.6e-15 |
| `inst:arousal` | 30878 / 4296 | 47 | -0.073 [-0.26, +0.05] 19/47 p=0.24 | +0.463 [+0.38, +0.52] 47/47 p=1.4e-14 | +0.497 [+0.42, +0.58] 47/47 p=1.4e-14 | -0.058 [-0.24, +0.03] 17/47 p=0.079 | -0.261 [-0.39, -0.14] 2/47 p=1.6e-11 |

Each cell: median rho [interquartile range over lineages], lineages positive / lineages, sign-test p.

Coverage of rated words (median over charged cells, share of mass): `k_charge` barred 1.00, arriving 1.00, base 1.00; `inst:arousal` barred 0.00, arriving 0.05, base 0.09
