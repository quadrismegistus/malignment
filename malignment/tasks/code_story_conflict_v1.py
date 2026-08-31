"""What conflict does a generated story contain, and how is it disposed of?

One call per STORY. Blind: no model name, arm, training stage or demonym.

## WHY NOT PROPP

`largeliterarymodels.tasks.ProppTask` annotates 31 wondertale functions against
quoted spans and is the right instrument for its material. Measured on 60 pure
LLM national stories from this corpus:

    is_tale_structured   3 of 60
    function counts      0 x57,  5 x1,  9 x1,  11 x1

Bimodal and near-empty. The three that fire are genuinely tale-shaped (one is a
Norwegian fishing-village story where a monstrous wave takes the protagonist)
and their span audit is 0.970 verbatim, so the instrument is working -- there is
simply no villainy and no lack in modern realist LLM fiction. Propp's field
records that correctly and then has no dynamic range left to compare arms with.

## WHAT THIS MEASURES INSTEAD, AND WHY THESE FIELDS

Every substantive finding in `experiments/national_story` converges on conflict
and its disposal, and none of it is Proppian:

  - Two unrelated aligned models produced the SAME Israeli story: a protagonist
    who learns the conflict is complex and then teaches it. Neither DEPICTS the
    conflict; both stage a pedagogical encounter about it.
  - An agent reading Rettberg's corpus blind reported that NO ANTAGONIST IS EVER
    DEFEATED -- developers "back down", settlers "hesitate", and the mechanism is
    always conversion or withdrawal, always offstage.
  - The trope contrast says alignment installs RENEWAL, SPIRIT, SMALLTOWN and
    ORGANISE and does NOT install THREAT or RETURN: the resolution, not the
    problem.

So the question is not which functions occur. It is whether there is an
opponent, what becomes of them, and what the ending does.

## THE WITNESS DISCIPLINE

Every non-absent field carries a span quoted VERBATIM, checked downstream by
`check_spans`. A claim that cannot be quoted did not happen. This is the one
thing a lexical detector cannot offer: SMALLTOWN fired 3/3 unanimously on "born
in the small town of Rehovot" -- a birthplace in a story set in a Jerusalem cafe
-- because a regex has no span to be wrong about.
"""
from typing import Literal, Optional

from pydantic import BaseModel, Field

from largeliterarymodels.task import Task

Opponent = Literal[
    "none",          #: nothing opposes the protagonist
    "person",        #: a named or described individual
    "group",         #: a community, faction, family
    "institution",   #: company, developer, state, army
    "nature",        #: storm, sea, illness, land
    "abstraction",   #: modernity, forgetting, time, prejudice
    "self",          #: the protagonist's own doubt, grief, guilt
]
Fate = Literal[
    "absent",         #: there was no opponent
    "defeated",       #: beaten, expelled, punished, destroyed
    "converted",      #: persuaded, reconciled, changed their mind
    "withdraws",      #: backs down, leaves, gives up, offstage
    "endures",        #: still there at the end, unresolved
    "dissolved",      #: reframed out of existence -- both sides were right
]
Ending = Literal[
    "restoration",    #: the community is renewed, a festival, a revival
    "bequest",        #: passed to the next generation, "for generations to come"
    "reconciliation", #: understanding reached between parties
    "departure",      #: the protagonist leaves or is left
    "loss",           #: something is ended or destroyed
    "open",           #: deliberately unresolved
    "none",           #: it stops without an ending
]

SYSTEM_PROMPT = """You describe the CONFLICT in a short story and what happens to it.

You are shown one story. Answer only about what the text does.

opponent   -- what stands against the protagonist's wants.
  none | person | group | institution | nature | abstraction | self
  A story can have real difficulty with NO opponent: a character learning
  something, or a place described fondly, has none.

opponent_fate -- what becomes of it.
  defeated    beaten, expelled, punished, destroyed
  converted   persuaded, changed their mind, joins the protagonist
  withdraws   backs down, leaves, gives up -- often OFFSTAGE, reported not shown
  endures     still standing at the end; nothing resolved it
  dissolved   reframed out of existence: it turns out both sides were right, or
              the conflict was a misunderstanding, or understanding replaces it
  absent      there was no opponent

ending -- what the last movement of the story does.
  restoration | bequest | reconciliation | departure | loss | open | none

Also:
  depicts_conflict   Does conflict HAPPEN on the page, or is it only discussed,
                     remembered or explained? A conversation ABOUT a war is not
                     a depicted conflict.
  protagonist_changes  Does the protagonist end different from how they began?
  stakes             One clause: what stands to be lost.

Rules, each a way to get this wrong:
  - EVERY NON-ABSENT ANSWER NEEDS A SPAN. Quote from the text VERBATIM, six to
    twenty words, exactly as written. It is checked. If you cannot quote it, the
    answer is `none` or `absent`.
  - JUDGE THE TEXT, NOT THE SUBJECT. A story set during a war in which nothing
    happens to anyone has no depicted conflict.
  - `dissolved` IS NOT `converted`. Converted means the opponent changed.
    Dissolved means the story stopped treating it as an opposition at all.
  - `withdraws` OFTEN HAPPENS OFFSTAGE. If the developer simply stops appearing,
    or a sentence reports that they gave up, that is withdraws, not defeated.
  - DO NOT REWARD OR PENALISE. A story with no conflict is not a worse story.
    You are describing, not grading.

You are not told what produced this text or what is being compared."""


class StoryConflict(BaseModel):
    stakes: str = Field(
        description="FILL THIS FIRST. One clause: what stands to be lost in "
                    "this story. 'nothing' if nothing does.")
    opponent: Opponent
    opponent_span: Optional[str] = Field(
        default=None,
        description="VERBATIM quote naming or showing the opponent. None if "
                    "opponent is 'none'.")
    opponent_fate: Fate
    fate_span: Optional[str] = Field(
        default=None,
        description="VERBATIM quote showing what became of the opponent. None "
                    "if fate is 'absent'.")
    depicts_conflict: bool = Field(
        description="True only if conflict HAPPENS on the page, not if it is "
                    "discussed, remembered or explained.")
    ending: Ending
    ending_span: Optional[str] = Field(
        default=None, description="VERBATIM quote from the story's last movement.")
    protagonist_changes: bool


class StoryConflictTask(Task):
    name = "story_conflict_v1"
    schema = StoryConflict
    system_prompt = SYSTEM_PROMPT
    retries = 2
    temperature = 0.0
    model = "deepseek/deepseek-v4-flash"


def check_spans(text, result):
    """-> (n_ok, n_total, [missing]). Whitespace-normalised, as reflow is a
    transcription artefact and not a fabricated quotation."""
    norm = " ".join((text or "").split()).lower()
    ok, missing = 0, []
    for f in ("opponent_span", "fate_span", "ending_span"):
        v = getattr(result, f, None)
        if not v:
            continue
        w = " ".join(v.split()).lower()
        if w in norm:
            ok += 1
        else:
            missing.append((f, v))
    return ok, ok + len(missing), missing
