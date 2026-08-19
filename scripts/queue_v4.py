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
    ap.add_argument("--no-endpoints-first", action="store_true",
                    help="disable endpoint priority; order by cjk_chars alone")
    ap.add_argument("--only", choices=["slots", "cjk", "latin"], default=None,
                    help="pass through to run_v4.py: measure one tranche of the "
                         "population. slots and cjk carry the information; latin "
                         "is 76%% of the runtime and v4 == v3 on it.")
    ap.add_argument("--python", default=None,
                    help="override; by default each model gets the venv its "
                         "roster profile requires")
    ap.add_argument("--max-model-min", type=float, default=90.0,
                    help="kill a model exceeding this many minutes and move on. "
                         "0 disables. Default 90: generous for a 7B cold load "
                         "plus 2,983 cells at any plausible rate, and far under "
                         "the 152 HOURS Zamba2-7B would have taken.")
    a = ap.parse_args()

    #: **`--models` USED TO HARDCODE cjk_chars=0**, so an explicit roster printed
    #: "ordered by cjk_chars desc" above nineteen models all showing 0 -- while
    #: actually preserving argv order. Harmless to the cells and not to the
    #: reader: the ordering is the whole reason this file exists (run where the
    #: rule BITES first, so a defect surfaces on checkpoint one rather than
    #: twenty), and a header claiming it while not doing it is worse than no
    #: header. Same lookup for both paths now; a model absent from the vocab
    #: measurement sorts last and SAYS SO rather than silently reading 0.
    vocab = json.load(open(MEAS))["sections"]["vocab"]["models"]
    if a.models:
        todo = sorted(((m, vocab.get(m, {}).get("cjk_chars", -1)) for m in a.models),
                      key=lambda r: -r[1])
    else:
        todo = sorted(((m, v["cjk_chars"]) for m, v in vocab.items()
                       if v["cjk_tier"] in a.tier and cached(m)),
                      key=lambda r: -r[1])
    #: **THE BASE->ENDPOINT PAIR IS THE UNIT THE PAPER COMPARES**, so those models
    #: run before the arms that only sit in a lineage. `roster.endpoints()` gives
    #: 50 bases and their 50 commodity-form endpoints; the other 44 members of
    #: those lineages are intermediates, ablations and method variants, which
    #: answer their own questions and block nothing.
    #:
    #: Secondary key stays cjk_chars, so within each group the models where the
    #: v4 rule actually bites still come first. RH's ask, 2026-08-18.
    if not a.no_endpoints_first:
        from malignment import roster as _r
        _eps, _ = _r.endpoints()
        prio = set(_eps) | set(_eps.values())
        todo = sorted(todo, key=lambda r: (r[0] not in prio, -r[1]))
        n_p = sum(1 for m, _n in todo if m in prio)
        print("queue: ENDPOINTS FIRST -- %d of %d are a base or an endpoint"
              % (n_p, len(todo)), flush=True)
    unknown = [m for m, n in todo if n < 0]
    if a.only:
        print("queue: TRANCHE=%s" % a.only, flush=True)
    #: Names BOTH keys. It said "ordered by cjk_chars desc" while endpoint
    #: membership was the primary sort -- true of the secondary key and false of
    #: the order. Fifth time in one day a line described something its run was
    #: not doing; the others were the loader's rule_version, ingest's includable
    #: header, the topup instrument line, and this file's own hardcoded
    #: cjk_chars=0.
    print("queue: %d checkpoints, ordered by %scjk_chars desc%s"
          % (len(todo),
             "" if a.no_endpoints_first else "endpoint membership, then ",
             "" if not unknown else
             "  (%d not in the vocab measurement, sorted last)" % len(unknown)),
          flush=True)
    for m, n in todo:
        print("  %-46s cjk_chars=%-7s %s"
              % (m, "?" if n < 0 else n, os.path.basename(venv_for(m))), flush=True)

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
        #: **A PER-MODEL WALL-CLOCK CEILING, BECAUSE ONE MODEL CAN EAT A SHARD.**
        #: `Zyphra/Zamba2-7B` measured **183 s/cell** on an RTX 4090 -- 152 hours
        #: for its 2,983 cells -- while the fleet planner, having no recorded rate
        #: for it, priced it at the 0.35 s/cell fallback. It is a hybrid SSM and
        #: the box had no `mamba_ssm`/`causal_conv1d`, so it ran the slow path.
        #:
        #: Without a ceiling that model blocks the other TEN in its shard forever,
        #: and every health signal reads normal: tmux up, GPU at 100%, cells
        #: creeping up one per three minutes. **A guessed rate can be wrong by
        #: 500x, so the guess must not be able to consume the run** -- the model is
        #: killed, RECORDED as timed out, and the queue moves on. Nothing is lost:
        #: twp writes and flushes per prompt, so its cells survive and a later run
        #: resumes from them.
        try:
            r = subprocess.run([py, "-u", os.path.join(ROOT, "scripts", "run_v4.py"),
                                "--model", m, "--cache"]
                               + (["--only", a.only] if a.only else []),
                               cwd=ROOT, capture_output=True, text=True,
                               timeout=(a.max_model_min * 60 if a.max_model_min else None))
        except subprocess.TimeoutExpired:
            print("  TIMED OUT after %.0f min -- moving on. This model is not "
                  "broken, it is SLOW: measure it and give it its own run rather "
                  "than letting it block the shard." % a.max_model_min, flush=True)
            continue
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
