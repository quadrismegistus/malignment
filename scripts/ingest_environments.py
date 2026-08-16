#!/usr/bin/env python
"""ONE-SHOT: pull the campaign's environment knowledge out of the archive.

    scripts/ingest_environments.py            # dry run, prints the plan
    scripts/ingest_environments.py --write

Nine sources across two repos became four files with declared trust classes.
**This script is a record, not a tool.** It ran once, on 2026-08-16; after that
`models.yaml` and `environments.yaml` are HAND-EDITED like everything else
authored. Re-running it would overwrite hand edits with the archive's frozen
state, so it refuses unless `--force`.

## THE THREE FACT CLASSES, AND WHY THEY CANNOT SHARE A KEY

    REQUIREMENT  per CHECKPOINT             what the model needs      models.yaml env:
    OUTCOME      per (MODEL x ENVIRONMENT)  what happened on a box    observations.json
    SUPPORT      per (ARCHITECTURE x ENGINE) what vLLM hosts          observations.json

The middle one is not a property of the model and the archive's own note says
so: "WHETHER A MODEL LOADS IS NOT A PROPERTY OF THE MODEL." Seven models carry
BOTH a failure and a success -- AmberSafe, OLMo-2-0425-1B-DPO, both RWKVs,
Olmo-3-1125-32B, both internlm2 arms. Flattening those onto the checkpoint would
author "AmberSafe: load_failed" about a model that loads fine once sentencepiece
and protobuf are installed. The third is a property of vLLM: Aquila is not
broken, it was DELETED after v0.24.0 and runs on the 0.22.1 image.

## WHAT IS DERIVED AND THEREFORE NOT WRITTEN

`min_vram_gb` and `gpus` are a clean step function of MEASURED `params_b`
(<=9 -> 24, <=17 -> 48, <=35 -> 80, else 2x80; verified no overlaps across 159
rows). Transcribing them onto 160 checkpoints would create 160 derived values
with no producer, which is the failure this repo exists to stop. The resolver
computes them.

## TRUST CLASS CHANGES HERE, DELIBERATELY

`data/model_requirements.json` is DERIVED and says "Regenerate; never
hand-edit". Its producer reads `MODEL_FAMILIES`, `model_registry.json` and
`twp.LOADER_OVERRIDE` -- none of which exist in this repo, because `models.yaml`
replaced all three. So the requirement becomes AUTHORED here and the archive's
producer becomes historical. Keeping it derived would mean keeping the archive's
five upstream files alive, which is the scattering being removed.
"""
import argparse
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

ARCHIVE = "/Users/rj416/github/malign-logits"
MODELS_YAML = os.path.join(ROOT, "roster", "models", "models.yaml")
ENVS_YAML = os.path.join(ROOT, "roster", "environments.yaml")
OBS_JSON = os.path.join(ROOT, "roster", "models", "observations.json")

#: The 7 roster checkpoints with no row in the archive's requirements file, and
#: what each inherits. **Four of the seven are one story**: mosaicml's repos went
#: 404 and the weights were recovered from mirrors under new ids, so the
#: requirements file is keyed to the dead ids and the roster to the live ones.
#: The archive's 6 orphan rows are the other half of the same story and are NOT
#: imported: mosaicml/* x2 superseded here, gpt-sw3 x3 declared access_denied,
#: glm-4-9b-hf not in this roster.
INHERIT = {
    "gl198976/mpt-7b": ("mosaicml/mpt-7b", "mirror"),
    "gl198976/mpt-7b-instruct": ("mosaicml/mpt-7b-instruct", "mirror"),
    "Alchan/mpt-7b-chat": ("mosaicml/mpt-7b", "mirror"),
    "HuggingFaceTB/SmolLM3-3B-checkpoints@it-soup-APO":
        ("HuggingFaceTB/SmolLM3-3B", "repo_grain"),
    "mistralai/Mistral-7B-Instruct-v0.1":
        ("mistralai/Mistral-7B-v0.1", "sibling"),
    "openGPT-X/Teuken-7B-instruct-commercial-v0.4":
        ("openGPT-X/Teuken-7B-instruct-v0.6", "sibling"),
    "microsoft/Phi-4-reasoning-plus": ("microsoft/phi-4", "sibling"),
}

#: **A MIRROR MUST NOT INHERIT ITS SOURCE'S DEATH.** Caught by reading the dry
#: run's output rather than its summary: `gl198976/mpt-7b` came out carrying
#: `blocked: repo_dead`, inherited from the `mosaicml/mpt-7b` row -- and the
#: mirror is in this roster PRECISELY BECAUSE it is alive. Importing that would
#: have excluded three working checkpoints from every fleet plan, with a reason
#: attached that reads perfectly true ("404 at the API") and is about a
#: different repository. The requirements are inheritable; the death is not.
INHERIT_DROP = {"mirror": ("blocked",)}

#: **AUTHORED CORRECTIONS to the archive's rows.** Not transcription: each is a
#: disagreement between two archive files that the ingest cannot carry forward
#: unresolved.
CORRECT = {
    "Zyphra/Zamba2-7B": ("ssm", "profile"),
    "Zyphra/Zamba2-7B-Instruct": ("ssm", "profile"),
}
CORRECT_WHY = (
    "CORRECTED ON INGEST, 2026-08-16. The archive profiled Zamba2 `tf457`, which "
    "scripts/build_fleet.py:78 launches on `dense` -- a box that installs NO "
    "kernels, while the row itself declares kernels [mamba-ssm, causal-conv1d]. "
    "Zamba2 is a Mamba2/attention HYBRID and the measured hybrid penalty for "
    "missing kernels is 19.3x, so the plan would have run it ~19x slow and "
    "reported nothing wrong. The two archive files already disagreed: the `ssm` "
    "BOX pins transformers==4.57.1 and its description says it does so FOR "
    "ZAMBA2. So `ssm` is the profile that satisfies both constraints, and "
    "`tf457` was the half of the requirement that got written down."
)

#: **AUTHORED BOX OVERRIDES.** A profile names a DEFAULT box; a model whose
#: measured size exceeds it needs a bigger one, and nothing in the archive
#: reconciled the two. `build_fleet.py` emits `launch_profile: dense` and
#: `min_vram_gb: 80` side by side in the same plan dict and never compares them,
#: so the Olmo-3-32B quartet -- profile `default`, and `default` launches on a
#: 48 GB box -- would have been sent to a card that cannot hold them, AFTER
#: paying for four 64 GB downloads. `big80` exists for exactly this and its own
#: description says so: "For the 32B pair, which needs >48GB VRAM but not two
#: cards and not 600GB of disk."
BOX_OVERRIDE = {
    "allenai/Olmo-3-1125-32B": "big80",
    "allenai/Olmo-3.1-32B-Instruct": "big80",
    "allenai/Olmo-3.1-32B-Instruct-DPO": "big80",
    "allenai/Olmo-3.1-32B-Instruct-SFT": "big80",
}
BOX_OVERRIDE_WHY = (
    "32.2B measured: needs an 80 GB card. Profile `default` launches on `dense`, "
    "which filters for 48 GB, so the declared profile cannot host it. Set on "
    "ingest 2026-08-16 after the box-fit check was added -- the archive computed "
    "min_vram_gb=80 for these four and emitted launch_profile=dense in the same "
    "plan without ever comparing them."
)

#: `why` text for the inherited seven. An override with no reason is what the
#: schema forbids, so a script that creates one is creating the defect it checks.
INHERIT_WHY = {
    "mirror": "mosaicml's repo returned 404 at the API (not a permissions "
              "error); weights recovered from this mirror. Requirements "
              "inherited from the dead id, which is where the archive keyed them.",
    "repo_grain": "a repo@revision checkpoint inherits its repo's requirements: "
                  "transformers floor, torch floor, kernels, VRAM and dtype are "
                  "properties of the architecture and the weights' size, and a "
                  "training step changes none of them.",
    "sibling": "inherited from the same-architecture sibling in this lineage; no "
               "row was built for this id before it entered the roster.",
}

#: **THE TOKENIZER LOADER LEAVES CODE AND BECOMES DATA.** These lived in
#: `malign_logits/twp.py:600 LOADER_OVERRIDE`, where a fleet script could not
#: read them without importing torch. Each is a model that LOADS AND RUNS and
#: silently corrupts the prompt -- the fifth and worst kind in
#: docs/local_capability.md, because nothing errors.
FIDELITY_WHY = {
    "deepseek-ai/deepseek-llm-7b-base":
        "AutoTokenizer resolves to LlamaTokenizer and deletes every space: "
        "'He lay naked in his bed and' -> 'Helaynakedinhisbedand'. Re-confirmed "
        "at transformers 5.14.1. Loads and runs and destroys the prompt.",
    "deepseek-ai/deepseek-llm-7b-chat":
        "as the base sibling: encode('a b') == encode('ab').",
    "croissantllm/CroissantLLMBase":
        "DELETES CJK CHARACTERS -- drops both halves of the ji...you both-and "
        "construction. English is exact, so an English-only check passes it.",
    "openGPT-X/Teuken-7B-base-v0.6":
        "normalises the FULLWIDTH COMMA to ASCII. Milder than Croissant and a "
        "different kind of loss. Also: sentencepiece IdToPiece OUT_OF_RANGE "
        "during vLLM cross-scoring, same defect as m-a-p/CT-LLM-Base.",
    "internlm/internlm2-chat-7b":
        "AutoTokenizer fetches the repo's bundled InternLM2TokenizerFast under "
        "trust_remote_code and it SHIFTS WORD BOUNDARIES. PreTrainedTokenizerFast "
        "scores 2/2 where AutoTokenizer scores 0/2.",
    "internlm/internlm2-base-7b":
        "same boundary shift as the chat arm, verified on the box. Both arms fail "
        "identically, so the pair is recoverable rather than lost.",
}


def load_sources():
    req = json.load(open(os.path.join(ARCHIVE, "data", "model_requirements.json")))
    envs = json.load(open(os.path.join(ARCHIVE, "data",
                                       "model_load_environments.json")))
    vllm = json.load(open(os.path.join(ARCHIVE, "data",
                                       "vllm_engine_support.json")))
    boxes = json.load(open(os.path.join(ARCHIVE, "data", "cloud_profiles.json")))
    return req, envs, vllm, boxes


def profile_floors(rows):
    """{profile: {field: modal value}} -- derived, then diffed against.

    Derived rather than declared so that a field the archive set per-model but
    which is in fact uniform across a profile shows up as a floor, not as 126
    identical overrides. The MODE is used, not the first value, so one odd row
    cannot define the floor for its profile.
    """
    fields = ("transformers", "torch", "kernels", "compute_dtype",
              "tokenizer_loader")
    out = {}
    for prof in sorted({r["profile"] for r in rows}):
        mem = [r for r in rows if r["profile"] == prof]
        f = {}
        for k in fields:
            vals = collections.Counter(
                json.dumps(r.get(k)) for r in mem)
            f[k] = json.loads(vals.most_common(1)[0][0])
        out[prof] = f
    return out


def env_block(row, floors, mid):
    """The `env:` mapping for one checkpoint: profile + deviations + why.

    Returns (env, unexplained) -- `unexplained` names any override field that
    got no reason. **The first version of this check asked only "is there a
    `why` at all", and passed Zamba2 with a `kernels` override explained by a
    sentence about transformers.** A coarse predicate standing in for a fine
    fact is the defect this repo keeps paying for; the check is now per field.
    """
    prof = row["profile"]
    if mid in CORRECT:
        prof = CORRECT[mid][0]
    fl = floors[prof]
    explained = set()
    env = {"profile": prof}
    why = []

    for k in ("transformers", "torch", "kernels", "compute_dtype",
              "tokenizer_loader"):
        v = row.get(k)
        if v in (None, [], {}, ""):
            continue
        if v == fl.get(k):
            continue
        env[k] = v
        r = row.get(k + "_reason")
        if r:
            why.append(r)
            explained.add(k)
        elif k in ("kernels", "compute_dtype") and prof in PROFILE_WHY:
            #: the profile's own text IS the reason for these two -- `ssm` and
            #: `bf16` exist to state exactly them.
            explained.add(k)

    pk = row.get("packages") or {}
    if pk:
        env["packages"] = pk
        for p, r in (row.get("packages_reason") or {}).items():
            why.append("%s: %s" % (p, r))
            explained.add("packages")

    #: **NOT EVERY EXCLUSION IS AN ENVIRONMENT FACT.** `no_base_released` says
    #: phi-4 can never be the BASE ARM of a pair, because Microsoft never shipped
    #: the pretrained-only 14B -- and the archive's own row says so in as many
    #: words: "It runs and its distribution is fine. Exclude from pair rosters,
    #: not from distribution rosters." Writing it into `env.blocked` made
    #: `fleet()` skip three checkpoints that run, which is the mirror of the
    #: mosaicml defect: there a dead repo was inherited by a live mirror, here a
    #: POPULATION ruling was filed as an ENVIRONMENT one. Only these two kinds
    #: mean "this box cannot obtain the weights".
    exc = row.get("exclusion") or {}
    if exc.get("kind") in ("no_base_released",):
        exc = {}
    if row.get("blocked") and not exc:
        exc = {}
    if exc:
        env["blocked"] = exc.get("kind", "blocked")
        why.append(exc.get("why") or row.get("blocked_reason") or "")
        if exc.get("reversible_by"):
            why.append("reversible by: %s" % exc["reversible_by"])
        if exc.get("also"):
            why.append(exc["also"])
        explained.add("blocked")

    if mid in FIDELITY_WHY:
        why.append(FIDELITY_WHY[mid])
        explained.add("tokenizer_loader")

    if mid in BOX_OVERRIDE:
        env["box"] = BOX_OVERRIDE[mid]
        why.append(BOX_OVERRIDE_WHY)
        explained.add("box")

    if mid in CORRECT:
        why.append(CORRECT_WHY)
        explained.add(CORRECT[mid][1])
        explained.add("kernels")

    #: THE PROFILE ITSELF IS A CLAIM AND CARRIES ITS REASON. `torch26`, `tf457`,
    #: `ssm` and `bf16` each exist because a run died; a checkpoint declaring one
    #: with no `why` would be citing a rule whose reason is in another file.
    if prof != "default" and not why:
        why.append(PROFILE_WHY[prof])

    why = [w.strip() for w in why if w and w.strip()]
    if len(env) > 1 or prof != "default":
        env["why"] = " ".join(why) if why else None
    unexplained = sorted((set(env) - {"profile", "why"}) - explained)
    if prof != "default" and "profile" not in explained and not why:
        unexplained.append("profile")
    return env, unexplained


PROFILE_WHY = {
    "default": "safetensors, dense, current transformers.",
    "torch26": "bin-only weights: transformers' check_torch_load_is_safe refuses "
               ".bin under torch<2.6 (CVE-driven torch.load policy). Thirteen "
               "models failed this way in the July grid and it read as a model "
               "problem, not an environment one.",
    "tf457": "transformers 5.x CANNOT RUN this; pin 4.57.1.",
    "ssm": "mamba-ssm + causal-conv1d. NOT optional for hybrids: 19.3x measured "
           "on Falcon-H1-7B (0.0670 -> 1.2933 cells/s, A100 bf16). The pure-SSM "
           "null does not generalise to hybrids.",
    "bf16": "compute in bfloat16, NOT float16: fp16 overflows the SSM scan and "
            "yields all-NaN logits on prompts >=13 tokens (1/12 finite at fp16, "
            "12/12 at bf16). Storage stays f16.",
    "twogpu": "~140GB bf16 per arm; device_map=auto shards across two cards. A "
              "single card OOMs AFTER paying for the download.",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--force", action="store_true",
                    help="re-run after the one-shot. Overwrites hand edits.")
    a = ap.parse_args()

    if a.write and os.path.exists(ENVS_YAML) and not a.force:
        raise SystemExit(
            "environments.yaml exists -- this script already ran.\n"
            "It is a RECORD of the one-shot ingest, not a maintenance tool:\n"
            "re-running replaces hand edits with the archive's frozen state.\n"
            "Edit the yaml by hand, or pass --force if you mean it.")

    from malignment import roster
    req, envs, vllm, boxes = load_sources()
    rows = {r["model"]: r for r in req["requirements"]}
    floors = profile_floors(list(rows.values()))
    ros = sorted(roster.population("all"))

    print("profile floors, derived from %d archive rows:" % len(rows))
    for p, f in sorted(floors.items()):
        print("  %-9s %s" % (p, {k: v for k, v in f.items() if v not in (None, [])}))

    resolved, missing, unexplained = {}, [], {}
    for m in ros:
        r = rows.get(m)
        src = "own"
        if r is None and m in INHERIT:
            parent, kind = INHERIT[m]
            r = rows.get(parent)
            src = kind
        if r is None:
            missing.append(m)
            continue
        e, unexp = env_block(r, floors, m)
        if src != "own":
            for drop in INHERIT_DROP.get(src, ()):
                e.pop(drop, None)
            e["why"] = ((e.get("why") or "") + " " + INHERIT_WHY[src]).strip()
            unexp = [u for u in unexp if u not in INHERIT_DROP.get(src, ())]
        resolved[m] = e
        if unexp:
            unexplained[m] = unexp

    print("\n%d of %d checkpoints resolved" % (len(resolved), len(ros)))
    if missing:
        print("  UNRESOLVED (%d) -- the ingest STOPS rather than defaulting:" % len(missing))
        for m in missing:
            print("     ", m)
        raise SystemExit(1)

    prof = collections.Counter(e["profile"] for e in resolved.values())
    print("  profiles:", dict(prof))
    n_over = sum(1 for e in resolved.values() if set(e) - {"profile", "why"})
    print("  with overrides beyond the profile: %d" % n_over)
    print("  overrides with NO reason of their own (schema violation): %d"
          % len(unexplained))
    for m, u in sorted(unexplained.items()):
        print("     %-46s %s" % (m, u))
    if unexplained:
        raise SystemExit("REFUSING: an override with no reason is a rule whose "
                         "reason lives nowhere.")
    print("  corrections applied: %s" % sorted(CORRECT))

    orphans = sorted(set(rows) - set(ros))
    print("\n%d archive rows NOT imported (id superseded or out of roster):" % len(orphans))
    for m in orphans:
        print("     ", m)

    if not a.write:
        print("\ndry run. --write to apply.")
        return 0

    write_envs_yaml(boxes, floors)
    write_observations(envs, vllm)
    patch_models_yaml(resolved)
    print("\nwrote:\n  %s\n  %s\n  %s" % (ENVS_YAML, OBS_JSON, MODELS_YAML))
    return 0


def write_envs_yaml(boxes, floors):
    """The VOCABULARY: requirement profiles, box shapes, and the map between.

    Generated once from cloud_profiles.json rather than retyped, because
    transcribing 11 profiles x 11 fields by hand is exactly where a wrong
    min_gpu_ram enters. Hand-edited from here on.
    """
    from ruamel.yaml import YAML
    from ruamel.yaml.comments import CommentedMap
    y = YAML()
    y.preserve_quotes = True
    y.width = 4096

    doc = CommentedMap()
    doc.yaml_set_start_comment(HEADER)

    profs = CommentedMap()
    for p in sorted(floors):
        m = CommentedMap()
        m["why"] = PROFILE_WHY[p]
        for k, v in sorted(floors[p].items()):
            if v not in (None, [], {}):
                m[k] = v
        m["launch"] = LAUNCH_PROFILE[p]
        profs[p] = m
    doc["profiles"] = profs
    profs.yaml_set_start_comment(
        "REQUIREMENT profiles -- what a MODEL needs.\n"
        "`launch:` names the box below. AN ENVIRONMENT IS NOT A MACHINE SHAPE:\n"
        "`tf457` and `torch26` describe PACKAGE state, so a vast search naming\n"
        "them finds nothing -- the pin is applied after setup. `torch26`\n"
        "collapses onto a normal box because every box already pins torch>=2.6,\n"
        "which is why it exists as a LABEL and not as a provisioning difference.\n",
        indent=2)

    bx = CommentedMap()
    for k, v in boxes.items():
        if k.startswith("_"):
            continue
        m = CommentedMap()
        for f in ("description", "note", "image", "gpu_name", "num_gpus",
                  "min_gpu_ram", "disk_gb", "min_inet_down_mbps",
                  "min_reliability", "cuda_max_good", "pins", "pin_reasons"):
            if v.get(f) not in (None, "", [], {}):
                m[f] = v[f]
        #: `min_gpu_ram` is the VAST SEARCH FLOOR (47 to match 48 GB cards);
        #: `provides_vram_gb` is the card class you actually get. They differ by
        #: one GB and comparing a model's need against the wrong one is off by a
        #: whole hardware tier -- 48 vs 80.
        m["provides_vram_gb"] = 80 if (v.get("min_gpu_ram") or 0) >= 79 else 48
        bx[k] = m
    doc["boxes"] = bx
    bx.yaml_set_start_comment(BOXES_COMMENT, indent=2)

    #: **THE ENGINE PATH HAD NO EDGE IN THE LAUNCH MAP.** `profiles` route by
    #: what the MODEL needs; five boxes (vllm022, vllm022_a100, vllm0220,
    #: vllm0220_a100, vllm_nightly) are reachable only by what the ENGINE
    #: supports, and that route existed as English inside a `recovery:` string
    #: ("profile vllm022_a100"). A plan cannot follow prose.
    #: `null` means NO vLLM version works and the pair needs the transformers
    #: path -- which is a different answer from "untested", and both were
    #: previously the same silence.
    doc["engine_recovery"] = CommentedMap([
        ("_why", "architecture -> box that can host it, for architectures vLLM "
                 "REMOVED or never supported. Keyed on ARCHITECTURE because that "
                 "is the fact's shape: BaichuanForCausalLM went after 0.23.0 and "
                 "every Baichuan went with it."),
        ("AquilaForCausalLM", "vllm022_a100"),
        ("BaichuanForCausalLM", "vllm022_a100"),
        ("JAISLMHeadModel", "vllm0220_a100"),
        ("OlmoHybrid", "vllm_nightly"),
        ("RwkvForCausalLM", None),
        ("PhariaForCausalLM", None),
        ("Zamba2ForCausalLM", None),
        ("RecurrentGemmaForCausalLM", None),
    ])

    doc["sizing"] = CommentedMap([
        ("why", "min_vram_gb and num_gpus are a STEP FUNCTION of measured "
                "params_b, verified with no overlaps across 159 archive rows. "
                "Declared as a rule so 160 checkpoints do not each carry a "
                "derived number with no producer."),
        ("steps", [{"max_params_b": 9, "vram_gb": 24, "gpus": 1},
                   {"max_params_b": 17, "vram_gb": 48, "gpus": 1},
                   {"max_params_b": 35, "vram_gb": 80, "gpus": 1},
                   {"max_params_b": None, "vram_gb": 80, "gpus": 2}]),
    ])
    with open(ENVS_YAML, "w") as fh:
        y.dump(doc, fh)


LAUNCH_PROFILE = {"default": "dense", "torch26": "dense", "tf457": "dense",
                  "ssm": "ssm", "twogpu": "twogpu", "bf16": "big80"}

HEADER = """ENVIRONMENTS: what a checkpoint needs, and what to rent to give it.
AUTHORED. Hand-edit this. Ingested once from the archive on 2026-08-16 by
scripts/ingest_environments.py, which is a record of that ingest and not a
maintenance tool.

TWO VOCABULARIES, AND THEY ARE NOT THE SAME ONE. `profiles` are what a MODEL
needs. `boxes` are machine SHAPES to rent. They were separate files in the
archive with the map between them buried in scripts/build_fleet.py:78, so a
seat reading either one alone could not answer "what do I rent for this model".

WHAT IS NOT HERE: whether a model LOADED. That is a property of
(model x environment), not of either, and it lives in
roster/models/observations.json -- seven models carry both a failure and a
success. Nor (architecture x engine) support: Aquila is not broken, vLLM
DELETED it after v0.24.0.
"""

BOXES_COMMENT = """BOX shapes for `malign cloud launch --profile NAME`.

THERE ARE NO vast.ai TEMPLATES. The template's whole role is played by
`image`, and there are only five distinct images across these entries. A box
is (shape x image x pins); the names below are a partially-enumerated
cross-product, which is why "ssm on the 0.22.1 image" cannot be named today.

min_inet_down_mbps IS A SELECTION CRITERION AND WE NEVER FILTERED ON IT until
2026-08-02: compute parallelises across GPUs and the network does not. A 4xA100
box at identical per-GPU price was the SLOWEST option on the board because its
link was 624 Mbps against a 1.42 TB roster -- 10.0 h -> 15.1 h, $42 -> $63,
entirely on a field nobody was looking at.
"""


def write_observations(envs, vllm):
    """OBSERVED: (model x environment) outcomes and (architecture x engine) support."""
    doc = {
        "_about": "OBSERVED. What HAPPENED, keyed the way the fact is actually "
                  "shaped. Neither block is per-checkpoint and neither can be "
                  "folded into models.yaml without destroying its meaning.",
        "_why_not_in_models_yaml":
            "WHETHER A MODEL LOADS IS NOT A PROPERTY OF THE MODEL. Seven models "
            "here carry BOTH a load_failed and a loads: AmberSafe failed and "
            "then succeeded ON THE SAME BOX after two packages were installed. "
            "Authoring 'AmberSafe: load_failed' would state as a model fact "
            "something that was true of a box for twenty minutes.",
        "_absence": "Absence of an observation means UNTESTED, never 'works'.",
        "_source": "malign-logits/data/model_load_environments.json and "
                   "data/vllm_engine_support.json, ingested 2026-08-16.",
        "environments": envs["environments"],
        "observations": envs["observations"],
        #: FLATTENED TO arch -> ruling. The source nests these under
        #: `architectures` beside three sibling blocks, and a resolver written
        #: against the outer dict iterates `engine_versions_available` looking
        #: for a model list, finds none, and returns None for EVERY model --
        #: which reads exactly like "no ruling exists", the same shape as
        #: "supported". Caught by exercising Aquila, whose whole point is that
        #: it has a ruling.
        "engine_support": vllm.get("architectures", {}),
        "engine_versions": vllm.get("engine_versions_available", {}),
        #: NOT (architecture x engine): these load and host fine and die in
        #: TOKENIZATION or DETOKENIZATION. Kept because the operational
        #: question -- "will this fleet lose the pair?" -- is the same one.
        "tokenizer_class": vllm.get("tokenizer_class", {}),
        "_error_shape": vllm.get("_error_shape"),
        "_engine_support_about": vllm.get("_about"),
    }
    with open(OBS_JSON, "w") as fh:
        json.dump(doc, fh, indent=1, ensure_ascii=False)
        fh.write("\n")


def patch_models_yaml(resolved):
    """Add `env:` to every node. ruamel round-trip: comments must survive.

    `yaml.safe_dump` destroyed 114 comment lines and 16 evidence quotes on this
    file once. ruamel is a dependency of this repo for exactly this call.
    """
    from ruamel.yaml import YAML
    y = YAML()
    y.preserve_quotes = True
    y.width = 4096
    #: **MATCH THE FILE'S EXISTING STYLE.** ruamel's default (sequence=4,
    #: offset=2) re-indents every block sequence in the file: a first run
    #: produced 954 insertions and 608 deletions for what is 160 additions,
    #: burying the real change in cosmetic churn. The file writes `- yi` flush
    #: under its key, which is sequence=2, offset=0.
    y.indent(mapping=2, sequence=2, offset=0)
    with open(MODELS_YAML) as fh:
        doc = y.load(fh)
    from ruamel.yaml.comments import CommentedMap
    n = 0
    for mid, node in doc["nodes"].items():
        e = resolved.get(mid)
        if e is None:
            continue
        m = CommentedMap()
        for k, v in e.items():
            if v is not None:
                m[k] = v
        node["env"] = m
        n += 1
    with open(MODELS_YAML, "w") as fh:
        y.dump(doc, fh)
    print("  patched %d nodes with env:" % n)


if __name__ == "__main__":
    sys.exit(main())
