---
subject: surprisal_matrix
question: Does alignment reduce entropy for an external observer, or only from the model's own point of view?
status: |
  RUN, 20 lineage pairs. Both fall and not equally: self H -0.1814 (0/20 up),
  external Q -0.1433, outsider's excess Q-H +0.0392 (19/20, p=4.0e-05). A RETRY
  of F18, run before the seat recognised it as one.
grain: page
---

# surprisal_matrix

**The same text, scored by several observers.** Named for the object rather than
the finding: `private_language` was the alternative and would have baked F18's
conclusion into the folder's identity, so a later retry that weakened it would
leave the directory misnamed by its own title.

    H   the generator's surprisal at its own output      how few options it had
    X   the lineage partner's surprisal at that output   what the other arm pays
    Q   an external reference's surprisal                what an outsider pays

    base output      H(b->b)   X(b->a)   Q(ref->b)
    aligned output   X(a->b)   H(a->a)   Q(ref->a)

## THE QUESTION, WHICH IS RH'S

*"Everyone talks about how alignment reduces entropy, but do they generally mean
entropy from its own POV -- reduces the number of options available to itself?
It seems stranger that it would also reduce entropy for an external observer."*

Two claims routinely run together. **Self-entropy** is a claim about the MODEL:
its next-token distribution gets peakier, fewer options per step. That is what
RLHF-reduces-diversity work measures. **External surprisal** is a claim about the
TEXT, in which the generating model does not appear at all -- and it is what
machine-text detection measures with a proxy model, a literature that mostly does
not talk to the first one.

They are coupled but not identical, and `../jakobson_space/ogden_axes.py` shows
them coming apart in the other direction: Ogden Basic English restricts options
to 850 words -- maximal narrowing -- and RAISES external surprisal on 47 of 47
paired passages. Narrowing your own options does not entail becoming predictable
to anyone else.

## THIS IS A RETRY OF F18, NOT A DISCOVERY

`malign-logits/findings/F18_shannon_entropy.md:73` already found it and named it:

> **Alignment creates private language.** The gap between self-surprisal and
> reference surprisal widens with alignment. Aligned models produce text that is
> increasingly predictable to themselves but not to external observers.

F19 repeats it. F18 sits on `meta/TODO.md`'s never-retried list, and this seat
ran the retry without recognising it as one. What the retry adds:

    F18                          here
    Pythia 1B reference          deepseek-llm-7b-base
    nats and bits-per-char       bits per BYTE throughout
    a handful of families        20 lineage pairs, paired, sign-tested
    a gap quoted per model       +0.0392, 19 of 20, p = 4.0e-05

`../jakobson_space/surprisal_by_passage.py` had already built H and X at the
passage level and says in its own docstring that the reference column was the
missing piece. This supplies it.

## RESULT: BOTH FALL, AND NOT EQUALLY

Median over 20 lineage pairs, bits per byte, narrative-coded f11_l2 passages:

                     H self    X partner   Q deepseek   Q - H
    base output      0.9449      1.0314      1.0292     0.0848
    aligned output   0.7638      0.8279      0.8914     0.1244

    aligned - base            median    up/dn        p
    H  self-surprisal        -0.1814     0/20    1.9e-06
    Q  external              -0.1433     1/19    4.0e-05
    Q - H  outsider's excess +0.0392    19/1     4.0e-05

**Self-entropy falls further than external surprisal does, so the gap widens.**
About 22% of alignment's self-narrowing does not transfer to an outsider: the
model becomes confident in its own output faster than that output becomes
predictable to anyone else. The two claims are not interchangeable, and the
larger of them is the one about the model rather than the text.

**For aligned output the three nest: H < X < Q** (0.764, 0.828, 0.891) -- least
surprised by yourself, then your lineage partner, then a stranger. **For base
output the nesting collapses:** H 0.9449, Q 1.0292, X 1.0314. The aligned model
finds its own base's output as surprising as a stranger does.

## WHY BITS PER BYTE, AND WHY IT IS NOT OPTIONAL

H and X share the lineage's tokenizer -- checked, not assumed: **219,170 of
220,258 f11_l2 passages (99.51%) receive an identical token count from both
scorers**, so the roster's rule that an arm pair shares a tokenizer holds. The
1,088 that disagree are not boundary noise: mean gap 72 to 92 tokens on
256-token passages, confined to the Qwen2.5-0.5B and Olmo-3 lineages, so a
truncation or text-version mismatch. Dropped and counted.

Q is on a THIRD tokenizer. `Q - H` in bits/token would not be a quantity at all.
The byte denominator is what `ref_surprisal.score` stored the `.i32` byte-end
offsets for, and it is the only reason the subtraction is legitimate.

## ONE READING WITHDRAWN

`self_vs_external.py` also reports the off-diagonal in EXCESS form -- each
scorer's cost over the text's own generator, `cross - self`, which prices out the
text's own entropy. Simple narrowing (aligned nested inside base) predicts an
ASYMMETRY there: base output should be costly to the aligned model while aligned
output is cheap to the base.

**Measured, it is null: -0.0304, 12 up / 16 down, p = 0.57**, with the group
medians running the other way (0.335 against 0.567). This seat first glossed that
as supporting nesting, which is backwards -- a null asymmetry is evidence
AGAINST simple nesting. It sits in tension with the collapsed nesting above, and
both are left on the record rather than the flattering one being chosen.

The raw off-diagonal (`cross(b->a) - cross(a->b)`, +1.3721, p = 2.7e-05) is
printed marked CONFOUNDED: base output is higher-entropy text to begin with, so
it costs more to whoever reads it, and that comparison cannot separate the two.
