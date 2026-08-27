"""Score every passage on every norm and every field. The wide net.

    python .../measure.py --corpus quadrants          # 14,414, ~15 min
    python .../measure.py --corpus ch --workers 8     # 1,523,368, ~3.3 h
    python .../measure.py --corpus ch --limit 5000    # smoke

Writes one parquet row per passage: identity, then every key
`fields.norms()` and `fields.count()` emit. **The goal is exploratory** -- cast
the net wide and see what separates the arms -- so nothing is dropped for being
uninteresting and the registered hypotheses are a subset of what comes out.

## TWO CORPORA, AND WHY BOTH

    quadrants   14,414 narrative-coded passages: 53 open models both arms, ELEVEN
                API endpoints, and 3,000 human passages from six corpora. Small,
                filtered, and the only one carrying an API arm or a human floor.
    ch          1,523,368 passages from `malign_logits.gen_sequences`: every
                corpus whose rows are actually passages. Unfiltered, 84 models,
                and large enough that a per-arm difference of 0.01 is resolvable.

The narrative corpus is where an effect can be interpreted; the big one is where
it can be detected. A finding that appears in one and not the other is a finding
about filtering, which is worth knowing either way.

## `beam_fc` IS EXCLUDED AND IT IS THE BIGGEST TABLE

1,636,400 rows, and a median of **39 characters / 10 tokens**. They are
ten-token beam continuations, not passages: M04's spec says "beam text is the
mode rather than a sample", and a valence mean over ten tokens measures the
prompt. Including it would have doubled the run and halved its meaning.

`passage_run2` is SmolLM2-360M measured twice -- every key exactly twice per
M06's population note -- so it is deduplicated on (model, prompt, sample_idx)
rather than counted as 29,504 independent passages.

## WHAT IS STORED, AND WHY NOT A SUMMARY

Every key, per passage, unaggregated. The contrast is computed later and
downstream, because the unit for an arm claim is the model and the pairing is by
lineage -- decisions that belong to the analysis and not to the scorer. A
producer that wrote per-model means would have made them for it.

Coverage keys ride on every row. They are the denominators, they differ by
source by design, and they are EXPECTED to differ by arm: proper nouns are not
in the norms and NNP runs about 7 per 1000 words lower in the aligned arm.
"""

import argparse, collections, csv, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
JAK = os.path.abspath(os.path.join(HERE, "..", "jakobson_space"))
#: 94 shards, 237 MB. Data, not source -- same root and shape as `novel_arc/`
#: and `drift_geometry/`. `contrast.py` resolves the same path and falls back
#: to the pre-move `results/norms_ch/` if a checkout still has it there.
DATA = os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data"))

#: passage-length corpora only. See the docstring on beam_fc.
CH_CORPORA = ("passage", "f11_l2", "y", "passage_run2")

#: **SET BEFORE ANY malignment IMPORT.** `ch.py` resolves its target database at
#: IMPORT time, so setting this inside a function runs after the constant is
#: already bound and every `{db}` still expands to `malignment` -- which is our
#: database, does not hold `gen_sequences`, and fails with UNKNOWN_TABLE rather
#: than reading the wrong rows. Loud, but only because the two databases happen
#: not to share a table name.
os.environ.setdefault("MALIGNMENT_CH_DB", "malign_logits")


def _chunk(jobs):
    """[(id, corpus, model, arm, prompt, text)] -> [flat row]. Runs in a worker.

    A CHUNK rather than one job, because the cost here is spaCy's tagger and
    `nlp.pipe` amortises it across documents. Per core this is ~86 passages/s
    against ~21 for the per-passage path that called `norms()` and `count()`
    separately -- two parses each, and the parse is 75% of the work.
    """
    from malignment import fields
    rows = []
    texts = [j[5] for j in jobs]
    #: the batch is generated lazily and a raising passage would abandon the
    #: rest of the chunk, so each is guarded and MARKED -- never silently
    #: absent, which would shrink a denominator nobody is watching.
    it = fields.all_batch(texts)
    for j in jobs:
        pid, corpus, model, arm, prompt, _ = j
        row = {"id": pid, "corpus": corpus, "model": model, "arm": arm,
               "prompt": prompt}
        try:
            row.update(next(it))
        except StopIteration:
            row["error"] = "batch ended early"
        except Exception as e:
            row["error"] = "%s: %s" % (type(e).__name__, str(e)[:80])
        rows.append(row)
    return rows


def _one(job):
    """One job, unbatched. Kept for callers that want a single passage."""
    from malignment import fields
    pid, corpus, model, arm, prompt, text = job
    row = {"id": pid, "corpus": corpus, "model": model, "arm": arm,
           "prompt": prompt}
    try:
        row.update(fields.all_fields(text))
    except Exception as e:
        row["error"] = "%s: %s" % (type(e).__name__, str(e)[:80])
    return row


def jobs_quadrants(limit=None):
    csv.field_size_limit(10 ** 7)
    src = os.path.join(JAK, "results", "quadrants.csv")
    out = []
    for r in csv.DictReader(open(src, newline="")):
        out.append((r["id"], "quadrants", r["model"] or r["category"],
                    r["category"], r["prompt"], r["text"]))
        if limit and len(out) >= limit:
            break
    return out


#: ## FORCED_WORD: THE CORPUS IS FREE GENERATION ONLY, AND THE FIRST RUN WAS NOT
#:
#: `gen_sequences` mixes free continuations with FORCED-WORD generations, where
#: a chosen word is inserted into the continuation. Over the four passage
#: corpora that is 904,345 + 104,300 + 23,488 forced rows against 490,882 free
#: ones -- 79% of the store -- with 1,458 distinct forced words in `passage`
#: alone. Those texts have had their lexical content manipulated by design, and
#: lexical content is exactly what `fields.norms()` and `fields.count()`
#: measure, so including them measures the stimulus rather than the arm.
#:
#: The first run did not filter them, and its dedup key
#: `(corpus, model, prompt, sample_idx)` does not separate a free row from the
#: forced rows sharing its prompt: 1,523,015 rows collapse to 490,890 groups,
#: and `if k in seen: continue` kept whichever row the unordered scan returned
#: first. That is an arbitrary and non-reproducible choice between a free
#: continuation and a forced one, made silently, on 68% of the store.
#:
#: Under `forced_word = ''` the same key is EXACTLY unique -- 490,882 rows,
#: 490,882 keys -- so the filter is what makes the unit well defined and the
#: dedup a no-op. `prompt` here is the 60-char truncated column; `prompt_full`
#: exists beside it and is emptier, which is why the truncated one is the
#: better key and why neither is unique without the filter.


def ch_models():
    """[(model, n_rows)] over the passage corpora, biggest first."""
    from malignment import ch
    return [(r["model"], r["n"]) for r in ch.query("""
        SELECT model, count() AS n FROM {db}.gen_sequences
        WHERE corpus IN (%s) AND length(text) > 0 AND forced_word = ''
        GROUP BY model ORDER BY n DESC
    """ % ", ".join("'%s'" % c for c in CH_CORPORA))]


def jobs_ch_model(model, arm, limit=None):
    """One model's passages. -> [job]

    **FETCHED PER MODEL, NOT IN ONE QUERY.** The first version asked for all
    1,523,368 rows at once and `ch.query` raised on an unterminated JSON line
    partway through -- about 1.6 GB of text through a single pipe. That raise is
    the module working as designed (it refuses to skip a line it cannot parse
    rather than dropping rows silently), meeting a fetch that was simply too
    large. Per-model chunks are 40k rows at the worst, and sharding the output
    the same way makes the run resumable.
    """
    from malignment import ch
    lim = " LIMIT %d" % limit if limit else ""
    rows = ch.query("""
        SELECT corpus, prompt, toString(sample_idx) AS si, text
        FROM {db}.gen_sequences
        WHERE corpus IN (%s) AND length(text) > 0 AND forced_word = ''
          AND model = '%s'
        %s
    """ % (", ".join("'%s'" % c for c in CH_CORPORA), model, lim))
    seen, out, dup = set(), [], 0
    for r in rows:
        k = (r["corpus"], model, r["prompt"], r["si"])
        if k in seen:
            dup += 1
            continue
        seen.add(k)
        out.append(("%s|%s|%s|%s" % k, r["corpus"], model, arm,
                    r["prompt"], r["text"]))
    #: the key is UNIQUE under the free-generation filter, so this must never
    #: fire. It is kept as an assertion rather than removed because the earlier
    #: version relied on it silently -- see the note above `FORCED_WORD`.
    if dup:
        raise ValueError("%s: key collided %d times under forced_word='' -- "
                         "the identity key is wrong, do not dedup past it"
                         % (model, dup))
    return out


def _run_ch(a, t0, pa, pq):
    """Model by model, one parquet shard each. Resumable by construction."""
    from malignment import roster
    lin = roster.lineages()
    arm = {}
    for base, members in lin.items():
        for m in members:
            arm[m] = "base" if m == base else "aligned"
    outdir = a.out or os.path.join(DATA, "passage_norms", "norms_ch")
    os.makedirs(outdir, exist_ok=True)
    models = ch_models()
    print("%d models, %s passages total" % (len(models),
          "{:,}".format(sum(n for _, n in models))), flush=True)
    import multiprocessing as mp
    pool = mp.Pool(a.workers) if a.workers > 1 else None
    done_n = 0
    for mi, (model, n_rows) in enumerate(models, 1):
        safe = model.replace("/", "__").replace("@", "__at__")
        fp = os.path.join(outdir, safe + ".parquet")
        if os.path.exists(fp):
            print("  [%d/%d] %-44s cached" % (mi, len(models), safe[:44]), flush=True)
            done_n += n_rows
            continue
        jobs = jobs_ch_model(model, arm.get(model, ""), a.limit)
        CH_SZ = 200
        chunks = [jobs[i:i + CH_SZ] for i in range(0, len(jobs), CH_SZ)]
        rows = ([r for part in pool.imap_unordered(_chunk, chunks) for r in part]
                if pool else [r for c in chunks for r in _chunk(c)])
        keys = sorted({k for r in rows for k in r})
        pq.write_table(pa.table({k: [r.get(k) for r in rows] for k in keys}),
                       fp, compression="zstd")
        done_n += len(rows)
        el = time.time() - t0
        print("  [%d/%d] %-44s %6s rows  %.0f/s  eta %.1f h"
              % (mi, len(models), safe[:44], "{:,}".format(len(rows)),
                 done_n / el, max(0, (sum(x for _, x in models) - done_n))
                 / max(done_n / el, 1) / 3600), flush=True)
    if pool:
        pool.close(); pool.join()
    print("-> %s  (%s passages, %.1f min)"
          % (outdir, "{:,}".format(done_n), (time.time() - t0) / 60))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", choices=("quadrants", "ch"), required=True)
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    import pyarrow as pa, pyarrow.parquet as pq

    t0 = time.time()
    if a.corpus == "ch":
        return _run_ch(a, t0, pa, pq)
    jobs = jobs_quadrants(a.limit)
    print("%s: %s passages" % (a.corpus, "{:,}".format(len(jobs))), flush=True)
    out = a.out or os.path.join(HERE, "results", "norms_%s.parquet" % a.corpus)

    rows = []
    if a.workers > 1:
        import multiprocessing as mp
        with mp.Pool(a.workers) as pool:
            for i, r in enumerate(pool.imap_unordered(_one, jobs, chunksize=200), 1):
                rows.append(r)
                if i % 20000 == 0:
                    el = time.time() - t0
                    print("  %s / %s  %.0f/s  eta %.1f h"
                          % ("{:,}".format(i), "{:,}".format(len(jobs)), i / el,
                             (len(jobs) - i) / (i / el) / 3600), flush=True)
    else:
        for i, j in enumerate(jobs, 1):
            rows.append(_one(j))
            if i % 2000 == 0:
                el = time.time() - t0
                print("  %s / %s  %.0f/s" % ("{:,}".format(i),
                      "{:,}".format(len(jobs)), i / el), flush=True)

    #: union of keys -- sources differ in which categories a passage triggers,
    #: so a fixed schema would either drop columns or invent zeros. Absent
    #: means the category did not appear, which is NOT the same as a rate of 0
    #: for a source the passage had no coverage in at all.
    keys = sorted({k for r in rows for k in r})
    tbl = pa.table({k: [r.get(k) for r in rows] for k in keys})
    os.makedirs(os.path.dirname(out), exist_ok=True)
    pq.write_table(tbl, out, compression="zstd")
    n_err = sum(1 for r in rows if r.get("error"))
    print("-> %s  (%s rows, %d columns, %d errors, %.1f min)"
          % (out, "{:,}".format(len(rows)), len(keys), n_err,
             (time.time() - t0) / 60))


if __name__ == "__main__":
    main()
