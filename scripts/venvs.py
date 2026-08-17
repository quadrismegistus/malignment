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
from packaging.specifiers import SpecifierSet
from packaging.version import InvalidVersion, Version

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_YAML = os.path.join(ROOT, "roster", "models", "models.yaml")
ENVS_YAML = os.path.join(ROOT, "roster", "environments.yaml")

#: **THE DECLARATIONS ARE PEP 440 AND ARE READ AS PEP 440.** They always looked
#: like it (`>=4.57`, `==4.57.1`); what was missing was ever writing a RANGE, so
#: `tf457` expressed a ceiling by being a separate profile and every other
#: profile read as "no ceiling" when it meant "ceiling never tested". Grouping on
#: the specifier rather than on an exact-pin special case is what lets `>=5` and
#: `>=4.57` share an interpreter while `>=4.57,<5` cannot.
def _candidates(specs):
    """Versions worth testing for satisfiability, taken from the specs themselves.

    A SpecifierSet cannot be enumerated, and asking PyPI would put a network call
    inside a planning step. But an intersection of simple specifiers is non-empty
    iff it contains a point at one of the boundaries they name -- so the boundary
    versions, each also bumped by a hair to clear a strict `<`, plus one below all
    and one above all, decide it without guessing and without a candidate list
    anybody has to maintain.
    """
    out = {Version("0"), Version("9999")}
    for s in specs:
        for clause in SpecifierSet(s):
            try:
                v = Version(clause.version)
            except InvalidVersion:
                continue
            out.add(v)
            parts = list(v.release) + [0]
            parts[-1] += 1
            out.add(Version(".".join(str(x) for x in parts)))
            if len(v.release) > 1:
                bumped = list(v.release)
                bumped[-1] += 1
                out.add(Version(".".join(str(x) for x in bumped)))
    return sorted(out)


def _satisfiable(specs):
    """True if one installed version can satisfy every declaration in `specs`."""
    specs = [s for s in specs if s]
    if not specs:
        return True
    combined = SpecifierSet(",".join(specs))
    return any(v in combined for v in _candidates(specs))


def _ceiling(sp):
    """The clauses that bound a spec from ABOVE, as a signature. -> tuple

    **A CEILING IS WHAT FORCES A SECOND ENVIRONMENT; A FLOOR NEVER DOES**, because
    the newest release satisfies every floor at once. So `>=4.57` and `>=5` share
    an interpreter and `>=4.57,<5` cannot, and that is the whole partition.

    Grouping instead by "can these share SOME version" is satisfiable-but-wrong:
    4.57.1 satisfies `>=4.57` and `>=4.57,<5` together, so a merge on that test
    pins the entire roster to its own floor -- a year-old transformers for 250
    models that have only ever been measured at 5.x. Fewest environments is not
    the objective; the NEWEST admissible version for each node is.
    """
    return tuple(sorted(str(c) for c in SpecifierSet(sp or "")
                        if c.operator in ("<", "<=", "==", "===", "~=")))


def _name_for(profiles):
    """`.venv` for the group holding the `default` profile, else `.venv-<profile>`.

    Named after a PROFILE rather than after a version string, because the version
    is what changes: `.venv-tf457` survives `==4.57.1` being rewritten as the
    range it always meant, and a directory name that moves on every re-pin would
    invalidate every path anyone has written down.
    """
    named = {p: n for p, n in profiles.items() if p}
    if "default" in named or not named:
        return ".venv"
    #: **COUNTED OVER MODELS, NOT OVER THE SET OF PROFILE NAMES.** Counting the
    #: set gives every profile a tally of one, so the tie-break decides alone and
    #: the group of 11 `tf457` nodes gets named for the 2 `ssm` ones that only
    #: landed here via Zamba2's deviation -- alphabetical order masquerading as
    #: a constituency.
    return ".venv-%s" % sorted(named.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]


def spec():
    """-> {venv_name: {specs, packages, profiles, models}} derived from the roster."""
    doc = yaml.safe_load(open(MODELS_YAML))
    envs = yaml.safe_load(open(ENVS_YAML))
    profiles = envs.get("profiles") or {}

    #: a node's own `transformers:` OVERRIDES its profile's -- that is what a
    #: deviation is for. Zamba2 is the case (profile `ssm`, its own `>=4.57,<5`),
    #: and so now is Olmo-Hybrid, whose `default` profile declares a floor its
    #: own architecture does not exist under.
    bysp = collections.defaultdict(list)
    for model, node in (doc.get("nodes") or {}).items():
        env = (node or {}).get("env") or {}
        sp = (env.get("transformers")
              or (profiles.get(env.get("profile")) or {}).get("transformers") or "")
        bysp[str(sp).strip()].append((model, env))

    byceil = collections.defaultdict(
        lambda: {"specs": set(), "packages": {},
                 "profiles": collections.Counter(), "models": []})
    for sp in sorted(bysp, key=lambda s: (-len(bysp[s]), s)):
        g = byceil[_ceiling(sp)]
        g["specs"].add(sp)
        #: every declaration in the group must be jointly satisfiable, and a
        #: shared ceiling does not guarantee it (`>=5,<5.2` and `>=5.4,<5.2`).
        if not _satisfiable(g["specs"]):
            raise ValueError("declarations cannot share an environment: %s"
                             % ", ".join(sorted(g["specs"])))
        for model, env in bysp[sp]:
            g["profiles"][env.get("profile")] += 1
            g["models"].append(model)
            for pkg, ver in (env.get("packages") or {}).items():
                prev = g["packages"].get(pkg)
                #: two incompatible pins for one package inside one venv is
                #: unsatisfiable and must be reported, not resolved by iteration
                #: order.
                if prev and ver and not _satisfiable([prev, ver]):
                    raise ValueError(
                        "%s: declarations %r and %r cannot share an environment"
                        % (pkg, prev, ver))
                if ver or not prev:
                    g["packages"][pkg] = ver or prev or ""
    out = {}
    for g in byceil.values():
        name = _name_for(g["profiles"])
        #: two groups resolving to one directory would silently drop one of them,
        #: and the dropped one is the exception -- exactly the models that need
        #: their own interpreter.
        if name in out:
            raise ValueError("two environments both want %s: profiles %s and %s"
                             % (name, sorted(out[name]["profiles"]),
                                sorted(g["profiles"])))
        out[name] = g
    return out


def venv_for(model):
    """-> absolute path to the venv this checkpoint's declaration requires."""
    for name, g in spec().items():
        if model in g["models"]:
            return os.path.join(ROOT, name)
    raise KeyError("%s is not a node in %s" % (model, MODELS_YAML))


def _requirements(g):
    #: EVERY declaration in the group is passed, not a summary of them -- the
    #: resolver intersects them, and if that intersection is empty it says so
    #: rather than us having decided which declaration wins.
    out = ["-e", "%s[dev]" % ROOT]
    for sp in sorted(s for s in g["specs"] if s):
        out.append("transformers" + sp)
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
        print("%-14s transformers %-16s %3d models   profiles: %s"
              % (name, ",".join(sorted(s for s in g["specs"] if s)) or "(current)",
                 len(g["models"]),
                 ", ".join(sorted(str(p) for p in g["profiles"]))))
        print("               install: %s" % " ".join(_requirements(g)))
        if a.action == "build":
            path = os.path.join(ROOT, name)
            #: `--allow-existing` UPDATES IN PLACE rather than recreating. uv
            #: refuses to overwrite an existing venv without `--clear`, and
            #: `--clear` here would delete the interpreter this script is running
            #: on -- `build` is normally invoked from `.venv` itself.
            subprocess.run(["uv", "venv", "--allow-existing", "--python", a.python,
                            path], check=True)
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
