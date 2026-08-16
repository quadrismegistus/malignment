#!/usr/bin/env python
"""Measure `params_b` from PUBLISHED FILE SIZES for repos the safetensors route cannot reach.

## WHY THE EXISTING PASS CANNOT MEASURE THESE

`malignment.observe --weights` calls `HfApi().model_info(expand=['safetensors'])`.
That field is a SERVER-SIDE INDEX of safetensors headers: the Hub parses the
header of every `*.safetensors` file in a repo and publishes `{dtype: n_params}`.
A repo that ships `pytorch_model-*.bin` has no safetensors header to parse, so
the field is absent — not "small", not "zero", ABSENT. The pass recorded 19 such
repos as "no safetensors metadata published", which is an honest answer and a
permanently unimprovable one BY THAT ROUTE. Re-running it can never help.

Two routes that do work, neither of which downloads weights:

    route 1 "file_sizes"      model_info(files_metadata=True) returns a `size`
                              per sibling file. Sum the weight shards, divide by
                              bytes-per-parameter read from the first shard's
                              header. This measures WHAT MUST FIT IN VRAM, which
                              is what `roster._sizing()` actually wants.
    route 2 "config_analytic" hf_hub_download of config.json alone (a few kB) and
                              the transformer parameter formula. A cross-check on
                              route 1, and the fallback when a repo's file sizes
                              are unavailable.

Route 2 IS A TRANSFORMER FORMULA AND ONLY A TRANSFORMER FORMULA. RWKV (linear
attention, no KV projections) and MPT (non-gated FFN, ALiBi) are handled by
architecture; anything unrecognised returns None with a reason rather than a
number produced by a formula that does not describe the model.

## THE DTYPE IN config.json IS A DECLARATION, NOT THE STORED FORMAT

`BAAI/AquilaChat2-7B` declares `torch_dtype: "float16"` and ships 29.2 GB of
`.bin` across 3 shards. Divide by the declared 2 bytes and you get **14.591B**
for a model whose own config (4096 x 32, vocab 100008, untied) cannot exceed
7.296B. The shards are float32: a Range read of the first 2 MB of shard 1 finds
`FloatStorage` and no `HalfStorage`. The declared dtype was wrong by a factor of
two, in the direction that pushes a 7B model over the 9B step and rents a 48 GB
box for it.

So bytes-per-parameter comes from a RANGE READ OF THE FIRST SHARD'S HEADER —
the safetensors JSON header, or the pickle's `*Storage` tokens for `.bin` — and
falls back to the config's declaration only when the probe cannot read one. Both
are recorded (`dtype`, `dtype_declared`) and a mismatch is kept in the entry,
because the next seat to hit this repo needs to know the config lies.

Tied embeddings are observed the same way. `tie_word_embeddings` is absent from
SmolLM3's and MPT's configs and the transformers default flips by config class,
so route 2 reads the SHARD INDEX instead: no `lm_head.weight` in the weight map
means the matrix is shared, which is a fact about the files rather than a guess
about the class hierarchy.

## WHAT THE NUMBER IS FOR

`roster.environment()` steps params_b into VRAM: <=9B -> 24 GB, <=17B -> 48,
<=35B -> 80, else 2x80. Accuracy matters at those edges and almost nowhere else,
so the script flags any model landing within 10% of a boundary.

## IDEMPOTENCE

Writes only `sections.weights_from_files`, at the file's own indent so the diff
is an addition and not a reformat. Re-running remeasures THE SAME POPULATION —
this section's existing models plus any roster id no other section has measured —
and rewrites that one section with a fresh stamp; every other section is loaded
and dumped untouched. So a re-run reproduces the section, and a model added to
`models.yaml` joins it on the next run with no list here to maintain.

    python scripts/measure_weights_from_files.py --dry-run
    python scripts/measure_weights_from_files.py --write
"""
import argparse
import json
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OBSERVED = os.path.join(ROOT, "roster", "models", "measurements.json")
MODELS_YAML = os.path.join(ROOT, "roster", "models", "models.yaml")
SECTION = "weights_from_files"

ROUTE = ("scripts/measure_weights_from_files.py: huggingface_hub "
         "HfApi().model_info(files_metadata=True) -> sum of weight-shard `size` / "
         "bytes-per-param read from the first shard's header (safetensors JSON header or "
         "pickle *Storage token, HTTP Range, no weights downloaded); cross-checked against "
         "the transformer parameter formula on config.json. No safetensors metadata is "
         "involved, which is why it reaches the .bin repos `weights` could not.")

#: bytes per stored parameter. The file on the Hub is the dtype it was SAVED in,
#: which is what the download costs and what a full-precision load occupies.
BPP = {"float16": 2, "fp16": 2, "half": 2, "bfloat16": 2, "bf16": 2,
       "float32": 4, "fp32": 4, "float": 4, "float64": 8,
       "int8": 1, "uint8": 1, "int4": 0.5}

#: `.bin` files that are not weights. `training_args.bin` is a pickled argparse
#: namespace and turns up in SFT repos; counting it is a rounding error, but the
#: optimizer states in some checkpoint repos are 2x the model.
NOT_WEIGHTS = re.compile(
    r"(training_args|optimizer|scheduler|rng_state|adapter_|tokenizer|"
    r"scaler|trainer_state)", re.I)
WEIGHT_EXT = (".safetensors", ".bin", ".pt", ".pth")


def _log(*a):
    print(*a, file=sys.stderr, flush=True)


# --------------------------------------------------------------------------- #
# population
# --------------------------------------------------------------------------- #
def _yaml_nodes():
    import yaml
    with open(MODELS_YAML, encoding="utf-8") as fh:
        return yaml.safe_load(fh).get("nodes") or {}


def population(doc, only_missing=True):
    """Roster ids this section is responsible for.

    The population is the AUTHORED roster, exactly as `observe.roster_ids()` has
    it, so a checkpoint added to models.yaml is measurable with no list here to
    maintain. `only_missing` reads EVERY OTHER section, not a named one — the
    same rule `roster._measured_params()` uses to consume the file.

    **THIS SECTION'S OWN MODELS ARE ALWAYS IN THE POPULATION.** Skipping what is
    already measured is right for models another pass owns and fatal for the ones
    this pass owns: a second `--write` would find nothing missing, measure zero,
    and overwrite `weights_from_files` with an empty models dict and a fresh
    stamp. Idempotent means a re-run REPRODUCES the section, not that it declines
    to write one.
    """
    ids = sorted(_yaml_nodes())
    if not only_missing:
        return ids
    mine = set((doc.get("sections", {}).get(SECTION, {}).get("models") or {}))
    have = set()
    for name, sec in (doc.get("sections") or {}).items():
        if name == SECTION:
            continue
        for k, v in (sec.get("models") or {}).items():
            if isinstance(v, dict) and v.get("params_b"):
                have.add(k)
    return [m for m in ids if m in mine or m not in have]


def split_revision(model_id, nodes):
    """`repo@revision` -> (repo, revision, source).

    A bare id can still need a revision: `SmolLM3-3B-checkpoints` is a revision
    CONTAINER whose `main` holds a README and nothing else, and models.yaml pins
    `revision: it-SFT`. Measuring `main` there would not fail — it would return
    zero weight files, which is the failure that looks like an answer.
    """
    if "@" in model_id:
        repo, rev = model_id.split("@", 1)
        return repo, rev, "id"
    rev = (nodes.get(model_id) or {}).get("revision")
    return model_id, (rev or None), ("models.yaml" if rev else "default")


# --------------------------------------------------------------------------- #
# route 1: file sizes
# --------------------------------------------------------------------------- #
def weight_files(siblings):
    """(chosen files, format). Prefers safetensors when a repo ships both, which
    several do — summing both formats double-counts the whole model."""
    cand = [s for s in siblings
            if s.rfilename.endswith(WEIGHT_EXT) and not NOT_WEIGHTS.search(s.rfilename)]
    st = [s for s in cand if s.rfilename.endswith(".safetensors")]
    bins = [s for s in cand if not s.rfilename.endswith(".safetensors")]
    if st and bins:
        #: "mixed" is the existing `weights` section's word for a repo carrying
        #: both; only the safetensors set is summed, and `counted_format` says so.
        return st, "mixed"
    if st:
        return st, "safetensors"
    if bins:
        return bins, "bin"
    return [], None


def dtype_of(cfg):
    for k in ("torch_dtype", "dtype"):
        v = (cfg or {}).get(k)
        if isinstance(v, str) and v.replace("torch.", "") in BPP:
            return v.replace("torch.", "")
    return None


#: safetensors header dtype names -> the config-style names BPP is keyed on.
ST_DTYPE = {"F64": "float64", "F32": "float32", "F16": "float16", "BF16": "bfloat16",
            "I8": "int8", "U8": "uint8", "I64": "int64", "I32": "int32", "F8_E4M3": "int8"}
PICKLE_DTYPE = [(b"BFloat16Storage", "bfloat16"), (b"HalfStorage", "float16"),
                (b"FloatStorage", "float32"), (b"DoubleStorage", "float64"),
                (b"CharStorage", "int8"), (b"ByteStorage", "uint8")]


def _range(url, lo, hi, token):
    import requests
    h = {"Range": "bytes=%d-%d" % (lo, hi)}
    if token:
        h["Authorization"] = "Bearer " + token
    r = requests.get(url, headers=h, allow_redirects=True, timeout=60)
    r.raise_for_status()
    return r.content


def probe_dtype(repo, revision, filename, token):
    """Stored dtype of the first weight shard, read from its header. (dtype, how).

    Not the config's word for it — see the module docstring. Downloads at most
    the first few MB of ONE shard and never the tensors.
    """
    url = "https://huggingface.co/%s/resolve/%s/%s" % (repo, revision or "main", filename)
    try:
        if filename.endswith(".safetensors"):
            n = int.from_bytes(_range(url, 0, 7, token), "little")
            if n <= 0 or n > 200_000_000:
                return None, "safetensors header length implausible (%d)" % n
            hdr = json.loads(_range(url, 8, 8 + n - 1, token).decode("utf-8"))
            dts = {v["dtype"] for k, v in hdr.items()
                   if k != "__metadata__" and isinstance(v, dict) and "dtype" in v}
            if len(dts) == 1:
                d = ST_DTYPE.get(dts.pop())
                return d, "safetensors header"
            return None, "shard mixes dtypes %s" % sorted(dts)
        blob = _range(url, 0, 4_000_000, token)
        hits = [name for tok, name in PICKLE_DTYPE if tok in blob]
        if len(hits) == 1:
            return hits[0], "pickle header"
        if hits:
            return None, "pickle header mixes dtypes %s" % hits
        return None, "no storage token in first 4 MB"
    except Exception as e:                                  # noqa: BLE001
        return None, "%s: %s" % (type(e).__name__, str(e).split("\n")[0][:120])


def tied_from_index(repo, revision, files, token):
    """Are the embeddings shared? Read the shard index's weight map. (bool, how).

    An output matrix that is not in the weight map is not stored, and route 2
    must not count it. Returns (None, reason) for single-shard repos, which have
    no index — there the config's key is all there is.
    """
    from huggingface_hub import hf_hub_download
    for name in ("model.safetensors.index.json", "pytorch_model.bin.index.json"):
        if not any(s.rfilename == name for s in files):
            continue
        try:
            with open(hf_hub_download(repo, name, revision=revision, token=token),
                      encoding="utf-8") as fh:
                wm = (json.load(fh).get("weight_map") or {})
        except Exception as e:                              # noqa: BLE001
            return None, "%s: %s" % (type(e).__name__, str(e)[:100])
        heads = [k for k in wm if k.endswith(("lm_head.weight", "embed_out.weight",
                                              "output.weight"))]
        return (not heads), name
    return None, "no shard index (single-file repo)"


# --------------------------------------------------------------------------- #
# route 2: the parameter formula
# --------------------------------------------------------------------------- #
GATED = {  # SwiGLU: gate + up + down
    "llamaforcausallm", "mistralforcausallm", "qwen2forcausallm", "qwen3forcausallm",
    "internlm2forcausallm", "baichuanforcausallm", "baichuanforcausallm2",
    "olmoforcausallm", "olmo2forcausallm", "olmo3forcausallm", "aquilaforcausallm",
    "smollm3forcausallm", "deepseekforcausallm", "gemmaforcausallm",
}
UNGATED = {  # h -> 4h -> h
    "gptneoxforcausallm", "gpt2lmheadmodel", "gptjforcausallm", "mptforcausallm",
    "falconforcausallm", "rwforcausallm",
}


def analytic(cfg, tied=None):
    """Parameter count from config.json, or (None, reason).

    Returns the STORED parameter count: embeddings + blocks + head, with the head
    dropped when the embeddings are shared. `tied` is the OBSERVED answer from
    the shard index when there is one; the config's key is the fallback and the
    transformers default (True) the last resort, because that default is what
    every config class silently overrides. Norm and bias terms are included where
    they are cheap to state and ignored where the config does not say (they are
    <0.1% at 7B; a route-1/route-2 gap of that size is noise, a gap of 5% is a
    wrong formula).
    """
    archs = [a.lower() for a in (cfg.get("architectures") or [])]
    a = archs[0] if archs else ""
    h = cfg.get("hidden_size") or cfg.get("n_embd") or cfg.get("d_model")
    L = (cfg.get("num_hidden_layers") or cfg.get("n_layer")
         or cfg.get("num_layers") or cfg.get("n_layers"))
    V = cfg.get("vocab_size")
    if not (h and L and V):
        return None, "config lacks hidden_size/num_hidden_layers/vocab_size"
    if "rwkv" in a or "rwkv" in str(cfg.get("model_type", "")).lower():
        return None, "RWKV is not a transformer; route-2 formula does not apply"
    if "mamba" in a or "mamba" in str(cfg.get("model_type", "")).lower():
        return None, "SSM is not a transformer; route-2 formula does not apply"

    nh = cfg.get("num_attention_heads") or cfg.get("n_head") or cfg.get("n_heads")
    nkv = cfg.get("num_key_value_heads") or cfg.get("num_kv_heads") or nh
    if cfg.get("multi_query"):          # MPT / Falcon MQA
        nkv = 1
    hd = cfg.get("head_dim") or (h // nh if nh else None)
    if not (nh and hd):
        return None, "config lacks head counts"
    inter = (cfg.get("intermediate_size") or cfg.get("ffn_hidden_size")
             or cfg.get("n_inner") or cfg.get("d_ff"))
    ffn_mult = (cfg.get("ffn_config") or {}).get("ffn_hidden_size")
    if ffn_mult:
        inter = ffn_mult
    if inter is None:
        exp = cfg.get("expansion_ratio") or 4
        inter = int(h * exp)

    attn = h * (nh * hd) + 2 * h * (nkv * hd) + (nh * hd) * h

    n_exp = cfg.get("num_experts") or cfg.get("num_local_experts")
    if n_exp:                                   # MoE: every expert is stored
        mlp = n_exp * 3 * h * inter + h * n_exp
    elif a in GATED or (a not in UNGATED and cfg.get("intermediate_size")
                        and str(cfg.get("hidden_act", "")).startswith("sil")):
        mlp = 3 * h * inter
    elif a in UNGATED:
        mlp = 2 * h * inter
    else:
        return None, "architecture %r not in the route-2 formula table" % (a or "?")

    per_layer = attn + mlp + 2 * h
    total = V * h + L * per_layer + h
    if tied is None:
        tied = cfg.get("tie_word_embeddings")
    if tied is None:
        tied = True
    if not tied:
        total += V * h
    return total, None


# --------------------------------------------------------------------------- #
def measure(model_id, nodes, api, token):
    from huggingface_hub import hf_hub_download
    repo, rev, rev_src = split_revision(model_id, nodes)
    out = {"repo": repo}
    if rev:
        out["revision"] = rev
        out["revision_source"] = rev_src

    info = api.model_info(repo, revision=rev, files_metadata=True)
    files, fmt = weight_files(info.siblings)

    cfg, cfg_err = None, None
    try:
        p = hf_hub_download(repo, "config.json", revision=rev, token=token)
        with open(p, encoding="utf-8") as fh:
            cfg = json.load(fh)
    except Exception as e:                                  # noqa: BLE001
        cfg_err = "%s: %s" % (type(e).__name__, str(e).split("\n")[0][:160])

    if cfg:
        out["architecture"] = (cfg.get("architectures") or [None])[0]
        if cfg.get("quantization_config"):
            out["quantized"] = True
    declared = dtype_of(cfg)

    p_files, tied = None, None
    if files:
        shards = sorted(files, key=lambda s: s.rfilename)
        nbytes = sum(s.size or 0 for s in shards)
        out["weights_format"] = fmt
        if fmt == "mixed":
            out["counted_format"] = "safetensors"
        out["n_weight_files"] = len(shards)
        out["weight_bytes"] = nbytes
        probed, how = probe_dtype(repo, rev, shards[0].rfilename, token)
        if probed is None and "mixes dtypes" in how:
            out["dtype_shard_mix"] = how
        dt = probed or declared
        if dt:
            out["dtype"] = dt
        out["dtype_source"] = how if probed else ("config.json (%s)" % how)
        if declared and probed and declared != probed:
            #: KEPT, NOT RESOLVED SILENTLY. The declaration is what every tool
            #: that reads config.json will believe about this repo.
            out["dtype_declared"] = declared
            out["dtype_mismatch"] = "config declares %s; shards store %s" % (declared, probed)
        if nbytes and dt in BPP:
            p_files = nbytes / BPP[dt] / 1e9
        elif nbytes:
            out["note"] = "stored dtype unknown (%s); params_b not derivable from bytes" % how
        tied, tied_how = tied_from_index(repo, rev, info.siblings, token)
        if tied is not None:
            out["tied_embeddings"] = tied
            out["tied_source"] = tied_how
    elif cfg_err is None:
        out["note"] = "no weight files at this revision"

    p_cfg, why = (analytic(cfg, tied) if cfg else (None, cfg_err))
    if p_cfg:
        out["params_b_config"] = round(p_cfg / 1e9, 3)
    elif why:
        out["config_analytic_note"] = why

    if p_files:
        out["params_b"] = round(p_files, 3)
        out["route"] = "file_sizes"
    elif p_cfg:
        out["params_b"] = round(p_cfg / 1e9, 3)
        out["route"] = "config_analytic"
        out.setdefault("weights_format", fmt or "unknown")
    else:
        raise RuntimeError("no route succeeded (files=%d, config=%s)"
                           % (len(files), cfg_err or "read"))

    if p_files and p_cfg:
        d = abs(p_files - p_cfg / 1e9) / (p_cfg / 1e9)
        out["routes_agree_pct"] = round(100 * d, 2)
    return out


BOUNDARIES = (9, 17, 35)


def near_boundary(p, frac=0.10):
    return [b for b in BOUNDARIES if abs(p - b) <= frac * b]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="write measurements.json")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--all", action="store_true",
                    help="remeasure every roster id, not only those lacking params_b")
    ap.add_argument("--models", nargs="*", help="explicit ids instead of the roster")
    args = ap.parse_args()

    from huggingface_hub import HfApi
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    api = HfApi(token=token)

    with open(OBSERVED, encoding="utf-8") as fh:
        doc = json.load(fh)
    nodes = _yaml_nodes()
    ids = args.models or population(doc, only_missing=not args.all)
    _log("population: %d" % len(ids))

    models, bad = {}, {}
    for i, m in enumerate(ids, 1):
        try:
            models[m] = measure(m, nodes, api, token)
            _log("[%d/%d] %-58s %8.3fB  %s" % (i, len(ids), m,
                                               models[m]["params_b"], models[m]["route"]))
        except Exception as e:                              # noqa: BLE001
            bad[m] = "%s: %s" % (type(e).__name__, str(e).split("\n")[0][:200])
            _log("[%d/%d] %-58s FAILED %s" % (i, len(ids), m, bad[m]))

    sec = {"_why": ("A SECOND ROUTE, NOT A RESTAMP OF THE FIRST. `weights` measured 138 "
                    "checkpoints on 2026-08-15 via model_info(expand=['safetensors']) and "
                    "named 19 it could not reach: those repos publish .bin, so no "
                    "safetensors header exists for the Hub to index and re-running that "
                    "call can never help. This section measures those 19 plus 7 added to "
                    "models.yaml afterwards, from file sizes. `weights` is left exactly as "
                    "it stood -- restamping it would assert a freshness that did not "
                    "happen -- and roster._measured_params() reads every section, taking "
                    "the later measured_at on conflict."),
           "measured_by": ROUTE,
           "measured_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "n": len(models),
           "models": dict(sorted(models.items())),
           "unmeasured": dict(sorted(bad.items()))}

    for m, v in sec["models"].items():
        if v.get("routes_agree_pct", 0) > 5:
            _log("DISAGREE >5%%: %s  files=%s config=%s (%.1f%%)"
                 % (m, v["params_b"], v.get("params_b_config"), v["routes_agree_pct"]))
        nb = near_boundary(v["params_b"])
        if nb:
            _log("NEAR VRAM BOUNDARY %s: %s = %.3fB" % (nb, m, v["params_b"]))
    #: A silent boundary check is indistinguishable from one that did not run.
    closest = sorted(((min(abs(v["params_b"] - b) / b for b in BOUNDARIES), m, v["params_b"])
                      for m, v in sec["models"].items()))[:3]
    for d, m, p in closest:
        _log("closest to a VRAM step: %-52s %7.3fB  (%.0f%% away)" % (m, p, 100 * d))

    if args.write and not args.dry_run:
        doc["sections"][SECTION] = sec
        #: indent=1, no trailing newline, ensure_ascii=False -- the file's OWN
        #: formatting, verified by round-tripping it before writing. A section
        #: appended under a different dump style reformats all 138 pre-existing
        #: entries, and a diff that touches every line cannot be reviewed for
        #: what actually changed.
        with open(OBSERVED, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=1, ensure_ascii=False)
        _log("wrote %s (%d measured, %d unmeasured)" % (OBSERVED, len(models), len(bad)))
    else:
        print(json.dumps(sec, indent=2))


if __name__ == "__main__":
    main()
