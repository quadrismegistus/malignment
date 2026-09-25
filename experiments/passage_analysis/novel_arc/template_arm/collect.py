"""All TEMPLATE_ARM passages from the synced pod stashes -> one parquet.

    python collect.py      # -> $MALIGNMENT_DATA/template_arm/passages.parquet

One row per passage: model, base (lineage), arm (base / raw / prefill / continue),
set (f11 / y), stem (the bare prompt, without "Continue this text: "), prompt (as sent),
sample_idx, seed, text, n_words, finish, frame, engine, engine_version, dtype, render.
Deduplicated on the stash key, so a pod synced twice counts once.
"""
import glob, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
DATA = os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data"))
PODS = os.path.join(DATA, "template_arm", "pods")
OUT = os.path.join(DATA, "template_arm", "passages.parquet")
Y = os.path.join(ROOT, "experiments", "division_of_labour", "superego_stages", "prompts", "y_cells.jsonl")
CONT = "Continue this text: "


def main():
    import pyarrow as pa, pyarrow.parquet as pq
    fe = json.load(open(os.path.join(ROOT, "roster", "models", "populations", "framed_empty.json")))["models"]
    lin = {}
    for r in fe:
        lin[r["base"]] = r["base"]; lin[r["model"]] = r["base"]
    ystems = {json.loads(l)["prompt"] for l in open(Y)}
    rows, seen = [], set()
    for f in sorted(glob.glob(os.path.join(PODS, "*", "*", "*", "*", "data.jsonl"))):
        for l in open(f):
            r = json.loads(l); k = r["__key__"]
            kid = json.dumps(k, sort_keys=True)
            if kid in seen:
                continue
            seen.add(kid)
            m = k["model"]; fr = k["frame"]
            if m not in lin:
                continue
            base = lin[m]
            arm = "base" if m == base else ("prefill" if fr.startswith("prefill") else "continue" if fr.startswith("chat") else "raw")
            stem = k["prompt"][len(CONT):] if k["prompt"].startswith(CONT) else k["prompt"]
            t = r.get("text") or ""
            rows.append(dict(model=m, base=base, arm=arm, set=("y" if stem in ystems else "f11"), stem=stem,
                             prompt=k["prompt"], sample_idx=int(k["sample_idx"]), seed=int(k["seed"]), text=t,
                             n_words=len(t.split()), finish=r.get("finish"), frame=fr, engine=r.get("engine"),
                             engine_version=str(r.get("engine_version")), dtype=str(r.get("dtype")), render=str(k.get("render"))))
    t = pa.Table.from_pylist(rows)
    pq.write_table(t, OUT, compression="zstd")
    import collections
    c = collections.Counter((r["arm"], r["set"]) for r in rows)
    print("%d passages, %d models -> %s" % (len(rows), len({r["model"] for r in rows}), OUT))
    for k in sorted(c):
        print("  %-9s %-4s %7d" % (k[0], k[1], c[k]))


if __name__ == "__main__":
    main()
