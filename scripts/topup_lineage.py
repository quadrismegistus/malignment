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
from malignment.prompts import Prompts
from malignment import twp_v4 as V4
from malignment.checkpoint import Checkpoint
from malignment.runners import PRODUCER, TWPRunner, _Tee


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", help="one lineage root")
    ap.add_argument("--all-endpoints", action="store_true",
                    help="every lineage containing a declared endpoint base -- "
                         "the 50 that roster.endpoints() resolves")
    ap.add_argument("--only", choices=["slots", "cjk", "latin"], default=None,
                    help="scope pass 2 to a prompt tranche. The UNION is computed "
                         "over that tranche only; `have` stays unscoped, because a "
                         "word already measured anywhere must never be rescored.")
    ap.add_argument("--cache", action="store_true", default=True)
    a = ap.parse_args()
    T.USE_PROMPT_CACHE = bool(a.cache)

    lin = roster.lineages(ops=roster.ALIGNING)
    if a.all_endpoints:
        eps, unresolved = roster.endpoints()
        if unresolved:
            raise SystemExit("%d lineages unresolved -- resolve before sweeping"
                             % len(unresolved))
        roots = sorted({r for b in eps for r, ms in lin.items() if b in ms or b == r})
        members = sorted({m for r in roots for m in lin[r]})
        root_of = {m: r for r in roots for m in lin[r]}
    elif a.root:
        if a.root not in lin:
            raise SystemExit("%s is not a lineage root" % a.root)
        roots, members = [a.root], sorted(lin[a.root])
        root_of = {m: a.root for m in members}
    else:
        raise SystemExit("give --root or --all-endpoints")

    prompts = None
    if a.only:
        allp = {p.text: p for p in Prompts.all()}
        if a.only == "slots":
            prompts = sorted(t for t, p in allp.items()
                             if str(getattr(p, "source", "")).startswith("SLOT"))
        elif a.only == "cjk":
            prompts = sorted(t for t in allp if T.is_cjk(t))
        else:
            prompts = sorted(t for t, p in allp.items()
                             if not T.is_cjk(t)
                             and not str(getattr(p, "source", "")).startswith("SLOT"))

    #: **PASS 2 NEEDS A PASS-1 CELL.** `topup` merges onto the expand cell, so a
    #: member with none is skipped rather than run -- it would load 14 GB to
    #: discover it has nothing to merge onto. Checked from the corpus, which is
    #: also what the union is built from.
    from malignment import ch
    measured = {r["model"] for r in ch.query(
        "SELECT DISTINCT model FROM {db}.twp_cells_v4 WHERE topup=0")}
    skipped = [m for m in members if m not in measured]
    members = [m for m in members if m in measured]
    logdir = os.path.join(Checkpoint(roots[0]).dir, PRODUCER)
    os.makedirs(logdir, exist_ok=True)
    tee = _Tee(os.path.join(logdir, "topup_lineage.log"))
    sys.stdout = tee
    print("pass 2 over %d lineage(s): %d members with a pass-1 cell, %d skipped "
          "without one\n  rules=%s cache=%s tranche=%s%s"
          % (len(roots), len(members), len(skipped), V4.ADOPTED.label(),
             bool(a.cache), a.only or "ALL",
             "" if prompts is None else " (%d prompts)" % len(prompts)), flush=True)
    out = []
    try:
        for i, m in enumerate(members, 1):
            t0 = time.time()
            print("\n[%d/%d] %s" % (i, len(members), m), flush=True)
            ck = Checkpoint(m)
            os.makedirs(os.path.dirname(ck.stash(PRODUCER).path), exist_ok=True)
            r = TWPRunner(ck).topup(rules=V4.ADOPTED, root=root_of[m],
                                    prompts=prompts)
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
