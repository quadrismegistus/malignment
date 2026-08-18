#!/usr/bin/env python
"""What the store HOLDS. The read accessors, so an experiment writes no SQL.

    from malignment import corpus

    n, prompts = corpus.panel()          # crossed over the pairs population, live-gated
    corpus.prompt_map()                  # prompt_key -> id, domain, subdomain, text
    corpus.measured_pairs()              # (base, aligned) present in `movement`
    corpus.measured_models()

## WHY THIS EXISTS, AND IT IS THE SAME LESSON TWICE IN ONE DAY

On 2026-08-16 `panel()` was written into `division_of_labour/lexical_domains`
and then COPY-PASTED into `division_of_labour/removal_rates` -- the exact
duplication `roster.chains()` had been consolidated to prevent, repeated hours
after the comment warning against it was written. The two copies were logically
identical and textually not, and **the docstring explaining why the status gate
exists survived in only one of them**. A rule whose reason is in the other file
is a rule someone deletes.

RH's question was sharper than the duplication: *does the repo require
experiments to hand-write SQL?* It did -- 29 SQL lines across four experiment
producers. That is what the archive's `Cell`/`Step` classes were for.

## FUNCTIONS RETURNING ROWSETS, NOT OBJECTS WRAPPING A CELL

The archive wrapped one cell at a time because its store was a key-value stash
that had to be assembled per cell. ClickHouse is not that: a query returns the
whole set, and `views.py` makes the argument already -- "ClickHouse aggregates
tens of millions of rows in well under a second". An object per cell would
reintroduce a Python loop over what SQL does once. So: named accessors,
returning tables.

**An experiment that needs SQL this module does not have should ADD IT HERE**,
not inline it -- the second copy is always the one without the docstring.
"""
import functools

from . import ch

PAIRS_POPULATION = """SELECT base FROM {db}.pairs
                      UNION DISTINCT SELECT aligned FROM {db}.pairs"""


def measured_models():
    """Every model with cells in `twp_words`."""
    return {r["model"] for r in
            ch.query("SELECT DISTINCT model FROM {db}.twp_words")}


def measured_pairs():
    """Every (base, aligned) present in `movement`."""
    return {(r["base"], r["aligned"]) for r in
            ch.query("SELECT DISTINCT base, aligned FROM {db}.movement")}


def panel(models=None, live=True, verbose=False):
    """(n_models, prompts) -- prompts held by EVERY model in the population.

    **NOT "all prompts".** Prompt sets are fleet-defined and do not nest: the
    universal intersection over all 402 measured models is ONE prompt; over the
    154 in `pairs` it is 2,190. A cross-model comparison on anything wider is
    comparing differently-composed batteries.

    **THE STATUS GATE IS APPLIED, NOT ASSUMED.** Building the panel from
    `twp_words` alone takes whatever was MEASURED, which is not the declared
    population -- it admitted `f11_reason_BOTH`, status
    `MIXED: ACTIVE/DISPUTED`, which `Prompts.all()` excludes. One prompt of
    1,760, and the defect is not its size: the panel was being defined by
    measurement history rather than by the declaration, and a seat struck that
    prompt for a reason.

    `models=None` means the pairs population. Pass an explicit set for a
    different population -- the step/ladder checkpoints, say, whose own crossed
    panel is 2,247 and shares only 473 prompts with this one.
    """
    if models is None:
        n = ch.scalar("SELECT count(DISTINCT base) FROM (%s) AS t"
                      % PAIRS_POPULATION.replace("base FROM", "base AS base FROM")
                      .replace("SELECT aligned", "SELECT aligned AS base"))
        rows = ch.query("""SELECT prompt FROM {db}.twp_words
            WHERE model IN (%s) GROUP BY prompt
            HAVING count(DISTINCT model) = %d""" % (PAIRS_POPULATION, n))
    else:
        ms = "','".join(m.replace("'", "\\'") for m in sorted(models))
        n = len(set(models))
        rows = ch.query("""SELECT prompt FROM {db}.twp_words
            WHERE model IN ('%s') GROUP BY prompt
            HAVING count(DISTINCT model) = %d""" % (ms, n))
    crossed = [r["prompt"] for r in rows]
    if not live:
        return n, crossed
    from .prompts import Prompts
    declared = {p.text for p in Prompts.all()}
    kept = [p for p in crossed if p in declared]
    if verbose and len(kept) != len(crossed):
        print("  panel: %d crossed, %d dropped by the status gate"
              % (len(crossed), len(crossed) - len(kept)))
    return n, kept


@functools.lru_cache(maxsize=1)
def _rows_by_text():
    """{prompt_text: [row, ...]} -- ALL declared rows, because texts repeat.

    2,783 declared rows are 2,706 distinct TEXTS: 73 texts appear more than
    once and **47 of those disagree about `domain`**. `He slammed her against
    the wall and` is `violence` under `setd_and_M_2` and `other` under
    `store_g004_B`. Collapsing to one row per text -- by dict comprehension, or
    by `setdefault` in a loop -- resolves that by ITERATION ORDER, silently, and
    every experiment stratifying by domain has been doing so.
    """
    import collections
    from .prompts import Prompts
    out = collections.defaultdict(list)
    for p in Prompts.all():
        out[p.text].append(p._row)
    return dict(out)


def domain_conflicts():
    """{text: {domain: [prompt_id, ...]}} for texts whose rows disagree.

    Reported, not resolved silently. A stratified result should say how many of
    its prompts sat here.
    """
    import collections
    out = {}
    for text, rows in _rows_by_text().items():
        by = collections.defaultdict(list)
        for r in rows:
            d = (r.get("domain") or "").strip()
            if d:
                by[d].append(r.get("prompt_id"))
        if len(by) > 1:
            out[text] = dict(by)
    return out


def domains(prompts=None, on_conflict="specific"):
    """{prompt_text: domain}. Deterministic, and the rule is declared.

    `on_conflict`:
      "specific"  prefer a named domain over the catch-all `other`; among
                  equals take the lexicographically first prompt_id, so the
                  answer does not depend on file order. THE DEFAULT, because
                  `other` is an absence of classification rather than a claim.
      "drop"      exclude conflicted texts entirely. The conservative choice for
                  a result that leans on domain.
      "first_id"  lowest prompt_id wins whatever it says.
    """
    keep = set(prompts) if prompts is not None else None
    conflicted = set(domain_conflicts())
    out = {}
    for text, rows in _rows_by_text().items():
        if keep is not None and text not in keep:
            continue
        cands = sorted((r.get("prompt_id") or "", (r.get("domain") or "").strip())
                       for r in rows if (r.get("domain") or "").strip())
        if not cands:
            continue
        if text in conflicted:
            if on_conflict == "drop":
                continue
            if on_conflict == "specific":
                named = [c for c in cands if c[1] != "other"]
                cands = named or cands
        out[text] = cands[0][1]
    return out


@functools.lru_cache(maxsize=1)
def prompt_map():
    """{prompt_text: row}. FIRST row by prompt_id, deterministically.

    **THE AUTHORED FILES ARE THE AUTHORITY AND `{db}.prompts` IS DOWNSTREAM.**
    The first version of this module read the ClickHouse table and moved 970
    rows -- prompts the declaration gives a domain came back as `other`,
    silently, inside a SHARED accessor every experiment was about to adopt. A
    read layer that changes the source of truth is worse than the inline SQL it
    replaces, because the inline copy at least showed which table it hit.
    """
    return {t: sorted(rows, key=lambda r: r.get("prompt_id") or "")[0]
            for t, rows in _rows_by_text().items()}


def lineage_union(root, prompts=None, ops=None):
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
    from . import ch
    from . import roster
    members = roster.lineages(ops=ops or roster.ALIGNING).get(root)
    if not members:
        raise KeyError("%s is not a lineage root -- see roster.lineages()" % root)
    ids = ",".join("'%s'" % m.replace("'", "\\'") for m in members)
    where = "model IN (%s)" % ids
    if prompts:
        ps = ",".join("'%s'" % p.replace("'", "\\'") for p in prompts)
        where += " AND prompt IN (%s)" % ps
    out = {}
    for r in ch.query("SELECT prompt, groupUniqArray(word) ws FROM {db}.twp_words "
                      "WHERE %s GROUP BY prompt" % where):
        out[r["prompt"]] = set(r["ws"])
    return out


def topup_todo(model, root=None, ops=None):
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
    from . import ch
    from . import roster
    if root is None:
        for r, members in roster.lineages(ops=ops or roster.ALIGNING).items():
            if model in members:
                root = r
                break
        if root is None:
            raise KeyError("%s is in no lineage" % model)
    union = lineage_union(root, ops=ops)
    have = {}
    for r in ch.query("SELECT prompt, groupUniqArray(word) ws FROM {db}.twp_words "
                      "WHERE model='%s' GROUP BY prompt" % model.replace("'", "\\'")):
        have[r["prompt"]] = set(r["ws"])
    todo = {}
    for p, words in union.items():
        missing = sorted(words - have.get(p, set()))
        if missing:
            todo[p] = missing
    return todo
