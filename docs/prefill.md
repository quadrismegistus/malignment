# twp under a chat template: the template as a rung

Status: **not started.** Written 2026-08-21, rewritten the same evening after RH corrected its central framing. Nothing here has been run except the two censuses reported below.

## The conception: templating is scaffolding on top of weight-level alignment

RH, 2026-08-21: *"I like thinking of templating as a scaffolding on top of the weight-level alignment."*

That is the frame this document is built on, and it is stronger than the one it replaces. The campaign measures a pipeline — base → SFT → DPO → RLVR — where each stage changes the weights. But a deployed instruct model is never used as those weights alone: it is used wrapped in a chat template that injects a persona, a turn structure, and often a vendor system message nobody typed.

So the template is not a confound to be controlled away. **It is another stage of the same pipeline**, applied at inference instead of in training, and it can be measured on the same axis as the stages that precede it. The question the corpus cannot currently answer is *which does more* — the weights, or the wrapper.

## Three rungs, and the deployed contrast is their composition

    rung A   raw base      ->  raw aligned       weights change, frame held constant   HAVE IT
    rung B   raw aligned   ->  prefill aligned   frame changes, weights held constant  THE SWEEP
    pair C   raw base      ->  prefill aligned   as actually deployed                  A then B

This is exactly the shape `produce_movement` already uses for the training stages, and its docstring gives the reason to measure both the rungs and the transitive pair rather than inferring one from the other:

> a word can fall at SFT and rise at DPO, so the riser/faller classification of `base -> DPO` is NOT recoverable from `base -> SFT` plus `SFT -> DPO`. The transitive edge answers *what did the whole pipeline do*; the rungs answer *which stage did it*.

The same non-additivity applies here: a word suppressed by the weights may be restored by the template, or vice versa. So rung B enters the graph as its own relation — `relation='frame'`, depth 1 — alongside `sft`, `dpo`, `rlvr`, and pair C is measured rather than derived.

**Base-prefill is not required for any of this.** C decomposes through A and B, and both exist for every aligned arm whatever its base ships. This is the correction that retired the objection below.

## THE OBJECTION, RECORDED — it was wrong as stated and it is not empty

The first version of this document argued: *a base model ships no chat template, so it cannot be prefilled, so there is no base→aligned edge under prefill, so this is not an extension of the displacement finding but a separate within-checkpoint experiment.*

**Two things are wrong with that.**

**It is factually wrong about base models.** Measured 2026-08-21 across all 50 base arms, probing `tokenizer_config.json`, `chat_template.jinja` and `chat_template.json` with the HF token and with 404 distinguished from 401/403:

    ships a chat_template      9
    ships none                41
    unknown                    0

    Qwen/Qwen3-8B-Base, Qwen/Qwen2.5-7B, Qwen/Qwen2.5-0.5B
    huggyllama/llama-7b        m-a-p/neo_7b
    BAAI/Aquila2-7B            kakaocorp/kanana-1.5-8b-base
    team-hatakeyama-phase2/Tanuki-8B-base-v1.0
    openbmb/MiniCPM5-1B-Base   <- template in chat_template.jinja, NOT the config

A base checkpoint shipping chat scaffolding is itself worth noticing — it says something about how base-like that release is.

**THIS NUMBER TOOK THREE ATTEMPTS AND THE FIRST TWO WERE WRONG.** Reading `tokenizer_config.json` alone missed MiniCPM5-1B-Base, whose template is a separate `chat_template.jinja` — transformers resolves either location and a config-only probe does not. The second attempt added those files but mapped every HTTP 4xx to "absent", which would have recorded six GATED repos (meta-llama x2, gemma x2, jais, Zamba2) as shipping no template: an unreadable state reported as a negative. With 401/403 separated from 404 and the HF token applied, all 50 resolve and those six turn out to ship none anyway — but they were being counted, not measured.

**AND 9 IS AN UPPER BOUND, NOT A COUNT.** This tests PRESENCE. `frame_eligibility.py` tests USABILITY, by applying the template and byte-comparing, because "a template that discards a system message raises nothing and produces a treatment arm that never received the treatment". A repo can ship a `chat_template` that `apply_chat_template` refuses or that drops the system block. The authoritative check is loading each tokenizer and calling `render(..., prefill=True)`; that is what the census below should do, and it is not what produced this table.

**And it answers a question the design does not ask.** Even where a base has no template, pair C is available as A-then-B. The missing cell was never load-bearing.

**What survives, and it binds on the other side.** The constraint is real but it is on the ALIGNED arm, which is where I had it backwards. Rung B requires the *aligned* checkpoint to take a template. From `experiments/instrument_calibrations/generation_provenance/results/frame_eligibility.csv`, 25 aligned arms tested by byte comparison:

    OK             15
    NO TEMPLATE     5     archangel_sft-dpo_pythia2-8b, AmberSafe, beaver-7b-v1.0,
                          eleuther-pythia6.9b-hh-dpo, RedPajama-INCITE-7B-Chat
    NO TOKENIZER    5

So roughly a fifth of endpoints ship no chat template at all and **cannot be measured under prefill in any frame**. Those lineages drop out of the frame analysis entirely — not because of the base, because of the aligned arm. ~~If 15-of-25 holds, the sweep reaches perhaps 30 of 50 endpoints.~~

**SUPERSEDED BY THE CENSUS BELOW: it is 39 of 50, not ~30.** The 25-model sample was skewed toward older checkpoints. The shape of the constraint survives — a fifth of endpoints really are excluded, and by their own packaging — but the projected magnitude was too pessimistic and should not be quoted.

That population is selected by **whether a vendor shipped a template**, which correlates with vintage and organisation rather than with anything under study. It has to be declared and reported as a population, not discovered at analysis time. That is the part of the objection worth keeping.

## Why prefill is the only frame with a word slot in it

`generate.py` declares four frames — `raw`, `chat`, `continue`, `system` — and only one can host a twp measurement.

Under `chat`, `continue` and `system` the stem occupies the **user turn**, so the model's next word begins its *answer*: `I`, `Sure`, `It`. A fine object, but not a continuation, and comparing it to a raw cell compares a reply to a continuation.

Under `prefill` the stem is appended **after** the generation prompt, inside a started assistant turn, so the model resumes a sentence it is already writing. `render()`'s docstring:

> prefill True -> `text` goes in a prefilled ASSISTANT turn instead, and the user turn takes `user_msg`. The model resumes a sentence it is already writing, **which is the only chat-mode position with a word slot in it.**

## What exists, and the one gap

| | |
|---|---|
| `generate.render(loaded, text, system, user, prefill, user_msg, template)` | composes the string, returns `(rendered, sys_supported)` |
| `generate.encode(loaded, text_in, templated)` | exactly one leading BOS — neither blanket `True` nor `False` is correct, and it is measured |
| `generate.next_token(..., prefill=...)` | token grain, **already frame-aware** |
| `Checkpoint.next_token(..., prefill=...)` | passes through |

**`Checkpoint.next_word()` delegates to `probs(prompt, loaded=None, **kw)`, which hands the raw string straight to `twp.expand`.** The frame machinery stops at the token grain and never reaches the word instrument. That is the whole code gap: `probs()` would take the frame slots, call `render()`, and pass the rendered string on. `encode()`'s one-BOS rule already handles the tokenisation trap.

## Design notes

### The three free slots are not optional

`conditions.py` measured a target word's probability moving **2,500x** on one stem across combinations the caller never typed: default system `.246`, empty system `.106`, a persona `.0001`.

    system   DEFAULT -> the template's own persona fires
             ""      -> asserts an empty one, OVERRIDING that persona
             "..."   -> ours
    user_msg what occupies the user turn under prefill; "Hi." is the PRESENCE
             CONTROL, semantically empty on purpose

`frame='prefill'` alone is not an identity. `system` and `user_msg` belong in the cell key, or this repeats the decoder problem `generate.py` documents: an unpinned parameter is not a constant, it is a per-vendor covariate aligned with the arm contrast.

`render()` returns `sys_supported`, and a template that silently drops a system block yields a condition wearing the wrong name. That flag must reach the stored cell.

### Storage: a frame dimension that must never merge

Third instance of one pattern in this corpus:

    rule_version   selects the TABLE      (v3 -> twp_cells, v4 -> twp_cells_v4)
    topup          must not be merged     (two measurements of one surface)
    frame          ...the same argument

A prefill cell measures a **different surface**. Put `frame`, `system`, `user_msg` in the cell key with `raw` as the default for everything already measured, and expect the `_best` question back: it must not collapse across frame, for the reason it must not collapse pass 1 into topup.

### An expectation, stated so it can be falsified

Templated distributions should be **sharper** — an instruct model is confident inside its own frame — so at fixed `THETA = 0.001` a prefill cell should admit **fewer words** and carry **more tail** than its raw twin. If so, `n_words` and `tail` move together across the sweep and any raw-vs-prefill mass comparison must account for it rather than reading it as displacement. If not, that is worth more than the sweep.

### Topup does not obviously transfer

Pass 2 is scoped to the **lineage union**. Under prefill the eligible set is different and smaller, so the union is differently shaped. Whether pass 2 means anything here is open, not a port.

### The templated-base control

For the 8+ base arms that do ship a template, `raw base -> prefill base` is available: the frame effect on an **unaligned** model. That is the control for whether the template's effect is itself a product of alignment, or something any model does when wrapped. Worth having on those lineages precisely because it is not available on the rest.

## THE CENSUS IS DONE — 2026-08-22

`experiments/instrument_calibrations/generation_provenance/prefill_census.py`, tokenizers only, no weights, no GPU. All 144, results in `results/prefill_census.csv`.

    role        OK    NO_TEMPLATE   NO_TOKENIZER
    base         9        41             0        of 50
    endpoint    39        11             0        of 50
    member      32        11             1        of 44
                80        63             1

Zero `STEM_LOST`, zero `REFUSED`, zero `GATED`. **Where a template exists at all, the stem always lands last** — the word slot is where the design assumes.

**The 9 bases independently reproduce the HTTP probe's 9.** Two instruments, different failure modes, same answer.

### What this licenses

**Rung B needs only the ALIGNED arm, and 71 of them have it** — 39 endpoints plus 32 members. That is the sweep, and it is much larger than the "~30 of 50" this document estimated from a 15-of-25 sample, which was skewed toward older checkpoints. The earlier estimate is withdrawn.

    rung B  (raw aligned -> prefill aligned)     71 arms
    pair C  (decomposes through A and B)         all 71
    templated-base control (raw -> prefill base)  9 lineages
    fully paired prefill (both arms templated)    7 of 50 lineages

**7 of 50 is the only scarce number**, and it constrains only the fully-paired variant, which the rung design does not need.

### Two facts for the design, not the population

**The wrapper is not a constant.** Characters prepended before the stem: min 21 (`huggyllama/llama-7b`), median 63, **max 1,491** (`BSC-LT/salamandra-7b-instruct`; SmolLM3 1,357). A 1,491-character prior ahead of a 22-character stem is not the same treatment as a 21-character one, and "prefill" names both. Any cross-model comparison of the frame effect has to carry this, or it will read template VERBOSITY as frame STRENGTH.

**8 of the 80 do not support a system role**: gemma-2-9b-it, recurrentgemma-9b-it, llm-jp-3-7.2b-instruct2/3, the three neo_7b arms, Teuken-7B-instruct-v0.6. For those, the `system` slot silently does nothing, so a system-vs-no-system contrast on them is an arm that never received the treatment — the exact failure `frame_eligibility.py` exists to catch.

## Superseded: run this first

**Finish the template census on the ~95 aligned arms.** DONE, above. The base side is done (above); `frame_eligibility.csv` covers only 25 of the aligned arms. Tokenizer-config read, no GPU, about an hour. It answers:

1. how many endpoints can take rung B at all, and which drop out;
2. how many lineages retain both arms — i.e. how much of the roster the frame rung reaches;
3. whether the eligible set is skewed by organisation or vintage, which decides how the population gets declared.

**The census decides the design; the design decides whether the sweep is worth buying.**

## Cost, roughly

2,983 prompts x ~30 eligible arms x ~0.8 s/cell = **~20 GPU-hours** for rung B alone, before any topup. At A100 rates, $30-40. The census may cut the arm count further.

## Open questions

- Does `decoded_boundary` behave at the template/stem seam as it does mid-sentence? The stem is appended after the generation prompt so the boundary logic sees the stem's tail as usual — believed fine, unverified.
- Should rung B use the full prompt population or a subset chosen for continuation-freedom?
- Does the frame rung belong in `movement_v4` proper, with `relation='frame'`, or in its own table? It is an edge between two measurements of the SAME checkpoint, which no existing relation is.
