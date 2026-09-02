---
kind: calibration
id: frame_pilot
question: Does the chat frame move the word distribution, and does it depend on alignment stage?
status: DESIGNED, NOT RUN. `run.py` exists and `results/` does not; nothing here has been measured.
headline: NONE STATED -- the design is registered, the pilot has not been run.
grain: distribution
---

# frame_pilot

**Nothing has been measured.** `run.py` was written 2026-08-22 and never run: there is no `results/` directory here and no `$MALIGNMENT_DATA/frame_pilot`. This README exists because the folder had a producer and no written claim, which `index.py --check` now refuses -- and which it could not previously even see, since the first version of that checker only walked directories that already had a README.

The design is in `run.py`'s docstring and is not restated here. What it is for, in one line: a PILOT to decide whether the full rung-B sweep in `docs/prefill.md` is worth buying, and to fix the measures before it is.

## Why it is a calibration and not a question

It asks whether a chat template changes the distribution -- it does, and that is a fact about templates, not about alignment. The thing it is built to separate is whether the change TRACKS ALIGNMENT STAGE, using the Olmo-3 ladder (base to SFT to DPO to Instruct) plus two other vendors so a result is not one family's habit. Until it runs it registers a construction, not a claim.

## The two design commitments worth not losing

**The measures are lexicon-free** -- entropy, tail mass, support size, JS between conditions. `kill`-counting produced two claims in one afternoon that did not survive: "the turn structure raises kill" (3 of 4 base arms, one contradicting, n=1 prompt) and "the vendor persona suppresses violent completions in an unaligned base" (46.6x on Qwen2.5-7B against 1.3x on Qwen2.5-0.5B with the IDENTICAL persona string). A lexicon is a category judgement wearing a number, and a lexical follow-up can always be run on whatever the lexicon-free measures single out.

**Neutral prompts are not optional.** Every transgressive prompt measured under a frame will show the distribution move; without a neutral arm there is no telling "the frame suppresses transgression" from "the frame changes every distribution". The control comes from `corpus.domains()`'s 205 declared neutral prompts rather than an invented string.

Selection is declared and blind to the outcome: stable-hash order within each domain, not by coverage and not by how interesting a prompt looks.

## What already suggests the result, and why it is not one

Measured on ONE prompt before this folder existed: base entropy barely moves under framing (5.20 to 5.12, 5.52 to 5.30, 5.57 to 5.84 on three base arms) while aligned arms collapse about 3 bits (kanana-instruct 4.33 to 1.37). **n=1 prompt, no control, no ladder.** That observation is what this pilot exists to test properly, and it is recorded here as the motivation rather than as evidence.

Related and separate: `../frame_prefill/` and the wrapper row in `../../passage_analysis/jakobson_space/` -- which measures a continuation wrapper moving a model 80% as far as alignment did, at the PAGE grain rather than this one.
