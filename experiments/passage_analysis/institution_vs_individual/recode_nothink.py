"""Recode ONLY the three thinking models' aligned rows, after their thinking-off regeneration. (thinking_off.md)

    python -u recode_nothink.py --plan
    python -u recode_nothink.py --run

Reads `run_regen.population()` (which now takes thinking-off passages for these three),
codes their 1,080 aligned rows with task.py v2 exactly as run_regen does, archives the
rows they replace to coded_regen.pre_nothink.jsonl, and rewrites coded_regen.jsonl with
every other row untouched and in its original order.
"""
import argparse, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run_regen as RR  # noqa: E402

ARCHIVE = RR.OUT.replace(".jsonl", ".pre_nothink.jsonl")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--workers", type=int, default=24)
    a = ap.parse_args()
    rows, skipped = RR.population()
    new = [r for r in rows if r["arm"] == "aligned" and r["model"] in RR.NO_THINK]
    per = {m: sum(r["model"] == m for r in new) for m in sorted(RR.NO_THINK)}
    think = sum("<think>" in r["text"] or "</think>" in r["text"] for r in new)
    print("thinking-off aligned rows: %s | with a think marker: %d" % (per, think))
    if any(n != 360 for n in per.values()):
        sys.exit("REFUSED: every model needs 360 thinking-off passages before recoding")
    if not a.run:
        return
    T = RR.T
    prompts = [T.render(r["prompt"], r["text"], RR.DESIGN[r["key"]]["speaker"], RR.DESIGN[r["key"]]["counterparty"]) for r in new]
    errors = {}
    res = T.task().map(prompts, num_workers=a.workers, errors=errors)
    if len(res) != len(new):
        raise RuntimeError("map returned %d for %d" % (len(res), len(new)))
    coded = []
    for r, x in zip(new, res):
        r = dict(r, coded=x.model_dump() if x else None, thinking_off=True)
        if x:
            r["spans_ok"], r["spans_total"], _ = T.check_spans(r["text"], x)
        coded.append(r)
    old = [json.loads(l) for l in open(RR.OUT)]
    out_old = [r for r in old if r["arm"] == "aligned" and r["model"] in RR.NO_THINK]
    keep = [r for r in old if not (r["arm"] == "aligned" and r["model"] in RR.NO_THINK)]
    with open(ARCHIVE, "w") as fh:
        for r in out_old:
            fh.write(json.dumps(r) + "\n")
    with open(RR.OUT, "w") as fh:
        for r in keep + coded:
            fh.write(json.dumps(r) + "\n")
    print("archived %d old rows -> %s; wrote %d kept + %d recoded (%d failures) -> %s"
          % (len(out_old), ARCHIVE, len(keep), len(coded), len(errors), RR.OUT))


if __name__ == "__main__":
    main()
