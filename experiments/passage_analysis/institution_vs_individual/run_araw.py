"""Code the aligned-raw cell with task.py (v2). -> ~/malignment-data/institution_vs_individual/coded_aligned_raw.jsonl

    python -u run_araw.py --plan
    python -u run_araw.py --run

Registered in `aligned_raw.md` (459f6c97) before any passage was generated; the
analysis is `aligned_raw.py` (dario, 0d460404).

POPULATION: for each of the 43 lineages with both arms in `coded_regen.jsonl`,
every passage of its ALIGNED endpoint in the local generation stash whose prompt
is one of the 36 in `prompts/design.json`, generated with 256 new tokens, in the
RAW frame, on the fixed render path (`render == "ids_v2"`). The pilot's
accidental raw passages (the first fleet's string render) are therefore NOT
coded here: they differ in `render`, and `aligned_raw.py` uses them only as a
determinism check.

ONE BOS, checked 2026-09-24 as the registration requires: the fixed path renders
a raw prompt with `add_special_tokens=True` (`vllm_generate`, templated -> False),
so a tokenizer that writes a BOS writes exactly one -- measured on
Llama-3.1-8B-Instruct (128000 once) and Mistral-7B-Instruct-v0.1 (1 once). Yi-1.5
writes none by its own config, as its base arm does.

RECORD SHAPE is `run_regen.py`'s, so `aligned_raw.py` reads both the same way:
lineage (the BASE id), arm ("aligned_raw"), model, key, scenario, side, prompt,
seed, frame, finish, text, coded, spans_ok, spans_total.
"""
import argparse, collections, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run_regen as RR  # noqa: E402

OUT = os.path.expanduser("~/malignment-data/institution_vs_individual/coded_aligned_raw.jsonl")
T, DESIGN, BY_PROMPT = RR.T, RR.DESIGN, RR.BY_PROMPT


def lineages():
    """{base: aligned endpoint} for the 43 lineages with both arms coded in the main run."""
    from malignment import roster
    arms = collections.defaultdict(set)
    for line in open(RR.OUT):
        r = json.loads(line)
        arms[r["lineage"]].add(r["arm"])
    eps, _ = roster.endpoints()
    return {b: eps[b] for b, a in sorted(arms.items()) if a == {"base", "aligned"}}


def population():
    from malignment.checkpoint import Checkpoint
    rows, skipped = [], collections.Counter()
    for base, m in lineages().items():
        seen = set()
        for st in Checkpoint(m).gen_stashes():
            for _, v in st.items():
                hit = BY_PROMPT.get(v.get("prompt"))
                if not hit or (v.get("decoder") or {}).get("max_new_tokens") != 256:
                    continue
                if v.get("frame") != "raw":
                    continue
                if v.get("render") != "ids_v2":
                    skipped["pilot_or_superseded_render"] += 1
                    continue
                key = (hit[0], v.get("seed"))
                if key in seen:
                    skipped["duplicate"] += 1
                    continue
                seen.add(key)
                d = hit[1]
                rows.append({"lineage": base, "arm": "aligned_raw", "model": m, "key": hit[0],
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
    L = lineages()
    rows, skipped = population()
    per = collections.Counter(r["lineage"] for r in rows)
    full = [l for l in L if per[l] == 360]
    print("lineages %d | passages %d | complete (360) %d | skipped %s"
          % (len(L), len(rows), len(full), dict(skipped)))
    for l in sorted(set(L) - set(full)):
        print("  incomplete: %s (%s) %d" % (l, L[l], per[l]))
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
