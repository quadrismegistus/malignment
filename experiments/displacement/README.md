---
type: subject
question: What does alignment do to a distribution -- how much moves, what kind of movement, and along which dimension?
---

# displacement

**A SUBJECT, not an experiment.** It holds questions; it holds no code, no data
and no claims of its own. Anything shared between its questions belongs in
`malignment/`, not here.

Four questions that all measure THE MOVEMENT ITSELF, as against the folders that
rate the words (`slot_ratings`), read the generated text (`passage_analysis`),
check the instruments (`instrument_calibrations`) or open the training data
(`posttraining_corpus_analysis`).

| question | status | gist -- see its README for the claim |
|---|---|---|
| [`displacement_axis/`](displacement_axis/) | awaiting more lineages | how MUCH mass moves, and in which direction along an author-declared pole axis |
| [`displacement_taxonomy/`](displacement_taxonomy/) | RUN | what KIND of movement, built from blind coders rather than from a metric |
| [`register_shift/`](register_shift/) | REGISTERED, NOT RUN | does alignment shift REGISTER -- vulgar to clinical -- rather than only lowering transgressive mass |
| [`salary_probe/`](salary_probe/) | PARKED | what alignment does to a distribution over money, after a two-lineage pilot |

The first two are the pair that motivates the grouping: `displacement_axis`
gives a magnitude and a direction and cannot say what kind of movement produced
them -- 69% of its cells class as `churn` -- and `displacement_taxonomy` exists
to supply the vocabulary that number lacks.

## The move that created this folder

2026-08-21 (RH). These four sat at `experiments/<question>` and were regrouped
here. **Sixteen producers had to be fixed first**, because they computed the repo
root as `dirname(dirname(HERE))` -- correct at depth 1, wrong at depth 2, and
wrong SILENTLY: `REPO` builds real paths, and a glob under a root that does not
exist returns `[]` rather than raising. `malignment.paths.repo_root()` now finds
the root by walking up from `malignment` itself and refuses if it cannot, so
nothing under `experiments/` encodes its own depth any more and this folder can
be reorganised again without the same repair.
