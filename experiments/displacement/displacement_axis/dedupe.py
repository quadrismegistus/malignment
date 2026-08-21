"""One frame per prompt. Import this before iterating items, or repeat a defect.

24 prompts in pilot3 carry THREE item_ids each -- `nn_andstartedto_a26ad841`
suffixed `-actionsexual`, `-actionverbal`, `-actionviolence` -- which differ only
in the declared pole set. They share a prompt, so they share their words, their
ratings, and (because `words.jsonl` is keyed on item and the underlying store is
keyed on prompt) byte-identical movement: the median |difference| in held-out R2
between two rows of the same prompt is 0.0000.

All 72 sit in `identity`, which is why that domain reads as 107 frames when it
holds 59 distinct ones. Domain assignment is unaffected -- no prompt's duplicates
straddle two domains -- so medians and per-domain point estimates are correct as
computed. What is NOT correct is any count, sign test or paired p-value over
frames, because 48 of the rows are copies. p=5e-29 over 95/95 frames is really
over about 53 independent ones.

This is the `p-values-over-correlated-subunits` defect with a new face: nothing
about a triplicate looks wrong, the numbers agree because they must, and
agreement reads as replication.

WHICH COPY SURVIVES. The first item_id in sorted order, deterministically. Any
choice is equivalent while the movement data is identical, and `check()` asserts
that it still is rather than assuming it -- if an ingest ever makes the copies
diverge, the assumption becomes false silently and the assert is the only thing
that would say so.
"""

import collections


def keep(prompt_of):
    """item_ids to keep: one per prompt, the first in sorted order."""
    by = collections.defaultdict(list)
    for item, p in prompt_of.items():
        by[p].append(item)
    return {sorted(v)[0] for v in by.values()}


def report(prompt_of, kept):
    n = len(prompt_of) - len(kept)
    if n:
        print("dedupe: %d of %d items dropped as same-prompt copies (%d frames)"
              % (n, len(prompt_of), len(kept)))
    return kept


def check(cells, prompt_of, tol=1e-12):
    """Assert the copies really are copies. Returns (checked, mismatched)."""
    by = collections.defaultdict(list)
    for item, p in prompt_of.items():
        if item in cells:
            by[p].append(item)
    checked = bad = 0
    for p, items in by.items():
        if len(items) < 2:
            continue
        a = cells[items[0]]
        for b_ in items[1:]:
            checked += 1
            b = cells[b_]
            if set(a) != set(b):
                bad += 1; continue
            for l in a:
                if set(a[l]) != set(b[l]) or any(
                        abs(a[l][w] - b[l][w]) > tol for w in a[l]):
                    bad += 1; break
    return checked, bad
