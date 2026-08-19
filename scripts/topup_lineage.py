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
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from venvs import venv_for  # noqa: E402

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
    ap.add_argument("--from-stash", action="store_true",
                    help="build the lineage union from the LOCAL STASH instead "
                         "of ClickHouse. What a fleet box uses: a fresh rental "
                         "has no corpus, and the first real launch died on "
                         "`FileNotFoundError: /opt/homebrew/bin/clickhouse` -- a "
                         "macOS path, on a Linux box, in pass 2.")
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
    from malignment import ch, corpus
    if a.from_stash:
        from malignment import twp_v4 as _V4
        measured = {m for m in members
                    if corpus._stash_words(m, prompts=prompts,
                                           rules=_V4.ADOPTED.label())}
    else:
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
            #: **ONE MODEL MUST NOT END THE SWEEP, AND EACH NEEDS ITS OWN VENV.**
            #: This loop used to call TWPRunner in-process, so every model ran
            #: under whichever interpreter launched the script. OLMo-2-0425-1B
            #: declares tf457, got .venv, raised `Validation error for field
            #: 'tie_word_embeddings'` -- and took the whole run down at 27 of 72,
            #: losing the 45 after it for a reason that had nothing to do with
            #: them.
            #:
            #: `queue_v4.py` solved both years ago and this file did not reuse it:
            #: spawn the per-model entry point with `venvs.venv_for(m)`, record a
            #: failure, move on. Third time this week a driver ignored the roster's
            #: per-model env and the fourth place the same lesson has had to land.
            py = os.path.join(venv_for(m), "bin", "python")
            cmd = [py, "-u", os.path.join(ROOT, "scripts", "run_v4.py"),
                   "--model", m, "--cache", "--topup", "--root", root_of[m]]
            if a.from_stash:
                cmd += ["--from-stash"]
            if a.only:
                cmd += ["--only", a.only]
            r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
            mins = round((time.time() - t0) / 60.0, 1)
            tail = [l for l in (r.stdout or "").splitlines() if l.strip()][-2:]
            if r.returncode:
                err = [l for l in (r.stderr or "").splitlines() if l.strip()][-1:]
                print("  exit=%d  %.1f min  FAILED: %s"
                      % (r.returncode, mins, (err or tail or ["?"])[-1][:110]), flush=True)
                out.append({"model": m, "venv": os.path.basename(venv_for(m)),
                            "error": (err or ["?"])[-1][:200], "minutes": mins})
                continue
            print("  exit=0  %.1f min  %s" % (mins, (tail or ["?"])[-1][:110]), flush=True)
            #: **INGEST PER ARM, RH's call.** The alternative is one ingest at the
            #: end, and it leaves the corpus behind the whole time a long sweep
            #: runs -- measured mid-run: 10 models and 1,630 cells written to disk
            #: and invisible to every consumer, including `topup_todo`, which then
            #: re-lists words that are already measured. Scoped by --source so it
            #: costs seconds, and --replace keeps it idempotent.
            d = os.path.join("malignment-data", "twp", m.replace("/", "__"), PRODUCER)
            ing = subprocess.run(
                [os.path.join(ROOT, ".venv", "bin", "malign"), "ingest",
                 "--rule-version", "4", "--run", "--replace", "--source", d],
                cwd=ROOT, capture_output=True, text=True)
            pl = [l for l in (ing.stdout or "").splitlines() if "planned" in l]
            print("  ingest: %s" % (pl[-1].strip() if pl else
                                    "FAILED rc=%d %s" % (ing.returncode,
                                    (ing.stderr or "")[-90:])), flush=True)
            out.append({"model": m, "venv": os.path.basename(venv_for(m)),
                        "minutes": mins, "tail": (tail or [""])[-1][:200]})
    finally:
        sys.stdout = tee.stream
        tee.close()
    return out


if __name__ == "__main__":
    for r in main():
        print(r)
