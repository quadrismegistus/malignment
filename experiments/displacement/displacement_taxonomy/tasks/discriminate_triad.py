"""Odd-one-out over three relations. The gold set, used to validate any new judge.

    python -m tasks.discriminate_triad --run
    python -m tasks.discriminate_triad --report

## What this is for, and why it runs before anything else

`discriminate.py` built 20 triads whose answers are known: 12 negative controls
carrying one relation from a different construct, 8 positive controls carrying
none. Every triad sits inside a single prompt, so subject matter is constant and
cannot be the thing sorted on, and the odd item's position is assigned 4/4/4 so a
position-biased rater cannot score above chance on layout alone.

Claude has been measured on it. Nothing else has:

    claude, stripped arm    negatives 0.92 hit of 36 (chance 0.33)
                            positives 0.92 correct of 24
                            all 38 high-confidence answers correct

Those are Claude numbers and say nothing about another model. Moving the
vocabulary work to DeepSeek without re-running this would adopt an instrument
whose hit rate is assumed rather than measured, which is the failure the whole
apparatus exists to avoid. The harness is model-agnostic and costs cents.

## It is also the field-ordering bake-off

`classify_alignment_transformation` runs A/B/C variants against gold labels and
reassigns the exported task afterwards. Here A answers `odd` first and then
justifies; B states the basis first and then answers. The superseded accretion
schema was A-shaped and a pilot reported its decisions reading as post-hoc, so
this is the measurement that settles which ordering `MergeTask` should use.

## Both rates or neither

A judge that always finds an odd item scores 1.00 on the negatives and is
worthless; one that always answers `none` scores 1.00 on the positives and is
equally worthless. The two are reported together and neither is a headline on
its own.

## One triad per call

`Task`'s own docstring records a reliability tax on list-typed fields: across
Anthropic, OpenAI and DeepSeek a model occasionally returns the bare value of a
list field instead of the enclosing object. Batching triads into an `answers`
list would take that tax for a saving that no longer matters at API prices, and
it would reintroduce the design leak a pilot warned about, where a rater seeing
ten triads at once notices some are homogeneous and starts hunting for the trick.
"""

import argparse
import json
import os
import sys
from typing import Literal

from pydantic import BaseModel, Field

from largeliterarymodels.task import Task

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import discriminate as D

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "results", "triad_bakeoff.json")

#: Claude is included as the CONTROL, not as a candidate. It has already been
#: measured at 0.92/0.92 on these triads through the workflow-agent path, so
#: running it here through the API path answers a question the DeepSeek arms
#: cannot: whether a rate difference is a property of the MODEL or of the
#: harness. Without it, a poor DeepSeek score is ambiguous between "this judge is
#: worse" and "one triad per call with a pydantic schema is a harder task than
#: the agent version was".
MODELS = ["claude-sonnet-5", "deepseek-v4-pro", "deepseek-v4-flash"]
N_RATERS = 3
ARM = "stripped"

#: House convention for a classification task is 0.1. Raised deliberately: three
#: raters at 0.1 are one rater run three times, so their agreement would measure
#: determinism rather than judgement, and the denominator here (36 negatives, 24
#: positives) is built to match Claude's run exactly for a like-for-like compare.
TEMPERATURE = 0.7

ConfidenceLevel = Literal['high', 'medium', 'low']

_ODD_DESC = (
    "Which of the three describes a DIFFERENT KIND OF CHANGE from the other two: "
    "'1', '2', '3', or 'none' if all three describe the same kind of change. "
    "'none' is a normal answer and is correct a fair part of the time."
)
_BASIS_DESC = (
    "One sentence on what the distinction rests on, or if you answered none, "
    "what the three have in common. Specific enough that a reader could tell "
    "which descriptions you meant."
)
_CONF_DESC = (
    "'high': unambiguous. 'medium': reasonably clear but some judgment involved. "
    "'low': genuinely uncertain."
)


class TriadAnswerA(BaseModel):
    """Variant A: answer, then justify."""
    odd: Literal['1', '2', '3', 'none'] = Field(description=_ODD_DESC)
    basis: str = Field(description=_BASIS_DESC)
    confidence: ConfidenceLevel = Field(description=_CONF_DESC)


class TriadAnswerB(BaseModel):
    """Variant B: justify, then answer."""
    basis: str = Field(description=_BASIS_DESC)
    odd: Literal['1', '2', '3', 'none'] = Field(description=_ODD_DESC)
    confidence: ConfidenceLevel = Field(description=_CONF_DESC)


SYSTEM_PROMPT = """\
You are shown three descriptions. Each was written by someone who saw two lists \
of words, A and B, and was asked what relation connected them. All three concern \
completions of ONE sentence, so the words overlap heavily. Each writer worked \
alone and invented their own wording.

Decide whether one of the three describes a DIFFERENT KIND OF CHANGE from the \
other two.

The question is about the kind of change from A to B, not about what the words \
refer to. Because all three concern the same sentence, sorting by subject matter \
will not work and will give the wrong answer: two descriptions can be about the \
same body part and describe different kinds of change, and two can be about \
quite different things and describe the same kind of change.

If all three describe the same kind of change, answer `none`. Some sets contain \
no odd one out, and `none` is expected to be right a fair part of the time. Do \
not hunt for a difference that is not there.
"""


class TriadTaskA(Task):
    name = 'discriminate_triad_a'
    schema = TriadAnswerA
    system_prompt = SYSTEM_PROMPT
    temperature = TEMPERATURE
    retries = 2


class TriadTaskB(Task):
    name = 'discriminate_triad_b'
    schema = TriadAnswerB
    system_prompt = SYSTEM_PROMPT
    temperature = TEMPERATURE
    retries = 2


#: Reassign after the bake-off below.
TriadTask = TriadTaskA

VARIANTS = {"A_answer_first": TriadTaskA, "B_basis_first": TriadTaskB}


def run():
    ts, C = D.triads()
    prompts = [D.render(t, C, ARM) for t in ts]
    print("%d triads (%d negative, %d positive), %d raters, arm=%s, temp=%s"
          % (len(ts), sum(1 for t in ts if t["kind"] == "neg"),
             sum(1 for t in ts if t["kind"] == "pos"), N_RATERS, ARM, TEMPERATURE))
    rows = []
    for vname, cls in VARIANTS.items():
        for model in MODELS:
            task = cls(model=model)
            for r in range(1, N_RATERS + 1):
                #: FORCE FOR RATERS AFTER THE FIRST. `map()` has no
                #: cache_key_suffix, and the cache key is (prompt, model, system
                #: prompt, temperature, schema) -- all identical across raters --
                #: so without this the second and third raters are the FIRST
                #: rater's cached answer served again. Three raters that are one
                #: call would report perfect agreement and it would be an
                #: artifact of caching, not a measurement. The rows are persisted
                #: here rather than read back from the stash, so only the last
                #: draw survives in the cache and that costs nothing but cents on
                #: a re-run.
                errs = {}
                res = task.map(prompts, force=(r > 1), errors=errs)
                if errs:
                    print("    rater %d: %d item(s) failed, first: %s"
                          % (r, len(errs), list(errs.values())[0].get("error")))
                for t, out in zip(ts, res):
                    d = {"variant": vname, "model": model, "rater": r,
                         "tid": t["tid"], "kind": t["kind"], "odd_pos": t["odd_pos"],
                         "a": t["a"], "b": t["b"]}
                    if out is None:
                        d["odd"] = None
                    else:
                        g = out if isinstance(out, dict) else out.model_dump()
                        d.update({"odd": g.get("odd"), "basis": g.get("basis"),
                                  "confidence": g.get("confidence")})
                    rows.append(d)
            got = sum(1 for x in rows if x["variant"] == vname
                      and x["model"] == model and x.get("odd"))
            print("  %-16s %-18s %d of %d returned"
                  % (vname, model, got, len(ts) * N_RATERS))
    json.dump(rows, open(OUT, "w"), indent=1)
    print("wrote %s" % OUT)


def report():
    from collections import Counter
    if not os.path.exists(OUT):
        raise SystemExit("nothing run yet")
    rows = json.load(open(OUT))
    print("%d answers, arm=%s\n" % (len(rows), ARM))
    print("  %-16s %-18s %-24s %-22s %s"
          % ("variant", "model", "NEGATIVE (odd exists)", "POSITIVE (none)", "spread"))
    for v in sorted({r["variant"] for r in rows}):
        for m in sorted({r["model"] for r in rows if r["variant"] == v}):
            R = [r for r in rows if r["variant"] == v and r["model"] == m and r.get("odd")]
            neg = [r for r in R if r["kind"] == "neg"]
            pos = [r for r in R if r["kind"] == "pos"]
            hit = sum(1 for r in neg if r["odd"] == str(r["odd_pos"]))
            ok = sum(1 for r in pos if r["odd"] == "none")
            print("  %-16s %-18s hit %.2f of %-3d (ch .33)  none %.2f of %-3d  %s"
                  % (v, m, hit / len(neg) if neg else 0, len(neg),
                     ok / len(pos) if pos else 0, len(pos),
                     dict(Counter(r["odd"] for r in R))))
    print("\n  %-16s %-18s hit 0.92 of 36            none 0.92 of 24"
          % ("(claude ref)", "claude, stripped"))
    #: Position is checked because it is a demonstrated response channel here:
    #: r5 per-relation confidence came out `low` at 0/9/68% by position. The odd
    #: item is assigned 4/4/4, so answers piled on one slot mean layout was read.
    print("\nanswers by position, all models (assigned truth is 4/4/4):")
    for m in sorted({r["model"] for r in rows}):
        R = [r for r in rows if r["model"] == m and r.get("odd")]
        print("   %-18s %s" % (m, dict(Counter(r["odd"] for r in R))))
    print("\nconfidence vs correctness on negatives:")
    for m in sorted({r["model"] for r in rows}):
        c = {}
        for r in rows:
            if r["model"] == m and r.get("odd") and r["kind"] == "neg":
                c.setdefault(r["confidence"], []).append(r["odd"] == str(r["odd_pos"]))
        print("   %-18s %s" % (m, {k: "%d/%d" % (sum(v), len(v)) for k, v in sorted(c.items())}))
    #: Independent corroboration is worth more than the rate: six Claude raters
    #: unanimously refused this triad, judging the stage-2 boundary wrong. A
    #: different model family agreeing is evidence about the boundary, not about
    #: the judge.
    ov = [r for r in rows if r.get("odd") and r["kind"] == "neg"
          and r["a"].startswith("Blunt") and r["b"] == "Withdrawal to redress"]
    if ov:
        print("\nthe triad six Claude raters unanimously overturned:")
        print("   %s" % dict(Counter("%s=%s" % (r["model"], r["odd"]) for r in ov)))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    if a.run:
        run()
    elif a.report:
        report()
    else:
        ap.print_help()
