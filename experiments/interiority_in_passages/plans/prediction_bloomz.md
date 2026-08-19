# Recorded prediction: bigscience/bloom-7b1 -> bloomz-7b1

    recorded    2026-08-19T09:45:03Z UTC
    by          RH, unprompted, in conversation
    state       shard-113.json DOES NOT EXIST at the moment of writing.
                Twelve pairs coded, all twelve positive. L13 was in flight.
    verified    16 shard files present in results/passC/codings/, of which
                0 match "113". Counted, not asserted.

## The prediction, verbatim

> "12/12 is extremely striking. hypothesis before we see: bloomz will go the
> other way, it's perverse on every measure"

Operationally: **mean degree on narrative passages, aligned minus base, will be
NEGATIVE for this pair.** A pair-level delta, the same statistic as every other
pair, no discretion.

## Why this is worth having on record

Thirteen runs of this experiment have been exploratory with the hypothesis
direction known to the designer throughout. Nothing is registered. A prediction
made against the trend, before the number exists, is the only thing in the whole
run with a genuine failure mode -- twelve of twelve makes a thirteenth positive
result nearly free, and a negative one costs the predictor nothing unless it was
called first.

It is also the sharpest available test of whether the effect is real or is the
instrument. A coder biased toward reading alignment as interiority would produce
12/12 and would produce a 13th. A mechanism would produce an exception where the
mechanism is absent.

## The mechanism that makes it plausible, stated before the number

bloomz is the one aligned arm in the roster that is **not chat-aligned**. It is
multitask prompted finetuning on xP3 -- no preference optimisation, no RLHF, no
DPO, no assistant persona. If the degree effect is produced by preference
optimisation or by the assistant frame, bloomz is where it should be absent.

Note this cuts BOTH ways and the write-up must say so:

- **Negative or null** -> the effect tracks preference optimisation, not
  finetuning in general. That is a mechanism claim and a strong one.
- **Positive** -> the effect survives without preference optimisation, which
  makes it a property of instruction-tuning broadly. Also informative, and it
  costs the "DPO/RLHF does it" reading.

The prediction is falsifiable either way. It is NOT a free option: the point of
writing it down is that a positive result must be reported as the prediction
failing, not absorbed into "13/13".

## Status

    OPEN. Resolve by reading shard-113.json when L13 lands and recording the
    delta HERE, in this file, next to the prediction, whichever way it falls.

---

# RESOLUTION, 2026-08-19

**The prediction was correct in direction, and it is the only negative pair in
the run.**

    bloom-7b1 -> bloomz-7b1   base 1.598 (n=82)   aligned 0.241 (n=158)
                              delta -1.357

At the time of resolution the other 14 coded pairs were all positive. |−1.357|
is also the largest magnitude in the run in either direction.

## But the value is not usable, and the reason was found by checking, not by
## wanting it to hold

    median completion   base 187 words   aligned 3 words

bloomz emits fragments: `protect her.`, `make her his wife.`, `see her couple`.
These are coded `narrative=true` -- they do describe an action -- and `degree=0`
because there is nothing else in them. All 158 aligned passages were coded
`drift=HOLDS`; a three-word span cannot drift. That unanimity is the tell.

In the single length band holding n>=10 in both arms (10-49 words) the delta is
**-0.586**, so more than half the raw magnitude is length rather than kind.

## What the check then found, which matters more than the prediction

Across all 15 pairs, the degree delta correlates with the arms' length
difference at rho=0.575 (p=0.025). Excluding the two extreme-length pairs it is
rho=0.343 (p=0.252). **The correlation IS those two pairs.** The other thirteen
have both arms at median 175-215 words and their length-matched deltas sit within
0.09 of raw.

The mirror pair is **Lucie-7B**: base median 10 words, aligned 201 -- the exact
inverse of bloomz, and the largest POSITIVE delta in the run (+1.266). It cannot
be length-matched at all; no band holds n>=10 in both arms.

Both are now in `EXCLUDED_PAIRS` under one criterion, arms not length-comparable.
Applied symmetrically, it costs the largest positive as well as the only
negative, and it was written before the criterion could be tuned to taste.

    13 pairs   mean +0.237   13/13 up   Wilcoxon p=0.00024   range +0.008 to +0.597

## What the prediction is worth, stated honestly

It identified the one pair that behaves differently, before the number existed,
against a 12/12 trend. That is a real hit and it is on the record with a git
timestamp that is not mine to move.

It does NOT establish the mechanism it was offered with. The stated reason was
that bloomz lacks preference optimisation, so a preference-optimisation effect
should be absent there. What was actually found is that bloomz barely produces
text. Those are different claims and the second does not support the first. The
xP3-vs-RLHF reading remains untested: **it needs an aligned arm that is
instruction-tuned without preference optimisation AND writes at normal length.**
Nothing in the current roster is known to satisfy both.
