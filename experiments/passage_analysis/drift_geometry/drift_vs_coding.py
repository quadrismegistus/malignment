"""Does geometric drift track what a blind reader calls staying in the scene?

    python experiments/passage_analysis/drift_geometry/drift_vs_coding.py

The external criterion the audit never had. `drift_metric_audit.md` compared the
metrics against each other -- order-invariance, ICC, n-dependence -- and had
nothing outside the family to test them on. `../interiority_in_passages/` supplies
one: 13,565 passages read blind and coded HOLDS / SHIFTS / UNMOORED at kappa 0.904.

## THE UNIT QUESTION, WHICH IS TWO QUESTIONS

RH's correction, and it is the design:

  * **Does geometric drift correspond to the coded judgment?** That is a
    PASSAGE-LEVEL relationship. Each passage was coded blind and scored
    independently, so each is an independent observation OF THAT CORRESPONDENCE.
    Passage n is the right n.
  * **Does anything here differ by ARM?** That is an ALIGNMENT claim, and there
    the lineage pair is the unit, because passages from one model share a recipe.

So both are reported, and the second is a robustness check on the first rather
than a replacement for it. Reported three ways:

    passage      mean difference and Mann-Whitney over passages
    clustered    cluster bootstrap resampling LINEAGE PAIRS, not passages
    per-pair     the contrast computed inside each pair, then a sign test

If the passage-level result is carried by within-cluster correlation, the bootstrap
widens and the sign test thins. If it is a real per-passage correspondence, all
three agree.

## Controls, each because something forced it

  NARRATIVE       `narrative` and `drift` are entangled -- UNMOORED is 17
                  narrative against 1,435 not -- and non-narrative passages drift
                  more anyway (0.4726 vs 0.4442) for reasons that are about format
                  rather than about drifting. Every contrast runs WITHIN a
                  narrative level, never pooled across.
  n_sents         the audit's defect 3: directedness IS sentence count. Reported
                  per contrast so a length difference cannot hide inside one.
  AGREEMENT       3,610 passages carry a second blind coder. The contrast is
                  re-run where both agree, which is a purity filter, not a
                  robustness one: if the effect is real it should SHARPEN there.

## HOLDS vs SHIFTS is the only powered pair inside narrative

UNMOORED has 17 narrative passages. It is reported and never tested.

## And a fence carried from the archive

A null on `ordering` licenses "no consistent direction" and never "no effect" --
registrar [6216], on this seat's own English case -- because it is a CENTRED
statistic: zero is where a shuffled passage sits, not where nothing happens.
"""

import argparse, csv, collections, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "results", "drift_by_passage.csv")
OUT = os.path.join(HERE, "results", "drift_vs_coding.json")
METRICS = ["mean_drift", "total_drift", "directedness", "ordering", "n_sents"]


def load():
    """Rows carrying EVERY metric this file uses.

    **IT GATED ON `mean_drift` AND THEN READ FIVE COLUMNS.** That was safe only
    while the producer's floor was per-ROW; once `drift_metrics.py` began
    emitting `mean_drift` at n_sents==2 while leaving `total_drift` and
    `directedness` blank -- which it must, they are degenerate there -- 252 rows
    passed the gate and died on `float("")`.

    A consumer must state its OWN requirement rather than inherit a floor from
    the producer, which is the same rule the producer change was making: gate on
    what you read, not on a proxy for it.
    """
    rows, partial = [], 0
    for r in csv.DictReader(open(SRC)):
        if any(not r[m] for m in METRICS):
            partial += not not r["mean_drift"]
            continue
        d = {k: r[k] for k in ("pid", "model", "arm", "pair", "prompt",
                               "narrative_A", "drift_A", "drift_B")}
        for m in METRICS:
            d[m] = float(r[m])
        rows.append(d)
    if partial:
        #: SAY IT. These rows HAVE mean_drift and are excluded anyway because
        #: this file needs the degenerate columns too -- an exclusion nobody
        #: would see from the row count alone.
        print("  %d row(s) have mean_drift but not every metric this file uses"
              " -- excluded here, still present in the CSV" % partial)
    return rows


def contrast(rows, metric, a="HOLDS", b="SHIFTS", draws=2000, seed=20260820):
    """-> dict. Passage-level, cluster-bootstrapped, and per-pair."""
    import numpy as np
    rng = np.random.default_rng(seed)
    from scipy import stats
    A = [r for r in rows if r["drift_A"] == a]
    B = [r for r in rows if r["drift_A"] == b]
    if len(A) < 20 or len(B) < 20:
        return dict(metric=metric, n_a=len(A), n_b=len(B), underpowered=True)
    va = np.array([r[metric] for r in A]); vb = np.array([r[metric] for r in B])
    diff = float(vb.mean() - va.mean())
    mw = stats.mannwhitneyu(va, vb)

    #: CLUSTER BOOTSTRAP over lineage pairs. Resamples PAIRS with replacement and
    #: recomputes the difference from whichever passages those pairs carry, so the
    #: interval widens exactly to the extent that passages within a pair agree
    #: with each other more than passages across pairs.
    byp = collections.defaultdict(lambda: ([], []))
    for r in A: byp[r["pair"]][0].append(r[metric])
    for r in B: byp[r["pair"]][1].append(r[metric])
    pairs = [p for p, (x, y) in byp.items() if x and y]
    boot = []
    for _ in range(draws):
        take = rng.choice(len(pairs), len(pairs), replace=True)
        xs = [v for i in take for v in byp[pairs[i]][0]]
        ys = [v for i in take for v in byp[pairs[i]][1]]
        if xs and ys:
            boot.append(np.mean(ys) - np.mean(xs))
    lo, hi = (float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))
              ) if boot else (float("nan"), float("nan"))

    #: PER-PAIR: the contrast inside each lineage, then a sign test across them.
    per = [float(np.mean(byp[p][1]) - np.mean(byp[p][0])) for p in pairs
           if len(byp[p][0]) >= 5 and len(byp[p][1]) >= 5]
    up = sum(1 for x in per if x > 0)
    sp = stats.binomtest(max(up, len(per) - up), len(per), 0.5).pvalue if per else float("nan")
    return dict(metric=metric, a=a, b=b, n_a=len(A), n_b=len(B),
                mean_a=float(va.mean()), mean_b=float(vb.mean()), diff=diff,
                mw_p=float(mw.pvalue), n_pairs=len(pairs),
                boot_lo=lo, boot_hi=hi, boot_excludes_zero=bool(lo > 0 or hi < 0),
                per_pair_n=len(per), per_pair_up=up, per_pair_p=float(sp),
                per_pair_median=float(np.median(per)) if per else float("nan"))


def show(title, rows, draws):
    print("\n%s  (n=%d passages)" % (title, len(rows)))
    print("  %-13s %8s %8s %8s %10s | %13s %6s | %11s %8s"
          % ("metric", "HOLDS", "SHIFTS", "diff", "mw p",
             "boot 95% CI", "excl0", "per-pair", "sign p"))
    out = []
    for m in ("mean_drift", "total_drift", "directedness", "ordering", "n_sents"):
        c = contrast(rows, m, draws=draws)
        out.append(c)
        if c.get("underpowered"):
            print("  %-13s underpowered (%d vs %d)" % (m, c["n_a"], c["n_b"]))
            continue
        print("  %-13s %8.4f %8.4f %+8.4f %10.1e | %+6.4f %+6.4f %6s | %4d/%-4d %8.3g"
              % (m, c["mean_a"], c["mean_b"], c["diff"], c["mw_p"],
                 c["boot_lo"], c["boot_hi"], "yes" if c["boot_excludes_zero"] else "NO",
                 c["per_pair_up"], c["per_pair_n"], c["per_pair_p"]))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", type=int, default=2000)
    a = ap.parse_args(argv)
    rows = load()
    nar = [r for r in rows if r["narrative_A"] == "True"]
    print("scored passages: %d | narrative: %d | lineage pairs: %d"
          % (len(rows), len(nar), len({r["pair"] for r in rows})))
    print("HOLDS vs SHIFTS throughout. UNMOORED has 17 narrative passages and is")
    print("reported in drift_by_passage.csv, never tested here.")

    res = {}
    res["narrative"] = show("WITHIN NARRATIVE", nar, a.draws)
    res["not_narrative"] = show("WITHIN NON-NARRATIVE",
                                [r for r in rows if r["narrative_A"] == "False"], a.draws)
    for arm in ("base", "aligned"):
        res["narrative_" + arm] = show("WITHIN NARRATIVE, %s arm" % arm.upper(),
                                       [r for r in nar if r["arm"] == arm], a.draws)
    agree = [r for r in nar if r["drift_B"] and r["drift_B"] == r["drift_A"]]
    res["narrative_both_coders_agree"] = show(
        "WITHIN NARRATIVE, BOTH CODERS AGREE (a purity filter -- should SHARPEN)",
        agree, a.draws)

    json.dump(dict(_what="geometric drift against the blind coded judgment; "
                         "passage-level, cluster-bootstrapped over lineage pairs, "
                         "and per-pair", results=res),
              open(OUT, "w"), indent=1)
    print("\n-> results/drift_vs_coding.json")


if __name__ == "__main__":
    main()
