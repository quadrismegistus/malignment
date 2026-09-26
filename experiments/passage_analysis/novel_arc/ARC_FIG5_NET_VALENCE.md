# Net valence (positive minus negative), Figure 5 variant (EXPLORATORY)

Producer `arc_fig5_net_valence.py` (method in its docstring). Plate: figures/arc_fig5_conc_netval_v1_1700.png. Per content word.

## Model lines (median over lineages)

| line | positive | negative | net | sum (v4 panel) | placement of net on the history |
|---|---|---|---|---|---|
| Base models | 0.1190 | 0.0517 | 0.0681 | 0.1721 | above every decade |
| Aligned models | 0.1840 | 0.0353 | 0.1399 | 0.2174 | above every decade |
| Aligned (prefilled) | 0.1829 | 0.0398 | 0.1413 | 0.2217 | above every decade |
| Aligned (chat) | 0.1844 | 0.0443 | 0.1388 | 0.2322 | above every decade |

Medians are taken per measure, so positive minus negative medians need not equal the net median.

## History (smoothed net)

- Range 0.0283 to 0.0642; peak at 1705.
- 1765: 0.0608; 1955: 0.0290; 2005: 0.0316.
- With concreteness partialled (within-decade slope -0.0133): 1765 0.0535, 1955 0.0291.

## Aligned minus base, per lineage (net)

| condition | up, raw | p | median gap | up, concreteness partialled | p | median gap |
|---|---|---|---|---|---|---|
| Aligned models | 29/32 | 0.0000 | +0.0690 | 30/32 | 0.0000 | +0.0551 |
| Aligned (prefilled) | 23/23 | 0.0000 | +0.0554 | 21/23 | 0.0001 | +0.0532 |
| Aligned (chat) | 17/20 | 0.0026 | +0.0816 | 16/20 | 0.0118 | +0.0584 |
