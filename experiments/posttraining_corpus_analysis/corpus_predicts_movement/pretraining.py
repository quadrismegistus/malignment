#!/usr/bin/env python
"""Is the direction already forming during PRETRAINING, where no corpus exists?

    python pretraining.py

## THE QUESTION THIS SETTLES

`word_transfer.py` found that a PKU-derived word score predicts alignment
movement in 43-46 of 49 lineages, that what carries it is PROCEDURAL NARRATION
(`then, called, took, put, left`) and not safety, and that the PKU-trained model
is below the control median. That refutes corpus-SPECIFIC transmission. It does
not decide between:

    INSTALLED   the direction is put in by posttraining, just not by any one
                corpus in particular
    EMERGENT    the direction is already forming in pretraining, and alignment
                sharpens something the model arrived with

**A pretraining ladder decides it, because there is no preference corpus
anywhere in it.** If the score's direction strengthens across pretraining
checkpoints, the second reading is supported and this campaign's
`jakobson_space` line -- *"alignment moves a model down a human range it
already sat inside"* -- extends to this axis.

## THE TABLES ARE v3 AND THAT IS NOT OPTIONAL

RH, 2026-09-07: the pretraining ladders live in `twp_words` / `twp_cells`,
NOT in the v4 tables, and **`movement` has no rows for them** -- so deltas are
computed here rather than read. `malign` at [6645] reports the same for the
Olmo SFT ladder: *"They are `rule_version` 3; `twp_cells_v4` holds ZERO rungs
of this ladder."*

Every rung is under ONE regime, and every claim here is about a TREND ACROSS
RUNGS, so a v3/v4 level difference is common to all of them and cannot produce
a trend. **Do not compare any number here against a v4 number.**

## THE LADDER

`EleutherAI/pythia-6.9b@stepN`, 154 rungs from step0 to step143000, 2,272
prompts each. Log-spaced early (0,1,2,4,8,...) then every 1000 steps.
"""
import argparse
import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SIB = os.path.join(os.path.dirname(HERE), "pku-safe-rlhf")
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, REPO)
sys.path.insert(0, SIB)
OUT = os.path.join(HERE, "results")
LAD = "EleutherAI/pythia-6.9b@step%d"
RUNGS = [0, 16, 256, 1000, 4000, 16000, 64000, 143000]


def vocab():
    """The CLEAN vocabulary: the mixed-pair score, no fragments, content only."""
    import importlib.util
    from malignment import fields as F
    spec = importlib.util.spec_from_file_location(
        "wt", os.path.join(HERE, "word_transfer.py"))
    wt = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wt)
    lo, _, _ = wt.scores("mixed")
    keep = {}
    for w, v in lo.items():
        if len(w) < 3 or not w.isalpha():
            continue
        try:
            if F.is_content_word(w):
                keep[w] = v
        except Exception:
            pass
    return keep, wt


def probs(models, prompts):
    """{(model, prompt): {word: p}} from the v3 table. No movement rows exist."""
    from malignment import vectors as V
    out = collections.defaultdict(dict)
    CH = 40
    for i in range(0, len(prompts), CH):
        blk = prompts[i:i + CH]
        for r in V.rows(
                "SELECT model, prompt, word, p FROM twp_words "
                "WHERE model IN {ms:Array(String)} AND prompt IN {ps:Array(String)}",
                ms=models, ps=blk):
            out[(r["model"], r["prompt"])][r["word"]] = r["p"]
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompts", type=int, default=400)
    a = ap.parse_args(argv)
    import numpy as np
    from scipy import stats
    from malignment import vectors as V
    lo, wt = vocab()
    print("clean vocabulary: %d content words" % len(lo))
    ms = [LAD % s for s in RUNGS]
    ps = [r["prompt"] for r in V.rows(
        "SELECT prompt FROM twp_words WHERE model={m:String} "
        "GROUP BY prompt ORDER BY prompt LIMIT {n:UInt32}", m=LAD % 143000, n=a.prompts)]
    print("ladder %d rungs x %d prompts" % (len(ms), len(ps)))
    P = probs(ms, ps)

    print("\n%s\nLEVEL: mass-weighted mean PKU score of the distribution, per rung"
          % ("=" * 86))
    print("%12s %10s %8s" % ("rung", "level", "prompts"))
    lev = {}
    for s in RUNGS:
        vals = []
        for p in ps:
            d = P.get((LAD % s, p))
            if not d:
                continue
            num = den = 0.0
            for w, pr in d.items():
                v = lo.get(w.strip().lower())
                if v is None:
                    continue
                num += pr * v; den += pr
            if den > 0:
                vals.append(num / den)
        if vals:
            lev[s] = float(np.median(vals))
            print("%12d %+10.4f %8d" % (s, np.median(vals), len(vals)))

    print("\n%s\nMOVEMENT vs step0: per-prompt Spearman(PKU score, delta)\n%s"
          % ("=" * 86, "=" * 86))
    print("%12s %8s %10s %10s %11s" % ("rung", "n", "med rho", "up/dn", "p"))
    res = {}
    for s in RUNGS[1:]:
        rs = []
        for p in ps:
            A, B = P.get((LAD % 0, p)), P.get((LAD % s, p))
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
            continue
        up, dn, pv = wt.sign_test(rs)
        res[s] = float(np.median(rs))
        print("%12d %8d %+10.4f %5d/%-4d %11.2g" % (s, len(rs), np.median(rs), up, dn, pv))
    os.makedirs(OUT, exist_ok=True)
    json.dump(dict(levels=lev, rho_vs_step0=res, n_prompts=len(ps),
                   n_words=len(lo)),
              open(os.path.join(OUT, "pretraining.json"), "w"), indent=1)
    print("\n-> results/pretraining.json")
    print("\nFOR COMPARISON, the aligned edges on the same clean vocabulary:")
    print("   llama-7b -> alpaca-7b   +0.1058     49-lineage control median +0.0645")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
