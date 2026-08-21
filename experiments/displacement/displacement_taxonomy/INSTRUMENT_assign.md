# INSTRUMENT: assign a1

Many-way assignment of a relation to an existing vocabulary, or to none of it.

    version   a1
    unit      one held-out relation against a vocabulary of exemplar sets
    data      cores only
    arms      one per model; the model is part of the key

## Why this instrument decides whether any of this scales

Pairwise merging does not scale. Forty prompts give roughly 250 constructs, so
all-pairs is about 31,000 comparisons, and even name-blocked candidates run to
~750 pairs and thousands of agents. The linear alternative is to stop comparing
and start ASSIGNING: hold the vocabulary as it stands, and ask where a new
construct goes. That is one call per prompt rather than one per pair.

The odd-one-out instrument (`INSTRUMENT_discriminate.md`) validated a three-way
choice with topic held constant, because every relation completed the same
sentence. Assignment is strictly harder on both counts: it is many-way, and the
vocabulary spans prompts, so **topic now varies and becomes available as a
shortcut.** Nothing in the discrimination result licenses assignment, and this
instrument exists because that gap would otherwise be crossed silently.

## The topic shortcut, and how the panel is read for it

A rater can score well by sending a sexual-domain item to a sexual-domain entry
without considering the operation at all. Two features of the design expose it:

- The vocabulary deliberately contains an institutional entry and a sexual entry
  that look like ONE operation (`Blunt word, formal counterpart` and
  `Same-referent register swap`, both same-referent-register-rises). A rater
  working from the operation can cross domains here; a rater working from topic
  cannot.
- `basis` is required on every assignment. An answer justified by what the words
  refer to is a hit obtained the wrong way, and a rate alone cannot see it.

## Both directions again

Some held-out items have their home construct present in the vocabulary; for
others the home construct is withheld entirely and `new` is the correct answer.
Without the second kind, a rater who assigns everything somewhere scores
perfectly, and the whole point of a vocabulary is that it can refuse an item.

## PROMPT TEMPLATE

```
Below is a VOCABULARY of {{n_entries}} entries, then {{n_items}} ITEMS.

Each entry is a group of descriptions that were judged to describe the same kind
of change. Each description was written by someone shown two word lists, A and
B, and asked what relation connected them. The entries have no names, only
letters. The letter means nothing; it is a label.

Every item is one further description of the same sort. For each item, decide
which entry describes the SAME KIND OF CHANGE, or answer `new` if none of them
does.

Two warnings, and the task is built so that ignoring them gives wrong answers.

The descriptions come from several different sentences on different subjects, so
the words differ a lot between entries. DO NOT ASSIGN BY SUBJECT MATTER. Two
descriptions about the same body part can be different kinds of change, and two
about completely different things can be the same kind of change. At least one
pair of entries here concerns quite different subjects and is a candidate for
being the same operation.

`new` is a real answer and some items have no home among these entries. Do not
force an item into the nearest entry. Equally, do not answer `new` merely
because the words look unfamiliar; the question is about the kind of change.

For each item give:

  item        the item's id, copied exactly
  assign      the entry letter, or `new`
  basis       one sentence saying what the change is, in terms that would apply
              equally to a description about some other subject. If your reason
              mentions only what the words refer to, you have answered the wrong
              question.
  confidence  high / medium / low

Answer every item.

VOCABULARY

{{vocabulary}}

ITEMS

{{items}}
```

---

## SCHEMA JSON

```json
{
  "additionalProperties": false,
  "properties": {
    "assignments": {
      "items": {
        "additionalProperties": false,
        "properties": {
          "assign": {
            "type": "string"
          },
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
          "item": {
            "type": "string"
          }
        },
        "required": [
          "item",
          "assign",
          "basis",
          "confidence"
        ],
        "type": "object"
      },
      "type": "array"
    }
  },
  "required": [
    "assignments"
  ],
  "type": "object"
}
```

## Notes for the caller

- Entry letters are assigned from a fixed seed and their order is shuffled, so a
  rater cannot infer the answer from position. The distribution of answers over
  letters is part of the report for the same reason position is in `d1`.
- Names are not shown. The discrimination run found boundaries recoverable
  without them (0.92 stripped against 0.83 named), so the vocabulary is defined
  ostensively and this instrument tests that definition directly.
- Run every model as its own arm. The first stage-2 and stage-3 runs inherited
  claude-opus-5 because no model was named, and a rate measured on one model
  says nothing about another.
