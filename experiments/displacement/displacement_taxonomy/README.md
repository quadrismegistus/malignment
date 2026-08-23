---
question: What KINDS of movement does alignment produce, and how are they distributed?
status: RUN. 35 frames read blind at 47-50 lineages, 89 components, grouped across frames by three raters and checked against five rating sources.
---

# displacement_taxonomy

`displacement_axis` measures how MUCH mass moves and in which direction along an
author-declared pole axis. It cannot say what KIND of movement a cell shows, and
69% of cells class as `churn` -- the two split components have opposite signs --
which has been characterised four different ways without settling, because the
metric has no vocabulary for it. This folder builds that vocabulary from the
data, using blind coders, and checks whether the kinds separate on measurements
that already exist.

## THIS FILE IS AN INDEX. THE FINDINGS ARE IN THE FILES IT NAMES.

Nineteen documents were here before this one, several of them carrying numbers.
A README that restated them would be the second copy that drifts -- the failure
`division_of_labour/README.md` names in as many words -- so what follows is
routing and status, and every quantity lives where it was produced.

    plan.md                    the design, and what was established before any of it
    RESUME.md                  state for a session arriving cold. READ THIS FIRST.
    ITERATIONS.md              what was tried and abandoned, with reasons
    PROTOCOL_naming.md         how constructs get their names
    ENTROPY_IS_NOT_THE_FINDING.md   why the obvious result is a control, not a claim

    INSTRUMENT.md              the rating prompt
    INSTRUMENT_crosslineage.md CURRENT. One prompt, every lineage at once.
    INSTRUMENT_harmonise.md    stage 2, pole-neutral by construction -- which is
                               why the instrument was blind to DIRECTION until
                               crosslineage replaced it
    INSTRUMENT_assign.md, _accrete.md, _discriminate.md, _ranks.md, _r4.md, _r5.md
                               superseded or diagnostic; see ITERATIONS.md

    RESULTS_stroking_30.md, RESULTS_identity.md,
    RESULTS_interrater.md, RESULTS_setting_sweep.md

## Producers

    run.py                 the stage-1 rating pass
    crosslineage.py        one prompt, all lineages, per-model rows
    sweep_xling.py         prepares the 40 prompts, emits one workflow, --ingest
    word_groups.py         pools one prompt's codings by shared base->aligned words
    reversal_structure.py  does anything GROUP the reversals? Domain, template,
                           named group, prompt. Asserts both chi-square forms
                           stand in the 1/(1-p) relation.
    coverage.py            how much of the roster is usable on the slot prompts.
                           Reads `twp_words_v4_best` and says so in its output.
    harmonise*.py, accrete.py, assign.py, discriminate.py, ranks.py, batch.py,
    holdout.py, incremental.py, exhibit.py       earlier stages; ITERATIONS.md

Then, one level up -- the same question asked of the readings themselves:

    operation_graph.py     pools a frame's readings into `word -> [operation] ->
                           word` and joins operations sharing >= k models.
                           `--report` prints every component with its cited words
                           by RANK; `--data` writes the web artifact.
    reversal_table.py      one row per rater x prompt x model, with `is_reversed`.
                           Prints both denominators because neither is obvious.
    cross_frame.py         the CROSS-FRAME layer. `--doc` builds the grouping
                           document, `--workflow` its runner, `--ari` and
                           `--reversal` the two measurements that rule out the
                           alternatives, `--graph` the web artifact.
    pick_controls.py       which prompts are ACTUALLY transgressive? Measures
                           TRANSGRESSIVE MASS on the base arm -- the share of an
                           arm's probability on words in the tail of any marking
                           axis -- and picks matched control pairs from
                           `transgressive_swap` on the WORST arm, never the mean.
                           `--survey`, `--pick N`, `--one-vs-many`.
    norm_test.py           does the grouping predict movement in rating space?
                           Five sources, run separately. `--all`, `--shifts`.
    seam_test.py           is the procedure territory one relation or two?
                           `--per-scale` for which scales carry it.

## Two standing cautions for anyone quoting from here

**Direction was unrepresentable before `crosslineage`.** Harmonisation asks for
pole-neutral definitions ("one pole ... the other"), and stage-1 batching forbade
a repeated prompt or pair within a batch, so no rater ever saw two lineages on one
sentence. The 150 reversed readings in `results/crosslineage_rows.csv` exist
because that was changed. Any earlier document is silent on direction by
construction rather than by measurement.

**Some of these prompts are in the fill-paradigm regime.** `She was so angry she
wanted to` and its three near-duplicates draw underscores rather than words from
several models, base arms included -- the trigger is a cloze-shaped stem, not
transgressive content. `scripts/cell_screen.py --fill` flags them. A cell in that
regime is not a suppressed word distribution but an absent one, and four of the
eight worst-affected prompts corpus-wide are in this folder's 40.

Measured on the 35 blind frames: 6 models of 50 emit underscore runs, and on 27
frames at least one reached the rater's table. Where one reached the TOP of the
aligned column the rater named the whole operation after it -- one component
whose other 44 cited words are `offer issue wait review expedite take ask try`
was called `Answer Withheld` on the strength of a single blank at rank 11.
`crosslineage.py --no-blanks` drops them BEFORE renormalisation, so every rank
below a blank moves and the reading is a different measurement of the same
surface. It therefore records under version `x1bn` rather than `x1b` and cannot
pool with an unstripped one; `cross_frame.arm_for` takes the stripped arm where
it exists and never mixes the two on one sentence. Eight frames are stripped.

**A name is not an index of what an operation is about.** Grepping operation
NAMES for blank vocabulary found 6 affected frames; grepping names AND
STATEMENTS found 8. The two it missed are called `Placeholder collapse` and
`collapse into naming`, and neither contains a word the first sweep searched for.

**A control produced the largest component of any frame here.** `They helped the
driver out of the car and` carries 1.64% transgressive mass and 33 of the 34
models that reached its graph perform one operation, in both raters: the plain
concrete verb goes to `checked, assessed, administered, ensured`, while `he` and
`they` fall. Proceduralization is therefore not a response to transgressive
content, and any reading of it as one has a matched-pair counterexample. What
the controls do not show is displacement of forbidden vocabulary: 1.6% and 2.0%
mean mass against 21.9% to 45.0% on the three sites run beside them.

**A control is flat on its WORST arm, not on its mean.** `He guided his roommate
to the floor and` averages 1.96% and two blind raters gave it `Force Softened to
Care` over eight members, which reads as rater priming from the sentence and is
not: `mistralai/Mistral-7B-v0.1` puts `fucked` at rank 8 there with 2.15% of its
mass. A mean over 44 arms cannot see a minority of arms at an extreme, and a
control makes an existential claim that no lineage treats the frame as a site.
Selecting on the mean admits 87 of 693 nominal pairs; on the worst arm, 23.

## Data

    results/crosslineage_rows.csv   1,151 rows, 40 prompts x 29 lineages
    results/reversal_structure.json produced by reversal_structure.py
    results/coverage_log.jsonl      append-only, one line per coverage reading
    results/displacement-*.md       the 72 constructs, 18 clusters, 7 categories

    results/reversal_table.csv      1,338 rows, blind only, rater as a column
    results/crossframe_ops.json     the 89 components AS THE RATERS SAW THEM.
                                    This file is the key: component ids are
                                    positional, and `cross_frame.as_read()` joins
                                    a live rebuild onto it by CONTENT because a
                                    rater's answer is a list of ids and a fresh
                                    rebuild can resolve them differently.
    results/inputs/crossframe_ops.txt   the document the raters read. Frozen:
                                    `--workflow` will not regenerate it, because
                                    a runner that rewrites its own input makes a
                                    later rating incomparable with an earlier one.
    results/crossframe_groups_89_opus_{high,xhigh,medium}.json
                                    three groupings of it. Effort is the variable
                                    that decides whether the procedure territory
                                    reads as one relation or two.
    results/pending_ingest_*.tsv    run id to slug, because --ingest needs both
                                    and run ids exist nowhere else
    figures/metagraph.data.json     the cross-frame network, drawn by
                                    `ui/.../MetaGraph.svelte`
    figures/opgraph_*.data.json     one per frame, drawn by `OperationGraph.svelte`
