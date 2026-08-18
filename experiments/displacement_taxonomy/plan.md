# displacement_taxonomy

What KINDS of movement does alignment produce, and how are they distributed across the corpus?

## The question this exists to answer

`displacement_axis` measures HOW MUCH mass moves and IN WHICH DIRECTION along an author-declared pole axis. Over pilot3 it gives 62.7% of cells moving toward the permitted pole, z=+19.1, 17 of 21 lineages replicating, and a 10-17% median reduction in transgressive mass. That result is solid and it is not what this folder is about.

What it cannot say is WHAT KIND of movement any cell shows. **69% of cells are classed `churn`** -- the two split components have opposite signs -- and churn has been characterised four different ways over one evening without settling, because the metric has no vocabulary for it. A number cannot say whether a distribution was reorganised by substituting one word for a milder one, by abandoning a construction, or by deferring the content to a later slot.

This folder builds that vocabulary from the data, using coders, and then checks whether the kinds it finds separate on measurements that already exist.

## What is already established

Four runs on 2026-08-18, all on the `movement` table (v3) filtered to the 50 declared endpoint pairs.

**The riser/faller split is legible to a blind reader.** Six raters, two frames, three of six presentations swapped, lists unlabelled: all six named the same dimension per frame (violence severity; garment intimacy/exposure) and **6 of 6 correctly identified which group alignment moves toward**, against a chance rate of 1/2. Direction recovery is therefore banked and does not need re-establishing per frame.

**Informed raters distinguish signal from noise, but only in their confidence.** A sham arm (same words, same magnitudes, deltas randomly reassigned) cohered 7/8 times against the real arm's 8/8 -- so the binary "does this cohere" flag is near-useless. But confidence separated with **zero overlap**: high 5 / medium 3 / low 0 on the real arm, high 0 / medium 3 / low 5 on the sham. Raters detect the difference and express it in confidence rather than in the coherence verdict. **Score confidence, not coherence.**

**Two kinds of movement are already visible**, and they correspond to Jakobson's two axes:

- **KIND 1, selection / paradigmatic.** A different word occupies the same slot. `kill` -> `scream`, `bra` -> `coat`. Movement along a content gradient with a more- and less-transgressive pole; the grammatical frame is unchanged.
- **KIND 2, combination / syntagmatic.** The word keeps its place in the sentence but moves to a LATER slot. "is sunny" -> "is expected to be sunny". A construction is abandoned rather than a point on a scale vacated. Four raters found this independently on the weather frame in four different vocabularies ("syntactic-frame shift", "deferred/hedged prediction", "shift in evidential frame", "commitment deferral").

**The tell that separates them, which no metric currently computes: valence-indifference.** In Kind 2 the losses have no pole -- `sunny`, `rainy`, `good`, `bad`, `perfect`, `cold` all fall together. In Kind 1 the losses cluster at one end of a gradient.

**Per-model resolution exists.** On the anger frame, Llama-3.1 and SmolLM3 were described by independent raters as doing different operations: Llama removes the victim (transitive assault -> intransitive vocal release), SmolLM3 narrows the range from both ends (lethal violence AND self-directed collapse both fall, blunt sub-lethal aggression rises). Both read as "nice-ward" on the pole axis, which is why the axis cannot tell them apart.

## The hazard this creates for the existing result

**If alignment defers content rather than replacing it, `twp` measures the deferral as suppression.** `sunny` falling in the weather frame is not `sunny` being avoided; it is `sunny` arriving two words later, outside the measured slot. Wherever a hedge construction is adopted, apparent suppression is inflated by an unknown amount.

This is not a reason to distrust the pilot3 numbers, which are about pole mass on frames with declared poles. It is a reason the taxonomy has to exist before the numbers are interpreted, and it is the strongest argument for this folder.

## Design

### Stage 1: open coding

One call per (frame, arm) where arm is either the pooled 50-endpoint movement or a single lineage. Input: the fragment, and every word that moved at k>=2, each with its net change. Words sorted by change, largest gain first.

The rater is told what the lists are and what the numbers mean -- direction recovery is banked, blinding it further buys nothing and prevents magnitude weighting. It is told to weight by magnitude, explicitly, because a rater given unweighted lists describes the vocabulary rather than the movement and an earlier run was misread on exactly that.

Returns, per relation found (**up to 3, not 1 -- earlier runs allowed only one and raters had more to say**):

    name          2-4 words, INVENTED by the rater, no vocabulary supplied
    sentence      one sentence stating the relation
    from_words    the words vacated
    to_words      the words gaining
    mass_share    the rater's estimate of what fraction of the total movement this relation accounts for

plus, per frame:

    kind          the rater's own phrase for what dimension is being altered
    residue       words belonging to no relation, with one sentence on why
    confidence    high / medium / low / none
    counterexamples   words that do not fit, named

**The name and the sentence are both required.** A name alone is uncontrolled; a sentence alone never forces the rater to commit. Disagreement between a rater's name and their own sentence is itself a signal.

### Stage 2: harmonisation

A separate pass, its own instrument, its own agreement measure. Reads all Stage 1 names and sentences with no access to the frames, and proposes a controlled vocabulary: which invented names denote one construct, which are genuinely distinct. This is an annotation task in its own right and must not be folded into Stage 1 -- a rater who has seen a vocabulary will use it whether or not it fits.

### Stage 3: does the taxonomy separate on existing measurements

The point of naming the kinds is to test them against instruments already built:

- Do Kind 1 and Kind 2 cells separate on **F13's `syntagmatic_js` vs paradigmatic similarity**? Those two are negatively correlated at the pair level -- the campaign's strongest quantitative result -- and if the kinds are the two Jakobsonian axes, that correlation is these kinds trading off, measured before anyone named them.
- Do Kind 2 cells show **valence-indifferent losses**, computable directly from k_ratings valence over the fallers?
- Does the `churn` class in `displacement_axis` consist disproportionately of Kind 2?

Stage 3 is where this stops being interpretation and becomes evidence.

## Population and sampling

    303 items x 21 lineages = 6,363 cells -- too many to code, and per-cell coding is the wrong unit anyway.

**Stage 1a, frame-level, pooled over the 50 endpoint pairs.** 303 frames x 2 raters = 606 calls. Gives the frame-level taxonomy and the distribution of kinds across domains.

**Stage 1b, per-lineage, on a subset.** The Llama/SmolLM3 contrast shows lineage matters. Select ~20 frames spanning the kinds found in 1a, x 6 lineages spanning the alignment technologies (safety-tuned, RLHF, DPO, instruction-tuned, multitask-prompted), x 2 raters = 240 calls.

Two model families for the rater, not two samples of one. M01's IAA used deepseek-v4-flash against claude-haiku-4-5, and that is the design that gives a band; two runs of one model measure stochastic consistency only.

## Implementation

`largeliterarymodels.task.Task`, following `malign_logits/tasks/rate_charge_v1.py` and `code_m05_sense_v1.py`:

- pydantic schema, with a free-text `reading` field FIRST so the model commits to a reading before numbers
- `temperature = 0.0`, `retries = 2`, versioned `name` -- the cache and the freeze key off it
- one call per (frame, arm); the judgment is a property of the pair, never of a checkpoint, **so blindness to which lineage produced it is structural rather than promised**
- `INSTRUMENT.md` frozen beside the producer: model id, temperature, the exact prompt, the full field set, a sha

**A rating is a property of the INSTRUMENT VERSION.** `k_bulk.py` records that adding three scales moved `penis` vulgarity 2->4 at temperature 0. Measured again here: the same frame with the same words and the same question scored 0.714 under one four-scale set and 1.500 under another. Version bumps get a new directory and are never pooled.

`largeliterarymodels` is not currently installed in the malignment venv. That is the first blocker.

## Known problems, carried rather than hidden

**The movement table is v3.** `corpus.movement` refuses `rule_version=4` because there is no column to distinguish rebuilt rows. Everything here is v3 until `movement_v4` is built from `twp_words_v4` -- a change to a shared object, malign's to make. The taxonomy is unlikely to be rule-sensitive, but no number from here may be joined to a pilot3 v4 figure.

**Tokenizer residue is in the vocabulary.** `___`, `own`, `sumptuous`, `$40`, `You`. Raters catch these unaided and consistently; the residue bucket measures them rather than a filter hiding them. Do not pre-filter -- the residue count is a measurement of extraction quality.

**Lists are lopsided by construction.** Anger gives 29 risers against 87 fallers. That is concentration, not signal, and raters should be told so.

**`mass_share` is a rater estimate, not a computation.** Once words are assigned to relations the true share is arithmetic from the movement table. Collect both and compare -- a rater whose estimates track the arithmetic is a rater whose other judgments are worth more.
