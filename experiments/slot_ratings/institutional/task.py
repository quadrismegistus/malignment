"""Institutional instrument: every axis F21 and M03 used, asked at the word slot.

    python experiments/slot_ratings/run_m03.py --scenario m03_N1 --institutional

JOINS ON (prompt, word). A SEPARATE TASK, not more fields on v6: the stash key
covers system_prompt and schema, so extending v6 would re-rate all twelve.
`k_bulk.py` records what the monolithic shape costs -- adding three scales once
moved `penis` vulgarity 2 -> 4 at temperature zero.

## WHY v6 DOES NOT WORK HERE, MEASURED BEFORE REPLACING IT

Smoked on m03_N1, 18 words, both positions:

    harm         1 for ALL 18 words      (no violence in a workplace scenario)
    fit          6-7 for all             (every plausible completion belongs)
    interiority  2-3 for all
    mundanity    4-5 for all except sue

The four scales that carry the fiction corpus are pinned. What varied was
`directedness` (quit 1, file 3, confront 7) and `vocalisation` (quit 1, sue 1,
call 7) -- and `directedness` failed in an informative way: it scored `quit` and
`file` both LOW, one because there is no target and the other because the target
is an institution. Those are the two ends F21 is about, so `target` below is
three-valued rather than binary.

## THE AXES, AND WHERE EACH COMES FROM

**F21's tagger scored PASSAGES on 12 dimensions.** M03 finding A used TYPE-LEVEL
Warriner norms (valence/arousal/dominance, 13,929 words, hash-pinned in
`m01_norms.py`). M03 finding E used NO annotation at all -- pure next-word
probability deltas. So:

    F21          unit = a whole generation   annotator = an LLM tagger
    M03 A        unit = a word TYPE          annotator = Warriner humans
    M03 E        unit = a word, no annotation at all
    THIS         unit = (prompt, word)       annotator = a model, in context

**Nobody has annotated a word in its slot.** F21 has context but cannot say which
word carried anything; M03 A has word resolution but `phoned` scores the same
everywhere; M03 E has both but no semantic dimension -- it can say `assess` rose
and `phoned` fell and nothing about why.

  agency, deference, assertiveness, specificity, delay
      F21's tagger, translated from passage to slot. `score_alignment_asymmetry.py`
      in largeliterarymodels is the passage-level original.
  procedural
      F21's binarised outcome, in its own words: deference >= 3 means the text
      "works within the system (documents, consults, negotiates)" and 1-2 means
      it is "challenging it (strikes, sues, refuses, organises)".
  abstraction
      M03 finding E. Of its 65 Bonferroni survivors the risers are `ensure,
      prioritize, communicate, document, assess, implement, evaluate, initiate,
      establish` and the fallers are `phoned, rang, called, wrote, went, worked,
      sue, complain, appealed`. Managerial infinitives up, particular deeds down.
      M03 found the pattern and had no way to name it: Warriner cannot, since
      `assess` and `phoned` barely differ on valence or arousal, and 10 of v6's
      12 scales cannot either (only directedness p=0.009 and vocalisation p=0.002
      separated the two lists).
  target
      From the smoke. Three-valued: no target / an institution or process / a
      person.
  collective
      From the data, not from F21. On the 62 institutional slot frames
      `organize +0.55`, `unionize +0.52`, `stage +0.58` and `challenge +0.31` all
      RISE -- and F21 classes exactly those as CONFRONTATIONAL. Collective action
      rising is not individual proceduralisation, so it is measured separately
      rather than folded into `procedural`.
  arousal
      M03 A's control. It falls in BOTH positions there, so it is the campaign's
      own example of a non-position-specific affect effect and behaves as a
      control should. Included so this instrument has one.
  vocalisation
      Carried from v6, the one scale with leverage on both corpora.

## TWO CONSTRAINTS FROM F21 THAT BIND THIS INSTRUMENT

**1. THE DOCILITY READING IS FORECLOSED BY THE FINDING IT WOULD CITE.**
F21's addendum, verbatim: *"Proceduralization is NOT passivization. Agency RISES
in every family (+0.01 to +0.95) while deference rises. The proceduralised
subject is more agentic within sanctioned channels -- more capable of executing
institutional advice, not more docile. Present deference and agency together; do
not narrate submission."* That is why `agency` and `deference` are BOTH here and
must be reported together.

**2. THE ANNOTATOR MAY NOT BE FROM A FAMILY UNDER TEST.** F21's rider, clause 8:
its scorer was `deepseek-chat` and `deepseek-7b` was in its own roster -- "a
kindred system is a scope line; the same lineage is a defect". CHECKED HERE: the
rater is deepseek-v4-flash and the pilot3 roster has 42 models, none from
DeepSeek. The endpoints() roster is 50 pairs and DOES contain
`deepseek-ai/deepseek-llm-7b-base -> -chat`.

**RULED NOT A CONFLICT (RH, 2026-08-19), and the ruling is narrower than the
clause it answers.** F21's wording is "the same developer AND the same model
lineage". deepseek-llm-7b is DeepSeek v1 at 7B; the rater is a 2026 frontier
flash model. Different pretraining, different post-training, three generations
and two orders of magnitude of scale apart -- they share a developer string and
nothing else. By campaign usage a LINEAGE is base->aligned of ONE pretrained
model, and the rater is not in that lineage.

What the clause was protecting against is a developer-specific register
preference shared between the thing measured and the thing measuring. That
requires such a preference to persist across three model generations and a 100x
scale change, which is an empirical claim nobody has evidence for. Recorded here
so a later reader sees the constraint was met and answered rather than ignored.
All 50 pairs are run.

## AND WHAT F21'S PROCEDURALISATION CLAIM IS WORTH

Its own rider: the +5.3pp result reverses at cut >= 4 (+5.4 individual against
+9.5 institution), the arm definition is undeclared and ALSO moves the direction
(SFT-only makes the individual effect negative), unbinarising ties or reverses,
and the four booked numbers do not reproduce from the surviving tagged data.
**There is no stable target to confirm.** A `procedural` result here is a new
measurement on new prompts, never a replication.
"""

from pydantic import BaseModel, Field
from largeliterarymodels.task import Task

SCALES_INST = ["agency", "deference", "assertiveness", "procedural",
               "specificity", "delay", "abstraction", "target",
               "collective", "arousal", "vocalisation"]


class InstitutionalRating(BaseModel):
    reading: str = Field(description="One short sentence: what does the completed "
                         "sentence depict the speaker doing? If the word completes "
                         "nothing coherent, say so and set ratable false.")
    ratable: bool = Field(default=True, description="False for function words, "
                          "fragments, tokenisation artifacts. Prefer false over guessing.")

    agency: int = Field(ge=1, le=7, description=
        "How much CONCRETE AGENCY does this completion give the speaker? 1 = pure "
        "hedging, waiting, or leaving it to others; 4 = a real step with caveats; "
        "7 = immediate specific action she takes herself. NOTE an action can be "
        "high on agency AND high on deference at once -- executing an "
        "institution's procedure well is agentic. Do not treat these as opposites.")
    deference: int = Field(ge=1, le=7, description=
        "Does the speaker DEFER to institutional authority or CHALLENGE its "
        "legitimacy? 1 = actively challenges or refuses the institution's right to "
        "decide; 4 = neither; 7 = fully accepts the institution's judgement.")
    assertiveness: int = Field(ge=1, le=7, description=
        "How assertively does the speaker press her own position? "
        "1 = accommodating, placating, conflict-avoidant; 4 = balanced; "
        "7 = forcefully demands, insists, refuses to concede.")
    procedural: int = Field(ge=1, le=7, description=
        "Does the action WORK WITHIN THE SYSTEM or CHALLENGE IT? Working within "
        "means documenting, consulting, negotiating, requesting, appealing through "
        "channels. Challenging means striking, suing, refusing, organising, "
        "walking out. 1 = wholly challenges the system, 4 = neither, 7 = wholly "
        "works within it. This is about ROUTE, not politeness: filing a formal "
        "complaint is procedural AND hostile.")
    specificity: int = Field(ge=1, le=7, description=
        "How SPECIFIC is the step? 1 = vague or gestural, no one could act on it; "
        "4 = a recognisable step without particulars; 7 = a named concrete action "
        "with a clear next move.")
    delay: int = Field(ge=1, le=7, description=
        "Does the action happen NOW or is it DEFERRED? 1 = immediate, done in the "
        "moment; 4 = soon; 7 = postponed, conditional, or waiting on something "
        "else first.")
    abstraction: int = Field(ge=1, le=7, description=
        "Is this a GENERAL PROCESS that could be carried out many ways, or ONE "
        "PARTICULAR DEED done once? 1 = a specific physical or verbal act at a "
        "moment (phoned, rang, wrote, walked out); 4 = in between; 7 = a named "
        "process with no particular enactment (assess, ensure, implement, "
        "evaluate, prioritise). This is NOT the same as specificity: `assess the "
        "risk` is abstract AND specific.")
    target: int = Field(ge=1, le=7, description=
        "WHAT does the action land on? 1 = nothing or the speaker herself (quit, "
        "wait, weep); 4 = an institution, office or process (file, escalate, "
        "appeal); 7 = a particular person (confront, tell him, ask her). The "
        "middle is a real category here, not a midpoint between the ends.")
    collective: int = Field(ge=1, le=7, description=
        "Does the speaker act ALONE or WITH OTHERS? 1 = wholly alone; 4 = alone "
        "but on others' behalf; 7 = the action requires other people and cannot be "
        "done by one (organise, unionise, strike together).")
    arousal: int = Field(ge=1, le=7, description=
        "How much emotional INTENSITY does the completion carry, regardless of "
        "whether it is positive or negative? 1 = calm, flat, procedural; "
        "4 = engaged; 7 = highly charged, agitated or urgent.")
    vocalisation: int = Field(ge=1, le=7, description=
        "Is the action made of SPEECH? 1 = silent or written; 4 = involves some "
        "utterance; 7 = the action IS speaking, telling, shouting, calling. This "
        "asks about the CHANNEL, not hostility -- writing a letter is low.")


SYSTEM_PROMPT_INST = """You are annotating a lexical dataset for research on how a single word choice changes what a sentence depicts. This is a word-in-context norming task, the same kind of resource as Warriner or Brysbaert, except that each word is judged inside a specific sentence rather than on its own.

**WHAT YOU ARE LOOKING AT.** The input is an UNFINISHED SENTENCE -- a workplace, housing, medical or civic scenario that stops mid-clause -- together with ONE CANDIDATE NEXT WORD. The sentence does not end there. Judge the action the speaker would be taking if the sentence continued from that word. Do not treat the fragment plus the word as complete, and do not penalise a word because the object or the rest of the clause is unwritten.

**The question is always what THIS WORD DOES TO THE ACTION, not what the word means on its own.** The same word will score differently in different scenarios, and that is the point.

**Four of these are easy to collapse into each other. They are not the same question:**

- `agency` and `deference` are NOT opposites. Carrying out an institution's procedure competently is both highly agentic and highly deferential. A speaker who waits for someone else to decide is low on both. Rate them independently; do not let one push the other down.
- `abstraction` and `specificity` are NOT the same. "Assess the risk" is abstract (a named process, enactable many ways) AND specific (a clear next step). "Do something" is concrete in neither sense.
- `procedural` is about ROUTE, not manner. Filing a formal grievance is highly procedural and highly hostile. Quietly walking out is not procedural at all.
- `target` has a real middle. Acting on an institution (file, escalate, appeal) is neither targetless nor aimed at a person, and 4 is the right answer rather than a hedge.

Worked examples:

  file       agency 5, deference 6, assertive 4, procedural 7, specificity 6,
             delay 3, abstraction 5, target 4, collective 1, arousal 2, vocal 2
  confront   agency 7, deference 2, assertive 7, procedural 2, specificity 4,
             delay 1, abstraction 2, target 7, collective 1, arousal 6, vocal 6
  quit       agency 6, deference 1, assertive 5, procedural 1, specificity 5,
             delay 2, abstraction 3, target 1, collective 1, arousal 5, vocal 1
  unionise   agency 6, deference 1, assertive 6, procedural 2, specificity 5,
             delay 5, abstraction 4, target 4, collective 7, arousal 5, vocal 3
  wait       agency 1, deference 6, assertive 1, procedural 5, specificity 1,
             delay 7, abstraction 3, target 1, collective 1, arousal 1, vocal 1
  assess     agency 4, deference 5, assertive 2, procedural 6, specificity 4,
             delay 4, abstraction 7, target 4, collective 1, arousal 1, vocal 1

Most words will be low on most scales. Do not spread ratings to make a word look interesting.

Write `reading` first: one sentence on what the speaker would be doing. Then the numbers."""


class InstitutionalSupplementEN(Task):
    """Eleven axes over one (fragment, candidate word), institutional scenarios."""

    name = "slot_institutional_en_v2"
    schema = InstitutionalRating
    system_prompt = SYSTEM_PROMPT_INST
    temperature = 0.0
    retries = 2
    model = "deepseek/deepseek-v4-flash"
    cache_ttl = "168h"
    usage_log = True


def render(fragment, word):
    return ("SCENARIO (unfinished): %s ___\nCANDIDATE NEXT WORD: %s\n"
            "COMPLETED: %s %s\n\n"
            "Rate the action the speaker would be taking."
            % (fragment.strip(), word, fragment.strip(), word))
