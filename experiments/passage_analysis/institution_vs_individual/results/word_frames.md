# Plate A's words by condition (EXPLORATORY)

Producer `word_frames.py`. Share of passages containing the word, every passage unfiltered, individual / institution. Open models: the six lineages with base-raw, aligned-raw and aligned-chat cells (AquilaChat2-7B, archangel_sft-dpo_pythia2-8b, eleuther-pythia6.9b-hh-dpo, AmberSafe, beaver-7b-v1.0, RedPajama-INCITE-7B-Chat). API: claude-haiku-4-5, claude-sonnet-4-6, deepseek-v4-flash, gpt-4o-mini, pooled.

| word | base raw (6) | aligned raw (6) | aligned chat (6) | API (4) | base raw (all 43) | aligned chat (all 43) |
|---|---|---|---|---|---|---|
| contact | 0.05 / 0.07 | 0.18 / 0.12 | 0.29 / 0.14 | 0.55 / 0.09 | 0.06 / 0.06 | 0.36 / 0.09 |
| rights | 0.04 / 0.03 | 0.10 / 0.06 | 0.11 / 0.05 | 0.35 / 0.11 | 0.05 / 0.04 | 0.21 / 0.08 |
| seek | 0.01 / 0.01 | 0.03 / 0.03 | 0.05 / 0.05 | 0.14 / 0.05 | 0.02 / 0.02 | 0.22 / 0.08 |
| request | 0.03 / 0.03 | 0.05 / 0.06 | 0.08 / 0.08 | 0.50 / 0.12 | 0.04 / 0.05 | 0.26 / 0.13 |
| local | 0.04 / 0.04 | 0.08 / 0.04 | 0.13 / 0.04 | 0.29 / 0.15 | 0.04 / 0.04 | 0.18 / 0.08 |
| consider | 0.02 / 0.04 | 0.07 / 0.06 | 0.15 / 0.13 | 0.54 / 0.53 | 0.05 / 0.05 | 0.40 / 0.29 |
| file | 0.07 / 0.05 | 0.07 / 0.04 | 0.11 / 0.03 | 0.57 / 0.09 | 0.05 / 0.04 | 0.15 / 0.03 |
| department | 0.03 / 0.06 | 0.08 / 0.07 | 0.09 / 0.06 | 0.25 / 0.11 | 0.04 / 0.05 | 0.15 / 0.07 |
| listen | 0.01 / 0.01 | 0.01 / 0.04 | 0.01 / 0.07 | 0.00 / 0.46 | 0.01 / 0.02 | 0.01 / 0.21 |
| concerns | 0.01 / 0.02 | 0.07 / 0.12 | 0.09 / 0.18 | 0.13 / 0.38 | 0.02 / 0.04 | 0.16 / 0.35 |
| ensure | 0.01 / 0.01 | 0.07 / 0.13 | 0.08 / 0.17 | 0.06 / 0.17 | 0.03 / 0.04 | 0.16 / 0.29 |
| offer | 0.04 / 0.04 | 0.05 / 0.11 | 0.05 / 0.13 | 0.23 / 0.31 | 0.04 / 0.05 | 0.10 / 0.25 |

## API by model (individual / institution)

| word | claude-haiku-4-5 | claude-sonnet-4-6 | deepseek-v4-flash | gpt-4o-mini |
|---|---|---|---|---|
| contact | 0.64 / 0.10 | 0.76 / 0.18 | 0.17 / 0.04 | 0.62 / 0.02 |
| rights | 0.33 / 0.09 | 0.46 / 0.23 | 0.23 / 0.03 | 0.37 / 0.07 |
| seek | 0.04 / 0.02 | 0.07 / 0.06 | 0.01 / 0.02 | 0.44 / 0.12 |
| request | 0.58 / 0.13 | 0.62 / 0.16 | 0.40 / 0.13 | 0.41 / 0.07 |
| local | 0.32 / 0.18 | 0.25 / 0.16 | 0.22 / 0.12 | 0.37 / 0.16 |
| consider | 0.62 / 0.64 | 0.55 / 0.69 | 0.25 / 0.16 | 0.76 / 0.65 |
| file | 0.64 / 0.12 | 0.74 / 0.13 | 0.42 / 0.08 | 0.46 / 0.02 |
| department | 0.25 / 0.13 | 0.30 / 0.12 | 0.14 / 0.09 | 0.29 / 0.08 |
| listen | 0.01 / 0.51 | 0.00 / 0.47 | 0.00 / 0.22 | 0.00 / 0.66 |
| concerns | 0.10 / 0.37 | 0.07 / 0.34 | 0.01 / 0.13 | 0.33 / 0.68 |
| ensure | 0.01 / 0.06 | 0.01 / 0.18 | 0.00 / 0.01 | 0.21 / 0.45 |
| offer | 0.31 / 0.38 | 0.35 / 0.22 | 0.16 / 0.20 | 0.09 / 0.43 |

## Per lineage, the six (individual / institution)

| word | lineage | base raw | aligned raw | aligned chat |
|---|---|---|---|---|
| contact | AquilaChat2-7B | 0.06 / 0.06 | 0.07 / 0.11 | 0.15 / 0.14 |
| contact | archangel_sft-dpo_pythia2-8b | 0.04 / 0.10 | 0.03 / 0.06 | 0.13 / 0.09 |
| contact | eleuther-pythia6.9b-hh-dpo | 0.06 / 0.06 | 0.01 / 0.03 | 0.11 / 0.08 |
| contact | AmberSafe | 0.03 / 0.04 | 0.65 / 0.28 | 0.68 / 0.26 |
| contact | beaver-7b-v1.0 | 0.07 / 0.06 | 0.24 / 0.13 | 0.38 / 0.09 |
| contact | RedPajama-INCITE-7B-Chat | 0.06 / 0.10 | 0.09 / 0.08 | 0.28 / 0.14 |
| rights | AquilaChat2-7B | 0.03 / 0.03 | 0.04 / 0.07 | 0.05 / 0.06 |
| rights | archangel_sft-dpo_pythia2-8b | 0.02 / 0.01 | 0.04 / 0.06 | 0.03 / 0.01 |
| rights | eleuther-pythia6.9b-hh-dpo | 0.01 / 0.03 | 0.06 / 0.07 | 0.06 / 0.06 |
| rights | AmberSafe | 0.03 / 0.01 | 0.19 / 0.11 | 0.19 / 0.09 |
| rights | beaver-7b-v1.0 | 0.07 / 0.06 | 0.21 / 0.04 | 0.24 / 0.03 |
| rights | RedPajama-INCITE-7B-Chat | 0.04 / 0.03 | 0.06 / 0.03 | 0.07 / 0.03 |
| seek | AquilaChat2-7B | 0.01 / 0.01 | 0.01 / 0.02 | 0.04 / 0.10 |
| seek | archangel_sft-dpo_pythia2-8b | 0.00 / 0.01 | 0.00 / 0.01 | 0.00 / 0.00 |
| seek | eleuther-pythia6.9b-hh-dpo | 0.01 / 0.01 | 0.02 / 0.02 | 0.01 / 0.01 |
| seek | AmberSafe | 0.00 / 0.01 | 0.08 / 0.04 | 0.08 / 0.06 |
| seek | beaver-7b-v1.0 | 0.03 / 0.00 | 0.02 / 0.04 | 0.07 / 0.04 |
| seek | RedPajama-INCITE-7B-Chat | 0.01 / 0.01 | 0.04 / 0.05 | 0.07 / 0.06 |
| request | AquilaChat2-7B | 0.04 / 0.06 | 0.03 / 0.03 | 0.07 / 0.08 |
| request | archangel_sft-dpo_pythia2-8b | 0.03 / 0.03 | 0.02 / 0.02 | 0.05 / 0.08 |
| request | eleuther-pythia6.9b-hh-dpo | 0.00 / 0.01 | 0.02 / 0.04 | 0.01 / 0.04 |
| request | AmberSafe | 0.03 / 0.01 | 0.12 / 0.11 | 0.12 / 0.08 |
| request | beaver-7b-v1.0 | 0.04 / 0.02 | 0.04 / 0.10 | 0.12 / 0.04 |
| request | RedPajama-INCITE-7B-Chat | 0.04 / 0.04 | 0.07 / 0.07 | 0.11 / 0.14 |
| local | AquilaChat2-7B | 0.04 / 0.03 | 0.03 / 0.01 | 0.07 / 0.04 |
| local | archangel_sft-dpo_pythia2-8b | 0.04 / 0.06 | 0.06 / 0.06 | 0.03 / 0.01 |
| local | eleuther-pythia6.9b-hh-dpo | 0.02 / 0.03 | 0.01 / 0.02 | 0.04 / 0.02 |
| local | AmberSafe | 0.02 / 0.03 | 0.21 / 0.08 | 0.33 / 0.11 |
| local | beaver-7b-v1.0 | 0.04 / 0.03 | 0.12 / 0.04 | 0.19 / 0.03 |
| local | RedPajama-INCITE-7B-Chat | 0.05 / 0.04 | 0.03 / 0.03 | 0.09 / 0.06 |
| consider | AquilaChat2-7B | 0.02 / 0.08 | 0.08 / 0.06 | 0.12 / 0.14 |
| consider | archangel_sft-dpo_pythia2-8b | 0.02 / 0.04 | 0.01 / 0.02 | 0.02 / 0.02 |
| consider | eleuther-pythia6.9b-hh-dpo | 0.02 / 0.02 | 0.02 / 0.02 | 0.08 / 0.08 |
| consider | AmberSafe | 0.01 / 0.01 | 0.17 / 0.08 | 0.29 / 0.17 |
| consider | beaver-7b-v1.0 | 0.03 / 0.04 | 0.08 / 0.07 | 0.15 / 0.12 |
| consider | RedPajama-INCITE-7B-Chat | 0.01 / 0.02 | 0.08 / 0.13 | 0.22 / 0.23 |
| file | AquilaChat2-7B | 0.16 / 0.06 | 0.04 / 0.01 | 0.13 / 0.02 |
| file | archangel_sft-dpo_pythia2-8b | 0.02 / 0.02 | 0.02 / 0.02 | 0.06 / 0.04 |
| file | eleuther-pythia6.9b-hh-dpo | 0.02 / 0.05 | 0.01 / 0.01 | 0.07 / 0.01 |
| file | AmberSafe | 0.09 / 0.07 | 0.09 / 0.06 | 0.11 / 0.01 |
| file | beaver-7b-v1.0 | 0.06 / 0.05 | 0.17 / 0.06 | 0.19 / 0.05 |
| file | RedPajama-INCITE-7B-Chat | 0.05 / 0.05 | 0.08 / 0.07 | 0.09 / 0.06 |
| department | AquilaChat2-7B | 0.02 / 0.07 | 0.05 / 0.03 | 0.11 / 0.07 |
| department | archangel_sft-dpo_pythia2-8b | 0.04 / 0.07 | 0.05 / 0.07 | 0.03 / 0.03 |
| department | eleuther-pythia6.9b-hh-dpo | 0.02 / 0.06 | 0.04 / 0.06 | 0.05 / 0.06 |
| department | AmberSafe | 0.03 / 0.04 | 0.19 / 0.14 | 0.21 / 0.14 |
| department | beaver-7b-v1.0 | 0.03 / 0.06 | 0.08 / 0.04 | 0.04 / 0.02 |
| department | RedPajama-INCITE-7B-Chat | 0.04 / 0.08 | 0.07 / 0.06 | 0.07 / 0.06 |
| listen | AquilaChat2-7B | 0.01 / 0.01 | 0.01 / 0.06 | 0.00 / 0.08 |
| listen | archangel_sft-dpo_pythia2-8b | 0.01 / 0.02 | 0.02 / 0.01 | 0.00 / 0.01 |
| listen | eleuther-pythia6.9b-hh-dpo | 0.01 / 0.02 | 0.01 / 0.02 | 0.02 / 0.04 |
| listen | AmberSafe | 0.01 / 0.00 | 0.01 / 0.06 | 0.01 / 0.12 |
| listen | beaver-7b-v1.0 | 0.00 / 0.01 | 0.00 / 0.03 | 0.00 / 0.05 |
| listen | RedPajama-INCITE-7B-Chat | 0.01 / 0.01 | 0.02 / 0.09 | 0.01 / 0.11 |
| concerns | AquilaChat2-7B | 0.00 / 0.04 | 0.06 / 0.11 | 0.08 / 0.20 |
| concerns | archangel_sft-dpo_pythia2-8b | 0.00 / 0.01 | 0.02 / 0.03 | 0.02 / 0.04 |
| concerns | eleuther-pythia6.9b-hh-dpo | 0.01 / 0.02 | 0.02 / 0.07 | 0.11 / 0.10 |
| concerns | AmberSafe | 0.01 / 0.02 | 0.13 / 0.21 | 0.13 / 0.31 |
| concerns | beaver-7b-v1.0 | 0.01 / 0.01 | 0.09 / 0.16 | 0.06 / 0.15 |
| concerns | RedPajama-INCITE-7B-Chat | 0.01 / 0.01 | 0.08 / 0.13 | 0.14 / 0.26 |
| ensure | AquilaChat2-7B | 0.01 / 0.01 | 0.01 / 0.06 | 0.04 / 0.13 |
| ensure | archangel_sft-dpo_pythia2-8b | 0.01 / 0.01 | 0.01 / 0.01 | 0.01 / 0.02 |
| ensure | eleuther-pythia6.9b-hh-dpo | 0.01 / 0.02 | 0.02 / 0.04 | 0.02 / 0.03 |
| ensure | AmberSafe | 0.02 / 0.02 | 0.22 / 0.30 | 0.23 / 0.39 |
| ensure | beaver-7b-v1.0 | 0.02 / 0.02 | 0.08 / 0.19 | 0.10 / 0.26 |
| ensure | RedPajama-INCITE-7B-Chat | 0.02 / 0.01 | 0.09 / 0.16 | 0.10 / 0.18 |
| offer | AquilaChat2-7B | 0.01 / 0.04 | 0.03 / 0.09 | 0.01 / 0.12 |
| offer | archangel_sft-dpo_pythia2-8b | 0.08 / 0.02 | 0.06 / 0.06 | 0.05 / 0.04 |
| offer | eleuther-pythia6.9b-hh-dpo | 0.04 / 0.04 | 0.03 / 0.04 | 0.06 / 0.07 |
| offer | AmberSafe | 0.03 / 0.03 | 0.09 / 0.17 | 0.10 / 0.21 |
| offer | beaver-7b-v1.0 | 0.02 / 0.06 | 0.05 / 0.21 | 0.04 / 0.13 |
| offer | RedPajama-INCITE-7B-Chat | 0.04 / 0.06 | 0.04 / 0.07 | 0.06 / 0.19 |
