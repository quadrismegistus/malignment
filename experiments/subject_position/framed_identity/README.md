---
kind: question
status: RUN, not yet written up. results/framed_identity.jsonl exists
headline: The one cell F20 never filled -- identity questions INSIDE the chat template
grain: model x question
---
# framed_identity

**id:** subject_position/framed_identity **status:** RUN 2026-08-23, not yet written up. Producer `run.py`. The result is on disk and unanalysed.

# THE GAP THIS FILLS

`f20x_annotations` codes 18,720 generations for `identity_kind`, and its verified headline is that alignment swaps what the first person predicates: human 0.468 → 0.199, AI 0.235 → 0.509.

**The whole corpus is UNTEMPLATED.** Its producer declares `RUNG = "Q: {q}\nA:"` and never calls `apply_chat_template` — the docstring says the roster is larger than the beam battery's precisely because "dyad_qa needs none".

Per-question, paired over 29 lineages, that corpus says the median base model identifies as an AI **0.0%** of the time and the aligned model **43.3%** on "Who are you?", against 43.3% claiming a HUMAN identity. Aligned models tell you they are software engineers, students, children's book illustrators.

So the F20 reading is bounded: outside its template, the aligned "I" is still freely predicable of a person. **What the deployed model does when actually addressed is the cell nobody has measured**, and it is the cell every claim about "the LLM's I" is really about.

# THE DESIGN

Within-model, not between-arm. See `run.py`'s docstring for the full statement.

# WHAT IS IN HERE

    run.py                          the producer
    results/framed_identity.jsonl   2.3 MB, run 2026-08-23
    results/log_framed.txt          the run log

# WHAT IS NEEDED

An analysis. The measurement exists; nothing reads it yet.
