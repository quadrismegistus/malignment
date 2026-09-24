"""Code the 256-token regeneration with task.py (v2). -> ~/malignment-data/institution_vs_individual/coded_regen.jsonl

    python -u run_regen.py --plan
    python -u run_regen.py --run

POPULATION: every passage in the local generation stash (pulled from the RunPod
fleet, `fleet/`) whose prompt is one of the 36 in `prompts/design.json`,
generated with 256 new tokens by vLLM, in the arm's declared frame -- `raw` for
a lineage's base, `chat_sysdefault` for its endpoint (`roster.endpoints()`).
A passage in the wrong frame for its arm is counted and left out, never coded.
Speaker and counterparty come from the design, as in pass 1.
"""
import argparse, collections, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import task as T  # noqa: E402

DESIGN = json.load(open(os.path.join(HERE, "prompts", "design.json")))
BY_PROMPT = {d["prompt"]: (k, d) for k, d in DESIGN.items()}
OUT = os.path.expanduser("~/malignment-data/institution_vs_individual/coded_regen.jsonl")
FRAME = {"base": "raw", "aligned": "chat_sysdefault"}
#: WHICH RENDER COUNTS (2026-09-23). The first fleet passed rendered templates to
#: vLLM as strings: templated prompts got a second BOS (measured, Mistral-7B-
#: Instruct [1, 1, ...]) and 8 aligned models silently got RAW prompts. Every
#: aligned passage must therefore come from the fixed path (render='ids_v2').
#: Raw base prompts were tokenized correctly (one BOS) and are kept, EXCEPT the
#: three bases rerun for their own reasons: Falcon-H1 x2 at bfloat16 (the 7B
#: was 360/360 empty at float16) and Aquila2-7B at the roster's revision pin.
RERUN_BASES = {"tiiuae/Falcon-H1-7B-Base", "tiiuae/Falcon-H1-1.5B-Base", "BAAI/Aquila2-7B"}
#: 250,880 embedding rows against 250,680 tokenizer pieces: its raw passages are
#: multilingual gibberish (sampled ids with no piece). Excluded, not repaired.
EXCLUDE = {"openGPT-X/Teuken-7B-base-v0.6"}


#: THINKING OFF (thinking_off.md, 2026-09-24): these three aligned endpoints think by
#: default under their template; their chat cells are read ONLY from passages generated
#: with the vendor switch, and every other model only from passages with no switch.
NO_THINK = {"Qwen/Qwen3-8B", "HuggingFaceTB/SmolLM3-3B", "openbmb/MiniCPM5-1B"}
THINK_OFF = {"enable_thinking": False}


def population():
    from malignment import roster
    from malignment.checkpoint import Checkpoint
    eps, _ = roster.endpoints()
    rows, skipped = [], collections.Counter()
    for base, end in sorted(eps.items()):
        for arm, m in (("base", base), ("aligned", end)):
            seen = set()
            for st in Checkpoint(m).gen_stashes():
                for _, v in st.items():
                    hit = BY_PROMPT.get(v.get("prompt"))
                    if not hit or (v.get("decoder") or {}).get("max_new_tokens") != 256:
                        continue
                    if m in EXCLUDE:
                        skipped["excluded_model"] += 1
                        continue
                    if (arm == "aligned" or m in RERUN_BASES) and v.get("render") != "ids_v2":
                        skipped["superseded_render_%s" % arm] += 1
                        continue
                    if v.get("frame") != FRAME[arm]:
                        skipped["wrong_frame_%s" % arm] += 1
                        continue
                    want = THINK_OFF if (arm == "aligned" and m in NO_THINK) else None
                    if (v.get("template_kwargs") or None) != want:
                        skipped["thinking_switch_%s" % arm] += 1
                        continue
                    key = (hit[0], v.get("seed"))
                    if key in seen:
                        skipped["duplicate"] += 1
                        continue
                    seen.add(key)
                    d = hit[1]
                    rows.append({"lineage": base, "arm": arm, "model": m, "key": hit[0],
                                 "scenario": d["scenario"], "side": d["side"],
                                 "prompt": d["prompt"], "seed": v.get("seed"),
                                 "frame": v.get("frame"), "finish": v.get("finish"),
                                 "text": v.get("text") or ""})
    return rows, skipped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--workers", type=int, default=24)
    a = ap.parse_args()
    rows, skipped = population()
    per = collections.Counter((r["lineage"], r["arm"]) for r in rows)
    lin = {l for l, _ in per}
    full = [l for l in lin if per[(l, "base")] == 360 and per[(l, "aligned")] == 360]
    print("passages %d | lineages with any %d | complete (360+360) %d | skipped %s"
          % (len(rows), len(lin), len(full), dict(skipped)))
    for l in sorted(lin - set(full)):
        print("  incomplete: %s base %d aligned %d" % (l, per[(l, "base")], per[(l, "aligned")]))
    if not a.run:
        return
    prompts = [T.render(r["prompt"], r["text"], DESIGN[r["key"]]["speaker"],
                        DESIGN[r["key"]]["counterparty"]) for r in rows]
    errors = {}
    res = T.task().map(prompts, num_workers=a.workers, errors=errors)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as fh:
        for r, x in zip(rows, res):
            r = dict(r, coded=x.model_dump() if x else None)
            if x:
                r["spans_ok"], r["spans_total"], _ = T.check_spans(r["text"], x)
            fh.write(json.dumps(r) + "\n")
    print("coded %d of %d; failures %d -> %s" % (len(rows) - len(errors), len(rows), len(errors), OUT))


if __name__ == "__main__":
    main()
