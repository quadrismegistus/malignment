"""Read accessors for the ClickHouse store. Being dissolved — import from the new homes.

    ch.TABLES, ch.retable, ch._tables, ch._lit
    prompts.PAIRS_POPULATION, prompts.panel, prompts.domains, prompts.prompt_map
    prompts.domain_conflicts, prompts._rows_by_text
    movement.measured_models, movement.measured_pairs, movement.movement_rows
    movement.endpoint_movement, movement.movement_pairs_list

The runner functions (topup_todo, pass1_todo, stash_union, lineage_union) stay
here until runners.py absorbs them — circular import risk otherwise.
"""
import functools

from . import ch

# Re-exports for backward compatibility — update your imports.
from .ch import TABLES, retable, _tables, _lit  # noqa: F401
from .prompts import (PAIRS_POPULATION, panel, _rows_by_text,  # noqa: F401
                      domain_conflicts, domains, prompt_map)
from .movement import (measured_models, measured_pairs,  # noqa: F401
                       movement_pairs_list as movement_pairs,
                       movement_rows, endpoint_movement)


def movement(base, aligned, prompt=None, cls=None, min_abs_delta=None,
             limit=None, rule_version=3):
    return movement_rows(base, aligned, prompt=prompt, cls=cls,
                         min_abs_delta=min_abs_delta, limit=limit,
                         rule_version=rule_version)


# ---------------------------------------------------------------------------
# Runner functions — stay here until runners.py absorbs them
# ---------------------------------------------------------------------------

def _stash_words(model, prompts=None, rules=None):
    """{prompt: set(words)} this ONE model has, from its stash, INCLUDING topup.

    Asymmetric to the union on purpose and for the same reason as the ClickHouse
    path: a word measured anywhere must never be rescored, so `have` counts
    topup rows while the union does not.
    """
    import os
    import glob
    import json as _json
    from .checkpoint import Checkpoint
    base = Checkpoint(model).dir
    want = set(prompts) if prompts else None
    out = {}
    for path in glob.glob(os.path.join(base, "*", "jsonl.hashstash.raw", "data.jsonl")):
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                if '"rules"' not in line:
                    continue
                try:
                    d = _json.loads(line)
                except ValueError:
                    continue
                k = d.get("__key__") or {}
                if rules and k.get("rules") != rules:
                    continue
                p = k.get("prompt")
                if p is None or (want is not None and p not in want):
                    continue
                out.setdefault(p, set()).update(
                    r.get("word") for r in (d.get("rows") or ()))
    return out


def stash_union(root, prompts=None, ops=None, producer=None, rules=None):
    """{prompt: set(words)} for a lineage, read from the LOCAL STASH.

        corpus.stash_union("kakaocorp/kanana-1.5-8b-base")

    **A FLEET BOX HAS NO CLICKHOUSE, AND `lineage_union` ASKS CLICKHOUSE.**
    `pass1_todo`'s docstring has warned about this shape since it was written --
    "a fresh rental has none, so a box asked to run what is missing re-measures
    everything" -- and sharding by lineage was adopted precisely so a box could
    compute its own union. But the code still queried the corpus, so the first
    real rental died on `FileNotFoundError: /opt/homebrew/bin/clickhouse`, a
    macOS path, on a Linux box, during pass 2. The design was right and the
    implementation never followed it.

    Reads every member's stash directly, across ALL producer directories: cells
    shipped from another machine sit under that machine's producer name, and they
    are exactly the ones a box needs to build the union it did not measure
    itself.

    Pass-1 rows only (`topup` false), same rule as `lineage_union`: pass 2 must
    not chase its own output.
    """
    import os
    import glob
    import json as _json
    from . import roster
    from .checkpoint import Checkpoint
    members = roster.lineages(ops=ops or roster.ALIGNING).get(root)
    if not members:
        raise KeyError("%s is not a lineage root -- see roster.lineages()" % root)
    want = set(prompts) if prompts else None
    out = {}
    for m in sorted(members):
        base = Checkpoint(m).dir
        for path in glob.glob(os.path.join(base, "*", "jsonl.hashstash.raw",
                                           "data.jsonl")):
            with open(path, encoding="utf-8") as fh:
                for line in fh:
                    if '"rules"' not in line:
                        continue
                    try:
                        d = _json.loads(line)
                    except ValueError:
                        continue
                    k = d.get("__key__") or {}
                    if rules and k.get("rules") != rules:
                        continue
                    if k.get("topup"):
                        continue
                    p = k.get("prompt")
                    if p is None or (want is not None and p not in want):
                        continue
                    out.setdefault(p, set()).update(
                        r.get("word") for r in (d.get("rows") or ()))
    return out


def lineage_union(root, prompts=None, ops=None, rule_version=4):
    """{prompt: set(words)} -- every word ANY member of this lineage cleared.

        corpus.lineage_union("meta-llama/Llama-3.1-8B")

    **THIS IS PASS 2's INPUT AND ITS COST.** `expand` gates on `P0 >= theta`, so a
    word below the gate on one model is ABSENT from that cell and every consumer
    imputes zero. Across the declared pairs that is ~34 base-only and ~18
    aligned-only words per cell -- an asymmetry running 2:1, because alignment
    concentrates and pushes words under the gate. The top-up measures them
    instead of imputing them.

    ## THE SCOPE IS THE LINEAGE, WHICH IS WHAT WE ACTUALLY COMPARE

    Not the pair: `tulu-sft` and `tulu-dpo` share a base and ARE compared, so a
    pair-scoped union misses them. Not all 160: cross-lineage comparisons are
    never made, and an all-models union costs ~8x more per cell (median 785 words
    against 95 present) for a common vocabulary almost nothing reads.

    Measured on the store, per prompt:

        words present per (model, prompt)   median  95
        union across ALL models             median 785   <- wrong scope
        union across a declared pair        median ~113

    `roster.lineages()` supplies the membership and enforces the rule that
    `scale` and `predecessor` RELATE lineages rather than deriving them.
    """
    from . import roster
    members = roster.lineages(ops=ops or roster.ALIGNING).get(root)
    if not members:
        raise KeyError("%s is not a lineage root -- see roster.lineages()" % root)
    wt, _ct = _tables(rule_version)
    ids = ",".join("'%s'" % m.replace("'", "\\'") for m in members)
    where = "model IN (%s)" % ids
    if rule_version != 3:
        where += " AND topup = 0"
    if prompts:
        ps = ",".join("'%s'" % p.replace("'", "\\'") for p in prompts)
        where += " AND prompt IN (%s)" % ps
    out = {}
    for r in ch.query("SELECT prompt, groupUniqArray(word) ws FROM {db}.%s "
                      "WHERE %s GROUP BY prompt" % (wt, where)):
        out[r["prompt"]] = set(r["ws"])
    return out


def topup_todo(model, root=None, ops=None, rule_version=4, prompts=None,
               from_stash=False):
    """{prompt: [words this model lacks that its LINEAGE has]} -- the pass-2 worklist.

    Exactly what `twp_v4.score_words4` should be handed. A word already present
    on this model was measured by `expand` and must NOT be rescored: the two are
    different measurements of the same surface -- beam-accumulated against
    single-path -- and replacing one with the other would silently change the
    instrument for words that never needed touching.

    **THE CALLER STILL OWES THE `tail` DECREMENT.** These words' mass sits in
    `tail` by construction, since they are sub-theta on this model. Writing them
    without subtracting breaks conservation, which is exactly 1.000000 on all
    984,857 stored cells.
    """
    from . import roster
    if root is None:
        for r, members in roster.lineages(ops=ops or roster.ALIGNING).items():
            if model in members:
                root = r
                break
        if root is None:
            raise KeyError("%s is in no lineage" % model)
    wt, _ct = _tables(rule_version)
    if from_stash:
        from . import twp_v4 as _V4
        lbl = _V4.ADOPTED.label()
        union = stash_union(root, prompts=prompts, ops=ops, rules=lbl)
        mine = _stash_words(model, prompts=prompts, rules=lbl)
        todo = {}
        for p_, words in union.items():
            missing = sorted(words - mine.get(p_, set()))
            if missing:
                todo[p_] = missing
        return todo
    union = lineage_union(root, ops=ops, rule_version=rule_version, prompts=prompts)
    have = {}
    for r in ch.query("SELECT prompt, groupUniqArray(word) ws FROM {db}.%s "
                      "WHERE model='%s' GROUP BY prompt"
                      % (wt, model.replace("'", "\\'"))):
        have[r["prompt"]] = set(r["ws"])
    todo = {}
    for p, words in union.items():
        missing = sorted(words - have.get(p, set()))
        if missing:
            todo[p] = missing
    return todo


def pass1_todo(model, rule_version=4, rules=None, prompts=None):
    """Prompts this model still needs, asked of CLICKHOUSE rather than a stash.

        corpus.pass1_todo("Qwen/Qwen2.5-7B")   -> [prompt, ...]

    **A FLEET BOX CANNOT COMPUTE THIS FOR ITSELF.** `Checkpoint.done()` reads the
    local stash and a fresh rental has none, so a box asked to "run what is
    missing" re-measures the entire prompt set and reports success -- the
    failure-that-looks-like-progress shape, at the cost of a whole rental.

    So the worklist is computed where the knowledge is: ClickHouse holds every
    ingested cell, and the difference against `Prompts.all()` is what the box
    should be handed via `runners --prompts FILE`.

    **IT ASKS ABOUT THE INSTRUMENT, NOT JUST THE PROMPT.** A v3 cell does not
    satisfy a v4 run; `rule_version` and `rules` are part of what "done" means,
    exactly as they are in `Checkpoint.key`. Passing `rule_version=3` asks the v3
    question instead.
    """
    from .prompts import Prompts
    want = prompts if prompts is not None else sorted({p.text for p in Prompts.all()})
    _wt, ct = _tables(rule_version)
    q = ("SELECT DISTINCT prompt FROM {db}.%s WHERE model=%s AND rule_version=%d"
         % (ct, _lit(model), int(rule_version)))
    if rule_version != 3:
        q += " AND topup = 0"
    if rules:
        q += " AND rules=%s" % _lit(rules)
    have = {r["prompt"] for r in ch.query(q)}
    return [p for p in want if p not in have]
