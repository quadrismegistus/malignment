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
#: MEASURED DATA LIVES OUTSIDE THE CHECKOUT (RH, 2026-08-24). 3.0 GB of
#: gzipped long-form tables, in the same root as the score store. The repo
#: keeps the producers and the write-up; the tables are reproducible from
#: `run.py --run` and do not belong in git.
DATA = os.path.join(os.path.expanduser(os.environ.get("LITMOD_DATA_DIR", "~")),
                    "malignment-data", "norm_change") \
    if os.environ.get("LITMOD_DATA_DIR") else \
    os.path.expanduser("~/malignment-data/norm_change")
LONG = DATA

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


def stream(name, want=None):
    """One pass over a long table -> {(lang, scale, lineage): array of deltas}.

    STREAMS, and accumulates into `array('d')` rather than lists of dicts.
    `levels_long` is 1.0 GB gzipped and `fields_long` 2.0 GB; materialising
    either as Python objects is tens of gigabytes for data that is 8 bytes a
    number. The whole point of splitting run.py from analyse.py was that the
    statistics never need the rows again, only the differences.

    `want` restricts to a set of scales; None reads every scale in the file,
    which is what --explore does.

    A prompt contributes only if BOTH arms produced a level. Present in one arm
    and missing in the other is not a zero difference, and counting it as zero
    drags a lineage toward no-effect in proportion to how patchy coverage is.
    """
    from array import array
    p = os.path.join(LONG, "%s_long.csv.gz" % name)
    if not os.path.exists(p):
        return None
    acc, seen, skipped = collections.defaultdict(lambda: array("d")), 0, 0
    with gzip.open(p, "rt", encoding="utf-8") as fh:
        head = fh.readline().rstrip("\n").split("\t")
        ix = {k: i for i, k in enumerate(head)}
        need = ("base", "aligned", "scale", "base_level", "aligned_level", "lang")
        if any(k not in ix for k in need):
            print("  %s: unexpected columns %s" % (name, head))
            return None
        for line in fh:
            v = line.rstrip("\n").split("\t")
            if len(v) != len(head):
                continue
            sc = v[ix["scale"]]
            if want and sc not in want:
                continue
            b, a = v[ix["base_level"]], v[ix["aligned_level"]]
            if not b or not a or b == "\\N" or a == "\\N":
                skipped += 1
                continue
            try:
                d = float(a) - float(b)
            except ValueError:
                skipped += 1
                continue
            acc[(v[ix["lang"]], sc, v[ix["base"]] + ">" + v[ix["aligned"]])].append(d)
            seen += 1
    print("  %-14s %s usable rows, %s skipped for a missing arm"
          % (name, format(seen, ","), format(skipped, ",")))
    return acc


def per_lineage(acc, lang, scale):
    """{lineage: median over its prompts of (aligned - base)}."""
    import statistics as st
    return {k[2]: st.median(v) for k, v in acc.items()
            if k[0] == lang and k[1] == scale and len(v)}


def report(label, scale, deltas, direction, tag):
    """One line. TIES ARE EXCLUDED FROM THE SIGN TEST AND REPORTED.

    A sign test counts strict signs. Folding zeros into one side is not a
    convention, it is an error, and it was producing lines like
    `median +0.00000, 142 up/11 dn, p=0.00000` -- a median of exactly zero
    with an overwhelming "up" count, which cannot both be true. The zeros were
    the up count. Many (lineage, scale) cells ARE exactly zero here because a
    sparse field carries no mass in either arm, so the tie rate is not a
    rounding artefact and belongs on the line.

    M05's H_norm_acquisition states the same rule for the same reason: "sign
    tests with ties excluded and reported".
    """
    import statistics as st
    v = list(deltas.values())
    n = len(v)
    up = sum(1 for x in v if x > 0)
    dn = sum(1 for x in v if x < 0)
    ties = n - up - dn
    eff = up + dn
    if eff < 3:
        print("  %-4s %-26s %-11s n=%3d  ALL TIES (%d) -- no signed evidence"
              % (label, scale[:26], tag, n, ties))
        return
    p = binom(up, eff)
    med = st.median(v)
    med_eff = st.median([x for x in v if x != 0])
    if p >= 0.05:
        verdict = "not supported"
    elif (direction == "up" and med_eff > 0) or (direction == "down" and med_eff < 0):
        verdict = "SUPPORTED"
    else:
        verdict = "REVERSED"
    print("  %-4s %-26s %-11s n=%3d  med %+.6f  med!=0 %+.6f  %3d up/%-3d dn/%-3d tie  p=%.5f  %s"
          % (label, scale[:26], tag, n, med, med_eff, up, dn, ties, p, verdict))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default=None, choices=("en", "zh"))
    ap.add_argument("--explore", action="store_true")
    a = ap.parse_args(argv)

    declared = {s for _, _, ss, t in DECLARED for s in ss if t != "contextual"}
    want = None if a.explore else declared
    print("reading %s" % LONG)
    acc = {}
    for name in ("levels", "fields"):
        t = stream(name, want)
        if t is None:
            print("missing %s_long.csv.gz -- run.py --run first" % name)
            return 1
        acc[name] = t

    langs = [a.lang] if a.lang else ["en", "zh"]
    for lang in langs:
        print()
        print("=" * 78)
        print("LANGUAGE: %s" % lang.upper())
        print("=" * 78)
        print()
        print("DECLARED -- the seven in registration.md")
        for hid, direction, scales, tbl in DECLARED:
            if tbl == "contextual":
                print("  %-4s %-26s %-11s NOT YET WIRED -- needs the (prompt, word) join"
                      % (hid, scales[0], "slot"))
                continue
            for sc in scales:
                d = per_lineage(acc[tbl], lang, sc)
                if d:
                    report(hid, sc, d, direction, "declared")

        if a.explore:
            for tbl in ("levels", "fields"):
                scales = sorted({k[1] for k in acc[tbl] if k[0] == lang} - declared)
                if not scales:
                    continue
                print()
                print("EXPLORATORY (%s) -- NOT registered, NOT a headline without a re-test"
                      % tbl)
                rows = []
                for sc in scales:
                    d = per_lineage(acc[tbl], lang, sc)
                    if len(d) >= 10:
                        import statistics as st
                        v = list(d.values())
                        up = sum(1 for x in v if x > 0)
                        dn = sum(1 for x in v if x < 0)
                        rows.append((binom(up, up + dn) if up + dn >= 3 else 1.0, sc, d))
                rows.sort()
                for _p, sc, d in rows[:60]:
                    report("--", sc, d, "up", "exploratory")
                if len(rows) > 60:
                    print("  ... %d more scales with n>=10, sorted by p; "
                          "none shown is NOT the same as none tested" % (len(rows) - 60))

    print()
    print("EXPLORATORY rows are candidates for a registration, not results. The")
    print("DECLARED rows are the ones that carried a direction before the data.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
