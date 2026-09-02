---
type: subject
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
| [`existence/`](existence/) | RUN 2026-08-30 | **does it happen at all?** Content-selective (40/50 lineages, p=2e-5), same-kind landing (47/49, p<1e-6), selectivity scales with lift. Variance decomposition: ~35% word, ~12% context, ~53% model-specific. |
| [`displacement_axis/`](displacement_axis/) | direction settled; magnitude re-run at 50 and REVERSED | how MUCH mass moves, in which direction along author-declared pole axes. 60% nice-ward. Magnitude: named scales 62% of benchmark, bge 73%, nothing reaches it. Naming gain null REVERSES under lift dose (p=0.015). |
| [`displacement_taxonomy/`](displacement_taxonomy/) | DONE | what KIND of movement, from blind coders. Ten canonical meta-relations. Operations are a property of alignment as such, not specific to transgression. |
| [`norm_change/`](norm_change/) | RUN, corrected 2026-08-24, lift added 2026-08-30 | does alignment move the distribution along word norms and semantic fields? Register rises and valence rises in BOTH languages. Concreteness falls in Chinese only. Dose-response: lift reorders the top (arousal over bodily harm). Three doses agree on 19 targets with no sign disagreement. |
| [`named_under_dose/`](named_under_dose/) | building | do named norms predict direction better under dose? Dose interaction: 8% to 40% headroom recovery. Softens to 20% to 34% under lift. |
| [`rate_and_magnitude/`](rate_and_magnitude/) | RUN 2026-08-24 | how MUCH mass moves and how OFTEN. English: both rate and magnitude rise with dose. Chinese: rate rises, magnitude INVERTS (dispersal). The two come apart by language. |
| [`register_shift/`](register_shift/) | RUN 2026-08-24 | does alignment shift REGISTER? G NOT supported (30/50, p=0.203). G1 supported (what leaves is low-register). G2 REVERSED (what arrives is ALSO low-register, p=0.0003). |
| [`readout_share/`](readout_share/) | RUN 2026-08-30 | **where** the movement is implemented: in the state that reaches the readout, or in the readout itself. Separable because the two arms share a tokenizer and hidden size, so a base residual stream can be pushed through its aligned sibling's unembedding. Both contribute COMPARABLY. An earlier "Llama is the lone readout counter-case" is WITHDRAWN. |

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
