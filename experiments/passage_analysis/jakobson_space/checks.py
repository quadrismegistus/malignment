"""Re-run every provenance claim this folder's docstrings assert.

    python .../checks.py
    python .../checks.py --sample 400

Each docstring here carries numbers that were established once, at a terminal,
and then written into prose. A number that cannot be re-run is a number nobody
will re-run, and the first thing to rot when the data moves. This file is the
counterpart: every check prints PASS or FAIL against the value the prose claims,
and a FAIL means the prose is now wrong.

Checks, and where each is asserted:

    1  explode.py   the bge stash reproduces the stored mean_drift for the open
                    models (claimed: 400 of 400 sampled)
    2  explode.py   drift_geometry's stanza vectors do NOT (claimed: 236 of 315,
                    9% off by more than 0.01) -- the reason the stash is used
    3  explode.py   the nltk re-split reproduces `sent_chars` exactly for the
                    human pool (claimed: 3,000 of 3,000)
    4  explode.py   reading quadrants.csv WITHOUT newline="" corrupts two
                    passages (claimed: 2 rows stop hashing to their text_sha)
    5  README       the semantic coding and the M06 passage corpus are DISJOINT
                    (claimed: passC's 100 prompts, 0 in beam_sample_105)
    6  README       every sentence decomposition reproduces its passage drift
                    (claimed: 14,414 of 14,414)

Check 4 is deliberately a check that something FAILS. A guard nobody has watched
refuse is a guard nobody has tested, and this one exists because the corruption
it names was real and silent.
"""

import argparse, collections, csv, hashlib, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data"))
ARCHIVE = "/Users/rj416/github/malign-logits"
STASH = os.path.join(ARCHIVE, "data/raw/cache/sent_embeddings")
QUAD = os.path.join(HERE, "results", "quadrants.csv")
EXPLODED = os.path.join(DATA, "jakobson_space", "exploded")
NS_EN = "BAAI/bge-m3|nltk-en|refuse-untrunc-2026-08-14"

N = {"ok": 0, "fail": 0}


def report(name, ok, got, claimed):
    N["ok" if ok else "fail"] += 1
    print("  %-4s %-46s %s%s" % ("PASS" if ok else "FAIL", name, got,
                                 "" if ok else "   CLAIMED: %s" % claimed))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=400)
    a = ap.parse_args(argv)
    import numpy as np, nltk, pyarrow.parquet as pq
    import random
    from hashstash import HashStash

    csv.field_size_limit(10 ** 7)
    rows = list(csv.DictReader(open(QUAD, newline="")))
    mod = [r for r in rows if r["category"] in ("base", "aligned")]
    st = HashStash(STASH, engine="lmdb", serializer="hashstash",
                   compress="lz4", b64=True, flat=True)

    print("1-2. WHICH SENTENCE-VECTOR SOURCE REPRODUCES THE PASSAGE NUMBER")
    hit = bad = 0
    for r in random.Random(1).sample(mod, min(a.sample, len(mod))):
        sv = st.get({"embedder": NS_EN, "prompt": r["prompt"], "text": r["text"]})
        if sv is None:
            continue
        V = np.asarray(sv, dtype=np.float32)
        if len(V) < 2:
            continue
        hit += 1
        md = float(np.mean([1 - float(V[i - 1] @ V[i]) for i in range(1, len(V))]))
        bad += abs(md - float(r["drift"])) > 1e-6
    report("stash reproduces stored mean_drift", bad == 0,
           "%d of %d sampled" % (hit - bad, hit), "all of them")

    #: the stanza comparison needs passC to map pid -> text_sha
    passc = os.path.join(os.path.dirname(HERE), "interiority_in_passages",
                         "results", "passC")
    id2sha = {}
    for fn in ("sample.parquet", "triage.parquet"):
        fp = os.path.join(passc, fn)
        if os.path.exists(fp):
            t = pq.read_table(fp, columns=["id", "text"])
            for i, tx in zip(t.column("id").to_pylist(), t.column("text").to_pylist()):
                if tx:
                    id2sha.setdefault(i, hashlib.sha256(tx.encode()).hexdigest()[:16])
    q = {r["text_sha"]: float(r["drift"]) for r in mod if r["text_sha"]}
    root = os.path.join(DATA, "drift_geometry", "sentence_vecs")
    n_cmp = n_exact = n_off = 0
    if os.path.isdir(root):
        for fn in sorted(os.listdir(root))[:6]:
            if not fn.endswith(".parquet"):
                continue
            t = pq.read_table(os.path.join(root, fn),
                              columns=["pid", "sent_idx", "vec"])
            pid = t.column("pid").to_pylist(); si = t.column("sent_idx").to_pylist()
            V = np.asarray(t.column("vec").to_pylist(), dtype=np.float32)
            grp = collections.defaultdict(list)
            for k, p in enumerate(pid):
                grp[p].append((si[k], k))
            for p, rs in grp.items():
                sh = id2sha.get(p)
                if sh not in q:
                    continue
                M = V[[k for _, k in sorted(rs)]]
                if len(M) < 2:
                    continue
                md = float(np.mean([1 - float(M[i - 1] @ M[i]) for i in range(1, len(M))]))
                n_cmp += 1
                n_exact += abs(md - q[sh]) < 1e-6
                n_off += abs(md - q[sh]) > 0.01
    report("stanza vectors do NOT reproduce it", n_cmp and n_exact < n_cmp,
           "%d of %d exact, %d off by >0.01" % (n_exact, n_cmp, n_off),
           "236 of 315, 9% off")

    print("\n3. THE nltk RE-SPLIT REPRODUCES sent_chars")
    pool = {}
    for line in open(os.path.join(DATA, "ref_pool", "ref_pool.jsonl")):
        j = json.loads(line)
        if j.get("anchor_id"):
            pool[j["anchor_id"]] = j["text"]
    ok = miss = 0
    for line in open(os.path.join(DATA, "jakobson_space", "bge_human",
                                  "bge_human00.jsonl")):
        r = json.loads(line)
        t = pool.get(r["id"])
        if t is None:
            continue
        if [len(x) for x in nltk.sent_tokenize(t)] == list(r["sent_chars"]):
            ok += 1
        else:
            miss += 1
    report("sent_chars reproduced element-wise", miss == 0,
           "%d of %d" % (ok, ok + miss), "all of them")

    print("\n4. THE newline='' CORRUPTION IS REAL (this check expects a FAILURE)")
    bad_no = sum(1 for r in csv.DictReader(open(QUAD))
                 if r["text_sha"] and
                 hashlib.sha256(r["text"].encode()).hexdigest()[:16] != r["text_sha"])
    bad_yes = sum(1 for r in rows if r["text_sha"] and
                  hashlib.sha256(r["text"].encode()).hexdigest()[:16] != r["text_sha"])
    report("without newline='': text stops matching sha", bad_no > 0,
           "%d rows corrupted" % bad_no, "2 rows")
    report("with newline='': every row matches", bad_yes == 0,
           "%d rows corrupted" % bad_yes, "0 rows")

    print("\n5. THE SEMANTIC CODING AND THE M06 PASSAGE CORPUS ARE DISJOINT")
    pr = set()
    fp = os.path.join(passc, "sample.parquet")
    if os.path.exists(fp):
        pr = set(pq.read_table(fp, columns=["prompt"]).column("prompt").to_pylist())
    beam = os.path.join(ARCHIVE, "data", "beam_sample_105_plus_anger.csv")
    stems = ({r["prompt"] for r in csv.DictReader(open(beam))}
             if os.path.exists(beam) else set())
    report("passC prompts absent from the passage corpus",
           bool(pr) and bool(stems) and not (pr & stems),
           "%d coded prompts, %d overlap with %d stems" % (len(pr), len(pr & stems),
                                                           len(stems)), "0 overlap")

    print("\n6. EVERY SENTENCE DECOMPOSITION REPRODUCES ITS PASSAGE")
    sp = os.path.join(EXPLODED, "sentences.parquet")
    if os.path.exists(sp):
        t = pq.read_table(sp, columns=["id", "reproduces"]).to_pydict()
        seen = {}
        for pid, rep in zip(t["id"], t["reproduces"]):
            seen[pid] = rep
        good = sum(1 for v in seen.values() if v)
        report("reproduces == True on every passage", good == len(seen),
               "%s of %s" % ("{:,}".format(good), "{:,}".format(len(seen))),
               "all of them")
    else:
        report("sentences.parquet present", False, "MISSING -- run explode.py", "")

    print("\n%d passed, %d FAILED" % (N["ok"], N["fail"]))
    return 1 if N["fail"] else 0


if __name__ == "__main__":
    sys.exit(main())
