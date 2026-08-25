"""P's question, conditioned on dose: held out by WORD, low-dose against high-dose.

    python -u analyse.py --lang en
    python -u analyse.py --lang en --min-cells 12 --folds 5

Fits on the named norms to predict a word's DIRECTION (+1 riser / -1 faller), holding
out by word, separately in a low-dose and a high-dose stratum, **on the same words**.

## THE PRIMARY TEST, AND THE CONTROL THAT MAKES IT MEAN ANYTHING

Dose is confounded with vocabulary: high-dose prompts contain different words, so a
naive low-vs-high comparison measures "are transgressive words easier to predict"
rather than "does a loaded frame help". Only the second is Findings P's question.

So a word enters only if it has `--min-cells` moving cells on BOTH sides of the dose
split, the word set is then FIXED, and only the dose varies. Any AUC difference is
attributable to the frame rather than to which words were in it.

The unrestricted comparison is printed too, labelled, because it answers the
vocabulary question and must not be read as answering P's.

## HELD OUT BY WORD, WHICH IS THE WHOLE POINT

GroupKFold on `word`: no word appears in both the fitting and the evaluation fold.
Without it a model memorises "the word `strangle` falls" and reports it as the norms
having predicted something, which is exactly the failure P's design exists to prevent.
The features are constant within a word, so a word-level leak is total.

## THE BENCHMARK IS REACHABLE AND SCORED BY THE SAME RULE

`emp_word` -- a word's own majority direction estimated on its OTHER cells within
the stratum -- is what a perfect word-level theory could achieve here, and it is
scored by the identical function the models are. **Never compare to 1.0 and never to
a ceiling fitted on the target**; that defect cost this campaign a day and is
documented in displacement_axis/README.md.

`p_base` alone is carried as the floor, because P's headroom is measured OVER base
probability rather than over chance.

## WHAT IS EXPLORATORY

The primary test is the shared-word conditional AUC. Per-language splits, per-norm
contributions, and which scales carry any conditioning are EXPLORATORY -- candidates
for a hypothesis, not results -- and are printed under that heading.
"""

import argparse, collections, gzip, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
DATA = os.path.expanduser("~/malignment-data/named_under_dose")

DROP = {"lineage", "prompt", "word", "lang", "dose", "direction",
        "p_base", "p_aligned", "k_coverage", "brysbaert_coverage",
        "warriner_coverage", "n_tokens", "n_content",
        "concreteness_zh_coverage", "n_words"}


def auc(y, s):
    """P(score of a +1 case > score of a -1 case), ties half. Chance 0.5."""
    pos = [x for x, t in zip(s, y) if t > 0]
    neg = [x for x, t in zip(s, y) if t < 0]
    if not pos or not neg:
        return None
    allv = sorted(pos + neg)
    rank = {}
    i = 0
    while i < len(allv):
        j = i
        while j + 1 < len(allv) and allv[j + 1] == allv[i]:
            j += 1
        r = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            rank[allv[k]] = r
        i = j + 1
    rp = sum(rank[x] for x in pos)
    return (rp - len(pos) * (len(pos) + 1) / 2.0) / (len(pos) * len(neg))


def load(lang, want=None):
    #: PER-LANGUAGE FILE FIRST. en and zh carry different norm sets, so a shared
    #: file silently blanks one language's columns; see run.py's note.
    p = os.path.join(DATA, "cells_%s.csv.gz" % lang)
    if not os.path.exists(p):
        p = os.path.join(DATA, "cells.csv.gz")
    if not os.path.exists(p):
        sys.exit("no cells file in %s -- run run.py first" % DATA)
    rows = []
    with gzip.open(p, "rt", encoding="utf-8") as fh:
        head = fh.readline().rstrip("\n").split("\t")
        ix = {k: i for i, k in enumerate(head)}
        feats = [k for k in head if k not in DROP]
        if want == "k":
            feats = [k for k in feats if k.startswith("k_")]
        elif want:
            keep = {x.strip() for x in want.split(",")}
            feats = [k for k in feats if k in keep]
        if not feats:
            sys.exit("no features left after --features %s" % want)
        for line in fh:
            v = line.rstrip("\n").split("\t")
            if len(v) != len(head):
                continue
            if v[ix["lang"]] != lang:
                continue
            try:
                d = float(v[ix["dose"]])
                y = int(v[ix["direction"]])
                pb = float(v[ix["p_base"]])
            except ValueError:
                continue
            x = []
            ok = True
            for k in feats:
                s = v[ix[k]]
                if s == "":
                    ok = False
                    break
                try:
                    x.append(float(s))
                except ValueError:
                    ok = False
                    break
            if not ok:
                continue
            rows.append((v[ix["word"]], d, y, pb, x))
    return rows, feats


def fit_eval(rows, feats, folds, seed=20260825):
    """GroupKFold on word. -> {model: auc} over the pooled held-out predictions."""
    import numpy as np
    words = sorted({r[0] for r in rows})
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(words))
    fold_of = {words[order[i]]: i % folds for i in range(len(words))}

    X = np.array([r[4] for r in rows], float)
    y = np.array([r[2] for r in rows], float)
    pb = np.array([r[3] for r in rows], float)
    w = [r[0] for r in rows]
    f = np.array([fold_of[x] for x in w])

    #: a word's majority direction from its OTHER cells -- the reachable benchmark
    by = collections.defaultdict(lambda: [0, 0])
    for wi, yi in zip(w, y):
        by[wi][0] += yi
        by[wi][1] += 1
    emp = np.array([(by[wi][0] - yi) / max(1, by[wi][1] - 1) for wi, yi in zip(w, y)])

    out = {}
    preds = {k: np.zeros(len(y)) for k in ("named", "named_p", "logp")}
    for k in range(folds):
        tr, te = f != k, f == k
        if tr.sum() < 50 or te.sum() < 20:
            continue
        mu, sd = X[tr].mean(0), X[tr].std(0)
        sd[sd == 0] = 1.0
        Z = (X - mu) / sd
        lp = np.log(np.clip(pb, 1e-12, None)).reshape(-1, 1)
        Zp = np.hstack([Z, (lp - lp[tr].mean()) / (lp[tr].std() or 1.0)])
        for name, M in (("named", Z), ("named_p", Zp),
                        ("logp", (lp - lp[tr].mean()) / (lp[tr].std() or 1.0))):
            A = np.hstack([M[tr], np.ones((tr.sum(), 1))])
            #: ridge, because 17 correlated norms on a binary target overfit a fold
            beta = np.linalg.solve(A.T @ A + 1.0 * np.eye(A.shape[1]), A.T @ y[tr])
            preds[name][te] = np.hstack([M[te], np.ones((te.sum(), 1))]) @ beta
    for name, v in preds.items():
        out[name] = auc(y, v)
    out["emp_word"] = auc(y, emp)
    out["_n"] = len(y)
    out["_words"] = len(words)
    out["_pos"] = float((y > 0).mean())
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="en", choices=("en", "zh"))
    ap.add_argument("--min-cells", type=int, default=10,
                    help="moving cells a word needs IN EACH stratum to enter the "
                         "shared-word test")
    ap.add_argument("--folds", type=int, default=5)
    ap.add_argument("--features", default=None,
                    help="comma-separated subset, or 'k' for the k_ratings only. "
                         "'k' is how en is made comparable to zh, which has no "
                         "Warriner or Brysbaert columns at all -- without it a "
                         "cross-language difference is confounded with a 12-vs-7 "
                         "feature-set difference.")
    a = ap.parse_args(argv)

    rows, feats = load(a.lang, a.features)
    if not rows:
        sys.exit("no rows for lang=%s" % a.lang)
    import numpy as np
    dose = np.array([r[1] for r in rows])
    cut = float(np.median(dose))
    print("=" * 92)
    print("P's QUESTION UNDER DOSE  --  lang=%s, %d moving cells, %d words, %d norms"
          % (a.lang, len(rows), len({r[0] for r in rows}), len(feats)))
    print("=" * 92)
    print("  dose = base-arm k_transgressiveness; median split at %.4f" % cut)
    print("  features: %s" % ", ".join(feats))

    lo = [r for r in rows if r[1] <= cut]
    hi = [r for r in rows if r[1] > cut]

    #: THE SHARED-WORD SET -- the control. Without it this measures vocabulary.
    cl = collections.Counter(r[0] for r in lo)
    ch_ = collections.Counter(r[0] for r in hi)
    shared = {w for w in cl if cl[w] >= a.min_cells and ch_[w] >= a.min_cells}
    print("\n  words with >=%d moving cells in BOTH strata: %d" % (a.min_cells, len(shared)))
    if len(shared) < 50:
        print("  TOO FEW for the primary test; lower --min-cells or widen the corpus")

    def block(title, L, H, note=""):
        print("\n" + "-" * 92)
        print("  %s%s" % (title, note))
        print("-" * 92)
        print("  %-12s %10s %10s %10s   %s"
              % ("stratum", "named", "named+p", "log p_base", "emp_word (reachable)"))
        res = {}
        for nm, part in (("LOW dose", L), ("HIGH dose", H)):
            if len(part) < 200:
                print("  %-12s  too few cells (%d)" % (nm, len(part)))
                continue
            r = fit_eval(part, feats, a.folds)
            res[nm] = r
            print("  %-12s %10.4f %10.4f %10.4f   %10.4f      n=%d, %d words, %.0f%% risers"
                  % (nm, r["named"], r["named_p"], r["logp"], r["emp_word"],
                     r["_n"], r["_words"], 100 * r["_pos"]))
        if len(res) == 2:
            l, h = res["LOW dose"], res["HIGH dose"]
            print("\n  HIGH minus LOW      %+9.4f %+9.4f %+9.4f   %+10.4f"
                  % (h["named"] - l["named"], h["named_p"] - l["named_p"],
                     h["logp"] - l["logp"], h["emp_word"] - l["emp_word"]))
            #: P's quantity: the share of the reachable headroom over log p that the
            #: names recover. Computed per stratum so the two are comparable.
            for nm, r in (("LOW", l), ("HIGH", h)):
                head = r["emp_word"] - r["logp"]
                got = r["named_p"] - r["logp"]
                print("  %-5s headroom over log p_base = %+.4f; named recovers %+.4f = %s"
                      % (nm, head, got,
                         ("%.0f%%" % (100 * got / head)) if abs(head) > 1e-6 else "n/a"))
        return res

    if len(shared) >= 50:
        block("PRIMARY -- SAME WORDS IN BOTH STRATA",
              [r for r in lo if r[0] in shared], [r for r in hi if r[0] in shared],
              "  (%d words)" % len(shared))
    block("SECONDARY -- ALL WORDS (answers the VOCABULARY question, not P's)", lo, hi)

    print("\n" + "=" * 92)
    print("  emp_word is the REACHABLE benchmark: a word's majority direction from its")
    print("  own other cells in the same stratum, scored by the identical rule. It is")
    print("  the most a word-level theory can do here. Compare to it, never to 1.0.")
    print("  bge is not run as a rival here -- see README: it is a ceiling on naming.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
