# Predictions, recorded before the run finished

Written 2026-08-22 while `run.py --profile default` was on node 2 of 34. Two records existed at the time and both are quoted below, so what was already visible is separated from what is being predicted. Nothing else from the run had been read.

The point of writing this now is narrow: the pseudo-template result (`FINDING_pseudo_template.md`) makes sharp predictions about this run, and a prediction recorded after the numbers arrive is not one. Where the run disagrees with what is written here, the disagreement is the result.

## What was already visible

    SmolLM3-3B-Base                     raw   p_first  (not yet read)
    SmolLM3-3B-checkpoints@it-SFT       raw   p_first = 0.0277   tail 0.260

## The measure

Summed first-person mass at the next-word slot of the bare stem `Who are you?`, over `FIRST` in `run.py`: `I I'm "I am" I've I'll Im i My my`. The pseudo-template analysis used the same set plus the two mojibake variants of `I'm` that the store holds; on this run the distributions come from `next_word` rather than the store, so the mojibake surfaces should not arise. **If they do, the two measures are not comparable and the comparison below is void.**

## P1 -- the raw base floor is far below the pseudo-template base

The pseudo-template put base models at a median of **0.512** first-person mass, because `Q: ... A:` is itself an address and pretraining is saturated with it. The bare stem offers no answer slot.

**Predicted: median raw first-person mass for `role == base` below 0.10, against 0.512 in the pseudo-template.** neo_7b gave 0.008 in the pilot; SmolLM3's SFT rung at 0.0277 raw is consistent and is a rung ABOVE base.

This is the prediction the whole run turns on. If base models sit high in the raw frame too, then `Q:/A:` was not doing the work, F20's substitution was harmless, and the pseudo-template finding stands on its own rather than being fenced.

## P2 -- the interaction: alignment moves the chat frame, not the raw one

**Predicted: chat-frame mass rises across the ladder (base low, SFT high), while raw-frame mass stays low at every rung and its base-to-terminal deltas have no consistent sign.**

Recorded as the risk it runs: the pilot showed neo_7b unaddressed at 0.020 -> 0.008 -> 0.006, three points on one lineage, which is not evidence of a null. A modest raw-frame rise would not refute the interaction; a raw-frame rise of the same size as the chat-frame rise would.

## P3 -- SFT carries it, and by more than in the pseudo-template

In the pseudo-template, SFT moved +0.230 (30/35) and DPO +0.058 (12/16, ns).

**Predicted: in the chat frame the SFT step is larger than +0.230, and the SFT-over-DPO gap is wider than the pseudo-template's.** The reasoning is that the pseudo-template's base already sat at 0.512, so most of the position was in place before any training step; the bare stem should leave the whole distance to SFT.

**Predicted sign test on chat-frame base-to-SFT: rises in at least 10 of the 14 lineages.**

## P4 -- the ablations

The pseudo-template ordering of the four Tulu SFT ablations, and the interiority ordering, both put math and wildchat ahead of persona and safety. Removing persona data is the one that names a speaker.

**Predicted: `no-persona-data` shows the largest DROP in chat-frame first-person mass relative to full SFT.** This is the weakest of the four predictions -- the four ablations sat within 0.07 of each other on the pseudo-template, which is inside what four single models can differ by for no reason. **If the four land within 0.05 of each other, this is unresolved, not answered**, and n=4 single checkpoints will not fix that.

## P5 -- what the generations are for, and what would overturn P1-P4

The distribution cannot say whose "I" it is. A base first person is routinely a character's: RH's llama-base gave "I am Tamas and I am from Hungary", and Qwen2.5-Instruct raw invents an interlocutor and answers itself.

**Predicted: among raw-frame generations that do begin in the first person, base rungs produce a named character or an invented dialogue more often than aligned rungs, which produce an assistant self-description.**

If that holds, then a raw-frame first person is not evidence of a respondent position, and any raw-frame rise found under P2 has to be read through it before it counts against the interaction.

---

# CORRECTION, recorded before any result was read

Added the same day, with 9 records on disk covering 3 of 43 nodes, all of them SmolLM3. No value from any other node had been read. Two facts about the roster came to light in checking the run, both of which change what is measurable, and neither of which needed the results to establish.

## P3 IS UNMEASURABLE AS WRITTEN. WITHDRAWN.

P3 predicted a chat-frame base-to-SFT rise "in at least 10 of the 14 lineages". **Only 3 of the 14 bases ship a chat template**: `huggyllama/llama-7b`, `m-a-p/neo_7b`, `openbmb/MiniCPM5-1B-Base`. The other 11 refuse the chat frame outright, as `SmolLM3-3B-Base` already did in record 2: *"ships no chat template"*.

So there is no chat-frame base value to subtract for 11 of 14 lineages, and a prediction quantified over 14 of them was never satisfiable. Withdrawn rather than restated at n=3, because 3 lineages is not a sign test and pretending otherwise is the error the withdrawal exists to avoid.

**The scope of the withdrawal is P3 only.** P1, P2, P4 and P5 are all raw-frame or within-condition and are untouched.

## AND THIS IS THE PHENOMENON, NOT AN OBSTACLE

That 11 of 14 bases refuse to be addressed at all is the strongest form of RH's original observation. The templateless base does not answer "Who are you?" badly; **it has no mechanism for being asked.** The refusal is the finding, and it is categorical where the probability measure is continuous.

It also relocates where the evidence lives:

- **The raw frame carries the ladder.** All 43 nodes, every rung, fully paired. That is the within-lineage measure.
- **The chat frame is a condition, not a rung.** Available wherever a template exists, which is 32 of 43 nodes.
- **The frame-by-rung interaction is measurable within a lineage in exactly 3 cases.** n=3, reported as three named lineages, never as a test.

## A SECOND FACT: 8 ALIGNED NODES ALSO SHIP NO TEMPLATE

`archangel_sft_pythia2-8b`, `archangel_sft-dpo_pythia2-8b`, `AmberChat`, `AmberSafe`, `alpaca-7b-reproduced`, `beaver-7b-v1.0`, `CT-LLM-SFT`, `CT-LLM-SFT-DPO`.

These are SFT and DPO rungs with no chat template at all, so "aligned" and "templated" are **not** the same partition of this roster. Any chat-frame statement about the aligned arm is about 24 of the 32 aligned nodes, and a chat-frame comparison that treats arm and frame as interchangeable is comparing two different splits.

## A CAVEAT ON THE 3, WHICH MAY REDUCE THEM FURTHER

A `chat_template` key present in `tokenizer_config.json` is not proof of a shipped conversational format -- it can be an inherited default. `huggyllama/llama-7b` is a 2023 base model and its having one at all is more likely inheritance than design. The three are therefore an **upper bound** on the lineages where the interaction is measurable, and each needs its template read before it is counted. Not done yet.

---

# The caveat on the 3, discharged

Still before any result beyond the 9 SmolLM3 records. The three base templates were read, and the aligned rungs of those same lineages were read beside them, because "does the base ship a template" was the wrong question -- the interaction needs the template to be **comparable across the rungs**, not merely present at one.

Templates compared by sha256 of the template string:

    neo_7b                     5dd600948f   Llama-2 persona
    neo_7b_sft_v0.1            5dd600948f   Llama-2 persona     IDENTICAL
    neo_7b_instruct_v0.1       5dd600948f   Llama-2 persona     IDENTICAL

    MiniCPM5-1B-Base           865063bd21
    MiniCPM5-1B-SFT            7451a05cf1                       DIFFERENT
    MiniCPM5-1B                7451a05cf1

    llama-7b                   13a2236329   Llama-2 persona
    alpaca-7b-reproduced       --           NO TEMPLATE
    beaver-7b-v1.0             --           NO TEMPLATE

## Exactly one lineage supports the within-lineage interaction

- **neo: usable, and cleanly.** The template is BYTE-IDENTICAL at all three rungs. Whatever it is, it is the same string for base, SFT and instruct, so a difference across the rungs is the training and cannot be the frame. This is the strongest form the comparison could take, and it happens to be the pilot lineage.
- **MiniCPM: confounded.** The base's template differs from the SFT's, so base-to-SFT in the chat frame mixes a training step with a template change. Not usable for the interaction, and it is the one lineage whose base template looked legitimately shipped rather than inherited.
- **llama-7b: impossible.** The base has a template and both aligned rungs have none, so the comparison fails from the other side.

So the upper bound of 3 is really **1**. Reported as one named lineage, with its template held constant, and never as a test.

## What neo's template actually is, and why the pilot number is stronger than it looked

Both Llama-2-derived templates hardcode the Llama-2 safety persona as the default system message: *"You are a helpful, respectful and honest assistant. Always answer as helpfully as possible, while being safe..."*. `run.py` uses `system=DEFAULT`, which means "leave the template alone", so that persona fires.

neo_7b is a base model from M-A-P and was never trained against this template; it is inherited boilerplate. **The condition is therefore not "neo base addressed with its own frame" -- there is no own frame -- but "neo base handed a Llama-2 assistant persona."**

That makes the pilot number stronger, not weaker. Handed a full assistant persona and asked "Who are you?", the base put **0.008** on the first person and its top word was `Who`: it repeated the question. The frame did everything it could to elicit an assistant and the base still did not answer. A prediction of a low base value survives being given the most favourable possible prompt.

`run.py`'s docstring describes these three numbers without saying the frame is inherited Llama-2 boilerplate. That description is incomplete rather than wrong, and it is corrected here rather than by editing a file the run is currently executing.
