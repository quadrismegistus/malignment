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

WHAT TO COMPARE, AND WHAT TO IGNORE.

The entries and candidates come from DIFFERENT sentences. Across sentences the
words are the variable and the operation is the invariant, so the word lists will
not match even when the operation is identical, and matching words are weak
evidence rather than strong. Two changes involving the same words can be
different operations, and two involving no shared words at all can be the same
one. Read the operation statement first and treat the words as illustration.

The question to ask of each pair is: if you described this change without naming
any of the words, would the same description fit both?

DO NOT SPLIT TO BE SAFE, AND DO NOT MERGE TO BE TIDY. These fail in opposite
directions and BOTH are failures.

A vocabulary that collapses everything is worthless: it says only that something
changed. But a vocabulary that refuses every merge is equally worthless, because
it is just the input list rewritten, and it makes the false claim that every
sentence performs its own unique operations. If you keep two entries apart you
are asserting that a reader could reliably tell them apart; if you cannot say
what that difference IS, in terms that do not name the words, then it is not a
difference and they should be merged.

Different wording is not a difference. The entries were named and described by
different people who never conferred, working on different sentences, and the
same operation will routinely arrive under two unrelated names.

The one thing that IS a real difference, and worth checking every time: the
DIRECTION of travel. A change from explicit to innocuous and a change from
innocuous to explicit are opposite operations even when they involve identical
words, and one has already been found folded wrongly into the other.

For each candidate give:

  candidate   the candidate's id, copied exactly
  merge       the entry letter it belongs to, or `new`
  name        if `new`, two to four words naming the kind of change. If merging,
              the name you would give the merged entry, which may be the
              existing name or a better one covering both.
  basis       one sentence saying what the operation is, phrased so it would
              apply to a sentence on some other subject. THIS SENTENCE IS
              CARRIED FORWARD as the entry's definition and is what the next
              reader will compare against, so write it to survive a change of
              subject matter: name what sort of thing is different, not which
              words differ.
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
- An entry carries its `basis`, its constituent names, and its source prompts,
  not only the exemplar word lists. The first accretion run showed the merged
  name and up to three exemplars and NOTHING ELSE, which discarded the one field
  written to survive a change of subject. It refused 36 merges of 40, including a
  pair that three harmonisers and a six-rater discrimination panel had both
  independently treated as one construct.
- Word overlap between entries is NOT supplied and must not be inferred as a
  signal. Measured over the 171 institutional entry pairs from that run, the pair
  known to belong together ranked 60th at a mean Jaccard of 0.024, while the top
  pair at 0.500 was a coincidence of two tiny word sets. Token overlap indexes
  subject matter, which is the confound, so it points the wrong way.
- Uncapping exemplars was considered and is minor: it adds 29% more exemplars and
  cannot help the 37 of 68 entries that rest on a single relation. Thin entries
  are a DATA limit, fixed by more cells per prompt, not by showing more of what
  is not there.
