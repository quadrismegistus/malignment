#!/usr/bin/env python
"""Write the SUCCESSES into the environment record. They were never being written.

    python scripts/record_successes.py --dry-run
    python scripts/record_successes.py --run

## THE RECORD WAS A FAILURE LOG PRETENDING TO BE A LOAD RECORD

`data/model_load_environments.json` held 64 observations on 2026-08-18, of which
38 were `load_failed` or `run_failed`. Meanwhile 52 models had v4 cells in
ClickHouse -- measured, on this machine, under a known interpreter -- and not one
of them had an observation.

That asymmetry is not a backlog, it is a **bias in what gets written**. A failure
interrupts you, so you record it; a success is invisible, so you do not. The
consequence is that `preflight_env.py` can never move a model out of UNVERIFIED
however many times it runs, and the record slowly becomes a list of everything
that has ever gone wrong with no denominator.

RH asked whether lessons were going into the file as they were learned. The
failures were. The successes were not, and they are the larger half.

## WHY THIS DERIVES RATHER THAN ASSERTS

Every row here is computed from two things that already exist: the CELLS in
`twp_cells_v4` (the model ran, and produced output) and the model's declared
`env: profile`, which resolves through `venvs.venv_for` to the interpreter that
produced them. Nothing is typed from memory, so nothing can be typed wrong.

**This is the strongest evidence class the campaign has** -- CLAUDE.md's rule is
that the corpus outranks the record precisely because a complete output file
cannot be mistaken about whether the thing ran.

The limit, stated because it is real: cells prove the model LOADED and PRODUCED,
not that the output is CORRECT. `deepseek` and `croissant` both produce cells and
both mangle the prompt in the tokenizer. So these rows say `load_ok` and never
`ok`, and a `run_failed` already on record is NEVER overwritten -- the outcome is
skipped for any model carrying one, because "it ran" does not answer "it ran
right", and this script must not be able to launder a known-bad tokenizer into a
green row.
"""
import argparse
import json
import os
import sys
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

from venvs import venv_for                                   # noqa: E402

from malignment import ch, roster                            # noqa: E402

RECORD = os.path.expanduser(
    "~/github/malign-logits/data/model_load_environments.json")
ENV_FOR_VENV = {".venv": "local_mps", ".venv-tf457": "local_mps_tf457"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--dry-run", action="store_true", default=True)
    a = ap.parse_args()

    rec = json.load(open(RECORD), object_pairs_hook=OrderedDict)
    by_model = {}
    for o in rec["observations"]:
        by_model.setdefault(o["model_id"], []).append(o)

    cells = {r["model"]: r["n"] for r in ch.query(
        "SELECT model, count() n FROM {db}.twp_cells_v4 GROUP BY model")}
    nodes = roster.load()["nodes"]

    add, skip = [], []
    for m, n in sorted(cells.items()):
        if m not in nodes:
            skip.append((m, "not in the roster"))
            continue
        venv = os.path.basename(venv_for(m))
        env = ENV_FOR_VENV.get(venv)
        if env is None:
            skip.append((m, "no environment mapped for %s" % venv))
            continue
        prior = by_model.get(m, [])
        #: **NEVER OVERWRITE A run_failed.** deepseek and croissant produce cells
        #: AND destroy the prompt in the tokenizer. Cells prove it ran, not that
        #: the output is usable, so a model with a recorded run_failure is left
        #: exactly as it is.
        if any(o["outcome"] == "run_failed" for o in prior):
            skip.append((m, "run_failed on record -- cells do not clear it"))
            continue
        if any(o["environment"] == env and o["outcome"] in
               ("load_ok", "loads", "ok") for o in prior):
            skip.append((m, "already recorded load_ok in %s" % env))
            continue
        add.append(OrderedDict([
            ("model_id", m),
            ("environment", env),
            ("outcome", "load_ok"),
            ("cause", ""),
            ("fix", "DERIVED FROM THE CORPUS, not hand-observed: %s cells in "
                    "twp_cells_v4 under profile `%s` -> %s. Says the model "
                    "loaded and produced output; says nothing about whether the "
                    "output is correct."
                    % (format(n, ","),
                       (nodes[m].get("env") or {}).get("profile", "default"), venv)),
        ]))

    print("v4 corpus covers %d models" % len(cells))
    print("  would ADD  %d load_ok observations" % len(add))
    print("  skipped    %d" % len(skip))
    for m, why in skip[:12]:
        print("     %-46s %s" % (m[:46], why))
    if len(skip) > 12:
        print("     ... and %d more" % (len(skip) - 12))

    if a.run:
        rec["observations"].extend(add)
        json.dump(rec, open(RECORD, "w"), indent=1, ensure_ascii=False)
        print("\nwrote %d; observations now %d" % (len(add), len(rec["observations"])))
    else:
        print("\n(dry run -- pass --run to write)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
