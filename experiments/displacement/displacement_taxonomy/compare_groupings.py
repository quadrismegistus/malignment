"""Two agents grouped the 907 raw operations. Do they find the ten?

    python -u compare_groupings.py            the comparison
    python -u compare_groupings.py --names    every surviving group, named

## WHAT WAS RUN

`export_909.py` wrote the 907 operations shuffled, with `cross_frame.py`'s own
instruction, direction withheld. Two agents partitioned them independently:

    gpt6-astra-high   200 groups,  82 singletons
    opus5-max         107 groups,   9 singletons

Both returned complete partitions -- 907 ids, no duplicate, nothing dropped.

## THE HEADLINE IS NOT THE GROUP COUNT

907 operations come from 95 frames, and a frame was read 2 to 16 times, so the
file is full of near-duplicate accounts of ONE sentence. Merging those is
deduplication, not relation-finding, and it is where the group counts come from:

    gpt6    158 of 200 groups sit inside a single frame  (513 of 825 members)
    opus5    62 of 107                                   (260 of 898)

So the comparable object is the groups spanning SEVERAL frames, which is also
what the instruction asked for -- "a transformation appearing in several subject
areas is more interesting than one confined to a single area". `--min-frames`
sets the cut and defaults to 4.

## THE DOMAIN CONFOUND FIRED, IN THE TAIL

This file carried words where `cross_frame.py`'s blind document withheld them,
and the risk was a reader sorting by subject matter instead of by movement.
Measured against a size-matched shuffle, groups spanning more than one domain:

    gpt6     2% against 82% by chance
    opus5   21% against 93%

Both far below chance, so the shortcut was taken. But the LARGE groups span
freely -- `lateral-reshuffle` covers violence 16, sexual 12, institutional 8,
identity 3 -- so it is the long tail of small groups that is sorted by subject,
which is the same artefact as the single-frame merging seen from another side.

## THE JOIN IS PARTIAL AND THAT IS NOT A DEFECT TO HIDE

`crossframe_ops.json` holds 89 components built from an earlier, smaller set of
readings; the 907 come from the full 337-reading stash. Joining on (frame,
operation name) maps **183 of 907** operations to a component. Every number
below that compares against the existing taxonomy is computed on those 183 and
says so. A comparison quoted over 907 would be wrong by a factor of five.
"""
import argparse, collections, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
AG = os.path.join(HERE, "results", "agent_groupings")
FILES = {"gpt6-astra-high": "gpt6-astra-high_transformation_groups.json",
         "opus5-max": "opus5-max_transformation_groups.json"}


def load(which):
    return json.load(open(os.path.join(AG, FILES[which])))


def labels(d):
    """op id -> group label, singletons each their own."""
    m = {}
    for i, x in enumerate(d.get("groups") or []):
        for k in (x.get("members") or []):
            m[k] = "G%03d" % i
    for j, k in enumerate(d.get("singletons") or []):
        m[k] = "S%03d" % j
    return m


def op_to_component():
    """op id -> component id, joined on (frame, operation name). -> dict"""
    import export_909 as E
    byfn = collections.defaultdict(list)
    for r in E.rows():
        byfn[(r["frame"], r["name"])].append(r["id"])
    out = {}
    for c in json.load(open(os.path.join(HERE, "results", "crossframe_ops.json"))):
        for entry in c["names"]:
            for oid in byfn.get((c["prompt"], entry[1]), []):
                out[oid] = c["id"]
    return out


def op_to_relation():
    """op id -> meta-relation, via component and the k=3 hub graph. -> dict"""
    import dose_relations as DR
    o2c = op_to_component()
    home = {}
    for i, (name, ids, _h, _r) in enumerate(DR.clusters()):
        for cid in ids:
            home[cid] = "%02d %s" % (i, name)
    return {o: home[c] for o, c in o2c.items() if c in home}, o2c


def frames():
    import export_909 as E
    return {r["id"]: r["frame"] for r in E.rows()}


def main(argv=None):
    from sklearn.metrics import adjusted_rand_score as ari
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--min-frames", type=int, default=4)
    ap.add_argument("--names", action="store_true")
    a = ap.parse_args(argv)
    fr = frames()
    rel, o2c = op_to_relation()
    parts = {k: load(k) for k in FILES}
    lab = {k: labels(v) for k, v in parts.items()}

    ids = sorted(set(lab["gpt6-astra-high"]) & set(lab["opus5-max"]))
    print("\n%d operations partitioned by both agents" % len(ids))
    print("  ARI  gpt6 vs opus5      %+.3f"
          % ari([lab["gpt6-astra-high"][i] for i in ids],
                [lab["opus5-max"][i] for i in ids]))

    #: **THE ONLY POPULATION ON WHICH THE EXISTING TAXONOMY CAN BE SCORED.**
    shared = sorted(i for i in ids if i in rel)
    print("\n%d of those carry a k=3 meta-relation (the join through "
          "crossframe_ops.json)" % len(shared))
    for k in FILES:
        print("  ARI  %-16s vs the ten   %+.3f"
              % (k, ari([lab[k][i] for i in shared], [rel[i] for i in shared])))
    print("  ARI  gpt6 vs opus5, same subset      %+.3f"
          % ari([lab["gpt6-astra-high"][i] for i in shared],
                [lab["opus5-max"][i] for i in shared]))

    print("\nGROUPS SPANNING >= %d FRAMES -- the comparable object\n" % a.min_frames)
    print("  %-17s %8s %10s %9s" % ("", "groups", "members", "of total"))
    keep = {}
    for k, d in parts.items():
        g = [x for x in (d.get("groups") or [])
             if len({fr.get(m) for m in x["members"]}) >= a.min_frames]
        keep[k] = g
        tot = sum(len(x["members"]) for x in (d.get("groups") or []))
        print("  %-17s %8d %10d %8.0f%%"
              % (k, len(g), sum(len(x["members"]) for x in g),
                 100 * sum(len(x["members"]) for x in g) / tot))
    print("\n  for comparison: the hub graph gives 12 clusters at k=3, 11 with "
          "all three\n  raters, and TAXONOMY.md's ten need a further manual "
          "merge. Ten appears at\n  no threshold: the sweep runs 14, 19, 12, 8, "
          "6, 3.")
    if a.names:
        for k in FILES:
            print("\n=== %s, >=%d frames\n" % (k, a.min_frames))
            for x in sorted(keep[k], key=lambda x: -len(x["members"])):
                nf = len({fr.get(m) for m in x["members"]})
                print("  %3d members %3d frames  %s"
                      % (len(x["members"]), nf, x["name"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
