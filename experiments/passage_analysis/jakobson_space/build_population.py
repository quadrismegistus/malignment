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

## ONE ROW PER PASSAGE, WITH POINTERS DOWN TO THE OTHER TWO GRAINS

There are three grains and this file is the middle one:

    passage    THIS TABLE. Both axes are defined here and it is the analysis unit.
    sentence   the bge stash holds n_sents vectors of 1024 floats per passage. The
               drift family COLLAPSES them -- mean_drift is the mean step between
               consecutive sentences, total_drift the diameter of the whole set --
               so the sentences do not survive into these columns.
    byte       BLT's `.f32` holds per-byte surprisal; `bits_per_byte` is its mean.

**A row therefore carries the KEY to each lower grain rather than the data.**
`bge_embedder` + `prompt` + `text` is exactly the stash key, so the sentence
vectors are one `st.get()` away. `blt_box` + `blt_shard` + `blt_row` + `blt_n`
locate the per-byte block in the fleet's flat float32. Nothing is duplicated and
nothing is unreachable.

A per-sentence table is deliberately NOT built: 4.4M sentences at 1024 float32
each is ~18 GB, and the step distances that drift is made of are recomputable from
the stash in seconds.

## Enough to join back to ClickHouse

`model`, `sample_idx`, `role`, `pair`, `prompt_id`, `temp`, `seed`,
`gen_n_tokens`, `finish_reason` come from `gen_sequences`, which is also where the
TEXT is taken from -- so the text in this file is the authoritative one and not a
re-derivation. `(corpus, model, prompt, sample_idx)` is the gen_sequences key.

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
SIDECAR = os.path.join(DATA, "passages_manifest.json")   # beside the data
CORPORA = ("passage", "f11_l2", "y")
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


def ch_rows():
    """gen_sequences for our corpora: the AUTHORITATIVE text plus every CH key."""
    import subprocess
    cols = ("corpus", "model", "prompt", "sample_idx", "role", "pair", "prompt_id",
            "temp", "seed", "n_tokens", "finish_reason", "text")
    sql = ("SELECT %s FROM malign_logits.gen_sequences WHERE corpus IN (%s) "
           "AND forced_word='' FORMAT JSONEachRow"
           % (", ".join(cols), ",".join("'%s'" % c for c in CORPORA)))
    pr = subprocess.Popen(["clickhouse", "client", "-q", sql],
                          stdout=subprocess.PIPE, text=True, bufsize=1 << 20)
    #: CLOSE THE CHILD DOWN ON EARLY EXIT. A `--limit` run breaks out of this
    #: generator while clickhouse is still streaming, which leaves it writing to a
    #: closed pipe (errno 32) and, worse, leaves the process alive. try/finally
    #: makes the smoke run and the real run behave the same way.
    try:
        for line in pr.stdout:
            line = line.strip()
            if line:
                yield json.loads(line)
    finally:
        try:
            pr.stdout.close()
        except Exception:
            pass
        if pr.poll() is None:
            pr.terminate()
        pr.wait()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    ap.add_argument("--flush", type=int, default=20000)
    a = ap.parse_args(argv)
    import numpy as np, pyarrow as pa, pyarrow.parquet as pq
    from hashstash import HashStash

    #: BLT metadata, carrying WHICH SHARD AND ROW so the per-byte block stays
    #: reachable. `row`/`n` index into the sibling .f32; without the box and shard
    #: they point at nothing.
    blt = {}
    for f in sorted(glob.glob(SHARDS)):
        if ".skipped." in f:
            continue
        box = os.path.basename(os.path.dirname(f))
        shard = os.path.basename(f)
        for line in open(f):
            d = json.loads(line)
            d["_box"], d["_shard"] = box, shard
            blt[(d["prompt"], d["text_sha"])] = d
    print("BLT metadata rows: %d over %d shard files"
          % (len(blt), len(set((d["_box"], d["_shard"]) for d in blt.values()))))

    #: ARM AND LINEAGE, because ClickHouse does not have them for f11_l2.
    #: gen_sequences carries `role` and `pair` for `passage` and `y` and leaves
    #: BOTH EMPTY on all 192,119 f11_l2 rows -- which would make the arm
    #: unrecoverable on the one corpus the drift axis was validated against.
    #: roster.lineages() is {base: [base, aligned, ...]}, so membership gives the
    #: arm and the key gives the lineage. Used to FILL, never to overwrite: where
    #: CH has a role it wins, and `arm_src` records which answered.
    from malignment import roster as _roster
    _lin = _roster.lineages()
    arm_of, lineage_of = {}, {}
    for base, members in _lin.items():
        for m in members:
            lineage_of[m] = base
            arm_of[m] = "base" if m == base else "aligned"

    st = HashStash(STASH, engine="lmdb", serializer="hashstash",
                   compress="lz4", b64=True, flat=True)
    os.makedirs(DATA, exist_ok=True)
    os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
    if os.path.exists(OUT):
        os.remove(OUT)

    buf, rows, writer = [], 0, None
    seen, no_blt, no_vec = set(), 0, 0
    for r in ch_rows():
        if a.limit and rows >= a.limit:
            break
        text = r.get("text") or ""
        sha = hashlib.sha256(text.encode()).hexdigest()[:16]
        key = (r["prompt"], sha)
        if key in seen:
            continue
        meta = blt.get(key)
        if meta is None:
            no_blt += 1
            continue
        script = meta.get("script")
        ns = NS.get("zh" if script == "zh" else "en")
        try:
            sv = st.get({"embedder": ns, "prompt": r["prompt"], "text": text})
        except Exception:
            sv = None
        if sv is None:
            no_vec += 1
            continue
        seen.add(key)
        row = dict(
            #: identity, and the text itself -- from gen_sequences, so it is the
            #: authoritative copy rather than a re-derivation
            text_sha=sha, prompt=r["prompt"], text=text,
            corpus=r["corpus"], corpora=",".join(sorted(meta.get("corpora") or [])),
            script=script,
            #: ClickHouse: (corpus, model, prompt, sample_idx) is the gen_sequences key
            model=r.get("model"), sample_idx=r.get("sample_idx"),
            role=r.get("role"), pair=r.get("pair"), prompt_id=r.get("prompt_id"),
            arm=(r.get("role") or arm_of.get(r.get("model")) or ""),
            arm_src=("clickhouse" if r.get("role")
                     else ("roster" if arm_of.get(r.get("model")) else "")),
            lineage=(r.get("pair") or lineage_of.get(r.get("model")) or ""),
            temp=r.get("temp"), seed=r.get("seed"),
            gen_n_tokens=r.get("n_tokens"), finish_reason=r.get("finish_reason"),
            #: BLT: the axis, and where its per-byte block lives
            bits_per_byte=meta.get("bits_per_byte"), blt_ref=meta.get("ref"),
            blt_box=meta["_box"], blt_shard=meta["_shard"],
            blt_row=meta.get("row"), blt_n=meta.get("n"),
            n_bytes=meta.get("n_bytes"), n_chars=meta.get("n_chars"),
            blt_n_tokens=meta.get("n_tokens"),
            #: bge: `bge_embedder` + prompt + text IS the stash key
            bge_embedder=ns, splitter=ns.split("|", 1)[1],
        )
        row.update(metrics(np.asarray(sv, dtype=np.float32)))
        buf.append(row); rows += 1
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

    t = pq.read_table(OUT, columns=["corpus", "script", "model", "n_sents",
                                    "bits_per_byte", "mean_drift", "n_bytes",
                                    "arm", "arm_src", "lineage"])
    d = {c: t.column(c).to_pylist() for c in t.schema.names}
    man = dict(_what="one row per passage: BLT surprisal axis, bge drift axis, the "
                     "text, and keys down to ClickHouse / the BLT .f32 / the bge stash",
               out=OUT, rows=t.num_rows, columns=pq.read_schema(OUT).names,
               grain="passage; bge_embedder+prompt+text reaches the sentence "
                     "vectors, blt_box+blt_shard+blt_row+blt_n reaches the per-byte block",
               namespaces=NS, blt_ref="itazap/blt-1b-hf", corpora=list(CORPORA),
               dropped_no_blt=no_blt, dropped_no_vector=no_vec,
               by_corpus=dict(collections.Counter(d["corpus"])),
               by_script=dict(collections.Counter(d["script"])),
               models=len(set(d["model"])),
               by_arm=dict(collections.Counter(d["arm"])),
               arm_source=dict(collections.Counter(d["arm_src"])),
               lineages=len({x for x in d["lineage"] if x}),
               bytes=os.path.getsize(OUT))
    json.dump(man, open(MANIFEST, "w"), indent=1)
    json.dump(man, open(SIDECAR, "w"), indent=1)
    print("\n  rows %d | %.1f MB | %d models"
          % (t.num_rows, os.path.getsize(OUT) / 1048576, len(set(d["model"]))))
    print("  dropped: no BLT %d | no sentence vector %d" % (no_blt, no_vec))
    print("  by corpus:", dict(collections.Counter(d["corpus"]).most_common()))
    print("  by script:", dict(collections.Counter(d["script"])))
    print("  by arm   :", dict(collections.Counter(d["arm"]).most_common()),
          "| source:", dict(collections.Counter(d["arm_src"]).most_common()))
    print("  lineages :", len({x for x in d["lineage"] if x}))
    print("\n-> %s" % OUT)
    print("-> %s  (sidecar, beside the data)" % SIDECAR)


if __name__ == "__main__":
    main()
