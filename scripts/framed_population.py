#!/usr/bin/env python
"""Which framed edges were measured with an EMPTY SYSTEM SLOT. A REPORT, not a rule.

    python scripts/framed_population.py            counts
    python scripts/framed_population.py --list     every edge

**The rule lives in `malignment.movement.clean_frame_pairs()`, not here.** This
file used to carry its own copy and that was the mistake it was written to fix:
a predicate with two implementations has two answers. It now prints what the
accessor returns.

Two scopes, and they are different questions rather than different answers:

    clean_frame_pairs()          every clean framed edge in movement_v4,
                                 including depth-2/3 rungs
    ...restricted to endpoints() the declared base->endpoint pairs, which is
                                 the population a headline contrast uses
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args(argv)
    from malignment import movement as M, roster
    trip = M.clean_frame_pairs()
    ep, _ = roster.endpoints()
    endp = [(b, al, m) for b, al, m in trip if ep.get(b) == al]
    print("framed edges with an EMPTY SYSTEM SLOT as measured")
    print("  all edges in movement_v4      : %d" % len(trip))
    print("  restricted to endpoints()     : %d" % len(endp))
    print("  intermediate rungs, not endpoints: %d" % (len(trip) - len(endp)))
    if a.list:
        print()
        for b, al, m in endp:
            print("   %-40s %-40s %s" % (b.split("/")[-1][:40],
                                         al.split("/")[-1][:40], m))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
