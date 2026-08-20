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

**I6 tested six domains and neither of ours is among them.** Its decomposition runs `animal / betrayal / property / sexual / taboo / violence` on the M01 twin pairs. `identity` and `institutional` were never in it -- and those are the two domains where the mass-weighted results in `experiments/displacement_axis/` are strongest (`fit` 47/55 p=8.1e-08; `harm` 20/20) and the two where the declared pole axis is null.

So the tonic reading is established where it was measured and **untested where our current results live**. Two further cautions before anyone treats it as settled:

- the overlap that does exist is by domain NAME, not population: I6's `violence` is the M01 twin corpus, not pilot3's slot frames
- `property`, the most institution-adjacent domain in I6's set, is the one lean toward a page-grain DiD (-0.00133, p=0.09) and the only domain where the base arm shows a marked-excess (p=0.0008) while the aligned arm shows none

Nowhere near quotable. Exactly the shape a site-conditional page-grain effect would have, in the domain nearest the one F21 argues about.

## Questions here

    interiority_in_passages/    COMPLETE. Does alignment shift passages toward
                                interior state? Human-coded, 26 lineage pairs,
                                10,355 passages, blind coders.
    predicting_aligned_text/    OPEN. Can the arm be predicted from a page, and
                                can NAMED scales do it -- the page-grain version
                                of the distribution-grain question answered in
                                experiments/displacement_axis/.
