"""EXPLORATORY. The shape of the Q3 relation, before the test is chosen.

    python -u explore_q3.py

**THIS IS NOT A TEST AND NOTHING HERE IS DECLARED.** `REGISTRATION.md` §5a fixes
Q3's moderator as `scene(w) - frame` -- the faller's own increment over its setup
-- and states a bound on it: the increment is zero-inflated (n=6,884, median 0,
eight of ten deciles exactly 0), so a linear fit would be driven by a thin
charged tail while reporting a slope as though it described the whole.

The amendment deliberately left the TEST undecided. This file exists to look at
the shape first, so the choice is made against something visible. RH, 2026-09-06.

Everything it prints is DISCOVERED and must be labelled as such if cited.
"""
import collections, json, math, os, statistics as S, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
from analyse import sites, curves, auc, binom, ci, END           # noqa: E402

ANN = os.path.join(HERE, "results", "charge_olmo_thinksft_v3.jsonl")


def increments():
    """-> {(prompt, word): scene - frame}. The faller's own charge in context."""
    out = {}
    with open(ANN) as fh:
        for line in fh:
            r = json.loads(line)
            fr = r["frame"]
            for w in r["words"]:
                out[(r["prompt"], w["word"])] = w["scene"] - fr
    return out


def main():
    st = sites(False)
    cv = curves([(p, r["faller"]) for p, r in st.items()]
                + [(p, r["riser"]) for p, r in st.items()])
    inc = increments()

    rows = []
    for p, r in st.items():
        fa = auc(cv.get((p, r["faller"]), {}))
        ri = auc(cv.get((p, r["riser"]), {}))
        k = inc.get((p, r["faller"]))
        if fa is None or ri is None or k is None:
            continue
        rows.append((k, fa[0] - ri[0], fa[0], ri[0], p, r["faller"], r["riser"]))

    print("EXPLORATORY -- nothing here is declared.")
    print("sites with an AUC pair AND a rated faller: %d of %d"
          % (len(rows), len(st)))
    print()
    print("AUC(faller) - AUC(riser), by the FALLER's increment (scene - frame)")
    print()
    print("  %-12s %5s %10s %10s %10s %9s" %
          ("increment", "n", "med diff", "faller AUC", "riser AUC", "up/dn"))
    by = collections.defaultdict(list)
    for k, d, fa, ri, *_ in rows:
        by[k].append((d, fa, ri))
    for k in sorted(by):
        v = by[k]
        up = sum(1 for d, _, _ in v if d > 0)
        print("  %-12s %5d %+10.4f %10.4f %10.4f %5d/%-4d"
              % (("%+d" % k), len(v), S.median([d for d, _, _ in v]),
                 S.median([f for _, f, _ in v]), S.median([r for _, _, r in v]),
                 up, len(v) - up))

    print()
    print("  COLLAPSED: zero mass against the charged tail")
    for lab, sel in (("increment == 0", lambda k: k == 0),
                     ("increment  < 0", lambda k: k < 0),
                     ("increment >= 1", lambda k: k >= 1),
                     ("increment >= 3", lambda k: k >= 3)):
        v = [d for k, d, *_ in rows if sel(k)]
        if len(v) < 3:
            print("    %-16s n=%-4d (too few)" % (lab, len(v)))
            continue
        up = sum(1 for d in v if d > 0)
        lo, hi = ci(v)
        print("    %-16s n=%-4d median %+0.4f  %3d up/%-3d dn  p=%.5f  CI [%+0.4f, %+0.4f]"
              % (lab, len(v), S.median(v), up, len(v) - up,
                 binom(min(up, len(v) - up), len(v)), lo, hi))

    #: rank correlation, which is what the amendment named as one option --
    #: printed so the choice can be made against it, NOT as a result
    xs = [k for k, *_ in rows]
    ys = [d for _, d, *_ in rows]
    def rank(x):
        o = sorted(range(len(x)), key=lambda i: x[i])
        r = [0.0] * len(x)
        for pos, i in enumerate(o):
            r[i] = pos
        return r
    ra, rb = rank(xs), rank(ys)
    ma, mb = S.mean(ra), S.mean(rb)
    num = sum((ra[i] - ma) * (rb[i] - mb) for i in range(len(xs)))
    den = math.sqrt(sum((v - ma) ** 2 for v in ra) * sum((v - mb) ** 2 for v in rb))
    print()
    print("  spearman(increment, AUC diff) = %+0.4f   n=%d"
          % (num / den if den else float("nan"), len(xs)))
    print("  (printed to inform the choice of test, not as a result --")
    print("   with eight deciles tied at 0 the rank transform is mostly ties)")

    print()
    print("  the charged tail, site by site (increment >= 3):")
    print("    %-26s %-12s %-12s %8s %8s" % ("prompt", "faller", "riser", "fAUC", "rAUC"))
    for k, d, fa, ri, p, fw, rw in sorted(
            [r for r in rows if r[0] >= 3], key=lambda z: -z[0])[:14]:
        print("    %-26s %-12s %-12s %8.3f %8.3f"
              % (p.replace("\n", " ")[:26], fw[:12], rw[:12], fa, ri))
    return 0


if __name__ == "__main__":
    sys.exit(main())
