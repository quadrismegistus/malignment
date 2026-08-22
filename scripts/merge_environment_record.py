#!/usr/bin/env python
"""Merge the ARCHIVE's environment record into the LIVE roster. Additive, re-runnable.

    python scripts/merge_environment_record.py            # dry run, prints the diff
    python scripts/merge_environment_record.py --run

## THE DEFECT THIS EXISTS TO FIX

Model information is being written into a repo RH has declared READ-ONLY.
`scripts/record_successes.py` lives in THIS repo and its `RECORD` constant is
`~/github/malign-logits/data/model_load_environments.json` -- so every success it
derives lands in the archive. The only path out of the archive was
`ingest_environments.py`, which is a ONE-SHOT: it refuses to run once
`environments.yaml` exists, by design, because it hand-authored that file.

The result, measured 2026-08-22: the archive held 131 observations and the live
roster held 72.

## WHY MERGE AND NOT RE-INGEST

**BOTH FILES HAVE BEEN WRITTEN TO SINCE THE SPLIT, AND NEITHER IS A SUPERSET.**
Re-running the ingest -- or any copy in either direction -- destroys real work:

    archive has 78 observations the roster lacks   (record_successes.py output)
    roster  has 19 observations the archive lacks  (hand edits after 16 Aug)
    roster  has 4 environments the archive lacks   (the two rtx4090 tf-pinned
                                                    boxes and two overrides)

A copy was the first thing that came to mind and it would have silently deleted
23 hand-authored facts. The check that caught it -- comparing both directions
before writing -- is the only reason this file is a merge.

## THE KEY, AND WHY IT IS NOT (model, environment)

Observations are keyed on **(model_id, environment, outcome)**. Not on
(model_id, environment): the same model in the same environment legitimately
carries TWO outcomes -- `internlm2-chat-7b` holds `load_failed`, `ok` AND
`run_failed`, and AmberSafe failed then loaded on ONE box after two packages went
in. Collapsing on (model, environment) would silently drop one of them, which is
the exact fact `_why_not_in_models_yaml` exists to protect.

Where the same key appears on both sides with different prose, the RICHER record
wins (longer cause+fix) and the loss is REPORTED rather than swallowed. Nothing
is ever deleted: a key present on one side only is always carried through.

## WHAT ELSE COMES ACROSS

`predicted_untested` and `provisioning_lessons` have NEVER been ingested -- they
are archive-only blocks, and the second is eight items of fleet knowledge
("INSTALL requirements.txt ON THE BOX", "PIN torch >= 2.6", "AN ENVIRONMENT TAG
IS NOT A CAUSE") sitting in a repo nobody is supposed to write to.
"""
import argparse
import json
import os
import sys
from collections import OrderedDict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARCHIVE = "/Users/rj416/github/malign-logits"
SRC = os.path.join(ARCHIVE, "data", "model_load_environments.json")
DST = os.path.join(ROOT, "roster", "models", "observations.json")

#: An observation is (model x environment x outcome). See the docstring: keying
#: on (model, environment) alone collapses the seven models that carry both a
#: failure and a success, which is the file's whole point.
KEY = ("model_id", "environment", "outcome")


def key(rec):
    return tuple(str(rec.get(k) or "") for k in KEY)


def combine(field, cur, rec):
    """Keep BOTH prose bodies when they differ. Never pick one and drop the other.

    **A LONGER STRING IS NOT A BETTER RECORD.** The first version of this chose
    the longer cause+fix, and on the two CJK tokenizer entries it discarded a
    different fact each time: for Croissant it kept the 19 Aug SCOPE RULING and
    threw away the roster's character-level evidence (`他既是美丽的又是恶心的`
    -> `他是美的是心的想要`); for Teuken it kept the evidence and threw away the
    ruling. Those are not two drafts of one sentence, they are the DEFECT and the
    RULING ABOUT ITS SCOPE, and the file exists to hold both.
    """
    a = str(cur.get(field) or "").strip()
    b = str(rec.get(field) or "").strip()
    if not a:
        return b
    if not b or b in a:
        return a
    if a in b:
        return b
    return "%s || %s" % (a, b)


def merge_observations(src, dst):
    """(merged, added, kept_dst_only, conflicts) -- never deletes.

    `conflicts` carries the true provenance of the incumbent. An earlier version
    labelled every incumbent "roster", which is wrong whenever the archive holds
    TWO records under one key -- the second collides with the first ARCHIVE
    record, and the report claimed a roster hand-edit had been preserved when no
    roster record existed at all.
    """
    by, origin = OrderedDict(), {}
    for rec in dst:
        by[key(rec)] = rec
        origin[key(rec)] = "roster"
    dst_keys = set(by)
    added, conflicts = [], []
    for rec in src:
        k = key(rec)
        if k not in by:
            by[k] = rec
            origin[k] = "archive"
            added.append(rec)
            continue
        cur = by[k]
        if json.dumps(cur, sort_keys=True) == json.dumps(rec, sort_keys=True):
            continue
        merged = OrderedDict(cur)
        for field in ("cause", "fix"):
            merged[field] = combine(field, cur, rec)
        for f, v in rec.items():
            if f not in merged or not merged.get(f):
                merged[f] = v
        conflicts.append((k, origin[k], merged))
        by[k] = merged
    src_keys = {key(r) for r in src}
    return (list(by.values()), added,
            [by[k] for k in dst_keys - src_keys], conflicts)


def merge_dicts(src, dst, label, report):
    """Union. Keys on both sides that DIFFER are reported and the roster wins."""
    out = OrderedDict(dst)
    for k, v in (src or {}).items():
        if k not in out:
            out[k] = v
            report.append("  + %s: %s" % (label, k))
        elif json.dumps(out[k], sort_keys=True) != json.dumps(v, sort_keys=True):
            report.append("  ! %s: %s DIFFERS on both sides -- kept the roster's"
                          % (label, k))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true",
                    help="write. Without it, prints the diff and changes nothing.")
    a = ap.parse_args()
    if not os.path.exists(SRC):
        raise SystemExit("archive record not found: %s" % SRC)
    src = json.load(open(SRC), object_pairs_hook=OrderedDict)
    dst = json.load(open(DST), object_pairs_hook=OrderedDict)

    merged, added, dst_only, conflicts = merge_observations(
        src.get("observations") or [], dst.get("observations") or [])

    report = []
    envs = merge_dicts(src.get("environments"), dst.get("environments"),
                       "environment", report)

    out = OrderedDict(dst)
    out["environments"] = envs
    out["observations"] = merged
    #: Archive-only blocks that no ingest has ever carried across.
    for block in ("predicted_untested", "provisioning_lessons"):
        if block in src and block not in dst:
            out[block] = src[block]
            report.append("  + block: %s (never ingested before)" % block)
    out["_source"] = (
        "roster/models/observations.json is the LIVE record. Merged from "
        "malign-logits/data/model_load_environments.json by "
        "scripts/merge_environment_record.py; re-runnable and additive. The "
        "archive is read-only and must stop being a write target.")

    print("observations  archive %d | roster %d -> merged %d"
          % (len(src.get("observations") or []),
             len(dst.get("observations") or []), len(merged)))
    print("  + %d added from the archive" % len(added))
    print("  = %d roster-only records PRESERVED" % len(dst_only))
    print("  ! %d key collisions -- prose COMBINED, nothing dropped" % len(conflicts))
    for k, whose, merged in conflicts[:8]:
        print("      %s | %s | %s   (incumbent was %s)"
              % (k[0].split("/")[-1], k[1], k[2], whose))
    for line in report:
        print(line)
    print("environments  %d -> %d" % (len(dst.get("environments") or {}), len(envs)))

    if not a.run:
        print("\nDRY RUN. Nothing written. Re-run with --run.")
        return 0
    with open(DST, "w") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    print("\nwrote %s" % DST)
    return 0


if __name__ == "__main__":
    sys.exit(main())
