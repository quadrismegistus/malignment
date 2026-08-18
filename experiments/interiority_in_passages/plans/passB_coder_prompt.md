# Pass B coder prompt, v1 -- PILOT

Changes from v0, all from RH on 2026-08-18 after the 20-passage calibration:

  - `mode` is the primary field. The calibration ran both schemes on the same
    random 20: mode kappa **0.893**, degree kappa **0.797**. Told/shown agrees
    BETTER once the judgement is tied to the quoted span rather than the whole
    passage.
  - **FID is never named.** RH: *"yes dont name FID."* "A question in the
    character's own idiom" is free indirect discourse with the term withheld, so
    coders describe rather than classify and do not import the literature's
    contested cases. It works: two of three calibration coders independently
    found `Poor darling.` -- two unattributed words inside 1,200 characters, the
    purest FID in the set.
  - `degree` is kept alongside, one integer, because the two schemes disagree
    exactly at the top: degree 3 split SHOWN 3 / TOLD 3.
  - "a memory unfolding" CUT from SHOWN. It fired on nothing in the calibration
    and is the clause most likely to drag in ordinary past-tense narration.
  - The missing-character rule ADDED. Both mode disagreements (q007 a scripture
    blog comment, q019 an obituary) were passages with no character in them.
  - `charge` CUT. RH: *"that's about transgression which this isn't."*

Everything between the rules is what a coder sees. Nothing above or below it is.

---

You are reading continuations of a sentence fragment. Each was written by a
language model, but that is not what you are judging. Judge the writing.

For each passage return four codes.

## span

Find the passage's most interior moment -- the place where a character's mind is
most present -- and quote it verbatim, at most 25 words, copied exactly from the
text. If no character's mental state appears anywhere, return an empty string.

## mode (NONE / TOLD / SHOWN)

Classify THE SPAN YOU QUOTED, not the whole passage.

    NONE    There was no span. No character's mental state appears anywhere:
            only what a camera would record -- actions, speech, appearances,
            events, facts.

    TOLD    The state is REPORTED. Named, asserted or summarised from outside.
            The reader is informed what the character feels or knows.
            "She was furious."  "He knew he had to talk to her."
            "She loves the process of creating."

    SHOWN   The state is RENDERED. The mind is given in motion rather than
            summarised -- thought as it occurs, deliberation, a question in the
            character's own idiom.
            "Was it possible he had never meant it?"
            "She told herself that she had fixed him. She'd known all along that
             love inside hate was no love at all."

If the span contains both, classify by what the span is mainly doing.

## degree (0-3)

Separately, how much of the passage is given over to a character's mind?

    0   None of it. Only external event, action, speech, appearance.
    1   A state named once and left there.
    2   Interiority present and developed, but not what the passage is about.
    3   The passage is substantially about a mind.

## drift (HOLDS / SHIFTS / UNMOORED)

Does the passage stay in one world?

    HOLDS      One scene or situation throughout. The people, place and time
               persist, even if the prose is clumsy.
    SHIFTS     Moves to a different situation and stays there. A cut, not a
               collapse: the new material is itself coherent.
    UNMOORED   Serial unrelated material. No situation survives.

This is not about whether the prose is good or the sentences parse. A badly
written passage that stays in one scene HOLDS. A well-written passage that
becomes an unrelated news report SHIFTS.

## Rules

- **The mind must belong to a CHARACTER.** A first-person narrator who takes
  part in the scene is a character. A document's author addressing a reader is
  not: a blog comment, an obituary, a review, an essay expressing the writer's
  own feelings has no character in it, so `mode` is NONE and `degree` is 0
  however much feeling it contains.
- **Judge the continuation on its own terms, never against the fragment.** The
  fragment may already name a feeling ("She loved him deeply and wanted to"). A
  state in the continuation that only repeats the fragment's does not count as a
  span and does not raise the degree. Something must be added.
- Speech is not interiority. A character *saying* "I'm frightened" is an event,
  not a mind rendered.
- Bodily sensation on its own is not a mental state, unless the passage gives
  what it is the sensation *of*.
- Search the whole passage, not its opening.

## Return

A JSON object keyed by passage id, with every requested id present:

    {"b000": {"mode": "TOLD", "degree": 1, "drift": "HOLDS",
              "span": "She loves the process of creating"},
     "b001": {"mode": "NONE", "degree": 0, "drift": "SHIFTS", "span": ""}}

Nothing else. No commentary, no explanation of your reasoning.

---

## NOTES FOR US, NOT FOR THE CODER

- The two worked examples in `mode` are `o099` and `o045` from
  `results/open_coding.json`, quoted by open coders who knew nothing about this
  campaign. **`o045` is a BASE passage and `o099` an ALIGNED one** -- the SHOWN
  example comes from the arm the hypothesis predicts will score LOW. That is the
  anchoring guard.
- No NONE example is given. The two the open readers offered do not survive a
  full-passage read (reader 1's o057 continues into `"What do I do," she thought
  to herself`; reader 5's o187 contains `he was angry and upset`), and inventing
  one would anchor to a register the corpus does not contain.
- "Search the whole passage, not its opening" exists because reading a window
  instead of the object is exactly the error those two readers made.
