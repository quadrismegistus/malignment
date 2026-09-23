# institution_vs_individual: the declared contrast

Producer `analyse.py`, written before any coded row was read. 20387 coded rows.

## Form, by arm

| arm | n | continuation | advice | quiz_item | web_boilerplate | other_language | degenerate |
|---|---|---|---|---|---|---|---|
| base | 6000 | 55.9% | 11.6% | 9.4% | 1.2% | 1.9% | 20.1% |
| aligned | 5995 | 49.1% | 29.4% | 13.6% | 0.6% | 1.5% | 5.8% |
| frontier | 2400 | 2.3% | 97.5% | 0.1% | 0.0% | 0.1% | 0.0% |

Quiz share, aligned minus base, by family: 8 up / 1 down, p=0.0391.

## Base -> aligned, individual side minus institution side

Continuation and advice only; referrals counted only if recommended or marked correct. `diff` = (aligned - base on the individual side) - (aligned - base on the institution side). Cells missing a side or an arm after the form filter are dropped from that unit.

| outcome | base ind | base inst | aligned ind | aligned inst | pairs +/- | p | families +/- | p | predicted |
|---|---|---|---|---|---|---|---|---|---|
| any | 0.107 | 0.082 | 0.206 | 0.113 | 10/2 | 0.0386 | 8/2 | 0.109 |  |
| outward | 0.060 | 0.023 | 0.111 | 0.027 | 9/3 | 0.146 | 9/1 | 0.0215 | > 0 |
| inward | 0.024 | 0.046 | 0.055 | 0.071 | 8/4 | 0.388 | 6/4 | 0.754 | < 0 |
| channel | 0.013 | 0.008 | 0.054 | 0.015 | 9/2 | 0.0654 | 8/2 | 0.109 |  |
| authority | 0.051 | 0.031 | 0.094 | 0.035 | 9/3 | 0.146 | 8/2 | 0.109 |  |
| move_exit | 0.073 | 0.030 | 0.045 | 0.014 | 3/6 | 0.508 | 5/5 | 1 |  |
| move_voice_direct | 0.246 | 0.157 | 0.301 | 0.319 | 0/12 | 0.000488 | 1/9 | 0.0215 |  |
| move_third_party | 0.134 | 0.102 | 0.193 | 0.107 | 9/3 | 0.146 | 8/2 | 0.109 |  |
| move_self_help | 0.022 | 0.051 | 0.017 | 0.034 | 7/5 | 0.774 | 6/4 | 0.754 |  |
| move_accept | 0.037 | 0.043 | 0.044 | 0.035 | 7/5 | 0.774 | 9/1 | 0.0215 |  |
| perspective_flip | 0.091 | 0.238 | 0.092 | 0.213 | 8/4 | 0.388 | 5/5 | 1 |  |

## POST-HOC robustness: the 6 pairs ending "I should" on both sides

Continuation and advice only; referrals counted only if recommended or marked correct. `diff` = (aligned - base on the individual side) - (aligned - base on the institution side). Cells missing a side or an arm after the form filter are dropped from that unit.

| outcome | base ind | base inst | aligned ind | aligned inst | pairs +/- | p | families +/- | p | predicted |
|---|---|---|---|---|---|---|---|---|---|
| any | 0.099 | 0.097 | 0.209 | 0.143 | 4/2 | 0.688 | 5/5 | 1 |  |
| outward | 0.047 | 0.022 | 0.091 | 0.026 | 3/3 | 1 | 6/4 | 0.754 | > 0 |
| inward | 0.029 | 0.059 | 0.081 | 0.096 | 5/1 | 0.219 | 7/3 | 0.344 | < 0 |
| channel | 0.014 | 0.012 | 0.051 | 0.025 | 4/2 | 0.688 | 6/4 | 0.754 |  |
| authority | 0.047 | 0.037 | 0.090 | 0.044 | 4/2 | 0.688 | 7/3 | 0.344 |  |
| move_exit | 0.094 | 0.044 | 0.058 | 0.020 | 1/4 | 0.375 | 4/6 | 0.754 |  |
| move_voice_direct | 0.110 | 0.140 | 0.192 | 0.335 | 0/6 | 0.0312 | 2/8 | 0.109 |  |
| move_third_party | 0.164 | 0.147 | 0.235 | 0.152 | 5/1 | 0.219 | 8/2 | 0.109 |  |
| move_self_help | 0.028 | 0.042 | 0.025 | 0.019 | 3/3 | 1 | 7/3 | 0.344 |  |
| move_accept | 0.037 | 0.058 | 0.057 | 0.039 | 5/1 | 0.219 | 8/2 | 0.109 |  |
| perspective_flip | 0.087 | 0.293 | 0.078 | 0.271 | 4/2 | 0.688 | 5/5 | 1 |  |

## Frontier chat models: individual minus institution (no base arm)

| outcome | claude-haiku-4-5-raw | claude-sonnet-4-6-raw | deepseek-chat-raw | gpt-4o-mini-raw | pairs +/- (pooled over models) | p |
|---|---|---|---|---|---|---|
| any | 0.53 / 0.19 | 0.58 / 0.17 | 0.20 / 0.21 | 0.34 / 0.06 | 5/1 | 0.219 |
| outward | 0.30 / 0.03 | 0.44 / 0.01 | 0.07 / 0.01 | 0.15 / 0.01 | 5/0 | 0.0625 |
| inward | 0.25 / 0.15 | 0.20 / 0.13 | 0.10 / 0.16 | 0.08 / 0.04 | 2/3 | 1 |
| channel | 0.25 / 0.02 | 0.12 / 0.01 | 0.07 / 0.04 | 0.13 / 0.01 | 5/1 | 0.219 |
| authority | 0.25 / 0.03 | 0.29 / 0.00 | 0.07 / 0.01 | 0.04 / 0.00 | 5/1 | 0.219 |
| move_exit | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 | 0/0 | 1 |
| move_voice_direct | 0.38 / 0.37 | 0.41 / 0.38 | 0.25 / 0.34 | 0.56 / 0.58 | 3/3 | 1 |
| move_third_party | 0.46 / 0.15 | 0.46 / 0.11 | 0.19 / 0.14 | 0.18 / 0.04 | 4/1 | 0.375 |
| move_self_help | 0.01 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 | 2/0 | 0.5 |
| move_accept | 0.00 / 0.08 | 0.00 / 0.06 | 0.00 / 0.03 | 0.00 / 0.04 | 0/2 | 0.5 |
| perspective_flip | 0.04 / 0.18 | 0.00 / 0.13 | 0.11 / 0.19 | 0.09 / 0.14 | 1/3 | 0.625 |

Cells read individual / institution.

Span verification: 20627 of 21113 quoted spans found verbatim in their text (97.7%).
