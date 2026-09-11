---
type: subject
kind: subject
status: "OPEN 2026-09-11, split out of displacement/architecture the same day it outgrew it. Four questions; three run, rhyme is spec-only. The folder was moved because rhyme pull is not a displacement question and because the subject's headline finding came from none of the displacement instruments."
question: Does the architecture a model is built from exert itself anywhere we can measure?
headline: "So far, nowhere. Corpus dominates and architecture does not register: the most similar pair of 1,225 bases is a transformer and an RNN that share the Pile, and a model computing no attention at all is the median of the census. Every instrument here reads one window, though -- what a model puts in a slot -- and rhyme, the one built to read a formal equivalence class instead, has not been run."
---

# architectures

**A SUBJECT, not an experiment.** It holds questions; it holds no code, no data and no claims of its own. Anything shared between its questions belongs in `malignment/`, not here.

## Why this is a subject and not a folder under `displacement`

It began as `displacement/architecture` and outgrew that in a day, in two ways that the layout rules caught before anyone argued about it. It accumulated three producers, against the one-producer-per-directory rule, which is what a directory does when it is holding more than one question. And its headline result came from none of the displacement instruments: it came from a pairwise similarity sweep over 50 bases, which is not a displacement measurement at all. Rhyme pull, the direct test of the claim the subject exists to contest, is not a displacement question either.

    displacement    does charge-selective displacement depend on attention?   DELTA
    norm_change     does movement along word norms depend on attention?       DELTA
    similarity      do the models differ by architecture AT ALL?              BASE + ALIGNED
    rhyme           does rhyme pull depend on attention?                      SPEC ONLY

**The two delta questions are the weak ones and are kept for the record rather than for the claim.** Alignment is the most architecture-independent stage in the pipeline -- broadly shared SFT mixtures, broadly shared DPO recipes, often the same public corpora -- so a convergent delta across the roster substantially records convergent post-training. `similarity` asks at base, where the answer does not inherit that.

## The contest

Weatherby's *Language Machines* (2025) locates the poetic function in the transformer's attention mechanism: "the transformer architecture gives us quantitative aboutness" (161-62), and computation and language "share form" as "a demonstrable technical fact". The claim is architecture-specific by construction. He hedges it once, and the hedge is the testable part: attention is "probably just one way, we do not yet know of any others, to make this function computationally manipulable" (155), with a note pointing at Google's Griffin, "RNNs with local attention" (227n26).

That Griffin model is in this census. So is a model with no attention at all.

**A note on where the paradigm actually lives, because it predicts the results below.** Attention relates positions within a sequence: items present together in the chain, Saussure's *in praesentia*, which is the syntagmatic axis. The paradigmatic axis is constituted by what could have filled the slot and did not, *in absentia*, and attention never touches an absent alternative. The each-to-all structure is the unembedding matrix and the output softmax, where the hidden state is scored against every vocabulary item and normalised against all of them. Every model in this census has that, transformer or not. **Three of the four questions here read the output distribution, which is exactly the architecturally invariant part** -- so their nulls are what one should expect, and `rhyme` is the one that reads something else.


## TWO TURFS, AND EVERY RESULT BELOW BELONGS TO ONE OF THEM


**This folder originally ran one question and reported it as two.** The correction, RH 2026-09-11, and it is the frame for everything here.

    HIS TURF     a claim about the ARCHITECTURE: does the mechanism realize
                 the poetic function? A property of a model, testable on a
                 BASE model, with no reference to post-training at all.

    OURS         a claim about the OPERATION: alignment displaces along a
                 chain of permitted substitutes, and the wave misses it
                 because it reads theory off the aligned surface. A
                 base->aligned DELTA, and the delta is the point.

`existence` and `norm_change` are delta instruments. `existence` regresses (p_aligned - p_base) on scene; `norm_change` regresses (aligned - base) on the base dose. **Neither speaks to a claim about an architecture**, and the sentence this README carried until today -- that the transformer "demonstrates nothing about language that autoregression had not already" -- did not follow from either and is withdrawn.

**The delta is close to the worst place to look for an architecture effect,** which makes the null it produced much weaker than it first reads. Alignment is the most architecture-independent stage in the pipeline: broadly shared SFT mixtures, broadly shared DPO recipes, often the same public corpora. Convergent deltas across architectures are substantially evidence that post-training converged. This folder's own `norm_change` section says so without having been asked: agreement with the roster median tracks how much a model was ALIGNED, and the two dissenters are the two weakest movers. A quantity dominated by post-training cannot be informative about construction.

So the folder now runs both arms, and labels which turf each result stands on. **What survives on our turf** is the original finding, unchanged and now correctly scoped: alignment's operation does not depend on the architecture it runs on. **What is needed on his** is a base-level capacity read, and the honest position is that this folder held none until today.

## Where the metadata comes from


`roster/models/models.yaml` has no architecture field, and it is AUTHORED (hand-edited, no script writes it), so this folder does not add one. What it does have is `env.profile: ssm`, an environment requirement (mamba-ssm and causal-conv1d kernels) carrying its own `why`, which picks out the SSM and hybrid families exactly. The rest comes from `roster/models/attestations.json`, whose `notes` carry sourced architecture prose at `confidence: high`.

`run.py` declares the architecture of every departure from the default and cites the source inline. **The default is a dense transformer with full attention.** Nothing is coded as unknown.

Two axes, because they cross:

    attn    full | full+linear | local+linear | full+ssm | linear | none
    block   dense | moe | ssm | hybrid

`recurrentgemma` is local attention AND linear recurrence; `Olmo-Hybrid` is full attention AND linear attention. A single axis would have to collapse them into the same cell.
