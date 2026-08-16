#!/usr/bin/env python
"""Slot items: the derived id, and nothing else yet.

    from malignment.slots import item_id
    item_id("She slowly took off her", "coat", "dress")   # nn_tookoffher_coat-dress

## WHY THIS IS A MODULE AND NOT A LINE IN THE UI

`item_id` is a PURE FUNCTION the client could trivially reimplement, and that is
exactly the argument for not letting it. A reimplementation silently re-chooses
every rule inside it -- and this one has four, three of which are invisible
until they are wrong:

    the last THREE words, not two or four
    each word stripped to [a-z0-9] BEFORE joining, so "man's" -> "mans"
    NICE FIRST, then naughty
    CJK falls back to the last 8 characters, because `split()` on a Chinese
      prompt returns ONE token and the id would carry the whole sentence

A JavaScript port would also get the character classes wrong for free: Python's
`\\w` is Unicode-aware by default and JavaScript's is ASCII-only, so a naive port
strips accented and CJK characters that the original keeps. That is a divergence
no test in either language would notice, producing ids that look right and do
not match the ones already written.

## PORTED VERBATIM FROM `malign_logits/server.py._slot_item_id`

Logic unedited, on the `twp.py` precedent: a pure move so the rule has one home.
**86 items in `pair_drafts/round3/round3_slots.yaml` already carry ids from this
function**, so it is not a convention being chosen here -- it is one being
honoured, and a change to it orphans them.

Verified against that file on 2026-08-16: 84 of 86 decompose as
`nn_<last3>_<nice0>-<naughty0>` under a straightforward reading, and the two
that do not are an artifact of the CHECKING regex splitting `man's` into two
tokens, not of the ids. `nn_tookoffher_coat-dress`, `nn_reachedforhis_hand-belt`,
`nn_andstartedto_search-beat`.

## WHAT `item_id` IS NOT

It is not provenance. It encodes the prompt tail and the highest-mass word of
each branch -- **it says nothing about which checkpoints produced the
distribution**, and no field in those 86 items does. That is a real gap and a
narrow one; it is not the same as the items carrying nothing, which they plainly
do not: they carry both pole lists mass-ordered, `naughty_mass`, `nice_mass`,
`share`, `domain`, `writer`, and `global_cos` on 39 of 86.
"""
import re

#: The CJK block, matching the archive's `[一-鿿]` exactly. Written as an escape
#: rather than as literal characters so that a file-encoding accident cannot
#: silently narrow it.
_CJK = re.compile(r"[一-鿿]")


# ---------------------------------------------------------------------------
# the diagnostic pair
# ---------------------------------------------------------------------------

#: **`tiiuae/Falcon3-10B-Base -> tiiuae/Falcon3-10B-Instruct`** (RH, 2026-08-16).
#:
#: ## OUT OF SAMPLE IS NON-NEGOTIABLE, AND I BRIEFLY GAVE IT AWAY
#:
#: [6368] lifted the out-of-population requirement and recommended `kanana`, on
#: the grounds that contamination had been withdrawn as a hazard. **It had not.
#: TWO hazards were in play and only one was withdrawn:**
#:
#:     DIRECT         screening frames while looking at movement on a pair that
#:                    IS in the measured 50 selects frames on the outcome of a
#:                    measurement we will report. X_safety_ablation §4a, where 39
#:                    never-scored items reversed the ordering.  NEVER WITHDRAWN.
#:     CORRELATIONAL  a HELD-OUT pair's movement correlating with in-sample
#:                    pairs.  Withdrawn by RH, accepted at [6368].
#:
#: My [6366] withdrew the second. [6368] read it as the first and expanded the
#: pool to in-sample pairs. **Both arms of `kanana` and of `RedPajama` are in
#: `endpoints()`** -- verified, not assumed -- so either would have made the
#: authoring screen select on the outcome of a measured lineage.
#:
#: ## WHAT IS LEFT ONCE THE CONSTRAINT IS RESTORED
#:
#: Out of sample AND runnable on this machine leaves the unused Falcon3s:
#:
#:     pair                  screener rank   max_dev   edge JS   env
#:     Falcon3-10B-Base           16 / 56      26.8     0.0714   default/default
#:     Falcon3-3B-Base            53 / 58      46.6     0.0898   default/default
#:     Falcon3-1B-Base                 -          -     0.0501   default/default
#:
#: `Falcon3-Mamba-7B` moves best of the free pairs at 0.1674 and is ruled out on
#: AVAILABILITY: `mamba_ssm` and `causal_conv1d` are CUDA-only and absent, both
#: arms are 4.4 MB stubs, ~28 GB to find out ([6368] §2).
#:
#: **The 10B over the 3B, on the screening half.** 26.8 against 46.6 -- the 3B is
#: 3rd/10th/3rd percentile and would reject frames that are alive everywhere
#: else. The 3B moves marginally more (0.0898 vs 0.0714) and both are below the
#: 0.1030 roster mean anyway, so the movement difference buys less than the
#: representativeness difference costs.
#:
#: ## THE LIMITATION, STATED RATHER THAN DISCOVERED
#:
#: **0.0714 is BELOW the roster mean of 0.1030.** A frame that looks unmoved here
#: may move on a median lineage. That is the price of out-of-sample on this
#: machine and it belongs on the panel, not in a footnote: the diagnostic is
#: evidence that a frame DOES move, and weak evidence that it does not.
DIAGNOSTIC_PAIR = ("tiiuae/Falcon3-10B-Base", "tiiuae/Falcon3-10B-Instruct")

#: Falcon3-3B has a booked MPS observation from [6363] (fp16, ~6 s from local
#: cache); the 10B arms do not, and both are stubs locally. That is a download
#: and a load test, not a design question -- unlike `kanana`, nothing about the
#: 10B's FITNESS is open.
DIAGNOSTIC_PAIR_PROVISIONAL = True


def check_diagnostic_pair(pair=None):
    """Verify the pair still satisfies what is actually required of it.

    **THE OUT-OF-POPULATION CHECK IS BACK, AND REMOVING IT WAS MY ERROR.**
    I took it out on [6368], which lifted the requirement because "contamination
    has been withdrawn as a hazard". Two hazards were in play and only one was
    withdrawn -- see `DIAGNOSTIC_PAIR`. The direct one, selecting frames on the
    outcome of a pair that IS in the measured 50, was never withdrawn by anybody.

    For an hour this guard would have PASSED a pair with both arms in
    `endpoints()`. A guard that has been relaxed to admit the thing it was
    written to refuse is worse than a guard that never existed, because its
    silence now reads as clearance.

    What survives, because it is still required and still cheap:

        both arms declared        a pair naming a checkpoint the roster does not
                                  hold is a typo, not a decision
        base is UNTREATED         `pretrained: false` outright, or an ALIGNING op
                                  anywhere in its ancestry. A base that is already
                                  aligned makes the pooled y-axis post-repression
                                  and dN a measurement of the second treatment.
        the edge IS an ALIGNING   otherwise the pair measures `prune` or
        op                        `upscale` and dN is not about alignment at all
        OUT OF SAMPLE             neither arm in endpoints(), chain_rungs or any
                                  declared chain -- the check restored above

    What is NOT checked here and must not be inferred from a pass: that the base
    is TYPICAL (a property of `screening_base`'s ranking, which moves when the
    roster does) and that the pair MOVES (a property of `movement_cells`). Both
    are recorded in `DIAGNOSTIC_PAIR`'s comment with their numbers, and neither
    is a cheap lookup.

    Returns the pair. Raises `ValueError` naming what failed.
    """
    from . import roster
    base, aligned = pair or DIAGNOSTIC_PAIR
    doc = roster.load()
    nodes = doc.get("nodes") or {}
    bad = []

    for m in (base, aligned):
        if m not in nodes:
            bad.append("%s is not in the roster" % m)

    #: THE DECLARED FLAG FIRST, THEN THE GRAPH. Reading the graph alone is the
    #: bug that put three `pretrained: false` checkpoints into an "untreated"
    #: set: a model whose aligned parent is absent from the roster has no
    #: incoming edge, so an ancestry walk finds nothing and calls it a base.
    if nodes.get(base, {}).get("pretrained") is False:
        bad.append("%s is declared `pretrained: false` -- it is already aligned, "
                   "so the pooled distribution would be post-repression" % base)

    parents = {}
    for p, op, c in (doc.get("edges") or []):
        parents.setdefault(c, []).append((p, op))
    seen, stack = set(), [base]
    while stack:
        cur = stack.pop()
        if cur in seen:
            continue
        seen.add(cur)
        for p, op in parents.get(cur, []):
            if op in roster.ALIGNING:
                bad.append("%s has an ALIGNING op (%s) in its ancestry, so it is "
                           "not a base" % (base, op))
                stack = []
                break
            stack.append(p)

    #: **OUT OF SAMPLE.** Neither arm may appear in any population a finding is
    #: measured over. This is the check that makes looking at movement while
    #: authoring safe at all: it is what stops frame selection from being
    #: selection on the outcome of a lineage we report.
    endpoints, _ = roster.endpoints()
    rungs = set(roster.population("chain_rungs"))
    chain_members = set()
    for ch_ in roster.chains():
        chain_members |= {ch_["base"], ch_["sft"], ch_["pref"]}
    for m in (base, aligned):
        for name, pop in (("endpoints (as a base)", set(endpoints)),
                          ("endpoints (as a target)", set(endpoints.values())),
                          ("chain_rungs", rungs),
                          ("a declared chain", chain_members)):
            if m in pop:
                bad.append("%s is in %s, so frames screened while looking at its "
                           "movement would be selected on the outcome of a "
                           "measured lineage" % (m, name))

    ops = [op for p, op, c in (doc.get("edges") or [])
           if p == base and c == aligned]
    if not ops:
        bad.append("no declared edge %s -> %s" % (base, aligned))
    elif not any(op in roster.ALIGNING for op in ops):
        bad.append("the edge %s -> %s is %s, which is not an ALIGNING op, so dN "
                   "over it would not be about alignment"
                   % (base, aligned, "/".join(ops)))

    if bad:
        raise ValueError(
            "the declared diagnostic pair is unfit: %s. See DIAGNOSTIC_PAIR's "
            "comment for what the pair has to satisfy." % "; ".join(bad))
    return (base, aligned)


def item_id(prompt, top_nice, top_naughty):
    """`nn_reachedforhis_hand-cock` -- RH's format.

    Last three words of the prompt, then the HIGHEST-MASS word of each branch,
    **nice first**. The mass words are the discriminating part: two prompts can
    end the same way and contend over completely different vocabulary, and an id
    made only of the prompt would collide on exactly the pairs a battery most
    needs to tell apart.

    CJK HAS NO SPACES, so `split()` returns one token for a Chinese prompt and
    the id would carry the whole sentence. Falls back to the last 8 characters,
    which is the same intent by the only means available.

    **The caller passes the highest-mass word of each branch, and that ordering
    is the caller's job to get right.** Passing tag order instead yields an id
    that is a property of the order someone happened to click rather than of the
    distribution -- stable-looking, and different on a second pass over the same
    item.
    """
    p = (prompt or "").strip()
    if _CJK.search(p):
        stem = re.sub(r"[^\w一-鿿]", "", p)[-8:]
    else:
        stem = "".join(re.sub(r"[^a-z0-9]", "", w.lower()) for w in p.split()[-3:])
    part = lambda w: re.sub(r"[^\w一-鿿]", "", (w or "none").lower())
    return "nn_%s_%s-%s" % (stem or "prompt", part(top_nice), part(top_naughty))
