# experiments/

One directory per QUESTION. Not per theme, not per script.

    experiments/<question>/
        README.md         the question, its id, the population, the claim, the status
        registration.md   what was declared BEFORE the first run. Append-only.
        run.py            THE producer. Writes long form to ClickHouse.
        plot.py           reads the STORE and writes figures/. Never reads run.py.
        population.json   generated receipt: the exact ids the result used
        figures/          regenerable output

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

**NO DATA IN THE DIRECTORY.** Long form goes to ClickHouse (see `RESULTS.md`).
M01 accumulated 455 result files beside its scripts; that is what "results live
next to code" looks like at scale. `figures/` holds regenerable output and
`population.json` holds the receipt.

**A REGISTRATION IS FROZEN OR IT IS NOT A REGISTRATION.** `registration.md` is
committed before `run.py` is first run, and is never edited afterwards —
amendments append with a date and a reason. A pre-registration editable after
seeing the result is a post-hoc rationalisation with better typography.

## Scratch work

Does not live here. Use the session scratchpad or a gitignored `sandbox/`. The
reason v1 accumulated 477 scripts in `scripts/` is that there was nowhere else to
put something you tried once. **This directory holds questions that have answers.**
