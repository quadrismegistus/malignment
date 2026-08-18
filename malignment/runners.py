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
import collections
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


class _Tee:
    """Write to the terminal AND to a log beside the data.

    The log lives at `twp/<model>/<producer>/run.log`, so it rsyncs with the
    cells it describes: a box's output and the account of how it was produced
    travel together. It is not `.jsonl`, so the ingest walks past it.

    Kept as a tee rather than a shell redirect because the path depends on the
    model and producer, which only the runner knows -- a redirect the caller has
    to compose is a redirect someone eventually composes wrong, or forgets.
    """

    def __init__(self, path):
        self.stream = sys.stdout
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.fh = open(path, "a", encoding="utf-8")
        self.fh.write("\n===== %s  %s =====\n"
                      % (time.strftime("%Y-%m-%d %H:%M:%S"), PRODUCER))
        self.fh.flush()

    def write(self, data):
        self.stream.write(data)
        self.fh.write(data)
        self.fh.flush()          # a killed run keeps its log up to the kill

    def flush(self):
        self.stream.flush()
        self.fh.flush()

    def close(self):
        try:
            self.fh.close()
        except Exception:
            pass


#: **REMOTE CODE IS REFUSED UNLESS THE CONFIG ASKS FOR IT.** RH, 2026-08-16:
#: "i think only a few of our models need trust_remote_code". Measured across all
#: 159 declared checkpoints by reading each config.json: **19 declare `auto_map`,
#: 138 do not.** So passing `trust_remote_code=True` unconditionally -- which
#: this file did -- enabled arbitrary code execution for 87% of the roster that
#: never needed it.
#:
#: It also HID a failure. With remote code preferred, MPT loaded five-year-old
#: bundled code that crashes on transformers 5.x, while native MPT support sat
#: unused. `tiiuae/falcon-7b` and the three Teuken models are the same shape:
#: `model_type` falcon/llama, natively supported, and still shipping `auto_map`
#: that was being preferred over the working path.
#:
#: The flag now follows the config: `auto_map` present -> allow, absent -> refuse.
#: A model that needs it declares it, which is the same principle as taking the
#: ingest population from the payload stamp rather than a maintained list.
#:
#: mpt: the bundled remote code imports `_expand_mask` from
#:      `transformers.models.bloom.modeling_bloom`, a private helper DELETED in
#:      transformers 5.x -- so `trust_remote_code=True` raises ImportError before
#:      a single weight loads. transformers has had NATIVE MPT support since
#:      4.32, and it works, but the repo's five-year-old config.json writes `0`
#:      where the strict dataclass demands `0.0`.
#:
#:      Exactly two fields need coercing, READ OFF THE ANNOTATIONS rather than
#:      guessed: resid_pdrop and emb_pdrop. **attn_pdrop is annotated `int` and
#:      must be left alone** -- coercing it "for consistency" fails with the
#:      mirror-image error, which cost a cycle to learn.
#:
#:      Verified on gl198976/mpt-7b: loads as MptForCausalLM in ~104s, forward
#:      pass gives logits (1, 6, 50432), and "She slept and the house was" ->
#:      " quiet".
MPT_DROP = ("auto_map", "architectures", "model_type", "transformers_version",
            "init_config", "tokenizer_name", "torch_dtype", "verbose")
MPT_FLOAT = ("resid_pdrop", "emb_pdrop")
MPT_ATTN_DROP = ("attn_impl", "prefix_lm", "attn_uses_sequence_id")


def _mpt_config(repo, revision):
    """Native MptConfig from a repo whose config.json predates strict typing."""
    import json
    from huggingface_hub import hf_hub_download
    from transformers.models.mpt.configuration_mpt import MptConfig, MptAttentionConfig
    raw = json.load(open(hf_hub_download(repo, "config.json", revision=revision)))
    ac = {k: v for k, v in (raw.get("attn_config") or {}).items()
          if k not in MPT_ATTN_DROP}
    kw = {k: (float(v) if k in MPT_FLOAT else v) for k, v in raw.items()
          if k not in MPT_DROP and k != "attn_config"}
    return MptConfig(attn_config=MptAttentionConfig(**ac), **kw)


def _config_facts(repo, revision):
    """(model_type, declares_auto_map). The config decides, not a maintained list."""
    import json
    from huggingface_hub import hf_hub_download
    try:
        c = json.load(open(hf_hub_download(repo, "config.json", revision=revision)))
        return c.get("model_type"), bool(c.get("auto_map"))
    except Exception:
        #: UNREADABLE CONFIG -> REFUSE remote code. The safe direction: a model
        #: whose config cannot be read has not asked for anything.
        return None, False


def _is_rate_limit(msg):
    """Status code and phrase, never the symptom. See the module docstring."""
    return ("429" in msg or "Too Many Requests" in msg
            or "rate limit" in msg.lower())


#: What a loaded checkpoint IS, for `twp.expand`: exactly its argument tuple
#: plus the two stamp fields. A dict would let a caller reach for a key that is
#: not there and get `None` into `expand`, where a None `bmask` is not an error,
#: it is a different word-boundary rule.
Loaded = collections.namedtuple(
    "Loaded", "model tok dev bmask cjk bos_policy loader_id")


def load_for_twp(ck, dict_path=None, purge=False, say=None):
    """Put `ck` on a device and build its masks. The inputs `twp.expand` needs.

    **EXTRACTED FROM `TWPRunner.run` ON 2026-08-16, LOGIC UNEDITED**, because a
    second consumer arrived: `malignment.serve` answers `/slot` from a resident
    model. The archive did this the other way -- `server.py._get_slot_model`
    was a SECOND load path, and it drifted: it never grew the MPT override, the
    rate-limit retry, or the mask guard, so the app could load a model the
    runner refuses and measure it with a boundary rule the runner would not
    accept. **A second loader is a second instrument**, and this repo's whole
    premise is that the second copy is the one without the docstring.

    Nothing here is new. If this function and `run()` ever disagree about how a
    model is loaded, that is the defect, not a configuration.

    **THE CALLER OWNS THE UNLOAD.** `T.free()` and `T.purge_model` are not
    called here on success, because the point of loading separately is to HOLD
    the model across calls. On failure they are, since there is nothing to hold.
    """
    import torch
    from transformers import AutoModelForCausalLM

    say = say or (lambda m: None)
    dev = T.pick_device()
    trie = T.load_prefix_trie(dict_path or T.DICT)
    #: **THE LOADER DOES NOT KNOW THE INSTRUMENT AND MUST NOT NAME IT.** This
    #: line printed `T.RULE_VERSION`, a module constant equal to 3, on every
    #: caller including v4 ones -- so a topup run under `v4[decoded,depth=9]`
    #: announced itself as rule_version 3 while stamping every cell it wrote
    #: with 4. The run was right and the sentence was wrong, which is the shape
    #: nothing catches: a wrong cell gets found by the next reader, a wrong
    #: LABEL on a right cell gets found by nobody. The authoritative statement
    #: is the `INSTRUMENT:` line, emitted by whoever holds the `rules`.
    say("  device %s | dict_sha %s" % (dev, T.dict_sha()))

    model = tok = loader_id = None
    for attempt in range(MAX_RL_RETRIES + 1):
        try:
            #: CONFIG FIRST. The MPT override below refuses remote code,
            #: and the tokenizer load must be covered by it -- it runs first
            #: and used to trust remote code unconditionally.
            mtype, has_remote = _config_facts(ck.repo, ck.revision)
            tok, loader_id = T.load_tokenizer(
                ck.repo, revision=ck.revision,
                trust_remote_code=(mtype != "mpt"))
            kw = {"dtype": torch.float16, "trust_remote_code": bool(has_remote)}
            if has_remote:
                say("  config declares auto_map -> remote code ALLOWED")
            #: MPT is the exception to the exception: it DECLARES auto_map,
            #: and that code is dead on transformers 5.x. Native impl instead.
            if mtype == "mpt":
                kw = {"dtype": torch.float16, "trust_remote_code": False,
                      "config": _mpt_config(ck.repo, ck.revision)}
                say("  LOADER OVERRIDE mpt: native impl, remote code REFUSED"
                    " (its `_expand_mask` import is dead on transformers 5.x)")
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

    return Loaded(model, tok, dev, bmask, cjk, pol, loader_id)


class TWPRunner:
    """Measures one `Checkpoint` and appends jsonl. Holds no state of its own."""

    def __init__(self, checkpoint):
        self.ck = checkpoint

    def run(self, prompts, purge=False, limit=None, dict_path=None, verbose=True,
            rules=None):
        """`rules=None` is v3 and dispatches to `twp.expand` ITSELF.

        **Not to `expand4(Rules())`, which produces the same numbers.** If v3's
        path ran through v4 code, v3's correctness would depend on v4 being
        right, and the whole point of the separate module is that it cannot be.
        One `if`, and the 984,857 stored cells keep a producer that does not
        import the thing under test.
        """
        import torch
        from transformers import AutoModelForCausalLM

        ck = self.ck
        os.makedirs(ck.dir, exist_ok=True)
        have = ck.done(rules)
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

        #: ONE LOADER, SHARED WITH `malignment.serve`. See `load_for_twp`.
        ld = load_for_twp(ck, dict_path=dict_path, purge=purge, say=say)
        #: **`load_for_twp` PRINTS `T.RULE_VERSION`, WHICH IS ALWAYS 3.** It runs
        #: before the rules are known and cannot say otherwise, so on a v4 run
        #: the log named the wrong instrument -- `run.log` rsyncs with the data,
        #: so that line is what a later reader would trust. Corrected here, where
        #: the rules ARE known, rather than by threading them into a loader that
        #: does not otherwise need them.
        model, tok, dev = ld.model, ld.tok, ld.dev
        #: **PROBE THE CACHE ONCE, WHERE THE MODEL EXISTS, BEFORE ANY KEY IS
        #: BUILT.** `expand4` disables the prompt cache per-model when the KV
        #: shape is unexpected (Baichuan2: "'tuple' object has no attribute
        #: 'layers'"), but the KEY is stamped from `T.USE_PROMPT_CACHE` -- so a
        #: run that silently fell back would write 2,706 cells claiming
        #: `prompt_cache=True` while measuring uncached. **A stamp that says what
        #: was REQUESTED rather than what HAPPENED is this campaign's most-booked
        #: defect.**
        #:
        #: My first attempt put this before `model` was bound, so it caught a
        #: NameError and disabled the cache for EVERY model -- an honest stamp
        #: carrying a wrong value, which is the same defect wearing the fix's
        #: clothes.
        if rules is not None and T.USE_PROMPT_CACHE:
            try:
                #: `bos_policy_for` rather than the local `pol`, which binds
                #: LATER -- my second attempt caught a NameError on it and
                #: reported Baichuan2 as cache-incapable for the wrong reason.
                #: It happens to BE incapable, so the answer was right and the
                #: evidence was not, which is worse than a wrong answer.
                _pol = T.bos_policy_for(ck.model_id)
                T.prompt_cache(model, T._prompt_ids(tok, todo[0], _pol)[0], dev)
            except Exception as e:                              # noqa: BLE001
                T.USE_PROMPT_CACHE = False
                say("  prompt-cache UNAVAILABLE on this architecture (%s)"
                    " -- cells stamped prompt_cache=False" % str(e)[:46])

        if rules is not None:
            say("  INSTRUMENT: rule_version %d | %s | prompt_cache %s"
                % (__import__("malignment.twp_v4", fromlist=["x"]).RULE_VERSION,
                   rules.label(), bool(T.USE_PROMPT_CACHE)))

        bmask, cjk, pol, loader_id = ld.bmask, ld.cjk, ld.bos_policy, ld.loader_id

        n_ok = n_skip = 0
        t0 = time.time()
        stamp = {"theta": T.THETA, "rule_version": T.RULE_VERSION,
                 "dict_sha": T.dict_sha(), "bos_policy": pol,
                 "loader": loader_id, "device": dev,
                 "revision": ck.revision or "", "compute_dtype": "float16",
                 "producer": PRODUCER}
        #: **THE BODY MUST CARRY WHAT THE KEY CARRIES.** `ck.key(p, rules)` puts
        #: `rule_version`, `rules` and `prompt_cache` on the KEY; the ingest reads
        #: the BODY. A v4 cell stamped with `T.RULE_VERSION` (always 3) and no
        #: rules would be correctly keyed and would FILE as something else --
        #: which is what `m-a-p/CT-LLM-Base`'s 2,706 cells did on 2026-08-17,
        #: key saying `v4[decoded,depth=9]` and body saying `None`.
        #:
        #: `ingest._key_body_agree` now refuses that shape. This is the producer
        #: half: derived FROM the key so the two cannot drift.
        if rules is not None:
            stamp.update({f: v for f, v in ck.key("", rules).items()
                          if f not in ("model", "prompt")})
        st = ck.stash()
        try:
            from tqdm import tqdm
            bar = tqdm(todo, desc=ck.model_id.split("/")[-1][:28], unit="cell",
                       dynamic_ncols=True, file=sys.stderr)
        except ImportError:
            bar = todo
        #: **SKIPS GO TO A SIDECAR, NOT INTO THE KEY SPACE.** A skip is an
        #: ATTEMPT, not a result. Writing one under the cell's key would make
        #: `key in stash` true, so a later tokenizer fix would find the prompt
        #: "done" and never re-offer it -- exactly how internlm2's 402 prompts
        #: would have stayed lost after the LOADER_OVERRIDE that recovered them.
        #: Kept beside the stash so the refusal and its reason are still
        #: recorded, just not as an answer.
        skip_path = os.path.join(os.path.dirname(st.path), "skipped.jsonl")
        for i, p in enumerate(bar, 1):
            rec = dict(stamp, model=ck.model_id, prompt=p)

            def _skip(reason):
                rec.update(skipped=reason, rows=[], residual=None)
                with open(skip_path, "a", encoding="utf-8") as sf:
                    sf.write(json.dumps(rec, ensure_ascii=False) + "\n")

            try:
                if rules is None:
                    w, res, _calls = T.expand(model, tok, p, dev, bmask,
                                              cjk=cjk, bos_policy=pol)
                else:
                    from . import twp_v4 as V4
                    w, res, _meta = V4.expand4(model, tok, p, dev, bmask,
                                               cjk=cjk, bos_policy=pol,
                                               rules=rules)
                    res = dict(res, total=(res['tail'] + res['drop']
                                           + res['open'] + res['mojibake']
                                           + res.get('term_floored', 0.0)))

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
            st[ck.key(p, rules)] = rec
            n_ok += 1
            if hasattr(bar, "set_postfix"):
                bar.set_postfix(ok=n_ok, skip=n_skip, refresh=False)
            #: A DURABLE LINE EVERY 25 (~35 s), because a progress bar is a LIVE
            #: VIEW on stderr and the log is the RECORD. tqdm's \r updates would
            #: make the log unreadable, so the heartbeat is plain lines: frequent
            #: enough to `tail -f`, and still true after the terminal is gone.
            if verbose and (i % 25 == 0 or i == len(todo)):
                el = time.time() - t0
                spc = el / max(1, i)
                #: ETA IN THE LOG, NOT ONLY IN THE BAR. tqdm's ETA lives on
                #: stderr and dies with the terminal; the question "when does
                #: this finish" is asked of a `tail -f` hours later, by someone
                #: who never saw the bar.
                left = (len(todo) - i) * spc
                eta = time.strftime("%H:%M:%S", time.localtime(time.time() + left))
                say("     %d/%d (%.1f%%)  %.1f min  %.2f s/cell  "
                    "(%d ok, %d skipped)  left %.0f min  ETA %s"
                    % (i, len(todo), 100.0 * i / len(todo), el / 60, spc,
                       n_ok, n_skip, left / 60, eta))
        T.free()
        T.purge_model(ck.model_id, purge)
        return {"model": ck.model_id, "producer": PRODUCER, "written": n_ok,
                "skipped": n_skip, "already": len(have), "path": st.path,
                "minutes": (time.time() - t0) / 60}


    def topup(self, rules, root=None, limit=None, dict_path=None, verbose=True):
        """PASS 2: score the words this model's LINEAGE cleared and it did not.

            Runner(ck).topup(rules=V4.ADOPTED)

        `expand` gates on `P0 >= theta`, so a word below the gate is ABSENT from
        the cell and every consumer imputes zero -- ~30% of falling mass. This
        measures them with `score_words4` over `corpus.topup_todo`, which is the
        lineage union minus what the model already has.

        ## IT WRITES A NEW CELL, IT DOES NOT MUTATE THE OLD ONE

        The key gains `topup: True` beside `rule_version`/`rules`/`prompt_cache`,
        and the record holds the MERGED distribution -- expand's rows plus the
        scored ones, with `tail` already decremented. So a consumer asks for
        topped-up cells or plain ones and gets a self-contained distribution
        either way, with **no merge protocol to forget**. The pass-1 cell is
        untouched and remains comparable.

        Same reasoning as `rule_version` being in the key: a different instrument
        is a different key, and the old rows stay for comparison.

        ## THE `tail` DECREMENT, AND WHY IT CAN REFUSE

        These words' mass sits in `tail` by construction. Writing them without
        subtracting breaks conservation, which is exactly 1.000000 on all 984,857
        stored cells. So `tail` is reduced by exactly the mass written -- and if
        that mass EXCEEDS `tail`, the cell is refused rather than clamped.
        Measured on CT-LLM-Base before building this: median tail 0.2102 against
        ~20 sub-theta words, ample -- but **min tail is 0.002668**, which 20 words
        at up to theta could exceed. The overflow is a real case, and it means the
        sub-theta words are not where this assumes, which is a refusal and not a
        rounding error.
        """
        from . import corpus
        from . import twp_v4 as V4

        ck = self.ck
        os.makedirs(ck.dir, exist_ok=True)
        say = (lambda m: print(m, flush=True)) if verbose else (lambda m: None)
        todo_words = corpus.topup_todo(ck.model_id, root=root)
        say("  INSTRUMENT: rule_version %d | %s | prompt_cache %s | topup"
            % (V4.RULE_VERSION, rules.label(), bool(T.USE_PROMPT_CACHE)))
        base_key = lambda p: dict(ck.key(p, rules), topup=True)          # noqa: E731
        st = ck.stash(PRODUCER)
        have1 = {k["prompt"]: v for k, v in st.items()
                 if k.get("rule_version") == V4.RULE_VERSION
                 and not k.get("topup")
                 and k.get("rules") == rules.label()}
        todo = [p for p in sorted(todo_words) if p in have1 and base_key(p) not in st]
        if limit:
            todo = todo[:limit]
        say("  %s\n  topup: %d prompts with missing words | %d have a pass-1 cell"
            " | %d to run" % (ck, len(todo_words), len(have1), len(todo)))
        if not todo:
            return dict(model=ck.model_id, written=0, refused=0, skipped=0)

        ld = load_for_twp(ck, dict_path=dict_path, purge=False, say=say)
        model, tok, dev = ld.model, ld.tok, ld.dev
        bmask, cjk, pol = ld.bmask, ld.cjk, ld.bos_policy
        n_ok = n_ref = n_skip = 0
        refuse_path = os.path.join(os.path.dirname(st.path), "topup_refused.jsonl")
        #: **THIS FILE IS APPEND-ONLY AND OUTLIVES THE RUN THAT WROTE IT.**
        #: CT-LLM-SFT's held 57 records: 55 from the v3-sourced worklist, whose
        #: refusals ran 0.75-0.93 mass against tails of 0.08-0.46, and 2 from
        #: the corrected run. Read without that separation it reports a
        #: catastrophe that was fixed hours earlier -- and unlike the stash,
        #: nothing here is keyed, so a later record cannot supersede an earlier
        #: one. A marker line is the cheapest thing that makes the boundary
        #: legible; purging would destroy the record of a real failure.
        with open(refuse_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"_run": True, "model": ck.model_id,
                                 "rules": rules.label(),
                                 "prompt_cache": bool(T.USE_PROMPT_CACHE),
                                 "prompts_todo": len(todo),
                                 "producer": PRODUCER}) + "\n")
        for i, p in enumerate(todo, 1):
            rec1 = have1[p]
            try:
                got, refused, total = V4.score_words4(
                    model, tok, p, todo_words[p], dev, bmask, cjk=cjk,
                    bos_policy=pol, rules=rules)
            except Exception as e:                                  # noqa: BLE001
                n_skip += 1
                continue
            res = dict(rec1["residual"])
            #: **REFUSE, DO NOT CLAMP.** More mass than `tail` holds means the
            #: sub-theta words are not where this assumes.
            if total > res["tail"]:
                n_ref += 1
                with open(refuse_path, "a", encoding="utf-8") as fh:
                    #: SELF-DESCRIBING, because a marker line and the records
                    #: it introduces are separated by any crash. Every record
                    #: carries the instrument that produced it, so the 55
                    #: v3-sourced refusals in CT-LLM-SFT's log stay
                    #: distinguishable from the 2 real ones no matter how the
                    #: file is read or truncated.
                    fh.write(json.dumps({"model": ck.model_id, "prompt": p,
                                         "topup_mass": total, "tail": res["tail"],
                                         "n_words": len(got),
                                         "rules": rules.label(),
                                         "rule_version": V4.RULE_VERSION,
                                         "prompt_cache": bool(T.USE_PROMPT_CACHE),
                                         "producer": PRODUCER},
                                        ensure_ascii=False) + "\n")
                continue
            res["tail"] = res["tail"] - total
            #: `n_paths = 1` BY CONSTRUCTION -- a scored row is a single-path
            #: lower bound, an expand row is beam-accumulated. Marked so nothing
            #: reads them as the same measurement.
            rows = list(rec1["rows"]) + [
                {"word": w, "t1": int(t), "p": float(v), "n_paths": 1, "topup": True}
                for (w, t), v in got.items()]
            cons = sum(r["p"] for r in rows) + res["tail"] + res["drop"] + \
                res["open"] + res["mojibake"] + res.get("term_floored", 0.0)
            if abs(cons - 1.0) > 1e-4:
                n_ref += 1
                with open(refuse_path, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps({"model": ck.model_id, "prompt": p,
                                         "conservation": cons}, ensure_ascii=False) + "\n")
                continue
            st[base_key(p)] = dict(rec1, rows=rows, residual=res, conservation=cons,
                                   topup=True, topup_words=len(got),
                                   topup_mass=total, topup_refused=len(refused))
            n_ok += 1
            if verbose and i % 200 == 0:
                say("    %d/%d  ok=%d refused=%d" % (i, len(todo), n_ok, n_ref))
        say("  topup done: %d written, %d refused, %d skipped" % (n_ok, n_ref, n_skip))
        return dict(model=ck.model_id, written=n_ok, refused=n_ref, skipped=n_skip)


def main():
    from .checkpoint import Checkpoint
    ap = argparse.ArgumentParser()
    ap.add_argument("model_id")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--purge", action="store_true",
                    help="delete the weights afterwards (rented disks)")
    ap.add_argument("--prompts", default=None, help="txt file, one prompt per line")
    #: **A FLEET BOX CANNOT COMPUTE ITS OWN TODO.** `Checkpoint.done()` reads the
    #: LOCAL stash, and a fresh box has none -- so it would re-measure everything
    #: and report success. The worklist is computed HERE against ClickHouse,
    #: which is the only place that knows what exists, and shipped as `--prompts`.
    ap.add_argument("--rules", default=None, choices=["v4"],
                    help="measure under twp_v4.ADOPTED instead of v3")
    ap.add_argument("--all-prompts", action="store_true",
                    help="every admitted prompt, not just what will pair")
    ap.add_argument("--log", default=None,
                    help="default: <twp>/<model>/<producer>/run.log")
    a = ap.parse_args()

    ck = Checkpoint(a.model_id)
    tee = _Tee(a.log or os.path.join(ck.dir, PRODUCER, "run.log"))
    sys.stdout = tee
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
    try:
        rules = None
        if a.rules == "v4":
            from . import twp_v4 as V4
            rules = V4.ADOPTED
        print("\n  %s" % json.dumps(
            ck.run_twp(prompts, purge=a.purge, limit=a.limit, rules=rules), indent=1))
    finally:
        sys.stdout = tee.stream
        tee.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
