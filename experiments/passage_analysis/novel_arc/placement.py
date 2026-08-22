"""Where model prose sits on the historical abstraction axis.

    python .../placement.py

Reads the chadwyck series and the scored model corpus and puts them on one
scale. Reports the PASSAGE-level distribution for each population, and where
each model arm falls as a PERCENTILE of the chadwyck passage distribution.

## THE COMPARISON IS PASSAGE TO PASSAGE, AND BOTH SIDES ARE ~200 WORDS

chadwyck is chunked at n=200 by sentence accumulation (median 216 words); the
model passages are ~200 tokens and the human anchor ~193 words. Close enough to
compare directly, and the alternative -- text-level means for chadwyck against
passage-level for models -- would compare a distribution of book averages
against a distribution of individual passages, which are not the same object.

## PERCENTILE, NOT DISTANCE FROM A MEAN

"More abstract than the C18" is a claim about where a value falls in a
distribution, and the chadwyck passage distribution is wide. A model median
quoted as a distance from a period mean says nothing about whether it is inside
or outside the range of what was actually written.

Sign: HIGH = CONCRETE. More abstract is more NEGATIVE.
"""

import argparse, collections, os, statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
#: RESULTS GO TO $MALIGNMENT_DATA, NOT THE REPO. The chadwyck table is 128 MB
#: and chicago is ~760 MB; `results/` here is untracked but was not ignored, so
#: a single careless `git add` on the folder would have swept them in.
DATA = os.path.join(os.environ.get("MALIGNMENT_DATA",
                                   os.path.expanduser("~/malignment-data")),
                    "novel_arc")
COL = "rh_absconc_median"


def pctile(v, arr):
    return 100.0 * sum(1 for x in arr if x < v) / len(arr)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--hist", nargs="*", default=None,
                    help="historical parquets; default chadwyck + chicago "
                         "if present")
    ap.add_argument("--models", default=os.path.join(DATA,
                                                     "model_placement.parquet"))
    ap.add_argument("--col", default=COL)
    a = ap.parse_args(argv)
    import pyarrow.parquet as pq

    #: the historical scale is built from EVERY corpus given, and each is kept
    #: labelled -- pooling them into one anonymous distribution would hide that
    #: chadwyck and chicago overlap only 1880-1954 and disagree there or not.
    srcs = a.hist
    if not srcs:
        srcs = [os.path.join(DATA, f) for f in
                ("chadwyck_n200.parquet", "chicago_n200.parquet")]
        srcs = [f for f in srcs if os.path.exists(f)]
    hist, bysrc = [], {}
    for f in srcs:
        t = pq.read_table(f, columns=["year", a.col])
        rows = [(y, v) for y, v in zip(t.column("year").to_pylist(),
                                       t.column(a.col).to_pylist())
                if v is not None and y]
        name = os.path.basename(f).split("_")[0]
        bysrc[name] = rows
        hist += rows
    allc = sorted(v for _, v in hist)
    print("historical scale: %s passages from %s"
          % ("{:,}".format(len(allc)), ", ".join(
              "%s (%s)" % (k, "{:,}".format(len(v))) for k, v in bysrc.items())))
    print("  passage distribution  p5 %+.3f  p25 %+.3f  median %+.3f  p75 %+.3f  p95 %+.3f"
          % (allc[len(allc)//20], allc[len(allc)//4], st.median(allc),
             allc[3*len(allc)//4], allc[19*len(allc)//20]))

    #: PER SOURCE as well as pooled. Where two corpora cover the same period,
    #: agreement is evidence the period value is a property of the writing and
    #: not of the collection; disagreement is the thing to report first.
    print("\nBY PERIOD (passage medians), each corpus separately")
    names = list(bysrc)
    pers = {n: collections.defaultdict(list) for n in names}
    for n in names:
        for y, v in bysrc[n]:
            pers[n][(int(y) // 25) * 25].append(v)
    keys = sorted({k for n in names for k in pers[n]})
    print("  %-6s %s" % ("period", "  ".join("%-22s" % n for n in names)))
    for k in keys:
        cells = []
        for n in names:
            v = pers[n].get(k, [])
            cells.append("%-22s" % ("%+.4f (n=%s)" % (st.median(v),
                                                      "{:,}".format(len(v)))
                                    if len(v) >= 500 else "-"))
        print("  %-6d %s" % (k, "  ".join(cells)))
    per = collections.defaultdict(list)
    for y, v in hist:
        per[(int(y)//25)*25].append(v)

    md = pq.read_table(a.models, columns=["category", "human_or_ai", a.col])
    cat = md.column("category").to_pylist()
    mv = md.column(a.col).to_pylist()
    byc = collections.defaultdict(list)
    for c, v in zip(cat, mv):
        if v is not None:
            byc[c].append(v)
    order = ["base", "aligned", "API"] + sorted(set(byc) - {"base", "aligned", "API"})
    print("\nMODEL AND HUMAN-ANCHOR POPULATIONS, placed on the pooled scale")
    print("  %-22s %7s %10s %9s  %s" % ("population", "n", "median", "pctile",
                                        "nearest period"))
    pm = {k: st.median(v) for k, v in per.items() if len(v) >= 500}
    for c in order:
        v = byc.get(c)
        if not v:
            continue
        m = st.median(v)
        near = min(pm, key=lambda k: abs(pm[k] - m))
        #: a model can fall OUTSIDE the historical range entirely, in which case
        #: "nearest period" is an endpoint and says nothing -- flag it.
        #: the flag says ONLY that the value falls outside every period median.
        #: It was previously worded "MORE ABSTRACT"/"MORE CONCRETE", which is
        #: hardcoded to the abstraction column and reads as a flat error on any
        #: other -- on `usas_x` a value above every period is MORE INTERIOR,
        #: and the old label called it more concrete.
        out = ""
        if m < min(pm.values()):
            out = "  <-- BELOW EVERY PERIOD MEDIAN"
        elif m > max(pm.values()):
            out = "  <-- ABOVE EVERY PERIOD MEDIAN"
        print("  %-22s %7s %+10.4f %8.1f%%  %d%s"
              % (c, "{:,}".format(len(v)), m, pctile(m, allc), near, out))


if __name__ == "__main__":
    main()
