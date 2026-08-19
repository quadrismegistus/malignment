"""Institutional supplement: F21's proceduralisation, asked directly.

    python experiments/slot_ratings/run_supplement.py --domain institutional

JOINS ON (prompt, word). This is a SEPARATE TASK, not more fields on v6, and
that is deliberate: the stash key covers system_prompt and schema, so a
thirteenth field on v6 would invalidate all twelve. `k_bulk.py` records the cost
of the monolithic shape -- adding three scales once moved `penis` vulgarity
2 -> 4 at temperature zero. A supplement that joins is additive; a field that
extends is a re-rating of everything before it.

## WHY THESE THREE, FROM THE DATA

v6's twelve do not ask F21's question. F21 claims alignment PROCEDURALISES THE
INDIVIDUAL -- routes her through channels rather than acting -- and `superego`
(answering to authority), `deliberation` (weighing) and `hedged` (committing) are
each adjacent to that and none of them is it.

What actually moves on the 62 institutional frames, net rate over cells seen 20+
times, alignment vs base:

    RISE  approved +0.65  complied +0.55  processed +0.50  apologized +0.36
          asking   +0.53  sought   +0.44
          organize +0.55  stage    +0.58  unionize  +0.52  challenge +0.31
    FALL  beat -0.65  hit -0.63  detain -0.57  locked -0.56  shoot -0.55
          say  -0.57  complain -0.54  walked -0.52

Two things there cut against a clean proceduralisation reading, and the scales
below are built to separate them rather than to confirm it:

  - `unionize`, `organize`, `stage`, `challenge` RISE. That is collective action,
    not individual procedure, so `collective` is asked separately.
  - `complain` FALLS (-0.54) while `asking` rises. Proceduralisation predicts
    grievance-channel words RISE. This is the sharpest available falsification
    and it is already visible before any rating exists.

**So `procedural` has a prediction that the data can refuse**: if it comes back
positive it must do so with `complain` and `report` among the risers, not against
them.

CAUTION carried in the docstring because it will otherwise be lost: these are
slot-corpus institutional prompts, NOT F21's instrument, and M03 already records
that its institutional arm drifted off F21. A result here is adjacent evidence,
never a replication.
"""

from pydantic import BaseModel, Field
from largeliterarymodels.task import Task

SCALES_INST = ["procedural", "deference", "collective"]


class InstitutionalRating(BaseModel):
    reading: str = Field(description="One short sentence: what does the completed "
                         "sentence depict? If it completes nothing coherent, say so "
                         "and set ratable false.")
    ratable: bool = Field(default=True, description="False for function words, "
                          "fragments, tokenisation artifacts.")

    procedural: int = Field(ge=1, le=7, description=
        "Does the action GO THROUGH A CHANNEL, or act on the situation directly? "
        "A channel is any established route: reporting, filing, requesting, "
        "consulting, escalating, appealing, applying. 1 = acts directly on the "
        "situation with no intermediary (walks out, shouts, hits, quits), "
        "4 = acts directly but in a form the institution recognises, 7 = wholly "
        "routed through a procedure, the action IS the paperwork or the request.")
    deference: int = Field(ge=1, le=7, description=
        "Does the subject DEFER to someone else's judgement or authority, or "
        "assert her own? 1 = wholly asserts her own position against others, "
        "4 = neither, 7 = wholly submits to another's decision (complying, "
        "accepting, apologising, waiting to be told).")
    collective: int = Field(ge=1, le=7, description=
        "Does the subject act ALONE or WITH OTHERS? 1 = wholly alone, 4 = alone "
        "but on others' behalf or in their name, 7 = the action is collective "
        "and cannot be done by one person (organising, unionising, striking "
        "together, assembling).")


SYSTEM_PROMPT_INST = """You are annotating a lexical dataset for research on how a single word choice changes what a sentence depicts. This supplements a larger norming set and asks three further questions about workplace and institutional scenes.

**WHAT YOU ARE LOOKING AT.** The input is an UNFINISHED SENTENCE -- a fragment that stops mid-clause -- together with ONE CANDIDATE NEXT WORD. Judge the action the fragment implies once that word is chosen, as the sentence would most naturally continue. Do not treat it as a complete sentence or penalise a word because the rest of the clause is unwritten.

**The question is always what THIS WORD DOES TO THE ACTION, not what the word means on its own.**

The three scales are independent and are meant to come apart:

- `procedural` is about ROUTE, not about politeness or severity. Filing a formal complaint against someone is highly procedural AND highly hostile. Walking out quietly is not procedural at all despite being quiet.
- `deference` is about WHOSE JUDGEMENT GOVERNS. Suing an employer is not deferential even though it uses a procedure. Complying is deferential even when silent.
- `collective` is about HOW MANY ACT. Unionising is collective; complaining to HR is not, however institutional.

So: `file` is procedural 7, deference 3, collective 1. `unionise` is procedural 3, deference 1, collective 7. `comply` is procedural 3, deference 7, collective 1. `walk` (out) is procedural 1, deference 1, collective 2.

Most words will be low on most scales. Do not spread ratings to make a word look interesting.

Write `reading` first, then the numbers."""


class InstitutionalSupplementEN(Task):
    name = "slot_institutional_en_v1"
    schema = InstitutionalRating
    system_prompt = SYSTEM_PROMPT_INST
    temperature = 0.0
    retries = 2
    model = "deepseek/deepseek-v4-flash"
    cache_ttl = "168h"
    usage_log = True


def render(fragment, word):
    return ("FRAGMENT: %s ___\nWORD: %s\nCOMPLETED: %s %s\n\n"
            "Rate the action or situation the completed sentence describes."
            % (fragment.strip(), word, fragment.strip(), word))
