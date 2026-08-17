#!/usr/bin/env python
"""THE LOCAL ENVIRONMENTS, DERIVED FROM THE ROSTER RATHER THAN CHOSEN.

    python scripts/venvs.py plan             what venvs the roster implies, and why
    python scripts/venvs.py build            create/update them with uv
    python scripts/venvs.py which MODEL      which venv that checkpoint needs

## WHY MORE THAN ONE

**No single `transformers` satisfies the roster, and it is a two-sided
constraint** -- not a preference, and not fixable by upgrading:

    13 nodes CANNOT run 5.x   Pharia x2, Aquila x2, Baichuan2 x2, falcon-7b x2,
                              internlm2 x3 (profile `tf457`: "transformers 5.x
                              CANNOT RUN this"), Zamba2 x2 (pinned deviation)
     3 nodes CANNOT run 4.57  Olmo-Hybrid x3 -- `model_type: olmo_hybrid`, which
                              is ABSENT from 4.57.1's CONFIG_MAPPING_NAMES
                              (checked in the built venv, not inferred)

The corpus shows the same split independently: Pharia/Aquila/falcon-7b have
cells ONLY at 4.57.1, Olmo-Hybrid and MiniCPM5 ONLY at 5.14.1.

## THE DECLARATION IS THE SOURCE, AND THAT IS THE POINT

Nothing here names a model or a version. The venvs are GROUPED BY THE EFFECTIVE
`transformers` PIN each node declares in `roster/models/models.yaml` (`env:`
profile, plus any per-node deviation), and each venv installs the union of the
`packages:` those same nodes declare. So the roster's `env:` block acquires a
LOCAL CONSUMER instead of describing only what happens on a rented box -- add a
node that pins a third version and `plan` grows a third venv without anyone
editing this file.

**`requirements.txt` is not enough on its own and the reason is structural.** It
is derived by walking the ASTs of `malignment/*.py`, so it lists what OUR CODE
imports. `sentencepiece` and `protobuf` are imported by neither: they are needed
by MODELS (AmberSafe's loader falls back to TikToken without sentencepiece, then
demands protobuf). Two different dependency sets with two different sources, and
a venv needs the union. Adding them to `requirements.txt` by hand would break the
one property that file has.

## THE SENTENCEPIECE TRAP, WHICH THE SPLIT HAPPENS TO SOLVE

`default` resolves `sentencepiece` to 0.2.2 -- the version that fails internlm2's
SentencePiece->fast conversion outright. That is safe ONLY because internlm2 is
`tf457` and lands in the other venv at its declared `==0.2.1`. It is safe by
construction rather than by luck, but it is worth knowing that the two venvs
disagree about a package neither profile mentions in its `why`.
"""
import argparse
import collections
import os
import subprocess
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_YAML = os.path.join(ROOT, "roster", "models", "models.yaml")
ENVS_YAML = os.path.join(ROOT, "roster", "environments.yaml")

#: A pin that is a floor (`>=4.57`) does not distinguish an environment -- every
#: venv we build satisfies it. Only an EXACT pin forces a separate interpreter,
#: so that is what groups. `None` is the group that takes whatever is current.
def _exact(pin):
    pin = (pin or "").strip()
    return pin[2:].strip() if pin.startswith("==") else None


def _name_for(pin):
    return ".venv" if pin is None else ".venv-tf%s" % pin.replace(".", "")[:3]


def spec():
    """-> {venv_name: {pin, packages, profiles, models}} derived from the roster."""
    doc = yaml.safe_load(open(MODELS_YAML))
    envs = yaml.safe_load(open(ENVS_YAML))
    profiles = envs.get("profiles") or {}

    groups = collections.defaultdict(
        lambda: {"pin": None, "packages": {}, "profiles": set(), "models": []})
    for model, node in (doc.get("nodes") or {}).items():
        env = (node or {}).get("env") or {}
        prof = env.get("profile")
        #: a node's own `transformers:` OVERRIDES its profile's -- that is what a
        #: deviation is for, and Zamba2 is the case: profile `ssm` (>=4.57) with
        #: `transformers: ==4.57.1` beside it.
        pin = _exact(env.get("transformers")
                     or (profiles.get(prof) or {}).get("transformers"))
        g = groups[pin]
        g["pin"] = pin
        g["profiles"].add(prof)
        g["models"].append(model)
        for pkg, ver in (env.get("packages") or {}).items():
            prev = g["packages"].get(pkg)
            #: two EXACT pins for one package inside one venv is unsatisfiable and
            #: must be reported, not silently resolved by iteration order.
            if prev and ver and prev != ver:
                raise ValueError(
                    "%s: conflicting pins %r and %r declared for the same "
                    "environment (%s)" % (pkg, prev, ver, _name_for(pin)))
            if ver or not prev:
                g["packages"][pkg] = ver or prev or ""
    return {_name_for(p): g for p, g in groups.items()}


def venv_for(model):
    """-> absolute path to the venv this checkpoint's declaration requires."""
    for name, g in spec().items():
        if model in g["models"]:
            return os.path.join(ROOT, name)
    raise KeyError("%s is not a node in %s" % (model, MODELS_YAML))


def _requirements(g):
    out = ["-e", ROOT]
    if g["pin"]:
        out.append("transformers==%s" % g["pin"])
    for pkg, ver in sorted(g["packages"].items()):
        out.append(pkg + ver if ver else pkg)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("action", choices=["plan", "build", "which"])
    ap.add_argument("model", nargs="?")
    ap.add_argument("--python", default="3.11")
    a = ap.parse_args()

    if a.action == "which":
        if not a.model:
            ap.error("which needs a model id")
        print(venv_for(a.model))
        return

    sp = spec()
    for name, g in sorted(sp.items()):
        print("%-14s transformers %-10s %3d models   profiles: %s"
              % (name, g["pin"] or "(current)", len(g["models"]),
                 ", ".join(sorted(str(p) for p in g["profiles"]))))
        print("               install: %s" % " ".join(_requirements(g)))
        if a.action == "build":
            path = os.path.join(ROOT, name)
            subprocess.run(["uv", "venv", "--python", a.python, path], check=True)
            subprocess.run(["uv", "pip", "install", "--python",
                            os.path.join(path, "bin", "python")] + _requirements(g),
                           check=True)
            #: **REPORT WHAT LANDED, NOT WHAT WAS ASKED FOR.** `>=4.57` resolving
            #: to 5.15.0 is the whole reason the split exists; a build that says
            #: "done" without naming the version it installed cannot be checked.
            got = subprocess.run(
                [os.path.join(path, "bin", "python"), "-c",
                 "import transformers, torch; print(transformers.__version__, torch.__version__)"],
                capture_output=True, text=True, check=True).stdout.strip()
            print("               BUILT: transformers %s torch %s" % tuple(got.split()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
