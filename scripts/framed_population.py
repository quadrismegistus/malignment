#!/usr/bin/env python
"""Which framed cells were measured with an EMPTY SYSTEM SLOT. -> the population.

    python scripts/framed_population.py            the count and the roster
    python scripts/framed_population.py --list     every pair
    python scripts/framed_population.py --excluded why each exclusion happened

## WHY THIS IS A SCRIPT AND NOT A SENTENCE

This number was re-derived in conversation eight times on 2026-09-03 and came out
differently almost every time -- 29, 34, 47, 28, 35, 45, 24, 44. The DATA was
stable throughout; `roster/models/chat_renders.json` did not change. What changed
was which rule got applied to it, because the rule lived in prose and was
reconstructed from memory at each asking.

So the rule lives here now. If the number changes, this file changed.

## THE RULE

A framed cell belongs to the population iff the SYSTEM SLOT WAS EMPTY IN THE MODE
THE CELL WAS STORED UNDER.

    slot = row["system_slot"]        when system_mode == "default"
    slot = row["system_slot_empty"]  when system_mode == "empty"
    in   = (slot == "")

## THE TWO WRONG RULES, NAMED SO THEY ARE NOT REACHED FOR AGAIN

**`clean_via`** says a model CAN be brought to a clean slot. It is a property of
the MODEL and says nothing about the condition its cells were measured in.
Counting it admits models measured in the mode that is NOT clean for them.

**`system_mode == clean_via`** is too strict in the other direction. A model whose
DEFAULT slot is empty is equally clean when measured at `empty`; requiring the
labels to match discards those.

Both are the same error: reading a property of the MODEL where the question is
about the CELL.
"""
import argparse
import collections
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
RENDERS = os.path.join(ROOT, "roster", "models", "chat_renders.json")


def population():
    """-> (kept, excluded). kept is [(base, aligned, mode)]."""
    from malignment import ch, roster
    rows = {r["model"]: r for r in
            json.load(open(RENDERS, encoding="utf-8"))["models"]}
    ep, _ = roster.endpoints()
    raw = {x["model"] for x in ch.query("SELECT DISTINCT model FROM twp_cells_v4")}
    modes = collections.defaultdict(set)
    for x in ch.query("SELECT DISTINCT model, system_mode FROM twp_cells_v4 "
                      "WHERE frame='prefill'"):
        modes[x["model"]].add(x["system_mode"])

    kept, excluded = [], []
    for b, a in sorted(ep.items()):
        if b not in raw or a not in modes:
            continue
        r = rows.get(a) or {}
        good = []
        for m in sorted(modes[a]):
            slot = r.get("system_slot") if m == "default" else r.get("system_slot_empty")
            if slot == "":
                good.append(m)
        if good:
            kept.append((b, a, good[0]))
        else:
            excluded.append((a, {m: (r.get("system_slot") if m == "default"
                                     else r.get("system_slot_empty"))
                                 for m in sorted(modes[a])}))
    return kept, excluded


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--excluded", action="store_true")
    a = ap.parse_args(argv)
    kept, excluded = population()
    print("base_raw -> aligned_framed, system slot EMPTY as measured")
    print("  pairs IN  : %d" % len(kept))
    print("  pairs OUT : %d" % len(excluded))
    if a.list:
        print()
        for b, al, m in kept:
            print("   %-42s %-40s %s" % (b.split("/")[-1][:42],
                                         al.split("/")[-1][:40], m))
    if a.excluded:
        print()
        for al, s in excluded:
            print("   %-42s %s" % (al.split("/")[-1][:42],
                                   {k: (v if v is None else v[:44]) for k, v in s.items()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
