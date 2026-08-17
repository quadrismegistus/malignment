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

#: **DDL GOES THROUGH `ch.execute`; DATA GOES THROUGH clickhouse-connect.** Not a
#: half-migration -- the split is the point. `ch._guard` refuses any statement
#: naming a database other than ours, and its docstring gives the reason: *"lltk
#: alone is 409 GiB on this daemon; a DROP is exactly the statement you want
#: refused."* A connect client bypasses that guard entirely, so the statements
#: worth guarding keep going through the guarded path.
#:
#: What connect buys is not speed -- embedding at ~55-99 vec/s is 25x slower than
#: any insert path, so the run time is unchanged. It buys PARAMETER BINDING. The
#: previous version escaped prompts into SQL with a hand-rolled `esc()` lambda,
#: and a prompt corpus full of apostrophes and backslashes is the worst possible
#: input for hand-rolled quoting.
_CLIENT = []


def client():
    """A clickhouse-connect client, or None. Never raises.

    Same contract as the old stash: a store that cannot be reached makes a run
    SLOWER, never wrong. Warns once rather than failing silently, because silence
    is right for a transient outage and wrong for a misconfiguration -- the lesson
    from `slot_axis._stash`, where a missing package left the cache off for a day.
    """
    if not _CLIENT:
        try:
            import clickhouse_connect
            _CLIENT.append(clickhouse_connect.get_client(
                host=os.environ.get("MALIGNMENT_CH_HOST", "localhost"),
                port=int(os.environ.get("MALIGNMENT_CH_PORT", 8123)),
                database=ch.DB))
        except Exception as e:
            print("vectors: clickhouse-connect unavailable (%s: %s); vectors will "
                  "be recomputed and not cached" % (type(e).__name__, e),
                  file=sys.stderr)
            _CLIENT.append(None)
    return _CLIENT[0]

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
    """Create the table. Idempotent unless `drop`.

    **`CODEC(NONE)` ON `vec` ONLY, and it is measured rather than received advice.**
    On 338,610 real rows the column compressed 1.24 GiB to 1.24 GiB -- ratio 0.998,
    so LZ4 was spending CPU on every read and write to make it marginally LARGER.
    Dense normalised float32 has no exploitable redundancy.
    #:
    **The other columns keep their codec, which is why this is per-column.**
    `prompt` compresses 162x (it repeats once per word of its slot) and `word`
    2.4x. A table-level `CODEC(NONE)` would have thrown that away.

    **THE CONSTRAINT IS THE POINT OF THE `dims` COLUMN, DONE PROPERLY.** `dims`
    RECORDS the length; a CHECK REFUSES a wrong one. Same distinction as an assert
    against a comment, and this seat has spent the day on the difference. All
    338,610 rows measured 1024 before it was added, so it is satisfiable rather
    than aspirational.
    """
    if drop:
        ch.execute("DROP TABLE IF EXISTS {db}.%s" % TABLE)
    ch.execute("""CREATE TABLE IF NOT EXISTS {db}.%s (
        embedder    LowCardinality(String),
        revision    LowCardinality(String),
        sep         LowCardinality(String),
        normalized  UInt8,
        prompt      String,
        word        String,
        vec         Array(Float32) CODEC(NONE),
        dims        UInt16,
        source      LowCardinality(String),
        created_at  DateTime DEFAULT now(),
        CONSTRAINT vec_len CHECK length(vec) = 1024
    ) ENGINE = ReplacingMergeTree
      ORDER BY (embedder, revision, sep, normalized, prompt, word)""" % TABLE)
    return TABLE


COLS = ("embedder", "revision", "sep", "normalized", "prompt", "word", "vec",
        "dims", "source")


def put(prompt, words, vecs, embedder=None, source="slot_axis"):
    """Insert vectors for one prompt. -> count

    Column-oriented through clickhouse-connect: no JSON encoding of 1024 floats
    per row, and no SQL string to escape.
    """
    from .slot_axis import NAMESPACE, sep_for
    cl = client()
    if cl is None:
        return 0
    emb, sep = embedder or NAMESPACE, sep_for(prompt)
    data = [[emb, UNPINNED, sep, 1, prompt, w, [float(x) for x in v],
             int(len(v)), source] for w, v in zip(words, vecs)]
    n = 0
    for i in range(0, len(data), CHUNK):
        cl.insert(TABLE, data[i:i + CHUNK], column_names=list(COLS))
        n += len(data[i:i + CHUNK])
    return n


def fetch(prompt, words, embedder=None):
    """Vectors already in ClickHouse for these words. -> {word: list[float]}

    One query for the whole prompt, never one per word: the measured 176 ms is
    fixed round-trip overhead, so 70 words cost what 1 does and 70 separate
    queries cost 70x.

    **PARAMETERS, NOT INTERPOLATION.** The prompt corpus is full of apostrophes
    and the previous version escaped them by hand into the SQL text.
    """
    from .slot_axis import NAMESPACE, sep_for
    cl = client()
    if cl is None or not words:
        return {}
    r = cl.query(
        "SELECT word, vec FROM " + TABLE + " WHERE embedder = {e:String} AND "
        "revision = {r:String} AND sep = {s:String} AND normalized = 1 AND "
        "prompt = {p:String} AND word IN {w:Array(String)}",
        parameters={"e": embedder or NAMESPACE, "r": UNPINNED,
                    "s": sep_for(prompt), "p": prompt, "w": list(words)})
    return {row[0]: row[1] for row in r.result_rows}


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
    A seed direction is 4 KB; the candidates are megabytes. Both sides are
    L2-normalised at write, so `dotProduct` IS cosine -- stated rather than
    assumed, which is why `normalized` sits in the key: an unnormalised row cannot
    be pooled with these.

    **This is a PROJECTION, not a nearest-neighbour search**, which is why there is
    no HNSW index and no `ORDER BY ... LIMIT`. It scores a named set of words on
    one prompt. An ANN index would need the distance function to match its
    declaration and would buy nothing here; brute force over ~1M rows measured
    ~12 s and is exact.
    """
    import numpy as np
    from .slot_axis import NAMESPACE, sep_for
    cl = client()
    if cl is None:
        return {}
    v = np.asarray(seed, dtype=np.float32).reshape(-1)
    n = float(np.linalg.norm(v))
    if n:
        v = v / n
    sql = ("SELECT word, dotProduct(vec, {q:Array(Float32)}) AS s FROM " + TABLE +
           " WHERE embedder = {e:String} AND revision = {r:String} AND "
           "sep = {s:String} AND normalized = 1 AND prompt = {p:String}")
    par = {"q": [float(x) for x in v], "e": embedder or NAMESPACE,
           "r": UNPINNED, "s": sep_for(prompt), "p": prompt}
    if words:
        sql += " AND word IN {w:Array(String)}"
        par["w"] = list(words)
    return {row[0]: float(row[1]) for row in cl.query(sql, parameters=par).result_rows}


def rows(sql, **params):
    """Read rows. JSON when there is nothing to bind, parameters when there is.

    **NEVER `ch.raw(... FORMAT TabSeparated)` FOR A STRING COLUMN.** TSV output is
    ESCAPED: a prompt comes back as `"He\\\\'d never seen ... \\\\nThey sprawled"`,
    with literal backslash-quote and backslash-n where the real string has an
    apostrophe and a newline. Feeding that back into `WHERE prompt = '...'` matches
    NOTHING, so the loop skips the prompt and reports success. Measured: 1,562 of
    4,484 prompts (35%) carry a quote, newline or backslash, and every one was being
    dropped silently.

    **THE RIGHT TOOL WAS ALREADY IN `ch.py` AND I REACHED PAST IT** (RH: "use JSON
    read instead of TSV"). `ch.query` is *"rows as dicts, via JSONEachRow. Types
    survive; escaping is not your problem"*, and `ch.raw`'s own docstring says
    *"prefer query -- if you reach for this with FORMAT TSV and then split on tabs,
    you have re-created defect (2)."* Two docstrings, both read earlier today.

    So the split, which is about which HALF of the escaping problem each side
    solves:

        no bound value   -> `ch.query`, JSON. Decodes strings correctly AND stays on
                            the guarded path, where `ch._guard` still refuses a
                            statement naming a foreign database.
        a string goes IN -> clickhouse-connect parameters. JSON fixes reading a
                            string OUT; it does nothing for interpolating one IN,
                            and hand-quoting a prompt full of apostrophes is the
                            other half of the same defect.

    Returns dicts either way, so callers do not care which path ran.
    """
    if not params:
        #: Qualify FROM/JOIN targets for `ch.query`, which needs `db.table`, while
        #: connect is already bound to the database and takes them bare. `{db}`
        #: cannot be used for both: connect would read it as a parameter
        #: placeholder. JOIN is in the pattern because `population_prompts` has
        #: one and a chained `.replace(" FROM ...")` silently missed it.
        import re as _re
        return ch.query(_re.sub(
            r"\b(FROM|JOIN)\s+(twp_words|prompts|slot_word_vec)\b",
            lambda m: "%s %s.%s" % (m.group(1), ch.DB, m.group(2)), sql))
    cl = client()
    if cl is None:
        raise SystemExit("clickhouse-connect unavailable; see vectors.client()")
    r = cl.query(sql, parameters=params)
    return [dict(zip(r.column_names, row)) for row in r.result_rows]


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

    **STREAMED PER PROMPT, NOT MATERIALISED.** The first version pulled all
    3,839,090 `(prompt, word)` pairs into a python list and then duplicated the
    references into a dict -- roughly a gigabyte of interpreter objects before any
    work began, on a box that happened to have 103 GB. `embed_population` was
    written to stream from the start and this was not; the difference only showed
    up as a risk I had to flag rather than a failure, which is the worst way to
    carry a defect. Now it asks for the prompt list, then each prompt's words in
    turn, and holds one prompt at a time.
    """
    import numpy as np
    from . import slot_axis as A
    st = A._stash()
    if st is None:
        raise SystemExit("legacy stash unavailable -- see slot_axis._stash's warning")
    create()
    #: ORDER BY, for the reason booked against `population_prompts`: an unordered
    #: DISTINCT means `--limit` selects a different population per invocation.
    plist = [r["prompt"] for r in rows(
        "SELECT DISTINCT prompt FROM twp_words ORDER BY prompt"
        + (" LIMIT %d" % limit if limit else ""))]
    if verbose:
        print("prompts to probe: %d" % len(plist), flush=True)
    hit = miss = skipped = 0
    for i, p in enumerate(plist, 1):
        ws = [r["word"] for r in rows(
            "SELECT DISTINCT word FROM twp_words WHERE prompt = {p:String} "
            "ORDER BY word", p=p)]
        if not ws:
            continue
        sep = A.sep_for(p)
        #: **ASK CLICKHOUSE FIRST, so a resume is free.** Without this the stage
        #: re-probed the stash and re-inserted everything it had already copied --
        #: 251,122 rows on the run that died at errno 28. ReplacingMergeTree would
        #: collapse the duplicates eventually, but "eventually" means carrying them
        #: on a volume that had just filled, and re-probing is wasted either way.
        #: `embed_population` was written this way from the start; this stage was
        #: not, and the disk failure is what exposed the difference.
        already = set(fetch(p, ws))
        todo = [w for w in ws if w not in already]
        if not todo:
            skipped += len(ws)
            continue
        skipped += len(already)
        vs, hits = [], []
        for w in todo:
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
            #: **ONE INSERT PATH.** This built rows by hand and sent them through
            #: ch.insert (JSONEachRow) while put() went through connect. Two
            #: encoders for one table is how two writers come to disagree about a
            #: column, so it goes through put() like everything else.
            put(p, hits, vs, source="stash-ingest")
            hit += len(hits)
        if verbose and i % 200 == 0:
            print("  %d/%d prompts   copied %d   absent %d   already had %d"
                  % (i, len(plist), hit, miss, skipped), flush=True)
    out = {"copied": hit, "absent_from_stash": miss,
           "already_in_ch": skipped, "prompts": len(plist)}
    if verbose:
        print("\n%s" % out)
    return out


#: The population RH asked for first (2026-08-17): his three live domains, plus the
#: two SOURCES that carry institutional relations under finer domain names --
#: M03 files them as labor/housing/medical/police/benefits/civic/banking/insurance/
#: immigration/utilities/consumer/education, so a domain-only filter misses 252
#: institutional frames entirely.
POPULATION = {
    "domains": ("sexual", "violence", "institutional"),
    "sources": ("M03_SPEAKER_KERNEL", "INSTITUTIONAL"),
}


def population_prompts(domains=None, sources=None):
    """Declared prompts in the population that have measured words. -> [str]"""
    d = domains if domains is not None else POPULATION["domains"]
    s = sources if sources is not None else POPULATION["sources"]
    where, par = [], {}
    if d:
        where.append("p.domain IN {dom:Array(String)}")
        par["dom"] = list(d)
    if s:
        where.append("p.source IN {src:Array(String)}")
        par["src"] = list(s)
    if not where:
        raise ValueError("give domains or sources")
    #: **`ORDER BY prompt`, AND IT IS NOT COSMETIC.** A `SELECT DISTINCT` with no
    #: ORDER BY returns rows in whatever order the read produced, so `[:limit]`
    #: selects a DIFFERENT SUBSET on each run. That is exactly the defect booked
    #: against `ch_read.prefetch` -- two runs of unchanged code differing on 4,051
    #: of 4,413 cells -- and it made the first resumability test compare two
    #: different populations and report a real feature broken.
    #:
    #: **AND IT GOES THROUGH `rows`, NOT `ch.raw(FORMAT TabSeparated)`** -- see that
    #: function. TSV output escapes strings, so prompts carrying a quote, backslash
    #: or newline came back mangled and matched nothing downstream. This query is
    #: where that entered the population run.
    return [r["prompt"] for r in rows(
        "SELECT DISTINCT w.prompt FROM twp_words w INNER JOIN prompts p "
        "ON p.prompt = w.prompt WHERE %s ORDER BY w.prompt" % " OR ".join(where),
        **par)]


def embed_population(domains=None, sources=None, limit=0, verbose=True):
    """Embed every unmeasured (prompt, word) in the population. -> dict

    **RESUMABLE BY CONSTRUCTION, because three hours is long enough to be
    interrupted.** Each prompt asks ClickHouse which of its words it already holds
    and embeds only the rest, so a re-run after a kill costs one query per prompt
    and no duplicate embedding. There is no checkpoint file to go stale.

    **IT DOES NOT USE `get`, DELIBERATELY.** `get` memoises into `slot_axis._MEM`,
    which is right for a session with one prompt on screen and fatal here: a
    million vectors at 4 KB is 4 GB of resident python by the end of the run. This
    embeds, inserts, and keeps nothing.

    Words are the UNION ACROSS EVERY MODEL that answered the prompt -- ~950 per
    prompt against the ~90 that clear theta for any one model -- because a vector
    is a property of the strings, so a store built for one pair would have to be
    rebuilt for the next.
    """
    import numpy as np
    from . import slot_axis as A
    create()
    prompts = sorted(population_prompts(domains, sources))
    if limit:
        #: Sliced AFTER sorting. Slicing an unordered list is what made --limit
        #: mean a different population on every invocation.
        prompts = prompts[:limit]
    done = new = skipped = 0
    t0 = __import__("time").time()
    for i, pr in enumerate(prompts, 1):
        words = [r["word"] for r in rows(
            "SELECT DISTINCT word FROM twp_words WHERE prompt = {p:String} "
            "ORDER BY word", p=pr)]
        if not words:
            continue
        have = set(fetch(pr, words))
        todo = [w for w in words if w not in have]
        skipped += len(have)
        if todo:
            sep = A.sep_for(pr)
            V = np.asarray(A._model().encode(
                ["%s%s%s" % (pr, sep, w) for w in todo],
                normalize_embeddings=True, show_progress_bar=False,
                batch_size=256), dtype=np.float32)
            put(pr, todo, V, source="population")
            new += len(todo)
        done += 1
        if verbose and (i % 10 == 0 or i == len(prompts)):
            el = __import__("time").time() - t0
            rate = new / el if el else 0
            left = (len(prompts) - i) / (i / el) / 3600 if i else 0
            print("  %d/%d prompts | embedded %d (%.0f vec/s) | already had %d | "
                  "~%.1f h left" % (i, len(prompts), new, rate, skipped, left),
                  flush=True)
    return {"prompts": done, "embedded": new, "already_present": skipped}


WORD_TABLE = "word_vec"


def create_words(drop=False):
    """The BARE-WORD table: one vector per word, no prompt, no separator.

    **A SEPARATE SPACE FROM `slot_word_vec`, AND THEY MUST NOT BE MIXED.** That table
    holds `prompt + sep + word`; this holds `word`. A cosine between one of each is
    meaningless, so they are different tables rather than a nullable column -- a NULL
    prompt would let a join produce exactly that silently.

    ## WHY IT EXISTS (RH, 2026-08-17)

    The in-frame validity check has a defect RH diagnosed better than I did: the
    panel's untagged candidates are, for a well-tagged item, *the irrelevant
    remainder* -- "when I tag I pretty much get every relevant word to the poles" --
    so the check gets WEAKER the better the tagging is. Demonstrated on
    `He told his boss he wanted to`: tagged `quit resign kill die`, its in-frame
    untagged extremes are `leave, retire, stop, change, switch`, indistinguishable
    from the same item tagged `quit resign leave`. The frame offers no death words,
    so the death direction is invisible from inside it.

    Scored against a WIDE vocabulary the same one-word change is unmistakable:

        quit,resign,kill,die   die, perish, died, resigned, depressed, killed, hanged
        quit,resign,leave      resigned, resign, forsake, divorce, renounce, 放弃

    So this is the held-out set the in-frame check cannot have, and it works for a
    prompt that has never been measured -- which is the case that matters while
    authoring.

    **BUILD THE AXIS FROM BARE POLE VECTORS TOO.** Mixing a prompt-conditioned axis
    with bare candidates compares across two spaces and returns plausible nonsense.
    """
    if drop:
        ch.execute("DROP TABLE IF EXISTS {db}.%s" % WORD_TABLE)
    ch.execute("""CREATE TABLE IF NOT EXISTS {db}.%s (
        embedder    LowCardinality(String),
        revision    LowCardinality(String),
        normalized  UInt8,
        word        String,
        vec         Array(Float32) CODEC(NONE),
        dims        UInt16,
        source      LowCardinality(String),
        created_at  DateTime DEFAULT now(),
        CONSTRAINT vec_len CHECK length(vec) = 1024
    ) ENGINE = ReplacingMergeTree
      ORDER BY (embedder, revision, normalized, word)""" % WORD_TABLE)
    return WORD_TABLE


WCOLS = ("embedder", "revision", "normalized", "word", "vec", "dims", "source")


def put_words(words, vecs, embedder=None, source="vocab"):
    """Insert bare-word vectors. -> count"""
    from .slot_axis import EMBEDDER
    cl = client()
    if cl is None:
        return 0
    emb = embedder or EMBEDDER
    data = [[emb, UNPINNED, 1, w, [float(x) for x in v], int(len(v)), source]
            for w, v in zip(words, vecs)]
    n = 0
    for i in range(0, len(data), CHUNK):
        cl.insert(WORD_TABLE, data[i:i + CHUNK], column_names=list(WCOLS))
        n += len(data[i:i + CHUNK])
    return n


def fetch_words(words, embedder=None):
    """Bare-word vectors already stored. -> {word: list[float]}"""
    from .slot_axis import EMBEDDER
    cl = client()
    if cl is None or not words:
        return {}
    r = cl.query(
        "SELECT word, vec FROM " + WORD_TABLE + " WHERE embedder = {e:String} AND "
        "revision = {r:String} AND normalized = 1 AND word IN {w:Array(String)}",
        parameters={"e": embedder or EMBEDDER, "r": UNPINNED, "w": list(words)})
    return {row[0]: row[1] for row in r.result_rows}


def embed_vocab(shard=0, n_shards=1, limit=0, batch=512, verbose=True):
    """Embed the distinct `twp_words` vocabulary, bare. -> dict

    **SHARDED BY `cityHash64(word) % n_shards`, so workers partition the vocabulary
    without coordinating.** Deterministic and balanced, and a worker re-run covers
    exactly its own slice again -- no shared cursor to corrupt.

    **PARALLELISM IS WORTH IT HERE AND THAT WAS MEASURED, not assumed.** One encode
    process uses ~243% CPU of 12 cores with the machine 55% idle, so the cores are
    not the binding constraint at N=1. ClickHouse takes concurrent inserts happily --
    each becomes a part and merges run in the background -- so the limit is CPU, and
    there is room for roughly four workers beside a running job.

    Resumable like the others: it asks what is already stored and embeds the rest.
    """
    import numpy as np
    from . import slot_axis as A
    create_words()
    q = "SELECT DISTINCT word FROM twp_words"
    if n_shards > 1:
        q += " WHERE cityHash64(word) %% %d = %d" % (n_shards, shard)
    q += " ORDER BY word" + (" LIMIT %d" % limit if limit else "")
    vocab = [r["word"] for r in rows(q)]
    if verbose:
        print("shard %d/%d: %d words" % (shard, n_shards, len(vocab)), flush=True)
    new = skipped = 0
    for i in range(0, len(vocab), batch):
        chunk = vocab[i:i + batch]
        have = fetch_words(chunk)
        todo = [w for w in chunk if w not in have]
        skipped += len(have)
        if todo:
            V = np.asarray(A._model().encode(
                todo, normalize_embeddings=True, show_progress_bar=False,
                batch_size=256), dtype=np.float32)
            put_words(todo, V)
            new += len(todo)
        if verbose and (i // batch) % 20 == 0:
            print("  shard %d: %d/%d  embedded %d  had %d"
                  % (shard, i + len(chunk), len(vocab), new, skipped), flush=True)
    return {"shard": shard, "n_shards": n_shards, "words": len(vocab),
            "embedded": new, "already": skipped}


FT_TABLE = "ft_word_vec"
FT_DIR = os.path.join(DATA if "DATA" in dir() else
                      os.environ.get("MALIGNMENT_DATA",
                                     os.path.expanduser("~/malignment-data")),
                      "vecs", "muse")


def create_ft(drop=False):
    """fastText aligned vectors: a THIRD space, en and zh in one alignment.

    **300 DIMENSIONS, NOT 1024, WHICH IS WHY IT IS ITS OWN TABLE AND ITS OWN
    CHECK.** Copying the working DDL from `word_vec` would have silently accepted
    300-element rows against a `length(vec) = 1024` constraint -- except it would
    have refused every row, which is the lucky direction. A table keyed on a
    different embedder with a different dimensionality cannot share either.

    ## WHAT IT IS FOR, AND WHAT IT IS NOT

    It answers ONE question the bge tables cannot: **is this pole word stable
    outside its frame?** bge conditions on the prompt, so in `She slowly took off
    her ___` it reads `glasses` correctly as eyewear. fastText has no frame, so it
    reads `glasses` as eyewear AND drinkware AND laboratory glass at once, and
    `bra` mostly as the country code for Brazil.

    **That is not a referee on bge.** For the in-frame measurement bge is right and
    fastText is wrong. What the disagreement identifies is a POLE WORD whose sense
    is unstable in general English -- which matters if the item is reused, or
    compared against a twin whose frame differs.

    Filtered to twp surfaces at load (RH, 2026-08-17), so candidates are words the
    models actually produce: 2.85M vocabulary down to ~112k rows. Note the filter
    cleans the CANDIDATES and cannot repair a polysemous SEED -- `bra` still means
    Brazil, and `ita/gre/arg/esp` survive the filter because models emit them.
    """
    if drop:
        ch.execute("DROP TABLE IF EXISTS {db}.%s" % FT_TABLE)
    ch.execute("""CREATE TABLE IF NOT EXISTS {db}.%s (
        embedder    LowCardinality(String),
        lang        LowCardinality(String),
        word        String,
        vec         Array(Float32) CODEC(NONE),
        dims        UInt16,
        source      LowCardinality(String),
        created_at  DateTime DEFAULT now(),
        CONSTRAINT vec_len CHECK length(vec) = 300
    ) ENGINE = ReplacingMergeTree ORDER BY (embedder, lang, word)""" % FT_TABLE)
    return FT_TABLE


FTCOLS = ("embedder", "lang", "word", "vec", "dims", "source")


def load_ft(lang="en", path=None, only_twp=True, verbose=True):
    """Stream a `.vec` file into ClickHouse, filtered to twp surfaces. -> dict"""
    cl = client()
    if cl is None:
        raise SystemExit("clickhouse-connect unavailable")
    create_ft()
    path = path or os.path.join(FT_DIR, "wiki.%s.align.vec" % lang)
    keep = None
    if only_twp:
        twp = {r["word"] for r in rows("SELECT DISTINCT word FROM twp_words")}
        keep = twp | {w.lower() for w in twp}
        if verbose:
            print("filtering to %d twp surfaces (exact + lowercased)" % len(keep),
                  flush=True)
    have = {r["word"] for r in rows(
        "SELECT word FROM ft_word_vec WHERE lang = '%s'" % lang)}
    buf, n, seen = [], 0, 0
    with open(path, encoding="utf-8", errors="replace") as fh:
        header = fh.readline().split()
        for line in fh:
            i = line.find(" ")
            w = line[:i]
            seen += 1
            #: The leading `</s>` sentinel is not a word.
            if w == "</s>" or (keep is not None and w not in keep) or w in have:
                continue
            p = line.rstrip("\n").split(" ")
            if len(p) != 301:
                continue
            buf.append(["fasttext-align", lang, w,
                        [float(x) for x in p[1:]], 300, "muse"])
            if len(buf) >= CHUNK:
                cl.insert(FT_TABLE, buf, column_names=list(FTCOLS))
                n += len(buf); buf = []
                if verbose and n % 20000 == 0:
                    print("  %s: %d loaded (%d lines scanned)" % (lang, n, seen),
                          flush=True)
    if buf:
        cl.insert(FT_TABLE, buf, column_names=list(FTCOLS))
        n += len(buf)
    return {"lang": lang, "declared": header[0], "scanned": seen, "loaded": n}


def ft_fetch(words, lang="en"):
    """fastText vectors for these words. -> {word: list[float]}"""
    cl = client()
    if cl is None or not words:
        return {}
    r = cl.query("SELECT word, vec FROM " + FT_TABLE +
                 " WHERE lang = {l:String} AND word IN {w:Array(String)}",
                 parameters={"l": lang, "w": list(words)})
    return {row[0]: row[1] for row in r.result_rows}


def cross_corpus(prompt, naughty, nice, k=8, min_prompts=8):
    """What this axis selects for across every OTHER measured frame. -> dict

    **THE HELD-OUT CHECK, and the only one of the three that reliably works.** The
    in-frame version is weak by construction: a well-tagged item leaves only the
    irrelevant words untagged, so it gets WEAKER as the tagging improves (RH's
    diagnosis). Demonstrated on `He told his boss he wanted to` tagged
    `quit resign kill die`, whose in-frame extremes are indistinguishable from the
    same item tagged `quit resign leave` -- the frame offers no death words, so the
    death direction is invisible from inside it. Across the corpus the same
    one-word change is unmistakable:

        quit,resign,kill,die   die, perish, died, resigned, killed, hanged
        quit,resign,leave      resigned, forsake, divorce, renounce, 放弃

    **EACH CANDIDATE PROMPT IS CENTRED ON ITS OWN MEAN**, because eta^2 is 0.764 --
    three quarters of a raw score is which frame the word sits in. The SEED needs no
    centring: it is a difference of two vectors sharing one prompt, so the frame
    component cancels (measured: each pole is 0.9885 aligned with the frame mean,
    their difference 0.0172).

    A word's score is averaged over the prompts it appears in, and `min_prompts`
    keeps a word that appears once out of a ranking that reads as lexical.
    """
    import numpy as np
    from . import slot_axis as A
    cl = client()
    if cl is None:
        return None
    seed = A.embed_cached(prompt, list(naughty)).mean(0) - \
        A.embed_cached(prompt, list(nice)).mean(0)
    seed = (seed / np.linalg.norm(seed)).astype(np.float32)
    q = ("WITH s AS (SELECT prompt, word, dotProduct(vec, {q:Array(Float32)}) AS raw "
         "FROM " + TABLE + " WHERE prompt != {p:String}), "
         "m AS (SELECT prompt, avg(raw) AS mu, count() AS n FROM s GROUP BY prompt "
         "HAVING n > 50) "
         "SELECT s.word AS w, avg(s.raw - m.mu) AS c, count() AS n FROM s "
         "INNER JOIN m ON m.prompt = s.prompt GROUP BY s.word "
         "HAVING n >= {mp:UInt32} ORDER BY c %s LIMIT {k:UInt32}")
    par = {"q": [float(x) for x in seed], "p": prompt, "mp": min_prompts, "k": k}
    out = {}
    for lab, order in (("naughty_end", "DESC"), ("nice_end", "ASC")):
        out[lab] = [{"word": w, "s": float(c), "prompts": int(n)}
                    for w, c, n in cl.query(q % order, parameters=par).result_rows]
    out["scored_prompts"] = cl.query(
        "SELECT uniqExact(prompt) AS n FROM " + TABLE).result_rows[0][0]
    return out


def pole_stability(naughty, nice, lang="en"):
    """Are these pole words stable in general English? -> dict

    **A DIFFERENT QUESTION FROM THE OTHER TWO, not a referee on them.** bge
    conditions on the prompt, so in `She slowly took off her ___` it reads
    `glasses` as eyewear and is RIGHT. fastText has no frame, so it reads `glasses`
    as eyewear and drinkware and laboratory glass at once, and `bra` mostly as the
    country code for Brazil. For the in-frame measurement bge wins every time.

    What the disagreement identifies is a pole word whose sense is UNSTABLE outside
    its frame -- which matters when an item is reused, or set against a twin whose
    wording differs. Reported as: which pole words are missing from a 2.5M-word
    vocabulary at all, and for those present, each word's nearest neighbours, since
    a word whose neighbours are country codes is telling you something.
    """
    import numpy as np
    cl = client()
    if cl is None:
        return None
    ws = [w for w in list(naughty) + list(nice)]
    got = ft_fetch(ws, lang) or ft_fetch([w.lower() for w in ws], lang)
    lower = {w.lower(): w for w in ws}
    got = {lower.get(k, k): v for k, v in got.items()}
    missing = [w for w in ws if w not in got]
    nb = {}
    for w in ws:
        if w not in got:
            continue
        v = np.asarray(got[w], dtype=np.float32)
        v = v / (np.linalg.norm(v) or 1.0)
        r = cl.query(
            "SELECT word, dotProduct(vec, {q:Array(Float32)}) AS s FROM " + FT_TABLE +
            " WHERE lang = {l:String} AND word != {w:String} ORDER BY s DESC LIMIT 5",
            parameters={"q": [float(x) for x in v], "l": lang, "w": w})
        nb[w] = [{"word": a, "s": float(b)} for a, b in r.result_rows]
    return {"lang": lang, "missing": missing, "neighbours": nb,
            "vocab": cl.query("SELECT count() AS n FROM " + FT_TABLE +
                              " WHERE lang = {l:String}",
                              parameters={"l": lang}).result_rows[0][0]}


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
    ap.add_argument("--embed-population", action="store_true", dest="pop",
                    help="embed RH's three domains + the institutional sources")
    ap.add_argument("--stats", action="store_true")
    a = ap.parse_args(argv)
    if a.create:
        print("created", create(drop=a.drop))
    if a.ingest:
        ingest_stash(limit=a.limit)
    if a.pop:
        print(embed_population(limit=a.limit))
    if a.stats or not (a.create or a.ingest or a.pop):
        print(stats())
    return 0


if __name__ == "__main__":
    sys.exit(main())
