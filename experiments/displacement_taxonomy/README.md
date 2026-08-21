---
question: What KINDS of movement does alignment produce, and how are they distributed?
status: RUN. Cross-lineage instrument current; the 40-prompt sweep is at 26-29 lineages and the roster now supports 46.
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

## Data

    results/crosslineage_rows.csv   1,151 rows, 40 prompts x 29 lineages
    results/reversal_structure.json produced by reversal_structure.py
    results/coverage_log.jsonl      append-only, one line per coverage reading
    results/displacement-*.md       the 72 constructs, 18 clusters, 7 categories
