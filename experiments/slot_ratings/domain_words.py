"""Raw risers and fallers per domain. No ratings, no scales, no instrument.

    python experiments/slot_ratings/domain_words.py --domain sexual violence identity

Looks at the vocabulary BEFORE deciding what to measure. This is how
`termination` and `mediation` came out of the institutional words: the eleven
scales did not name what the risers had in common, and reading the list did.

Aggregates CANONICAL verdicts over (frame x lineage) cells within a domain,
restricted to words eligible in that cell (p_base >= min_prob, so the word could
have fallen). `net` is (rise - fall) / seen. Saves to results/domain_words.json.
"""
import argparse, collections, json, os, sys
import statistics as st
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, REPO)
CELLS = os.path.join(REPO, "experiments", "displacement", "displacement_axis",
                     "results", "pilot3", "cells.jsonl")
MIN_PROB = 0.003


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", nargs="+",
                    default=["sexual", "violence", "identity", "institutional"])
    ap.add_argument("--min-seen", type=int, default=30)
    ap.add_argument("--top", type=int, default=28)
    a = ap.parse_args(argv)
    from malignment import vectors as V
    from malignment.movement import movement, CANONICAL
    from malignment.pos import get_pos
    cells = [json.loads(l) for l in open(CELLS, encoding="utf-8")]
    byitem = collections.defaultdict(list)
    for c in cells:
        byitem[c["item_id"]].append(c)
    out = {}
    for dom in a.domain:
        items = [i for i, v in byitem.items() if v[0].get("domain") == dom]
        rise = collections.Counter(); fall = collections.Counter(); seen = collections.Counter()
        for iid in items:
            mine = byitem[iid]
            ms = sorted({c["base"] for c in mine} | {c["endpoint"] for c in mine})
            rows = V.rows("SELECT model, groupArray(word) AS ws, groupArray(p) AS ps "
                          "FROM twp_words_v4_best WHERE prompt={p:String} "
                          "AND model IN {ms:Array(String)} GROUP BY model",
                          p=mine[0]["prompt"], ms=ms)
            store = {r["model"]: dict(zip(r["ws"], r["ps"])) for r in rows}
            for c in mine:
                pb, pa = store.get(c["base"]), store.get(c["endpoint"])
                if not pb or not pa:
                    continue
                m = movement(pb, pa, CANONICAL,
                             residual_pre=c.get("residual_base"),
                             residual_post=c.get("residual_endpoint"))
                rs, fs = set(m.risers), set(m.fallers)
                for w, p in pb.items():
                    if p < MIN_PROB:
                        continue
                    seen[w] += 1
                    if w in rs: rise[w] += 1
                    elif w in fs: fall[w] += 1
        net = {w: (rise[w] - fall[w]) / seen[w] for w in seen if seen[w] >= a.min_seen}
        pos = get_pos(sorted(net), items and byitem[items[0]][0]["prompt"] or "")
        out[dom] = [dict(word=w, net=net[w], rise=rise[w], fall=fall[w], seen=seen[w])
                    for w in net]
        top = sorted(net, key=lambda w: -net[w])[:a.top]
        bot = sorted(net, key=lambda w: net[w])[:a.top]
        print("\n=== %s: %d frames, %d words seen %d+ times" % (dom, len(items), len(net), a.min_seen))
        print("  RISE  " + ", ".join("%s%+.2f" % (w, net[w]) for w in top))
        print("  FALL  " + ", ".join("%s%+.2f" % (w, net[w]) for w in bot))
    json.dump(out, open(os.path.join(HERE, "results", "domain_words.json"), "w"))
    print("\n-> results/domain_words.json")


if __name__ == "__main__":
    main()
