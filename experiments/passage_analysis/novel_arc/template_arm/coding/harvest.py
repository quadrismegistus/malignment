"""Collect TEMPLATE_ARM codings from the Workflow runs' journals -> codings.parquet.

    python harvest.py wf_... wf_...

The ta_code_*.js scripts inherit passC's final `return`, which carries a `_missing_B`
list (every id, since there is one coder) and fails the workflow boundary's 4,096-element
cap AFTER every agent has finished (chunk 1, 2026-09-25). The agents' results are in
each run's journal.jsonl, one line per agent; this reads them there, keeps only ids the
selection asked for, and reports any requested id that never came back.
"""
import json, os, sys
DATA = os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data"))
WF = os.path.expanduser("~/.claude/projects/-Users-rj416-github-malign-logits/412328a9-b178-4724-9c75-eca7f1f0e80b/subagents/workflows")
OUT = os.path.join(DATA, "template_arm", "coding", "codings.parquet")


def main(runs):
    import pyarrow as pa, pyarrow.parquet as pq
    batches = json.load(open(os.path.join(DATA, "template_arm", "coding", "batches.json")))
    asked = {i for b in batches for i in b["ids"]}
    got, stray = {}, 0
    for run in runs:
        for l in open(os.path.join(WF, run, "journal.jsonl")):
            r = json.loads(l)
            if r.get("type") != "result":
                continue
            for c in ((r.get("result") or {}).get("codings") or []):
                if c.get("id") not in asked:
                    stray += 1; continue
                got[c["id"]] = dict(c, run=run)
    old = {}
    if os.path.exists(OUT):
        old = {r["id"]: r for r in pq.read_table(OUT).to_pylist()}
    old.update(got)
    pq.write_table(pa.Table.from_pylist(list(old.values())), OUT, compression="zstd")
    per_batch_missing = [b["file"] for b in batches if any(i not in old for i in b["ids"])]
    print("this harvest %d | total %d of %d asked | stray %d | batches with a missing id: %d"
          % (len(got), len(old), len(asked), stray, len(per_batch_missing)))


if __name__ == "__main__":
    main(sys.argv[1:])
