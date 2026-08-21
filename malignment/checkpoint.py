"""One checkpoint, as an object. Identity, roster facts, corpus state, and a run.

    from malignment import Checkpoint

    apo = Checkpoint("HuggingFaceTB/SmolLM3-3B-checkpoints@it-soup-APO")
    apo.declared          # is it in the authored roster?
    apo.parents           # what it was trained from
    apo.cells             # how many cells the store holds for it
    apo.done()            # prompts already written to jsonl
    apo.run_twp()         # measure the prompts that will PAIR

## THE NOUN IS HERE, THE VERB IS IN `runners.py`

RH, 2026-08-15: *"I'd really like to have a checkpoint.py for ease of access
operations ... runners.py could declare a TWPRunner or something that
checkpoint's run_twp imports."*

So this file answers questions about a checkpoint and holds no measurement
machinery: no torch import, no model load, nothing that needs a GPU. Every
attribute here is cheap and reads either the authored roster or the store.
`run_twp` constructs a `runners.TWPRunner` and hands off.

That split is not only tidiness. The archive's `Checkpoint` was an accessor
whose `landed_v3` globbed a DIRECTORY while its data came from the STORE, and
nothing tied the two -- a checkpoint could report landed and hold no cells. Here
`cells` reads the store and `done()` reads the artifact, and they are named for
what they read rather than for what someone hoped they meant.

## `repo@revision` IS PARSED IN ONE PLACE

`twp._repo_of` / `_revision_of`. `split("@")` written at each call site is one
chance per site at `[-1]`.
"""
import json
import os

#: **NO MODULE-LEVEL `from . import twp`.** This file's docstring promises "no
#: torch import", README.md promises "three lines suffice to ANALYSE", and both
#: were FALSE: `__init__.py:11` imports `Checkpoint` eagerly, this line imported
#: `twp`, and `twp.py:52` imports `transformers`. So `import malignment.roster`
#: on a machine without transformers raised ModuleNotFoundError, and all four
#: analysis entry points -- ch, corpus, roster, checkpoint -- failed identically.
#: dario reproduced it on 2026-08-16 while building a server that only reads.
#:
#: The symptom was visible on EVERY invocation as a FutureWarning from
#: twp.py:405 and was suppressed rather than asked about, including by the seat
#: that owns this file.
#:
#: `T` is now imported inside the four methods that use it -- which is the
#: idiom this file ALREADY used for `roster` and `ch` at seven other call
#: sites. Verified safe: no use of `T` at class-definition time (lines 45, 46,
#: 81, 234, 250, all method bodies).


class Checkpoint:
    """One checkpoint, addressable as `repo` or `repo@revision`."""

    def __init__(self, model_id, out=None):
        from . import twp as T
        self.model_id = model_id
        self.repo = T._repo_of(model_id)
        self.revision = T._revision_of(model_id) or self._declared_revision(model_id)
        self._out = out

    @staticmethod
    def _declared_revision(model_id):
        """The roster's `revision:` pin, for ids that carry no `@`.

        **TWO MECHANISMS, AND ONLY ONE OF THEM USED TO REACH THIS RUNNER.**
        `@revision` is an IDENTITY mechanism -- two revisions of one repo need
        distinct ids or the store cannot tell them apart. `revision:` on the node
        is the PIN. The archive fleet read the pin (Aquila2-7B is stamped at
        9c76e143..., SmolLM3-3B-checkpoints at it-SFT, both correct); this class
        read only the `@`, so a bare id silently loaded `main`.

        For SmolLM3 that fails loudly -- main holds a README and no weights. For
        `BAAI/Aquila2-7B` it would NOT: its main branch was replaced with a
        RE-TOKENISED model, vocab 143,973 against the pinned 100,008, so the run
        succeeds and pairs a 100k-vocab model with a 144k tokenizer. A wrong
        answer that loads is worse than one that crashes.

        Raises on disagreement rather than picking: an id saying one revision
        while the roster says another is a question for a person.
        """
        try:
            from . import roster
            node = (roster.load().get("nodes") or {}).get(model_id) or {}
        except Exception:                                      # noqa: BLE001
            return None                                        # roster absent: unchanged
        return str(node.get("revision") or "") or None

    def check_revision(self):
        """Raise if the id's `@revision` contradicts the roster's pin."""
        from . import twp as T
        from . import roster
        node = (roster.load().get("nodes") or {}).get(self.model_id) or {}
        declared = str(node.get("revision") or "") or None
        from_id = T._revision_of(self.model_id)
        if declared and from_id and declared != from_id:
            raise ValueError(
                "%s: id pins %r, roster pins %r. One of them is wrong and this "
                "is not a runner's decision." % (self.model_id, from_id, declared))
        return self.revision

    def __repr__(self):
        return "Checkpoint(%r)" % self.model_id

    def __eq__(self, other):
        return isinstance(other, Checkpoint) and other.model_id == self.model_id

    def __hash__(self):
        return hash(self.model_id)

    # -- the authored roster -------------------------------------------------

    @property
    def _roster(self):
        from . import roster
        return roster.load()

    @property
    def declared(self):
        return self.model_id in (self._roster.get("nodes") or {})

    @property
    def node(self):
        """The authored block for this checkpoint, or {}."""
        return (self._roster.get("nodes") or {}).get(self.model_id) or {}

    def _edges(self, deriving_only=True):
        from . import roster
        for p, op, c in (self._roster.get("edges") or []):
            if deriving_only and op not in roster.DERIVING:
                continue
            yield p, op, c

    @property
    def parents(self):
        """[(model_id, op)] this checkpoint was DERIVED from."""
        return [(p, op) for p, op, c in self._edges() if c == self.model_id]

    @property
    def children(self):
        """[(model_id, op)] derived FROM this checkpoint."""
        return [(c, op) for p, op, c in self._edges() if p == self.model_id]

    def neighbours(self):
        """Declared parents and children -- what this checkpoint will PAIR with."""
        return sorted({m for m, _ in self.parents} | {m for m, _ in self.children})

    @property
    def lineage(self):
        """The pretraining root this descends from, by walking DERIVING edges."""
        par = {c: p for p, op, c in self._edges()}
        m, seen = self.model_id, set()
        while m in par and m not in seen:
            seen.add(m)
            m = par[m]
        return m

    # -- the store -----------------------------------------------------------

    @property
    def cells(self):
        """Cells the store holds for this checkpoint. Reads CH, not a directory."""
        from . import ch
        return ch.scalar("SELECT count() FROM {db}.twp_cells WHERE model = '%s'"
                         % self.model_id.replace("'", "\\'")) or 0

    def store_prompts(self):
        from . import ch
        return {r["prompt"] for r in ch.query(
            "SELECT DISTINCT prompt FROM {db}.twp_words WHERE model = '%s'"
            % self.model_id.replace("'", "\\'"))}

    def neighbour_prompts(self):
        """The prompts this checkpoint must hold for its declared pairs to build.

        **NOT "every admitted prompt", and the difference is the point.**
        `movement` intersects the two arms of a pair, so a cell measured on a
        prompt no neighbour holds pairs with nothing: real data answering no
        declared question, at the same cost as one that does.

        UNION of the neighbours, never one arm's list -- taking either alone
        silently measures a different population, the error that once dropped
        65% of amber's cells.
        """
        from . import ch
        nb = self.neighbours()
        if not nb:
            return []
        q = "','".join(m.replace("'", "\\'") for m in nb)
        return sorted({r["prompt"] for r in ch.query(
            "SELECT DISTINCT prompt FROM {db}.twp_words WHERE model IN ('%s')" % q)})

    # -- the run artifact ----------------------------------------------------

    @property
    def dir(self):
        """`<TWP_OUT>/<model>/` -- one directory per checkpoint, producers inside."""
        from .runners import TWP_OUT
        safe = self.model_id.replace("/", "__").replace("@", "__at__")
        return self._out or os.path.join(TWP_OUT, safe)

    def producers(self):
        """Every producer that has written this checkpoint here.

        The layout is `twp/<model>/<producer>/`, and the producer segment is the
        whole reason rsync can merge: two runs of one checkpoint on different
        machines are different FILES. Measured without it, a 200-cell run
        overwrote a 500-cell one and the loss was silent.
        """
        if not os.path.isdir(self.dir):
            return []
        return sorted(d for d in os.listdir(self.dir)
                      if os.path.isdir(os.path.join(self.dir, d)))

    def stash(self, producer=None):
        """The HashStash for one producer. ABSOLUTE root_dir, always.

        **A bare name silently resolves to `~/.cache/hashstash/`** -- the trap
        CLAUDE.md warns about for this library, and one this session walked into
        on its first probe. `self.dir` is absolute by construction.
        """
        from hashstash import HashStash
        from .runners import PRODUCER
        return HashStash(root_dir=os.path.join(self.dir, producer or PRODUCER),
                         engine="jsonl", flat=True)

    def stashes(self):
        """Every producer's stash. Resume must see ALL of them, not just ours."""
        return [(p, self.stash(p)) for p in self.producers()]

    def key(self, prompt, rules=None):
        """**THE INSTRUMENT IS PART OF THE KEY.**

        `done()` used to gate on "has rows and is not skipped" while the INGEST
        additionally required `rule_version == 3`. Nothing tied them, so bumping
        the rule -- or changing the dictionary, which moves dict_sha -- gave:
        done() reports complete, the runner writes nothing, the ingest excludes
        every old-rule record, and the checkpoint VANISHES from ClickHouse while
        the run prints success.

        Putting rule_version and dict_sha IN THE KEY makes that impossible rather
        than guarded: a rule bump is a different key, every prompt is re-offered
        automatically, and the old rows remain for comparison. A defect you
        cannot express beats one you remember to check.

        **`rules=None` IS v3 AND MUST STAY THE EXACT DICT IT WAS.** Adding a
        field unconditionally -- even one set to `None` -- would change every
        v3 key and orphan 984,857 stored cells. So the v4 fields appear ONLY
        when a rule set is passed.
        """
        from . import twp as T
        from .ingest import RULE_VERSION
        if rules is None:
            return {"model": self.model_id, "prompt": prompt,
                    "rule_version": RULE_VERSION, "dict_sha": T.dict_sha()}
        from .twp_v4 import RULE_VERSION as V4_RULE_VERSION
        return {"model": self.model_id, "prompt": prompt,
                "rule_version": V4_RULE_VERSION, "dict_sha": T.dict_sha(),
                "rules": rules.label(),
                #: the prompt cache is not bit-identical, so a cached and an
                #: uncached cell are different measurements of one prompt.
                "prompt_cache": bool(T.USE_PROMPT_CACHE)}

    @property
    def paths(self):
        """Every `data.jsonl` for this checkpoint, one per producer."""
        return [st.path for _, st in self.stashes()]

    def done(self, rules=None):
        """Prompts measured BY THIS INSTRUMENT, across every producer.

        A skip is an attempt, not a result: `runners` records refusals in a
        sidecar and writes NO key for them, so a tokenizer fix re-offers the
        prompt instead of finding it done -- the failure that would have left
        internlm2's 402 recovered prompts unmeasured.
        **AND `rules` IS PART OF "DONE", or a v4 run sees v3's cells and
        concludes it has nothing to do.** The same argument the docstring above
        makes for `rule_version`, one level in: a rule set is an instrument.
        """
        from . import twp as T
        probe = self.key("", rules)
        want = {k: v for k, v in probe.items() if k != "prompt"}
        out = set()
        for _, st in self.stashes():
            for k in st.keys():
                if not isinstance(k, dict):
                    continue
                if all(k.get(f) == v for f, v in want.items()):
                    out.add(k.get("prompt"))
        return out

    def skipped(self):
        """{prompt: reason}, from the sidecar. Outside the key space on purpose."""
        out = {}
        for _, st in self.stashes():
            p = os.path.join(os.path.dirname(st.path), "skipped.jsonl")
            if not os.path.exists(p):
                continue
            with open(p, encoding="utf-8") as fh:
                for ln in fh:
                    try:
                        r = json.loads(ln)
                    except ValueError:
                        continue
                    out[r.get("prompt")] = r.get("skipped")
        return out

    def provenance(self):
        """{(producer, rule_version, dict_sha): n}. A mixed tree is legible."""
        import collections
        out = collections.Counter()
        for prod, st in self.stashes():
            for k in st.keys():
                if isinstance(k, dict):
                    out[(prod, k.get("rule_version"), k.get("dict_sha"))] += 1
        return out

    # -- the verb, delegated -------------------------------------------------

    def run_twp(self, prompts=None, **kw):
        """Measure. `prompts=None` means the prompts that will PAIR.

        Machinery lives in `runners.TWPRunner`; this is the handle.
        """
        from .runners import TWPRunner
        if prompts is None:
            prompts = self.neighbour_prompts()
            if not prompts:
                raise ValueError(
                    "%s has no declared neighbour with cells, so nothing measured "
                    "here could pair. Declare an edge first, or pass prompts "
                    "explicitly." % self.model_id)
        return TWPRunner(self).run(prompts, **kw)

    def load(self, **kw):
        """Put this checkpoint on a device. Returns a `runners.Loaded`.

        The same handle as `run_twp`, for the other verb: `run_twp` measures and
        writes; `load` hands back the loaded model so a caller can measure
        repeatedly without paying the load again. `malignment.serve` is why it
        exists -- an interactive `/slot` query is ~2.6 s against ~8 s cold, and
        only if something holds the model between requests.

        **The torch import stays inside the method**, exactly as `run_twp` does
        it, so this file keeps the property its docstring claims: importing
        `Checkpoint` imports no torch.

        **THE CALLER OWNS THE UNLOAD**, which is the whole point. See
        `runners.load_for_twp`.
        """
        from .runners import load_for_twp
        return load_for_twp(self, **kw)

    def probs(self, prompt, loaded=None, **kw):
        """The twp word distribution at this prompt. `{surface: probability}`.

        **WANTED BY RH VIA `MANIFEST.md`, AND THE GAP HAD ALREADY COST ME.**
        `malignment.serve._slot` composed `load()` + `twp.expand` by hand, which
        made it a SECOND place the instrument is reached -- the exact thing my
        own [6358] extraction removed from the archive, reintroduced by me one
        level up. A missing method is not a missing convenience; it is an
        invitation to a second path, and the second path is always the one
        without the guards.

        Returns `(words, residual)`. `words` is keyed on the SURFACE with mass
        summed across token paths, because a word reachable by several paths
        gets one row per path from `expand` and a caller that ignores that is
        under-counting: 20.4% of source cells contain a duplicated surface.

        **`loaded=` REUSES AN ALREADY-RESIDENT MODEL AND IS NOT AN OPTIMISATION
        DETAIL.** A server holding models across requests must not reload per
        call, and a `probs()` that always loaded would force it to keep its own
        composition -- which is how this duplication started. Pass a
        `runners.Loaded`; omit it and this loads, measures and frees.

        `SkipPrompt` PROPAGATES. twp refuses a prompt that does not survive the
        model's own tokenizer, and that refusal is an answer about the prompt.
        Swallowing it here would return an empty distribution, which reads as
        "this model says nothing" rather than "this model cannot be asked".
        """
        from . import twp as T
        own = loaded is None
        ld = loaded if loaded is not None else self.load(**kw)
        try:
            w, res, _calls = T.expand(ld.model, ld.tok, prompt, ld.dev, ld.bmask,
                                      cjk=ld.cjk, bos_policy=ld.bos_policy)
        finally:
            if own:
                #: Drop OUR references, then free. `T.free` takes arguments and
                #: cannot use them -- see its docstring. Only the caller that
                #: loaded may free; a passed-in `Loaded` belongs to whoever
                #: holds it.
                ld = None
                T.free()
        out = {}
        for (surface, _t1), mass in w.items():
            out[surface] = out.get(surface, 0.0) + float(mass)
        return out, res

    def gen_dir(self):
        """`<GEN_OUT>/<model>/` -- the generations twin of `dir`."""
        from .generate import GEN_OUT
        safe = self.model_id.replace("/", "__").replace("@", "__at__")
        return os.path.join(GEN_OUT, safe)

    def gen_stash(self, producer=None):
        """This checkpoint's generation stash, for ONE producer.

        Same engine and layout as `stash()`: jsonl, flat, ABSOLUTE root_dir --
        a bare name resolves to `~/.cache/hashstash/`, which is the trap
        `stash()`'s docstring records walking into.
        """
        from hashstash import HashStash
        from .runners import PRODUCER
        return HashStash(root_dir=os.path.join(self.gen_dir(), producer or PRODUCER),
                         engine="jsonl", flat=True)

    def gen_stashes(self):
        """Every producer's generation stash. READS must see all of them.

        Writes go to ours; reads span the lot, for the reason `stashes()` gives:
        a cache written on the other machine is not a cache miss, and treating
        it as one regenerates work that already exists and costs money or GPU.
        """
        d = self.gen_dir()
        if not os.path.isdir(d):
            return []
        return [self.gen_stash(p) for p in sorted(os.listdir(d))
                if os.path.isdir(os.path.join(d, p))]

    def generate(self, text, n=1, system=None, user=None, prefill=False,
                 user_msg="Hi.", template=None, seed=None, decoder=None,
                 loaded=None, cache=True, **kw):
        """Sample `n` continuations. -> [generate.Passage], length `n`.

        The third verb on the one loader, beside `run_twp` (measure and write)
        and `probs` (measure and return). Machinery is in `generate.py`; this is
        the handle, exactly as `run_twp` is the handle to `TWPRunner`.

        ## THE CACHE FILLS THE SHORTFALL AND LOADS NOTHING IT DOES NOT NEED

        `n=10` with 9 already stored returns the 9 and generates ONE. `n=10`
        with 10 stored **never touches a GPU** -- the load is lazy and happens
        only if something is missing. That is the point of keying on
        `sample_idx`: samples are addressable individually, so a shortfall is a
        shortfall and not a rerun.

        Reads span every producer's stash; writes go to ours. A passage
        generated on the other machine is not a cache miss.

        ## WHAT MAKES TWO DRAWS THE SAME DRAW

        See `generate.gen_key`. Model, prompt, frame, system hash, the RESOLVED
        decoder, seed and sample_idx. Change the temperature and you are asking
        a different question, so you get a different cell rather than a stale
        hit.

        `cache=False` bypasses both read and write, for a caller who wants a
        fresh draw and does not want it stored.
        """
        from . import generate as G
        if system is None:
            #: `None` from a caller means "leave the template alone", which is
            #: G.DEFAULT. `system=""` stays an explicit empty one -- the two are
            #: 2,500x apart on a measured stem and must not collapse here.
            system = G.DEFAULT
        dec = dict(G.DECODER)
        dec.update(decoder or {})
        frame = G.frame_label(system, user, prefill, template)
        #: the KEY carries every slot, not just the label: two combinations can
        #: share a label and differ in the strings, and a cache that ignored
        #: that would hand back the wrong condition.
        sysk = "" if system is G.DEFAULT else system
        keys = [dict(G.gen_key(self.model_id, text, frame, sysk, dec, seed, i,
                               system_set=(system is not G.DEFAULT)),
                     user=user, prefill=bool(prefill),
                     user_msg=(user_msg if prefill else None),
                     template=template)
                for i in range(n)]

        out = [None] * n
        if cache:
            for st in self.gen_stashes():
                for i, k in enumerate(keys):
                    if out[i] is not None:
                        continue
                    try:
                        rec = st.get(k)
                    except Exception:
                        rec = None
                    if rec:
                        out[i] = G.Passage(**rec)
        missing = [i for i, v in enumerate(out) if v is None]
        if not missing:
            return out

        own = loaded is None
        ld = loaded if loaded is not None else self.load(**kw)
        try:
            wst = self.gen_stash() if cache else None
            for i in missing:
                #: seeded PER SAMPLE INDEX, not per call, so sample 7 is sample 7
                #: whether it was made now or in a previous run -- otherwise a
                #: shortfall fill would draw a different distribution from the
                #: cached siblings it joins.
                p = G.generate(ld, text, n=1, system=system, user=user,
                               prefill=prefill, user_msg=user_msg,
                               template=template,
                               seed=None if seed is None else seed + i,
                               decoder=dec)[0]
                out[i] = p
                if wst is not None:
                    wst[keys[i]] = p._asdict()
        finally:
            if own:
                from . import twp as T
                ld = None
                T.free()
        return out

    def generations(self, prompt=None, frame=None, system=None, **match):
        """Every generation cached for this checkpoint. -> iterator of Passage

        The stash IS the record. Nothing needs to keep a second copy in a JSON
        beside it, and a run that wrote one had two stores to keep in step --
        which is the shape of a divergence nobody notices until they disagree.

        Reads span EVERY producer, so a passage generated on the other machine
        is visible here. Order is by producer then by write time within a
        producer; it is not a meaningful order and nothing should depend on it.

        Filters are exact matches against the stored KEY, so they name the
        condition rather than guessing at it:

            ck.generations()                          everything
            ck.generations(frame="raw")               one arm
            ck.generations(prompt=stem, seed=7)       one cell's samples
            ck.generations(sample_idx=0)              first draw of each

        `system=` matches the STORED TEXT, not its hash, so a caller can ask
        for the condition it ran without recomputing a digest.

        Each yielded Passage carries its key under `extra["__key__"]`, so the
        condition survives into anything built from the iterator.
        """
        from .passage import Passage
        want = dict(match)
        if prompt is not None:
            want["prompt"] = prompt
        if frame is not None:
            want["frame"] = frame
        for st in self.gen_stashes():
            for k, v in st.items():
                if not isinstance(v, dict) or "text" not in v:
                    continue
                #: match against the KEY first, then the record, because some
                #: fields live in one and some in the other (`system` is text
                #: on the record and a sha in the key).
                merged = dict(k if isinstance(k, dict) else {}, **v)
                if system is not None and merged.get("system") not in (system,):
                    continue
                if any(merged.get(f) != val for f, val in want.items()):
                    continue
                p = Passage.from_row(v)
                p.extra["__key__"] = k
                yield p

    def next_token(self, text, k=10, system=None, user=None, prefill=False,
                   user_msg="Hi.", loaded=None, **kw):
        """Top-`k` next-TOKEN distribution. -> ([(token, prob)], vocab_size)

        Tokens, not words -- see `next_word`, which is the instrument for any
        question about vocabulary. This one shows the tokenizer's units, so a
        word split across two tokens appears as its first piece.
        """
        from . import generate as G
        own = loaded is None
        ld = loaded if loaded is not None else self.load(**kw)
        try:
            if system is None:
                system = G.DEFAULT
            return G.next_token(ld, text, k=k, system=system, user=user,
                                prefill=prefill, user_msg=user_msg)
        finally:
            if own:
                from . import twp as T
                ld = None
                T.free()

    def next_word(self, prompt, loaded=None, **kw):
        """The twp WORD distribution at `prompt`. -> ({surface: prob}, residual)

        A name for what `probs` already does, because `probs` does not say which
        grain it is on and this file now has a `next_token` beside it. Same
        method, same guards; `probs` is kept so existing callers do not break.
        """
        return self.probs(prompt, loaded=loaded, **kw)

    def status(self):
        """Everything cheap, in one dict. For a human deciding what to run."""
        return {"model": self.model_id, "revision": self.revision,
                "declared": self.declared, "lineage": self.lineage,
                "parents": self.parents, "children": self.children,
                "cells_in_store": self.cells,
                "jsonl": self.path if os.path.exists(self.path) else None,
                "done": len(self.done()), "skipped": len(self.skipped())}
