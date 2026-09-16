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
import time
import traceback
import sys

from malignment import twp as T
from malignment import twp_v4 as V4
from malignment.checkpoint import Checkpoint
from malignment.prompts import Prompts



def _resolved_env():
    """EVERY installed distribution, RESOLVED, not the constraint we asked for.

    **The corpus records resolved versions for exactly two packages and only on
    the success path.** `runners.run` stamps `transformers_version` and
    `torch_version` by reading `__version__` off the live interpreter -- which
    is the right thing -- but it builds that stamp AFTER `load_for_twp`
    returns, and it rides on the CELL. A model that dies at load writes no
    cells, so a failed run records no versions at all: internlm2's environment
    on 2026-09-11 had to be attributed from SIBLING models on the same box.

    And two packages is the wrong number. The package that broke internlm2 is
    `sentencepiece`, which no column, no stamp and no manifest field names.
    **The relevant package is by definition the one nobody thought to list**,
    so this takes the whole freeze rather than a curated set: a few KB, written
    beside the data, and a later failure becomes a DIFF against a working run
    instead of an argument about what the box probably had.
    """
    import importlib.metadata as _md
    pkgs = {}
    for dist in _md.distributions():
        try:
            nm = dist.metadata["Name"]
        except Exception:                                       # noqa: BLE001
            continue
        if nm:
            pkgs[nm.lower()] = dist.version
    return {"python": sys.version.split()[0], "executable": sys.executable,
            "packages": dict(sorted(pkgs.items()))}


def _declared_vs_resolved(model_id, pkgs):
    """The PIN beside the RESOLVED version, per declared package. -> dict

    lacan's rule, 2026-09-14: *a pin plus the resolved version is a diff; a pin
    alone is still a claim.* `roster/models/requirements.json` says what a
    checkpoint needs; this says what the interpreter actually has, and whether
    the two agree. Neither half is worth much without the other -- a manifest
    nothing checks is folklore, and a freeze with nothing to check it against
    is 160 lines nobody reads.

    `overridden_from` rides through untouched when the roster carries it, so a
    reader can tell a pin that was CHOSEN for this model from a default it
    INHERITED from its profile. Absent today; this does not synthesise one,
    because a fabricated provenance is worse than a missing one.

    Specifiers are PEP 440 and already compound in the roster (`>=4.57,<5`), so
    nothing here needs a grammar of its own.
    """
    out = {}
    try:
        import json as _j
        from packaging.specifiers import SpecifierSet
        from packaging.version import Version
        #: located from the PACKAGE, not from this file's path: run_v4.py is
        #: invoked from several working directories and a relative walk up from
        #: __file__ broke the moment the fleet ran it from /root/malignment.
        import malignment as _m
        _root = os.path.dirname(os.path.dirname(os.path.abspath(_m.__file__)))
        rq = _j.load(open(os.path.join(_root, "roster", "models",
                                       "requirements.json")))
        row = next((r for r in rq["requirements"] if r["model"] == model_id), None)
        if row is None:
            return {"_note": "no requirements row for %s" % model_id}
        #: `packages` is lacan's additive field and is read if present. The two
        #: that exist TODAY are checked the same way, so this mechanism is not
        #: waiting on a schema change to start being useful.
        want = {k: v for k, v in (row.get("packages") or {}).items()}
        for k in ("transformers", "torch"):
            if row.get(k):
                want.setdefault(k, row[k])
        for name, spec in sorted(want.items()):
            got = pkgs.get(name.lower())
            #: **A BARE REQUIREMENT IS A REAL REQUIREMENT, NOT A MISSING
            #: VALUE.** `einops: ''` in models.yaml means "required, any
            #: version" -- but an empty `specifier` in a JSON record reads as
            #: "nothing declared", which is the opposite. `required` is
            #: therefore always True for anything in this block, and the
            #: specifier is rendered `*` when it is bare. lacan, 2026-09-14.
            rec = {"specifier": spec or "*", "required": True, "resolved": got,
                   "overridden_from": row.get("overridden_from")}
            try:
                rec["satisfied"] = (
                    bool(got) and Version(got) in SpecifierSet(spec))
            except Exception:                                   # noqa: BLE001
                #: UNKNOWN, never True. An unparseable version is the state a
                #: silent pass would hide.
                rec["satisfied"] = None
            out[name] = rec
    except Exception as e:                                      # noqa: BLE001
        out["_error"] = "%s: %s" % (type(e).__name__, e)
    return out

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
    #: **BOTH SIDES OF THE DIFF, OR IT IS NOT A DIFF.** Written on every run,
    #: not only failing ones: a failed box's freeze is only legible against a
    #: working box's, and the working one is the half nobody thinks to keep.
    try:
        _env = _resolved_env()
        _env["declared"] = _declared_vs_resolved(a.model, _env["packages"])
        json.dump(_env, open(os.path.join(logdir, "ENV.json"), "w"), indent=1)
        #: **SAY IT IN THE LOG, NOT ONLY IN THE SIDECAR.** A mismatch buried in
        #: a 160-package JSON is a mismatch nobody reads; this is the line a
        #: `tail -f` shows and the line the next person greps for. It does NOT
        #: refuse: the corpus outranks the record, a declared window can be
        #: stale, and a run_v4 that exits on a version string can lose a whole
        #: shard to a wrong manifest. Refusal belongs at PROVISION time, before
        #: the weights are downloaded -- `preflight_env.py --assert-venv`.
        for _n, _r in sorted(_env["declared"].items()):
            if _r.get("satisfied") is False:
                print("  REQUIREMENT %s %s: roster wants %s, venv has %s"
                      % ("ABSENT" if not _r["resolved"] else "MISMATCH", _n,
                         "any version" if _r["specifier"] == "*"
                         else _r["specifier"],
                         _r["resolved"] or "NOTHING"), flush=True)
            elif _r.get("satisfied") is None and not _n.startswith("_"):
                print("  REQUIREMENT UNCHECKABLE %s: wants %s, venv has %r"
                      % (_n, _r.get("specifier"), _r.get("resolved")), flush=True)
    except Exception:                                           # noqa: BLE001
        pass
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
    except BaseException as e:
        #: **THE FAILURE MUST LAND IN THE LOG THAT RSYNCS.** `_Tee` wraps
        #: STDOUT only, and a traceback goes to STDERR -- which `queue_v4` then
        #: captures into its own pipe and prints two lines of to the box's
        #: ephemeral stage log. So the one artifact that travels off the box,
        #: `twp/<model>/<producer>/run_v4.log`, recorded the ATTEMPT and never
        #: the OUTCOME: both internlm2 arms stop dead after
        #: `device cuda | dict_sha ...` on 2026-09-11, with the cause reachable
        #: only on a machine that was destroyed an hour later.
        #:
        #: Restoring stdout in `finally` and letting the interpreter print the
        #: traceback does NOT fix it: by then the tee is closed. It has to be
        #: caught and written HERE.
        print("\n  *** FAILED %s: %s: %s" % (a.model, type(e).__name__, e),
              flush=True)
        traceback.print_exc(file=sys.stdout)
        #: And a MACHINE-READABLE sidecar beside it, because a census asking
        #: "which models did this box fail on" should not have to parse prose.
        #: Absence of a cell is not evidence of absence of an attempt, and this
        #: is the file that tells them apart.
        try:
            json.dump({"model": a.model, "producer": PRODUCER,
                       "when": time.strftime("%Y-%m-%dT%H:%M:%S"),
                       "error": type(e).__name__, "message": str(e)[:2000],
                       "traceback": traceback.format_exc()[-4000:],
                       #: the RESOLVED environment at the moment it died --
                       #: the thing the cell stamp cannot carry, because a
                       #: failed run has no cell to carry it on
                       "env": _resolved_env()},
                      open(os.path.join(logdir, "FAILED.json"), "w"), indent=1)
        except Exception:
            pass                      # never let the recorder mask the failure
        raise
    finally:
        sys.stdout = tee.stream
        tee.close()


if __name__ == "__main__":
    print(main())
    sys.exit(0)
