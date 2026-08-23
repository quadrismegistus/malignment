"""G, G1, G2 — does alignment raise the register of the distribution, and is the
rise displacement or suppression?

    .venv/bin/python -u experiments/displacement/register_shift/run.py

Runs the design frozen in `registration.md` AMENDMENT A1. R1-R4 in that file were
superseded before any run and are NOT what this executes.

    INSTRUMENT   k_register_level, English + Chinese, 1-7 continuous
    STATISTIC    mass-weighted mean register, sum(mass * register) / sum(mass)
    EDGE         base -> endpoint (the commodity form)
    UNIT         the lineage

## THE THREE HYPOTHESES, AND WHY G ALONE IS NOT ENOUGH

    G    the mass-weighted mean register RISES, base -> endpoint
    G1   what LEAVES is low-register     mean_register(removed) < distribution mean
    G2   what ARRIVES is high-register   mean_register(arrived) > distribution mean

Decision rule 6 of the registration: **G1/G2 are required for the word
"displacement"; G alone licenses only "the register rises."** The mean can rise
either because low-register mass fell or because high-register mass arrived, and
only the decomposition separates suppression from displacement. `arrived >
removed` is the displacement signature.

## WHAT IS DECLARED BEFORE ANY NUMBER IS READ

**Coverage is a covariate, not a footnote.** A base->endpoint comparison is
confounded if the k-covered subset moves between the arms. The registration
requires per-pair coverage shift and a pre-committed sensitivity dropping pairs
above 2pp; both are printed.

**The sign-test MDE is printed before any p-value**, per decision rule 1.

**A null is reported as a BOUND**, per rule 2.

**S (the sexual subset) is CONFIRMATORY, not a discovery**, per rule 5 and the
registration's own disclosure: vulgar-out/clinical-retained was observed in
`removal_rates` exemplars before this was frozen.
"""
import argparse, collections, json, math, os, statistics as S, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
SCALE = "register_level"


def binom(k, n):
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(0, min(k, n - k) + 1))
               / 2.0 ** n) if n else float("nan")


def mde_sign(n, alpha=0.05):
    """Smallest majority split reaching alpha on a two-sided sign test."""
    for k in range(n // 2, -1, -1):
        if binom(k, n) <= alpha:
            return n - k, n
    return None, n


def cells(model, ch, fields, lut):
    """-> {prompt: {word: p}} for one model, plus covered/total mass."""
    q = ("SELECT prompt, word, p FROM twp_words_v4_best WHERE model = %s"
         % repr(model).replace('"', "'"))
    out = collections.defaultdict(dict)
    cov = tot = 0.0
    for r in ch.query(q):
        w, p = r["word"], float(r["p"])
        out[r["prompt"]][w] = p
        tot += p
        if w not in lut:
            lut[w] = fields.k(w) or fields.k(w.lower())
        if lut[w]:
            cov += p
    return out, cov, tot


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "results", "by_lineage.csv"))
    a = ap.parse_args(argv)
    from malignment import ch, roster, fields

    pairs = roster.endpoints()[0]
    lut = {}
    rows = []
    print("base->endpoint pairs in the roster: %d" % len(pairs), flush=True)

    for i, (b, e) in enumerate(sorted(pairs.items()), 1):
        try:
            B, bc, bt = cells(b, ch, fields, lut)
            E, ec, et = cells(e, ch, fields, lut)
        except Exception as ex:
            print("  %-44s SKIP %s" % (b.split("/")[-1][:44], str(ex)[:40]), flush=True)
            continue
        shared = [p for p in B if p in E]
        if not shared:
            continue
        num_b = den_b = num_e = den_e = 0.0
        rem_n = rem_d = arr_n = arr_d = 0.0
        for pr in shared:
            bw, ew = B[pr], E[pr]
            for w in set(bw) | set(ew):
                d = lut.get(w)
                if not d:
                    continue
                r = d[SCALE]
                pb, pe = bw.get(w, 0.0), ew.get(w, 0.0)
                num_b += pb * r; den_b += pb
                num_e += pe * r; den_e += pe
                dp = pe - pb
                if dp < 0:
                    rem_n += -dp * r; rem_d += -dp
                elif dp > 0:
                    arr_n += dp * r; arr_d += dp
        if den_b <= 0 or den_e <= 0 or rem_d <= 0 or arr_d <= 0:
            continue
        rows.append(dict(
            base=b, endpoint=e, n_prompts=len(shared),
            reg_base=num_b / den_b, reg_end=num_e / den_e,
            reg_removed=rem_n / rem_d, reg_arrived=arr_n / arr_d,
            cov_base=bc / bt if bt else 0.0, cov_end=ec / et if et else 0.0))
        if i % 10 == 0:
            print("  %d/%d pairs" % (i, len(pairs)), flush=True)

    if not rows:
        print("NO USABLE PAIRS"); return 1
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    import csv
    with open(a.out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        for r in rows:
            w.writerow({k: (round(v, 6) if isinstance(v, float) else v)
                        for k, v in r.items()})

    n = len(rows)
    need, _ = mde_sign(n)
    print()
    print("USABLE LINEAGES: %d" % n)
    print("SIGN-TEST MDE at alpha=.05: %d of %d (%.0f%%) -- printed BEFORE any p"
          % (need, n, 100.0 * need / n))

    print()
    print("COVERAGE, the declared covariate")
    shifts = [abs(r["cov_end"] - r["cov_base"]) * 100 for r in rows]
    print("  k-covered mass: base median %.3f   endpoint median %.3f"
          % (S.median([r["cov_base"] for r in rows]),
             S.median([r["cov_end"] for r in rows])))
    print("  |within-pair shift| median %.2fpp   max %.2fpp   pairs >2pp: %d"
          % (S.median(shifts), max(shifts), sum(1 for x in shifts if x > 2)))

    def report(label, deltas):
        up = sum(1 for x in deltas if x > 0); dn = sum(1 for x in deltas if x < 0)
        d = sorted(deltas)
        lo, hi = d[int(0.025 * len(d))], d[int(0.975 * len(d))]
        print("  %-42s %2d/%2d  median %+.4f  [%+.4f, %+.4f]  p=%.5f"
              % (label, up, up + dn, S.median(d), lo, hi, binom(min(up, dn), up + dn)))

    print()
    print("G  -- does the mass-weighted mean register RISE, base -> endpoint?")
    report("G: reg_end - reg_base", [r["reg_end"] - r["reg_base"] for r in rows])

    print()
    print("G1/G2 -- REQUIRED for the word 'displacement' (decision rule 6)")
    report("G1: reg_removed - reg_base  (want <0)",
           [r["reg_removed"] - r["reg_base"] for r in rows])
    report("G2: reg_arrived - reg_base  (want >0)",
           [r["reg_arrived"] - r["reg_base"] for r in rows])
    report("SIGNATURE: reg_arrived - reg_removed",
           [r["reg_arrived"] - r["reg_removed"] for r in rows])

    print()
    print("SENSITIVITY, pre-committed: dropping pairs with coverage shift >2pp")
    keep = [r for r in rows if abs(r["cov_end"] - r["cov_base"]) * 100 <= 2]
    print("  %d of %d pairs retained" % (len(keep), len(rows)))
    if len(keep) >= 5:
        report("G  (sensitivity)", [r["reg_end"] - r["reg_base"] for r in keep])
        report("SIGNATURE (sensitivity)",
               [r["reg_arrived"] - r["reg_removed"] for r in keep])
    print()
    print("-> %s" % a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
