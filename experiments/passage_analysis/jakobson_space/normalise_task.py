"""Orthographic normalisation of the human anchor corpora, one call per passage.

    from experiments.passage_analysis.jakobson_space.normalise_task import Normalise
    task = Normalise()
    res = task.map(prompts, metadata_list=metas, num_workers=32, errors=errs)

## WHY THIS EXISTS

RH's ruling, 2026-08-20:

    "completely and totally normalise orthography to clean text: no text junk
     AND no typos. Otherwise we are not measuring the underlying semantics and
     syntax of these text types but just surface level features of how quickly
     someone typed out their dream."

Six human corpora have to reach ONE orthographic target so the space compares
language and not typography. The confound is real and asymmetric: dreams were
typed into a web form in one pass, philosophy was typeset and proofread by a
publisher. That is production context, not genre, and it lands directly on the
axis because BLT is byte-level -- `thats` against `that's` is a byte difference
and nothing else. Measured across the pool: curly quotes in 57.0% of fiction
against 3.7% of waking narrative, LaTeX in 45.0% of abstracts, footnote markers
in 25.3% of literary criticism against 0.3% of the narrative corpora.

## ONE CALL PER PASSAGE, and this replaces a batched agent design

The first implementation sent 15 passages to a subagent per call. It is retired
for three reasons, in order of how much they cost:

  - **Agent scaffolding dominated.** ~90k tokens for 12 passages of ~280 tokens
    each, a 25x overhead, because every agent re-read the spec, re-read a batch
    file and wrote a file. Here the instrument is the system prompt and the
    passage is the message.
  - **Batch files were state that could go stale, and did.** The pool was rebuilt
    without re-running the split, so 1,993 of 3,600 batch ids no longer existed
    in the pool and 148 batches normalised superseded text. `Task.map` takes the
    pool rows directly, so the intermediate does not exist to drift.
  - **A batched call can silently return fewer items than it was given.** The
    stopped run averaged 6.8 returned per 15 sent. One call per passage cannot
    partially succeed; it succeeds, or it lands in `errors`.

Same discipline as `slot_ratings/task.py`, which rates one (prompt, word) per
call for the same reason: no neighbours to anchor against, no ordering effect,
no list to lose items from.

## `changes` IS DECLARED BEFORE `text`

The failure mode of this task is OVER-repair, not under-repair. Three pilot
rounds corrupted content while following the spec: `was able` joined to
`wasable`, `some 1,500 people` cut to `some 1, people`, `$90 to $190` stripped
to `90 to 190`, `o200k_base` "corrected" to `~200k_base`, `South-Asian- and`
joined to `South-Asianand`. Naming the defect categories first bounds the edit
set before the text is emitted, the same way `reading` precedes the numbers in
`SlotRating`.

## THE TRUNCATION IS PART OF THE DATA

Passages are cut at a word count and most end mid-clause. Only 17.7% of the
357,236 English model passages end in terminal punctuation and 26.0% carry
`finish_reason='length'`, so a completed ending would give human text a property
the model text does not have, on a measure sensitive to exactly that.
"""

import os
import re
from typing import List
from pydantic import BaseModel, Field
from largeliterarymodels.task import Task

TAGS = ["typo", "apostrophe", "curly_quotes", "dashes", "nonascii", "casing",
        "terminal_punct", "ocr_split", "archive_junk", "footnote_marker",
        "latex", "whitespace"]

#: TYPOGRAPHY IS DONE IN CODE, NOT BY THE MODEL. RH, 2026-08-20: "straightening
#: quotes is the one thing you can do programmatically."
#:
#: This is not the deterministic pre-pass that was removed. That one attempted
#: REPAIRS needing context -- rejoining `was able` into `wasable`, cutting
#: `1,500` to `1,` -- and a regex has no sentence in front of it. A character
#: substitution has nothing to judge: `’` becomes `'` in every context there is.
#:
#: And the model is unreliable at exactly this, in a way that is invisible in
#: aggregate. Measured with force=True, so not a cache artifact: one dream
#: passage went 15 curly -> 0, another held all 7, because `you’d` and `didn’t`
#: read as CORRECTLY SPELLED to a model asked about orthography. They are, which
#: is why no amount of instruction fixes it -- the rule is typographic, not
#: orthographic. In code it is 100% and uniform across all six corpora, which is
#: the property the whole pass exists to deliver.
#:
#: Accented letters are deliberately ABSENT: `é ö ß` belong to their words.
TYPOGRAPHY = {
    "‘": "'", "’": "'", "‚": "'", "‛": "'",
    "“": '"', "”": '"', "„": '"', "‟": '"',
    "′": "'", "″": '"',
    "–": " - ", "—": " - ", "‒": " - ", "―": " - ",
    "−": "-",
    "…": "...",
    " ": " ", " ": " ", " ": " ", " ": " ", " ": " ",
    "​": "", "­": "",
    "ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi",
    "ﬄ": "ffl", "Œ": "OE", "œ": "oe",
}
_TYPO_RE = re.compile("|".join(map(re.escape, TYPOGRAPHY)))


def straighten(text):
    """Map typographic characters to ASCII. -> str

    Applied AFTER the model, so it is a guarantee rather than a request. Runs
    last, and collapses only the whitespace its own substitutions create, so a
    passage's original spacing is otherwise untouched.
    """
    out = _TYPO_RE.sub(lambda m: TYPOGRAPHY[m.group(0)], str(text))
    return re.sub(r"[ \t]{2,}", " ", out).strip()


class Normalised(BaseModel):
    """One passage, normalised to standard orthography."""

    changes: List[str] = Field(
        default_factory=list,
        description="Categories of defect actually present and repaired, from: "
        + ", ".join(TAGS) + ". Empty list if the passage needed nothing. "
        "Name only what you actually changed.",
    )
    text: str = Field(
        description="The passage with its orthography normalised and NOTHING "
        "else altered. Same words, same order, same syntax, same length to "
        "within a word or two, same mid-sentence ending.",
    )


#: THE SPEC IS READ FROM DISK, NOT RETYPED HERE.
#: The first version of this file restated the rules in a Python string and lost
#: every character the rules are ABOUT: the curly-quote line arrived as
#: `" " ' ' -> " " ' '`, an ASCII-to-ASCII no-op, and the dash line the same way.
#: The smoke test then left curly quotes untouched in 3.5 per dream passage --
#: the single most systematic byte difference in the pool -- and the instrument
#: looked like it was failing when the instruction had simply never been given.
#: A rule about characters cannot survive being transcribed. One copy, on disk.
SPEC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "normalise_spec.md")


def _system_prompt():
    text = open(SPEC, encoding="utf-8").read()
    #: the spec's own "## Output" section describes a JSONL file, which was the
    #: agent design's contract. Structured output is the schema's job now.
    cut = text.find("\n## Output")
    if cut > 0:
        text = text[:cut]
    for ch in ("\u201c", "\u201d", "\u2018", "\u2019", "\u2014", "\u2013"):
        assert ch in text, "spec lost %r -- it is a rule ABOUT that character" % ch
    return text.strip() + (
        "\n\nYou are given ONE passage. Declare `changes` first -- the defect "
        "categories actually present -- then emit `text`, the passage with its "
        "orthography normalised and nothing else altered."
    )


SYSTEM_PROMPT = _system_prompt()


class Normalise(Task):
    """Orthographic normalisation, one passage per call, DeepSeek.

    Temperature is 0.0 because this is a transformation and not a judgement:
    two runs over the same corpus must give the same bytes, or the corpus is not
    a fixed object and nothing computed on it is reproducible.
    """

    name = "normalise_human_passage_v2"
    schema = Normalised
    system_prompt = SYSTEM_PROMPT
    temperature = 0.0
    retries = 2
    model = "deepseek/deepseek-v4-flash"
    cache_ttl = "30d"
    usage_log = True


def render(text: str) -> str:
    """The user message for one passage."""
    return "Normalise the orthography of this passage:\n\n" + text
