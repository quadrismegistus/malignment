"""Guard the one thing that can go silently wrong here.

    python -m pytest tests.py -q

`run.py --ungated` re-reads the generation stash to check that the pure-story
gate is not manufacturing the frame effect. That check is only worth anything if
it selects **the same population** the gated pass selects, minus the gate. It
does that by duplicating `national_story/judge.py`'s reader -- same glob, same
decoder filter, same duplicate-producer rule -- and a duplicate drifts.

**A divergence here does not fail loudly. It makes the gate check answer a
different question than the gated pass asked, and report a clean result.** That
is the failure these tests exist for.
"""
import os
import re
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))

JUDGE = os.path.abspath(os.path.join(
    HERE, "..", "..", "passage_analysis", "national_story", "judge.py"))


def judge_src():
    if not os.path.exists(JUDGE):
        pytest.skip("judge.py not present: %s" % JUDGE)
    return open(JUDGE, encoding="utf-8").read()


def test_stash_and_producer_constants_match_judge():
    """The VALUES, imported -- not the source text that spells them."""
    import importlib.util
    import run
    spec = importlib.util.spec_from_file_location("_ns_judge", JUDGE)
    if spec is None:
        pytest.skip("cannot load judge.py")
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as e:                       # noqa: BLE001
        pytest.skip("judge.py not importable here: %s" % e)
    assert run.STASH == mod.STASH
    assert run.KEEP_FIRST == mod.KEEP_FIRST
    assert run.DROP_WHEN_DUP == mod.DROP_WHEN_DUP


@pytest.mark.parametrize("lit", [
    "max_new_tokens", "0.95", "1.0", "'raw'", "'prefill_sysdefault'",
])
def test_decoder_filter_literals_still_in_judge(lit):
    """A SOURCE check, and it is the weaker kind -- say so rather than imply it.

    The decoder filter is control flow, not a constant, so there is nothing to
    import. This asserts only that judge.py still MENTIONS each literal the
    ungated reader hardcodes. It cannot see a restructure that keeps every
    literal and changes what they gate, and it is not evidence that the two
    readers agree -- only that the obvious way for them to disagree has not
    happened.
    """
    assert lit in judge_src()


def test_person_rule_abstains_and_splits():
    from run import person
    assert person("") == "none"
    assert person("He said it. She left. He saw her. His hands.") == "3rd"
    assert person("I said it. I left. I saw. My hands. Me.") == "1st"
    #: below MIN_PRON there is no narrator to identify, and guessing one would
    #: put a coin-flip label on the cell rather than leaving it out
    assert person("He walked.") == "none"


def test_dialogue_strip_removes_the_character_and_not_the_narrator():
    """The correction the whole first-person result turned on."""
    from run import person
    #: exactly 5 narrator pronouns, all third -- at MIN_PRON, so the stripped
    #: version is the smallest story that still gets a label at all
    third = ('He crossed the yard. His boots were wet. He did not follow. '
             'The dog found him. His hands shook.')
    #: 6 character "I"s, one more than the narrator has pronouns
    quoted = third + ' "I can\'t. I won\'t. I told you. I meant it. I am done. I go."'
    assert person(third, strip=True) == "3rd"
    #: unstripped, the CHARACTER outvotes the narrator and the story reads 1st
    assert person(quoted, strip=False) == "1st"
    #: stripped, the narrator is restored -- this is the whole correction
    assert person(quoted, strip=True) == "3rd"


def test_binom_is_two_sided_and_exact():
    from run import binom
    assert binom(0, 1) == 1.0                       #: 2 * 1/2
    assert abs(binom(0, 5) - 2 * (1 / 32)) < 1e-12
    assert binom(5, 10) == 1.0                      #: clamped, never above 1
