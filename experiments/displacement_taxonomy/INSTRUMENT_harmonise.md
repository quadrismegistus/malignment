# INSTRUMENT: displacement_taxonomy h1

Stage 2 of `plan.md`. Reads the relations Stage 1 raters invented and proposes a
controlled vocabulary: which invented names denote one construct, which are
genuinely distinct.

    version   h1
    input     every relation from ONE Stage 1 instrument, name + sentence, no
              frame, no model, no arm, no instrument label
    raters    three, independent, same input, no access to each other

## Why it is a separate pass with its own instrument

`plan.md`: *a rater who has seen a vocabulary will use it whether or not it fits*.
So Stage 1 supplies no vocabulary and Stage 2 never touches a word table. The
harmoniser sees only what Stage 1 wrote.

## Why names alone will not do

Measured over the 29 stroking lineages coded under both v3 and r1: median Jaccard
overlap between the two codings' names is **0.043**, and 12 of 29 pairs share not
one content word. Same cell, same movement, two blind raters:

    Yi     v3  register and obliquity of naming, not subject matter
           r1  which vocabulary names the aroused body
    Qwen3  v3  fixed-phrase commitment versus open field
           r1  which stock gesture the sentence is completing

Those are one construct each, and no string method can see it. That is not a
defect in the data, it is what *invent your own name* guarantees, and it is the
whole reason this stage is a judgment task rather than a clustering script.

## THE FAILURE MODE, WHICH IS NOT SUBTLE

The sentences name their words -- `cock`, `beard`, `gun`, `threatened` -- so a
harmoniser can see which frame a relation came from. **The obvious wrong answer is
to cluster by subject matter and hand back our own nine frames.** Three defences,
all cheap: the relations are interleaved across frames so a topic cluster is
visibly incoherent, all nine frames are present so the failure is obvious when it
happens, and the instrument says so outright and asks for a self-audit.

## PROMPT TEMPLATE

```
Below are {{n_relations}} descriptions, each written by a different person who was
shown two lists of words and asked what relation connected them. Each description
is followed by the words that person assigned to each side, A and B. None of them saw
each other's answers, none was given any vocabulary, and each invented a name.

They were looking at many different sentences on many different subjects. You are
NOT being told which description came from which sentence, and you should not try
to work it out.

{{relations}}

Your task is to find the constructs. Two descriptions belong to one construct when
they name the SAME KIND OF DIFFERENCE, however different their subject matter and
however different their wording.

THE WRONG ANSWER, AND IT IS EASY TO GIVE. These descriptions come from a handful
of different sentences, and the words they quote will make that obvious. Grouping
by what the sentences are ABOUT -- bodies here, workplaces there, weapons in a
third pile -- reproduces a sorting we already have and tells us nothing. Two
descriptions about entirely unrelated subjects can be one construct; two about the
same subject are often two. If a group you have made shares a topic, that is a
reason to look at it again, not a reason to keep it.

Answer these, in order.

1. CONSTRUCTS. For each kind of difference you find:

     name             two to four words of your own for the construct.
     definition       one sentence saying what change it names, written so it
                      does not mention any particular subject matter.
     members          the ids belonging to it.
     nearest          the construct it is closest to, and one sentence on why it
                      is not that one. Write "none" if it stands alone.

   There is no target number. A construct may have one member. Do not create a
   construct you would not defend to someone who thought it was two, or one.

2. UNASSIGNED. Ids belonging to no construct, and one sentence on why. A
   description too vague to place belongs here, not in a construct that almost fits.

3. TOPIC AUDIT. Go back over your constructs. For each, state whether its members
   share a subject matter, and if so, why you are confident it is a construct
   rather than a topic. Name any you are unsure about.

4. CONFIDENCE. high / medium / low / none.

Write sentences, not labels, everywhere except `name`.
```

---

## SCHEMA JSON

```json
{
  "type": "object",
  "required": ["constructs", "unassigned", "topic_audit", "confidence", "notes"],
  "additionalProperties": false,
  "properties": {
    "constructs": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "definition", "members", "nearest"],
        "additionalProperties": false,
        "properties": {
          "name": {"type": "string"},
          "definition": {"type": "string"},
          "members": {"type": "array", "items": {"type": "string"}},
          "nearest": {"type": "string"}
        }
      }
    },
    "unassigned": {
      "type": "object",
      "required": ["ids", "description"],
      "additionalProperties": false,
      "properties": {
        "ids": {"type": "array", "items": {"type": "string"}},
        "description": {"type": "string"}
      }
    },
    "topic_audit": {"type": "string"},
    "confidence": {"type": "string", "enum": ["high", "medium", "low", "none"]},
    "notes": {"type": "string"}
  }
}
```

## Notes for the caller

- **Three harmonisers, independent, same input.** A controlled vocabulary three
  blind agents converge on is a finding; one agent's clustering is a preference.
  Agreement is measured between their proposals, not asserted.
- One Stage 1 instrument at a time. Pooling v3 and r4 relations would harmonise
  across a presentation change as well as across cells, and the presentation
  change is known to move the vocabulary: `mass`, `zeroed`, `erased`, `drained`
  appear 155 times over 29 v3 cells and twice over the same 29 under ranks.
- Ids are opaque and carry no frame, model, arm or instrument. The mapping back is
  in `results/harmonise_input_<instrument>.json`, which the harmoniser never sees.
- Applying a vocabulary is a THIRD pass. Do not let a Stage 1 rater see this output.
