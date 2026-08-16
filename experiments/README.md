# experiments/

One directory per QUESTION. Not per theme, not per script.

    experiments/<question>/
        README.md         the question, its id, the population, the claim, the status
        registration.md   OPTIONAL -- see below. Frozen before the first run.
        run.py            THE producer. Writes the result AT ITS GRAIN.
        plot.py           reads the stored result and writes figures/.
        population.json   generated receipt: the exact ids the result used
        results/          one file per GRAIN, named for it:
                            by_chain.csv, by_chain_domain.csv, ...
        figures/          regenerable output

Only `README.md` and `run.py` are required.

## The rules, and what each one is a response to

**ONE PRODUCER PER DIRECTORY, named `run.py`. A variant is a FLAG, not a file.**
v2's `meta/M01_displacement/scripts/` held 250 scripts for 32 findings — eight
scripts per claim — and the letter prefixes accumulated `k_`×47, `x_`×36, `y_`×26.
**A letter is a namespace, and namespaces fill.** Nobody can now say what `k`
meant. If a thing is not a flag on the existing question, it is a different
question and gets its own directory, which forces someone to name it.

**A SECOND LEVEL ONLY WHEN A SUBJECT HAS TWO QUESTIONS, AND THE SUBJECT HOLDS
NOTHING.** `experiments/<subject>/<question>/` is allowed once a second question
genuinely exists — and the subject directory then contains a README that INDEXES
its questions and nothing else: no code, no data, no claims. Anything shared
between the questions goes in `malignment/`.

That constraint is the whole difference from `meta/M01_displacement`, which was
created EMPTY, absorbed everything vaguely related, and reached 250 scripts for
32 findings. **A container that exists before its contents will be filled by
whatever is nearby.** So the first question of a subject lives flat, and the
subject appears by promotion when the second arrives.

**AND A FOLLOW-UP IS A NEW QUESTION, NEVER A ROUND.**
`division_of_labour_round2` is `k_01`…`k_47` with better spelling: a variant
nobody declared, whose relation to the first is knowable only by asking whoever
ran it. A follow-up gets its own name, its own registration, and — if it was
chosen because the first result disappointed — **a line saying so**, because a
follow-up selected on a disappointing result is a specification search unless it
is declared as one.

**FLAT. NO NUMBERS.** `01_` encodes creation order, which git already knows, and
invites `01a`/`01b` the first time a variant appears. Directories are named for
their question because the question is the stable thing. A citable handle, if the
paper needs one, is an `id:` field in the README — so renaming costs nothing.

**THE FINDING LIVES IN THE QUESTION'S README, AND NOWHERE ELSE.** A subject
README indexes its questions with a status and a navigational gist; it must not
restate their numbers. A number in two files is a number that will disagree with
itself — the failure `movement` had when it stored `relation` beside the
measurement, and the failure four archive artifacts had when they each defined
"the population".

**THERE IS NO `findings/`.** v1 kept 46 findings in a
separate directory and **42 were cited by nothing**: a claim living apart from
its producer has nothing keeping it true. Put the claim beside the code and a
stale claim sits next to the code that contradicts it.

**SHARED CODE GOES IN `malignment/`, NEVER COPIED BETWEEN EXPERIMENTS.** This is
the rule that would have prevented most of those 250 scripts: they copied each
other because there was no library to import from. Two experiments needing the
same function is the signal it belongs in the package.

**STORE THE GRAIN, NOT ONLY THE SUMMARY — BUT THE GRAIN DECIDES WHERE.**
`RESULTS.md` asks for long form; it does not ask for a database. Two different
things were being conflated:

    SHARED MEASUREMENT      cells, movement -- millions of rows, read by many
                            experiments -> ClickHouse
    EXPERIMENT-LOCAL RESULT tens to hundreds of rows, read by this experiment
                            and the paper -> `results.csv` here, tracked

Division of labour is ~20 chains. That is a CSV. Putting it in ClickHouse would
add a table nobody else queries and a migration nobody wants. What is NOT
acceptable either way is storing only the mean: the row per chain must exist, so
the summary can be re-derived and disagreements can surface.

**ONE EXPERIMENT USUALLY HAS SEVERAL GRAINS, so `results/` holds one file per
grain and THE FILENAME IS THE GRAIN**: `by_chain.csv`, `by_chain_domain.csv`,
`by_lineage.csv`. Not `results_2.csv`, not `results_final.csv`.

That naming rule is what keeps a `results/` directory from becoming M01's 455
files: **two files at the same grain is a defect, not a variant.** If
`by_chain.csv` and `by_chain_v2.csv` both exist, one of them is stale and the
question is which — exactly the ambiguity that made 455 files unusable. A new
grain is a new name and is obvious; a new *version* of a grain overwrites, and
git holds the history.

Figures follow the same rule: `plot.py` may write several, and a variant is a
FLAG on it, never a second plotting script.

**A REGISTRATION IS FROZEN OR IT IS NOT A REGISTRATION** — but not every
experiment needs one. It is required when the result has **a direction you would
be disappointed by**, or when a different specification could give a different
answer you would prefer. It is not required for descriptive work: counting what
exists, mapping a corpus, listing a population. Forcing one onto a description is
ceremony, and ceremony devalues the registrations that carry weight.

The tell, since "this one is just descriptive" is exactly what gets said to avoid
registering: **if you can name an outcome you would rather see, register.**

When there is one, it is committed before `run.py` is first run and never edited
afterwards — amendments append with a date and a reason. A pre-registration
editable after seeing the result is a post-hoc rationalisation with better
typography.

## Scratch work

Does not live here. Use the session scratchpad or a gitignored `sandbox/`. The
reason v1 accumulated 477 scripts in `scripts/` is that there was nowhere else to
put something you tried once. **This directory holds questions that have answers.**

---

# THE HYPOTHESIS REGISTER

**Every hypothesis this project has registered, with its status. If a claim is not in this table it is not registered, and if it is here it is findable.**

This table exists because separating instrument registrations from hypothesis registrations — which is right, see below — made the hypotheses hard to FIND. RH asked "where are our hypotheses about sex and violence?" twice on 2026-08-16, and both times the answer was three directories deep. **Separation without an index is just scattering.**

| id | claim | where | status |
|---|---|---|---|
| **H1** | SFT carries the majority of displacement | `division_of_labour/sft_share` | **SUPPORTED** — median share 0.819 |
| **H2** | the recorded ~90% SFT figure does not replicate | `division_of_labour/sft_share` | **SPLIT** — Olmo-3 Instruct 0.773, Think 0.950; the figure is branch-specific |
| **H3** | *"SFT handles sex, DPO handles violence"* — at PROMPT level | `division_of_labour/sft_share` | **NOT SUPPORTED** — chain p=0.031 but base p=0.077, and base was pre-declared decisive |
| **L1** | the same claim at WORD level, via the lexicon | `division_of_labour/lexical_domains` | **NOT SUPPORTED AS TESTED** — +0.0024, CI ±0.047. Operationalisation later found wrong (see its README) |
| **L2** | is it content or stimulus? sexual-word displacement measured *inside violence and neutral prompts* | `division_of_labour/lexical_domains` | **RUN** — under *sexual* prompts the effect runs BACKWARDS (−0.0433, 5/16); `taboo` is the one positive cell |
| **L3** | does displaced mass leave the domain or move within it | `division_of_labour/lexical_domains` | **RUN** — both categories lose net mass; departure ≈ 2× arrival |
| **R1a** | vulgar-register sexual mass FALLS under alignment | `register_shift` | not run |
| **R1b** | clinical/euphemistic mass RISES — **required**, or it is suppression not displacement | `register_shift` | not run |
| **R2** | the register signature is larger for sexual than violent | `register_shift` | not run |
| **R3** | archaic violent mass rises (`smite`) | `register_shift` | not run — **declared underpowered, ineligible for a headline** |
| **R4** | every R1/R2 effect survives frequency-matched controls | `register_shift` | not run — **a gate, not a robustness check** |

`sex_violence_lexicon` appears nowhere in this table **on purpose**: it registers no hypothesis. It declares one gate (controls >5% ⇒ the instrument is not admitted) and five construction/custody rules, and says nothing about what alignment does.

## Why instrument and hypothesis registrations are kept apart

A registration that makes no claim about the world cannot be tuned toward a finding, because there is no finding in it to aim at. Had L1 lived in the lexicon's registration, every judgment in building the instrument — which words to seed, how strict to make the raters, where to set the control ceiling — would have had a preferred answer sitting on the next page.

The two also fail differently, and the difference is the point:

    instrument registration   worst outcome: "the tool is too loose to use"
    hypothesis registration   worst outcome: "the claim is false and is withdrawn"

**But the separation has a cost and this table is the payment.** Update it in the same commit as any new registration.


## Withdrawn claims

**2026-08-16 — *"SFT handles sex, DPO handles violence."*** Null at prompt level (H3, base p=0.077) and at word level (L1, +0.0024, CI ±0.047), on two different measurements. `lexical_domains`'s registered stopping rule pre-committed withdrawal on a second null, so it is withdrawn rather than tested a third time. **Nothing in this project may rest on it.** The better instrument did not rescue the effect — it made it smaller (+0.0086 → +0.0052) and less certain (p=0.077 → p=0.45).

**Recorded honestly: L1's operationalisation was later found wrong** — `share` is not a share (JS is not additive along a path), violence was used as sexual's baseline (blind to "SFT handles both"), and the preference step never entered the statistic. The withdrawal fired on a pre-committed test and is **not** being quietly reversed; the claim stands as *not supported as tested*, and the correct test is a new question to be registered with the contrast and baseline agreed first.
