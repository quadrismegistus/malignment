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


# --------------------------------------------------------------------------
# TIER 1 (cont.) — a quote that exists is not a quote that says anything
# --------------------------------------------------------------------------

def test_unsupported_finds_what_unsourced_cannot():
    """RED RECEIPT, and it is the sibling check's blind spot, not a fixture.

    `unsourced()` reports **0** unsourced `safety_data` claims across the 100
    declared arms — a clean bill — while `unsupported()` finds 5 `present`
    claims whose own quote never mentions safety. Asserting both together is the
    point: the number that matters is that one is 0 while the other is not.
    """
    from malignment import attest, ch
    doc = attest.load()
    arms = {m for e in ch.query("SELECT base, endpoint FROM endpoints")
            for m in (e["base"], e["endpoint"])}
    unsourced_sd = [t for t in attest.unsourced(doc)
                    if t[0] in arms and t[1] == "safety_data"]
    assert unsourced_sd == [], "premise changed: unsourced() now flags safety_data"
    assert attest.unsupported(doc, models=arms), (
        "unsupported() found nothing where it previously found 5 — either the "
        "attestations were fixed (good, retire this) or the check went inert")


def test_unsupported_is_conditioned_on_the_value():
    """A NEGATIVE value must not be flagged for a quote that omits the term.

    Constructed red: an earlier pass counted 22 of 50 `safety_data` quotes as
    silent and that number was meaningless, because 16 were `absent` — where a
    mix-enumerating quote IS the evidence. If this test fails, the check has
    reverted to a field-level predicate on a value-level fact.
    """
    from malignment import attest
    doc = {"checkpoints": {
        "x/absent": {"claims": [{"field": "safety_data", "value": "absent",
                                 "quote": "trained on math, code and chat data"}]},
        "x/present_ok": {"claims": [{"field": "safety_data", "value": "present",
                                     "quote": "we include safety data"}]},
        "x/present_bad": {"claims": [{"field": "safety_data", "value": "present",
                                      "quote": "a model for instruction following"}]}}}
    got = {m for m, _f, _v, _q in attest.unsupported(doc)}
    assert got == {"x/present_bad"}, got


def test_lineages_do_not_follow_relating_edges():
    """`scale` and `predecessor` RELATE lineages; they do not derive them.

    RED RECEIPT: walk every edge instead of `ALIGNING` and this fails on Olmo-3.
    `models.yaml` states the rule -- *"relating (NOT deriving): scale |
    predecessor"* -- and nothing enforced it, so the first hand-walk of the edge
    list for the v4 union produced a FIFTEEN-model OLMo lineage by following
    `Olmo-3-1025-7B <- predecessor <- OLMo-2-0425-1B`. Two different pretraining
    runs merged because one succeeds the other.
    """
    L = roster.lineages()
    assert "allenai/Olmo-3-1025-7B" in L, (
        "Olmo-3 is not a root -- a relating edge is being followed as a parent")
    assert "allenai/OLMo-2-0425-1B" in L, "OLMo-2 is not a root"
    assert len(L["allenai/OLMo-2-0425-1B"]) < 10, (
        "OLMo-2 has %d members; it absorbed a successor run"
        % len(L["allenai/OLMo-2-0425-1B"]))


def test_lineages_keep_siblings_together():
    """A lineage is the SIBLING SET, which `endpoints()` collapses to one row.

    RED RECEIPT: implement this over `endpoints()` and it returns 2 for Llama,
    not 11. The four-way comparison the campaign rests on -- base against
    instruct, against tulu-sft, against tulu-dpo, against the no-safety ablation
    -- is four children of ONE root, and `endpoints()` reports one endpoint per
    lineage by construction.
    """
    L = roster.lineages()
    llama = L.get("meta-llama/Llama-3.1-8B", [])
    assert len(llama) >= 10, "Llama-3.1-8B has %d members, expected ~11" % len(llama)
    for want in ("meta-llama/Llama-3.1-8B-Instruct",
                 "allenai/Llama-3.1-Tulu-3-8B-DPO"):
        assert want in llama, "%s is not in the Llama lineage" % want


def test_every_node_is_in_exactly_one_lineage():
    """Partition, not a cover. A root with no children is a lineage of one.

    RED RECEIPT: drop the `setdefault` root case and childless roots vanish --
    silently, since the total only falls by the number of such nodes and nothing
    reports it. A lineage of one is a fact about the publisher, not an absence.
    """
    L = roster.lineages()
    seen = [m for v in L.values() for m in v]
    assert len(seen) == len(set(seen)), "a node appears in two lineages"
    assert len(seen) == len(roster.population("all")), (
        "%d nodes across lineages, %d declared" % (len(seen), len(roster.population("all"))))


def test_lineages_measured_filter_runs():
    """`measured=True` must EXECUTE, not just parse.

    RED RECEIPT: the first version called `_measured_ids()`, a helper that does
    not exist. It raised NameError for anyone who passed the argument, and the
    three tests written beside it all left the default -- **a keyword nobody
    exercises is a keyword nobody has tested**, and the parameter list makes it
    look supported.
    """
    all_l = roster.lineages()
    got = roster.lineages(measured=True)
    assert isinstance(got, dict)
    n_all = sum(len(v) for v in all_l.values())
    n_got = sum(len(v) for v in got.values())
    assert 0 < n_got <= n_all, "measured=True kept %d of %d" % (n_got, n_all)
