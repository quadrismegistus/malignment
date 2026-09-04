---
type: subject
kind: subject
status: "OPEN. Eight questions; readout_share moved here from top level on 2026-09-02. Frame variants added to three of them, 2026-08-30 to 2026-09-04."
headline: "Alignment displaces on its own; the chat frame displaces too, on weights nobody touched; together about 2.8x. But content-selectivity needs aligned weights and the frame alone cannot produce it."
question: What does alignment do to a distribution -- how much moves, what kind of movement, along which dimension, and where in the model is it implemented?
---

# displacement

**A SUBJECT, not an experiment.** It holds questions; it holds no code, no data
and no claims of its own. Anything shared between its questions belongs in
`malignment/`, not here.

Eight questions measuring THE MOVEMENT ITSELF, plus a cross-reference note
against M01.

**The fourth clause of the question above arrived with the eighth folder.**
`readout_share` moved here from top level on 2026-09-02 and asks where in the
model the movement is implemented, which the subject's stated scope did not
cover. The question line was extended rather than the folder being filed under a
scope that excluded it -- a subject whose README does not describe one of its
members is the failure this grouping exists to avoid. As against the folders that rate the words (`slot_ratings`), read
the generated text (`passage_analysis`), check the instruments
(`instrument_calibrations`) or open the training data
(`posttraining_corpus_analysis`).

| question | status | gist -- see its README for the claim |
|---|---|---|
| [`existence/`](existence/) | RUN 2026-08-30, FRAMED 2026-09-03 | **does it happen at all?** Content-selective (40/50 lineages, p=2e-5), same-kind landing (47/49, p<1e-6), selectivity scales with lift. Variance decomposition: ~35% word, ~12% context, ~53% model-specific. **Framed: selectivity holds and is 2.8x larger; the four-row dissociation is here.** |
| [`displacement_axis/`](displacement_axis/) | direction settled; magnitude re-run at 50 and REVERSED | how MUCH mass moves, in which direction along author-declared pole axes. 60% nice-ward. Magnitude: named scales 62% of benchmark, bge 73%, nothing reaches it. Naming gain null REVERSES under lift dose (p=0.015). |
| [`displacement_taxonomy/`](displacement_taxonomy/) | DONE | what KIND of movement, from blind coders. Ten canonical meta-relations. Operations are a property of alignment as such, not specific to transgression. |
| [`norm_change/`](norm_change/) | RUN, corrected 2026-08-24, lift added 2026-08-30, FRAMED 2026-09-04 | does alignment move the distribution along word norms and semantic fields? Register rises and valence rises in BOTH languages. Concreteness falls in Chinese only. Dose-response: lift reorders the top (arousal over bodily harm). Three doses agree on 19 targets with no sign disagreement. **Framed: word-level norms amplify ~2x, SLOT-RATED contextual scales 3 to 14x. `k_register_level` rises 40/5 framed and is absent from raw's top band.** |
| [`named_under_dose/`](named_under_dose/) | RUN, NULL | do named norms predict direction better under dose? **They do not, for anything.** The `8% to 40% headroom recovery` this row advertised until 2026-09-02 is listed in the folder's own `FINDINGS.md` as an unoriented `log p_base` floor that inflated the headroom 2.8x. |
| [`rate_and_magnitude/`](rate_and_magnitude/) | RUN 2026-08-24, FRAMED + LADDER + ABLATIONS 2026-09-04 | how MUCH mass moves and how OFTEN. English: both rate and magnitude rise with dose. Chinese: rate rises, magnitude INVERTS (dispersal). The two come apart by language. **Self-edges split the frame effect from the weights'. The Tulu ladder and its four SFT data ablations are here.** |
| [`register_shift/`](register_shift/) | RUN 2026-08-24. **NO FRAME VARIANT -- the one gap** | does alignment shift REGISTER? G NOT supported (30/50, p=0.203). G1 supported (what leaves is low-register). G2 REVERSED (what arrives is ALSO low-register, p=0.0003). **`norm_change` finds `k_register_level` rising 40/5 under the frame with dose, so this folder's unsupported headline has a live framed question it has not been asked.** |
| [`readout_share/`](readout_share/) | RUN 2026-08-30 | **where** the movement is implemented: in the state that reaches the readout, or in the readout itself. Separable because the two arms share a tokenizer and hidden size, so a base residual stream can be pushed through its aligned sibling's unembedding. Both contribute COMPARABLY. An earlier "Llama is the lone readout counter-case" is WITHDRAWN. |

## THE FRAME (2026-08-30 to 2026-09-04)

**The cross-cutting result, and the reason three folders were re-run.** Every
displacement number in this subject was measured with BOTH arms bare. Aligned
models are deployed inside a chat template, so the question is whether the
finding is an artifact of measuring the aligned arm out of its habitat.

**It is not, and the frame is a second displacing thing in its own right.**
`existence` states it in four rows on the same 45 pairs:

    base_raw    -> aligned_raw       43/50   p=2e-7      content-selective
    base_raw    -> aligned_framed    41/45   p<1e-6      about 2.8x row 1
    aligned_raw -> aligned_framed    40/45   p<1e-6      NO weight change
    base_raw    -> base_framed        4/4    p=1.000     null on content

Alignment displaces on its own (row 1). The chat frame displaces too, on weights
nobody touched during the measurement (row 3). **But only on weights alignment
has already touched** (row 4). And together they displace about 2.8 times as
much as alignment alone (row 2).

**The base arm is n=8 and permanently capped**, because 43 of the 50 bases ship
no chat template at all. It is a real control and it is a weak one; the folders
print it separately and never pool it.

### What each folder adds

- **`existence`** -- content-selectivity needs aligned weights; same-kind landing
  does not. That dissociation is the sharpest thing the frame work produced.
- **`norm_change`** -- the amplification is not uniform. Word-level norms roughly
  double; the SLOT-RATED contextual scales go up three to fourteen times. Every
  dose effect in the base arm is null (smallest p = 0.289).
- **`rate_and_magnitude`** -- self-edges decompose the full contrast: **the
  departure gradient is the weights', the arrival concentration is the frame's.**
  Then the Tulu ladder (DPO raises how much moves, 4/4, t=15-31; it does not
  change the dose response, signs split 3/1 over n=4 families) and the four SFT
  data ablations (WildChat).

### The population rule, which is in code because it drifted

A framed cell is in the population iff **the system slot was empty in the mode
the cell was stored under**. Not `clean_via`, which is a property of the model;
not `system_mode`, which records the argument passed rather than the treatment
received. Run `scripts/framed_population.py` rather than restating the count --
it was answered eight different ways in one session before the rule was moved
into `malignment/movement.py:clean_frame_pairs()`.

Self-edges are EXCLUDED from that accessor by default. They silently contaminated
three call sites before the flag existed.

### What is NOT established

`register_shift` has no framed variant and has a live question. Chinese is absent
from every framed column, because charge ratings are English-only. And nothing in
any framed section was registered -- all of it is exploratory.

[`M01_RECONSIDERED.md`](M01_RECONSIDERED.md) maps these findings back to the
archive's M01 displacement findings.

`salary_probe/` moved to `../exploratory/salary_probe/` on 2026-08-24: parked
after a two-lineage pilot and never promoted to a declared question.

The first two are the pair that motivates the grouping: `existence` establishes
that displacement is content-selective and within-kind, `displacement_axis`
gives a magnitude and a direction and cannot say what kind of movement produced
them -- 69% of its cells class as `churn` -- and `displacement_taxonomy` exists
to supply the vocabulary that number lacks.

## The move that created this folder

2026-08-21 (RH). These sat at `experiments/<question>` and were regrouped
here. **Sixteen producers had to be fixed first**, because they computed the repo
root as `dirname(dirname(HERE))` -- correct at depth 1, wrong at depth 2, and
wrong SILENTLY: `REPO` builds real paths, and a glob under a root that does not
exist returns `[]` rather than raising. `malignment.paths.repo_root()` now finds
the root by walking up from `malignment` itself and refuses if it cannot, so
nothing under `experiments/` encodes its own depth any more and this folder can
be reorganised again without the same repair.
