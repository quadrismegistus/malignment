# Interiority curves over arc_fiction, before and after the precision re-rating (EXPLORATORY)

Producer `arc_interiority_precision.py`. Same 82080 arc_fiction reps, denominator, floors (at least 2000 content tokens, 5 texts per decade and source group) as ARC_INTERIORITY.md; 75974 texts enter. BEFORE numerators from arc_interiority's parquet; AFTER lists from precision_keep_v2.csv (see the docstring for the rule). Plate: figures/arc_interiority_precision_decades.png (levels, not indexed).

## Lists

- Clean X, precision: base_kept 1054, base_rated 1526, variants_kept 2557, variants_dropped_modern thinkin, long_s 2107, expanded 5514, dropped_as_stopword 0
- Candidates, precision: base_kept 1243, base_rated 2159, variants_kept 3125, variants_dropped_modern dont, lovin, long_s 2993, expanded 7361, dropped_as_stopword 0
- Clean X + candidates, precision: expanded 12873

## Does the re-rating change the history? Decade-series agreement, before vs after

| source | decades | rho(clean X) | rho(candidates) | rho(clean X + candidates) | rho(clean X after, comb after) |
|---|---|---|---|---|---|
| modern/other | 20 | +0.944 | +0.304 | +0.820 | +0.447 |
| ocr | 25 | +0.931 | +0.822 | +0.898 | +0.621 |
| transcribed | 41 | +0.971 | +0.924 | +0.951 | +0.721 |

## Decade medians (percent of content tokens)

| source | decade | texts | clean X before | clean X after | cand before | cand after | comb before | comb after |
|---|---|---|---|---|---|---|---|---|
| modern/other | 1810 | 36 | 5.18 | 3.95 | 7.40 | 2.59 | 12.80 | 6.62 |
| modern/other | 1820 | 36 | 5.39 | 3.89 | 7.92 | 2.84 | 13.16 | 6.73 |
| modern/other | 1830 | 59 | 4.96 | 3.81 | 7.89 | 2.88 | 13.11 | 6.50 |
| modern/other | 1840 | 91 | 5.03 | 3.72 | 7.70 | 2.69 | 12.61 | 6.58 |
| modern/other | 1850 | 86 | 6.36 | 4.76 | 8.35 | 2.87 | 14.40 | 7.65 |
| modern/other | 1860 | 121 | 5.64 | 4.47 | 7.76 | 2.28 | 13.51 | 6.81 |
| modern/other | 1870 | 144 | 5.89 | 4.71 | 8.38 | 2.55 | 14.33 | 7.28 |
| modern/other | 1880 | 311 | 6.39 | 4.99 | 8.42 | 2.59 | 14.66 | 7.47 |
| modern/other | 1890 | 387 | 6.43 | 5.03 | 8.36 | 2.45 | 14.80 | 7.41 |
| modern/other | 1900 | 526 | 6.45 | 5.04 | 8.40 | 2.42 | 14.92 | 7.42 |
| modern/other | 1910 | 546 | 6.57 | 5.12 | 8.33 | 2.26 | 14.85 | 7.40 |
| modern/other | 1920 | 561 | 6.80 | 5.22 | 8.52 | 2.28 | 15.31 | 7.58 |
| modern/other | 1930 | 1020 | 6.69 | 5.26 | 8.31 | 2.05 | 14.95 | 7.34 |
| modern/other | 1940 | 916 | 6.77 | 5.39 | 8.32 | 1.92 | 15.13 | 7.37 |
| modern/other | 1950 | 760 | 6.65 | 5.27 | 8.10 | 1.85 | 14.70 | 7.12 |
| modern/other | 1960 | 737 | 6.51 | 5.20 | 7.86 | 1.73 | 14.52 | 7.03 |
| modern/other | 1970 | 1044 | 6.55 | 5.25 | 7.82 | 1.76 | 14.40 | 6.99 |
| modern/other | 1980 | 1753 | 6.57 | 5.24 | 7.76 | 1.75 | 14.33 | 7.03 |
| modern/other | 1990 | 3375 | 6.42 | 5.16 | 7.71 | 1.64 | 14.12 | 6.84 |
| modern/other | 2000 | 1188 | 6.09 | 4.87 | 7.43 | 1.59 | 13.60 | 6.51 |
| ocr | 1710 | 8 | 5.06 | 3.77 | 7.25 | 2.51 | 12.09 | 6.18 |
| ocr | 1720 | 5 | 5.86 | 4.32 | 8.16 | 2.99 | 13.64 | 7.31 |
| ocr | 1730 | 7 | 5.43 | 3.86 | 9.09 | 3.06 | 14.05 | 6.75 |
| ocr | 1740 | 9 | 5.73 | 4.27 | 7.40 | 2.88 | 13.40 | 7.29 |
| ocr | 1750 | 16 | 6.28 | 4.90 | 9.68 | 3.52 | 16.03 | 8.46 |
| ocr | 1760 | 25 | 6.40 | 5.05 | 10.78 | 4.34 | 17.30 | 9.59 |
| ocr | 1770 | 22 | 6.12 | 4.71 | 9.67 | 3.85 | 15.52 | 8.49 |
| ocr | 1780 | 20 | 5.83 | 4.47 | 8.86 | 3.77 | 14.64 | 8.15 |
| ocr | 1790 | 32 | 6.37 | 5.04 | 9.69 | 4.26 | 15.93 | 9.28 |
| ocr | 1800 | 395 | 6.49 | 5.00 | 9.44 | 3.88 | 15.83 | 8.92 |
| ocr | 1810 | 652 | 6.58 | 5.00 | 9.36 | 3.81 | 15.81 | 8.86 |
| ocr | 1820 | 1082 | 6.36 | 4.82 | 8.74 | 3.34 | 15.04 | 8.13 |
| ocr | 1830 | 1526 | 6.21 | 4.72 | 8.43 | 3.11 | 14.61 | 7.83 |
| ocr | 1840 | 2402 | 6.15 | 4.69 | 8.41 | 2.95 | 14.54 | 7.67 |
| ocr | 1850 | 3352 | 6.43 | 4.93 | 8.76 | 2.99 | 15.14 | 7.96 |
| ocr | 1860 | 3442 | 6.33 | 4.88 | 8.64 | 2.75 | 14.98 | 7.71 |
| ocr | 1870 | 4490 | 6.44 | 5.00 | 8.78 | 2.77 | 15.19 | 7.76 |
| ocr | 1880 | 6519 | 6.51 | 5.04 | 8.79 | 2.72 | 15.28 | 7.80 |
| ocr | 1890 | 10797 | 6.43 | 4.95 | 8.56 | 2.58 | 15.00 | 7.60 |
| ocr | 1900 | 10737 | 6.40 | 4.95 | 8.47 | 2.49 | 14.84 | 7.47 |
| ocr | 1910 | 10307 | 6.55 | 5.10 | 8.49 | 2.38 | 15.02 | 7.51 |
| ocr | 1920 | 3039 | 6.49 | 5.02 | 8.39 | 2.30 | 14.85 | 7.37 |
| ocr | 1930 | 81 | 5.12 | 3.93 | 6.75 | 1.75 | 11.72 | 5.66 |
| ocr | 1940 | 34 | 5.44 | 4.24 | 6.91 | 1.68 | 12.20 | 5.91 |
| ocr | 1950 | 23 | 5.58 | 4.43 | 7.41 | 1.97 | 13.01 | 6.47 |
| transcribed | 1600 | 45 | 5.18 | 4.20 | 7.96 | 2.47 | 13.23 | 6.54 |
| transcribed | 1610 | 28 | 5.14 | 3.79 | 8.19 | 2.56 | 12.97 | 6.54 |
| transcribed | 1620 | 25 | 5.60 | 4.29 | 9.01 | 2.86 | 14.23 | 6.55 |
| transcribed | 1630 | 38 | 5.85 | 4.61 | 8.65 | 3.44 | 14.60 | 7.49 |
| transcribed | 1640 | 21 | 5.66 | 4.40 | 8.57 | 3.04 | 14.90 | 7.48 |
| transcribed | 1650 | 40 | 6.59 | 5.25 | 10.01 | 4.17 | 16.54 | 9.35 |
| transcribed | 1660 | 32 | 6.20 | 4.86 | 9.64 | 3.69 | 15.44 | 8.69 |
| transcribed | 1670 | 35 | 6.97 | 5.61 | 10.57 | 4.05 | 16.87 | 9.33 |
| transcribed | 1680 | 78 | 6.74 | 5.44 | 10.45 | 3.87 | 17.14 | 9.24 |
| transcribed | 1690 | 51 | 6.04 | 4.84 | 9.81 | 3.40 | 15.85 | 8.29 |
| transcribed | 1700 | 16 | 6.07 | 4.73 | 8.54 | 3.18 | 14.45 | 8.00 |
| transcribed | 1710 | 15 | 5.75 | 4.54 | 8.74 | 3.20 | 14.29 | 7.51 |
| transcribed | 1720 | 53 | 6.96 | 5.32 | 10.79 | 4.15 | 17.08 | 9.32 |
| transcribed | 1730 | 22 | 6.39 | 4.76 | 9.98 | 4.04 | 15.63 | 8.69 |
| transcribed | 1740 | 25 | 6.89 | 5.32 | 10.56 | 4.33 | 17.42 | 9.51 |
| transcribed | 1750 | 53 | 7.22 | 5.68 | 11.25 | 4.56 | 18.39 | 10.33 |
| transcribed | 1760 | 61 | 7.10 | 5.44 | 10.09 | 3.99 | 16.74 | 9.60 |
| transcribed | 1770 | 56 | 7.23 | 5.61 | 10.63 | 4.57 | 17.67 | 10.12 |
| transcribed | 1780 | 69 | 7.45 | 5.76 | 11.43 | 5.12 | 18.81 | 10.80 |
| transcribed | 1790 | 182 | 7.14 | 5.51 | 10.49 | 4.56 | 17.59 | 10.13 |
| transcribed | 1800 | 88 | 6.97 | 5.37 | 9.98 | 4.33 | 16.84 | 9.69 |
| transcribed | 1810 | 108 | 7.36 | 5.73 | 10.31 | 4.34 | 17.45 | 10.17 |
| transcribed | 1820 | 170 | 6.70 | 5.15 | 9.24 | 3.56 | 15.86 | 8.69 |
| transcribed | 1830 | 240 | 6.52 | 4.92 | 8.72 | 3.31 | 15.14 | 8.09 |
| transcribed | 1840 | 320 | 6.45 | 5.00 | 8.56 | 2.99 | 14.94 | 7.94 |
| transcribed | 1850 | 295 | 6.67 | 5.17 | 9.22 | 3.19 | 15.93 | 8.44 |
| transcribed | 1860 | 263 | 6.74 | 5.19 | 9.15 | 2.95 | 15.91 | 8.28 |
| transcribed | 1870 | 236 | 6.91 | 5.39 | 9.36 | 2.90 | 16.24 | 8.40 |
| transcribed | 1880 | 243 | 7.18 | 5.60 | 9.78 | 3.12 | 16.69 | 8.69 |
| transcribed | 1890 | 194 | 7.11 | 5.53 | 9.32 | 2.90 | 16.54 | 8.45 |
| transcribed | 1900 | 19 | 6.97 | 5.41 | 9.17 | 2.81 | 16.09 | 8.13 |
| transcribed | 1910 | 8 | 6.90 | 5.21 | 7.91 | 2.46 | 15.00 | 7.79 |
| transcribed | 1920 | 12 | 6.18 | 4.98 | 7.75 | 1.62 | 14.20 | 6.49 |
| transcribed | 1930 | 12 | 5.29 | 3.90 | 6.70 | 1.72 | 12.19 | 5.81 |
| transcribed | 1940 | 5 | 6.64 | 5.12 | 7.76 | 1.86 | 15.21 | 6.98 |
| transcribed | 1950 | 14 | 7.13 | 5.60 | 8.15 | 1.65 | 15.11 | 7.33 |
| transcribed | 1960 | 19 | 6.19 | 4.99 | 7.88 | 1.78 | 13.87 | 6.62 |
| transcribed | 1970 | 14 | 6.45 | 5.25 | 7.57 | 1.92 | 14.17 | 6.81 |
| transcribed | 1980 | 21 | 6.44 | 5.13 | 7.27 | 1.56 | 14.03 | 6.79 |
| transcribed | 1990 | 15 | 5.77 | 4.65 | 7.44 | 1.65 | 13.10 | 6.21 |
| transcribed | 2000 | 8 | 6.75 | 5.37 | 7.28 | 1.65 | 14.02 | 7.17 |

## Token mass after: share of each list's tokens carried by its most frequent forms (all texts)

- Clean X, precision: top 10 35%, top 25 50% of 3031 forms with any tokens. Top 25: know 6.7%, see 6.2%, think 4.7%, thought 4.3%, knew 2.8%, heard 2.5%, felt 2.3%, want 2.3%, seen 2.0%, hear 1.5%, believe 1.5%, hope 1.4%, feel 1.4%, wish 1.2%, wanted 1.1%, known 1.0%, understand 1.0%, suppose 1.0%, remember 1.0%, reason 0.9%, idea 0.8%, thinking 0.8%, try 0.8%, interest 0.7%, wonder 0.7%
- Candidates, precision: top 10 13%, top 25 24% of 3976 forms with any tokens. Top 25: doubt 1.7%, glad 1.6%, afraid 1.4%, thoughts 1.4%, pleasure 1.3%, sorry 1.1%, meant 1.1%, happiness 1.0%, joy 1.0%, pleased 0.9%, observed 0.9%, anxious 0.8%, judge 0.8%, fancy 0.8%, faith 0.8%, liked 0.8%, angry 0.8%, proud 0.8%, pride 0.7%, pity 0.7%, supposed 0.7%, carefully 0.7%, respect 0.7%, courage 0.6%, wants 0.6%
