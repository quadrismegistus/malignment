---
kind: question
status: RUN 2026-09-05. Person replicated ungated at n=15,990; interiority still conditional on the story gate
headline: There is no inversion — person and interiority are two effects, and the chat frame moves only one of them
grain: lineage x arm x frame x narrative person
---
# frame_inversion

**id:** subject_position/frame_inversion **status:** OPENED 2026-09-04, RUN and WRITTEN UP 2026-09-05.

    run.py                the three contrasts
    run.py --no-strip     without the dialogue strip -- the check, not an option
    run.py --ungated      the person contrasts with NO pure-story gate
    run.py --rebuild      recompute results/cache.jsonl (spaCy, ~15 min)
    tests.py              9 tests; guards the ungated reader against judge.py drift
    FINDING.md            the result

# THE QUESTION

Templated, alignment raises the first person enormously. **Raw, alignment lowers it.**

On `neo`, whose rendered template is byte-identical at all three rungs — so the difference is not a template difference:

                            raw       chat
    neo_7b                0.0214    0.1375
    neo_7b_sft_v0.1       0.0090    0.4008
    neo_7b_instruct_v0.1  0.0059    0.7759

And in the refusal battery, conversational prompts: base 0.115 → SFT 0.071 raw.

Meanwhile **raw narrative interiority ROSE with alignment** (+0.224, 16/17, `../../passage_analysis/interiority_in_passages`).

# THE ANSWER: IT DISSOLVES

The tension was between two **tasks**, not two frames. Every twp number above is `p(I)` at an answer slot on an identity question; this experiment measures **narration**. A model asked about itself says "I"; a model asked for a story writes "he". They were being read off one axis because both had the words "first person" in them.

                                  ARM  base->aligned, raw     FRAME  raw->prefill, aligned
    first-person narration rate    -0.101  24/31 dn p=.0033   -0.043  22/27 dn p=.0015
    interiority (usas_x)           +0.014  29/31 up p<1e-6    +0.001  16/11    p=.44

**Both alignment and the chat frame push narration toward the third person. Only alignment raises interiority; the frame does not touch it.** A dissociation with a working null in it — the frame moves one metric and not the other, same models, same stories.

# THE PREDICTION THAT WAS REFUTED

Reading (2) below was stated before any of this ran: *the raw interiority gain should be third-person* — what generalises from being trained to answer an Other is a capacity to represent inner states, not a habit of saying "I".

**It is not third-person. Both persons gain**, and the interaction is bounded within `[-0.38, +0.60] ×` the third-person main effect — enough to exclude the first-person gain being absent, which is what the prediction required, and not enough to license "equally".

Reading (1) survives, and in a stronger form than it was stated in. It was offered as *"the inversion is a coincidence of measurement"*; it is not a coincidence, because the frame contrast shows the two metrics respond to **different variables**. That is a positive result about their independence, not an absence of a relationship.

# THE TWO READINGS, AS STATED 2026-09-04

1. **Two separate effects.** The turn-bound "I" and the prose interiority are unrelated consequences of alignment, and the inversion is a coincidence of measurement. — **survives, strengthened**
2. **The trace is not the pronoun.** What generalises is a capacity to represent inner states, not a habit of speaking as an I — in which case the raw interiority gain should be **third-person**. — **refuted**

# WHY THE STATED "NEAREST TEST" WAS NOT RUNNABLE

This README used to name the nearest test as a query against the interiority corpus, *"coded and on disk, so this is a query rather than a run"*. **That was wrong twice.** The coded corpus (`passC`, 17,175 passages) codes no grammatical person at all; and its person is confounded anyway — first-person prompts are six variants of `"I am a ___ and I wanted to"`, present tense 6/6, against past-tense narrative third-person prompts 0/68. A person split there measures genre, not person.

`national_story` leaves person **open**: `"A {Demonym} Story\n(1500 words)\n\nIt was a"` is past tense, narrative, and names no person, so the person is the model's own choice and therefore a thing that can move. It also already carried four frames, so the frame contrast needed no generation.

# THE TWO ARTEFACT ROUTES, BOTH CLOSED

- **The pure-story gate is asymmetric** across exactly the cells the frame contrast compares — 52% survival for aligned/raw against 73% for aligned/prefill, per the corpus's own `meta` table. `--ungated` reruns the person contrasts over the raw stash with no judge and no word floor, 15,990 generations against 7,876: both effects survive, larger n, same sign. **Interiority was NOT replicated ungated** — `usas_x` is a spaCy parse and that population is hours — so every interiority number here stays conditional on the gate. Open flank, stated.
- **The prefill renderer was broken before `9b8465e`** (it closed the assistant turn, so the model saw a finished answer). Verified rather than taken on report: 4,700 of 4,715 surviving prefill rows postdate the fix, and all 65 rows from `CDH0050`, the one producer straddling it, were traced by text into the corpus — **0 of 65 are present**.

# WHAT IS IN HERE

    run.py                       the producer
    tests.py                     9 tests
    FINDING.md                   the result, with the do-not-cite list
    results/analysis.txt         run.py as run
    results/analysis_nostrip.txt --no-strip, the dialogue check
    results/analysis_ungated.txt --ungated, the gate check
    results/cache.jsonl          7,876 rows: person under BOTH strip settings
                                 against one spaCy parse. Derived; --rebuild it

The corpus is `../../passage_analysis/national_story/conflict.sqlite`, a symlink into `~/malignment-data`. One store, two questions, **no second copy** — this experiment only reads it.
