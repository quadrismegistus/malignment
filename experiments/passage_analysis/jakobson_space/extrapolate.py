"""Where does the open-model size trend PREDICT the API models should sit?

    python .../extrapolate.py

RH, 2026-08-21: "Frontier models are 2 orders of magnitude larger than these
ones we have; if size drives down surprisal, it seems likelier that's the cause
than the prompt." Right in principle -- so the way to settle it is to fit the
trend where we can measure it and ask where it puts the models we cannot.

Only two API models have disclosed sizes, both DeepSeek, so this is a check on
two points and not a fit. It is still the only quantitative purchase available.

## TOTAL PARAMETERS AND ACTIVE PARAMETERS GIVE COMPLETELY DIFFERENT ANSWERS

Both DeepSeek models are mixture-of-experts:

    deepseek-v4-flash    284B total,  13B active per token
    deepseek-v4-pro      1.6T total,  49B active per token

Our open models are dense, so their total IS their active. "Two orders of
magnitude larger" is true of TOTAL and false of ACTIVE: against our largest
measured model (Falcon3-10B at 10.3B), v4-flash is **1.3x** on active parameters
and v4-pro is **4.8x**. On total it is 28x and 155x.

Which one the trend should be extrapolated on is a real question and not a
detail: a dense 10B and an MoE routing 13B of 284B do the same arithmetic per
token and hold very different amounts. Both are computed here.

## THE TREND IS FITTED ON THE CONTROLLED LADDER, NOT THE 47-MODEL REGRESSION

`scale_ladder.py` showed the cross-model regression is confounded on drift and
understates size on surprisal. So the slope comes from the Falcon3 ladder --
one lab, one recipe, one data mix, size the only variable -- fitted on the
aligned arm, which is the arm the API models belong to.

Two rungs (1.7B and 10.3B) define the slope and the middle two are printed
against it, so a reader can see how well a straight line describes four points
before trusting it two decades out. It does not describe them perfectly: the
3.2B rung is the most surprising of the four.
"""

import argparse, collections, csv, json, math, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "results", "two_axes.csv")
QUAD = os.path.join(HERE, "results", "quadrants.csv")
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
MEAS = os.path.join(ROOT, "roster", "models", "measurements.json")

#: DISCLOSED by the vendor, verified against the HF model card and arXiv
#: 2606.19348 by an agent that was told to return UNKNOWN rather than guess.
#: The other nine endpoints publish nothing and cannot appear here at all.
API_SIZES = {
    "deepseek-v4-flash": dict(total_b=284.0, active_b=13.0),
    "deepseek-v4-pro": dict(total_b=1600.0, active_b=49.0),
}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", default="Falcon3")
    a = ap.parse_args(argv)

    csv.field_size_limit(10 ** 7)
    w = json.load(open(MEAS))["sections"]["weights"]["models"]
    pb = {k: v["params_b"] for k, v in w.items() if v.get("params_b")}
    per = collections.defaultdict(list)
    for r in csv.DictReader(open(SRC)):
        m = r.get("model") or ""
        if a.family in m and ("Instruct" in m or "instruct" in m):
            per[m].append(float(r["bits_per_token"]))
    rungs = sorted((pb[m], statistics.median(v), m) for m, v in per.items()
                   if m in pb and len(v) >= 20)
    if len(rungs) < 2:
        raise SystemExit("need two rungs")
    (x0, y0, m0), (x1, y1, m1) = rungs[0], rungs[-1]
    slope = (y1 - y0) / (math.log10(x1) - math.log10(x0))
    print("SLOPE from the %s ALIGNED ladder: %.3f bits per decade of parameters"
          % (a.family, slope))
    print("  fitted on %.1fB (%.4f) and %.1fB (%.4f)" % (x0, y0, x1, y1))
    print("\n  how well does one line describe the four rungs?")
    for x, y, m in rungs:
        pred = y0 + slope * (math.log10(x) - math.log10(x0))
        print("    %-30s %5.1fB  observed %.4f  line %.4f  %+.4f"
              % (m.split("/")[-1], x, y, pred, y - pred))

    #: the observed API values, from the same table and the same M=200 prefix
    obs = collections.defaultdict(list)
    for r in csv.DictReader(open(QUAD, newline="")):
        if r["category"] == "API":
            obs[r["model"]].append(float(r["surprisal"]))
    al = [float(r["surprisal"]) for r in csv.DictReader(open(QUAD, newline=""))
          if r["category"] == "aligned"]
    al_med = statistics.median(al)

    print("\nWHERE THE TREND PUTS THE TWO API MODELS WHOSE SIZE IS DISCLOSED")
    print("%-20s %9s %10s %10s %10s" % ("", "size", "predicted", "observed", "gap"))
    for name, d in API_SIZES.items():
        if name not in obs:
            print("%-20s -- not measured here --" % name)
            continue
        o = statistics.median(obs[name])
        for kind in ("active_b", "total_b"):
            x = d[kind]
            pred = y0 + slope * (math.log10(x) - math.log10(x0))
            print("%-20s %8.0fB %10.4f %10.4f %+10.4f"
                  % ("%s (%s)" % (name.split("-")[-1], kind[:-2]), x, pred, o,
                     o - pred))

    print("\nTHE OPEN ALIGNED MEDIAN IS %.4f, AND EVERY API MODEL SITS NEAR IT"
          % al_med)
    print("%-24s %10s %10s" % ("", "surprisal", "vs aligned"))
    for m, v in sorted(obs.items(), key=lambda kv: statistics.median(kv[1])):
        print("%-24s %10.4f %+10.4f" % (m, statistics.median(v),
                                        statistics.median(v) - al_med))
    print("""
READ IT THIS WAY.

  ON ACTIVE PARAMETERS the trend roughly WORKS for v4-flash: 13B active is 1.3x
  our largest dense model, the line predicts a small drop, and a small drop is
  what there is. Size is a sufficient explanation for that one.

  ON TOTAL PARAMETERS it fails badly for both, predicting drops of 1-2 bits that
  do not occur. A 1.6T model writes about as unpredictably as an 8B one.

  AND THE WHOLE API SET SITS IN THE OPEN ALIGNED RANGE. Whatever these models
  are, they are not two decades down a size trend. Either the trend saturates
  well before frontier scale, or active parameters is the operative variable and
  frontier active counts are close to ours, or something pushes back up against
  size. This file cannot separate those three, and nine of the eleven endpoints
  publish no size at all, so for them the question is not open -- it is unaskable.
""")


if __name__ == "__main__":
    main()
