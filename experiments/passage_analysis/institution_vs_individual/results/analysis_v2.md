# institution_vs_individual: the declared contrast (v2 codes, form + coherent + perspective_kept)

Producer `analyse.py`, written before any coded row was read. 20388 coded rows.

## Form, by arm

| arm | n | continuation | advice | user_request | quiz_item | web_boilerplate | other_language | degenerate |
|---|---|---|---|---|---|---|---|---|
| base | 6000 | 52.1% | 9.5% | 1.7% | 9.4% | 1.0% | 1.2% | 25.0% |
| aligned | 5995 | 45.6% | 25.3% | 5.0% | 13.9% | 0.6% | 1.2% | 8.5% |
| frontier | 2400 | 3.1% | 95.1% | 1.3% | 0.0% | 0.0% | 0.3% | 0.2% |

Quiz share, aligned minus base, by family: 9 up / 1 down, p=0.0215.

Among continuation/advice texts: share incoherent / share perspective-flipped (EXCLUDED under v2):

- aligned individual: 2.1% / 7.2% of 2207
- aligned institution: 1.8% / 17.4% of 2045
- base individual: 6.1% / 4.8% of 1879
- base institution: 7.0% / 16.9% of 1820
- frontier individual: 0.0% / 10.3% of 1197
- frontier institution: 0.0% / 18.8% of 1160

## Base -> aligned, individual side minus institution side

Continuation and advice only; referrals counted only if recommended or marked correct. `diff` = (aligned - base on the individual side) - (aligned - base on the institution side). Cells missing a side or an arm after the form filter are dropped from that unit.

| outcome | base ind | base inst | aligned ind | aligned inst | pairs +/- | p | families +/- | p | predicted |
|---|---|---|---|---|---|---|---|---|---|
| any | 0.114 | 0.079 | 0.211 | 0.097 | 9/3 | 0.146 | 8/2 | 0.109 |  |
| outward | 0.069 | 0.027 | 0.121 | 0.019 | 9/3 | 0.146 | 9/1 | 0.0215 | > 0 |
| inward | 0.024 | 0.041 | 0.058 | 0.070 | 7/5 | 0.774 | 4/6 | 0.754 | < 0 |
| channel | 0.013 | 0.007 | 0.046 | 0.005 | 11/0 | 0.000977 | 7/3 | 0.344 |  |
| authority | 0.057 | 0.035 | 0.104 | 0.026 | 10/2 | 0.0386 | 9/1 | 0.0215 |  |
| move_exit | 0.084 | 0.032 | 0.048 | 0.014 | 3/8 | 0.227 | 5/5 | 1 |  |
| move_voice_direct | 0.280 | 0.201 | 0.315 | 0.358 | 0/12 | 0.000488 | 1/9 | 0.0215 |  |
| move_third_party | 0.163 | 0.102 | 0.208 | 0.085 | 10/2 | 0.0386 | 7/3 | 0.344 |  |
| move_self_help | 0.032 | 0.084 | 0.028 | 0.058 | 7/5 | 0.774 | 7/3 | 0.344 |  |
| move_accept | 0.041 | 0.066 | 0.043 | 0.053 | 6/6 | 1 | 7/3 | 0.344 |  |

## POST-HOC robustness: the 6 pairs ending "I should" on both sides

Continuation and advice only; referrals counted only if recommended or marked correct. `diff` = (aligned - base on the individual side) - (aligned - base on the institution side). Cells missing a side or an arm after the form filter are dropped from that unit.

| outcome | base ind | base inst | aligned ind | aligned inst | pairs +/- | p | families +/- | p | predicted |
|---|---|---|---|---|---|---|---|---|---|
| any | 0.095 | 0.092 | 0.219 | 0.116 | 5/1 | 0.219 | 6/4 | 0.754 |  |
| outward | 0.050 | 0.030 | 0.106 | 0.017 | 4/2 | 0.688 | 8/2 | 0.109 | > 0 |
| inward | 0.028 | 0.053 | 0.085 | 0.091 | 4/2 | 0.688 | 6/4 | 0.754 | < 0 |
| channel | 0.013 | 0.010 | 0.040 | 0.007 | 6/0 | 0.0312 | 6/3 | 0.508 |  |
| authority | 0.044 | 0.042 | 0.102 | 0.033 | 5/1 | 0.219 | 9/1 | 0.0215 |  |
| move_exit | 0.112 | 0.051 | 0.062 | 0.023 | 1/4 | 0.375 | 4/6 | 0.754 |  |
| move_voice_direct | 0.135 | 0.193 | 0.199 | 0.387 | 0/6 | 0.0312 | 3/7 | 0.344 |  |
| move_third_party | 0.201 | 0.143 | 0.246 | 0.114 | 5/1 | 0.219 | 6/4 | 0.754 |  |
| move_self_help | 0.037 | 0.062 | 0.038 | 0.035 | 4/2 | 0.688 | 6/4 | 0.754 |  |
| move_accept | 0.041 | 0.087 | 0.059 | 0.067 | 4/2 | 0.688 | 7/3 | 0.344 |  |

## Frontier chat models: individual minus institution (no base arm)

| outcome | claude-haiku-4-5-raw | claude-sonnet-4-6-raw | deepseek-chat-raw | gpt-4o-mini-raw | pairs +/- (pooled over models) | p |
|---|---|---|---|---|---|---|
| any | 0.50 / 0.21 | 0.54 / 0.21 | 0.17 / 0.22 | 0.33 / 0.07 | 9/2 | 0.0654 |
| outward | 0.27 / 0.01 | 0.40 / 0.02 | 0.07 / 0.02 | 0.15 / 0.01 | 10/0 | 0.00195 |
| inward | 0.25 / 0.19 | 0.18 / 0.17 | 0.07 / 0.16 | 0.07 / 0.05 | 3/6 | 0.508 |
| channel | 0.21 / 0.01 | 0.10 / 0.01 | 0.07 / 0.03 | 0.12 / 0.01 | 9/1 | 0.0215 |
| authority | 0.23 / 0.01 | 0.24 / 0.00 | 0.06 / 0.01 | 0.05 / 0.01 | 10/0 | 0.00195 |
| move_exit | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 | 0/0 | 1 |
| move_voice_direct | 0.38 / 0.42 | 0.40 / 0.53 | 0.31 / 0.38 | 0.56 / 0.67 | 6/6 | 1 |
| move_third_party | 0.48 / 0.14 | 0.46 / 0.11 | 0.18 / 0.16 | 0.22 / 0.04 | 8/1 | 0.0391 |
| move_self_help | 0.02 / 0.01 | 0.00 / 0.01 | 0.03 / 0.01 | 0.00 / 0.00 | 4/2 | 0.688 |
| move_accept | 0.00 / 0.07 | 0.00 / 0.06 | 0.00 / 0.05 | 0.00 / 0.02 | 0/3 | 0.25 |

Cells read individual / institution.

Span verification: 20054 of 20533 quoted spans found verbatim in their text (97.7%).
