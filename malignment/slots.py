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

#: **`kakaocorp/kanana-1.5-8b-base -> kanana-1.5-8b-instruct-2505`** (malign,
#: [6368], superseding Falcon3-3B).
#:
#: ONE PAIR DOES BOTH JOBS NOW (RH's design): the panel pools base+aligned on the
#: y-axis, so poles are tagged on exactly the vocabulary movement is measured
#: over. The two-object design had a silent hole -- poles tagged on model A's
#: vocabulary, dN computed on pair B, so a frame whose poles B barely offers
#: yields a dN that is arithmetically fine and about nothing.
#:
#: THE REQUIREMENT, IN ONE SENTENCE: a pair whose BASE is typical enough that a
#: frame looking dead on it is really dead, and whose EDGE moves enough that a
#: frame looking live on it really moves.
#:
#:     base typical      in the 14 candidates of `instrument_calibrations/
#:                       screening_base` -- untreated models only
#:     edge moves        mean JS 0.3960, 3.8x the 0.1030 roster mean
#:     runnable here     profile=default on BOTH arms
#:     peripheral        in no finding in the project
#:
#: **AND OUT-OF-POPULATION IS NO LONGER REQUIRED.** [6363] demanded it to prevent
#: contamination -- selecting frames on the outcome of a pair the findings use.
#: RH withdrew the hazard and malign accepted the withdrawal at [6368], on the
#: argument that survives without any claim about how movement transfers:
#: `removal_rates` compares sexual against frequency-matched neutral ON THE SAME
#: FRAMES, so a non-differential filter sits identically on both sides and
#: cancels. Levels stay conditional on the battery, which they already were and
#: which the population receipts already record; contrasts are protected.
#:
#: That constraint was also what made the problem hard. It left seven pairs and
#: forced a choice between a typical base that does not move and a mover that is
#: not typical. Lifted, several pairs are both.
#:
#: **Falcon3-3B is withdrawn as unfit**: 3rd/10th/3rd percentile, rank 53 of 58
#: untreated models. Screening on a quiet model rejects frames that are alive
#: elsewhere. **Falcon3-Mamba-7B is ruled out on availability, not risk**:
#: `mamba_ssm` and `causal_conv1d` are CUDA-only, absent locally, and both arms
#: are 4.4 MB stubs -- a ~28 GB download to discover that.
DIAGNOSTIC_PAIR = ("kakaocorp/kanana-1.5-8b-base",
                   "kakaocorp/kanana-1.5-8b-instruct-2505")

#: **PROVISIONAL PENDING AN MPS LOAD TEST** (malign, [6368]). Neither arm has an
#: MPS observation and neither is fully cached; malign is running the same timed
#: fp16 round-trip used for Falcon3-3B and will book the result. If it fails the
#: fallback is `RedPajama-INCITE-Base-7B-v0.1 -> RedPajama-INCITE-7B-Chat`
#: (0.4920, Chat arm already cached). Building against kanana on malign's word.
DIAGNOSTIC_PAIR_PROVISIONAL = True


def check_diagnostic_pair(pair=None):
    """Verify the pair still satisfies what is actually required of it.

    **THE OUT-OF-POPULATION CHECK WAS REMOVED, AND ITS REMOVAL IS THE POINT OF
    THIS DOCSTRING.** The first version refused any pair whose members appeared
    in `endpoints()` or a chain, because [6363] required that. [6368] withdrew
    the requirement -- contamination was retracted as a hazard by RH and by
    malign -- and the declared pair is now an endpoint pair by design.

    So this guard would have refused the pair it exists to protect. **A guard
    enforcing a rule that has been withdrawn is worse than no guard**: it fires
    with authority, names a real-sounding hazard, and sends the next reader to
    fix something that was deliberately chosen. It is the code form of a figure
    that revives a retracted result.

    What survives, because it is still required and still cheap:

        both arms declared        a pair naming a checkpoint the roster does not
                                  hold is a typo, not a decision
        base is UNTREATED         `pretrained: false` outright, or an ALIGNING op
                                  anywhere in its ancestry. A base that is already
                                  aligned makes the pooled y-axis post-repression
                                  and dN a measurement of the second treatment.
        the edge IS an ALIGNING   otherwise the pair measures `prune` or
        op                        `upscale` and dN is not about alignment at all

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
