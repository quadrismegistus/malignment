"""Redraw and recode the F21-task sample's cells for the three thinking models. (thinking_off.md)

    python -u f21_nothink.py --plan
    python -u f21_nothink.py --run      then: python -u f21_task_sample.py  (analysis only)

RH, 2026-09-24. The F21-task sample (8d2103b9) drew 164 aligned passages from Qwen3-8B,
SmolLM3-3B and MiniCPM5-1B before their chat cells were regenerated with thinking off;
all 164 were reasoning traces. This replaces ONLY those three lineages' aligned cells.

SAME RULE, NOT THE SAME STREAM. f21_task_sample.py draws every cell from ONE seeded
stream in sorted order, so re-running it whole would shift the draw of every later
cell and bring uncoded passages in. Here each of the six cells (3 models x 2 sides) is
drawn with the same size rule -- all if <= 30, else a seeded sample of 30 -- from its own
stream, Random("20260924|lineage|arm|side"), over the passages that pass
analyse_regen.keep in the CURRENT coded_regen.jsonl (thinking-off texts). Every other
row of f21task_regen.jsonl is untouched; the replaced rows go to
f21task_regen.pre_nothink.jsonl. Coder and input convention unchanged.
"""
import collections, json, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import analyse_regen as A  # noqa: E402
import f21_task_sample as S  # noqa: E402
import run_regen as RR  # noqa: E402

ARCHIVE = S.OUT_R.replace(".jsonl", ".pre_nothink.jsonl")


def draw():
    rows = [json.loads(l) for l in open(A.SRC)]
    rows = [r for r in rows if r["arm"] == "aligned" and r["model"] in RR.NO_THINK and r.get("coded") and A.keep(r["coded"])]
    cells = collections.defaultdict(list)
    for r in rows:
        cells[(r["lineage"], r["arm"], r["side"])].append(r)
    out = []
    for k in sorted(cells):
        c = sorted(cells[k], key=lambda r: (r["key"], r["seed"]))
        out += c if len(c) <= S.PER_CELL else random.Random("20260924|%s|%s|%s" % k).sample(c, S.PER_CELL)
    return out, {k: len(v) for k, v in cells.items()}


def main():
    new, pool = draw()
    print("kept passages per cell:", pool)
    print("drawn:", collections.Counter(r["model"] for r in new), "| total", len(new),
          "| with think marker", sum("<think>" in r["text"] or "</think>" in r["text"] for r in new))
    if "--run" not in sys.argv:
        return
    tmp = S.OUT_R + ".nothink_tmp"
    S.code(new, lambda r: False, tmp)
    coded = [json.loads(l) for l in open(tmp)]
    old = [json.loads(l) for l in open(S.OUT_R)]
    out_old = [r for r in old if r["arm"] == "aligned" and r["model"] in RR.NO_THINK]
    keep = [r for r in old if not (r["arm"] == "aligned" and r["model"] in RR.NO_THINK)]
    with open(ARCHIVE, "w") as fh:
        for r in out_old:
            fh.write(json.dumps(r) + "\n")
    with open(S.OUT_R, "w") as fh:
        for r in keep + [dict(r, thinking_off=True) for r in coded]:
            fh.write(json.dumps(r) + "\n")
    os.remove(tmp)
    print("archived %d; wrote %d kept + %d new -> %s" % (len(out_old), len(keep), len(coded), S.OUT_R))


if __name__ == "__main__":
    main()
