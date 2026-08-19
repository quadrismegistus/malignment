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
critical path is the LARGEST lineage — Llama-3.1-8B, 11 models. Measured over the
current corpus, and the SHAPE is what matters rather than the absolute hours:

     8 boxes  1.9x critical      12 boxes  1.08x
    10 boxes  1.4x critical      16 boxes  1.00x   <- critical path bound
                                 20 boxes  1.00x   <- buys NOTHING over 16

So beyond ~12 the wall clock stops moving and only the number of things that can
fail goes up. The runbook's casualty rate is the other half of that argument: the
L2 fleet lost 3 of 14 and the grid lost 6 of 14 in provisioning, and every one
needed a human. 12 boxes at 1.08x critical beats 20 at 1.00x on every axis that
matters.

## THERE IS NO SINGLE RATE, AND TWO CORRECTIONS WERE NEEDED TO SEE IT

`SEC_PER_CELL` was a constant here, and it was wrong twice for different reasons:

    0.8    the MPS rate, while every box in this plan is CUDA          4x slow
    0.19   CUDA, measured on ONE model (kanana, 8B), applied to 144
           models whose measured rates span 0.155 to 6.04 s/cell

**Correcting the first to the second fixed the DEVICE and left the sampling error
untouched**, which is how one class of error survived its own correction: both
numbers were a single measurement standing in for 144 models.

An earlier version of this block blamed the spread on vocabulary size. **That is
refuted on our own data** -- over 107 MPS observations, r(log vocab, log s/cell)
= -0.05 while r(log params, log s/cell) = +0.54. Model size is the driver.

So the constant is gone. `malignment.rates` stores an observation per run --
model, device, card, vocab size, n_cells, load and compute SEPARATELY -- and
`seconds()` prices a shard at per-model recorded rates, returning the models it
had to guess for alongside the total. RH's ask: *"why don't we store
model-specific twp rates?"*

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

from malignment import ch, rates, roster                     # noqa: E402
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

#: **KEPT ONLY AS THE NAME OF A MISTAKE.** Nothing reads it. Planning goes through
#: `seconds()` -> `rates.rate_for(model, device)`; a module-level scalar is exactly
#: the shape that let one model's measurement price a 144-model fleet.
SEC_PER_CELL = None


def seconds(remaining, device="cuda", only=None):
    """(seconds, guessed_models) for {model: cells}, at PER-MODEL recorded rates.

    **A rate is a property of (model x device), not of twp.** `SEC_PER_CELL` was a
    single number twice, and both times it was one model's measurement standing in
    for 144 models whose measured rates span 0.155 to 6.04 s/cell -- a 39x range
    that no scalar can carry. Model size predicts it (r = +0.54 in log-log over
    107 observations); vocabulary, which an earlier version of this docstring
    named as the mechanism, does not (r = -0.05).

    Models never measured fall back, and **the fallback list comes back with the
    answer** so a caller cannot quote the total without also being handed how much
    of it is a guess.
    """
    est, guessed = rates.estimate(sorted(remaining), device, only=only)
    return sum(remaining[m] * est[m][0] for m in remaining), guessed


def lineage_work(pop=None):
    """[(root, members, venv, cells_remaining, {model: cells})] -- ENDPOINTS only."""
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
        per = {m: max(0, pop - have.get(m, 0)) for m in ms}
        out.append((r, ms, venvs.pop(), sum(per.values()), per))
    return out


def pack(work, nboxes, device="cuda"):
    """Longest-processing-time-first on SECONDS, never mixing venvs on one box.

    **Cells are not the cost.** This packed by cell count while the measured rates
    span 0.155 to 6.04 s/cell, so it balanced the wrong quantity: with per-model
    rates in hand, the cell-balanced plan ran 5.2 h on its slowest box against
    1.2 h on its fastest, for a total that would have fitted in ~3.1 h. A lineage
    of four small models and a lineage of four 7B models are the same number of
    cells and nothing like the same job.
    """
    bins = [{"cells": 0, "secs": 0.0, "lineages": [], "models": [], "venv": None,
             "per": {}} for _ in range(nboxes)]
    scored = [(w, seconds(w[4], device)[0]) for w in work]
    for (root, ms, venv, cells, per), sec in sorted(scored, key=lambda x: -x[1]):
        cand = [b for b in bins if b["venv"] in (None, venv)] or bins
        b = min(cand, key=lambda b: b["secs"])
        b["cells"] += cells
        b["secs"] += sec
        b["lineages"].append(root)
        b["models"] += ms
        b["per"].update(per)
        b["venv"] = venv
    return bins


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--boxes", type=int, default=12)
    ap.add_argument("--write", default=None)
    ap.add_argument("--device", default="cuda",
                    help="which device's recorded rates to plan against")
    a = ap.parse_args()
    work = lineage_work()
    tot = sum(w[3] for w in work)
    bins = [b for b in pack(work, a.boxes, a.device) if b["lineages"]]

    tot_s, guessed = seconds({m: c for w in work for m, c in w[4].items()}, a.device)
    crit = max(work, key=lambda w: seconds(w[4], a.device)[0])
    crit_s = seconds(crit[4], a.device)[0]
    print("endpoint lineages %d | models %d | %s cells | %.1f GPU-h on %s"
          % (len(work), sum(len(w[1]) for w in work), format(tot, ","),
             tot_s / 3600, a.device))
    #: **THE GUESSED COUNT IS PRINTED WITH THE TOTAL, NOT UNDER IT.** An estimate
    #: whose provenance sits three lines down gets quoted without it -- which is
    #: how a single model's rate became the fleet's rate, twice.
    nm = sum(len(w[1]) for w in work)
    est_all, _g = rates.estimate(sorted({m for w in work for m in w[1]}), a.device)
    kinds = {"measured": 0, "transferred": 0, "fallback": 0}
    for _m, (_s, why) in est_all.items():
        kinds["fallback" if why.startswith("FALLBACK") else
              "transferred" if why.startswith("TRANSFERRED") else "measured"] += 1
    rr, rwhy = rates.device_ratio(a.device)
    print("             of %d models: %d measured on %s, %d transferred, %d guessed"
          % (nm, kinds["measured"], a.device, kinds["transferred"], kinds["fallback"]))
    print("             transfer basis: %s" % rwhy)
    print("critical path: %s, %d models, %s cells, %.1f h -- a lineage is NOT splittable"
          % (crit[0], len(crit[1]), format(crit[3], ","), crit_s / 3600))
    print("\n%-4s %-13s %-9s %-7s %s" % ("box", "venv", "cells", "hours", "lineages"))
    for i, b in enumerate(sorted(bins, key=lambda b: -seconds(b["per"], a.device)[0]), 1):
        print("%-4d %-13s %-9s %-7.1f %d: %s"
              % (i, b["venv"], format(b["cells"], ","),
                 seconds(b["per"], a.device)[0] / 3600,
                 len(b["lineages"]),
                 ", ".join(r.split("/")[-1] for r in b["lineages"])[:52]))
    if a.write:
        json.dump({"boxes": [{"venv": b["venv"], "cells": b["cells"],
                              "per": b["per"],
                              "lineages": b["lineages"], "models": b["models"]}
                             for b in bins]},
                  open(a.write, "w"), indent=1)
        print("\nwrote %s" % a.write)
    return 0


if __name__ == "__main__":
    sys.exit(main())
