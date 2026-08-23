"""Is the procedure territory ONE relation or TWO? Decide by measurement, not by vote.

    python seam_test.py                 # the test, on every rating source
    python seam_test.py --scales        # which scales separate the two arms

## THE QUESTION

Thirteen components form one territory every rater recognises. They disagree on
whether it is one relation or two:

    opus high    Grievance routed into formal recourse (9)     SPLITS
                 The authority's act rewritten as procedure (4)
    opus xhigh   Proceduralization (13)                        MERGES
    opus medium  Direct action routed through an institution (14)  MERGES

Three of five raters across both documents split it, two merge it. A fourth
rater is another vote, not evidence, and the membership is not in dispute: high's
9+4 and xhigh's 13 hold EXACTLY the same components, zero on either side only. So
what is contested is a seam inside a fixed set, which is answerable.

## THE TEST

If the seam is real, the two arms move DIFFERENTLY through rating space. Take
high's split as the hypothesis, compute each component's shift vector, and ask
whether the between-arm distance exceeds what the same split sizes give on the
same 13 components permuted at random.

    observed = Euclidean distance between the two arms' MEAN SHIFT VECTORS
    null     = the same, over random 8/4 splits of the same components

A large, unlikely gap says the arms sit in different places -- the seam is there
and two raters missed it. A null says the 13 components are one cloud and the
raters who merged them were right.

An earlier version measured within-arm COHESION minus across-arm cohesion and
returned p = 0.32 on institutional, which I read as "no seam" before the
per-scale table showed `deference` +1.00 and `assertiveness` -0.94 between the
arms. Cohesion was the wrong question: two clouds can each be loose and still sit
apart, and at 8 and 4 components the within-arm term is mostly noise. The
corrected statistic gives p = 0.056 on the same data.

## WHAT IT CANNOT DO

It cannot show the seam is ABSENT. A null means these scales do not see it, and
`institutional` -- whose vocabulary is agency, deference, procedural, mediation --
is the one most likely to if anything does. That asymmetry is RH's, and it is why
the result is reported per source rather than pooled into a verdict.
"""
import argparse
import itertools
import json
import os
import random
import math
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cross_frame as CF  # noqa: E402
import norm_test as NT  # noqa: E402

#: THE HYPOTHESIS UNDER TEST, taken from the rater that split rather than
#: invented here. Reading the arms off a fresh reading of the components would
#: be fitting the seam to the data it is meant to test.
SPLIT_FROM = "high"
ARM_A = "Grievance routed into formal recourse"
ARM_B = "The authority's act rewritten as procedure"


def arms():
    p = os.path.join(HERE, "results", "crossframe_groups_89_opus_%s.json" % SPLIT_FROM)
    g = {x["name"]: set(x["members"]) for x in json.load(open(p))["groups"]}
    a, b = g.get(ARM_A), g.get(ARM_B)
    assert a and b, "the %s rater has no arms named %r / %r" % (SPLIT_FROM, ARM_A, ARM_B)
    assert not (a & b), "the two arms overlap on %s" % sorted(a & b)
    return a, b


def _vec(S, SC, cid):
    return [S[cid].get(s) for s in SC]


def centroid_gap(S, SC, a, b):
    """Euclidean distance between the two arms' MEAN SHIFT VECTORS.

    ## WHY THIS REPLACED A COSINE-COHESION STATISTIC

    The first version measured within-arm cohesion minus across-arm cohesion in
    cosine: does each arm hold together more tightly than it resembles the other.
    It returned +0.02 on institutional and I read that as "no seam" -- then the
    per-scale table showed `deference` +1.00 and `assertiveness` -0.94 between
    the arms, which is a large, coherent difference the statistic could not see.

    Cohesion is the wrong question. Two clouds can be individually loose and
    still sit in different places, and at 8 and 4 components within-arm cohesion
    is mostly noise, so the statistic was dominated by the term that carries no
    information about the seam. A difference of MEANS is what the claim is about.

    ## THE p FLOOR IS REAL AND IS PRINTED

    With 8 and 4 components there are C(12,4) = 495 distinct label assignments,
    so no permutation test on this split can report below about 0.002 however
    large the effect. That is a property of the sample, not of the result.
    """
    ca = [c for c in a if c in S]
    cb = [c for c in b if c in S]
    ks = [s for s in SC
          if sum(1 for c in ca if S[c].get(s) is not None) >= 2
          and sum(1 for c in cb if S[c].get(s) is not None) >= 2]
    if not ks or len(ca) < 2 or len(cb) < 2:
        return None, ks, (len(ca), len(cb))
    d = 0.0
    for s in ks:
        va = [S[c][s] for c in ca if S[c].get(s) is not None]
        vb = [S[c][s] for c in cb if S[c].get(s) is not None]
        d += (statistics.mean(vb) - statistics.mean(va)) ** 2
    return math.sqrt(d), ks, (len(ca), len(cb))


def test(src, iters=5000, seed=20260823, M=None):
    SC, _, kind = NT.SOURCES[src]
    M = M if M is not None else CF.as_read()
    S, _ = NT.shifts(M, NT.ratings(src), SC)
    a, b = arms()
    pool = sorted((a | b) & set(S))
    obs, ks, ns = centroid_gap(S, SC, a, b)
    if obs is None:
        return dict(src=src, kind=kind, covered=len(pool), obs=None, p=None, ns=ns)
    na = ns[0]
    rng = random.Random(seed)
    null = []
    for _ in range(iters):
        p = pool[:]
        rng.shuffle(p)
        v, _, _ = centroid_gap(S, SC, set(p[:na]), set(p[na:]))
        if v is not None:
            null.append(v)
    pv = (sum(1 for x in null if x >= obs) + 1.0) / (len(null) + 1.0)
    return dict(src=src, kind=kind, covered=len(pool), obs=obs, p=pv, ns=ns,
                nscale=len(ks), null=statistics.median(null),
                p95=sorted(null)[int(.95 * len(null))] if null else None)


def per_scale(src, iters=5000, seed=20260823, M=None):
    """Which scales carry it, each with its own permutation p. Uncorrected."""
    SC, _, _ = NT.SOURCES[src]
    M = M if M is not None else CF.as_read()
    S, _ = NT.shifts(M, NT.ratings(src), SC)
    a, b = arms()
    ca = [c for c in a if c in S]
    cb = [c for c in b if c in S]
    pool = ca + cb
    rng = random.Random(seed)
    out = []
    for s in SC:
        va = [S[c][s] for c in ca if S[c].get(s) is not None]
        vb = [S[c][s] for c in cb if S[c].get(s) is not None]
        if len(va) < 2 or len(vb) < 2:
            continue
        obs = statistics.mean(vb) - statistics.mean(va)
        null = []
        for _ in range(iters):
            p = pool[:]
            rng.shuffle(p)
            xa = [S[c][s] for c in p[:len(ca)] if S[c].get(s) is not None]
            xb = [S[c][s] for c in p[len(ca):] if S[c].get(s) is not None]
            if len(xa) >= 2 and len(xb) >= 2:
                null.append(statistics.mean(xb) - statistics.mean(xa))
        pv = (sum(1 for x in null if abs(x) >= abs(obs)) + 1.0) / (len(null) + 1.0)
        out.append((s, statistics.mean(va), statistics.mean(vb), obs, pv))
    return out


def scales_table():
    M = CF.as_read()
    a, b = arms()
    print("PER-SCALE MEAN SHIFT, the two arms of the procedure territory\n")
    for src in ("institutional", "v6"):
        SC, _, _ = NT.SOURCES[src]
        S, _ = NT.shifts(M, NT.ratings(src), SC)
        ca = [c for c in a if c in S]
        cb = [c for c in b if c in S]
        if not ca or not cb:
            print("  %s: not covered\n" % src)
            continue
        print("  %s  (%d aggrieved-party, %d authority)" % (src, len(ca), len(cb)))
        print("     %-16s %8s %8s %8s" % ("scale", "arm A", "arm B", "diff"))
        for s in SC:
            va = [S[c][s] for c in ca if s in S[c]]
            vb = [S[c][s] for c in cb if s in S[c]]
            if not va or not vb:
                continue
            ma, mb = statistics.mean(va), statistics.mean(vb)
            print("     %-16s %+8.2f %+8.2f %+8.2f" % (s, ma, mb, mb - ma))
        print()


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--iters", type=int, default=5000)
    ap.add_argument("--scales", action="store_true")
    ap.add_argument("--per-scale", action="store_true",
                    help="permutation p per scale, uncorrected -- for reading, not deciding")
    a = ap.parse_args()
    if a.per_scale:
        for src in ("institutional", "v6"):
            print("\n%s -- mean shift per scale, arm A (aggrieved) vs arm B (authority)" % src)
            print("  %-16s %8s %8s %8s %8s" % ("scale", "A", "B", "diff", "p"))
            for s_, ma, mb, d, pv in sorted(per_scale(src, a.iters), key=lambda x: x[4]):
                print("  %-16s %+8.2f %+8.2f %+8.2f %8.3f%s"
                      % (s_, ma, mb, d, pv, "  *" if pv < .05 else ""))
        print("\n  Uncorrected across 13 and 12 scales; at alpha .05 one hit is expected")
        print("  by chance in each. Read as which scales carry the gap, not as a verdict.")
        return
    if a.scales:
        scales_table()
        return
    M = CF.as_read()
    aa, bb = arms()
    print("IS THE PROCEDURE SEAM REAL?  %d components, split %d / %d by opus-%s\n"
          % (len(aa | bb), len(aa), len(bb), SPLIT_FROM))
    print("  %-14s %-11s %8s %7s %9s %9s %9s"
          % ("source", "kind", "covered", "scales", "gap", "null95", "p"))
    for src in ("institutional", "v6", "k", "human", "sexual"):
        try:
            r = test(src, a.iters, M=M)
        except Exception as e:
            print("  %-14s FAILED %s" % (src, str(e)[:50]))
            continue
        if r["obs"] is None:
            print("  %-14s %-11s %8d %9s %9s %9s"
                  % (r["src"], r["kind"], r["covered"], "-", "-", "no pairs"))
            continue
        print("  %-14s %-11s %8d %7d %9.3f %9.3f %9.4f%s"
              % (r["src"], r["kind"], r["covered"], r["nscale"], r["obs"],
                 r["p95"], r["p"], "  SEAM" if r["p"] < .05 else ""))
    import math as _m
    n = sum(1 for _ in itertools.combinations(range(12), 4))
    print("\n  p floor for an 8/4 split is 1/%d = %.4f: no permutation test on this"
          % (n + 1, 1.0 / (n + 1)))
    print("  sample can go below it however large the effect.")
    print("\n  A null does not show the seam is absent -- only that these scales")
    print("  do not see it. Reported per source for that reason.")


if __name__ == "__main__":
    main()
