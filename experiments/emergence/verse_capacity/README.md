---
subject: verse_capacity
status: PORTED from M05, 2026-08-24. Numbers recomputed by analyse.py, fleet not re-run.
headline: Pretraining builds rhyme pull to 0.383; SFT erodes it to 0.262. DPO has one checkpoint.
source: ~/github/malign-logits/meta/M05_emergence (read-only archive)
---

# verse_capacity

**When does a model learn that a line-end is owed a rhyme, and what does
post-training do to it?**

The verse fleet ran 2026-08-13 under `plan_verse_fleet.md`, cost ~$37.50, and
delivered four parquets and six figures. **No findings document was ever written
against any of it.** This ports the core instrument. Nothing is re-run; the
archive is read-only and `analyse.py` reads it and recomputes every number below.

## THE INSTRUMENT, AND WHY ITS NULL IS THE GOOD PART

Instrument 1 of the plan's eight. At a **called slot** -- a line-end whose scheme
partner sits in the window -- `called_mean` is the probability mass on the rhyme
partner. The null is the same rhyme-set's mass at **uncalled line-ends and
mid-line slots in the same poem**. `pull_delta = called - null`.

The null is within-poem and deliberately NOT a matched control word-set; the plan
cites "the R decoy lesson" for refusing one. A matched set asserts a
comparability it has not earned. The same poem's own uncalled slots do not.

## 1. IT IS A CAPACITY, NOT A COMPULSION

    ladder   rhymed     called      null       pull   frac>0
    olmo     False      0.0033    0.0131    -0.0025     0.23
    olmo     True       0.2389    0.0177    +0.2185     0.73
    pythia   False      0.0047    0.0133    -0.0043     0.23
    pythia   True       0.1452    0.0073    +0.1382     0.68

**On rhymed poems the model puts ~14-22 points of mass on the partner; on free
verse it puts none, and the sign is faintly negative.** The pull is not a tic
that fires at every line-end. It is conditional on the poem actually having a
scheme, which is what makes it a formal competence rather than a habit. Both
ladders agree, and this is the discriminator the plan declared in advance.

## 2. PRE-1900 VERSE PULLS HARDER, ON BOTH LADDERS

    ladder   era           pull   frac>0
    olmo     1900+       0.1533     0.63
    olmo     pre-1900    0.3886     0.88
    pythia   1900+       0.1215     0.67
    pythia   pre-1900    0.1886     0.80

Two and a half times on OLMo, one and a half on Pythia. "Modernism arrives late"
in its cheapest form: the model's rhyme expectation is much stronger for verse
written before the twentieth century, which is where the scheme is more regular
and more predictable from the corpus.

## 3. PRETRAINING BUILDS IT. SFT TAKES IT BACK DOWN.

    arm         rungs        first -> last     Spearman(step, pull)
    pretrain       42     0.0000 -> 0.3834     +0.769   p = 2.8e-09
    Think-SFT      43     0.3691 -> 0.2620     -0.591   p = 3.1e-05

**Pretraining installs the capacity from nothing to 0.383. Supervised
fine-tuning then erodes it by 29%, monotonically across 43 rungs.** The decline
is fast and then flat: the SFT ladder's median is 0.267 against a maximum of
0.369 at step 1000, so most of the loss has happened within the first few
thousand steps.

**This is the same shape as Findings U, in a different faculty.** U established
that SFT does the cutting for displacement. Here SFT does the cutting for a
formal capacity that pretraining had built. Whatever SFT is, it is not additive
over what came before.

### THE GROUP-MEDIAN VERSION OF THIS IS BACKWARDS, AND I GOT IT WRONG FIRST

Comparing arms by their medians gives pretrain 0.215 against Think-SFT 0.283 and
says SFT ADDS pull. That is an artefact: the pretrain ladder spans the whole
developmental range including the early rungs where the capacity does not exist
yet, so its median is dragged down by checkpoints that have not learned to rhyme.
The SFT ladder starts where pretraining finished. **Compare trends within an arm,
never medians across arms whose ladders cover different ranges.**

## 4. THERE IS NO DPO LADDER, SO THERE IS NO SFT-VS-DPO RESULT

    Olmo-3-1025-7B          0.3834     pretrain endpoint
    Olmo-3-7B-Think-DPO     0.2682     n = 1
    Olmo-3-7B-Think-SFT     0.2619     n = 1

42 pretrain rungs, 43 Think-SFT rungs, and **exactly one DPO checkpoint.** DPO
sits 0.006 above the SFT endpoint, which on a single checkpoint is not a
measurement of anything. The question the ladder was built to answer for
displacement -- SFT or DPO -- **cannot be answered here for verse.** Any
statement that DPO leaves rhyme alone is a statement about one model.

## WHAT THIS IS NOT, AND IT MATTERS FOR THE BOOK

**Pull is not production.** This measures p(the poem's own rhyme partner) under
teacher forcing, on existing poems. It does NOT measure whether the model rhymes
when it writes. The fleet deferred generation on purpose -- "twp first,
generation decided later."

RH's *Generative Formalism* reports **~50pp more rhyme after instruction-tuning**,
measured on generated verse, and refutes the training-data explanation directly
(poems in the training data are not disproportionately rhyming). That result and
this one point opposite ways only if pull and production are the same quantity.
They are not, and the coherent reading is that **instruction-tuning makes a model
rhyme more in its own verse while tracking a given poet's chosen partner less** --
more formulaic, less attentive. That is a hypothesis this instrument cannot test,
and generating from the SFT ladder is what would test it.

## WHAT WAS MIGRATED, AND WHAT THE COPIES CAN AND CANNOT DO

Copied 2026-08-24 -- **copy, not move.** The archive still holds every one of
these and was not written to. All five data files verified **md5-identical** to
their sources, and `analyse.py` reproduces its numbers to the digit from the
local copy.

    results/         verse_capacity_cells.parquet    14M, 404,176 cells
                     verse_capacity_rungs.parquet    67K, the analysis-ready table
                     verse_error_rates.parquet       7.5K
                     capacities_by_rung.parquet      94K
                     capacity_examples.md            26K

    producers/       verse_capacity.py               writes cells + rungs
                     aggregate_capacities.py         writes capacities_by_rung
                     m05_capacities_overview.py      writes verse_error_rates
                     m05_capacity_examples.py        writes capacity_examples.md
                     verse_capacity_figs.py          the figures
                     verse_fleet_producer.py         the fleet runner
                     rhyme_pull_pilot.py             `last_word`, imported by it

    registration/    plan_verse_fleet.md             the declared design
                     plan_rhyme.md

**THE PIPELINE RUNS HERE, AND WAS VERIFIED BY RUNNING IT.** Repointed
2026-08-24: `ROOT` is now the experiment folder, `OUT` is `results/`, the
`malign_logits.` database prefixes are gone (the live `ch._guard` refuses any
statement naming another database), and `from malign_logits import ch` is now
`from malignment import ch`.

    experiments/emergence/verse_capacity/producers/verse_capacity.py --out DIR
    ... /aggregate_capacities.py --out FILE
    ... /m05_capacities_overview.py          # figures/

**The re-run against `malignment.twp_words` reproduces the archive exactly.**

    verse_capacity.py     1,000 shared rung rows, max abs diff 0.000e+00 on
                          called_mean, null_mean, pull_delta_mean/median,
                          frac_positive, copy_called_mean, n_cells_present
    aggregate_capacities  10,404 rows matched on the full key, 0 unmatched
                          either way, max abs diff 1.19e-07 (float32
                          round-trip, on `censored` only)

and it GAINS a checkpoint: `Olmo-3-7B-Think`, 251 models against the archive's
250, measured into `twp_words` after the fleet ran.

### TWO THINGS THE MIGRATION HAD TO DECIDE

**`rule_version = 3` was dropped, and that is exactly equivalent here.**
`malignment.twp_words` has no `rule_version` column (nor `t1`, `theta`,
`dict_sha`, `ingested`). Checked before removing the filter: all 33,148,202
archive rows for this fleet's cells carry `rule_version = 3`, the sole value.

**`twp_residual` DOES NOT EXIST in the live db**, so `censored` cannot be
recomputed there. It holds expand's theta=0.001 residual and feeds
`censored_called_mean`. The merge is now conditional and **announces the
absence** rather than defaulting: a NaN is honest, a 0.0 would read as "nothing
was censored", which is the opposite of not knowing. Every other column is
unaffected, and `results/` still holds the archive's parquets WITH `censored`
intact -- which is why `aggregate_capacities.py` still reproduces it.

### `--out` EXISTS BECAUSE THE FIRST VERIFICATION RUN DESTROYED ITS OWN CONTROL

Both producers wrote straight into `results/`. `aggregate_capacities.py` ran
once that way and REPLACED the archived `capacities_by_rung.parquet` -- the file
the comparison was against. Recoverable only because it was already committed.
Both now take `--out`, and a verification run must use it.

`verse_fleet_producer.py` and `rhyme_pull_pilot.py` are NOT repointed and remain
provenance: they regenerate the raw fleet data through the archive's `twp`
machinery, which is a different job from re-reading the store.

## THE SOURCE twp DATA IS IN THE LIVE DB, BUT IT IS NOT THE SAME DATA

The fleet read `twp_words` (NOT `twp_words_v4`). Checked 2026-08-24, both stores:

    malign_logits.twp_words    95,180,535 rows    the archive, what the fleet read
    malignment.twp_words       94,887,319 rows    the live db

All **250 fleet checkpoints are present in the live db**, none missing, 49.2M
rows against the archive's 49.3M. So the migration happened and is complete at
the checkpoint level.

**AND ON THIS FLEET'S OWN DATA THE TWO STORES ARE IDENTICAL.** Restricted to the
250 fleet checkpoints x the 1,586 prompts the cells table actually uses:

    archive   33,148,202 rows   1,586 prompts   250 models
    live      33,148,202 rows   1,586 prompts   250 models
    sum(cityHash64(word)) matches exactly

Every `(model, prompt)` cell the fleet used is present in the live db -- checked
per model, **0 missing across all 250**. A recompute from `malignment.twp_words`
would read the same rows.

> **CORRECTED, same day.** An earlier version of this section said "re-running
> against the live db would not reproduce these numbers." That was wrong, and
> wrong in an instructive way: the two stores DO differ in total, by 293,216 rows
> overall and on 113 of 250 checkpoints in BOTH directions, and I generalised
> from that to the fleet's data without restricting to it. The difference lives
> ENTIRELY in prompts the fleet never used -- other experiments on the same
> checkpoints. Whole-table counts answered a question nobody asked.

The store-level difference, kept because it is true of the stores and someone
will hit it on other work:

                        archive                        live
    Olmo-3-1025-7B      4,413 prompts  497,440 rows    4,428 prompts  474,663
    pythia-6.9b         4,413          517,478         4,428          495,894
    Think-SFT           4,378          390,111         4,393          391,264

The live store carries 15 MORE distinct prompts on every model. Its row deficit
on the two base endpoints is in those non-fleet prompts, not here.

## WHAT IS STILL OWED FROM THIS FLEET

Eight instruments were declared; this ports ONE. Now local in `results/` and
unanalysed:

- **Instrument 8, copy-pull vs rhyme-pull.** `copy_called_mean` and
  `censored_called_mean` already ride in the rung table, and
  `p_actual_word` / `p_nonpartner_word` / `p_target_word` sit per-cell in the
  404,176-row `verse_capacity_cells.parquet`. The plan's framing: "rhyme is
  repetition-with-difference, and the gap between the curves is the acquisition
  of the difference." Everything needed is on disk; no run required.
- **The error-rate surface.** `verse_error_rates.parquet`, 500 rows of
  miss/false_alarm by margin over rhymed and unrhymed poems. Bears directly on
  whether the pull measure has a usable operating point.
- **The cell-level covariates.** `collides` and `censored` are per-cell flags
  that nothing here conditions on. `censored_called_mean` runs ~0.19-0.39 in the
  rung table, which is large enough that the headline pull could move under it.
  **This is the one that could change a number in this README.**

Not from this fleet but owed beside it:

- **Instrument 6, the P-axis installation** (`p_axis_installation.json` in the
  archive, not copied here): rho/CI/n for axis, armAUC, delta, named and
  residual measures at SFT, DPO and Instruct rungs, floored and no-floor. Its
  plan (`plan_p_axis_installation.md`) declares P1/Q1/Q2 directions and nothing
  has been read against them. The plan's own fence: the axis's stability gate
  still fails, so it is a descriptive drift curve and not a named-axis verdict.

## WHAT ELSE IS IN THE ARCHIVE AND STILL UNREAD

The fleet declared eight instruments and this ports one. Also delivered and with
no write-up:

    verse_capacity_cells.parquet    404,176 cells -- per-slot, with tclass,
                                    nclass, phase, scheme, era, collides,
                                    censored, p_target/p_nonpartner/p_actual
    verse_error_rates.parquet       500 rows, miss / false_alarm by margin
    capacities_by_rung.parquet      10,404 rows across measures and families
    capacity_examples.md
    p_axis_installation.json        instrument 6, the interiority axis across
                                    rungs -- a separate owed write-up

`copy_called_mean` and `censored_called_mean` ride in the rung table and bear on
instrument 8 (copy-pull vs rhyme-pull, "rhyme is repetition-with-difference").
Not analysed here.
