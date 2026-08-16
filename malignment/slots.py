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
