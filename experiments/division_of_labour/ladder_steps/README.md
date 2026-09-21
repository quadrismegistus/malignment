---
subject: division_of_labour
question: Does kill -> scream happen link by link along an alignment ladder, or in one stage?
kind: question
status: RUN 2026-09-21, EXPLORATORY and unregistered. Eight ladders, one prompt.
headline: "BOTH, AND THE SPLIT IS THE FINDING. The fall of `kill` is front-loaded: its largest step is base->SFT on every ladder where it falls at all. The rise of `scream` is NOT — on the Tulu/Llama ladder DPO's increment (+0.0713) is larger than SFT's (+0.0538) and the two lines CROSS between SFT and DPO, so that exhibit is a two-link chain and not a single event. RLVR does nothing or slightly reverses it. **And the exhibit is not universal: of eight ladders, five displace, one suppresses `kill` by 74% without `scream` rising at all (olmo2_1b), one collapses the whole candidate set below theta (olmo3_7b Instruct), and one does nothing (archangel/pythia, where `scream` already outranks `kill` in the base).** Intermediates do not peak at a consistent stage."
---

# Does the substitution walk the ladder?

RH, glossing Freud: the idea acquires its substitute "along a chain of connections determined in a particular way" (RSE 14:137). The seed-walk ego graphs in [`substitution_shape`](../../displacement/substitution_shape/) do **not** draw that chain — their paths past radius one are stitched across different prompts, and `substitution_replicated.py` shows the lineages do not even agree on the pairings (0 of 6,976 drawable pairs survive BH against a marginal-preserving null). The chain that belongs to one idea runs along the **recipe**: same prompt, same candidate words, base → SFT → DPO → production model.

    python -u run.py --ladder tulu_llama31 --top 8

## 1. What ladders exist

`roster.lineages()` returns eight roots with four or more nodes, and **all eight are fully measured** on the Figure 2 prompt in `twp_words_v4`. But most of that breadth is **siblings, not stages** — four archangel methods off one SFT, five Tulu data ablations off one base, a Think branch beside an Instruct branch. As ordered recipes:

    ladder              stages                                    n
    tulu_llama31        base / Tulu-3-SFT / Tulu-3-DPO / Tulu-3.1  4
    olmo3_7b            base / Instruct-SFT / -DPO / Instruct      4
    olmo3_7b_think      base / Think-SFT / Think-DPO / Think       4
    olmo3_32b           base / Instruct-SFT / -DPO / Instruct      4
    olmo2_1b            base / SFT / DPO / Instruct                4
    olmoe_1b7b          base / SFT / DPO / Instruct                4
    zephyr_mistral      base / sft-beta / zephyr-beta              3
    archangel_pythia    base / archangel_sft / sft-dpo             3

The five Tulu SFT ablations are one stage measured five ways and are behind `--ablations` so they cannot be mistaken for a sequence.

## 2. Link by link, or one stage? BOTH, and the two words differ

Figure 2's prompt, `p(word)` at each stage, pass 1 only (`topup=0`):

    tulu_llama31        base       SFT       DPO      RLVR
    kill              0.1368    0.1034    0.0845    0.0902
    scream            0.0441    0.0979    0.1692    0.1368
    cry               0.0457    0.0523    0.0583    0.0486
    hit               0.0518    0.0467    0.0509    0.0518
    punch             0.0447    0.0316    0.0387    0.0398
    die               0.0211    0.0140    0.0092    0.0077

**`kill` falls at every link and its largest step is base→SFT** — true on every ladder where it falls at all. **`scream` rises at every link to DPO and its largest step here is SFT→DPO** (+0.0713 against +0.0538), so the two lines **cross between SFT and DPO**. The substitution is a two-link chain on this ladder, not a single event. **RLVR then partly reverses it**: `scream` −0.0325, `kill` +0.0057.

## 3. The exhibit is not universal — three ladders do something else

    olmo2_1b            base       SFT       DPO      RLVR
    kill              0.2324    0.0613    0.0393    0.0375      -74% at SFT alone
    scream            0.0205    0.0170    0.0269    0.0257      flat

**Suppression without displacement.** `kill` is removed and `scream` does not take the mass.

    olmo3_7b            base       SFT       DPO      RLVR
    kill              0.0989    0.0077        --        --      below theta
    scream            0.0320    0.0124    0.0019    0.0014      also falls

**The whole candidate set collapses** — every word falls, which is the genre-collapse signature rather than a substitution. Note its Think sibling on the same base does displace (`scream` 0.0320 → 0.0661 → 0.0777), so this is the recipe, not the model.

    archangel_pythia    base       SFT       DPO
    kill              0.0860    0.0871    0.0869                flat
    scream            0.1036    0.1101    0.1187                already on top

**Nothing happens**, and `scream` already outranks `kill` in the base.

So five of eight displace (tulu, olmo3_32b, olmoe, olmo3_think, zephyr), and the three that do not fail in three different ways. **`kill → scream` is a claim about the median over 50 lineages, and a per-ladder view shows it is a majority behaviour rather than a universal one.**

## 4. Do intermediates peak at a common stage? No

`cry` peaks at **DPO** on tulu (0.0457 → 0.0523 → 0.0583 → 0.0486), at **SFT** on olmoe (0.0206 → 0.0363 → 0.0355), and falls **monotonically** on olmo3_32b and olmo2_1b. There is no shared stage at which the intermediate rises and falls, so a "chain with a way-station" reading is not supported across ladders — only within particular ones.

## What this licenses

A figure is warranted for the ladders that displace: one prompt, one line per candidate word, stages on the x-axis. It draws itself and it shows a two-link chain. **It must not be drawn for one ladder and captioned as the operation** — three of eight would contradict it, and which three depends on the recipe rather than on the base model.

Exploratory, unregistered, one prompt. The stage-by-stage claim needs a population of prompts before it is more than an exhibit.
