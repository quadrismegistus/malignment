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

### CORRECTED 2026-09-11: why the delta questions are weak, and it is not because they are deltas

An earlier version of this file said deltas are weak *as such*, because alignment is the architecture-independent stage and a convergent delta records convergent post-training. RH pushed on it and that framing is close to backwards.

**A DELTA DIFFERENCES OUT THE CORPUS.** Within a lineage, base and aligned share a pretraining corpus exactly. And corpus is the confound that has destroyed every level measure in this subject -- "corpus dominates, architecture does not register" is its main finding, reached twice, at the slot grain and the page grain. So a delta removes precisely the nuisance that swamps a level.

The delta's own confound is that ALIGNMENT data varies across labs. That is controllable and we hold controls for it: the Dolci mixtures across the two Olmo ladders, Tulu-3 across the Llama arms.

**So a delta with alignment data controlled is the only design here that removes the corpus confound**, and it is the best instrument in the subject rather than the worst. There is exactly one such contrast in the roster: `Olmo-3-1025-7B` against `Olmo-Hybrid-7B`, same lab, attested-identical Dolci SFT, a single-variable swap of the local attention mechanism.

`displacement` and `norm_change` are weak for the narrower reason: **alignment data is NOT controlled across their 50 lineages.** That is a different criticism with a different remedy -- restrict to shared-mixture lineages -- and it is fixable, where "deltas are the wrong idea" would not have been.

## THE NULL LEDGER: every place architecture has been looked for and not found

**Recorded as data points, because a null is only worth something if the population it was sought in is written down.** Each row is a distinct instrument, not a re-run of one.

    instrument                grain / regime                 n on the thin side      result
    similarity --arm base     slot probabilities, 50 models  1 pure SSM, 1 RNN       falcon-mamba rank 25/50, MEDIAN of the census
    similarity --arm aligned  slot probabilities, 50 models  same                    aligned models spread 0.407 -> 0.669, no arch signal
    similarity --grain page   page vocabulary, 35 lineages   2 SSM, 1 hybrid, Griffin same vendor DIFF block beats same vendor SAME block
    combination               page drift, 188 words          1 SSM, 1 hybrid, 1 MoE  falcon-mamba 3/6; whole range spanned by dense
    combination --spread      page drift, 37 models          2 SSM, 1 hybrid, 1 MoE  SSMs at 6/37 and 17/37; both extremes dense
    combination --score       deepseek surprisal, 13 models  2 SSM, 1 hybrid, 1 MoE  non-dense inside the dense range
    combination --long        page drift, 1,503 words        1 LINEAGE               attention-free drift LOWER where they overlap;
                                                                                     too few long texts to estimate a bin above 1,200
    combination --names       character-name carryover       1 MODEL                 gap +0.000 in the only bin with usable n
    combination --repair      recovery after a forced word   2 MODELS                gap NEGATIVE and largest FAR from the
                                                                                     imposition, the opposite of the prediction
    displacement              charge delta, 50 lineages      1 SSM, 1 RNN, hybrids   all displace but rwkv, which is confounded
    norm_change               norm delta, 45 lineages        same                    falcon-mamba 12/12 with the roster median

**`--names` is the sharpest of these and the only one with a prediction written down before the run.** Attention keeps every past token addressable and a recurrent state compresses; so what should be lost is exact recall of arbitrary high-entropy detail, and a character name is the purest case -- not reconstructible from context, carried verbatim, failure visible. Gist is low-entropy and survives compression, which is why the semantic measures above are null by construction; a proper noun cannot. **Carryover at matched length: gap +0.000 in the 400-900 bin (54 attention-free texts), and the one apparent gap sits in a bin holding FIVE.** If compression caused it the gap would grow with length rather than appear in the middle and vanish above it.

That null is bounded twice over. `falcon-mamba-7b` is the only attention-free model in `national_story`, so n is one model in every bin; and 3,000 words is probably still too short, since the quantity that matters is interference -- a name introduced at word 50 and needed at word 2,000 must survive 1,950 words written into the same fixed state -- and the published SSM recall failures appear at thousands to tens of thousands of tokens. **A null here means the regime is too short, or that carryover is not what compression costs. It does not mean the architectures are equivalent.**

**`--long` is the one that should have found something and is the most informative null**, because it is the only instrument in the regime where attention's actual technical advantage -- exact long-range recall -- is exercised. It found nothing, and the reason is worth the row: `falcon-mamba` writes 557 words median and only 2 of 57 raw generations clear 1,200, too few to estimate a bin. **It is not that the model cannot write long -- its longest is 2,362 words** -- it is that the roster cannot MEASURE it there. That is a fact about coverage, not about architecture, and it is why the row says what it says rather than "no effect".

**What is NOT in this ledger**, and therefore not tested: needle-in-a-haystack retrieval, many-shot in-context learning, exact copying. That is where the published literature does separate these architectures, and this subject has no instrument in it.

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

**`measurements.json` section `architecture`, 158 checkpoints, written by `scripts/probe_architecture.py`, read through `roster.architecture()`.** @malign's ruling, 2026-09-11, and the reasoning is better than the version it replaced: that file's own `_about` says it holds "OBSERVED facts about checkpoints -- what inspection returned, never what anyone declared. `models.yaml` is the authored side; this is the found side." **An architecture is not authored.** It is read off `config.json`, which every repo publishes, which parses without executing anything, and which evidences its own claim -- `layer_types` for a hybrid, `state_size` for an SSM, `num_experts_per_tok` for a mixture.

**The labels are DERIVED at read time, not stored.** The four-way taxonomy is a proposal in `docs/model_census.md` rather than a ruling, so storing labels would ratify one by writing it down; deriving them means a ruling changes `roster.architecture()` and re-probes nothing.

### CORRECTED: `env.profile` does not pick out these families, and this file said it did

An earlier version of this section said `env.profile: ssm` "picks out the SSM and hybrid families exactly". **That was false, and its own table below contradicted it.** As a predictor of "non-dense block" over the eight cases then declared:

    on the ATTENTION axis (block in ssm, hybrid)      miss 2 of 6
    with SPARSITY folded in (block also moe)          miss 3 of 7

**Two denominators, not a discrepancy.** The taxonomy keeps the axes apart on purpose -- `docs/model_census.md`: MoE is a sparsity property, a different axis from the attention mechanism. On attention the misses are `recurrentgemma-9b` (Griffin) and `Olmo-Hybrid-7B` (Gated DeltaNet); fold in sparsity and `OLMoE-1B-7B-0125` joins them. Recorded this way so nobody later reads the 2 and the 3 as one of them being wrong. It fails the other way too: `profile: ssm` holds `falcon-mamba` and `Falcon3-Mamba`, which are PURE SSM rather than hybrid, so the profile cannot separate the two classes it would have to separate. `env.profile` answers "does this need mamba-ssm and causal-conv1d kernels", and two different architectures share one answer.

**And the hand table forgot the arms nobody had looked at.** It declared bases only, so six checkpoints carrying `env.profile: ssm` -- `Zamba2-7B-Instruct`, both `Falcon-H1-*-Instruct`, both `Falcon3-Mamba-7B-*` and `falcon-mamba-7b-instruct` -- fell to its "unlisted means dense transformer" default. Nothing had stratified the aligned arm, so no published number was wrong; the defect was one analysis away. **`roster.architecture()` returns `unknown` for an unprobed model rather than `dense`**, which is the honest answer and the one that cannot silently absorb a sibling.

Replacing the table also corrected a live label: `Olmo-3-1025-7B` was declared plain `full`, and its config declares `layer_types: ['full_attention', 'sliding_attention']`, so it is **`full+local`** -- which happens to be exactly the distinction the Olmo-Hybrid contrast turns on, since what AI2 replaced was the sliding-window half.

### The census as found

    full / dense           126        full+ssm / hybrid        6
    full+local / dense      11        none / ssm               4
    full / moe               4        full+linear / hybrid     3
    local+linear / hybrid    2        linear / rnn             2

Two checkpoints are unreadable (`SmolLM3-3B-checkpoints`, 404 on the raw endpoint) and are recorded as `unmeasured` rather than guessed.
