#!/usr/bin/env python
"""bge vectors in ClickHouse: the store AND the scoring surface.

    python -m malignment.vectors --create
    python -m malignment.vectors --ingest-stash [--limit N]
    python -m malignment.vectors --stats

    from malignment import vectors
    V = vectors.get(prompt, words)                 # (n, dims), CH-first
    s = vectors.score(prompt, seed_vec)            # {word: cosine}, computed IN SQL

## WHY CH-FIRST, DECIDED 2026-08-17

The scoring case requires it. `dotProduct` over a million vectors measured ~12 s
server-side; the same work in python means pulling 4 GB across HTTP to compute a
number. Once ClickHouse must hold them, a second copy in hashstash is two stores
that can silently disagree -- and that is not hypothetical here:

  * `slot_axis._stash()` pinned two of five hashstash options and resolved to
    `lmdb.hashstash.lz4` while the archive's identical namespace resolved to
    `lz4+b64`. Two stores, same name, mutually invisible.
  * `lmdb` was missing from this venv, so the cache was silently OFF for a day.
  * `lz4` was missing, so a PINNED `compress="lz4"` was accepted and quietly
    resolved to `lmdb.hashstash.RAW`, a third empty store. No error at any point.

A store that becomes unreadable when a backing package is absent is not one to
keep a duplicate in. ClickHouse has no equivalent failure: a missing dependency
there is a connection error, not a silently different corpus.

## THE KEY IS WHAT CHANGES THE VECTOR

`ORDER BY (embedder, revision, sep, normalized, prompt, word)` under
ReplacingMergeTree. Every one of those changes the value, so a change COLLIDES
into a new row rather than overwriting -- which is also why no UPDATE mechanic is
needed. A vector is immutable given its key; re-inserting is idempotent and
duplicates collapse on merge.

`sep` is the ACTUAL separator, not a rule name. `sep_for` returns `""` for a CJK
prompt and `" "` otherwise, so the same word under two prompts is two different
embedded strings. Storing the instance rather than a rule version means a change
to the rule re-keys the affected rows automatically, with nothing to remember to
bump.

`dims`, `source` and `created_at` are values: they describe the row without
changing what it holds.

## THE CH ROUND TRIP IS NOT BIT-IDENTICAL, AND THAT IS A TRADE NOT A BUG

`slot_axis`'s hashstash path IS bit-identical (its comment says so, verified). This
one is not, and the difference is measured rather than assumed:

    max abs diff     7.276e-12   on 2 of 2048 components
    float32 eps      1.192e-07   so ~16,000x below float32 resolution
    score agreement  4.5e-08     against a local dot product
    noise floor      1.2e-03     the instrument's own irreducible batch nondeterminism

Python's json round trip is exact; the loss is ClickHouse PRINTING Float32 at nine
significant digits, which costs a few ULP on components near zero. Five orders of
magnitude below the noise floor already declared for this instrument, so it cannot
reach a finding.

**The fix would be to store the vector as an opaque blob, which would forfeit
`dotProduct` in SQL -- the entire reason the table exists.** So it is a deliberate
exchange of exact bytes for server-side scoring, stated here because a reader who
knows the hashstash path round-trips exactly would otherwise assume this does too.
A byte comparison of two artifacts derived through DIFFERENT stores will differ;
that is expected and is not evidence of a change.

## THE PROVENANCE HOLE, DECLARED RATHER THAN PAPERED OVER

**`revision` is `unpinned`, because nothing in this repo pins a bge-m3 snapshot.**
`slot_axis.EMBEDDER` is the bare id `BAAI/bge-m3`, so vectors computed months
apart from different upstream snapshots are indistinguishable and would pool
silently. Recording the literal string `unpinned` keeps the absence VISIBLE in
every row and makes a future pin a key change rather than a migration. It is a
column that currently carries no information and exists so that it can.
"""
import os
import sys

from . import ch

TABLE = "slot_word_vec"

#: What `revision` holds until a snapshot is pinned. See the module docstring --
#: the point is that this is legible as missing, not that it is a value.
UNPINNED = "unpinned"

#: Rows per INSERT. `ch.insert` goes out as JSONEachRow, which is why the measured
#: rate is ~2,400 vec/s rather than anything like the disk's: 1024 floats become
#: 1024 decimal literals. Batching amortises the round trip; it does not fix the
#: encoding, and a RowBinary path in `ch.py` would, if this ever needs to be fast.
#:
#: **AND MANY SMALL INSERTS IS ITS OWN PROBLEM.** Each one is a MergeTree part, so
#: an interactive screen firing ~70 rows per prompt grows the part count until
#: merges catch up. Callers adding a handful should let `get` buffer rather than
#: inserting per call.
CHUNK = 2000


def create(drop=False):
    """Create the table. Idempotent unless `drop`."""
    if drop:
        ch.execute("DROP TABLE IF EXISTS {db}.%s" % TABLE)
    ch.execute("""CREATE TABLE IF NOT EXISTS {db}.%s (
        embedder    LowCardinality(String),
        revision    LowCardinality(String),
        sep         LowCardinality(String),
        normalized  UInt8,
        prompt      String,
        word        String,
        vec         Array(Float32),
        dims        UInt16,
        source      LowCardinality(String),
        created_at  DateTime DEFAULT now()
    ) ENGINE = ReplacingMergeTree
      ORDER BY (embedder, revision, sep, normalized, prompt, word)""" % TABLE)
    return TABLE


def _rows(prompt, words, vecs, embedder, source):
    from .slot_axis import sep_for
    sep = sep_for(prompt)
    for w, v in zip(words, vecs):
        yield {"embedder": embedder, "revision": UNPINNED, "sep": sep,
               "normalized": 1, "prompt": prompt, "word": w,
               "vec": [float(x) for x in v], "dims": int(len(v)),
               "source": source}


def put(prompt, words, vecs, embedder=None, source="slot_axis"):
    """Insert vectors for one prompt. -> count"""
    from .slot_axis import NAMESPACE
    rows = list(_rows(prompt, words, vecs, embedder or NAMESPACE, source))
    n = 0
    for i in range(0, len(rows), CHUNK):
        n += ch.insert(TABLE, rows[i:i + CHUNK])
    return n


def fetch(prompt, words, embedder=None):
    """Vectors already in ClickHouse for these words. -> {word: list[float]}

    One query for the whole prompt, never one per word: the measured 176 ms is
    fixed round-trip overhead, so 70 words cost the same as 1 and 70 separate
    queries cost 70x.
    """
    from .slot_axis import NAMESPACE, sep_for
    if not words:
        return {}
    esc = lambda s: s.replace("\\", "\\\\").replace("'", "\\'")
    lst = ",".join("'%s'" % esc(w) for w in words)
    q = ("SELECT word, vec FROM {db}.%s WHERE embedder = '%s' AND revision = '%s' "
         "AND sep = '%s' AND prompt = '%s' AND word IN (%s) FORMAT JSONEachRow"
         % (TABLE, esc(embedder or NAMESPACE), UNPINNED, esc(sep_for(prompt)),
            esc(prompt), lst))
    import json
    out = {}
    for line in ch.raw(q).strip().splitlines():
        if not line.strip():
            continue
        d = json.loads(line)
        out[d["word"]] = d["vec"]
    return out


def get(prompt, words, embedder=None, source="slot_axis", write=True):
    """Vectors for `prompt + sep + word`, CH-first. -> np.ndarray (len(words), dims)

    Order matches `words`. Misses are embedded in ONE batch and inserted.

    **A STORE FAILURE MUST NOT BE ABLE TO FAIL THE ANALYSIS**, inherited from
    `slot_axis.embed_cached`: if ClickHouse is unreachable this embeds everything
    and returns the right answer slowly. It warns rather than passing silently,
    because silence is right for a transient outage and wrong for a
    misconfiguration, and the two are indistinguishable without the line.
    """
    import numpy as np
    from . import slot_axis as A
    sep = A.sep_for(prompt)
    memo_keys = ["%s%s%s" % (prompt, sep, w) for w in words]
    out = {}
    todo = []
    for w, mk in zip(words, memo_keys):
        if mk in A._MEM:
            out[w] = A._MEM[mk]
        else:
            todo.append(w)

    if todo:
        got = {}
        try:
            got = fetch(prompt, todo, embedder)
        except Exception as e:
            print("vectors: ClickHouse read failed (%s: %s); embedding instead"
                  % (type(e).__name__, e), file=sys.stderr)
        for w, v in got.items():
            a = np.asarray(v, dtype=np.float32).reshape(-1)
            A._MEM["%s%s%s" % (prompt, sep, w)] = a
            out[w] = a
        missing = [w for w in todo if w not in got]
        if missing:
            V = np.asarray(A._model().encode(
                ["%s%s%s" % (prompt, sep, w) for w in missing],
                normalize_embeddings=True, show_progress_bar=False,
                batch_size=64), dtype=np.float32)
            for w, v in zip(missing, V):
                A._MEM["%s%s%s" % (prompt, sep, w)] = v
                out[w] = v
            if write:
                try:
                    put(prompt, missing, V, embedder, source)
                except Exception as e:
                    print("vectors: ClickHouse write failed (%s: %s); this run is "
                          "correct, the next will re-embed"
                          % (type(e).__name__, e), file=sys.stderr)
    return np.stack([out[w] for w in words])


def score(prompt, seed, words=None, embedder=None):
    """Cosine of every stored word against `seed`, computed IN SQL. -> {word: float}

    **THE VECTORS NEVER LEAVE THE SERVER, which is the whole point of the table.**
    A seed direction is 4 KB; the candidates are megabytes. Sending the small
    thing to the data beats pulling the data to the small thing, and it is what
    makes an axis pass over hundreds of frames affordable.

    Both sides are L2-normalised at write, so `dotProduct` IS cosine here. Stated
    rather than assumed: `normalized` is in the key precisely so a future
    unnormalised row cannot be pooled with these.
    """
    import numpy as np
    from .slot_axis import NAMESPACE, sep_for
    v = np.asarray(seed, dtype=np.float32).reshape(-1)
    n = float(np.linalg.norm(v))
    if n:
        v = v / n
    esc = lambda s: s.replace("\\", "\\\\").replace("'", "\\'")
    seed_sql = "[" + ",".join("%.8f" % float(x) for x in v) + "]"
    where = ("embedder = '%s' AND revision = '%s' AND sep = '%s' AND normalized = 1 "
             "AND prompt = '%s'" % (esc(embedder or NAMESPACE), UNPINNED,
                                   esc(sep_for(prompt)), esc(prompt)))
    if words:
        where += " AND word IN (%s)" % ",".join("'%s'" % esc(w) for w in words)
    q = ("SELECT word, dotProduct(vec, CAST(%s AS Array(Float32))) AS s "
         "FROM {db}.%s WHERE %s FORMAT TabSeparated" % (seed_sql, TABLE, where))
    out = {}
    for line in ch.raw(q).strip().splitlines():
        if not line.strip():
            continue
        w, s = line.rsplit("\t", 1)
        out[w] = float(s)
    return out


def ingest_stash(limit=0, verbose=True):
    """Copy the legacy hashstash vectors into ClickHouse. -> dict

    **RECONSTRUCTS THE KEY RATHER THAN PARSING IT.** The legacy store is keyed on
    the fused string `prompt + sep + word`, which cannot be split back apart --
    the separator is a space and prompts end in spaces. So this does not read the
    stash's keys at all: it takes candidate `(prompt, word)` pairs from
    `twp_words`, builds the string each one WOULD have, and probes. A hit is
    copied; a miss is left for lazy embedding.

    That turns an unparseable key from fatal into merely inelegant, and it means
    the ingest covers exactly the pairs the store can be asked about.
    """
    import numpy as np
    from . import slot_axis as A
    st = A._stash()
    if st is None:
        raise SystemExit("legacy stash unavailable -- see slot_axis._stash's warning")
    create()
    q = ("SELECT DISTINCT prompt, word FROM {db}.twp_words"
         + (" LIMIT %d" % limit if limit else "") + " FORMAT TabSeparated")
    pairs = []
    for line in ch.raw(q).strip().splitlines():
        if "\t" not in line:
            continue
        p, w = line.rsplit("\t", 1)
        pairs.append((p, w))
    if verbose:
        print("candidate (prompt, word) pairs from twp_words: %d" % len(pairs))

    by_prompt = {}
    for p, w in pairs:
        by_prompt.setdefault(p, []).append(w)
    hit = miss = 0
    buf = []
    for i, (p, ws) in enumerate(sorted(by_prompt.items()), 1):
        sep = A.sep_for(p)
        vs, hits = [], []
        for w in ws:
            v = None
            for probe in (A.vec_key(p, w), "%s%s%s" % (p, sep, w)):
                try:
                    v = st.get(probe)
                except Exception:
                    v = None
                if v is not None:
                    break
            if v is None:
                miss += 1
                continue
            hits.append(w)
            vs.append(np.asarray(v, dtype=np.float32).reshape(-1))
        if hits:
            buf.extend(_rows(p, hits, vs, A.NAMESPACE, "stash-ingest"))
            hit += len(hits)
        if len(buf) >= CHUNK:
            ch.insert(TABLE, buf[:CHUNK])
            buf = buf[CHUNK:]
        if verbose and i % 200 == 0:
            print("  %d/%d prompts   copied %d   absent %d"
                  % (i, len(by_prompt), hit, miss), flush=True)
    while buf:
        ch.insert(TABLE, buf[:CHUNK])
        buf = buf[CHUNK:]
    out = {"pairs_considered": len(pairs), "copied": hit, "absent_from_stash": miss,
           "prompts": len(by_prompt)}
    if verbose:
        print("\n%s" % out)
    return out


def stats():
    """Row counts by embedder/revision. -> str"""
    if not ch.exists(TABLE):
        return "%s does not exist -- run --create" % TABLE
    return ch.raw(
        "SELECT embedder, revision, sep, normalized, count() AS rows, "
        "any(dims) AS dims FROM {db}.%s GROUP BY embedder, revision, sep, "
        "normalized ORDER BY rows DESC FORMAT TabSeparated" % TABLE)


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--create", action="store_true")
    ap.add_argument("--drop", action="store_true", help="with --create, recreate")
    ap.add_argument("--ingest-stash", action="store_true", dest="ingest")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--stats", action="store_true")
    a = ap.parse_args(argv)
    if a.create:
        print("created", create(drop=a.drop))
    if a.ingest:
        ingest_stash(limit=a.limit)
    if a.stats or not (a.create or a.ingest):
        print(stats())
    return 0


if __name__ == "__main__":
    sys.exit(main())
