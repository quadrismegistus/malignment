#!/usr/bin/env python
"""Measure a checkpoint under v4's ADOPTED rules, through the PRODUCTION path.

    python scripts/run_v4.py --model Qwen/Qwen2.5-7B --cache

## A THIN WRAPPER, AND THE EARLIER VERSION WAS NOT

This file used to carry its own loop: its own model loading, its own record
shape, its own population, its own logging. Every one of those diverged from
`runners.py` and every divergence was a defect --

    record shape   folded `rows` to surfaces, discarding `t1`, and wrote no
                   `__key__`, so the output was invisible to the ingest
    population     read v3's OWN OUTPUT, so a prompt v3 skipped for a defect v4
                   FIXES could never be reached -- the internlm2 failure
                   `checkpoint.py` documents
    logging        to whatever /tmp file the launcher chose, rather than
                   `run.log` beside the data, which rsyncs with it

`Runner` takes a `rules` object now, so all of that comes for free and this file
is argument parsing. **Three times in one day I rebuilt a producer instead of
reusing one**; the fix was to make the shared one take a parameter.

## ORDERING

CJK first. v3's natural order put all 407 of Mistral's zh prompts last, so the
first informative cell would have arrived 117 minutes into a 138 minute run. The
rules only bite where the boundary rule does, so those cells go first and a
defect surfaces in minutes rather than hours.

## THE CACHE IS AN INSTRUMENT, NOT A SPEED KNOB

`--cache` is ~4.5x and NOT bit-identical: values move by up to 8.25e-04, which is
below THETA, so a word can cross the gate. It is therefore part of the KEY -- a
cached and an uncached cell are different measurements of one prompt and both are
kept. Do not mix them inside one corpus.
"""
import argparse
import os
import sys

from malignment import twp as T
from malignment import twp_v4 as V4
from malignment.checkpoint import Checkpoint
from malignment.prompts import Prompts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--cache", action="store_true",
                    help="prompt KV cache: ~4.5x, NOT bit-identical, part of the key")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--neighbours", action="store_true",
                    help="declared-neighbour prompts instead of every admitted one")
    a = ap.parse_args()

    #: set BEFORE the key is built -- `Checkpoint.key` reads it, so flipping it
    #: afterwards would stamp a cell with the wrong instrument.
    T.USE_PROMPT_CACHE = bool(a.cache)
    ck = Checkpoint(a.model)
    #: **THE TEE LIVES IN `runners.main()`, NOT IN `Runner.run()`.** So a caller
    #: reaching `run_twp` directly -- which this file does, and which was the
    #: whole point of becoming a thin wrapper -- gets NO run.log. I removed the
    #: one I had written on the assumption that `Runner` provided it, and
    #: committed a message saying logging now went beside the data at the moment
    #: it stopped doing so.
    #:
    #: `run.log` rsyncs with the data; a log in /tmp does not travel with the
    #: cells it describes.
    from malignment.runners import PRODUCER, _Tee
    logdir = os.path.join(ck.dir, PRODUCER)
    os.makedirs(logdir, exist_ok=True)
    tee = _Tee(os.path.join(logdir, "run_v4.log"))
    sys.stdout = tee
    prompts = (ck.neighbour_prompts() if a.neighbours
               else sorted({p.text for p in Prompts.all()}))
    prompts.sort(key=lambda p: not T.is_cjk(p))

    print("%s\n  rules=%s  cache=%s  prompts=%d (%d CJK first)"
          % (a.model, V4.ADOPTED.label(), bool(a.cache), len(prompts),
             sum(1 for p in prompts if T.is_cjk(p))), flush=True)
    try:
        return ck.run_twp(prompts, rules=V4.ADOPTED, limit=a.limit)
    finally:
        sys.stdout = tee.stream
        tee.close()


if __name__ == "__main__":
    print(main())
    sys.exit(0)
