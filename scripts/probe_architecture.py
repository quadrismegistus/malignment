#!/usr/bin/env python
"""What each checkpoint is BUILT FROM, read off config.json. Never declared.

    python scripts/probe_architecture.py
    python scripts/probe_architecture.py --write   -> measurements.json `architecture`

## WHY THIS IS THE FOUND SIDE AND NOT THE AUTHORED ONE

`measurements.json`'s own `_about` settles where this goes: "OBSERVED facts about
checkpoints -- what inspection returned, never what anyone declared.
`models.yaml` is the authored side; this is the found side."

An architecture is not authored. It is read off `config.json`, which every repo
publishes, which needs no code execution to parse, and which evidences its own
claim: a hybrid carries `layer_types` or `hybrid_layer_ids`, an SSM carries
`state_size` or `conv_kernel`, a mixture carries `num_experts_per_tok`.

## `env.profile` CANNOT DERIVE IT, AND THIS WAS MEASURED RATHER THAN ARGUED

`experiments/architectures` began with an 8-model hand-declared table and the
claim that `env.profile: ssm` "picks out the SSM and hybrid families exactly".
It does not. As a predictor of "non-dense block" over those 8:

    hit 4    miss 3    false alarm 0

The misses are `recurrentgemma-9b` (Griffin), `Olmo-Hybrid-7B` (Gated DeltaNet)
and `OLMoE-1B-7B-0125` (mixture-of-experts), all on a non-`ssm` profile. It fails
the other way too: `profile: ssm` holds `falcon-mamba` and `Falcon3-Mamba`, which
are PURE SSM rather than hybrid, so the profile cannot separate the two classes
it would have to separate. **`env.profile` is an ENVIRONMENT requirement** -- it
answers "does this need mamba-ssm and causal-conv1d kernels" -- and two different
architectures can share one answer.

**And a hand-declared table forgets the arms nobody looked at.** That 8-model
table declared bases only, so six checkpoints carrying `env.profile: ssm` --
`Zamba2-7B-Instruct`, both `Falcon-H1-*-Instruct`, both `Falcon3-Mamba-7B-*` and
`falcon-mamba-7b-instruct` -- fell to its "unlisted means dense transformer"
default. Nothing had stratified the aligned arm yet, so nothing was wrong on
paper; the defect was one analysis away. A probe over the roster cannot forget a
sibling.

## STORE THE KEYS, DERIVE THE LABELS

This section holds **what `config.json` said**, nothing more. The attention-type
and block-type labels are computed in `roster.architecture()` at read time.

That split is `probe_config_dtype.py`'s, whose docstring says deriving one of its
two facts from the other "would have been a disaster", and it is load-bearing
here for a specific reason: the four-way taxonomy is a PROPOSAL, not a ruling --
`docs/model_census.md` says so, one class holds a single model, and two of the
boundaries are arguable. **Storing labels would ratify a taxonomy by writing it
down.** Storing keys means a ruling on the taxonomy changes one accessor and
re-probes nothing, and a new roster model is classified by re-running this rather
than by someone remembering.
"""
import argparse
import json
import os
import sys
from collections import Counter, OrderedDict
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
from probe_config_dtype import MEAS, _get, _token          # noqa: E402

#: The keys kept, and each is here because it EVIDENCES a class rather than
#: because it is interesting. Anything absent from a config is absent here:
#: a missing key and a null value are different answers.
KEEP = (
    "model_type", "architectures",
    #: attention shape
    "num_attention_heads", "num_key_value_heads", "num_hidden_layers",
    #: the same fact under other families' spellings -- mpt says `n_heads`,
    #: several gpt-lineage configs say `n_head`. Missing these read as
    #: "this model has no attention", which is how 6 dense transformers were
    #: first classified attention-free.
    "n_head", "n_heads", "num_heads", "n_layer", "n_layers",
    "sliding_window", "use_sliding_window", "layer_types", "attn_layer_indices",
    "attention_layers", "full_attn_idxs", "attn_type_list",
    #: recurrence / state space
    "state_size", "conv_kernel", "mamba_d_state", "mamba_d_conv",
    "mamba_expand", "mamba_n_heads", "hybrid_layer_ids", "hybrid_override_pattern",
    "linear_attn_config", "linear_num_key_heads", "linear_num_value_heads",
    "linear_conv_kernel_dim", "use_mamba_kernels", "mamba_d_ssm", "n_mamba_heads",
    "attn_implementation",
    #: mixture
    "num_experts", "num_experts_per_tok", "num_local_experts",
    "n_routed_experts", "moe_layer_freq",
)
URL = "https://huggingface.co/%s/raw/main/config.json"


def probe(models, token, workers=12):
    def one(m):
        try:
            cfg = _get(URL % m, token)
        except Exception as e:                       # noqa: BLE001
            return m, {"error": "%s: %s" % (type(e).__name__, e)}
        #: text_config / decoder nesting: some multimodal repos bury it.
        inner = cfg.get("text_config") or {}
        got = OrderedDict()
        for k in KEEP:
            if k in cfg:
                got[k] = cfg[k]
            elif k in inner:
                got[k] = inner[k]
        if "model_type" not in got:
            got["error"] = "config.json has no model_type"
        return m, got
    with ThreadPoolExecutor(max_workers=workers) as ex:
        return dict(ex.map(one, models))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    import yaml
    nodes = yaml.safe_load(open(os.path.join(ROOT, "roster", "models",
                                             "models.yaml")))["nodes"]
    res = probe(sorted(nodes), _token())
    ok = {m: v for m, v in res.items() if not v.get("error")}
    bad = {m: v for m, v in res.items() if v.get("error")}
    c = Counter(v.get("model_type") for v in ok.values())
    print("config.json read for %d of %d checkpoints, %d distinct model_type\n"
          % (len(ok), len(res), len(c)))
    for k, n in c.most_common():
        print("   %-28s %d" % (k, n))
    if bad:
        print("\nunreadable: %d" % len(bad))
        for m in sorted(bad)[:8]:
            print("   %-52s %s" % (m, bad[m]["error"]))
    #: what the labels would be, PRINTED not stored -- the accessor owns them.
    try:
        from malignment import roster
        lab = Counter(roster.architecture(m, probe=ok) for m in ok)
        print("\nderived by roster.architecture(), for inspection only:")
        for k, n in lab.most_common():
            print("   %-30s %d" % ("%s / %s" % k, n))
    except Exception as e:                           # noqa: BLE001
        print("\n(accessor not derivable yet: %s)" % e)
    if not a.write:
        print("\nDRY RUN -- pass --write.")
        return 0
    import datetime
    doc = json.load(open(MEAS), object_pairs_hook=OrderedDict)
    doc["sections"]["architecture"] = OrderedDict([
        ("_why", "What each checkpoint is BUILT FROM, from config.json. The "
                 "FOUND side of a fact `models.yaml` never asserts: that file "
                 "carries `env.profile`, which is an ENVIRONMENT requirement "
                 "(does this need mamba-ssm and causal-conv1d) and cannot "
                 "stand in for an architecture -- measured over 8 declared "
                 "cases it hit 4 and missed 3, and it cannot separate pure SSM "
                 "from hybrid because both need the same kernels."),
        ("_instrument", "config.json via the HF raw endpoint, parsed as JSON. "
                        "No code execution, no model load, no trust_remote_code. "
                        "Keys kept are the ones that EVIDENCE a class: "
                        "layer_types and hybrid_layer_ids for hybrids, "
                        "state_size and conv_kernel for SSMs, "
                        "num_experts_per_tok for mixtures. A key absent from a "
                        "config is absent here; a missing key and a null value "
                        "are different answers."),
        ("_labels_are_not_stored", "Deliberate. The attn/block taxonomy is a "
                                   "PROPOSAL in docs/model_census.md, not a "
                                   "ruling -- one class holds a single model "
                                   "and two boundaries are arguable -- so "
                                   "storing labels would ratify it by writing "
                                   "it down. `roster.architecture()` derives "
                                   "them at read time, so a ruling on the "
                                   "taxonomy changes one accessor and "
                                   "re-probes nothing."),
        ("measured_by", "scripts/probe_architecture.py"),
        ("measured_at", datetime.datetime.now().replace(microsecond=0).isoformat()),
        ("n", len(ok)),
        ("models", OrderedDict(sorted(ok.items()))),
        ("unmeasured", OrderedDict(sorted((m, v["error"]) for m, v in bad.items()))),
    ])
    json.dump(doc, open(MEAS, "w"), indent=1)
    print("\nwrote section `architecture`, n=%d" % len(ok))
    return 0


if __name__ == "__main__":
    sys.exit(main())
