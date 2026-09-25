"""Collect TEMPLATE_ARM codings from the Workflow runs' journals -> codings.parquet.

    python harvest.py wf_... wf_...

The ta_code_*.js scripts inherit passC's final `return`, which carries a `_missing_B`
list (every id, since there is one coder) and fails the workflow boundary's 4,096-element
cap AFTER every agent has finished (chunk 1, 2026-09-25). The agents' results are in
each run's journal.jsonl, one line per agent; this reads them there, keeps only ids the
selection asked for, and reports any requested id that never came back.
"""
import json, os, re, sys
DATA = os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data"))
WF = os.path.expanduser("~/.claude/projects/-Users-rj416-github-malign-logits/412328a9-b178-4724-9c75-eca7f1f0e80b/subagents/workflows")
OUT = os.path.join(DATA, "template_arm", "coding", "codings.parquet")


def main(runs):
    import pyarrow as pa, pyarrow.parquet as pq
    batches = []
    for f in sorted(os.listdir(os.path.join(DATA, "template_arm", "coding"))):
        if re.fullmatch(r"batches(_\d+)?\.json", f):                #: batches.json + batches_2.json ..., not *_fillers
            batches += json.load(open(os.path.join(DATA, "template_arm", "coding", f)))
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
    #: NEVER overwrite a coding from another run. A second coding of an id (the straggler
    #: pass's fillers) is a RETEST and goes to its own file.
    retest = {i: c for i, c in got.items() if i in old and old[i].get("run") != c["run"]}
    for i, c in got.items():
        if i not in retest:
            old[i] = c
    pq.write_table(pa.Table.from_pylist(list(old.values())), OUT, compression="zstd")
    if retest:
        RT = OUT.replace("codings.parquet", "codings_retest.parquet")
        prev = {(r["id"], r["run"]): r for r in pq.read_table(RT).to_pylist()} if os.path.exists(RT) else {}
        prev.update({(i, c["run"]): c for i, c in retest.items()})
        pq.write_table(pa.Table.from_pylist(list(prev.values())), RT, compression="zstd")
        print("retest codings (not overwritten): %d -> %s" % (len(retest), RT))
    per_batch_missing = [b["file"] for b in batches if any(i not in old for i in b["ids"])]
    print("this harvest %d | total %d of %d asked | stray %d | batches with a missing id: %d"
          % (len(got), len(old), len(asked), stray, len(per_batch_missing)))


if __name__ == "__main__":
    main(sys.argv[1:])
