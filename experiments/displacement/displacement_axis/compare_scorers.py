"""Head to head: does a contextual rating explain WHICH WORDS MOVE better than bge?

    python experiments/displacement_axis/compare_scorers.py

`rated_contextual.py` compares the three scorers on `dN`, the mass-weighted
position shift. This compares them on the other question, which is X_metonymy's:

    per frame, over its words, does the score predict NET MOVEMENT?

That is a different quantity from dN and the two can disagree -- a scale can order
which words move without shifting the centroid, and vice versa. Both are reported
because the campaign has confused them before.

**NO RE-EMBEDDING IS NEEDED.** `results/<run>/words.jsonl` already carries `s`,
the per-word projection on the frame's own axis, for every (item, base, endpoint,
word). 252 MB, streamed. I nearly rebuilt the Axis and re-scored 300 frames
before reading the file.

    bge            s from words.jsonl
    k_ratings      type-level, lexicons/norms/k_ratings_en.json
    slot_ratings   contextual, per (prompt, word)

All three scored on THE SAME WORDS -- the intersection where all three have a
value -- so a difference is the scorer and not its coverage.
"""

import collections, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
#: The root, found by walking up from `malignment` itself, so this file does
#: not encode how deep under `experiments/` it sits. A wrong root makes the
#: globs below return [] instead of raising; `repo_root` refuses instead.
from malignment.paths import REPO
sys.path.insert(0, REPO)
#: `--run` selects the run directory; pilot3 stays the default so every
#: command already written against this file keeps meaning what it meant.
RUN = os.environ.get("AXIS_RUN", "pilot3")
RESULTS = os.path.join(HERE, "results", RUN)
SLOT = os.path.join(REPO, "experiments", "slot_ratings")
NORMS = os.path.join(REPO, "lexicons", "norms")
DROP = {"n_eligible", "n_present", "rise", "fall", "net", "ratable"}


def main():
    from scipy import stats
    import numpy as np
    ctx = collections.defaultdict(dict)
    import glob
    for f in glob.glob(os.path.join(SLOT, "results", "v6", "rated_v6_*.json")):
        for x in json.load(open(f)):
            if x.get("ratable"):
                ctx[(x["prompt"], x["word"])].update(
                    {k: v for k, v in x.items()
                     if isinstance(v, int) and not isinstance(v, bool) and k not in DROP})
    k = json.load(open(os.path.join(NORMS, "k_ratings_en.json")))
    #: k_ratings stores a LIST per word, positionally aligned to _meta.scales,
    #: not a dict. Indexed by position here.
    KSC = k["_meta"]["scales"]
    KIX = {s: i for i, s in enumerate(KSC)}
    KR = {w.lower(): v for w, v in k["ratings"].items()}
    CSC = sorted({s for v in ctx.values() for s in v})
    print("contextual %d (prompt,word) / %d scales | k_ratings %d words / %d scales"
          % (len(ctx), len(CSC), len(KR), len(KSC)))

    #: stream words.jsonl, accumulating per (item, word): the bge score and the
    #: net movement across this frame's cells. dP>0 is a rise.
    acc = collections.defaultdict(lambda: {"s": None, "net": 0, "n": 0})
    prompt_of = {}
    with open(os.path.join(RESULTS, "words.jsonl")) as fh:
        for line in fh:
            d = json.loads(line)
            key = (d["item_id"], d["word"])
            a = acc[key]
            a["s"] = d["s"]
            a["net"] += 1 if d["dP"] > 0 else (-1 if d["dP"] < 0 else 0)
            a["n"] += 1
    for c in (json.loads(l) for l in open(os.path.join(RESULTS, "cells.jsonl"))):
        prompt_of[c["item_id"]] = c["prompt"]
    print("words.jsonl: %d (item, word) keys over %d items"
          % (len(acc), len({i for i, _ in acc})))

    by = collections.defaultdict(list)
    for (item, w), a in acc.items():
        p = prompt_of.get(item)
        if p and a["s"] is not None:
            by[item].append((w, a["s"], a["net"]))

    rows = []
    for item, ws in by.items():
        p = prompt_of[item]
        #: THE SAME WORDS for all three scorers
        keep = [(w, s, net) for w, s, net in ws
                if (p, w) in ctx and w.lower() in KR]
        if len(keep) < 15:
            continue
        net = [n for _, _, n in keep]
        if len(set(net)) < 2:
            continue
        r = dict(item_id=item, prompt=p, n_words=len(keep))
        r["rho_bge"] = stats.spearmanr([s for _, s, _ in keep], net).statistic
        for s in CSC:
            v = [ctx[(p, w)].get(s) for w, _, _ in keep]
            if any(x is None for x in v) or len(set(v)) < 2:
                continue
            r["ctx_" + s] = stats.spearmanr(v, net).statistic
        for s in KSC:
            v = [KR[w.lower()][KIX[s]] for w, _, _ in keep]
            if any(x is None for x in v) or len(set(v)) < 2:
                continue
            r["k_" + s] = stats.spearmanr(v, net).statistic
        rows.append(r)
    print("frames compared: %d (>=15 words scored by all three)\n" % len(rows))

    def best(prefix, r):
        vs = [(abs(v), kk) for kk, v in r.items() if kk.startswith(prefix) and v == v]
        return max(vs) if vs else (float("nan"), None)

    print("%-26s %8s %8s %8s   %s"
          % ("scorer", "median", "mean |rho|", "|rho|>.3", "best single scale"))
    bg = [abs(r["rho_bge"]) for r in rows if r["rho_bge"] == r["rho_bge"]]
    print("%-26s %8.3f %8.3f %7.0f%%" % ("bge (the frame's axis)", float(np.median(bg)),
                                         float(np.mean(bg)),
                                         100 * sum(1 for x in bg if x > .3) / len(bg)))
    for label, pre, sc in (("k_ratings, type-level", "k_", KSC),
                           ("slot_ratings, contextual", "ctx_", CSC)):
        b = [best(pre, r)[0] for r in rows]
        b = [x for x in b if x == x]
        names = collections.Counter(best(pre, r)[1] for r in rows)
        print("%-26s %8.3f %8.3f %7.0f%%   %s"
              % (label + " (best of %d)" % len(sc), float(np.median(b)), float(np.mean(b)),
                 100 * sum(1 for x in b if x > .3) / len(b),
                 ", ".join("%s %d" % (n.split("_", 1)[1], c)
                           for n, c in names.most_common(3) if n)))
    print("\nper scale, median |rho| across frames:")
    for pre, sc in (("ctx_", CSC), ("k_", KSC)):
        for s in sc:
            v = [abs(r[pre + s]) for r in rows
                 if r.get(pre + s) is not None and r.get(pre + s) == r.get(pre + s)]
            if len(v) < 30:
                continue
            print("   %-28s %6.3f   (%d frames)"
                  % (("contextual " if pre == "ctx_" else "k_ratings ") + s,
                     float(np.median(v)), len(v)))
    #: THE PER-FRAME MAXIMUM IS BIASED UPWARD BY THE NUMBER OF CANDIDATES, and
    #: the three scorers have 1, 7 and 12. So it is reported above and then
    #: matched two ways: one scale fixed GLOBALLY per scorer (k=1 for all three),
    #: and best-of-7 for the contextual set to match k_ratings.
    print("\n" + "=" * 78)
    print("MATCHED COMPARISON. The table above takes a per-frame maximum over")
    print("1, 7 and 12 candidates, which favours whichever scorer has most.\n")
    print("  (a) ONE SCALE FIXED GLOBALLY -- the scale with the best median, k=1 each")
    print("      %-34s %8s %8s" % ("scorer", "median", "|rho|>.3"))
    print("      %-34s %8.3f %7.0f%%" % ("bge (the frame's axis)", float(np.median(bg)),
                                         100 * sum(1 for x in bg if x > .3) / len(bg)))
    for label, pre, sc in (("k_ratings", "k_", KSC), ("slot_ratings", "ctx_", CSC)):
        per = {}
        for sname in sc:
            v = [abs(r[pre + sname]) for r in rows if r.get(pre + sname) is not None]
            if len(v) >= 30:
                per[sname] = v
        if not per:
            continue
        bestname = max(per, key=lambda n: float(np.median(per[n])))
        v = per[bestname]
        print("      %-34s %8.3f %7.0f%%"
              % ("%s: %s" % (label, bestname), float(np.median(v)),
                 100 * sum(1 for x in v if x > .3) / len(v)))
    print("\n  (b) BEST-OF-7 for the contextual set, matching k_ratings' 7 candidates")
    import itertools, random
    rr = random.Random(20260820)
    avail = [s2 for s2 in CSC
             if sum(1 for r in rows if r.get("ctx_" + s2) is not None) >= 30]
    meds = []
    for _ in range(200):
        sub = rr.sample(avail, min(7, len(avail)))
        b = []
        for r in rows:
            vs = [abs(r["ctx_" + s2]) for s2 in sub if r.get("ctx_" + s2) is not None]
            if vs:
                b.append(max(vs))
        if b:
            meds.append(float(np.median(b)))
    if meds:
        print("      %-34s %8.3f   (200 random 7-subsets, %.3f to %.3f)"
              % ("slot_ratings, best of 7", float(np.median(meds)),
                 float(np.min(meds)), float(np.max(meds))))

    json.dump(dict(_what="per frame, spearman of each scorer against net word "
                         "movement, all three on the same words", rows=rows),
              open(os.path.join(RESULTS, "compare_scorers.json"), "w"))
    print("\n-> results/pilot3/compare_scorers.json")


if __name__ == "__main__":
    main()
