"""The chadwyck series: coverage first, then RH's axis, then the LLM axis.

    python .../arc.py                      # 25-year bins
    python .../arc.py --bin 50 --min-texts 8

## THE TEXT IS THE UNIT, NOT THE PASSAGE

Book length varies by an order of magnitude, so pooling passages lets a few long
novels set a decade's value. Every column is therefore averaged WITHIN text
first and the bin statistic is the median over TEXTS. `n_texts` is printed
beside every row because a bin of four texts is an anecdote whatever its
passage count says.

## COVERAGE IS READ BEFORE ANY CONSTRUCT, AND THAT ORDER IS NOT COSMETIC

The modernisation gradient sits INSIDE chadwyck -- its early texts carry `shew`
and `vertue`, its late ones do not -- so orthographic drift is collinear with
year, which is the axis every slope here lives on. If `*_cov` trends with the
bin, part of any curve below it is an orthography curve rather than a content
curve. The coverage block prints first so it cannot be skipped to the result.

## SIGN

RH's scale is z-scored with HIGH = CONCRETE. **A RISE IN ABSTRACTION IS A FALL
IN `rh_absconc_median`.** Brysbaert runs 1-5 the same way (high = concrete) but
is not on a common scale with it and the two are never differenced.
"""

import argparse, collections, os, statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
#: RESULTS GO TO $MALIGNMENT_DATA, NOT THE REPO. The chadwyck table is 128 MB
#: and chicago is ~760 MB; `results/` here is untracked but was not ignored, so
#: a single careless `git add` on the folder would have swept them in.
DATA = os.path.join(os.environ.get("MALIGNMENT_DATA",
                                   os.path.expanduser("~/malignment-data")),
                    "novel_arc")

COVERAGE = ["rh_absconc_median_cov", "brysbaert_concreteness_cov",
            "warriner_valence_cov", "k_register_level_cov", "variant_rate"]
RH_AXIS = ["rh_absconc_median", "rh_absconc_orig"]
#: the five that replicated at q<.05 on BOTH disjoint corpora in the alignment
#: contrast, plus the two scalars. Direction there, aligned minus base:
#: usas_x UP, gi_role DOWN, k_bodily_harm DOWN, usas_n5 DOWN, concreteness DOWN.
LLM_AXIS = ["usas_x", "gi_role", "k_bodily_harm", "usas_n5",
            "brysbaert_concreteness", "gi_passive", "gi_positiv", "gi_emot",
            "gi_enltot", "warriner_valence", "k_register_level"]


def per_text(d, n, cols):
    """{text_id: (year, {col: mean})} -- the passage is averaged away here."""
    acc = collections.defaultdict(lambda: collections.defaultdict(list))
    yr = {}
    #: HOIST the column lists. `d.get(c, [None] * n)[i]` inside the row loop
    #: allocates a 551,575-element list per row per missing column, which turns
    #: a seconds-long pass into a quadratic one.
    tid, year = d["text_id"], d["year"]
    series = [(c, d[c]) for c in cols if c in d]
    for i in range(n):
        t = tid[i]
        yr[t] = year[i]
        for c, col in series:
            v = col[i]
            if v is not None:
                acc[t][c].append(float(v))
    return {t: (yr[t], {c: st.mean(v) for c, v in cc.items()})
            for t, cc in acc.items()}


def show(title, txt, cols, width, min_texts, note=""):
    bins = collections.defaultdict(list)
    for t, (y, vals) in txt.items():
        bins[(int(y) // width) * width].append(vals)
    ks = sorted(bins)
    print("\n%s%s" % (title, note))
    print("  %-6s %7s   %s" % ("period", "n_texts",
                               " ".join("%-13s" % c[:13] for c in cols)))
    for k in ks:
        rows = bins[k]
        if len(rows) < min_texts:
            continue
        cells = []
        for c in cols:
            v = [r[c] for r in rows if c in r]
            cells.append("%-13s" % ("%+.4f" % st.median(v) if v else "--"))
        print("  %-6d %7d   %s" % (k, len(rows), " ".join(cells)))
    skipped = [(k, len(bins[k])) for k in ks if len(bins[k]) < min_texts]
    if skipped:
        #: SAY IT. A bin dropped for thinness is a period the series cannot
        #: speak about, and silently omitting it makes the range look wider
        #: than the evidence.
        print("  omitted (< %d texts): %s" % (
            min_texts, ", ".join("%d(n=%d)" % s for s in skipped)))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=os.path.join(DATA,
                                                  "chadwyck_n200.parquet"))
    ap.add_argument("--bin", type=int, default=25)
    ap.add_argument("--min-texts", type=int, default=5)
    a = ap.parse_args(argv)
    import pyarrow.parquet as pq
    t = pq.read_table(a.src)
    d = {c: t.column(c).to_pylist() for c in t.column_names}
    n = t.num_rows
    cols = COVERAGE + RH_AXIS + LLM_AXIS
    cols = [c for c in cols if c in d]
    txt = per_text(d, n, cols)
    print("%s passages, %d texts, %d-year bins, min %d texts/bin"
          % ("{:,}".format(n), len(txt), a.bin, a.min_texts))
    yrs = [y for y, _ in txt.values()]
    print("years %d-%d" % (min(yrs), max(yrs)))

    show("1. COVERAGE -- read this before anything below it",
         txt, [c for c in COVERAGE if c in d], a.bin, a.min_texts,
         "\n  a slope here puts an orthography curve inside every curve below.")
    show("2. RH ABSTRACTION AXIS -- high = CONCRETE, so abstraction rising is "
         "this FALLING", txt, [c for c in RH_AXIS if c in d], a.bin,
         a.min_texts)
    show("3. THE LLM AXIS -- the keys that replicated across both disjoint "
         "corpora", txt, [c for c in LLM_AXIS if c in d], a.bin, a.min_texts)


if __name__ == "__main__":
    main()
