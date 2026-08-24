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

**THE PRODUCERS ARE PROVENANCE, NOT A RUNNABLE PIPELINE HERE.** They are copied
so the numbers can be audited against the code that made them, and they will NOT
execute in place:

- `ROOT = HERE/../../..` resolved to the archive's repo root; under this path it
  resolves to `experiments/`, which is wrong.
- Outputs are hard-coded archive-relative, e.g.
  `OUT = "meta/M05_emergence/results/capacities_by_rung.parquet"`.
- `verse_capacity.py` does `from malign_logits import ch`, the archive's package
  and its ClickHouse layer, and reads `twp_words` -- so re-running the fleet
  means the archive's environment and its store, not this one.

Repointing them is a real port and has not been done. `analyse.py` is the only
file here that runs against the local copy, and it reads the rung table only.

## THE SOURCE twp DATA IS IN THE LIVE DB, BUT IT IS NOT THE SAME DATA

The fleet read `twp_words` (NOT `twp_words_v4`). Checked 2026-08-24, both stores:

    malign_logits.twp_words    95,180,535 rows    the archive, what the fleet read
    malignment.twp_words       94,887,319 rows    the live db

All **250 fleet checkpoints are present in the live db**, none missing, 49.2M
rows against the archive's 49.3M. So the migration happened and is complete at
the checkpoint level.

**It is not a copy, and re-running against the live db would not reproduce these
numbers.** Row counts differ on 113 of 250 checkpoints and the difference runs
BOTH ways -- the archive is ahead on 61 (+44,697) and the live db on 52
(-2,552). It is concentrated on the endpoint models, and the composition says
what happened:

                        archive                        live
    Olmo-3-1025-7B      4,413 prompts  497,440 rows    4,428 prompts  474,663
    pythia-6.9b         4,413          517,478         4,428          495,894
    Think-SFT           4,378          390,111         4,393          391,264

**The live store has MORE distinct prompts (+15 everywhere) and MORE distinct
words, but FEWER rows on the two base endpoints.** Broader coverage, shallower
per cell. That is a different measurement generation, not a subset or a truncated
transfer.

So: the numbers in this README are the archive's, `results/` holds the archive's
parquets, and anyone recomputing from `malignment.twp_words` should expect small
differences and should say which store they read.

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
