#!/usr/bin/env python
"""run.py — is the unresolved-mass leak CORRELATED with the effect it could fake?

    python run.py --write

**THIS FILE EXISTS BECAUSE ITS RESULT WAS ORPHANED.** The measurement was first
run as an inline heredoc and its numbers went only into a commit message
(`d7138dc`) which — separately, and my fault — carried another seat's diff. A
result whose only record is a commit message on the wrong diff is not a result.
So it is a script now, and it reproduces.

## THE QUESTION

`twp_v4.leak_bound` gives a per-cell worst case that is the same order as the
effects (registration N: *"It is the same order as plausible effects"*), and on
`kill->scream` only 8 of 50 pairs individually exceed it. Aggregate claims —
`41/50 lineages`, `91% negative` — survive that **only if the leak is not
adversarially CORRELATED with the effect.** Nobody had checked.

Correlation is not a nuisance here, it is the mechanism running through
everything else measured this week: the residual is enriched in lexicon words
(dario: 27.1% vanish below theta against 16.9% of controls), alignment pushes
lexicon words below theta, so unresolved mass grows in the naughty direction in
the ALIGNED arm specifically. Same shape as `T` being a mediator ([6374]).

## WHAT IT REPORTS

    same-sign rate   how often `matched` leak co-signs with `dN`.
                     50% = independent. Anything near 100% = the leak is
                     pushing the result in its own direction.
    corrected count  sign count after subtracting the matched leak
    survival         how much of the median |dN| is left

`matched` assumes the tail is distributed like the head. dario measured it is
NOT, so **the correction this computes is a FLOOR on the true one**, and the
"12% of magnitude" below should never be quoted as its size.
"""
import argparse
import json
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "dn_convention"))

from malignment import ch, twp_v4 as V4               # noqa: E402
from malignment.slot_axis import Axis                 # noqa: E402
import kill_scream as KS                              # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    P = KS.PROMPT
    by = {}
    for r in ch.query("SELECT model, word, p FROM twp_words WHERE prompt='%s'" % P,
                      limit_bytes=None):
        by.setdefault(r["model"], {})[r["word"]] = r["p"]
    res = {r["model"]: r["total"] for r in ch.query(
        "SELECT model, total FROM twp_cells WHERE prompt='%s'" % P, limit_bytes=None)}
    S = KS.declared_axis(P, sorted({w for m in by for w in by[m]}))
    ax = object.__new__(Axis)

    rows = []
    for e in ch.query("SELECT base, endpoint FROM endpoints", limit_bytes=None):
        b, al = e["base"], e["endpoint"]
        if b not in by or al not in by:
            continue
        dn = ax.split(by[b], by[al], S)["dN"]
        lb = V4.leak_bound(by[b], by[al], S, res[b], res[al])
        rows.append({"aligned": al, "dN": dn, "matched": lb["matched"],
                     "worst": lb["worst"], "corrected": dn - lb["matched"]})

    n = len(rows)
    same = sum(1 for r in rows if (r["dN"] < 0) == (r["matched"] < 0))
    neg = sum(1 for r in rows if r["dN"] < 0)
    negc = sum(1 for r in rows if r["corrected"] < 0)
    exceeds = sum(1 for r in rows if abs(r["dN"]) > r["worst"])
    md, mc = (st.median(abs(r["dN"]) for r in rows),
              st.median(abs(r["corrected"]) for r in rows))
    print("  prompt: %r   n=%d pairs" % (P, n))
    print("  matched leak SAME SIGN as dN in %d/%d (%.0f%%)   [50%% = independent]"
          % (same, n, 100.0 * same / n))
    print("  |dN| exceeds the WORST-case bound in %d/%d" % (exceeds, n))
    print("  displacing (dN<0)            %d/%d" % (neg, n))
    print("  displacing AFTER correction  %d/%d" % (negc, n))
    print("  median |dN| %.5f -> %.5f  (%.0f%% survives, %d sign flips)"
          % (md, mc, 100.0 * mc / md, sum(1 for r in rows
                                          if (r["dN"] < 0) != (r["corrected"] < 0))))
    if a.write:
        out = os.path.join(HERE, "results")
        os.makedirs(out, exist_ok=True)
        json.dump({"prompt": P, "n_pairs": n, "same_sign": same,
                   "exceeds_worst": exceeds, "neg": neg, "neg_corrected": negc,
                   "median_abs_dN": md, "median_abs_corrected": mc,
                   "pairs": rows}, open(os.path.join(out, "leak_bound.json"), "w"),
                  indent=1)
        print("\n  wrote %s/leak_bound.json" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
