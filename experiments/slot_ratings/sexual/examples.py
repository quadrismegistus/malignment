"""Word-level examples: what alignment installs and removes at each prompt.

    python experiments/slot_ratings/sexual/examples.py

The scale deltas are unreadable on their own. This prints, per prompt, the words
that gain and lose the most probability mass across the 33 lineages, annotated
with the ratings that produced the scale numbers, so any claim in the README can
be traced to the words that carry it.

Mass is averaged over the lineages, not summed, so the numbers are per-lineage
probabilities and comparable across prompts.

Writes results/examples.json.
"""

import collections, json, os, sys
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, HERE); sys.path.insert(0, REPO)
OUT = os.path.join(HERE, "results")
COLS = ["genitality", "charge", "explicitness", "body_distance", "euphemism",
        "orality", "tactility", "incorporation"]


def main():
    from analyse import load, masses
    from gender_pairs import PAIRS, DIRECTION, ACTANT
    R = load()
    prompts = sorted({k[0] for k in R})
    M = masses(prompts)
    saved = {}
    for pr in sorted({PAIRS[p][0] for p in prompts}):
        ps = [p for p in prompts if PAIRS[p][0] == pr]
        print("=" * 104)
        for p in sorted(ps, key=lambda x: DIRECTION[x]):
            lins = [l for (t, l) in M if t == p]
            b = collections.defaultdict(float); a = collections.defaultdict(float)
            for l in lins:
                pb, pa = M[(p, l)]
                for w, v in pb.items():
                    b[w] += v / len(lins)
                for w, v in pa.items():
                    a[w] += v / len(lins)
            ws = [(w, b[w], a[w]) for w in set(b) | set(a) if (p, w) in R]
            up = sorted(ws, key=lambda t: -(t[2] - t[1]))[:8]
            dn = sorted(ws, key=lambda t: (t[2] - t[1]))[:8]
            print("\n  [%s / %s / actant %s]  %s ___"
                  % (pr, DIRECTION[p], ACTANT[p], p))
            for lab, sl in (("ALIGNMENT ADDS   ", up), ("ALIGNMENT REMOVES", dn)):
                print("    %s" % lab)
                for w, x, y in sl:
                    r = R[(p, w)]
                    print("      %-13s %.4f -> %.4f  %+.4f | %s | %s"
                          % (w, x, y, y - x,
                             " ".join("%s %d" % (c[:4], r[c]) for c in COLS
                                      if r.get(c) is not None),
                             r["zone_kind"]))
            saved["%s|%s" % (pr, DIRECTION[p])] = dict(
                prompt=p, direction=DIRECTION[p], actant=ACTANT[p],
                adds=[dict(word=w, base=x, aligned=y,
                           **{c: R[(p, w)].get(c) for c in COLS}) for w, x, y in up],
                removes=[dict(word=w, base=x, aligned=y,
                              **{c: R[(p, w)].get(c) for c in COLS}) for w, x, y in dn])
    json.dump(dict(_what="per prompt, the 8 largest mass gainers and losers across "
                         "the 33 lineages, with their v2 ratings", prompts=saved),
              open(os.path.join(OUT, "examples.json"), "w"), indent=1)
    print("\n-> results/examples.json")


if __name__ == "__main__":
    main()
