# Plate A's words by condition (EXPLORATORY)

Producer `word_frames.py`. Share of passages containing the word, every passage unfiltered, individual / institution. Open models: the same 42 lineages in all three conditions (7,560 passages per condition and side). API: claude-haiku-4-5, claude-sonnet-4-6, deepseek-v4-flash, gpt-4o-mini, pooled (720 per side).

| word | base raw | aligned raw | aligned chat | API |
|---|---|---|---|---|
| contact | 0.059 / 0.060 | 0.171 / 0.099 | 0.369 / 0.095 | 0.547 / 0.086 |
| rights | 0.047 / 0.038 | 0.124 / 0.064 | 0.219 / 0.079 | 0.347 / 0.106 |
| seek | 0.018 / 0.017 | 0.083 / 0.052 | 0.224 / 0.085 | 0.140 / 0.054 |
| request | 0.041 / 0.052 | 0.118 / 0.099 | 0.263 / 0.134 | 0.501 / 0.124 |
| consider | 0.048 / 0.053 | 0.158 / 0.146 | 0.409 / 0.297 | 0.544 / 0.535 |
| local | 0.045 / 0.038 | 0.103 / 0.056 | 0.184 / 0.085 | 0.290 / 0.153 |
| file | 0.053 / 0.043 | 0.096 / 0.036 | 0.153 / 0.031 | 0.565 / 0.087 |
| department | 0.040 / 0.053 | 0.080 / 0.068 | 0.158 / 0.069 | 0.246 / 0.108 |
| listen | 0.007 / 0.022 | 0.009 / 0.079 | 0.005 / 0.210 | 0.001 / 0.464 |
| concerns | 0.020 / 0.046 | 0.089 / 0.211 | 0.167 / 0.363 | 0.126 / 0.383 |
| ensure | 0.027 / 0.046 | 0.097 / 0.191 | 0.162 / 0.298 | 0.056 / 0.175 |
| offer | 0.037 / 0.056 | 0.067 / 0.146 | 0.107 / 0.259 | 0.226 / 0.307 |

## API by model (individual / institution)

| word | claude-haiku-4-5 | claude-sonnet-4-6 | deepseek-v4-flash | gpt-4o-mini |
|---|---|---|---|---|
| contact | 0.64 / 0.10 | 0.76 / 0.18 | 0.17 / 0.04 | 0.62 / 0.02 |
| rights | 0.33 / 0.09 | 0.46 / 0.23 | 0.23 / 0.03 | 0.37 / 0.07 |
| seek | 0.04 / 0.02 | 0.07 / 0.06 | 0.01 / 0.02 | 0.44 / 0.12 |
| request | 0.58 / 0.13 | 0.62 / 0.16 | 0.40 / 0.13 | 0.41 / 0.07 |
| consider | 0.62 / 0.64 | 0.55 / 0.69 | 0.25 / 0.16 | 0.76 / 0.65 |
| local | 0.32 / 0.18 | 0.25 / 0.16 | 0.22 / 0.12 | 0.37 / 0.16 |
| file | 0.64 / 0.12 | 0.74 / 0.13 | 0.42 / 0.08 | 0.46 / 0.02 |
| department | 0.25 / 0.13 | 0.30 / 0.12 | 0.14 / 0.09 | 0.29 / 0.08 |
| listen | 0.01 / 0.51 | 0.00 / 0.47 | 0.00 / 0.22 | 0.00 / 0.66 |
| concerns | 0.10 / 0.37 | 0.07 / 0.34 | 0.01 / 0.13 | 0.33 / 0.68 |
| ensure | 0.01 / 0.06 | 0.01 / 0.18 | 0.00 / 0.01 | 0.21 / 0.45 |
| offer | 0.31 / 0.38 | 0.35 / 0.22 | 0.16 / 0.20 | 0.09 / 0.43 |
