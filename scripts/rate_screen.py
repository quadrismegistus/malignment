#!/usr/bin/env python
"""Measure a SMALL sample of every fleet model that has no rate, before renting.

    python scripts/rate_screen.py --dry-run
    python scripts/rate_screen.py --cells 30

## WHY THIS EXISTS

`Zyphra/Zamba2-7B` ran at **183 s/cell** on a rented RTX 4090 -- 152 hours for
its 2,983 cells -- while `fleet_shards` priced it at the 0.35 s/cell FALLBACK,
because nothing had ever measured it. The shard was planned at 3.2 hours and held
at least 300. It was found by renting a box and watching cells creep up one per
three minutes.

**37 of 144 fleet models have no recorded rate, and every one of them is a
Zamba2-shaped hole.** The fallback is not a small error bar; it is an unbounded
one, and the plan cannot tell which model holds it. Thirty cells locally costs
nothing and converts each unknown into a bound.

RH approved this over launching first: *"yes good idea"*.

## WHAT IT DELIBERATELY DOES

**Derives its worklist from the rates store and the plan**, never a typed list --
the same rule as `fleet_shards`, and for the same reason: a list of "models that
need measuring" is stale the moment one is measured.

**Marks every observation with a note.** A screen shares the GPU with whatever
else is running and reads HIGH, which is safe for catching an outlier and wrong
as a planning number. `rates.rate_for` prefers un-noted rows and says so when all
it has are noted ones -- so a screen can never silently become the number a fleet
is planned on.

**Uses the median of consecutive deltas**, which `runners.run` now records: the
cold load sits before the first cell and enters no delta, so 30 cells is a real
throughput rather than a load measurement wearing a throughput label. That
distinction cost four OLMoE models a place on a roster earlier the same day.

**Spawns per model with `venv_for`**, because a model's declared environment is
not optional -- ignoring it is what broke Baichuan2 for an hour and killed a
72-model sweep at 27.
"""
import argparse
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

from venvs import venv_for                                      # noqa: E402

from malignment import rates                                    # noqa: E402


def todo(device="mps", plan=None):
    """Fleet models with no usable rate on `device`. Derived, never typed."""
    import json
    from fleet_shards import lineage_work
    if plan and os.path.exists(plan):
        models = sorted({m for b in json.load(open(plan))["boxes"]
                         for m in b["models"]})
    else:
        models = sorted({m for w in lineage_work() for m in w[1]})
    obs = rates.load()
    out = []
    for m in models:
        sec, _why = rates.rate_for(m, device, obs=obs)
        if sec is None:
            out.append(m)
    return models, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cells", type=int, default=30,
                    help="prompts per model. Must exceed rates.MIN_CELLS (%d) or "
                         "the observation will be refused by its own store."
                         % rates.MIN_CELLS)
    ap.add_argument("--device", default="mps")
    ap.add_argument("--plan", default="data/fleet_shards.json")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only-slow", action="store_true",
                    help="stop at the first model that exceeds --alarm-sec, "
                         "rather than finishing its sample")
    ap.add_argument("--alarm-sec", type=float, default=20.0,
                    help="s/cell above which a model is called out. 20 is ~3x the "
                         "slowest thing ever measured here (Olmo-Hybrid, 6.04) "
                         "and ~1/9th of Zamba2's 183.")
    a = ap.parse_args()

    if a.cells <= rates.MIN_CELLS:
        raise SystemExit("--cells must exceed MIN_CELLS=%d, or rate_for() will "
                         "refuse every row this writes -- a screen whose output "
                         "its own store rejects is worse than no screen."
                         % rates.MIN_CELLS)

    models, need = todo(a.device, os.path.join(ROOT, a.plan))
    print("fleet models %d | no rate on %s: %d" % (len(models), a.device, len(need)))
    for m in need:
        print("   %-52s %s" % (m[:52], os.path.basename(venv_for(m))))
    if a.dry_run:
        print("\nDRY RUN -- nothing measured.")
        return 0

    #: Every row this run writes is marked. See the module docstring.
    env = dict(os.environ)
    env["MALIGNMENT_RATE_NOTE"] = ("screen: %d cells, GPU possibly shared"
                                   % a.cells)
    slow, done, failed = [], [], []
    for i, m in enumerate(need, 1):
        py = os.path.join(venv_for(m), "bin", "python")
        t0 = time.time()
        print("\n[%d/%d] %s" % (i, len(need), m), flush=True)
        r = subprocess.run([py, "-u", os.path.join(HERE, "run_v4.py"),
                            "--model", m, "--cache", "--limit", str(a.cells)],
                           cwd=ROOT, capture_output=True, text=True)
        mins = (time.time() - t0) / 60
        #: **READ THE RATE BACK FROM THE STORE, NOT FROM THIS PROCESS'S CLOCK.**
        #: Wall time here includes the download and the load; the store holds the
        #: median inter-cell delta, which is the thing being screened for.
        sec, why = rates.rate_for(m, a.device)
        if r.returncode:
            err = [l for l in (r.stderr or "").splitlines() if l.strip()][-1:]
            print("  FAILED rc=%d %.1f min  %s"
                  % (r.returncode, mins, (err or ["?"])[0][:110]), flush=True)
            failed.append((m, (err or ["?"])[0][:160]))
            continue
        print("  %.1f min wall | %s s/cell  (%s)"
              % (mins, "%.2f" % sec if sec else "no rate recorded", why), flush=True)
        done.append((m, sec))
        if sec and sec >= a.alarm_sec:
            hrs = sec * 2983 / 3600.0
            print("  *** SLOW: %.1f s/cell -> %.0f h for a full 2,983-prompt pass"
                  % (sec, hrs), flush=True)
            slow.append((m, sec, hrs))
            if a.only_slow:
                break

    print("\n" + "=" * 66)
    print("screened %d | slow %d | failed %d" % (len(done), len(slow), len(failed)))
    for m, sec, hrs in sorted(slow, key=lambda x: -x[1]):
        print("  SLOW   %-46s %8.2f s/cell  %6.0f h" % (m[:46], sec, hrs))
    for m, e in failed:
        print("  FAILED %-46s %s" % (m[:46], e[:60]))
    #: A model that FAILS here would fail on a box too, and finding that out for
    #: free is the same win as finding out it is slow.
    return 0


if __name__ == "__main__":
    sys.exit(main())
