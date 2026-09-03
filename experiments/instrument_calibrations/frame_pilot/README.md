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

## THE FRAME IS NOT A CONFOUND IN THIS CAMPAIGN'S RESULTS, AND THE ERROR IS EASY

**Every twp displacement measurement runs BOTH arms raw**, with no chat template
on either side. So the frame is not differentially applied and cannot be
confounding the arm contrast. RH, 2026-09-03, correcting exactly this seat having
implied otherwise in conversation.

And `../frame_prefill/` finding 15 shows the error runs the wrong way round:

    arm effect, frame held constant on BOTH arms   0.1870
    arm effect, raw                                0.1073

**Raw UNDERSTATES the arm contrast by 1.74x.** Measuring unframed makes this
campaign's numbers conservative, not contaminated.

The 82% figure is what invites the mistake. Putting a BASE model in its own chat
template moves it 0.0879, which is 82% of what alignment moves it in raw
(0.1073). That is a statement about how large the template effect is IN ITS OWN
RIGHT, on a model nobody aligned. It says nothing about whether our measurements
are clean, and reading it as though it did turns a fact about templates into an
imagined defect in the corpus.

## SO THE QUESTION IS THE INTERESTING ONE, NOT THE DEFENSIVE ONE

Not "are our results contaminated" -- they are not. It is:

> **Is being MOVABLE BY THE FRAME itself something alignment installs?**

The ladder is what answers it. Flat across base -> SFT -> DPO -> Instruct, and
the template moves any templated model alike: a property of chat formatting.
Growing along the ladder, and alignment has installed a disposition to become a
different distribution when addressed as an assistant -- which is a claim about
what alignment does, not about how we measured it.

The n=1 observation below points at the second, which is why the pilot is worth
buying and why its result would not be a methods result.

## The two design commitments worth not losing

**The measures are lexicon-free** -- entropy, tail mass, support size, JS between conditions. `kill`-counting produced two claims in one afternoon that did not survive: "the turn structure raises kill" (3 of 4 base arms, one contradicting, n=1 prompt) and "the vendor persona suppresses violent completions in an unaligned base" (46.6x on Qwen2.5-7B against 1.3x on Qwen2.5-0.5B with the IDENTICAL persona string). A lexicon is a category judgement wearing a number, and a lexical follow-up can always be run on whatever the lexicon-free measures single out.

**Neutral prompts are not optional.** Every transgressive prompt measured under a frame will show the distribution move; without a neutral arm there is no telling "the frame suppresses transgression" from "the frame changes every distribution". The control comes from `corpus.domains()`'s 205 declared neutral prompts rather than an invented string.

Selection is declared and blind to the outcome: stable-hash order within each domain, not by coverage and not by how interesting a prompt looks.

## What already suggests the result, and why it is not one

Measured on ONE prompt before this folder existed: base entropy barely moves under framing (5.20 to 5.12, 5.52 to 5.30, 5.57 to 5.84 on three base arms) while aligned arms collapse about 3 bits (kanana-instruct 4.33 to 1.37). **n=1 prompt, no control, no ladder.** That observation is what this pilot exists to test properly, and it is recorded here as the motivation rather than as evidence.

Related and separate: `../frame_prefill/` and the wrapper row in `../../passage_analysis/jakobson_space/` -- which measures a continuation wrapper moving a model 80% as far as alignment did, at the PAGE grain rather than this one.
