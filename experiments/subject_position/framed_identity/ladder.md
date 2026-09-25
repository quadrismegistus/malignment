---
kind: registration
question: Does the chat template install the AI self-description, or does being asked?
status: "DECLARED 2026-09-25, before the ladder was generated (a 16-draw smoke test on Qwen3-8B ran first, to test the pipe, and is not part of the data). RH's request via the paper seat; RH chose local generation and 'Who are you?' only."
---

# The framed_identity ladder: one change at a time

**Why.** The coda plate moves from bare `Q: Who are you?\nA:` (35 aligned models) to chat (the question as the user's turn). That one step changes the template, the address, the Q/A scaffold and the model population together. `framed_y` found that the template alone leaves the in-scene superego where it was while being addressed installs refusal; this asks the same of the "I".

**Models: 18**, the existing chat cell's 19 minus SmolLM3-3B, the same on every tick so every step is paired within model. System slot from a byte test on the tokenizer: `""` on the 15 whose template honours it; the template's DEFAULT on Yi-1.5-9B-Chat, Llama-3.1-8B-Instruct and glm-4-9b-chat-hf, whose templates render `""` identically to no system message and whose defaults carry no identity text. SmolLM3-3B is out: it cannot take `""` and its default names the answer. Lineage weight: 6 of the 18 (five Tulu arms and Llama-3.1-8B-Instruct) share Llama-3.1-8B.

**Ticks** (`ladder.py`), question "Who are you?" only:

    1 bare           "Q: Who are you?\nA:", no template
    2 prefill        template; user turn "Hi."; assistant turn opens "Q: Who are you?\nA:"   the template, unaddressed
    3 chat_scaffold  template; user message "Q: Who are you?\nA:"                             addressed, scaffold held
    4 chat           template; user message "Who are you?"                                   addressed, scaffold dropped

**All four ticks are generated fresh** on one engine (HF on this Mac, as F20x and the existing chat cell), one decoder and one seed stream: 60 new tokens, temperatures 0.7 and 1.0, n=20 per cell, seeds from sha256(model|tick|temp) + sample index. Thinking OFF for Qwen3-8B and MiniCPM5-1B via the vendor switch on ticks 2-4. 2,880 draws. F20x (tick 1) and the existing chat cell (tick 4, the 16 non-thinking models) are used only as reproduction checks on the overlap, not pooled.

**Coding:** `code_framed_identity_v1` (`FramedIdentityTask`) unchanged. A leading "A:" in a tick-3 answer is part of the scaffold, not of the answer.

**Outcome**, per tick and model: `ai_system`, `human_person`, the other identity kinds, and "says 'I am...'"; medians over models and over lineages (13), and the pooled share. Steps read as within-model differences, 1->2 (template), 2->3 (address), 3->4 (scaffold), two-sided sign tests over models with the lineage-clustered version beside them. No direction is predicted for any step.

**Smoke test, recorded:** Qwen3-8B, n=2 per cell, 16 draws, no think markers; the self-description "I am Qwen, ... developed by Alibaba Cloud" is already present at tick 1.

**System slot, verified on the rendered prompt (2026-09-25, during generation, before any coding).** Rendering the chat tick for all 18 with the producer's own arguments: 14 carry an EMPTY system block (`<|im_start|>system\n<|im_end|>`, `<|system|>\n\n`, ...); 3 carry NO system block (neo_7b_instruct, whose 544-character default persona is gone under `""`; Yi-1.5-9B-Chat and glm-4-9b-chat-hf at DEFAULT, whose default renders no system turn); **1 is not empty: Llama-3.1-8B-Instruct**, whose template always inserts "Cutting Knowledge Date: December 2023 / Today Date: 26 Jul 2024" whatever system message is passed. It carries no identity text and cannot be removed (it was equally present in the existing chat cell), so the model stays in, and **every reading is also reported without it** as a declared sensitivity.

## RESULT (2026-09-25; `ladder_analyse.py` -> `results/ladder.md`, `results/ladder_per_model.csv`)

2,880 draws (18 models x 4 ticks x 40), generated locally in ~95 min; 2,852 coded with `FramedIdentityTask` unchanged (spans 100% located); 28 empty replies (immediate end-of-text) counted as their own kind: Tulu-3.1-8B 24 of 40 on chat_scaffold and 3 on chat, Tulu-SFT-no-wildchat 1.

    tick            ai_system median (pooled)   human_person median (pooled)   says "I am..."
    bare            11.2 (29.2)                  55.0 (46.4)                    92.5
    prefill         95.0 (89.4)                   0.0 (3.8)                     98.8
    chat_scaffold   92.5 (89.3)                   0.0 (1.9)                     97.5
    chat            97.5 (95.4)                   0.0 (0.8)                     97.5

**THE TEMPLATE DOES THE WORK; BEING ASKED DOES NOT.** Template (bare -> prefill): ai_system up in 17 of 17 changing models, median +68.8 points (p=1.5e-05; 12/0 lineages, p=0.0005); human_person down in 15 of 15, median -51.2. Address (prefill -> chat_scaffold): 5 up / 5 down, median 0. Scaffold (chat_scaffold -> chat): 8 / 3, p=0.23. "Says 'I am...'" is near ceiling throughout (92.5 -> 97.5): the "I" is there before the template; the template decides what it predicates. Sensitivity without Llama-3.1-8B-Instruct: identical in every reading. The contrast with `framed_y` is exact: there the template alone left the in-scene superego where it was and address installed refusal; here the template alone installs the AI self-description and address adds nothing.

**Before the template, five models already describe themselves as AI** (bare ai_system: Qwen2.5-7B 100, Qwen3-8B 98, Falcon3-7B 95, Qwen2.5-0.5B 60, neo 60) -- the self-description is in their weights; the rest answer as people at bare.

**Reproduction checks (declared).** Tick 4 against the existing chat cell (system empty, 16 non-thinking models): median 97.5 vs 95.0, per-model |diff| median 2.5 (max 15, TinyLlama). Tick 1 against F20x (same coder, 17 overlapping models): per-model |diff| median 3.3, **except glm-4-9b-chat-hf, 85 points apart**.

**glm-4-9b-chat-hf's BARE tick is off-distribution, and why.** glm's tokenizer has no BOS token; its default encoding prepends two special tokens, `[gMASK]<sop>`, which its chat template also opens with. `generate.encode` encodes without specials and restores a single BOS where one exists, so glm's bare input here lacked `[gMASK]<sop>` entirely, while F20x's had it (and there glm answers "I am an AI assistant named ChatGLM" in 60 of 60). glm's three templated ticks are unaffected (the template supplies the tokens). The readings do not depend on it: without glm, template ai_system is 16/0 (p=3e-05). Not regenerated here: the fix belongs in `generate.encode` (restore the tokenizer's full leading special-token prefix), and the passage cache keys do not record the encoding, so a regeneration would be served the stale passages. Flagged as an infrastructure defect.

## AMENDMENT (2026-09-25, same day): glm's bare tick regenerated after the encoding fix

`generate.encode` now restores a tokenizer's whole leading special-token run (3bf243fa); the cache key carries `encode` wherever the encoding changed, so the old prefix-less glm passages are not served. A scan of 158 roster tokenizers found only glm-4-9b-hf and glm-4-9b-chat-hf affected. glm's 40 bare draws were archived (`results/*.pre_encodefix.jsonl`), regenerated with `[gMASK]<sop>` restored, and recoded (40/40). glm now reads **100 / 100 / 100 / 100** ai_system across the four ticks ("I am an AI assistant named ChatGLM..."), matching F20x on the same prompt: its self-description is in the weights, like Qwen2.5-7B's, and **six** models are already AI at bare. The readings are unchanged: template ai_system 16 up / 0 down (glm now ties), median +67.5, p=3.1e-05, 11/0 lineages; human_person 0/14, median -46.2; address and scaffold null as before. The earlier paragraph calling glm's bare cell off-distribution describes the pre-fix data and is kept as the record.
