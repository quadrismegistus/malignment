#!/usr/bin/env python
"""Pass 2 for every member of a lineage, in one process, resumable.

    python scripts/topup_lineage.py --root m-a-p/CT-LLM-Base

## WHY THE LINEAGE AND NOT THE MODEL

The union that defines the worklist is lineage-scoped (`corpus.lineage_union`),
so running one member tells you nothing about whether the lineage closes. And
the members share nothing else -- each loads its own weights -- so this is a
convenience wrapper over `TWPRunner.topup`, not a new producer. **Three times in
one day I rebuilt a producer instead of reusing one**; this file is argument
parsing and a loop.

## RESUME IS BY KEY, NOT BY COUNT

`topup` writes one cell per prompt under a key carrying `topup=True`, and skips a
prompt that already has one. So killing this and restarting costs the cell in
flight and nothing else. Do NOT add a `--limit` and treat the remainder as done.
"""
import argparse
import os
import sys
import time

from malignment import roster, twp as T
from malignment import twp_v4 as V4
from malignment.checkpoint import Checkpoint
from malignment.runners import PRODUCER, TWPRunner, _Tee


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--cache", action="store_true", default=True)
    a = ap.parse_args()
    T.USE_PROMPT_CACHE = bool(a.cache)

    members = roster.lineages(ops=roster.ALIGNING).get(a.root)
    if not members:
        raise SystemExit("%s is not a lineage root" % a.root)
    members = sorted(members)
    logdir = os.path.join(Checkpoint(a.root).dir, PRODUCER)
    os.makedirs(logdir, exist_ok=True)
    tee = _Tee(os.path.join(logdir, "topup_lineage.log"))
    sys.stdout = tee
    print("lineage %s -- %d members, rules=%s, cache=%s"
          % (a.root, len(members), V4.ADOPTED.label(), bool(a.cache)), flush=True)
    out = []
    try:
        for i, m in enumerate(members, 1):
            t0 = time.time()
            print("\n[%d/%d] %s" % (i, len(members), m), flush=True)
            ck = Checkpoint(m)
            os.makedirs(os.path.dirname(ck.stash(PRODUCER).path), exist_ok=True)
            r = TWPRunner(ck).topup(rules=V4.ADOPTED, root=a.root)
            r["minutes"] = round((time.time() - t0) / 60.0, 1)
            out.append(r)
            print("  %s" % r, flush=True)
    finally:
        sys.stdout = tee.stream
        tee.close()
    return out


if __name__ == "__main__":
    for r in main():
        print(r)
