#!/usr/bin/env python
"""Cross-tier and derived-store invariants.

    python -m pytest tests/test_roster_invariants.py -q

**Every test here carries its red receipt in its docstring** — the commit or the
constructed input at which it fails. See `tests/README.md` for why that is a
hard rule rather than a nicety.
"""
import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from malignment import roster  # noqa: E402

#: The commit that FIXED the fabricated stablelm edge. Its parent is the last
#: tree in which the topology check has a real defect to find, and the two
#: tests below stand or fall on that being true.
FIX_COMMIT = "b265bc9"


def _edges_at(rev):
    """The authored edge list as of `rev`, or None if git cannot reach it."""
    import yaml
    try:
        blob = subprocess.run(
            ["git", "-C", ROOT, "show", "%s:roster/models/models.yaml" % rev],
            capture_output=True, text=True, check=True).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return [tuple(e) for e in (yaml.safe_load(blob).get("edges") or [])]


# --------------------------------------------------------------------------
# TIER 1 — cross-tier invariants
# --------------------------------------------------------------------------

def test_topology_check_fires_on_the_known_positive():
    """RED RECEIPT for the test below. At `b265bc9^` this MUST report stablelm.

    Without this, `test_attested_parent_matches_authored_edge` is a green
    assertion that has never been shown capable of failing — which is the exact
    shape of the three checkers this repo shipped that read clean on the case
    they existed for. **The check is parameterised by `edges` so that it can be
    aimed at a broken roster; that parameter exists for this test.**
    """
    old = _edges_at(FIX_COMMIT + "^")
    if old is None:
        pytest.skip("git history unavailable")
    problems, checkable = roster.check_attested_topology(edges=old)
    assert checkable > 0, "nothing was checkable at %s^ — the check is inert" % FIX_COMMIT
    assert any("zephyr" in p for p in problems), (
        "the check did NOT fire on the fabricated stablelm edge; it cannot be "
        "trusted on the current tree either. Got: %s" % problems)


def test_attested_parent_matches_authored_edge():
    """No authored parent contradicts that checkpoint's own attested quote.

    RED at `b265bc9^` — see the test above, which asserts exactly that.

    `checkable` is asserted non-zero because **silence here is not a clean bill**:
    if the quote format changed, or attestations stopped carrying URLs, this
    would pass by finding nothing to look at.
    """
    problems, checkable = roster.check_attested_topology()
    assert checkable > 0, "no attestation carried a parseable parent quote"
    assert problems == [], "\n".join(problems)


def test_endpoint_rulings_are_live():
    """Every `rulings.endpoint` entry still decides something, and decides it right.

    RED receipt is the test below, which doctors a dead ruling in and requires
    it to be reported. A ruling that decides nothing still READS as in force,
    which is a guard killed by a field shift.
    """
    assert roster.check_authored() == []


def test_a_dead_ruling_is_reported():
    """RED RECEIPT for the test above. A ruling on a chain-resolved base must
    be reported STALE or CONTRADICTED, never silently dropped.

    Written because the FIRST version of this staleness check could not have
    passed it: it read the post-ruling `endpoints()` and so inferred the
    pre-ruling state through the very thing it was checking, reporting a working
    ruling as stale and a dead one as fine. `apply_rulings=False` exists for it.
    """
    d = roster.load()
    chain, unres = roster.endpoints(apply_rulings=False)
    settled = [b for b in chain if b not in unres]
    if not settled:
        pytest.skip("no chain-resolved base to hang a dead ruling on")
    b = settled[0]
    hacked = dict(d)
    hacked["rulings"] = dict(d.get("rulings") or {},
                             endpoint={b: {"endpoint": chain[b]}})
    saved = roster.load
    roster.load = lambda *a, **k: hacked
    try:
        problems = roster.check_authored()
    finally:
        roster.load = saved
    assert any("STALE RULING" in p or "CONTRADICTED" in p for p in problems), (
        "a ruling on a base the chain already settles was not reported: %s"
        % problems)


def test_a_ruling_naming_a_non_candidate_raises():
    """`endpoints()` refuses a ruling that resolves to nothing. Constructed red.

    The failure mode being excluded: a ruling silently doing nothing would leave
    the lineage in `unresolved` while the file reads as decided.
    """
    d = roster.load()
    ruled = (d.get("rulings") or {}).get("endpoint") or {}
    real = [b for b in ruled if not b.startswith("_")]
    if not real:
        pytest.skip("no endpoint ruling declared")
    base = real[0]
    hacked = dict(d)
    hacked["rulings"] = dict(d["rulings"],
                             endpoint={base: {"endpoint": "not-a/model"}})
    saved = roster.load
    roster.load = lambda *a, **k: hacked
    try:
        with pytest.raises(ValueError, match="not one of that base's candidates"):
            roster.endpoints()
    finally:
        roster.load = saved


# --------------------------------------------------------------------------
# TIER 2 — derived-store freshness
# --------------------------------------------------------------------------

def test_pairs_is_not_stale():
    """`{db}.pairs` matches the edges it is derived from.

    RED for a full day in the real repo: `pairs` sat at 146 rows after
    `distill_align` (d9b33aa) took the roster to 151, and **the count stayed
    plausible the whole time** — it surfaced only because an unrelated one-edge
    edit moved the total by +5 instead of −1. A count is not a freshness test;
    this is set difference in both directions.
    """
    problems = roster.check_derived()
    assert problems == [], "\n".join(problems)


def test_freshness_check_detects_a_missing_pair():
    """RED RECEIPT for the test above, constructed rather than historical.

    Removing one pair from the producer's own definition must be reported. If
    this passes with a doctored input, the real check is measuring nothing.
    """
    from malignment import produce_movement
    real = produce_movement.buildable
    full = real()
    if len(full) < 2:
        pytest.skip("not enough pairs to drop one")
    produce_movement.buildable = lambda: full[1:]
    try:
        problems = roster.check_derived()
    finally:
        produce_movement.buildable = real
    assert any("ORPHAN" in p for p in problems), (
        "dropping a pair from the roster side was not reported: %s" % problems)
