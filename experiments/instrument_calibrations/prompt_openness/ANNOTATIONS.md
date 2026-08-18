# Annotation passes — prompt_openness

Every LLM annotation run behind this calibration. **The workflow script carries
the coding scheme verbatim**, so the instructions the agents received are the
committed artifact, not a paraphrase of them.

| # | run id | script | population | agents | failed | agreement |
|---|---|---|---|---|---|---|
| 1 | `wf_1468cab2-4b6` | `results/workflow.js` | 482 prompts with unforced generations | 18 (2 coders x 9 batches of 55) | 0 | 0.9087 raw, 438/482 |
| 2 | `wf_12fdefad-2b0` | `results/workflow_round2.js` | 197 slot prompts + 74 adjudication (44 contested + 30 anchors) | 10 | 0 | slots 0.8782, 173/197 |
| 3 | `wf_e5180606-142` | `results/workflow_round3.js` | 24 contested slot prompts + 20 anchors | 2 | 0 | anchors 16/20 = 80% |

## What each pass produced

    1  results/codings.json        coder_A, coder_B, raw_agreement, run_id
    2  results/round2.json         slot A/B + adjudication C
    3  results/round3.json         slot adjudication C
       results/partition.json      the consolidated 666-prompt partition
       results/openness.csv        per-prompt, with source and pair_role

## Blinding, stated per pass

- **Items carry `id` and text ONLY.** No source, corpus, domain, `pair_role` or
  family label reaches a coder.
- Order shuffled at export (seeds 20260818, 20260819, 20260820), so neither key
  order nor batch membership encodes provenance.
- **Adjudication sets mix contested items with ANCHORS** -- items the first two
  coders already agreed on -- shuffled indistinguishably, so the third coder's
  competence is measured rather than assumed. Passes 2 and 3 both report the
  anchor hit rate against a 33% chance baseline.

## What is NOT stored

Per-agent transcripts. The batch ranges are in each script and item ids are
sequential, so agent-to-item attribution is RECOVERABLE from script plus ids,
but it is not written down. No pass had a failure, so no failure record exists
to check that against.
