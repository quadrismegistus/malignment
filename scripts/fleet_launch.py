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
    ap.add_argument("--poll", type=int, default=120,
                    help="seconds between health polls once the run is detached")
    ap.add_argument("--stall-min", type=float, default=25.0,
                    help="minutes with NO new cells written, tmux still up, before "
                         "the box is called stalled. Must exceed the slowest cold "
                         "model load in the shard, or a normal load reads as a "
                         "stall -- the one number here that is a judgement.")
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
    if r.returncode == 3:
        #: **rc=3 IS THE HF REACHABILITY ASSERT, AND IT IS A MACHINE DEFECT.**
        #: Box 48145433 carried an HF proxy at http://117.175.104.83 and 404'd 10
        #: of its 11 models. That is a property of the HOST, not a race, so the
        #: runbook's rule applies: blocklist the machine and take another offer,
        #: never retry the same one. Destroying here is safe because the assert
        #: runs BEFORE any model is fetched -- there is nothing on the box to lose.
        cloud.blocklist(best.get("machine_id"), "HF unreachable from this host")
        print("  HF UNREACHABLE from this machine -- blocklisted.\n%s"
              % (r.stdout or "")[-300:])
        if cloud.destroy_verified(iid):
            cloud.state({})
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
    if a.stop_after == "provision":
        return 0

    # ---- token -------------------------------------------------------------
    #: Asked UNAUTHENTICATED, which is the BOX's condition rather than ours --
    #: this Mac holds a token in its shell profile, so every gated repo resolves
    #: here and nowhere else, which is why two pilots never surfaced it.
    from preflight_env import gated as _gated
    gated_here = _gated(models)
    #: **12 OF 144 MODELS ARE GATED AND A TOKENLESS BOX CANNOT FETCH THEM.**
    #: Measured unauthenticated by `preflight_env.gated()` -- including
    #: `meta-llama/Llama-3.1-8B`, a whole lineage root. RH, 2026-08-19: *"I have
    #: HF_TOKEN here just rsync it over."*
    #:
    #: **The value never touches an argv, a log, or a commit.** It is written to a
    #: 0600 temp file and rsynced to the location huggingface_hub reads by itself,
    #: because `ssh_run(st, "echo $TOK > ...")` would put a live credential in the
    #: local process table and in this script's own output. `hfenv.sh` then exports
    #: it by READING that file, so the script text never contains it either.
    #: **THE LOCAL TOKEN FILE IS THE SOURCE, AND IT IS SHIPPED AUTOMATICALLY.**
    #: RH, 2026-08-19: *"save the token to ~/.cache/huggingface/token too / then in
    #: the box launcher script make the rsync of that file automatic."* So the
    #: same path holds it on both machines and the transfer is a plain file copy
    #: with no credential in any argv. The env var is a FALLBACK for a shell that
    #: exports one without having written the file; when it is used, the file is
    #: created first, so there is exactly one thing to ship either way.
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
        cloud.rsync(st, tok_path, "/root/.cache/huggingface/token")
        cloud.ssh_run(st, "chmod 600 /root/.cache/huggingface/token")
        #: Confirmed by asking the BOX who it is, not by trusting the copy.
        who = cloud.ssh_run(st, "cd /root/malignment && . /root/hfenv.sh && "
                                "./%s/bin/python -c \"from huggingface_hub import "
                                "whoami; print('HF AUTH OK as', whoami()['name'])\""
                            % venv)
        line = (who.stdout or "").strip().splitlines()[-1:] or ["(no answer)"]
        print("  token       %s" % line[0][:70])
        if "HF AUTH OK" not in (who.stdout or ""):
            _billing(cloud, iid, "HF token did not authenticate on the box")
            raise SystemExit("  the token did not authenticate -- 12 gated models "
                             "would fail. Box kept for inspection.")
    else:
        print("  token       NO ~/.cache/huggingface/token and none in env -- "
              "%d gated model(s) in this shard WILL fail" % len(gated_here))

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
# **THE BOX'S OWN NETWORK CONFIG IS NOT TRUSTED.** Fleet box 48145433 shipped with
# an HF proxy at http://117.175.104.83 and 10 of its 11 models died on 404 -- a
# machine property we paid to provision, ship to, and run a whole shard against
# before learning. Normalise the endpoint and drop inherited proxies, then PROVE
# the box can reach HF before any model is asked for.
cat > /root/hfenv.sh <<'HFEOF'
export HF_ENDPOINT=https://huggingface.co
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy ALL_PROXY all_proxy
[ -f /root/.cache/huggingface/token ] && export HF_TOKEN=$(cat /root/.cache/huggingface/token)
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
