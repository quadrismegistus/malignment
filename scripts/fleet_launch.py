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

import box_guard                               # noqa: E402
from venvs import venv_for                     # noqa: E402
import cards                                   # noqa: E402
from fleet_shards import seconds               # noqa: E402

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


def resume(iid):
    """Bring a STOPPED-then-STARTED box back to work. Idempotent.

    **A vast.ai stop/start reverts the container, and three things break every
    time.** Observed on all three boxes on 2026-08-20, in the same order:

      1. `hf_config.pth` is BACK in both venvs, so downloads silently go to
         http://117.175.104.83:8081 again. The purge in PROVISION runs once; a
         restart undoes it. Three for three -- a property of the restart, not
         bad luck.
      2. `tmux` does not survive, so the box comes back RUNNING and IDLE,
         billing while doing nothing, with no session and no error.
      3. The ssh host and port can CHANGE, so the stored state points at a
         closed door and every check reads as unreachable.

    I fixed each of those by hand, per box, three times. The purge belonged
    wherever work STARTS rather than only where a box is first provisioned --
    the same error as putting the VRAM guard at launch when the thing that
    repeats is run.sh.
    """
    import json as _j
    from malignment import cloud
    st = cloud.states().get(str(iid))
    if not st:
        raise SystemExit("  %s is not tracked" % iid)
    api = {str(i.get("id")): i for i in
           _j.loads(cloud.vastai("show", "instances", "--raw") or "[]")}.get(str(iid), {})
    if api.get("actual_status") != "running":
        print("  %s is %s -- asking it to start" % (iid, api.get("actual_status")))
        print("  ", (cloud.vastai("start", "instance", str(iid)) or "").strip()[:70])
        return 1
    if api.get("ssh_host") and (api["ssh_host"] != st.get("ssh_host")
                                or api.get("ssh_port") != st.get("ssh_port")):
        st["ssh_host"], st["ssh_port"] = api["ssh_host"], api["ssh_port"]
        cloud.state(st)
        print("  ssh refreshed -> %s:%s" % (st["ssh_host"], st["ssh_port"]))
    venv = st["venv"]
    r = cloud.ssh_run(st, "find /root/malignment /opt/uv /usr/local/lib /usr/lib "
                          "-name hf_config.pth -delete 2>/dev/null; "
                          "rm -f /opt/uv/cache/archive-v0/*/hf_config.pth 2>/dev/null; "
                          "cd /root/malignment && ./%s/bin/python -c "
                          "'import huggingface_hub.constants as C; print(C.ENDPOINT)'"
                      % venv)
    ep = (r.stdout or "").strip().splitlines()[-1:] or ["?"]
    print("  endpoint  %s" % ep[0])
    if "huggingface.co" not in ep[0]:
        raise SystemExit("  endpoint still hijacked -- not restarting work")
    #: **ASK WHETHER WORK IS RUNNING, NOT WHETHER A SESSION IS NAMED `fleet`.**
    #: The first version tested `tmux has-session -t fleet`, and on box 48182910
    #: the work was running under a session named `baichuan` -- so resume() read
    #: "idle" and started a SECOND queue against the same stash. This function's
    #: own docstring warns that two queues on one stash is the thing to avoid; the
    #: check I wrote could not see it.
    #:
    #: A producer process is the condition. `pgrep -f` on the script names catches
    #: the work whatever the session is called, and `-c` counts rather than
    #: matching, so the checker's own ssh command line cannot be the hit.
    n = cloud.ssh_run(st, "pgrep -fc 'scripts/(run_v4|queue_v4|topup_lineage)\\.py'"
                          " 2>/dev/null || true")
    busy = int((n.stdout or "0").strip() or 0) > 0
    if busy:
        print("  already working -- left alone")
        return 0
    cloud.ssh_run(st, "rm -f /root/DONE /root/RECOVER_DONE; "
                      "tmux new-session -d -s fleet 'bash /root/run.sh'")
    out = cloud.ssh_run(st, "sleep 2; tmux ls").stdout or ""
    print("  restarted %s" % out.strip()[:70])
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", default="data/fleet_shards.json")
    ap.add_argument("--box", type=int, help="1-based index into the plan")
    ap.add_argument("--resume", metavar="INSTANCE_ID",
                    help="bring a stopped-then-started box back to work: purge "
                         "the re-injected HF mirror, refresh ssh host/port, and "
                         "restart run.sh if nothing is running. A vast.ai restart "
                         "breaks all three, every time.")
    ap.add_argument("--only", choices=["slots", "cjk", "latin"], default=None)
    ap.add_argument("--image", default=DEFAULT_IMAGE)
    ap.add_argument("--disk", type=int, default=0,
                    help="GB of disk to rent. 0 = SIZED FROM THE SHARD: ~15 GB per "
                         "7B checkpoint plus headroom, because nothing purges "
                         "weights between models and a 150 GB box died at model "
                         "11 of 11 with `No space left on device`.")
    ap.add_argument("--gb-per-model", type=float, default=15.0,
                    help="disk each checkpoint's weights occupy. 15 is measured: "
                         "the 7B arms on box 48153389 were 13.9-14.0 GB each.")
    ap.add_argument("--yes", action="store_true", help="actually rent")
    ap.add_argument("--dry-run", action="store_true", default=True)
    ap.add_argument("--box-profile", default=None,
                    help="omit to DERIVE it from the shard's biggest model. "
                         "roster/environments.yaml already declares `big80` (one "
                         "80GB card, 'for the 32B pair') and `twogpu` (2x80GB, "
                         "'for the 70B pair ~140GB bf16 each') -- written for "
                         "exactly this and never used, because this flag defaulted "
                         "to `dense` for all twelve shards and a 32B arm died with "
                         "CUDA OOM on a 4090 after a 9.6-minute download.")
    ap.add_argument("--box-profile-legacy-default", default="dense",
                    help="a box shape declared in roster/environments.yaml. "
                         "cloud.box() RAISES on an unknown name rather than "
                         "defaulting -- a typo falling back to `default` would "
                         "rent an A100 for a job that asked for `dense`, and the "
                         "bill is the only place that shows.")
    ap.add_argument("--stop-after", choices=STAGES, default=None)
    ap.add_argument("--poll", type=int, default=120,
                    help="seconds between health polls once the run is detached")
    ap.add_argument("--stall-min", type=float, default=25.0,
                    help="minutes with NO new cells written, tmux still up, before "
                         "the box is called stalled. Must exceed the slowest cold "
                         "model load in the shard, or a normal load reads as a "
                         "stall -- the one number here that is a judgement.")
    ap.add_argument("--pull-every", type=int, default=5,
                    help="pull the cells home every N polls (0 disables). At the "
                         "default poll of 180s that is every 15 min, so a box "
                         "lost mid-run costs at most that much work rather than "
                         "the whole shard.")
    ap.add_argument("--max-hours", type=float, default=6.0)
    ap.add_argument("--models", nargs="*", default=None,
                    help="explicit model ids instead of --plan/--box. For a "
                         "declared population that is not a shard of the 144 -- "
                         "e.g. roster.framed('ladder'). Must share one venv.")
    ap.add_argument("--frame", choices=["chat", "prefill"], default=None,
                    help="measure the shard under a CHAT TEMPLATE. Framed cells "
                         "carry frame=<this> in twp_cells_v4 and are excluded "
                         "from the _best views, which return raw only.")
    ap.add_argument("--system", default=None,
                    help="explicit system message. OMIT for the template's own "
                         "default; '' forces an empty block and is NOT the same "
                         "thing (docs/prefill.md).")
    ap.add_argument("--user-msg", default=None)
    ap.add_argument("--prompts-file", default=None,
                    help="one prompt per line, shipped to the box. Without it "
                         "each model measures the pairing population.")
    ap.add_argument("--i-know-the-record-is-broken", action="store_true",
                    help="rent even though check_record.py fails. For an "
                         "emergency, not for bookkeeping you mean to do later: "
                         "the shard is PLANNED from the record this flag is "
                         "ignoring. Exists because a gate with no override gets "
                         "commented out instead of overridden.")
    ap.add_argument("--i-have-rh-authorisation", action="store_true",
                    help="asserts RH said to spend on THIS launch, not a "
                         "remembered earlier yes")
    ap.add_argument("--no-ssm-kernels", action="store_true",
                    help="do NOT install mamba-ssm/causal-conv1d even where the "
                         "roster declares profile ssm. A DELIBERATE CONTROL, not "
                         "a fix: the hypothesis it was built for (that kernels "
                         "caused Falcon-H1-7B's empty cells) was tested and is "
                         "FALSE -- the cause was fp16. Kernels are 26x on that "
                         "model. Do not pass this to make a model work.")
    a = ap.parse_args()
    if a.resume:
        return resume(a.resume)
    #: **AN EXPLICIT LIST IS A SHARD OF ONE, NOT A SECOND CODE PATH.** A pilot
    #: measures a DECLARED population -- `roster.framed("ladder")` -- which is
    #: 16 models over 7 lineages and has nothing to do with how `fleet_shards`
    #: packs the 144 by seconds. Rather than teach the packer a second
    #: population, the list is turned into the same shape a plan entry has, so
    #: every gate below it (preflight, record, cards, disk, VRAM, run.sh) runs
    #: unchanged and untested code is not what stands between us and a rental.
    if a.models:
        from malignment import roster as _r0
        _lin0 = _r0.lineages(ops=_r0.ALIGNING)
        models = sorted(set(a.models))
        unknown = [m for m in models if not any(m in ms for ms in _lin0.values())]
        if unknown:
            raise SystemExit("not in any lineage: %s" % ", ".join(unknown))
        roots = sorted({r for r, ms in _lin0.items() if any(m in ms for m in models)})
        venvs = {os.path.basename(venv_for(m)) for m in models}
        if len(venvs) != 1:
            #: Same rule `fleet_shards.pack` enforces: never silently split.
            raise SystemExit("that list spans %s -- one box, one venv. Split it."
                             % sorted(venvs))
        venv = venvs.pop()
        #: **`per` IS THE TIME ESTIMATE'S INPUT, SO IT MUST BE REAL.** A plan
        #: entry carries measured per-model cell counts; a zero here would price
        #: the shard at zero hours and print a confident 0.0 h beside a rental.
        #: With `--prompts-file` every model measures the same declared set, so
        #: the count is the file's line count.
        _n = 0
        if a.prompts_file:
            _pf0 = os.path.abspath(os.path.expanduser(a.prompts_file))
            if os.path.exists(_pf0):
                _n = sum(1 for ln in open(_pf0) if ln.strip())
        if not _n:
            raise SystemExit(
                "--models needs --prompts-file: without a declared prompt set "
                "the per-model cell count is unknown and the shard cannot be "
                "priced or its ETA reported.")
        b = {"models": models, "lineages": roots, "venv": venv,
             "per": {m: _n for m in models}, "cells": _n * len(models)}
        #: Everything downstream indexes scratch paths and state by `--box`;
        #: an explicit list is box 0 so those stay one namespace rather than
        #: growing a None branch each.
        a.box = a.box or 0
        print("EXPLICIT LIST  %d models over %d lineages (box %d)"
              % (len(models), len(roots), a.box))
    else:
        if not a.box:
            raise SystemExit("--box is required unless --resume or --models is given")
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
    #: Priced at PER-MODEL recorded rates, and the guess count is on the same
    #: line as the estimate -- see fleet_shards.seconds.
    b_per = b.get("per") or {m: b["cells"] // max(1, len(models)) for m in models}
    est_s, guessed = seconds(b_per, "cuda")
    #: **DISK IS A RESOURCE THE PLANNER NEVER LOOKED AT.** `fleet_shards` packs by
    #: SECONDS; bytes are invisible to it. Box 48153389 held 11 checkpoints on the
    #: `dense` profile's 150 GB, filled at ~133 GB of hub cache, and then: model 11
    #: could not download, pass 2 crashed OPENING ITS LOG FILE, the run ended
    #: without its DONE sentinel, and the recovery session waited forever on a
    #: sentinel that would never come. A deadlock caused by a full disk two stages
    #: upstream. Shards in this plan carry up to 22 models.
    #: Sized by the LARGEST LINEAGE, not by every model, because pass 1 and pass 2
    #: now run per lineage with a cache wipe between -- so only one lineage's
    #: weights are ever live. Box 11: 370 GB -> 85 GB.
    from malignment import roster as _r1
    _l1 = _r1.lineages(ops=_r1.ALIGNING)
    _biggest = max([len([m for m in _l1.get(r_, []) if m in models])
                    for r_ in roots] or [len(models)])
    #: **MEASURED BYTES BEAT A UNIFORM GUESS, AND fp32 IS THE REASON.**
    #: `--gb-per-model` is a flat 15 GB. Fifteen roster checkpoints ship fp32 --
    #: TWICE the bytes per parameter -- and two of them are the 32B arms at
    #: **129 GB each**. Sizing a lineage of those at 15 GB apiece under-provisions
    #: the disk by an order of magnitude, and the failure lands mid-download with
    #: the box already rented. `requirements.json` carries `params_b` and
    #: `storage_dtype` for all 160, so the real figure costs nothing.
    _W = {"float32": 4, "bfloat16": 2, "float16": 2}

    def _gb(m):
        r = _reqs().get(m) or {}
        pb, dt = r.get("params_b"), r.get("storage_dtype")
        return pb * _W.get(dt, 2) if pb else a.gb_per_model

    _lin_gb = max([sum(_gb(m) for m in _l1.get(r_, []) if m in models)
                   for r_ in roots] or [sum(_gb(m) for m in models)])
    need_gb = int(_lin_gb + 40)
    _flat = int(_biggest * a.gb_per_model + 40)
    if need_gb > _flat:
        print("  disk NOTE   measured weights need %d GB where the flat "
              "%.0f GB/model guess says %d -- fp32 on this shard"
              % (need_gb, a.gb_per_model, _flat))
    disk_gb = a.disk or need_gb
    #: **CARRIED ON THE ARGS, BECAUSE `execute()` IS A DIFFERENT SCOPE.** Computed
    #: here and referenced there, it raised `NameError: disk_gb is not defined` at
    #: the moment of building the create call -- after the offer was taken and
    #: printed, which reads like a launch about to happen. The DRY RUN cannot catch
    #: it: dry run returns before `execute()` is ever entered, so this whole
    #: function is untested by the check that is supposed to make launching safe.
    a.disk_gb = disk_gb
    print("  disk      %d GB for the largest lineage (%d models x %.0f GB + 40)%s"
          % (disk_gb, _biggest, a.gb_per_model,
             "" if not a.disk else "  [OVERRIDDEN to %d]" % a.disk))
    print("  cells     %s  (~%.1f h; %d of %d models have a recorded rate)"
          % (format(b["cells"], ","), est_s / 3600,
             len(models) - len(guessed), len(models)))

    #: **DERIVED FROM THE SHARD, NOT DEFAULTED.** fp16 bytes = params x 2, and the
    #: thresholds are the cards the roster already declares, so this is a lookup
    #: rather than a judgement.
    if not a.box_profile:
        a.box_profile, _vram, _gpus, _pb = shard_profile(models)
        print("  profile   %s  (biggest model %.1fB -> the roster's sizing rule "
              "says %d GB x %d GPU)" % (a.box_profile, _pb, _vram, _gpus))
    #: **THE RECORD GATE RUNS HERE, BECAUSE A GATE NOBODY RUNS IS NOT A GATE.**
    #: `check_record.py` has nine assertions and exits non-zero, and until now
    #: the only thing making it run was a human remembering to -- which is the
    #: exact failure mode the whole record exists to fix. It fails on a derived
    #: file older than its source, a card the fleet rents but has not declared,
    #: a measured (model x environment) with no observation, and five more.
    #: Every one of those makes THIS decision worse: the shard is planned from
    #: `requirements.json`, and a stale requirements file plans the wrong boxes.
    #:
    #: `--i-know-the-record-is-broken` exists because a legitimate emergency
    #: should not be blocked by bookkeeping, and because a gate with no override
    #: gets commented out rather than overridden.
    _rc = subprocess.run([sys.executable, os.path.join(HERE, "check_record.py")],
                         capture_output=True, text=True)
    if _rc.returncode:
        _bad = [ln for ln in (_rc.stdout or "").splitlines()
                if ln.startswith(("FAIL", "ERROR"))]
        print("  record    %d check(s) FAILING:" % len(_bad))
        for ln in _bad:
            print("     %s" % ln)
        if not a.i_know_the_record_is_broken:
            raise SystemExit(
                "  REFUSING: the environment record does not pass its own "
                "checks, and this shard is planned FROM that record. Run\n"
                "    python scripts/check_record.py\n"
                "  and clear it -- a stale derived file names the producer that "
                "fixes it. Override with --i-know-the-record-is-broken.")
        print("  record    OVERRIDDEN by --i-know-the-record-is-broken")
    else:
        print("  record    check_record.py passes")
    ok, n = preflight(models)
    print("  preflight %s" % " ".join("%s=%d" % (k, v) for k, v in sorted(n.items())))
    if not ok:
        raise SystemExit("  REFUSING: this shard has a BLOCKER. Renting a box that "
                         "cannot load its models costs money to learn what the "
                         "preflight already knows.")

    paths, nbytes = payload(models, "/tmp/fleet_payload_%d" % a.box)
    print("  payload   %d stash files, %.1f MB  (the WHOLE lineage -- pass 2 needs "
          "siblings' words, not their prompt list)" % (len(paths), nbytes / 1e6))

    #: **THE PREVIEW IS BUILT THE SAME WAY THE REAL COMMANDS ARE.** It used to be
    #: composed independently, so after the run order changed to per-lineage the
    #: dry run still advertised the old shape -- an operator reading it would have
    #: been told something the box would not do. Exactly the defect that made
    #: `--box N` mean two different shards, and the same fix: derive both from one
    #: place rather than describing one in terms of the other.
    only_s = " --only %s" % a.only if a.only else ""
    #: **AND THE FRAME FLAGS AND THE TOPUP SKIP MUST BE HERE TOO.** Adding
    #: `--frame` broke the parity this comment was written to protect: the
    #: preview kept advertising `topup_lineage` on a framed run that deliberately
    #: skips it, and omitted the frame flags entirely. An operator reading it
    #: would have been told the box does pass 2 with no template -- while the box
    #: does pass 1 with one. Same defect, one release later, which is what a
    #: parity comment cannot prevent on its own.
    _preview_extra = only_s
    if a.frame:
        _preview_extra += " --frame %s" % a.frame
    if a.system is not None:
        _preview_extra += " --system %r" % a.system
    if a.prompts_file:
        _preview_extra += " --prompts-file /root/prompts.txt"
    steps = 2 if a.frame else 3
    print("  will run, PER LINEAGE (%s, then wipe the weights):"
          % ("pass 1 ONLY -- no topup under a frame" if a.frame
             else "pass 1 then pass 2"))
    shown = 0
    for r in roots:
        mem = [m for m in _l1.get(r, []) if m in models]
        if not mem:
            continue
        shown += 1
        if shown > 2:
            continue
        print("      queue_v4.py --models %s%s   [%d model(s)]"
              % (" ".join(x.split("/")[-1] for x in mem[:3])
                 + (" ..." if len(mem) > 3 else ""), _preview_extra, len(mem)))
        if not a.frame:
            print("      topup_lineage.py --root %s --from-stash%s" % (r, only_s))
        print("      rm -rf ~/.cache/huggingface/hub/models--*")
    if shown > 2:
        print("      ... and %d more lineage(s), same %d steps each"
              % (shown - 2, steps))

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

    hrs = seconds(b.get("per") or {m: b["cells"] // max(1, len(models))
                                   for m in models}, "cuda")[0] / 3600
    #: **EVERY MODEL IS FETCHED ONCE**, because the run script wipes the hub
    #: between lineages. So the shard's download is its model count x the same
    #: per-checkpoint figure `--disk` is sized from -- not a guess, the number
    #: already trusted enough to buy disk with.
    dl_gb = a.gb_per_model * len(models)
    offers = cloud.offers(a.box_profile, limit=5, gb=dl_gb, hours=hrs)
    if not offers:
        raise SystemExit("  no offers matched profile %r" % a.box_profile)
    #: **bfloat16 NEEDS AMPERE, AND `dense` HAS NO CARD FILTER.** Selection for
    #: the dense roster is deliberately by CAPABILITY (VRAM, link, disk) with no
    #: `gpu_name`, offers sort by price, and the cheapest 48 GB board is
    #: routinely a Turing `Q RTX 8000` (cc 7.5). Twelve models declare bf16 and
    #: none had landed on Turing -- by luck, not by rule. Baichuan2 shows the
    #: failure: it auto-selects bf16 and dies at LOAD on a Quadro RTX 8000,
    #: after the download is paid for, with a dtype error naming neither the
    #: card nor the reason. Unknown cards are refused, not allowed.
    _bf = sorted({m for m in models
                  if (_reqs().get(m) or {}).get("compute_dtype") == "bfloat16"})
    if _bf:
        keep = [o for o in offers if cards.ok_for(o.get("gpu_name"), "bfloat16")[0]]
        dropped = [o for o in offers if o not in keep]
        for o in dropped:
            print("  card SKIP   #%s %s -- %s"
                  % (o.get("id"), o.get("gpu_name"),
                     cards.ok_for(o.get("gpu_name"), "bfloat16")[1]))
        if not keep:
            raise SystemExit(
                "  no offer on this profile can run bfloat16, which %d model(s) "
                "on this shard require: %s\n  Re-search, or split them onto an "
                "Ampere+ box. Renting anyway buys a load failure after the "
                "download." % (len(_bf), ", ".join(x.split("/")[-1] for x in _bf)))
        offers = keep
    best = offers[0]
    print("  best offer  #%s  %sx %s  $%s/hr  %s"
          % (best.get("id"), best.get("num_gpus"), best.get("gpu_name"),
             best.get("dph_total"), best.get("geolocation")))
    egress = float(best.get("inet_down_cost") or 0) * dl_gb
    est = float(best.get("dph_total") or 0) * hrs
    print("  estimated   $%.2f = $%.2f compute (%.1f h) + $%.2f egress "
          "(%d models x %g GB @ $%.5f/GB)"
          % (est + egress, est, hrs, egress, len(models), a.gb_per_model,
             float(best.get("inet_down_cost") or 0)))
    #: Ranked on the SUM, so say what was rejected and why -- an offer $0.10/hr
    #: cheaper that loses $8 on egress must not look like the one we passed up.
    _dph = sorted(offers, key=lambda o: float(o.get("dph_total") or 0))[0]
    if _dph.get("id") != best.get("id"):
        print("  NOT the cheapest $/hr: #%s at $%s/hr would cost $%.2f total "
              "($%.5f/GB egress)"
              % (_dph.get("id"), _dph.get("dph_total"),
                 float(_dph.get("dph_total") or 0) * hrs
                 + float(_dph.get("inet_down_cost") or 0) * dl_gb,
                 float(_dph.get("inet_down_cost") or 0)))
    #: **REFUSE BEFORE CREATE, NOT AFTER A 9.6-MINUTE DOWNLOAD.**
    #: Reported here, DROPPED at the run-script stage below. Refusing the whole
    #: shard would have thrown away the four viable lineages that shared box 12
    #: with the 32B quartet.
    _big = too_big_for(best, models)
    if _big:
        print("  VRAM      %d model(s) exceed this offer's %s x %.0f GB and will "
              "be OMITTED from the run:"
              % (len(_big), best.get("num_gpus"),
                 float(best.get("gpu_ram") or 0) / 1024.0))
        for _m, (_need, _av) in sorted(_big.items()):
            print("     %-46s needs ~%.0f GB, usable ~%.0f GB" % (_m[:46], _need, _av))
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
                       #: The SHARD's need wins over the profile's default: a
                       #: profile is a box shape, and how many checkpoints land on
                       #: it is not something the profile can know.
                       "--disk", str(max(int(shape.get("disk_gb", 0) or 0),
                                         getattr(a, "disk_gb", 0) or 400)),
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
            cloud.state(forget=iid)
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
    #: **THE PROMPT SET IS SHIPPED, NOT NAMED.** `--prompts-file` puts
    #: `/root/prompts.txt` in the run command, so the file has to arrive or every
    #: stage dies on a path that does not exist -- after the box is rented and
    #: the weights are pulled. Sent before the tree so a failure here costs
    #: nothing.
    if a.prompts_file:
        _pf = os.path.abspath(os.path.expanduser(a.prompts_file))
        if not os.path.exists(_pf):
            raise SystemExit("  --prompts-file %s does not exist" % _pf)
        _n = sum(1 for ln in open(_pf) if ln.strip())
        pr = cloud.rsync(st, _pf, "/root/prompts.txt", is_file=True)
        if pr.returncode:
            raise SystemExit("  could not ship the prompt file (rc=%d) -- "
                             "refusing to launch a run whose every stage would "
                             "fail on a missing path" % pr.returncode)
        print("  prompts     %d shipped -> /root/prompts.txt" % _n)
    cloud.rsync(st, ROOT, "/root/malignment",
                #: **`data/` HOLDS AN ASSET, NOT ONLY DATA.** Excluding it whole
                #: shipped a box that died on
                #: `data/dict/jieba_dict_big.txt` -- the prefix trie twp needs
                #: for the CJK boundary rule. Exclude the measured outputs, keep
                #: the assets: a directory name is not a category.
                exclude=(".git", ".venv*", "__pycache__", "*.pyc",
                         "data/raw", "data/*.json", "data/*.csv", "data/*.parquet",
                         "experiments", "*.egg-info"))
    # ---- token (SHIPPED BEFORE PROVISION) -----------------------------------
    #: **BEFORE provision, because provision READS it.** Ordered after, the
    #: token file did not exist when `hfenv.sh` was written and sourced -- and
    #: that file's `[ -f token ] && export ...` returns 1 when absent, which
    #: under `set -e` aborted the whole provision with rc=1. Two of my own lines
    #: disagreeing about ordering, and the symptom was a bare `provision FAILED
    #: rc=1` with empty stderr.
    #:
    #: The `&&` is now an `if`, so the ordering and the guard are independently
    #: correct rather than jointly.
    tok_path = os.path.expanduser("~/.cache/huggingface/token")
    if not os.path.exists(tok_path):
        env_tok = (os.environ.get("HF_TOKEN")
                   or os.environ.get("HUGGING_FACE_HUB_TOKEN"))
        if env_tok:
            import stat
            os.makedirs(os.path.dirname(tok_path), exist_ok=True)
            with open(tok_path, "w") as fh:
                fh.write(env_tok.strip())
            os.chmod(tok_path, stat.S_IRUSR | stat.S_IWUSR)
            print("  token       wrote %s from the environment" % tok_path)
    if os.path.exists(tok_path):
        cloud.ssh_run(st, "mkdir -p /root/.cache/huggingface")
        #: is_file=True, and the RETURN CODE IS CHECKED. The first version did
        #: neither: rsync failed, the destination became a directory, and this
        #: line printed "shipped" anyway -- an operation reporting success while
        #: doing the opposite of its name.
        rr = cloud.rsync(st, tok_path, "/root/.cache/huggingface/token",
                         is_file=True)
        chk = cloud.ssh_run(st, "test -f /root/.cache/huggingface/token && "
                                "wc -c < /root/.cache/huggingface/token")
        if rr.returncode or chk.returncode:
            _billing(cloud, iid, "token copy failed rc=%d/%d"
                     % (rr.returncode, chk.returncode))
            raise SystemExit("  token did NOT ship. Box kept for inspection.")
        cloud.ssh_run(st, "chmod 600 /root/.cache/huggingface/token")
        print("  token       shipped, %s bytes on the box"
              % (chk.stdout or "?").strip())
    else:
        from preflight_env import gated as _gated
        print("  token       NO ~/.cache/huggingface/token and none in env -- "
              "%d gated model(s) in this shard WILL fail" % len(_gated(models)))

    print("  provision   venv %s" % venv)
    #: What THIS checkout's venv of the same name actually has -- asked of the
    #: interpreter, not read from a requirements file, because the file is what
    #: was wrong.
    want = ""
    try:
        want = subprocess.run(
            [os.path.join(ROOT, venv, "bin", "python"), "-c",
             "import transformers;print(transformers.__version__)"],
            capture_output=True, text=True).stdout.strip()
    except Exception:                                           # noqa: BLE001
        pass
    print("  provision   %s must carry transformers %s" % (venv, want or "(unknown)"))
    #: Derived from the roster, per model in THIS shard.
    from malignment import roster as _ros
    _nodes = _ros.load()["nodes"]
    _ssm = [m for m in models
            if (_nodes.get(m, {}).get("env") or {}).get("profile") == "ssm"]
    #: **`--no-ssm-kernels` WAS BUILT ON A HYPOTHESIS THAT IS FALSE. IT IS KEPT
    #: AS A CONTROL AND MUST NOT BE USED AS A FIX.**
    #:
    #: The observation was real: `Falcon-H1-7B` wrote 2,981 cells containing NO
    #: WORDS -- residual.tail == 1.0 on every cell, zero word rows -- on a box
    #: where the kernels were active, while its 1.5B sibling on the SAME box in
    #: the SAME run was healthy. Docket [6486] [6487] [6488], 2026-08-21.
    #:
    #: The inference from it was wrong. Kernels were not the variable; **dtype
    #: was**. The two boxes differed in fp16 vs bf16 as well as in kernels, and
    #: the arm that finally succeeded ran WITH kernels under bf16:
    #: 2,981 cells, 355,005 word rows, 0 dead, tail max 0.7506 -- identical to
    #: the 2026-08-03 v3 run. `tail == 1.0` means `sel` was empty, and NaN logits
    #: produce exactly that because every comparison against NaN is False.
    #:
    #: And the flag then cost what it was meant to save. Carried forward after
    #: its hypothesis had already died, it ran an A100 arm at **21.2 s/cell**
    #: where kernels give **0.8** -- 26x, on the model the flag was invented for.
    #:
    #: Kept because a deliberate kernel-free run is a legitimate control and the
    #: original finding should be reproducible rather than inferred. Not kept as
    #: a remedy: a model writing empty cells is a DTYPE question, and
    #: `runners.compute_dtype` reads the roster's `env.dtype` for it.
    if a.no_ssm_kernels and _ssm:
        print("  provision   --no-ssm-kernels: NOT installing mamba kernels for "
              "%d model(s) that declare profile ssm: %s"
              % (len(_ssm), ", ".join(x.split("/")[-1] for x in _ssm)))
        _ssm = []
    elif _ssm:
        print("  provision   %d model(s) declare profile ssm -> installing mamba "
              "kernels: %s" % (len(_ssm), ", ".join(x.split("/")[-1] for x in _ssm)))
    r = cloud.ssh_run(st, PROVISION % {
        "venv": venv, "want": want,
        "ssm": (SSM_KERNELS % {"venv": venv}) if _ssm else ""})
    if r.returncode == 5:
        #: Kernels absent. OURS, not the host's -- never blocklist for it.
        _billing(cloud, iid, "SSM kernels failed to install (rc=5)")
        raise SystemExit("  mamba kernels missing -- this shard would run ~200x "
                         "slow and look healthy doing it. Box kept.\n%s"
                         % (r.stdout or "")[-400:])
    if r.returncode == 4:
        #: The venv carries the wrong transformers. OURS, not the host's -- never
        #: blocklist for it.
        _billing(cloud, iid, "venv pin mismatch (rc=4)")
        raise SystemExit("  VENV MISMATCH:\n%s" % (r.stdout or "")[-400:])
    if r.returncode == 3:
        #: **rc=3 IS THE HF REACHABILITY ASSERT, AND IT IS A MACHINE DEFECT.**
        #: Box 48145433 carried an HF proxy at http://117.175.104.83 and 404'd 10
        #: of its 11 models. That is a property of the HOST, not a race, so the
        #: runbook's rule applies: blocklist the machine and take another offer,
        #: never retry the same one. Destroying here is safe because the assert
        #: runs BEFORE any model is fetched -- there is nothing on the box to lose.
        #: **BLAME THE HOST ONLY FOR THE HOST'S FAULTS.** Machine 61353 was
        #: blocklisted on 2026-08-19 for an `IsADirectoryError` -- our own token
        #: file shipped as a directory -- because this branch treated every rc=3
        #: as a network verdict. A blocklist that accumulates our bugs shrinks the
        #: offer pool for reasons nobody can audit afterwards, and the machine was
        #: never shown to be bad. Local causes name local objects; check first.
        out = (r.stdout or "") + (r.stderr or "")
        ours = [w for w in ("IsADirectoryError", "PermissionError", "token",
                            "No such file or directory") if w in out]
        if ours:
            _billing(cloud, iid, "HF assert failed on OUR defect: %s" % ours[0])
            raise SystemExit("  the HF assert failed for a LOCAL reason (%s), so "
                             "the machine is NOT blocklisted. Box kept.\n%s"
                             % (ours[0], out[-400:]))
        cloud.blocklist(best.get("machine_id"), "HF unreachable from this host")
        print("  HF UNREACHABLE from this machine -- blocklisted.\n%s"
              % (r.stdout or "")[-300:])
        if cloud.destroy_verified(iid):
            cloud.state(forget=iid)
            raise SystemExit("  destroyed and CONFIRMED gone. Re-run to take a "
                             "different offer.")
        _billing(cloud, iid, "HF unreachable AND destroy did not take")
        raise SystemExit("  HF unreachable and still billing -- see above.")
    if r.returncode:
        #: **A FAILURE AFTER `create` LEAVES A BOX BILLING.** Raising here without
        #: saying so is the casualty pattern from the other side: not a box that
        #: looks alive while doing nothing, but a box nobody remembers renting.
        #: The id and the destroy command go in the message, and `state()` still
        #: holds it, so `malign cloud stop` finds it too.
        _billing(cloud, iid, "provision failed rc=%d" % r.returncode)
        raise SystemExit("  provision FAILED rc=%d\n%s"
                         % (r.returncode, (r.stderr or "")[-600:]))
    #: **CONFIRMED BY ASKING THE BOX WHO IT IS**, not by trusting that the copy
    #: succeeded. A token that arrives and does not authenticate fails 12 gated
    #: models three hours later; here it fails in seconds, with the box kept.
    if os.path.exists(tok_path):
        from preflight_env import gated as _gated
        gated_here = _gated(models)
        who = cloud.ssh_run(st, "cd /root/malignment && . /root/hfenv.sh && "
                                "./%s/bin/python -c \"from huggingface_hub import "
                                "whoami; print('HF AUTH OK as', whoami()['name'])\""
                            % venv)
        line = ((who.stdout or "").strip().splitlines() or ["(no answer)"])[-1]
        print("  auth        %s  (%d gated model(s) in this shard)"
              % (line[:60], len(gated_here)))
        if "HF AUTH OK" not in (who.stdout or ""):
            _billing(cloud, iid, "HF token did not authenticate on the box")
            raise SystemExit("  the token did not authenticate -- gated models "
                             "would fail. Box kept for inspection.")
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
    #: **DETACHED UNDER tmux, THEN POLLED.** This used to send each command as
    #: `nohup ... > /root/stage.log` with NO `&`, through an `ssh_run` that has no
    #: timeout -- so the ssh channel was held open for the entire measurement, a
    #: dropped connection killed the work, and each command overwrote the previous
    #: one's log. Survivable while a human watches a 40-minute pilot; precisely
    #: what cannot be left alone. Under tmux the BOX owns the work and ssh is only
    #: how we ask about it, so a dropped poll costs one poll.
    only = (" --only %s" % a.only) if a.only else ""
    #: **PASS 1 THEN PASS 2, PER LINEAGE -- NOT ALL OF PASS 1 THEN ALL OF PASS 2.**
    #: RH asked which it was. It was the latter, and the latter is worse in three
    #: ways, two of which bit tonight:
    #:
    #:   DISK. Measuring every model first means every model's weights coexist.
    #:   Box 48153389 filled 150 GB at model 11 of 11 and deadlocked. Per lineage
    #:   only ONE lineage's weights are live at a time -- box 11 needs 85 GB rather
    #:   than 370 GB, because its 22 models sit 3 to a lineage.
    #:
    #:   PARTIAL FAILURE. A box lost halfway used to leave 22 half-measured models
    #:   and ZERO closed lineages. Per lineage it leaves N CLOSED lineages and one
    #:   unstarted, and the closed lineage is the unit every consumer reads.
    #:
    #:   And it matches why we shard by lineage at all: the union is lineage-scoped
    #:   (`topup_lineage --root R`), so pass 2 needs nothing from any other lineage.
    #:   The old order invented a dependency that does not exist.
    #:
    #: **`--from-stash` IS NOT OPTIONAL ON A RENTED BOX.** Without it,
    #: `topup_lineage` builds the union by querying ClickHouse -- which does not
    #: exist on a rental, and the 2026-08-19 pilot died on `FileNotFoundError:
    #: /opt/homebrew/bin/clickhouse` having written 3,090 pass-1 cells and ZERO
    #: pass-2 ones. This module's own docstring claimed the dependency was gone;
    #: the flag that removes it was never passed.
    from malignment import roster as _r2
    _lin2 = _r2.lineages(ops=_r2.ALIGNING)
    cmds = []
    #: **OMIT A LINEAGE THE CARD CANNOT HOLD, DO NOT REFUSE THE SHARD.**
    #: `too_big_for` refuses at LAUNCH, which does nothing about a run.sh already
    #: written with an impossible lineage inside it -- so every restart of box
    #: 48182910 went straight back to `Olmo-3-1125-32B` (64 GB on a 47 GB card),
    #: burned ten minutes downloading, filled the disk to 69%, and I killed it by
    #: hand. Twice. A guard that only fires before the first launch is not
    #: protecting the thing that repeats.
    #:
    #: Dropping the lineage rather than the shard keeps the other four viable
    #: ones, which is what actually happened by hand both times. The dropped
    #: lineage is NAMED in the output, because a silently shorter run reads as a
    #: complete one.
    _too_big = too_big_for(best, models)
    if _too_big:
        print("  VRAM      omitting %d model(s) this card cannot hold; they need "
              "their own shard on a bigger profile:" % len(_too_big))
        for _m, (_need, _av) in sorted(_too_big.items()):
            print("     %-44s needs ~%.0f GB, usable ~%.0f GB" % (_m[:44], _need, _av))
    #: **THE FRAME FLAGS GO TO queue_v4, WHICH PASSES THEM TO run_v4.** Quoted,
    #: because a system message is arbitrary user text landing in a shell heredoc
    #: and `--system ""` is a real treatment that must survive the round trip.
    import shlex as _shlex
    framed = ""
    if a.frame:
        framed += " --frame %s" % a.frame
    if a.system is not None:
        framed += " --system %s" % _shlex.quote(a.system)
    if a.user_msg is not None:
        framed += " --user-msg %s" % _shlex.quote(a.user_msg)
    if a.prompts_file:
        framed += " --prompts-file %s" % _shlex.quote("/root/prompts.txt")
    for r_ in roots:
        mem = [m for m in _lin2.get(r_, []) if m in models and m not in _too_big]
        if not mem:
            continue
        cmds.append("./%s/bin/python scripts/queue_v4.py --models %s%s%s"
                    % (venv, " ".join(mem), only, framed))
        #: **NO TOPUP ON A FRAMED RUN, AND THIS IS NOT AN OMISSION.**
        #: `topup_lineage.py` takes no frame, so it would score the lineage's
        #: word union against the RAW surface and write pass-2 cells that do not
        #: belong to the pass-1 cells beside them -- two frames in one lineage
        #: under one label. Pass 2 for a framed population is its own decision
        #: and its own run, made once there is a framed union to take.
        if not a.frame:
            cmds.append("./%s/bin/python scripts/topup_lineage.py --root %s "
                        "--from-stash%s" % (venv, r_, only))
        #: The wipe is what makes the disk saving real. Weights are
        #: re-downloadable; the cells they produced are already written and pulled.
        cmds.append("rm -rf /root/.cache/huggingface/hub/models--*")
    #: Anything in the shard no lineage claimed is still measured, at the end.
    orphan = [m for m in models if not any(m in _lin2.get(r_, []) for r_ in roots)]
    if orphan:
        cmds.append("./%s/bin/python scripts/queue_v4.py --models %s%s%s"
                    % (venv, " ".join(orphan), only, framed))
    script = ["cd /root/malignment", ". /root/hfenv.sh",
              "rm -f /root/DONE /root/FAILED"]
    for i, c in enumerate(cmds):
        script.append("%s > /root/stage%d.log 2>&1 || touch /root/FAILED" % (c, i))
    script.append("touch /root/DONE")
    cloud.ssh_run(st, "cat > /root/run.sh <<'MLEOF'\n%s\nMLEOF" % "\n".join(script))
    cloud.ssh_run(st, "command -v tmux >/dev/null || (apt-get update -qq && "
                      "apt-get install -y -qq tmux)")
    rr = cloud.ssh_run(st, "tmux new-session -d -s fleet 'bash /root/run.sh'")
    if rr.returncode:
        _billing(cloud, iid, "tmux would not start rc=%d" % rr.returncode)
        raise SystemExit("  could not detach the run: %s" % (rr.stderr or "")[-300:])
    print("  run         %d commands detached under tmux 'fleet'" % len(cmds))
    for c in cmds:
        print("                %s" % c[:92])
    if a.stop_after == "run":
        print("\n  STOPPED AFTER run -- the box is WORKING and BILLING. It will "
              "not destroy itself.")
        return 0

    if not _await(cloud, st, models, iid, a):
        return 1

    # ---- pull --------------------------------------------------------------
    #: **THE LOGS COME BACK TOO, AND BEFORE THE DESTROY.** A box is the only place
    #: its own logs exist; destroying it on a clean verification also destroys the
    #: record of every refusal, warning and slow arm inside a run that "passed".
    logdir = os.path.join(ROOT, "data", "fleet_logs", str(iid))
    os.makedirs(logdir, exist_ok=True)
    for i in range(len(cmds)):
        lg = cloud.ssh_run(st, "cat /root/stage%d.log 2>/dev/null" % i)
        open(os.path.join(logdir, "stage%d.log" % i), "w").write(lg.stdout or "")
    print("  logs        %s" % logdir)
    #: **AND THE RATES THE BOX MEASURED, WHICH OTHERWISE DIE WITH IT.**
    #: `runners.run` records one observation per model into the repo's own
    #: `data/model_twp_rates.jsonl` -- on the BOX. The pull fetches twp data and
    #: nothing else, so a 12-box fleet would measure 144 models on real CUDA and
    #: destroy every rate it learned, leaving the next plan on the same fallbacks
    #: that mispriced Zamba2 by 500x.
    #:
    #: MERGED, never overwritten: the local file holds every earlier observation
    #: and the box holds only its own, so copying over the top would be a silent
    #: deletion. `rates.load` tolerates duplicates and `rate_for` takes a median,
    #: so appending is safe and re-running is harmless.
    rp = cloud.ssh_run(st, "cat /root/malignment/data/model_twp_rates.jsonl "
                           "2>/dev/null")
    got = [l for l in (rp.stdout or "").splitlines() if l.strip()]
    if got:
        from malignment import rates as _rates
        have = {l.strip() for l in
                (open(_rates.PATH, encoding="utf-8") if os.path.exists(_rates.PATH)
                 else [])}
        new_rows = [l for l in got if l.strip() not in have]
        with open(_rates.PATH, "a", encoding="utf-8") as fh:
            for l in new_rows:
                fh.write(l + "\n")
        print("  rates       %d observation(s) from the box, %d new"
              % (len(got), len(new_rows)))
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
    #:
    #: **BUT A TRANSFER CHECK IS NOT A WORK CHECK, AND THIS PASSED A BOX THAT DID
    #: HALF THE JOB.** The 2026-08-19 pilot ran pass 1 to completion, died in pass
    #: 2 on a missing ClickHouse, wrote /root/FAILED, and was VERIFIED and
    #: DESTROYED -- because remote and local line counts agreed exactly, which
    #: they do whether the box wrote everything or nothing. Every byte it produced
    #: came home; half of what it was asked to produce never existed.
    #:
    #: So the sentinel is now load-bearing. `FAILED` refuses the destroy on its
    #: own, before any counting: a command exited non-zero, and the box is the
    #: only place the evidence for WHY still exists.
    #: Re-read from the BOX rather than carrying a flag out of `_await`: the
    #: sentinel is the box's own statement about itself, and a copy of it in a
    #: local variable is one more thing that can drift from what is true there.
    if cloud.ssh_run(st, "ls /root/FAILED 2>/dev/null").returncode == 0:
        _billing(cloud, iid, "a command exited non-zero (/root/FAILED)")
        print("  NOT DESTROYING -- the run reported a failure. Logs are already "
              "pulled to %s, but the box is kept so the failure can be inspected "
              "live. Destroy by hand once you know what happened." % logdir)
        return 1
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
    #: **COUNTING LINES VERIFIES TRANSFER, NOT CONTENT.** The loop above proves
    #: every cell the box wrote arrived here. It cannot tell whether those cells
    #: hold anything: Falcon-H1-7B at fp16 returned all-NaN logits and wrote
    #: 5,166 cells that were EMPTY, and they satisfied conservation EXACTLY,
    #: because `sum([]) + 1.0 == 1.0`. Remote count, local count and ledger all
    #: agreed; the run was worthless. Destroying on a byte match would have
    #: thrown away the only machine that could re-run it.
    for m in models:
        v, why = box_guard.emptiness_verdict(
            os.path.join(dst, m.replace("/", "__")))
        if v == "EMPTY":
            ok = False
            print("     %-46s EMPTY  %s" % (m[:46], why))
    if a.stop_after == "verify" or not ok:
        if not ok:
            print("\n  NOT DESTROYING -- verification failed. The box is still "
                  "billing; inspect it, then destroy by hand.")
        return 0 if ok else 1

    # ---- destroy -----------------------------------------------------------
    if not cloud.destroy_verified(iid):
        _billing(cloud, iid, "verification PASSED but destroy did not take")
        return 1
    cloud.state(forget=iid)
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
# **THE VENV IS BUILT FROM THE ROSTER, NOT FROM requirements.txt.** This ran
# `pip install -r requirements.txt` into a venv NAMED .venv-tf457 and got
# transformers 5.15.0 -- because the 5.4.0 cap in requirements.txt is
# darwin-only, and the 4.57.1 pin lives in roster/models/models.yaml where only
# scripts/venvs.py reads it. So on every rented box the `env: profile` mechanism
# was inert and the venv name was a label with nothing behind it. venvs.py's own
# docstring names this exact number: ">=4.57 resolving to 5.15.0 is the whole
# reason the split exists".
command -v uv >/dev/null || pip -q install uv
python3 scripts/venvs.py build --python 3.11
# **THE IMAGE INJECTS AN HF MIRROR INTO SITE-PACKAGES, AND IT BEATS THE SHELL.**
# Found on box 48180548 after the shell said HF_ENDPOINT=https://huggingface.co
# and Python said otherwise:
#
#   .venv/lib/python3.11/site-packages/hf_config.pth
#   import os; os.environ["HF_ENDPOINT"] = "http://117.175.104.83:8081"; ...
#
# Python EXECUTES .pth files at interpreter startup, so this overwrites the
# environment INSIDE the process, after every export we make. That is why the
# reachability assert passed -- a tiny public file the mirror happens to hold --
# while multi-GB shards 404'd.
#
# **ONE CAUSE, THREE SIGNATURES**, each of which I had been treating as its own
# bug across three boxes: 404 Not Found from an http:// host; `IncompleteRead(1.5
# of 4.8 GB)` truncated downloads, a mirror serving partial files; and `Invalid
# rev id: <35 chars>`, mangled metadata. The same IP appears in all of them.
# Purge it at SOURCE first -- uv copies this archive into every venv it builds,
# so deleting only from the venv is undone by the next `uv pip install`.
rm -f /opt/uv/cache/archive-v0/*/hf_config.pth 2>/dev/null || true
find /opt/uv /usr/local/lib /usr/lib -name "hf_config.pth" -delete 2>/dev/null || true
find /root/malignment -name "hf_config.pth" -delete 2>/dev/null || true
# **PIN transformers TO WHAT THIS MACHINE HAS, NOT TO WHAT LINUX RESOLVES.** The
# roster's spec for the default profile is loose (`>=5`), so it resolved to 5.4.0
# here -- capped on darwin because 5.15 hangs on MPS -- and to 5.15.1 on the box.
# Two different minors producing cells for one corpus, silently, until the venv
# assert caught it. 100k+ cells in the corpus were measured under this Mac's
# versions, so PARITY is the defensible direction: the same principle as shipping
# the tree instead of cloning, applied to dependencies.
#
# Empty `want` means the local venv of that name does not exist, and then there is
# nothing to match and the roster's own resolution stands.
if [ -n "%(want)s" ]; then
  uv pip install -q --system-certs --python ./%(venv)s/bin/python \
      "transformers==%(want)s" || echo "could not pin transformers==%(want)s"
fi
# **AND THE PACKAGE ITSELF.** requirements.txt lists DEPENDENCIES; without
# `pip install -e .` every script dies on `ModuleNotFoundError: malignment` --
# after the venv built, after the payload shipped, with the rental running.
# **uv's venvs HAVE NO `pip`.** `venvs.py build` uses `uv venv`, which omits it
# by design, so `./<venv>/bin/pip` is `No such file or directory` -- which is what
# it was, immediately after the roster-derived build finally installed the right
# transformers. Install through uv, targeting the venv's interpreter, exactly as
# venvs.py does.
uv pip install -q --python ./%(venv)s/bin/python -e .
# **AND THE PIN IS ASSERTED, NOT ANNOUNCED.** A build that prints a version
# nobody compares is how 5.15.0 ran for an hour under a name meaning 4.57.1.
# The expected value is this checkout's OWN venv, so the box matches the machine
# the code was tested on -- the same principle as shipping the tree.
# **AND AGAIN AFTER THE INSTALLS.** The purge above runs before them; every
# `uv pip install` since is another chance for the cached archive to put it back.
# Deleting once and asserting later would test a state two commands ago.
find /root/malignment /opt/uv -name "hf_config.pth" -delete 2>/dev/null || true
./%(venv)s/bin/python - <<'VEOF'
import sys, torch, transformers
want, got = "%(want)s", transformers.__version__
print("torch", torch.__version__, "transformers", got, "cuda", torch.cuda.is_available())
#: **COMPARED ON MAJOR.MINOR, WHICH IS THE GRAIN THE PROFILE IS NAMED FOR.** The
#: first version demanded exact equality and would have REJECTED A GOOD BOX: this
#: Mac pinned 4.57.1, the box legitimately resolved 4.57.6, and `tf457` means the
#: 4.57 line. The defect this guards against is 5.15.0 wearing that name, which
#: major.minor catches and patch-equality would have buried under false alarms.
mm = lambda v: ".".join(v.split(".")[:2])
if want and mm(got) != mm(want):
    print("VENV MISMATCH: %(venv)s has transformers", got,
          "but this roster declares", want)
    sys.exit(4)
print("VENV OK: transformers", got, "on the", mm(want) or "?", "line")
VEOF
%(ssm)s
# **THE BOX'S OWN NETWORK CONFIG IS NOT TRUSTED.** Fleet box 48145433 shipped with
# an HF proxy at http://117.175.104.83 and 10 of its 11 models died on 404 -- a
# machine property we paid to provision, ship to, and run a whole shard against
# before learning. Normalise the endpoint and drop inherited proxies, then PROVE
# the box can reach HF before any model is asked for.
cat > /root/hfenv.sh <<'HFEOF'
export HF_ENDPOINT=https://huggingface.co
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy ALL_PROXY all_proxy
if [ -f /root/.cache/huggingface/token ]; then
  export HF_TOKEN=$(cat /root/.cache/huggingface/token)
fi
HFEOF
. /root/hfenv.sh
# A REACHABILITY ASSERT, NOT A PING. It fetches the same way the runner does --
# through huggingface_hub, from the venv that will do the work -- because a
# curl that succeeds proves nothing about a library reading a different env.
./%(venv)s/bin/python - <<'PYEOF'
import sys
import huggingface_hub.constants as _C
from huggingface_hub import hf_hub_download
#: **ASSERT THE ENDPOINT, NOT ONLY THE FETCH.** A mirror answers small files
#: happily, so "a download worked" proved nothing about where from.
if "huggingface.co" not in (_C.ENDPOINT or ""):
    print("HF ENDPOINT HIJACKED:", _C.ENDPOINT)
    sys.exit(3)
try:
    p = hf_hub_download("hf-internal-testing/tiny-random-gpt2", "config.json")
    print("HF REACHABLE via", _C.ENDPOINT, "->", p)
except Exception as e:
    print("HF UNREACHABLE:", type(e).__name__, str(e)[:200])
    sys.exit(3)
PYEOF
"""


def _written(cloud, st):
    """Cells the box has WRITTEN. Counted from the stash, never from a message.

    The runbook's rule and the reason this poll exists: *"an orphaned engine makes
    every unit complete in 0.3 min having produced nothing, and the health loop
    reports it as throughput. Check what was WRITTEN, never what was attempted."*
    A completion line, a progress bar and an exit code are all things the box SAYS;
    lines in `data.jsonl` are the only thing it has done.
    """
    r = cloud.ssh_run(st, "cat /root/malignment-data/twp/*/*/jsonl.hashstash.raw/"
                          "data.jsonl 2>/dev/null | wc -l")
    try:
        return int((r.stdout or "0").strip().split()[-1])
    except (ValueError, IndexError):
        return -1


def _await(cloud, st, models, iid, a):
    """Poll until DONE, and distinguish the three ways that never arrives.

    **A box has more states than done/not-done, and they need different actions:**

        DONE sentinel            finished -- go verify
        FAILED sentinel          a command exited non-zero -- keep it, look
        tmux gone, no sentinel   died without writing either -- keep it, look
        cells not moving         ALIVE AND PRODUCING NOTHING -- the dangerous one

    The last is the casualty pattern, and it is the only one that looks healthy
    from every angle except the one that counts. It is reported as a STALL rather
    than destroyed, because destroying it destroys the evidence of why -- and RH's
    standing gate is byte-level verification before any box goes.
    """
    import time
    t0 = time.time()
    last_n, last_change, ticks = -1, time.time(), 0
    slow_at = None
    while True:
        if time.time() - t0 > a.max_hours * 3600:
            _billing(cloud, iid, "exceeded --max-hours %.1f" % a.max_hours)
            return False
        time.sleep(a.poll)
        ticks += 1
        n = _written(cloud, st)
        #: **A SECOND WATCHER MUST NOT CONSUME THIS SIGNAL.** On 2026-08-20 I
        #: queued a recovery session that waited for /root/DONE, DELETED it, and
        #: re-ran the work. So when box 48180548 finished its shard, the recovery
        #: removed the sentinel this loop was waiting on -- the launcher saw tmux
        #: gone and no DONE, called it a failure, and skipped pull, verify and
        #: destroy on a box that had just written 36,220 cells correctly.
        #:
        #: The sentinel is a LEVEL, not an event: it must stay true once true. A
        #: recovery that wants to re-run should write its own marker and leave
        #: DONE alone, which is why the counterpart file is RECOVER_DONE and not
        #: a second use of this one.
        done = cloud.ssh_run(st, "ls /root/DONE /root/RECOVER_DONE 2>/dev/null"
                             ).returncode == 0
        failed = cloud.ssh_run(st, "ls /root/FAILED 2>/dev/null").returncode == 0
        alive = cloud.ssh_run(st, "tmux has-session -t fleet 2>/dev/null").returncode == 0
        if n != last_n:
            last_n, last_change = n, time.time()
        #: **PULL WHILE IT RUNS, NOT ONLY AT THE END.** There was exactly one
        #: rsync of the cells and it came AFTER the run finished, so a box lost at
        #: 2h50m of a 3h shard lost everything it had written. RH: *"we don't have
        #: an rsync auto-looping do we? when do you rsync?"* -- we did not.
        #:
        #: rsync is delta-based, so repeating it costs the new cells and a
        #: directory walk. A failed intermediate pull is NOT fatal: the box still
        #: holds the data and the final pull is authoritative, so this warns and
        #: continues rather than tearing down a healthy run over a network blip.
        if a.pull_every and ticks % a.pull_every == 0:
            try:
                pr = cloud.rsync(st, "/root/malignment-data/twp",
                                 os.path.expanduser("~/malignment-data/twp"),
                                 from_remote=True)
                print("     incremental pull rc=%d" % pr.returncode, flush=True)
            except Exception as e:                              # noqa: BLE001
                print("     incremental pull FAILED (not fatal): %s"
                      % str(e)[:80], flush=True)
        idle = (time.time() - last_change) / 60.0
        #: **CELLS MOVING IS NOT CELLS MOVING FAST ENOUGH.** Every other signal
        #: here -- done, failed, tmux, idle -- reads green while a box runs 178x
        #: slow, because it IS producing. `Zamba2-7B` without the mamba kernels
        #: loads and runs without erroring at 183.4 s/cell against 1.03 with
        #: them: 152 hours for one model, and the only symptom is the clock.
        #: `environments.yaml` says verify the kernels are IN USE and not merely
        #: installed -- and asking the library cannot answer it, since
        #: `is_mamba_ssm_available()` returned True throughout that failure. The
        #: rate does answer it, and being ignorant of mechanism it also catches
        #: the wrong card, thermal throttling and contention.
        if slow_at is None and n >= box_guard.MIN_CELLS:
            v, why = box_guard.throughput_verdict(models, n, time.time() - t0)
            if v == "SLOW":
                slow_at = ticks
                print("  ** SLOW     %s" % why)
                print("  **          NOT destroying: that would destroy the "
                      "evidence. Check the kernels on a load that SUCCEEDED -- "
                      "a fast-path warning during a FAILED load says nothing "
                      "about the kernels.")
        print("  poll %-3d    %s cells written | tmux %s | %.0f min elapsed%s%s"
              % (ticks, format(max(n, 0), ","), "up" if alive else "GONE",
                 (time.time() - t0) / 60.0,
                 " | IDLE %.0f min" % idle if idle > 2 else "",
                 " | SLOW since poll %d" % slow_at if slow_at else ""))
        if done:
            print("  complete    DONE after %.0f min, %s cells written"
                  % ((time.time() - t0) / 60.0, format(max(n, 0), ",")))
            if failed:
                #: A stage failed and later stages still ran. Not fatal -- pass 1
                #: can fail for one arm while the rest close -- but never silent.
                print("  NOTE        /root/FAILED exists: at least one command "
                      "exited non-zero. Logs pulled below; verify decides.")
            return True
        if not alive:
            _billing(cloud, iid, "tmux session gone with no DONE sentinel")
            print("  last log:")
            print((cloud.ssh_run(st, "tail -n 25 /root/stage*.log").stdout or "")[-1500:])
            return False
        if idle >= a.stall_min:
            #: **ALIVE AND PRODUCING NOTHING.** Do not retry and do not destroy.
            _billing(cloud, iid, "STALL: no new cells for %.0f min while tmux is up"
                                 % idle)
            print("  last log:")
            print((cloud.ssh_run(st, "tail -n 25 /root/stage*.log").stdout or "")[-1500:])
            return False


#: **KERNELS ARE INSTALLED ONLY FOR SHARDS THAT DECLARE THEY NEED THEM**, and
#: the declaration comes from the roster (`env: profile: ssm`, 10 nodes), never
#: from a name. `Zyphra/Zamba2-7B` ran at **183 s/cell** on a box without them --
#: 152 hours for one model -- while the archive's `twpssm` fleet did the same
#: architecture at **<=0.905 s/cell**, a 200x gap that is entirely environment.
#:
#: Not installed everywhere because `mamba-ssm` COMPILES, slowly, and a shard
#: with no SSM member should not pay for it. Note the roster does NOT class rwkv,
#: recurrentgemma or Olmo-Hybrid as `ssm` -- they are recurrent but need nothing
#: special, and their measured rates (2.4-6.0 s/cell) confirm it. My own guess by
#: name said 15 models; the roster says 10, and the roster is right.
SSM_KERNELS = """
echo "SSM shard: installing mamba kernels (this COMPILES and is slow)"
# **`--system-certs`, AND THE OUTPUT IS KEPT.** Without it uv rejects a host that
# intercepts TLS -- `invalid peer certificate: UnknownIssuer` on
# files.pythonhosted.org, which is the same machine-level interference as the HF
# proxy that killed an earlier box, and invisible to the HF assert because
# huggingface_hub uses SYSTEM certs while uv bundles its own trust store.
#
# The first version ended `|| echo "returned non-zero"` and ran with `-q`, so the
# failure arrived as "SSM KERNELS MISSING" with the REASON discarded. A guard that
# hides why it fired costs a whole round trip to a live box to recover.
uv pip install --system-certs --python ./%(venv)s/bin/python \
    --no-build-isolation causal-conv1d mamba-ssm 2>&1 | tail -25
./%(venv)s/bin/python - <<'KEOF'
import importlib.util, sys
missing = [m for m in ("mamba_ssm", "causal_conv1d")
           if importlib.util.find_spec(m) is None]
if missing:
    # **FAIL RATHER THAN RUN SLOWLY.** Without these the models still LOAD and
    # still produce correct cells -- at 183 s/cell, which reads as a healthy box
    # doing nothing for six days. A wrong answer would be caught; this would not.
    print("SSM KERNELS MISSING:", missing)
    sys.exit(5)
print("SSM KERNELS OK")
KEOF
"""


def _reqs():
    """{model: requirements row} from roster/models/requirements.json.

    Cached on the function so the offer loop does not re-read a 4,400-line file
    per candidate.
    """
    import json as _j
    if not hasattr(_reqs, "_c"):
        p = os.path.join(ROOT, "roster/models/requirements.json")
        _reqs._c = {r["model"]: r for r in _j.load(open(p))["requirements"]}
    return _reqs._c


def _params_b():
    """{model: params_b} from roster/models/measurements.json. MEASURED, 164 rows.

    **THE REPO ALREADY KNEW THIS AND I ASKED THE INTERNET INSTEAD.** I sized
    shards by hitting the HF API for `safetensors.total`, which returns nothing
    for 21 of our models -- every pre-safetensors repo, so RWKV, Baichuan2,
    deepseek, RedPajama, mpt. `measurements.json` has all 164 with no network and
    no blind spots.
    """
    import json as _j
    out = {}

    def walk(o, path=()):
        if isinstance(o, dict):
            if "params_b" in o:
                #: The file keys models by their FULL id in ONE segment
                #: ("allenai/Olmo-3-1125-32B"), so the last path element IS the
                #: model id. Joining the last two prepended "models/" and every
                #: lookup silently missed -- every shard then reported 0.0B and
                #: resolved to the smallest profile, which is the dangerous
                #: direction: a 32B arm sent to a 24 GB card.
                out[path[-1]] = o["params_b"]
            else:
                for k, v in o.items():
                    walk(v, path + (str(k),))
        elif isinstance(o, list):
            for v in o:
                walk(v, path)
    walk(_j.load(open(os.path.join(ROOT, "roster/models/measurements.json"))))
    return out


def _sizing_steps():
    """The DECLARED step function: params_b -> (vram_gb, gpus).

    `roster/environments.yaml` carries it with its own justification: *"a STEP
    FUNCTION of measured params_b, verified with no overlaps across 159 archive
    rows. Declared as a rule so 160 checkpoints do not each carry a derived number
    with no producer."* I then derived one anyway, with invented thresholds.
    """
    import yaml
    d = yaml.safe_load(open(os.path.join(ROOT, "roster/environments.yaml")))
    return (d.get("sizing") or {}).get("steps") or []


def shard_profile(models):
    """(profile, vram_gb, gpus, biggest_params_b) for this shard, from the roster."""
    pb = _params_b()
    biggest = max([pb.get(m.split("/")[-1], 0) or pb.get(m, 0) or 0
                   for m in models] or [0])
    vram, gpus = 24, 1
    for step in _sizing_steps():
        cap = step.get("max_params_b")
        if cap is None or biggest <= cap:
            vram, gpus = step.get("vram_gb", 80), step.get("gpus", 1)
            break
    prof = ("twogpu" if gpus > 1 else
            "big80" if vram >= 80 else
            "dense")
    return prof, vram, gpus, biggest


def too_big_for(offer, models, dtype_bytes=2, headroom=0.90):
    """{model: (gb_needed, gb_available)} for models that cannot fit this offer.

    **THE PLANNER PACKS BY SECONDS AND DISK AND NEVER LOOKED AT VRAM.** Shard 12
    put the four 32B Olmo arms on a `dense` box and the first one died with `CUDA
    out of memory ... GPU 0 has a total capacity of 47.37 GiB` after a 9.6-minute
    download. 32B at fp16 is ~64 GB; the card is a 4090.

    Checked against the OFFER's real `gpu_ram`, not the profile's prose. `dense`
    describes itself as "48GB-class" in a `description` string and declares no
    VRAM field at all, so a profile-based check would have been reading marketing
    copy. The offer knows.

    Param counts come from the HF API unauthenticated, the same route
    `preflight_env.gated` uses. A model whose size cannot be determined is NOT
    flagged -- silence here means unknown, and refusing on unknown would ground
    the fleet for every repo that does not publish safetensors metadata.
    """
    import json as _j
    import urllib.request
    per = float(offer.get("gpu_ram") or 0) / 1024.0          # MB -> GB, per GPU
    n = int(offer.get("num_gpus") or 1)
    avail = per * n * headroom
    if avail <= 0:
        return {}
    out = {}
    for m in sorted(set(models)):
        try:
            with urllib.request.urlopen(
                    "https://huggingface.co/api/models/%s" % m, timeout=8) as fh:
                d = _j.loads(fh.read().decode("utf-8"))
            tot = (d.get("safetensors") or {}).get("total")
            if not tot:
                continue
            need = tot * dtype_bytes / 1e9
            if need > avail:
                out[m] = (round(need, 1), round(avail, 1))
        except Exception:                                    # noqa: BLE001
            continue
    return out


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
