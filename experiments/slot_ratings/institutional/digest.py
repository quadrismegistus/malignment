"""Pre-digest the two position corpora into one compact table.

    python experiments/slot_ratings/institutional/digest.py          # build + verify
    python experiments/slot_ratings/institutional/digest.py --force  # rebuild

`f21.json` and `m03.json` are 5.1 MB and 54.8 MB of JSON and every consumer pays
that cost to reach a few columns. They hold one record per (prompt, lineage,
position) cell with `base_<scale>`, `aligned_<scale>` and `cov_<arm>_<scale>` for
24 scales, which is a rectangle wearing a nested format.

This writes that rectangle to parquet ONCE. It computes nothing: no statistic, no
selection, no aggregation. Every row of both corpora survives, and `corpus` is a
column so the two stay separable.

## The digest is derived, and it is not a witness

`bundle_ishould.py` and every other producer keep reading the JSON. That is
deliberate. If the analysis read the digest, a bug here would move published
numbers with nothing to compare against; because it does not, `verify()` can
check the digest against `ishould.json`'s booked levels and a disagreement
accuses the digest rather than the finding.

Delete the parquet at any time; the next `load()` rebuilds it.
"""

import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results", "base_side")
CELLS = os.path.join(OUT, "position_cells.parquet")

#: The two corpora reading the `movement` table. slotpov is excluded and that is
#: not an omission: its 12 prompts have ZERO rows in `movement` and come from
#: `twp_words_v4_best`, so pooling it here would silently mix two sources.
CORPORA = ("f21", "m03")

KEYS = ("prompt", "lineage", "position", "stratum", "cluster",
        "mass_base", "mass_aligned")


def build(force=False, quiet=False):
    import pandas as pd
    if os.path.exists(CELLS) and not force:
        return pd.read_parquet(CELLS)
    recs = []
    for c in CORPORA:
        p = os.path.join(OUT, "%s.json" % c)
        if not os.path.exists(p):
            raise SystemExit("missing %s -- run run_%s.py" % (p, c))
        d = json.load(open(p))
        for r in d["rows"]:
            recs.append(dict(r, corpus=c))
        if not quiet:
            print("  %-4s %6d cells  (%.1f MB json)"
                  % (c, len(d["rows"]), os.path.getsize(p) / 1048576))
    df = pd.DataFrame.from_records(recs)
    #: str dtype for the identifier columns: a groupby on Arrow-backed strings
    #: with NA keys silently DROPS those groups, which is how 53 rungs went
    #: missing from a figure elsewhere in this campaign without raising.
    for k in ("prompt", "lineage", "position", "stratum", "cluster", "corpus"):
        if k in df:
            df[k] = df[k].astype("string").fillna("?").astype(str)
    os.makedirs(OUT, exist_ok=True)
    df.to_parquet(CELLS, index=False, compression="zstd")
    if not quiet:
        print("  -> %s  %d rows x %d cols, %.1f MB"
              % (os.path.relpath(CELLS, HERE), len(df), df.shape[1],
                 os.path.getsize(CELLS) / 1048576))
    return df


def load(force=False):
    """The table. Builds it on first use."""
    import pandas as pd
    if os.path.exists(CELLS) and not force:
        return pd.read_parquet(CELLS)
    return build(force=force, quiet=True)


def scales(df):
    return sorted(c[5:] for c in df.columns if c.startswith("base_"))


def ishould(df=None):
    """The 'I should' selection, by the SAME rule `bundle_ishould.py` applies.

    Imported rather than restated: two copies of a selection rule drift, and this
    one decides which 2,600 of 13,800 cells a finding rests on.
    """
    sys.path.insert(0, HERE)
    from bundle_ishould import SUFFIX
    df = load() if df is None else df
    return df[df.prompt.str.rstrip().str.endswith(SUFFIX)].copy()


def verify(df=None):
    """Check the digest against `ishould.json`'s booked levels.

    The digest must reproduce every level the finding quotes. This runs the same
    unweighted mean over the same selection and refuses on any disagreement above
    float noise, naming the scale and both values.
    """
    import statistics as st
    d = ishould(df)
    book = json.load(open(os.path.join(OUT, "ishould.json")))
    assert book["n_prompts"] == d.prompt.nunique(), (
        "prompt count: booked %d, digest %d" % (book["n_prompts"], d.prompt.nunique()))
    bad, n = [], 0
    for row in book["rows"]:
        s = row["scale"]
        for arm in ("base", "aligned"):
            for pos in ("indiv", "inst"):
                col = "%s_%s" % (arm, s)
                v = d[d.position == pos][col].dropna()
                got, want = st.mean(v), row["%s_%s" % (arm, pos)]
                n += 1
                if abs(got - want) > 1e-9:
                    bad.append("%s %s/%s: digest %.6f booked %.6f" % (s, arm, pos, got, want))
    if bad:
        raise SystemExit("DIGEST DISAGREES WITH ishould.json on %d of %d levels:\n  %s"
                         % (len(bad), n, "\n  ".join(bad[:10])))
    print("  verified %d booked levels against ishould.json, worst |diff| < 1e-9" % n)
    print("  'I should' selection: %d cells, %d prompts, %d lineages, %d clusters"
          % (len(d), d.prompt.nunique(), d.lineage.nunique(), d.cluster.nunique()))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--force", action="store_true", help="rebuild even if present")
    a = ap.parse_args()
    df = build(force=a.force)
    print("  %d rows, %d scales: %s" % (len(df), len(scales(df)), ", ".join(scales(df))))
    verify(df)
