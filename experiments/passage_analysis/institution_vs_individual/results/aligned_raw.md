# Aligned raw: weights against frame over every lineage

Registration `aligned_raw.md` (459f6c97); producer `aligned_raw.py`, written before the data. Source `coded_aligned_raw.jsonl`: 15480 rows, 15479 coded, over 43 of the 43 lineages.

**Determinism check (reported, not pooled):** the frame pilot's accidental raw passages against the new ones on the same model, prompt and seed: 872 of 2160 texts identical.

## E1: form

Aligned-raw writes advice less often than aligned-chat in 39 of 43 lineages (fewer: 3; sign p 5.63e-09) -> **MET**.
Median advice share: base 0.07, aligned raw 0.46, aligned chat 0.92.

## channel (PRIMARY), lineages

Defined in 42 lineages. Median weights +0.118, frame +0.221, total +0.348 (raw DiDs).
- weights in the declared direction: 38 of 42 (against 2; sign p 1.49e-09) -> **E2 MET**
- frame beyond weights: 27 of 42 (weights beyond frame 15; sign p 0.0884) -> **mixed**
- median share weights / total, over the 41 lineages where total moved the declared way: 0.37

| lineage (aligned model) | weights | frame | total | kept base i/s | kept raw i/s | kept chat i/s |
|---|---|---|---|---|---|---|
| AmberSafe | +0.239 | +0.135 | +0.374 | 18/18 | 160/118 | 156/101 |
| AquilaChat2-7B | +0.104 | +0.061 | +0.165 | 20/12 | 151/109 | 115/112 |
| Baichuan2-7B-Chat | +0.264 | +0.183 | +0.447 | 19/19 | 132/130 | 166/134 |
| CroissantLLMChat-v0.1 | +0.172 | +0.111 | +0.283 | 12/2 | 50/44 | 49/43 |
| Falcon-H1-1.5B-Instruct | +0.129 | +0.224 | +0.353 | 20/23 | 105/108 | 167/147 |
| Falcon-H1-7B-Instruct | +0.176 | +0.215 | +0.391 | 44/48 | 126/121 | 159/160 |
| Falcon3-7B-Instruct | +0.162 | +0.217 | +0.380 | 21/22 | 139/115 | 168/151 |
| Llama-3.1-70B-Instruct | +0.273 | +0.286 | +0.559 | 109/59 | 131/57 | 151/162 |
| Llama-3.1-8B-Instruct | +0.075 | +0.387 | +0.461 | 87/69 | 103/69 | 169/153 |
| Lucie-7B-Instruct-v1.1 | +0.428 | -0.219 | +0.209 | 17/7 | 37/20 | 155/115 |
| MiniCPM5-1B | +0.231 | -0.116 | +0.114 | 5/7 | 13/12 | 35/14 |
| Mistral-7B-Instruct-v0.1 | +0.204 | +0.226 | +0.430 | 98/92 | 158/126 | 165/141 |
| OLMo-2-0425-1B-Instruct | +0.185 | +0.313 | +0.498 | 19/20 | 119/80 | 172/120 |
| OLMoE-1B-7B-0125-Instruct | +0.280 | +0.122 | +0.402 | 36/37 | 133/86 | 169/150 |
| Olmo-3-7B-Instruct | +0.018 | +0.316 | +0.334 | 55/32 | 63/62 | 170/129 |
| Olmo-3.1-32B-Instruct | +0.103 | +0.382 | +0.485 | 77/46 | 115/93 | 177/152 |
| Qwen2.5-0.5B-Instruct | -0.083 | +0.226 | +0.143 | 9/6 | 16/9 | 97/69 |
| Qwen2.5-7B-Instruct | +0.198 | +0.260 | +0.458 | 79/45 | 124/83 | 177/160 |
| Qwen3-8B | +0.027 | -0.062 | -0.035 | 79/63 | 131/107 | 133/112 |
| RedPajama-INCITE-7B-Chat | +0.106 | +0.055 | +0.161 | 12/10 | 67/76 | 116/89 |
| SmolLM2-360M-Instruct | +0.018 | +0.201 | +0.219 | 2/1 | 55/59 | 40/36 |
| SmolLM3-3B | +0.012 | +0.193 | +0.205 | 77/58 | 113/114 | 134/128 |
| Tanuki-8B-dpo-v1.0 | +0.155 | +0.251 | +0.406 | 4/5 | 40/50 | 149/112 |
| TinyLlama-1.1B-Chat-v1.0 | +0.000 | +0.300 | +0.300 | 11/7 | 23/36 | 87/91 |
| Yi-1.5-9B-Chat | +0.049 | +0.293 | +0.342 | 46/24 | 115/99 | 155/161 |
| Zamba2-7B-Instruct | +0.078 | +0.475 | +0.553 | 82/68 | 110/78 | 173/155 |
| archangel_sft-dpo_pythia2-8b | +0.000 | +0.106 | +0.106 | 11/9 | 25/24 | 29/45 |
| beaver-7b-v1.0 | +0.172 | +0.043 | +0.215 | 67/64 | 134/107 | 140/100 |
| deepseek-llm-7b-chat | +0.059 | +0.352 | +0.411 | 76/67 | 142/141 | 162/156 |
| eleuther-pythia6.9b-hh-dpo | -0.032 | +0.180 | +0.147 | 18/10 | 84/79 | 58/47 |
| falcon-7b-instruct | +0.189 | +0.066 | +0.255 | 51/51 | 109/92 | 61/71 |
| falcon-mamba-7b-instruct | +0.041 | +0.261 | +0.302 | 81/65 | 91/83 | 140/111 |
| gemma-2-9b-it | +0.212 | +0.186 | +0.398 | 121/95 | 167/109 | 180/148 |
| glm-4-9b-chat-hf | +0.073 | +0.230 | +0.302 | 106/129 | 124/135 | 171/162 |
| granite-3.0-8b-instruct | +0.092 | +0.276 | +0.368 | 39/24 | 128/115 | 174/168 |
| internlm2-chat-7b | -- | -- | -- | 0/0 | 0/0 | 0/0 |
| jais-family-6p7b-chat | +0.055 | +0.397 | +0.452 | 16/18 | 89/78 | 146/137 |
| kanana-1.5-8b-instruct-2505 | +0.224 | +0.178 | +0.402 | 36/23 | 137/66 | 171/157 |
| kanana-2-3b-instruct | +0.094 | +0.226 | +0.321 | 50/41 | 90/60 | 160/123 |
| llm-jp-3-7.2b-instruct3 | +0.243 | +0.041 | +0.284 | 97/73 | 142/123 | 169/154 |
| neo_7b_instruct_v0.1 | +0.162 | +0.294 | +0.457 | 4/4 | 135/126 | 174/147 |
| salamandra-7b-instruct | +0.043 | +0.020 | +0.063 | 45/50 | 85/67 | 93/101 |
| stablelm-2-1_6b-chat | +0.159 | +0.283 | +0.442 | 29/32 | 156/121 | 159/143 |

## outward (secondary), lineages

Defined in 42 lineages. Median weights +0.075, frame +0.099, total +0.174 (raw DiDs).
- weights in the declared direction: 34 of 42 (against 7; sign p 2.53e-05)
- frame beyond weights: 20 of 42 (weights beyond frame 22; sign p 0.878) -> **mixed**
- median share weights / total, over the 40 lineages where total moved the declared way: 0.48

| lineage (aligned model) | weights | frame | total | kept base i/s | kept raw i/s | kept chat i/s |
|---|---|---|---|---|---|---|
| AmberSafe | +0.237 | +0.069 | +0.307 | 18/18 | 160/118 | 156/101 |
| AquilaChat2-7B | +0.012 | +0.061 | +0.073 | 20/12 | 151/109 | 115/112 |
| Baichuan2-7B-Chat | +0.370 | +0.067 | +0.437 | 19/19 | 132/130 | 166/134 |
| CroissantLLMChat-v0.1 | +0.071 | -0.017 | +0.054 | 12/2 | 50/44 | 49/43 |
| Falcon-H1-1.5B-Instruct | +0.048 | -0.006 | +0.042 | 20/23 | 105/108 | 167/147 |
| Falcon-H1-7B-Instruct | +0.093 | -0.021 | +0.072 | 44/48 | 126/121 | 159/160 |
| Falcon3-7B-Instruct | +0.125 | +0.057 | +0.182 | 21/22 | 139/115 | 168/151 |
| Llama-3.1-70B-Instruct | +0.265 | +0.236 | +0.501 | 109/59 | 131/57 | 151/162 |
| Llama-3.1-8B-Instruct | +0.123 | +0.120 | +0.244 | 87/69 | 103/69 | 169/153 |
| Lucie-7B-Instruct-v1.1 | +0.003 | -0.079 | -0.075 | 17/7 | 37/20 | 155/115 |
| MiniCPM5-1B | +0.147 | -0.119 | +0.029 | 5/7 | 13/12 | 35/14 |
| Mistral-7B-Instruct-v0.1 | +0.080 | +0.147 | +0.227 | 98/92 | 158/126 | 165/141 |
| OLMo-2-0425-1B-Instruct | -0.075 | +0.237 | +0.161 | 19/20 | 119/80 | 172/120 |
| OLMoE-1B-7B-0125-Instruct | +0.137 | +0.059 | +0.196 | 36/37 | 133/86 | 169/150 |
| Olmo-3-7B-Instruct | +0.105 | +0.132 | +0.236 | 55/32 | 63/62 | 170/129 |
| Olmo-3.1-32B-Instruct | +0.047 | +0.120 | +0.167 | 77/46 | 115/93 | 177/152 |
| Qwen2.5-0.5B-Instruct | +0.201 | -0.101 | +0.101 | 9/6 | 16/9 | 97/69 |
| Qwen2.5-7B-Instruct | +0.021 | +0.317 | +0.338 | 79/45 | 124/83 | 177/160 |
| Qwen3-8B | +0.051 | -0.143 | -0.092 | 79/63 | 131/107 | 133/112 |
| RedPajama-INCITE-7B-Chat | -0.030 | +0.099 | +0.069 | 12/10 | 67/76 | 116/89 |
| SmolLM2-360M-Instruct | +0.000 | +0.169 | +0.169 | 2/1 | 55/59 | 40/36 |
| SmolLM3-3B | +0.096 | -0.029 | +0.066 | 77/58 | 113/114 | 134/128 |
| Tanuki-8B-dpo-v1.0 | +0.035 | +0.225 | +0.260 | 4/5 | 40/50 | 149/112 |
| TinyLlama-1.1B-Chat-v1.0 | +0.130 | -0.049 | +0.081 | 11/7 | 23/36 | 87/91 |
| Yi-1.5-9B-Chat | -0.048 | +0.215 | +0.168 | 46/24 | 115/99 | 155/161 |
| Zamba2-7B-Instruct | +0.060 | +0.274 | +0.334 | 82/68 | 110/78 | 173/155 |
| archangel_sft-dpo_pythia2-8b | -0.062 | +0.121 | +0.060 | 11/9 | 25/24 | 29/45 |
| beaver-7b-v1.0 | +0.159 | +0.077 | +0.236 | 67/64 | 134/107 | 140/100 |
| deepseek-llm-7b-chat | +0.119 | +0.215 | +0.334 | 76/67 | 142/141 | 162/156 |
| eleuther-pythia6.9b-hh-dpo | +0.055 | +0.128 | +0.182 | 18/10 | 84/79 | 58/47 |
| falcon-7b-instruct | -0.004 | +0.135 | +0.131 | 51/51 | 109/92 | 61/71 |
| falcon-mamba-7b-instruct | +0.053 | +0.201 | +0.254 | 81/65 | 91/83 | 140/111 |
| gemma-2-9b-it | +0.064 | +0.156 | +0.219 | 121/95 | 167/109 | 180/148 |
| glm-4-9b-chat-hf | +0.080 | +0.100 | +0.179 | 106/129 | 124/135 | 171/162 |
| granite-3.0-8b-instruct | +0.166 | +0.088 | +0.254 | 39/24 | 128/115 | 174/168 |
| internlm2-chat-7b | -- | -- | -- | 0/0 | 0/0 | 0/0 |
| jais-family-6p7b-chat | -0.080 | +0.121 | +0.041 | 16/18 | 89/78 | 146/137 |
| kanana-1.5-8b-instruct-2505 | -0.014 | +0.122 | +0.108 | 36/23 | 137/66 | 171/157 |
| kanana-2-3b-instruct | +0.259 | -0.149 | +0.110 | 50/41 | 90/60 | 160/123 |
| llm-jp-3-7.2b-instruct3 | +0.157 | +0.118 | +0.274 | 97/73 | 142/123 | 169/154 |
| neo_7b_instruct_v0.1 | +0.116 | +0.066 | +0.182 | 4/4 | 135/126 | 174/147 |
| salamandra-7b-instruct | +0.010 | +0.003 | +0.014 | 45/50 | 85/67 | 93/101 |
| stablelm-2-1_6b-chat | +0.109 | +0.084 | +0.194 | 29/32 | 156/121 | 159/143 |

## authority (secondary), lineages

Defined in 42 lineages. Median weights +0.043, frame +0.099, total +0.160 (raw DiDs).
- weights in the declared direction: 31 of 42 (against 11; sign p 0.00289)
- frame beyond weights: 25 of 42 (weights beyond frame 17; sign p 0.28) -> **mixed**
- median share weights / total, over the 38 lineages where total moved the declared way: 0.33

| lineage (aligned model) | weights | frame | total | kept base i/s | kept raw i/s | kept chat i/s |
|---|---|---|---|---|---|---|
| AmberSafe | +0.164 | +0.132 | +0.297 | 18/18 | 160/118 | 156/101 |
| AquilaChat2-7B | +0.066 | +0.143 | +0.209 | 20/12 | 151/109 | 115/112 |
| Baichuan2-7B-Chat | +0.423 | +0.021 | +0.444 | 19/19 | 132/130 | 166/134 |
| CroissantLLMChat-v0.1 | +0.132 | +0.046 | +0.178 | 12/2 | 50/44 | 49/43 |
| Falcon-H1-1.5B-Instruct | -0.112 | +0.062 | -0.050 | 20/23 | 105/108 | 167/147 |
| Falcon-H1-7B-Instruct | +0.031 | +0.065 | +0.095 | 44/48 | 126/121 | 159/160 |
| Falcon3-7B-Instruct | +0.005 | +0.179 | +0.184 | 21/22 | 139/115 | 168/151 |
| Llama-3.1-70B-Instruct | +0.245 | +0.110 | +0.355 | 109/59 | 131/57 | 151/162 |
| Llama-3.1-8B-Instruct | +0.093 | +0.131 | +0.224 | 87/69 | 103/69 | 169/153 |
| Lucie-7B-Instruct-v1.1 | -0.024 | -0.073 | -0.097 | 17/7 | 37/20 | 155/115 |
| MiniCPM5-1B | +0.218 | -0.161 | +0.057 | 5/7 | 13/12 | 35/14 |
| Mistral-7B-Instruct-v0.1 | +0.043 | +0.151 | +0.194 | 98/92 | 158/126 | 165/141 |
| OLMo-2-0425-1B-Instruct | -0.095 | +0.236 | +0.141 | 19/20 | 119/80 | 172/120 |
| OLMoE-1B-7B-0125-Instruct | +0.122 | +0.037 | +0.159 | 36/37 | 133/86 | 169/150 |
| Olmo-3-7B-Instruct | +0.113 | +0.139 | +0.252 | 55/32 | 63/62 | 170/129 |
| Olmo-3.1-32B-Instruct | +0.034 | +0.126 | +0.160 | 77/46 | 115/93 | 177/152 |
| Qwen2.5-0.5B-Instruct | +0.139 | -0.032 | +0.107 | 9/6 | 16/9 | 97/69 |
| Qwen2.5-7B-Instruct | -0.021 | +0.270 | +0.249 | 79/45 | 124/83 | 177/160 |
| Qwen3-8B | -0.040 | -0.038 | -0.079 | 79/63 | 131/107 | 133/112 |
| RedPajama-INCITE-7B-Chat | -0.096 | +0.176 | +0.080 | 12/10 | 67/76 | 116/89 |
| SmolLM2-360M-Instruct | -0.017 | +0.003 | -0.014 | 2/1 | 55/59 | 40/36 |
| SmolLM3-3B | +0.047 | -0.007 | +0.040 | 77/58 | 113/114 | 134/128 |
| Tanuki-8B-dpo-v1.0 | +0.025 | +0.190 | +0.215 | 4/5 | 40/50 | 149/112 |
| TinyLlama-1.1B-Chat-v1.0 | +0.130 | -0.037 | +0.093 | 11/7 | 23/36 | 87/91 |
| Yi-1.5-9B-Chat | -0.053 | +0.212 | +0.159 | 46/24 | 115/99 | 155/161 |
| Zamba2-7B-Instruct | +0.017 | +0.283 | +0.300 | 82/68 | 110/78 | 173/155 |
| archangel_sft-dpo_pythia2-8b | +0.029 | -0.014 | +0.015 | 11/9 | 25/24 | 29/45 |
| beaver-7b-v1.0 | +0.097 | +0.088 | +0.185 | 67/64 | 134/107 | 140/100 |
| deepseek-llm-7b-chat | +0.112 | +0.224 | +0.336 | 76/67 | 142/141 | 162/156 |
| eleuther-pythia6.9b-hh-dpo | -0.057 | +0.122 | +0.065 | 18/10 | 84/79 | 58/47 |
| falcon-7b-instruct | -0.023 | +0.135 | +0.112 | 51/51 | 109/92 | 61/71 |
| falcon-mamba-7b-instruct | +0.040 | +0.170 | +0.209 | 81/65 | 91/83 | 140/111 |
| gemma-2-9b-it | +0.022 | +0.195 | +0.217 | 121/95 | 167/109 | 180/148 |
| glm-4-9b-chat-hf | +0.153 | +0.026 | +0.179 | 106/129 | 124/135 | 171/162 |
| granite-3.0-8b-instruct | +0.047 | +0.096 | +0.143 | 39/24 | 128/115 | 174/168 |
| internlm2-chat-7b | -- | -- | -- | 0/0 | 0/0 | 0/0 |
| jais-family-6p7b-chat | -0.042 | +0.130 | +0.089 | 16/18 | 89/78 | 146/137 |
| kanana-1.5-8b-instruct-2505 | +0.183 | +0.090 | +0.274 | 36/23 | 137/66 | 171/157 |
| kanana-2-3b-instruct | +0.194 | -0.087 | +0.107 | 50/41 | 90/60 | 160/123 |
| llm-jp-3-7.2b-instruct3 | +0.152 | +0.101 | +0.253 | 97/73 | 142/123 | 169/154 |
| neo_7b_instruct_v0.1 | +0.123 | +0.087 | +0.211 | 4/4 | 135/126 | 174/147 |
| salamandra-7b-instruct | +0.033 | +0.067 | +0.101 | 45/50 | 85/67 | 93/101 |
| stablelm-2-1_6b-chat | +0.042 | +0.093 | +0.135 | 29/32 | 156/121 | 159/143 |

## move_voice_direct (secondary), lineages

Defined in 42 lineages. Median weights -0.133, frame -0.126, total -0.271 (raw DiDs). Verdicts on -DiD (the declared direction is negative).
- weights in the declared direction: 32 of 42 (against 10; sign p 0.000941)
- frame beyond weights: 21 of 42 (weights beyond frame 21; sign p 1) -> **mixed**
- median share weights / total, over the 38 lineages where total moved the declared way: 0.48

| lineage (aligned model) | weights | frame | total | kept base i/s | kept raw i/s | kept chat i/s |
|---|---|---|---|---|---|---|
| AmberSafe | -0.228 | -0.142 | -0.370 | 18/18 | 160/118 | 156/101 |
| AquilaChat2-7B | -0.035 | -0.171 | -0.206 | 20/12 | 151/109 | 115/112 |
| Baichuan2-7B-Chat | -0.208 | -0.029 | -0.237 | 19/19 | 132/130 | 166/134 |
| CroissantLLMChat-v0.1 | -0.283 | -0.095 | -0.379 | 12/2 | 50/44 | 49/43 |
| Falcon-H1-1.5B-Instruct | -0.402 | -0.119 | -0.521 | 20/23 | 105/108 | 167/147 |
| Falcon-H1-7B-Instruct | -0.052 | -0.167 | -0.219 | 44/48 | 126/121 | 159/160 |
| Falcon3-7B-Instruct | -0.117 | -0.107 | -0.224 | 21/22 | 139/115 | 168/151 |
| Llama-3.1-70B-Instruct | -0.224 | -0.146 | -0.369 | 109/59 | 131/57 | 151/162 |
| Llama-3.1-8B-Instruct | -0.064 | -0.234 | -0.298 | 87/69 | 103/69 | 169/153 |
| Lucie-7B-Instruct-v1.1 | +0.144 | -0.509 | -0.365 | 17/7 | 37/20 | 155/115 |
| MiniCPM5-1B | +0.168 | -0.439 | -0.271 | 5/7 | 13/12 | 35/14 |
| Mistral-7B-Instruct-v0.1 | -0.262 | -0.108 | -0.370 | 98/92 | 158/126 | 165/141 |
| OLMo-2-0425-1B-Instruct | -0.057 | -0.152 | -0.210 | 19/20 | 119/80 | 172/120 |
| OLMoE-1B-7B-0125-Instruct | -0.186 | -0.124 | -0.310 | 36/37 | 133/86 | 169/150 |
| Olmo-3-7B-Instruct | -0.149 | -0.086 | -0.235 | 55/32 | 63/62 | 170/129 |
| Olmo-3.1-32B-Instruct | -0.363 | -0.127 | -0.491 | 77/46 | 115/93 | 177/152 |
| Qwen2.5-0.5B-Instruct | +0.431 | -0.276 | +0.155 | 9/6 | 16/9 | 97/69 |
| Qwen2.5-7B-Instruct | +0.023 | -0.355 | -0.332 | 79/45 | 124/83 | 177/160 |
| Qwen3-8B | -0.116 | +0.207 | +0.091 | 79/63 | 131/107 | 133/112 |
| RedPajama-INCITE-7B-Chat | -0.132 | -0.174 | -0.307 | 12/10 | 67/76 | 116/89 |
| SmolLM2-360M-Instruct | -0.684 | +0.064 | -0.619 | 2/1 | 55/59 | 40/36 |
| SmolLM3-3B | -0.237 | +0.179 | -0.058 | 77/58 | 113/114 | 134/128 |
| Tanuki-8B-dpo-v1.0 | -0.345 | -0.412 | -0.757 | 4/5 | 40/50 | 149/112 |
| TinyLlama-1.1B-Chat-v1.0 | -0.052 | +0.026 | -0.026 | 11/7 | 23/36 | 87/91 |
| Yi-1.5-9B-Chat | +0.012 | -0.116 | -0.103 | 46/24 | 115/99 | 155/161 |
| Zamba2-7B-Instruct | -0.017 | -0.373 | -0.390 | 82/68 | 110/78 | 173/155 |
| archangel_sft-dpo_pythia2-8b | -0.199 | +0.253 | +0.054 | 11/9 | 25/24 | 29/45 |
| beaver-7b-v1.0 | -0.203 | +0.173 | -0.030 | 67/64 | 134/107 | 140/100 |
| deepseek-llm-7b-chat | -0.134 | -0.136 | -0.270 | 76/67 | 142/141 | 162/156 |
| eleuther-pythia6.9b-hh-dpo | +0.003 | +0.036 | +0.039 | 18/10 | 84/79 | 58/47 |
| falcon-7b-instruct | +0.090 | -0.116 | -0.026 | 51/51 | 109/92 | 61/71 |
| falcon-mamba-7b-instruct | +0.037 | -0.243 | -0.205 | 81/65 | 91/83 | 140/111 |
| gemma-2-9b-it | -0.307 | -0.089 | -0.396 | 121/95 | 167/109 | 180/148 |
| glm-4-9b-chat-hf | -0.013 | -0.146 | -0.159 | 106/129 | 124/135 | 171/162 |
| granite-3.0-8b-instruct | -0.441 | -0.214 | -0.654 | 39/24 | 128/115 | 174/168 |
| internlm2-chat-7b | -- | -- | -- | 0/0 | 0/0 | 0/0 |
| jais-family-6p7b-chat | +0.062 | -0.214 | -0.151 | 16/18 | 89/78 | 146/137 |
| kanana-1.5-8b-instruct-2505 | -0.186 | -0.280 | -0.466 | 36/23 | 137/66 | 171/157 |
| kanana-2-3b-instruct | -0.180 | -0.203 | -0.383 | 50/41 | 90/60 | 160/123 |
| llm-jp-3-7.2b-instruct3 | -0.306 | -0.076 | -0.382 | 97/73 | 142/123 | 169/154 |
| neo_7b_instruct_v0.1 | -0.223 | -0.117 | -0.340 | 4/4 | 135/126 | 174/147 |
| salamandra-7b-instruct | +0.013 | -0.049 | -0.036 | 45/50 | 85/67 | 93/101 |
| stablelm-2-1_6b-chat | -0.007 | -0.081 | -0.087 | 29/32 | 156/121 | 159/143 |

## Disputes beside (18), each cell pooled over lineages

| outcome | defined | weights declared-way | frame beyond weights | median weights | median frame |
|---|---|---|---|---|---|
| channel | 18 | 16/2 (p 0.00131) | 17/1 (p 0.000145) -> frame-dominated | +0.113 | +0.217 |
| outward | 18 | 16/2 (p 0.00131) | 9/9 (p 1) -> mixed | +0.062 | +0.067 |
| authority | 18 | 13/5 (p 0.0963) | 11/7 (p 0.481) -> mixed | +0.067 | +0.098 |
| move_voice_direct | 18 | 15/3 (p 0.00754) | 8/10 (p 0.815) -> mixed | -0.086 | -0.051 |

Each DiD = (individual change) - (institution change) over kept passages (continuation or advice, coherent, perspective kept). total = weights + frame exactly (asserted). A `--` is an empty cell.
Limits are the registration's: aligned-raw is an instruction-tuned model continuing text it was not tuned to continue, and form gates the keep filter, so kept counts are printed per lineage.
