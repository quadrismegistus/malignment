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
