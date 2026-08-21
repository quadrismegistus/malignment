"""The blind codes against the two measured axes: does the reader agree with bge?

    python .../coded_axes.py

Three questions on the same join, all using `../interiority_in_passages`'s blind
Opus coding (rubric `plans/passC_rubric.md`) against this folder's deepseek
surprisal and bge drift.

    1  drift_A  HOLDS vs SHIFTS   -- VALIDATION. Does a human-grade reader's
                                     judgment of topical drift track the
                                     embedding's? Replicates `../drift_geometry`
                                     on a different population and splitter.
    2  drift_A  against SURPRISAL -- new. The coder judged TRAJECTORY; nobody has
                                     asked whether that judgment also tracks
                                     PREDICTABILITY.
    3  mode_A   TOLD vs SHOWN     -- new on these axes. The base/aligned contrast
                                     on mode was not significant; where it sits
                                     on drift and surprisal was never asked.

## THE VALIDATION IS THE POINT OF (1) AND IT IS NOT CIRCULAR

`mean_drift` is a cosine statistic over sentence embeddings. `drift_A` is a
reader who never saw it, coding at kappa 0.904. They share no machinery, so
agreement is evidence the axis measures what its name says -- the only kind of
evidence a metric-vs-metric comparison cannot give.

`../drift_geometry` ran this on ITS population (13,565 coded, stanza vectors) and
got `mean_drift` +0.0208, 24 of 27 pairs. Here the population is narrative-only
(4,931), the vectors are the nltk-en stash, and the unit is the lineage. Same
construct, different everything else.

## MODE IS CONFOUNDED WITH DEGREE AND IS THEREFORE STRATIFIED BY IT

TOLD holds 1,181 passages at degree 1 against SHOWN's 119; SHOWN skews to
degree 3 (622 against 365). Since degree independently predicts drift
(`interiority_axis.py`: -0.2207, 29/29 lineages), an uncontrolled TOLD-vs-SHOWN
difference would substantially re-measure degree and report it as mode.

So the mode contrast is computed WITHIN (model, degree) and averaged across the
degree levels that carry both modes. `NONE` is dropped: it is not a third mode
but an alias for degree 0 -- all 146 NONE passages are degree 0 and all degree 0
passages are NONE, which the rubric mandates ("mode is NONE and degree is 0").

## UNMOORED IS DROPPED AND COUNTED

16 passages of 4,931. A third class at n=16 cannot carry a per-model contrast,
and folding it into SHIFTS would change the construct being validated without
saying so. Contrast 1 is HOLDS vs SHIFTS.

## THE UNIT, AS EVERYWHERE ELSE HERE

Difference computed WITHIN a model, so no model-level or arm-level difference can
enter it -- and the codes are arm-skewed (base SHIFTS 10.3% of its passages,
aligned 5.1%), so this matters. Then children average into their lineage and the
sign test runs over lineages.
"""

import argparse, collections, csv, json, math, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data"))
SRC = os.path.join(HERE, "results", "quadrants.csv")
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))

AXES = [("surprisal", "surprisal"), ("drift", "drift"), ("n_sents", "n_sents")]


def sign_test(d):
    v = [x for x in d if x != 0]
    n, up = len(v), sum(1 for x in v if x > 0)
    if not n:
        return 0, 0, 0, float("nan"), float("nan")
    k = max(up, n - up)
    p = min(1.0, 2 * sum(math.comb(n, i) for i in range(k, n + 1)) / 2 ** n)
    return n, up, n - up, statistics.median(v), p


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=SRC)
    ap.add_argument("--min-per-cell", type=int, default=5)
    a = ap.parse_args(argv)
    from malignment import roster

    csv.field_size_limit(10 ** 7)
    cod = {}
    for line in open(os.path.join(DATA, "ref_pool", "ref_pool.jsonl")):
        j = json.loads(line)
        if j.get("degree_A") not in (None, ""):
            cod[j["id"]] = j
    ns = {}
    for r in csv.DictReader(open(os.path.join(HERE, "results", "two_axes.csv"))):
        if r.get("n_sents"):
            ns[r["id"]] = float(r["n_sents"])
    rows = []
    for r in csv.DictReader(open(a.src, newline="")):
        c = cod.get(r["id"])
        if not c or r["id"] not in ns:
            continue
        r["drift_A"], r["mode_A"] = c["drift_A"], c["mode_A"]
        r["degree"] = int(c["degree_A"])
        r["n_sents"] = ns[r["id"]]
        rows.append(r)
    print("joined: %s passages, %d models" % ("{:,}".format(len(rows)),
                                              len({r["model"] for r in rows})))
    print("  drift_A %s" % dict(collections.Counter(r["drift_A"] for r in rows).most_common()))
    print("  mode_A  %s" % dict(collections.Counter(r["mode_A"] for r in rows).most_common()))

    lin = roster.lineages()
    of_lineage = {m: b for b, ms in lin.items() for m in ms}

    def band(r):
        """n_sents in coarse bands -- fine enough to match, coarse enough to fill."""
        n = r["n_sents"]
        return 0 if n <= 8 else 1 if n <= 12 else 2 if n <= 18 else 3

    def contrast(field, A, B, strat=None, label="", by_len=False):
        """Median(A) - median(B) within model (and within `strat`), -> lineage."""
        per = collections.defaultdict(list)
        for r in rows:
            per[r["model"]].append(r)
        by_model = {}
        for m, v in per.items():
            def sk(r):
                return ((r[strat] if strat else None), band(r) if by_len else None)
            keys = sorted({sk(r) for r in v})
            got = collections.defaultdict(list)
            for k in keys:
                sub = [r for r in v if sk(r) == k]
                va = [r for r in sub if r[field] == A]
                vb = [r for r in sub if r[field] == B]
                if len(va) < a.min_per_cell or len(vb) < a.min_per_cell:
                    continue
                for lab, col in AXES:
                    got[lab].append(statistics.median(float(x[col]) for x in va)
                                    - statistics.median(float(x[col]) for x in vb))
            if got:
                by_model[m] = {k: statistics.mean(v2) for k, v2 in got.items()}
        by_lin = collections.defaultdict(list)
        for m, d in by_model.items():
            by_lin[of_lineage.get(m, m)].append(d)
        lrows = [{k: statistics.mean(x[k] for x in v) for k in v[0]}
                 for v in by_lin.values()]
        print("\n%s - %s%s   %d models -> %d lineages"
              % (A, B, label, len(by_model), len(lrows)))
        if not lrows:
            print("  no model had >= %d in both cells" % a.min_per_cell)
            return
        print("  %-22s %10s %5s %5s %12s" % ("", "median", "up", "dn", "p"))
        for lab, _ in AXES:
            n, up, dn, med, p = sign_test([x[lab] for x in lrows])
            print("  %-22s %+10.4f %5d %5d %12.3g" % (lab, med, up, dn, p))

    print("\n" + "=" * 68)
    print("1 + 2. CODED DRIFT against both axes  (validation, and surprisal is new)")
    contrast("drift_A", "SHIFTS", "HOLDS")
    print("\n" + "=" * 68)
    print("3. MODE, stratified by degree so it is not re-measuring interiority")
    contrast("mode_A", "SHOWN", "TOLD", strat="degree",
             label="  within (model, degree)")
    print("\n   and the SAME contrast uncontrolled, for the size of the confound:")
    contrast("mode_A", "SHOWN", "TOLD")
    #: SHOWN carries ~1.6 more sentences (26/2 lineages, p=3e-06), and that is
    #: the standing alternative explanation for its drift difference. Matching
    #: on a length band as well as degree is the test, not a formality.
    print("\n   and matched on an n_sents BAND as well, because SHOWN is longer:")
    contrast("mode_A", "SHOWN", "TOLD", strat="degree", by_len=True,
             label="  within (model, degree, length band)")
    #: MODE LOCATES ON THE AXES BUT DOES NOT EXPLAIN THE ARM. Tested here rather
    #: than assumed, because a reader who has just seen SHOWN drift more will
    #: reach for it as the mechanism behind the arm effect.
    per = collections.defaultdict(list)
    for r in rows:
        per[r["model"]].append(r["mode_A"])

    def shown_share(v):
        tw = [x for x in v if x in ("TOLD", "SHOWN")]
        return sum(1 for x in tw if x == "SHOWN") / len(tw) if tw else None

    d = []
    for b, ms in lin.items():
        kids = [m for m in ms if m != b and m in per and len(per[m]) >= 10]
        if b not in per or len(per[b]) < 10 or not kids:
            continue
        sb = shown_share(per[b])
        if sb is not None:
            d.append(statistics.mean(shown_share(m2) for m2 in
                                     (per[m] for m in kids)) - sb)
    n, up, dn, med, p = sign_test(d)
    print("\n" + "=" * 68)
    print("DOES THE ARM DIFFER ON MODE? No -- so mode is not the arm's mechanism.")
    print("  SHOWN share, aligned - base, lineage-paired: %+.4f  %d up / %d dn "
          "of %d  p=%.3g" % (med, up, dn, n, p))
    print("  SHOWN drifts more and is more surprising than TOLD, but the arms")
    print("  produce it at the same rate, so it locates the axes without")
    print("  explaining base->aligned.")

    print("\nn is LINEAGES. `n_sents` is printed on every contrast because it is")
    print("the standing alternative explanation for anything on the drift axis.")


if __name__ == "__main__":
    main()
