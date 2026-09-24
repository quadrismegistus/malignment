# USAS semantic fields: a check with no LLM in the measurement

Producer `usas_test.py`, declared before tagging. Lexicon coverage of tokens (first 3,000 passages): 93.3%.

## PRIMARY: all passages, unfiltered

| field | base ind | base inst | aligned ind | aligned inst | lineages +/- | p | disputes +/- | p | predicted | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| GOV_LAW | 15.90 | 14.86 | 19.46 | 13.43 | 39/3 | 5.63e-09 | 15/3 | 0.00754 | > 0 | SUPPORTED (Holm 1.13e-08 / 0.0151) |
| SPEECH | 29.35 | 34.95 | 49.67 | 46.16 | 37/5 | 4.43e-07 | 15/3 | 0.00754 | < 0 | not supported (Holm 4.43e-07 / 0.0151) |

Rates are field tokens per 1,000 tokens, mean over passages.

## SECONDARY: advice only (coder's form label)

| field | base ind | base inst | aligned ind | aligned inst | lineages +/- | p | disputes +/- | p | predicted | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| GOV_LAW | 21.10 | 15.46 | 19.78 | 13.61 | 8/7 | 1 | 10/8 | 0.815 | > 0 | (secondary) (Holm 1 / 0.815) |
| SPEECH | 37.74 | 38.42 | 50.79 | 46.51 | 14/1 | 0.000977 | 15/3 | 0.00754 | < 0 | (secondary) (Holm 0.00195 / 0.0151) |

Rates are field tokens per 1,000 tokens, mean over passages.

