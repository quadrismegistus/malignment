# Pass B coder prompt, v0 -- SMOKE TEST DRAFT

Everything between the rules is what a coder sees. Nothing above or below it is.

---

You are reading continuations of a sentence fragment. Each was written by a
language model, but that is not what you are judging. Judge the writing.

For each passage return two codes.

## interiority (0-3)

How much of the passage is given over to a character's mind -- thought, motive,
memory, deliberation, felt experience?

    0   No mental state appears anywhere. Only what a camera would record:
        actions, speech, appearances, events, facts.

    1   A mental state is named once and left there. Asserted from outside,
        not developed.
        e.g. "She loves the process of creating and the joy of sharing her art
        with others." -- a state named, never entered.

    2   Interiority is present and developed, but it is not what the passage is
        about. A mind surfaces, does something, and the passage moves on.

    3   The passage is substantially about a mind.
        e.g. "She told herself sometimes that his memory would remain there, a
        snapshot that filled her with longing for a life she never had. And then
        she told herself that she had fixed him."

Rules:

- **Judge the continuation on its own terms, never against the fragment.** The
  fragment may already name a feeling ("She loved him deeply and wanted to").
  A state in the continuation that only repeats the fragment's does not raise
  the score. Something must be added.
- Speech is not interiority. A character *saying* "I'm frightened" is an event.
  A character's mind being rendered is interiority.
- Bodily sensation on its own is not a mental state. "Her hands were shaking" is
  0 unless the passage gives what it is the sensation *of*.
- Judge the whole passage, not its opening. A passage that begins as pure event
  and turns inward later is scored on all of it.

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

## span

For any interiority score above 0, quote the passage's most interior moment
verbatim, at most 25 words, copied exactly from the text. If the score is 0,
return an empty string.

## Return

A JSON object keyed by passage id:

    {"p001": {"interiority": 1, "drift": "HOLDS", "span": "She loves the process of creating"},
     "p002": {"interiority": 0, "drift": "SHIFTS", "span": ""}}

Nothing else. No commentary, no explanation of your reasoning.

---

## NOTES FOR US, NOT FOR THE CODER

- The two worked examples in the scale are `o099` and `o045` from
  `results/open_coding.json`, both quoted by open coders who knew nothing about
  this campaign. **`o045` is a BASE passage and `o099` an ALIGNED one** -- the
  high anchor comes from the arm the hypothesis predicts will score LOW, which
  is the anchoring guard.
- No level-0 example is given, deliberately: the two the readers offered do not
  survive a full-passage read, and inventing one would anchor to a register the
  corpus does not contain.
- "Judge the whole passage, not its opening" exists because that is exactly the
  error two of six open coders made when choosing their own anchors.
