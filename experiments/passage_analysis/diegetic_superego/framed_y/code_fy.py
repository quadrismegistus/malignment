"""Code framed-Y passages with Y's coder, both length strata. -> ~/malignment-data/framed_y/{coded,pools}.jsonl

    python -u code_fy.py --plan                  # pools and draws per model; spends nothing
    python -u code_fy.py --run [--limit N] [--only M ...] [--workers 32]

Registered in README.md (2904c6fb) before any framed passage was generated.

WHAT IS CODED, per model in `population.json`:

    prefill, continue   the two framed conditions, read from the generation stash:
                        vLLM, render ids_v2, t=1.0, top_p=1.0, 256 new tokens,
                        seed 42+sample_idx, the model's declared system mode
                        (sysempty / sysdefault), prefill user turn "Hi."
    raw, stratum B      ONLY for models whose raw pass B no store holds: the
                        superego_stages rungs and beaver (Y's own aligned models
                        have a pass-B census in Y's store). Their raw pass A is
                        already coded in superego_stages.

STRATA, as Y's manifest: A = n_new_tokens >= 256, B = 11..255, and <= 10 counted,
not coded. Per (model, frame, cell) a seeded draw of min(20, eligible) from EACH
stratum, one stream `Random("20260808|model|frame|prompt_id|word")`, A then B.
**Pass B is sampled, not a census** (declared departure from Y). Every pool size
goes to `pools.jsonl`, so the analysis can weight A and B to an all-length rate.

A model is drawn only once all of its framed passages exist (68 conditions x 50),
because the eligible pools are not final before that. The coded item is Y's:
`prepare(Y prompt, word, continuation)` -- for `continue` the continuation is the
assistant's reply to "Continue this text: <Y prompt>", coded against the Y prompt,
and the coder never sees the frame.
"""
import argparse, collections, hashlib, importlib.util, json, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
OUTDIR = os.path.expanduser("~/malignment-data/framed_y")
OUT, POOLS = os.path.join(OUTDIR, "coded.jsonl"), os.path.join(OUTDIR, "pools.jsonl")
CELLS = os.path.join(REPO, "experiments", "division_of_labour", "superego_stages", "prompts", "y_cells.jsonl")
SS_MODELS = os.path.join(REPO, "experiments", "division_of_labour", "superego_stages", "fleet", "models.txt")
LOGITS = os.path.expanduser("~/github/malign-logits")
CODER = os.path.join(LOGITS, "malign_logits", "tasks", "code_y_superego_v3.py")
Y_RAW = os.path.join(LOGITS, "data", "raw", "y_y-03", "y__huggyllama__llama-7b.jsonl")
SEED, N, FULL, MIN_B, N_GEN = 20260808, 20, 256, 11, 50
CONT = "Continue this text: "
os.environ.setdefault("LITMOD_DATA_DIR", os.path.expanduser("~/github/largeliterarymodels/data"))


def cells():
    out = {}
    for line in open(CELLS):
        d = json.loads(line)
        pid, w = d["_key"].split("__")
        w = None if w == "UNDISTURBED" else w
        out[d["prompt"]] = (pid, w, d["prompt"][: -len(" " + w)] if w else d["prompt"])
    return out


def framed_pool(model, mode, C):
    """{(frame, pid, word): {i: (text, n_new_tokens, finish)}} for the model's declared system mode."""
    from malignment.checkpoint import Checkpoint
    want = {"prefill_sys" + mode: "prefill", "chat_sys" + mode: "continue"}
    got = collections.defaultdict(dict)
    for st in Checkpoint(model).gen_stashes():
        for k, v in st.items():
            fr = want.get(k.get("frame"))
            if not fr or k.get("render") != "ids_v2" or v.get("engine") != "vllm":
                continue
            d = k.get("decoder") or {}
            if d.get("max_new_tokens") != FULL or d.get("temperature") != 1.0 or d.get("top_p") != 1.0:
                continue
            if k.get("seed") != 42 + (k.get("sample_idx") or 0):
                continue
            p = k.get("prompt") or ""
            if fr == "prefill":
                if k.get("user_msg") != "Hi.":
                    continue
                c = C.get(p)
            else:
                c = C.get(p[len(CONT):]) if p.startswith(CONT) else None
            if c:
                got[(fr,) + c[:2]].setdefault(k.get("sample_idx"), (v.get("text") or "", int(v.get("n_new_tokens") or 0), v.get("finish")))
    return got


def raw_pool(model, C):
    """Raw passages for the pass-B baseline: the stash (superego_stages rungs) or Y's raw file (beaver)."""
    got = collections.defaultdict(dict)
    if model == "PKU-Alignment/beaver-7b-v1.0":
        for line in open(Y_RAW):
            r = json.loads(line)
            if r.get("model") == model and "sequences" in r:
                for i, s in enumerate(r["sequences"]):
                    got[("raw", r["prompt_id"], r.get("word"))][i] = (s.get("text") or "", len(s.get("tokens") or []), None)
        return got
    from malignment.checkpoint import Checkpoint
    for st in Checkpoint(model).gen_stashes():
        for k, v in st.items():
            c = C.get(k.get("prompt"))
            d = k.get("decoder") or {}
            if (c and k.get("frame") == "raw" and k.get("render") == "ids_v2" and v.get("engine") == "vllm"
                    and d.get("max_new_tokens") == FULL and d.get("temperature") == 1.0 and d.get("top_p") == 1.0
                    and k.get("seed") == 42 + (k.get("sample_idx") or 0)):
                got[("raw",) + c[:2]].setdefault(k.get("sample_idx"), (v.get("text") or "", int(v.get("n_new_tokens") or 0), v.get("finish")))
    return got


def draw(model, pool, keys, strata):
    """Rows and pool sizes, or None if any condition lacks its 50 passages."""
    if any(len(pool.get(k, {})) != N_GEN for k in keys):
        return None
    rows, pools = [], []
    for fr, pid, w in sorted(keys, key=lambda x: (x[0], x[1], x[2] or "")):
        P = pool[(fr, pid, w)]
        A = sorted(i for i, t in P.items() if t[1] >= FULL)
        B = sorted(i for i, t in P.items() if MIN_B <= t[1] < FULL)
        pools.append({"model": model, "frame": fr, "prompt_id": pid, "word": w,
                      "n_A": len(A), "n_B": len(B), "n_short": N_GEN - len(A) - len(B)})
        rng = random.Random("%d|%s|%s|%s|%s" % (SEED, model, fr, pid, w or ""))
        for stratum, elig in (("A", A), ("B", B)):
            pick = sorted(rng.sample(elig, min(N, len(elig))))
            if stratum not in strata:
                continue
            for i in pick:
                txt, n, fin = P[i]
                rows.append({"sid": hashlib.sha256(json.dumps([model, fr, pid, w, i]).encode()).hexdigest()[:16],
                             "model": model, "frame": fr, "prompt_id": pid, "word": w, "seq_i": i, "pass": stratum,
                             "n_tokens": n, "finish": fin, "n_chars": len(txt),
                             "sha256": hashlib.sha256(txt.encode("utf-8")).hexdigest()[:16], "_text": txt})
    return rows, pools


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
    ap.add_argument("--only", nargs="*")
    a = ap.parse_args()
    C = cells()
    assert len(C) == 34, len(C)
    pop = json.load(open(os.path.join(HERE, "population.json")))["models"]
    ss = {l.split()[0] for l in open(SS_MODELS) if l.strip() and not l.startswith("#")}
    need_raw_b = ss | {"PKU-Alignment/beaver-7b-v1.0"}
    if a.only:
        pop = [r for r in pop if r["model"] in a.only]
    done = {json.loads(l)["sid"] for l in open(OUT)} if os.path.exists(OUT) else set()
    old_pools = {}
    if os.path.exists(POOLS):
        for l in open(POOLS):
            p = json.loads(l)
            old_pools[(p["model"], p["frame"], p["prompt_id"], p["word"])] = p
    todo, new_pools = [], []
    print("%-44s %-8s %6s %6s %6s %6s %6s" % ("model", "mode", "cond", "A", "B", "short", "todo"))
    ckeys = sorted({c[:2] for c in C.values()}, key=lambda x: (x[0], x[1] or ""))
    for r in pop:
        m, mode = r["model"], r["system_mode"]
        fp = framed_pool(m, mode, C)
        got = draw(m, fp, [(f, p, w) for f in ("prefill", "continue") for p, w in ckeys], ("A", "B"))
        if got is None:
            print("%-44s %-8s %6d  (incomplete: %d of 68 conditions have 50)" % (m, mode, len(fp), sum(len(v) == N_GEN for v in fp.values())))
            continue
        rows, pools = got
        if m in need_raw_b:
            rg = draw(m, raw_pool(m, C), [("raw", p, w) for p, w in ckeys], ("B",))
            if rg is None:
                print("%-44s raw pool incomplete -- REFUSED for this model" % m)
                continue
            rows += rg[0]
            pools += rg[1]
        new_pools += pools
        t = [x for x in rows if x["sid"] not in done]
        fr = collections.Counter(p["frame"] for p in pools)
        print("%-44s %-8s %6d %6d %6d %6d %6d" % (m, mode, sum(fr.values()), sum(p["n_A"] for p in pools if p["frame"] != "raw"),
                                                  sum(p["n_B"] for p in pools if p["frame"] != "raw"),
                                                  sum(p["n_short"] for p in pools if p["frame"] != "raw"), len(t)))
        todo += t
    print("to code: %d" % len(todo))
    if not a.run:
        return
    os.makedirs(OUTDIR, exist_ok=True)
    for p in new_pools:
        old_pools[(p["model"], p["frame"], p["prompt_id"], p["word"])] = p
    with open(POOLS, "w") as fh:
        for p in old_pools.values():
            fh.write(json.dumps(p) + "\n")
    if not todo:
        return
    if a.limit:
        todo = todo[: a.limit]
    Y = coder()
    stems = {c[:2]: c[2] for c in C.values()}
    task, errors, n_ok = Y.SuperegoV3Task(), {}, 0
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
                row["coder"], row["parsed"] = a.model, out is not None
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
