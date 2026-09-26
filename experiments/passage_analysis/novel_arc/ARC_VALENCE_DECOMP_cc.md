# Decomposing valence: fewer negative words, more positive words, or intensity? (EXPLORATORY)

Producer `arc_valence_decomp.py` (method and identity in its docstring). Components sum exactly to the observed change (asserted). Percentages are shares of the observed change and can exceed 100 or go negative.

## History: arc_fiction, Chadwyck and Chicago only, 1750-1799 -> 1850-1899 (pooled word counts)

### human lookup

1750-99: p 0.413 q 0.176 r 0.411 D+ 1.863 D- 1.960 mean 5.5358; 1850-99: p 0.405 q 0.150 r 0.445 D+ 1.804 D- 1.957 mean 5.5548

Change +0.0190 = more positive words -0.0143 (-75%), fewer negative words +0.0513 (270%), positive words stronger -0.0242 (-127%), negative words weaker +0.0004 (2%), neutral band +0.0059 (31%)

- raising valence (x1e4): face +59.2, eyes +45.2, suffer +30.9, unhappy +29.7, beautiful +28.5, rose +24.9, white +24.1, smile +20.9, head +18.7, water +17.8, fact +16.9, feeling +16.8, fear +16.2, bright +16.0, distress +15.7
- lowering valence (x1e4): happiness -66.0, pleasure -57.1, heart -55.8, fortune -48.8, happy -43.1, affection -41.6, passion -38.2, hope -38.1, gentleman -32.7, friendship -31.7, dead -29.4, pleased -27.6, virtue -22.9, conversation -22.9, joy -22.2

### plain vector

1750-99: p 0.404 q 0.205 r 0.391 D+ 1.162 D- 1.482 mean 0.0673; 1850-99: p 0.396 q 0.176 r 0.428 D+ 1.158 D- 1.377 mean 0.1210

Change +0.0537 = more positive words -0.0087 (-16%), fewer negative words +0.0418 (78%), positive words stronger -0.0014 (-3%), negative words weaker +0.0200 (37%), neutral band +0.0020 (4%)

- raising valence (x1e4): beautiful +18.0, white +15.0, suffer +13.4, bright +11.4, unhappy +10.6, resentment +9.5, rose +9.5, suffered +8.7, distress +8.4, fear +8.3, violence +8.3, pleasant +8.0, violent +7.8, cruel +7.8, confusion +7.5
- lowering valence (x1e4): pleasure -16.9, happiness -15.4, happy -13.6, received -13.0, company -12.5, fortune -11.5, conversation -11.4, ladies -11.3, favour -11.2, desired -10.8, pleased -10.6, friendship -10.5, agreeable -10.4, hope -9.9, character -9.1

