---
kind: subject
status: OPEN
headline: NONE STATED
grain: corpus
---

# posttraining_corpus_analysis

**The subject, not a question.** This directory indexes its questions and holds
nothing else: no code, no data, no claims. Anything shared between the questions
goes in `malignment/`.

Promoted with one occupant on RH's word, because a second is already named.

## Why this subject exists

Every other experiment here measures a MODEL. These measure the CORPUS a model
was aligned on — the preference data itself, as text on disk.

**Which makes them the only cluster in the repo untouched by the v4 boundary
work.** No cells, no `boundary_mask`, no `twp_words`, no rebuild. They were
runnable while everything else waited, which is why they exist.

And the question is upstream of the campaign's own findings: M01 established that
alignment displaces transgressive vocabulary. **These ask whether the preference
data encodes that lexically in the first place**, or whether displacement is
something the optimisation produces from data that does not look like a word list.

## Questions

| question | corpus | status |
|---|---|---|
| [`hh-rlhf`](hh-rlhf/) | Anthropic/hh-rlhf, 160,800 pairs | CLOSED, exploratory — the axis is engage-vs-deflect |
| [`pku-safe-rlhf`](pku-safe-rlhf/) | PKU-SafeRLHF, 73,907 pairs | worked out; one control outstanding |
| [`tulu3-safety-slice`](tulu3-safety-slice/) | coconot + wildguardmix + wildjailbreak, 110,983 prompts | registered, data not yet downloaded |

**PKU is the one that matters, because it is the only cached corpus that TRAINED
MODELS WE MEASURE**: `beaver-7b-v1.0` (a declared lineage off `llama-7b`),
`alpaca-7b-reproduced` (the SFT input to Safe RLHF) and `AmberSafe` (**card says
DPO on PKU-SafeRLHF alone; the paper says ShareGPT-90K SFT plus a SafeRLHF DPO
stage. `roster/models/attestations.json` records the contradiction and rates the
checkpoint confidence: medium**). A signal found in the corpus can be checked against the
model trained on it. Neither hh-rlhf nor ultrafeedback offers that — no Anthropic
model is in the roster.

It carries `is_response_N_safe`, **19** harm categories, `severity_level`, and
`better_response_id` / `safer_response_id` as separate judgements disagreeing on
17,798 pairs (24.1%).

`HuggingFaceH4/ultrafeedback_binarized` (61,135 pairs, graded scores, no harm
labels) is the pure-quality comparison and is unstarted.

**Named, not started, and the better design: PROMPTS DERIVED FROM A SAFETY
CORPUS, RUN ON MODELS NOT TRAINED ON IT** (RH). It inverts the relation — the
corpus becomes a stimulus source rather than an object — and it breaks the
circularity, because only beaver and AmberSafe saw this data. Needs a fleet, so
it waits, and it gets its own question.

## What is cached locally

All three, no download. `pyarrow` is declared as the `corpora` extra in
`pyproject.toml` — **experiment-only: nothing in `malignment/` imports it, and
`import malignment` must keep working in a venv that never installed it.**
