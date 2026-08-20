# Resume: cross-lineage sweep

State at 2026-08-20, coverage section refreshed ~07:45 after the fleet's overnight run. Everything below is committed in `~/github/malignment/experiments/displacement_taxonomy` unless marked otherwise.

## Where to pick up

Two things were waiting on a download to finish, and one question was outstanding for malign.

~~1. Ingest `~/malignment-data/twp`.~~ **DONE by the fleet overnight.** Pass 2 more than doubled (36,181 to 85,424 topped cells, 114 models, malign [6467]) and it reached these prompts.

~~2. Ask malign about the missing arms.~~ **Partly answered by [6467]**: the four 32B Olmo arms need box profile `big80` and the two Llama-70B arms need `twogpu` (141 GB at fp16 fits neither a 4090 nor a single A100), so those are queued behind hardware rather than behind a decision. Shard 8 is refused by preflight on a deepseek record from transformers 5.14.1.

1. **Decide whether to re-run the sweep at the larger roster** -- see below. This is now the only thing waiting on RH.

## The open decision

Run the remaining ~177 prompts now, or wait for a bigger roster.

The case for waiting is RH's and it is good: the 18-vs-29 test showed roster growth **replaces** operations rather than adding members. **Zero of the 7 operations found at 29 lineages existed in the 3-operation legend from 18.** So a 177-prompt run at 32 could be invalidated by a later run at 50.

The case against waiting has STRENGTHENED, because pass 2 has now nearly caught up with pass 1:

    over the 279 slot prompts        was (08-20 06:45)   now (07:45)
      topped pairs per prompt         31.8 / median 33    34.7 / median 36
      measured (pass 1+) per prompt   34.8 / median 35    35.9 / median 36
      prompts with 35+ topped                        0            215 of 279

**Only ~1.2 pairs of headroom remain from topup.** Everything past 36 needs pass 1
on models never measured on these prompts, which is exactly the 32B and 70B arms
waiting on box profiles. So "wait for 50" is not a short wait and may not be a
reachable one.

But 36 is a real increase over the 26-29 the sweep actually ran at -- 24 to 38%
-- and 18 to 29 REPLACED the operations rather than adding members. So a re-run
at 36 is a genuine question rather than a refresh, and the same argument that says
do not wait for 50 also says today's 40-prompt result was taken at a roster that
has since moved.

**The cheap thing that settles it, and is not wasted either way:** re-read one prompt at 36 and compare to its 29 reading. One agent. If a 10% roster increase leaves operations intact while a 61% increase replaced them, the instability is threshold-like and running now is safe. If 32 reshapes again, the instability is continuous, no roster is a safe stopping point, and the result has to be reported as roster-dependent whenever it is run.

## Worth more than more prompts

The **Tulu ablation family** is in the download:

    allenai__Llama-3.1-Tulu-3-8B-SFT
    allenai__Llama-3.1-Tulu-3-8B-SFT-no-safety-data
    allenai__Llama-3.1-Tulu-3-8B-SFT-no-persona-data
    allenai__Llama-3.1-Tulu-3-8B-SFT-no-wildchat-data
    allenai__Llama-3.1-Tulu-3-8B-SFT-no-math-data
    allenai__Llama-3.1-Tulu-3-8B-DPO

Same base, same recipe, one training component removed at a time. Every direction claim made so far is **correlational across unrelated lineages**. If `SFT` and `SFT-no-safety-data` differ on the direction of an operation, that attributes the direction to the safety data rather than to alignment in general. This is the only set in the corpus that can do that.

## What runs

    crosslineage.py --prepare "<prompt prefix>"     one prompt, every topped-up lineage
    crosslineage.py --ingest RUN --slug <slug>
    sweep_xling.py --build | --prepare [--all] | --ingest RUN
    incremental.py --prepare "<prefix>"            extend a reading with new lineages
    word_groups.py --prompt | --all | --csv        arithmetic pooling, no model judgement

`sweep_xling.py --prepare --all` targets every prompt in the slot corpora rather than the 40.

## Results in hand

    40 prompts x 26-29 lineages, 1,151 model-readings
      150 reversed (13%)   263 unassigned (23%)
      27 of 29 lineages reverse on at least one prompt
      never reversed: archangel_sft-dpo_pythia2-8b, eleuther-pythia6.9b-hh-dpo
      mean per prompt: 2.8 operations, 18.4 assigned, ~4 reversed, ~7 unassigned

Reversal concentrates by prompt, not by model: 13 of 29 on "The three Arabs who moved in next door", 12 on the asylum letter, 0 on either first-person advice prompt. On the asylum prompt, 7 lineages run FLIGHT to RECOURSE and 12 run RECOURSE to FLIGHT — the two explicitly safety-tuned models (AmberSafe, beaver-7b-v1.0) both promote appealing, while Llama-3.1, gemma-2, granite-3.0 and OLMo-2 promote leaving.

Domain shape: identity is repetitive (2.0 operations per prompt, 20 distinct names over 10 prompts) but NOT flat — it has the highest reversal rate at 20% against 9-12% elsewhere. Keep the 10 as a controlled template family, do not extend them.

## Artifacts

    results/crosslineage_rows.csv     1,151 rows: prompt, status, operation, model, base/aligned words
    results/word_groups.csv           989 rows, one per stage-1 relation
    results/categories_traced.csv     1,019 rows: category down to model and relation
    results/word_groups/*.txt         40 per-prompt pooled-vocabulary documents
    results/displacement-constructs-72.md
    results/displacement-categories-7.md

`crosslineage_rows.csv` joins `word_groups.csv` on (prompt, model).

## Traps, all paid for once

- **The stash key must carry the roster.** `lineages_sha` and `n_lineages` are in the crosslineage key now; before that a 29-lineage run silently overwrote the 18-lineage one and the comparison was lost. Same lesson as `pairs_sha` in harmonisation.
- **A hand-built JSON schema needs `"type": "object"` at every level.** Its absence is reported as `tools.11.custom.input_schema.type: Field required`, naming a tool index, and surfaces as the workflow dying on a null field. `incremental.py` has a validator that walks the schema before spending.
- **`git commit` commits the INDEX in a shared checkout.** Two commits by other seats swept my staged files today. Use `git commit -F msg -- <explicit paths>`, and note a FAILED pathspec commit leaves staging exposed. Never put `grep -c` in an `&&` chain where zero is the good answer.
- **Pass-1 cells are unusable here.** The instrument needs `merged=1` on both arms, because a word missing from a pass-1 column may never have been scored rather than ranked low.
