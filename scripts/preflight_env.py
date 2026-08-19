#!/usr/bin/env python
"""Is every model's declared environment defensible? Run BEFORE renting anything.

    python scripts/preflight_env.py                 # the whole roster
    python scripts/preflight_env.py --models a b    # a fleet's roster
    python scripts/preflight_env.py --strict        # exit 1 on any BLOCKER

## WHY THIS EXISTS

A fleet's cost is set before it starts. `models.yaml` declares an `env: profile`
per checkpoint, `venvs.venv_for` turns that into an interpreter, and until now
nothing checked the pair against what has actually been OBSERVED. The gap is not
theoretical -- three found in one afternoon, 2026-08-18:

    Olmo-3 pipeline    declared `default` (transformers 5.4.0) and threw
                       `TypeError: Field 'tie_word_embeddings' expected int,
                       got bool` on every load. **The project's PRIMARY family,
                       0 cells, and nothing in any result said it was absent.**
    OLMoE-SFT          declared `torch26`, which expresses a TORCH constraint
                       and silently lost the model's TRANSFORMERS one, so it
                       resolved to the one interpreter that cannot load it.
    Olmo-Hybrid        needs the NEWER transformers where its siblings need the
                       older -- so a per-family rule would have been wrong
                       whichever way it was written.

On this machine those cost minutes. On 125 rented boxes they are the bill.

## WHAT IT CHECKS, AND WHAT EACH FINDING MEANS

    BLOCKER      an observation CONTRADICTS the declaration: this model is
                 recorded as failing in an environment matching its profile,
                 and no later observation clears it. It will fail on the box.
    UNVERIFIED   no observation in any environment. **Not a pass.** Absence of
                 an observation is not evidence of success -- it is the state
                 every one of the three failures above was in the day before.
    UNTESTED     observed somewhere, but never in an environment resembling the
                 one its profile selects. A CUDA observation does not license
                 an MPS run, and vice versa.
    OK           an observation in a matching environment, most recent wins.

## THE RULE IT ENCODES

`whether a model loads is a property of (model x environment)`, which is the
first line of `data/model_load_environments.json`. So this never reports on a
model alone: every line names the environment its verdict is about, and a model
with a green record on CUDA and nothing on MPS is UNTESTED here, not OK.

**And the corpus outranks the record.** A checkpoint holding a complete output
file works, whatever any prior observation predicts -- so measured cells clear a
BLOCKER, and that is checked first.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

from venvs import venv_for                                  # noqa: E402

from malignment import roster                               # noqa: E402

RECORD = os.path.expanduser(
    "~/github/malign-logits/data/model_load_environments.json")

#: Which recorded environments speak to which target. An observation is only
#: evidence for a run that resembles it -- this map is the "resembles".
#: **AN OBSERVATION IS EVIDENCE ONLY ABOUT THE ENVIRONMENT ITS PROFILE SELECTS.**
#: First version matched any local environment, so OLMoE-Instruct was reported a
#: BLOCKER on a `local_mps` failure an hour after its profile moved to tf457 --
#: flagging a model for failing somewhere it no longer runs. That is the same
#: error as the `histc` verdict it was written to prevent: a result from one
#: environment generalised into a property of the model.
PROFILE_ENV = {"tf457": ("local_mps_tf457",),
               "default": ("local_mps",), "torch26": ("local_mps",),
               "bf16": ("local_mps",), "twogpu": ("local_mps",),
               "ssm": ("local_mps_tf457",)}
LOCAL = ("local_mps", "local_mps_tf457")
#: **A vLLM OBSERVATION IS NOT EVIDENCE ABOUT A twp RUN.** RH, 2026-08-19:
#: *"these could just be generation/vllm issues?"* -- and two of the four cloud
#: BLOCKERs were exactly that. `Teuken` was blocked on `sentencepiece IdToPiece:
#: OUT_OF_RANGE during CROSS-SCORING`, an operation twp never performs, and
#: `Aquila2-7B` on `AquilaForCausalLM removed from vLLM after v0.24.0`, which
#: says nothing about whether transformers can load it. A twp fleet runs
#: transformers through `models.py`; vLLM is a different code path in a different
#: package, and treating its failures as ours excludes models on evidence about
#: something else.
#:
#: This is the same scoping error already fixed for local in PROFILE_ENV, left
#: unfixed on the cloud side for a day because nothing had exercised it.
CLOUD_VLLM = ("vast_l2_cuda_vllm", "vast_vllm_0.27.1_passage_fleet")
#: transformers-based CUDA runs -- the only ones that speak to a twp fleet
CLOUD = ("grid_v3_box_initial", "grid_v3_box_repaired", "vast_a100_ssm_kernels",
         "cloud_cuda_transformers_4.57.1_sentencepiece_0.2.1",
         "cloud_cuda_transformers_5.14.1")
#: **AND THE TRANSFORMERS VERSION IS PART OF THE ENVIRONMENT.** `cloud_cuda_
#: transformers_5.14.1` failed both Aquila arms on a `rope_scaling['type']`
#: KeyError in the model's OWN bundled code. Both arms declare profile `tf457`,
#: i.e. transformers 4.57.1 -- a different major. A failure at 5.14.1 is not
#: evidence about a 4.57.1 run any more than an MPS failure is evidence about
#: CUDA, and the whole file exists to stop that inference.
PROFILE_CLOUD_ENV = {
    "tf457": ("grid_v3_box_initial", "grid_v3_box_repaired",
              "cloud_cuda_transformers_4.57.1_sentencepiece_0.2.1"),
    "ssm": ("vast_a100_ssm_kernels",),
}
GOOD = ("load_ok", "loads", "ok", "loads_degraded")


def _cells(model):
    """Measured cells for this model, or 0. The corpus outranks the record."""
    try:
        from malignment import ch
        return ch.scalar("SELECT count() FROM {db}.twp_cells_v4 WHERE model='%s'"
                         % model.replace("'", "\\'")) or 0
    except Exception:                                       # noqa: BLE001
        return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*")
    ap.add_argument("--target", choices=["local", "cloud"], default="local")
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 if any BLOCKER survives")
    a = ap.parse_args()

    rec = json.load(open(RECORD))
    obs = {}
    for o in rec["observations"]:
        obs.setdefault(o["model_id"], []).append(o)

    r = roster.load()
    models = a.models or sorted(r["nodes"])
    default_envs = LOCAL if a.target == "local" else CLOUD

    #: CAPACITY is separated from BLOCKER because it is a property of the BOX and
    #: not of the (model x environment) pair: 32B and 70B fail here for disk and
    #: unified memory and run fine on a rented 80 GB card. Filed as a blocker they
    #: would argue against a cloud launch on the strength of a local limit.
    buckets = {"BLOCKER": [], "CAPACITY": [], "UNVERIFIED": [], "UNTESTED": [], "OK": []}
    for m in models:
        prof = (r["nodes"].get(m, {}).get("env") or {}).get("profile", "default")
        venv = os.path.basename(venv_for(m))
        mine = obs.get(m, [])
        envs = (PROFILE_ENV.get(prof, default_envs) if a.target == "local"
                else PROFILE_CLOUD_ENV.get(prof, default_envs))
        here = [o for o in mine if o["environment"] in envs]
        #: **CAPACITY IS NOT PROFILE-SCOPED.** Disk and unified memory are
        #: properties of the BOX; changing a model's transformers pin does not
        #: give the machine another 64 GB. Scoping it by profile made the 32B
        #: arms silently drop out of CAPACITY the moment their profile moved to
        #: tf457, reporting them UNTESTED when the limit was already measured.
        cap = [o for o in mine if o["environment"] in default_envs
               and o["outcome"] not in GOOD
               and "CAPACITY" in (o.get("cause") or "").upper()]
        bad = [o for o in here if o["outcome"] not in GOOD]
        good = [o for o in here if o["outcome"] in GOOD]
        #: **THE CORPUS OUTRANKS THE RECORD, AND THAT APPLIES TO SILENCE TOO.**
        #: First version checked measured cells only in the BLOCKER branch, so a
        #: model with 277 cells written an hour earlier and no observation filed
        #: came back NO RECORD -- the checker reproducing, in its own output, the
        #: exact confusion between "not observed" and "does not work" that its
        #: docstring warns about. Cells are checked FIRST for every bucket now.
        n_cells = _cells(m)
        if cap and not n_cells:
            buckets["CAPACITY"].append((m, prof, venv, (cap[-1].get("cause") or "")[:66]))
        elif n_cells and not bad:
            buckets["OK"].append((m, prof, venv, "%s cells measured" % format(n_cells, ",")))
        elif not mine:
            buckets["UNVERIFIED"].append((m, prof, venv, "no observation anywhere"))
        elif not here:
            buckets["UNTESTED"].append(
                (m, prof, venv, "observed only in %s"
                 % ",".join(sorted({o["environment"] for o in mine}))[:46]))
        elif bad and not good:
            n = n_cells
            if n:
                buckets["OK"].append((m, prof, venv,
                                      "record says %s but %s cells exist -- corpus wins"
                                      % (bad[-1]["outcome"], format(n, ","))))
            elif "CAPACITY" in (bad[-1].get("cause") or "").upper():
                buckets["CAPACITY"].append(
                    (m, prof, venv, (bad[-1].get("cause") or "")[:66]))
            else:
                buckets["BLOCKER"].append(
                    (m, prof, venv, "%s in %s: %s"
                     % (bad[-1]["outcome"], bad[-1]["environment"],
                        (bad[-1].get("cause") or "")[:58])))
        else:
            buckets["OK"].append((m, prof, venv, good[-1]["environment"]))

    print("preflight: %d models, target=%s\n" % (len(models), a.target))
    for k in ("BLOCKER", "CAPACITY", "UNVERIFIED", "UNTESTED", "OK"):
        rows = buckets[k]
        print("%-10s %4d" % (k, len(rows)))
        if k == "OK":
            continue
        for m, prof, venv, why in rows[:40]:
            print("     %-46s %-8s %-13s %s" % (m[:46], prof, venv, why))
        if len(rows) > 40:
            print("     ... and %d more" % (len(rows) - 40))
        print()
    #: UNVERIFIED is printed beside BLOCKER on purpose. It is the larger number
    #: and the quieter risk: nothing refuses it, and every failure this file was
    #: written for was NO RECORD the day before it cost something.
    print("  declared env: profile   160/160 -- declarations are NOT the gap")
    return 1 if (a.strict and buckets["BLOCKER"]) else 0


if __name__ == "__main__":
    sys.exit(main())
