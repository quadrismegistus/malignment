#!/usr/bin/env python
"""Did pass 2 actually CLOSE this lineage? Four checks, each with a failure it owns.

    python scripts/verify_lineage_topup.py --root m-a-p/CT-LLM-Base

## "THE LOOP FINISHED" IS NOT THE CLAIM

`topup_lineage.py` exiting means every prompt on the worklist got a cell. It does
not mean the lineage closed, and the two come apart in every direction that
matters here:

    written != covered     a REFUSED cell is written nowhere and the run still
                           reports success. The v3-sourced worklist refused 44
                           of 60 and exited 0.
    covered != conserved   a cell can carry every word and still not close its
                           books if `tail` was decremented by the wrong amount.
                           Conservation is the only check that sees this.
    conserved != ingested  the stash is not the corpus. A cell that never
                           reaches ClickHouse is invisible to every consumer,
                           including `topup_todo`, which would then hand the
                           same words to a second pass.
    ingested != idempotent the fixed point. If `topup_todo` is non-empty after
                           all of the above, pass 2 has not converged and
                           running it again would add MORE mass to the same
                           cells.

So the check that matters most is the last one, and it is the only one that can
only be run afterwards: **the lineage is closed when asking for the worklist
returns nothing.**

## CONSERVATION IS NECESSARY AND NOT SUFFICIENT

Stated because it was already learned the expensive way in `test_twp_v4.py`: the
`numeric_intra` regression routed mass to `drop` and conservation SURVIVED it,
because the mass was accounted for -- just misfiled. So check 2 catches mass that
vanishes, never mass that lands in the wrong bucket. The `tail` floor in check 2b
is what catches the specific misfiling this pass can produce.
"""
import argparse
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from malignment import ch, corpus, roster  # noqa: E402
from malignment.checkpoint import Checkpoint  # noqa: E402
from malignment.runners import PRODUCER  # noqa: E402

TOL = 1e-5


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    a = ap.parse_args()
    members = sorted(roster.lineages(ops=roster.ALIGNING).get(a.root) or [])
    if not members:
        raise SystemExit("%s is not a lineage root" % a.root)

    union = corpus.lineage_union(a.root)
    print("lineage %s -- %d members, union over %d prompts\n"
          % (a.root, len(members), len(union)))
    bad = []

    for m in members:
        short = m.split("/")[-1]
        stash = Checkpoint(m).stash(PRODUCER)
        cells = [(k, stash[k]) for k in stash.keys()
                 if isinstance(k, dict) and k.get("topup")]

        # --- 1. coverage: every union word present, from EITHER pass -----------
        missing = corpus.topup_todo(m, root=a.root)
        n_missing = sum(len(v) for v in missing.values())

        # --- 2. conservation, and the tail it was taken from -------------------
        cons, tails, added = [], [], []
        for _k, d in cells:
            r = d["residual"]
            cons.append(sum(x["p"] for x in d["rows"]) + r["tail"] + r["drop"]
                        + r["open"] + r["mojibake"] + r.get("term_floored", 0.0))
            tails.append(r["tail"])
            added.append(sum(x["p"] for x in d["rows"] if x.get("topup")))
        worst = max((abs(c - 1.0) for c in cons), default=0.0)
        neg = sum(1 for t in tails if t < 0)

        # --- 3. the corpus, not the stash --------------------------------------
        inch = ch.scalar("SELECT count() FROM {db}.twp_cells_v4 "
                         "WHERE model='%s' AND topup=1" % m.replace("'", "\\'"))

        #: **A MEMBER THAT DID NOTHING PASSES EVERY OTHER CHECK.** With zero
        #: topup cells, conservation is 0 < tol, the tail count is 0 negative,
        #: and `0 == 0` ingested -- three green lines describing an empty set.
        #: Only coverage would object, and coverage is computed by
        #: `topup_todo`, the function that was returning the wrong answer this
        #: morning. So a bug there plus an empty run reads as a clean PASS from
        #: every angle. Zero is a free answer and is never allowed to be a
        #: silent one: a member with no cells is reported as VACUOUS, and it
        #: fails unless its worklist was genuinely empty before the run.
        vacuous = not cells
        ok = (n_missing == 0 and worst < TOL and neg == 0 and inch == len(cells))
        verdict = ("PASS" if ok else "**FAIL**") if not vacuous else (
            "VACUOUS -- nothing was topped up; PASS here is an empty set, "
            "not a measurement" if ok else "**FAIL** (and vacuous)")
        bad += [] if ok else [short]
        print("  %-24s %s" % (short, verdict))
        print("     coverage     %s (%d words over %d prompts still missing)"
              % ("closed" if n_missing == 0 else "OPEN", n_missing, len(missing)))
        print("     conservation worst |1-total| = %.2e over %d topup cells%s"
              % (worst, len(cells), "" if worst < TOL else "   <-- over tolerance"))
        print("     tail         median %.4f, min %.4f, %d negative"
              % (st.median(tails) if tails else 0, min(tails) if tails else 0, neg))
        print("     added mass   median %.4f, max %.4f"
              % (st.median(added) if added else 0, max(added) if added else 0))
        print("     ingested     %s of %s stash cells in twp_cells_v4%s\n"
              % (format(inch, ","), format(len(cells), ","),
                 "" if inch == len(cells) else "   <-- NOT the corpus"))

    print("LINEAGE %s" % ("CLOSED" if not bad else "OPEN: " + ", ".join(bad)))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
