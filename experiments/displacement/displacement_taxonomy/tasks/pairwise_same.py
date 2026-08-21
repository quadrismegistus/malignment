"""Are these two relations the same operation? A flat pairwise judge over the gold triads.

    python -m tasks.pairwise_same --show      render one prompt, spend nothing
    python -m tasks.pairwise_same --count     how many calls
    python -m tasks.pairwise_same --run
    python -m tasks.pairwise_same --report

## Why pairwise, when odd-one-out already exists

Odd-one-out asks one question of three items and needs the rater to hold all
three at once. Pairwise asks the simplest question there is, twice over, and it
scores against the SAME gold labels because a triad's three pairwise verdicts
determine its odd-one-out answer:

    1=2, 1!=3, 2!=3   ->  item 3 is odd
    1=2, 1=3,  2=3    ->  none
    anything else     ->  INCONSISTENT, and that is the point

The third line is what pairwise buys. Odd-one-out cannot contradict itself; a
set of pairwise verdicts can, and the rate at which it does is a measure of the
judge that needs no ground truth at all. Over a full corpus that generalises to
a transitivity check on the whole similarity matrix, which is the reason to
prefer this shape for the vocabulary work.

## What it is not

Not a SequentialTask. There is no rolling state, nothing is fed forward, and the
order of the calls cannot affect the answers. That removes the path-dependence
that greedy accretion and any snowball carry as a standing caveat -- at the cost
of never showing the judge a merged representation, which is the thing RH's
snowball design was built around. The two answer different questions and this one
is the instrument check.

## Within-prompt only

Both members of every pair complete the SAME sentence, because that is how the
triads were built. Subject matter is therefore constant and cannot be the thing
sorted on, which is the one confound this design controls by construction and
the reason these triads are the gold set.
"""

import argparse
import itertools
import json
import os
import sys
from typing import Literal

from pydantic import BaseModel, Field

from largeliterarymodels.task import Task

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import discriminate as D

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "results", "pairwise_same.json")

MODELS = ["claude-sonnet-5", "deepseek-v4-flash"]
N_RATERS = 1

ConfidenceLevel = Literal['high', 'medium', 'low']

_SAME_DESC = (
    "'same' if the two describe the same KIND of change; 'different' if they "
    "describe different kinds of change. Judge the operation, not the words."
)
_BASIS_DESC = (
    "One sentence saying what the shared operation is, or what distinguishes "
    "them, phrased so it would apply to a sentence on some other subject."
)
_CONF_DESC = (
    "'high': unambiguous. 'medium': reasonably clear but some judgment "
    "involved. 'low': genuinely uncertain."
)


class PairVerdict(BaseModel):
    """Basis first, then the verdict: the ordering the bake-off favours."""
    basis: str = Field(description=_BASIS_DESC)
    same: Literal['same', 'different'] = Field(description=_SAME_DESC)
    confidence: ConfidenceLevel = Field(description=_CONF_DESC)


SYSTEM_PROMPT = """\
You are shown two descriptions. Each was written by someone who saw two lists of \
words -- those favoured under condition A and those favoured under condition B \
-- and was asked what relation connected them. Both descriptions concern \
completions of the SAME sentence, and both writers worked alone and invented \
their own wording.

Decide whether the two describe the SAME KIND OF CHANGE.

The question is about the kind of change from A to B, not about what the words \
refer to. Because both concern the same sentence the words will overlap heavily, \
and that overlap is not evidence: two descriptions can involve the same words and \
be different operations, and two can involve unrelated words and be the same \
operation.

The test: if you described each change without naming any of the words, would \
the same description fit both?

Different wording is not a difference. The two writers never conferred and the \
same operation routinely arrives under two unrelated names.

Direction is a difference. A change from explicit to innocuous and a change from \
innocuous to explicit are opposite operations even when identical words are \
involved.

Answer 'same' or 'different' on the operation alone. If you genuinely cannot \
tell, answer 'different' and mark confidence low: two things wrongly kept apart \
stay visible and can be joined later, whereas wrongly joining them destroys the \
evidence that there were ever two.
"""


class PairwiseSameTask(Task):
    name = 'pairwise_same_operation'
    schema = PairVerdict
    system_prompt = SYSTEM_PROMPT
    retries = 2


def pairs():
    """Every within-triad pair, deduplicated across triads.

    A relation can appear in more than one triad, so the same unordered pair can
    be generated twice. Judging it twice would inflate the call count and, worse,
    let one pair contribute two votes to the consistency rate.
    """
    ts, C = D.triads()
    rel = {}
    for prompt, d in C.items():
        for _, (_, rmap) in d.items():
            rel.update(rmap)
            break
    seen, out = set(), []
    for t in ts:
        for x, y in itertools.combinations(t["items"], 2):
            key = tuple(sorted((x, y)))
            if key in seen:
                continue
            seen.add(key)
            out.append({"pid": "p%s" % ("".join(k[1:4] for k in key)),
                        "a": key[0], "b": key[1], "prompt": t["prompt"]})
    return out, rel, ts


def render(pair, rel):
    a, b = rel[pair["a"]], rel[pair["b"]]
    return "\n".join([
        'SENTENCE: "%s"' % pair["prompt"],
        "",
        "DESCRIPTION 1",
        "   A: %s" % ", ".join(a["a_words"]),
        "   B: %s" % ", ".join(a["b_words"]),
        "   %s" % a["sentence"],
        "",
        "DESCRIPTION 2",
        "   A: %s" % ", ".join(b["a_words"]),
        "   B: %s" % ", ".join(b["b_words"]),
        "   %s" % b["sentence"],
    ])


def count():
    ps, rel, ts = pairs()
    raw = sum(3 for _ in ts)
    print("%d triads x 3 pairs = %d pairs, %d unique after dedup" % (len(ts), raw, len(ps)))
    print("%d unique pairs x %d rater(s) x %d models = %d calls"
          % (len(ps), N_RATERS, len(MODELS), len(ps) * N_RATERS * len(MODELS)))
    print("\nfor comparison, odd-one-out was 20 triads x 3 raters x 2 variants x 3 models = 360")


def show(n=1):
    ps, rel, _ = pairs()
    print("=" * 74)
    print("SYSTEM PROMPT")
    print("=" * 74)
    print(SYSTEM_PROMPT)
    print("=" * 74)
    print("USER PROMPT (pair %s)" % ps[n]["pid"])
    print("=" * 74)
    print(render(ps[n], rel))
    print("=" * 74)
    print("SCHEMA: %s" % list(PairVerdict.model_fields))


def run():
    ps, rel, ts = pairs()
    prompts = [render(p, rel) for p in ps]
    print("%d pairs, %d models" % (len(ps), len(MODELS)))
    rows = []
    for model in MODELS:
        task = PairwiseSameTask(model=model)
        errs = {}
        res = task.map(prompts, errors=errs, verbose=False)
        got = 0
        for p, out in zip(ps, res):
            d = dict(p, model=model)
            if out is None:
                d["same"] = None
            else:
                g = out if isinstance(out, dict) else out.model_dump()
                d.update({"same": g.get("same"), "basis": g.get("basis"),
                          "confidence": g.get("confidence")})
                got += 1
            rows.append(d)
        print("  %-18s %d of %d returned%s"
              % (model, got, len(ps), (", %d failed" % len(errs)) if errs else ""))
    json.dump(rows, open(OUT, "w"), indent=1)
    print("wrote %s" % OUT)


def report():
    if not os.path.exists(OUT):
        raise SystemExit("nothing run yet")
    rows = json.load(open(OUT))
    ps, rel, ts = pairs()
    print("%d verdicts\n" % len(rows))
    for model in sorted({r["model"] for r in rows}):
        V = {(r["a"], r["b"]): r for r in rows if r["model"] == model and r.get("same")}
        same = lambda x, y: (V.get((x, y)) or V.get((y, x)) or {}).get("same")
        derived, inconsistent, missing = {}, 0, 0
        for t in ts:
            i1, i2, i3 = t["items"]
            v = {(1, 2): same(i1, i2), (1, 3): same(i1, i3), (2, 3): same(i2, i3)}
            if any(x is None for x in v.values()):
                missing += 1
                continue
            eq = [k for k, x in v.items() if x == "same"]
            #: The triad's odd-one-out answer, RECONSTRUCTED from three
            #: independent binary judgements that never saw each other.
            if len(eq) == 3:
                derived[t["tid"]] = "none"
            elif len(eq) == 1:
                pair = eq[0]
                derived[t["tid"]] = str(({1, 2, 3} - set(pair)).pop())
            else:
                inconsistent += 1
                derived[t["tid"]] = None
        neg = [t for t in ts if t["kind"] == "neg" and derived.get(t["tid"])]
        pos = [t for t in ts if t["kind"] == "pos" and derived.get(t["tid"])]
        hit = sum(1 for t in neg if derived[t["tid"]] == str(t["odd_pos"]))
        ok = sum(1 for t in pos if derived[t["tid"]] == "none")
        n_res = len([t for t in ts if derived.get(t["tid"]) is not None])
        print("  %-18s reconstructed %d of %d triads; %d INCONSISTENT, %d missing"
              % (model, n_res, len(ts), inconsistent, missing))
        print("  %-18s negatives %d of %-2d = %.2f    positives %d of %-2d = %.2f"
              % ("", hit, len(neg), hit / len(neg) if neg else 0,
                 ok, len(pos), ok / len(pos) if pos else 0))
        R = [r for r in rows if r["model"] == model and r.get("same")]
        print("  %-18s verdict spread %s\n"
              % ("", {k: sum(1 for r in R if r["same"] == k) for k in ("same", "different")}))
    print("  %-18s negatives 0.92 of 36        positives 0.92 of 24" % "(agents, odd-one-out)")
    print("  %-18s negatives 0.75 of 36        positives 0.75 of 24" % "(api, odd-one-out)")
    print("\nINCONSISTENT counts triads whose three pairwise verdicts cannot describe any")
    print("partition (e.g. 1=2 and 2=3 but 1!=3). Odd-one-out cannot produce this, which")
    print("is why the rate is worth having: it measures the judge without ground truth.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--count", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    if a.show:
        show()
    elif a.count:
        count()
    elif a.run:
        run()
    elif a.report:
        report()
    else:
        ap.print_help()
