# USAS semantic fields: a check with no LLM in the measurement

Producer `usas_test.py`, declared before tagging. Lexicon coverage of tokens (first 3,000 passages): 93.3%.

## PRIMARY: all passages, unfiltered

| field | base ind | base inst | aligned ind | aligned inst | lineages +/- | p | disputes +/- | p | predicted | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| GOV_LAW | 15.90 | 14.86 | 19.53 | 13.63 | 38/4 | 5.65e-08 | 15/3 | 0.00754 | > 0 | SUPPORTED (Holm 1.13e-07 / 0.0151) |
| SPEECH | 29.35 | 34.95 | 49.51 | 46.23 | 37/5 | 4.43e-07 | 15/3 | 0.00754 | < 0 | not supported (Holm 4.43e-07 / 0.0151) |

Rates are field tokens per 1,000 tokens, mean over passages.

## SECONDARY: advice only (coder's form label)

| field | base ind | base inst | aligned ind | aligned inst | lineages +/- | p | disputes +/- | p | predicted | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| GOV_LAW | 21.10 | 15.46 | 19.77 | 13.45 | 8/5 | 0.581 | 11/7 | 0.481 | > 0 | (secondary) (Holm 0.581 / 0.481) |
| SPEECH | 37.74 | 38.42 | 51.01 | 46.67 | 12/1 | 0.00342 | 15/3 | 0.00754 | < 0 | (secondary) (Holm 0.00684 / 0.0151) |

Rates are field tokens per 1,000 tokens, mean over passages.

