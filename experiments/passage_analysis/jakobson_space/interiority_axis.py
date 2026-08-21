"""Does interiority reduce drift and surprisal? `degree` against both axes.

    python .../interiority_axis.py
    python .../interiority_axis.py --min-per-model 20

RH's hypothesis, 2026-08-21: **interiority reduces drift and surprisal.**

`degree` is the blind coding from `../interiority_in_passages` (rubric
`plans/passC_rubric.md`), 0-3, "how much of the passage is given over to a
character's mind": 0 only external event, 3 substantially about a mind. It rides
on the ref_pool rows as `degree_A`, so this is a join and not a new coding run.

## THE POOLED CORRELATION IS CONFOUNDED BY ARM AND MUST NOT BE THE ANSWER

Alignment RAISES interiority -- mean degree 1.799 base against 1.940 aligned --
and alignment LOWERS both axes. So any pooled correlation between `degree` and
drift or surprisal contains the arm effect, and would be partly manufactured
whatever the within-model truth is. Both are printed and the pooled one is
labelled, because the gap between them IS the confound, made visible rather than
argued about.

## THE DESIGN: WITHIN MODEL, THEN THE LINEAGE IS THE UNIT

One Spearman per model, over that model's own passages -- so every model-level
difference, arm included, is removed by construction. 53 of 54 models carry at
least three distinct degree levels, so the within-model variance exists.

Then children are averaged into their base's lineage and the sign test runs over
lineages, because models within a lineage share a base and are not independent.
The test asks whether the within-model relation is consistently negative, not
whether one big pooled correlation is.

## SPEARMAN, BECAUSE `degree` IS ORDINAL AND CLUMPED

0-3 with 56% of passages at 2. A Pearson on that is a correlation with an
interval assumption nobody made; ranks with ties averaged carry what the rubric
actually claims, which is an ordering.

## THE LENGTH CONTROL, BECAUSE IT RUNS THE SAME WAY AS THE FINDING

Interior passages have slightly FEWER sentences (within-model spearman -0.0518,
36 of 51 models negative) and passages with more sentences drift slightly MORE
(+0.0439). Both push `degree ~ drift` negative on their own, which is the
direction of the result -- so length is a live alternative explanation and not a
box to tick. The partial correlation holding `n_sents` out is reported beside the
raw one: **-0.2062 against -0.2207, 51 of 51 models negative.** The relation is
not length.

## THE TWO-WAY CHECK

`--twoway` removes the model mean AND the stem mean from both variables before
correlating (an additive two-way demeaning), then reports one pooled figure on
the residuals. Cells are too thin for a true within-cell correlation -- median 2
passages per (model, stem) -- so this is the available way to hold the SCENE as
well as the model, and it is a check on the main design rather than a
replacement for it.
"""

import argparse, collections, csv, json, math, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data"))
SRC = os.path.join(HERE, "results", "quadrants.csv")
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))


def ranks(v):
    """Average ranks, ties shared -- what Spearman needs."""
    order = sorted(range(len(v)), key=lambda i: v[i])
    out = [0.0] * len(v)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
            j += 1
        r = (i + j) / 2.0 + 1
        for k in range(i, j + 1):
            out[order[k]] = r
        i = j + 1
    return out


def pearson(x, y):
    n = len(x)
    if n < 3:
        return None
    mx, my = sum(x) / n, sum(y) / n
    sx = math.sqrt(sum((v - mx) ** 2 for v in x))
    sy = math.sqrt(sum((v - my) ** 2 for v in y))
    if sx == 0 or sy == 0:
        return None
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy)


def spearman(x, y):
    return pearson(ranks(x), ranks(y))


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
    ap.add_argument("--min-per-model", type=int, default=15)
    ap.add_argument("--twoway", action="store_true", default=True)
    a = ap.parse_args(argv)
    from malignment import roster

    csv.field_size_limit(10 ** 7)
    deg = {}
    for line in open(os.path.join(DATA, "ref_pool", "ref_pool.jsonl")):
        j = json.loads(line)
        if j.get("degree_A") not in (None, ""):
            deg[j["id"]] = int(j["degree_A"])
    #: `n_sents` lives on two_axes.csv, not quadrants.csv, and the length
    #: control needs it -- joined here rather than recomputed from the text.
    ns = {}
    for r in csv.DictReader(open(os.path.join(HERE, "results", "two_axes.csv"))):
        if r.get("n_sents"):
            ns[r["id"]] = float(r["n_sents"])
    rows = [r for r in csv.DictReader(open(a.src, newline=""))
            if r["id"] in deg and r["id"] in ns]
    for r in rows:
        r["degree"] = deg[r["id"]]
        r["n_sents"] = ns[r["id"]]
    print("passages with a degree code: %s over %d models"
          % ("{:,}".format(len(rows)), len({r["model"] for r in rows})))
    print("  degree distribution: %s"
          % dict(sorted(collections.Counter(r["degree"] for r in rows).items())))

    #: ---- descriptive: the shape, per arm, so a monotone claim is visible
    print("\nMEDIAN BY DEGREE, WITHIN ARM  (descriptive; the arm is held, the model is not)")
    print("%-9s %8s %9s %9s %9s %9s" % ("arm", "degree", "n", "surprisal", "drift", ""))
    for arm in ("base", "aligned"):
        for g in range(4):
            v = [r for r in rows if r["category"] == arm and r["degree"] == g]
            if len(v) < 5:
                continue
            print("%-9s %8d %9s %9.4f %9.4f"
                  % (arm, g, "{:,}".format(len(v)),
                     statistics.median(float(x["surprisal"]) for x in v),
                     statistics.median(float(x["drift"]) for x in v)))

    #: ---- POOLED, and labelled as confounded
    print("\nPOOLED over all %s passages  <-- CONFOUNDED BY ARM, shown for contrast"
          % "{:,}".format(len(rows)))
    for lab, key in (("surprisal", "surprisal"), ("drift", "drift")):
        rho = spearman([r["degree"] for r in rows], [float(r[key]) for r in rows])
        print("  spearman(degree, %-9s) = %+.4f" % (lab, rho))

    #: ---- WITHIN MODEL, lineage as the unit
    per = collections.defaultdict(list)
    for r in rows:
        per[r["model"]].append(r)
    rho = {}
    for m, v in per.items():
        if len(v) < a.min_per_model:
            continue
        g = [x["degree"] for x in v]
        d = [float(x["drift"]) for x in v]
        n = [float(x["n_sents"]) for x in v]
        rgd, rgn, rdn = spearman(g, d), spearman(g, n), spearman(d, n)
        part = None
        if None not in (rgd, rgn, rdn):
            den = math.sqrt((1 - rgn ** 2) * (1 - rdn ** 2))
            part = (rgd - rgn * rdn) / den if den else None
        rho[m] = (spearman(g, [float(x["surprisal"]) for x in v]), rgd, part, len(v))
    rho = {m: v for m, v in rho.items() if v[0] is not None and v[1] is not None}

    lin = roster.lineages()
    lrows = []
    for base, members in sorted(lin.items()):
        have = [m for m in members if m in rho]
        if not have:
            continue
        pv = [rho[m][2] for m in have if rho[m][2] is not None]
        lrows.append((base,
                      statistics.mean(rho[m][0] for m in have),
                      statistics.mean(rho[m][1] for m in have),
                      statistics.mean(pv) if pv else None))
    print("\nWITHIN MODEL, then the LINEAGE is the unit  (%d models -> %d lineages)"
          % (len(rho), len(lrows)))
    print("%-34s %9s %5s %5s %11s" % ("", "median", "neg", "pos", "p"))
    for lab, i in (("spearman(degree, surprisal)", 1), ("spearman(degree, drift)", 2),
                   ("  the same, holding n_sents out", 3)):
        vals = [x[i] for x in lrows if x[i] is not None]
        n, up, dn, med, p = sign_test(vals)
        print("%-34s %+9.4f %5d %5d %11.3g" % (lab, med, dn, up, p))

    #: same, split by arm -- a relation present in one arm only is a different
    #: claim from one present in both, and pooling the two would hide it.
    print("\nthe same, per arm (models, not lineages -- an arm has no pairing)")
    print("%-34s %6s %9s %5s %5s %11s" % ("", "models", "median", "neg", "pos", "p"))
    al, ba = roster.population("aligned"), roster.population("bases")
    for arm, s in (("base", ba), ("aligned", al)):
        sub = [m for m in rho if m in s]
        for lab, i in (("spearman(degree, surprisal)", 0), ("spearman(degree, drift)", 1)):
            n, up, dn, med, p = sign_test([rho[m][i] for m in sub])
            print("%-34s %6d %+9.4f %5d %5d %11.3g"
                  % ("%-8s %s" % (arm, lab.split("(")[1][:-1].split(", ")[1]),
                     len(sub), med, dn, up, p))

    if a.twoway:
        #: remove the model mean AND the stem mean from every variable, then
        #: correlate the residuals. Holds the scene as well as the model, which
        #: the thin (model, stem) cells cannot do directly.
        def demean(vals, keys):
            m = collections.defaultdict(list)
            for k, v in zip(keys, vals):
                m[k].append(v)
            mu = {k: sum(v) / len(v) for k, v in m.items()}
            return [v - mu[k] for k, v in zip(keys, vals)]

        mk = [r["model"] for r in rows]
        sk = [r["prompt"] for r in rows]
        out = ["\nTWO-WAY DEMEANED (model mean and stem mean removed from each "
               "variable)"]
        for lab, key in (("surprisal", "surprisal"), ("drift", "drift")):
            g = demean(demean([float(r["degree"]) for r in rows], mk), sk)
            y = demean(demean([float(r[key]) for r in rows], mk), sk)
            out.append("  pearson(degree, %-9s | model, stem) = %+.4f"
                       % (lab, pearson(g, y)))
        print("\n".join(out))
        print("  (pearson, not spearman: demeaning has already made these "
              "continuous residuals,\n   and ranking a residual would discard "
              "the centring that is the point)")


if __name__ == "__main__":
    main()
