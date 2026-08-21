"""Place the human anchor and the two arms on the deepseek surprisal axis.

    python .../ref_anchor.py                  # the M=200 report
    python .../ref_anchor.py --sweep          # plus the stability sweep

Consumes `~/malignment-data/ref_pool/deepseek/ref_shard00.{jsonl,f32,i32}` --
13,124 passages scored in one pass, 0 skipped, 76.8 min.

## THE UNIT IS THE TOKEN, AND THAT IS NOT A DETAIL

An earlier version controlled on BYTES, which gives each corpus a different
amount of text: arXiv abstracts run **5.53 bytes per token** against dreams'
**4.28**, a 29% spread. Per byte the abstracts looked like the flattest prose in
the set; per token they are mid-range. The byte axis was crediting them for
packing more characters into each model decision.

deepseek sees tokens, the sidecar IS per-token surprisal, so the first M
predictions are `sur[row:row+M]` -- a partial sum needing no offsets at all.

## M = 200, AND WHY IT IS NOT AN EYEBALL

M is the largest prefix at which EVERY human corpus retains 100% of its 500
passages. Above it the corpora become length-selected, so any ordering change
there is selection rather than measurement:

    M                 100    150    200    220    240
    waking_narrative 100%   100%   100%    54%     5%
    dreams           100%   100%   100%    74%    13%
    c20_fiction      100%   100%   100%    94%    43%

The byte-axis version used K=1000, where dreams was 27% of its sample. That
number should not have been quoted and is not quoted here.

## WHAT IS EXCLUDED

`Falcon3-1B/3B/10B-Base` -- `scale` children of `Falcon3-7B-Base`, so not
independent observations of a pretrained model (RH, 2026-08-21).
`roster.population('bases')` already excludes them, which is correct behaviour
here and not the defect it first looked like.

## THE UNIT FOR AN ARM CLAIM IS THE MODEL, NEVER THE PASSAGE

Passages within a model are not independent and models within a lineage share a
base. The arm rows below are medians of per-model medians, and the paired test
is over LINEAGES.
"""

import argparse, collections, json, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.expanduser("~/malignment-data/ref_pool")
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))

CORPORA = ("literary_criticism", "c20_fiction", "arxiv_abstracts",
           "philosophy", "dreams", "waking_narrative")
#: the REPORTING value. See the docstring: the largest 100%-retention prefix.
M_REPORT = 200
SWEEP = (60, 80, 100, 120, 150, 175, 200)
MIN_PASSAGES_PER_MODEL = 5


def load():
    import numpy as np
    from malignment import roster
    pool = {}
    for line in open(os.path.join(DATA, "ref_pool.jsonl")):
        r = json.loads(line)
        pool[r["id"]] = r.get("pool")
    rows = [json.loads(l) for l in
            open(os.path.join(DATA, "deepseek", "ref_shard00.jsonl"))]
    for r in rows:
        r["pool"] = pool.get(r["id"])
    sur = np.fromfile(os.path.join(DATA, "deepseek", "ref_shard00.f32"),
                      dtype=np.float32)
    aligned, bases = roster.population("aligned"), roster.population("bases")
    mn = [r for r in rows if r["pool"] == "model_narrative"]
    #: anything in NEITHER population is a scale child -- see the docstring.
    exc = {m for m in {r["model"] for r in mn}
           if m not in aligned and m not in bases}
    return rows, mn, sur, aligned, bases, exc


def bits(r, sur, M):
    """Mean bits/token over the first M PREDICTED positions. -> float or None"""
    return None if r["n"] < M else float(sur[r["row"]:r["row"] + M].mean())


def arm_medians(mn, sur, bases, aligned, exc, M):
    """-> {model: median bits/token}, filtered to models with enough passages."""
    per = collections.defaultdict(list)
    for r in mn:
        if r["model"] in exc:
            continue
        b = bits(r, sur, M)
        if b is not None:
            per[r["model"]].append(b)
    return {m: statistics.median(v) for m, v in per.items()
            if len(v) >= MIN_PASSAGES_PER_MODEL}


def table(rows, mn, sur, bases, aligned, exc, M):
    """-> [(name, median bits/token, n, unit)] for one M."""
    mm = arm_medians(mn, sur, bases, aligned, exc, M)
    out = [("MODEL base", statistics.median([v for m, v in mm.items() if m in bases]),
            len([m for m in mm if m in bases]), "models"),
           ("MODEL aligned", statistics.median([v for m, v in mm.items() if m in aligned]),
            len([m for m in mm if m in aligned]), "models")]
    for c in CORPORA:
        v = [bits(r, sur, M) for r in rows
             if r["pool"] == "human_anchor" and r["corpus"] == c]
        v = [x for x in v if x is not None]
        out.append(("human " + c, statistics.median(v), len(v), "passages"))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--m", type=int, default=M_REPORT)
    ap.add_argument("--sweep", action="store_true")
    a = ap.parse_args(argv)
    rows, mn, sur, aligned, bases, exc = load()
    from malignment import roster

    print("excluded as non-independent (scale children): %s"
          % ", ".join(sorted(x.split("/")[-1] for x in exc)))

    print("\nRETENTION -- the constraint that fixes M\n")
    print("%-26s %s" % ("group", "  ".join("%5d" % m for m in (100, 150, 200, 220, 240))))
    for c in CORPORA:
        t = [r["n"] for r in rows if r["pool"] == "human_anchor" and r["corpus"] == c]
        print("%-26s %s" % (c, "  ".join(
            "%4.0f%%" % (100 * sum(1 for x in t if x >= m) / len(t))
            for m in (100, 150, 200, 220, 240))))

    print("\n\nM = %d TOKENS      HIGH = more surprising = LESS predictable\n" % a.m)
    print("%-26s %11s %8s %s" % ("", "bits/token", "n", "unit"))
    for name, val, n, u in sorted(table(rows, mn, sur, bases, aligned, exc, a.m),
                                  key=lambda x: -x[1]):
        print("%-26s %11.4f %8d %s" % (name, val, n, u))

    print("\n\nARM EFFECT, lineage-paired\n")
    lin = roster.lineages()
    root_of = {}
    for root, ms in lin.items():
        root_of[root] = root
        for m in ms:
            root_of[m] = root
    print("%-6s %10s %10s %10s   %s" % ("M", "base", "aligned", "gap", "lineages, aligned lower"))
    for M in (100, 150, a.m):
        mm = arm_medians(mn, sur, bases, aligned, exc, M)
        byl = collections.defaultdict(dict)
        for m, v in mm.items():
            byl[root_of.get(m, m)]["base" if m in bases else "aligned"] = v
        pr = [(d["base"], d["aligned"]) for d in byl.values()
              if "base" in d and "aligned" in d]
        print("%-6d %10.4f %10.4f %+10.4f   %d of %d"
              % (M, statistics.median([v for m, v in mm.items() if m in bases]),
                 statistics.median([v for m, v in mm.items() if m in aligned]),
                 statistics.median([v for m, v in mm.items() if m in aligned])
                 - statistics.median([v for m, v in mm.items() if m in bases]),
                 sum(1 for b, al in pr if al < b), len(pr)))

    if not a.sweep:
        return
    vals = {}
    for M in SWEEP:
        for name, val, _, _ in table(rows, mn, sur, bases, aligned, exc, M):
            vals[(M, name)] = val
    print("\n\nMEDIAN bits/token BY M -- and the RATE, which is its own finding\n")
    order = [n for n, _, _, _ in sorted(table(rows, mn, sur, bases, aligned, exc, a.m),
                                        key=lambda x: -x[1])]
    print("%-26s %s %9s" % ("", "  ".join("%7d" % m for m in SWEEP), "M60->200"))
    for n in order:
        print("%-26s %s %+9.3f"
              % (n, "  ".join("%7.4f" % vals[(M, n)] for M in SWEEP),
                 vals[(SWEEP[-1], n)] - vals[(SWEEP[0], n)]))

    print("\n\nWHICH ARM-vs-CORPUS COMPARISONS SURVIVE THE SWEEP?\n")
    print("%-9s %-20s %-9s %10s %s" % ("arm", "corpus", "M=60..200", "gap@%d" % a.m, "verdict"))
    for arm in ("MODEL base", "MODEL aligned"):
        for c in CORPORA:
            sgn = ["Y" if vals[(M, arm)] > vals[(M, "human " + c)] else "n" for M in SWEEP]
            gap = vals[(a.m, arm)] - vals[(a.m, "human " + c)]
            v = ("STABLE above" if all(x == "Y" for x in sgn)
                 else "STABLE below" if all(x == "n" for x in sgn) else "*** FLIPS ***")
            print("%-9s %-20s %-9s %+10.4f %s"
                  % (arm.split()[1], c, "".join(sgn), gap, v))


if __name__ == "__main__":
    main()
