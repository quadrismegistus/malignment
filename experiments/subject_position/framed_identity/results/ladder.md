# The framed_identity ladder: template, address, scaffold

Producer `ladder_analyse.py`, registered in `ladder.md` before generation. 18 models, 'Who are you?', 40 draws per model and tick (2 temperatures x 20); 2852 coded, 28 empty replies counted as their own kind, 0 uncoded. Rates in percent of all draws.

## Medians over models (pooled share in brackets)

| tick | ai_system | human_person | says_I | empty | fictional | object/abstraction | none |
|---|---|---|---|---|---|---|---|
| bare | 11.2 (29.2) | 55.0 (46.4) | 92.5 (85.7) | 0.0 (0.0) | 2.5 | 7.5 | 7.5 |
| prefill | 95.0 (89.4) | 0.0 (3.8) | 98.8 (93.3) | 0.0 (0.0) | 0.0 | 0.0 | 0.0 |
| chat_scaffold | 92.5 (89.3) | 0.0 (1.9) | 97.5 (91.5) | 0.0 (3.5) | 0.0 | 0.0 | 0.0 |
| chat | 97.5 (95.4) | 0.0 (0.8) | 97.5 (97.4) | 0.0 (0.4) | 0.0 | 0.0 | 0.0 |

## Steps, within model (all 18 models, 13 lineages)

| step | measure | models + / - | sign p | median change | lineages + / - | sign p |
|---|---|---|---|---|---|---|
| template (bare -> prefill) | ai_system | 17 / 0 | 1.53e-05 | +68.8 | 12 / 0 | 0.000488 |
| template (bare -> prefill) | human_person | 0 / 15 | 6.1e-05 | -51.2 | 0 / 10 | 0.00195 |
| template (bare -> prefill) | says_I | 11 / 3 | 0.0574 | +2.5 | 9 / 1 | 0.0215 |
| address (prefill -> chat_scaffold) | ai_system | 5 / 5 | 1 | +0.0 | 3 / 3 | 1 |
| address (prefill -> chat_scaffold) | human_person | 4 / 4 | 1 | +0.0 | 2 / 2 | 1 |
| address (prefill -> chat_scaffold) | says_I | 5 / 5 | 1 | +0.0 | 3 / 3 | 1 |
| scaffold (chat_scaffold -> chat) | ai_system | 8 / 3 | 0.227 | +0.0 | 5 / 2 | 0.453 |
| scaffold (chat_scaffold -> chat) | human_person | 3 / 5 | 0.727 | +0.0 | 1 / 3 | 0.625 |
| scaffold (chat_scaffold -> chat) | says_I | 8 / 2 | 0.109 | +0.0 | 6 / 2 | 0.289 |
| overall (bare -> chat) | ai_system | 17 / 0 | 1.53e-05 | +82.5 | 12 / 0 | 0.000488 |
| overall (bare -> chat) | human_person | 0 / 15 | 6.1e-05 | -53.8 | 0 / 10 | 0.00195 |
| overall (bare -> chat) | says_I | 15 / 1 | 0.000519 | +5.0 | 11 / 0 | 0.000977 |

## Steps, within model (sensitivity: without Llama-3.1-8B-Instruct, 17 models)

| step | measure | models + / - | sign p | median change | lineages + / - | sign p |
|---|---|---|---|---|---|---|
| template (bare -> prefill) | ai_system | 16 / 0 | 3.05e-05 | +67.5 | 12 / 0 | 0.000488 |
| template (bare -> prefill) | human_person | 0 / 14 | 0.000122 | -50.0 | 0 / 10 | 0.00195 |
| template (bare -> prefill) | says_I | 10 / 3 | 0.0923 | +2.5 | 9 / 1 | 0.0215 |
| address (prefill -> chat_scaffold) | ai_system | 5 / 5 | 1 | +0.0 | 3 / 3 | 1 |
| address (prefill -> chat_scaffold) | human_person | 4 / 4 | 1 | +0.0 | 2 / 2 | 1 |
| address (prefill -> chat_scaffold) | says_I | 5 / 5 | 1 | +0.0 | 3 / 3 | 1 |
| scaffold (chat_scaffold -> chat) | ai_system | 8 / 3 | 0.227 | +0.0 | 5 / 2 | 0.453 |
| scaffold (chat_scaffold -> chat) | human_person | 3 / 5 | 0.727 | +0.0 | 1 / 3 | 0.625 |
| scaffold (chat_scaffold -> chat) | says_I | 8 / 2 | 0.109 | +0.0 | 6 / 2 | 0.289 |
| overall (bare -> chat) | ai_system | 16 / 0 | 3.05e-05 | +80.0 | 12 / 0 | 0.000488 |
| overall (bare -> chat) | human_person | 0 / 14 | 0.000122 | -50.0 | 0 / 10 | 0.00195 |
| overall (bare -> chat) | says_I | 14 / 1 | 0.000977 | +5.0 | 11 / 0 | 0.000977 |

## Per model: ai_system % by tick (bare / prefill / chat_scaffold / chat)

| model | ai_system | human_person | says_I | empty |
|---|---|---|---|---|
| `01-ai/Yi-1.5-9B-Chat` | 32 / 100 / 100 / 98 | 42 / 0 / 0 / 0 | 92 / 100 / 100 / 98 | 0 / 0 / 0 / 0 |
| `HuggingFaceH4/zephyr-7b-beta` | 0 / 100 / 100 / 100 | 60 / 0 / 0 / 0 | 68 / 100 / 100 / 100 | 0 / 0 / 0 / 0 |
| `HuggingFaceTB/SmolLM2-360M-Instruct` | 10 / 90 / 82 / 98 | 50 / 0 / 10 / 0 | 88 / 90 / 92 / 95 | 0 / 0 / 0 / 0 |
| `Qwen/Qwen2.5-0.5B-Instruct` | 60 / 100 / 90 / 95 | 15 / 0 / 2 / 5 | 95 / 100 / 98 / 100 | 0 / 0 / 0 / 0 |
| `Qwen/Qwen2.5-7B-Instruct` | 100 / 100 / 100 / 100 | 0 / 0 / 0 / 0 | 100 / 100 / 100 / 100 | 0 / 0 / 0 / 0 |
| `Qwen/Qwen3-8B` | 98 / 100 / 100 / 100 | 0 / 0 / 0 / 0 | 100 / 100 / 100 / 100 | 0 / 0 / 0 / 0 |
| `TinyLlama/TinyLlama-1.1B-Chat-v1.0` | 0 / 32 / 70 / 75 | 50 / 42 / 10 / 2 | 92 / 98 / 90 / 95 | 0 / 0 / 0 / 0 |
| `allenai/Llama-3.1-Tulu-3-8B-SFT` | 10 / 80 / 92 / 98 | 72 / 0 / 2 / 0 | 92 / 80 / 98 / 98 | 0 / 0 / 0 / 0 |
| `allenai/Llama-3.1-Tulu-3-8B-SFT-no-math-data` | 5 / 72 / 80 / 95 | 82 / 5 / 8 / 0 | 90 / 68 / 85 / 98 | 0 / 0 / 0 / 0 |
| `allenai/Llama-3.1-Tulu-3-8B-SFT-no-persona-data` | 10 / 78 / 92 / 90 | 62 / 10 / 0 / 5 | 82 / 85 / 95 / 95 | 0 / 0 / 0 / 0 |
| `allenai/Llama-3.1-Tulu-3-8B-SFT-no-wildchat-data` | 2 / 90 / 85 / 95 | 78 / 5 / 0 / 2 | 88 / 88 / 82 / 98 | 0 / 0 / 2 / 0 |
| `allenai/Llama-3.1-Tulu-3.1-8B` | 15 / 90 / 38 / 88 | 68 / 2 / 2 / 0 | 88 / 88 / 32 / 85 | 0 / 0 / 60 / 8 |
| `m-a-p/neo_7b_instruct_v0.1` | 60 / 100 / 100 / 100 | 32 / 0 / 0 / 0 | 92 / 100 / 100 / 98 | 0 / 0 / 0 / 0 |
| `meta-llama/Llama-3.1-8B-Instruct` | 12 / 100 / 100 / 100 | 78 / 0 / 0 / 0 | 98 / 100 / 100 / 100 | 0 / 0 / 0 / 0 |
| `openbmb/MiniCPM5-1B` | 0 / 90 / 85 / 100 | 0 / 0 / 0 / 0 | 0 / 95 / 80 / 98 | 0 / 0 / 0 / 0 |
| `stabilityai/stablelm-2-zephyr-1_6b` | 0 / 88 / 92 / 88 | 78 / 2 / 0 / 0 | 92 / 90 / 95 / 98 | 0 / 0 / 0 / 0 |
| `tiiuae/Falcon3-7B-Instruct` | 95 / 100 / 100 / 100 | 2 / 0 / 0 / 0 | 98 / 100 / 100 / 100 | 0 / 0 / 0 / 0 |
| `zai-org/glm-4-9b-chat-hf` | 15 / 100 / 100 / 100 | 65 / 0 / 0 / 0 | 88 / 100 / 100 / 100 | 0 / 0 / 0 / 0 |
