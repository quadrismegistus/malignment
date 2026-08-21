# SPEC: what a templated twp run must emit, and where each field lands

**Status: PARKED until the current fleet run completes (RH, 2026-08-21).** This
is the consumer-side statement — what `frame_prefill` will read — written before
the producer is changed, so a mismatch is found now rather than after ~29 hours
of compute. Implementation is malign's; nothing here is a request for a
particular patch.

Companion to `README.md`, which carries the findings and the frame policy.

---

## 1. THE ONE-LINE VERSION

`twp` gains an optional PRE-TOKENIZED IDS input. Every cell measured through it
carries a digest of the FULL RENDERED CONTEXT, not just the stem, because the
stem does not identify the measurement.

---

## 2. WHY THE STEM IS NOT THE KEY

Four `prefill` rows for one stem on Olmo-3-7B-Instruct-DPO, varying only strings
the caller never typed (dario [6493]):

    default system (function-calling persona)   cock .246
    "You are a helpful assistant."              cock .181
    empty system string                         cock .106
    "You are a creative fiction writer."        cock .0001

A single `frame: prefill` label keys a **2,500x range** to one cell. If those
share a key the store averages them; if they collide with the `raw` cell too,
`topup`'s lineage union is computed over a population that does not exist
(malign [6494]).

**So `frame` alone is insufficient. `context_sha` is the discriminator.**

---

## 3. FIELDS THIS FOLDER WILL CONSUME

    prompt          the stem, verbatim, for reading
    prompt_ids      the ids actually measured
    context_sha     digest over the rendered string -- THE DISCRIMINATOR
    frame           raw | chat | prefill              (coarse, for filtering)
    system          the system string AS RENDERED, including a default
                    the caller did not choose
    template_id     hash of the tokenizer's chat_template; templates change
                    under us
    bos_policy      already stored; the caller owns BOS when ids are passed,
                    so the policy APPLIED must be recorded, not inferred
    resolver_id     'pretokenized'

`system` is stored VERBATIM rather than as a flag precisely because of the table
in §2: the default is not neutral and nobody typed it. A boolean `templated=true`
would hide the entire effect.

---

## 4. THE THREE PLACES IT LANDS

Not two. The KEY is separate from the BODY, and conflating them is a defect this
repo has already booked.

### 4a. The stash key — `Checkpoint.key()`, `checkpoint.py:234`

Its own docstring states the binding rule:

> *"`rules=None` IS v3 AND MUST STAY THE EXACT DICT IT WAS. Adding a field
> unconditionally -- even one set to `None` -- would change every v3 key and
> orphan 984,857 stored cells."*

**So the frame fields must appear in the key ONLY when a frame is passed**,
exactly as `rules` and `prompt_cache` did when v4 arrived.

This is also the mechanical answer to the "is `raw` now a named frame" question:
done this way, **no existing key moves and nothing is retroactively relabelled**.
A stored cell keeps meaning exactly what it meant; new cells say more.

### 4b. The jsonl body — `runners.py:638`

    rec = dict(stamp, model=ck.model_id, prompt=p)

Written to the local HashStash and identically on fleet boxes.

**KEY AND BODY MUST BE WRITTEN FROM ONE SOURCE.** `ingest.py:357` records the
failure: a record whose KEY carried `rules: "v4[decoded,depth=9]",
prompt_cache: true` while its BODY carried `rules: None, prompt_cache: None`,
because `run_v4.py` built a stamp that disagreed with the key. The frame fields
are the same shape -- an instrument field set in two code paths -- and are the
most likely thing to reproduce it.

### 4c. The ClickHouse ingest — `ingest.py`

    line 202   CREATE TABLE {db}.twp_cells      already carries bos_policy
    line 348   INSTRUMENT_FIELDS = ("rule_version", "dict_sha", "rules",
                                    "prompt_cache")

`INSTRUMENT_FIELDS` decides what counts as instrument identity. **A frame field
must join it or the ingest treats two frames as one cell.**

---

## 5. THE POPULATION, AND HOW IT IS DERIVED

Use `roster.population()` and `roster.lineages()`. Do NOT filter
`malign_logits.models` on `position='base'` -- that is the ARCHIVE at 159 rows
against the current 160, and it calls
`Aleph-Alpha/Pharia-1-LLM-7B-control-hf` a base model when `models.yaml` and
`malignment.checkpoints` both say `pretrained: false`. Counting that way gave
three successive wrong denominators (10 of 54, then 9 of 53) before the roster
function gave 9 of 50.

    population('all')              160 | template 91 | none 67 | unknown 2
    population('bases')             50 | template  9 | none 41
    population('endpoints')         50 | template 39 | none 11
    endpoint lineages, all members 144 | template 79 | none 63 | unknown 2
      roots and members BOTH templated:  18 pairs over 9 roots

**Two populations, two different questions:**

  * **89 models / 233,607 cells** -- every prefillable model with twp v3 cells.
    28.6 h at the median 0.441 s/cell, 91.4 h at p90 1.408. Answers *how
    frame-bound is each model* (aligned-raw vs aligned-presence), which needs no
    base arm and so is the better-powered design.
  * **9 roots / 18 pairs** -- where BOTH arms have a template, so a templated
    ARM CONTRAST is defined at all. Everything else is aligned-only.

Two prefillable models have no twp v3 cells: `allenai/Olmo-3-7B-Think` and
`mistralai/Mistral-7B-Instruct-v0.1`.

---

## 6. `prefillable_roster.json` IS NOT DEFINITIVE AND MUST BE REGENERATED

`~/malignment-data/prefillable_roster.json` is a MEASUREMENT taken 2026-08-21
06:16, not a config file: 160 entries, 158 booleans and 2 error strings. Two
defects, both mine:

**It records no environment.** The repo already knows this class of fact is
environment-keyed -- `data/model_load_environments.json` exists because internlm2
resolves to a different tokenizer class on transformers 5.14.1 than on 4.57.1,
which changes what template you get. A verdict taken in `.venv` may be false in
`.venv-tf457`, and 38 of 160 nodes need the second interpreter.

**It tests a weaker predicate than the sweep needs.** It asks *does a
`chat_template` exist*. What is needed is `conditions.check()`: do all conditions
render, does the tokenizer round-trip the stem, does the prefill string end with
the stem. `m-a-p/neo_7b` passes the weak test and **silently discards the system
message** -- all four personas render byte-identically to empty -- which never
appears as `False`.

**Before the run: regenerate per-venv using `check()`, and put the environment in
the file.** A model is prefillable IN AN ENVIRONMENT, not in general.

---

## 7. WHAT THIS FOLDER WILL DO WITH THE OUTPUT

Restate the frame contrast in WORD-LEVEL MASS rather than next-token entropy.
Everything in `README.md` is next-token over a top-50 window, and only **34.2% of
attested top-30 surfaces are single-token**, so none of it can carry a mass-level
claim in the units the campaign's other findings use.

Specifically: `raw` minus `presence` per model, which `README.md` [2] gives as
+1.279 bits on aligned arms and -0.019 on base arms over five lineages, restated
over the full prompt roster in the units of F01.

---

## 8. SEQUENCING

    1  RH's ruling                     see §4a -- may be smaller than it sounded
    2  malign lands the second dtype   dario [6514]: models.load_model still
       path                            hardcodes float16, three producers use it
    3  _prompt_ids accepts ids         additive, ids=None reproduces today
                                       byte-for-byte; no fleet dependency
    4  context_sha in the key          NEEDS A QUIET CORPUS -- mid-run gives a
                                       store where some cells carry the field
    5  regenerate prefillable_roster   §6, per-venv, using check()
    6  the run                         needs boxes; cost is malign's to quote
