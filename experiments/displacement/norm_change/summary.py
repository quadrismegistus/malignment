"""MARGINAL vs DOSE, one table, one pass over the data.

    python -u summary.py                 # both languages, both tables
    python -u summary.py --lang en --table levels

Two questions about every scale, side by side, on the same 50 endpoint lineages:

    MARGINAL   does this move under alignment, on average across prompts?
               per lineage, median over prompts of (aligned - base)
    DOSE       does it move MORE where the base arm was more transgressive?
               per lineage, OLS slope of (aligned - base) on base transgressive
               level, across prompts

**They answer different questions and can disagree in every combination**, which
is the reason for printing them together rather than in two reports a reader has
to align by hand. A scale flat marginally and steep under dose is one that only
moves where the frame is loaded; a scale that moves marginally with a flat slope
moves everywhere alike.

Both use the lineage as the unit and a two-sided sign test with TIES EXCLUDED.
Both restrict to `roster.endpoints()` -- 50 pairs, not the 153 edges in
`movement`, which include rungs and transitive pairs and would let one base
model vote up to eleven times.
"""

import argparse, collections, gzip, math, os, sys

#: **THE VARIANT AND THE POPULATION, SAME AS run.py AND dose.py.** run.py writes
#: three sets side by side; without the suffix this reads v3 while the caller
#: believes it asked for framed. And the framed set covers 45 of the 50 pairs,
#: so an unmatched comparison differs partly by which labs ship a template.
_SFX = {"v": ""}
_MATCH = {"v": False}


def _suffix(rule_version, frame):
    if int(rule_version) == 3:
        if frame != "raw":
            raise SystemExit("--frame needs --rule-version 4")
        return ""
    return "_v4" if frame == "raw" else "_v4_framed"

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
sys.path.insert(0, HERE)
DATA = os.path.expanduser("~/malignment-data/norm_change")

MIN_PROMPTS = 25
DOSE = "k_transgressiveness"


def binom(k, n):
    if not n:
        return float("nan")
    return min(1.0, 2 * sum(math.comb(n, j) for j in range(0, min(k, n - k) + 1)) / 2.0 ** n)


def signtest(vals):
    """-> (n, up, dn, ties, median_nonzero, p) or None if too few signed."""
    import statistics as st
    up = sum(1 for x in vals if x > 0)
    dn = sum(1 for x in vals if x < 0)
    ties = len(vals) - up - dn
    if up + dn < 3:
        return None
    nz = [x for x in vals if x != 0]
    return (len(vals), up, dn, ties, st.median(nz), binom(up, up + dn))


def load(name, endpoints, dose_scale=DOSE):
    """-> {(lang, scale): {lineage: [deltas]}}, {(lang,): {(lin,prompt): dose}}"""
    p = os.path.join(DATA, "%s_long%s.csv.gz" % (name, _SFX["v"]))
    if not os.path.exists(p):
        return None, None
    deltas = collections.defaultdict(lambda: collections.defaultdict(list))
    pairs = collections.defaultdict(lambda: collections.defaultdict(list))
    with gzip.open(p, "rt", encoding="utf-8") as fh:
        head = fh.readline().rstrip("\n").split("\t")
        ix = {k: i for i, k in enumerate(head)}
        for line in fh:
            v = line.rstrip("\n").split("\t")
            if len(v) != len(head):
                continue
            lin = v[ix["base"]] + ">" + v[ix["aligned"]]
            if lin not in endpoints:
                continue
            b, a = v[ix["base_level"]], v[ix["aligned_level"]]
            if not b or not a or b == "\\N" or a == "\\N":
                continue
            try:
                bf, af = float(b), float(a)
            except ValueError:
                continue
            lg, sc, pr = v[ix["lang"]], v[ix["scale"]], v[ix["prompt"]]
            deltas[(lg, sc)][lin].append(af - bf)
            pairs[(lg, sc)][lin].append((pr, bf, af))
    return deltas, pairs


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--rule-version", type=int, default=3, choices=(3, 4),
                    help="which *_long* set run.py wrote; 3 is the v3 artifact")
    ap.add_argument("--frame", default="raw", choices=("raw", "prefill"),
                    help="prefill requires --rule-version 4")
    ap.add_argument("--match-framed", action="store_true",
                    help="restrict to the pairs the framed set covers, so the "
                         "two columns are the same population")
    ap.add_argument("--lang", default=None, choices=("en", "zh"))
    ap.add_argument("--table", default="both",
                    choices=("levels", "fields", "contextual", "both", "all"))
    ap.add_argument("--min-n", type=int, default=10)
    a = ap.parse_args(argv)
    _SFX["v"] = _suffix(a.rule_version, a.frame)
    if _SFX["v"]:
        print("reading *_long%s.csv.gz" % _SFX["v"])

    from analyse import endpoint_pairs
    import statistics as st
    EP = endpoint_pairs()
    if a.match_framed or a.frame != "raw":
        #: **THE SAME 45 IN BOTH COLUMNS.** The framed set covers 45 of the 50
        #: pairs, so n=50 beside n=45 differs partly by which labs ship a chat
        #: template. Applied automatically for --frame prefill, since the framed
        #: file cannot contain the other five anyway, and on request for raw.
        from malignment import movement as M, roster
        ep, _u = roster.endpoints()
        keep = {"%s>%s" % (b, al) for b, al, _m in M.clean_frame_pairs()
                if ep.get(b) == al}
        EP = {e for e in EP if e in keep}
    print("MARGINAL vs DOSE, unit = lineage, %d endpoint pairs, ties excluded" % len(EP))
    print("dose predictor: base-arm %s, measured BEFORE alignment" % DOSE)

    lv_d, lv_p = load("levels", EP)
    if lv_d is None:
        print("no levels_long")
        return 1
    #: the dose always comes from levels; fields have no transgressiveness twin
    dose_by = {}
    for (lg, sc), bylin in lv_p.items():
        if sc != DOSE:
            continue
        for lin, rows in bylin.items():
            for pr, bf, _af in rows:
                dose_by[(lg, lin, pr)] = bf

    tables = (["levels", "fields"] if a.table == "both"
              else ["levels", "fields", "contextual"] if a.table == "all"
              else [a.table])
    for name in tables:
        #: the contextual table exists only where slot_ratings and the
        #: movement roster overlap -- 279 prompts before the endpoint filter --
        #: so its lineage counts are smaller and its scales are keyed
        #: `<instrument>:<scale>`, two instruments rating one scale name being
        #: two constructs rather than one.
        d, pr_ = (lv_d, lv_p) if name == "levels" else load(name, EP)
        if d is None:
            continue
        langs = [a.lang] if a.lang else ["en", "zh"]
        for lang in langs:
            rows = []
            for (lg, sc), bylin in d.items():
                if lg != lang or sc == DOSE:
                    continue
                marg = signtest([st.median(v) for v in bylin.values() if v])
                slopes = {}
                for lin, obs in pr_[(lg, sc)].items():
                    xs, ys = [], []
                    for p_, bf, af in obs:
                        dv = dose_by.get((lg, lin, p_))
                        if dv is None:
                            continue
                        xs.append(dv)
                        ys.append(af - bf)
                    if len(xs) < MIN_PROMPTS:
                        continue
                    mx = sum(xs) / len(xs)
                    sxx = sum((x - mx) ** 2 for x in xs)
                    if sxx <= 0:
                        continue
                    my = sum(ys) / len(ys)
                    slopes[lin] = sum((x - mx) * (y - my)
                                      for x, y in zip(xs, ys)) / sxx
                dose = signtest(list(slopes.values())) if slopes else None
                if marg and marg[0] >= a.min_n:
                    rows.append((sc, marg, dose))
            if not rows:
                continue
            rows.sort(key=lambda r: min(r[1][5], r[2][5] if r[2] else 1.0))
            print()
            print("=" * 100)
            print("%s / %s  --  %d scales" % (lang.upper(), name, len(rows)))
            print("=" * 100)
            print("  %-30s %22s   %22s   %s"
                  % ("scale", "MARGINAL med / p", "DOSE slope / p", "verdict"))
            for sc, m, dz in rows:
                ms = "%+9.5f %8.5f%s" % (m[4], m[5], "*" if m[5] < 0.05 else " ")
                ds = ("%+9.5f %8.5f%s" % (dz[4], dz[5], "*" if dz[5] < 0.05 else " ")
                      if dz else "        --        ")
                msig = m[5] < 0.05
                dsig = bool(dz) and dz[5] < 0.05
                if msig and dsig:
                    v = "both"
                elif dsig:
                    v = "DOSE ONLY -- moves only where the frame is loaded"
                elif msig:
                    v = "marginal only -- moves everywhere alike"
                else:
                    v = ""
                print("  %-30s %22s   %22s   %s" % (sc[:30], ms, ds, v))
    print()
    print("* = p < 0.05. MARGINAL med is the median over lineages of the")
    print("per-lineage median delta, ties excluded. DOSE slope is the median")
    print("per-lineage OLS slope. Everything not in registration.md's seven is")
    print("EXPLORATORY and is a candidate for a hypothesis, not a result.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
