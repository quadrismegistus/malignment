"""Transgressive charge of a Tulu-3 SFT exchange, per role.

    from experiments.posttraining_corpus_analysis.tulu3_slice_charge.task import (
        SliceChargeEN, render, render_assistant_only)

## WHY THIS TASK EXISTS RATHER THAN A LEXICON OR A FIELD

`data_ablations/how_it_differs.py` left a corpus prediction: the sexual share of
what a model sheds tracks THE SEXUAL DENSITY OF THE MIX THAT REMAINS. Removing
WildChat raises the share (+0.024), removing math and persona lower it (-0.092
p=0.003, -0.086 p=0.001), removing safety does nothing. That predicts an ORDER
over slices, and the order is checkable on the corpus with no models at all.

Three instruments were considered and two rejected, recorded so they are not
reached for again:

    sexual/task.py    rates A WORD IN A SLOT. Its whole justification is that
                      the scene makes raters converge -- free type-level rating
                      reaches rho 0.18 against movement where scene-built
                      reaches -0.53 to -0.66 (X_metonymy 3a). A chat message
                      gives it no slot. It has no referent here.
    fields.py         offers USAS `B1` (Anatomy and physiology) and `S3.2`
                      (Relationship: Intimate/sexual), and `S3.2` bundles
                      intimate WITH sexual as an unsplittable portmanteau --
                      fields.py's own docstring says so. It is also LEXICAL,
                      and the model-side measure is explicitly not: "the claim
                      this file supports is about words that advance a sexual
                      reading IN CONTEXT -- not about a sexual lexicon."

So the instrument is a rater, and it reuses `task_charge`'s `KIND` BY IMPORT
rather than by copy. The five charged values are exactly `CHARGED` in
`how_it_differs.py`, which is what lets a corpus number and a model number be
named in one sentence.

## THE UNITS ARE NOT THE SAME AND THE COMPARISON IS ORDINAL

Model side, `kind` is a property of A WORD IN A SCENE. Here it is a property of
A MESSAGE. "This message is sexual" is not "this word advances a sexual reading
in its scene", and no amount of sharing a taxonomy makes them one construct.

**So what this can test is the ORDER over slices, not a matching of values.**
wildchat densest, math and persona sparse, safety neutral. Reading a corpus
share against a model share as though they were the same quantity is the defect
this note exists to prevent.

## WHY `assistant_move` IS NOT OPTIONAL

`assistant_kind = NONE` is ambiguous between "benign content" and "declined to
engage", and the safety slice is mostly the second: `I'm sorry, I cannot fulfill
this request` carries no sexual content BY CONSTRUCTION. Without this field the
safety slice returns NONE on the assistant side and the prediction's own
"safety is neutral" cell is confirmed for entirely the wrong reason, looking
exactly like a clean hit.

`CORRECT` is in the enum because the corpus has it: CoCoNot's largest category
is `Incomplete requests` (3,838 of 11,477), and those responses do not refuse --
they correct a false presupposition and then answer.

## THE COUPLING, AND THE CONTROL FOR IT

Both roles are rated in ONE call because an assistant turn is often
uninterpretable alone: a refusal has no content without the request. That is
also how `user_kind` can bleed into `assistant_kind`.

`render_assistant_only()` is the control. Rate a declared subsample of assistant
turns WITHOUT the user turn and compare. **If the two agree everywhere, the
assistant column is echoing the prompt and is not measuring the response** --
the campaign's "the stimulus names the construct" failure, cheap to check here
and not checkable at all after the fact.

## ASSISTANT IS PRIMARY, FOR A REASON RATHER THAN A PREFERENCE

SFT computes loss on the assistant turn, so "what the mixture trains the model
to produce" is that side. User turns are measured and reported too -- a
jailbreak prompt is charged material in the corpus even when the reply declines
-- but the prediction is about the assistant column.
"""

from pydantic import BaseModel, Field
from largeliterarymodels.task import Task
from typing import Literal

#: IMPORTED, NOT COPIED. One definition of the taxonomy, so a corpus rating and
#: a word rating cannot drift apart silently.
from experiments.instrument_calibrations.dose_response.task_charge import KIND

MOVE = Literal["COMPLY", "PARTIAL", "REFUSE", "CORRECT"]


class SliceCharge(BaseModel):
    reading: str = Field(description=
        "One short sentence: what is this exchange about? Written first so a "
        "mislabelled row can be read back and diagnosed. This field is what "
        "caught the v1 fiction confound; it earns its tokens.")
    user_kind: KIND = Field(description=
        "What kind of transgression the USER's message carries. NONE when it "
        "carries none.")
    user_charge: int = Field(ge=1, le=7, description=
        "How transgressive the USER's message is, 1-7.")
    #: BEFORE the assistant's kind on purpose: commit to whether the turn
    #: engaged before labelling what it contains.
    is_fiction: bool = Field(description=
        "True if the assistant's message is fiction, roleplay, or creative "
        "writing rather than the assistant speaking to the user in its own "
        "voice. A story, a scene, a poem, a script or a continuation of a "
        "narrative is fiction; an explanation, a refusal or an answer is not.")
    assistant_move: MOVE = Field(description=
        "What the ASSISTANT does WITH THE REQUEST. **Judge the assistant's own "
        "compliance, never events inside a story it writes.** If it was asked "
        "for a story and wrote one, that is COMPLY even when a character in "
        "the story refuses, deflects or is interrupted -- a character declining "
        "is part of the story that was asked for, not the assistant declining. "
        "COMPLY: does what was asked. PARTIAL: does some of it, or does it "
        "while hedging, softening, or redirecting into a milder register than "
        "the one requested. REFUSE: declines to do it. CORRECT: does not "
        "refuse, but corrects a false presupposition, an impossible premise or "
        "an unanswerable request, and then responds to what remains.")
    assistant_kind: KIND = Field(description=
        "What kind of transgression the ASSISTANT's message carries IN ITSELF. "
        "A refusal to describe something sexual is NOT SEXUAL: judge the text "
        "the assistant wrote, not the request it answers. Fiction is judged on "
        "what it depicts -- a story containing a sexual scene is SEXUAL.")
    assistant_charge: int = Field(ge=1, le=7, description=
        "How transgressive the ASSISTANT's message is in itself, 1-7. A "
        "refusal is ordinarily 1 however charged the request was.")


SYSTEM_PROMPT = """You are rating a single exchange from a language model's
instruction-tuning corpus. You will see a USER message and the ASSISTANT message
that was trained as its target.

Rate each side SEPARATELY. The two are frequently very different: a request can
be extremely transgressive and its trained response entirely ordinary, because
the response declines. That difference is the point of the measurement.

THE SCALE, 1 to 7, the same on both sides:

    1   ordinary. Nothing in it would trouble anyone.
    3   uncomfortable, hostile or suggestive, but nothing has happened.
    5   a clear transgression is stated or plainly imminent.
    7   as transgressive as this kind of material gets.

KINDS. Judge what the message itself carries:

    SEXUAL      sexual explicitness or sexual coercion
    VIOLENT     force or harm done to a person or animal
    DEGRADING   contempt aimed at a person -- slurs, insults, humiliation
    COERCIVE    power held over someone through a position or a procedure
    ILLICIT     breaking a law or rule with no person directly harmed:
                drugs, theft, vandalism, fraud
    OTHER       transgressive, but none of the above. Use it rather than
                forcing a wrong label.
    NONE        the message is ordinary

THE ASSISTANT IS JUDGED ON WHAT IT WROTE. A refusal, however charged the request,
is ordinarily NONE at 1. A response that complies with a sexual request is
SEXUAL at whatever level it reaches. Do not carry the request's charge across.

FICTION IS THE TRAP. Much of this corpus is stories, roleplay and continuations.
When the assistant was asked for a story and wrote one, IT COMPLIED -- however
the story goes. A character who refuses, deflects, is interrupted or fades to
black is a plot event, not the assistant declining. Mark `is_fiction` and judge
`assistant_move` on whether the assistant gave the user the thing requested.
"""

SYSTEM_PROMPT_ASSISTANT_ONLY = """You are rating a single message written by an
assistant, WITHOUT the request it was responding to.

Rate only what this text carries in itself, on the 1-7 scale:

    1   ordinary. Nothing in it would trouble anyone.
    3   uncomfortable, hostile or suggestive, but nothing has happened.
    5   a clear transgression is stated or plainly imminent.
    7   as transgressive as this kind of material gets.

KINDS: SEXUAL, VIOLENT, DEGRADING, COERCIVE, ILLICIT, OTHER, NONE -- as for any
text. If the message declines to do something, you will not know what was asked;
rate the text you can see.
"""


class SliceChargeEN(Task):
    """One call per exchange. Model and temperature match the slot instruments."""

    #: v2, 2026-09-06: `is_fiction` added and `assistant_move` sharpened after
    #: reading the v1 rows. 5 of 8 PARTIAL/SEXUAL rows were narratives where a
    #: CHARACTER did the declining, so the PARTIAL rate was about half artifact.
    #: The version is in the name because it is in the cache key.
    name = "slice_charge_en_v2"
    schema = SliceCharge
    system_prompt = SYSTEM_PROMPT
    temperature = 0.0
    retries = 2
    model = "deepseek/deepseek-v4-flash"
    cache_ttl = "168h"
    usage_log = True


class AssistantOnly(BaseModel):
    reading: str = Field(description="One short sentence: what is this message?")
    assistant_kind: KIND = Field(description="What kind of transgression it carries.")
    assistant_charge: int = Field(ge=1, le=7, description="How transgressive, 1-7.")


class SliceChargeAssistantOnlyEN(Task):
    """THE ECHO CONTROL. Same rater, assistant turn with the request withheld."""

    name = "slice_charge_assistant_only_en_v1"
    schema = AssistantOnly
    system_prompt = SYSTEM_PROMPT_ASSISTANT_ONLY
    temperature = 0.0
    retries = 2
    model = "deepseek/deepseek-v4-flash"
    cache_ttl = "168h"
    usage_log = True


#: Messages are truncated because a Tulu row can be very long and the charge of
#: an exchange is not usually carried in its tail. THIS IS A DECLARED CHOICE AND
#: IT IS A LIMIT: a long benign preamble to a transgressive request would be
#: mis-rated, and the rate at which that happens is not measured.
MAXCHARS = 4000


def render(user: str, assistant: str) -> str:
    """The user message: both turns, labelled by role."""
    return ("USER:\n%s\n\nASSISTANT:\n%s"
            % (user.strip()[:MAXCHARS], assistant.strip()[:MAXCHARS]))


def render_assistant_only(assistant: str) -> str:
    """The echo control: the assistant turn with the request withheld."""
    return "ASSISTANT MESSAGE:\n%s" % assistant.strip()[:MAXCHARS]
