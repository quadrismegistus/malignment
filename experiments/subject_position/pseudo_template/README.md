---
kind: question
status: MEASURED. 145-model corpus; the citable figure is n=14 matched BASES. Measures first-person MASS and cannot see who the "I" refers to
headline: The address supplies ten times what the models bring -- and it is the FAIR arm comparison, not the degraded one
grain: model
---
# pseudo_template

**id:** subject_position/pseudo_template **status:** MEASURED. Producer `run.py`, 145 models, read from the twp store. Finding in `FINDING.md`.

> **INSTRUMENT BOUND, added 2026-09-05 from `../framed_identity`.** Everything
> here is `p(I)` at one position. **It cannot distinguish "I am an AI assistant"
> from "I am Tamas, a cybersecurity expert" — both are ~1.0.** So this question
> measures how much first-person MASS an address supplies, and is not evidence
> about the subject position, self-reference, or whether the "I" refers to the
> speaker at all. On this instrument the subject's thesis reads as REFUTED — 34
> of 50 bases already exceed 0.5 when addressed at `Q:/A:`, so alignment would
> be "installing" something already present. Coded for KIND on overlapping
> models it is supported (`ai_system` 0.4% → 18.3%, base to aligned). **Do not
> cite this question for the thesis in either direction.**

# THE QUESTION

F20 substituted `Q: ... A:` for the missing plain-completion arm and read the result as being about the models. How much of it is the address?

# THE RESULT

**CORRECTED 2026-09-05. The earlier version of this table read `median 0.512
(145 models)` and labelled it "base models". Three things were wrong with that
line and RH's rule — bases are not pooled with aligned in results — catches all
three.** `0.5121` is the median PARENT MASS ON SFT EDGES (n=35) lifted out of the
headroom table; 145 is the CORPUS SIZE, models with cells on this prompt; and
145 pools 50 bases with 95 post-trained checkpoints. Recomputed base-only:

**MATCHED, BASE-ONLY, THE SAME 14 MODELS IN BOTH CONDITIONS.** The 14 bases with
a bare-prompt measurement are a strict SUBSET of the 50 with a `Q:/A:` one, so
the comparison can be run within-model with the address as the only variable:

    first-person mass at the answer slot, n=14 BASES, matched
      Q: Who are you?\nA:      median 0.5251
      bare "Who are you?"      median 0.0483      -> 10.9x

That is the citable form of the claim. The wider base population agrees:

    Q:/A:, all bases with cells        n=50   median 0.5497
    Q:/A:, SFT-edge parents            n=35   median 0.5121   <- what was misquoted
    Q:/A:, depth > 0 (post-trained)    n=95   median 0.7439
    Q:/A:, POOLED over everything     n=145   median 0.6955   <- cite nothing here

The pooled row is the one the rule exists to prevent: it sits between the arms,
describes neither, and would have understated the address effect by inflating the
baseline it is measured against.

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
