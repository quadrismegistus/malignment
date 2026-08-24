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
#: A DECLARED SCALE'S `_z` TWIN IS THE SAME HYPOTHESIS, not a new one. H2 says
#: register rises; `k_register_level` and `k_register_level_z` are one claim on
#: one construct, standardised or not. The first version matched literal names,
#: so every twin fell through to EXPLORATORY and H2's own evidence was printed
#: as an unregistered finding (RH caught it). `_absz` is NOT a twin -- it is a
#: different quantity, extremity, which is why H5 names it explicitly and H1/H2
#: do not inherit it.
DECLARED = [
    ("H1", "down", ["brysbaert_concreteness", "k_concreteness", "concreteness_zh"], "levels"),
    ("H2", "up",   ["k_register_level", "brooke_formality"], "levels"),
    ("H3", "up",   ["X1"], "fields"),
    ("H4", "up",   ["warriner_valence", "k_valence"], "levels"),
    ("H5", "down", ["warriner_valence_absz", "k_valence_absz"], "levels"),
    ("H6", "up",   ["euphemism"], "contextual"),
    ("H7", "up",   ["mediation"], "contextual"),
]


def _with_z(scales):
    """A declared scale plus its `_z` twin. Never `_absz`: see DECLARED."""
    out = []
    for s in scales:
        out.append(s)
        if not s.endswith(("_z", "_absz")):
            out.append(s + "_z")
    return out



def endpoint_pairs():
    """The 50 base->endpoint lineages, as "base>aligned" strings.

    **THE MOVEMENT TABLE IS NOT A ROSTER.** It holds 153 edges over 85 base
    models -- RUNGS (base->SFT, SFT->DPO) and TRANSITIVE pairs as well as
    endpoints, because `produce_movement` builds both deliberately: a word can
    fall at SFT and rise at DPO, so base->DPO is not recoverable from the rungs.

    Counting those 153 as lineages is PSEUDO-REPLICATION. Llama-3.1-8B alone
    contributes 11 edges, so one pretrained model votes eleven times in a sign
    test whose unit is supposed to be the lineage. Every n=153 reported from
    this folder before 2026-08-24 has that defect (RH caught it).

    `roster.endpoints()` is the shared rule and exists precisely so this is not
    retyped per experiment -- its docstring records four shell heredocs that
    each filtered differently, one matching `"lmo" in base` and so finding 4 of
    6 OLMo lineages. It resolves 50, all present in `movement`, and applies the
    rulings: terminal under aligning ops only, no ablations, no attested
    `direction: inverted` de-aligning finetunes.
    """
    from malignment import roster
    ep, _unresolved = roster.endpoints()
    return {"%s>%s" % (b, a) for b, a in ep.items()}


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
    EP = endpoint_pairs()
    acc, seen, skipped, off = collections.defaultdict(lambda: array("d")), 0, 0, 0
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
            lin = v[ix["base"]] + ">" + v[ix["aligned"]]
            if lin not in EP:
                off += 1
                continue
            acc[(v[ix["lang"]], sc, lin)].append(d)
            seen += 1
    print("  %-14s %s usable rows, %s skipped for a missing arm, %s dropped as "
          "non-endpoint edges" % (name, format(seen, ","), format(skipped, ","),
                                  format(off, ",")))
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
        print("  %-4s %-34s %-11s n=%3d  ALL TIES (%d) -- no signed evidence"
              % (label, scale[:34], tag, n, ties))
        return
    p = binom(up, eff)
    med = st.median(v)
    med_eff = st.median([x for x in v if x != 0])
    if direction is None:
        #: EXPLORATORY ROWS HAVE NO REGISTERED DIRECTION, so they get a SIGN and
        #: never a verdict. The first version passed direction="up" as a default
        #: and every falling scale printed REVERSED -- reversed against a
        #: prediction nobody made. A verdict implies something was predicted.
        verdict = ("rises" if med_eff > 0 else "falls") if p < 0.05 else "flat"
    elif p >= 0.05:
        verdict = "not supported"
    elif (direction == "up" and med_eff > 0) or (direction == "down" and med_eff < 0):
        verdict = "SUPPORTED"
    else:
        verdict = "REVERSED"
    #: SCALE COLUMN IS 34 WIDE, not 26. At 26 `warriner_valence_extremity`,
    #: `..._z` and `..._absz` all truncate to one string and print as three
    #: rows with one name and three different numbers.
    print("  %-4s %-34s %-11s n=%3d  med %+.6f  med!=0 %+.6f  %3d up/%-3d dn/%-3d tie  p=%.5f  %s"
          % (label, scale[:34], tag, n, med, med_eff, up, dn, ties, p, verdict))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default=None, choices=("en", "zh"))
    ap.add_argument("--explore", action="store_true")
    a = ap.parse_args(argv)

    declared = {s for _, _, ss, t in DECLARED if t != "contextual" for s in _with_z(ss)}
    want = None if a.explore else declared
    print("reading %s" % LONG)
    acc = {}
    for name in ("levels", "fields", "contextual"):
        #: contextual is optional: it comes from `run.py --contextual` and the
        #: declared tests for H1-H5 do not need it.
        t = stream(name, None if name == "contextual" else want)
        if t is None:
            if name == "contextual":
                print("  contextual    absent -- run.py --contextual for H6/H7")
                acc[name] = {}
                continue
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
                #: the contextual table keys scales as `<instrument>:<scale>`,
                #: because two instruments rating one scale NAME are not one
                #: construct -- the same rule contextual_norms() follows.
                hits = sorted({k[1] for k in acc["contextual"]
                               if k[0] == lang and k[1].split(":")[-1] in scales})
                if not hits:
                    print("  %-4s %-34s %-11s no rated (prompt, word) overlap in %s"
                          % (hid, scales[0], "slot", lang))
                for sc in hits:
                    d = per_lineage(acc["contextual"], lang, sc)
                    if d:
                        report(hid, sc, d, direction, "declared")
                continue
            for sc in _with_z(scales):
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
                    report("--", sc, d, None, "exploratory")
                if len(rows) > 60:
                    print("  ... %d more scales with n>=10, sorted by p; "
                          "none shown is NOT the same as none tested" % (len(rows) - 60))

    print()
    print("EXPLORATORY rows are candidates for a registration, not results. The")
    print("DECLARED rows are the ones that carried a direction before the data.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
