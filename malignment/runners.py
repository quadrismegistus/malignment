"""Runners: the machinery that puts a model on a device and writes records.

    python -m malignment.runners "<model_id>" [--limit N] [--purge]

    from malignment import Checkpoint
    Checkpoint("HuggingFaceTB/SmolLM3-3B-checkpoints@it-soup-APO").run_twp()

## WHERE THE DATA GOES, AND WHY NOT INTO THIS REPO

**`~/github/malignment` is a PUBLIC repo.** A twp jsonl carries the prompts
VERBATIM -- including the transgressive battery -- alongside full word
distributions. The first version of this defaulted to `malignment/data/twp/`,
which is not gitignored, so an ordinary `git add data` would have published the
battery. Nothing did, because the default was wrong for a second reason that
caught it first:

**The ingest scans `MALIGNMENT_CORPUS`, which is the ARCHIVE's data root.** A run
writing into this repo would never be ingested -- the producer completes, prints
a row count, and nothing downstream ever sees it. An operation that completes
without doing anything is the failure mode this campaign keeps paying for, and
here two independent defaults would have had to agree for it to work.

So output goes to `$MALIGNMENT_DATA/twp/` -- a root OUTSIDE both checkouts,
which the ingest scans as its second root. RH created it 2026-08-15. The archive
stays read-only legacy; new measurement lands somewhere with one sentence of
provenance. At 0.4-3.6 MB per checkpoint (sidecars off) the whole 157-checkpoint
roster is ~300 MB, so this needs no external volume -- and an unmounted external
volume is a failed run, which is a failure mode bought for no capacity gain.

## THE RULES THAT COST SOMETHING TO LEARN

**A SKIP IS AN ATTEMPT, NOT A RESULT.** twp writes `rows: []` plus a reason when a
prompt does not survive the model's own tokenizer, and those records carry a
`prompt` key -- so a resume that counts them as done never re-offers the prompts
a fix exists to recover. internlm2 wrote 402 skips under
`prompt_does_not_survive_encoding` because AutoTokenizer picked a repo-bundled
class that shifts word boundaries; with skips counted done, the LOADER_OVERRIDE
repair installs cleanly and changes nothing. The cost of the other direction is
one cheap re-attempt for a genuinely dead prompt, and the model then reads as
INCOMPLETE, which is true. **Absence of data must read as absence, never as
completion.**

**A 429 IS A RACE, NOT A STATE, AND THE MESSAGE DOES NOT SAY 429.** A rate-limited
file listing surfaces as *"does not appear to have files named
model-00001-of-00030.safetensors"* -- which reads as a fact about the MODEL. That
log, read without the quota in mind, says Llama-3.1-70B has no safetensors; it
has thirty. On 2026-08-10 this cost a whole fleet: 36 of 36 models "completed" in
three minutes having written zero cells, and the run printed ALL MODELS COMPLETE.
The detector matches the status code and the phrase, never the symptom.

**GUARD THE MASK BUILD, NOT JUST THE LOAD.** `boundary_mask` sat between two
guarded blocks in the archive, so CT-LLM's sentencepiece -- whose config
`vocab_size` exceeds its actual piece count -- killed an entire roster from one
unguarded line. Guarding two of three phases is guarding none of them.

**WRITE AND FLUSH PER PROMPT.** A model that dies partway keeps what it finished
and resumes there.

**THE ROW KEY IS `(surface, first_token_id)`, NOT A SURFACE.** A word reachable by
several token paths gets one row per path, and those rows are the partition the
ingest folds and counts as `n_paths` -- 20.4% of source cells contain a
duplicated surface. Writing the tuple into `word` yields `{"word": ["in", 304]}`,
which the ingest cannot fold. Caught by a 3-prompt smoke test, which is what a
smoke test is for.

## NO LOCAL/CLOUD SWITCH

`pick_device()` returns mps or cuda; the multi-GPU branch fires only when
`device_count() > 1`. On this Mac that branch is dead and the rest is identical,
so the same call that measures SmolLM3-3B here measures a 70B on a rented box.

## THE SIDECARS ARE OFF

The fleet runner writes `.f16` logits (109 KB/cell) and `.hidden.f32` states
(540 KB/cell). RH, 2026-08-15: *"We basically never use logits btw / Everything is
on twp"*, and the CH ingest stores neither. 30 GB per fleet that nothing reads is
not a default.
"""
import argparse
import json
import os
import socket
import sys
import time

from . import twp as T
from .ingest import DATA

#: BESIDE THE CORPUS THE INGEST READS, NOT INSIDE THIS PUBLIC REPO. See above.
TWP_OUT = os.environ.get("MALIGNMENT_TWP_OUT", os.path.join(DATA, "twp"))
#: WHO MEASURED THIS. The layout is `twp/<model>/<producer>/`, so two boxes
#: measuring one checkpoint write different FILES and rsync MERGES them. Measured
#: without the segment: a 200-cell run overwrote a 500-cell one, silently.
#: It also lands in the ingest's `source` column, so "which box produced this
#: cell" stays answerable -- the thing a per-cell store would lose.
PRODUCER = os.environ.get("MALIGNMENT_PRODUCER") or socket.gethostname().split(".")[0]
MAX_RL_RETRIES = 5


def _is_rate_limit(msg):
    """Status code and phrase, never the symptom. See the module docstring."""
    return ("429" in msg or "Too Many Requests" in msg
            or "rate limit" in msg.lower())


class TWPRunner:
    """Measures one `Checkpoint` and appends jsonl. Holds no state of its own."""

    def __init__(self, checkpoint):
        self.ck = checkpoint

    def run(self, prompts, purge=False, limit=None, dict_path=None, verbose=True):
        import torch
        from transformers import AutoModelForCausalLM

        ck = self.ck
        os.makedirs(ck.dir, exist_ok=True)
        have = ck.done()
        todo = [p for p in prompts if p not in have]
        if limit:
            todo = todo[:limit]
        say = (lambda m: print(m, flush=True)) if verbose else (lambda m: None)
        say("  %s" % ck)
        say("  %d prompts | %d already done | %d to run"
            % (len(prompts), len(have), len(todo)))
        say("  -> %s  (producer %s)" % (ck.dir, PRODUCER))
        if not todo:
            return {"model": ck.model_id, "producer": PRODUCER, "written": 0,
                    "skipped": 0, "already": len(have), "path": ck.stash().path}

        dev = T.pick_device()
        trie = T.load_prefix_trie(dict_path or T.DICT)
        say("  device %s | rule_version %d | dict_sha %s"
            % (dev, T.RULE_VERSION, T.dict_sha()))

        model = tok = loader_id = None
        for attempt in range(MAX_RL_RETRIES + 1):
            try:
                tok, loader_id = T.load_tokenizer(ck.repo, revision=ck.revision)
                kw = {"dtype": torch.float16, "trust_remote_code": True}
                if ck.revision:
                    kw["revision"] = ck.revision
                    say("  PINNED REVISION %s (main is the wrong model here)"
                        % ck.revision)
                if torch.cuda.is_available() and torch.cuda.device_count() > 1:
                    say("  device_map=auto across %d GPUs" % torch.cuda.device_count())
                    model = AutoModelForCausalLM.from_pretrained(
                        ck.repo, device_map="auto", **kw).eval()
                else:
                    model = AutoModelForCausalLM.from_pretrained(
                        ck.repo, **kw).to(dev).eval()
                break
            except Exception as e:
                msg = str(e)
                if _is_rate_limit(msg) and attempt < MAX_RL_RETRIES:
                    wait = min(300, 30 * 2 ** attempt)
                    say("  HF RATE LIMIT (attempt %d/%d) -- backing off %ds, then "
                        "RETRYING. A 429 is a race, not a model defect."
                        % (attempt + 1, MAX_RL_RETRIES, wait))
                    T.free()
                    time.sleep(wait)
                    continue
                T.free()
                T.purge_model(ck.model_id, purge)
                #: RAISED, not returned as an empty success. A load failure that
                #: returns {"written": 0} is indistinguishable from a checkpoint
                #: with nothing left to do -- the ambiguity that printed ALL
                #: MODELS COMPLETE over a dead fleet.
                raise RuntimeError("LOAD FAILED for %s: %s%s" % (
                    ck.model_id, msg[:160],
                    "  <- THIS WAS A RATE LIMIT, not a model defect"
                    if _is_rate_limit(msg) else ""))

        T.reset_batch()                 # a new checkpoint gets a fresh ceiling
        try:
            bmask = T.boundary_mask(tok, model.config.vocab_size)
            cjk = None
            if trie is not None:
                cids, cstrs, lids, pids = T.cjk_vocab(tok, model.config.vocab_size)
                if len(cids):
                    cjk = (trie, cids, cstrs, lids, pids)
                    say("  cjk: %s tokens" % format(len(cids), ","))
        except Exception as e:
            T.free()
            raise RuntimeError("MASK FAILED for %s: %s: %s"
                               % (ck.model_id, type(e).__name__, str(e)[:120]))

        pol = T.bos_policy_for(ck.model_id)
        if pol != "inherited":
            say("  bos_policy: %s" % pol)

        n_ok = n_skip = 0
        t0 = time.time()
        stamp = {"theta": T.THETA, "rule_version": T.RULE_VERSION,
                 "dict_sha": T.dict_sha(), "bos_policy": pol,
                 "loader": loader_id, "device": dev,
                 "revision": ck.revision or "", "compute_dtype": "float16",
                 "producer": PRODUCER}
        st = ck.stash()
        #: **SKIPS GO TO A SIDECAR, NOT INTO THE KEY SPACE.** A skip is an
        #: ATTEMPT, not a result. Writing one under the cell's key would make
        #: `key in stash` true, so a later tokenizer fix would find the prompt
        #: "done" and never re-offer it -- exactly how internlm2's 402 prompts
        #: would have stayed lost after the LOADER_OVERRIDE that recovered them.
        #: Kept beside the stash so the refusal and its reason are still
        #: recorded, just not as an answer.
        skip_path = os.path.join(os.path.dirname(st.path), "skipped.jsonl")
        for i, p in enumerate(todo, 1):
            rec = dict(stamp, model=ck.model_id, prompt=p)

            def _skip(reason):
                rec.update(skipped=reason, rows=[], residual=None)
                with open(skip_path, "a", encoding="utf-8") as sf:
                    sf.write(json.dumps(rec, ensure_ascii=False) + "\n")

            try:
                w, res, _calls = T.expand(model, tok, p, dev, bmask,
                                          cjk=cjk, bos_policy=pol)
            except T.SkipPrompt as sk:
                _skip(str(sk)); n_skip += 1
                continue
            except Exception as e:
                #: ONE PROMPT MUST NOT END THE CHECKPOINT, for the same reason
                #: one model must not end a roster.
                _skip("%s: %s" % (type(e).__name__, str(e)[:120])); n_skip += 1
                continue
            rows = [{"word": s, "t1": int(t), "p": float(m)}
                    for (s, t), m in w.items()]
            #: THE PAYLOAD CARRIES ITS OWN ARITHMETIC, so the ingest gate can
            #: refuse a producer that cannot close its books rather than
            #: averaging it into a table.
            rec.update(rows=rows, residual=res,
                       conservation=sum(w.values()) + res["total"])
            #: One append per cell, healed and flushed by the engine. The key
            #: carries the instrument, so a rule bump writes a NEW key rather
            #: than overwriting a measurement made by a different instrument.
            st[ck.key(p)] = rec
            n_ok += 1
            if verbose and (i % 100 == 0 or i == len(todo)):
                el = time.time() - t0
                say("     %d/%d  %.1f min  %.2f s/cell  (%d skipped)"
                    % (i, len(todo), el / 60, el / max(1, i), n_skip))
        T.free()
        T.purge_model(ck.model_id, purge)
        return {"model": ck.model_id, "producer": PRODUCER, "written": n_ok,
                "skipped": n_skip, "already": len(have), "path": st.path,
                "minutes": (time.time() - t0) / 60}


def main():
    from .checkpoint import Checkpoint
    ap = argparse.ArgumentParser()
    ap.add_argument("model_id")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--purge", action="store_true",
                    help="delete the weights afterwards (rented disks)")
    ap.add_argument("--prompts", default=None, help="txt file, one prompt per line")
    ap.add_argument("--all-prompts", action="store_true",
                    help="every admitted prompt, not just what will pair")
    a = ap.parse_args()

    ck = Checkpoint(a.model_id)
    if not ck.declared:
        print("  NOTE: %s is not declared in the roster. It will be measured and"
              "\n  ingested, but `movement` builds only DECLARED edges, so nothing"
              "\n  will pair with it until it is." % a.model_id)
    if a.prompts:
        with open(a.prompts, encoding="utf-8") as fh:
            prompts = [ln.rstrip("\n") for ln in fh if ln.strip()]
    elif a.all_prompts:
        from .prompts import Prompts
        prompts = sorted({p.text for p in Prompts.all()})
        print("  --all-prompts: %d admitted. Cells on prompts no neighbour holds"
              "\n  will pair with nothing." % len(prompts))
    else:
        prompts = ck.neighbour_prompts()
        print("  prompt set: %d, from declared neighbours %s"
              % (len(prompts), ", ".join(n.split("/")[-1] for n in ck.neighbours())))
        if not prompts:
            print("  REFUSING: no declared neighbour has cells, so nothing measured"
                  "\n  here could pair. Declare an edge first, or pass --prompts /"
                  "\n  --all-prompts deliberately.")
            return 1
    print("\n  %s" % json.dumps(ck.run_twp(prompts, purge=a.purge, limit=a.limit),
                                indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
