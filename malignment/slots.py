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

#: **RH's ruling, 2026-08-16: "ok lets use falcon3b".** Confirming malign's
#: [6363] pick against the enumerated alternatives below.
#:
#: THE DIAGNOSTIC PAIR ANSWERS "what does the instrument do here" -- dN,
#: suppression, substitution, dP per word. It is NOT the screening base, which
#: answers "can this frame move at all" and takes a different answer for a
#: measured reason: Falcon3-3B sits at the 32nd and 25th percentile of 389
#: models on naughty-pole mass, so screening frames on it would reject stimuli
#: that are alive in the models actually measured. That is M01 in reverse.
#: **Do not prefill this as a screening base.**
#:
#: WHY THIS PAIR CANNOT CONTAMINATE. `Falcon3-3B-Base` is `prune`d from
#: `Falcon3-7B-Base`, and `prune` is DERIVING but not ALIGNING -- so the 3B is
#: not a lineage root, takes no endpoint, and appears in no chain. Nothing seen
#: here can select an item into a population it is not in.
#:
#: CHOSEN FROM AN ENUMERATED POOL, not by availability. Seven alignment edges sit
#: outside every experimental population (2026-08-16, >500 cells each):
#:
#:     Falcon3-Mamba-7B -> Instruct   instruct  2,641   0.1674
#:     Falcon3-3B       -> Instruct   instruct  2,663   0.0898   <- THIS
#:     phi-4            -> reasoning  sft       2,663   0.0749
#:     Falcon3-10B      -> Instruct   instruct  2,663   0.0714
#:     Falcon3-1B       -> Instruct   instruct  2,663   0.0501
#:     Pharia-1-7B      -> aligned    dpo       2,215   0.0311
#:     phi-4-reasoning  -> -plus      rlvr      2,579   0.0157
#:
#: Roster mean over all cells is 0.103. **Two things that pool tells you and no
#: single choice does.** Falcon3-Mamba moves 1.9x better and is the only free
#: pair above the roster mean -- passed over because it is an SSM, its roster
#: environment reads `profile: ssm / box: ssm` rather than this Mac, and SSMs are
#: untested across devices at any quantity ([6357], and [4917]'s
#: `selective_scan_cuda` failures). And the pool is four-sevenths `instruct`,
#: with exactly one `dpo`, one `sft` and one `rlvr`, all of them the quietest in
#: the set -- **so a diagnostic pair chosen for movement is an `instruct` edge,
#: and the instrument never gets diagnosed on a preference edge.** That is a
#: standing limitation of this choice, not a defect in it.
DIAGNOSTIC_PAIR = ("tiiuae/Falcon3-3B-Base", "tiiuae/Falcon3-3B-Instruct")


def check_diagnostic_pair(pair=None):
    """Verify the pair is still outside every experimental population.

    **A RULE THAT EXECUTES RATHER THAN ONE THAT MUST BE RECALLED.** The comment
    above states that neither member is an endpoint or a chain rung; that is a
    fact about the roster TODAY, and the roster changes -- `endpoints()` went 48
    to 50 on the day this was written. A comment asserting it would go quietly
    stale, and the failure mode is the worst kind: the pair keeps working, keeps
    looking safe, and silently starts selecting.

    Returns the pair. Raises `ValueError` naming which member and which
    population, so the message says what to do rather than that something is
    wrong.
    """
    from . import roster
    base, aligned = pair or DIAGNOSTIC_PAIR
    endpoints, _ = roster.endpoints()
    rungs = set(roster.population("chain_rungs"))
    chain_members = set()
    for c in roster.chains():
        chain_members |= {c["base"], c["sft"], c["pref"]}
    bad = []
    for m in (base, aligned):
        for name, pop in (("endpoints (as a base)", set(endpoints)),
                          ("endpoints (as a target)", set(endpoints.values())),
                          ("chain_rungs", rungs),
                          ("a declared chain", chain_members)):
            if m in pop:
                bad.append("%s is in %s" % (m, name))
    if bad:
        raise ValueError(
            "the diagnostic pair is no longer out-of-population: %s. Anything "
            "screened while looking at it can now select into a population it "
            "belongs to, which is the contamination this pair exists to avoid. "
            "Pick another from the free pool (see DIAGNOSTIC_PAIR's comment) or "
            "re-declare deliberately." % "; ".join(bad))
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
