"""Code the new rungs with Y's coder, pass A as Y. -> ~/malignment-data/superego_stages/coded.jsonl

    python -u code_ss.py --plan                 # population and draw, per model; spends nothing
    python -u code_ss.py --run --limit 100      # pilot: first 100 undone items (measure the cost)
    python -u code_ss.py --run                  # everything drawn and not yet coded

Registered in README.md (47f22c0a) before any new rung was generated; the
coder-drift gate PASSED 40/40 (`results/drift_gate.md`, b259be86), so NOTHING
Y coded is re-coded here. Coded here, for the first time:

    14 new rungs     generated on RunPod by `fleet/box_ss.sh`, read from the
                     local generation stash: raw frame, render ids_v2, vLLM,
                     t=1.0, top_p=1.0, 256 new tokens, n=50 per cell
    llama-7b, beaver generated in Y's own run (`malign-logits
                     data/raw/y_y-03/y__huggyllama__llama-7b.jsonl`) and left out
                     of Y's manifest only for a cross-scoring vocabulary block

PASS A AS Y (`malign-logits meta/M01_displacement/scripts/y_build_manifest.py`):
a passage is eligible if it ran the full 256 tokens; per cell, a seeded draw of
min(20, eligible). Seed 20260808, Y's. **The RNG stream is NOT Y's**: Y drew
from one stream over every cell of all 51 pairs in sorted order, which cannot be
reproduced for a model Y never had. Here each (model, cell) gets its own stream,
`Random("20260808|model|prompt_id|word")`, so a model's draw does not depend on
which other models exist -- which is also what lets a pilot be an exact subset
of the full run. Y balanced base against aligned within a cell; a ladder has no
such pair, so the cap is per model. A model is drawn only once all 34 x 50 of
its passages exist, because the eligible pool is not final before that.

ITEM AND ROW are Y's: `prepare(stem, word, continuation)`, the coder's own
`SuperegoV3Task`, `deepseek/deepseek-v4-flash`, then `roundtrip`,
`tag_field_mismatches` and `COMPOSITES` exactly as `y_run_manifest.py` writes
them, so the analysis reads Y's rows and these the same way. The id is a hash
of (model, prompt_id, word, seq_i), so resuming skips what is written.
"""
import argparse, collections, glob, hashlib, importlib.util, json, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.expanduser("~/malignment-data/superego_stages/coded.jsonl")
CELLS = os.path.join(HERE, "prompts", "y_cells.jsonl")
MODELS = os.path.join(HERE, "fleet", "models.txt")
LOGITS = os.path.expanduser("~/github/malign-logits")
CODER = os.path.join(LOGITS, "malign_logits", "tasks", "code_y_superego_v3.py")
Y_RAW = os.path.join(LOGITS, "data", "raw", "y_y-03", "y__huggyllama__llama-7b.jsonl")
Y_MODELS = ("huggyllama/llama-7b", "PKU-Alignment/beaver-7b-v1.0")
SEED, N_PER_CELL, FULL, N_GEN = 20260808, 20, 256, 50
os.environ.setdefault("LITMOD_DATA_DIR", os.path.expanduser("~/github/largeliterarymodels/data"))


def cells():
    """{prompt string: (prompt_id, word or None, stem)} for the 34 cells."""
    out = {}
    for line in open(CELLS):
        d = json.loads(line)
        pid, w = d["_key"].split("__")
        w = None if w == "UNDISTURBED" else w
        stem = d["prompt"][: -len(" " + w)] if w else d["prompt"]
        out[d["prompt"]] = (pid, w, stem)
    return out


def from_stash(model, C):
    """{(pid, word): {seq_i: (text, n_new_tokens)}} from the generation stash, Y's settings only."""
    from malignment.checkpoint import Checkpoint
    got = collections.defaultdict(dict)
    for st in Checkpoint(model).gen_stashes():
        for k, v in st.items():
            c = C.get(k.get("prompt"))
            d = k.get("decoder") or {}
            if (not c or k.get("frame") != "raw" or k.get("seed") != 42 or k.get("render") != "ids_v2" or v.get("engine") != "vllm"
                    or d.get("max_new_tokens") != FULL or d.get("temperature") != 1.0 or d.get("top_p") != 1.0):
                continue
            got[c[:2]].setdefault(k.get("sample_idx"), (v.get("text") or "", int(v.get("n_new_tokens") or 0)))
    return got


def from_y_raw(model):
    got = collections.defaultdict(dict)
    for line in open(Y_RAW):
        r = json.loads(line)
        if r.get("model") != model or "sequences" not in r:
            continue
        for i, s in enumerate(r["sequences"]):
            got[(r["prompt_id"], r.get("word"))][i] = (s.get("text") or "", len(s.get("tokens") or []))
    return got


def draw(model, pool, C):
    """Pass A rows for one model, or None if its generation is incomplete."""
    want = {c[:2] for c in C.values()}
    if set(pool) != want or any(len(pool[c]) != N_GEN for c in want):
        return None
    rows = []
    for pid, w in sorted(want, key=lambda x: (x[0], x[1] or "")):
        full = sorted(i for i, (_t, n) in pool[(pid, w)].items() if n >= FULL)
        take = min(N_PER_CELL, len(full))
        for i in sorted(random.Random("%d|%s|%s|%s" % (SEED, model, pid, w or "")).sample(full, take)):
            txt, n = pool[(pid, w)][i]
            rows.append({"sid": hashlib.sha256(json.dumps([model, pid, w, i]).encode()).hexdigest()[:16],
                         "model": model, "prompt_id": pid, "word": w, "seq_i": i, "pass": "A",
                         "n_tokens": n, "n_chars": len(txt),
                         "sha256": hashlib.sha256(txt.encode("utf-8")).hexdigest()[:16],
                         "source": "y_raw" if model in Y_MODELS else "stash", "_text": txt})
    return rows


def coder():
    spec = importlib.util.spec_from_file_location("code_y_superego_v3", CODER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=32)
    ap.add_argument("--model", default="deepseek/deepseek-v4-flash")
    ap.add_argument("--only", nargs="*", help="restrict to these checkpoints")
    a = ap.parse_args()
    C = cells()
    assert len(C) == 34, len(C)
    models = [l.split()[0] for l in open(MODELS) if l.strip() and not l.startswith("#")] + list(Y_MODELS)
    if a.only:
        models = [m for m in models if m in a.only]
    done = set()
    if os.path.exists(OUT):
        done = {json.loads(l)["sid"] for l in open(OUT)}
    todo, short = [], collections.Counter()
    print("%-45s %8s %8s %8s %8s" % ("model", "passages", "drawn", "short", "coded"))
    for m in models:
        pool = from_y_raw(m) if m in Y_MODELS else from_stash(m, C)
        n = sum(len(v) for v in pool.values())
        rows = draw(m, pool, C)
        if rows is None:
            print("%-45s %8d %8s %8s %8s   (incomplete: %d of %d)" % (m, n, "--", "--", "--", n, 34 * N_GEN))
            continue
        per = collections.Counter((r["prompt_id"], r["word"]) for r in rows)
        short[m] = sum(1 for c in {c[:2] for c in C.values()} if per[c] < N_PER_CELL)
        print("%-45s %8d %8d %8d %8d" % (m, n, len(rows), short[m], sum(r["sid"] in done for r in rows)))
        todo += [r for r in rows if r["sid"] not in done]
    print("to code: %d" % len(todo))
    if not a.run or not todo:
        return
    if a.limit:
        todo = todo[: a.limit]
    Y = coder()
    stems = {c[:2]: c[2] for c in C.values()}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    errors, n_ok = {}, 0
    task = Y.SuperegoV3Task()
    for start in range(0, len(todo), 2000):
        part = todo[start:start + 2000]
        items = [Y.prepare(stems[(r["prompt_id"], r["word"])], r["word"] or "", r["_text"]) for r in part]
        res = task.map(items, model=a.model, num_workers=a.workers, errors=errors)
        if len(res) != len(part):
            raise RuntimeError("map returned %d results for %d items" % (len(res), len(part)))
        with open(OUT, "a", encoding="utf-8") as fh:
            for r, out in zip(part, res):
                src = r["_text"]
                row = {k: v for k, v in r.items() if k != "_text"}
                row["coder"] = a.model
                row["parsed"] = out is not None
                if out is not None:
                    n_ok += 1
                    row.update(json.loads(out.model_dump_json()))
                    row.update(Y.roundtrip(src, out.tagged or ""))
                    row["tag_field_mismatches"] = out.tag_field_mismatches()
                    for name, fn in Y.COMPOSITES.items():
                        row[name] = bool(fn(row))
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        print("[%d-%d] written, parsed %d, errors %d" % (start, start + len(part), n_ok, len(errors)), flush=True)
    try:
        print("usage: %s" % task.usage.summary_line())
    except Exception:
        pass
    print("parsed %d of %d -> %s" % (n_ok, len(todo), OUT))


if __name__ == "__main__":
    main()
