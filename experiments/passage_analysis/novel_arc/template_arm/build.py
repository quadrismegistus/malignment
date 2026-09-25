"""TEMPLATE_ARM.md's generation inputs: one prompts file per checkpoint, and the jobs lists.

    python build.py            # print the plan, write nothing
    python build.py --write

Population: roster.population("framed_empty") (41 lineages). Two prompt sets, both arms:

    f11   the 100 English f11_l2 strings Figure 5 draws from, n=20
    y     Y's 34 cells (superego_stages/prompts/y_cells.jsonl), n=50

Arms: base (base model, raw, NO TEMPLATE EVER), and on the aligned model raw, prefill
(system per system_mode; user "Hi."; assistant turn opens with the stem) and continue
(system per system_mode; user "Continue this text: " + stem). Thinking off where a vendor
switch exists. Seed per condition: sha256(model|arm|stem)[:8] % 2**31, sample i gets
seed + i. Engine class per lineage: vLLM on one A40, vLLM tp=4 on a 4xA40 pod, or the
batched HF runner (hf_batch.py) for the four vLLM 0.22.1 cannot host or corrupts.
"""
import argparse, hashlib, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, ROOT)
F11 = os.path.expanduser("~/malignment-data/f11_l2/f11_l2_full.parquet")
Y = os.path.join(ROOT, "experiments", "division_of_labour", "superego_stages", "prompts", "y_cells.jsonl")
PDIR = os.path.join(HERE, "prompts")
N = {"f11": 20, "y": 50}
NO_THINK = {"Qwen/Qwen3-8B", "openbmb/MiniCPM5-1B"}
#: vLLM 0.22.1 refuses (rwkv, recurrentgemma), needs tf>=5 + fla (Olmo-Hybrid), or writes
#: word salad in every cell (internlm2, institution_vs_individual README) -> batched HF
HF = {"RWKV/rwkv-4-7b-pile", "google/recurrentgemma-9b", "allenai/Olmo-Hybrid-7B", "internlm/internlm2-base-7b"}
#: one 48 GB A40 is not enough: 32B at fp16; Falcon-H1-7B OOMs at engine init (mamba state)
TP4 = {"allenai/Olmo-3-1125-32B", "tiiuae/Falcon-H1-7B-Base"}
#: falcon-7b needs trust_remote_code=False (vllm_generate.NO_REMOTE_CODE) and transformers 5
PIP = {"tiiuae/falcon-7b": "transformers==5.10.2", "tiiuae/falcon-7b-instruct": "transformers==5.10.2"}


def seed(model, arm, stem):
    return int(hashlib.sha256(("%s|%s|%s" % (model, arm, stem)).encode()).hexdigest()[:8], 16) % (2 ** 31)


def stems():
    import pandas as pd
    df = pd.read_parquet(F11, columns=["language", "prompt"])
    f = sorted(df[df.language == "en"].prompt.unique())
    assert len(f) == 100, len(f)
    y = [json.loads(l) for l in open(Y)]
    assert len(y) == 34
    return [("f11", "f11:%03d" % i, s) for i, s in enumerate(f)] + [("y", r["_key"], r["prompt"]) for r in y]


def conditions(model, arms, system_mode, S):
    out = []
    for arm in arms:
        for pset, key, stem in S:
            c = {"prompt": stem, "n": N[pset], "seed": seed(model, arm, stem), "_key": "%s|%s" % (key, arm), "_set": pset}
            if arm in ("prefill", "continue"):
                if system_mode == "empty":
                    c["system"] = ""
                if arm == "prefill":
                    c.update(prefill=True, user_msg="Hi.")
                else:
                    c.update(prompt="Continue this text: " + stem, chat=True)
                if model in NO_THINK:
                    c["template_kwargs"] = {"enable_thinking": False}
            out.append(c)
    return out


def safe(m):
    return m.replace("/", "__")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    from malignment import roster
    R = {r["model"]: r for r in json.load(open(os.path.join(ROOT, "roster", "models", "requirements.json")))["requirements"]}
    fe = json.load(open(os.path.join(ROOT, "roster", "models", "populations", "framed_empty.json")))["models"]
    assert len(fe) == 41 and set(r["model"] for r in fe) <= set(roster.population("endpoints"))
    S = stems()
    files, jobs = {}, {"vllm": [], "tp4": [], "hf": []}
    for r in fe:
        b, m = r["base"], r["model"]
        files[b] = conditions(b, ("base",), None, S)
        files[m] = conditions(m, ("raw", "prefill", "continue"), r["system_mode"], S)
        cls = "hf" if b in HF else "tp4" if b in TP4 else "vllm"
        size = sum((R.get(x, {}).get("params_b") or 0) for x in (b, m))
        jobs[cls].append((size, b, m))
    n_pass = sum(c["n"] for cs in files.values() for c in cs)
    print("checkpoints %d | conditions %d | passages %d" % (len(files), sum(len(c) for c in files.values()), n_pass))
    for k, v in jobs.items():
        print("  %-5s %2d lineages: %s" % (k, len(v), ", ".join(x[1].split("/")[-1] for x in v)))
    if not a.write:
        return
    os.makedirs(PDIR, exist_ok=True)
    for m, cs in files.items():
        with open(os.path.join(PDIR, safe(m) + ".jsonl"), "w") as fh:
            for c in cs:
                fh.write(json.dumps(c, ensure_ascii=False) + "\n")
    rel = os.path.relpath(PDIR, ROOT)

    def line(m):
        dt = (R.get(m, {}).get("compute_dtype") or "float16")
        return " ".join(x for x in (m, "%s/%s.jsonl" % (rel, safe(m)), dt, PIP.get(m, "")) if x)
    #: vLLM lineages dealt to 6 single-A40 pods, largest first onto the lightest pod
    NS = 6
    shards, load = [[] for _ in range(NS)], [0.0] * NS
    for size, b, m in sorted(jobs["vllm"], reverse=True):
        i = load.index(min(load))
        shards[i].append((b, m))
        load[i] += size
    #: a pip-spec model changes transformers for the rest of its pod: put it last
    for i, sh in enumerate(shards):
        sh.sort(key=lambda bm: bm[0] in PIP)
        open(os.path.join(HERE, "fleet", "a40_%d.txt" % i), "w").write("".join(line(b) + "\n" + line(m) + "\n" for b, m in sh))
    open(os.path.join(HERE, "fleet", "tp4.txt"), "w").write("".join(line(b) + "\n" + line(m) + "\n" for _, b, m in jobs["tp4"]))
    open(os.path.join(HERE, "fleet", "hf.txt"), "w").write("".join("%s %s\n" % (b, m) for _, b, m in jobs["hf"]))
    print("wrote %d prompt files, %d a40 shards (params_b load %s), tp4, hf" % (len(files), NS, [round(x) for x in load]))


if __name__ == "__main__":
    main()
