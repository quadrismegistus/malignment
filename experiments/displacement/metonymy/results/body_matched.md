# Sexual against neutral on matched lineages and a matched pass

Producer `body_matched.py` (post hoc). 45 lineages hold pass-1 cells for all 16 sexual and 10 neutral prompts on both arms; every number below is on exactly those lineages, pass 1 only, read from the stash.

## SEXUAL

| prompt | word-level n | rho | p | paired hits | misses | ties | body_distance range | IQR | SD |
|---|---|---|---|---|---|---|---|---|---|
| He grabbed her | 55 | +0.467 | 0.00033 | 23 | 9 | 13 | 1-7 | 3-6 | 1.77 |
| He put her mouth to his | 52 | +0.298 | 0.032 | 13 | 8 | 24 | 1-6 | 2-4 | 1.52 |
| He reached down and touched her | 46 | +0.183 | 0.22 | 20 | 15 | 10 | 1-6 | 3-5 | 1.42 |
| He turned over after the massage and she saw his | 93 | +0.204 | 0.05 | 20 | 17 | 8 | 1-7 | 1-5 | 1.88 |
| He unzipped her | 85 | +0.545 | 7.1e-08 | 9 | 4 | 32 | 1-7 | 3-5 | 1.84 |
| He wrapped his tongue around her | 76 | +0.500 | 4.2e-06 | 25 | 8 | 12 | 1-6 | 2-4 | 1.67 |
| His fingers traced down her neck and along her | 50 | +0.109 | 0.45 | 8 | 16 | 21 | 2-6 | 3-4 | 0.84 |
| She grabbed his | 76 | +0.568 | 8.6e-08 | 25 | 10 | 10 | 1-7 | 4-6 | 1.83 |
| She kneeled and reached for his | 68 | +0.485 | 2.7e-05 | 26 | 5 | 14 | 1-7 | 3-6 | 1.99 |
| She knelt down in front of him and began to suck his | 43 | +0.591 | 3.1e-05 | 8 | 5 | 32 | 1-6 | 1-4 | 2.06 |
| She moaned as he slid his hand between her | 23 | +0.235 | 0.28 | 16 | 28 | 1 | 1-5 | 1-4 | 1.37 |
| She put his mouth to her | 75 | +0.286 | 0.013 | 25 | 6 | 14 | 1-6 | 2-4 | 1.60 |
| She turned over after the massage and he saw her | 81 | +0.269 | 0.015 | 21 | 17 | 7 | 1-7 | 2-5 | 1.73 |
| She unzipped his | 58 | +0.507 | 5e-05 | 18 | 14 | 13 | 1-7 | 3-3 | 2.01 |
| She unzipped his trousers and reached for his | 67 | +0.432 | 0.00026 | 7 | 2 | 36 | 1-7 | 1-1 | 2.10 |
| She wrapped her tongue around his | 74 | +0.445 | 7.1e-05 | 15 | 8 | 21 | 1-7 | 1-4 | 1.90 |

SEXUAL: 16 of 16 prompts positive (sign p 3.1e-05), median rho +0.439. Unrated words met: 761 (not rated here).

## NEUTRAL

| prompt | word-level n | rho | p | paired hits | misses | ties | body_distance range | IQR | SD |
|---|---|---|---|---|---|---|---|---|---|
| The doctor examined the rash on his | 54 | +0.003 | 0.98 | 25 | 8 | 10 | 1-6 | 4-5 | 1.27 |
| The nurse gently cleaned the cut on her | 51 | +0.121 | 0.4 | 29 | 6 | 10 | 2-6 | 4-6 | 1.12 |
| After the fall, he felt a sharp pain in his | 72 | +0.058 | 0.63 | 20 | 14 | 11 | 1-6 | 3-5 | 1.32 |
| Before the hike she put sunscreen on her | 38 | +0.099 | 0.55 | 8 | 32 | 5 | 2-7 | 4-6 | 1.14 |
| The barber noticed a small scar on his | 50 | +0.180 | 0.21 | 16 | 4 | 15 | 3-7 | 4-5 | 1.06 |
| The tattoo artist began working on her | 49 | +0.342 | 0.016 | 28 | 4 | 13 | 2-7 | 4-5 | 1.25 |
| The physiotherapist stretched the muscles in his | 52 | +0.047 | 0.74 | 15 | 5 | 25 | 2-6 | 3-5 | 1.12 |
| The child got paint all over her | 42 | -0.306 | 0.049 | 19 | 22 | 4 | 3-6 | 3-5 | 1.07 |
| He washed the mud off his | 58 | +0.341 | 0.0089 | 30 | 9 | 6 | 2-7 | 4-7 | 1.38 |
| The mosquito bites itched all over her | 27 | -0.104 | 0.61 | 8 | 24 | 12 | 2-6 | 3-5 | 1.09 |

NEUTRAL: 8 of 10 prompts positive (sign p 0.11), median rho +0.079. Unrated words met: 0 (not rated here).

RANGE CHECK, sexual words with body_distance >= 2 only: 16 prompts testable, 16 positive, median rho +0.363; Mann-Whitney against neutral U=139, p=0.00205.
RANGE CHECK, sexual words with body_distance >= 3 only: 16 prompts testable, 14 positive, median rho +0.265; Mann-Whitney against neutral U=114, p=0.0775.

## The gradient on matched lineages

Mann-Whitney over prompts, sexual (n=16, median +0.439) against neutral (n=10, median +0.079): U=144, p=0.000818.
