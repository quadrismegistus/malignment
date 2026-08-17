#!/usr/bin/env python
"""run.py — does an archive finding re-run HERE and agree?

    python run.py --scope        # what the archive claimed, what we can match
    python run.py --run --write  # reproduce it

**THE REPO'S OWN COMPLETION CRITERION, NEVER YET MET.** `MANIFEST.md` closes:

    What would tell us this migration is finished
    Not a file count. **An analysis that ran in the old repo, re-run here,
    agreeing.** Until one does, everything above is scaffolding that has never
    been asked a question it could get wrong.

Every other check in this repo asks whether a number is internally consistent.
This asks whether the port PRESERVED A RESULT, which nothing has.

## THE TARGET: FINDING N, the flagship

`meta/M01_displacement/findings/N_mass_migration.md`, registration
`9fb5e13fd1c3b1c8`, artifact `result_n_primary` `8a2ce3fdf4950ff2`:

    SUBSTITUTION CONFIRMED. 2,199 stimuli x 44 edges, 82,775 cells,
    91% NEGATIVE, 34/34 clusters agree. Stouffer Z is a FLOOR.

Chosen over F/G/L/M/Q because it is the anchor of the paper's first axis, it is
stated as a plain proportion (91%) rather than a model-dependent effect size,
and its statistic survived the port: `movement.decompose()` and `tail_excess`
are at `malignment/movement.py:535`, carried over rather than rewritten.

**The statistic, from the registration verbatim:** `tail_excess`, *"POSITIVE
means mass went into the unresolved tail beyond what renormalisation hands it
(the step DISPERSED); NEGATIVE means the tail gave mass up to nameable words
(the step SUBSTITUTED)."* So "91% negative" is 91% of cells substituting.

## WHAT AGREEMENT CAN AND CANNOT MEAN HERE

**This is a REPRODUCTION on a different population, not a re-run on the same
one.** The archive's 44 edges and 2,199 stimuli are not this store's 50 pairs
and 4,484 prompts, and no amount of care makes them the same cells. So:

    AGREES      the proportion negative is close to 91% and the per-cluster
                sign is unanimous or near it
    DISAGREES   the proportion is materially off, or clusters split

**A disagreement would NOT immediately convict the port** — it could be the
population. That is why the per-pair breakdown is reported beside the pooled
figure: a port defect should move all pairs together, a population difference
should move some. Neither reading is available from the pooled number alone,
which is the mistake this file exists to avoid making.

`residual_pre`/`residual_post` come from `twp_cells.total` — the MEASURED
four-way residual, accumulated from below by the tree expansion, not
`1 - sum(retained)`. The registration is explicit that this matters: it makes
`tail_excess` a measurement rather than a complement by construction.
"""
import argparse
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
RESULTS = os.path.join(HERE, "results")
sys.path.insert(0, ROOT)

from malignment import ch, movement as MV          # noqa: E402

ARCHIVE = {"pct_negative": 91.0, "cells": 82775, "edges": 44,
           "stimuli": 2199, "clusters_agree": "34/34"}


def _L(s):
    return "'" + s.replace("\\", "\\\\").replace("'", "\\'") + "'"


def pairs_and_prompts():
    eps = [(r["base"], r["endpoint"])
           for r in ch.query("SELECT base, endpoint FROM endpoints ORDER BY base")]
    prompts = {r["prompt"] for r in ch.query(
        "SELECT DISTINCT prompt FROM prompts WHERE language='en'", limit_bytes=None)}
    return eps, prompts


def run(eps, en_prompts, limit_pairs=None):
    out = []
    for n, (b, a) in enumerate(eps if limit_pairs is None else eps[:limit_pairs], 1):
        cells = {}
        for m, slot in ((b, 0), (a, 1)):
            for r in ch.query(
                    "SELECT prompt, total FROM twp_cells WHERE model=%s" % _L(m),
                    limit_bytes=None):
                cells.setdefault(r["prompt"], [None, None])[slot] = r["total"]
        shared = [p for p, v in cells.items()
                  if v[0] is not None and v[1] is not None and p in en_prompts]
        if not shared:
            continue
        words = collections.defaultdict(lambda: [{}, {}])
        for m, slot in ((b, 0), (a, 1)):
            for r in ch.query(
                    "SELECT prompt, word, p FROM twp_words WHERE model=%s" % _L(m),
                    limit_bytes=None):
                if r["prompt"] in cells:
                    words[r["prompt"]][slot][r["word"]] = r["p"]
        neg = tot = 0
        for p in shared:
            P, Q = words[p]
            if not P or not Q:
                continue
            try:
                d = MV.decompose(P, Q, residual_pre=cells[p][0],
                                 residual_post=cells[p][1])
            except Exception:
                continue
            te = d.get("tail_excess")
            if te is None:
                continue
            #: **ZERO-FALLER CELLS ARE EXCLUDED, per the registration §309** --
            #: `tail_excess` is DEFINED but degenerate there (with no fallers the
            #: ratio collapses to ~1 and excess becomes the raw delta), and the
            #: CLAIM does not apply: no mass departed, so nothing can have landed.
            if not d.get("n_fallers"):
                continue
            tot += 1
            neg += te < 0
        if tot:
            out.append({"base": b, "aligned": a, "cells": tot, "neg": neg,
                        "pct": 100.0 * neg / tot})
            print("  [%2d] %-42s %5d cells  %5.1f%% negative"
                  % (n, a[-42:], tot, 100.0 * neg / tot), flush=True)
    return out


def report(rows, write=False):
    cells = sum(r["cells"] for r in rows)
    neg = sum(r["neg"] for r in rows)
    pooled = 100.0 * neg / cells if cells else 0.0
    unanimous = sum(1 for r in rows if r["pct"] > 50)
    print("\n" + "=" * 66)
    print("  ARCHIVE  Finding N: %.0f%% negative, %s clusters agree, %s cells"
          % (ARCHIVE["pct_negative"], ARCHIVE["clusters_agree"],
             format(ARCHIVE["cells"], ",")))
    print("  HERE     %.1f%% negative, %d/%d pairs majority-negative, %s cells"
          % (pooled, unanimous, len(rows), format(cells, ",")))
    print("  delta    %+.1f points" % (pooled - ARCHIVE["pct_negative"]))
    #: **THE PER-PAIR SPREAD IS THE DIAGNOSTIC, not decoration.** A port defect
    #: should move every pair together; a population difference should move some.
    v = sorted(r["pct"] for r in rows)
    if v:
        print("  per-pair %%negative: min %.1f  median %.1f  max %.1f"
              % (v[0], v[len(v) // 2], v[-1]))
        low = sorted(rows, key=lambda r: r["pct"])[:4]
        print("  lowest pairs:")
        for r in low:
            print("     %-46s %5.1f%% (%d cells)" % (r["aligned"][-46:], r["pct"], r["cells"]))
    if write:
        os.makedirs(RESULTS, exist_ok=True)
        p = os.path.join(RESULTS, "archive_agreement.json")
        json.dump({"archive": ARCHIVE, "pooled_pct_negative": pooled,
                   "cells": cells, "pairs": rows}, open(p, "w"), indent=1)
        print("\n  wrote %s" % p)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scope", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--pairs", type=int)
    a = ap.parse_args()
    eps, en = pairs_and_prompts()
    print("  declared pairs %d | English prompts %d" % (len(eps), len(en)))
    print("  archive claim: %.0f%% negative over %s cells, %s edges, %s stimuli"
          % (ARCHIVE["pct_negative"], format(ARCHIVE["cells"], ","),
             ARCHIVE["edges"], format(ARCHIVE["stimuli"], ",")))
    if a.scope or not a.run:
        print("\n  --run to reproduce")
        return 0
    report(run(eps, en, a.pairs), write=a.write)
    return 0


if __name__ == "__main__":
    sys.exit(main())
