# Figure 5 checks for the paper seat (EXPLORATORY)

Producer `arc_fig5_checks.py` (method in its docstring). Figure: figures/arc_fig5_conc_eval_v3_1700.png. History: 9,836 Chadwyck and Chicago novels, 1700-2009. USAS E list: 1734 rank-0 members of E1-E6, 10,263 forms after expansion; full X: 14,906 forms.

## 1. Paired concreteness (abstraction's text score; negative gap = more abstract)

| contrast | lineages more abstract | p | median gap |
|---|---|---|---|
| Aligned models minus Base models | 25/32 | 0.0021 | -0.1952 |
| Aligned (prefilled) minus Base models | 19/23 | 0.0026 | -0.1633 |
| Aligned (chat) minus Base models | 19/20 | 0.0000 | -0.2806 |
| Aligned (prefilled) minus Aligned models | 9/27 | 0.1221 | +0.0480 |
| Aligned (chat) minus Aligned models | 14/24 | 0.5413 | -0.0409 |

## 2. One population: the 20 lineages run in all four conditions

Lines = median over those lineages; crossings on the same smoothed 1700+ history as the figure.

| measure | line | all lineages (figure) | crossing | common set | crossing |
|---|---|---|---|---|---|
| concreteness | Base models | 0.0968 | 1969 | 0.0883 | 1964 |
| concreteness | Aligned models | -0.1248 | 1894 | -0.1417 | 1889 |
| concreteness | Aligned (prefilled) | -0.0594 | 1914 | -0.0623 | 1913 |
| concreteness | Aligned (chat) | -0.1776 | 1875 | -0.1776 | 1875 |
| evaluative share | Base models | 0.1732 | 1904 | 0.1752 | 1899 |
| evaluative share | Aligned models | 0.2212 | 1816 | 0.2226 | 1814 |
| evaluative share | Aligned (prefilled) | 0.2291 | 1726, 1803 | 0.2258 | 1708, 1809 |
| evaluative share | Aligned (chat) | 0.2327 | 1745, 1797 | 0.2302 | 1732, 1801 |

Paired tests on the common set (aligned minus base; concreteness counts MORE ABSTRACT, evaluation counts MORE EVALUATIVE):

| measure | condition | k/n | p | median gap |
|---|---|---|---|---|
| concreteness | Aligned models | 15/20 | 0.0414 | -0.1952 |
| concreteness | Aligned (prefilled) | 16/20 | 0.0118 | -0.1626 |
| concreteness | Aligned (chat) | 19/20 | 0.0000 | -0.2806 |
| evaluative share | Aligned models | 18/20 | 0.0004 | +0.0421 |
| evaluative share | Aligned (prefilled) | 18/20 | 0.0004 | +0.0500 |
| evaluative share | Aligned (chat) | 18/20 | 0.0004 | +0.0534 |

## 3. Evaluative share against inner-life vocabulary

Raw levels (median over lineages / history range):

| measure | base | aligned | prefilled | chat | history 1765 | history 1955 |
|---|---|---|---|---|---|---|
| USAS X share | 0.1166 | 0.1311 | 0.1365 | 0.1301 | 0.1106 | 0.1067 |
| USAS E share | 0.0463 | 0.0495 | 0.0495 | 0.0373 | 0.0656 | 0.0457 |
| evaluative share | 0.1732 | 0.2212 | 0.2291 | 0.2327 | 0.2360 | 0.1547 |
| evaluative share, X and E words removed | 0.1320 | 0.1632 | 0.1632 | 0.1780 | 0.1608 | 0.1148 |

Share of evaluative TOKENS that are also X or E words, model meta-texts (median): 25.9%.

Controls. History: the smoothed 1765-1955 fall, kept share. Models: aligned minus base per lineage, k MORE EVALUATIVE of n, and the median gap kept.

| control | history fall kept | aligned (raw) | prefilled | chat |
|---|---|---|---|---|
| none | 100% | 28/32 (p 0.0000), 100% | 20/23 (p 0.0005), 100% | 18/20 (p 0.0004), 100% |
| concreteness | 65% | 25/32 (p 0.0021), 78% | 20/23 (p 0.0005), 80% | 17/20 (p 0.0026), 75% |
| USAS X | 101% | 28/32 (p 0.0000), 100% | 19/23 (p 0.0026), 96% | 18/20 (p 0.0004), 96% |
| USAS E | 56% | 26/32 (p 0.0005), 79% | 19/23 (p 0.0026), 87% | 19/20 (p 0.0000), 118% |
| X and E | 52% | 27/32 (p 0.0001), 84% | 19/23 (p 0.0026), 85% | 19/20 (p 0.0000), 121% |
| X, E and concreteness | 17% | 24/32 (p 0.0070), 68% | 21/23 (p 0.0001), 64% | 19/20 (p 0.0000), 95% |
| lexical: X and E words removed | 57% | 23/32 (p 0.0201), 49% | 19/23 (p 0.0026), 56% | 17/20 (p 0.0026), 78% |

Gap kept is against the UNCONTROLLED evaluative gap in every row, including the lexical one, so the rows are comparable.
That makes the lexical row conservative: removing X and E words shrinks the lexicon, so absolute gaps shrink with it. In RELATIVE terms (from the levels table): history 1765 to 1955, all evaluative words -34%, X and E removed -29%; base to aligned / prefilled / chat, all +28% / +32% / +34%, removed +24% / +24% / +35%.
Statistical partials on E overlap the evaluative lexicon by construction (love, fear), so they remove shared vocabulary as well as shared variance; the lexical row is the cleaner test of whether inner-life words carry the result.
