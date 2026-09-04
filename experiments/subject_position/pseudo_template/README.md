---
kind: question
status: MEASURED. 145 models, from the twp store
headline: The address supplies ten times what the models bring -- and it is the FAIR arm comparison, not the degraded one
grain: model
---
# pseudo_template

**id:** subject_position/pseudo_template **status:** MEASURED. Producer `run.py`, 145 models, read from the twp store. Finding in `FINDING.md`.

# THE QUESTION

F20 substituted `Q: ... A:` for the missing plain-completion arm and read the result as being about the models. How much of it is the address?

# THE RESULT

    first-person mass at the answer slot, base models
      Q: Who are you?\nA:      median 0.512   (145 models)
      bare "Who are you?"      median 0.048   (14 bases, max 0.114)

`Q:/A:` is an address written into the text, and pretraining is saturated with it.

**It is also the only condition in which base and aligned receive an IDENTICAL address**, because 11 of 14 bases ship no chat template at all — so it is the fair arm comparison, not the degraded one. The template condition cannot compare arms for most lineages.

## Under that identical address, alignment concentrates rather than creates

    share of models above       base   aligned
      p_first > 0.25             93%       97%
      p_first > 0.50             67%       87%
      p_first > 0.75              4%       49%
      p_first > 0.90              0%       21%

Given the slot, the base takes it. The arms are near-identical at the bottom of the range and separate entirely at the top.

**RH's reading, which the data support:** `Q: Who are you?\nA:` near-obligates `I`, so a base at 0.54 is **low capacity to hold a basic sociolinguistic frame**, not partial occupancy of a position, and alignment closing that gap IS installation.

Measured directly, the base is not repeating the question (interrogatives are 0.011 of its non-first-person mass); it is **dispersed** — entropy 3.09 bits against aligned 2.08, about eight ways to begin an answer against four, falling in 73 of 82 forward edges.

## The confound, stated

Placed against all 2,985 prompts in the store, that entropy drop ranks **7th**, and all four `Q:/A:` identity prompts sit in the top 1.5%. But the confound is total: all four are identity questions AND all four are `Q:/A:`, so format and content cannot be separated here. The extreme tail is otherwise dominated by intimate narrative and salary stems — prompts sharing not a subject but a canonical answer.

# WHAT IS IN HERE

    run.py             the 145-model Q:/A: contrast, from the twp store
    FINDING.md         the written finding
    results/output.txt the run's printed output
