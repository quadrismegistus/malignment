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
