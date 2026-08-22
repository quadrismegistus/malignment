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
