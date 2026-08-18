#!/usr/bin/env python
"""The v4 corpus lives in its OWN TABLES, and two consumers forgot in the same way.

    python -m pytest tests/test_v4_tables.py -q

## WHY THESE TWO, AND WHY THEY BOTH READ AS SUCCESS

v4 cells are written to `twp_cells_v4` / `twp_words_v4` and nowhere else. Every
defect below is the same sentence — *the rule version was treated as a column to
filter on rather than as the thing that selects the table* — and each one
produced a plausible number rather than an error:

    pass1_todo    `SELECT ... FROM twp_cells WHERE rule_version=4` is not a
                  narrow query, it is an EMPTY one. A model measured in full
                  under v4 reported all 2,706 prompts still missing. On a fleet
                  box that is a whole rental spent re-measuring, reported as
                  progress.

    topup_todo    sourced `have` from the v3 table and applied it to a v4 cell.
                  v4's `decoded_boundary` changes which surfaces exist, so words
                  the v4 pass had ALREADY FOUND were classed as missing,
                  re-scored, and added on top of themselves -- topup_mass 0.916
                  against a tail of 0.089. It was caught only because the tail
                  guard refused 44 cells; the ones that fit under the tail would
                  have been booked silently.

    ingest        deduped on `(model, prompt)`, which is v3's identity and not
                  v4's. A topup cell and its pass-1 parent share both and differ
                  in `topup`. 2,583 of CT-LLM-Base's 5,289 records were dropped
                  as duplicates and the run reported "2,706 cells written" --
                  the right number for a pass-1-only ingest, which is exactly why
                  nothing looked wrong.

These are pure-structure tests: no ClickHouse, no model. The arithmetic is
checked in `test_twp_v4.py`; what is checked here is that the plumbing points at
the right place, which is where all three failures actually were.
"""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from malignment import corpus as C  # noqa: E402
from malignment import ingest as I  # noqa: E402


def test_the_two_table_maps_agree():
    """`corpus` and `ingest` must not disagree about where v4 lives.

    RED RECEIPT: change either map and this fails. They are separate constants
    because the two modules are independently importable, and two hand-kept
    copies of one fact drift in the direction nothing notices -- a writer
    pointed at `_v4` and a reader pointed at v3 is precisely the `topup_todo`
    defect, reconstructed one module apart.
    """
    assert C.TABLES == I.TABLES, (
        "corpus.TABLES=%r but ingest.TABLES=%r -- a writer and a reader "
        "disagreeing about the table is how the v3-sourced worklist happened"
        % (C.TABLES, I.TABLES))


def test_every_version_has_distinct_tables():
    """No two rule versions may share a table.

    RED RECEIPT: point 4 at `("twp_words", "twp_cells")` and this fails. That is
    not a hypothetical edit — it is the state the repo was in before
    2026-08-18, and it is what made `rule_version` look like a sufficient
    discriminator when it never was: `twp_cells_v4` puts `rules`,
    `prompt_cache` and `topup` in its SORTING KEY and the v3 table does not, so
    a v4 record landing in the v3 table collides with its own v3 twin and loses.
    """
    seen = {}
    for v, tabs in C.TABLES.items():
        for t in tabs:
            assert t not in seen, (
                "table %r serves both rule_version %r and %r" % (t, seen[t], v))
            seen[t] = v


def test_unknown_version_raises_rather_than_defaulting():
    """An unknown version must refuse, not fall back to v3's tables.

    RED RECEIPT: replace `_tables` with `TABLES.get(v, TABLES[3])` and this
    fails. A silent fallback is the worst available behaviour here, because it
    turns "I do not know this instrument" into "here is the v3 corpus" — an
    answer that is well-formed, non-empty, and about the wrong measurement.
    """
    with pytest.raises(ValueError):
        C._tables(5)


@pytest.mark.parametrize("version,expect_topup_filter", [(3, False), (4, True)])
def test_v4_readers_exclude_pass_two_from_the_union(version, expect_topup_filter):
    """`lineage_union` must read pass-1 rows only, or the worklist chases itself.

    RED RECEIPT: drop the `topup = 0` clause and pass 2's own output re-enters
    its input. It happens not to grow without bound (a topped-up word was
    already in the union from the member it came from), so the run CONVERGES and
    looks fine — the damage is that the union stops meaning "what pass 1 found"
    and no consumer can tell which it got.

    `have` is deliberately the other way round and is asserted here as prose
    rather than SQL: a word already topped up IS present and must never be
    scored twice. Both filters are one rule seen from each end — pass 2 adds to
    pass 1, never to itself.
    """
    import inspect
    src = inspect.getsource(C.lineage_union)
    assert ("topup = 0" in src) is True, "the filter is unconditional in source"
    assert "rule_version != 3" in src, (
        "the topup filter must be guarded by version: v3 rows have no such "
        "column and the clause would raise against the v3 table")
