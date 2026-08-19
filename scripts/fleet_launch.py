#!/usr/bin/env python
"""Rent one box per shard, ship its lineages' cells, run pass 1 then pass 2.

    python scripts/fleet_launch.py --plan data/fleet_shards.json --box 4 --dry-run
    python scripts/fleet_launch.py --plan data/fleet_shards.json --box 4 --yes

## RENTING SPENDS MONEY ON RH'S OWN WORD

`--dry-run` is the default and prints the whole plan without touching vast.ai.
`--yes` is required to create anything, and the preflight below runs BEFORE the
offer is taken, not after -- a box that cannot load its models has already cost
money by the time it says so.

## WHAT SHIPS, AND WHY IT IS CELLS AND NOT A MANIFEST

RH asked whether we tell the box which twp cells we already have. We must, and it
has to be the CELLS:

    a MANIFEST ("you already have these prompts") lets a box skip pass 1 --
    and then it cannot run PASS 2 AT ALL, because the lineage union is built
    from its siblings' WORDS, not from their prompt list.

Shipping the union-relevant stash for the whole lineage is therefore not an
optimisation, it is what makes a box able to close its own lineage -- which is
the entire reason `fleet_shards.py` shards by lineage rather than by environment.
It also removes the dependency `pass1_todo`'s docstring names: a fresh rental has
no ClickHouse, so it cannot compute its own worklist. With the lineage local it
can.

The shard's cell estimate already assumes this. `fleet_shards.lineage_work()`
counts `POP - have`, so a box that re-measured what we already hold would cost
more than the plan says.

## WHAT THE BOX RUNS

    scripts/queue_v4.py  --models <shard>  --only <tranche>     pass 1
    scripts/topup_lineage.py --root <each root> --only <tranche> pass 2

In that order, because **pass 2 cannot score a prompt with no pass-1 cell** --
measured here 2026-08-19, when a cleanup pass wrote 0 cells across 10 arms for
exactly that reason. Pass 2 runs per lineage root, and every root in a shard is
whole by construction.

## WHAT THIS DOES THAT THE ARCHIVE'S LAUNCH DID NOT

The archive (`malign_logits/cloud.py`) rents a box and hands it a model list.
This one:

  - takes its roster from `fleet_shards.json`, so the population is DERIVED from
    `roster.endpoints()` rather than typed into a launch command
  - PREFLIGHTS before spending, and refuses on a BLOCKER
  - ships the lineage's cells so the box can close pass 2 locally
  - names the venv per shard, since a shard is single-venv by construction and
    hardcoding one venv for a queue is what broke Baichuan2 for an hour
"""
import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

DEFAULT_IMAGE = "pytorch/pytorch:2.4.0-cuda12.4-cudnn9-devel"


def preflight(models):
    """Refuse to spend on a shard with a BLOCKER. Returns (ok, summary)."""
    r = subprocess.run([sys.executable, os.path.join(HERE, "preflight_env.py"),
                        "--target", "cloud", "--models"] + models,
                       cwd=ROOT, capture_output=True, text=True)
    out = r.stdout or ""
    n = {}
    for k in ("BLOCKER", "CAPACITY", "UNVERIFIED", "UNTESTED", "OK"):
        for line in out.splitlines():
            if line.startswith(k):
                n[k] = int(line.split()[-1]); break
    return n.get("BLOCKER", 0) == 0, n


def payload(models, out_dir):
    """Copy each model's stash into a shippable tree. Returns (paths, bytes).

    **The whole lineage, not only the unmeasured members.** A box needs its
    siblings' WORDS to build the union that pass 2 scores against; without them
    it can run pass 1 and then nothing.
    """
    os.makedirs(out_dir, exist_ok=True)
    root = os.path.expanduser("~/malignment-data/twp")
    paths, total = [], 0
    for m in models:
        src = os.path.join(root, m.replace("/", "__"))
        if not os.path.isdir(src):
            continue
        for dirpath, _dirs, files in os.walk(src):
            for f in files:
                if not f.endswith(".jsonl"):
                    continue
                p = os.path.join(dirpath, f)
                total += os.path.getsize(p)
                paths.append(os.path.relpath(p, root))
    return paths, total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", default="data/fleet_shards.json")
    ap.add_argument("--box", type=int, required=True, help="1-based index into the plan")
    ap.add_argument("--only", choices=["slots", "cjk", "latin"], default=None)
    ap.add_argument("--image", default=DEFAULT_IMAGE)
    ap.add_argument("--disk", type=int, default=400)
    ap.add_argument("--yes", action="store_true", help="actually rent")
    ap.add_argument("--dry-run", action="store_true", default=True)
    ap.add_argument("--box-profile", default="dense",
                    help="a box shape declared in roster/environments.yaml. "
                         "cloud.box() RAISES on an unknown name rather than "
                         "defaulting -- a typo falling back to `default` would "
                         "rent an A100 for a job that asked for `dense`, and the "
                         "bill is the only place that shows.")
    ap.add_argument("--stop-after", choices=STAGES, default=None)
    ap.add_argument("--i-have-rh-authorisation", action="store_true",
                    help="asserts RH said to spend on THIS launch, not a "
                         "remembered earlier yes")
    a = ap.parse_args()

    plan = json.load(open(os.path.join(ROOT, a.plan)))
    boxes = plan["boxes"]
    if not 1 <= a.box <= len(boxes):
        raise SystemExit("--box must be 1..%d" % len(boxes))
    b = boxes[a.box - 1]
    models, roots, venv = sorted(b["models"]), b["lineages"], b["venv"]

    print("SHARD %d of %d" % (a.box, len(boxes)))
    print("  venv      %s" % venv)
    print("  lineages  %d: %s" % (len(roots), ", ".join(r.split("/")[-1] for r in roots)))
    print("  models    %d" % len(models))
    print("  cells     %s  (~%.1f h @0.8s)" % (format(b["cells"], ","), b["cells"] * .8 / 3600))

    ok, n = preflight(models)
    print("  preflight %s" % " ".join("%s=%d" % (k, v) for k, v in sorted(n.items())))
    if not ok:
        raise SystemExit("  REFUSING: this shard has a BLOCKER. Renting a box that "
                         "cannot load its models costs money to learn what the "
                         "preflight already knows.")

    paths, nbytes = payload(models, "/tmp/fleet_payload_%d" % a.box)
    print("  payload   %d stash files, %.1f MB  (the WHOLE lineage -- pass 2 needs "
          "siblings' words, not their prompt list)" % (len(paths), nbytes / 1e6))

    cmds = [
        "python scripts/queue_v4.py --models %s%s"
        % (" ".join(models[:3]) + (" ..." if len(models) > 3 else ""),
           " --only %s" % a.only if a.only else ""),
    ] + ["python scripts/topup_lineage.py --root %s%s"
         % (r, " --only %s" % a.only if a.only else "") for r in roots[:2]]
    print("  will run:")
    for c in cmds:
        print("      %s" % c)
    if len(roots) > 2:
        print("      ... and %d more topup roots" % (len(roots) - 2))

    if not a.yes:
        print("\n  DRY RUN -- nothing rented. Pass --yes to spend.")
        return 0

    return execute(b, models, roots, venv, a)


#: ## THE STAGES, AND WHY EACH IS SEPARATELY STOPPABLE
#:
#: `--stop-after` exists because every stage below has failed on some fleet and
#: the runbook's casualty pattern is a box that LOOKS alive: "instance running"
#: is the rental, not the work. Being able to stop at `reachable` or `payload`
#: means the expensive stages are entered only after the cheap ones are seen to
#: work, on a real box, once.
STAGES = ("offer", "create", "reachable", "provision", "payload", "run", "pull",
          "verify", "destroy")


def execute(b, models, roots, venv, a):
    from malignment import cloud
    shape = cloud.box(a.box_profile)
    print("\n  box profile %s: %s" % (a.box_profile, str(shape.get("description"))[:70]))

    offers = cloud.offers(a.box_profile, limit=5)
    if not offers:
        raise SystemExit("  no offers matched profile %r" % a.box_profile)
    best = offers[0]
    print("  best offer  #%s  %sx %s  $%s/hr  %s"
          % (best.get("id"), best.get("num_gpus"), best.get("gpu_name"),
             best.get("dph_total"), best.get("geolocation")))
    est = float(best.get("dph_total") or 0) * (b["cells"] * .8 / 3600)
    print("  estimated   $%.2f for %.1f h of compute (EXCLUDES download time, "
          "which dominates on a fresh box)" % (est, b["cells"] * .8 / 3600))
    if a.stop_after == "offer":
        print("\n  STOPPED AFTER offer -- nothing rented.")
        return 0

    #: **THE CONFIRMATION IS HERE AND NOT EARLIER.** Everything above is free;
    #: the next call bills. RH's standing rule is that cloud spend begins on his
    #: own word, so `--yes` alone does not suffice for the first box of a
    #: campaign -- it is the flag that ALLOWS this prompt, not one that skips it.
    if not a.i_have_rh_authorisation:
        raise SystemExit(
            "  REFUSING to create an instance.\n"
            "  --yes allows the attempt; --i-have-rh-authorisation asserts that RH\n"
            "  said to spend on THIS launch. Two flags because a single one gets\n"
            "  copied from a previous command line, and the runbook's rule is that\n"
            "  renting starts on RH's own word rather than on a remembered yes.")

    raise SystemExit(
        "  create/provision/payload/run/pull/verify/destroy are NOT wired yet.\n"
        "  Offer selection and costing above are live and free. The remaining\n"
        "  stages touch money and a remote filesystem and land next, so that this\n"
        "  commit can be read without any of them having run.")


if __name__ == "__main__":
    sys.exit(main())
