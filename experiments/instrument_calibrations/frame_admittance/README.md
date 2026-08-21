---
stub: true
stub_written_by: dario, 2026-08-21, from the folder's own files
question: Does a frame admit a transgressive continuation at all, before anyone pays to pole-tag it?
status: RUN. `run.py` and 8 result files present; no write-up.
---

# frame_admittance

**A STUB.** Written by a seat that did not do this work, from `run.py`'s
docstring and the contents of `results/`. **It states no finding**: the results
are here and unread by me, and the number belongs to whoever produced it.

## The question, from the producer's own docstring

Roughly 276 institutional prompts are already measured on ~406 checkpoints, none
of them pole-tagged. Tagging is the expensive part, so this ranks frames by
whether tagging them could produce anything at all: a frame whose base
distribution offers only `contact / consider / discuss` has foreclosed the
transgressive pole, and no tagging will recover it. Store-only triage.

    python .../frame_admittance/run.py --domain institutional
    ... --axis        # adds the bge pass, slow, embeds per frame

## What is here

    run.py                                   the producer
    results/admittance_institutional.{csv,json}
    results/admittance_m03_speaker_kernel.{csv,json}
    ... 8 files in total

## What a replacement should say

Which frames were admitted and which foreclosed, at what threshold, and whether
the ranking was used to select anything downstream. **A triage that ranked frames
and then selected on the ranking is a selection rule, and it needs stating
wherever the selected set is quoted** -- which is the one thing a reader of the
result cannot recover from the CSVs.
