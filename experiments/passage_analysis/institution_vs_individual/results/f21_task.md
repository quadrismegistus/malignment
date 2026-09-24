# F21's annotation task on the regeneration sample and the frontier

Producer `f21_task_sample.py`, committed before coding. 4377 regeneration passages (up to 30 per lineage x arm x side cell), 1366 kept frontier passages. Model deepseek/deepseek-flash.

## Base -> aligned, individual change minus institution change

| field | base ind | base inst | aligned ind | aligned inst | lineages +/- | p | disputes +/- | p | expected |
|---|---|---|---|---|---|---|---|---|---|
| institutional_deference | 2.88 | 3.74 | 3.38 | 4.15 | 25/17 | 0.28 | 12/6 | 0.238 | E1 null |
| agency | 2.46 | 2.67 | 3.57 | 3.40 | 35/7 | 1.51e-05 | 16/2 | 0.00131 |  |
| assertiveness | 2.55 | 2.52 | 2.76 | 2.55 | 31/11 | 0.00289 | 12/6 | 0.238 |  |
| power_acknowledgment | 2.76 | 2.76 | 2.32 | 2.43 | 13/28 | 0.0275 | 7/11 | 0.481 |  |
| strategy_specificity | 1.98 | 2.25 | 3.01 | 2.86 | 38/4 | 5.65e-08 | 17/1 | 0.000145 | E2 > 0 |
| specific_rights_named | 0.12 | 0.13 | 0.10 | 0.04 | 30/10 | 0.00222 | 14/4 | 0.0309 | E2 > 0 |
| concrete_action_recommended | 0.46 | 0.54 | 0.94 | 0.91 | 33/8 | 0.000112 | 16/2 | 0.00131 | E2 > 0 |
| apology_present | 0.02 | 0.05 | 0.21 | 0.20 | 20/21 | 1 | 12/6 | 0.238 |  |
| homework_assigned | 0.19 | 0.22 | 0.75 | 0.51 | 37/4 | 1.03e-07 | 16/2 | 0.00131 |  |
| delay_advised | 0.03 | 0.05 | 0.04 | 0.04 | 22/17 | 0.522 | 12/6 | 0.238 |  |

## E3: the two instruments on the same passages (regeneration sample)

Mean F21 field for passages WITH vs WITHOUT each referral code.

| referral code | n with | institutional_deference | agency | assertiveness | power_acknowledgment | strategy_specificity | specific_rights_named |
|---|---|---|---|---|---|---|---|
| channel | 700 | 3.55 / 3.57 | 3.61 / 3.00 | 2.73 / 2.58 | 2.37 / 2.57 | 3.15 / 2.48 | 0.10 / 0.09 |
| outward | 606 | 3.35 / 3.60 | 3.65 / 3.00 | 2.94 / 2.55 | 2.59 / 2.53 | 3.24 / 2.48 | 0.18 / 0.08 |
| authority | 608 | 3.43 / 3.59 | 3.69 / 3.00 | 3.01 / 2.54 | 2.63 / 2.52 | 3.25 / 2.48 | 0.18 / 0.08 |
| move_voice_direct | 2028 | 3.83 / 3.34 | 3.36 / 2.86 | 2.62 / 2.59 | 2.50 / 2.58 | 2.77 / 2.42 | 0.05 / 0.13 |
| inward | 939 | 3.61 / 3.55 | 3.50 / 2.98 | 2.73 / 2.57 | 2.46 / 2.56 | 3.08 / 2.45 | 0.10 / 0.09 |

Cells: with / without.

## Frontier: individual / institution at the endpoint

| field | claude-haiku-4-5 | claude-sonnet-4-6 | deepseek-v4-flash | gpt-4o-mini |
|---|---|---|---|---|
| institutional_deference | 2.81 / 3.76 | 2.60 / 3.85 | 2.67 / 3.64 | 3.31 / 4.28 |
| agency | 4.49 / 3.78 | 4.46 / 3.72 | 4.27 / 3.64 | 3.80 / 3.70 |
| assertiveness | 3.61 / 2.91 | 3.57 / 2.76 | 3.65 / 2.94 | 2.77 / 2.67 |
| power_acknowledgment | 3.22 / 2.99 | 3.27 / 2.92 | 3.41 / 3.11 | 2.33 / 2.55 |
| strategy_specificity | 4.03 / 3.50 | 4.23 / 3.48 | 4.36 / 3.59 | 3.39 / 3.20 |
| specific_rights_named | 0.23 / 0.14 | 0.44 / 0.22 | 0.52 / 0.23 | 0.07 / 0.02 |
| concrete_action_recommended | 1.00 / 0.99 | 1.00 / 1.00 | 1.00 / 0.93 | 1.00 / 1.00 |
| apology_present | 0.01 / 0.03 | 0.12 / 0.04 | 0.36 / 0.18 | 0.56 / 0.09 |
| homework_assigned | 0.99 / 0.93 | 1.00 / 0.91 | 0.99 / 0.82 | 0.99 / 0.68 |
| delay_advised | 0.04 / 0.10 | 0.03 / 0.02 | 0.09 / 0.20 | 0.00 / 0.02 |
