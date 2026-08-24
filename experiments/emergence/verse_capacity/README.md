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
