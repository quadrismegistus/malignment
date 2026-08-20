"""One parquet with both axes for the whole generated population. No stash hunting.

    python experiments/passage_analysis/jakobson_space/build_population.py
    python experiments/passage_analysis/jakobson_space/build_population.py --limit 5000

Writes `$MALIGNMENT_DATA/jakobson_space/passages.parquet`: one row per passage,
carrying the BLT surprisal axis and the bge drift axis together with the keys to
join back to anything. **The point is that nobody has to open a 40 GB hashstash or
a fleet shard directory again.**

## The two axes, and where they come from

    SURPRISAL   `bits_per_byte`, already computed per passage in the BLT fleet's
                shard metadata (`data/raw/blt_fleet/*/blt_shardNN.jsonl`).
                ref `itazap/blt-1b-hf`. BYTE-LEVEL, so it is one scale across all
                58 generator models AND across en/zh -- which is the whole reason
                a fixed scorer was hard: cross-scoring in `gen_scores` works only
                because base and aligned share a tokenizer, and no roster model
                can score another family's token_ids without re-tokenising.

    DRIFT       computed here from the fleet's sentence vectors in
                `data/raw/cache/sent_embeddings` (40 GB, 524,603 keys), using the
                archive's own definitions -- see `../drift_geometry/PROVENANCE.md`,
                which quotes them verbatim so they cannot drift.

## WHICH EMBEDDER NAMESPACE, AND WHY IT IS NOT OBVIOUS

The stash holds eight. Three matter, and the same passage has a different sentence
count under each:

    BAAI/bge-m3|nltk-en                        14,178   mean  5.26 sentences
    BAAI/bge-m3|nltk-en|full                   16,002   mean 10.91
    BAAI/bge-m3|nltk-en|refuse-untrunc-...    372,042   mean 11.89

**The bare namespace is TRUNCATED** -- mean 5.26 sentences, which is F15's regime
exactly (its median was 5) and the population where drift reliability measured
ICC 0.07. `|full` is an earlier untruncated pilot. **`refuse-untrunc-2026-08-14`
is the one to use**: untruncated, largest, and matching `bge_population.json`'s
planned totals exactly (en 372,103 / zh 78,879).

`BAAI/bge-m3|slot-word` is a DIFFERENT SPACE -- word vectors, not sentences -- and
is excluded. Mixing it in would be the error `malignment/vectors.py` warns about
in its own docstring.

## The join

`text_sha = sha256(text)[:16]`, verified against a real shard row. `bge_cloud.py`
says the two runs were "keyed the same way, so the two join on (prompt, text_sha)
with no re-derivation" -- the stash keys on (embedder, prompt, text), the BLT
shards on (prompt, text_sha), and text is what connects them.

## Splitter rides on every row

`splitter` is a column, not a footnote. The ingest that wrote these vectors says
"`BAAI/bge-m3` alone is not the identity of this result -- the same passage under
nltk-en and stanza-zh yields different sentences." Measured on the 13,016 passages
where this repo's own stanza-en run overlaps the fleet's nltk-en: **r = 0.961,
62.3% identical sentence counts, 85.1% within one sentence.** So the two English
splitters are effectively one instrument and the earlier claim that they were not
was an over-read -- but the field stays, because zh is a different matter and
because a nuisance variable you cannot see is one you cannot check.
"""

import argparse, collections, glob, gzip, hashlib, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ARCHIVE = "/Users/rj416/github/malign-logits"
STASH = os.path.join(ARCHIVE, "data/raw/cache/sent_embeddings")
SHARDS = os.path.join(ARCHIVE, "data/raw/blt_fleet/*/blt_shard*.jsonl")
PASSAGES = os.path.join(ARCHIVE, "data/raw/blt_passages.jsonl.gz")
DATA = os.path.join(os.environ.get("MALIGNMENT_DATA",
                                   os.path.expanduser("~/malignment-data")),
                    "jakobson_space")
OUT = os.path.join(DATA, "passages.parquet")
MANIFEST = os.path.join(HERE, "results", "population_manifest.json")
NS = {"en": "BAAI/bge-m3|nltk-en|refuse-untrunc-2026-08-14",
      "zh": "BAAI/bge-m3|stanza-zh|refuse-untrunc-2026-08-14"}


def metrics(sv):
    """The archive's drift family plus `ordering`. sv: (n, 1024) L2-normalised."""
    import numpy as np
    #: EVERY ROW CARRIES EVERY FIELD. A first batch of single-sentence passages
    #: would otherwise let pyarrow infer a schema with no drift columns at all,
    #: and every later batch would then fail to match it -- which is how this
    #: failed the first time.
    keys = ("mean_drift", "max_drift", "std_drift", "total_drift", "path_length",
            "directedness", "mean_pairwise", "ordering")
    n = len(sv)
    if n < 2:
        return dict(n_sents=n, **{k: None for k in keys})
    step = 1.0 - np.sum(sv[:-1] * sv[1:], axis=1)
    sim = sv @ sv.T
    total = float(1.0 - sim.min()); path = float(step.sum())
    iu = np.triu_indices(n, k=1)
    mp = float((1.0 - sim[iu]).mean())
    return dict(n_sents=n, mean_drift=round(float(step.mean()), 6),
                max_drift=round(float(step.max()), 6),
                std_drift=round(float(step.std()), 6),
                total_drift=round(total, 6), path_length=round(path, 6),
                directedness=round(total / path if path > 0 else 0.0, 6),
                mean_pairwise=round(mp, 6),
                ordering=round(float(step.mean()) - mp, 6))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    ap.add_argument("--flush", type=int, default=25000)
    a = ap.parse_args(argv)
    import numpy as np, pyarrow as pa, pyarrow.parquet as pq
    from hashstash import HashStash

    #: BLT metadata: the surprisal axis, already per passage.
    blt = {}
    for f in sorted(glob.glob(SHARDS)):
        if ".skipped." in f:
            continue
        for line in open(f):
            d = json.loads(line)
            blt[(d["prompt"], d["text_sha"])] = d
    print("BLT metadata rows: %d" % len(blt))

    #: texts, so the stash (keyed on text) can meet BLT (keyed on text_sha)
    text_of = {}
    with gzip.open(PASSAGES, "rt") as fh:
        for line in fh:
            d = json.loads(line)
            t = d.get("text") or ""
            text_of[(d.get("prompt"), hashlib.sha256(t.encode()).hexdigest()[:16])] = (
                t, d.get("corpora") or [], d.get("script"))
    print("BLT passage texts: %d" % len(text_of))

    st = HashStash(STASH, engine="lmdb", serializer="hashstash",
                   compress="lz4", b64=True, flat=True)
    os.makedirs(DATA, exist_ok=True)
    os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
    for f in glob.glob(os.path.join(DATA, "passages.parquet")):
        os.remove(f)

    buf, rows, part, miss_vec, miss_blt = [], 0, 0, 0, 0
    seen = set()
    writer = None
    for (prompt, sha), meta in blt.items():
        if a.limit and rows >= a.limit:
            break
        got = text_of.get((prompt, sha))
        if got is None:
            miss_blt += 1
            continue
        text, corpora, script = got
        ns = NS.get("zh" if script == "zh" else "en")
        try:
            sv = st.get({"embedder": ns, "prompt": prompt, "text": text})
        except Exception:
            sv = None
        if sv is None:
            miss_vec += 1
            continue
        if (prompt, sha) in seen:
            continue
        seen.add((prompt, sha))
        m = metrics(np.asarray(sv, dtype=np.float32))
        r = dict(text_sha=sha, prompt=prompt, script=script,
                 corpora=",".join(sorted(corpora)),
                 splitter=ns.split("|", 1)[1],
                 bits_per_byte=meta.get("bits_per_byte"),
                 blt_ref=meta.get("ref"), n_bytes=meta.get("n_bytes"),
                 n_chars=meta.get("n_chars"), blt_n_tokens=meta.get("n_tokens"))
        r.update(m)
        buf.append(r); rows += 1
        if len(buf) >= a.flush:
            t = pa.Table.from_pylist(buf)
            writer = writer or pq.ParquetWriter(OUT, t.schema, compression="zstd")
            writer.write_table(t); buf = []
            print("  %d rows ..." % rows, flush=True)
    if buf:
        t = pa.Table.from_pylist(buf)
        writer = writer or pq.ParquetWriter(OUT, t.schema, compression="zstd")
        writer.write_table(t)
    if writer:
        writer.close()

    t = pq.read_table(OUT)
    d = {c: t.column(c).to_pylist() for c in ("corpora", "script", "n_sents",
                                              "bits_per_byte", "mean_drift")}
    cc = collections.Counter(d["corpora"]); sc = collections.Counter(d["script"])
    man = dict(_what="one row per passage: BLT bits_per_byte and bge drift, both axes",
               out=OUT, rows=t.num_rows, columns=t.schema.names,
               namespaces=NS, blt_ref="itazap/blt-1b-hf",
               blt_metadata_rows=len(blt), blt_texts=len(text_of),
               dropped_no_vector=miss_vec, dropped_no_text=miss_blt,
               by_corpora=dict(cc), by_script=dict(sc),
               bytes=os.path.getsize(OUT))
    json.dump(man, open(MANIFEST, "w"), indent=1)
    print("\n  rows %d | %.1f MB" % (t.num_rows, os.path.getsize(OUT) / 1048576))
    print("  dropped: no sentence vector %d | no text %d" % (miss_vec, miss_blt))
    print("  by corpus:", dict(cc.most_common()))
    print("  by script:", dict(sc))
    print("\n  %-16s %9s %9s" % ("", "median", "mean"))
    for k in ("bits_per_byte", "mean_drift", "n_sents"):
        v = np.array([x for x in d[k] if x is not None], float)
        print("  %-16s %9.4f %9.4f" % (k, np.median(v), v.mean()))
    print("\n-> %s" % OUT)
    print("-> results/population_manifest.json")


if __name__ == "__main__":
    main()
