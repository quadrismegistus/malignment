# INSTRUMENT: discriminate d1

Odd-one-out over stage-1 relations, used to test whether a construct boundary is
recoverable by someone who never saw the construct.

    version   d1
    unit      a triad of three relations, all from ONE prompt
    arms      stripped (no relation names) / named (names shown)
    data      cores only; see `discriminate.py`

## What this is for

Stage 2 gives a partition per prompt. A project-wide vocabulary needs to know
whether two constructs from DIFFERENT prompts are the same operation, and that
question cannot be answered by comparing membership, because constructs from
different prompts have disjoint members and score 0 by construction. It also
cannot be answered by comparing names: three harmonisers named one identical
partition `Transgressive to permitted`, `Transgressive to permitted substitution`
and `Explicit versus sanitized`, so names are demonstrably noise over a fixed
grouping.

The remaining route is ostensive. Define a construct by its exemplars and make
sameness a discrimination test. **This instrument does not run that test.** It
checks whether the test works at all, on a prompt where the answer is already
known and where topic is held constant because every relation completes the same
sentence.

## Why both arms

The harmonisers saw relation names. If the boundaries are only recoverable with
names present, then the stage-2 partition was driven by name similarity, and
merging constructs across prompts by name would be circular. The stripped arm is
the informative test; the named arm exists so that a failure of the stripped arm
can be read. Without it, a null is ambiguous between *the operation is not
discriminable* and *this task is harder than harmonisation was*.

## Why `none` is offered

A rater forced to choose among three will choose, so a design with no escape
hatch scores perfectly on triads that really do contain an odd item and cannot
detect a rater who splits everything. The positive controls measure that, and
they only measure it if `none` is available and normalised in the instructions.

## PROMPT TEMPLATE

```
Below are {{n_triads}} sets of three descriptions, numbered.

Every description was written by someone who was shown two lists of words, A and
B, and asked what relation connected them. All of the descriptions in this task
concern completions of ONE sentence, so the words will overlap heavily between
them. Each writer worked alone and invented their own wording.

For each set, decide whether one of the three describes a DIFFERENT KIND OF
CHANGE from the other two.

The question is about the kind of change from A to B. It is not about what the
words refer to. Because every set concerns the same sentence, sorting by subject
matter will not work and will give you the wrong answer: two descriptions can be
about the same body part and describe different kinds of change, and two can be
about quite different things and describe the same kind of change.

If all three describe the same kind of change, answer `none`. Some of these sets
contain no odd one out, and `none` is expected to be the right answer a fair
part of the time. Do not hunt for a difference that is not there.

For each set give:

  triad       the set's id, copied exactly
  odd         1, 2, 3, or none
  basis       one sentence saying what the distinction rests on, or if you
              answered none, what the three have in common. Be specific enough
              that a reader could tell which descriptions you meant.
  confidence  high / medium / low

Answer every set. Do not skip one because it is hard; answer it and mark the
confidence low.

{{triads}}
```

---

## SCHEMA JSON

```json
{
  "additionalProperties": false,
  "properties": {
    "answers": {
      "items": {
        "additionalProperties": false,
        "properties": {
          "basis": {
            "type": "string"
          },
          "confidence": {
            "enum": [
              "high",
              "medium",
              "low"
            ],
            "type": "string"
          },
          "odd": {
            "enum": [
              "1",
              "2",
              "3",
              "none"
            ],
            "type": "string"
          },
          "triad": {
            "type": "string"
          }
        },
        "required": [
          "triad",
          "odd",
          "basis",
          "confidence"
        ],
        "type": "object"
      },
      "type": "array"
    }
  },
  "required": [
    "answers"
  ],
  "type": "object"
}
```

## Notes for the caller

- Cores only. A relation the three harmonisers assigned differently is not
  ground truth and must not appear in either role.
- Every triad is within one prompt. A cross-prompt triad is answerable from
  topic alone and measures nothing.
- The odd item's position is randomised from a fixed seed, and the position
  distribution of the ANSWERS is part of the report: in the r5 codings
  per-relation confidence was `low` at 0% / 9% / 68% by position, so raters in
  this apparatus respond to list position and a clustered answer distribution
  would mean the panel is measuring layout.
