# experiments/

One directory per QUESTION. Not per theme, not per script.

    experiments/<question>/
        README.md         the question, its id, the population, the claim, the status
        registration.md   OPTIONAL -- see below. Frozen before the first run.
        run.py            THE producer. Writes the result AT ITS GRAIN.
        plot.py           reads the stored result and writes figures/.
        population.json   generated receipt: the exact ids the result used
        results.csv       the result at its own grain, when it is small
        figures/          regenerable output

Only `README.md` and `run.py` are required.

## The rules, and what each one is a response to

**ONE PRODUCER PER DIRECTORY, named `run.py`. A variant is a FLAG, not a file.**
v2's `meta/M01_displacement/scripts/` held 250 scripts for 32 findings — eight
scripts per claim — and the letter prefixes accumulated `k_`×47, `x_`×36, `y_`×26.
**A letter is a namespace, and namespaces fill.** Nobody can now say what `k`
meant. If a thing is not a flag on the existing question, it is a different
question and gets its own directory, which forces someone to name it.

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

M01 accumulated 455 result files beside its scripts, which is what this looks
like when there is no size rule. The rule is the size, not the prohibition.

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
