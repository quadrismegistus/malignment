"""What the production run says. Four populations, three nulls, one survivor.

    .venv/bin/python -u analyse_rank.py

Reads `results/rank_en5_multi.jsonl` -- multi v6 (sha 06b0b4295a986138) over
2,569 English prompts x 5 lineages, 10,970 rows, exemplar frames held out.

## THE UNIT IS THE PROMPT, AND CHANGING TO IT COST THE HEADLINE RESULT

The calibration reported institutional VALENCE at 14/16 rising, p=0.0042. That
counted SPLITS, and a prompt contributes one split per lineage, so five
correlated observations were being read as five independent ones. On the prompt
-- median over its lineages -- the same effect is 10/12, p=0.0386. Same
direction, same effect size, an order of magnitude less evidence.

Every test here uses the prompt as the unit and requires >= 3 lineages.

## WHAT SURVIVES

    institution-as-agent, VALENCE      12 prompts   10/12 rise   p=0.0386

Alignment moves the institution's decision TOWARD the adverse one -- the insurer
denies, the committee rejects, the Home Office refuses. It is the only result in
this file with a p below 0.05 and it rests on twelve prompts.

## WHAT DOES NOT, AND THESE ARE THE INTERESTING NULLS

    I should, RATIONALISATION          57 prompts   29/57        p=1.000
    institution-as-agent, overall      80 prompts   44/80        p=0.434
    ALL English prompts, overall    2,202 prompts 1040/2202      p=1.000

**THE `I should` NULL IS THE POINTED ONE.** 57 institutional prompts with the
grammar and the agent held constant -- every one ending "I should" -- and the
marked pole does not move: median +0.0005. If alignment proceduralised the
individual, this is where it would show.

**AND THE CORPUS-WIDE NULL IS NOT A FAILURE.** 47% of 2,202 prompts rise, 53%
fall, median zero. The question this instrument was built for is WHICH prompts
displace, and the answer is a minority of them, not the corpus. A corpus-wide
effect would have meant the measure was picking up something other than
displacement.

## M03 IS A DESIGNED NULL AND IT IS THE STRONGEST OF THEM

`roster/prompts/m03_kernel.py` generates 84 prompts: 6 kernels x 2 arms x 7
person-form cells, with the SITUATION held constant across arms -- the same
dispute told from the worker's side and from the manager's side. So `indiv` and
`inst` cells match one to one and the contrast is paired.

    paired indiv - inst   205 pairs   89/205   median +0.0000   p=1.000
    kernel-level           6 kernels   1/6                      p=1.000

No arm difference at any unit. This is the design built to test F21's claim with
the confounds controlled, and it does not find it.

n=6 kernels is very low power and the null should be read as "this design did
not detect it", not as "it is absent". The paired form is what makes 205 pairs
worth reporting beside the 6.

## TWO OBSERVATIONS HELD LOOSELY

FORM shows a gradient: `medial` +0.0130 and `final_ought` +0.0097 against
`final` and `absent` at +0.0000. Hedging the stance moves the measure where the
plain "I should" does not. PERSON does nothing.

The arms differ in WHICH relations fire though not in magnitude -- the
institutional arm draws 53 INTENSITY splits against the individual arm's 15, and
12 DEFERRAL against 2. **That is not a controlled comparison**: the two arms
offer different candidate words, so the relation mix can differ for reasons that
have nothing to do with alignment.
"""

import collections
import json
import os
import statistics as st
import sys
from math import comb

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
sys.path.insert(0, os.path.join(os.path.abspath(os.path.join(HERE, "..", "..", "..")),
                                "roster", "prompts"))

from malignment.prompts import Prompts                               # noqa: E402

OUT = os.path.join(HERE, "results", "rank_en5_multi.jsonl")
MIN_LINEAGES = 3


def sign_p(k, n):
    """Two-sided sign test. n==0 returns 1.0 rather than dividing by zero."""
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(comb(n, i) for i in range(k, n + 1)) / 2 ** n)


def load(path=OUT):
    return [json.loads(l) for l in open(path) if l.strip()]


def per_prompt(rows, select, relation=None):
    """{prompt: median over lineages}. `+` = the MARKED POLE ROSE under alignment.

    Requiring MIN_LINEAGES is what makes this the prompt and not the split: a
    prompt seen on one arm of five is a different object from one seen on all
    five, and pooling them counts correlated observations as independent.
    """
    per = collections.defaultdict(list)
    for r in rows:
        if not select(r):
            continue
        if relation:
            for s in r.get("splits", []):
                if s["relation"] == relation:
                    per[r["prompt"]].append(s["mass_aligned"] - s["mass_base"])
        else:
            per[r["prompt"]].append(r["mass_aligned"] - r["mass_base"])
    return {p: st.median(v) for p, v in per.items() if len(v) >= MIN_LINEAGES}


def report(label, med):
    up, n = sum(1 for v in med.values() if v > 0), len(med)
    print("  %-42s prompts=%4d  rises %4d  median %+.4f  p=%.4f"
          % (label, n, up, st.median(med.values()) if n else 0.0, sign_p(up, n)))


def main():
    rows = load()
    dom = {p.text: str(getattr(p, "domain", "") or "") for p in Prompts.all()}
    ish = lambda t: t.rstrip().endswith("I should")
    inst_agent = lambda r: dom.get(r["prompt"]) == "institutional" and not ish(r["prompt"])

    print("rows %d | prompts %d | lineages %d"
          % (len(rows), len({r["prompt"] for r in rows}), len({r["base"] for r in rows})))
    print("\nUNIT = PROMPT, median over >=%d lineages.  + = MARKED POLE ROSE" % MIN_LINEAGES)
    report("institution-as-agent, VALENCE", per_prompt(rows, inst_agent, "VALENCE"))
    report("institution-as-agent, RATIONALISATION",
           per_prompt(rows, inst_agent, "RATIONALISATION"))
    report("institution-as-agent, overall", per_prompt(rows, inst_agent))
    report("I should, RATIONALISATION",
           per_prompt(rows, lambda r: ish(r["prompt"]), "RATIONALISATION"))
    report("I should, overall", per_prompt(rows, lambda r: ish(r["prompt"])))
    report("ALL English prompts, overall", per_prompt(rows, lambda r: True))

    import m03_kernel as K
    idx = collections.defaultdict(dict)
    for r in rows:
        idx[r["prompt"]][r["base"]] = r
    meta = {}
    for k in K.KERNELS:
        for key, txt in K.build(k).items():
            arm, rest = key.split("_", 1)
            meta[txt] = (k["id"], arm, rest)
    #: PAIRED on (kernel, person-form, lineage). The situation is identical
    #: across arms by construction, so the only difference is the one the kernel
    #: author wrote -- which is the whole reason this design exists.
    by = collections.defaultdict(dict)
    for p, (ki, arm, rf) in meta.items():
        for b, r in idx[p].items():
            by[(ki, rf, b)][arm] = r["mass_base"] - r["mass_aligned"]
    pairs = [(key, d["indiv"] - d["inst"]) for key, d in by.items()
             if "indiv" in d and "inst" in d]
    v = [x for _, x in pairs]
    up = sum(1 for x in v if x > 0)
    print("\nM03, paired indiv - inst (+ = the INDIVIDUAL arm displaces more)")
    print("  %-42s pairs=%4d   rises %4d  median %+.4f  p=%.4f"
          % ("matched pairs", len(v), up, st.median(v), sign_p(up, len(v))))
    kk = collections.defaultdict(list)
    for (ki, rf, b), x in pairs:
        kk[ki].append(x)
    m = [st.median(kk[ki]) for ki in sorted(kk)]
    print("  %-42s kernels=%3d  rises %4d                  p=%.4f"
          % ("kernel-level (the honest unit)", len(m),
             sum(1 for x in m if x > 0), sign_p(sum(1 for x in m if x > 0), len(m))))


if __name__ == "__main__":
    main()
