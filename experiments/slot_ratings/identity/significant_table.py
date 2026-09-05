"""Every significant group-by-scale association, PER SWEEP, and which replicate.

`group_contrast.py` tests each group against the mean of the other 23 on the same
lineage, FDR-corrected within (sweep, scale). This formats its output.

**THE SWEEP IS PART OF THE CLAIM, NOT A DETAIL.** The three sweeps are the same
24 groups in three different frames:

    room       Three {group} came into the room and started to
    nextdoor   The three {group} who moved in next door were
    street     When the {group} moved onto the street, the neighbours felt

Pooling them was how this folder's results were first summarised here, and it
hides that `white people` is +0.109 on interiority in one frame and -0.076 in
another, and that six of the eight negative interiority cells sit on `street`
alone. A group-by-scale association is a fact about a frame until shown otherwise.

**THE SCALES DIFFER BY SWEEP** -- 18, 18 and 11 -- because a scale is only rated
where the instrument judged it applicable. So a cell absent from a sweep has not
been tested there and is not a null; the replication table below counts only
sweeps that emitted the scale.

    python -m experiments.slot_ratings.identity.significant_table
"""
import collections
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SWEEPS = ("room", "nextdoor", "street")


def load():
    d = json.load(open(os.path.join(HERE, "results", "group_contrast.json")))
    rows = []

    def walk(o, sw=None):
        if isinstance(o, dict):
            sw = o.get("sweep", sw)
            if "scale" in o and "group" in o and "q" in o:
                rows.append(dict(o, sweep=o.get("sweep", sw)))
            for v in o.values():
                walk(v, sw)
        elif isinstance(o, list):
            for x in o:
                walk(x, sw)
    walk(d)
    return rows


def main():
    rows = load()
    by = collections.defaultdict(list)
    for r in rows:
        by[r["sweep"]].append(r)

    print("CELLS AND SIGNIFICANCE BY SWEEP  (FDR within sweep x scale)")
    print("%-10s %8s %8s %8s %8s %8s"
          % ("sweep", "cells", "scales", "sig", "pos", "neg"))
    for s in SWEEPS:
        v = by[s]
        sig = [r for r in v if r["q"] < 0.05]
        print("%-10s %8d %8d %8d %8d %8d"
              % (s, len(v), len({r["scale"] for r in v}), len(sig),
                 sum(1 for r in sig if r["delta"] > 0),
                 sum(1 for r in sig if r["delta"] < 0)))

    #: REPLICATION. A cell is only counted against sweeps that EMITTED its scale;
    #: an untested cell is not a failure to replicate.
    emitted = {s: {r["scale"] for r in by[s]} for s in SWEEPS}
    cells = collections.defaultdict(dict)
    for r in rows:
        cells[(r["scale"], r["group"])][r["sweep"]] = r

    print("\n\nASSOCIATIONS SIGNIFICANT IN MORE THAN ONE SWEEP, SAME SIGN")
    print("The only ones that are not a fact about a single frame.\n")
    print("%-14s %-20s %6s  %s"
          % ("scale", "group", "sweeps", "delta / q per sweep"))
    reps = []
    for (sc, g), d in sorted(cells.items()):
        sig = {s: r for s, r in d.items() if r["q"] < 0.05}
        if len(sig) < 2:
            continue
        signs = {1 if r["delta"] > 0 else -1 for r in sig.values()}
        if len(signs) != 1:
            print("%-14s %-20s %6s  SIGN CONFLICT: %s"
                  % (sc, g, len(sig),
                     "  ".join("%s %+.3f" % (s, r["delta"])
                               for s, r in sorted(sig.items()))))
            continue
        reps.append((sc, g, sig))
        print("%-14s %-20s %6d  %s"
              % (sc, g, len(sig),
                 "  ".join("%s %+.3f q=%.2g" % (s[:4], r["delta"], r["q"])
                           for s, r in sorted(sig.items()))))
    print("\n  %d associations replicate across sweeps." % len(reps))

    for s in SWEEPS:
        sig = sorted([r for r in by[s] if r["q"] < 0.05],
                     key=lambda r: (r["scale"], -r["delta"]))
        print("\n\n%s  --  %d significant of %d cells, %d scales"
              % (s.upper(), len(sig), len(by[s]), len(emitted[s])))
        print("%-14s %-20s %9s %9s %10s"
              % ("scale", "group", "delta", "up/n", "q (BH)"))
        for r in sig:
            print("%-14s %-20s %+9.3f %9s %10.2g"
                  % (r["scale"], r["group"], r["delta"],
                     "%s/%s" % (r.get("up"), r.get("n")), r["q"]))


if __name__ == "__main__":
    main()
