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

Every row here is computed from the CELLS in `twp_cells_v4` -- the model ran, and
produced output. Nothing is typed from memory, so nothing can be typed wrong.

## THE ENVIRONMENT COMES FROM THE CELLS, NOT FROM THE VENV

**IT USED TO COME FROM `venvs.venv_for(model)` THROUGH A TWO-ENTRY MAP:**

    ENV_FOR_VENV = {".venv": "local_mps", ".venv-tf457": "local_mps_tf457"}

so EVERY success was stamped as having happened on this Mac. It did not. Of the
145 models with v4 cells, **38 are cuda-only** -- they have never run here and
some of them cannot. Recording those as `local_mps` writes a flat impossibility:
`meta-llama/Llama-3.1-70B-Instruct` already carries

    local_mps | load_failed | "CAPACITY: ~140GB bf16 against 96GB unified memory"

and the venv map would have added `local_mps | load_ok` directly beside it. The
dedupe could not catch it: it skips an existing `run_failed`, or a matching
`load_ok` in the same environment, and a `load_failed` is neither.

`twp_cells_v4` carries `device`, `torch_version` and `transformers_version` per
cell, so the environment is MEASURED. The device split is unambiguous -- MPS runs
`torch 2.13.0`, the boxes run `2.13.0+cu130`.

**Cells with no version stamp get their own environment rather than a guess.**
The version fields were added mid-corpus; 338,644 cells predate them. Those are
`local_mps_unversioned` / `cloud_cuda_unversioned` -- honest about the device,
silent about the toolchain. Folding them into a versioned name would assert a
library version nobody observed.

`compute_dtype` is deliberately NOT part of the environment identity. It is
chosen per model by the producer (Falcon-H1 needs bf16 on the same box where
everything else runs fp16), so it is a property of the row, not of the machine.

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

from malignment import ch, roster                            # noqa: E402

#: **WRITES TO THE LIVE ROSTER, NOT THE ARCHIVE.** This pointed at
#: `~/github/malign-logits/data/model_load_environments.json` until 2026-08-22 --
#: a repo RH has declared READ-ONLY. So a script in the LIVE repo was depositing
#: new model information into the ARCHIVE, and the only path back out,
#: `ingest_environments.py`, is a one-shot that refuses to run twice by design.
#: The record forked in silence: 131 observations in the archive against 72 here,
#: diverging in BOTH directions because each side also took its own hand edits,
#: so neither was a superset and a copy either way would have destroyed work.
#: Rejoined by `scripts/merge_environment_record.py` (additive, re-runnable);
#: this constant is what stops it reopening.
RECORD = os.path.join(ROOT, "roster", "models", "observations.json")

#: LOCAL and CLOUD are different environments and must never share a name. The
#: discriminator is measured, not assumed: MPS reports `torch 2.13.0`, a rented
#: box reports `2.13.0+cu130`.
DEVICE_PREFIX = {"mps": "local_mps", "cuda": "cloud_cuda"}


def env_name(device, tf, torch):
    """(name, definition) for a measured (device x toolchain), or (None, why).

    Naming follows what `observations.json` already uses -- `local_mps_tf457`,
    `cloud_cuda_transformers_5.14.1` -- rather than inventing a third scheme.

    **THE DEFINITION IS STRUCTURED, NOT PROSE, AND THE FIRST VERSION WAS PROSE.**
    The 14 hand-authored environments carry `device` / `torch` / `transformers`
    as FIELDS; the five this function generated carried a `description` string
    instead, so nothing could read a version out of them. That silently blocks
    everything downstream that wants to compare versions across environments --
    which is the whole point of recording them. A producer that does not inherit
    its file's convention writes rows that only a human can use.
    """
    from collections import OrderedDict as _OD
    pre = DEVICE_PREFIX.get((device or "").lower())
    if pre is None:
        return None, "unknown device %r" % device
    where = "MPS (this Mac)" if pre == "local_mps" else "rented CUDA box"
    if not tf:
        #: **NOT FOLDED INTO A VERSIONED NAME.** The version fields were added
        #: mid-corpus. Naming these `local_mps` would assert the toolchain that
        #: `local_mps` declares (torch 2.11.0) for cells that never recorded one.
        return pre + "_unversioned", _OD([
            ("device", device),
            ("torch", None),
            ("transformers", None),
            ("note", "%s. Library versions NOT RECORDED -- these cells predate "
                     "the version stamp on twp cells. Device is measured; the "
                     "toolchain is not, and null here means UNKNOWN, never "
                     "'same as the versioned sibling'." % where),
            ("source", "derived by record_successes.py from twp_cells_v4"),
        ])
    cuda = "130" if "+cu130" in (torch or "") else ""
    tag = "tf" + tf.replace(".", "")[:4]
    return "%s%s_%s" % (pre, cuda, tag), _OD([
        ("device", device),
        ("torch", torch),
        ("transformers", tf),
        ("note", "%s. Derived from the cells that actually ran in it." % where),
        ("source", "derived by record_successes.py from twp_cells_v4"),
    ])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--dry-run", action="store_true", default=True)
    a = ap.parse_args()

    rec = json.load(open(RECORD), object_pairs_hook=OrderedDict)
    by_model = {}
    for o in rec["observations"]:
        by_model.setdefault(o["model_id"], []).append(o)

    #: GROUPED BY THE MEASURED ENVIRONMENT, not by model. One model legitimately
    #: yields several rows -- 86 of 145 have cells on BOTH devices, and that is a
    #: fact worth recording once per environment rather than collapsing.
    grouped = ch.query(
        "SELECT model, device, transformers_version tf, torch_version torch, "
        "  groupUniqArray(compute_dtype) dtypes, count() n "
        "FROM {db}.twp_cells_v4 "
        "GROUP BY model, device, tf, torch ORDER BY model, device, tf")
    nodes = roster.load()["nodes"]

    add, skip, envs_seen = [], [], OrderedDict()
    for row in grouped:
        m, n = row["model"], row["n"]
        if m not in nodes:
            skip.append((m, "not in the roster"))
            continue
        env, why = env_name(row["device"], row["tf"], row["torch"])
        if env is None:
            skip.append((m, why))
            continue
        envs_seen.setdefault(env, why)
        prior = by_model.get(m, [])
        #: **NEVER OVERWRITE A run_failed.** deepseek and croissant produce cells
        #: AND destroy the prompt in the tokenizer. Cells prove it ran, not that
        #: the output is usable, so a model with a recorded run_failure is left
        #: exactly as it is.
        if any(o["outcome"] == "run_failed" for o in prior):
            skip.append((m, "run_failed on record -- cells do not clear it"))
            continue
        #: **A load_failed IN THIS ENVIRONMENT IS A CONTRADICTION, NOT A GAP.**
        #: The venv-derived version could not reach this branch: it stamped every
        #: success `local_mps`, so a cuda-only model's cells arrived at the same
        #: environment as its MPS capacity failure and the two never met as a
        #: contradiction -- they met as a duplicate key. Refuse and report.
        clash = [o for o in prior if o["environment"] == env
                 and o["outcome"] in ("load_failed", "run_failed")]
        if clash:
            skip.append((m, "CONTRADICTS a recorded %s in %s -- refusing"
                         % (clash[0]["outcome"], env)))
            continue
        if any(o["environment"] == env and o["outcome"] in
               ("load_ok", "loads", "ok") for o in prior):
            skip.append((m, "already recorded load_ok in %s" % env))
            continue
        dts = ", ".join(sorted(x for x in (row.get("dtypes") or []) if x))
        add.append(OrderedDict([
            ("model_id", m),
            ("environment", env),
            ("outcome", "load_ok"),
            ("cause", ""),
            ("fix", "DERIVED FROM THE CORPUS, not hand-observed: %s cells in "
                    "twp_cells_v4 on device `%s`%s, profile `%s`, compute_dtype "
                    "%s. Says the model loaded and produced output; says nothing "
                    "about whether the output is correct."
                    % (format(n, ","), row["device"],
                       (", transformers %s / torch %s" % (row["tf"], row["torch"]))
                       if row["tf"] else " (library versions not recorded)",
                       (nodes[m].get("env") or {}).get("profile", "default"),
                       dts or "unrecorded")),
        ]))

    models = {r["model"] for r in grouped}
    print("v4 corpus covers %d models across %d measured environments"
          % (len(models), len(envs_seen)))
    for e, defn in envs_seen.items():
        n = sum(1 for r in add if r["environment"] == e)
        print("   %-28s +%-4d %s" % (e, n, str(defn.get("note"))[:60]))
    print("  would ADD  %d load_ok observations" % len(add))
    print("  skipped    %d" % len(skip))
    clashes = [s for s in skip if "CONTRADICTS" in s[1]]
    if clashes:
        print("  ** %d REFUSED as contradictions:" % len(clashes))
        for m, why in clashes[:8]:
            print("       %-44s %s" % (m[:44], why))
    for m, why in [s for s in skip if s not in clashes][:8]:
        print("     %-46s %s" % (m[:46], why))
    if len(skip) > 8:
        print("     ... and %d more" % (len(skip) - 8))

    if a.run:
        rec["observations"].extend(add)
        #: Register every environment we just named, so a reader can resolve it.
        #: **STRUCTURED, matching the 14 hand-authored entries.** Also REPAIRS
        #: any earlier entry this script wrote as prose: those carried a
        #: `description` and no `transformers`/`torch`, so no consumer could
        #: read a version out of them.
        envs = rec.setdefault("environments", OrderedDict())
        for e, defn in envs_seen.items():
            cur = envs.get(e)
            if cur is None or "transformers" not in cur:
                envs[e] = defn
        json.dump(rec, open(RECORD, "w"), indent=1, ensure_ascii=False)
        print("\nwrote %d; observations now %d; environments now %d"
              % (len(add), len(rec["observations"]), len(envs)))
    else:
        print("\n(dry run -- pass --run to write)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
