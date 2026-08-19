#!/usr/bin/env python
"""Shard the fleet by LINEAGE, not by environment. Emits one payload per box.

    python scripts/fleet_shards.py --boxes 12
    python scripts/fleet_shards.py --boxes 12 --write data/fleet_shards.json

## WHY LINEAGE AND NOT ENVIRONMENT

RH's call, and it is about PASS 2. `topup` scores the words a model's LINEAGE
cleared and it did not, so a model's pass 2 depends on its SIBLINGS' pass 1.

Sharded by environment, siblings scatter across boxes and **no box can run pass 2
at all** until every box has finished and been merged back — a second wave, with
a merge in between, and a corpus that is half-done in a way no single box can
detect. Sharded by lineage, a box runs pass 1 over its own members, then pass 2
over them, and ships a CLOSED lineage.

It also fixes something `pass1_todo`'s docstring already flags: a fleet box
cannot compute its own worklist because `topup_todo` reads ClickHouse and a fresh
rental has none. With the whole lineage local, the union is derivable from what
the box itself wrote.

**And it costs nothing in environments: all 50 endpoint lineages need exactly one
venv each.** Measured, not assumed — `{1: 50}`. That was the thing that could
have killed the idea and it does not.

## THE POPULATION IS THE ENDPOINT LINEAGES, AND ONLY THOSE

`roster.endpoints()` resolves 50 bases to one commodity-form endpoint each; the
lineages containing them hold 144 models. Lineages with no endpoint are NOT
included — they answer nothing the frame reads. Derived here from
`roster.endpoints()` on every call rather than written into a list, because an
inline population filter is how `"lmo" in base` once found 4 of 6 OLMo lineages.

## BOX COUNT: MORE IS NOT FASTER

A lineage cannot be split without losing the pass-2 locality above, so the
critical path is the LARGEST lineage — Llama-3.1-8B, 11 models, ~7.2 h. Measured
over the current corpus:

     8 boxes  15.3 h      12 boxes   7.8 h
    10 boxes  10.2 h      16 boxes   7.2 h   <- critical path bound
                          20 boxes   7.2 h   <- buys NOTHING over 16

So beyond ~12 the wall clock stops moving and only the number of things that can
fail goes up. The runbook's casualty rate is the other half of that argument: the
L2 fleet lost 3 of 14 and the grid lost 6 of 14 in provisioning, and every one
needed a human. 12 boxes at 7.8 h beats 20 at 7.2 h on every axis that matters.

Packing is longest-processing-time-first with a venv-compatibility constraint, so
a box never holds two lineages needing different interpreters.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

from venvs import venv_for                                   # noqa: E402

from malignment import ch, roster                            # noqa: E402
from malignment.prompts import Prompts                       # noqa: E402

#: **A TOKENIZER DEFECT IS SCOPED TO A PROMPT CLASS, NOT TO A MODEL.** Re-tested
#: 2026-08-19 by round-tripping each model on the surface its own record names,
#: rather than by trusting the record -- and the exclusion list was wrong in BOTH
#: directions:
#:
#:   deepseek base+chat   RE-ADMITTED. Recorded run_failed for deleting spaces
#:                        (encode('a b') == encode('ab')). That defect was FIXED
#:                        by the `tokenizer_loader` override in models.yaml and
#:                        the fix is live: loader=override:#45488/#47017,
#:                        LATIN and CJK both round-trip exactly. Its 2,663 v3
#:                        cells track Mistral and Llama to two decimals -- `fired
#:                        0.284 / 0.251 / 0.243` on one prompt -- which is not
#:                        what a space-deleted prompt produces. I excluded it all
#:                        day on a stale verdict.
#:
#:   CroissantLLMChat     NEWLY EXCLUDED on CJK. Only the Base arm was recorded;
#:                        the Chat arm has the IDENTICAL defect, losing the same
#:                        6 characters of 15. Nobody had tested it.
#:
#:   Teuken               CJK only, and milder: loses the fullwidth comma alone.
#:
#: All three are EXACT on Latin. So they are not dead models, they are models
#: with a CJK-class defect, and excluding them from Latin work threw away
#: measurable cells. Keyed by prompt class for that reason.
TOKENIZER_DEAD_CJK = {"croissantllm/CroissantLLMBase",
                      "croissantllm/CroissantLLMChat-v0.1",
                      "openGPT-X/Teuken-7B-base-v0.6"}
#: nothing is dead on every prompt class as of this test
TOKENIZER_DEAD = set()


def lineage_work(pop=None):
    """[(root, members, venv, cells_remaining)] over ENDPOINT lineages only."""
    pop = pop or len({p.text for p in Prompts.all()})
    eps, unresolved = roster.endpoints()
    if unresolved:
        raise SystemExit("%d lineages unresolved -- endpoints() returns candidates "
                         "rather than picking, and a caller ignoring that is "
                         "choosing by accident" % len(unresolved))
    lin = roster.lineages(ops=roster.ALIGNING)
    roots = sorted({r for b in eps for r, ms in lin.items() if b in ms or b == r})
    have = {r["model"]: r["n"] for r in ch.query(
        "SELECT model, countDistinct(prompt) n FROM {db}.twp_cells_v4 "
        "WHERE topup=0 GROUP BY model")}
    out = []
    for r in roots:
        ms = sorted(m for m in lin[r] if m not in TOKENIZER_DEAD)
        if not ms:
            continue
        venvs = {os.path.basename(venv_for(m)) for m in ms}
        if len(venvs) != 1:
            #: Never silently split. If this ever fires, the lineage genuinely
            #: needs two interpreters and the box must build both -- a decision,
            #: not something to paper over in a packer.
            raise SystemExit("lineage %s spans %s -- decide explicitly" % (r, venvs))
        out.append((r, ms, venvs.pop(), sum(max(0, pop - have.get(m, 0)) for m in ms)))
    return out


def pack(work, nboxes):
    """Longest-processing-time-first, never mixing venvs on one box."""
    bins = [{"cells": 0, "lineages": [], "models": [], "venv": None}
            for _ in range(nboxes)]
    for root, ms, venv, cells in sorted(work, key=lambda x: -x[3]):
        cand = [b for b in bins if b["venv"] in (None, venv)] or bins
        b = min(cand, key=lambda b: b["cells"])
        b["cells"] += cells
        b["lineages"].append(root)
        b["models"] += ms
        b["venv"] = venv
    return bins


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--boxes", type=int, default=12)
    ap.add_argument("--write", default=None)
    a = ap.parse_args()
    work = lineage_work()
    tot = sum(w[3] for w in work)
    crit = max(work, key=lambda w: w[3])
    bins = [b for b in pack(work, a.boxes) if b["lineages"]]
    print("endpoint lineages %d | models %d | %s cells | %.0f GPU-h @0.8s"
          % (len(work), sum(len(w[1]) for w in work), format(tot, ","), tot * .8 / 3600))
    print("critical path: %s, %d models, %s cells, %.1f h -- a lineage is NOT splittable"
          % (crit[0], len(crit[1]), format(crit[3], ","), crit[3] * .8 / 3600))
    print("\n%-4s %-13s %-9s %-7s %s" % ("box", "venv", "cells", "hours", "lineages"))
    for i, b in enumerate(sorted(bins, key=lambda b: -b["cells"]), 1):
        print("%-4d %-13s %-9s %-7.1f %d: %s"
              % (i, b["venv"], format(b["cells"], ","), b["cells"] * .8 / 3600,
                 len(b["lineages"]),
                 ", ".join(r.split("/")[-1] for r in b["lineages"])[:52]))
    if a.write:
        json.dump({"boxes": [{"venv": b["venv"], "cells": b["cells"],
                              "lineages": b["lineages"], "models": b["models"]}
                             for b in bins]},
                  open(a.write, "w"), indent=1)
        print("\nwrote %s" % a.write)
    return 0


if __name__ == "__main__":
    sys.exit(main())
