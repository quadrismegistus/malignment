---
subject: named_under_dose
status: building
question: |
  Findings P asked whether the named vocabulary predicts WHICH WAY alignment moves a
  word, held out by word, and answered no: 18 rated norms recovered 7% of the
  measured headroom against unsupervised embeddings' 18-21%. P tested that MARGINALLY.
  This folder asks P's question CONDITIONED ON DOSE.
---

# Do the named norms predict direction better where the base arm is transgressive?

**Where the ratings come from.** The contextual ratings this folder consumes are
commissioned by `experiments/instrument_calibrations/contextual_norms/` --
`priority.py` builds the manifest, `rate.py` runs the v6 instrument, and
`fields.contextual_norms` is the read path. Two defects found HERE sent work back
THERE and are recorded in that folder's README sections 5 and 6: rating coverage that
was correlated with dose, and a `--pos VERB` filter that deleted noun-slot prompts
instead of thinning them. Numbers in this file that predate those fixes are marked.

## THE QUESTION, AND WHY IT IS WORTH ASKING AGAIN

`malign-logits meta/M01_displacement/findings/P_unnamed_axis.md`:

> **THERE IS A WORD-LEVEL DIRECTION ALIGNMENT SORTS ON, IT IS NOT IN OUR DESCRIPTIVE
> VOCABULARY, AND THE UNNAMED RESIDUAL OUTPREDICTS EVERY NAME WE HAVE TRIED.**
> Held out by word, none of the eighteen rated norms predicts which way alignment
> moves a word. Word identity carries +0.121 AUC of headroom over base probability;
> 300 GloVe dimensions recover 18-21% of it against the rated norms' 7%.

P measured that **marginally** -- one model pooled across all sites. The 2026-08-24
work in `experiments/displacement/norm_change/` found that many named norms are
**DOSE ONLY**: flat on average and steep where the frame carries transgressive mass.

    k_concreteness       MARGINAL p=0.119   DOSE p=1e-5
    warriner_dominance   MARGINAL p=0.085   DOSE p=9e-5
    k_charge             MARGINAL p=0.533   DOSE p=2e-5
    vocalisation         MARGINAL p=0.480   DOSE p=9e-5

**So P's 7% may be a marginal 7%.** If the named vocabulary works where the frame is
loaded and not elsewhere, it is context-dependent rather than inadequate, and P's
ceiling was measured in the wrong condition. If it does not, P stands harder than
before, because the most favourable condition has now been tried.

**A prior worth recording before the run.** `displacement_axis/LINEAGE_AND_DOSE.md`
asked a mass-weighted cousin of this question and got a null: named dimensions beat
their own permutation 1.13x at low dose and 1.14x at high, gain 27/50, p=0.67. That
is not this test -- it holds out nothing and scores the centroid rather than the word,
and the folder's own fence says the two quantities disagree informatively -- but it
means a null here would be the second null, not a surprise.

## WHY NOT IN displacement_axis

That folder has a dose variable and the naming machinery, so it looks like the home.
It is not:

    displacement_axis                    here
    15,150 cells, 255 pole-tagged        19.0M rows over 2,720 prompts,
      slot prompts                         3.37M with movement
    axis-scored vocabulary               146,266 words; 7,571 with >=20 moving cells
    dose = base_naughty_mass, mass on    dose = k_transgressiveness, a rated
      a MEDIAN-5-WORD hand list            continuum, 401,886 (lineage, prompt) values

**P's test generalises over WORDS.** Running it on a pole-tagged vocabulary at 255
prompts restricts range on the dimension under test -- the same defect that makes
M01's own minimal pairs a weak foundation (`M01_RECONSIDERED.md`: the two arms differ
by 3% of the available transgressive range). P used 100,958 cells; this uses 3.37M.

What IS borrowed from displacement_axis is its protocol discipline, all of it bought
expensively: **a reachable benchmark scored by the identical rule the models get,
never a ceiling fitted on the target**; a known-perfect predictor as a row in the
table; bge as a **ceiling on naming rather than a neutral contest**, since it is
trained on the same kind of corpus; and the growth curve printed so that
n-boundedness is visible instead of assumed.

## DESIGN

    POPULATION   `movement`, restricted to roster.endpoints() -- 50 base->aligned
                 pairs -- and to cls != 'still'. 3.37M cells (1.79M faller,
                 1.58M riser), 146,266 words, 2,720 prompts, en and zh.
    UNIT         the WORD. GroupKFold on word, so no word appears in both the
                 fitting and the held-out fold. This is P's unit and the reason
                 its result is about the vocabulary rather than about memorisation.
    OUTCOME      direction: +1 riser, -1 faller. P's outcome family, unweighted --
                 a word at p=0.0001 counts as much as one at p=0.18.
    DOSE         `k_transgressiveness` base-arm level per (lineage, prompt), from
                 norm_change's levels_long. Measured BEFORE alignment, so a loaded
                 frame is free to move up, down or not at all.
    FEATURES     fields.py norms (17 per word: the k_ratings 7, Brysbaert
                 concreteness, the four Warriner scales, coverage and counts)
                 against bge principal components on the same words.
    BENCHMARK    reachable, not a ceiling. Split a word's own cells in half within
                 the stratum and predict half B from half A, scored by the identical
                 function the models are scored by.

## THE CONTROL THAT MAKES THE COMPARISON MEAN ANYTHING

**Dose is confounded with vocabulary.** High-dose prompts contain different words from
low-dose prompts, so a naive low-vs-high comparison measures "are transgressive words
easier to predict" and not "does a loaded frame help". Both answers are interesting
and only the second is P's question.

**So the strata are evaluated on the SAME WORDS.** A word enters only if it has enough
moving cells on BOTH sides of the dose split; the word set is then held fixed and only
the dose varies. Any AUC difference is then attributable to the frame rather than to
which words were in it. This is `adjacency-asserts-a-shared-population` applied before
the fact rather than after.

Secondary, reported alongside and never instead: the unrestricted comparison, which
answers the vocabulary question and must not be read as answering P's.

## LICENCE TO EXPLORE

Registered lightly, on the pattern of `norm_change/registration.md`. The primary test
is the shared-word conditional AUC above. Everything else here -- per-language splits,
per-norm contributions, whether specific scales carry the conditioning -- is
EXPLORATORY, is a candidate for a hypothesis rather than a result, and is labelled so
in the output.
