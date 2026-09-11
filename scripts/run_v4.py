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
import json
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
    ap.add_argument("--frame", choices=["chat", "prefill"], default=None,
                    help="measure under a CHAT TEMPLATE. 'prefill' makes the "
                         "stem a started ASSISTANT turn (the next word "
                         "continues it); 'chat' makes it the USER turn (the "
                         "next word begins the answer). Omit for the raw, "
                         "untemplated surface, which is what every stored cell "
                         "before 2026-08-22 is.")
    #: **ABSENT IS NOT THE SAME AS EMPTY, AND THE DIFFERENCE IS MEASURED.**
    #: Omitting `--system` passes the DEFAULT sentinel: supply NO system
    #: message and let the template do whatever it ships with. `--system ""`
    #: passes an explicit empty string, which DELETES a shipped persona on the
    #: models that have one and ADDS an empty block on the models that do not
    #: -- two opposite operations under one label.
    #:
    #: **CORRECTED 2026-08-23: this said docs/prefill.md "rules against" `""`.
    #: It does not, and has not since the amendment on that page.** The current
    #: ruling is `system` is a FACTOR, not a constant: run `""` as the UNIFORM
    #: CONDITION and `DEFAULT` as a second cell on a subset. This comment was
    #: quoting the superseded first recommendation, and it would have told the
    #: next seat that the adopted arm was forbidden -- the pilot's 16 checkpoints
    #: and box A's 40 all ran `""`.
    #:
    #: What survives from the two-operations argument is why the two CANNOT BE
    #: POOLED (prefill.md, closing line), which is a different claim from `""`
    #: being wrong. `measurements.json` section chat_template carries
    #: `sys_empty_ok` per model.
    ap.add_argument("--system", default=None,
                    help="explicit system message. OMIT for the template's own "
                         "default; '' forces an empty one, which is NOT the same "
                         "thing and is the adopted uniform condition.")
    ap.add_argument("--user-msg", default="Hi.",
                    help="the user turn placed before a prefill stem")
    ap.add_argument("--topup", action="store_true",
                    help="PASS 2 instead of pass 1: score_words4 over the lineage "
                         "union. Lives here because this is the per-model entry "
                         "point the queue spawns with the model's OWN venv -- "
                         "topup_lineage.py ran everything in one interpreter and "
                         "died on OLMo-2's tie_word_embeddings at 27 of 72.")
    ap.add_argument("--root", default=None, help="lineage root for --topup")
    ap.add_argument("--from-stash", action="store_true",
                    help="pass 2 builds its union from the local stash, for a box "
                         "with no ClickHouse")
    ap.add_argument("--purge", action="store_true",
                    help="delete this model's HF cache BEFORE its download, so a "
                         "long queue does not accumulate weights. `twp.purge_model` "
                         "runs on every exit path including failure -- a model that "
                         "OOMs at load is the least worth keeping and used to be the "
                         "only one kept.")
    ap.add_argument("--prompts-json", default=None,
                    help="a JSON array of prompt strings. USE THIS FOR ANY "
                         "PROMPT CONTAINING A NEWLINE -- --prompts-file is one "
                         "per line and cannot hold one. Declares its own "
                         "population, so prompts outside Prompts.all() are "
                         "measured rather than refused; the count is printed.")
    ap.add_argument("--closure-file", default=None,
                    help="a JSON array of context strings at "
                         "which to ALSO measure line closure. The verse slot "
                         "manifest's contexts. PLAIN STRINGS -- nothing "
                         "phonological runs here; the rime classes are applied "
                         "offline. Costs a measured +27%% on the cells it fires "
                         "on and nothing on the rest.")
    ap.add_argument("--prompts-file", default=None,
                    help="explicit prompt list, one per line, EXACT text. Takes "
                         "precedence over --only. Added for dario's frame-level "
                         "ask: topup coverage is per-PROMPT, so a consumer whose "
                         "frames sit late in a sweep's order waits for the whole "
                         "sweep to reach them even though their cells cost minutes.")
    ap.add_argument("--only", choices=["slots", "cjk", "latin"], default=None,
                    help="measure one TRANCHE of the population instead of all "
                         "of it. See the note below on why the tranches differ "
                         "in value by an order of magnitude.")
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
    #: **A CHECKPOINT WITH NO LOCAL v3 CORPUS HAS NO STASH DIRECTORY**, and
    #: nothing upstream creates it: `Runner.run` makes `ck.dir` but the engine
    #: sits a level deeper. Every model I tested against was one of the nine that
    #: already had a local corpus, so this appeared only when the queue reached
    #: Baichuan2 -- a model measured on the fleet and never here. The load
    #: succeeded, the INSTRUMENT line printed, and it died on the first write.
    os.makedirs(os.path.dirname(ck.stash(PRODUCER).path), exist_ok=True)
    tee = _Tee(os.path.join(logdir, "run_v4.log"))
    sys.stdout = tee
    #: **THE POPULATION IS NOT ONE THING AND ITS PARTS ARE NOT WORTH THE SAME.**
    #: Measured 2026-08-18 over 81 models:
    #:
    #:     slots   277 prompts   22,437 cells    5.0 h   NEVER MEASURED at all
    #:     cjk     407 prompts   32,967 cells    7.3 h   the ONLY place v4 != v3
    #:     latin  2299 prompts  186,219 cells   41.4 h   v4 == v3 to the bit
    #:
    #: `decoded_boundary` tests the token as spelled, which only changes anything
    #: on byte-level CJK surfaces. So re-measuring 2,299 Latin prompts under v4
    #: reproduces v3 cells we already hold -- 76% of the runtime for the tranche
    #: that answers nothing new. Run `slots` then `cjk` and the two tranches that
    #: carry information are done in 12 h instead of 54.
    #:
    #: Kept as a flag rather than a reordering because "which prompts did this
    #: run cover" must stay answerable, and a silent priority sort makes a
    #: partial run indistinguishable from a complete one.
    if a.prompts_json:
        #: **A LINE-PER-PROMPT FILE CANNOT CARRY A MULTI-LINE PROMPT**, and the
        #: verse slot manifest is 1,608 multi-line contexts out of 1,786. Found
        #: locally 2026-09-11 before any box: escaping the newline makes the
        #: string arrive as a literal backslash-n, which is a DIFFERENT PROMPT
        #: that measures cleanly and joins nothing -- the same class of defect
        #: as reading ClickHouse TSV without unescaping, one transport along.
        #:
        #: The `--prompts-file` refusal below is deliberate and stays: a list
        #: that half-resolves is a request the caller did not make. This route
        #: DECLARES its population instead of being checked against the shared
        #: one, because injecting 1,786 verse prefixes into `Prompts.all()`
        #: would move every other consumer's denominator.
        prompts = list(json.load(open(a.prompts_json, encoding="utf-8")))
        _all = {p.text for p in Prompts.all()}
        print("  prompts   %d from %s (%d outside Prompts.all(), declared)"
              % (len(prompts), os.path.basename(a.prompts_json),
                 sum(1 for t in prompts if t not in _all)), flush=True)
    elif a.prompts_file:
        want = [l.rstrip("\n") for l in open(a.prompts_file, encoding="utf-8") if l.strip()]
        allp = {p.text for p in Prompts.all()}
        prompts = [t for t in want if t in allp]
        missing = [t for t in want if t not in allp]
        if missing:
            #: REFUSE rather than silently measure a subset. A prompt list that
            #: half-resolves is a request the caller did not make, and the caller
            #: is downstream where a missing cell reads as a measured zero.
            raise SystemExit("%d of %d prompts are not in the population: %s"
                             % (len(missing), len(want), missing[:3]))
    elif a.neighbours:
        prompts = ck.neighbour_prompts()
    else:
        allp = {p.text: p for p in Prompts.all()}
        if a.only == "slots":
            prompts = sorted(t for t, p in allp.items()
                             if str(getattr(p, "source", "")).startswith("SLOT"))
        elif a.only == "cjk":
            prompts = sorted(t for t in allp if T.is_cjk(t))
        elif a.only == "latin":
            prompts = sorted(t for t, p in allp.items()
                             if not T.is_cjk(t)
                             and not str(getattr(p, "source", "")).startswith("SLOT"))
        else:
            prompts = sorted(allp)
    prompts.sort(key=lambda p: not T.is_cjk(p))

    print("%s\n  rules=%s  cache=%s  tranche=%s  prompts=%d (%d CJK first)"
          % (a.model, V4.ADOPTED.label(), bool(a.cache), a.only or "ALL", len(prompts),
             sum(1 for p in prompts if T.is_cjk(p))), flush=True)
    try:
        if a.topup:
            from malignment.runners import TWPRunner
            return TWPRunner(ck).topup(rules=V4.ADOPTED, root=a.root,
                                       limit=a.limit, prompts=prompts,
                                       from_stash=a.from_stash)
        from malignment.generate import DEFAULT
        #: `closure_at` is a SET OF PROMPTS, not a flag: the rider is meaningless
        #: at a prompt that is not a line-final slot, and it costs +27% where it
        #: fires. Reading it here rather than deriving it on the box keeps the
        #: box free of the manifest's semantics -- it gets strings.
        _cl = None
        if a.closure_file:
            #: JSON for the same reason as --prompts-json: these strings
            #: contain newlines, and an escaped one is a different string.
            _cl = set(json.load(open(a.closure_file, encoding="utf-8")))
            print("  closure   %d context(s); %d of this run's %d prompts match"
                  % (len(_cl), sum(1 for x in prompts if x in _cl), len(prompts)),
                  flush=True)
        return ck.run_twp(prompts, rules=V4.ADOPTED, limit=a.limit,
                          frame=a.frame,
                          system=DEFAULT if a.system is None else a.system,
                          user_msg=a.user_msg, closure_at=_cl,
                          purge=a.purge)
    finally:
        sys.stdout = tee.stream
        tee.close()


if __name__ == "__main__":
    print(main())
    sys.exit(0)
