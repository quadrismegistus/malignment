"""Split the human pool into per-agent batch files, and collate the results back.

    python .../split_pool.py split                     # -> batches/batch-NNN.jsonl
    python .../split_pool.py collate                   # cleaned/ -> human_passages.jsonl

The normalisation pass runs one agent per batch file. Batching through FILES
rather than through the workflow script's arguments matters for three reasons:

  * the workflow script cannot touch the filesystem, so passing 3,600 passages
    through it would put every one of them through the orchestrator's context;
  * an agent that writes `cleaned/batch-NNN.jsonl` makes the run RESUMABLE -- a
    re-run skips batches whose output already exists, so a failure costs one
    batch and not the pass;
  * the spec lives in one file that every agent reads, so revising it cannot
    leave some agents on an older version.

BATCH is 15 because the failure this pass is most likely to have is an agent
losing the correspondence between input and output items, and that risk grows
with batch length while the per-agent overhead falls. 15 keeps each call near
3,200 words in and out.
"""

import argparse, collections, json, os, sys

DATA = os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data"))
ROOT = os.path.join(DATA, "jakobson_space")
POOL = os.path.join(ROOT, "human_pool_raw.jsonl")
BATCHES = os.path.join(ROOT, "batches")
CLEANED = os.path.join(ROOT, "cleaned")
FINAL = os.path.join(ROOT, "human_passages.jsonl")
BATCH = 15


def split(a):
    rows = [json.loads(l) for l in open(POOL)]
    #: SHUFFLE, and it is not cosmetic. The pool is built corpus by corpus, so
    #: unshuffled batches are homogeneous and an agent handling 15 dreams in a row
    #: can settle into a dream-specific policy -- exactly the per-corpus variation
    #: in treatment this pass exists to remove. Mixed batches make the cleaner
    #: face all six registers at once and treat them by one rule.
    import random
    random.Random(a.seed).shuffle(rows)
    os.makedirs(BATCHES, exist_ok=True)
    n = 0
    for i in range(0, len(rows), a.batch):
        chunk = rows[i:i + a.batch]
        p = os.path.join(BATCHES, "batch-%03d.jsonl" % n)
        with open(p, "w") as fh:
            for r in chunk:
                #: the agent sees ONLY id and text. Provenance stays here and is
                #: rejoined at collate, so no metadata can leak into the prompt
                #: and bias the cleaning of a passage by its corpus.
                fh.write(json.dumps(dict(id=r["id"], text=r["text"])) + "\n")
        n += 1
    print("%d passages -> %d batches of %d in %s" % (len(rows), n, a.batch, BATCHES))
    print("cleaned output goes to %s" % CLEANED)


def collate(a):
    src = {r["id"]: r for r in (json.loads(l) for l in open(POOL))}
    got, bad, seen = [], collections.Counter(), set()
    files = sorted(f for f in os.listdir(CLEANED) if f.endswith(".jsonl")) \
        if os.path.isdir(CLEANED) else []
    for f in files:
        for line in open(os.path.join(CLEANED, f)):
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                bad["unparseable_line"] += 1
                continue
            i = d.get("id")
            if i not in src:
                bad["unknown_id"] += 1
                continue
            if i in seen:
                bad["duplicate_id"] += 1
                continue
            seen.add(i)
            out = dict(src[i])
            out["text_raw"] = out.pop("text")
            out["text"] = " ".join((d.get("text") or "").split())
            out["changes"] = d.get("changes") or []
            out["batch"] = f
            got.append(out)

    missing = [i for i in src if i not in seen]
    with open(FINAL, "w") as fh:
        for r in got:
            fh.write(json.dumps(r) + "\n")
    print("batches read      : %d" % len(files))
    print("passages collated : %d of %d" % (len(got), len(src)))
    if bad:
        print("rejected          : %s" % dict(bad))
    if missing:
        print("MISSING           : %d ids (re-run their batches)" % len(missing))
        by = collections.Counter(src[i]["corpus"] for i in missing)
        print("                    %s" % dict(by))
    print("-> %s" % FINAL)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["split", "collate"])
    ap.add_argument("--batch", type=int, default=BATCH)
    ap.add_argument("--seed", type=int, default=20260820)
    a = ap.parse_args(argv)
    (split if a.cmd == "split" else collate)(a)


if __name__ == "__main__":
    main()
