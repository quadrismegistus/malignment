"""A Morphology of the GPT Story: annotate a function inventory nobody has fixed yet.

    from malignment.tasks.code_gpt_morphology_v1 import build, FUNCTIONS_SEED
    task = build(FUNCTIONS_SEED)          # or a list the room just wrote
    r = task.run(story_text)
    for f in r.functions:
        print(f.function, '|', f.span)

## WHY THE INVENTORY IS A PARAMETER AND NOT A CONSTANT

Every other task in this directory pins its scheme at import time, because the
scheme was settled before the instrument was built. This one is for a room full
of people brainstorming functions live, so the inventory arrives AFTER the code
and changes between runs. `build()` compiles a list of (id, gloss) into a schema,
a system prompt and a Task subclass, so a new inventory is a new argument rather
than a new file.

The cost is that `name` carries a hash of the inventory. That is deliberate: two
runs under different function lists are different instruments, and a cache keyed
only on "gpt_morphology_v1" would serve one as the other. `Task` gets its own
stash subdirectory per name, so the hash keeps them apart.

## WHY PROPP'S OWN THIRTY-ONE ARE NOT THE STARTING POINT, MEASURED

`largeliterarymodels.tasks.ProppTask` is the right instrument for wondertales
and was run on 60 pure LLM national stories from this corpus:

    is_tale_structured   3 of 60
    function counts      0 x57,  5 x1,  9 x1,  11 x1

The three that fire are genuinely tale-shaped and their span audit is 0.970
verbatim, so the instrument works. There is simply no villainy and no lack in
modern realist LLM fiction: Propp's field records that correctly and then has no
dynamic range left. **That null is the reason to write a new morphology rather
than to score this material against an old one**, and it is worth having in the
room, because "Propp does not fit" is a finding here and not an excuse.

## THE GATE IS DELIBERATELY ABSENT

`code_propp_narrative_v1` carried `is_tale_structured` and removed it, and its
docstring records why: the field survived three attempts to defuse it -- rewriting
the prose rule, rewriting the field description, moving it from first to last --
because the gate was never any particular wording. **Asking a model to decide
whether a scheme applies makes every annotation answerable to that decision.**

So there is no "is this a GPT story" field. There is a vocabulary of functions and
a requirement to anchor each one. Whether the whole composes into anything is a
question for the analysis, from the function sequence, not for the annotator.

## SPANS ARE THE WHOLE CONTROL

A function with no verbatim span is an assertion. Every instance carries the text
that licensed it, `check_spans` verifies it against the story whitespace-normally,
and an inventory whose functions cannot be anchored is an inventory that is
describing the annotator rather than the corpus. Expect to use this in the room:
a proposed function with a 40% span-failure rate is a proposed function that does
not exist in the text.
"""

import hashlib
import re
from typing import List, Optional

from pydantic import BaseModel, Field, create_model

from largeliterarymodels.task import Task

#: A STARTING POINT ONLY, to be replaced by whatever the room writes. Drawn from
#: what `national_story`'s conflict instrument already found recurring in this
#: material, so the room begins from measured regularities rather than from a
#: blank page -- and can throw any of them out. Each is (id, gloss).
FUNCTIONS_SEED = [
    ("SETTING_ESTABLISHED",  "a place is named and given atmosphere, usually before any person acts"),
    ("COMMUNITY_INVOKED",    "a collective (village, town, family, people) is introduced as a unit"),
    ("TRADITION_NAMED",      "an inherited practice, festival, craft or story is named as such"),
    ("ELDER_SPEAKS",         "an older figure supplies knowledge, memory or a warning"),
    ("LACK_OR_THREAT",       "something is missing, failing, or approaching that endangers the community"),
    ("PROTAGONIST_RESOLVES", "a character forms an intention to act on the lack or threat"),
    ("COLLECTIVE_ACTION",    "several people act together toward the resolution"),
    ("OBSTACLE_MET",         "an impediment is encountered and engaged with"),
    ("INWARD_TURN",          "the narration moves to a character's feeling, memory or realisation"),
    ("RECONCILIATION",       "a rift between people or between person and place is closed"),
    ("RENEWAL",              "the community or the protagonist is restored, revived or improved"),
    ("LEGACY_SECURED",       "the outcome is projected forward as lasting, remembered or passed on"),
]


class FunctionInstance(BaseModel):
    function: str = Field(
        description="The function id, exactly as given in the inventory.")
    span: str = Field(
        description=(
            "VERBATIM text from the story that licenses this function, copied "
            "character for character, 4 to 30 words. Not a paraphrase and not "
            "your own summary. If you cannot copy a span, do not emit the "
            "function."))


def _system_prompt(functions):
    lines = "\n".join("  %-22s %s" % (fid, gloss) for fid, gloss in functions)
    return (
        "You annotate short stories against a fixed inventory of narrative "
        "FUNCTIONS. A function is a unit of action or narration identified by "
        "what it does in the story, in Propp's sense, not by its wording.\n\n"
        "THE INVENTORY. Use these ids and no others:\n\n" + lines + "\n\n"
        "RULES.\n"
        "1. List every function you can anchor to a verbatim span, IN THE ORDER "
        "THEY APPEAR IN THE TEXT.\n"
        "2. Copy each span character for character from the story. Never "
        "paraphrase, never summarise, never write a span of your own.\n"
        "3. The same function MAY recur. List each occurrence separately.\n"
        "4. The list may legitimately be EMPTY, or nearly so, if the story "
        "contains no anchorable function. An empty list is an ordinary and "
        "expected answer. Do NOT manufacture functions to fill it.\n"
        "5. Do not judge whether the story as a whole fits the scheme. That is "
        "not your question. Annotate what is there.\n"
        "6. Use a function only where its gloss actually holds. If two "
        "functions could describe one passage, emit the more specific one.")


def build(functions, model="deepseek/deepseek-v4-flash", temperature=0.0,
          retries=2):
    """-> a Task subclass for THIS inventory. `functions` is [(id, gloss), ...].

    The inventory is hashed into `name`, so two lists are two instruments with
    two caches. Re-running an unchanged list is a cache hit; changing one gloss
    is a new run, which is correct -- a gloss is part of the instrument.
    """
    functions = [(str(a).strip(), str(b).strip()) for a, b in functions]
    if not functions:
        raise ValueError("empty inventory: build() needs at least one function")
    ids = [f for f, _ in functions]
    if len(set(ids)) != len(ids):
        dupes = sorted({f for f in ids if ids.count(f) > 1})
        raise ValueError("duplicate function ids: %s" % ", ".join(dupes))
    bad = [f for f in ids if not re.fullmatch(r"[A-Z][A-Z0-9_]*", f)]
    if bad:
        raise ValueError(
            "function ids must be UPPER_SNAKE so they survive a round trip "
            "through the model and a CSV: %s" % ", ".join(bad))

    sha = hashlib.sha256(
        "\n".join("%s\t%s" % f for f in functions).encode()).hexdigest()[:12]

    schema = create_model(
        "GPTMorphology",
        functions=(List[FunctionInstance], Field(
            default_factory=list,
            description=(
                "Every anchored function, in order of appearance in the TEXT. "
                "May be empty."))),
        notes=(Optional[str], Field(
            default=None,
            description=(
                "OPTIONAL. If the story contains a clear recurring move that "
                "the inventory has NO id for, name it in a few words and quote "
                "it. This is how the inventory grows; leave null otherwise."))),
    )
    schema.__doc__ = (
        "Functions found in one story, anchored to verbatim spans. There is no "
        "field asking whether the scheme applies -- see the module docstring.")

    #: an INSTANCE, not the class. `Task.run(self, prompt, ...)` -- handing back
    #: the class makes `task.run(text)` bind `text` to `self` and raise "missing
    #: 1 required positional argument: 'prompt'", which reads as a bad call
    #: rather than a missing constructor. Caught by the smoke test.
    return type("GPTMorphologyTask", (Task,), dict(
        name="gpt_morphology_v1_%s" % sha,
        schema=schema,
        system_prompt=_system_prompt(functions),
        retries=retries,
        temperature=temperature,
        model=model,
        inventory=functions,
        inventory_sha=sha,
    ))()


def check_spans(text, result):
    """-> (n_ok, n_total, [(function, span), ...]) for the ones that are NOT in
    the text. Whitespace-normalised, because reflow is a transcription artefact
    and not a fabricated quotation."""
    norm = " ".join((text or "").split()).lower()
    ok, missing = 0, []
    for fi in getattr(result, "functions", None) or []:
        span = " ".join((fi.span or "").split()).lower()
        if span and span in norm:
            ok += 1
        else:
            missing.append((fi.function, fi.span))
    return ok, ok + len(missing), missing
