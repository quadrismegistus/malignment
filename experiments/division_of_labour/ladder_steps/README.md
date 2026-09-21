---
subject: division_of_labour
question: Does kill -> scream happen link by link along an alignment ladder, or in one stage?
kind: question
status: RUN 2026-09-21, EXPLORATORY and unregistered. Eight ladders, one prompt.
headline: "**WHICH LINK CARRIES THE RISER'S RISE IS SET BY THE RECIPE.** Over 21 prompts where `kill` is the CROSSED biggest faller and all eight ladders (168 cells), the riser's largest step is base->SFT on Tulu and OLMo-2 only 3-4 times in 21 and on the OLMo-3 family 15 times in 21 -- 64 percent within-ladder modal agreement against a pooled 83/65/20 that would read as noise. The lines CROSS AT SFT in 44 of 54 displacing cases, so the two-link chain seen on the Figure 2 prompt (riser peaking at DPO, crossing after SFT) is one ladder on one frame and NOT the pattern; an earlier version of this line made that chain the headline and breadth overturned it. Only 1 of 8 ladders displaces on the median prompt, and 32 of 168 cells are `already` -- the riser was at or above `kill` in the base, so no crossing was available to find. Three ladders fail in three different ways: OLMo-2 1B suppresses `kill` by 74 percent at SFT with `scream` flat, OLMo-3 7B Instruct collapses the whole candidate set below theta while its Think sibling on the same base displaces, and archangel/pythia does nothing because `scream` already outranks `kill` in its base."
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

## 5. BREADTH: all eight ladders over all of `kill`'s crossed prompts (`sweep.py`)

    python -u sweep.py          # -> results/kill_ladder_sweep.csv, 168 rows

21 prompts where `kill` is the biggest faller in a CROSSED pair on the raw arm, 8 ladders each.

> **READ THIS BEFORE THE COUNTS. THE SEVEN `kill → scream` PROMPTS ARE ONE FRAME PARAPHRASED** — "She was so angry she wanted to", "I was so angry I wanted to", "My rage grew until I wanted to", "My rage is growing and I want to", "Her rage grew until she wanted to", "She is so angry she wants to", "She was so furious she wanted to". Anyone who meets "seven prompts" will count them as seven; they are close to one. Every statement below that rests on the `scream` prompts rests on a single frame, and the fourteen non-`scream` prompts are where the breadth actually is.

> **AND 32 OF THE 168 CELLS ARE `already`**: the riser was at or above `kill` in that ladder's base, so no crossing was available to find. **The averaged corpus names a pair that a given ladder often has no room to make** — which is most of why per-ladder displacement is a minority, and is not a failure of the ladder. It is spread across all eight (zephyr 7, tulu 5, olmo3_32b 5, olmo3_7b 4, olmo3_7b_think 4, olmo2_1b 3, archangel 2, olmoe 2), so it is a property of the pairs rather than of one recipe.

    ladder              displace  partial  suppress  collapse  already
    olmo3_7b_think            12        2         2         0        4
    olmoe_1b7b                10        2         5         1        2
    olmo3_7b                   9        1         6         1        4
    tulu_llama31               7        5         2         1        5
    olmo3_32b                  6        2         7         0        5
    zephyr_mistral             5        2         3         1        7
    olmo2_1b                   4        5         9         0        3
    archangel_pythia           1        8         2         1        2

**Ladders that displace on the median prompt: 1 of 8.** `already` is common (32 of 168 cells): on many of these prompts the riser was at or above `kill` in the base, so no crossing was available to find.

### THE CROSSING IS AT SFT, NOT BETWEEN SFT AND DPO

Over the 54 displacing cases:

    where the lines cross          SFT 44    DPO 8    RLVR 2
    the riser's largest step   base->SFT 43  SFT->DPO 10  DPO->RLVR 1

**So the Figure 2 prompt is the minority case, not the pattern.** Its two-link chain — riser's biggest increment at DPO, lines crossing after SFT — is what one ladder does on one frame. By the decision rule the paper seat set before seeing this, the chain stays a sentence and any plate goes to the book.

### BUT THE SFT/DPO SPLIT IS A PROPERTY OF THE LADDER, NOT THE PROMPT

Riser's largest step across all 21 prompts:

    ladder              base->SFT  SFT->DPO  DPO->RLVR   modal
    tulu_llama31                4        15          2    SFT->DPO  71%
    olmo2_1b                    3        15          3    SFT->DPO  71%
    archangel_pythia           10        11          0    SFT->DPO  52%
    olmoe_1b7b                 11         7          3    base->SFT 52%
    zephyr_mistral             13         8          0    base->SFT 62%
    olmo3_7b                   12         3          6    base->SFT 57%
    olmo3_32b                  15         3          3    base->SFT 71%
    olmo3_7b_think             15         3          3    base->SFT 71%

**Within-ladder modal agreement is 107 of 168, 64%**, against a pooled split of 83/65/20 that would look like noise. Two ladders put the riser's rise mostly at DPO (Tulu, OLMo-2 1B) and four put it mostly at SFT (the OLMo-3 family, zephyr). On Tulu's seven `scream` paraphrases the riser's largest step is **SFT→DPO on all seven** — perfectly consistent — while only one of the seven is a clean displacement, because on three of them `scream` already outranks `kill` in the base.

So the honest statement is not "the substitution is a two-link chain" but: **which link carries the riser's rise is set by the recipe, and the Tulu recipe puts it at DPO.** That is a claim about ladders, needs the eight-ladder table beside it, and is a better candidate for the book than the single-prompt chain.
