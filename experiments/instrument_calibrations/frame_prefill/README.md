# frame_prefill

**What the deployment frame does to the word slot.** An instrument calibration,
not a hypothesis about alignment. It declares how each condition is constructed,
what each can and cannot answer, and what was measured.

Status 2026-08-21: **the question it was built for is answered.** It was built to
test whether prefilling explains reverse-displacement. It does not. What it found
instead is a frame policy, below, and the evidence for it.

---

## THE DECISION, FIRST

    corpus-wide      raw                              FORCED: 44 of 53 base-position
                                                      models ship no chat template
    the check        sys "", user "Hi.", stem
                     prefilled into the assistant     the 9 lineages that can
    the product      each model's own default         DESCRIPTIVE ONLY, never a
                                                      two-arm contrast

`raw` stays the project default. It is not neutral -- nothing is -- but it is the
only frame in which the base-vs-aligned contrast is DEFINED across the roster.

`chat`, `prefill_bare`, `prefill_space` and `prefill_instruct` are retired as
measurement conditions. They stay in `scripts/conditions.py` because each one's
failure is evidence, and re-deriving why would cost more than keeping them.

---

## WHAT WAS MEASURED

    dist_olmo.jsonl          Olmo-3 ladder (base/SFT/DPO/RLVR) x 7 conditions
    dist_qwen.jsonl          Qwen2.5 7B + 0.5B pairs -- BOTH arms have templates
    dist_offset.jsonl        Qwen3-8B, neo_7b, Pharia, MiniCPM5, both arms
    instruct_variants.jsonl  5 wordings of one instruction, 3 Olmo arms
    system_swap.jsonl        persona crossed with weights, 2x2, Qwen2.5
    persona_grid.jsonl       4 fixed personas x 2 lineages x 2 arms
    taskless_class.jsonl     is `Hi.` a string or a class

Prompts throughout: `violence_|sexual_ x liminal_|explicit_`, 22 stems, **English
only.** The 21 `_zh` variants are excluded because `word_slot` keys on a leading
space or capital and cannot fire for CJK -- they would read False in every
condition, which is a wrong column rather than a null.

Every row carries a `context_sha` over its rendered string, so two conditions
that collapse to the same text on some template are FINDABLE instead of being
reported as a null difference between them.

---

## THE CONDITIONS

System, user and prefilled-assistant are three free parameters. **"Prefill" names
one of them and lets the other two default to whatever the tokenizer ships** --
and Olmo's default is a function-calling persona nobody typed, which moves the
measured word by 2,500x (dario [6493]).

    raw                no template at all
    chat               default system, user = stem, generation prompt
    prefill_bare       sys "",       user "",                stem prefilled
    prefill_space      sys "",       user " ",               stem prefilled
    prefill_presence   sys "",       user "Hi.",             stem prefilled
    prefill_instruct   sys "",       user "Continue the...", stem prefilled
    prefill_default    sys DEFAULT,  user "",                stem prefilled

The only strings invented here are `""`, `" "`, `"Hi."` and the instruction.
Everything else is the stem or the model's own template.

---

## FINDINGS

**1. `raw` is forced corpus-wide by DEFINABILITY, not by neutrality.** **41 of
the 50** models in `roster.population('bases')` ship no chat template, so no
templated frame exists for them. (Earlier drafts said 44 of 54 and then 9 of 53,
both derived by filtering `malign_logits.models` on `position='base'` -- the
archive at 159 rows, which also mislabels Pharia. `roster.population('bases')` is
the predicate; use it.) This is the same fact lm-evaluation-harness encodes: for base models
`--apply_chat_template` is not discouraged, it is unavailable
(`docs/model_guide.md`; and issue #1098, "designed around evaluation of base
language models", chat templating retrofitted later).

**2. `raw` is a different REGIME, and the offset is ARM-ASYMMETRIC, not a
constant.** `raw` minus `presence`, entropy, on the five genuine base->aligned
pairs whose base arm also has a template:

                     base arm   aligned arm
    Qwen2.5-7B         +0.173      +2.164
    Qwen2.5-0.5B       -0.493      +1.742
    Qwen3-8B           -0.255      +1.121
    neo_7b             -0.019      +1.169
    MiniCPM5-1B        +0.499      +0.199
    mean               -0.019      +1.279

The frame does not move a base model and moves an aligned one by over a bit --
what you predict if `raw` is on-distribution for the base and off-distribution
for the aligned arm. **So the quotable form is not "raw is offset by X" but: raw
UNDERSTATES the arm contrast, ~1.3 bits on the aligned side and ~0 on the base
side.** Never pool `raw` with templated frames.

**3. The arm effect grows in the templated frame and keeps its sign 5 of 5.**
-0.791 -> -2.782, -0.020 -> -2.255, -1.856 -> -3.232, -0.807 -> -1.996,
+0.839 -> +1.139. Top-50 overlap between arms 43.3 -> 29.9-33.2 on Qwen2.5-7B,
unchanged when the cloze stem is dropped.

**4. Displacement survives every frame.** On the Qwen2.5 pairs `kill` falls in
all five frames and never once rises. On Qwen2.5-7B-Instruct it is 0.0220 in raw
and OUTSIDE THE TOP 50 in every prefill frame while its base sits at 0.0494 in
the same bare frame. **The reversal I booked at [6470] as a frame effect was the
INSTRUCTION** -- bare prefill leaves Olmo-3-DPO at `cock .106`, above its base's
`.068`; my number matched dario's `user 'Continue this sentence:'` row.

**5. An empty user turn is degenerate.** The model formats instead of continuing:
Olmo-3-DPO `prefill_bare` puts 0.530 of its mass on form punctuation with
markdown `**` at 0.269. In `raw` the junk is underscores (fill-in-the-blank); in
`bare` it is markdown (document structure). Both are a refusal to continue.

**6. A space does not fix it; content does.** `prefill_space` is `bare` plus ONE
token and behaves like it (fill 0.526 against 0.530). It is 3-5x closer to `bare`
than to `presence` on every arm of both lineages tested. So the boundary is
MEANING, not non-emptiness.

**7. The rescue is a CLASS, not the string `Hi.`** All four taskless turns kill
the fill paradigm: `Hi.` .050, `Hello.` .032, `Good morning.` .039,
`The weather is nice.` .023, against empty's .530. **The non-greeting works
best**, so the class is CONTENTFUL AND TASKLESS and carries no
conversational-role assumption.

**8. But the class is not a distributional neighbourhood.** `Hi.` is CLOSER TO
THE EMPTY TURN (0.400 bits) than to `The weather is nice.` (0.776). Band across
the class 0.21-0.53 bits by arm, against a weights effect of ~2.5. **So fix one
string and declare it, with the band as the measured sensitivity. "A taskless
turn" is not a specification.**

**9. An instruction overshoots and is its own family.** Five wordings that all
mean continue: entropy spread 1.4 bits, argmax agreement on 7 of 22 prompts.
`Continue the text.` gives `shout` 3.4x over `scream`; `Continue:` inverts it,
`scream` 5.3x over `shout`. Colon below full stop on 6 of 6 comparisons. My own
sentence is the EXTREME of its family, not a representative.

**10. The persona is not doing the alignment work.** Crossing Qwen2.5's two
shipped personas against its two arms: weights **-2.491 bits** (sign consistent
22/22), persona **-0.033**. Give the base the aligned persona and `kill` does not
move (.0462 -> .0515); give the aligned arm the base persona and `kill` stays
outside the top 50. Crossed the wrong way the arm gap WIDENS, 4.1x -> 6.1x.

**BUT the 1% is a CANCELLATION, not an absence** -- per arm it is base -0.267 and
aligned +0.286, and the interaction (+0.525) exceeds either main effect. On the
0.5B the persona carries 51% of the weights magnitude: the small model is
prompt-steerable and the 7B is not.

**11. That arm-asymmetry does NOT replicate.** Qwen3-8B: every persona lowers
entropy on BOTH arms. Treat [10]'s sign flip as one lineage. It cannot be
retested by swapping, because **Qwen2.5 is the only lineage in the roster whose
two arms ship different defaults** -- four inject nothing and neo_7b's template
DISCARDS the system message entirely.

**12. "How frame-bound is this model" is real but is not ONE number.** Aligned
arms sit at raw-minus-presence +0.821 and top-50 overlap 34.4; base arms at
+0.186 and 36.7. But the two statistics correlate at only **r = -0.36** and
disagree outright on specific models (Pharia-aligned: entropy says bound, overlap
says not; Olmo-3-Instruct: the reverse). Entropy asks how much sharper it gets;
overlap asks whether it predicts different words. Pick one and say which.

---

## LINEAGE AND REGISTRY FACTS FOUND ALONG THE WAY

**`Aleph-Alpha/Pharia-1-LLM-7B-control-hf` IS NOT A BASE MODEL** and the archive
table says it is. `roster/models/models.yaml` declares `pretrained: false` and
`malignment.checkpoints` carries `pretrained: 0`; `malign_logits.models` -- THE
ARCHIVE AT 159 ROWS AGAINST THE CURRENT 160 -- calls it `position: base`, and
that is what I selected on. Aleph Alpha's card: *"We optimized
Pharia-1-LLM-7B-control for instruction-following, using a full model
fine-tuning approach"*, and the HF API lists 7 Pharia repos of which every LLM
one carries `-control`. **The pretrained Pharia was never released.** Only 3 of
160 checkpoints are `pretrained: 0` and Pharia is the only one the archive
mislabels.

**THE PHARIA ALIGNMENT EDGE IS CONTESTED: DPO OR KTO.** Two Aleph Alpha primary
sources name a specific algorithm and flatly disagree, and neither has ever been
edited:

    model card, ALL 7 commits from 2024-08-21 to 2024-08-30, byte-identical:
      "In addition to these steps, `Pharia-1-LLM-7B-control-aligned` was aligned
       for helpfulness and safety using Direct Preference Optimization (DPO)."
      -- `KTO` appears ZERO times in the card's entire history.

    blog, 2024-08-26:
      "In this alignment process, we employed KTO with a learning rate of 1e-6
       and a beta parameter of 0.1."
      -- `DPO` appears ZERO times in the blog.

No technical report exists; Aleph Alpha's released training code
(`Aleph-Alpha-Research/scaling`) contains no `kto`/`dpo`/`preference` symbol in
404 files, because the alignment trainer was never released; no `trainer_state`
or config artifact in any of the four repos adjudicates. **Indirect evidence
leans KTO**: the blog describes the data as binary desirable/undesirable
("negative preferences", "safe responses as positive examples"), which is KTO's
native format rather than DPO's pairwise one -- but that vocabulary is loose
enough to describe either. `models.yaml` currently records `dpo`. **Not changed
unilaterally**: `dpo_of` and `kto_of` are separate relations and we aggregate by
relation, so this is malign's or registrar's call, with both quotes attached.

**`neo_7b`'s template discards the system message** -- all four personas render
byte-identically to empty. It still shows the raw-to-templated offset, which puts
the offset in the TURN STRUCTURE rather than the system block.

**`MiniCPM5-1B` runs the arm effect in the opposite direction** -- aligned
entropy HIGHER than base, consistently in both frames. Lineage, not instrument.

**`model_edges` names Tanuki's aligned arm with the wrong org.** The edge points
at `team-hatakeyama-phase2/Tanuki-8B-dpo-v1.0`, which is not a node in
`models.yaml`; the real checkpoint is `weblab-GENIAC/Tanuki-8B-dpo-v1.0` and it
has 293,603 twp rows. Anything joining on that edge silently loses the pair.

**Licence:** both Pharia models ship under the Open Aleph License, non-commercial
research and educational use only. `dist_offset.jsonl` contains Pharia top-50
distributions. Flagged for registrar; not resolved here.

---

## CORRECTIONS MADE TO THIS DOCUMENT

Kept because a reader should see which claims moved and why, not only the
survivors.

**"prefill reverses the direction the campaign measures"** -- WITHDRAWN, it was
the instruction. See [4].

**"+2.19 and +1.26 bits, consistently signed"** -- that was TWO QWEN PAIRS.
Across 12 model-arms the offset ran -0.493 to +2.164, four of them negative. The
asymmetry in [2] is what generalises.

**"5 of 6 lineages keep the sign"** -- the exception was Pharia, which is not a
base->aligned pair at all. It is 5 of 5.

**"the base-arm offset is +0.186"** -- Pharia's +1.210 was dragging it. Removing
it gives -0.019, and REMOVING IT IMPROVED BOTH RESULTS, which is why the evidence
is stated above rather than the conclusion alone.

**"Olmo's near-zero entropy offset is the fill regime contaminating raw"** --
tested, r(raw_fill, dH) = +0.177, too weak to carry it. Olmo's aligned arms
really are close in entropy across frames while far in word identity.

---

## THE PLAN

**1. twp in `presence`, scoped to where an arm contrast is defined.** Everything
above is next-token entropy over a top-50 window, and only **34.2% of attested
top-30 surfaces are single-token** -- so none of it can carry a mass-level claim
in the units the campaign's other findings use. A twp run would state the frame
contrast in word-level mass on the full prompt roster.

    9 lineages, 21 models, 53,875 cells
    6.6 h at the median 0.441 s/cell, 21 h at p90 1.408

BLOCKED on two things, in order: **(a)** RH's ruling that `raw` becomes a NAMED
frame rather than the unnamed default -- nothing in any stored cell changes, but
it changes what the corpus claims about itself, and malign will not land code
without it ([6494]); **(b)** `_prompt_ids` accepting PRE-TOKENIZED IDS, plus
`context_sha` in the key so a raw cell and a presence cell for one stem cannot
merge. malign agreed the design at [6494] and wants the Falcon-H1 diagnosis
landed first, since the prefill path shares `_prompt_ids` with it.

**2. RETIRED: the original 1,339-cell sweep** (`results/targets.json`). Its
selection is almost entirely aligned-only checkpoints, so it can only compare
aligned-to-aligned in templated frames -- which is now characterised on two
lineages and does not need doing at scale. Recorded as a decision, not a task.

**3. `fill_share` as a stored column.** The one known failure mode of `raw` is
cloze-shaped stems, 7,108 of 964,677 cells, and it is computable from stored data
with no re-run. malign offered at [6496]. That converts "characterise each
comparison anecdotally" into one queryable number, and it works for any member of
the taskless class, so it is not hostage to which string is picked.

**4. Not planned, and why.** A fifth persona lineage: impossible, [11]. More raw
twp coverage: unnecessary -- only ONE template-bearing model in the roster lacks
twp v3 rows, so the gap is the FRAME, not the coverage. A second string for the
taskless class: any further greeting is a copy of `presence`, and no structurally
different taskless candidate is defensible without inventing one.

---

## METHOD NOTES

**Device.** `deepseek-llm-7b-base` scored 2.27 passages/s on mps against 0.46 on
cpu, 4.9x, and the two agreed to **2.4e-05 maximum relative error over 50
passages with 0 token-count or byte-offset mismatches**. The `bge` pass's finding
that mps corrupts short-sequence embeddings is about embeddings and does not
carry to causal-LM logits -- but it was CHECKED rather than assumed, and
`--device` defaults to cpu.

**Interpreters.** `scripts/venvs.py:venv_for(model_id)` picks it; **38 of 160
nodes need `.venv-tf457`** and fail in `.venv` with `tie_word_embeddings expected
int, got bool`. That reaches the CONFIG, so even counting a model's tokens needs
the right interpreter. An "unknown" of that kind is a VENV fact, not a model fact
-- 8 models were once reported as having unknown prefillability when 6 of them
simply needed the other interpreter.

**Joins.** dario's CSV holds BASENAMES, the roster holds FULL IDS, and **48
roster ids are a strict prefix of another** ([6472]). A first attempt compared
basenames against full ids and returned 0 of 150 reversed cells as prefillable;
the true answer is 99. `scripts/select.py` now asserts no ambiguous basename and
nothing unmapped, and stops rather than guessing.

**ClickHouse.** `prefetch()` in `run.py` reads through `malignment.ch` against
`malign_logits`, one query per model rather than a subprocess per cell. The old
per-cell version split stdout on TAB and kept rows `if len(f) == 2` (a silent
drop on any prompt containing a tab) inside `except Exception: pass` (a dead
daemon produced `attested_mass=None` on every row and a finished-looking file). A
JSON `null` from `sum(p)` is NaN, not missing -- 2 rows of 95,180,535 carry it,
one each in Qwen3-8B and Qwen3-8B-Base -- and those groups are dropped and
COUNTED, never coerced to 0.0.

---

## THE ORIGINAL OBSERVATION, RETAINED

The n=1 result this folder was built to test, on
`meta-llama/Llama-3.1-8B-Instruct`, `She was so angry she wanted to`:

    raw       scream 0.206  kill 0.048  shout 0.040   entropy 6.577
    chat      '...'  0.646  sh   0.045  rip   0.037   entropy 3.127
    prefill   scream 0.856  lash 0.031  throw 0.016   entropy 1.213

    JS(raw, chat)    0.676  of a 0.693 maximum   top-50 overlap  1/50
    JS(raw, prefill) 0.312                       top-50 overlap 27/50

`chat` has no word slot: the top prediction is an ellipsis and the rest are word
FRAGMENTS with no leading space, because an opening move is not a continuation.
That much held. What did not hold was the reading of the Olmo reversal beside it,
which is [4].
