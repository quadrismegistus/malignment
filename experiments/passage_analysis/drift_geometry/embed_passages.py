"""Split the narrative-coded passages into sentences and embed them. Resumable.

    python experiments/passage_analysis/drift_geometry/embed_passages.py
    python experiments/passage_analysis/drift_geometry/embed_passages.py --limit 50
    python experiments/passage_analysis/drift_geometry/embed_passages.py --report

One job only: TEXT IN, VECTORS OUT. No metric is computed here and no comparison
is made, so a defect in the drift arithmetic later cannot be blamed on this pass
and a re-run of the arithmetic costs nothing.

## Population: narrative-coded only

`../interiority_in_passages/results/passC/` holds 13,565 passages coded by a blind
Opus reader; 13,557 join to text. ALL of them are embedded and `narrative_A` is
carried on every row, so the narrative filter is a downstream choice rather than a
property of the file.

**That is not fastidiousness: the filter and the outcome are entangled.**

    drift        narrative    not
    HOLDS            5,756   4,322
    SHIFTS             401   1,626
    UNMOORED            17   1,435

Filtering to narrative here would have kept 17 of 1,452 UNMOORED passages and
deleted a comparison group before anyone looked at it. Coder B covers 3,610 of
the same passages and rides along as `drift_B` for the agreement filter.

## The join

    codings/*.json    {"A": {pid: {narrative, drift, degree, mode, span}}, "B": ...}
    sample.parquet    id (== pid) -> text, model, arm, pair, prompt, sample_idx

Both already in the repo under `../interiority_in_passages/results/passC/`.

## Sentence splitting: stanza, not a regex and not the parser

`stanza` en, `tokenize` only. Generated text is messy in exactly the way that
breaks naive splitters -- run-ons, missing terminal punctuation, mid-sentence
newlines -- and a sentence count that is wrong is not a small error here: the
audit this folder ports found that `directedness` IS sentence count (Spearman
-0.923), so the splitter is upstream of the thing most likely to be an artifact.

## The embedder is the repo's, deliberately

`slot_axis._model()` -- `BAAI/bge-m3`, `normalize_embeddings=True`, and
**`device="cpu"` per RH's standing ruling that bge on MPS is not to be trusted**.
Using the repo's own accessor rather than constructing a SentenceTransformer here
is what makes these vectors comparable to every other vector in the project; a
second construction is a second set of defaults.

## Written in PARTS, and the vectors stay float32

`sentence_vecs/part-NNNNN.parquet`, flushed every `--flush` passages. The first
version of this file accumulated everything in a list and wrote once at the end,
which was wrong twice and the second one is worse:

  * a crash at minute 70 of 75 lost everything, and the docstring's claim to be
    "resumable by content" was decorative -- there was nothing on disk to resume
    FROM until the run had already succeeded;
  * `vec=v.tolist()` turns a 4,096-byte float32 array into a 32,824-byte list of
    Python floats, **8x**, so ~200k sentences meant about **6.1 GB resident**
    before any write. Measured, not estimated.

Now each part is written as it is finished and the vectors are stored as
`fixed_size_list<float32>[1024]` built straight from the numpy batch. Resume reads
the pids already on disk, so an interrupted run costs at most one part.

## Where the vectors go, and why not ClickHouse

`$MALIGNMENT_DATA/drift_geometry/sentence_vecs.parquet`. Nobody queries an
individual sentence vector -- the reusable artifact is the per-passage metric --
and the bare-word table in `malignment/vectors.py` says in its own docstring that
its space MUST NOT be mixed with another. Parquet in the data root keeps a metric
change from costing a re-embed, which is the only reuse that matters.
"""

import argparse, json, glob, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, REPO)
PASSC = os.path.join(os.path.dirname(HERE), "interiority_in_passages",
                     "results", "passC")
DATA = os.path.join(os.environ.get("MALIGNMENT_DATA",
                                   os.path.expanduser("~/malignment-data")),
                    "drift_geometry")
OUT = os.path.join(DATA, "sentence_vecs")   # a DIRECTORY of parts
MANIFEST = os.path.join(HERE, "results", "embed_passages_manifest.json")
DIM = 1024


def codings():
    """pid -> {coder: fields}. Coder A is the population; B is the overlap."""
    out = {}
    for f in sorted(glob.glob(os.path.join(PASSC, "codings", "*.json"))):
        d = json.load(open(f))
        for arm in ("A", "B"):
            for pid, v in (d.get(arm) or {}).items():
                if isinstance(v, dict):
                    out.setdefault(pid, {})[arm] = v
    return out


def population():
    """The narrative-coded rows, joined to their text. -> list[dict]"""
    import pyarrow.parquet as pq
    cod = codings()
    #: EVERY CODED PASSAGE, and the narrative filter applied downstream instead.
    #: Embedding is the expensive irreversible step and filtering is free, so a
    #: filter applied HERE bakes a design choice into the data. It also matters
    #: which choice: `narrative` and `drift` are not independent -- filtering to
    #: narrative keeps 5,756 HOLDS and 401 SHIFTS but only 17 of 1,452 UNMOORED,
    #: because a passage that comes unmoored has largely stopped being a
    #: narrative. Embedding the narrative subset alone would have destroyed a
    #: group before anyone looked. `narrative_A` rides on every row.
    keep = set(cod)
    #: TWO ID NAMESPACES, AND READING ONE OF THEM LOSES 76% SILENTLY.
    #: Pass A/B sampled into `p######` (sample.parquet, 41,412 rows); Pass C --
    #: which produced these codings -- drew from `f######` (triage.parquet,
    #: 104,000). Of the 13,565 coded pids, 3,210 are `p*` and 10,354 are `f*`,
    #: with exactly ONE in neither. The first version of this function read
    #: sample.parquet alone and reported 628 narrative passages as though that
    #: were the population: no error, a plausible number, 90% of the work gone.
    t = []
    for f in ("sample.parquet", "triage.parquet"):
        fp = os.path.join(PASSC, f)
        if os.path.exists(fp):
            t += pq.read_table(fp).to_pylist()
    rows, seen = [], set()
    for r in t:
        if r.get("id") in seen:
            continue
        seen.add(r.get("id"))
        pid = r.get("id")
        if pid in keep and (r.get("text") or "").strip():
            a = cod[pid]["A"]
            rows.append(dict(pid=pid, text=r["text"], model=r.get("model"),
                             arm=r.get("arm"), pair=r.get("pair"),
                             prompt=r.get("prompt"),
                             sample_idx=r.get("sample_idx"),
                             narrative_A=a.get("narrative"),
                             drift_A=a.get("drift"), degree_A=a.get("degree"),
                             mode_A=a.get("mode"),
                             drift_B=(cod[pid].get("B") or {}).get("drift")))
    return rows, len(cod), len(keep)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, help="first N passages, for a smoke run")
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--flush", type=int, default=250,
                    help="write a part every N passages")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args(argv)
    import numpy as np, pyarrow as pa, pyarrow.parquet as pq

    if a.report:
        if not glob.glob(os.path.join(OUT, "part-*.parquet")):
            print("nothing written yet at %s" % OUT); return
        t = pq.ParquetDataset(OUT).read(columns=["pid"])
        b = sum(os.path.getsize(f) for f in glob.glob(os.path.join(OUT, "part-*.parquet")))
        print("%s\n  %d sentence rows, %d passages, %.1f MB"
              % (OUT, t.num_rows, len(set(t.column("pid").to_pylist())), b / 1048576))
        if os.path.exists(MANIFEST):
            print(json.dumps(json.load(open(MANIFEST)), indent=1))
        return

    rows, n_coded, n_narr = population()
    import collections as _c
    nb = _c.Counter((r["narrative_A"], r["drift_A"]) for r in rows)
    print("codings: %d | joined to text: %d | ALL embedded, filter is downstream"
          % (n_coded, len(rows)))
    print("  %-10s %10s %8s" % ("drift", "narrative", "not"))
    for d in ("HOLDS", "SHIFTS", "UNMOORED"):
        print("  %-10s %10d %8d" % (d, nb.get((True, d), 0), nb.get((False, d), 0)))
    if a.limit:
        rows = rows[:a.limit]
        print("  --limit %d" % a.limit)

    #: RESUMABLE BY CONTENT, not by memory: whatever pids the output already holds
    #: are skipped. An interrupted run costs only what it had not written.
    os.makedirs(OUT, exist_ok=True)
    done = set()
    parts = glob.glob(os.path.join(OUT, "part-*.parquet"))
    if parts:
        done = set(pq.ParquetDataset(OUT).read(columns=["pid"]).column("pid").to_pylist())
        rows = [r for r in rows if r["pid"] not in done]
        print("  already embedded: %d pids; %d to do" % (len(done), len(rows)))
    if not rows:
        print("nothing to do"); return

    import stanza
    nlp = stanza.Pipeline("en", processors="tokenize", verbose=False,
                          use_gpu=False, download_method=None)
    from malignment import slot_axis as SA
    model = SA._model()
    print("splitter: stanza en tokenize | embedder: %s on cpu" % SA.EMBEDDER)

    os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
    def flush(buf, n):
        """One part file, vectors as fixed_size_list<float32>. -> path or None"""
        if not buf:
            return None
        V = np.concatenate([b.pop("_v") for b in buf]).astype(np.float32)
        #: pa.array wants 1-D; the (n, DIM) block flattens and
        #: FixedSizeListArray re-imposes the row width.
        arr = pa.FixedSizeListArray.from_arrays(pa.array(V.reshape(-1)), DIM)
        tbl = pa.Table.from_pylist(buf).append_column("vec", arr)
        fp = os.path.join(OUT, "part-%05d.parquet" % n)
        pq.write_table(tbl, fp, compression="zstd")
        return fp

    buf, t0, n_sent, part = [], time.time(), 0, 0
    while os.path.exists(os.path.join(OUT, "part-%05d.parquet" % part)):
        part += 1
    for i, r in enumerate(rows, 1):
        sents = [s.text.strip() for s in nlp(r["text"]).sentences if s.text.strip()]
        if not sents:
            continue
        V = np.asarray(model.encode(sents, normalize_embeddings=True,
                                    show_progress_bar=False, batch_size=a.batch),
                       dtype=np.float32)
        for j, s_ in enumerate(sents):
            #: EVERY KEY THE DOWNSTREAM ANALYSIS COULD NEED, on every row.
            #: `prompt` because passages CONTINUE their prompt, so a within-prompt
            #: control needs it -- composition_not_level had to have prompt_full
            #: restored because a 60-char truncation destroyed exactly this join.
            #: `sample_idx` because the audit's ICC is a within-CELL decomposition
            #: (same model, same prompt, different generation) and without it that
            #: check cannot be reproduced here. `narrative_A` so the population
            #: filter is recoverable FROM THE DATA, not just from how it was built.
            buf.append(dict(pid=r["pid"], sent_idx=j, n_sents=len(sents),
                            sent=s_, model=r["model"], arm=r["arm"],
                            pair=r["pair"], prompt=r["prompt"],
                            sample_idx=r["sample_idx"],
                            narrative_A=r["narrative_A"],
                            drift_A=r["drift_A"], drift_B=r["drift_B"],
                            degree_A=r["degree_A"], mode_A=r["mode_A"],
                            _v=V[j:j + 1]))
        n_sent += len(sents)
        if len({b["pid"] for b in buf}) >= a.flush:
            flush(buf, part); part += 1; buf = []
        if i % 200 == 0 or i == len(rows):
            el = time.time() - t0
            print("  [%d/%d] %d sentences, %d parts, %.0fs, %.2fs/passage"
                  % (i, len(rows), n_sent, part, el, el / i), flush=True)
    flush(buf, part)

    ds = pq.ParquetDataset(OUT)
    tbl = ds.read(columns=["pid", "n_sents"])
    man = dict(_what="sentence vectors for the coded interiority passages",
               out=OUT, parts=len(glob.glob(os.path.join(OUT, "part-*.parquet"))),
               embedder=SA.EMBEDDER, device="cpu", normalized=True, dim=DIM,
               splitter="stanza en tokenize", stanza=stanza.__version__,
               n_passages_coded=n_coded, n_passages_embedded=len(set(tbl.column("pid").to_pylist())),
               n_sentences=tbl.num_rows,
               median_sents=int(np.median(tbl.column("n_sents").to_pylist())),
               bytes=sum(os.path.getsize(f) for f in glob.glob(os.path.join(OUT, "part-*.parquet"))))
    json.dump(man, open(MANIFEST, "w"), indent=1)
    #: getsize() on a DIRECTORY is the inode, not the contents -- the first run
    #: printed "0.0 MB" beside 181,665 rows. Sum the parts.
    print("\n-> %s  (%d rows, %d parts, %.1f MB)"
          % (OUT, tbl.num_rows, man["parts"], man["bytes"] / 1048576))
    print("-> results/embed_passages_manifest.json")


if __name__ == "__main__":
    main()
