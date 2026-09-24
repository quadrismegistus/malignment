# Framed Y: the in-scene superego under the chat template

Producer `analyse.py`, the analysis registered in README.md (2904c6fb) and amendment 1, run after all coding. 40 checkpoints, 31 lineages. SUPEREGO = SUPEREGO_IN_SCENE given sexual_scene, pass A; REFUSAL, EXIT, SCENE = all-length rates (strata weighted by pool size). All in points.

## Per model

| model | sys | superego raw / prefill / continue | scenes (A) | refusal raw / prefill / continue | exit raw / prefill / continue | scene raw / prefill / continue |
|---|---|---|---|---|---|---|
| `01-ai/Yi-1.5-9B-Chat` | default | 16.2 / 11.8 / 12.1 | 450 / 110 / 398 | 0.0 / 0.7 / 4.0 | 21.3 / 4.0 / 1.7 | 66.3 / 46.5 / 55.6 |
| `BSC-LT/salamandra-7b-instruct` | empty | 9.8 / 30.0 / 10.4 | 328 / 60 / 212 | 0.4 / 0.1 / 0.2 | 43.8 / 2.1 / 0.9 | 48.2 / 35.3 / 62.8 |
| `ContextualAI/archangel_sft-dpo_pythia2-8b` | default | 20.7 / 12.7 / 14.0 | 450 / 418 / 179 | 0.0 / 0.5 / 0.7 | 5.1 / 45.1 / 83.5 | 65.7 / 55.4 / 21.1 |
| `HuggingFaceTB/SmolLM2-360M-Instruct` | empty | 6.4 / 12.1 / 9.9 | 265 / 66 / 111 | 0.0 / 0.0 / 0.0 | 22.8 / 3.7 / 8.7 | 39.6 / 33.1 / 38.0 |
| `HuggingFaceTB/SmolLM3-3B` | default | 16.5 / 15.7 / 6.6 | 425 / 414 / 457 | 0.0 / 0.6 / 0.1 | 22.1 / 4.7 / 0.4 | 62.7 / 60.9 / 67.1 |
| `LLM360/AmberSafe` | default | 48.3 / 45.4 / 27.8 | 261 / 355 / 108 | 8.7 / 5.4 / 58.3 | 18.7 / 8.9 / 2.3 | 36.4 / 52.4 / 12.3 |
| `OpenLLM-France/Lucie-7B-Instruct-v1.1` | empty | 18.5 / 32.6 / 31.8 | 54 / 46 / 321 | 0.1 / 0.0 / 0.1 | 44.2 / 3.9 / 0.5 | 12.4 / 22.9 / 45.9 |
| `PKU-Alignment/beaver-7b-v1.0` | empty | 9.0 / 7.3 / 1.1 | 465 / 315 / 88 | 0.0 / 0.0 / 0.1 | 17.2 / 14.9 / 3.5 | 67.9 / 61.3 / 62.6 |
| `Qwen/Qwen2.5-0.5B-Instruct` | empty | 10.7 / 0.0 / 8.6 | 103 / 1 / 140 | 1.6 / 0.1 / 0.0 | 84.5 / 3.7 / 1.5 | 15.5 / 6.8 / 49.9 |
| `Qwen/Qwen2.5-7B-Instruct` | empty | 13.5 / 13.9 / 15.0 | 148 / 36 / 20 | 2.2 / 16.7 / 66.6 | 88.4 / 54.1 / 6.6 | 25.7 / 37.0 / 6.1 |
| `Qwen/Qwen3-8B` | empty | 10.3 / 13.3 / 0.0 | 224 / 384 / 3 | 10.3 / 3.6 / 60.4 | 66.5 / 1.6 / 0.1 | 35.3 / 61.4 / 6.0 |
| `TinyLlama/TinyLlama-1.1B-Chat-v1.0` | empty | 13.6 / 10.6 / 7.2 | 369 / 406 / 428 | 0.0 / 0.0 / 0.0 | 25.4 / 2.8 / 2.6 | 53.5 / 59.6 / 63.3 |
| `allenai/Llama-3.1-Tulu-3-8B-DPO` | empty | 27.8 / 25.6 / 20.8 | 425 / 442 / 360 | 0.6 / 0.5 / 23.0 | 28.5 / 1.8 / 0.8 | 61.0 / 54.7 / 40.5 |
| `allenai/Llama-3.1-Tulu-3-8B-SFT` | empty | 24.0 / 24.1 / 22.1 | 338 / 79 / 163 | 0.7 / 0.0 / 17.7 | 32.1 / 2.0 / 2.1 | 56.4 / 43.3 / 41.7 |
| `allenai/OLMo-2-0425-1B-DPO` | empty | 27.4 / 31.0 / 18.3 | 358 / 361 / 399 | 0.0 / 1.9 / 11.1 | 12.5 / 6.5 / 4.9 | 51.4 / 45.5 / 51.5 |
| `allenai/OLMo-2-0425-1B-Instruct` | empty | 30.1 / 24.7 / 17.3 | 346 / 352 / 398 | 0.0 / 1.7 / 8.9 | 11.9 / 7.9 / 5.3 | 49.8 / 45.2 / 53.3 |
| `allenai/OLMo-2-0425-1B-SFT` | empty | 27.1 / 11.5 / 24.8 | 295 / 78 / 254 | 0.6 / 1.8 / 12.3 | 17.1 / 4.4 / 1.0 | 41.3 / 35.0 / 49.7 |
| `allenai/OLMoE-1B-7B-0125-DPO` | empty | 25.5 / 15.2 / 20.5 | 423 / 33 / 176 | 0.6 / 0.0 / 5.4 | 26.1 / 0.5 / 2.2 | 57.4 / 48.7 / 56.8 |
| `allenai/OLMoE-1B-7B-0125-Instruct` | empty | 28.5 / 20.3 / 23.7 | 431 / 64 / 224 | 0.5 / 0.3 / 6.4 | 25.6 / 1.2 / 1.2 | 57.8 / 51.8 / 60.1 |
| `allenai/OLMoE-1B-7B-0125-SFT` | empty | 24.2 / 25.0 / 33.3 | 368 / 8 / 6 | 0.4 / 0.1 / 6.3 | 25.8 / 1.5 / 3.3 | 50.1 / 32.2 / 45.2 |
| `allenai/Olmo-3-7B-Instruct` | empty | 21.6 / 18.6 / 100.0 | 352 / 242 / 2 | 3.2 / 5.4 / 66.8 | 38.1 / 18.8 / 6.4 | 43.8 / 48.9 / 4.1 |
| `allenai/Olmo-3-7B-Instruct-DPO` | empty | 14.5 / 18.0 / 50.0 | 338 / 311 / 4 | 2.1 / 4.2 / 65.6 | 42.0 / 19.3 / 3.6 | 43.7 / 50.1 / 5.5 |
| `allenai/Olmo-3-7B-Instruct-SFT` | empty | 20.5 / 17.3 / 14.3 | 268 / 156 / 7 | 0.9 / 0.3 / 44.9 | 44.1 / 15.4 / 7.5 | 33.9 / 43.1 / 15.6 |
| `baichuan-inc/Baichuan2-7B-Chat` | default | 26.2 / 29.1 / 11.1 | 408 / 258 / 451 | 0.0 / 1.1 / 1.0 | 5.1 / 6.2 / 2.3 | 59.8 / 47.3 / 65.1 |
| `google/gemma-2-9b-it` | default | 39.0 / 35.0 / 25.0 | 344 / 20 / 8 | 4.2 / 35.6 / 59.0 | 22.0 / 46.5 / 24.3 | 50.8 / 41.5 / 8.7 |
| `inceptionai/jais-family-6p7b-chat` | empty | 20.2 / 25.6 / 5.1 | 396 / 78 / 451 | 0.0 / 0.6 / 0.3 | 7.2 / 4.2 / 2.3 | 67.8 / 51.1 / 64.8 |
| `llm-jp/llm-jp-3-7.2b-instruct3` | empty | 41.9 / 45.0 / 30.9 | 403 / 151 / 282 | 0.1 / 2.4 / 5.2 | 12.5 / 10.0 / 29.2 | 57.0 / 49.2 / 51.7 |
| `lomahony/eleuther-pythia6.9b-hh-dpo` | default | 34.6 / 34.2 / 38.5 | 437 / 38 / 13 | 0.0 / 17.5 / 33.1 | 4.5 / 67.9 / 68.3 | 63.4 / 21.1 / 3.0 |
| `m-a-p/neo_7b_instruct_v0.1` | empty | 26.7 / 21.7 / 8.3 | 258 / 355 / 109 | 1.0 / 5.0 / 48.5 | 29.0 / 25.3 / 2.5 | 38.1 / 52.1 / 15.7 |
| `m-a-p/neo_7b_sft_v0.1` | empty | 17.9 / 20.4 / 12.6 | 212 / 157 / 95 | 1.0 / 1.4 / 53.0 | 41.9 / 11.1 / 1.5 | 30.2 / 45.7 / 10.9 |
| `meta-llama/Llama-3.1-8B-Instruct` | default | 16.8 / -- / 20.0 | 273 / 0 / 50 | 0.2 / 5.0 / 56.0 | 46.3 / 16.6 / 0.6 | 40.8 / 18.7 / 8.5 |
| `openbmb/MiniCPM5-1B` | empty | 14.3 / 12.5 / 21.4 | 98 / 40 / 14 | 1.2 / 1.6 / 8.2 | 65.4 / 17.2 / 32.0 | 14.7 / 15.2 / 19.8 |
| `stabilityai/stablelm-2-zephyr-1_6b` | empty | 16.1 / 22.8 / 13.8 | 411 / 403 / 392 | 0.0 / 1.7 / 0.0 | 25.7 / 23.1 / 3.5 | 60.1 / 58.1 / 57.5 |
| `tiiuae/Falcon3-10B-Instruct` | empty | 27.3 / 16.0 / 15.4 | 484 / 119 / 26 | 6.0 / 7.2 / 68.8 | 5.7 / 5.5 / 0.3 | 70.1 / 60.5 / 2.3 |
| `tiiuae/Falcon3-1B-Instruct` | empty | 17.5 / 0.0 / 27.3 | 160 / 2 / 150 | 12.2 / 2.2 / 23.2 | 44.5 / 3.7 / 0.7 | 23.7 / 16.8 / 17.6 |
| `tiiuae/Falcon3-3B-Instruct` | empty | 32.7 / 47.5 / 48.7 | 171 / 61 / 199 | 31.1 / 1.9 / 22.7 | 31.3 / 2.3 / 1.0 | 29.5 / 22.4 / 24.5 |
| `tiiuae/Falcon3-7B-Instruct` | empty | 25.3 / 12.9 / 22.2 | 470 / 85 / 9 | 6.7 / 17.4 / 70.7 | 7.1 / 6.2 / 0.1 | 69.1 / 41.8 / 1.0 |
| `tiiuae/Falcon3-Mamba-7B-Instruct` | empty | 24.0 / 19.3 / 17.9 | 467 / 457 / 435 | 0.3 / 1.0 / 4.1 | 4.3 / 18.1 / 0.8 | 73.6 / 61.9 / 60.4 |
| `tiiuae/falcon-mamba-7b-instruct` | empty | 15.2 / 13.9 / 13.9 | 508 / 309 / 432 | 0.1 / 0.9 / 0.2 | 6.3 / 21.3 / 3.7 | 72.1 / 44.9 / 61.0 |
| `togethercomputer/RedPajama-INCITE-7B-Chat` | default | 20.4 / 10.5 / 6.4 | 506 / 427 / 280 | 0.1 / 0.4 / 2.1 | 26.6 / 74.8 / 82.3 | 74.8 / 63.3 / 41.5 |

## Contrasts, all 40 models (PRIMARY)

| measure | contrast | models + / n (sign p) | median | lineages + / n (sign p) | lineage median |
|---|---|---|---|---|---|
| superego | C1 prefill - raw | 15 / 39 (0.2) | -1.8 | 10 / 31 (0.0708) | -1.7 |
| superego | C2 continue - prefill | 15 / 39 (0.2) | -2.0 | 11 / 31 (0.15) | -2.2 |
| superego | C3 continue - raw | 12 / 40 (0.0166) | -5.0 | 9 / 31 (0.0294) | -4.9 |
| refusal | C1 prefill - raw | 24 / 37 (0.0989) | +0.6 | 19 / 28 (0.0872) | +0.6 |
| refusal | C2 continue - prefill | 32 / 38 (2.43e-05) | +6.9 | 23 / 29 (0.00232) | +3.3 |
| refusal | C3 continue - raw | 33 / 37 (1.08e-06) | +6.5 | 24 / 28 (0.00018) | +4.0 |
| exit | C1 prefill - raw | 7 / 40 (4.23e-05) | -18.2 | 7 / 31 (0.00333) | -17.2 |
| exit | C2 continue - prefill | 10 / 40 (0.00222) | -2.8 | 7 / 31 (0.00333) | -2.7 |
| exit | C3 continue - raw | 5 / 40 (1.38e-06) | -22.4 | 5 / 31 (0.000192) | -19.5 |
| scene | C1 prefill - raw | 11 / 40 (0.00643) | -6.8 | 8 / 31 (0.0107) | -7.8 |
| scene | C2 continue - prefill | 21 / 40 (0.875) | +1.1 | 17 / 31 (0.72) | +1.3 |
| scene | C3 continue - raw | 11 / 40 (0.00643) | -8.4 | 8 / 31 (0.0107) | -6.0 |

## Sensitivity: the 31 empty-system models

| measure | contrast | models + / n (sign p) | median | lineages + / n (sign p) | lineage median |
|---|---|---|---|---|---|
| superego | C1 prefill - raw | 14 / 31 (0.72) | -1.7 | 9 / 23 (0.405) | -1.3 |
| superego | C2 continue - prefill | 12 / 31 (0.281) | -1.3 | 8 / 23 (0.21) | -1.3 |
| superego | C3 continue - raw | 10 / 31 (0.0708) | -3.1 | 8 / 23 (0.21) | -3.1 |
| refusal | C1 prefill - raw | 16 / 28 (0.572) | +0.4 | 12 / 20 (0.503) | +0.4 |
| refusal | C2 continue - prefill | 25 / 29 (0.000104) | +7.2 | 17 / 21 (0.0072) | +6.1 |
| refusal | C3 continue - raw | 24 / 28 (0.00018) | +7.0 | 16 / 20 (0.0118) | +5.2 |
| exit | C1 prefill - raw | 2 / 31 (4.63e-07) | -22.8 | 2 / 23 (6.6e-05) | -22.7 |
| exit | C2 continue - prefill | 7 / 31 (0.00333) | -2.7 | 4 / 23 (0.0026) | -2.7 |
| exit | C3 continue - raw | 1 / 31 (2.98e-08) | -24.4 | 1 / 23 (5.72e-06) | -23.9 |
| scene | C1 prefill - raw | 10 / 31 (0.0708) | -6.4 | 7 / 23 (0.0931) | -6.9 |
| scene | C2 continue - prefill | 18 / 31 (0.473) | +2.1 | 14 / 23 (0.405) | +2.1 |
| scene | C3 continue - raw | 9 / 31 (0.0294) | -5.3 | 6 / 23 (0.0347) | -5.3 |

## FY-3: displaced or added?

Among the 32 models whose REFUSAL rises from prefill to continue, SUPEREGO|scene FALLS in 17 of 31 with a defined contrast (sign p = 0.72).

## Registered readings

- **FY-1, the template alone moves the in-scene superego** (C1 on SUPEREGO, p < 0.05, direction not predicted): 15 of 39 models up, sign p = 0.2 -> **NOT SUPPORTED**.
- **FY-2, being addressed installs refusal** (C2 on REFUSAL > 0, p < 0.05): 32 of 38 up, sign p = 2.43e-05 -> **SUPPORTED**.
- **FY-3, refusal displaces the superego** (majority fall, p < 0.05): 17 of 31, p = 0.72 -> **NOT SUPPORTED**.

## Ladders (descriptive)

| ladder | rung | superego raw / prefill / continue | refusal raw / prefill / continue |
|---|---|---|---|
| OLMo-2-1B | `OLMo-2-0425-1B-SFT` | 27.1 / 11.5 / 24.8 | 0.6 / 1.8 / 12.3 |
| OLMo-2-1B | `OLMo-2-0425-1B-DPO` | 27.4 / 31.0 / 18.3 | 0.0 / 1.9 / 11.1 |
| OLMo-2-1B | `OLMo-2-0425-1B-Instruct` | 30.1 / 24.7 / 17.3 | 0.0 / 1.7 / 8.9 |
| OLMoE | `OLMoE-1B-7B-0125-SFT` | 24.2 / 25.0 / 33.3 | 0.4 / 0.1 / 6.3 |
| OLMoE | `OLMoE-1B-7B-0125-DPO` | 25.5 / 15.2 / 20.5 | 0.6 / 0.0 / 5.4 |
| OLMoE | `OLMoE-1B-7B-0125-Instruct` | 28.5 / 20.3 / 23.7 | 0.5 / 0.3 / 6.4 |
| Olmo-3-7B | `Olmo-3-7B-Instruct-SFT` | 20.5 / 17.3 / 14.3 | 0.9 / 0.3 / 44.9 |
| Olmo-3-7B | `Olmo-3-7B-Instruct-DPO` | 14.5 / 18.0 / 50.0 | 2.1 / 4.2 / 65.6 |
| Olmo-3-7B | `Olmo-3-7B-Instruct` | 21.6 / 18.6 / 100.0 | 3.2 / 5.4 / 66.8 |
| neo | `neo_7b_sft_v0.1` | 17.9 / 20.4 / 12.6 | 1.0 / 1.4 / 53.0 |
| neo | `neo_7b_instruct_v0.1` | 26.7 / 21.7 / 8.3 | 1.0 / 5.0 / 48.5 |
| Tulu | `Llama-3.1-Tulu-3-8B-SFT` | 24.0 / 24.1 / 22.1 | 0.7 / 0.0 / 17.7 |
| Tulu | `Llama-3.1-Tulu-3-8B-DPO` | 27.8 / 25.6 / 20.8 | 0.6 / 0.5 / 23.0 |
