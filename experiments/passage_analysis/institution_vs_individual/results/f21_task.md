# F21's annotation task on the regeneration sample and the frontier

Producer `f21_task_sample.py`, committed before coding. 4361 regeneration passages (up to 30 per lineage x arm x side cell), 1366 kept frontier passages. Model deepseek/deepseek-flash.

## Base -> aligned, individual change minus institution change

| field | base ind | base inst | aligned ind | aligned inst | lineages +/- | p | disputes +/- | p | expected |
|---|---|---|---|---|---|---|---|---|---|
| institutional_deference | 2.88 | 3.74 | 3.36 | 4.11 | 25/16 | 0.211 | 11/7 | 0.481 | E1 null |
| agency | 2.46 | 2.67 | 3.52 | 3.33 | 35/7 | 1.51e-05 | 16/2 | 0.00131 |  |
| assertiveness | 2.55 | 2.52 | 2.73 | 2.52 | 31/11 | 0.00289 | 12/6 | 0.238 |  |
| power_acknowledgment | 2.76 | 2.76 | 2.30 | 2.41 | 13/27 | 0.0385 | 7/11 | 0.481 |  |
| strategy_specificity | 1.98 | 2.25 | 2.95 | 2.79 | 38/4 | 5.65e-08 | 17/1 | 0.000145 | E2 > 0 |
| specific_rights_named | 0.12 | 0.13 | 0.08 | 0.04 | 28/11 | 0.00948 | 14/4 | 0.0309 | E2 > 0 |
| concrete_action_recommended | 0.46 | 0.54 | 0.92 | 0.87 | 33/8 | 0.000112 | 14/4 | 0.0309 | E2 > 0 |
| apology_present | 0.02 | 0.05 | 0.19 | 0.19 | 20/21 | 1 | 12/6 | 0.238 |  |
| homework_assigned | 0.19 | 0.22 | 0.73 | 0.49 | 37/4 | 1.03e-07 | 16/2 | 0.00131 |  |
| delay_advised | 0.03 | 0.05 | 0.04 | 0.04 | 22/17 | 0.522 | 10/8 | 0.815 |  |

## E3: the two instruments on the same passages (regeneration sample)

Mean F21 field for passages WITH vs WITHOUT each referral code.

| referral code | n with | institutional_deference | agency | assertiveness | power_acknowledgment | strategy_specificity | specific_rights_named |
|---|---|---|---|---|---|---|---|
| channel | 671 | 3.55 / 3.55 | 3.61 / 2.96 | 2.72 / 2.56 | 2.37 / 2.56 | 3.13 / 2.44 | 0.09 / 0.09 |
| outward | 595 | 3.34 / 3.58 | 3.65 / 2.96 | 2.94 / 2.53 | 2.58 / 2.52 | 3.23 / 2.44 | 0.17 / 0.08 |
| authority | 592 | 3.42 / 3.57 | 3.69 / 2.96 | 3.02 / 2.52 | 2.63 / 2.51 | 3.25 / 2.43 | 0.17 / 0.08 |
| move_voice_direct | 1965 | 3.81 / 3.33 | 3.34 / 2.82 | 2.61 / 2.57 | 2.49 / 2.56 | 2.74 / 2.39 | 0.04 / 0.13 |
| inward | 915 | 3.59 / 3.54 | 3.49 / 2.94 | 2.72 / 2.55 | 2.46 / 2.55 | 3.07 / 2.41 | 0.09 / 0.09 |

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
