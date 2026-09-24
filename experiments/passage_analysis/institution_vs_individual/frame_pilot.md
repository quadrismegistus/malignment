---
kind: registration
question: How much of the base-to-aligned shift is the chat frame, and how much the weights?
status: DECLARED 2026-09-24, before any aligned-raw passage was coded
---

# Frame pilot: the aligned models that also ran raw

Declared by the dario seat at RH's instruction ("Yes code them", 2026-09-24), before any of these passages was coded or read. Producer `frame_pilot.py`.

## Why this exists

The regeneration compares a raw base with an aligned model in chat, so the base-to-aligned change moves weights and frame together (README, "Weights and frame move together"). Chat was chosen so the aligned arm is comparable with the frontier API models, which have no base. Nothing in the folder isolates the frame.

The first fleet's render bug left an accidental third cell. Eight aligned models silently got RAW prompts. Their passages were superseded and never coded: 360 each, all 36 prompts x 10 seeds, 256 tokens, vLLM 0.22.1, `generate.DECODER`, stored as `frame: raw`, `template: False`. That is the same engine, decoder and code path as the base-raw passages the analysis already keeps.

## Population

- **Aligned, raw (to code):** AmberSafe, beaver-7b-v1.0, archangel_sft-dpo_pythia2-8b, eleuther-pythia6.9b-hh-dpo, RedPajama-INCITE-7B-Chat, AquilaChat2-7B, bloomz-7b1, CT-LLM-SFT-DPO. 8 x 360 = 2,880 passages.
- **Base, raw, and aligned, chat:** the rows already coded in `coded_regen.jsonl`, unchanged.
- The first six have all three cells. bloomz and CT-LLM have no chat cell: they ship no chat template and none was authored, which is why they are out of the main test.

Coder: `task.py` v2 (`institution_vs_individual_v2`), `deepseek/deepseek-flash`, temperature 0, the same task, shots and blinding as the main run. Output to `$MALIGNMENT_DATA/institution_vs_individual/coded_frame_pilot.jsonl`. Nothing is added to `coded_regen.jsonl`.

## Quantities

Same filter and outcomes as `analyse_regen.py`: continuation or advice form, coherent, perspective kept; `outcomes()` for channel (primary), outward, authority, move_voice_direct. Per lineage, with each DiD = (individual change) - (institution change) over cell means:

    total   = aligned-chat - base-raw        the quantity the main test reports
    weights = aligned-raw  - base-raw        frame held at raw
    frame   = aligned-chat - aligned-raw     weights held at the aligned model

`total = weights + frame` exactly, per lineage, because each is a difference of the same cell means.

## Declared expectations (the dario seat's, not RH's)

- **E1 (form).** The chat frame, not the weights, converts text to advice: aligned-raw writes advice LESS often than aligned-chat in at least 5 of the 6 three-cell lineages.
- **E2 (channel, weights).** Alignment widens the counterparty-channel gap without the chat frame: `weights` > 0 for channel in at least 6 of the 8 lineages.

## Decision rule for the decomposition (primary, descriptive)

Over the six three-cell lineages, channel: **frame-dominated** if `frame` > `weights` in at least 5 of 6, **weights-dominated** if `weights` > `frame` in at least 5 of 6, **mixed** otherwise. The per-lineage table is reported whatever the verdict.

## Limits, stated before the result

- Six lineages for the decomposition, eight for the weights effect. A sign test at 6/0 bottoms out at p = 0.031, so this is descriptive.
- They are atypical. In the main test five of the six sit below the population's median channel DiD (+0.348); only AmberSafe is above. They are old or small models.
- Their chat templates are the repo's reconstructions from each model's training code or card (`roster/models/chat_templates.json`), not vendor-shipped templates.
- archangel and hh-dpo keep few aligned passages after the filter (74 and 105 in chat).
- Nothing here generalises to the 43-lineage population. Only a raw-aligned run on all of them could say how much of the main effect is frame.
