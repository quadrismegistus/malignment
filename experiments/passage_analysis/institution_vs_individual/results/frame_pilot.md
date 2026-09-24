# Frame pilot: decomposition of the base-to-aligned shift

Registration `frame_pilot.md`; producer `frame_pilot.py`. Aligned-raw passages: 2880 coded of 2880.

## Form: share of passages in advice form

| lineage (aligned model) | base raw | aligned raw | aligned chat |
|---|---|---|---|
| AmberSafe | 0.03 | 0.66 | 0.98 |
| AquilaChat2-7B | 0.07 | 0.30 | 0.46 |
| CT-LLM-SFT-DPO | 0.00 | 0.34 | -- |
| RedPajama-INCITE-7B-Chat | 0.03 | 0.30 | 0.74 |
| archangel_sft-dpo_pythia2-8b | 0.01 | 0.04 | 0.08 |
| beaver-7b-v1.0 | 0.16 | 0.62 | 0.86 |
| bloomz-7b1 | 0.04 | 0.01 | -- |
| eleuther-pythia6.9b-hh-dpo | 0.02 | 0.11 | 0.69 |

**E1** (aligned-raw writes advice less often than aligned-chat, declared >= 5 of 6): 6 of 6 -> MET

## channel (PRIMARY)

| lineage | weights (raw -> raw) | frame (raw -> chat, aligned) | total (base raw -> aligned chat) |
|---|---|---|---|
| AmberSafe | +0.229 | +0.146 | +0.374 |
| AquilaChat2-7B | +0.092 | +0.072 | +0.165 |
| CT-LLM-SFT-DPO | -- | -- | -- |
| RedPajama-INCITE-7B-Chat | +0.054 | +0.107 | +0.161 |
| archangel_sft-dpo_pythia2-8b | +0.037 | +0.069 | +0.106 |
| beaver-7b-v1.0 | +0.173 | +0.043 | +0.215 |
| bloomz-7b1 | -0.111 | -- | -- |
| eleuther-pythia6.9b-hh-dpo | -0.075 | +0.222 | +0.147 |

weights > 0 in 5 of 7 lineages (sign p 0.453); median weights +0.054.
frame > weights in 3 of 6 three-cell lineages; median frame +0.090.

**E2** (channel weights > 0, declared >= 6 of 8): 5 of 7 -> NOT MET
**Decomposition verdict (declared rule, 5 of 6):** mixed.

## outward

| lineage | weights (raw -> raw) | frame (raw -> chat, aligned) | total (base raw -> aligned chat) |
|---|---|---|---|
| AmberSafe | +0.200 | +0.106 | +0.307 |
| AquilaChat2-7B | -0.019 | +0.092 | +0.073 |
| CT-LLM-SFT-DPO | -- | -- | -- |
| RedPajama-INCITE-7B-Chat | -0.037 | +0.105 | +0.069 |
| archangel_sft-dpo_pythia2-8b | -0.075 | +0.135 | +0.060 |
| beaver-7b-v1.0 | +0.161 | +0.074 | +0.236 |
| bloomz-7b1 | +0.027 | -- | -- |
| eleuther-pythia6.9b-hh-dpo | -0.018 | +0.200 | +0.182 |

weights > 0 in 3 of 7 lineages (sign p 1); median weights -0.018.
frame > weights in 4 of 6 three-cell lineages; median frame +0.106.

## authority

| lineage | weights (raw -> raw) | frame (raw -> chat, aligned) | total (base raw -> aligned chat) |
|---|---|---|---|
| AmberSafe | +0.125 | +0.171 | +0.297 |
| AquilaChat2-7B | +0.054 | +0.155 | +0.209 |
| CT-LLM-SFT-DPO | -- | -- | -- |
| RedPajama-INCITE-7B-Chat | -0.082 | +0.162 | +0.080 |
| archangel_sft-dpo_pythia2-8b | +0.016 | -0.001 | +0.015 |
| beaver-7b-v1.0 | +0.099 | +0.085 | +0.185 |
| bloomz-7b1 | +0.018 | -- | -- |
| eleuther-pythia6.9b-hh-dpo | -0.106 | +0.171 | +0.065 |

weights > 0 in 5 of 7 lineages (sign p 0.453); median weights +0.018.
frame > weights in 4 of 6 three-cell lineages; median frame +0.158.

## move_voice_direct

| lineage | weights (raw -> raw) | frame (raw -> chat, aligned) | total (base raw -> aligned chat) |
|---|---|---|---|
| AmberSafe | -0.251 | -0.119 | -0.370 |
| AquilaChat2-7B | -0.057 | -0.149 | -0.206 |
| CT-LLM-SFT-DPO | -- | -- | -- |
| RedPajama-INCITE-7B-Chat | -0.128 | -0.179 | -0.307 |
| archangel_sft-dpo_pythia2-8b | -0.330 | +0.384 | +0.054 |
| beaver-7b-v1.0 | -0.185 | +0.155 | -0.030 |
| bloomz-7b1 | -0.035 | -- | -- |
| eleuther-pythia6.9b-hh-dpo | -0.091 | +0.131 | +0.039 |

weights > 0 in 0 of 7 lineages (sign p 0.0156); median weights -0.128.
frame > weights in 4 of 6 three-cell lineages; median frame +0.006.

## Empty cells

- CT-LLM-SFT-DPO: kept passages per cell base/indi 0, base/inst 1, aligned_raw/indi 66, aligned_raw/inst 59, aligned_chat/indi 0, aligned_chat/inst 0. A DiD needs all four of its cells, so it is undefined here, and the lineage drops out of that count.
- bloomz-7b1 and CT-LLM-SFT-DPO have no aligned-chat cell by design (no chat template).

Cells: mean of the outcome over kept passages (continuation or advice, coherent, perspective kept).
Each DiD = (individual change) - (institution change). total = weights + frame exactly (asserted).
Six lineages for the decomposition, eight for weights: descriptive; see the registration's limits.
