# Interiority curves over arc_fiction, before and after the vetted lists (EXPLORATORY)

Producer `arc_interiority_precision.py`. Same 82080 arc_fiction reps, denominator, floors (at least 2000 content tokens, 5 texts per decade and source group) as ARC_INTERIORITY.md; 75974 texts enter. BEFORE numerators from arc_interiority's parquet; AFTER lists from precision_keep_v2_vetted.csv (keep_vetted) (see the docstring for the rule). Plate: figures/arc_interiority_precision_decades_vetted.png (levels, not indexed).

## Lists

- Clean X, vetted: base_kept 872, base_rated 1526, variants_kept 1831, variants_dropped_modern thinkin, long_s 1715, expanded 4216, dropped_as_stopword 0
- Candidates, vetted: base_kept 1077, base_rated 2159, variants_kept 2588, variants_dropped_modern dont, long_s 2452, expanded 6117, dropped_as_stopword 0
- Clean X + candidates, vetted: expanded 10331

## Does the re-rating change the history? Decade-series agreement, before vs after

| source | decades | rho(clean X) | rho(candidates) | rho(clean X + candidates) | rho(clean X after, comb after) |
|---|---|---|---|---|---|
| modern/other | 20 | +0.968 | +0.277 | +0.570 | +0.159 |
| ocr | 25 | +0.865 | +0.822 | +0.900 | +0.502 |
| transcribed | 41 | +0.951 | +0.921 | +0.964 | +0.709 |

## Decade medians (percent of content tokens)

| source | decade | texts | clean X before | clean X after | cand before | cand after | comb before | comb after |
|---|---|---|---|---|---|---|---|---|
| modern/other | 1810 | 36 | 5.18 | 2.59 | 7.40 | 1.90 | 12.80 | 4.53 |
| modern/other | 1820 | 36 | 5.39 | 2.49 | 7.92 | 1.92 | 13.16 | 4.63 |
| modern/other | 1830 | 59 | 4.96 | 2.53 | 7.89 | 2.19 | 13.11 | 4.74 |
| modern/other | 1840 | 91 | 5.03 | 2.41 | 7.70 | 1.90 | 12.61 | 4.68 |
| modern/other | 1850 | 86 | 6.36 | 3.03 | 8.35 | 2.12 | 14.40 | 5.01 |
| modern/other | 1860 | 121 | 5.64 | 2.87 | 7.76 | 1.67 | 13.51 | 4.64 |
| modern/other | 1870 | 144 | 5.89 | 3.18 | 8.38 | 1.85 | 14.33 | 5.09 |
| modern/other | 1880 | 311 | 6.39 | 3.24 | 8.42 | 1.77 | 14.66 | 5.02 |
| modern/other | 1890 | 387 | 6.43 | 3.31 | 8.36 | 1.69 | 14.80 | 5.05 |
| modern/other | 1900 | 526 | 6.45 | 3.28 | 8.40 | 1.68 | 14.92 | 4.93 |
| modern/other | 1910 | 546 | 6.57 | 3.32 | 8.33 | 1.54 | 14.85 | 4.92 |
| modern/other | 1920 | 561 | 6.80 | 3.43 | 8.52 | 1.57 | 15.31 | 5.10 |
| modern/other | 1930 | 1020 | 6.69 | 3.46 | 8.31 | 1.40 | 14.95 | 4.89 |
| modern/other | 1940 | 916 | 6.77 | 3.54 | 8.32 | 1.31 | 15.13 | 4.88 |
| modern/other | 1950 | 760 | 6.65 | 3.40 | 8.10 | 1.24 | 14.70 | 4.66 |
| modern/other | 1960 | 737 | 6.51 | 3.36 | 7.86 | 1.16 | 14.52 | 4.57 |
| modern/other | 1970 | 1044 | 6.55 | 3.37 | 7.82 | 1.16 | 14.40 | 4.59 |
| modern/other | 1980 | 1753 | 6.57 | 3.38 | 7.76 | 1.16 | 14.33 | 4.56 |
| modern/other | 1990 | 3375 | 6.42 | 3.30 | 7.71 | 1.08 | 14.12 | 4.40 |
| modern/other | 2000 | 1188 | 6.09 | 3.13 | 7.43 | 1.03 | 13.60 | 4.19 |
| ocr | 1710 | 8 | 5.06 | 2.45 | 7.25 | 1.77 | 12.09 | 4.14 |
| ocr | 1720 | 5 | 5.86 | 3.02 | 8.16 | 2.17 | 13.64 | 5.18 |
| ocr | 1730 | 7 | 5.43 | 2.55 | 9.09 | 2.41 | 14.05 | 4.40 |
| ocr | 1740 | 9 | 5.73 | 2.44 | 7.40 | 2.08 | 13.40 | 4.56 |
| ocr | 1750 | 16 | 6.28 | 3.17 | 9.68 | 2.63 | 16.03 | 5.74 |
| ocr | 1760 | 25 | 6.40 | 3.41 | 10.78 | 3.35 | 17.30 | 6.39 |
| ocr | 1770 | 22 | 6.12 | 2.99 | 9.67 | 2.90 | 15.52 | 6.01 |
| ocr | 1780 | 20 | 5.83 | 2.81 | 8.86 | 2.72 | 14.64 | 5.56 |
| ocr | 1790 | 32 | 6.37 | 3.31 | 9.69 | 3.22 | 15.93 | 6.53 |
| ocr | 1800 | 395 | 6.49 | 3.20 | 9.44 | 2.98 | 15.83 | 6.21 |
| ocr | 1810 | 652 | 6.58 | 3.19 | 9.36 | 2.87 | 15.81 | 6.04 |
| ocr | 1820 | 1082 | 6.36 | 3.11 | 8.74 | 2.46 | 15.04 | 5.58 |
| ocr | 1830 | 1526 | 6.21 | 3.03 | 8.43 | 2.26 | 14.61 | 5.31 |
| ocr | 1840 | 2402 | 6.15 | 3.00 | 8.41 | 2.13 | 14.54 | 5.15 |
| ocr | 1850 | 3352 | 6.43 | 3.22 | 8.76 | 2.15 | 15.14 | 5.43 |
| ocr | 1860 | 3442 | 6.33 | 3.22 | 8.64 | 1.98 | 14.98 | 5.26 |
| ocr | 1870 | 4490 | 6.44 | 3.33 | 8.78 | 1.98 | 15.19 | 5.34 |
| ocr | 1880 | 6519 | 6.51 | 3.36 | 8.79 | 1.94 | 15.28 | 5.33 |
| ocr | 1890 | 10797 | 6.43 | 3.30 | 8.56 | 1.84 | 15.00 | 5.19 |
| ocr | 1900 | 10737 | 6.40 | 3.28 | 8.47 | 1.75 | 14.84 | 5.08 |
| ocr | 1910 | 10307 | 6.55 | 3.36 | 8.49 | 1.67 | 15.02 | 5.07 |
| ocr | 1920 | 3039 | 6.49 | 3.30 | 8.39 | 1.60 | 14.85 | 4.97 |
| ocr | 1930 | 81 | 5.12 | 2.62 | 6.75 | 1.23 | 11.72 | 3.84 |
| ocr | 1940 | 34 | 5.44 | 2.74 | 6.91 | 1.12 | 12.20 | 3.88 |
| ocr | 1950 | 23 | 5.58 | 2.84 | 7.41 | 1.37 | 13.01 | 4.25 |
| transcribed | 1600 | 45 | 5.18 | 2.67 | 7.96 | 1.82 | 13.23 | 4.54 |
| transcribed | 1610 | 28 | 5.14 | 2.47 | 8.19 | 1.89 | 12.97 | 4.53 |
| transcribed | 1620 | 25 | 5.60 | 3.01 | 9.01 | 2.15 | 14.23 | 4.68 |
| transcribed | 1630 | 38 | 5.85 | 2.83 | 8.65 | 2.55 | 14.60 | 5.30 |
| transcribed | 1640 | 21 | 5.66 | 2.83 | 8.57 | 2.25 | 14.90 | 5.03 |
| transcribed | 1650 | 40 | 6.59 | 3.50 | 10.01 | 3.21 | 16.54 | 6.65 |
| transcribed | 1660 | 32 | 6.20 | 3.23 | 9.64 | 2.62 | 15.44 | 5.73 |
| transcribed | 1670 | 35 | 6.97 | 3.58 | 10.57 | 2.77 | 16.87 | 6.30 |
| transcribed | 1680 | 78 | 6.74 | 3.57 | 10.45 | 2.90 | 17.14 | 6.29 |
| transcribed | 1690 | 51 | 6.04 | 3.17 | 9.81 | 2.56 | 15.85 | 5.84 |
| transcribed | 1700 | 16 | 6.07 | 3.05 | 8.54 | 2.23 | 14.45 | 5.29 |
| transcribed | 1710 | 15 | 5.75 | 2.93 | 8.74 | 2.38 | 14.29 | 5.21 |
| transcribed | 1720 | 53 | 6.96 | 3.43 | 10.79 | 3.18 | 17.08 | 6.62 |
| transcribed | 1730 | 22 | 6.39 | 3.03 | 9.98 | 2.98 | 15.63 | 5.79 |
| transcribed | 1740 | 25 | 6.89 | 3.49 | 10.56 | 3.17 | 17.42 | 6.79 |
| transcribed | 1750 | 53 | 7.22 | 3.63 | 11.25 | 3.36 | 18.39 | 7.21 |
| transcribed | 1760 | 61 | 7.10 | 3.60 | 10.09 | 3.05 | 16.74 | 6.77 |
| transcribed | 1770 | 56 | 7.23 | 3.69 | 10.63 | 3.48 | 17.67 | 7.11 |
| transcribed | 1780 | 69 | 7.45 | 3.65 | 11.43 | 3.86 | 18.81 | 7.59 |
| transcribed | 1790 | 182 | 7.14 | 3.63 | 10.49 | 3.41 | 17.59 | 7.00 |
| transcribed | 1800 | 88 | 6.97 | 3.45 | 9.98 | 3.23 | 16.84 | 6.64 |
| transcribed | 1810 | 108 | 7.36 | 3.74 | 10.31 | 3.22 | 17.45 | 7.17 |
| transcribed | 1820 | 170 | 6.70 | 3.33 | 9.24 | 2.65 | 15.86 | 5.98 |
| transcribed | 1830 | 240 | 6.52 | 3.17 | 8.72 | 2.39 | 15.14 | 5.56 |
| transcribed | 1840 | 320 | 6.45 | 3.19 | 8.56 | 2.14 | 14.94 | 5.30 |
| transcribed | 1850 | 295 | 6.67 | 3.43 | 9.22 | 2.31 | 15.93 | 5.78 |
| transcribed | 1860 | 263 | 6.74 | 3.50 | 9.15 | 2.13 | 15.91 | 5.69 |
| transcribed | 1870 | 236 | 6.91 | 3.60 | 9.36 | 2.08 | 16.24 | 5.73 |
| transcribed | 1880 | 243 | 7.18 | 3.78 | 9.78 | 2.28 | 16.69 | 6.12 |
| transcribed | 1890 | 194 | 7.11 | 3.80 | 9.32 | 2.11 | 16.54 | 5.90 |
| transcribed | 1900 | 19 | 6.97 | 3.56 | 9.17 | 2.10 | 16.09 | 5.52 |
| transcribed | 1910 | 8 | 6.90 | 3.37 | 7.91 | 1.82 | 15.00 | 5.31 |
| transcribed | 1920 | 12 | 6.18 | 3.07 | 7.75 | 1.20 | 14.20 | 4.33 |
| transcribed | 1930 | 12 | 5.29 | 2.58 | 6.70 | 1.19 | 12.19 | 3.80 |
| transcribed | 1940 | 5 | 6.64 | 3.28 | 7.76 | 1.32 | 15.21 | 4.70 |
| transcribed | 1950 | 14 | 7.13 | 3.65 | 8.15 | 1.19 | 15.11 | 4.75 |
| transcribed | 1960 | 19 | 6.19 | 3.30 | 7.88 | 1.15 | 13.87 | 4.26 |
| transcribed | 1970 | 14 | 6.45 | 3.37 | 7.57 | 1.22 | 14.17 | 4.55 |
| transcribed | 1980 | 21 | 6.44 | 3.30 | 7.27 | 1.04 | 14.03 | 4.35 |
| transcribed | 1990 | 15 | 5.77 | 2.89 | 7.44 | 1.02 | 13.10 | 4.00 |
| transcribed | 2000 | 8 | 6.75 | 3.45 | 7.28 | 1.03 | 14.02 | 4.57 |

## Token mass after: share of each list's tokens carried by its most frequent forms (all texts)

- Clean X, vetted: top 10 42%, top 25 57% of 2256 forms with any tokens. Top 25: know 10.1%, think 7.1%, thought 6.5%, knew 4.3%, heard 3.7%, hear 2.3%, believe 2.2%, hope 2.2%, wish 1.8%, known 1.6%, understand 1.5%, suppose 1.5%, remember 1.5%, idea 1.3%, thinking 1.2%, wonder 1.0%, knows 1.0%, attention 1.0%, forget 0.8%, surprise 0.8%, expected 0.8%, desire 0.8%, wished 0.8%, learned 0.7%, listen 0.7%
- Candidates, vetted: top 10 17%, top 25 30% of 3303 forms with any tokens. Top 25: doubt 2.4%, glad 2.3%, afraid 2.0%, thoughts 1.9%, pleasure 1.8%, happiness 1.4%, joy 1.4%, pleased 1.2%, anxious 1.2%, faith 1.1%, liked 1.1%, angry 1.1%, proud 1.1%, pride 1.0%, pity 1.0%, courage 0.9%, sorrow 0.9%, affection 0.9%, delight 0.8%, confidence 0.8%, hoped 0.8%, forgive 0.8%, grief 0.8%, fond 0.8%, wise 0.8%
