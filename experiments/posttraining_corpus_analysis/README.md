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
| [`hh-rlhf`](hh-rlhf/) | Anthropic/hh-rlhf, 160,800 pairs | registered, not run |

Named and not started: **PKU-Alignment/pku-safe_rlhf** (73,907 pairs), which
carries `is_response_N_safe`, a 14-category `harm_category`, `severity_level`,
and — the reason it is worth its own question — **`better_response_id` and
`safer_response_id` as separate judgements that disagree on 17,798 pairs (24%)**.
That is a corpus encoding the quality/safety tradeoff rather than collapsing it.

`HuggingFaceH4/ultrafeedback_binarized` (61,135 pairs, graded scores, no harm
labels) is the pure-quality comparison and is also unstarted.

## What is cached locally

All three, no download. `pyarrow` is declared as the `corpora` extra in
`pyproject.toml` — **experiment-only: nothing in `malignment/` imports it, and
`import malignment` must keep working in a venv that never installed it.**
