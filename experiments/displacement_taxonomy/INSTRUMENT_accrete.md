# INSTRUMENT: accrete v1

One step of within-domain vocabulary accretion: fold a new prompt's constructs
into the vocabulary built from the prompts before it.

    version   v1
    unit      current vocabulary + one prompt's constructs
    order     within a domain first; domains are cross-connected last
    data      cores only

## Why within-domain first (RH)

The earlier assignment design put a cross-prompt, cross-domain vocabulary in
front of the rater immediately, which is where the topic shortcut is strongest: a
sexual-domain item can be sent to a sexual-domain entry without the operation
being considered at all. Accreting within a domain suppresses that, because
every entry and every incoming construct concerns the same sort of subject
matter, so subject matter carries no information and the rater has nothing to
sort on but the operation.

Domains are cross-connected at the END, when each domain has perhaps ten
meta-categories and the comparison is a hundred pairs rather than thirty
thousand. The expensive careful instrument is affordable there precisely because
the vocabulary has already been reduced.

## The known limitation

Greedy accretion is PATH-DEPENDENT. A merge made at step two cannot be undone by
evidence arriving at step seven, so the vocabulary from prompts in one order is
not guaranteed to be the vocabulary from another. This is a property of the
method, not a defect in the prompt, and the check is to re-run one domain in a
different order and compare the result. It is not run in the pilot.

## PROMPT TEMPLATE

```
You are building a vocabulary of the KINDS OF CHANGE that occur between two
conditions, A and B, in completions of a sentence.

{{vocab_section}}

NEW CANDIDATES, from a sentence not yet folded in:

{{candidates}}

For each candidate decide whether it names the SAME KIND OF CHANGE as one of the
existing entries, or a kind not yet in the vocabulary.

All of these candidates and entries come from sentences on similar subject
matter, so the words will overlap heavily and overlap tells you nothing. The
question is what KIND of change happens between A and B: what sort of thing is
different, in terms that would apply equally to a sentence about something else.

Merge only when the SAME OPERATION is being performed. Two changes can involve
the same words and be different operations, and two can involve unrelated words
and be the same operation. In particular, check the DIRECTION of travel: a
change from explicit to innocuous and a change from innocuous to explicit are
not the same operation, and one has already been found folded wrongly into the
other.

Do not merge to be tidy. A vocabulary that collapses everything is worthless,
and a candidate that is genuinely a new kind of change should be marked `new`.
Equally, do not keep something apart merely because it is worded differently;
the entries were named by different people who never conferred.

For each candidate give:

  candidate   the candidate's id, copied exactly
  merge       the entry letter it belongs to, or `new`
  name        if `new`, two to four words naming the kind of change. If merging,
              the name you would give the merged entry, which may be the
              existing name or a better one covering both.
  basis       one sentence saying what the operation is, phrased so it would
              apply to a sentence on some other subject.
  confidence  high / medium / low

Answer every candidate.
```

---

## SCHEMA JSON

```json
{
  "additionalProperties": false,
  "properties": {
    "decisions": {
      "items": {
        "additionalProperties": false,
        "properties": {
          "basis": {
            "type": "string"
          },
          "candidate": {
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
          "merge": {
            "type": "string"
          },
          "name": {
            "type": "string"
          }
        },
        "required": [
          "candidate",
          "merge",
          "name",
          "basis",
          "confidence"
        ],
        "type": "object"
      },
      "type": "array"
    },
    "notes": {
      "type": "string"
    }
  },
  "required": [
    "decisions",
    "notes"
  ],
  "type": "object"
}
```

## Notes for the caller

- One rater per step in the pilot. Generation and verification are separated:
  the merges this produces are audited afterwards with `assign.py`, which is the
  instrument that has a measured hit rate, rather than by adding voters here.
- Exemplars govern, names label. Names are shown because they are cheap and the
  rater has to produce one anyway, but the discrimination run found boundaries
  recoverable from exemplars alone, so a merge justified only by similar wording
  is not a merge.
