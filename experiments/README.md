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

**THE README IS THE FINDING. There is no `findings/`.** v1 kept 46 findings in a
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
