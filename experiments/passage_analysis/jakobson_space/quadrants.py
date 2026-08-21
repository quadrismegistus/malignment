"""Passage-level quadrant table: surprisal x drift, with drift residualised.

    python .../quadrants.py                       # summary
    python .../quadrants.py --csv results/quadrants.csv

Reads `results/two_axes.csv` and writes one row per passage with both axes, the
residualised drift, all three z-scores, and a quadrant label.

## THE RESIDUAL, AND WHY IT IS NEEDED LESS THAN IT LOOKS

Crossing two correlated axes does not give four populations, it gives a diagonal.
At the ENTITY level -- one median per model or corpus -- `r(surprisal, drift)` is
**+0.749** and the off-diagonal quadrants hold 16% of entities against the 50%
independence would give.

**But that correlation is largely an artefact of aggregation.** At the PASSAGE
level it is **+0.348**, and surprisal explains only **12%** of drift's variance
against 56% at entity level. So the raw passage axes are already close to
independent, and residualising is a modest correction here rather than the
rescue it is for the entity plane.

Both are provided. `drift` is the raw measurement; `drift_residual` is the OLS
residual of drift on surprisal, which is orthogonal to surprisal BY CONSTRUCTION
-- an arithmetic fact, not evidence, so the balanced quadrant counts it produces
are not a finding. What is substantive is WHICH passages land where.

## THE REFERENCE IS EVERY PASSAGE, POOLED, AND THAT IS A CHOICE

z-scores and the regression are computed over all 14,414 passages together --
open models, human anchor and API alike. Centring on a sub-population instead
moves membership substantially: at entity level, `salamandra-7b` is
`(+surp -drift)` against the six human corpora and `(+surp +drift)` against the
53 open models. So a quadrant label is meaningless without its reference, and
this file records the reference it used in the manifest beside the CSV.

## COLUMNS

    id                  the passage key. HETEROGENEOUS BY POOL, which is why the
                        text is carried here rather than left to a join:
                          huma-*            ref_pool.jsonl
                          mode-*            ref_pool.jsonl, and text_sha ->
                                            passages_std.parquet
                          <slug>-v4-NNN-S   api_passages/<slug>.jsonl
                        Three files, three key shapes. A reader wanting the
                        passage should not have to know which.
    text                the passage itself, AFTER clean() for API rows
    prompt              the stem it continues; empty for human passages, which
                        continue nothing
    text_sha            joins model passages to passages_std.parquet; empty for
                        human and API rows, which are not in it
    human_or_ai         human | ai
    category            base | aligned | API  for models; the corpus name for humans
    model               the model id, empty for human passages
    surprisal           deepseek bits/token over the first 200 tokens
    drift               bge mean_drift, uncontrolled (it is length-free)
    drift_residual      drift - (a + b*surprisal), fitted over all passages
    z_surprisal
    z_drift
    z_drift_residual
    quadrant            (+surp +drift) etc, on surprisal x DRIFT_RESIDUAL
    quadrant_raw        the same on surprisal x RAW drift, for comparison
"""

import argparse, collections, csv, json, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "results", "two_axes.csv")
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))

CATEGORIES = ["base", "aligned", "API"]


def quad(zs, zd):
    return ("(+surp +drift)" if zs > 0 and zd > 0 else
            "(+surp -drift)" if zs > 0 else
            "(-surp +drift)" if zd > 0 else "(-surp -drift)")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv")
    ap.add_argument("--src", default=SRC)
    a = ap.parse_args(argv)
    from malignment import roster
    al, ba = roster.population("aligned"), roster.population("bases")

    #: ---- text lookups, built once. The id shape differs by pool (see the
    #: docstring), so each pool gets its own map rather than one parse rule.
    DATA = os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data"))
    txt = {}
    for line in open(os.path.join(DATA, "ref_pool", "ref_pool.jsonl")):
        j = json.loads(line)
        txt[j["id"]] = (j.get("text", ""), j.get("prompt", ""))
    api_dir = os.path.join(DATA, "api_passages")
    if os.path.isdir(api_dir):
        for fn in os.listdir(api_dir):
            if not fn.endswith(".jsonl") or "_forscore" in fn:
                continue
            for line in open(os.path.join(api_dir, fn)):
                try:
                    j = json.loads(line)
                except ValueError:
                    continue
                if "stem" in j and "text" in j:
                    txt[j["id"]] = (j["text"], j["stem"])
    #: text_sha only exists for the open-model rows, and only they join to the
    #: parquet -- recorded rather than synthesised for the other two pools.
    sha = {}
    for line in open(os.path.join(DATA, "ref_pool", "deepseek", "ref_shard00.jsonl")):
        j = json.loads(line)
        sha[j["id"]] = j.get("text_sha", "")

    rows, no_text = [], 0
    for r in csv.DictReader(open(a.src)):
        if r["pool"] == "api":
            hoa, cat, model = "ai", "API", r["group"]
        elif r["pool"] == "human_anchor":
            hoa, cat, model = "human", r["group"], ""
        else:
            m = r["model"]
            cat = "base" if m in ba else "aligned" if m in al else None
            #: a model in NEITHER population is a scale child (Falcon3 size
            #: variants) -- excluded upstream as non-independent, and excluded
            #: here for the same reason rather than falling into a default.
            if not cat:
                continue
            hoa, model = "ai", m
        t, pr = txt.get(r["id"], ("", ""))
        if not t:
            no_text += 1
        rows.append(dict(id=r["id"], human_or_ai=hoa, category=cat, model=model,
                         text=t, prompt=pr if hoa == "ai" else "",
                         text_sha=sha.get(r["id"], ""),
                         surprisal=float(r["bits_per_token"]),
                         drift=float(r["mean_drift"])))

    S = [r["surprisal"] for r in rows]
    D = [r["drift"] for r in rows]
    mS, mD = statistics.mean(S), statistics.mean(D)
    b = sum((s - mS) * (d - mD) for s, d in zip(S, D)) / sum((s - mS) ** 2 for s in S)
    aa = mD - b * mS
    for r in rows:
        r["drift_residual"] = r["drift"] - (aa + b * r["surprisal"])
    R = [r["drift_residual"] for r in rows]
    sS, sD, sR = statistics.pstdev(S), statistics.pstdev(D), statistics.pstdev(R)
    mR = statistics.mean(R)
    for r in rows:
        r["z_surprisal"] = (r["surprisal"] - mS) / sS
        r["z_drift"] = (r["drift"] - mD) / sD
        r["z_drift_residual"] = (r["drift_residual"] - mR) / sR
        r["quadrant"] = quad(r["z_surprisal"], r["z_drift_residual"])
        r["quadrant_raw"] = quad(r["z_surprisal"], r["z_drift"])

    r_raw = (sum((s - mS) * (d - mD) for s, d in zip(S, D))
             / ((sum((s - mS) ** 2 for s in S) * sum((d - mD) ** 2 for d in D)) ** 0.5))
    print("%d passages | OLS drift = %.6f + %.6f * surprisal" % (len(rows), aa, b))
    #: SAY IT if any passage lost its text. A silent empty column is the defect
    #: this file exists to avoid making the reader chase.
    print("  text resolved for %d of %d rows%s"
          % (len(rows) - no_text, len(rows),
             "" if not no_text else "  <-- %d MISSING" % no_text))
    print("  r(surprisal, drift) = %+.3f | surprisal explains %.0f%% of drift variance"
          % (r_raw, 100 * (1 - (sR / sD) ** 2)))

    QS = ["(+surp +drift)", "(+surp -drift)", "(-surp +drift)", "(-surp -drift)"]
    #: ENRICHMENT against the pooled rate. A share alone cannot say whether a
    #: category is over- or under-represented in a cell, because the four cells
    #: are not equal-sized -- the pooled rates run 23.0% to 28.1%, so a flat 25%
    #: is enrichment in one cell and depletion in another. Reading shares as
    #: enrichment is the error this block exists to prevent.
    overall = collections.Counter(r["quadrant"] for r in rows)
    N = len(rows)
    order_all = CATEGORIES + sorted({r["category"] for r in rows} - set(CATEGORIES))
    byc = collections.defaultdict(collections.Counter)
    for r in rows:
        byc[r["category"]][r["quadrant"]] += 1
    print("\nENRICHMENT vs the pooled rate (1.00x = the same share as all %d "
          "passages)" % N)
    print("pooled: %s" % "  ".join("%s %.1f%%" % (q, 100 * overall[q] / N) for q in QS))
    print("%-22s %7s   %s" % ("", "n", " ".join("%-15s" % q for q in QS)))
    for c in order_all:
        t = sum(byc[c].values())
        print("%-22s %7d   %s" % (c, t, " ".join(
            "%-15s" % ("%5.2fx" % ((byc[c][q] / t) / (overall[q] / N))) for q in QS)))
    #: the two off-diagonal cells carry the Jakobsonian names, so the gradient
    #: across the three AI categories is printed on its own rather than left to
    #: be read off a nine-row table.
    print("\nthe two off-diagonal cells, across the arms")
    print("%-22s %16s %16s" % ("", "(+surp -drift)", "(-surp +drift)"))
    print("%-22s %16s %16s" % ("", "METAPHORIC", "METONYMIC"))
    for c in order_all:
        t = sum(byc[c].values())
        print("%-22s %15.2fx %15.2fx"
              % (c, (byc[c]["(+surp -drift)"] / t) / (overall["(+surp -drift)"] / N),
                 (byc[c]["(-surp +drift)"] / t) / (overall["(-surp +drift)"] / N)))
    hum = [r for r in rows if r["human_or_ai"] == "human"]
    if hum:
        hc = collections.Counter(r["quadrant"] for r in hum)
        print("%-22s %15.2fx %15.2fx"
              % ("ALL HUMAN", (hc["(+surp -drift)"] / len(hum)) / (overall["(+surp -drift)"] / N),
                 (hc["(-surp +drift)"] / len(hum)) / (overall["(-surp +drift)"] / N)))

    for axis, key in (("RESIDUALISED drift", "quadrant"), ("RAW drift", "quadrant_raw")):
        by = collections.defaultdict(collections.Counter)
        for r in rows:
            by[r["category"]][r[key]] += 1
        print("\n%s\n%-26s %6s   %s" % (axis, "category", "n",
                                        " ".join("%-15s" % q for q in QS)))
        order = CATEGORIES + sorted(k for k in by if k not in CATEGORIES)
        for c in order:
            t = sum(by[c].values())
            print("%-26s %6d   %s" % (c, t, " ".join(
                "%-15s" % ("%5.1f%%" % (100 * by[c][q] / t)) for q in QS)))

    if a.csv:
        cols = ["id", "human_or_ai", "category", "model", "prompt", "text",
                "text_sha", "surprisal", "drift",
                "drift_residual", "z_surprisal", "z_drift", "z_drift_residual",
                "quadrant", "quadrant_raw"]
        with open(a.csv, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            for r in rows:
                w.writerow({k: (round(v, 6) if isinstance(v, float) else v)
                            for k, v in r.items()})
        man = a.csv.rsplit(".", 1)[0] + ".manifest.json"
        json.dump(dict(n=len(rows), source=os.path.basename(a.src),
                       reference="all passages pooled",
                       ols=dict(intercept=aa, slope=b),
                       r_surprisal_drift=r_raw,
                       variance_explained=1 - (sR / sD) ** 2,
                       mean=dict(surprisal=mS, drift=mD, drift_residual=mR),
                       sd=dict(surprisal=sS, drift=sD, drift_residual=sR)),
                  open(man, "w"), indent=1)
        print("\n-> %s  (%d rows)\n-> %s" % (a.csv, len(rows), man))


if __name__ == "__main__":
    main()
