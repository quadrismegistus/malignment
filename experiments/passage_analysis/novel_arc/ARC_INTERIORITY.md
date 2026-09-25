# Interiority word lists over the arc_fiction set (EXPLORATORY)

Producer `arc_interiority.py`. 82080 arc_fiction reps (abstraction.scores_rep), share of alphabetic non-stopword tokens (lltk.text_freqs, surface forms) on each list; texts with at least 2000 such tokens (75974 texts); decade median over texts, decades with at least 5 texts per source group. Lists and their spelling expansion (MorphAdorner variants plus long-s OCR variants not common as modern words): Full USAS X 3225 -> 14908; Clean X 1526 -> 8633; Period candidates 2161 -> 15276; Clean X + candidates 3687 -> 23850. Plate: figures/arc_interiority_decades.png (each list indexed to its own mean, to compare shapes).

## Do the period candidates change the history? Decade-series agreement with clean X

| source | decades | span | rho(clean X, clean X + candidates) | rho(clean X, candidates) | rho(clean X, full X) |
|---|---|---|---|---|---|
| modern/other | 20 | 1810-2000 | +0.884 | +0.411 | +0.988 |
| ocr | 25 | 1710-1950 | +0.738 | +0.474 | +0.835 |
| transcribed | 41 | 1600-2000 | +0.826 | +0.627 | +0.772 |

## Decade medians (percent of content tokens)

| source | decade | texts | full X | clean X | candidates | clean X + candidates |
|---|---|---|---|---|---|---|
| modern/other | 1810 | 36 | 7.99 | 5.18 | 7.40 | 12.80 |
| modern/other | 1820 | 36 | 8.68 | 5.39 | 7.92 | 13.16 |
| modern/other | 1830 | 59 | 8.16 | 4.96 | 7.89 | 13.11 |
| modern/other | 1840 | 91 | 8.36 | 5.03 | 7.70 | 12.61 |
| modern/other | 1850 | 86 | 9.92 | 6.36 | 8.35 | 14.40 |
| modern/other | 1860 | 121 | 9.13 | 5.64 | 7.76 | 13.51 |
| modern/other | 1870 | 144 | 9.50 | 5.89 | 8.38 | 14.33 |
| modern/other | 1880 | 311 | 10.14 | 6.39 | 8.42 | 14.66 |
| modern/other | 1890 | 387 | 10.24 | 6.43 | 8.36 | 14.80 |
| modern/other | 1900 | 526 | 10.36 | 6.45 | 8.40 | 14.92 |
| modern/other | 1910 | 546 | 10.51 | 6.57 | 8.33 | 14.85 |
| modern/other | 1920 | 561 | 10.71 | 6.80 | 8.52 | 15.31 |
| modern/other | 1930 | 1020 | 10.54 | 6.69 | 8.31 | 14.95 |
| modern/other | 1940 | 916 | 10.67 | 6.77 | 8.32 | 15.13 |
| modern/other | 1950 | 760 | 10.63 | 6.65 | 8.10 | 14.70 |
| modern/other | 1960 | 737 | 10.46 | 6.51 | 7.86 | 14.52 |
| modern/other | 1970 | 1044 | 10.36 | 6.55 | 7.82 | 14.40 |
| modern/other | 1980 | 1753 | 10.39 | 6.57 | 7.76 | 14.33 |
| modern/other | 1990 | 3375 | 10.26 | 6.42 | 7.71 | 14.12 |
| modern/other | 2000 | 1188 | 9.91 | 6.09 | 7.43 | 13.60 |
| ocr | 1710 | 8 | 8.34 | 5.06 | 7.25 | 12.09 |
| ocr | 1720 | 5 | 9.71 | 5.86 | 8.16 | 13.64 |
| ocr | 1730 | 7 | 8.96 | 5.43 | 9.09 | 14.05 |
| ocr | 1740 | 9 | 8.51 | 5.73 | 7.40 | 13.40 |
| ocr | 1750 | 16 | 9.34 | 6.28 | 9.68 | 16.03 |
| ocr | 1760 | 25 | 9.49 | 6.40 | 10.78 | 17.30 |
| ocr | 1770 | 22 | 9.43 | 6.12 | 9.67 | 15.52 |
| ocr | 1780 | 20 | 9.12 | 5.83 | 8.86 | 14.64 |
| ocr | 1790 | 32 | 9.59 | 6.37 | 9.69 | 15.93 |
| ocr | 1800 | 395 | 9.67 | 6.49 | 9.44 | 15.83 |
| ocr | 1810 | 652 | 9.78 | 6.58 | 9.36 | 15.81 |
| ocr | 1820 | 1082 | 9.76 | 6.36 | 8.74 | 15.04 |
| ocr | 1830 | 1526 | 9.80 | 6.21 | 8.43 | 14.61 |
| ocr | 1840 | 2402 | 9.62 | 6.15 | 8.41 | 14.54 |
| ocr | 1850 | 3352 | 9.96 | 6.43 | 8.76 | 15.14 |
| ocr | 1860 | 3442 | 9.92 | 6.33 | 8.64 | 14.98 |
| ocr | 1870 | 4490 | 10.07 | 6.44 | 8.78 | 15.19 |
| ocr | 1880 | 6519 | 10.16 | 6.51 | 8.79 | 15.28 |
| ocr | 1890 | 10797 | 10.15 | 6.43 | 8.56 | 15.00 |
| ocr | 1900 | 10737 | 10.23 | 6.40 | 8.47 | 14.84 |
| ocr | 1910 | 10307 | 10.45 | 6.55 | 8.49 | 15.02 |
| ocr | 1920 | 3039 | 10.42 | 6.49 | 8.39 | 14.85 |
| ocr | 1930 | 81 | 8.46 | 5.12 | 6.75 | 11.72 |
| ocr | 1940 | 34 | 9.06 | 5.44 | 6.91 | 12.20 |
| ocr | 1950 | 23 | 9.04 | 5.58 | 7.41 | 13.01 |
| transcribed | 1600 | 45 | 8.93 | 5.18 | 7.96 | 13.23 |
| transcribed | 1610 | 28 | 8.74 | 5.14 | 8.19 | 12.97 |
| transcribed | 1620 | 25 | 9.49 | 5.60 | 9.01 | 14.23 |
| transcribed | 1630 | 38 | 9.60 | 5.85 | 8.65 | 14.60 |
| transcribed | 1640 | 21 | 9.43 | 5.66 | 8.57 | 14.90 |
| transcribed | 1650 | 40 | 10.11 | 6.59 | 10.01 | 16.54 |
| transcribed | 1660 | 32 | 9.64 | 6.20 | 9.64 | 15.44 |
| transcribed | 1670 | 35 | 10.28 | 6.97 | 10.57 | 16.87 |
| transcribed | 1680 | 78 | 10.39 | 6.74 | 10.45 | 17.14 |
| transcribed | 1690 | 51 | 9.65 | 6.04 | 9.81 | 15.85 |
| transcribed | 1700 | 16 | 9.71 | 6.07 | 8.54 | 14.45 |
| transcribed | 1710 | 15 | 9.00 | 5.75 | 8.74 | 14.29 |
| transcribed | 1720 | 53 | 10.27 | 6.96 | 10.79 | 17.08 |
| transcribed | 1730 | 22 | 9.67 | 6.39 | 9.98 | 15.63 |
| transcribed | 1740 | 25 | 10.16 | 6.89 | 10.56 | 17.42 |
| transcribed | 1750 | 53 | 10.29 | 7.22 | 11.25 | 18.39 |
| transcribed | 1760 | 61 | 10.35 | 7.10 | 10.09 | 16.74 |
| transcribed | 1770 | 56 | 10.30 | 7.23 | 10.63 | 17.67 |
| transcribed | 1780 | 69 | 10.49 | 7.45 | 11.43 | 18.81 |
| transcribed | 1790 | 182 | 10.26 | 7.14 | 10.49 | 17.59 |
| transcribed | 1800 | 88 | 10.05 | 6.97 | 9.98 | 16.84 |
| transcribed | 1810 | 108 | 10.49 | 7.36 | 10.31 | 17.45 |
| transcribed | 1820 | 170 | 10.19 | 6.70 | 9.24 | 15.86 |
| transcribed | 1830 | 240 | 10.09 | 6.52 | 8.72 | 15.14 |
| transcribed | 1840 | 320 | 9.97 | 6.45 | 8.56 | 14.94 |
| transcribed | 1850 | 295 | 10.39 | 6.67 | 9.22 | 15.93 |
| transcribed | 1860 | 263 | 10.49 | 6.74 | 9.15 | 15.91 |
| transcribed | 1870 | 236 | 10.64 | 6.91 | 9.36 | 16.24 |
| transcribed | 1880 | 243 | 10.83 | 7.18 | 9.78 | 16.69 |
| transcribed | 1890 | 194 | 10.87 | 7.11 | 9.32 | 16.54 |
| transcribed | 1900 | 19 | 10.82 | 6.97 | 9.17 | 16.09 |
| transcribed | 1910 | 8 | 10.56 | 6.90 | 7.91 | 15.00 |
| transcribed | 1920 | 12 | 9.80 | 6.18 | 7.75 | 14.20 |
| transcribed | 1930 | 12 | 8.91 | 5.29 | 6.70 | 12.19 |
| transcribed | 1940 | 5 | 11.04 | 6.64 | 7.76 | 15.21 |
| transcribed | 1950 | 14 | 11.17 | 7.13 | 8.15 | 15.11 |
| transcribed | 1960 | 19 | 10.02 | 6.19 | 7.88 | 13.87 |
| transcribed | 1970 | 14 | 10.52 | 6.45 | 7.57 | 14.17 |
| transcribed | 1980 | 21 | 10.53 | 6.44 | 7.27 | 14.03 |
| transcribed | 1990 | 15 | 9.54 | 5.77 | 7.44 | 13.10 |
| transcribed | 2000 | 8 | 10.46 | 6.75 | 7.28 | 14.02 |

## Candidate words carrying the most tokens, by century and source (the spelling check)

- C12 transcribed: love 4.4%, would 3.8%, like 2.0%, passions 1.7%, pleasure 1.5%, truth 1.5%, happy 1.4%, design 1.3%, seemed 1.1%, happiness 1.1%, pleasures 1.0%, sentiments 1.0%, says 1.0%, find 1.0%, ought 1.0%
- C15 transcribed: say 3.8%, wold 3.5%, loue 3.1%, ought 2.9%, saye 2.9%, would 2.6%, wise 2.1%, wyse 2.1%, love 1.8%, answered 1.7%, wolde 1.7%, telle 1.4%, lyke 1.4%, praye 1.3%, ansuerd 1.0%
- C16 transcribed: would 5.4%, like 3.2%, love 2.8%, say 2.4%, loue 2.0%, answered 1.6%, wise 1.4%, pleasure 1.2%, tell 1.1%, pray 1.0%, saith 0.9%, certain 0.8%, find 0.8%, fear 0.8%, mean 0.7%
- C17 transcribed: would 7.5%, love 3.7%, like 2.6%, say 1.9%, told 1.6%, tell 1.3%, answered 1.2%, find 1.2%, fear 1.0%, affection 0.9%, answer 0.9%, thoughts 0.8%, pleasure 0.8%, seemed 0.7%, certain 0.7%
- C18 modern/other: would 6.6%, told 3.6%, love 2.8%, like 2.3%, says 2.2%, truth 1.7%, say 1.5%, find 1.2%, sure 1.2%, asked 1.1%, joy 1.0%, wit 1.0%, read 1.0%, tell 1.0%, happy 0.9%
- C18 ocr: would 7.0%, love 2.2%, like 1.8%, told 1.4%, find 1.2%, tell 1.0%, happy 1.0%, fay 1.0%, look 0.8%, fear 0.7%, pleasure 0.7%, get 0.7%, truth 0.6%, fays 0.6%, ought 0.6%
- C18 transcribed: would 6.9%, love 2.0%, say 1.5%, like 1.5%, told 1.4%, find 1.1%, tell 1.1%, happy 1.0%, pleasure 0.9%, seemed 0.9%, happiness 0.9%, look 0.8%, answered 0.8%, fear 0.7%, says 0.7%
- C19 modern/other: would 7.6%, like 4.4%, say 2.8%, love 2.2%, tell 2.0%, look 1.9%, get 1.8%, looked 1.8%, seemed 1.7%, asked 1.5%, told 1.3%, find 1.2%, looking 1.0%, sure 0.9%, answered 0.9%
- C19 ocr: would 7.7%, like 3.6%, say 2.6%, love 2.0%, tell 1.8%, look 1.7%, looked 1.7%, seemed 1.6%, asked 1.4%, get 1.4%, told 1.3%, find 1.1%, sure 1.0%, answered 0.9%, looking 0.9%
- C19 transcribed: would 7.5%, like 3.3%, say 2.5%, love 1.8%, look 1.6%, seemed 1.6%, tell 1.6%, looked 1.5%, told 1.1%, get 1.1%, asked 1.0%, find 1.0%, sure 1.0%, looking 0.8%, answered 0.8%
- C20 modern/other: would 8.6%, like 7.0%, get 3.9%, looked 3.2%, say 2.5%, asked 2.5%, tell 2.3%, look 2.3%, told 2.2%, seemed 1.8%, sure 1.4%, find 1.4%, looking 1.3%, love 1.2%, mean 1.1%
- C20 ocr: would 8.1%, like 4.5%, say 2.6%, get 2.3%, looked 2.2%, tell 2.1%, asked 2.0%, seemed 1.9%, look 1.9%, told 1.7%, love 1.7%, find 1.1%, sure 1.0%, answered 1.0%, looking 1.0%
- C20 transcribed: would 8.7%, like 7.5%, get 3.5%, looked 2.8%, say 2.7%, look 2.3%, asked 2.2%, tell 2.0%, told 1.8%, seemed 1.8%, looking 1.3%, find 1.2%, sure 1.2%, mean 1.2%, love 1.2%
- C21 modern/other: would 8.7%, like 7.8%, get 4.2%, looked 3.5%, asked 2.8%, look 2.5%, say 2.5%, told 2.4%, tell 2.3%, sure 1.7%, seemed 1.6%, need 1.5%, find 1.5%, looking 1.4%, says 1.2%
- C21 transcribed: would 9.0%, like 4.3%, looked 2.8%, get 2.4%, tell 1.9%, asked 1.9%, say 1.7%, told 1.7%, look 1.6%, seemed 1.5%, need 1.4%, find 1.4%, looking 1.1%, sure 1.1%, secret 1.0%

## Token-mass concentration: share of a list's tokens carried by its most frequent words (all texts)

- Clean X: top 10 29%, top 25 43%, top 50 55%, top 100 69% of 4772 words with any tokens. Top 25: know 5.2%, see 4.8%, think 3.6%, thought 3.4%, saw 2.2%, knew 2.2%, mind 2.0%, heard 1.9%, felt 1.8%, want 1.8%, seen 1.5%, hear 1.2%, believe 1.1%, hope 1.1%, feel 1.1%, wish 0.9%, lost 0.9%, wanted 0.8%, known 0.8%, understand 0.8%, suppose 0.8%, remember 0.8%, feeling 0.8%, sight 0.7%, reason 0.7%
- Period candidates: top 10 28%, top 25 40%, top 50 50%, top 100 61% of 8199 words with any tokens. Top 25: would 7.9%, like 4.4%, say 2.6%, looked 2.0%, get 2.0%, tell 2.0%, look 1.9%, love 1.8%, asked 1.7%, seemed 1.7%, told 1.6%, find 1.2%, sure 1.1%, looking 1.0%, answered 0.9%, mean 0.8%, says 0.7%, read 0.7%, ask 0.7%, happy 0.7%, need 0.6%, answer 0.6%, certain 0.6%, fear 0.6%, question 0.6%
