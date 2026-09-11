#!/usr/bin/env python
"""Line closure from the twp jsonl into `twp_closure`. The words ingest is untouched.

    python scripts/ingest_closure.py --dry-run
    python scripts/ingest_closure.py --write
    python scripts/ingest_closure.py --write --source raw/rhyme4090

## WHY A SIDECAR AND NOT A COLUMN

`twp_words` is `(model, prompt, word, p, n_paths, source, mtime)`. A `p_close`
column there would be NULL on 37M rows for a quantity defined only at verse
slots, and `twp_cells` is cell metadata with no per-word grain at all. So closure
gets its own table, keyed the same way, and `malignment/ingest.py` needs NO
change: its include predicate wants `rule_version` + `rows` + `residual` and
ignores unknown top-level keys.

**It reads the SAME FILES the words ingest reads.** Closure rides as one extra
key on the ordinary record, so a cell and its closure cannot arrive separately,
cannot be rsynced separately, and cannot be forgotten separately. The `.f16`
tier is the counter-example this avoids: 59 GiB collected, paid for, and holding
zero live readers because nothing downstream could reach it.

## ABSENCE IS NOT ZERO, ON TWO AXES, AND `k_rider` IS WHY IT TRAVELS

    only DECLARED prompts carry closure   the verse slot manifest, ~1,786 of
                                          a model's ~4,400 measured prompts
    only the top K=40 SURFACES per cell   a cell holds 80-150 words; 40 are
                                          scored

So a word absent from `twp_closure` was NOT MEASURED AT ZERO, it was not
measured. `k_rider` and `n_scored` travel on every row so a consumer can tell
those apart without joining back to the jsonl. This is the same failure the
lineage-union topup pass exists to prevent -- a word a sibling cleared and this
model did not, which a consumer would otherwise impute as zero.

`n_scored < k_rider` is normal and is not loss: a rider word whose tokenisation
exceeds `closure.MAX_WORD_TOKENS` is dropped rather than scored short, because a
truncated word is a different word and its closure is a different quantity.

## THE NaN GATE FIRED ON ITS FIRST REAL DATA, AND THE PATTERN IS NOT THE OBVIOUS ONE

First cloud run, SmolLM2-360M on an RTX 4090 at float16: **24 NaN closures of
61,169 values (0.039%), in 10 of 1,621 cells.** Refused, not stored, and caught
only because `p != p` is tested explicitly -- every comparison against NaN is
False, so a range check alone (`0.0 <= p <= 1.0`) passes nothing and rejects
nothing, which is how two NaN cells once cleared a conservation gate built
entirely from inequalities.

**They cluster on the SHORTEST contexts, not the longest**: affected cells have a
median context of 11 characters against 86 for all cells. So this is not the
accumulate-with-length overflow that Falcon-H1's all-NaN failure was. The likely
mechanism is the rider's padded batch -- a very short context beside a multi-token
rider word leaves rows that are mostly pad, and a fully-masked attention row
softmaxes to NaN. Recorded rather than fixed: 0.04% is not worth a producer change
before the real fleet says whether it reproduces at other sizes and dtypes.

## WHAT IS NOT STORED, DELIBERATELY

Neither `line_closure` nor `rhyme_given_closure` nor `close_given_class`. Those
are RATIOS over a rime class, and a stored ratio bakes the class in -- which
would put the phonology at measurement time and make a rime-key revision
unrecoverable without re-running the model. There has already been one such
revision: v1 fell back to syllable SPELLING and shattered /ei/ into ay/ey/eigh.
The derivation runs one way; all three ratios follow from (rows, closure.words,
manifest) and none of them recovers the others.
"""
import argparse
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, ROOT)

STASH = os.path.expanduser("~/malignment-data/twp/*/*/jsonl.hashstash.raw/data.jsonl")

DDL = """CREATE TABLE IF NOT EXISTS {db}.twp_closure (
  model String,
  prompt String,
  word String,
  p_close Float32,
  k_rider UInt16,
  n_scored UInt16,
  rule_version UInt16,
  source LowCardinality(String),
  mtime DateTime
) ENGINE = ReplacingMergeTree(mtime) ORDER BY (model, prompt, word)"""


def records(pattern=None):
    """-> every stored record carrying a `closure` key, with its file's source."""
    for path in sorted(glob.glob(pattern or STASH)):
        #: the source label mirrors the words ingest: the producer directory
        #: two levels up, which is how a box's output is told from a Mac's.
        src = "raw/" + os.path.basename(os.path.dirname(os.path.dirname(path)))
        mtime = os.path.getmtime(path)
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                if '"closure"' not in line:
                    continue                      # cheap pre-filter, not a gate
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                v = d.get("_value") or d
                if not isinstance(v, dict) or "closure" not in v:
                    continue
                yield v, src, mtime


def rows(pattern=None, source=None):
    seen, n_cells, n_err = set(), 0, 0
    for v, src, mtime in records(pattern):
        c = v["closure"]
        words = c.get("words") or {}
        if not words:
            n_err += 1
            continue
        n_cells += 1
        k, ns, rv = c.get("k", 0), c.get("n_scored", len(words)), v.get("rule_version", 0)
        for w, p in words.items():
            #: **A CLOSURE OUTSIDE [0,1] IS NOT A PROBABILITY AND IS REFUSED.**
            #: The producer sums a softmax over a token subset, so the only ways
            #: out of range are a NaN or a corrupted read -- and `p != p` is
            #: tested explicitly because every comparison against NaN is False,
            #: which is how two NaN cells once passed a conservation gate built
            #: from inequalities.
            if p is None or p != p or not (0.0 <= p <= 1.0):
                n_err += 1
                continue
            key = (v["model"], v["prompt"], w)
            if key in seen:
                continue
            seen.add(key)
            yield {"model": v["model"], "prompt": v["prompt"], "word": w,
                   "p_close": float(p), "k_rider": int(k), "n_scored": int(ns),
                   "rule_version": int(rv), "source": source or src,
                   "mtime": int(mtime)}
    rows.stats = {"cells": n_cells, "refused": n_err}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--dry-run", action="store_true", default=True)
    ap.add_argument("--source", default=None, help="override the derived label")
    ap.add_argument("--glob", default=None)
    a = ap.parse_args(argv)

    out = list(rows(a.glob, a.source))
    st = getattr(rows, "stats", {})
    import collections
    by = collections.Counter(r["model"] for r in out)
    print("cells with closure  %d   refused %d" % (st.get("cells", 0), st.get("refused", 0)))
    print("word rows           %d over %d model(s)" % (len(out), len(by)))
    for m, n in by.most_common(8):
        print("   %-44s %7d" % (m, n))
    if not a.write:
        print("\n(dry run -- pass --write)")
        return 0
    from malignment import ch
    ch.execute(DDL.format(db=ch.DB))
    ch.insert("twp_closure", out)
    print("\nwrote %d rows to %s.twp_closure" % (len(out), ch.DB))
    return 0


if __name__ == "__main__":
    sys.exit(main())
