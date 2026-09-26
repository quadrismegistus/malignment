# Figure 5 draft: concrete and evaluative shares (EXPLORATORY)

Producer `arc_fig5_conc_eval.py` (method in its docstring). History 1700-2009, 9,836 texts. Concrete forms (z >= 1.0, stopwords out): 299,017.

Concrete share against abstraction's concreteness score: r = 0.928 over texts, 0.846 over model meta-texts.

## Evaluative share, aligned minus base, per lineage

| control | slope | condition | lineages up, raw | lineages up, partialled | p (partialled) | median gap raw | median gap partialled | kept |
|---|---|---|---|---|---|---|---|---|
| concreteness score | -0.0532 | Aligned models | 28/32 | 25/32 | 0.0021 | 0.0421 | 0.0329 | 78% |
| concreteness score | -0.0532 | Aligned (prefilled) | 20/23 | 20/23 | 0.0005 | 0.0474 | 0.0382 | 80% |
| concreteness score | -0.0532 | Aligned (chat) | 18/20 | 17/20 | 0.0026 | 0.0534 | 0.0403 | 75% |
| concrete share | -0.0404 | Aligned models | 28/32 | 28/32 | 0.0000 | 0.0421 | 0.0414 | 98% |
| concrete share | -0.0404 | Aligned (prefilled) | 20/23 | 20/23 | 0.0005 | 0.0474 | 0.0457 | 96% |
| concrete share | -0.0404 | Aligned (chat) | 18/20 | 18/20 | 0.0004 | 0.0534 | 0.0527 | 99% |

## Evaluative share in the history, smoothed fall 1765 to 1955

Partialled by the within-decade slope of text evaluative share on concreteness.

| control | slope | fall raw | fall partialled | kept |
|---|---|---|---|---|
| concreteness score | -0.0425 | 0.0813 | 0.0532 | 65% |
| concrete share | -0.1380 | 0.0813 | 0.0695 | 86% |
