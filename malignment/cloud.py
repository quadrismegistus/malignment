#!/usr/bin/env python
"""vast.ai orchestration, driven by `roster/environments.yaml`.

    python -m malignment.cloud boxes                 what shapes are declared
    python -m malignment.cloud offers --box dense    what is available, ranked
    python -m malignment.cloud launch --box dense    rent, verify, record
    python -m malignment.cloud status
    python -m malignment.cloud coverage --model M    what the box actually WROTE
    python -m malignment.cloud stop

## PORTED, NOT REWRITTEN -- AND ONLY THE EXECUTABLE HALF

The archive's `malign_logits/cloud.py` is 1,007 lines, of which `cmd_launch` is
312. **Most of that was knowledge, and the knowledge already crossed**: box
shapes, images, pins, GPU filters and the reasons for each live in
`roster/environments.yaml`, with `engine_recovery` for the eight architectures
vLLM has removed. So this reads the declaration instead of carrying a second copy
of it -- the archive's `load_profile()` had a `profiles.json` that could disagree
with the roster, and this cannot.

## THE TWO PIECES THAT ARE NOT POLISH

`_verify_reachable` and `_blocklist_machine` come over first, not last. The
runbook's §2.13 CASUALTY PATTERN is the most expensive recurring failure in the
campaign's history -- *"EVERY FLEET LOSES BOXES TO THE SAME LOOP: a box does not
respond, we retry, it does not respond, we retry"* -- and the discriminator is
that **retrying is correct for a RACE and never for a STATE.** A box that never
answers SSH is a state; the fix is to blocklist the machine and take another
offer, not to wait longer.

`coverage` is here for the same reason and reports what was WRITTEN, never what
was attempted. *"An orphaned vLLM engine holding the card makes every unit
'complete' in 0.3 min having produced nothing, and the health loop reports it as
throughput."*

## WHAT THIS DELIBERATELY DOES NOT DO

No `cmd_setup`. The archive's is 185 lines of image-specific pip surgery, and
this repo now has `scripts/venvs.py` deriving its environment from the same
roster -- so setup should build the declared venv on the box rather than replay a
transcript. Left unported on purpose rather than carried over stale.
"""
import argparse
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENVS = os.path.join(ROOT, "roster", "environments.yaml")
STATE = os.path.join(ROOT, "data", "cloud_state.json")
BLOCKLIST = os.path.join(ROOT, "data", "cloud_bad_machines.json")


def _envs():
    import yaml
    with open(ENVS, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def box(name):
    """One declared box shape. RAISES on an unknown name rather than defaulting.

    A typo that silently fell back to `default` would rent an A100 for a job
    that declared `dense`, and the bill is the only place it would show.
    """
    b = (_envs().get("boxes") or {}).get(name)
    if b is None:
        raise SystemExit("no box %r in %s -- declared: %s"
                         % (name, os.path.relpath(ENVS, ROOT),
                            ", ".join(sorted((_envs().get("boxes") or {})))))
    return b


def state(new=None):
    if new is not None:
        os.makedirs(os.path.dirname(STATE), exist_ok=True)
        with open(STATE, "w", encoding="utf-8") as fh:
            json.dump(new, fh, indent=1)
        return new
    if os.path.exists(STATE):
        with open(STATE, encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def vastai(*args, capture=True):
    r = subprocess.run(["vastai"] + list(args), capture_output=capture, text=True)
    if capture and r.returncode != 0:
        raise SystemExit("vastai %s failed: %s" % (args[0], (r.stderr or "").strip()[:200]))
    return (r.stdout or "").strip() if capture else ""


def _blocked():
    try:
        with open(BLOCKLIST, encoding="utf-8") as fh:
            return set(json.load(fh).get("machines", {}))
    except Exception:                                           # noqa: BLE001
        return set()


def blocklist(machine_id, symptom):
    """Record a machine that failed in a way retrying cannot fix.

    Dated so it can age out: a machine bad today may be fine next month, and a
    permanent blocklist silently shrinks the market.
    """
    if not machine_id:
        return
    os.makedirs(os.path.dirname(BLOCKLIST), exist_ok=True)
    try:
        with open(BLOCKLIST, encoding="utf-8") as fh:
            d = json.load(fh)
    except Exception:                                           # noqa: BLE001
        d = {"machines": {}}
    m = d.setdefault("machines", {}).setdefault(str(machine_id), {})
    m["seen"] = time.strftime("%Y-%m-%d")
    m["failures"] = int(m.get("failures", 0)) + 1
    m["symptom"] = symptom
    with open(BLOCKLIST, "w", encoding="utf-8") as fh:
        json.dump(d, fh, indent=1)
    print("    machine %s blocklisted: %s" % (machine_id, symptom), file=sys.stderr)


def query(b):
    """The vast.ai search string implied by a declared box."""
    q = []
    if b.get("gpu_name"):
        q.append("gpu_name=%s" % b["gpu_name"])
    q.append("num_gpus=%d" % int(b.get("num_gpus", 1)))
    for field, key in (("gpu_ram", "min_gpu_ram"), ("disk_space", "disk_gb"),
                       ("inet_down", "min_inet_down_mbps"),
                       ("reliability", "min_reliability")):
        if b.get(key) is not None:
            q.append("%s>=%s" % (field, b[key]))
    if b.get("cuda_max_good") is not None:
        q.append("cuda_max_good<=%s" % b["cuda_max_good"])
    q.append("rentable=true")
    return " ".join(q)


def offers(name, limit=8):
    """Ranked offers for a box, cheapest first, blocklisted machines removed."""
    b = box(name)
    raw = vastai("search", "offers", query(b), "-o", "dph", "--raw")
    try:
        got = json.loads(raw)
    except Exception:                                           # noqa: BLE001
        return []
    bad = _blocked()
    out = [o for o in got if str(o.get("machine_id")) not in bad]
    return out[:limit]


def verify_reachable(host, port, tries=3, wait=10):
    """(reachable, route). A box that never answers is a STATE, not a race.

    The runbook's discriminator: retrying is correct for a RACE and never for a
    STATE. Three tries with a wait covers boot; beyond that the machine is not
    coming up and the answer is another offer.
    """
    for _ in range(tries):
        r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no",
                            "-o", "UserKnownHostsFile=/dev/null",
                            "-o", "LogLevel=ERROR", "-o", "ConnectTimeout=10",
                            "-p", str(port), "root@%s" % host, "true"],
                           capture_output=True)
        if r.returncode == 0:
            return True
        time.sleep(wait)
    return False


def ssh_run(st, command, capture=True):
    cmd = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null",
           "-o", "LogLevel=ERROR", "-p", str(st["ssh_port"]),
           "root@%s" % st["ssh_host"], command]
    return subprocess.run(cmd, capture_output=capture, text=True)


def rsync(st, src, dst, from_remote=False, exclude=()):
    ssh = ("ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "
           "-o LogLevel=ERROR -p %s" % st["ssh_port"])
    cmd = ["rsync", "-az", "--partial", "-e", ssh]
    for pat in exclude:
        cmd += ["--exclude", pat]
    if from_remote:
        os.makedirs(dst, exist_ok=True)
        cmd += ["root@%s:%s/" % (st["ssh_host"], src), dst + "/"]
    else:
        cmd += [src + "/", "root@%s:%s/" % (st["ssh_host"], dst)]
    return subprocess.run(cmd)


def coverage(model, producer=None):
    """What a run actually WROTE, counted from the stash. Never what it attempted.

    *"An orphaned vLLM engine holding the card makes every unit complete in 0.3
    min having produced nothing, and the health loop reports it as throughput.
    Check what was WRITTEN, never what was attempted."*
    """
    from .checkpoint import Checkpoint
    from .runners import PRODUCER
    ck = Checkpoint(model)
    out = {}
    for prod, st in ck.stashes():
        n = {}
        for k, _v in st.items():
            rv = k.get("rule_version")
            n[(rv, k.get("rules", ""), bool(k.get("topup")))] = \
                n.get((rv, k.get("rules", ""), bool(k.get("topup"))), 0) + 1
        if not producer or prod == producer:
            out[prod] = {"|".join(str(x) for x in kk): vv for kk, vv in sorted(n.items())}
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["boxes", "offers", "launch", "status",
                                    "coverage", "stop"])
    ap.add_argument("--box", default="dense")
    ap.add_argument("--model")
    ap.add_argument("--limit", type=int, default=8)
    ap.add_argument("--yes", action="store_true", help="rent without confirming")
    a = ap.parse_args()

    if a.cmd == "boxes":
        for name, b in sorted((_envs().get("boxes") or {}).items()):
            print("  %-14s %-28s %s" % (name, b.get("image", ""), query(b)))
        return 0

    if a.cmd == "offers":
        got = offers(a.box, a.limit)
        print("  %s -> %s" % (a.box, query(box(a.box))))
        for o in got:
            print("    id=%-10s machine=%-8s $%.3f/h  %s x%s  %sGB  %s Mbps  rel=%.2f"
                  % (o.get("id"), o.get("machine_id"), o.get("dph_total", 0),
                     o.get("gpu_name"), o.get("num_gpus"), o.get("disk_space"),
                     o.get("inet_down"), o.get("reliability", 0)))
        if not got:
            print("    NO OFFERS -- loosen the box or check the blocklist (%d machines)"
                  % len(_blocked()))
        return 0

    if a.cmd == "status":
        st = state()
        if not st:
            print("  no instance recorded"); return 0
        print("  %s" % json.dumps(st, indent=1))
        return 0

    if a.cmd == "coverage":
        if not a.model:
            raise SystemExit("coverage needs --model")
        print(json.dumps(coverage(a.model), indent=1))
        return 0

    if a.cmd == "stop":
        st = state()
        if not st.get("instance_id"):
            print("  nothing to stop"); return 0
        vastai("destroy", "instance", str(st["instance_id"]), capture=False)
        state({})
        print("  destroyed %s" % st["instance_id"])
        return 0

    if a.cmd == "launch":
        raise SystemExit(
            "launch is not implemented yet -- `offers` and `boxes` are, and they "
            "are the read-only half.\n"
            "Renting spends money on RH's own word (CLAUDE.md), so the executor "
            "lands in a second commit with the confirmation path explicit, not "
            "bundled into the port of the read-only surface.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
