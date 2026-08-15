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

from . import twp as T


class Checkpoint:
    """One checkpoint, addressable as `repo` or `repo@revision`."""

    def __init__(self, model_id, out=None):
        self.model_id = model_id
        self.repo = T._repo_of(model_id)
        self.revision = T._revision_of(model_id)
        self._out = out

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
    def out(self):
        from .runners import TWP_OUT
        return self._out or TWP_OUT

    @property
    def path(self):
        """Where this checkpoint's jsonl lives."""
        safe = self.model_id.replace("/", "__").replace("@", "__at__")
        return os.path.join(self.out, "%s.jsonl" % safe)

    def _records(self):
        """Every parseable record in the jsonl. Tolerates a truncated last line."""
        if not os.path.exists(self.path):
            return
        with open(self.path, encoding="utf-8") as fh:
            for ln in fh:
                try:
                    yield json.loads(ln)
                except ValueError:
                    continue      # partial line from a kill: it will be redone

    def done(self):
        """Prompts with a REAL result THIS INSTRUMENT WOULD PRODUCE TODAY.

        Two conditions, and the second was missing:

        **A SKIP IS AN ATTEMPT, NOT A RESULT.** twp writes `rows: []` plus a
        reason when a prompt does not survive the model's own tokenizer. Counting
        those as done means a tokenizer fix installs cleanly and recovers
        nothing.

        **AND A RESULT FROM A DIFFERENT INSTRUMENT IS NOT A RESULT.** `done()`
        gated only on rows, while the INGEST requires `rule_version == 3`. So
        bumping the rule -- or changing the dictionary, which moves `dict_sha` --
        gave: done() reports every prompt complete, the runner writes nothing,
        the ingest then excludes every old-rule record, and the checkpoint
        VANISHES from ClickHouse while the run prints success. Two independent
        components each behaving sensibly, and the gap between them is silent.

        Matching the ingest's own predicate here means a rule bump automatically
        re-offers every prompt, with nothing to remember.
        """
        from .ingest import RULE_VERSION
        cur = T.dict_sha()
        seen = set()
        for r in self._records():
            if r.get("skipped") or not r.get("rows"):
                continue
            if r.get("rule_version") != RULE_VERSION:
                continue
            #: dict_sha absent = predates the stamp; treat as a different
            #: instrument rather than assuming it matches.
            if r.get("dict_sha") != cur:
                continue
            seen.add(r["prompt"])
        return seen

    def provenance(self):
        """What instruments produced this file. A mixed file is legible, not fatal.

        Running the same checkpoint on prompts A-C and later D-F APPENDS to one
        file and `done()` unions them -- which is the intent. This is how you see
        whether the two halves were measured by the same instrument.
        """
        import collections
        out = collections.Counter()
        for r in self._records():
            out[(r.get("rule_version"), r.get("dict_sha"), r.get("device"))] += 1
        return out

    def skipped(self):
        """{prompt: reason} for prompts attempted and refused. These are NOT done."""
        out = {}
        if not os.path.exists(self.path):
            return out
        with open(self.path, encoding="utf-8") as fh:
            for ln in fh:
                try:
                    r = json.loads(ln)
                except ValueError:
                    continue
                if r.get("skipped"):
                    out[r["prompt"]] = r["skipped"]
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

    def status(self):
        """Everything cheap, in one dict. For a human deciding what to run."""
        return {"model": self.model_id, "revision": self.revision,
                "declared": self.declared, "lineage": self.lineage,
                "parents": self.parents, "children": self.children,
                "cells_in_store": self.cells,
                "jsonl": self.path if os.path.exists(self.path) else None,
                "done": len(self.done()), "skipped": len(self.skipped())}
