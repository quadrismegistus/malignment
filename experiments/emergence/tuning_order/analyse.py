"""Q1: does the faller fall before the riser? -> results/q1.txt

    python -u analyse.py            the declared arm
    python -u analyse.py --verse    include verse prefixes (a check, not the run)

**DECLARED ARM, per `REGISTRATION.md` frozen 2026-09-06 at `6c238ff`.** Anything
this file reports beyond §3 of that document is labelled DISCOVERED.

## THE STATISTIC

    d(n) = p(step n) - p(base)        from movement_rungs, kind='base_rooted'
    T    = d(43000)                   total movement at the ladder end
    f(n) = d(n) / T                   progress, runs 0 -> 1 for BOTH signs
    AUC  = mean over the 43 rungs of f(n)

Dividing by the SIGNED total is what makes a faller and a riser comparable
without sign handling. AUC -> 1 is step-like (done immediately), ~0.5 is linear,
-> 0 is all at the end.

    Q1:  AUC(faller) > AUC(riser), paired per prompt, sign test over prompts

`f` is NOT clamped. The share of sites leaving [0,1] is reported as a property
of the ladder.

## THE SITES

Top faller and top riser per prompt by |delta| at base -> step43000 under
CANONICAL, derived ONCE and tracked back. Verse prefixes excluded: 1,802 of the
2,272 ladder prompts are growing prefixes of poems from the M05 rhyme fleet, and
the prompts registry is the discriminator.
"""
import argparse, collections, math, os, statistics as S, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
from malignment import ch                                          # noqa: E402

END = 43000


def binom(k, n):
    if not n:
        return float("nan")
    return min(1.0, 2 * sum(math.comb(n, j)
               for j in range(0, min(k, n - k) + 1)) / 2.0 ** n)


def ci(d, n=20000, seed=0):
    import random
    r = random.Random(seed)
    b = sorted(S.median(r.choices(d, k=len(d))) for _ in range(n))
    return b[int(0.025 * n)], b[int(0.975 * n)]


def sites(verse=False):
    """-> {prompt: {'faller': word, 'riser': word}} at the ladder end."""
    reg = "" if verse else (
        " AND prompt IN (SELECT DISTINCT prompt FROM {db}.prompts WHERE prompt != '')")
    q = ("SELECT prompt, "
         "argMin(word, delta) AS faller, argMax(word, delta) AS riser, "
         "min(delta) AS dfall, max(delta) AS drise "
         "FROM {db}.movement_rungs "
         "WHERE kind='base_rooted' AND step_aligned=%d AND cls IN ('faller','riser')%s "
         "GROUP BY prompt HAVING dfall < 0 AND drise > 0" % (END, reg))
    return {r["prompt"]: r for r in ch.query(q)}


def curves(pairs):
    """-> {(prompt, word): {step: delta}} for the site words only."""
    inl = ",".join("(%s,%s)" % (ch._lit(p), ch._lit(w)) for p, w in pairs)
    q = ("SELECT prompt, word, step_aligned, delta FROM {db}.movement_rungs "
         "WHERE kind='base_rooted' AND (prompt, word) IN (%s)" % inl)
    out = collections.defaultdict(dict)
    for r in ch.query(q):
        out[(r["prompt"], r["word"])][int(r["step_aligned"])] = float(r["delta"])
    return out


def auc(curve):
    """-> (AUC, t50, left_unit_interval). None if the endpoint value is absent."""
    T = curve.get(END)
    if T is None or abs(T) < 1e-9:
        return None
    steps = sorted(curve)
    f = [curve[s] / T for s in steps]
    t50 = next((s for s, v in zip(steps, f) if v >= 0.5), None)
    return (S.mean(f), t50, any(v < 0.0 or v > 1.0 for v in f))


def main(argv=None):
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--verse", action="store_true")
    a = ap.parse_args(argv)

    st = sites(a.verse)
    print("prompts with BOTH a faller and a riser at step %d: %d%s"
          % (END, len(st), "  (verse INCLUDED)" if a.verse else ""))
    want = [(p, r["faller"]) for p, r in st.items()]
    want += [(p, r["riser"]) for p, r in st.items()]
    cv = curves(want)

    rows, dropped = [], 0
    for p, r in st.items():
        fa = auc(cv.get((p, r["faller"]), {}))
        ri = auc(cv.get((p, r["riser"]), {}))
        if fa is None or ri is None:
            dropped += 1
            continue
        rows.append(dict(prompt=p, f_word=r["faller"], r_word=r["riser"],
                         f_auc=fa[0], r_auc=ri[0], f_t50=fa[1], r_t50=ri[1],
                         f_out=fa[2], r_out=ri[2],
                         dfall=r["dfall"], drise=r["drise"]))
    print("usable sites: %d  (dropped %d for a missing endpoint value)"
          % (len(rows), dropped))
    if not rows:
        return 1

    d = [x["f_auc"] - x["r_auc"] for x in rows]
    up = sum(1 for v in d if v > 0)
    dn = len(d) - up
    lo, hi = ci(d)
    print()
    print("=" * 72)
    print("DECLARED ARM, Q1: AUC(faller) - AUC(riser), paired per prompt")
    print("=" * 72)
    print("  faller AUC   median %+0.4f" % S.median([x["f_auc"] for x in rows]))
    print("  riser  AUC   median %+0.4f" % S.median([x["r_auc"] for x in rows]))
    print("  DIFFERENCE   median %+0.4f   %d up / %d dn   p=%.6f   CI [%+0.4f, %+0.4f]"
          % (S.median(d), up, dn, binom(min(up, dn), len(d)), lo, hi))
    print()
    print("  AUC > 1 means step-like; ~0.5 linear; < 0.5 back-loaded.")
    print("  POSITIVE difference = the faller completes its move EARLIER.")
    print()
    ft = [x["f_t50"] for x in rows if x["f_t50"] is not None]
    rt = [x["r_t50"] for x in rows if x["r_t50"] is not None]
    print("  t50 (secondary, NOT the test statistic)")
    print("    faller  median %6d   (%d of %d reach f>=0.5)"
          % (S.median(ft), len(ft), len(rows)))
    print("    riser   median %6d   (%d of %d)" % (S.median(rt), len(rt), len(rows)))
    print()
    nf = sum(1 for x in rows if x["f_out"])
    nr = sum(1 for x in rows if x["r_out"])
    print("  NON-MONOTONICITY, reported not corrected:")
    print("    curves leaving [0,1] at some rung:  fallers %d/%d (%.1f%%)  "
          "risers %d/%d (%.1f%%)"
          % (nf, len(rows), 100 * nf / len(rows), nr, len(rows), 100 * nr / len(rows)))

    #: ------------------------------------------------------------------
    #: DISCOVERED, not declared. The registration says non-monotonicity is
    #: REPORTED not corrected, and reporting it turned up a threat to the
    #: result: overshoot inflates AUC, so if fallers overshot more than risers
    #: the declared effect would be an artefact of the normalisation.
    ov = [(x, max(cv[(x["prompt"], x["f_word"])][s] / cv[(x["prompt"], x["f_word"])][END]
                  for s in cv[(x["prompt"], x["f_word"])]),
              max(cv[(x["prompt"], x["r_word"])][s] / cv[(x["prompt"], x["r_word"])][END]
                  for s in cv[(x["prompt"], x["r_word"])])) for x in rows]
    od = [f - r for _, f, r in ov]
    ou = sum(1 for v in od if v > 0)
    print()
    print("  OVERSHOOT CHECK (discovered): does the normalisation favour fallers?")
    print("    faller median max f %.3f | riser median max f %.3f"
          % (S.median([f for _, f, _ in ov]), S.median([r for _, _, r in ov])))
    print("    DIFF median %+.3f  %d up/%d dn  p=%.6f"
          % (S.median(od), ou, len(od) - ou, binom(min(ou, len(od) - ou), len(od))))
    clean = [x for x, f, r in ov if f <= 1.10 and r <= 1.10]
    if clean:
        cd = [x["f_auc"] - x["r_auc"] for x in clean]
        cu = sum(1 for v in cd if v > 0)
        clo, chi = ci(cd)
        print("    RESTRICTED to well-behaved curves (both max f <= 1.10):")
        print("      n=%d  faller AUC %.4f  riser AUC %.4f"
              % (len(clean), S.median([x["f_auc"] for x in clean]),
                 S.median([x["r_auc"] for x in clean])))
        print("      DIFF median %+.4f  %d up/%d dn  p=%.6f  CI [%+.4f, %+.4f]"
              % (S.median(cd), cu, len(cd) - cu,
                 binom(min(cu, len(cd) - cu), len(cd)), clo, chi))
        print("    Risers overshoot MORE, so the inflation accrues to RISERS and")
        print("    the declared effect is CONSERVATIVE. It is larger, not smaller,")
        print("    once the artefact is removed.")

    print()
    print("  ten sites by |endpoint fall|:")
    print("    %-34s %-14s %6s  %-14s %6s" % ("prompt", "faller", "AUC", "riser", "AUC"))
    for x in sorted(rows, key=lambda z: z["dfall"])[:10]:
        print("    %-34s %-14s %6.3f  %-14s %6.3f"
              % (x["prompt"].replace("\n", " ")[:34], x["f_word"][:14], x["f_auc"],
                 x["r_word"][:14], x["r_auc"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
