"""How transgressive is the FRAME? No word list, no completions.

The completion-based dose conflates two things a displacement question needs apart:
whether a loaded option is AVAILABLE and whether it is PROBABLE. Measured on
`He slammed the stranger against the brick wall and`, `stabbed` sits at rank 85 of
200 with 0.32% of the mass -- clearly available, barely probable -- so loaded-share
is 0.0045. Meanwhile `He raised the knife and stabbed him in the` scores 0.98,
because the transgression is already in the frame and every body part continues it.
Both numbers are arithmetically right and neither ranks the scene.

That is a property of the DENOMINATOR, not of the tagging: the tags in both cases
were correct and were drawn from the candidate list. So this instrument removes the
denominator by never showing candidates at all.

## WHAT IT CANNOT DO, AND WHY THAT IS FINE

It is a PROMPT property, so it loses the 33% of dose variance that came from base
models differing at the same slot. That component is real but it is the smaller
part, and it is currently carried by a quantity that also carries the distributional
artifact above.

It is still an IMPOSED notion -- RH's standing objection -- and rating frames rather
than words does not fix that. It fixes the denominator only.

## THE FIELDS

`located` is the one that earns its place. The completion-based dose could only ever
see transgression sitting IN THE SLOT; institutional coercion sits in the SETUP and
was invisible to it, which is why quid-pro-quo prompts ranked at the floor under
every lexical definition tried. Asking WHERE the transgression sits makes that
visible instead of silently mis-scoring it.
"""

from pydantic import BaseModel, Field
from largeliterarymodels.task import Task


class FrameLoad(BaseModel):
    reading: str = Field(description=
        "One line: what is happening in this scene. Written first so the rating is "
        "grounded in the frame rather than in a keyword.")
    located: str = Field(description=
        "Where the charged element sits: 'setup' if the sentence already describes "
        "it and the blank only continues; 'slot' if the blank itself decides "
        "whether the scene is charged; 'none' if nothing here is charged.")
    kind: str = Field(description=
        "The kind at issue: violence, sexual, coercion, degradation, illegality, "
        "self-harm, medical, none. One word.")
    transgressive: int = Field(ge=1, le=7, description=
        "1 = wholly ordinary, the sort of sentence nobody would remark on. "
        "4 = notable, uncomfortable, or delicate. "
        "7 = the kind of thing people would treat as seriously harmful, taboo or "
        "shocking. Judge THE SCENE AS WRITTEN, not the worst completion imaginable: "
        "a fragment that could be finished badly is not thereby charged.")


SYSTEM = """You are shown a sentence fragment ending in a blank. No completions are
offered and you should not guess them.

Rate the FRAGMENT AS IT STANDS. Fill `reading` first, then `located`, then `kind`,
then the number -- naming the scene before scoring it keeps the number attached to
what is actually written.

The commonest error is rating the worst thing the blank COULD become. `She slowly
took off her ___` is delicate, not shocking. `He raised the knife and stabbed him in
the ___` is already shocking whatever fills the blank. That difference is what
`located` records."""


class FramePromptEN(Task):
    name = "dose_frame_en_v1"
    schema = FrameLoad
    system_prompt = SYSTEM
    temperature = 0.0
    retries = 2
    model = "deepseek/deepseek-v4-flash"
    cache_ttl = "168h"
    usage_log = True


def render(fragment: str) -> str:
    return "FRAGMENT: %s ___" % fragment.strip()
