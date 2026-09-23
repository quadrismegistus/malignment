# Frontier API passages: individual minus institution at the endpoint

Producer `frontier_code.py`, written before any frontier passage was coded. Same 36 prompts, 256 tokens, t=1.0 (top_p pinned 1.0 on DeepSeek only; vendor default elsewhere), 10 draws. Cells: individual share / institution share (disputes with individual > institution / <). DeepSeek (*) is coded by its own model and is left out of the pooled test.

| outcome | claude-sonnet-4-6 | claude-haiku-4-5 | gpt-4o-mini | deepseek-v4-flash* | open aligned | pooled 3 frontier: disputes +/- | p | expected |
|---|---|---|---|---|---|---|---|---|
| outward | 0.79 / 0.14 (16/0) | 0.69 / 0.13 (17/0) | 0.46 / 0.04 (16/0) | 0.60 / 0.06 (15/1) | 0.32 / 0.05 (18/0) | 18/0 | 7.63e-06 | ind > inst |
| move_voice_direct | 0.19 / 0.74 (1/15) | 0.25 / 0.74 (1/15) | 0.42 / 0.95 (0/13) | 0.32 / 0.64 (4/12) | 0.45 / 0.80 (4/14) | 1/15 | 0.000519 | inst > ind |
| authority | 0.74 / 0.16 (15/2) | 0.66 / 0.15 (16/1) | 0.43 / 0.04 (14/1) | 0.47 / 0.07 (13/2) | 0.30 / 0.05 (16/2) | 17/1 | 0.000145 | ind > inst |
| channel | 0.42 / 0.07 (13/1) | 0.48 / 0.07 (12/2) | 0.60 / 0.01 (15/1) | 0.30 / 0.02 (12/1) | 0.45 / 0.02 (18/0) | 17/0 | 1.53e-05 | ind > inst |
| any | 0.86 / 0.62 (12/2) | 0.89 / 0.51 (15/2) | 0.88 / 0.38 (16/2) | 0.76 / 0.44 (13/2) | 0.75 / 0.32 (18/0) | 17/1 | 0.000145 |  |
| inward | 0.54 / 0.60 (8/8) | 0.51 / 0.45 (8/8) | 0.48 / 0.29 (11/4) | 0.28 / 0.40 (4/12) | 0.35 / 0.25 (9/9) | 9/8 | 1 |  |
| move_third_party | 0.79 / 0.18 (15/1) | 0.72 / 0.21 (14/1) | 0.57 / 0.01 (13/0) | 0.65 / 0.23 (14/2) | 0.47 / 0.10 (16/2) | 15/1 | 0.000519 |  |

Coded passages: 1440.
