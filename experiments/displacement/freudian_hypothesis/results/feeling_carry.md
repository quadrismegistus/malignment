# Does the arriving mass keep the barred word's feeling, or the scene's?

Producer `feeling_carry.py` (design in its docstring, declared before it ran). 12113 gated (lineage, prompt) cells.

- **CARRY beyond the scene**, O - E per lineage: +0.100 [+0.086, +0.113] +49/-0 of 49, p=3.6e-15
- **DECISIVE cells** (barred word's feeling differs from the frame's; 49 lineages with >= 5): share of arriving mass with the BARRED feeling minus share with the FRAME's feeling: -0.371 [-0.421, -0.302] +0/-49 of 49, p=3.6e-15
- **Suppression**: where the barred mass carried a feeling (> 50% named), median share of arriving mass rated `none`: 0.00 over 10373 cells

Pooled matrix, barred feeling (rows) -> arriving feeling (columns), each cell's joint mass summed over cells, row-normalised:

| barred \ arriving | anger | fear | desire | grief | disgust | shame | tenderness | joy | none | row mass |
|---|---|---|---|---|---|---|---|---|---|---|
| anger | **0.59** | 0.10 | 0.04 | 0.02 | 0.01 | 0.01 | 0.02 | 0.01 | 0.20 | 4778 |
| fear | 0.10 | **0.60** | 0.04 | 0.01 | 0.00 | 0.01 | 0.02 | 0.01 | 0.19 | 3583 |
| desire | 0.02 | 0.08 | **0.71** | 0.01 | 0.01 | 0.01 | 0.08 | 0.00 | 0.08 | 783 |
| grief | 0.06 | 0.09 | 0.12 | **0.29** | 0.00 | 0.03 | 0.13 | 0.01 | 0.26 | 673 |
| disgust | 0.05 | 0.10 | 0.05 | 0.03 | **0.52** | 0.00 | 0.02 | 0.01 | 0.22 | 169 |
| shame | 0.01 | 0.27 | 0.06 | 0.06 | 0.00 | **0.25** | 0.02 | 0.03 | 0.30 | 216 |
| tenderness | 0.00 | 0.01 | 0.01 | 0.00 | 0.00 | 0.00 | **0.61** | 0.01 | 0.36 | 96 |
| joy | 0.09 | 0.08 | 0.00 | 0.02 | 0.00 | 0.00 | 0.00 | **0.40** | 0.41 | 54 |
| none | 0.08 | 0.09 | 0.02 | 0.01 | 0.01 | 0.01 | 0.05 | 0.02 | **0.71** | 1710 |

## TYPE ARM: `doer_feeling` (words rated alone)

29968 gated cells.

- **CARRY beyond the scene's own words** (O - S per lineage): -0.008 [-0.016, -0.002] +9/-40 of 49, p=9.3e-06
- **DECISIVE** (barred named feeling differs from the scene's named feeling; 17013 cells, 49 lineages with >= 5): arriving share with the BARRED feeling minus with the SCENE's: -0.166 [-0.195, -0.132] +0/-49 of 49, p=3.6e-15

| barred \ arriving | anger | fear | desire | grief | disgust | shame | tenderness | joy | none | row mass |
|---|---|---|---|---|---|---|---|---|---|---|
| anger | **0.09** | 0.07 | 0.03 | 0.03 | 0.00 | 0.01 | 0.04 | 0.05 | 0.68 | 12617 |
| fear | 0.06 | **0.07** | 0.03 | 0.03 | 0.00 | 0.02 | 0.03 | 0.04 | 0.71 | 6548 |
| desire | 0.03 | 0.05 | **0.02** | 0.02 | 0.00 | 0.02 | 0.03 | 0.09 | 0.74 | 2260 |
| grief | 0.06 | 0.06 | 0.02 | **0.04** | 0.01 | 0.02 | 0.03 | 0.05 | 0.70 | 1032 |
| disgust | 0.11 | 0.04 | 0.03 | 0.01 | **0.00** | 0.01 | 0.06 | 0.07 | 0.68 | 284 |
| shame | 0.03 | 0.13 | 0.02 | 0.04 | 0.00 | **0.04** | 0.08 | 0.08 | 0.58 | 535 |
| joy | 0.03 | 0.04 | 0.06 | 0.03 | 0.00 | 0.04 | 0.01 | **0.03** | 0.77 | 23 |
| none | 0.04 | 0.04 | 0.01 | 0.02 | 0.00 | 0.01 | 0.02 | 0.03 | **0.82** | 6669 |

## TYPE ARM: `evoked_feeling` (words rated alone)

29968 gated cells.

- **CARRY beyond the scene's own words** (O - S per lineage): -0.004 [-0.011, +0.003] +14/-35 of 49, p=0.0038
- **DECISIVE** (barred named feeling differs from the scene's named feeling; 17597 cells, 49 lineages with >= 5): arriving share with the BARRED feeling minus with the SCENE's: -0.147 [-0.181, -0.114] +0/-49 of 49, p=3.6e-15

| barred \ arriving | anger | fear | desire | grief | disgust | shame | tenderness | joy | none | row mass |
|---|---|---|---|---|---|---|---|---|---|---|
| anger | **0.01** | 0.10 | 0.00 | 0.03 | 0.01 | 0.00 | 0.05 | 0.02 | 0.78 | 4313 |
| fear | 0.01 | **0.11** | 0.00 | 0.03 | 0.01 | 0.00 | 0.06 | 0.03 | 0.74 | 14854 |
| desire | 0.00 | 0.00 | **0.20** | 0.00 | 0.01 | 0.00 | 0.06 | 0.01 | 0.72 | 155 |
| grief | 0.00 | 0.08 | 0.00 | **0.05** | 0.01 | 0.00 | 0.07 | 0.03 | 0.76 | 4923 |
| disgust | 0.01 | 0.08 | 0.02 | 0.02 | **0.03** | 0.00 | 0.12 | 0.04 | 0.68 | 3059 |
| shame | 0.01 | 0.12 | 0.04 | 0.13 | 0.00 | **0.00** | 0.20 | 0.21 | 0.29 | 54 |
| tenderness | 0.00 | 0.11 | 0.00 | 0.03 | 0.01 | 0.00 | **0.10** | 0.04 | 0.71 | 232 |
| joy | 0.00 | 0.01 | 0.00 | 0.05 | 0.00 | 0.00 | 0.00 | **0.43** | 0.51 | 1 |
| none | 0.01 | 0.04 | 0.00 | 0.02 | 0.00 | 0.00 | 0.04 | 0.01 | **0.87** | 2376 |
