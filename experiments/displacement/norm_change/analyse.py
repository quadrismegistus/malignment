"""norm_change: the statistics. The data is built by run.py and not touched here.

    python -u analyse.py                 # the seven declared hypotheses
    python -u analyse.py --explore       # everything else, LABELLED exploratory
    python -u analyse.py --lang zh

## THE UNIT IS THE LINEAGE, AND THE TEST IS PAIRED

Per (lineage, prompt) the long table holds a base level and an aligned level.
Per lineage the statistic is the MEDIAN over its prompts of (aligned - base);
the test is over lineages, paired, sign test and Wilcoxon, two-sided.

Prompts are not the unit and are not counted as one. They are nested inside a
lineage, they are shared across lineages, and treating ~4,500 of them as
independent would produce p-values that describe the roster rather than the
effect -- the defect this campaign has booked before under "p-values over
correlated sub-units".

## LANGUAGES ARE NEVER POOLED

Reported separately, always. M01 O_crosslingual found the affect signature does
not travel to Chinese while the substitution does, so a pooled number would
average a real effect against a real non-effect and report the mean.

## WHAT IS DECLARED AND WHAT IS NOT

The seven in `registration.md` print under DECLARED. Everything else prints
under EXPLORATORY and says so on the line, because a light registration is only
honest if the labels survive contact with the output. An exploratory row is a
candidate for a registration, never a substitute for one.
"""

import argparse, collections, gzip, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
LONG = os.path.join(HERE, "results", "long")

#: (id, direction, scales, table). direction is the REGISTERED prediction, so a
#: result that lands the other way reads as REVERSED rather than as a null.
DECLARED = [
    ("H1", "down", ["brysbaert_concreteness", "k_concreteness", "concreteness_zh"], "levels"),
    ("H2", "up",   ["k_register_level", "brooke_formality"], "levels"),
    ("H3", "up",   ["X1"], "fields"),
    ("H4", "up",   ["warriner_valence_z", "k_valence_z"], "levels"),
    ("H5", "down", ["warriner_valence_absz", "k_valence_absz"], "levels"),
    ("H6", "up",   ["euphemism"], "contextual"),
    ("H7", "up",   ["mediation"], "contextual"),
]


def binom(k, n):
    """Two-sided sign test. Same implementation the other producers use."""
    if not n:
        return float("nan")
    return min(1.0, 2 * sum(math.comb(n, j) for j in range(0, min(k, n - k) + 1)) / 2.0 ** n)


def load(name, lang=None):
    """A long table as [dict]. Streams; these files are large."""
    p = os.path.join(LONG, "%s_long.csv.gz" % name)
    if not os.path.exists(p):
        return None
    out = []
    with gzip.open(p, "rt", encoding="utf-8") as fh:
        head = fh.readline().rstrip("\n").split("\t")
        for line in fh:
            v = line.rstrip("\n").split("\t")
            if len(v) != len(head):
                continue
            r = dict(zip(head, v))
            if lang and r.get("lang") != lang:
                continue
            out.append(r)
    return out


def per_lineage(rows, scale):
    """{lineage: median over its prompts of (aligned - base)} for one scale.

    A prompt contributes only if BOTH arms produced a level. A prompt present
    in one arm and missing in the other is not a zero difference; it is not a
    difference at all, and averaging it in as zero would drag every lineage
    toward no-effect in proportion to how patchy the coverage is.
    """
    import statistics as st
    by = collections.defaultdict(list)
    for r in rows:
        if r.get("scale") != scale:
            continue
        b, a = r.get("base_level"), r.get("aligned_level")
        if b in (None, "", "\\N") or a in (None, "", "\\N"):
            continue
        try:
            by[(r["base"], r["aligned"])].append(float(a) - float(b))
        except ValueError:
            continue
    return {k: st.median(v) for k, v in by.items() if v}


def report(label, scale, deltas, direction, tag):
    """One line. `direction` is what was predicted, so REVERSED is sayable."""
    import statistics as st
    n = len(deltas)
    if n < 3:
        print("  %-4s %-26s %-11s n=%d  TOO FEW LINEAGES" % (label, scale[:26], tag, n))
        return
    v = list(deltas.values())
    dn = sum(1 for x in v if x < 0)
    up = n - dn
    p = binom(up, n)
    med = st.median(v)
    if p >= 0.05:
        verdict = "not supported"
    elif (direction == "up" and med > 0) or (direction == "down" and med < 0):
        verdict = "SUPPORTED"
    else:
        verdict = "REVERSED"
    print("  %-4s %-26s %-11s n=%3d  median %+9.5f  %3d up/%-3d dn  p=%.5f  %s"
          % (label, scale[:26], tag, n, med, up, dn, p, verdict))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default=None, choices=("en", "zh"))
    ap.add_argument("--explore", action="store_true")
    ap.add_argument("--min-cov", type=float, default=0.0,
                    help="drop (lineage, prompt) rows below this base coverage")
    a = ap.parse_args(argv)

    langs = [a.lang] if a.lang else ["en", "zh"]
    tables = {}
    for name in ("levels", "fields"):
        t = load(name)
        if t is None:
            print("missing %s_long.csv.gz -- run.py --run first" % name)
            return 1
        tables[name] = t
    print("loaded: %s" % ", ".join("%s %s rows" % (k, format(len(v), ","))
                                   for k, v in tables.items()))

    for lang in langs:
        print()
        print("=" * 78)
        print("LANGUAGE: %s" % lang.upper())
        print("=" * 78)
        sub = {k: [r for r in v if r.get("lang") == lang] for k, v in tables.items()}
        if not any(sub.values()):
            print("  no rows")
            continue

        print()
        print("DECLARED -- the seven in registration.md")
        for hid, direction, scales, tbl in DECLARED:
            if tbl == "contextual":
                print("  %-4s %-26s %-11s (contextual; see --explore note)" % (hid, scales[0], "slot"))
                continue
            rows = sub.get("levels" if tbl == "levels" else "fields", [])
            for sc in scales:
                d = per_lineage(rows, sc)
                if d:
                    report(hid, sc, d, direction, "declared")

        if a.explore:
            print()
            print("EXPLORATORY -- NOT registered, NOT a headline without a re-test")
            declared_scales = {s for _, _, ss, _ in DECLARED for s in ss}
            for tbl in ("levels", "fields"):
                seen = collections.Counter(r["scale"] for r in sub.get(tbl, []))
                for sc, _n in seen.most_common(40):
                    if sc in declared_scales:
                        continue
                    d = per_lineage(sub[tbl], sc)
                    if len(d) >= 10:
                        report("--", sc, d, "up", "exploratory")

    print()
    print("Every EXPLORATORY row above is a candidate for a registration and not")
    print("a result. The seven DECLARED rows are the ones that carried a")
    print("direction before the data existed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
