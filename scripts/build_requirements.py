#!/usr/bin/env python
"""What each checkpoint NEEDS to run. Derived from the LIVE roster, no names typed.

    python scripts/build_requirements.py            report
    python scripts/build_requirements.py --write    -> roster/models/requirements.json

The artifact a launcher reads to provision a fleet without a human remembering
anything. One row per checkpoint, and the EVIDENCE for every field.

## THIS REPLACES AN ARCHIVE FILE THAT COULD NOT BE REFRESHED

`malign-logits/data/model_requirements.json` was the same idea and it worked,
but all five of its `_sources` are in a repo RH has declared READ-ONLY, and its
builder is over there too. It was dated 15 Aug against a source rewritten on the
19th, so it reported `none-local` for 50 checkpoints holding thousands of cells.
A derived file whose sources you cannot re-read is a hand-maintained file with
extra steps.

## NOTHING HERE KNOWS A MODEL'S NAME

The archive builder decided kernels with

    KERNELS = ("mamba", "zamba", "falcon-h1")

-- a substring match on the id. That is the error class this project keeps
paying for: RWKV matches nothing in that tuple but pattern-matches the SSM class
on every other axis (linear-attention RNN, bin-only weights, torch>=2.6), and it
needs NO kernels; meanwhile the `ssm` profile's own `why:` warns that a prior
tested on one member of a class is not a fact about the class. Here every field
comes from a DECLARATION or a MEASUREMENT:

    roster/models/models.yaml          env.profile, revision, per-node dtype
    roster/environments.yaml           profiles (transformers, torch, kernels,
                                       compute_dtype) and the `sizing:` steps
    roster/models/measurements.json    params_b, weights_format, architecture,
                                       vocab, chat_template, repos
    roster/models/observations.json    how many times it has been observed

Add a model that needs kernels and it gets them by declaring `profile: ssm`,
not by being called something.

## `launch:` IS NOT READ, DELIBERATELY

A box is a function of SIZE and a profile groups by LIBRARY PIN. `min_vram_gb`
and `gpus` come from `sizing:` applied to measured `params_b`, which is what
`fleet_launch.shard_profile()` does. See the note in environments.yaml.
"""
import argparse
import json
import os
import sys
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

OUT = os.path.join(ROOT, "roster", "models", "requirements.json")
SOURCES = ["roster/models/models.yaml", "roster/environments.yaml",
           "roster/models/measurements.json", "roster/models/observations.json"]


def _sections():
    m = json.load(open(os.path.join(ROOT, "roster", "models",
                                    "measurements.json")))["sections"]
    return {k: (v.get("models") or {}) for k, v in m.items()
            if isinstance(v, dict)}


def build():
    import yaml
    nodes = yaml.safe_load(open(os.path.join(ROOT, "roster", "models",
                                             "models.yaml")))["nodes"]
    E = yaml.safe_load(open(os.path.join(ROOT, "roster", "environments.yaml")))
    prof, steps = E["profiles"], E["sizing"]["steps"]
    sec = _sections()
    weights, wff = sec.get("weights", {}), sec.get("weights_from_files", {})
    vocab, chat, repos = (sec.get("vocab", {}), sec.get("chat_template", {}),
                          sec.get("repos", {}))
    obs = json.load(open(os.path.join(ROOT, "roster", "models",
                                      "observations.json")))["observations"]
    nobs = {}
    for o in obs:
        nobs[o["model_id"]] = nobs.get(o["model_id"], 0) + 1

    def sized(pb):
        for s in steps:
            cap = s.get("max_params_b")
            if cap is None or (pb is not None and pb <= cap):
                return s.get("vram_gb"), s.get("gpus")
        return None, None

    rows = []
    for m in sorted(nodes):
        node = nodes[m] or {}
        env = node.get("env") or {}
        p = env.get("profile") or "default"
        pr = prof.get(p) or {}
        w = weights.get(m) or {}
        wf = wff.get(m) or {}
        pb = w.get("params_b") or wf.get("params_b")
        vram, gpus = sized(pb)
        rp = repos.get(m) or {}
        state = rp.get("state")
        #: BLOCKED IS DERIVED FROM A PROBE, NOT DECLARED. `dead` and
        #: `gated_refused` are the two states no fleet can fix; `gated_held`
        #: is usable and only means the box must carry the token.
        blocked = state in ("dead", "gated_refused")
        rows.append(OrderedDict([
            ("model", m),
            ("profile", p),
            ("transformers", pr.get("transformers")),
            ("transformers_reason", (pr.get("why") or "")[:200] or None),
            ("torch", pr.get("torch")),
            ("kernels", pr.get("kernels") or []),
            ("compute_dtype", env.get("dtype") or pr.get("compute_dtype")),
            ("compute_dtype_reason",
             ("per-node env.dtype" if env.get("dtype")
              else ("profile %s" % p) if pr.get("compute_dtype") else None)),
            ("min_vram_gb", vram),
            ("gpus", gpus),
            ("params_b", pb),
            ("params_source", "weights" if w.get("params_b") else
             ("weights_from_files" if wf.get("params_b") else None)),
            ("weights_format", w.get("weights_format") or wf.get("weights_format")),
            ("architecture", wf.get("architecture")),
            ("vocab_len", (vocab.get(m) or {}).get("vocab_len")),
            ("byte_notation", (vocab.get(m) or {}).get("byte_notation")),
            ("revision", node.get("revision")),
            ("revision_ladder", node.get("revision_ladder")),
            ("chat_template", (chat.get(m) or {}).get("verdict")),
            ("repo_state", state),
            ("needs_hf_token", state == "gated_held"),
            ("blocked", blocked),
            ("blocked_reason", rp.get("note") if blocked else None),
            ("n_observations", nobs.get(m, 0)),
        ]))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--profile", default=None, help="report one profile's roster")
    a = ap.parse_args()
    rows = build()
    if a.profile:
        rows = [r for r in rows if r["profile"] == a.profile]
    import collections
    print("checkpoints %d" % len(rows))
    for f in ("profile", "transformers", "weights_format", "repo_state",
              "chat_template"):
        c = collections.Counter(str(r[f]) for r in rows)
        print("  %-15s %s" % (f, dict(c.most_common(6))))
    print("  %-15s %s" % ("min_vram_gb",
                          dict(collections.Counter(str(r["min_vram_gb"])
                                                   for r in rows))))
    miss = [r["model"] for r in rows if r["params_b"] is None]
    print("  no params_b     %d%s" % (len(miss),
                                      (": " + ", ".join(m.split("/")[-1]
                                                        for m in miss[:5]))
                                      if miss else ""))
    print("  needs HF token  %d" % sum(1 for r in rows if r["needs_hf_token"]))
    print("  blocked         %d" % sum(1 for r in rows if r["blocked"]))
    print("  with kernels    %d" % sum(1 for r in rows if r["kernels"]))
    print("  never observed  %d" % sum(1 for r in rows if not r["n_observations"]))
    if not a.write:
        print("\nDRY RUN -- pass --write.")
        return 0
    doc = OrderedDict([
        ("_about", "What each checkpoint NEEDS to run. DERIVED from the live "
                   "roster; no model names appear in the producer. Regenerate, "
                   "never hand-edit."),
        ("_producer", "scripts/build_requirements.py"),
        ("_sources", SOURCES),
        ("_supersedes", "malign-logits/data/model_requirements.json, whose five "
                        "sources are all in the read-only archive and which was "
                        "stale against them."),
        ("n", len(rows)),
        ("requirements", rows),
    ])
    with open(OUT, "w") as fh:
        json.dump(doc, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    print("\nwrote %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
