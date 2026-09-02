# experiments/ -- LAYOUT

**The rules. The FINDINGS are in `README.md`.**

Split out of `README.md` on 2026-09-02 (RH). That file had grown two jobs -- how
the directory is organised, and what the campaign found -- and the second is the
one people come for. Nothing here is new; it is the same text under its own
heading, so that a reader after a result does not have to scroll past a hundred
lines of filing convention to reach one.

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

**A REGISTRATION THAT CANNOT FAIL GOES IN `instrument_calibrations/`.** An
instrument registration declares how something is BUILT; a hypothesis
registration declares what would make a claim wrong. `sex_violence_lexicon` lived
flat and was excluded from the table below by a sentence, which is a rule with
nowhere to live. RH, 2026-08-16. The container arrived with two occupants, not
empty.

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

## TWO OF THE RULES ABOVE ARE NOT BEING FOLLOWED, AND RH HAS SAID SO

**Recorded 2026-09-02, unresolved, RH's.** Neither is amended here, because the
replacement is his call and a rule rewritten by whoever last tripped over it is
not a rule. But leaving them stated as though they held would be worse: a rule
everything violates teaches that the rules are decorative, and the next person
to read this file cannot tell which of these sentences are live.

**ONE PRODUCER PER DIRECTORY -- violated in 30 directories of 52.**

    >1 producer   30
     1 producer   22   (21 of them named run.py, so the NAMING rule holds
                        wherever the count rule does)

    41  passage_analysis/jakobson_space
    28  displacement/displacement_taxonomy
    21  displacement/displacement_axis
    20  instrument_calibrations/dose_response
    17  passage_analysis/national_story
    17  emergence/capacities
    16  slot_ratings/institutional

RH: *"we said just run.py / 1 producer but it turned out impractical for many
experiments."* The counts agree with him. `national_story` at 17 is not an
outlier, it is FIFTH, and the folders above it are the campaign's most productive
ones -- including `jakobson_space`, which at 41 producers already sits INSIDE a
subject, so "too many producers to be a question" is an objection the layout
already overrules in practice. A rule that the best work breaks hardest is a rule describing something
other than quality.

What the rule was actually defending is still real and is worth separating from
its mechanism: v2's 250 scripts for 32 findings, where `k_`x47 and `x_`x36 meant
nothing to anyone and no script could be traced to a claim. **The failure was
untraceable proliferation, not plurality.** `jakobson_space`'s 41 producers each
have a name that says what they do and a README section that cites them; M01's
250 did not. A rule keyed to the count cannot tell those apart, and this one
does not.

**FLAT AT TOP LEVEL UNTIL A SECOND QUESTION ARRIVES -- RH does not want it.**

RH: *"I know we initially said experiments should initially be top level but for
web UI reasons and organisational reasons I dont like it. Not sure what to do."*

The rule was a response to `meta/M01_displacement`, which was created empty and
absorbed everything nearby. That failure is real, and so is the cost RH is
naming: the top level currently mixes subjects (`displacement`,
`passage_analysis`, `slot_ratings`, `division_of_labour`, `emergence`) with
single questions (`posttraining_corpus_analysis`) and with class axes
(`instrument_calibrations`, `exploratory`), and nothing in a directory listing
says which kind a name is. `serve.py` walks that listing.

**Four moves were made on 2026-09-02, all RH's, and the top level went from 12
directories to 8:**

    story_decoder    -> instrument_calibrations/    class move
    mps_sampling     -> instrument_calibrations/    class move, README written
    national_story   -> passage_analysis/           by grain: the text-grain subject
    readout_share    -> displacement/               by scope, and the subject's
                                                    question was extended to cover it

The first two were uncontroversial: they are class moves rather than promotions.
The second two are the substantive ones. `national_story` went in despite being
subject-shaped (17 producers, five separable questions) because the destination
already holds a 41-producer folder, so the objection did not survive contact with
the tree. `readout_share` went to `displacement` because that subject's stated
scope -- "measuring THE MOVEMENT ITSELF" -- is the only one it falls inside, and
the scope line was extended to name the where-in-the-model clause rather than the
folder being filed under a question that excluded it.

**Each move was checked for the depth hazard first, and each time there was
one.** `displacement/README.md` records that the previous regroup silently broke
sixteen producers computing the root as `dirname(dirname(HERE))`. Three such
paths in `national_story`, one in `readout_share`, all now on
`malignment.paths.repo_root()`, all exercised at BOTH depths so that the answer
could be seen not to change. The `.gitignore` had the same disease from the other
side: every `national_story` rule was path-anchored, all of them stopped matching
at once, and git offered the machine-specific sqlite symlink as a new file to
track. Rewritten unanchored.

**The remaining cost is the web UI.** `malignment/serve.py` hardcodes
`EXPERIMENTS/national_story/` at six lines (2208, 2272, 2279, 2331, 2357, 2384)
and is not repaired here -- it carries another seat's uncommitted work, and RH is
handing it to Dario. If it resolves an experiment id to a path instead of
assuming top level, the layout stops being a UI constraint at all, which is the
part of RH's objection that is fixable in code rather than by argument.

## Scratch work

Does not live here. Use the session scratchpad or a gitignored `sandbox/`. The
reason v1 accumulated 477 scripts in `scripts/` is that there was nowhere else to
put something you tried once. **This directory holds questions that have answers.**

---

## Why instrument and hypothesis registrations are kept apart

A registration that makes no claim about the world cannot be tuned toward a finding, because there is no finding in it to aim at. Had L1 lived in the lexicon's registration, every judgment in building the instrument — which words to seed, how strict to make the raters, where to set the control ceiling — would have had a preferred answer sitting on the next page.

The two also fail differently, and the difference is the point:

    instrument registration   worst outcome: "the tool is too loose to use"
    hypothesis registration   worst outcome: "the claim is false and is withdrawn"

**But the separation has a cost and this table is the payment.** Update it in the same commit as any new registration.
