#!/usr/bin/env python
"""What dtype each checkpoint is STORED in. Not what it must be RUN in.

    python scripts/probe_config_dtype.py
    python scripts/probe_config_dtype.py --write   -> measurements.json `config_dtype`

## THE WHOLE POINT OF THIS FILE IS THAT THESE ARE TWO DIFFERENT FACTS

    safetensors `parameters`      what the weights ARE, from the files.
    config.json `torch_dtype`     the author's annotation of the same thing,
                                  and sometimes simply ABSENT.
                                  130 of 160 are bfloat16.
    roster `env.dtype`            what we must COMPUTE in, because the
                                  alternative is WRONG. 12 models.

**DERIVING THE SECOND FROM THE FIRST WOULD HAVE BEEN A DISASTER.** bf16 needs
compute capability 8.0, so treating all 130 as bf16-requiring would refuse every
Turing card for them -- and the Quadro RTX 8000 is our most-rented board, with
48 rate observations and thousands of cells for models in exactly that list. The
corpus holds 55,680 cells produced at float16. They are fine.

The 12 are the ones where fp16 is BROKEN, not merely different: Falcon-H1's
all-NaN overflow through the SSM scan, gemma-2's numerical instability. That is a
requirement. A storage dtype is a fact about a file.

## WHY IT IS WORTH RECORDING AT ALL

Two things read it. **Download size**: fp32 weights are twice the bytes, and
`Olmo-3.1-32B-Instruct-SFT`/`-DPO` ship F32 at 128.9 GB against their base's
BF16 64.5 GB -- assuming uniform size once nearly ran a 300 GB disk out mid-DPO.
And **`granite-3.0-8b`'s two arms disagree**: base F32 (8.17B x 4 = 32.7 GB),
instruct BF16 (16.3 GB) -- a same-lineage asymmetry a sizing rule keyed on
params alone cannot see. The chatlog that surfaced this called the instruct arm
fp16; it is bf16. Both are two bytes, so the SIZE was right and the dtype was
wrong, which is exactly why nobody caught it.

## AND IT SAYS NOTHING ABOUT WHETHER A LOADER WILL PICK IT

`transformers` selects bf16 from this field ONLY under `torch_dtype="auto"`.
Our loader hardcodes float16 (`runners.compute_dtype`, default `torch.float16`),
so the chatlogged Baichuan2 failure -- bf16 auto-selected, unsupported on a
Turing card -- is real for the vLLM Y-fleet path and does NOT apply here. Which
loader asked is part of that fact and is recorded with it.
"""
import argparse
import concurrent.futures as cf
import json
import os
import sys
import urllib.error
import urllib.request
from collections import Counter, OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

MEAS = os.path.join(ROOT, "roster", "models", "measurements.json")


def _token():
    p = os.path.expanduser("~/.cache/huggingface/token")
    return open(p).read().strip() if os.path.exists(p) else None


#: safetensors names dtypes in its own vocabulary.
_ST = {"F32": "float32", "BF16": "bfloat16", "F16": "float16",
       "F8_E4M3": "float8_e4m3", "I8": "int8", "U8": "uint8"}


def _get(url, token, timeout=40):
    req = urllib.request.Request(url)
    if token:
        req.add_header("Authorization", "Bearer %s" % token)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def probe(models, token, workers=12):
    """Storage dtype, from the WEIGHTS first and the config second.

    **CONFIG IS THE WEAKER INSTRUMENT AND THE FIRST VERSION USED ONLY IT.**
    `ibm-granite/granite-3.0-8b-base` has no `torch_dtype` key at all, so the
    config-only probe returned None while its safetensors index says `F32`
    without ambiguity -- 8.17B parameters at four bytes, the 32.7 GB download.
    Nine models answered None that way. The index is derived from the files
    themselves and cannot disagree with them; a config field is an author's
    annotation and is sometimes simply absent.
    """
    def one(m):
        repo = m.split("@")[0]
        rec = OrderedDict([("storage_dtype", None), ("source", None),
                           ("torch_dtype_config", None), ("error", None)])
        try:
            api = _get("https://huggingface.co/api/models/%s" % repo, token)
            params = ((api.get("safetensors") or {}).get("parameters") or {})
            if params:
                #: The dtype holding the MOST parameters. A repo can carry a
                #: stray I64 buffer beside 8B BF16 weights, and picking by name
                #: order would report the buffer as the model's dtype.
                top = max(params.items(), key=lambda kv: kv[1])[0]
                rec["storage_dtype"] = _ST.get(top, top)
                rec["source"] = "safetensors.parameters"
                rec["dtype_bytes"] = params
        except urllib.error.HTTPError as e:
            rec["error"] = "HTTP %s" % e.code
        except Exception as e:                                   # noqa: BLE001
            rec["error"] = type(e).__name__
        try:
            d = _get("https://huggingface.co/%s/resolve/main/config.json" % repo,
                     token)
            rec["torch_dtype_config"] = d.get("torch_dtype") or d.get("dtype")
            rec["architectures"] = (d.get("architectures") or [None])[0]
            if rec["storage_dtype"] is None and rec["torch_dtype_config"]:
                rec["storage_dtype"] = rec["torch_dtype_config"]
                rec["source"] = "config.json"
                rec["error"] = None
        except Exception:                                        # noqa: BLE001
            pass
        return m, rec
    out = OrderedDict()
    with cf.ThreadPoolExecutor(workers) as ex:
        for m, rec in ex.map(one, models):
            out[m] = rec
    return OrderedDict(sorted(out.items()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    import yaml
    nodes = yaml.safe_load(open(os.path.join(ROOT, "roster", "models",
                                             "models.yaml")))["nodes"]
    res = probe(sorted(nodes), _token())
    c = Counter(v["storage_dtype"] for v in res.values())
    print("STORAGE dtype (weights first, config as fallback):")
    for k, n in c.most_common():
        print("   %-12s %d" % (k, n))
    req = {r["model"]: r for r in json.load(open(os.path.join(
        ROOT, "roster", "models", "requirements.json")))["requirements"]}
    need = {m for m, r in req.items() if r.get("compute_dtype") == "bfloat16"}
    says = {m for m, v in res.items() if v["storage_dtype"] == "bfloat16"}
    print("\nstored bf16            %d" % len(says))
    print("REQUIRE bf16 to run    %d   <-- the only ones that constrain a card"
          % len(need))
    print("stored bf16, runs fine at fp16: %d" % len(says - need))
    miss = [m for m, v in res.items() if v.get("error")]
    if miss:
        print("\nunreadable config: %d" % len(miss))
        for m in miss[:6]:
            print("   %-52s %s" % (m, res[m]["error"]))
    if not a.write:
        print("\nDRY RUN -- pass --write.")
        return 0
    doc = json.load(open(MEAS), object_pairs_hook=OrderedDict)
    doc["sections"]["config_dtype"] = OrderedDict([
        ("_why", "STORAGE dtype, from safetensors `parameters` where present "
                 "and config.json only as a fallback. NOT a compute "
                 "requirement: 130 of 160 are bfloat16 while only 12 must RUN "
                 "in it, and the corpus holds 55,680 cells at float16 for "
                 "models in that 130. Read it for DOWNLOAD SIZE (fp32 is twice "
                 "the bytes) and for same-lineage asymmetries -- "
                 "granite-3.0-8b base is F32 and its instruct sibling BF16."),
        ("_instrument", "config.json is the WEAKER source and a config-only "
                        "probe returned None for 9 models, including "
                        "granite-3.0-8b-base, whose config carries no "
                        "torch_dtype at all while its safetensors index says "
                        "F32 without ambiguity."),
        ("_not_a_loader_verdict", "transformers picks this up only under "
                                  "torch_dtype='auto'. Our loader hardcodes "
                                  "float16 (runners.compute_dtype), so a card "
                                  "that cannot do bf16 is irrelevant here even "
                                  "when the config says bfloat16."),
        ("measured_by", "scripts/probe_config_dtype.py"),
        ("n", len(res)),
        ("models", res),
    ])
    with open(MEAS, "w") as fh:
        json.dump(doc, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    print("\nwrote `config_dtype` for %d models" % len(res))
    return 0


if __name__ == "__main__":
    sys.exit(main())
