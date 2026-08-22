#!/usr/bin/env python
"""Two runtime guards for a rented box. Both catch failures that LOOK HEALTHY.

    python scripts/box_guard.py --selftest        # validate against the real incidents
    python scripts/box_guard.py --models a b --cells 500 --elapsed 900
    python scripts/box_guard.py --empty ~/malignment-data/twp/MODEL/BOX

## THE TWO FAILURES THAT PRODUCE OUTPUT AND ARE STILL WRONG

The health loop in `fleet_launch._await` distinguishes done / failed / dead /
stalled, and "stalled" means CELLS NOT MOVING. Both failures below keep cells
moving, so every existing signal reads green.

**1. THE KERNELS ARE INSTALLED AND NOT IN USE -- 178x, SILENT.** `Zamba2-7B`
without mamba-ssm/causal-conv1d loads and runs without erroring at **183.4
s/cell against 1.03 with them** (152 h projected against 51 min).
`environments.yaml` says in bold: *"VERIFY IN USE, NOT MERELY INSTALLED:
transformers falls back SILENTLY."* Nothing implemented that check -- grepping
this repo for a fast-path verification returns nothing.

**AND THE OBVIOUS IMPLEMENTATION DOES NOT WORK.** The same file records that
while Zamba2 was failing, `is_mamba_ssm_available()` and
`is_causal_conv1d_available()` both returned True and all five entry points
imported, while the log still carried the fast-path warning -- *"a fast-path
warning emitted DURING a failed load is not evidence about the kernels"*. So
asking the library whether it has the kernels answers a different question from
whether this model is using them.

**The rate answers the real question and needs no introspection at all.** A box
running 178x slower than the recorded rate for its own models is broken,
whatever the cause -- kernels, wrong card, thermal, contention. This guard is
therefore deliberately ignorant of mechanism.

**2. ALL-NaN LOGITS PASS EVERY STRUCTURAL GATE.** Falcon-H1-7B at fp16 returned
all-NaN logits on **2,583/2,583 prompts** -- 5,166 empty cells that satisfied
conservation EXACTLY, because `sum([]) + 1.0 == 1.0`. Cells were written, the
count moved, the ledger closed. The only visible symptom is that the cells hold
no words.

## WHY A MINIMUM SAMPLE IS PART OF THE GUARD, NOT A NICETY

A rate measured on 3 cells is a load-time measurement wearing a throughput
label: OLMoE was booked at 10-15.5 s/cell from a three-cell sample and measured
1.9 s/cell over 277, and that error removed four models from a roster. Both
guards refuse to return a verdict below `MIN_CELLS`.
"""
import argparse
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

#: Below this, a cold load is most of the wall clock and the ratio is not a
#: throughput. Same constant, same reason, as `rates.MIN_CELLS`.
MIN_CELLS = 25

#: Per-model rates span 0.155..6.04 s/cell (39x) and a shard mixes them, so the
#: band must be wide enough that an unlucky model order does not trip it. The
#: signal it exists to catch is 178x. 8 sits an order of magnitude below that
#: and an order above ordinary mix variation.
SLOW_FACTOR = 8.0

#: Falcon-H1 produced 100% empty. A model can legitimately produce a few empty
#: cells (every candidate below theta), so the trigger is a MAJORITY over a real
#: sample rather than any single one.
EMPTY_FRACTION = 0.5


def throughput_verdict(models, n_cells, elapsed_s, device="cuda",
                       factor=SLOW_FACTOR):
    """(verdict, detail) -- 'OK' | 'SLOW' | 'UNKNOWN'.

    `expected` is the MEAN of the shard's per-model recorded rates. Not the
    minimum: a shard's fastest model would make every mixed shard look slow.
    Not a global constant: `SEC_PER_CELL` was one number twice and both times
    it was one model's measurement standing in for 144.
    """
    if n_cells < MIN_CELLS:
        return "UNKNOWN", ("%d cells is below the %d-cell floor; a rate here is "
                           "load time wearing a throughput label"
                           % (n_cells, MIN_CELLS))
    if elapsed_s <= 0:
        return "UNKNOWN", "no elapsed time"
    from malignment import rates
    est, guessed = rates.estimate(sorted(models), device)
    per = [est[m][0] for m in sorted(models) if est.get(m) and est[m][0]]
    if not per:
        return "UNKNOWN", "no recorded rate for any model on this shard"
    expected = sum(per) / len(per)
    observed = elapsed_s / float(n_cells)
    ratio = observed / expected if expected else float("inf")
    detail = ("observed %.3f s/cell vs expected %.3f (%.1fx), %d/%d models "
              "measured, %d guessed"
              % (observed, expected, ratio, len(per), len(models), len(guessed)))
    if ratio > factor:
        return "SLOW", detail + (" -- OVER the %.0fx band. Check the kernels are "
                                 "IN USE, not merely installed." % factor)
    return "OK", detail


def emptiness_verdict(path, limit=4000, threshold=EMPTY_FRACTION):
    """(verdict, detail) -- fraction of stored cells holding NO words.

    Reads the box's own jsonl rather than ClickHouse: this must work ON the box,
    before anything is ingested, which is the only moment the finding is cheap.
    """
    files = []
    if os.path.isdir(path):
        files = sorted(glob.glob(os.path.join(path, "**", "data.jsonl"),
                                 recursive=True))
    elif os.path.exists(path):
        files = [path]
    if not files:
        return "UNKNOWN", "no data.jsonl under %s" % path
    n = empty = 0
    for f in files:
        with open(f, errors="replace") as fh:
            for line in fh:
                if n >= limit:
                    break
                try:
                    r = json.loads(line)
                except Exception:                                # noqa: BLE001
                    continue
                if "rows" not in r:
                    continue
                n += 1
                if not (r.get("rows") or []):
                    empty += 1
        if n >= limit:
            break
    if n < MIN_CELLS:
        return "UNKNOWN", "%d cells is below the %d-cell floor" % (n, MIN_CELLS)
    frac = empty / float(n)
    detail = "%d/%d cells hold no words (%.1f%%)" % (empty, n, 100 * frac)
    if frac > threshold:
        return "EMPTY", detail + (" -- conservation CANNOT see this: sum([]) + "
                                  "1.0 == 1.0. Suspect fp16 on a model needing "
                                  "bfloat16.")
    return "OK", detail


def selftest():
    """Watch both guards FIRE on the real incidents, and stay quiet otherwise.

    A guard that has never been observed refusing is a belief, not a guard.
    """
    ok = True

    def show(name, got, want):
        nonlocal ok
        good = got == want
        ok = ok and good
        print("   %-46s %-8s %s" % (name, got, "ok" if good else "EXPECTED " + want))

    print("throughput_verdict -- synthetic rates, no ClickHouse needed")

    class _FakeRates:
        @staticmethod
        def estimate(models, device, only=None, fallback=True):
            return {m: (1.03, "measured") for m in models}, []

    import types
    fake = types.ModuleType("malignment.rates")
    fake.estimate = _FakeRates.estimate
    sys.modules["malignment.rates"] = fake
    import malignment
    malignment.rates = fake

    v, d = throughput_verdict(["Zyphra/Zamba2-7B"], 100, 100 * 183.4)
    show("Zamba2 at 183.4 s/cell (kernels idle)", v, "SLOW")
    v, d = throughput_verdict(["Zyphra/Zamba2-7B"], 100, 100 * 1.03)
    show("Zamba2 at 1.03 s/cell (kernels live)", v, "OK")
    v, d = throughput_verdict(["Zyphra/Zamba2-7B"], 3, 3 * 183.4)
    show("same slowness on a 3-cell sample", v, "UNKNOWN")
    v, d = throughput_verdict(["Zyphra/Zamba2-7B"], 100, 100 * 5.0)
    show("5x slow -- inside the mix band, must NOT fire", v, "OK")

    print("emptiness_verdict -- synthetic cells")
    import tempfile
    d0 = tempfile.mkdtemp()
    with open(os.path.join(d0, "data.jsonl"), "w") as fh:
        for _ in range(200):
            fh.write(json.dumps({"rows": [], "conservation": "1.000000"}) + "\n")
    v, _ = emptiness_verdict(d0)
    show("Falcon-H1 fp16: 200/200 empty, cons 1.000000", v, "EMPTY")
    d1 = tempfile.mkdtemp()
    with open(os.path.join(d1, "data.jsonl"), "w") as fh:
        for i in range(200):
            fh.write(json.dumps({"rows": ([] if i < 5 else [{"word": "a"}])}) + "\n")
    v, _ = emptiness_verdict(d1)
    show("healthy run with 5/200 legitimately empty", v, "OK")
    d2 = tempfile.mkdtemp()
    with open(os.path.join(d2, "data.jsonl"), "w") as fh:
        for _ in range(10):
            fh.write(json.dumps({"rows": []}) + "\n")
    v, _ = emptiness_verdict(d2)
    show("10 empty cells -- below the floor, no verdict", v, "UNKNOWN")

    print("\n%s" % ("all guards fire and stay quiet correctly"
                    if ok else "SELFTEST FAILED"))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--models", nargs="*", default=[])
    ap.add_argument("--cells", type=int, default=0)
    ap.add_argument("--elapsed", type=float, default=0.0, help="seconds")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--factor", type=float, default=SLOW_FACTOR)
    ap.add_argument("--empty", default=None, help="dir or data.jsonl to scan")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    rc = 0
    if a.models and a.cells:
        v, d = throughput_verdict(a.models, a.cells, a.elapsed, a.device, a.factor)
        print("throughput %-8s %s" % (v, d))
        rc |= 1 if v == "SLOW" else 0
    if a.empty:
        v, d = emptiness_verdict(a.empty)
        print("emptiness  %-8s %s" % (v, d))
        rc |= 1 if v == "EMPTY" else 0
    return rc


if __name__ == "__main__":
    sys.exit(main())
