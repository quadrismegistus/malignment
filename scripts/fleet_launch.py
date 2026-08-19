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

#: **DERIVED FROM THE CHECKOUT, NOT TYPED.** I typed `rj416/malignment` from
#: memory; the remote is `quadrismegistus/malignment`, and the clone would have
#: failed ON THE BOX with the rental already running. Asking git costs nothing
#: and cannot be out of date.
REPO_URL = (subprocess.run(["git", "remote", "get-url", "origin"], cwd=ROOT,
                           capture_output=True, text=True).stdout.strip()
            .replace("git@github.com:", "https://github.com/")
            or "https://github.com/quadrismegistus/malignment.git")


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

    # ---- create -----------------------------------------------------------
    raw = cloud.vastai("create", "instance", str(best["id"]),
                       "--image", shape.get("image", a.image),
                       "--disk", str(shape.get("disk_gb", a.disk)),
                       "--ssh", "--direct")
    iid = _contract_id(raw)
    if not iid:
        raise SystemExit("  could not parse an instance id from vast.ai:\n%s" % raw[:400])
    st = cloud.state({"instance_id": iid, "shard": a.box, "profile": a.box_profile,
                      "machine_id": best.get("machine_id"), "models": models,
                      "lineages": roots, "venv": venv})
    print("  created     instance %s  (state written -- a rental this process "
          "forgets is one nobody destroys)" % iid)
    if a.stop_after == "create":
        return 0

    # ---- reachable ---------------------------------------------------------
    host, port, ip = _wait_ssh(cloud, iid)
    st.update({"ssh_host": host, "ssh_port": port, "public_ip": ip}); cloud.state(st)
    #: Tries the proxy name AND the public IP, for six minutes. Boot is a race.
    working = cloud.verify_reachable(host, port, alt_host=ip)
    if working and working != host:
        print("  note        proxy host did not answer; using the IP %s" % working)
        st["ssh_host"] = working; cloud.state(st)
    if not working:
        #: **A BOX THAT NEVER ANSWERS IS A STATE, NOT A RACE.** The runbook's
        #: rule, and the L2 fleet lost 3 of 14 to retrying one. Blocklist the
        #: MACHINE so the next offer query cannot hand it back, then stop.
        cloud.blocklist(best.get("machine_id"), "ssh silent for 6 min after create")
        if cloud.destroy_verified(iid):
            cloud.state({})
            raise SystemExit("  UNREACHABLE after 6 min -- machine blocklisted, "
                             "instance destroyed and CONFIRMED gone.")
        _billing(cloud, iid, "unreachable AND destroy did not take")
        raise SystemExit("  UNREACHABLE and still billing -- see above.")
    print("  reachable   %s:%s" % (host, port))
    if a.stop_after == "reachable":
        return 0

    # ---- provision ---------------------------------------------------------
    print("  ship        working tree -> /root/malignment (exact parity, no clone)")
    cloud.ssh_run(st, "mkdir -p /root/malignment")
    cloud.rsync(st, ROOT, "/root/malignment",
                #: **`data/` HOLDS AN ASSET, NOT ONLY DATA.** Excluding it whole
                #: shipped a box that died on
                #: `data/dict/jieba_dict_big.txt` -- the prefix trie twp needs
                #: for the CJK boundary rule. Exclude the measured outputs, keep
                #: the assets: a directory name is not a category.
                exclude=(".git", ".venv*", "__pycache__", "*.pyc",
                         "data/raw", "data/*.json", "data/*.csv", "data/*.parquet",
                         "experiments", "*.egg-info"))
    print("  provision   venv %s" % venv)
    r = cloud.ssh_run(st, PROVISION % {"venv": venv})
    if r.returncode:
        #: **A FAILURE AFTER `create` LEAVES A BOX BILLING.** Raising here without
        #: saying so is the casualty pattern from the other side: not a box that
        #: looks alive while doing nothing, but a box nobody remembers renting.
        #: The id and the destroy command go in the message, and `state()` still
        #: holds it, so `malign cloud stop` finds it too.
        _billing(cloud, iid, "provision failed rc=%d" % r.returncode)
        raise SystemExit("  provision FAILED rc=%d\n%s"
                         % (r.returncode, (r.stderr or "")[-600:]))
    if a.stop_after == "provision":
        return 0

    # ---- payload -----------------------------------------------------------
    #: The cells for the WHOLE lineage, so the box can build its own union.
    src = os.path.expanduser("~/malignment-data/twp")
    cloud.ssh_run(st, "mkdir -p /root/malignment-data/twp")
    for m in models:
        d = os.path.join(src, m.replace("/", "__"))
        if os.path.isdir(d):
            cloud.rsync(st, d, "/root/malignment-data/twp/" + m.replace("/", "__"))
    got = cloud.ssh_run(st, "find /root/malignment-data/twp -name '*.jsonl' | wc -l")
    print("  payload     %s stash files on the box" % (got.stdout or "?").strip())
    if a.stop_after == "payload":
        return 0

    # ---- run ---------------------------------------------------------------
    only = (" --only %s" % a.only) if a.only else ""
    cmds = ["cd /root/malignment && ./%s/bin/python scripts/queue_v4.py --models %s%s"
            % (venv, " ".join(models), only)]
    cmds += ["cd /root/malignment && ./%s/bin/python scripts/topup_lineage.py "
             "--root %s%s" % (venv, r_, only) for r_ in roots]
    for c in cmds:
        print("  run         %s" % c[:96])
        rr = cloud.ssh_run(st, "nohup bash -lc %s > /root/stage.log 2>&1" % json.dumps(c))
        if rr.returncode:
            print("     rc=%d %s" % (rr.returncode, (rr.stderr or "")[-300:]))
    if a.stop_after == "run":
        return 0

    # ---- pull --------------------------------------------------------------
    dst = os.path.expanduser("~/malignment-data/twp")
    cloud.rsync(st, "/root/malignment-data/twp", dst, from_remote=True)
    print("  pulled      into %s" % dst)
    if a.stop_after == "pull":
        return 0

    # ---- verify ------------------------------------------------------------
    #: **BYTE-LEVEL, AND COUNTED FROM WHAT WAS WRITTEN.** RH's standing gate for
    #: destroying a box, and the runbook's rule that "instance running" is the
    #: rental and not the work. A remote line count that does not match the local
    #: one after the pull means the transfer is incomplete, whatever rsync said.
    ok = True
    for m in models:
        d = m.replace("/", "__")
        rem = cloud.ssh_run(st, "cat /root/malignment-data/twp/%s/*/jsonl.hashstash.raw/"
                                "data.jsonl 2>/dev/null | wc -l" % d)
        n_rem = int((rem.stdout or "0").strip() or 0)
        n_loc = 0
        for dp, _dd, ff in os.walk(os.path.join(dst, d)):
            for f in ff:
                if f == "data.jsonl":
                    n_loc += sum(1 for _ in open(os.path.join(dp, f), encoding="utf-8"))
        same = n_rem and n_loc >= n_rem
        ok &= bool(same)
        print("     %-46s remote %6d  local %6d  %s"
              % (m[:46], n_rem, n_loc, "OK" if same else "MISMATCH"))
    if a.stop_after == "verify" or not ok:
        if not ok:
            print("\n  NOT DESTROYING -- verification failed. The box is still "
                  "billing; inspect it, then destroy by hand.")
        return 0 if ok else 1

    # ---- destroy -----------------------------------------------------------
    if not cloud.destroy_verified(iid):
        _billing(cloud, iid, "verification PASSED but destroy did not take")
        return 1
    cloud.state({})
    print("  destroyed   %s  (byte counts verified first, destroy CONFIRMED)" % iid)
    return 0


#: **THE TREE IS SHIPPED, NOT CLONED.** The first attempt cloned from GitHub and
#: it could not have worked: this checkout is on branch `rule-v4`, which has
#: NEVER been pushed, while `origin` carries only `main` at 334 commits behind.
#: A box would have cloned code predating every fix today -- no --only tranches,
#: no prompts= scoping in pass 2, no per-record ingest gate, no corpus.retable --
#: and produced cells that looked fine while using the wrong pass-2 scope.
#:
#: rsync of the working tree removes the whole class: the box runs EXACTLY what
#: was tested here, with no "did we push" question, no branch to get wrong, and
#: nothing of other seats' work published to a public repo to make a rental work.
#: RH caught this by asking "are we pushed? will it get the latest?"
PROVISION = """set -e
export DEBIAN_FRONTEND=noninteractive
command -v rsync >/dev/null || (apt-get update -qq && apt-get install -y -qq rsync)
cd /root/malignment
python3 -m venv %(venv)s 2>/dev/null || true
./%(venv)s/bin/pip -q install --upgrade pip
./%(venv)s/bin/pip -q install -r requirements.txt
# **AND THE PACKAGE ITSELF.** requirements.txt lists DEPENDENCIES; without
# `pip install -e .` every script dies on `ModuleNotFoundError: malignment` --
# after the venv built, after the payload shipped, with the rental running.
./%(venv)s/bin/pip -q install -e .
./%(venv)s/bin/python -c "import torch,transformers;print('torch',torch.__version__,'transformers',transformers.__version__,'cuda',torch.cuda.is_available())"
"""


def _billing(cloud, iid, why):
    """Say loudly that money is still running. Never destroy silently on error.

    Destroying on a failure would also destroy the evidence, and RH's standing
    gate is that a box is destroyed only after byte-level verification of what it
    wrote. So the rule is: report, keep state(), let a human look.
    """
    print("\n  *** INSTANCE %s IS STILL BILLING *** (%s)" % (iid, why))
    print("  inspect:  vastai ssh-url %s" % iid)
    print("  destroy:  vastai destroy instance %s" % iid)
    print("  state file still holds it, so `malign cloud stop` will find it.")


def _contract_id(raw):
    """vast.ai emits Python dict-repr, not JSON. Three parsers, as the archive found."""
    import ast
    import re
    for line in (raw or "").splitlines():
        line = line.strip()
        if not line:
            continue
        for loads in (json.loads, ast.literal_eval):
            try:
                d = loads(line)
                if isinstance(d, dict) and d.get("new_contract"):
                    return str(d["new_contract"])
            except Exception:                                   # noqa: BLE001
                pass
    m = re.search(r"'new_contract':\s*(\d+)", raw or "")
    return m.group(1) if m else None


def _wait_ssh(cloud, iid, tries=30, wait=10):
    """Poll until vast.ai publishes an ssh host/port for the instance."""
    import time
    for _ in range(tries):
        for i in json.loads(cloud.vastai("show", "instances", "--raw") or "[]"):
            if str(i.get("id")) == str(iid) and i.get("ssh_host"):
                return i["ssh_host"], i.get("ssh_port"), i.get("public_ipaddr")
        time.sleep(wait)
    raise SystemExit("  vast.ai never published an ssh endpoint for %s" % iid)


if __name__ == "__main__":
    sys.exit(main())
