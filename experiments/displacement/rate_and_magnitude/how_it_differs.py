"""HOW does no-wildchat's displacement differ, not just THAT it differs.

`jaccard_lift.py` establishes that `no-wildchat`'s faller set diverges from the
full mix MORE at higher lift (paired contrast, slope -0.028, t=-3.1, unit = the
prompt). Jaccard is direction-blind: it counts overlap and cannot say what is in
the difference. This asks what the divergent words ARE.

The comparison is the two "uniquely shed" sets on each high-lift prompt --
words the arm sheds that full keeps, against words full sheds that the arm
keeps -- classified by the prompt's own per-word `kind` rating.

THE UNIT IS THE PROMPT, AND THREE AGGREGATIONS WERE TRIED IN THIS ORDER.
Declared because the third is the one reported and it was not the first:

  1. POOL ALL WORDS, chi-square style. no-wildchat SEXUAL odds ratio 0.44
     against full, z=-6.0; no-math and no-persona significant in the OPPOSITE
     direction (OR 1.84, 1.79). **Invalid** -- ~1,155 words treated as
     independent when they cluster in a few prompts, and the direction it gave
     for no-math and no-persona is contradicted below.
  2. PER PROMPT, sexual SHARE of charged words, requiring >=3 charged words on
     both sides. Defined on 17 prompts of 405. Underpowered, p=0.25.
  3. PER PROMPT, the sexual COUNT difference. Defined on every prompt, no
     threshold. This is what is reported.

Aggregation 1 got two of four arms backwards, which is the reason this file
prints all three rather than the conclusion alone.

    python -m experiments.displacement.rate_and_magnitude.how_it_differs
"""
import collections
import math

from malignment import charge
from .jaccard_lift import fallers, BASE, FULL, ABLATIONS

CHARGED = ("SEXUAL", "VIOLENT", "DEGRADING", "COERCIVE", "ILLICIT")


def sign_test(ds):
    up = sum(1 for d in ds if d > 0)
    dn = sum(1 for d in ds if d < 0)
    t = up + dn
    if not t:
        return up, dn, 1.0
    k = min(up, dn)
    return up, dn, min(1.0, 2 * sum(math.comb(t, i) for i in range(k + 1)) / 2 ** t)


def main():
    ix = charge.index()["prompts"]
    lift = {p: float(v) for (p, b), v in charge.lifts_per_lineage(BASE).items()}
    arms = {"full": fallers(FULL)}
    for name, m in ABLATIONS:
        arms[name] = fallers(m)
    shared = set(arms["full"])
    for name in arms:
        shared &= set(arms[name])
    # unsaturated only: readout_share 208 puts the headroom at frames 2-4
    pool = sorted(p for p in shared if p in lift and p in ix
                  and ix[p].get("frame") is not None and ix[p]["frame"] < 5)
    hi = sorted(pool, key=lambda p: -lift[p])[:len(pool) // 4]

    print("HIGH-LIFT UNSATURATED PROMPTS: n = %d of %d\n" % (len(hi), len(pool)))
    print("CATEGORY COMPOSITION, charged words only, pooled (AGGREGATION 1).")
    print("Shown for the shape; the test on it is invalid -- see the docstring.")
    print("%-12s %-5s %7s %8s %10s %9s %8s %6s"
          % ("arm", "side", "SEXUAL", "VIOLENT", "DEGRADING", "COERCIVE",
             "ILLICIT", "n"))
    for arm, _m in ABLATIONS:
        for lab in ("arm", "full"):
            c = collections.Counter()
            for p in hi:
                k = ix[p].get("kind") or {}
                S = (arms[arm][p] - arms["full"][p]) if lab == "arm" \
                    else (arms["full"][p] - arms[arm][p])
                for w in S:
                    if k.get(w) in CHARGED:
                        c[k[w]] += 1
            n = sum(c.values()) or 1
            print("%-12s %-5s %6.1f%% %7.1f%% %9.1f%% %8.1f%% %7.1f%% %6d"
                  % (arm if lab == "arm" else "", lab,
                     100 * c["SEXUAL"] / n, 100 * c["VIOLENT"] / n,
                     100 * c["DEGRADING"] / n, 100 * c["COERCIVE"] / n,
                     100 * c["ILLICIT"] / n, n))
        print()

    print("THE REPORTED TEST (AGGREGATION 3). Unit = the prompt.")
    print("  d = (# SEXUAL uniquely shed by FULL) - (# SEXUAL uniquely shed by ARM)")
    print("  positive d = the full mix targets sexual content MORE than the arm\n")
    print("%-12s %8s %9s %9s %9s" % ("arm", "n(d!=0)", "mean d", "up/dn", "p"))
    for arm, _m in ABLATIONS:
        ds = []
        for p in hi:
            k = ix[p].get("kind") or {}
            a = sum(1 for w in arms[arm][p] - arms["full"][p]
                    if k.get(w) == "SEXUAL")
            f = sum(1 for w in arms["full"][p] - arms[arm][p]
                    if k.get(w) == "SEXUAL")
            ds.append(f - a)
        up, dn, p = sign_test(ds)
        print("%-12s %8d %9.3f %9s %9.4f"
              % (arm, sum(1 for d in ds if d), sum(ds) / len(ds),
                 "%d/%d" % (up, dn), p))


if __name__ == "__main__":
    main()
