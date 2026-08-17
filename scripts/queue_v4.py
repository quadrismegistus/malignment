#!/usr/bin/env python
"""Work through checkpoints under v4's ADOPTED rules, one at a time, forever.

    python scripts/queue_v4.py --tier FLUENT MARGINAL
    python scripts/queue_v4.py --models a b c

**ORDERED BY EXPECTED EFFECT, NOT ALPHABETICALLY.** The v4 correction is a
tokenizer defect whose MAGNITUDE is a model property: Qwen2.5-7B (FLUENT, 8,624
CJK chars) moved +4.05% median on zh, Mistral (PARTIAL, 1,456) moved +0.001%. So
the queue runs high `cjk_chars` first -- the cells where the rule bites, on the
models where it bites -- and a defect or a surprise surfaces on the first
checkpoint rather than the twentieth.

**ONE MODEL MUST NOT END THE QUEUE**, the same rule `runners` applies to one
prompt inside a checkpoint. A load failure is recorded and the queue moves on;
`Checkpoint.done(rules)` makes every restart resume rather than repeat.

Weights must already be cached: this is the local MPS stream, not a fleet, and
downloading 15 GB between checkpoints would make the GPU idle for most of it.
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from venvs import venv_for  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEAS = os.path.join(ROOT, "roster", "models", "measurements.json")


def cached(m):
    """Weights on disk. A repo with only a README is NOT cached -- checked the
    hard way once, when a 135M fixture turned out to hold no safetensors."""
    pat = os.path.expanduser("~/.cache/huggingface/hub/models--%s/snapshots/*/*"
                             % m.replace("/", "--"))
    return any(f.endswith((".safetensors", ".bin")) for f in glob.glob(pat))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier", nargs="*", default=["FLUENT", "MARGINAL"])
    ap.add_argument("--models", nargs="*")
    ap.add_argument("--python", default=None,
                    help="override; by default each model gets the venv its "
                         "roster profile requires")
    a = ap.parse_args()

    if a.models:
        todo = [(m, 0) for m in a.models]
    else:
        vocab = json.load(open(MEAS))["sections"]["vocab"]["models"]
        todo = sorted(((m, v["cjk_chars"]) for m, v in vocab.items()
                       if v["cjk_tier"] in a.tier and cached(m)),
                      key=lambda r: -r[1])
    print("queue: %d checkpoints, ordered by cjk_chars desc" % len(todo), flush=True)
    for m, n in todo:
        print("  %-46s cjk_chars=%-7d %s"
              % (m, n, os.path.basename(venv_for(m))), flush=True)

    for i, (m, n) in enumerate(todo, 1):
        print("\n%s\n[%d/%d] %s  (cjk_chars=%d)\n%s"
              % ("=" * 68, i, len(todo), m, n, "=" * 68), flush=True)
        t0 = time.time()
        #: **THE VENV COMES FROM THE ROSTER, NOT FROM A DEFAULT.** Baichuan2 is
        #: profile `tf457` -- *"transformers 5.x CANNOT RUN this; pin 4.57.1"* --
        #: and this queue hardcoded `.venv` (5.x), so both arms failed 2,706
        #: prompts each with `Cannot copy out of meta tensor`. That IS the
        #: declared failure, arriving as a stack trace instead of a refusal.
        #:
        #: I built the split this morning and `venvs.py which MODEL` to resolve
        #: it, then wrote a queue that ignored both. Spent an hour patching
        #: rotary caches before RH said to read the environment notes.
        py = a.python or os.path.join(venv_for(m), "bin", "python")
        r = subprocess.run([py, "-u", os.path.join(ROOT, "scripts", "run_v4.py"),
                            "--model", m, "--cache"],
                           cwd=ROOT, capture_output=True, text=True)
        tail = [l for l in (r.stdout or "").splitlines() if l.strip()][-3:]
        print("  exit=%d  %.1f min" % (r.returncode, (time.time() - t0) / 60), flush=True)
        for l in tail:
            print("  | %s" % l[:150], flush=True)
        if r.returncode != 0:
            #: recorded, not fatal -- one checkpoint must not end the queue
            err = [l for l in (r.stderr or "").splitlines() if l.strip()][-2:]
            for l in err:
                print("  ! %s" % l[:150], flush=True)
    print("\nQUEUE DONE", flush=True)


if __name__ == "__main__":
    sys.exit(main())
