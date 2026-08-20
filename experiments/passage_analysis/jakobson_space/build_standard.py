"""Materialise the standard population as its own parquet.

    python .../build_standard.py

`population.standard()` is a per-row Python predicate over 432,064 rows -- it
calls `cjk_share` and a repetition check on every passage -- so every analysis
that wants the standard population pays tens of seconds to rebuild the same
boolean mask. This writes it once.

    passages.parquet        432,064   everything scored
    passages_std.parquet    358,633   RH's rule, plus a `has_both_axes` column

## THE FILTER IS NOT RE-IMPLEMENTED HERE

It calls `population.standard()`. A second copy of the rule would be a second
rule the first time either changed, and the whole point of `population.py` is
that there is one. This file only caches its verdict.

`filter_sha` records the SOURCE of population.py, so a filtered parquet built
under an older rule is identifiable rather than silently mixed with a newer one.

## `has_both_axes` IS PRECOMPUTED because it is not the same population

Drift covers 94.3% of passages and surprisal 100%, so an analysis using both
axes runs on 347,888 rows where a surprisal-only one runs on 358,633. Those are
different denominators, and quoting a rate from one against a count from the
other is the defect this column exists to make visible.
"""

import argparse, hashlib, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))

DATA = os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data"))
SRC = os.path.join(DATA, "jakobson_space", "passages.parquet")
OUT = os.path.join(DATA, "jakobson_space", "passages_std.parquet")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=SRC)
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args(argv)

    import numpy as np
    import pyarrow as pa
    import pyarrow.parquet as pq
    import population as P

    t = pq.read_table(a.src)
    d = t.to_pydict()
    n = t.num_rows
    print("source: %d rows, %d columns" % (n, t.num_columns))

    fl = P.zh_fluent()
    keep = np.array([P.standard(d["model"][i], d["text"][i], d["script"][i], fluent=fl)
                     for i in range(n)])
    bpb = np.array([x if x is not None else np.nan for x in d["bits_per_byte"]], float)
    mdr = np.array([x if x is not None else np.nan for x in d["mean_drift"]], float)
    both = keep & ~np.isnan(bpb) & ~np.isnan(mdr)

    out = t.filter(pa.array(keep))
    out = out.append_column("has_both_axes", pa.array(both[keep]))
    pq.write_table(out, a.out, compression="zstd")

    src = open(os.path.join(HERE, "population.py"), "rb").read()
    meta = dict(source=os.path.basename(a.src), rows_in=n, rows_kept=int(keep.sum()),
                rows_both_axes=int(both.sum()),
                filter="population.standard", filter_sha=hashlib.sha256(src).hexdigest()[:16],
                fluent_min=P.FLUENT_MIN, pure_min=P.PURE_MIN,
                zh_fluent_models=len(fl))
    with open(a.out.replace(".parquet", ".manifest.json"), "w") as fh:
        json.dump(meta, fh, indent=1)

    print("kept        : %d (%.1f%%)" % (keep.sum(), 100 * keep.mean()))
    print("both axes   : %d (%.1f%% of kept)" % (both.sum(), 100 * both.sum() / keep.sum()))
    print("zh-fluent   : %d models" % len(fl))
    print("filter sha  : %s" % meta["filter_sha"])
    print("-> %s (%.0f MB)" % (a.out, os.path.getsize(a.out) / 1e6))


if __name__ == "__main__":
    main()
