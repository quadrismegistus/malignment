"""What separates base from aligned, across every norm and field at once.

    python .../contrast.py --corpus quadrants
    python .../contrast.py --corpus ch --top 40
    python .../contrast.py --corpus quadrants --arms aligned,API

The wide net's other half. `measure.py` scores every passage on ~500 keys and
decides nothing; this pairs the arms and ranks the keys by how far apart they
sit.

## THE UNIT IS THE LINEAGE AND THE TEST IS A SIGN TEST

Per key: a median per model, then a difference within each lineage pair, then a
sign test over pairs. Passages within a model are not independent and models
within a lineage share a base, so a passage-level t-test over a million rows
would return a p-value about sample size rather than about alignment.

## ~500 KEYS MEANS ~500 TESTS AND THAT IS THE WHOLE PROBLEM

At 500 keys and alpha 0.05, twenty-five keys reach significance with nothing
happening. This is an EXPLORATORY sweep, so the response is not to pretend
otherwise:

  * A Benjamini-Hochberg FDR q-value rides beside every raw p. Ranking is by
    effect size, not by p, so a tiny consistent difference on a huge n cannot
    lead the table.
  * The REGISTERED hypotheses are printed separately, first, and are not
    subject to the correction -- they were named in advance, which is the only
    thing that distinguishes them from the other 495.
  * Everything else is labelled EXPLORATORY in the output itself. A key that
    surfaces here is a candidate for a registered test on the other corpus,
    not a finding.

## TWO CORPORA IS THE REAL CORRECTION

A key that separates the arms in the 14,414-passage narrative corpus AND in the
1.5M-passage unfiltered one, at the same sign, is worth more than any q-value:
the two differ in filtering, in model roster, in prompt design and in n. The
`--corpus` flag runs one; the table is meant to be read against its twin.

## COVERAGE KEYS ARE REPORTED, NEVER RANKED

`*_coverage` differences are real and expected -- proper nouns are absent from
the norms and NNP runs lower in the aligned arm -- so they are shown in their
own block. A coverage difference is a fact about the text; ranking it beside a
valence difference invites reading it as one.
"""

import argparse, glob, collections, math, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))

#: named in advance, in the folder README, before any of this ran
REGISTERED = {
    "brysbaert_concreteness": "H1 alignment reduces concreteness (down)",
    "warriner_valence": "H2 alignment raises valence slightly (up)",
    "warriner_valence_sd": "H3 alignment reduces valence range (down)",
    "warriner_valence_extremity": "H3' extremity, the plan's C.H1 (down)",
    #: H4 carries TWO instruments and they are shown side by side rather
    #: than one being demoted to the exploratory block. `k_register_level`
    #: covers 93.5% of content words to Brooke's 11.9%, and its IAA-0.597
    #: rider bars quoting an absolute LEVEL, not a paired rank contrast --
    #: it is corroborated externally against the displacement lexicon at
    #: Spearman rho 0.645 (n=480, p=1e-57), AUC 0.976 vulgar-vs-clinical.
    "k_register_level": "H4 alignment raises register (up, PRIMARY 93.5% cov)",
    "brooke_formality": "H4 the same, second instrument (up, 11.9% cov)",
    "rid_conceptual_secondary": "H5 secondary process (up)",
    "rid_primordial_primary": "H5 primary process (down)",
}


def sign_test(d):
    v = [x for x in d if x != 0]
    n, up = len(v), sum(1 for x in v if x > 0)
    if not n:
        return 0, 0, float("nan"), float("nan")
    k = max(up, n - up)
    return n, up, statistics.median(v), min(
        1.0, 2 * sum(math.comb(n, i) for i in range(k, n + 1)) / 2 ** n)


def bh(pairs):
    """Benjamini-Hochberg. [(key, p)] -> {key: q}"""
    ok = sorted([(k, p) for k, p in pairs if p == p], key=lambda x: x[1])
    m, out, prev = len(ok), {}, 1.0
    for i in range(m - 1, -1, -1):
        k, p = ok[i]
        prev = min(prev, p * m / (i + 1))
        out[k] = round(min(1.0, prev), 5)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", choices=("quadrants", "ch"), default="quadrants")
    ap.add_argument("--top", type=int, default=25)
    ap.add_argument("--min-passages", type=int, default=15)
    ap.add_argument("--min-lineages", type=int, default=8)
    a = ap.parse_args(argv)
    import pyarrow.parquet as pq
    from malignment import roster

    def medians(tbl, per):
        """Accumulate per-model lists from one table. Mutates `per`."""
        d = {c: tbl.column(c).to_pylist() for c in tbl.column_names}
        ks = [c for c in d if c not in SKIP]
        for i in range(tbl.num_rows):
            m = d["model"][i]
            if not m:
                continue
            for k in ks:
                v = d[k][i]
                if v is not None:
                    per[m][k].append(float(v))
        return set(ks)

    SKIP = ("id", "corpus", "model", "arm", "prompt", "error")
    fp = os.path.join(HERE, "results", "norms_%s.parquet" % a.corpus)
    dp = os.path.join(HERE, "results", "norms_%s" % a.corpus)
    per = collections.defaultdict(lambda: collections.defaultdict(list))
    keyset, n = set(), 0
    #: a SHARDED corpus is one parquet per model, reduced one shard at a time.
    #: The contrast needs only per-model medians, so the 1.5M-row corpus never
    #: has to be resident -- and the shards carry DIFFERENT column sets, since
    #: each writes the union of keys its own passages produced, which is why
    #: this unions the schemas rather than handing pyarrow the directory.
    if os.path.isdir(dp):
        shards = sorted(glob.glob(os.path.join(dp, "*.parquet")))
        if not shards:
            print("no shards under %s" % dp); return
        for sh in shards:
            t = pq.read_table(sh)
            n += t.num_rows
            keyset |= medians(t, per)
        print("%s: %s passages, %d columns, %d shards"
              % (a.corpus, "{:,}".format(n), len(keyset), len(shards)))
    else:
        t = pq.read_table(fp)
        n = t.num_rows
        keyset = medians(t, per)
        print("%s: %s passages, %d columns"
              % (a.corpus, "{:,}".format(n), len(keyset)))
    keys = sorted(keyset)
    med = {m: {k: statistics.median(v) for k, v in kk.items()
               if len(v) >= a.min_passages} for m, kk in per.items()}

    lin = roster.lineages()
    pairs = []
    for base, members in sorted(lin.items()):
        for al in [x for x in members if x != base]:
            if base in med and al in med:
                pairs.append((med[base], med[al]))
    print("lineage pairs with both arms: %d\n" % len(pairs))
    if len(pairs) < a.min_lineages:
        print("too few pairs to test"); return

    res = {}
    for k in keys:
        diffs = [A[k] - b[k] for b, A in pairs if k in b and k in A]
        if len(diffs) < a.min_lineages:
            continue
        nn, up, m, p = sign_test(diffs)
        res[k] = (m, nn, up, p)
    q = bh([(k, v[3]) for k, v in res.items()])

    def show(title, ks, note=""):
        if not ks:
            return
        print("%s%s" % (title, note))
        print("  %-38s %10s %6s %6s %10s %9s" % ("", "median", "n", "up", "p", "q"))
        for k in ks:
            m, nn, up, p = res[k]
            print("  %-38s %+10.4f %6d %6d %10.3g %9s"
                  % (k, m, nn, up, p, "%.4f" % q.get(k, float("nan"))))
        print()

    reg = [k for k in REGISTERED if k in res]
    print("REGISTERED HYPOTHESES -- named before the run, NOT FDR-corrected")
    for k in reg:
        m, nn, up, p = res[k]
        print("  %-38s %+10.4f  %2d/%2d up  p=%-9.3g  %s"
              % (k, m, up, nn, p, REGISTERED[k]))
    print()

    cov = sorted([k for k in res if k.endswith("_coverage")],
                 key=lambda k: -abs(res[k][0]))
    show("COVERAGE -- reported, never ranked as an effect", cov)

    rest = [k for k in res if k not in REGISTERED and not k.endswith("_coverage")
            and not k.startswith("n_")]
    rest.sort(key=lambda k: -abs(res[k][0]))
    show("EXPLORATORY, ranked by EFFECT SIZE -- top %d of %d" % (a.top, len(rest)),
         rest[:a.top],
         "\n  ~%d tests: at alpha .05 about %d reach p<.05 with nothing happening."
         % (len(res), int(0.05 * len(res))))
    print("A key here is a CANDIDATE for a registered test on the other corpus,")
    print("not a finding. The correction that matters is the twin corpus: same")
    print("key, same sign, different filtering, roster, prompts and n.")


if __name__ == "__main__":
    main()
