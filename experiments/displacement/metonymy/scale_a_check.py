"""Why scale A is null: its two runs named opposite axes. -> results/scale_a_check.md

    python scale_a_check.py

A is the open dimension named WITHOUT the sentences. `run.py` negates it with
the other ported scales, which assumes 100 = against the skin. The two runs did
not share an axis (dimension names from `malign-logits/meta/M01_displacement/
results/x_coders/A_{opus,sonnet}.json`):

    A_opus    "Layering depth"                 100 = outermost, removed first
    A_sonnet  "how much of the body it covers" 100 = full-length garment

So this correlates each RAW run, un-negated, against the median delta, on the
same word set and carrier floor as `run.py` (words_D.csv, >= 10 carriers), and
against the ported scales on the words all five share. Descriptive; nothing
here was declared.
"""
import csv
import os

from scipy.stats import spearmanr

HERE = os.path.dirname(os.path.abspath(__file__))
MIN_CARRIERS = 10
PORTED = ("A", "B", "Cexp", "Ccharge", "D")


def load(name):
    return {r["word"]: r for r in csv.DictReader(open(os.path.join(HERE, "data", "scale_%s.csv" % name)))
            if r["mean"]}


def col(S, w, c):
    v = S.get(w, {}).get(c)
    return float(v) if v else None


def rho(xs, ys):
    pairs = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
    r, p = spearmanr([a for a, _ in pairs], [b for _, b in pairs])
    return len(pairs), r, p


def main():
    S = {n: load(n) for n in PORTED}
    words = list(csv.DictReader(open(os.path.join(HERE, "results", "words_D.csv"))))
    L = ["# Scale A: two runs, two axes", "",
         "Producer `scale_a_check.py`. Raw (un-negated) scores; median per-lineage delta from `results/words_D.csv`, "
         ">= %d carriers. Spearman." % MIN_CARRIERS, "",
         "## Each run against the deltas", "",
         "| column | frame | n | rho | p |", "|---|---|---|---|---|"]
    for tag in ("her", "his"):
        d = {r["word"]: float(r["median_delta_pp"]) for r in words
             if (" %s" % tag) in r["prompt"] and int(r["n_carriers"]) >= MIN_CARRIERS}
        for name, c in (("A", "A_opus"), ("A", "A_sonnet"), ("A", "mean"), ("B", "mean"), ("D", "mean")):
            w = sorted(d)
            n, r, p = rho([col(S[name], x, c) for x in w], [d[x] for x in w])
            L.append("| %s %s | %s | %d | %+.3f | %.2g |" % (name, c, tag, n, r, p))
    shared = sorted(set.intersection(*[set(v) for v in S.values()]))
    L += ["", "## Each run against the other scales, on the %d words all five ported scales share" % len(shared), "",
          "| column | vs A other run | vs B | vs Cexp | vs Ccharge | vs D |", "|---|---|---|---|---|---|"]
    for c, other in (("A_opus", "A_sonnet"), ("A_sonnet", "A_opus")):
        cells = ["%+.3f" % rho([col(S["A"], x, c) for x in shared], [col(S["A"], x, other) for x in shared])[1]]
        cells += ["%+.3f" % rho([col(S["A"], x, c) for x in shared], [col(S[n], x, "mean") for x in shared])[1]
                  for n in PORTED[1:]]
        L.append("| %s | %s |" % (c, " | ".join(cells)))
    L += ["", "Ported scales B-D run 0 = off the body to 100 = against the skin; `run.py` negates them to `out`. "
          "A_opus runs the other way (100 = outermost), so a positive raw rho with the deltas is the PREDICTED "
          "direction for A_opus and the opposite for B and D."]
    out = os.path.join(HERE, "results", "scale_a_check.md")
    open(out, "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
