# superego_stages: which stage installs the in-scene superego?

Producer `analyse.py`, the analysis registered in README.md (47f22c0a) before any new rung was generated. Measure: SUPEREGO_IN_SCENE given sexual_scene, pass A, in points.

**Sanity check against Y's headline** (15.18 -> 21.60): this file's per-model rule on Y's store gives mean 15.18 -> 21.60 over 32 pairs.

## Per model

| ladder | rung | model | superego given scene | SE | scenes | passages | source |
|---|---|---|---|---|---|---|---|
| pythia-2.8b | base | `EleutherAI/pythia-2.8b` | 19.4 | 2.0 | 396 | 678 | Y |
| pythia-2.8b | rung 1 | `ContextualAI/archangel_sft_pythia2-8b` | 21.6 | 2.0 | 435 | 680 | superego_stages |
| pythia-2.8b | rung 2 | `ContextualAI/archangel_sft-dpo_pythia2-8b` | 20.7 | 1.9 | 450 | 679 | Y |
| pythia-6.9b | base | `EleutherAI/pythia-6.9b` | 20.5 | 2.0 | 424 | 680 | Y |
| pythia-6.9b | rung 1 | `lomahony/eleuther-pythia6.9b-hh-sft` | 25.9 | 2.1 | 437 | 680 | superego_stages |
| pythia-6.9b | rung 2 | `lomahony/eleuther-pythia6.9b-hh-dpo` | 34.6 | 2.3 | 437 | 680 | Y |
| Amber | base | `LLM360/Amber` | 8.6 | 1.4 | 409 | 628 | Y |
| Amber | rung 1 | `LLM360/AmberChat` | 19.0 | 1.9 | 426 | 644 | superego_stages |
| Amber | rung 2 | `LLM360/AmberSafe` | 48.3 | 3.1 | 261 | 634 | Y |
| OLMo-2-1B | base | `allenai/OLMo-2-0425-1B` | 10.0 | 1.6 | 339 | 675 | Y |
| OLMo-2-1B | rung 1 | `allenai/OLMo-2-0425-1B-SFT` | 27.1 | 2.6 | 295 | 678 | superego_stages |
| OLMo-2-1B | rung 2 | `allenai/OLMo-2-0425-1B-DPO` | 27.4 | 2.4 | 358 | 679 | Y |
| OLMo-2-1B | RLVR | `allenai/OLMo-2-0425-1B-Instruct` | 30.1 | 2.5 | 346 | 675 | superego_stages |
| OLMoE | base | `allenai/OLMoE-1B-7B-0125` | 21.4 | 2.1 | 387 | 678 | Y |
| OLMoE | rung 1 | `allenai/OLMoE-1B-7B-0125-SFT` | 24.2 | 2.2 | 368 | 678 | superego_stages |
| OLMoE | rung 2 | `allenai/OLMoE-1B-7B-0125-DPO` | 25.5 | 2.1 | 423 | 680 | Y |
| OLMoE | RLVR | `allenai/OLMoE-1B-7B-0125-Instruct` | 28.5 | 2.2 | 431 | 680 | superego_stages |
| Olmo-3-7B | base | `allenai/Olmo-3-1025-7B` | 20.8 | 2.0 | 399 | 645 | Y |
| Olmo-3-7B | rung 1 | `allenai/Olmo-3-7B-Instruct-SFT` | 20.5 | 2.5 | 268 | 632 | superego_stages |
| Olmo-3-7B | rung 2 | `allenai/Olmo-3-7B-Instruct-DPO` | 14.5 | 1.9 | 338 | 645 | Y |
| Olmo-3-7B | RLVR | `allenai/Olmo-3-7B-Instruct` | 21.6 | 2.2 | 352 | 646 | superego_stages |
| CT-LLM | base | `m-a-p/CT-LLM-Base` | 5.9 | 1.4 | 270 | 666 | Y |
| CT-LLM | rung 1 | `m-a-p/CT-LLM-SFT` | 21.9 | 2.3 | 324 | 677 | superego_stages |
| CT-LLM | rung 2 | `m-a-p/CT-LLM-SFT-DPO` | 20.8 | 2.4 | 284 | 676 | Y |
| neo | base | `m-a-p/neo_7b` | 22.2 | 2.6 | 261 | 675 | Y |
| neo | rung 1 | `m-a-p/neo_7b_sft_v0.1` | 17.9 | 2.6 | 212 | 677 | superego_stages |
| neo | rung 2 | `m-a-p/neo_7b_instruct_v0.1` | 26.7 | 2.8 | 258 | 678 | Y |
| Tulu | base | `meta-llama/Llama-3.1-8B` | 14.7 | 1.8 | 389 | 670 | Y |
| Tulu | rung 1 | `allenai/Llama-3.1-Tulu-3-8B-SFT` | 24.0 | 2.3 | 338 | 617 | superego_stages |
| Tulu | rung 2 | `allenai/Llama-3.1-Tulu-3-8B-DPO` | 27.8 | 2.2 | 425 | 676 | superego_stages |
| beaver | base | `huggyllama/llama-7b` | 18.4 | 1.9 | 402 | 677 | superego_stages |
| beaver | rung 1 | `PKU-Alignment/alpaca-7b-reproduced` | 8.5 | 1.3 | 470 | 679 | superego_stages |
| beaver | rung 2 | `PKU-Alignment/beaver-7b-v1.0` | 9.0 | 1.3 | 465 | 680 | superego_stages |

## Per ladder

| ladder | steps | base | rung 1 | rung 2 | step1 | step2 | total | SFT share | step3 (RLVR) |
|---|---|---|---|---|---|---|---|---|---|
| pythia-2.8b | SFT, DPO | 19.4 | 21.6 | 20.7 | +2.2 | -0.9 | +1.2 | 1.77 |  |
| pythia-6.9b | SFT, DPO | 20.5 | 25.9 | 34.6 | +5.3 | +8.7 | +14.0 | 0.38 |  |
| Amber | chat SFT, safety SFT | 8.6 | 19.0 | 48.3 | +10.5 | +29.3 | +39.7 | 0.26 |  |
| OLMo-2-1B | SFT, DPO, RLVR | 10.0 | 27.1 | 27.4 | +17.1 | +0.3 | +17.3 | 0.99 | +2.7 (SE 3.4) |
| OLMoE | SFT, DPO, RLVR | 21.4 | 24.2 | 25.5 | +2.7 | +1.3 | +4.1 | 0.67 | +3.0 (SE 3.0) |
| Olmo-3-7B | SFT, DPO, RLVR | 20.8 | 20.5 | 14.5 | -0.3 | -6.0 | -6.3 | -- (total <= 0) | +7.1 (SE 2.9) |
| CT-LLM | SFT, DPO | 5.9 | 21.9 | 20.8 | +16.0 | -1.1 | +14.8 | 1.08 |  |
| neo | SFT, preference | 22.2 | 17.9 | 26.7 | -4.3 | +8.8 | +4.5 | -0.95 |  |
| Tulu | SFT, DPO | 14.7 | 24.0 | 27.8 | +9.3 | +3.8 | +13.1 | 0.71 |  |
| beaver | SFT, safe-RLHF | 18.4 | 8.5 | 9.0 | -9.9 | +0.5 | -9.4 | -- (total <= 0) |  |

## The registered readings

- **SFT step (step1 > 0):** 7 of 10 ladders positive, median +4.0, mean +4.9; Wilcoxon p = 0.131, sign p = 0.344.
- **Second step (step2 > 0):** 7 of 10 positive, median +0.9, mean +4.5; Wilcoxon p = 0.193, sign p = 0.344.
- **SFT share** over the 8 ladders with total > 0: median 0.69, bootstrap 95% interval [0.26, 1.08] (10000 resamples of ladders, seed 20260924).
- **Verdict (rule fixed in the registration):** **Neither condition of the verdict rule is met**; reported as the interval: median SFT share 0.69 [0.26, 1.08].

## Per-ladder readings (declared: Amber, OLMo-2-1B, CT-LLM, pythia-6.9b-hh)

| ladder | step1 (SE) | step2 (SE) | total (SE) |
|---|---|---|---|
| pythia-6.9b | +5.3 (2.9) | +8.7 (3.1) | +14.0 (3.0) |
| Amber | +10.5 (2.4) | +29.3 (3.6) | +39.7 (3.4) |
| OLMo-2-1B | +17.1 (3.1) | +0.3 (3.5) | +17.3 (2.9) |
| CT-LLM | +16.0 (2.7) | -1.1 (3.3) | +14.8 (2.8) |

Amber's split is chat SFT (AmberChat) against safety SFT (AmberSafe), as declared.

## RLVR (step3), descriptive, three OLMo ladders

- OLMo-2-1B: +2.7 (SE 3.4)
- OLMoE: +3.0 (SE 3.0)
- Olmo-3-7B: +7.1 (SE 2.9)
