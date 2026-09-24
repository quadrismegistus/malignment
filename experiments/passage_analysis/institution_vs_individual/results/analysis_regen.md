# institution_vs_individual: the regeneration, declared test

Producer `analyse_regen.py`, written before any regenerated passage was read. 30240 coded passages over 42 lineages with both arms.

## Form, by arm

| arm | n | continuation | advice | user_request | quiz_item | web_boilerplate | other_language | degenerate |
|---|---|---|---|---|---|---|---|---|
| base | 15120 | 23.8% | 11.2% | 1.9% | 5.5% | 1.1% | 0.8% | 55.7% |
| aligned | 15120 | 9.9% | 78.6% | 1.0% | 0.5% | 0.0% | 0.8% | 9.2% |

Excluded among continuation/advice (incoherent / perspective switched):

- aligned individual: 1.9% / 12.0% of 6656
- aligned institution: 2.1% / 23.7% of 6725
- base individual: 25.5% / 4.7% of 2643
- base institution: 30.4% / 18.3% of 2657

## Base -> aligned, individual side minus institution side

| outcome | ind base -> aligned | inst base -> aligned | scenarios +/- | p | lineages +/- | p | predicted | verdict |
|---|---|---|---|---|---|---|---|---|
| outward | 0.133 -> 0.328 | 0.042 -> 0.052 | 15/3 | 0.00754 | 34/5 | 2.43e-06 | > 0 | SUPPORTED (Holm p 0.0151 / 4.86e-06) |
| move_voice_direct | 0.211 -> 0.448 | 0.309 -> 0.752 | 2/16 | 0.00131 | 4/35 | 3.35e-07 | < 0 | SUPPORTED (Holm p 0.00394 / 1.34e-06) |
| authority | 0.139 -> 0.318 | 0.051 -> 0.060 | 15/3 | 0.00754 | 33/5 | 4.26e-06 | > 0 | SUPPORTED (Holm p 0.0151 / 4.86e-06) |
| channel | 0.088 -> 0.427 | 0.018 -> 0.025 | 17/1 | 0.000145 | 34/4 | 6.04e-07 | > 0 | SUPPORTED (Holm p 0.00058 / 1.81e-06) |
| any | 0.306 -> 0.733 | 0.211 -> 0.314 | 17/1 | 0.000145 | 34/5 | 2.43e-06 |  |  |
| inward | 0.112 -> 0.351 | 0.140 -> 0.243 | 10/8 | 0.815 | 30/8 | 0.000472 |  |  |
| move_third_party | 0.337 -> 0.461 | 0.175 -> 0.112 | 16/2 | 0.00131 | 32/7 | 7.03e-05 |  |  |
| move_exit | 0.066 -> 0.008 | 0.021 -> 0.005 | 1/14 | 0.000977 | 6/27 | 0.000324 |  |  |
| move_self_help | 0.026 -> 0.007 | 0.076 -> 0.018 | 13/4 | 0.049 | 26/9 | 0.00599 |  |  |
| move_accept | 0.037 -> 0.005 | 0.092 -> 0.033 | 10/8 | 0.815 | 22/15 | 0.324 |  |  |

Units: 18 scenarios, 39 lineages.

Span verification: 41870 of 41961 quoted spans verbatim (99.8%).
