---
subject: passage_analysis
question: What survives from the policy to the page?
---

# Passage analysis

**A SUBJECT, not an experiment.** It holds questions; it holds no code, no data and no claims of its own. Anything shared between its questions belongs in `malignment/`, not here.

Every other experiment in this repo measures a **distribution**: what the model would say next, as probabilities over a vocabulary, at one slot. This subject measures **text**: what the model actually writes when you sample from that distribution for a couple of hundred tokens at temperature 1.

The two grains are not the same object and the difference is the point. A structure can be overwhelming in the distribution and invisible on the page, because sampling is lossy and autoregression carries its own momentum. So a claim proved at one grain is a hypothesis at the other, and this subject exists so that nobody quietly moves a result across without measuring it.

## What is already known about the trip, and by whom

**`P_unnamed_axis.md`** (malign-logits `meta/M01_displacement/findings/`) established the signature in the distribution: a classifier reads base from aligned out of word probabilities at AUC 0.956, held out by ORG. Its provisional name for the direction is INTERIORITY, *enacted -> represented*, worth roughly a quarter of it.

**`p_on_passages.md`** (malign-logits `meta/M06_generation/findings/`) asked whether that survives sampling, on 232,384 undisturbed passages over 41 pairs. In short: **the signature is an accent, not a flinch.**

    I3  does the word ordering survive?     Spearman +0.500, same prompts and models
    I2  can you tell the arms from a page?  0.39-0.50 above the null mean, k=25..200
    I5  force a demoted word -- recoil?     no; BOTH arms drag base-poleward, DiD p=0.63
    I6  transgressive site vs neutral?      no; both drag equally, DiD p=0.90

I6's conclusion, and the sentence this subject exists to test rather than inherit: *"The interiority signature is TONIC: a constant register shift, not a site-conditional deployment. Site-specificity lives only at the distribution grain."*

**`interiority_in_passages/`** (this repo, COMPLETE) is the human-coded version of the same trip and agrees on direction: alignment does not change how models represent inner life, it changes how much of it there is. H1 +0.224, 16/17 pairs, p=0.00015.

## The gap, and it is the reason to have a folder rather than a citation

**I6 tested six domains and neither of ours is among them.** Its decomposition runs `animal / betrayal / property / sexual / taboo / violence` on the M01 twin pairs. `identity` and `institutional` were never in it -- and those are the two domains where the mass-weighted results in `experiments/displacement/displacement_axis/` are strongest (`fit` 47/55 p=8.1e-08; `harm` 20/20) and the two where the declared pole axis is null.

So the tonic reading is established where it was measured and **untested where our current results live**. Two further cautions before anyone treats it as settled:

- the overlap that does exist is by domain NAME, not population: I6's `violence` is the M01 twin corpus, not pilot3's slot frames
- `property`, the most institution-adjacent domain in I6's set, is the one lean toward a page-grain DiD (-0.00133, p=0.09) and the only domain where the base arm shows a marked-excess (p=0.0008) while the aligned arm shows none

Nowhere near quotable. Exactly the shape a site-conditional page-grain effect would have, in the domain nearest the one F21 argues about.

## Questions here

    interiority_in_passages/    COMPLETE. Does alignment shift passages toward
                                interior state? It does not change HOW inner life
                                is represented, it changes HOW MUCH there is.
                                H1 +0.224, 16/17 pairs, p=0.00015.
    diegetic_superego/          COMPLETE, migrated. When alignment moralises, does
                                it leave the scene or stay inside it? It stays: the
                                extra-diegetic response is FLAT while the
                                intra-diegetic one moves ~4x, and it survives a
                                forced-word control (+5.0 pts, p=7.2e-08).
    second_order_naming/        COMPLETE, migrated. Does alignment name the
                                contradiction AS a contradiction? 3.37x the odds
                                [1.88, 6.30], p=9.6e-06, control at 1.00 -- and
                                only for contradiction, not transgression.
    selection_and_combination/  COMPLETE, migrated. Does alignment change WHICH
                                words appear or what they COST in context? It is
                                composition, near-entirely: -1.310 of a -1.285
                                nats/word drop, against +0.025 for level. Selection,
                                not combination -- Jakobson's axes as an arithmetic
                                partition that sums exactly.
    drift_geometry/             PORTED, new analysis not yet run. What the
                                geometric drift metrics can mean (total_drift is
                                order-INVARIANT and 92% noise per passage;
                                directedness IS sentence count, rho -0.923), and
                                whether mean_drift tracks what a reader calls
                                staying in the scene.
    predicting_aligned_text/    OPEN, and NOT blocked by the fleet. Can the arm be
                                predicted from a page, and can NAMED scales do it?
                                Its corpus is gen_sequences, not twp, so it does
                                not wait on lineage coverage the way the
                                distribution-grain work does.
    syntagmatic_damage/         PORTED, not re-run. When a model is forced to utter a
                                word alignment demoted, what happens to the sentence
                                around it? Nine archived measurements synthesised:
                                alignment changes SELECTION and leaves COMBINATION
                                alone. One gap named -- no true third-party scorer has
                                ever read a forced passage.

## The tension worth keeping visible

`predicting_aligned_text/` inherits I6's conclusion that the page-grain signature
is TONIC -- transgressive sites drag BOTH arms equally, DiD p=0.90, so alignment
neither amplifies nor defends there. `diegetic_superego/` finds a site-conditional
moral response on sexual scenes that survives a forced-word control.

Both can be true: guilt-attachment is not the axis I6 measures, and they run on
different corpora with different instruments. But **nobody has put them on the
same passages**, and until someone does, "the signature is tonic" and "alignment
moralises inside the scene" are two claims about the page that have never been
made to meet. That is a question, not a bookkeeping problem.

Note also that I6's six domains are `animal betrayal property sexual taboo
violence` -- so `sexual` IS in it, which makes the meeting cheaper than it looks.

## TWO THINGS HERE ARE CALLED "DRIFT" AND THEY ARE DIFFERENT OBJECTS

    interiority_in_passages/   CODED    HOLDS / SHIFTS / UNMOORED, blind Opus
                                        readers, raw 95.0%, kappa 0.904
    drift_geometry/            GEOMETRIC  computed from sentence embeddings:
                                        mean_drift, total_drift, directedness

Neither supersedes the other and the audit in `drift_geometry/` does NOT reach
interiority's H3 -- a coder reading in order is not noise-limited, has no
directedness and no truncation, and is already aggregated to the lineage pair.

**They may converge, which is the interesting part.** Interiority finds alignment
raises `drift = HOLDS` (+4.726pp, 14/17 pairs); the audit notes in passing that
drift FALLS under alignment. Less dispersion and more holding are the same claim
from two instruments. Testing that is what `drift_geometry/` is for.

## One shape showing up at both grains

`selection_and_combination/` reports, from the page: direction predicts composition
(`net_fall` 36/36) and volatility does not (`pct_moved` 18/36, exact chance).
`experiments/displacement/displacement_axis/` reports, from the distribution and by a different
estimator: direction is nameable (`harm` 44/47 frames, p=2.5e-10) and magnitude is
not (every named scale negative alone). Neither knew about the other.

That is the asymmetry to carry into the writing, and it is stronger for having been
found twice: **alignment has a direction you can name and a magnitude you cannot.**
