"""Write $MALIGNMENT_DATA/template_arm/MANIFEST.md + manifest.json: every data file with rows and sha256.

    python manifest.py

The registration (../TEMPLATE_ARM.md) says what was intended; this says what exists, where,
and how it was made, so a reader who has only the data directory can find the design and a
reader who has only the repo can find the data (DATA.md points here).
"""
import glob, hashlib, json, os, time
DATA = os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data"))
D = os.path.join(DATA, "template_arm")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def rows(p):
    if p.endswith(".parquet"):
        import pyarrow.parquet as pq
        return pq.ParquetFile(p).metadata.num_rows
    if p.endswith(".jsonl"):
        return sum(1 for _ in open(p, "rb"))
    return None


FILES = {
    "passages.parquet": "every generated passage, one row each (collect.py over pods/): model, base (lineage), arm (base|raw|prefill|continue), set (f11|y), stem, prompt as sent, sample_idx, seed, text, n_words, finish, frame, engine, engine_version, dtype, render",
    "coding/selection.parquet": "the Figure 5 coding draw (select_for_coding.py): f11 stems, continue preamble stripped, >= 40 words, passC classifier over all passages, top 200 per (model, arm); 161 cells, 31,831 passages",
    "coding/codings.parquet": "one coding per selected id (harvest.py from the journals): narrative, mode, drift, degree, span, break, run. Coder claude-opus-5 pinned, passC rubric + break (coding/ta_code_*.js)",
    "coding/survival_generation.parquet": "per (model, arm): generated, >= 40 words",
    "coding/batches.json": "the 708 batch files the coder read, in order",
    "calib/truth.json": "the 400 calibration passages' August coder A/B narrative calls",
    "calib/opus55_codings.json": "Opus 5.5 on the calibration set (FAILS, CALIBRATION.md)",
    "calib/opus5_codings.json": "claude-opus-5 pinned on the calibration set (FAILS too)",
    "pods.tsv": "RunPod pod ids, names, shards (all terminated)",
    "pods_deleted.tsv": "termination record; rwkv pod terminated UNVERIFIED",
}


def main():
    out = {"_about": "TEMPLATE_ARM data custody. Design: malignment/experiments/passage_analysis/novel_arc/TEMPLATE_ARM.md. "
                     "Code: novel_arc/template_arm/. Written by template_arm/manifest.py.",
           "written_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "files": {}}
    for rel, what in FILES.items():
        p = os.path.join(D, rel)
        if os.path.exists(p):
            out["files"][rel] = dict(what=what, bytes=os.path.getsize(p), rows=rows(p), sha256=sha(p))
    js = sorted(glob.glob(os.path.join(D, "coding", "journals", "*.jsonl")))
    out["journals"] = {os.path.basename(p): dict(bytes=os.path.getsize(p), sha256=sha(p)) for p in js}
    stashes = sorted(glob.glob(os.path.join(D, "pods", "*", "*", "*", "*", "data.jsonl")))
    out["pod_stashes"] = {os.path.relpath(p, D): dict(rows=rows(p), sha256=sha(p)) for p in stashes}
    out["canonical_copy"] = ("80 model/producer stash dirs copied into $MALIGNMENT_DATA/generations/<model>/<producer>/ "
                             "(Checkpoint.gen_stashes() reads them); the 2 RWKV dirs are NOT copied: degenerate, lineage dropped.")
    out["decoder"] = ("vLLM 0.22.1: t=1.0 top_p=1.0 top_k=-1 max_tokens=256 min_tokens=0 penalties 0/0/1.0, fp16 "
                      "(bf16 for gemma-2, Falcon-H1, Zamba2, falcon-mamba), max_model_len 1024; HF class (hf_batch.py): "
                      "generate.DECODER, bf16. Seed per condition sha256(model|arm|stem)[:8] % 2**31, sample i = seed + i. "
                      "Every record carries its resolved decoder, seed, engine_version, dtype, render.")
    json.dump(out, open(os.path.join(D, "manifest.json"), "w"), indent=1)
    L = ["# TEMPLATE_ARM data", "", out["_about"], "", "Written %s by `template_arm/manifest.py`; hashes in `manifest.json`." % out["written_utc"], "",
         "| file | rows | what |", "|---|---|---|"]
    for rel, v in out["files"].items():
        L.append("| `%s` | %s | %s |" % (rel, v["rows"] if v["rows"] is not None else "", v["what"]))
    L += ["", "**Journals** (raw coder output, one line per agent): `coding/journals/`, %d files." % len(js),
          "", "**Pod stashes**: `pods/<pod>/<model>/<producer>/`, %d files, %d records." % (len(stashes), sum(v["rows"] for v in out["pod_stashes"].values())),
          "", out["canonical_copy"], "", "**Decoder**: " + out["decoder"],
          "", "**Lost / excluded**: RWKV lineage (rwkv-4-7b-pile, rwkv-raven-7b) degenerate under HF bf16 (88-90% loops), raven's templated arms never synced (pod unreachable), dropped (amendment 3). internlm2-chat's continue arm is coded separately (coding/selection_2.parquet, when written)."]
    open(os.path.join(D, "MANIFEST.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
