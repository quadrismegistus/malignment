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
    ap.add_argument("--twin", action="store_true",
                    help="run BOTH corpora and report what replicates")
    a = ap.parse_args(argv)
    import pyarrow.parquet as pq
    from malignment import roster

    if a.twin:
        both = {}
        for c in ("quadrants", "ch"):
            r = analyse(c, a, pq, roster)
            if r is None:
                print("%s: unavailable, cannot twin" % c); return
            both[c] = r
        twin_report(both, a)
        return
    r = analyse(a.corpus, a, pq, roster)
    if r is None:
        return
    report(r, a)


def analyse(corpus, a, pq, roster):
    """One corpus -> dict(res, q, n, pairs, corpus), or None if untestable."""
    SKIP = ("id", "corpus", "model", "arm", "prompt", "error")

    def medians(tbl, per):
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

    fp = os.path.join(HERE, "results", "norms_%s.parquet" % corpus)
    dp = os.path.join(HERE, "results", "norms_%s" % corpus)
    per = collections.defaultdict(lambda: collections.defaultdict(list))
    keyset, n, nsh = set(), 0, 0
    #: a SHARDED corpus is one parquet per model, reduced one shard at a time.
    #: The contrast needs only per-model medians, so the 1.5M-row corpus never
    #: has to be resident -- and the shards carry DIFFERENT column sets, since
    #: each writes the union of keys its own passages produced, which is why
    #: this unions the schemas rather than handing pyarrow the directory.
    if os.path.isdir(dp):
        shards = sorted(glob.glob(os.path.join(dp, "*.parquet")))
        if not shards:
            print("no shards under %s" % dp); return None
        nsh = len(shards)
        for sh in shards:
            t = pq.read_table(sh)
            n += t.num_rows
            keyset |= medians(t, per)
    elif os.path.exists(fp):
        t = pq.read_table(fp)
        n = t.num_rows
        keyset = medians(t, per)
    else:
        return None
    med = {m: {k: statistics.median(v) for k, v in kk.items()
               if len(v) >= a.min_passages} for m, kk in per.items()}
    lin = roster.lineages()
    pairs = []
    for base, members in sorted(lin.items()):
        for al in [x for x in members if x != base]:
            if base in med and al in med:
                pairs.append((med[base], med[al]))
    if len(pairs) < a.min_lineages:
        print("%s: too few lineage pairs (%d)" % (corpus, len(pairs)))
        return None
    res = {}
    for k in sorted(keyset):
        diffs = [A[k] - b[k] for b, A in pairs if k in b and k in A]
        if len(diffs) < a.min_lineages:
            continue
        nn, up, m, pv = sign_test(diffs)
        res[k] = (m, nn, up, pv)
    return dict(res=res, q=bh([(k, v[3]) for k, v in res.items()]),
                n=n, pairs=len(pairs), shards=nsh, corpus=corpus,
                cols=len(keyset))


def report(r, a):
    res, q = r["res"], r["q"]
    print("%s: %s passages, %d columns%s"
          % (r["corpus"], "{:,}".format(r["n"]), r["cols"],
             "" if not r["shards"] else ", %d shards" % r["shards"]))
    print("lineage pairs with both arms: %d\n" % r["pairs"])

    def show(title, ks, note=""):
        if not ks:
            return
        print("%s%s" % (title, note))
        print("  %-38s %10s %6s %6s %10s %9s" % ("", "median", "n", "up", "p", "q"))
        for k in ks:
            m, nn, up, pv = res[k]
            print("  %-38s %+10.4f %6d %6d %10.3g %9s"
                  % (k, m, nn, up, pv, "%.4f" % q.get(k, float("nan"))))
        print()

    print("REGISTERED HYPOTHESES -- named before the run, NOT FDR-corrected")
    for k in [x for x in REGISTERED if x in res]:
        m, nn, up, pv = res[k]
        print("  %-38s %+10.4f  %2d/%2d up  p=%-9.3g  %s"
              % (k, m, up, nn, pv, REGISTERED[k]))
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


def twin_report(both, a):
    """The comparison the exploratory table exists to be disciplined by.

    ## WHY THE TWIN IS THE CORRECTION AND BH IS NOT

    BH controls the false-discovery rate WITHIN one family of tests on one
    corpus. It cannot see a key that separates the arms for a reason specific
    to that corpus -- a prompt set, a filter, a roster imbalance -- because
    that key's effect is real in the data and simply is not about alignment.
    The twin can: corpus A is 14,414 narrative-filtered passages including the
    API models, corpus B is the full `gen_sequences` store on a different
    roster with different prompts and no narrative filter. A key surviving on
    BOTH, with the SAME SIGN, has survived a change to nearly everything except
    the arm contrast.

    ## THE FOUR OUTCOMES, AND WHICH ONE IS INFORMATIVE

    REPLICATED is the only one that promotes a key. `A only` and `B only` are
    NOT half-evidence: an effect that appears on one corpus and not the other
    is the corpus-specific case the twin exists to catch, and the honest
    reading is that the key is not established. CONTRADICTED -- significant
    both times, opposite signs -- is the loudest outcome and is reported first
    however few there are, because a key that reverses is evidence the measure
    is picking up something other than the arm.
    """
    A, B = both["quadrants"], both["ch"]
    print("TWIN CORPUS COMPARISON")
    print("  A quadrants  %9s passages  %2d lineage pairs  (narrative filter, +API)"
          % ("{:,}".format(A["n"]), A["pairs"]))
    print("  B ch         %9s passages  %2d lineage pairs  (%d shards, no filter)"
          % ("{:,}".format(B["n"]), B["pairs"], B["shards"]))
    shared = [k for k in A["res"] if k in B["res"]]
    print("  %d keys tested on both\n" % len(shared))

    rows = []
    for k in shared:
        ma, _, _, _ = A["res"][k]
        mb, _, _, _ = B["res"][k]
        qa, qb = A["q"].get(k, 1.0), B["q"].get(k, 1.0)
        sa, sb = qa < 0.05, qb < 0.05
        same = (ma > 0) == (mb > 0)
        #: SIGN AGREEMENT, not dual significance, is the axis. Corpus A has
        #: ~22 lineage pairs to B's ~43, so a real effect can miss q<.05 on A
        #: purely on power -- `brysbaert_concreteness` is A -0.0591 (qA .067)
        #: against B -0.0663 (qB .00004), the same effect, and filing that as
        #: "A-specific" would be a deflation as wrong as the overclaim it was
        #: guarding against. What a corpus-specific key looks like is a sign
        #: that FLIPS, or an effect that collapses toward zero.
        cat = ("CONTRADICTED" if sa and sb and not same else
               "REPLICATED" if sa and sb else
               "SIGN FLIP" if (sa or sb) and not same else
               "CONSISTENT" if (sa or sb) else "neither")
        rows.append((cat, k, ma, mb, qa, qb))

    def block(cat, note):
        sel = [r for r in rows if r[0] == cat]
        #: ranked by the WEAKER of the two effects, so a key promoted here
        #: cannot be carried by one corpus alone.
        sel.sort(key=lambda r: -min(abs(r[2]), abs(r[3])))
        print("%s  (%d)%s" % (cat, len(sel), note))
        if not sel:
            print("  none\n"); return
        print("  %-34s %10s %10s %9s %9s" % ("", "A", "B", "qA", "qB"))
        for _, k, ma, mb, qa, qb in sel[:a.top]:
            print("  %-34s %+10.4f %+10.4f %9.4f %9.4f" % (k, ma, mb, qa, qb))
        if len(sel) > a.top:
            print("  ... %d more not shown" % (len(sel) - a.top))
        print()

    #: the headline number: among keys significant ANYWHERE, how often do the
    #: two corpora agree on direction? Chance is 50%.
    live = [r for r in rows if r[0] in ("REPLICATED", "CONTRADICTED",
                                        "CONSISTENT", "SIGN FLIP")]
    agree = sum(1 for r in live if r[0] in ("REPLICATED", "CONSISTENT"))
    if live:
        print("SIGN AGREEMENT among the %d keys significant on either corpus: "
              "%d (%.0f%%), chance 50%%\n" % (len(live), agree,
                                              100.0 * agree / len(live)))
    block("CONTRADICTED", "  significant BOTH, opposite signs -- read these first")
    block("SIGN FLIP", "  significant on one, opposite sign on the other")
    block("REPLICATED", "  significant on both at q<.05, same sign")
    block("CONSISTENT", "  significant on one, SAME sign on the other -- power, "
                        "not corpus-specificity")

    print("REGISTERED HYPOTHESES, both corpora")
    print("  %-34s %10s %10s %9s %9s" % ("", "A", "B", "pA", "pB"))
    for k in [x for x in REGISTERED if x in A["res"] or x in B["res"]]:
        ra, rb = A["res"].get(k), B["res"].get(k)
        f = lambda r, i: ("%+10.4f" % r[i]) if r else "%10s" % "--"   # noqa: E731
        g = lambda r: ("%9.3g" % r[3]) if r else "%9s" % "--"         # noqa: E731
        print("  %-34s %s %s %s %s   %s"
              % (k, f(ra, 0), f(rb, 0), g(ra), g(rb), REGISTERED[k]))


if __name__ == "__main__":
    main()
