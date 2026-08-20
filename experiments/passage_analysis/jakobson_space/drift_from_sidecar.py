"""Drift metrics from a bge sidecar, for any corpus scored by `bge_human.py`.

    python .../drift_from_sidecar.py --dir $MALIGNMENT_DATA/jakobson_space/bge_human
    python .../drift_from_sidecar.py --dir $MALIGNMENT_DATA/wrapper_confound/bge

Reads `bge_*NN.jsonl` plus its `.f32`, slices each passage's sentence vectors by
the stored `row`/`n`, and writes `drift.jsonl` beside them.

The metric code is IMPORTED from `../drift_geometry/drift_metrics.py`, which is
the ported archive implementation the model side used. Not re-derived here: a
cosine distance is easy to write and easy to write differently, and `mean_drift`
computed over a different pairing would not be comparable to the 337,355 model
passages it exists to be compared against.

## THE SIDECAR IS WHY THIS IS CHEAP

`bge_human.py` stores vectors, not metrics. Any drift statistic -- including ones
nobody has thought of -- is a slice and a few dot products away, with no
re-embedding. The same holds for BLT: per-byte surprisal in a `.f32` means
bits/byte over any prefix is a partial sum.

## WHICH METRICS ARE SAFE TO COMPARE ACROSS CORPORA

Measured on 327,207 English model passages, correlation with sentence count:

    mean_pairwise  -0.003     mean_drift  -0.050     ordering    -0.097
    max_drift      +0.323     total_drift +0.439     directedness -0.691
    path_length    +0.965

`mean_drift` is a per-step mean, so length divides out. The cumulative metrics
grow with sentence count by construction, and the human corpora differ in it
systematically -- 8 sentences for abstracts and literary criticism against 13 for
waking narrative -- so a cross-corpus comparison on `total_drift`,
`path_length` or `directedness` would largely be a length comparison. All are
written; only the length-free ones should carry a claim.
"""

import argparse, glob, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "drift_geometry"))
from drift_metrics import metrics                            # noqa: E402

DATA = os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data"))
SAFE = ("mean_drift", "mean_pairwise", "ordering")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.path.join(DATA, "jakobson_space", "bge_human"))
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    import numpy as np

    out = a.out or os.path.join(a.dir, "drift.jsonl")
    rows, n_short = [], 0
    for jl in sorted(glob.glob(os.path.join(a.dir, "bge_*[0-9].jsonl"))):
        fb = jl[:-len(".jsonl")] + ".f32"
        if not os.path.exists(fb):
            print("  no sidecar for %s, skipped" % os.path.basename(jl))
            continue
        size = os.path.getsize(fb)
        for line in open(jl):
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            dim, row, n = d["dim"], d["row"], d["n"]
            #: REFUSE a pointer past the end rather than let numpy return a short
            #: array and produce a metric over the wrong sentences.
            assert (row + n) * 4 <= size, (
                "%s: row %d + n %d runs past a %d-byte sidecar" % (d["id"], row, n, size))
            v = np.fromfile(fb, dtype=np.float32, count=n, offset=row * 4).reshape(-1, dim)
            assert v.shape[0] == d["n_sentences"], (
                "%s: %d vectors for %d sentences" % (d["id"], v.shape[0], d["n_sentences"]))
            m = metrics(v)
            if "mean_drift" not in m:
                n_short += 1
                continue                      # single-sentence passage: no step
            m.update(id=d["id"], corpus=d.get("corpus"), splitter=d.get("splitter"),
                     ref=d.get("ref"))
            for k in ("model", "prompt"):
                if d.get(k):
                    m[k] = d[k]
            rows.append(m)

    with open(out, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")

    import collections, statistics as st
    by = collections.defaultdict(list)
    for r in rows:
        by[r.get("corpus")].append(r)
    print("%-22s %7s %9s %13s %11s %9s"
          % ("corpus", "n", "n_sents", "mean_drift", "mean_pair", "ordering"))
    for k in sorted(by, key=lambda x: str(x)):
        g = by[k]
        print("%-22s %7d %9.1f %13.4f %11.4f %+9.4f"
              % (k, len(g), st.mean([x["n_sents"] for x in g]),
                 st.mean([x["mean_drift"] for x in g]),
                 st.mean([x["mean_pairwise"] for x in g]),
                 st.mean([x["ordering"] for x in g])))
    if n_short:
        print("\n%d passage(s) with <2 sentences, no drift defined" % n_short)
    print("\nlength-free metrics (safe across corpora): %s" % ", ".join(SAFE))
    print("-> %s  (%d passages)" % (out, len(rows)))


if __name__ == "__main__":
    main()
