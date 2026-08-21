# twp under a chat template: the prefill frame

Status: **not started, not costed past a rough estimate, and one load-bearing fact is unverified.** Written 2026-08-21 so the reasoning survives; nothing here has been run.

## The question

Every twp cell in the corpus is measured on a **raw, untemplated stem**. The model sees `He started stroking his` and nothing else — no chat template, no system message, no turn structure. That is the right instrument for a base model and it is what all 820,246 cells hold.

But an instruct checkpoint is not normally used that way, and the template is not neutral: it injects a persona, a turn boundary, and often a vendor system message the caller never typed. So there is a real question the corpus cannot currently answer — **how much of what we call alignment-induced displacement is in the weights, and how much is in the frame the weights are normally wrapped in?**

That is a different mechanism from the one the campaign has been measuring, and it is separable.

## Prefill is the only frame with a word slot in it

`malignment/generate.py` declares four frames — `raw`, `chat`, `continue`, `system` — and only one of them can host a twp measurement.

Under `chat`, `continue` and `system` the stem occupies the **user turn**, so the model's next word begins its *answer*: `I`, `Sure`, `It`. That is a perfectly good object but it is not the same object as "the word that continues this sentence", and comparing it to a raw cell would be comparing a reply to a continuation.

Under `prefill` the stem is appended **after** the generation prompt, inside a started assistant turn, so the model resumes a sentence it is already writing. `render()`'s own docstring puts it exactly:

> prefill True -> `text` goes in a prefilled ASSISTANT turn instead, and the user turn takes `user_msg`. The model resumes a sentence it is already writing, **which is the only chat-mode position with a word slot in it.**

So the design space is not "which frame" — it is prefill, or nothing.

## What already exists

| | |
|---|---|
| `generate.render(loaded, text, system, user, prefill, user_msg, template)` | composes the string, returns `(rendered, sys_supported)` |
| `generate.encode(loaded, text_in, templated)` | tokenises with exactly one leading BOS — neither blanket `True` nor blanket `False` is correct, and this is measured |
| `generate.next_token(..., prefill=False)` | token grain, **already frame-aware** |
| `Checkpoint.next_token(..., prefill=...)` | passes it through |

## What is missing

`Checkpoint.next_word()` delegates to `probs(prompt, loaded=None, **kw)`, which hands the raw string straight to `twp.expand`. **The frame machinery stops at the token grain and never reaches the word instrument.** That is the entire code gap: twp has no notion of a frame.

The plumbing itself is small — `probs()` would take the frame slots, call `render()`, and pass the rendered string to `expand`. `encode()`'s one-BOS rule already handles the tokenisation trap that would otherwise bite. The hard parts are all upstream of the code.

## THE PROBLEM THAT DECIDES WHETHER THIS IS WORTH DOING

**A base model ships no chat template, so it cannot be prefilled — which means there is no base→aligned edge under prefill.**

Every displacement result in this campaign rests on that edge. `movement` compares a base arm against an aligned one; if the base arm cannot take the frame, the pair does not exist. So a prefill sweep cannot extend the existing finding. It can only support:

- **within-checkpoint**: raw vs prefill on the same model — *what does the template do that the weights did not* — which is the interesting question and a genuinely new one;
- **across aligned arms**: comparing instruct checkpoints to each other under a shared frame.

Neither is the current contrast. This is a new experiment, not an extension, and it should be proposed as one.

### And the population is set by packaging, not by design

`experiments/instrument_calibrations/generation_provenance/results/frame_eligibility.csv` settles eligibility per model by byte comparison, because a template that silently discards a system block raises nothing and produces a treatment arm that never received the treatment.

Read 2026-08-21, and it covers **25 models with zero base arms in the sample**:

    OK             15    of which endpoint arms 11
    NO TEMPLATE     5    of which endpoint arms  5
    NO TOKENIZER    5    of which endpoint arms  2

Two things follow.

**The base-arm claim above is UNVERIFIED.** The one artifact that could settle it never tested a base arm. "Base models ship no template" is plausible and is not measured here. Do not build a plan on it without checking.

**Aligned arms are not uniformly eligible either**, which is the part I got wrong when reasoning without the file. Five endpoint checkpoints ship no chat template at all — `archangel_sft-dpo_pythia2-8b`, `AmberSafe`, `beaver-7b-v1.0`, `eleuther-pythia6.9b-hh-dpo`, `RedPajama-INCITE-7B-Chat`. If 15-of-25 holds, a prefill sweep reaches roughly **30 of the 50 endpoints, not 50** — and the eligible set is selected by whether a vendor happened to ship a template, which correlates with vintage and organisation rather than with anything we are studying. That is a population that has to be **declared and reported**, not discovered at analysis time.

## Run this first, before anything else

**A template census across all 145 measured models.** Tokenizer-config read, no GPU, no fleet, about an hour of laptop time. It answers:

1. do base arms in fact refuse? (the load-bearing unverified fact)
2. how many endpoints are eligible, and which?
3. how many lineages retain **both** arms under prefill — i.e. is any paired design available at all?

If (3) comes back near zero the experiment is within-checkpoint only, and that changes what it is for. **The census decides the design; the design decides whether the sweep is worth buying.**

## Design notes, for when it is

### The three free slots are not optional

`conditions.py` measured the probability of a target word moving **2,500x** on one stem across combinations the caller never typed: default system `.246`, empty system `.106`, a persona `.0001`.

    system   DEFAULT -> the template's own persona fires
             ""      -> asserts an empty one, OVERRIDING that persona
             "..."   -> ours
    user_msg what occupies the user turn under prefill; "Hi." is the PRESENCE
             CONTROL, semantically empty on purpose

So `frame='prefill'` alone is not an identity. `system` and `user_msg` must be in the cell key. Otherwise this repeats the decoder problem `generate.py` documents — an unpinned parameter is not a constant, it is a per-vendor covariate aligned with the arm contrast.

And `render()` returns `sys_supported`: a template that drops a system block yields a condition wearing the wrong name. That flag has to reach the stored cell rather than being swallowed.

### Storage: a frame dimension that must never merge

This is the **third** instance of one pattern in this corpus:

    rule_version   selects the TABLE      (v3 -> twp_cells, v4 -> twp_cells_v4)
    topup          must not be merged     (two measurements of one surface)
    frame          ...same argument

A prefill cell measures a **different surface**, not the same surface differently. Put `frame`, `system`, `user_msg` in the cell key with `raw` as the default for everything already measured, and expect the `_best` question to come back: it should not collapse across frame, for the same reason it must not collapse pass 1 into topup.

### An expectation, stated so it can be falsified rather than confirmed

Templated distributions should be **sharper** — an instruct model is confident inside its own frame — so at fixed `THETA = 0.001` a prefill cell should admit **fewer words** and carry **more tail** than its raw twin.

If that holds, `n_words` and `tail` move together across the whole sweep, and any raw-vs-prefill mass comparison has to account for it rather than reading it as displacement. If it does not hold, that is worth more than the sweep.

### Topup does not obviously transfer

Pass 2 is scoped to the **lineage union** — words a sibling cleared and this model did not. Under prefill the "lineage" is a set of arms that cannot include their own base, so the union is smaller and differently shaped. Whether pass 2 means anything here is an open question, not a port.

## Cost, roughly

2,983 prompts x ~30 eligible arms x ~0.8 s/cell = **~20 GPU-hours** for pass 1 alone, before any topup. At A100 rates that is $30-40. The census above costs nothing and may cut the arm count further.

## Open questions

- Does a base arm ever accept a chat template? (census)
- Is any **paired** design available under prefill, or is this within-checkpoint only?
- Does `decoded_boundary` behave at the template/stem seam the way it does mid-sentence? The stem is appended after the generation prompt, so the boundary logic sees the stem's tail as usual — believed fine, unverified.
- Should the raw-vs-prefill contrast use the same prompt population as the corpus, or a subset chosen for continuation-freedom?
