"""WHICH junk eludes a lexical detector? Read the misses, do not just score them.

The README established a ceiling (~0.73 AUC) and attributed it to the LABEL.
That attribution is a claim about the errors, and it was made without reading
them. This file reads them.

The question is not "what is the AUC" -- it is: of the passages two coders agreed
are junk, which ones does a lexical model score as clean, and do they look junk
to a human eye? If they do, the features are blind and there is headroom. If they
do not, the label is noisy at the boundary and the ceiling is real.

    python -u passA_errors.py                 # AUC, subtype table, the misses
    python -u passA_errors.py --show 25       # more misses
    python -u passA_errors.py --fp            # false positives instead

GROUND TRUTH
    880 Pass A items, double-coded on lexical/semantic/frame/repetition.
    JUNK = lexical in (mangled, nonwords) OR semantic == salad, kept only where
    BOTH CODERS AGREE on that derived binary: 814 items, 31.4% junk.

    Junk is NOT arm-balanced even though the sample is: base 146/406 = 36.0%,
    aligned 110/408 = 27.0%. The sample balance is what the README asserted; the
    rate is a different quantity and it differs by 9 points.

SCORES ARE OUT-OF-FOLD. A model scoring its own training data would rank its
memorised junk first and report the blindness as coverage.
"""

import argparse, collections, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
PASSA = os.path.join(REPO, "experiments", "passage_analysis",
                     "interiority_in_passages", "results")


def load():
    """-> (ids, texts, y, meta) on the coder-agreed subset."""
    k = json.load(open(os.path.join(PASSA, "passA_key.json")))
    c = json.load(open(os.path.join(PASSA, "passA_codings.json")))
    A, B = c["A"], c["B"]

    def junk(d):
        return bool(d.get("lexical") in ("mangled", "nonwords")
                    or d.get("semantic") == "salad")

    ids, texts, y, meta = [], [], [], []
    for i in sorted(k):
        if i not in A or i not in B or junk(A[i]) != junk(B[i]):
            continue
        ids.append(i)
        texts.append(k[i].get("text") or "")
        y.append(int(junk(A[i])))
        meta.append(dict(k[i], A=A[i], B=B[i]))
    return ids, texts, y, meta


def subtype(m):
    """Which coding made this item junk. Both coders agreed on the BINARY, not
    necessarily on the route, so the route is reported as A's unless A is clean."""
    for d in (m["A"], m["B"]):
        if d.get("lexical") in ("mangled", "nonwords"):
            return d["lexical"]
        if d.get("semantic") == "salad":
            return "salad"
    return "clean"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", type=int, default=12)
    ap.add_argument("--fp", action="store_true", help="false positives instead")
    ap.add_argument("--chars", type=int, default=700)
    a = ap.parse_args(argv)

    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import StratifiedKFold
    from sklearn.pipeline import make_pipeline
    from sklearn.metrics import roc_auc_score

    ids, texts, y, meta = load()
    y = np.array(y)
    print("%d coder-agreed items, %d junk (%.1f%%)" % (len(y), y.sum(), 100 * y.mean()))

    #: char n-grams, not word: the corpus is part Chinese and word tokenisation
    #: would discard the script where mangling is most visible.
    pipe = make_pipeline(
        TfidfVectorizer(analyzer="char", ngram_range=(1, 4), min_df=2,
                        sublinear_tf=True, max_features=200000),
        LogisticRegression(max_iter=2000, C=1.0, class_weight="balanced"))

    oof = np.zeros(len(y), float)
    for tr, te in StratifiedKFold(5, shuffle=True, random_state=0).split(texts, y):
        pipe.fit([texts[i] for i in tr], y[tr])
        oof[te] = pipe.predict_proba([texts[i] for i in te])[:, 1]
    print("out-of-fold AUC, char 1-4: %.3f" % roc_auc_score(y, oof))

    #: WHICH KIND of junk is being missed. Mean out-of-fold score per subtype,
    #: against the clean mean, is the whole question in one table.
    print()
    print("MEAN OUT-OF-FOLD SCORE BY SUBTYPE  (clean should sit low, junk high)")
    by = collections.defaultdict(list)
    for i, m in enumerate(meta):
        by[subtype(m) if y[i] else "clean"].append(oof[i])
    for st in ("clean", "mangled", "nonwords", "salad"):
        v = by.get(st, [])
        if not v:
            continue
        miss = sum(1 for x in v if x < 0.5)
        print("  %-9s n=%4d  mean %.3f  median %.3f  scored<0.5: %d (%.0f%%)"
              % (st, len(v), float(np.mean(v)), float(np.median(v)), miss,
                 100 * miss / len(v)))

    #: and by arm, because the junk RATE differs by arm and a detector that
    #: works on one arm only would be worse than none.
    print()
    print("AUC WITHIN ARM  (a detector must work on both)")
    for arm in ("base", "aligned"):
        sel = [i for i, m in enumerate(meta) if m.get("arm") == arm]
        yy = y[sel]
        if 0 < yy.sum() < len(yy):
            print("  %-8s n=%3d  junk %3d  AUC %.3f"
                  % (arm, len(sel), int(yy.sum()), roc_auc_score(yy, oof[sel])))

    want = 0 if a.fp else 1
    lab = "FALSE POSITIVES -- clean, scored as junk" if a.fp else \
          "THE JUNK THAT ELUDES US -- coder-agreed junk, scored CLEAN"
    order = [i for i in np.argsort(-oof if a.fp else oof) if y[i] == want]
    print()
    print("=" * 78)
    print(lab)
    print("=" * 78)
    for i in order[:a.show]:
        m = meta[i]
        print()
        print("  %s  score %.3f  %-8s %s" % (ids[i], oof[i], m.get("arm"),
                                             m.get("model", "")[:44]))
        print("  subtype %s | A lexical=%s semantic=%s | B lexical=%s semantic=%s"
              % (subtype(m), m["A"].get("lexical"), m["A"].get("semantic"),
                 m["B"].get("lexical"), m["B"].get("semantic")))
        for who in ("A", "B"):
            n = (m[who].get("note") or "").strip()
            if n:
                print("  note %s: %s" % (who, n[:150]))
        print("  PROMPT: %r" % (m.get("prompt") or "")[:80])
        t = (m.get("text") or "").replace("\n", " / ")
        print("  TEXT:   %s" % t[:a.chars])
    return 0


if __name__ == "__main__":
    sys.exit(main())
