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
