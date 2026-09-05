"""Which groups does alignment treat differently, and is it more than vocabulary?

    python experiments/slot_ratings/identity/group_contrast.py

## WHY THIS FILE EXISTS SEPARATELY FROM analyse.py

analyse.py reported a per-group mean rho and I read the between-group variation
off it by eye, then "checked" it by restricting to the words eligible in all 24
groups and finding the ranking reshuffled. That check was wrong twice over: it
had four words on the `street` sweep, so it had no power to find anything, and
its failure is not evidence of absence.

It also threw away the design. The SAME ~14-20 lineages run through all 24 groups
in the SAME frame, so the group contrast is paired within lineage. Treating the
groups as independent samples of noisy rhos discards the blocking factor that
makes this corpus worth having.

## THE TWO TRAPS THIS FILE AVOIDS

TOP-VS-BOTTOM IS SELECTED ON THE OUTCOME. Taking the highest and lowest group by
mean and testing them paired is significant by construction; the first version of
this analysis printed those p-values (13/14, p=0.0002) as though they were
evidence. Every group is instead tested against the mean of the OTHER groups on
the same lineage, which selects nothing, and the 24 tests are FDR-corrected.

`n_*` COLUMNS ARE NOT SCALES. They are how many rated words carried the scale,
and they differ by group enormously (Chinese 54 vs Christians 38 on `room`,
Friedman p=8e-14). That is the vocabulary difference stated directly. It is
excluded from the scale table and tested separately as a possible mediator.
"""

import collections, json, os, sys
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results")


def load():
    rows = json.load(open(os.path.join(OUT, "group_rho.json")))["rows"]
    meta = ("group", "sweep", "lineage", "n")
    scales = sorted({k for r in rows for k in r
                     if k not in meta and not k.startswith("n_")})
    return rows, scales


def matrix(rows, sweep, field):
    """(lineage, group) -> value, restricted to lineages present for EVERY group."""
    cell = {(r["lineage"], r["group"]): r[field]
            for r in rows if r["sweep"] == sweep and r.get(field) is not None}
    Gs = sorted({g for _, g in cell})
    Ls = [l for l in sorted({l for l, _ in cell})
          if all((l, g) in cell for g in Gs)]
    return cell, Ls, Gs


def main():
    from scipy import stats
    rows, scales = load()
    saved = []
    for sweep in ("room", "nextdoor", "street"):
        print("\n" + "=" * 78)
        print("SWEEP %r" % sweep)
        het = []
        for s in scales:
            cell, Ls, Gs = matrix(rows, sweep, s)
            if len(Ls) < 8 or len(Gs) < 10:
                continue
            fr = stats.friedmanchisquare(*[[cell[(l, g)] for l in Ls] for g in Gs])
            het.append((s, fr.pvalue, len(Ls), len(Gs)))
        het.sort(key=lambda t: t[1])
        bonf = 0.05 / max(1, len(het))
        print("\n  HETEROGENEITY across groups, Friedman blocked on lineage.")
        print("  %d scales tested, Bonferroni threshold %.4f\n" % (len(het), bonf))
        print("  %-14s %7s %7s %11s  %s" % ("scale", "blocks", "groups", "friedman", ""))
        for s, p, nl, ng in het:
            print("  %-14s %7d %7d %11.2g  %s"
                  % (s, nl, ng, p, "PASSES BONFERRONI" if p < bonf else ""))

        #: per group, against the mean of the OTHER groups on the same lineage.
        #:
        #: EMIT EVERY SCALE THAT PASSES BONFERRONI, not the top 4 (2026-09-05).
        #: `het[:4]` was a DISPLAY cut and it silently decided which cells exist:
        #: at 20 lineages `deference` made it and this folder's most-quoted result
        #: -- Muslims deference +0.198, 14 of 14 -- came from it. At 50 lineages
        #: other scales rank above it, so the cell vanished from the output
        #: without being tested, refuted, or mentioned. A ranking cut that
        #: changes which results EXIST when the panel grows is not a display
        #: choice; the Bonferroni threshold is already the test and it decides.
        for s, p, nl, ng in het:
            if p >= bonf:
                continue
            cell, Ls, Gs = matrix(rows, sweep, s)
            res = []
            for g in Gs:
                d = [cell[(l, g)] - st.mean(cell[(l, o)] for o in Gs if o != g)
                     for l in Ls]
                res.append((g, st.mean(d), sum(1 for x in d if x > 0), len(d),
                            stats.wilcoxon(d).pvalue))
            ps = [r[4] for r in res]
            rej, q = stats.false_discovery_control(ps), None
            print("\n  %s: each group vs the mean of the other %d, paired over %d lineages"
                  % (s.upper(), len(Gs) - 1, len(Ls)))
            print("  %-19s %8s %8s %10s" % ("group", "delta", "up/n", "q (BH)"))
            for (g, m, u, n, pv), qv in sorted(zip(res, rej), key=lambda t: -t[0][1]):
                star = "*" if qv < 0.05 else " "
                print("  %-19s %+8.3f %5d/%-3d %9.3g %s" % (g, m, u, n, qv, star))
                saved.append(dict(sweep=sweep, scale=s, group=g, delta=m,
                                  up=u, n=n, p=pv, q=qv))

        #: is the group effect just "more words rated"?
        print("\n  MEDIATION CHECK: does the group's rated-word count explain it?")
        for s, p, nl, ng in het[:4]:
            if p >= bonf:
                continue
            cell, Ls, Gs = matrix(rows, sweep, s)
            ncell, _, _ = matrix(rows, sweep, "n")
            xs, ys = [], []
            for g in Gs:
                for l in Ls:
                    if (l, g) in ncell:
                        xs.append(ncell[(l, g)]); ys.append(cell[(l, g)])
            r = stats.spearmanr(xs, ys)
            print("    %-14s rho(n_words, %s) = %+.3f  p=%.2g  (n=%d cells)"
                  % (s, s, r.statistic, r.pvalue, len(xs)))

    json.dump(dict(_what="per (sweep, scale, group) deviation from the mean of the "
                         "other groups on the same lineage; BH-corrected over groups",
                   rows=saved), open(os.path.join(OUT, "group_contrast.json"), "w"),
              indent=1)
    print("\n-> results/group_contrast.json (%d rows)" % len(saved))


if __name__ == "__main__":
    main()
