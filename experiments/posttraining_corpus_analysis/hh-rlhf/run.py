#!/usr/bin/env python
"""hh-rlhf — is preference lexically predictable? Registered at `889fbe7`.

    python run.py                 -> results/by_arm.csv, top_features.csv

**No model, no cells, no boundary rule.** This reads text out of the HuggingFace
dataset cache. It was written while every cell-based experiment waited on the v4
rebuild, which is the reason the subject exists.

## THE UNIT IS THE PAIR AND POOLING IS WRONG, NOT WEAKER

Both columns carry the entire dialogue — shared prefix is a median 74.4% of the
chosen text — so a model on raw text learns the PROMPT DISTRIBUTION and scores
well while measuring nothing about preference. The within-pair difference cancels
the shared prefix exactly, because a word appearing equally in both contributes
zero to `count(chosen) - count(rejected)`.

## SIGN RANDOMISATION IS WHAT MAKES 0.5 A TRUE NULL

Every pair is (chosen, rejected) in that order, so `y` would be constant 1 and a
model could score perfectly by predicting the constant. Half the pairs are
presented REVERSED with `y=0`, so the model must find a lexical asymmetry rather
than a bias. Seeded, because an unseeded coin makes the run unreproducible.

## LENGTH RUNS THE OPPOSITE WAY TO THE OBVIOUS GUESS

Chosen is SHORTER — median −21 chars, longer in only 42.1% of pairs. So
"shorter wins" is real, available, and not lexical. **Four numbers are reported
and no single one is the answer:**

    length ONLY      the confound's own AUC. If this is high, read everything
                     else against it.
    words            the headline, and not interpretable alone
    words + length   if this is no better than length alone, the words add nothing
    length-matched   words only, on pairs whose length difference is near zero

**If the words-AUC collapses to chance once length is matched, the signal is
length. That is the result, not a failed run.**
"""
import csv, glob, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")
CACHE = os.path.expanduser("~/.cache/huggingface/datasets/Anthropic___hh-rlhf")

#: Identified BY CONTENT, not by matching row counts against a dataset card:
#: harm-word rate in the opening turn is 18.1% against 1.3%.
ARMS = {"harmless-base": "default-52e03caf22ec705f",
        "helpful-base":  "default-cfba128a0ab1b99f"}

SEED = 20260817
TOKEN = re.compile(r"[a-z']+")


def load(cfg, split):
    import pyarrow as pa, pyarrow.ipc as ipc
    f = sorted(glob.glob(os.path.join(CACHE, cfg, "**", "*%s*.arrow" % split),
                         recursive=True))
    if not f:
        raise SystemExit("no %s file for %s" % (split, cfg))
    with pa.memory_map(f[0]) as src:
        t = ipc.open_stream(src).read_all()
    d = t.to_pydict()
    return d["chosen"], d["rejected"]


def divergent(c, r):
    """The text AFTER the shared prefix, both sides.

    Not strictly necessary — the count difference cancels shared words anyway —
    but it bounds the vocabulary to what actually differs and makes the
    top-feature table readable. The prefix is character-level, so this can cut
    mid-word; both sides are cut at the same index, so the asymmetry it could
    introduce is identical on both and cancels in the difference.
    """
    i, m = 0, min(len(c), len(r))
    while i < m and c[i] == r[i]:
        i += 1
    return c[i:], r[i:]


def build(pairs, vocab=None, min_df=20):
    from sklearn.feature_extraction.text import CountVectorizer
    import numpy as np, scipy.sparse as sp
    C = [divergent(c, r)[0] for c, r in pairs]
    R = [divergent(c, r)[1] for c, r in pairs]
    if vocab is None:
        v = CountVectorizer(lowercase=True, token_pattern=TOKEN.pattern,
                            min_df=min_df)
        v.fit(C + R)
    else:
        v = vocab
    X = (v.transform(C) - v.transform(R)).tocsr()
    #: Length in the SAME units the features are in — a word count, not
    #: characters — so the covariate and the vocabulary are commensurable.
    L = np.asarray([[len(TOKEN.findall(a.lower())) - len(TOKEN.findall(b.lower()))]
                    for a, b in zip(C, R)], dtype=float)
    return X, L, v


def randomise(X, L, seed=SEED):
    """Flip half the rows and label them 0. Without this, y is constant."""
    import numpy as np, scipy.sparse as sp
    rng = np.random.default_rng(seed)
    y = rng.integers(0, 2, X.shape[0])
    s = np.where(y == 1, 1.0, -1.0)
    return sp.diags(s) @ X, L * s[:, None], y


def auc(Xtr, ytr, Xte, yte):
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    m = LogisticRegression(max_iter=2000, C=1.0, solver="liblinear")
    m.fit(Xtr, ytr)
    return roc_auc_score(yte, m.decision_function(Xte)), m


def main():
    import numpy as np, scipy.sparse as sp
    os.makedirs(RESULTS, exist_ok=True)
    rows, feats = [], []
    for arm, cfg in ARMS.items():
        out = {"arm": arm, "config": cfg}
        tr = list(zip(*load(cfg, "train")))
        te = list(zip(*load(cfg, "test")))
        Xtr, Ltr, v = build(tr)
        Xte, Lte, _ = build(te, vocab=v)
        Xtr, Ltr, ytr = randomise(Xtr, Ltr)
        Xte, Lte, yte = randomise(Xte, Lte, seed=SEED + 1)
        out.update(n_train=Xtr.shape[0], n_test=Xte.shape[0], vocab=Xtr.shape[1])

        out["auc_length_only"], _ = auc(Ltr, ytr, Lte, yte)
        out["auc_words"], m = auc(Xtr, ytr, Xte, yte)
        out["auc_words_length"], _ = auc(sp.hstack([Xtr, sp.csr_matrix(Ltr)]).tocsr(),
                                         ytr,
                                         sp.hstack([Xte, sp.csr_matrix(Lte)]).tocsr(),
                                         yte)
        #: LENGTH-MATCHED: pairs whose word-count difference is within 5. The
        #: threshold is declared here rather than tuned; a sweep over it would
        #: be choosing the number that gives the answer.
        k = np.abs(Ltr[:, 0]) <= 5
        j = np.abs(Lte[:, 0]) <= 5
        out["n_matched_train"], out["n_matched_test"] = int(k.sum()), int(j.sum())
        out["auc_words_lenmatched"] = (auc(Xtr[k], ytr[k], Xte[j], yte[j])[0]
                                       if k.sum() > 500 and j.sum() > 100 else None)
        rows.append(out)

        names = v.get_feature_names_out()
        w = m.coef_[0]
        for i in np.argsort(w)[-25:][::-1]:
            feats.append({"arm": arm, "side": "chosen", "word": names[i],
                          "weight": round(float(w[i]), 4)})
        for i in np.argsort(w)[:25]:
            feats.append({"arm": arm, "side": "rejected", "word": names[i],
                          "weight": round(float(w[i]), 4)})
        print("%-14s n=%d vocab=%d | length %.3f | words %.3f | w+l %.3f | matched %s"
              % (arm, out["n_test"], out["vocab"], out["auc_length_only"],
                 out["auc_words"], out["auc_words_length"],
                 ("%.3f" % out["auc_words_lenmatched"])
                 if out["auc_words_lenmatched"] else "n/a"))

    for name, data in (("by_arm.csv", rows), ("top_features.csv", feats)):
        with open(os.path.join(RESULTS, name), "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(data[0].keys()))
            w.writeheader()
            for d in data:
                w.writerow(d)
    if len(rows) == 2:
        g = rows[0]["auc_words"] - rows[1]["auc_words"]
        print("\nharmless - helpful, words AUC: %+.3f  (registered threshold 0.05)" % g)
    print("  ->", RESULTS)


if __name__ == "__main__":
    main()
