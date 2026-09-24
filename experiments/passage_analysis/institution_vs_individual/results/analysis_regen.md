# institution_vs_individual: the regeneration, declared test

Producer `analyse_regen.py`, written before any regenerated passage was read. 30240 coded passages over 42 lineages with both arms.

## Form, by arm

| arm | n | continuation | advice | user_request | quiz_item | web_boilerplate | other_language | degenerate |
|---|---|---|---|---|---|---|---|---|
| base | 15120 | 23.8% | 11.2% | 1.9% | 5.5% | 1.1% | 0.8% | 55.7% |
| aligned | 15120 | 7.1% | 84.3% | 1.0% | 0.5% | 0.0% | 0.8% | 6.3% |

Excluded among continuation/advice (incoherent / perspective switched):

- aligned individual: 2.7% / 12.7% of 6867
- aligned institution: 2.7% / 24.8% of 6946
- base individual: 25.5% / 4.7% of 2643
- base institution: 30.4% / 18.3% of 2657

## Base -> aligned, individual side minus institution side

| outcome | ind base -> aligned | inst base -> aligned | scenarios +/- | p | lineages +/- | p | predicted | verdict |
|---|---|---|---|---|---|---|---|---|
| outward | 0.133 -> 0.335 | 0.042 -> 0.054 | 14/4 | 0.0309 | 35/5 | 1.38e-06 | > 0 | SUPPORTED (Holm p 0.0309 / 2.77e-06) |
| move_voice_direct | 0.211 -> 0.463 | 0.309 -> 0.783 | 2/16 | 0.00131 | 3/36 | 3.61e-08 | < 0 | SUPPORTED (Holm p 0.00394 / 1.44e-07) |
| authority | 0.138 -> 0.326 | 0.048 -> 0.062 | 15/3 | 0.00754 | 34/5 | 2.43e-06 | > 0 | SUPPORTED (Holm p 0.0151 / 2.77e-06) |
| channel | 0.087 -> 0.450 | 0.018 -> 0.026 | 18/0 | 7.63e-06 | 36/3 | 3.61e-08 | > 0 | SUPPORTED (Holm p 3.05e-05 / 1.44e-07) |
| any | 0.304 -> 0.754 | 0.211 -> 0.327 | 17/1 | 0.000145 | 36/4 | 1.86e-07 |  |  |
| inward | 0.112 -> 0.358 | 0.140 -> 0.254 | 10/8 | 0.815 | 30/9 | 0.00107 |  |  |
| move_third_party | 0.335 -> 0.463 | 0.175 -> 0.115 | 15/3 | 0.00754 | 33/7 | 4.23e-05 |  |  |
| move_exit | 0.066 -> 0.008 | 0.021 -> 0.005 | 1/14 | 0.000977 | 6/27 | 0.000324 |  |  |
| move_self_help | 0.026 -> 0.007 | 0.076 -> 0.019 | 14/4 | 0.0309 | 25/10 | 0.0167 |  |  |
| move_accept | 0.037 -> 0.005 | 0.092 -> 0.034 | 10/8 | 0.815 | 22/15 | 0.324 |  |  |

Units: 18 scenarios, 40 lineages.

Span verification: 43291 of 43391 quoted spans verbatim (99.8%).
