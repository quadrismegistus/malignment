#!/usr/bin/env python
"""v4 rule invariants: the pure ones always, the arithmetic ones on a tiny model.

    python -m pytest tests/test_twp_v4.py -q

**Every test here carries its red receipt in its docstring** — the commit or the
constructed input at which it fails, per `tests/README.md`.

## WHY THE FIRST TEST NEEDS NO MODEL AND MATTERS MOST

`Rules` is the thing that decides whether a run is v3 or v4, and a switch missing
from `is_v3()` makes a v4 run REPORT ITSELF AS v3 — and makes `compare()` assert
zero movement for it, which is the check that would otherwise catch the mistake.
That is not hypothetical: `decoded_boundary` was missing for exactly one commit
on 2026-08-17, and nothing in the suite could have found it.

## AND WHY THE REST NEED ONE

`expand4` and `score_words4` are arithmetic over forward passes; there is no
model-free way to assert they agree. So they run on the smallest cached
checkpoint and SKIP when it is absent, rather than being omitted — a test that
cannot run is still a test that says what it would have checked.
"""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from malignment import twp_v4 as V4  # noqa: E402

#: The smallest checkpoint whose WEIGHTS are cached. `smollm2-135M-SFT-Only` is
#: smaller and was the first choice, and its cache directory holds only a
#: README -- so the skip guard fired correctly and the model was genuinely
#: absent. **A skip that should not have happened reads as green**, so it is
#: worth having verified rather than assumed.
TINY = "HuggingFaceTB/SmolLM2-360M"
PROMPTS = [
    "She was so angry she wanted to",
    "那个自由的人选择了",          # the CJK arm, where the v4 rules actually bite
]


def test_every_rule_appears_in_is_v3():
    """A switch missing from `is_v3()` makes a v4 run call itself v3.

    RED RECEIPT: constructed, and it fired for real. Add a field to `Rules`
    without adding it to `is_v3()` — as `decoded_boundary` was on 2026-08-17,
    for one commit — and this fails on that field. Introspection rather than a
    hand-list, because a hand-list has the same defect as the thing it checks.
    """
    import dataclasses

    defaults = V4.Rules()
    assert defaults.is_v3(), "Rules() with no arguments must be v3"
    for f in dataclasses.fields(V4.Rules):
        cur = getattr(defaults, f.name)
        #: pick any value that differs from the default, whatever the type
        alt = (not cur) if isinstance(cur, bool) else (
            0.5 if isinstance(cur, float) else 9)
        flipped = dataclasses.replace(defaults, **{f.name: alt})
        assert not flipped.is_v3(), (
            "Rules(%s=%r).is_v3() is True -- the switch is missing from is_v3(), "
            "so a run using it reports itself as v3 and compare() will assert "
            "zero movement for it" % (f.name, alt))
        assert flipped.label() != "v3", (
            "Rules(%s=%r).label() is 'v3' -- the stamp on every cell this run "
            "writes would name the wrong instrument" % (f.name, alt))


def test_adopted_is_not_v3():
    """`ADOPTED` must be a v4 rule set, or the migration writes v3 under a v4 name.

    RED RECEIPT: set `ADOPTED = Rules()` and this fails. It is a one-line
    constant and the whole rebuild is keyed on what it says.
    """
    assert not V4.ADOPTED.is_v3()
    assert V4.ADOPTED.label().startswith("v4[")


def _tiny():
    """(model, tok, dev, bmask, cjk) on the tiny checkpoint, or skip."""
    from huggingface_hub import try_to_load_from_cache
    if try_to_load_from_cache(TINY, "config.json") is None:
        pytest.skip("%s not in the local cache" % TINY)
    import torch

    from malignment import models as M
    from malignment import twp as T
    torch.set_grad_enabled(False)
    tok, _loader = T.load_tokenizer(TINY)
    model, _t = M.load_model(TINY)
    vs = model.config.vocab_size
    bmask = T.boundary_mask(tok, vs)
    trie = T.load_prefix_trie()
    cids, cstrs, lids, pi = T.cjk_vocab(tok, vs)
    return model, tok, "mps", bmask, ((trie, cids, cstrs, lids, pi) if len(cids) else None)


@pytest.mark.parametrize("prompt", PROMPTS)
def test_rules_default_reproduces_v3_exactly(prompt):
    """`expand4(Rules())` must equal `twp.expand` to the BIT, not approximately.

    RED RECEIPT: this is the check the module's own docstring calls "the first
    thing to run after any edit here", and it is the reason `expand4` imports
    v3's helpers instead of forking them. Change a default in `Rules`, or let a
    rule apply when it is off, and this fails on the first prompt.
    """
    from malignment import twp as T
    model, tok, dev, bmask, cjk = _tiny()
    v3 = T.expand(model, tok, prompt, dev, bmask, cjk=cjk)
    v3 = v3[0] if isinstance(v3, tuple) else v3
    v4, _res, _meta = V4.expand4(model, tok, prompt, dev, bmask, cjk=cjk,
                                 rules=V4.Rules())
    worst = max((abs(v4.get(k, 0.0) - v3.get(k, 0.0)) for k in set(v3) | set(v4)),
                default=0.0)
    assert worst == 0.0, "Rules() moved %d words, max %.3e" % (
        sum(1 for k in set(v3) | set(v4) if v4.get(k, 0.0) != v3.get(k, 0.0)), worst)


@pytest.mark.parametrize("prompt", PROMPTS)
def test_conservation_holds_under_adopted(prompt):
    """v4 must still close its books: words + residual == 1.

    RED RECEIPT: the first `numeric_intra` had a fragment rule that routed mass
    to `drop`; conservation SURVIVED that (the mass was accounted) which is why
    this test is necessary AND not sufficient — it catches mass that vanishes,
    not mass that is misfiled. The -90.31%% regression passed this check.
    """
    model, tok, dev, bmask, cjk = _tiny()
    w, res, _m = V4.expand4(model, tok, prompt, dev, bmask, cjk=cjk,
                            rules=V4.ADOPTED)
    total = (sum(w.values()) + res["tail"] + res["drop"] + res["open"]
             + res["mojibake"] + res.get("term_floored", 0.0))
    assert abs(total - 1.0) < 1e-5, "conservation %.8f" % total


@pytest.mark.parametrize("prompt", PROMPTS)
def test_score_words4_agrees_with_expand4(prompt):
    """Pass 2 must measure the same object as pass 1.

    The migration is `expand4` then `score_words` over the per-prompt union, and
    the two would have disagreed silently in two ways: `score_words` capped at
    `MAX_DEPTH` 6 while `expand4` walked to 9, and it scored against the
    UNCORRECTED boundary mask.

    RED RECEIPT: call `twp.score_words` directly instead of `score_words4` and
    this fails — on the English prompt through the mask, and on any prompt with
    a 7+ token word through the depth cap, where a REFUSAL is not a zero.

    Tolerance is 1e-6 relative and not zero: the two batch their forward passes
    over different prefix sets, and fp16 attention accumulates differently. That
    difference is measured at ~1.2e-03 for a 251-prefix batch elsewhere; here it
    is 1.1e-07.
    """
    model, tok, dev, bmask, cjk = _tiny()
    w4, _res, _m = V4.expand4(model, tok, prompt, dev, bmask, cjk=cjk,
                              rules=V4.ADOPTED)
    surfaces = sorted({k[0] for k in w4})
    got, refused, _total = V4.score_words4(model, tok, prompt, surfaces, dev,
                                           bmask, cjk=cjk, rules=V4.ADOPTED)
    shared = [k for k in w4 if k in got]
    assert len(shared) >= 0.9 * len(w4), (
        "score_words4 reached %d of expand4's %d keys, refused %d"
        % (len(shared), len(w4), len(refused)))
    worst = max((abs(got[k] - w4[k]) / w4[k] for k in shared if w4[k] > 1e-9),
                default=0.0)
    assert worst < 1e-6, "max relative disagreement %.3e over %d keys" % (
        worst, len(shared))
