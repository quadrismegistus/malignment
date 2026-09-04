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
     threshold. **CONFOUNDED** -- full sheds 1.27 more words per prompt overall
     (221/137, p<1e-4), so a raw count favours it in every category.
  4. PER PROMPT, the sexual SHARE, requiring only >=1 word on each side rather
     than >=3 charged words. n=295 of 405. **This is what is reported.**

**AGGREGATION 3 IS THE ONE THAT GOT ARMS WRONG, NOT AGGREGATION 1.** On the
normalised share, 1 and 4 agree on the DIRECTION for all four arms; 1's p-values
are invalid because of the unit, but its signs were right the whole time. The
count test manufactured a `no-safety` result that is null on the share, and
erased the `no-math` / `no-persona` reversals that both other aggregations find.
This file prints all of them, plus the per-category confound table, because the
conclusion alone would hide that the reported effect is about a tenth the size
the count test implied.

AND THE `kind` LABEL IS CONTEXTUAL, NOT LEXICAL. Reading cells shows `said`,
`spoke`, `told`, `asked` and `gave` rated SEXUAL inside a sexual scene. The
rating is what the word DOES in its scene, so the claim this file supports is
about words that advance a sexual reading IN CONTEXT -- not about a sexual
lexicon. `division_of_labour/removal_rates` uses a blind-built lexical set and is
the instrument for the lexical version of the question.

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

    print("CONFOUND TABLE: the same statistic for EVERY category and the total.")
    print("If the excess were uniform set inflation, NONE would move too.\n")
    print("%-12s %9s %9s %9s" % ("category", "mean d", "up/dn", "p"))
    for cat in ("SEXUAL", "VIOLENT", "COERCIVE", "DEGRADING", "ILLICIT",
                "NONE", "*TOTAL*"):
        ds = []
        for q in hi:
            k = ix[q].get("kind") or {}
            A = arms["no-wildchat"][q] - arms["full"][q]
            F = arms["full"][q] - arms["no-wildchat"][q]
            if cat == "*TOTAL*":
                ds.append(len(F) - len(A))
            else:
                ds.append(sum(1 for w in F if k.get(w) == cat)
                          - sum(1 for w in A if k.get(w) == cat))
        up, dn, pv = sign_test(ds)
        print("%-12s %9.3f %9s %9.4f"
              % (cat, sum(ds) / len(ds), "%d/%d" % (up, dn), pv))

    print("\nTHE REPORTED TEST (AGGREGATION 4): SEXUAL as a SHARE of each")
    print("side's uniquely-shed set. Unit = the prompt. Normalised, so the")
    print("1.27-word set-size excess above cannot produce it.\n")
    print("%-12s %7s %10s %9s %9s" % ("arm", "n", "mean d", "up/dn", "p"))
    for arm, _m in ABLATIONS:
        ds = []
        for q in hi:
            k = ix[q].get("kind") or {}
            A = list(arms[arm][q] - arms["full"][q])
            F = list(arms["full"][q] - arms[arm][q])
            if not A or not F:
                continue
            ds.append(sum(1 for w in F if k.get(w) == "SEXUAL") / len(F)
                      - sum(1 for w in A if k.get(w) == "SEXUAL") / len(A))
        up, dn, pv = sign_test(ds)
        print("%-12s %7d %10.4f %9s %9.4f"
              % (arm, len(ds), sum(ds) / len(ds), "%d/%d" % (up, dn), pv))

    print("\nAGGREGATION 3, CONFOUNDED, kept visible. Unit = the prompt.")
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
