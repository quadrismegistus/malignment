#!/usr/bin/env python
"""Hua & Raley's KL asymmetry, measured. Is arrival rarer than collapse?

    python asymmetry.py

## THE CLAIM

Hua and Raley, "Optimization Is Not All You Need" (2026), section 2:

    "it is ruinously costly for the model to say what the archive has never
     said, and nearly costless to stop saying what the archive says only
     rarely... continuations the base model never entertained are excluded from
     the start."

## WHAT BEARS ON IT

A SYMMETRIC count, both directions across the same two orders of magnitude, on
the same rows. If the asymmetry holds, collapses should vastly outnumber
arrivals. Written before the query ran.

    collapse   p_base > 0.10   ->  p_aligned < 0.001
    arrival    p_base < 0.001  ->  p_aligned > 0.10

## THE POPULATION AND ITS FENCES

50 declared endpoint pairs, raw edge, `rule='canonical'`, and three exclusions
each of which was necessary:

    p_base > 0            a zero in this store can mean UNMEASURED rather than
                          measured-zero: topup covers 46.2% of endpoint cells,
                          and where it did not run an absent word is stored as
                          0. Including those would manufacture arrivals.
    real prompts          `<<<LOGICAL:BOS>>>` is a synthetic bare-BOS probe on
                          141 models. Its top "arrivals" are chat-template
                          tokens -- the model emitting its frame when given
                          nothing -- which is not a fact about language.
    no template tokens    `<|im_start|>`, `<s>`, `system`, and friends, for the
                          same reason.

**This measures the POLICY, one slot. It says nothing about what a decoder
emits, which is the subject of the essay's footnote 19 and is out of reach
here.**
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))))

TPL = ("word NOT LIKE '<%' AND word NOT LIKE '%|%' "
       "AND prompt != '<<<LOGICAL:BOS>>>' "
       "AND word NOT IN ('system','user','assistant','endoftext')")


def main():
    from malignment import movement as M, vectors as V
    w = M.endpoint_edge_where("raw")
    r = V.rows(
        "SELECT count() n, "
        "countIf(p_base>0.10 AND p_aligned<0.001) collapse, "
        "countIf(p_base<0.001 AND p_aligned>0.10) arrive, "
        "countIf(p_base>0.05 AND p_aligned<0.005) collapse2, "
        "countIf(p_base<0.005 AND p_aligned>0.05) arrive2, "
        "countIf(cls='riser' AND p_base<1e-4 AND p_aligned>0.01) tiny_arrive "
        "FROM movement_v4 WHERE rule='canonical' AND p_base>0 AND %s AND %s"
        % (TPL, w))[0]
    print("movement rows, 50 endpoint pairs, measured base mass: %d" % r["n"])
    print()
    print("  TWO ORDERS OF MAGNITUDE, BOTH DIRECTIONS")
    print("    collapse  p_base>0.10  -> p_aligned<0.001 : %6d" % r["collapse"])
    print("    arrival   p_base<0.001 -> p_aligned>0.10  : %6d" % r["arrive"])
    print("    collapse : arrival = %.2f : 1" % (r["collapse"] / max(r["arrive"], 1)))
    print()
    print("  ONE ORDER LOOSER")
    print("    collapse  p_base>0.05  -> p_aligned<0.005 : %6d" % r["collapse2"])
    print("    arrival   p_base<0.005 -> p_aligned>0.05  : %6d" % r["arrive2"])
    print("    collapse : arrival = %.2f : 1" % (r["collapse2"] / max(r["arrive2"], 1)))
    print()
    print("  arrivals from p_base<1e-4 reaching p_aligned>0.01 : %d" % r["tiny_arrive"])
    q = ("SELECT word, prompt, p_base, p_aligned, aligned FROM movement_v4 "
         "WHERE rule='canonical' AND cls='riser' AND p_base>0 AND p_base<1e-4 "
         "AND p_aligned>0.2 AND %s AND %s ORDER BY p_aligned DESC LIMIT 5" % (TPL, w))
    print("\n  largest measured arrivals from a rare base:")
    for x in V.rows(q):
        print("    %-12s %.2e -> %.3f (%8.0fx) %-22s | %s"
              % (x["word"], x["p_base"], x["p_aligned"], x["p_aligned"] / x["p_base"],
                 x["aligned"].split("/")[-1][:22], x["prompt"][:40]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
