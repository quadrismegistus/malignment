# Annotation passes — interiority_in_passages

Every LLM annotation run behind this experiment. **The workflow script carries
the task text verbatim**, so what the agents were asked is the committed
artifact.

| # | run id | script | population | agents | failed | result |
|---|---|---|---|---|---|---|
| 1 | `wf_5ccdce2d-361` | `results/workflow_prompts.js` | 212 l2 prompts (110 en, 102 zh) | 12 (3 coders x 4 batches of 53) | 0 | unanimous on 197/212 = 93% |
| 2 | `wf_d9e7b396-7f0` | `results/workflow_opencoding.js` | 192 passages, 24 en prompts, 22 endpoint pairs | 6 readers x 32 | 0 | 54 dimensions proposed |

## What each pass produced

    1  results/codings.json      A, B, C + per_coder_distribution
       results/prompt_kind.csv   per-prompt kind, family, language
    2  results/open_coding.json  six readers' proposed dimensions with quotations

## Blinding, and what each pass could NOT see

**Pass 1 (prompt kind).** Items carry `id` and prompt text only -- no family,
language tag or quintuplet role. Shuffled at seed 20260821. The scheme states
EXTERIOR and NEITHER are ordinary answers and excludes the `wanted to / chose to`
hinge by instruction, both against acquiescence.

**Pass 2 (open coding).** THE ARMS ARE MIXED AND UNLABELLED AND NO READER SEES A
CONTRAST. Readers were asked what varies among continuations of the SAME
fragment -- there is no group to characterise, so no answer can be guessed at.
Sampled at seed 20260822, 8 continuations per prompt drawn across both arms.

**Nothing in pass 2's task text names interiority, exteriority, mental states,
frames, contradiction, alignment, or any campaign construct.** That is what makes
6/6 convergence on interiority evidence rather than echo.

## What is NOT stored

Per-agent transcripts. Pass 2's readers each saw a disjoint 32-passage range, so
reader-to-passage attribution is recoverable from the script's ranges. Neither
pass had a failure.
