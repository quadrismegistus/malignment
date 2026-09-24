# USAS semantic fields: a check with no LLM in the measurement

Producer `usas_test.py`, declared before tagging. Lexicon coverage of tokens (first 3,000 passages): 93.3%.

## PRIMARY: all passages, unfiltered

| field | base ind | base inst | aligned ind | aligned inst | lineages +/- | p | disputes +/- | p | predicted | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| GOV_LAW | 15.69 | 14.67 | 19.13 | 13.37 | 39/4 | 3.11e-08 | 15/3 | 0.00754 | > 0 | SUPPORTED (Holm 6.22e-08 / 0.0151) |
| SPEECH | 28.94 | 34.48 | 48.43 | 45.23 | 38/5 | 2.5e-07 | 15/3 | 0.00754 | < 0 | not supported (Holm 2.5e-07 / 0.0151) |

Rates are field tokens per 1,000 tokens, mean over passages.

## SECONDARY: advice only (coder's form label)

| field | base ind | base inst | aligned ind | aligned inst | lineages +/- | p | disputes +/- | p | predicted | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| GOV_LAW | 21.10 | 15.46 | 19.77 | 13.45 | 8/5 | 0.581 | 11/7 | 0.481 | > 0 | (secondary) (Holm 0.581 / 0.481) |
| SPEECH | 37.74 | 38.42 | 51.01 | 46.67 | 12/1 | 0.00342 | 15/3 | 0.00754 | < 0 | (secondary) (Holm 0.00684 / 0.0151) |

Rates are field tokens per 1,000 tokens, mean over passages.

