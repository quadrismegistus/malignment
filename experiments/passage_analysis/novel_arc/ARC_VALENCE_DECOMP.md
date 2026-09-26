# Decomposing valence: fewer negative words, more positive words, or intensity? (EXPLORATORY)

Producer `arc_valence_decomp.py` (method and identity in its docstring). Components sum exactly to the observed change (asserted). Percentages are shares of the observed change and can exceed 100 or go negative.

## National stories: base -> aligned

### human lookup (neutral 5.000, band +-1.000)

Pooled over models, bin shares and distances: base p 0.449 q 0.121 r 0.430 D+ 1.809 D- 2.057; aligned_raw p 0.536 q 0.077 r 0.387 D+ 1.850 D- 1.937; aligned_prefill p 0.546 q 0.068 r 0.387 D+ 1.837 D- 1.888; aligned_rettberg p 0.527 q 0.080 r 0.393 D+ 1.812 D- 1.926

| base -> | observed rise (pooled) | more positive words | fewer negative words | positive words stronger | negative words weaker | neutral band |
|---|---|---|---|---|---|---|
| aligned, raw | +0.2812 | +0.1600 (57%) | +0.0879 (31%) | +0.0203 (7%) | +0.0119 (4%) | +0.0012 (0%) |
| aligned, chat, prefilled | +0.3164 | +0.1758 (56%) | +0.1050 (33%) | +0.0138 (4%) | +0.0159 (5%) | +0.0059 (2%) |
| aligned, chat, asked | +0.2421 | +0.1417 (59%) | +0.0823 (34%) | +0.0016 (1%) | +0.0132 (5%) | +0.0032 (1%) |

Per lineage, how many lineages have each component POSITIVE (i.e. pushing valence up; sign test p):

| base -> | lineages | observed rise | more positive words | fewer negative words | positive words stronger | negative words weaker | neutral band |
|---|---|---|---|---|---|---|---|
| aligned, raw | 32 | 28 up (p 0.000) | 28 up (p 0.000) | 28 up (p 0.000) | 24 up (p 0.007) | 23 up (p 0.020) | 17 up (p 0.860) |
| aligned, chat, prefilled | 23 | 22 up (p 0.000) | 22 up (p 0.000) | 20 up (p 0.000) | 15 up (p 0.210) | 19 up (p 0.003) | 15 up (p 0.210) |
| aligned, chat, asked | 20 | 16 up (p 0.012) | 16 up (p 0.012) | 18 up (p 0.000) | 11 up (p 0.824) | 16 up (p 0.012) | 11 up (p 0.824) |

Words driving base -> aligned raw (contribution to the change in mean valence, x1e4):

- raising valence: story +214.8, dead +89.3, heart +83.9, sense +82.9, hope +65.9, journey +64.6, beauty +54.7, adventure +53.7, lily +51.7, forest +49.5, grateful +47.5, warm +44.9, excitement +44.5, war +43.3, feeling +43.2
- lowering valence: house -109.3, water -58.7, money -52.2, white -39.3, dad -36.3, food -34.2, remember -31.5, bed -30.8, eat -27.5, head -27.4, car -26.1, grandma -25.9, island -22.9, milk -21.6, silver -20.8

### plain vector (neutral -0.142, band +-0.606)

Pooled over models, bin shares and distances: base p 0.411 q 0.147 r 0.442 D+ 1.129 D- 1.299; aligned_raw p 0.484 q 0.107 r 0.409 D+ 1.160 D- 1.251; aligned_prefill p 0.496 q 0.098 r 0.406 D+ 1.165 D- 1.227; aligned_rettberg p 0.473 q 0.117 r 0.410 D+ 1.163 D- 1.262

| base -> | observed rise (pooled) | more positive words | fewer negative words | positive words stronger | negative words weaker | neutral band |
|---|---|---|---|---|---|---|
| aligned, raw | +0.1509 | +0.0834 (55%) | +0.0515 (34%) | +0.0141 (9%) | +0.0062 (4%) | -0.0042 (-3%) |
| aligned, chat, prefilled | +0.1809 | +0.0969 (54%) | +0.0616 (34%) | +0.0164 (9%) | +0.0088 (5%) | -0.0028 (-2%) |
| aligned, chat, asked | +0.1214 | +0.0709 (58%) | +0.0383 (32%) | +0.0149 (12%) | +0.0049 (4%) | -0.0077 (-6%) |

Per lineage, how many lineages have each component POSITIVE (i.e. pushing valence up; sign test p):

| base -> | lineages | observed rise | more positive words | fewer negative words | positive words stronger | negative words weaker | neutral band |
|---|---|---|---|---|---|---|---|
| aligned, raw | 32 | 28 up (p 0.000) | 28 up (p 0.000) | 28 up (p 0.000) | 24 up (p 0.007) | 24 up (p 0.007) | 13 up (p 0.377) |
| aligned, chat, prefilled | 23 | 19 up (p 0.003) | 19 up (p 0.003) | 18 up (p 0.011) | 18 up (p 0.011) | 15 up (p 0.210) | 10 up (p 0.678) |
| aligned, chat, asked | 20 | 17 up (p 0.003) | 19 up (p 0.000) | 17 up (p 0.003) | 15 up (p 0.041) | 13 up (p 0.263) | 8 up (p 0.503) |

Words driving base -> aligned raw (contribution to the change in mean valence, x1e4):

- raising valence: story +41.9, beauty +30.1, journey +28.9, sense +26.9, grateful +24.7, lily +24.4, filled +20.6, warm +18.7, village +17.4, hope +16.9, library +16.4, dead +16.1, forest +16.0, kill +15.2, stories +15.1
- lowering valence: white -26.0, house -23.7, green -15.6, looked -14.2, water -13.4, asked -11.9, picture -11.8, mirror -11.7, red -11.1, coming -11.0, remember -10.3, table -10.2, silver -10.2, box -10.1, milk -9.6

## History: arc_fiction 1750-1799 -> 1850-1899 (pooled word counts)

### human lookup

1750-99: p 0.419 q 0.174 r 0.407 D+ 1.875 D- 1.963 mean 5.5542; 1850-99: p 0.411 q 0.153 r 0.435 D+ 1.818 D- 1.970 mean 5.5613

Change +0.0071 = more positive words -0.0133 (-187%), fewer negative words +0.0412 (578%), positive words stronger -0.0237 (-333%), negative words weaker -0.0011 (-15%), neutral band +0.0041 (58%)

- raising valence (x1e4): face +60.1, eyes +40.4, unhappy +31.3, smile +24.6, beautiful +24.0, rose +23.3, night +21.7, white +21.0, voice +20.4, glad +19.6, pretty +19.0, light +18.6, water +18.5, head +17.7, bright +17.6
- lowering valence (x1e4): happiness -71.7, heart -52.7, pleasure -51.1, fortune -48.6, happy -47.3, friendship -36.9, passion -36.3, affection -35.9, virtue -28.8, lie -27.4, heaven -27.2, dead -26.8, joy -25.1, nature -24.7, hope -23.3

### plain vector

1750-99: p 0.410 q 0.196 r 0.394 D+ 1.173 D- 1.469 mean 0.0947; 1850-99: p 0.396 q 0.172 r 0.432 D+ 1.162 D- 1.379 mean 0.1306

Change +0.0359 = more positive words -0.0154 (-43%), fewer negative words +0.0344 (96%), positive words stronger -0.0043 (-12%), negative words weaker +0.0166 (46%), neutral band +0.0047 (13%)

- raising valence (x1e4): beautiful +14.3, white +12.5, bright +11.9, unhappy +10.8, pleasant +9.1, violent +9.1, rose +8.5, light +8.4, cruel +8.0, asked +7.7, round +7.4, distress +7.2, wretch +7.0, fatal +6.7, table +6.4
- lowering valence (x1e4): happiness -16.2, pleasure -14.7, happy -14.6, amiable -13.5, received -12.9, agreeable -12.1, friendship -11.8, company -11.5, fortune -11.1, virtue -9.9, situation -9.5, attention -9.2, letter -9.2, worthy -8.1, joy -8.1

