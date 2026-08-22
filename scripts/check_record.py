#!/usr/bin/env python
"""THE GATE. Six assertions about the environment record. Exits non-zero.

    python scripts/check_record.py
    python scripts/check_record.py --only writes_to_archive
    python scripts/check_record.py -v          # show every passing detail

## WHY THIS EXISTS

Every environment fact lost this month was lost without anything exiting
non-zero. A lost fact and a recorded fact produce identical output from every
command we run, so the loss is invisible until a fleet is already rented. See
`docs/environment_record.md` for the six ways it happened.

**Recording a fact is the cheap half. Making something FAIL without it is the
half that works.**

## EACH CHECK NAMES THE INCIDENT IT WOULD HAVE CAUGHT

A check whose failure mode nobody has seen is a belief, not a guard. Every check
below is written against a specific thing that actually happened, and the
docstring says which -- so a future reader can decide whether the check still
earns its place rather than cargo-culting it.
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

ARCHIVE = "/Users/rj416/github/malign-logits"
OBS = os.path.join(ROOT, "roster", "models", "observations.json")

CHECKS = []


def check(fn):
    CHECKS.append(fn)
    return fn


def _obs():
    return json.load(open(OBS))


# --------------------------------------------------------------------------
@check
def writes_to_archive(v):
    """No live-repo script may WRITE to the read-only archive.

    INCIDENT: `record_successes.py` lived here and wrote to
    `~/github/malign-logits/data/model_load_environments.json`. New model
    information accumulated in a repo nobody reads, and the record forked --
    131 observations there against 72 here, diverging in BOTH directions.

    Reading the archive is fine and still necessary; only writes are refused.
    """
    bad = []
    pat = re.compile(r"malign-logits")
    for sub in ("scripts", "malignment"):
        d = os.path.join(ROOT, sub)
        for dirpath, _dn, files in os.walk(d):
            if "__pycache__" in dirpath:
                continue
            for f in files:
                if not f.endswith(".py"):
                    continue
                p = os.path.join(dirpath, f)
                src = open(p, errors="replace").read()
                if not pat.search(src):
                    continue
                #: A WRITE is `open(..., "w"/"a")` or a dump whose target
                #: resolves to the archive. Matching the path alone would flag
                #: every docstring that names it -- including this file.
                for m in re.finditer(r'open\(\s*([A-Za-z_][A-Za-z_0-9]*)\s*,\s*["\'][wa]',
                                     src):
                    var = m.group(1)
                    assign = re.search(
                        r'^%s\s*=\s*(.+?)$' % re.escape(var), src, re.M | re.S)
                    if assign and "malign-logits" in assign.group(1)[:300]:
                        bad.append("%s writes to the archive via `%s`"
                                   % (os.path.relpath(p, ROOT), var))
    return bad, "no live script writes to the archive"


# --------------------------------------------------------------------------
@check
def derived_not_stale(v):
    """A derived artifact must not be older than any source it declares.

    INCIDENT: `malign-logits/data/model_requirements.json` was dated 15 Aug and
    derives from five files, one of which was rewritten on the 19th. It ships a
    `--check` flag for exactly this and nobody ran it, so it reported
    `none-local` for 50 checkpoints holding thousands of cells.

    **THE ARCHIVE COPY IS NO LONGER CHECKED, BECAUSE IT IS NO LONGER OURS TO
    FIX.** All five of its sources are in a read-only repo, so the check could
    only ever report a failure nobody was permitted to clear -- and a gate that
    cannot be satisfied is a gate people learn to ignore. It is superseded by
    `roster/models/requirements.json`, which derives from live sources; that one
    IS checked, and can be cleared by running its producer.
    """
    bad = []
    for rel in ("roster/models/requirements.json",
                "roster/models/version_windows.json"):
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            bad.append("%s missing -- run scripts/build_requirements.py --write"
                       % rel)
            continue
        try:
            doc = json.load(open(p))
        except Exception as e:                                   # noqa: BLE001
            bad.append("%s unreadable: %s" % (rel, e))
            continue
        mt = os.path.getmtime(p)
        for s in doc.get("_sources") or []:
            sp = os.path.join(ROOT, s)
            if os.path.exists(sp) and os.path.getmtime(sp) > mt:
                bad.append("%s is older than its source %s -- rerun %s"
                           % (rel, s, doc.get("_producer") or "its producer"))
    return bad, "derived files are current with their live sources"


# --------------------------------------------------------------------------
@check
def cells_have_observations(v):
    """Every (model x environment) that produced CELLS must have an observation.

    INCIDENT: 107 models had v4 cells and no observation of any kind, while the
    file's own `_absence` note says absence means UNTESTED. The corpus is the
    denominator: a model that ran and is not recorded is a missing row, not an
    open question.

    **MODELS CARRYING A `run_failed` ARE EXEMPT, AND THAT IS NOT A LOOPHOLE.**
    `record_successes.py` refuses to write `load_ok` for them ON PURPOSE --
    deepseek and croissant produce cells AND destroy the prompt in the
    tokenizer, so "it ran" must never launder into "it ran right". Flagging a
    deliberate refusal as a gap trains the reader to ignore the gate, which is
    how a nagging check becomes no check at all. They are counted and named
    under `-v` so the exemption stays visible rather than silent.
    """
    from malignment import ch
    from record_successes import env_name
    doc = _obs()
    have = {(o["model_id"], o["environment"]) for o in doc["observations"]}
    withheld = {o["model_id"] for o in doc["observations"]
                if o["outcome"] == "run_failed"}
    rows = ch.query(
        "SELECT model, device, transformers_version tf, torch_version torch "
        "FROM {db}.twp_cells_v4 GROUP BY model, device, tf, torch")
    bad, exempt = [], []
    for r in rows:
        env, _why = env_name(r["device"], r["tf"], r["torch"])
        if not env or (r["model"], env) in have:
            continue
        if r["model"] in withheld:
            exempt.append("%s / %s" % (r["model"], env))
            continue
        bad.append("%s ran in %s with no observation" % (r["model"], env))
    if exempt and v:
        for e in exempt:
            print("        (withheld, run_failed on record) %s" % e)
    return bad, ("every measured (model x environment) is recorded "
                 "(%d withheld on a recorded run_failed)" % len(exempt))


# --------------------------------------------------------------------------
@check
def no_contradictions(v):
    """No (model, environment) may assert both a success and a load_failed.

    INCIDENT: deriving the environment from the VENV stamped every success
    `local_mps`, which would have written `load_ok` for Llama-3.1-70B-Instruct
    beside its recorded `load_failed | CAPACITY: ~140GB bf16 against 96GB`.

    `loads` + `load_failed` together is LEGITIMATE and exempt: AmberSafe failed,
    two packages went in, and it loaded on the same box. That repair-in-place is
    the fact `_why_not_in_models_yaml` exists to protect. `load_ok` is the
    corpus-derived outcome and carries no such story, so it is not exempt.
    """
    doc = _obs()
    by = {}
    for o in doc["observations"]:
        by.setdefault((o["model_id"], o["environment"]), set()).add(o["outcome"])
    bad = []
    for (m, e), outs in sorted(by.items()):
        if "load_ok" in outs and "load_failed" in outs:
            bad.append("%s in %s asserts both load_ok and load_failed" % (m, e))
    return bad, "no (model x environment) contradicts itself"


# --------------------------------------------------------------------------
@check
def launch_box_satisfies_sizing(v):
    """The box a shard would actually rent must satisfy the sizing rule.

    INCIDENT: reading `profiles.<p>.launch` to plan a fleet gave `dense` (48 GB)
    for the four 32B arms, which need 80. I built a costed plan on that field on
    2026-08-22 before checking what the launcher does.

    **`launch:` IS NOT WHAT THE LAUNCHER USES, AND THE FIELD IS MIS-KEYED.**
    `fleet_launch.shard_profile()` derives the box from `sizing:` on the
    shard's BIGGEST model and never reads `launch:` at all. It is right to:
    a box is a function of SIZE, while a profile groups by LIBRARY PIN, and
    those are orthogonal -- `tf457` holds 13 models of which only 4 are 32B, so
    no single `launch:` value can be correct for it.

    So this checks the REAL path, per model, as a one-model shard. A failure
    here is money. The `launch:` disagreement is reported separately as a
    documentation hazard, because it misleads readers without costing anything.
    """
    import yaml
    nodes = yaml.safe_load(open(os.path.join(ROOT, "roster", "models",
                                             "models.yaml")))["nodes"]
    E = yaml.safe_load(open(os.path.join(ROOT, "roster", "environments.yaml")))
    prof, boxes, steps = E["profiles"], E["boxes"], E["sizing"]["steps"]
    req = os.path.join(ARCHIVE, "data", "model_requirements.json")
    params = {}
    if os.path.exists(req):
        for r in json.load(open(req))["requirements"]:
            if r.get("params_b"):
                params[r["model"]] = r["params_b"]

    def demand(pb):
        for s in steps:
            if s["max_params_b"] is None or pb <= s["max_params_b"]:
                return s["vram_gb"], s["gpus"]
        return None, None

    from fleet_launch import shard_profile
    bad, misleading = [], []
    for m, node in sorted(nodes.items()):
        pb = params.get(m)
        if not pb:
            continue
        need_v, need_g = demand(pb)
        #: What the launcher WOULD rent for a shard holding just this model.
        real, _rv, _rg, _pb = shard_profile([m])
        rb = boxes.get(real) or {}
        got_v, got_g = rb.get("provides_vram_gb", 0), rb.get("num_gpus", 1)
        if got_v < need_v or got_g < need_g:
            bad.append("%s (%.1fB) would rent %s -> %sGB x%s, needs %sGB x%s"
                       % (m, pb, real, got_v, got_g, need_v, need_g))
        p = ((node or {}).get("env") or {}).get("profile") or "default"
        declared = (prof.get(p) or {}).get("launch")
        if declared and declared != real:
            misleading.append("%s: profile %s declares launch=%s, launcher "
                              "rents %s" % (m, p, declared, real))
    if misleading:
        print("        NOTE %d model(s) whose profile `launch:` disagrees with "
              "what the launcher rents." % len(misleading))
        print("             `launch:` is advisory and MIS-KEYED (box is a "
              "function of size; a profile groups by library pin). Do not plan "
              "a fleet from it -- read `sizing:`.")
        for line in misleading[:4] if v else []:
            print("             %s" % line)
    return bad, ("every shard rents a box satisfying the sizing rule"
                 " (%d advisory `launch:` mismatches noted)" % len(misleading))


# --------------------------------------------------------------------------
@check
def every_model_resolves(v):
    """Every roster node must resolve to a profile that exists and a venv.

    INCIDENT: hardcoding one venv for a queue broke Baichuan2 for an hour. A
    node naming a profile that `environments.yaml` does not define resolves to
    `default` silently, which is the same shape of failure one level up.
    """
    import yaml
    from venvs import venv_for
    nodes = yaml.safe_load(open(os.path.join(ROOT, "roster", "models",
                                             "models.yaml")))["nodes"]
    prof = yaml.safe_load(open(os.path.join(ROOT, "roster",
                                            "environments.yaml")))["profiles"]
    bad = []
    for m, node in sorted(nodes.items()):
        p = ((node or {}).get("env") or {}).get("profile")
        if p is None:
            bad.append("%s declares no env.profile" % m)
        elif p not in prof:
            bad.append("%s declares profile %r which environments.yaml does "
                       "not define" % (m, p))
        try:
            venv_for(m)
        except Exception as e:                                   # noqa: BLE001
            bad.append("%s does not resolve to a venv: %s" % (m, e))
    return bad, "every roster node resolves to a profile and a venv"


@check
def revision_required_is_pinned(v):
    """A repo whose `main` carries no model must declare a revision.

    INCIDENT: `HuggingFaceTB/SmolLM3-3B-checkpoints` holds 133 branches and its
    `main` contains exactly `.gitattributes` and `README.md`. Resolving the bare
    id gets NO MODEL -- not the wrong one, none. Both nodes do pin a revision
    today, so this passes; it exists because the next 133-branch container will
    be added by someone who does not know that, and the failure is a 404 halfway
    into a rented run rather than at declaration time.

    Measured by `scripts/probe_repos.py` into measurements.json `repos`, so this
    reads a fact rather than a list of names.
    """
    import yaml
    meas = json.load(open(os.path.join(ROOT, "roster", "models",
                                       "measurements.json")))
    repos = ((meas.get("sections") or {}).get("repos") or {}).get("models") or {}
    if not repos:
        return (["measurements.json has no `repos` section -- run "
                 "scripts/probe_repos.py --write"], "revision traps are pinned")
    nodes = yaml.safe_load(open(os.path.join(ROOT, "roster", "models",
                                             "models.yaml")))["nodes"]
    bad = []
    for m, r in sorted(repos.items()):
        if r.get("state") != "revision_required":
            continue
        node = nodes.get(m) or {}
        if not node.get("revision") and "@" not in m:
            bad.append("%s: main carries no model and no revision is declared"
                       % m)
    return bad, "every revision-trap repo declares a revision"


@check
def gated_repos_are_known(v):
    """Gated repos must be recorded, because a tokenless box fails on them.

    INCIDENT: `Zyphra/Zamba2-7B` 401'd on a box that shipped no token, and it
    was first mis-attributed to that box's separate HF-proxy 404 -- two failures
    with one appearance. 11 of 160 repos need the token, including all four
    meta-llama arms. This asserts the measurement EXISTS; the launcher ships a
    token unconditionally, so the risk is a silent change on either side.
    """
    meas = json.load(open(os.path.join(ROOT, "roster", "models",
                                       "measurements.json")))
    repos = ((meas.get("sections") or {}).get("repos") or {}).get("models") or {}
    if not repos:
        return (["no `repos` section -- run scripts/probe_repos.py --write"],
                "gated repos are measured")
    unknown = [m for m, r in sorted(repos.items())
               if r.get("state") in ("gated_unknown", "unknown")]
    gated = [m for m, r in repos.items() if r.get("state") == "gated_held"]
    if v:
        print("        %d gated repos need the token: %s"
              % (len(gated), ", ".join(sorted(x.split("/")[-1] for x in gated))))
    return unknown, ("gated repos measured (%d need the token, %d refused)"
                     % (len(gated),
                        sum(1 for r in repos.values()
                            if r.get("state") == "gated_refused")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None, help="run one check by name")
    ap.add_argument("-v", "--verbose", action="store_true")
    ap.add_argument("--max", type=int, default=8, help="failures shown per check")
    a = ap.parse_args()
    runs = [c for c in CHECKS if not a.only or c.__name__ == a.only]
    if a.only and not runs:
        raise SystemExit("no such check: %s (have: %s)"
                         % (a.only, ", ".join(c.__name__ for c in CHECKS)))
    failed = 0
    for c in runs:
        try:
            bad, label = c(a.verbose)
        except Exception as e:                                   # noqa: BLE001
            #: A check that CANNOT RUN is a failure, never a pass. Swallowing
            #: the exception is how a guard reports green while testing nothing.
            print("ERROR %-28s %s: %s" % (c.__name__, type(e).__name__, e))
            failed += 1
            continue
        if bad:
            failed += 1
            print("FAIL  %-28s %d problem(s)" % (c.__name__, len(bad)))
            for line in bad[:a.max]:
                print("        %s" % line)
            if len(bad) > a.max:
                print("        ... and %d more" % (len(bad) - a.max))
        else:
            print("ok    %-28s %s" % (c.__name__, label))
    print("\n%d/%d checks passed" % (len(runs) - failed, len(runs)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
