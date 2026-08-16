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

    def key(self, prompt):
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
        """
        from . import twp as T
        from .ingest import RULE_VERSION
        return {"model": self.model_id, "prompt": prompt,
                "rule_version": RULE_VERSION, "dict_sha": T.dict_sha()}

    @property
    def paths(self):
        """Every `data.jsonl` for this checkpoint, one per producer."""
        return [st.path for _, st in self.stashes()]

    def done(self):
        """Prompts measured BY THIS INSTRUMENT, across every producer.

        A skip is an attempt, not a result: `runners` records refusals in a
        sidecar and writes NO key for them, so a tokenizer fix re-offers the
        prompt instead of finding it done -- the failure that would have left
        internlm2's 402 recovered prompts unmeasured.
        """
        from . import twp as T
        from .ingest import RULE_VERSION
        want = (RULE_VERSION, T.dict_sha())
        out = set()
        for _, st in self.stashes():
            for k in st.keys():
                if not isinstance(k, dict):
                    continue
                if (k.get("model") == self.model_id
                        and (k.get("rule_version"), k.get("dict_sha")) == want):
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

    def status(self):
        """Everything cheap, in one dict. For a human deciding what to run."""
        return {"model": self.model_id, "revision": self.revision,
                "declared": self.declared, "lineage": self.lineage,
                "parents": self.parents, "children": self.children,
                "cells_in_store": self.cells,
                "jsonl": self.path if os.path.exists(self.path) else None,
                "done": len(self.done()), "skipped": len(self.skipped())}
