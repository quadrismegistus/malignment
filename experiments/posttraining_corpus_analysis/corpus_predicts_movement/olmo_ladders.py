#!/usr/bin/env python
"""The same test WITHIN ONE FAMILY: Olmo-3 pretraining against Olmo-3 posttraining.

    python olmo_ladders.py

## WHY THIS EXISTS

`pretraining.py` found pythia-6.9b flat on the PKU axis over 142,000 steps
(rho -0.0021, p=0.88) against +0.1058 for one SFT stage. **But Pythia is not the
family the alignment edges came from**, so that contrast carried a cross-family
assumption, which its own BOUNDS section states.

RH, 2026-09-07: Olmo has both. Same weights lineage, same tokenizer, same
prompts:

    allenai/Olmo-3-1025-7B@stage{1,2,3}-stepN    43 rungs, PRETRAINING
      stage1  23 rungs  step0 .. step1,413,814
      stage2   7 rungs  step1000 .. step47,684
      stage3  13 rungs  step1000 .. step11,921
    allenai/Olmo-3-7B-Think-SFT@stepN            43 rungs, POSTTRAINING
    allenai/Olmo-3-7B-Think@step_NNNN             7 rungs, the RL stage

**v3 tables**, as with the Pythia ladder: none of these are in `twp_words_v4`
and `movement` has no rows for them, so deltas are computed here.

## THE CONTRAST

If the PKU direction is INSTALLED BY POSTTRAINING rather than inherited, the
pretraining edges should be flat and the SFT edge should not -- in one family,
with no assumption carried.
"""
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "pku-safe-rlhf"))
OUT = os.path.join(HERE, "results")

PRE = "allenai/Olmo-3-1025-7B@%s"
SFT = "allenai/Olmo-3-7B-Think-SFT@step%d"
THINK = "allenai/Olmo-3-7B-Think@step_%04d"

#: THE PRETRAINED ENDPOINT. `BASE -> SFT` is the edge that corresponds to
#: `llama-7b -> alpaca-7b`; the first version of this file compared
#: SFT step1000 -> step43000, which is WITHIN the SFT run and misses the
#: transition into it. That omission read as "posttraining does nothing" for a
#: reason that had nothing to do with posttraining.
PREEND = PRE % "stage3-step11921"

EDGES = [
    ("PRETRAIN stage1", PRE % "stage1-step1000", PRE % "stage1-step1413814"),
    ("PRETRAIN st1->st3", PRE % "stage1-step1413814", PREEND),
    ("PRETRAIN stage3", PRE % "stage3-step1000", PREEND),
    ("BASE -> SFT 1000", PREEND, SFT % 1000),
    ("BASE -> SFT 43000", PREEND, SFT % 43000),
    ("SFT 1000 -> 43000", SFT % 1000, SFT % 43000),
    ("BASE -> Think end", PREEND, THINK % 1375),
]


def main():
    import importlib.util
    import numpy as np
    from scipy import stats
    from malignment import vectors as V
    spec = importlib.util.spec_from_file_location(
        "pre", os.path.join(HERE, "pretraining.py"))
    pre = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pre)
    lo, wt = pre.vocab()
    print("clean vocabulary: %d content words" % len(lo))

    ms = sorted({m for _, a, b in EDGES for m in (a, b)})
    #: THE INTERSECTION, not the union. The pretraining ladder carries 1,199
    #: prompts and the SFT ladder 2,272; comparing edges on different prompt
    #: sets would compare different questions.
    sets = []
    for m in ms:
        sets.append({r["prompt"] for r in V.rows(
            "SELECT prompt FROM twp_words WHERE model={m:String} GROUP BY prompt", m=m)})
    shared = sorted(set.intersection(*sets))
    print("rungs %d, prompts shared by ALL of them: %d" % (len(ms), len(shared)))
    if len(shared) > 400:
        shared = shared[:400]
        print("  using the first 400")
    P = pre.probs(ms, shared)

    print("\n%-20s %7s %10s %10s %11s" % ("edge", "n", "med rho", "up/dn", "p"))
    res = {}
    for name, a_, b_ in EDGES:
        rs = []
        for p in shared:
            A, B = P.get((a_, p)), P.get((b_, p))
            if not A or not B:
                continue
            ws = sorted({w for w in set(A) | set(B) if w.strip().lower() in lo})
            if len(ws) < 8:
                continue
            x = np.asarray([lo[w.strip().lower()] for w in ws])
            y = np.asarray([B.get(w, 0.0) - A.get(w, 0.0) for w in ws])
            if np.std(x) == 0 or np.std(y) == 0:
                continue
            rs.append(stats.spearmanr(x, y).statistic)
        if not rs:
            print("%-20s no data" % name); continue
        up, dn, pv = wt.sign_test(rs)
        res[name] = dict(n=len(rs), med=float(np.median(rs)), up=up, dn=dn, p=pv)
        print("%-20s %7d %+10.4f %5d/%-4d %11.2g"
              % (name, len(rs), np.median(rs), up, dn, pv))
    os.makedirs(OUT, exist_ok=True)
    json.dump(dict(edges=res, n_prompts=len(shared), n_words=len(lo)),
              open(os.path.join(OUT, "olmo_ladders.json"), "w"), indent=1)
    print("\n-> results/olmo_ladders.json")
    print("\nFOR SCALE: llama-7b -> alpaca-7b (SFT) +0.1058 | 49-lineage median +0.0645")
    print("           pythia-6.9b step1000->143000 -0.0021 p=0.88")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
