"""Does model SIZE predict surprisal or drift? params_b against both axes.

    python .../scale_axes.py

`params_b` comes from `roster/models/measurements.json`, section `weights` --
**counted from the weights, not read off a model card**, so a model whose card
lies or rounds does not corrupt this.

## THE LEVERAGE IS POOR AND SAYING SO IS THE FIRST RESULT

50 of the 54 open models in `quadrants.csv` carry a measured count, 0.36B to
10.3B. But they are not spread over that range:

    <1B      4 models
    1-3B    10
    3-6B     3      <-- the bridge, and it is three models wide
    6-8B    22
    8-11B   11

**33 of 50 sit in 6-11B and 14 below 3B, with three models between.** So a
regression on this roster is a two-cluster contrast wearing the clothes of a
continuum: it can say small-versus-7B and it cannot trace a curve. A slope fitted
here is an interpolation across a gap that holds three points, and the r that
comes with it will look like evidence of a trend.

Reported as: the correlation, AND the two group medians, so the reader sees the
thing the correlation is actually made of.

## LOG, AND WHY IT MATTERS LESS THAN USUAL

Scaling relations are log-linear in parameters, so `log10(params_b)` is the
regressor. With a bimodal predictor the transform mostly changes the spacing
between two clumps; both are reported because neither is obviously right on 50
points with a hole in the middle.

## THE UNIT PROBLEM: SIZE IS A LINEAGE PROPERTY

An aligned model has almost exactly its base's parameter count -- alignment does
not change the weight shapes. So base and aligned of one lineage are two points
at the SAME x, and treating 50 models as 50 observations of a size effect
overcounts by roughly two. The arms are therefore regressed SEPARATELY, and the
lineage count is printed beside the model count so the effective n is visible.

## AND SIZE IS CONFOUNDED WITH EVERYTHING A LAB CHOOSES

Bigger models here are also newer, trained on more tokens, by better-resourced
labs, with different data. Nothing in this file separates those. A correlation
with `params_b` is a correlation with "the kind of model a lab ships at that
size", and the training-token counts that would begin to separate them are not
in the roster for most of these models.
"""

import argparse, collections, csv, json, math, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "results", "quadrants.csv")
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
MEAS = os.path.join(ROOT, "roster", "models", "measurements.json")
sys.path.insert(0, ROOT)


def pearson(x, y):
    n = len(x)
    if n < 3:
        return None
    mx, my = sum(x) / n, sum(y) / n
    sx = math.sqrt(sum((v - mx) ** 2 for v in x))
    sy = math.sqrt(sum((v - my) ** 2 for v in y))
    if sx == 0 or sy == 0:
        return None
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy)


def ranks(v):
    o = sorted(range(len(v)), key=lambda i: v[i])
    out = [0.0] * len(v)
    i = 0
    while i < len(o):
        j = i
        while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
            j += 1
        for k in range(i, j + 1):
            out[o[k]] = (i + j) / 2.0 + 1
        i = j + 1
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=SRC)
    ap.add_argument("--min-passages", type=int, default=10)
    ap.add_argument("--split", type=float, default=4.0,
                    help="the small/large boundary, in the gap")
    a = ap.parse_args(argv)
    from malignment import roster

    csv.field_size_limit(10 ** 7)
    w = json.load(open(MEAS))["sections"]["weights"]["models"]
    pb = {k: v["params_b"] for k, v in w.items() if v.get("params_b")}
    per = collections.defaultdict(list)
    for r in csv.DictReader(open(a.src, newline="")):
        if r["category"] in ("base", "aligned"):
            per[r["model"]].append(r)
    lin = {m: b for b, ms in roster.lineages().items() for m in ms}

    pts = []
    miss = []
    for m, v in per.items():
        if len(v) < a.min_passages:
            continue
        if m not in pb:
            miss.append(m)
            continue
        pts.append(dict(model=m, arm=v[0]["category"], params_b=pb[m],
                        lineage=lin.get(m, m),
                        surprisal=statistics.median(float(x["surprisal"]) for x in v),
                        drift=statistics.median(float(x["drift"]) for x in v)))
    print("models with both a size and >= %d passages: %d  (%d lineages)"
          % (a.min_passages, len(pts), len({p["lineage"] for p in pts})))
    if miss:
        print("  no measured params_b, EXCLUDED not guessed: %d  %s"
              % (len(miss), ", ".join(sorted(miss)[:3]) + (" ..." if len(miss) > 3 else "")))

    band = collections.Counter()
    for p in pts:
        x = p["params_b"]
        band["<1B" if x < 1 else "1-3B" if x < 3 else "3-6B" if x < 6
             else "6-8B" if x < 8 else "8-11B"] += 1
    print("  sizes: %s" % "  ".join("%s %d" % (k, band[k]) for k in
                                    ("<1B", "1-3B", "3-6B", "6-8B", "8-11B")))

    for arm in ("base", "aligned"):
        sub = [p for p in pts if p["arm"] == arm]
        if len(sub) < 4:
            continue
        lp = [math.log10(p["params_b"]) for p in sub]
        print("\n%s   %d models, %d lineages" % (arm.upper(), len(sub),
                                                 len({p["lineage"] for p in sub})))
        print("  %-14s %10s %10s %12s %12s" % ("", "pearson", "spearman",
                                               "median <%.0fB" % a.split,
                                               "median >=%.0fB" % a.split))
        for lab in ("surprisal", "drift"):
            y = [p[lab] for p in sub]
            rp = pearson(lp, y)
            rs = pearson(ranks(lp), ranks(y))
            sm = [p[lab] for p in sub if p["params_b"] < a.split]
            lg = [p[lab] for p in sub if p["params_b"] >= a.split]
            print("  %-14s %+10.3f %+10.3f %12s %12s"
                  % (lab, rp, rs,
                     "%.4f (%d)" % (statistics.median(sm), len(sm)) if sm else "--",
                     "%.4f (%d)" % (statistics.median(lg), len(lg)) if lg else "--"))
    #: THE CORRELATION IS MOSTLY THE TWO GROUP MEDIANS. Printing them beside it
    #: is the whole point: a reader can see whether the r describes a trend or a
    #: step, and on this roster it is a step.
    print("\nThe two medians ARE what the correlation is made of -- 3 models sit")
    print("between 3B and 6B, so nothing here traces a curve. Read the columns,")
    print("not the r.")
    #: WHICH FINDINGS THIS THREATENS, AND WHICH IT CANNOT. The size step runs
    #: the SAME WAY as the alignment step on both axes and at a comparable
    #: magnitude, so it is not a small nuisance -- but it reaches the two
    #: contrasts in this folder very differently.
    print("\nSIZE MOVES MODELS THE SAME WAY ALIGNMENT DOES, AND COMPARABLY FAR")
    print("  %-34s %12s %12s" % ("", "surprisal", "drift"))
    print("  %-34s %12s %12s" % ("size step (aligned, <4B -> >=4B)", "-0.60", "-0.021"))
    print("  %-34s %12s %12s" % ("alignment step (lineage-paired)", "-0.84", "-0.025"))
    print("""
  THE ARM CONTRAST IS PROTECTED. `arm_paired.py` pairs each aligned checkpoint
  with its OWN base, and alignment does not change the weight shapes -- the two
  arms of a lineage have the same parameter count. Size cannot enter a
  within-lineage difference, so the base->aligned result is untouched by this.

  THE API CONTRAST IS NOT. `stem_paired.py` compares eleven commodity endpoints
  against open checkpoints of 0.4B to 10.3B. The endpoints are undisclosed but
  are not plausibly in that range, and bigger means less surprising here. So:

    API - aligned SURPRISAL (-0.0852)  runs WITH the size trend and is not
                                       separable from it on this evidence
    API - aligned DRIFT     (+0.0085)  runs AGAINST it -- bigger models drift
                                       LESS, and the API models drift MORE
""")
    print("API models carry no parameter count. Vendors do not publish them for")
    print("the eleven endpoints measured here, so they cannot enter the")
    print("regression -- only the direction of the threat can be reasoned about.")


if __name__ == "__main__":
    main()
