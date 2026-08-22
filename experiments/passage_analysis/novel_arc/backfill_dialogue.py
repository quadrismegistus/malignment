"""Add `dialogue_share` to tables scored before it existed.

    python .../backfill_dialogue.py --corpus chadwyck
    python .../backfill_dialogue.py --corpus chicago --workers 8

Writes `<corpus>_dialogue.parquet` keyed (text_id, seq), to be joined onto the
main table. Does NOT rescore: no lexicons, no spaCy, no norm tables loaded, so
it costs a re-chunk and a character scan rather than a full pass.

## WHY A JOIN AND NOT A RE-RUN

`t.passages(n=...)` is deterministic -- same text, same n, same sentence
accumulation -- so `(text_id, seq)` identifies the same span across runs and the
join is exact. Re-running the full scorer to add one cheap column would cost 22
minutes on chicago against roughly two here.

**The join must be VERIFIED, not assumed.** If lltk's chunker or the underlying
txt changed between runs the keys would still line up while pointing at
different spans, which is a silent corruption rather than a failed join. This
carries `n_tokens` for exactly that reason: it is already in the main table, and
a mismatch on it means the spans moved.
"""

import argparse, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
DATA = os.path.join(os.environ.get("MALIGNMENT_DATA",
                                   os.path.expanduser("~/malignment-data")),
                    "novel_arc")


def one_text(job):
    tid, corpus, n = job
    from measure_lltk import _dialogue, TOK
    import lltk
    C = lltk.Corpus(corpus)
    out = []
    try:
        for seq, p in enumerate(C.text(tid).passages(n=n).texts()):
            txt = p.txt
            raw = TOK.findall(txt)
            if not raw:
                continue
            out.append({"text_id": tid, "seq": seq,
                        "dialogue_share": _dialogue(txt),
                        "n_tokens_check": len(raw)})
    except Exception:
        pass
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="chadwyck")
    ap.add_argument("-n", type=int, default=200)
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args(argv)
    import pyarrow as pa, pyarrow.parquet as pq
    src = os.path.join(DATA, "%s_n%d.parquet" % (a.corpus, a.n))
    ids = sorted(set(pq.read_table(src, columns=["text_id"])
                     .column("text_id").to_pylist()))
    print("%d texts to re-chunk from %s" % (len(ids), os.path.basename(src)),
          flush=True)
    jobs = [(t, a.corpus, a.n) for t in ids]
    t0 = time.time()
    if a.workers > 1:
        import multiprocessing as mp
        pool = mp.get_context("spawn").Pool(a.workers)
        it = pool.imap_unordered(one_text, jobs, chunksize=4)
    else:
        pool, it = None, (one_text(j) for j in jobs)
    rows, done = [], 0
    for part in it:
        rows += part
        done += 1
        if done % 500 == 0:
            print("  [%d/%d] %s rows  %.1f min"
                  % (done, len(jobs), "{:,}".format(len(rows)),
                     (time.time() - t0) / 60), flush=True)
    if pool:
        pool.close(); pool.join()
    keys = ["text_id", "seq", "dialogue_share", "n_tokens_check"]
    fp = os.path.join(DATA, "%s_dialogue.parquet" % a.corpus)
    pq.write_table(pa.table({k: [r[k] for r in rows] for k in keys}), fp,
                   compression="zstd")
    print("-> %s  (%s rows, %.1f min)"
          % (fp, "{:,}".format(len(rows)), (time.time() - t0) / 60))


if __name__ == "__main__":
    main()
