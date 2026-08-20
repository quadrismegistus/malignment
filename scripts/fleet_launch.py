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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", default="data/fleet_shards.json")
    ap.add_argument("--box", type=int, required=True, help="1-based index into the plan")
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
    ap.add_argument("--box-profile", default="dense",
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
    need_gb = int(len(models) * a.gb_per_model + 40)
    disk_gb = a.disk or need_gb
    print("  disk      %d GB for %d models (%.0f GB each + 40 headroom)%s"
          % (disk_gb, len(models), a.gb_per_model,
             "" if not a.disk else "  [OVERRIDDEN to %d]" % a.disk))
    print("  cells     %s  (~%.1f h; %d of %d models have a recorded rate)"
          % (format(b["cells"], ","), est_s / 3600,
             len(models) - len(guessed), len(models)))

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
    ] + ["python scripts/topup_lineage.py --root %s --from-stash%s"
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
    hrs = seconds(b.get("per") or {m: b["cells"] // max(1, len(models))
                                   for m in models}, "cuda")[0] / 3600
    est = float(best.get("dph_total") or 0) * hrs
    print("  estimated   $%.2f for %.1f h of compute (EXCLUDES download time, "
          "which dominates on a fresh box)" % (est, hrs))
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
                                         a.disk or int(len(models) * a.gb_per_model + 40))),
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
    if _ssm:
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
    cmds = ["./%s/bin/python scripts/queue_v4.py --models %s%s"
            % (venv, " ".join(models), only)]
    #: **`--from-stash` IS NOT OPTIONAL ON A RENTED BOX.** Without it,
    #: `topup_lineage` builds the lineage union by querying ClickHouse -- which
    #: does not exist on a rental, and the 2026-08-19 pilot died on
    #: `FileNotFoundError: /opt/homebrew/bin/clickhouse` having written 3,090
    #: pass-1 cells and ZERO pass-2 ones. This module's own docstring claims to
    #: have removed that dependency; the flag that does so was never passed.
    cmds += ["./%s/bin/python scripts/topup_lineage.py --root %s --from-stash%s"
             % (venv, r_, only) for r_ in roots]
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
from huggingface_hub import hf_hub_download
try:
    p = hf_hub_download("hf-internal-testing/tiny-random-gpt2", "config.json")
    print("HF REACHABLE:", p)
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
    while True:
        if time.time() - t0 > a.max_hours * 3600:
            _billing(cloud, iid, "exceeded --max-hours %.1f" % a.max_hours)
            return False
        time.sleep(a.poll)
        ticks += 1
        n = _written(cloud, st)
        done = cloud.ssh_run(st, "ls /root/DONE 2>/dev/null").returncode == 0
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
        print("  poll %-3d    %s cells written | tmux %s | %.0f min elapsed%s"
              % (ticks, format(max(n, 0), ","), "up" if alive else "GONE",
                 (time.time() - t0) / 60.0,
                 " | IDLE %.0f min" % idle if idle > 2 else ""))
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
