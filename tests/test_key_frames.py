"""`Checkpoint.key` gained frame fields. These assert it orphaned nothing.

The claim being tested is not "the new fields work" -- it is that **adding them
changed no key that already exists**. 984,857 v3 cells and 820,246 v4 cells are
addressed by keys built before these parameters existed, and a key is how the
stash is read: a changed key does not error, it silently reports the corpus as
unmeasured and re-offers every prompt.

`Checkpoint.key`'s own docstring records the last time this was nearly done --
"Adding a field unconditionally -- even one set to `None` -- would change every
v3 key and orphan 984,857 stored cells" -- so the discipline exists and this file
holds it in place.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from malignment import Checkpoint                                # noqa: E402
from malignment.generate import DEFAULT                          # noqa: E402
from malignment.twp_v4 import ADOPTED                            # noqa: E402

M = "allenai/Olmo-3-1025-7B"
P = "She slept and the house was"


def test_v3_key_is_exactly_four_fields():
    """The pre-existing v3 shape, field for field."""
    k = Checkpoint(M).key(P)
    assert set(k) == {"model", "prompt", "rule_version", "dict_sha"}, k


def test_v4_key_gains_nothing_from_the_frame_parameters():
    """`key(P, ADOPTED)` must be what it was before `frame=` existed."""
    k = Checkpoint(M).key(P, ADOPTED)
    assert set(k) == {"model", "prompt", "rule_version", "dict_sha",
                      "rules", "prompt_cache"}, k


def test_frame_absent_means_no_frame_fields():
    """The defaults must not smuggle a frame in.

    `system=DEFAULT` and `user_msg="Hi."` are truthy-ish values sitting in the
    signature; if they leaked into the key on their own, every existing cell
    would be orphaned by a caller who never mentioned a frame.
    """
    for k in (Checkpoint(M).key(P), Checkpoint(M).key(P, ADOPTED)):
        assert "frame" not in k
        assert "system" not in k
        assert "system_set" not in k
        assert "user_msg" not in k


def test_frame_present_adds_exactly_four_fields():
    k = Checkpoint(M).key(P, ADOPTED, frame="prefill")
    assert k["frame"] == "prefill"
    assert k["system"] == ""
    assert k["user_msg"] == "Hi."
    #: DEFAULT means the caller supplied nothing, so False -- NOT bool("").
    assert k["system_set"] is False


def test_system_set_distinguishes_none_from_empty():
    """The 2,500x pair. `""` and DEFAULT both render as an empty string.

    `conditions.py` measured a target word at .246 under the template's own
    persona and .106 under an explicitly empty system message. If the key cannot
    tell them apart it serves one condition's cells for the other's question.
    """
    ck = Checkpoint(M)
    none_supplied = ck.key(P, ADOPTED, frame="prefill", system=DEFAULT)
    empty_supplied = ck.key(P, ADOPTED, frame="prefill", system="")
    assert none_supplied["system"] == empty_supplied["system"] == ""
    assert none_supplied["system_set"] is False
    assert empty_supplied["system_set"] is True
    assert none_supplied != empty_supplied


def test_system_is_stored_whole_not_hashed():
    """A long system prompt must come back readable, not as a digest."""
    s = "You are a helpful assistant. " * 40
    k = Checkpoint(M).key(P, ADOPTED, frame="prefill", system=s)
    assert k["system"] == s


def test_prompt_cache_argument_overrides_the_global_without_changing_the_default():
    """The parameter is new; the default behaviour is not.

    `T.USE_PROMPT_CACHE` is a module global that sits IN the key, so `done()`
    answers about whichever population it happens to name -- measured
    2026-08-22, Olmo-3-7B-Instruct reports 0 prompts done with it off and 2,983
    with it on. The argument makes that sayable; omitting it must keep the old
    answer exactly.
    """
    from malignment import twp as T
    ck = Checkpoint(M)
    before = T.USE_PROMPT_CACHE
    try:
        T.USE_PROMPT_CACHE = True
        assert ck.key(P, ADOPTED)["prompt_cache"] is True
        assert ck.key(P, ADOPTED, prompt_cache=False)["prompt_cache"] is False
        T.USE_PROMPT_CACHE = False
        assert ck.key(P, ADOPTED)["prompt_cache"] is False
        assert ck.key(P, ADOPTED, prompt_cache=True)["prompt_cache"] is True
    finally:
        T.USE_PROMPT_CACHE = before


def test_a_framed_key_never_equals_an_unframed_one():
    """The property the whole design rests on.

    If these compared equal, a prefill run would find the raw corpus already
    done, measure nothing, and print success -- the exact failure `key()`'s
    docstring describes for rule bumps.
    """
    ck = Checkpoint(M)
    raw = ck.key(P, ADOPTED)
    pre = ck.key(P, ADOPTED, frame="prefill")
    assert raw != pre
    assert all(raw[f] == pre[f] for f in raw), "shared fields must be untouched"


def test_key_matches_a_key_actually_in_the_stash():
    """The end-to-end claim: what we build is what was stored.

    Reads a real record rather than asserting against a literal, because the
    literal would be a second declaration of the same thing and could drift from
    the producer. Skipped where the stash is absent rather than passing vacuously.
    """
    import glob
    import json
    from malignment import twp as T
    root = os.path.expanduser("~/malignment-data/twp/allenai__Olmo-3-1025-7B")
    files = sorted(glob.glob(os.path.join(root, "*", "jsonl.hashstash.raw",
                                          "data.jsonl")))
    if not files:
        import pytest
        pytest.skip("no local stash for %s" % M)
    rec = None
    for line in open(files[0], encoding="utf-8"):
        d = json.loads(line)
        if d.get("rule_version") == 4 and not d.get("topup"):
            rec = d
            break
    if rec is None:
        import pytest
        pytest.skip("no v4 pass-1 record in the stash")
    before = T.USE_PROMPT_CACHE
    try:
        #: stamp what the RECORD says, not what this process happens to be set to
        T.USE_PROMPT_CACHE = bool(rec.get("prompt_cache"))
        k = Checkpoint(rec["model"]).key(rec["prompt"], ADOPTED)
    finally:
        T.USE_PROMPT_CACHE = before
    for f in ("model", "prompt", "rule_version", "dict_sha"):
        assert str(k[f]) == str(rec[f]), (f, k[f], rec[f])
    assert k["rules"] == rec["rules"]
    assert k["prompt_cache"] == bool(rec["prompt_cache"])
