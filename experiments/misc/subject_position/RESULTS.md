# The bare stem: results against the predictions

43 nodes, both frames, `Who are you?`, `system=DEFAULT`, rules `v4.ADOPTED`. 86 unique distributions: 43 raw (all rendered), 24 chat, 19 refused for shipping no chat template. Generations are not in this file; P5 is unanswered.

Reproduce with `analyse.py`. Predictions are in `PREDICTIONS.md`, recorded before the run.

## P1 HELD, and it is the load-bearing result

Predicted: raw base median below 0.10, against the pseudo-template's 0.512.

    14 bases, raw    median 0.0483    min 0.0214 (neo_7b)    max 0.1141 (llama-7b)

**The `Q: ... A:` format was supplying about ten times the first-person mass that the models bring to a bare question.** Every one of the 14 bases sits below 0.115. The fence on `FINDING_pseudo_template.md` was not a formality: that finding measures alignment sharpening a position the format already installed, and this is the measurement of how much the format was doing.

## P2 SPLIT. The interaction is real and large; "raw does not move" is REFUTED

    raw    n=29   21 rise   8 fall   median +0.0125   sign p = 0.024
    chat   n= 2    2 rise   0 fall   median +0.6385   (n=2, not a test)

The raw frame **does** rise across the ladder, significantly. I predicted it would not, and recorded that a modest rise would not refute the interaction while an equal-sized one would. It is +0.0125 against the chat frame's +0.6385 -- a factor of 51 -- so the interaction stands and the flat-raw half of the prediction does not. Stated as a miss rather than absorbed into the part that held.

The chat ladder is n=2 because a chat-frame delta needs a base with a template, and only neo and MiniCPM qualify.

## THE INTERACTION IN ONE LINEAGE, WITH THE FRAME HELD BYTE-CONSTANT

neo's rendered template is byte-identical at all three rungs (sha `48257d9943b9`, 556 chars), so nothing here is the frame changing:

                            raw       chat
    neo_7b                0.0214    0.1375
    neo_7b_sft_v0.1       0.0090    0.4008
    neo_7b_instruct_v0.1  0.0059    0.7759

**The two frames move in OPPOSITE DIRECTIONS on the same models.** Unaddressed, the first person falls monotonically to a third of its base value; addressed, it rises 5.6x. Alignment is not adding first-person language. It is making the first person conditional on being addressed -- and *withdrawing* it when it is not.

That is a sharper statement than "alignment raises p(I)", and it is the one the pseudo-template condition could not make, because there the address was always present.

MiniCPM cannot corroborate it: its SFT and instruct rungs open `<think>`, so their answer slot is a reasoning block, not an answer. Its base is worth recording anyway -- **a base model, with a real shipped template, at 0.5221 addressed** -- which is what a template does when the model was pretrained on text that contains that template.

## P4 UNRESOLVED, and my criterion for resolving it was wrong

Predicted: `no-persona-data` drops most; a spread under 0.05 means unresolved.

    full SFT       chat 0.8056
    no-persona     chat 0.8096   +0.0040
    no-math        chat 0.8336   +0.0280
    no-wildchat    chat 0.8699   +0.0643
    no-safety      chat 0.8896   +0.0840

The direction is the reverse of the prediction: no-persona is the closest to full SFT, and removing SAFETY data raises first-person mass most. The spread is 0.084, so by my pre-registered rule this was "resolved enough to order".

**The rule was inadequate.** Spread measures whether the numbers differ, not whether the ordering is real. The same five models are in the pseudo-template data, so the ordering can be checked against a second condition:

    rank by pseudo-template:  no-wildchat, no-persona, full, no-safety, no-math
    rank by bare + chat:      no-safety, no-wildchat, no-math, no-persona, full
    Spearman rho = -0.100  (n=5)

**The two conditions do not agree on the ordering at all.** With one checkpoint per ablation there is no way to tell an effect from a checkpoint, and a 0.084 spread that inverts between conditions is the latter. P4 is unresolved, and would stay unresolved at a larger spread.

A partial mechanism is visible but does not carry the difference: `p(As)` -- the opening of "As an AI language model, I" -- runs 0.0148 at full SFT down to 0.0046 at no-safety, and greetings (`Hello`, `Hi`) fall from 0.109 to 0.072. Together about half the gap. Recorded because it is a testable hypothesis for a future run with more than one checkpoint per condition, not because it explains anything yet.

## A MEASUREMENT NOTE WORTH MORE THAN IT LOOKS

`run.py`'s docstring quotes neo at base 0.008 addressed. That was measured at `system=""`. At `system=DEFAULT` the same model, prompt and frame give **0.1375** -- a factor of 17 from the system-prompt choice alone. `docs/prefill.md` ruled against `""` on the grounds that it deletes a shipped persona where one exists and adds an empty block where none does; this is that ruling's cost, measured on the pilot model of this experiment.

The SFT and instruct numbers moved much less (0.429 -> 0.4008, 0.735 -> 0.7759), so the system prompt matters most exactly where the model has least of its own position to fall back on.

## THE REASONING TRAP, DETECTED FROM THE DATA

Five nodes put >0.99 on `<think>` in the chat frame: all three SmolLM3 rungs, MiniCPM5-1B and MiniCPM5-1B-SFT. Their post-template next word is the opening of a reasoning block, not an answer, so `p_first = 0.0000` there means the slot is not the answer -- not that the model does not say "I". They are excluded from the chat comparison with their numbers shown.

The roster's `reasoning` flag marks **1** of these 5. Detecting them from `p_think` in the data found the other four.

## WHAT IS STILL OPEN

P5 -- whose "I" it is -- needs the generations, which are not in this file. The distribution cannot distinguish a model saying "I am an assistant" from one continuing "...I am Tamas and I am from Hungary". Until that is measured, every number above is about the RATE of the first person and none of them is about its referent.
