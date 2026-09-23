"""Pick which USAS sense a word carries IN THIS CONTEXT. One call per prompt.

`fields.usas()` returns every sense a word has, undisambiguated, and
`adjacency._spread` then divides the word's moved mass evenly across them. A
third of the coded vocabulary carries more than one fine code -- 2,625 of 7,825
types, 50,638 of 156,475 (prompt, word) observations -- so about a third of all
measured movement is being split between domains the word does not mean here.

The damage is not hypothetical and it is visible in the words: `hit -> see`
files under Religion because a "see" is a bishopric, `hit -> let` under
Business: Selling, and `kill -> express` puts a fifth of a communication verb
into "Measurement: Speed". `--max-freq 500` currently dissolves the worst of
these, but by DROPPING the words rather than by reading them, which is why the
registered channel's significance depends on that filter.

## THE UNIT IS THE PROMPT, AND THE WORD IS A CONTINUATION

50,638 ambiguous pairs sit in 2,389 prompts, median 19 words each and 69 at the
most, so one call per prompt costs a fifth of what the charge annotation already
spent. It also gives the coder the whole slot at once rather than 19 separate
views of it.

**The word does not appear in the prompt.** These are candidate next words, so
the item presents the completed sentence. Asking about the word alone rebuilds
the context-free lookup this exists to replace.

## ABSTENTION IS ALLOWED, AND THAT IS WHAT MAKES IT SAFE

A word may genuinely fit two senses here, or none of the offered ones may fit.
Forcing a single pick manufactures precision the context does not support, so
`codes` may hold one, several, or none of the offered codes. Downstream,
`_spread` divides across whatever comes back and falls back to the full
undisambiguated set when the coder abstains -- so the worst case reproduces
today's behaviour exactly and the run cannot come out worse than its baseline.

## IT IS STRUCTURALLY BLIND

The coder sees a sentence, a candidate word and a list of dictionary senses. It
never sees a model, an arm, a base/aligned label, a charge rating, or which
channel the word belongs to. It cannot know what any answer would support.

## THE ACCEPTANCE TEST, FIXED BEFORE THE RUN

Not "do the numbers improve". The known artifacts must die WITHOUT the frequency
filter: `hit -> see` must leave Religion, and `L1- -> A4.2+` (`kill -> express`)
must fall from p=2.5e-05 toward the p=0.072 that `--max-freq 500` produces, on a
run that drops no words. If the bishopric survives, the pass has not worked and
no headline is recomputed.
"""
from pydantic import BaseModel, Field

from largeliterarymodels.task import Task

SYSTEM_PROMPT = """You are a lexicographer disambiguating word senses.

You are shown a sentence that stops mid-stream, and a list of candidate
words that could each continue it as the very next word. Every candidate
carries two or more dictionary senses. For each candidate, decide which
of its listed senses the word would carry IF it continued THIS sentence.

How to get this right:
  - READ THE SENTENCE FIRST. The same word takes different senses in
    different frames. "He wanted to point" and "She reached the point"
    are different words wearing one spelling.
  - THE WORD IS THE NEXT WORD. Judge the sense it would have there, not
    the sense it has most often in general.
  - GLOSS BEFORE YOU PICK. Write what the word would mean here in a few
    plain words, then choose the sense codes that match your gloss. A
    code you cannot justify from your own gloss is the wrong code.
  - SEVERAL SENSES MAY FIT. If the context genuinely leaves two open,
    return both. Do not invent a distinction the sentence does not make.
  - NONE MAY FIT. If the word would carry a sense that is not in its
    list, return an empty list for it. An honest empty answer is more
    useful than a forced one, and it is treated as "no information",
    never as "no senses".
  - ONLY THE CODES OFFERED. Never return a code that is not in that
    word's own list. Never move a code from one word to another.

You are not told what the sentence is for, what is being compared, or
what any answer would support."""


class WordSense(BaseModel):
    word: str = Field(description="The candidate word, copied exactly as given.")
    gloss: str = Field(
        description="FILL THIS FIRST. What the word would mean if it "
                    "continued this sentence, in a few plain words. No "
                    "sense codes here.")
    codes: list[str] = Field(
        description="The sense codes from THIS WORD'S OWN list that match "
                    "your gloss. One code usually, several if the context "
                    "genuinely leaves them open, and an empty list if none "
                    "of the offered senses fits.")


class SenseChoices(BaseModel):
    position: str = Field(
        description="FILL THIS FIRST. One short phrase naming what the next "
                    "word would be doing in this sentence (e.g. 'the verb of "
                    "an infinitive complement after wanted to').")
    words: list[WordSense] = Field(
        description="One entry per candidate word given, in the order given. "
                    "Do not skip a word; use an empty code list to abstain.")


class USASSenseTask(Task):
    name = "usas_sense_v1"
    schema = SenseChoices
    system_prompt = SYSTEM_PROMPT
    retries = 2
    temperature = 0.0
    #: **THE VERSION CANNOT BE PINNED AND THIS IS NOT THE USUAL CAVEAT.**
    #: `code_m05_licit_v1` pins `deepseek-v4-flash` on the rule that a model of
    #: record must be a resolved id rather than an alias. That id no longer
    #: exists: on 2026-09-16 the endpoint answers `deepseek-v4.1-flash` with
    #: "The supported API model names are deepseek-flash, deepseek-v4-pro", and
    #: `/models` lists exactly those two. The completion's own `model` field
    #: comes back as `deepseek-flash`, unversioned, so the API offers no route
    #: to the version at all -- the rule cannot be followed here, and saying so
    #: is the only honest option. The model of record is "deepseek-flash as
    #: served on 2026-09-16"; a later run may silently be a different model, and
    #: every row carries its own `model` string so the file at least records
    #: what was asked for.
    #:
    #: **NOT the coder that produced the charge ratings**, which ran on
    #: deepseek-v4-flash (`charge_en50_flash.jsonl`) when that id still
    #: resolved. Senses and ratings come from different models, so a
    #: disagreement between them is evidence about neither.
    model = "deepseek/deepseek-flash"


def render(prompt, items):
    """One item: the sentence plus its ambiguous candidates and their senses.

    `items` is [(word, [(code, name), ...]), ...]. The codes are printed WITH
    their tagset names because a bare `Q2.2` is not something to disambiguate
    against, and the name is what makes an abstention meaningful.
    """
    lines = ["SENTENCE (stops mid-stream):", "    %s ___" % prompt.rstrip(), "",
             "CANDIDATE WORDS, each with its dictionary senses:"]
    for w, codes in items:
        lines.append("  %s" % w)
        for c, nm in codes:
            lines.append("      %-10s %s" % (c, nm))
    lines.append("")
    lines.append("For each candidate: gloss the sense it would carry HERE, "
                 "then give the matching codes from that word's own list.")
    return "\n".join(lines)
