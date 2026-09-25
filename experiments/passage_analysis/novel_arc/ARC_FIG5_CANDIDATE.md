# Figure 5 candidate: four measures, four arms (EXPLORATORY)

Producer `arc_fig5_candidate.py` (method in its docstring). Plate: figures/arc_fig5_candidate_v1.png. Arms are medians over 30 lineages of per-model meta-texts. Crossing years: where an arm's level crosses the smoothed history (several where the curve is not monotone; 'above'/'below' where it clears every decade).

| measure | Base models | Aligned models | Aligned, chat, prefilled | Aligned, chat, asked |
|---|---|---|---|---|
| conc | 0.137 (2001) | -0.036 (1933) | -0.135 (1907) | -0.275 (1606, 1868) |
| valence | 5.646 (below all) | 5.690 (1662, 1792, 1840, 1928) | 5.739 (above all) | 5.631 (below all) |
| arousal | 4.166 (1667, 1694) | 4.159 (1651, 1709) | 4.152 (1629, 1725) | 4.167 (1671, 1689) |
| emo | 2.10% (1886) | 2.51% (1638, 1843) | 2.99% (1728, 1805) | 4.15% (above all) |

Per-lineage agreement with the median ordering (share of the 30 lineages where the aligned arm moves from base in the median's direction):

- conc: raw 27/30, prefill 29/30, continue 30/30
- valence: raw 20/30, prefill 22/30, continue 18/30
- arousal: raw 13/30, prefill 20/30, continue 16/30
- emo: raw 23/30, prefill 27/30, continue 30/30
