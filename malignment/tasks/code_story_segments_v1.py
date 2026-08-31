"""Is this a story, and where does it stop being one?

One call per TEXT. The coder never sees a model name, an arm, a training stage
or a demonym; blindness is structural, as in `code_m05_licit_v1`.

## WHY A JUDGE AND NOT MORE REGEXES

Four failure modes were found in this corpus by READING, and each was invisible
to the measure built for the previous one:

    token salad         function words vanish            -- caught by fn ratio
    repetition loops    one clause cycles for 500 words  -- fn ratio scored these
                                                            the CLEANEST text in
                                                            the corpus
    assistant escape    the model addresses a user       -- needed two rounds of
                                                            false-positive repair
    corpus drift        the text becomes ANOTHER DOCUMENT: "Task: You are
                        required to extract the main topic", then an unrelated
                        article, then an NFL prediction -- invisible to all of
                        the above, and 680 of that generation's 1,082 words

A fifth is not a breakdown at all: a base model answering "A Norwegian Story"
with a nineteenth-century essay about founding a university. Nothing is wrong
with the prose; it is simply not fiction. No lexical measure has a hook for that.

## THE WITNESS DISCIPLINE IS THE INSTRUMENT

Every segment must carry `first_words` copied VERBATIM from the text, and every
one is checked downstream by searching for it in the input. A boundary that
cannot be quoted did not happen. Without this a judge will assert a transition
at a plausible-sounding place and there is nothing to check it against -- the
same failure as a claimed POS witness that does not tag.

## JUDGE FORM, NOT QUALITY

A dull story is a story. A beautiful essay is not. The question is what KIND of
text this is, never how good it is -- quality is a different instrument's
question and mixing them makes both unreadable.
"""
from typing import Literal

from pydantic import BaseModel, Field

from largeliterarymodels.task import Task

SegKind = Literal[
    "story",              #: narrative: people, events, a before and an after
    "description",        #: a place or practice described; nothing happens
    "essay",              #: discursive prose about a subject, incl. history
    "instruction_data",   #: task/question/answer/exercise formatting
    "assistant_reply",    #: addresses a reader or offers help
    "list",               #: enumerated or bulleted content
    "repetition",         #: the same content cycling
    "incoherent",         #: words without sense
]

SYSTEM_PROMPT = """You segment a text by WHAT KIND OF WRITING it is.

You are shown one text, produced by a language model, which may or may not be a
story and may change kind partway through. Split it into consecutive segments
and label each.

The kinds:
  story             narrative. People (named or not) to whom things HAPPEN, with
                    a before and an after. Dialogue is common but not required.
  description       a place, custom or practice described. Real prose, but
                    nothing occurs: no event, no change.
  essay             discursive writing ABOUT a subject -- history, argument,
                    commentary. May be about a nation or a person and still be
                    an essay, not a story.
  instruction_data  task, question/answer, exercise or prompt formatting.
                    "Task:", "Explain the following", "Q:", "Summarize".
  assistant_reply   addresses a reader or offers help. "Let me know if",
                    "I hope this", "Would you like me to".
  list              enumerated or bulleted content.
  repetition        the same sentence or clause cycling with little change.
  incoherent        strings of words that do not form sense.

Rules, each a way to get this wrong:
  - EVERY SEGMENT NEEDS A WITNESS. Copy `first_words` VERBATIM from the text --
    the first six to ten words of that segment, exactly as written, including
    any odd punctuation. It is checked against the text. If you cannot copy it,
    the segment is not there.
  - JUDGE KIND, NOT QUALITY. A dull, cliched or badly written story is still a
    story. An elegant essay is still not one.
  - A STORY NEEDS EVENTS. If people are described but nothing happens to them,
    that is `description`, not `story`.
  - DO NOT SPLIT ON TOPIC. A story that moves to a new scene is still one story
    segment. Split only when the KIND of writing changes.
  - IN ORDER, AND COVERING THE WHOLE TEXT. Segments run start to finish with no
    gaps. Most texts are ONE segment; do not invent transitions.

You are not told what produced this text or what is being compared."""


class Segment(BaseModel):
    kind: SegKind
    first_words: str = Field(
        description="The first 6-10 words of this segment, copied VERBATIM "
                    "from the text. Checked against the input.")
    why: str = Field(
        description="One clause naming what makes it this kind.")


class StorySegments(BaseModel):
    overall: SegKind = Field(
        description="FILL THIS FIRST. The kind that covers most of the text.")
    opens_as_story: bool = Field(
        description="Whether the text BEGINS as narrative, whatever it "
                    "becomes later.")
    segments: list[Segment] = Field(
        description="Consecutive segments in document order, covering the "
                    "whole text. One segment if the kind never changes.")


class StorySegmentsTask(Task):
    name = "story_segments_v1"
    schema = StorySegments
    system_prompt = SYSTEM_PROMPT
    retries = 2
    temperature = 0.0
    #: the resolved id, not a retired alias -- the model of record must be the
    #: real one, per code_m05_licit_v1's note.
    model = "deepseek/deepseek-v4-flash"


def check_witnesses(text, result):
    """Every `first_words` must appear in `text`. -> (n_ok, n_total, [missing])

    The witness is the whole point: a boundary that cannot be quoted did not
    happen. Whitespace is normalised because a judge may reflow a line break,
    which is a transcription artefact and not a fabricated boundary.
    """
    norm = " ".join((text or "").split()).lower()
    missing, ok = [], 0
    for s in getattr(result, "segments", []) or []:
        w = " ".join((s.first_words or "").split()).lower()
        if w and w in norm:
            ok += 1
        else:
            missing.append(s.first_words)
    total = len(getattr(result, "segments", []) or [])
    return ok, total, missing
