"""Q2: does the PROMPT's charge modulate the lag? -> results/q2.txt

    python -u q2.py

**DECLARED ARM**, `REGISTRATION.md` §4: *"Regress the per-prompt lag on
`charge.lift(p)`. Continuous, not a two-bin contrast."*

`charge.lift(p)` is dose - frame at the PROMPT level, from the existing 50-pair
corpus. Q3 asked the same question of the FALLER WORD's own charge; this asks it
of the prompt as a whole, so the two are different grains of one question and
both are reported.

Run on BOTH statistics: the registered AUC lag, and the timing lag that
supersedes it. Reporting only the second would quietly drop the declared arm;
reporting only the first would answer with the instrument the finding rejects.
"""
import collections, math, os, statistics as S, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
from malignment import charge as CH                                # noqa: E402
from timing import timings                                        # noqa: E402
from analyse import sites, curves, auc                            # noqa: E402


def spear(a, b):
    def rk(x):
        o = sorted(range(len(x)), key=lambda i: x[i]); r = [0.0] * len(x)
        for pos, i in enumerate(o):
            r[i] = pos
        return r
    ra, rb = rk(a), rk(b); ma, mb = S.mean(ra), S.mean(rb)
    num = sum((ra[i] - ma) * (rb[i] - mb) for i in range(len(a)))
    den = math.sqrt(sum((v - ma) ** 2 for v in ra) * sum((v - mb) ** 2 for v in rb))
    return num / den if den else float("nan")


def pval(rho, n):
    from math import erf, sqrt
    t = rho * math.sqrt((n - 2) / max(1e-12, 1 - rho ** 2))
    return t, 2 * (1 - 0.5 * (1 + erf(abs(t) / sqrt(2))))


def main():
    t = timings()
    byp = collections.defaultdict(lambda: {"faller": [], "riser": []})
    for p, w, c, tm in t:
        byp[p][c].append(tm)
    lag = {p: S.mean(d["riser"]) - S.mean(d["faller"])
           for p, d in byp.items() if d["faller"] and d["riser"]}
    st = sites(False)
    cv = curves([(p, r["faller"]) for p, r in st.items()]
                + [(p, r["riser"]) for p, r in st.items()])
    aucl = {}
    for p, r in st.items():
        fa, ri = auc(cv.get((p, r["faller"]), {})), auc(cv.get((p, r["riser"]), {}))
        if fa and ri:
            aucl[p] = fa[0] - ri[0]

    print("Q2 -- DECLARED ARM. Prompt-level charge.lift as a moderator.")
    print()
    for lab, d in (("TIMING lag (steps)", lag), ("DECLARED AUC lag", aucl)):
        xs, ys = [], []
        for p, v in d.items():
            L = CH.lift(p)
            if L is not None:
                xs.append(L); ys.append(v)
        rho = spear(xs, ys); tt, pp = pval(rho, len(xs))
        q = sorted(xs)
        lo = [y for x, y in zip(xs, ys) if x <= q[len(q) // 3]]
        hi = [y for x, y in zip(xs, ys) if x >= q[2 * len(q) // 3]]
        print("  %s" % lab)
        print("    n=%-4d  spearman rho %+0.4f   t=%.2f   p=%.3f"
              % (len(xs), rho, tt, pp))
        print("    low-lift tercile  n=%-4d median %+.4g" % (len(lo), S.median(lo)))
        print("    high-lift tercile n=%-4d median %+.4g" % (len(hi), S.median(hi)))
        if lab.startswith("TIMING"):
            diff = S.median(hi) - S.median(lo)
            print("    DIFFERENCE %+.0f steps = %.1f%% of the %.0f-step effect."
                  % (diff, 100 * abs(diff) / S.median(lo), S.median(lo)))
            print("    **Quote the bound as that fraction, never as p=%.3f.**" % pp)
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
