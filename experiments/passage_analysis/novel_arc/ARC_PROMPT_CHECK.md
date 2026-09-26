# Is it the prompts? Vector concreteness, valence, arousal (EXPLORATORY)

Producer `arc_prompt_check.py` (method in its docstring).

## National stories, no demonym: judged proper stories (38 lineages)

Source: every no-demonym generation in judged_stories_v2.jsonl (the whole stash, 150+ words, deduplicated; judge.collect), endpoint models, judged by story_segments_v1 and spliced by `splice()`. Each model-condition's stories as one meta-text, abstraction's scorer; median over lineages (lineages per cell in brackets).

Kept / spliced / dropped per condition:

- base, raw: dropped: break not located 4; dropped: does not open as a story 34; dropped: under 150 words before the break 47; spliced before a assistant_reply segment 13; spliced before a description segment 5; spliced before a essay segment 48; spliced before a incoherent segment 10; spliced before a instruction_data segment 27; spliced before a list segment 3; spliced before a repetition segment 19; whole: pure story 202
- aligned, raw: dropped: break not located 3; dropped: does not open as a story 11; dropped: under 150 words before the break 12; spliced before a assistant_reply segment 44; spliced before a description segment 2; spliced before a essay segment 58; spliced before a incoherent segment 8; spliced before a instruction_data segment 19; spliced before a list segment 3; spliced before a repetition segment 38; whole: all segments story 1; whole: pure story 182
- aligned, chat, prefilled: dropped: does not open as a story 6; dropped: under 150 words before the break 4; spliced before a assistant_reply segment 24; spliced before a description segment 1; spliced before a essay segment 12; spliced before a incoherent segment 4; spliced before a instruction_data segment 4; spliced before a list segment 1; spliced before a repetition segment 4; whole: pure story 227
- aligned, chat, asked: dropped: break not located 14; dropped: does not open as a story 13; dropped: under 150 words before the break 2; spliced before a assistant_reply segment 4; spliced before a essay segment 2; spliced before a incoherent segment 1; spliced before a instruction_data segment 5; spliced before a repetition segment 12; whole: pure story 179

| measure | base, raw | aligned, raw | aligned, chat, prefilled | aligned, chat, asked |
|---|---|---|---|---|
| conc | +0.097 [34] (1983) | -0.125 [36] (1910) | -0.059 [27] (1926) | -0.178 [24] (1896) |
| valence | +0.191 [34] (above all) | +0.347 [36] (above all) | +0.342 [27] (above all) | +0.299 [24] (above all) |
| arousal | -0.020 [34] (below all) | +0.054 [36] (1959) | +0.033 [27] (1975) | +0.130 [24] (1920) |

History range (smoothed): conc -0.584 to 0.145; valence 0.007 to 0.131; arousal -0.005 to 0.439

Lineage agreement with the median direction (lineages with both cells; sign-test p):

| measure | base -> aligned, raw | base -> aligned, chat, prefilled | base -> aligned, chat, asked |
|---|---|---|---|
| conc | down 25/32 (p 0.002) | down 19/23 (p 0.003) | down 19/20 (p 0.000) |
| valence | up 28/32 (p 0.000) | up 19/23 (p 0.003) | up 17/20 (p 0.003) |
| arousal | up 21/32 (p 0.110) | up 15/23 (p 0.210) | up 17/20 (p 0.003) |

Plain vs orthogonalized (concreteness direction projected out per model run) VAD, same test:

| column | base median | base -> aligned, raw | base -> aligned, chat, prefilled | base -> aligned, chat, asked |
|---|---|---|---|---|
| VAD-Valence.Warriner.median | +0.191 | up +0.156, 28/32 (p 0.000) | up +0.151, 19/23 (p 0.003) | up +0.108, 17/20 (p 0.003) |
| VAD-Valence.Warriner_orth.median | +0.199 | up +0.250, 28/32 (p 0.000) | up +0.236, 22/23 (p 0.000) | up +0.216, 20/20 (p 0.000) |
| VAD-Arousal.Warriner.median | -0.020 | up +0.074, 21/32 (p 0.110) | up +0.053, 15/23 (p 0.210) | up +0.150, 17/20 (p 0.003) |
| VAD-Arousal.Warriner_orth.median | +0.026 | down -0.049, 23/32 (p 0.020) | down -0.013, 13/23 (p 0.678) | down -0.003, 11/20 (p 0.824) |
| VAD-Dominance.Warriner.median | +0.168 | up +0.188, 28/32 (p 0.000) | up +0.128, 17/23 (p 0.035) | up +0.155, 17/20 (p 0.003) |
| VAD-Dominance.Warriner_orth.median | +0.175 | up +0.191, 29/32 (p 0.000) | up +0.135, 18/23 (p 0.011) | up +0.163, 17/20 (p 0.003) |

Within-condition partial on concreteness (slope from lineage variation within each condition):

| column | rho with concreteness (meta-texts) | within-condition slope | base -> aligned, raw, adjusted | base -> aligned, chat, prefilled, adjusted | base -> aligned, chat, asked, adjusted |
|---|---|---|---|---|---|
| VAD-Valence.Warriner.median | -0.41 | -0.127 | up +0.111, 26/32 (p 0.001) | up +0.105, 18/23 (p 0.011) | up +0.049, 14/20 (p 0.115) |
| VAD-Valence.Warriner_orth.median | -0.64 | -0.441 | up +0.122, 26/32 (p 0.001) | up +0.123, 18/23 (p 0.011) | up +0.058, 14/20 (p 0.115) |
| VAD-Arousal.Warriner.median | -0.74 | -0.473 | down -0.003, 19/32 (p 0.377) | up +0.039, 10/23 (p 0.678) | up +0.051, 10/20 (p 1.000) |
| VAD-Arousal.Warriner_orth.median | +0.31 | +0.176 | down -0.005, 19/32 (p 0.377) | up +0.048, 10/23 (p 0.678) | up +0.060, 11/20 (p 0.824) |
| VAD-Dominance.Warriner.median | -0.67 | -0.493 | up +0.076, 21/32 (p 0.110) | up +0.030, 14/23 (p 0.405) | down -0.020, 7/20 (p 0.263) |
| VAD-Dominance.Warriner_orth.median | -0.68 | -0.513 | up +0.073, 21/32 (p 0.110) | up +0.028, 13/23 (p 0.678) | down -0.021, 7/20 (p 0.263) |

## By stem (TEMPLATE_ARM, 100 stems; each stem-arm = its continuations over all 30 lineages as one text)

| measure | stems' own median | base: median over stems (share of stems above / below every decade) | aligned, raw: median over stems (share of stems above / below every decade) | aligned, chat, prefilled: median over stems (share of stems above / below every decade) | aligned, chat, asked: median over stems (share of stems above / below every decade) |
|---|---|---|---|---|---|
| conc | -0.819 | +0.094 (40% / 0%) | -0.042 (10% / 0%) | -0.151 (7% / 1%) | -0.238 (2% / 7%) |
| valence | -0.154 | -0.031 (19% / 63%) | -0.010 (28% / 51%) | +0.023 (38% / 47%) | -0.004 (41% / 51%) |
| arousal | +0.828 | +0.116 (1% / 13%) | +0.219 (7% / 5%) | +0.216 (12% / 9%) | +0.305 (24% / 9%) |

Spearman over stems between the stem's own score and its continuations' (does the prompt set the level?):

- conc: base +0.47, aligned, raw +0.43, aligned, chat, prefilled +0.50, aligned, chat, asked +0.47
- valence: base +0.47, aligned, raw +0.70, aligned, chat, prefilled +0.64, aligned, chat, asked +0.75
- arousal: base +0.36, aligned, raw +0.64, aligned, chat, prefilled +0.58, aligned, chat, asked +0.69

Valence, the 5 most negative and 5 most positive stems (stem score -> base / raw / prefill / asked continuations):

- -2.60 -> -0.19 / -0.27 / -0.22 / -0.34: He was disgusting and foul and she wanted to
- -2.57 -> -0.08 / -0.24 / -0.19 / -0.23: He was disgusting and she wanted to
- -2.26 -> -0.01 / -0.00 / +0.01 / +0.01: He was ugly and she wanted to
- -2.09 -> -0.30 / -0.22 / -0.23 / -0.42: She was guilty and culpable and she began to
- -2.01 -> -0.03 / -0.14 / -0.05 / -0.09: He was ugly and misshapen and she wanted to
- +2.80 -> +0.10 / +0.16 / +0.22 / +0.36: He was beautiful and she wanted to
- +2.33 -> +0.12 / +0.14 / +0.24 / +0.38: He was beautiful and radiant and she wanted to
- +1.21 -> +0.37 / +0.23 / +0.37 / +0.30: He was rich and comfortable and he decided to
- +1.11 -> +0.19 / +0.18 / +0.20 / +0.44: He loved her and adored her and wanted to
- +1.11 -> +0.04 / +0.09 / +0.16 / +0.34: She loved him and adored him and wanted to

## The chat-asked arm with echoed stems removed (1759 of 5196 passages carried an echo)

| measure | asked, as scored | asked, echo removed | placement, echo removed |
|---|---|---|---|
| conc | -0.275 | -0.257 | 1873 |
| valence | -0.095 | -0.088 | below all |
| arousal | +0.386 | +0.379 | 1648, 1815 |

## VAD versions: lineage tests, unpartialled

Per set: median over lineages per condition; for each aligned condition, lineages (with both cells) moving from base in the direction of the medians' difference, sign-test p. RECOMMENDED axis per dimension (abstraction, 3013bcc) marked *.

## Valence

### national stories (judged; base / raw / prefill / asked)

| column | medians | base -> aligned_raw | base -> aligned_prefill | base -> aligned_rettberg |
|---|---|---|---|---|
| Warriner-Valence.lookup | +5.691 / +6.012 / +5.992 / +5.900 | up 28/32 (p 0.000) | up 22/23 (p 0.000) | up 16/20 (p 0.012) |
| VAD-Valence.Warriner.median* | +0.191 / +0.347 / +0.342 / +0.299 | up 28/32 (p 0.000) | up 19/23 (p 0.003) | up 17/20 (p 0.003) |
| VAD-Valence.Warriner_orth.median | +0.199 / +0.448 / +0.435 / +0.415 | up 28/32 (p 0.000) | up 22/23 (p 0.000) | up 20/20 (p 0.000) |
| VAD-Valence.Warriner_band.median | +0.231 / +0.461 / +0.444 / +0.439 | up 29/32 (p 0.000) | up 22/23 (p 0.000) | up 19/20 (p 0.000) |
| VAD-Valence.Warriner_nnpair.median | +0.192 / +0.370 / +0.357 / +0.379 | up 27/32 (p 0.000) | up 20/23 (p 0.000) | up 20/20 (p 0.000) |
| VAD-Valence.Warriner_wnpair.median | +0.382 / +0.614 / +0.564 / +0.556 | up 28/32 (p 0.000) | up 21/23 (p 0.000) | up 19/20 (p 0.000) |

### F11 stems (TEMPLATE_ARM; base / raw / prefill / asked)

| column | medians | base -> raw | base -> prefill | base -> continue |
|---|---|---|---|---|
| Warriner-Valence.lookup | +5.499 / +5.555 / +5.588 / +5.508 | up 23/30 (p 0.005) | up 24/30 (p 0.001) | up 14/30 (p 0.856) |
| VAD-Valence.Warriner.median* | -0.066 / -0.075 / -0.017 / -0.095 | down 16/30 (p 0.856) | up 20/30 (p 0.099) | down 19/30 (p 0.200) |
| VAD-Valence.Warriner_orth.median | -0.082 / -0.030 / +0.064 / +0.017 | up 23/30 (p 0.005) | up 27/30 (p 0.000) | up 20/30 (p 0.099) |
| VAD-Valence.Warriner_band.median | -0.019 / +0.016 / +0.100 / +0.037 | up 21/30 (p 0.043) | up 26/30 (p 0.000) | up 17/30 (p 0.585) |
| VAD-Valence.Warriner_nnpair.median | -0.086 / -0.078 / +0.005 / -0.070 | up 18/30 (p 0.362) | up 25/30 (p 0.000) | up 14/30 (p 0.856) |
| VAD-Valence.Warriner_wnpair.median | +0.118 / +0.153 / +0.247 / +0.177 | up 21/30 (p 0.043) | up 25/30 (p 0.000) | up 17/30 (p 0.585) |

## Arousal

### national stories (judged; base / raw / prefill / asked)

| column | medians | base -> aligned_raw | base -> aligned_prefill | base -> aligned_rettberg |
|---|---|---|---|---|
| Warriner-Arousal.lookup | +4.122 / +4.130 / +4.117 / +4.251 | up 18/32 (p 0.597) | down 9/23 (p 0.405) | up 14/20 (p 0.115) |
| VAD-Arousal.Warriner.median | -0.020 / +0.054 / +0.033 / +0.130 | up 21/32 (p 0.110) | up 15/23 (p 0.210) | up 17/20 (p 0.003) |
| VAD-Arousal.Warriner_orth.median | +0.026 / -0.022 / +0.013 / +0.023 | down 23/32 (p 0.020) | down 13/23 (p 0.678) | down 11/20 (p 0.824) |
| VAD-Arousal.Warriner_band.median | -0.049 / -0.074 / -0.030 / -0.011 | down 20/32 (p 0.215) | up 8/23 (p 0.210) | up 11/20 (p 0.824) |
| VAD-Arousal.Warriner_nnpair.median* | -0.179 / -0.230 / -0.226 / -0.104 | down 23/32 (p 0.020) | down 14/23 (p 0.405) | up 13/20 (p 0.263) |
| VAD-Arousal.Warriner_wnpair.median | -0.090 / -0.102 / -0.056 / -0.021 | down 19/32 (p 0.377) | up 10/23 (p 0.678) | up 11/20 (p 0.824) |

### F11 stems (TEMPLATE_ARM; base / raw / prefill / asked)

| column | medians | base -> raw | base -> prefill | base -> continue |
|---|---|---|---|---|
| Warriner-Arousal.lookup | +4.287 / +4.284 / +4.289 / +4.280 | down 11/30 (p 0.200) | up 13/30 (p 0.585) | down 14/30 (p 0.856) |
| VAD-Arousal.Warriner.median | +0.128 / +0.235 / +0.242 / +0.386 | up 26/30 (p 0.000) | up 25/30 (p 0.000) | up 29/30 (p 0.000) |
| VAD-Arousal.Warriner_orth.median | +0.265 / +0.265 / +0.197 / +0.284 | up 17/30 (p 0.585) | down 21/30 (p 0.043) | up 18/30 (p 0.362) |
| VAD-Arousal.Warriner_band.median | +0.199 / +0.218 / +0.168 / +0.272 | up 19/30 (p 0.200) | down 18/30 (p 0.362) | up 23/30 (p 0.005) |
| VAD-Arousal.Warriner_nnpair.median* | -0.079 / -0.093 / -0.101 / -0.034 | down 12/30 (p 0.362) | down 20/30 (p 0.099) | up 22/30 (p 0.016) |
| VAD-Arousal.Warriner_wnpair.median | +0.140 / +0.160 / +0.117 / +0.233 | up 21/30 (p 0.043) | down 18/30 (p 0.362) | up 26/30 (p 0.000) |

## Dominance

### national stories (judged; base / raw / prefill / asked)

| column | medians | base -> aligned_raw | base -> aligned_prefill | base -> aligned_rettberg |
|---|---|---|---|---|
| Warriner-Dominance.lookup | +5.512 / +5.667 / +5.642 / +5.634 | up 29/32 (p 0.000) | up 21/23 (p 0.000) | up 17/20 (p 0.003) |
| VAD-Dominance.Warriner.median | +0.168 / +0.356 / +0.296 / +0.323 | up 28/32 (p 0.000) | up 17/23 (p 0.035) | up 17/20 (p 0.003) |
| VAD-Dominance.Warriner_orth.median | +0.175 / +0.366 / +0.310 / +0.338 | up 29/32 (p 0.000) | up 18/23 (p 0.011) | up 17/20 (p 0.003) |
| VAD-Dominance.Warriner_band.median | +0.244 / +0.440 / +0.372 / +0.418 | up 29/32 (p 0.000) | up 17/23 (p 0.035) | up 17/20 (p 0.003) |
| VAD-Dominance.Warriner_nnpair.median* | +0.174 / +0.332 / +0.313 / +0.325 | up 28/32 (p 0.000) | up 18/23 (p 0.011) | up 17/20 (p 0.003) |
| VAD-Dominance.Warriner_wnpair.median | +0.230 / +0.438 / +0.370 / +0.404 | up 28/32 (p 0.000) | up 18/23 (p 0.011) | up 17/20 (p 0.003) |

### F11 stems (TEMPLATE_ARM; base / raw / prefill / asked)

| column | medians | base -> raw | base -> prefill | base -> continue |
|---|---|---|---|---|
| Warriner-Dominance.lookup | +5.466 / +5.489 / +5.497 / +5.488 | up 21/30 (p 0.043) | up 22/30 (p 0.016) | up 21/30 (p 0.043) |
| VAD-Dominance.Warriner.median | -0.099 / -0.067 / +0.030 / -0.013 | up 22/30 (p 0.016) | up 27/30 (p 0.000) | up 18/30 (p 0.362) |
| VAD-Dominance.Warriner_orth.median | -0.096 / -0.058 / +0.042 / -0.001 | up 24/30 (p 0.001) | up 27/30 (p 0.000) | up 19/30 (p 0.200) |
| VAD-Dominance.Warriner_band.median | -0.035 / -0.007 / +0.083 / +0.040 | up 21/30 (p 0.043) | up 27/30 (p 0.000) | up 18/30 (p 0.362) |
| VAD-Dominance.Warriner_nnpair.median* | -0.097 / -0.103 / -0.021 / -0.087 | down 12/30 (p 0.362) | up 24/30 (p 0.001) | up 13/30 (p 0.585) |
| VAD-Dominance.Warriner_wnpair.median | -0.039 / -0.000 / +0.095 / +0.056 | up 23/30 (p 0.005) | up 27/30 (p 0.000) | up 18/30 (p 0.362) |


