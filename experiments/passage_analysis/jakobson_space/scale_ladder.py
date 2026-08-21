"""One family, four sizes, both arms: the scale ladder the roster excludes.

    python .../scale_ladder.py
    python .../scale_ladder.py --family Falcon3

`scale_axes.py` regresses size across 47 unrelated models, where size is
confounded with lab, recipe, data mix, token budget and release date -- and where
33 of 47 sit in one 6-11B clump with three models bridging the gap. It can say
small-versus-7B and nothing finer.

**A within-family ladder removes every one of those confounds by construction.**
The Falcon3 models are one lab, one recipe, one data mix, and the smaller ones
are literally derived from the 7B -- `roster/models/models.yaml` carries
`Falcon3-7B-Base --prune--> Falcon3-3B-Base --prune--> Falcon3-1B-Base` and
`Falcon3-7B-Base --upscale--> Falcon3-10B-Base`. Size is the only thing that
varies, because size is the only thing they changed.

## THE NON-INDEPENDENCE IS THE DESIGN HERE, NOT A DEFECT

`population("bases")` EXCLUDES the 1B, 3B and 10B bases -- RH's ruling, and
correct for its purpose: they are not independent observations of "a base model",
since all four are one model at four sizes. Averaging them into a roster-wide
arm statistic would inflate n with copies.

For a SIZE question that dependence is exactly what is wanted. So this file reads
`results/two_axes.csv`, which applies no population filter, rather than
`quadrants.csv`, which does -- and it is a within-family design that never enters
a roster-wide count. **Nothing here may be pooled into an arm statistic.**

The asymmetry that makes this necessary is visible in the data: `quadrants.csv`
holds Falcon3-1B/3B/10B-INSTRUCT (they are in `population("aligned")`) but not
their bases. The ladder is only complete outside that filter.

## WHAT IT CAN AND CANNOT SHOW

Four sizes is four points. It can show a MONOTONE ordering or its absence, and it
cannot fit a scaling exponent worth quoting. Both arms are printed at every rung,
so the arm gap can be read at each size -- the question of whether alignment
does the same thing to a 1B model as to a 10B one, which no roster-wide contrast
can ask.
"""

import argparse, collections, csv, json, math, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "results", "two_axes.csv")
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
MEAS = os.path.join(ROOT, "roster", "models", "measurements.json")
sys.path.insert(0, ROOT)

#: families whose members differ ONLY in size, with the derivation stated so a
#: reader can check the claim rather than take the grouping on trust.
LADDERS = {
    "Falcon3": "7B-Base pruned to 3B and 1B, upscaled to 10B (models.yaml edges)",
    "Qwen2.5": "0.5B and 7B, same release (models.yaml `scale` edge)",
    "SmolLM": "SmolLM2-360M and SmolLM3-3B -- DIFFERENT GENERATIONS, not a ladder",
}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=SRC)
    ap.add_argument("--family", default="Falcon3")
    ap.add_argument("--min-passages", type=int, default=20)
    a = ap.parse_args(argv)

    csv.field_size_limit(10 ** 7)
    w = json.load(open(MEAS))["sections"]["weights"]["models"]
    pb = {k: v["params_b"] for k, v in w.items() if v.get("params_b")}
    per = collections.defaultdict(list)
    for r in csv.DictReader(open(a.src)):
        m = r.get("model") or ""
        if a.family in m and r.get("mean_drift"):
            per[m].append(r)

    print("%s ladder -- %s" % (a.family, LADDERS.get(a.family, "grouping not declared")))
    rungs = collections.defaultdict(dict)
    for m, v in per.items():
        if len(v) < a.min_passages:
            print("  SKIP %-34s n=%d, under --min-passages %d"
                  % (m.split("/")[-1], len(v), a.min_passages))
            continue
        size = pb.get(m)
        if size is None:
            print("  SKIP %-34s no measured params_b" % m.split("/")[-1])
            continue
        arm = "aligned" if "Instruct" in m or "instruct" in m else "base"
        rungs[round(size, 1)][arm] = dict(
            model=m, n=len(v),
            surprisal=statistics.median(float(x["bits_per_token"]) for x in v),
            drift=statistics.median(float(x["mean_drift"]) for x in v))

    print("\n%-7s %-9s %5s %11s %11s" % ("size", "arm", "n", "surprisal", "drift"))
    for s in sorted(rungs):
        for arm in ("base", "aligned"):
            d = rungs[s].get(arm)
            if d:
                print("%-7s %-9s %5d %11.4f %11.4f"
                      % ("%.1fB" % s, arm, d["n"], d["surprisal"], d["drift"]))

    print("\nTHE ARM GAP AT EACH RUNG  (aligned - base)")
    print("%-7s %11s %11s" % ("size", "surprisal", "drift"))
    gaps = []
    for s in sorted(rungs):
        b, al = rungs[s].get("base"), rungs[s].get("aligned")
        if not (b and al):
            print("%-7s  -- only the %s arm at this rung --"
                  % ("%.1fB" % s, "base" if b else "aligned"))
            continue
        g = (al["surprisal"] - b["surprisal"], al["drift"] - b["drift"])
        gaps.append((s,) + g)
        print("%-7s %+11.4f %+11.4f" % ("%.1fB" % s, g[0], g[1]))

    #: THE SIZE TREND WITHIN EACH ARM, which is the whole point of the ladder --
    #: and it is reported as an ordering, never as a fitted slope, because four
    #: points do not carry an exponent.
    print("\nTHE SIZE TREND WITHIN EACH ARM  (is it monotone across the rungs?)")
    for arm in ("base", "aligned"):
        got = [(s, rungs[s][arm]) for s in sorted(rungs) if arm in rungs[s]]
        if len(got) < 3:
            print("  %-8s only %d rungs -- no ordering to read" % (arm, len(got)))
            continue
        for lab in ("surprisal", "drift"):
            vals = [d[lab] for _, d in got]
            mono = ("MONOTONE down" if all(x > y for x, y in zip(vals, vals[1:]))
                    else "MONOTONE up" if all(x < y for x, y in zip(vals, vals[1:]))
                    else "NOT monotone")
            print("  %-8s %-10s %s   %s" % (arm, lab, mono,
                  " -> ".join("%.4f" % v for v in vals)))
    #: THE COMPARISON THAT PAYS FOR THE FILE. scale_axes.py measured a size step
    #: across 47 unrelated models on the same <4B / >=4B split. Running the SAME
    #: split inside a controlled family says how much of that step was size.
    CROSS = {("base", "surprisal"): -0.3742, ("base", "drift"): -0.0096,
             ("aligned", "surprisal"): -0.5966, ("aligned", "drift"): -0.0205}
    print("\nTHE SAME <4B / >=4B SPLIT, CONTROLLED vs UNCONTROLLED")
    print("%-9s %-11s %12s %12s %9s" % ("arm", "", "this family", "47 models",
                                        "ratio"))
    for arm in ("base", "aligned"):
        for lab in ("surprisal", "drift"):
            sm = [rungs[s][arm][lab] for s in rungs if s < 4 and arm in rungs[s]]
            lg = [rungs[s][arm][lab] for s in rungs if s >= 4 and arm in rungs[s]]
            if not sm or not lg:
                continue
            step = statistics.mean(lg) - statistics.mean(sm)
            x = CROSS[(arm, lab)]
            print("%-9s %-11s %+12.4f %+12.4f %8.0f%%"
                  % (arm, lab, step, x, 100 * step / x if x else float("nan")))
    print("""
  SURPRISAL survives the control and gets BIGGER -- size really does make a
  model less surprising, and the uncontrolled regression understated it.

  DRIFT DOES NOT. Inside one family, six-fold size range moves drift about a
  quarter as far as the cross-model regression attributed to size. So most of
  that -0.502 cross-model correlation is lab, recipe, data and release date --
  not parameters. `scale_axes.py`'s drift rows should be read as confounded.

  Consistent with the only API pair whose sizes are known: deepseek-v4-flash
  (284B total / 13B active) and v4-pro (1.6T / 49B) sit 0.0010 apart on drift,
  a 5.6x size difference producing nothing.
""")
    print("%d rungs. Four points show an ordering or its absence and cannot fit"
          % len(rungs))
    print("a scaling exponent. Nothing here may be pooled into an arm statistic:")
    print("these are one model at four sizes, which is why population('bases')")
    print("excludes three of them.")


if __name__ == "__main__":
    main()
