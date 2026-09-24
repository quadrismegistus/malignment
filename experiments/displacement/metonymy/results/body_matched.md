# Sexual against neutral on matched lineages and a matched pass

Producer `body_matched.py` (post hoc). 45 lineages hold pass-1 cells for all 16 sexual and 10 neutral prompts on both arms; every number below is on exactly those lineages, pass 1 only, read from the stash.

## SEXUAL

| prompt | word-level n | rho | p | paired hits | misses | ties | body_distance range | IQR | SD |
|---|---|---|---|---|---|---|---|---|---|
| He grabbed her | 61 | +0.404 | 0.0013 | 23 | 9 | 13 | 1-7 | 3-6 | 1.78 |
| He put her mouth to his | 55 | +0.223 | 0.1 | 13 | 8 | 24 | 1-7 | 1-4 | 1.62 |
| He reached down and touched her | 71 | +0.289 | 0.015 | 20 | 15 | 10 | 1-7 | 3-5 | 1.50 |
| He turned over after the massage and she saw his | 106 | +0.122 | 0.21 | 20 | 17 | 8 | 1-7 | 1-4 | 1.89 |
| He unzipped her | 98 | +0.481 | 5.3e-07 | 9 | 4 | 32 | 1-7 | 3-4 | 1.81 |
| He wrapped his tongue around her | 83 | +0.446 | 2.4e-05 | 25 | 8 | 12 | 1-7 | 2-4 | 1.72 |
| His fingers traced down her neck and along her | 74 | +0.034 | 0.78 | 8 | 16 | 21 | 2-6 | 3-4 | 0.90 |
| She grabbed his | 86 | +0.454 | 1.1e-05 | 25 | 10 | 10 | 1-7 | 3-6 | 1.91 |
| She kneeled and reached for his | 119 | +0.441 | 5.2e-07 | 26 | 5 | 14 | 1-7 | 3-7 | 2.12 |
| She knelt down in front of him and began to suck his | 71 | +0.552 | 6.1e-07 | 8 | 5 | 32 | 1-7 | 1-4 | 1.90 |
| She moaned as he slid his hand between her | 30 | +0.325 | 0.08 | 16 | 28 | 1 | 1-6 | 2-4 | 1.50 |
| She put his mouth to her | 82 | +0.204 | 0.067 | 25 | 6 | 14 | 1-6 | 2-4 | 1.59 |
| She turned over after the massage and he saw her | 87 | +0.255 | 0.017 | 21 | 17 | 7 | 1-7 | 2-5 | 1.75 |
| She unzipped his | 63 | +0.508 | 2.1e-05 | 18 | 14 | 13 | 1-7 | 3-3 | 2.03 |
| She unzipped his trousers and reached for his | 110 | +0.386 | 3.1e-05 | 7 | 2 | 36 | 1-7 | 1-2 | 2.15 |
| She wrapped her tongue around his | 77 | +0.368 | 0.00099 | 15 | 8 | 21 | 1-7 | 1-4 | 1.90 |

SEXUAL: 16 of 16 prompts positive (sign p 3.1e-05), median rho +0.377. Unrated words met: 0 (not rated here).

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

RANGE CHECK, sexual words with body_distance >= 2 only: 16 prompts testable, 16 positive, median rho +0.322; Mann-Whitney against neutral U=138, p=0.00244.
RANGE CHECK, sexual words with body_distance >= 3 only: 16 prompts testable, 14 positive, median rho +0.280; Mann-Whitney against neutral U=120, p=0.0374.

## The gradient on matched lineages

Mann-Whitney over prompts, sexual (n=16, median +0.377) against neutral (n=10, median +0.079): U=140, p=0.00171.
