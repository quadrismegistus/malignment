"""Assemble everything to be scored by the reference model into one shuffled JSONL.

    python .../build_ref_pool.py
    python .../ref_surprisal.py --input $MALIGNMENT_DATA/ref_pool/ref_pool.jsonl \
        --out $MALIGNMENT_DATA/ref_pool/deepseek --device mps

Three populations go in one file with a `pool` field, and a manifest beside it
records what each is and where it came from.

    model_narrative   coded-narrative model passages -- 58 models, both arms,
                      narrative_A True per the blind coding
    human_anchor      the six human corpora at 193 words
    wrapper           six aligned models under `:continue` against their raw
                      generations, for the chat-wrapper confound

## ONE FILE, SHUFFLED, AND BOTH PARTS MATTER

**Shuffled**, because a run stopped early must be a SAMPLE and not a prefix. An
earlier normalisation run in this folder was killed at 14% and had processed 496
dreams and 14 of everything else -- enough to look like progress and useless for
judging whether the pass worked on academic prose. The shuffle is seeded, so the
order is reproducible.

**One file**, because the three populations must be scored by one model on one
device in one pass. Scoring them separately invites exactly the defect this
campaign has paid for repeatedly: a comparison across groups measured by
instruments that differ in some way nobody wrote down.

## WHAT EACH ROW CARRIES

`id`, `pool`, `text`, plus provenance -- `model`/`arm` for model passages,
`corpus` for human ones, `mode`/`prompt` for the wrapper pool. The scorer copies
`id`, `corpus` and `model` into its output, and everything else rejoins here by
`id`.

## LENGTHS DIFFER BY POOL AND THAT IS NOT A DEFECT

    model_narrative   ~1,100 bytes    256-token generations
    human_anchor      970-1,406       193 words, varying by genre
    wrapper           ~450            the archive's generations are ~80 words

They are not compared raw. The `.f32`/`.i32` sidecars make any byte prefix a
partial sum, so cross-pool comparisons are taken at a common K -- which is why
the wrapper pool's short passages are worth scoring at all rather than being an
apples-to-oranges liability.
"""

import argparse, csv, hashlib, json, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data"))
OUT = os.path.join(DATA, "ref_pool", "ref_pool.jsonl")
CODED = os.path.join(os.path.dirname(HERE), "drift_geometry", "results",
                     "drift_by_passage.csv")


def model_narrative():
    import pyarrow.parquet as pq
    t = pq.read_table(os.path.join(DATA, "jakobson_space", "passages_std.parquet"),
                      columns=["model", "prompt", "sample_idx", "arm", "text",
                               "n_bytes", "corpus", "has_both_axes", "script"])
    d = t.to_pydict()
    idx = {(d["model"][i], d["prompt"][i], str(d["sample_idx"][i])): i
           for i in range(t.num_rows)}
    out, unjoined = [], 0
    for r in csv.DictReader(open(CODED)):
        if r["narrative_A"] != "True":
            continue
        i = idx.get((r["model"], r["prompt"], str(r["sample_idx"])))
        if i is None:
            unjoined += 1
            continue
        if not d["has_both_axes"][i]:
            continue
        out.append(dict(pool="model_narrative", model=d["model"][i], arm=d["arm"][i],
                        corpus=d["corpus"][i], prompt=d["prompt"][i],
                        sample_idx=str(d["sample_idx"][i]),
                        drift_A=r["drift_A"], degree_A=r["degree_A"], mode_A=r["mode_A"],
                        text=d["text"][i]))
    return out, {"unjoined_coded_rows": unjoined}


def human_anchor():
    p = os.path.join(DATA, "jakobson_space", "human_anchor.jsonl")
    out = []
    for line in open(p):
        r = json.loads(line)
        out.append(dict(pool="human_anchor", corpus=r["corpus"], anchor_id=r["id"],
                        n_words=r.get("n_words"), text=r["text"]))
    return out, {}


def wrapper():
    p = os.path.join(DATA, "wrapper_confound", "wrapper_pool.jsonl")
    if not os.path.exists(p):
        return [], {"missing": p}
    out = []
    for line in open(p):
        r = json.loads(line)
        out.append(dict(pool="wrapper", mode=r["corpus"], model=r["model"],
                        prompt=r["prompt"], wrapper_id=r["id"], text=r["text"]))
    return out, {}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--seed", type=int, default=20260820)
    a = ap.parse_args(argv)
    import numpy as np

    rows, notes = [], {}
    for fn in (model_narrative, human_anchor, wrapper):
        got, note = fn()
        rows += got
        if note:
            notes[fn.__name__] = note
        print("  %-18s %6d passages" % (fn.__name__, len(got)))

    for r in rows:
        r["id"] = "%s-%s" % (r["pool"][:4],
                             hashlib.sha256(r["text"].encode()).hexdigest()[:14])
    #: dedupe on the text hash: a passage appearing in two pools would be scored
    #: twice and counted twice in whichever comparison pooled them
    seen, keep = set(), []
    for r in rows:
        if r["id"] in seen:
            continue
        seen.add(r["id"]); keep.append(r)
    dropped = len(rows) - len(keep)

    random.Random(a.seed).shuffle(keep)

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w") as fh:
        for r in keep:
            fh.write(json.dumps(r) + "\n")

    import collections, statistics as st
    by = collections.defaultdict(list)
    for r in keep:
        by[r["pool"]].append(len(r["text"].encode()))
    man = dict(rows=len(keep), duplicates_dropped=dropped, seed=a.seed,
               shuffled=True, notes=notes,
               pools={k: dict(n=len(v), bytes_median=int(st.median(v)),
                              bytes_p10=int(np.percentile(v, 10)),
                              bytes_p90=int(np.percentile(v, 90))) for k, v in by.items()})
    with open(a.out.replace(".jsonl", ".manifest.json"), "w") as fh:
        json.dump(man, fh, indent=1)

    print()
    print("%-18s %8s %10s %10s %10s" % ("pool", "n", "p10 bytes", "median", "p90"))
    for k in sorted(by):
        v = by[k]
        print("%-18s %8d %10d %10d %10d"
              % (k, len(v), np.percentile(v, 10), st.median(v), np.percentile(v, 90)))
    if dropped:
        print("\n%d duplicate passages dropped (same text in two pools)" % dropped)
    print("\n-> %s  (%d rows, shuffled, seed %d)" % (a.out, len(keep), a.seed))
    print("-> %s" % a.out.replace(".jsonl", ".manifest.json"))


if __name__ == "__main__":
    main()
