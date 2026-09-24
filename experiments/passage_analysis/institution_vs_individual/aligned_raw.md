---
kind: registration
question: How much of the base-to-aligned shift is the chat frame, and how much the weights, across all 43 lineages?
status: DECLARED 2026-09-24, before any aligned-raw passage was generated or coded
---

# Aligned raw: the fourth cell on every lineage

Commissioned by the dario seat at RH's request ("political economy is the priority"; RH: "yes let's do this", 2026-09-24), after the frame pilot (`frame_pilot.md`, 35d19fc8; result 65027652) came out mixed on six atypical lineages. Declared by the malign seat before any passage was generated. The analysis generalises `frame_pilot.py --analyse` and is the dario seat's; the quantities, population and readings below bind it.

## Why

The regeneration has base raw and aligned chat, so the base-to-aligned change moves weights and frame together (README, "Weights and frame move together"). The pilot split them on six old or small models with reconstructed templates. This adds the aligned-raw cell on every lineage the main test uses.

## Generation

- **Models:** the aligned endpoint of each of the 43 lineages with both arms in `coded_regen.jsonl`, INCLUDING the pilot's six, so the whole cell comes from one path. The pilot's accidental passages then serve as a determinism check on the same seeds (reported, not pooled).
- **Prompts:** `prompts/raw.jsonl`, the 36 prompts with no template, exactly as the base arm.
- **Decoder, engine, render:** `generate.DECODER` (t=1.0, top_p=1.0, top_k disabled, 256 new tokens, n=10, seeds 42+i), vLLM 0.22.1 (the version of every existing cell), the fixed render path (`render="ids_v2"`), with one BOS checked on a model whose tokenizer writes BOS. Each model at the dtype its chat cell used (`fleet/regen*.txt`).
- **Hardware:** RunPod. 24 GB cards for the models that fit; 80 GB cards for Llama-3.1-70B-Instruct (tp=2), Olmo-3.1-32B-Instruct, gemma-2-9b-it and glm-4-9b-chat-hf. Card type does not enter the key; the engine, decoder and render do.
- A model that fails to generate is listed and dropped from every contrast needing its cell; none is substituted.

## Coding

`task.py` v2 (`institution_vs_individual_v2`), `deepseek/deepseek-flash`, temperature 0, the same task, shots and blinding as the main run. Output `$MALIGNMENT_DATA/institution_vs_individual/coded_aligned_raw.jsonl`, `arm="aligned_raw"`. `coded_regen.jsonl` and `coded_frame_pilot.jsonl` are not touched. The same `analyse_regen.keep` filter (continuation or advice, coherent, perspective kept) and `outcomes()`.

## Quantities (as `frame_pilot.md`)

Per lineage, each a difference-in-differences, (individual change) - (institution change), over cell means:

    total   = aligned-chat - base-raw
    weights = aligned-raw  - base-raw
    frame   = aligned-chat - aligned-raw          total = weights + frame, exactly

Outcomes: channel (PRIMARY), outward, authority, move_voice_direct. Units: lineages (43 minus failures); disputes (18) beside them.

## Readings, fixed now

- **E1 (form), re-declared at scale.** The chat frame, not the weights, converts text to advice: aligned-raw writes advice less often than aligned-chat in a majority of lineages, two-sided sign test p < 0.05.
- **E2 (channel, weights).** Alignment widens the counterparty-channel gap without the chat frame: `weights` > 0 for channel, sign test over lineages p < 0.05.
- **Decomposition (primary, channel).** Sign test over lineages of `frame - weights`: **frame-dominated** if frame > weights with p < 0.05; **weights-dominated** if weights > frame with p < 0.05; **mixed** otherwise, reported with the median share `weights / total` over lineages where total > 0.
- The same three for move_voice_direct, where the pilot put the institution's direct voice in the weights (7/7), reported as secondary.

## Limits, stated now

- Aligned-raw asks an instruction-tuned model to continue text it was not trained to continue; its output is a real behaviour of the weights under a frame they were not tuned for, not the model's "true" disposition.
- The coder sees each passage without its arm, so frame is not coded, but raw continuations and chat answers differ in form, and form gates the `keep` filter. A lineage whose aligned-raw passages mostly fail `keep` enters with few passages; per-lineage kept counts are reported.
