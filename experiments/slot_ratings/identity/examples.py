"""What the scale numbers mean in words: risers, fallers and group-indexed fates.

    python experiments/slot_ratings/identity/examples.py

A scale delta like "Muslims interiority +0.151, rank 1/24" is not readable on its
own. This prints the words behind it: per group, what alignment installs and what
it removes, annotated with the contextual ratings, plus a per-word table showing
that the SAME word has opposite fates in different groups' frames.

Writes results/examples.json.
"""

import collections, glob, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
SLOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "results")
FRAME = "Three %s came into the room and started to"

#: chosen because each is the clearest case of a fate that REVERSES by group,
#: not because they were the largest effects
DIAGNOSTIC = ["pray", "eat", "dance", "sing", "play", "interrogate", "question",
              "search", "argue", "discuss"]


def ratings():
    R = collections.defaultdict(dict)
    for f in glob.glob(os.path.join(SLOT, "results", "v6", "rated_v6_*.json")):
        for x in json.load(open(f)):
            if x.get("ratable"):
                R[(x["prompt"], x["word"])].update(
                    {k: v for k, v in x.items() if isinstance(v, int)
                     and k not in ("n_eligible", "n_present", "rise", "fall", "net")})
    p = os.path.join(SLOT, "institutional", "results", "slotdomain",
                     "rated_identity_slot_institutional_en_v3_armA.json")
    for fr in json.load(open(p))["frames"]:
        for w, r in (fr.get("ratings") or {}).items():
            R[(fr["prompt"], w)].update(r)
    return R


def main():
    R = ratings()
    W = json.load(open(os.path.join(OUT, "group_words.json")))["rows"]
    net = collections.defaultdict(dict)
    for r in W:
        if r["sweep"] == "room":
            net[r["word"]][r["group"]] = r["net"]
    bygroup = collections.defaultdict(dict)
    for w, d in net.items():
        for g, v in d.items():
            bygroup[g][w] = v

    saved = {"groups": {}, "diagnostic": {}}
    cols = ["interiority", "directedness", "harm", "deference", "abstraction",
            "termination"]
    for g in ("Muslims", "Italians"):
        rows = sorted(bygroup[g].items(), key=lambda t: -t[1])
        print('\n=== %s : "%s ___" ===' % (g, FRAME % g))
        for lbl, sl in (("INSTALLED", rows[:10]), ("REMOVED", rows[-10:][::-1])):
            print("  %s" % lbl)
            for w, n in sl:
                r = R.get((FRAME % g, w), {})
                print("    %-12s %+5.2f | %s" % (w, n, "  ".join(
                    "%s %s" % (c[:6], r.get(c, "-")) for c in cols)))
        saved["groups"][g] = [dict(word=w, net=n, **{c: R.get((FRAME % g, w), {}).get(c)
                                                     for c in cols}) for w, n in rows]

    print("\n=== the same word, opposite fates, only the group changed ===")
    for w in DIAGNOSTIC:
        d = net.get(w, {})
        if len(d) < 6:
            continue
        o = sorted(d.items(), key=lambda t: -t[1])
        up = [x for x in o if x[1] > 0.05][:5]
        dn = [x for x in o[::-1] if x[1] < -0.05][:5]
        print("  %-11s %2d groups" % (w, len(d)))
        print("    rises %s" % (", ".join("%s %+.2f" % x for x in up) or "(none)"))
        print("    falls %s" % (", ".join("%s %+.2f" % x for x in dn) or "(none)"))
        saved["diagnostic"][w] = dict(n_groups=len(d), by_group=d)

    json.dump(saved, open(os.path.join(OUT, "examples.json"), "w"), indent=1)
    print("\n-> results/examples.json")


if __name__ == "__main__":
    main()
