# Vector norms: concreteness, valence, arousal, with four arms (EXPLORATORY)

Producer `arc_fig5_vector.py` (method in its docstring). Arm values are medians over 30 lineages of meta-text scores; placement = crossing years of the smoothed history; agreement = lineages (of 30) whose arm moves from base in the median's direction. No partial or adjustment here.

| measure | Base models | Aligned models | Aligned, chat, prefilled | Aligned, chat, asked | agreement raw / prefill / asked |
|---|---|---|---|---|---|
| conc | +0.137 (2001) | -0.037 (1933) | -0.136 (1907) | -0.275 (1606, 1868) | 27 / 29 / 30 |
| valence | -0.066 (below all) | -0.075 (below all) | -0.017 (below all) | -0.095 (below all) | 16 / 20 / 19 |
| arousal | +0.128 (1921) | +0.235 (1875) | +0.242 (1872) | +0.386 (1652, 1811) | 26 / 25 / 29 |

History ranges (smoothed): conc -0.584 to 0.145; valence 0.007 to 0.131; arousal -0.005 to 0.439
