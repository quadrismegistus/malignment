"""Lexical well-formedness features: does the passage contain WORDS?

WHY THIS EXISTS, AND WHAT THE README GOT WRONG

`junk_passages` tried nine surface features -- gzip_ratio, ttr, nonascii,
mean_word_len, top_word_share, long_word_share, alpha_share, digit, bigram_rep --
plus char and word n-grams, topped out near AUC 0.73, and concluded that the
ceiling was THE LABEL.

That conclusion was reached without reading the errors. Read, they are these:

    andclimbed  hewas  herhusband  youGeorgia     a missing space
    wasn,t                                        a comma for an apostrophe
    couldn' refresh                               a broken contraction
    spritit  wel  continuied  screent  arketysh   not words
    W R I T I N G & R E A D I N G                 a letter-spaced running head
    HARPILIA / HARPILER                           one name, two spellings

Every one is lexically obvious, and NOT ONE of the nine features asks whether a
string is a word. The tried set is entirely STATISTICAL. Char n-grams cannot
recover it either: `andclimbed` decomposes into `andc`, `ndcl`, `dcli`, each
individually common -- what is rare is the WORD, an object the representation
never forms.

So the ceiling was never shown to be the label. It was the ceiling of a family of
features that share one blind spot. This file adds the missing sense.

    python -u lexical.py              # per-feature AUC, then combined
    python -u lexical.py --misses     # what still eludes after these

MULTILINGUAL CAVEAT, LOAD-BEARING. Part of this corpus is Chinese, where an
English OOV rate is 1.0 by construction and means nothing. Every rate below is
computed over ASCII-alphabetic tokens only and `ascii_share` is carried
alongside, so a consumer can see when a rate rests on almost no tokens.
"""

import argparse, json, os, re, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
BYU = os.path.join(REPO, "lexicons", "external", "worddb.byu.txt")
WEB2 = "/usr/share/dict/words"

_TOKEN = re.compile(r"[A-Za-z]+(?:['’][A-Za-z]+)?")
_CONTRACT = {"s", "t", "re", "ve", "ll", "d", "m", "n"}


def dictionary():
    """Lowercased word set: BYU's 86k frequency-ranked list plus web2."""
    w = set()
    if os.path.exists(BYU):
        with open(BYU, encoding="utf-8", errors="replace") as fh:
            head = fh.readline().rstrip("\n").split("\t")
            col = head.index("word") if "word" in head else -1
            for line in fh:
                p = line.rstrip("\n").split("\t")
                if col < len(p):
                    t = p[col].strip().lower()
                    if t.isalpha():
                        w.add(t)
    if os.path.exists(WEB2):
        with open(WEB2, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                t = line.strip().lower()
                if t.isalpha():
                    w.add(t)
    return w


DICT = None


def feats(text):
    """-> dict of lexical well-formedness rates. Higher = more malformed."""
    global DICT
    if DICT is None:
        DICT = dictionary()
    t = text or ""
    n_chars = max(len(t), 1)
    toks = _TOKEN.findall(t)
    #: apostrophe forms are stripped to the stem for membership; a contraction
    #: is well-formed and must not read as OOV.
    def known(tok):
        s = tok.lower().replace("’", "'")
        if s in DICT:
            return True
        if "'" in s:
            a, _, b = s.partition("'")
            return (a in DICT or a in ("do", "does", "did", "is", "are", "was",
                                       "were", "have", "has", "had", "can",
                                       "could", "would", "should", "will")) \
                and (b in _CONTRACT or b == "")
        return False

    ascii_alpha = [x for x in toks if len(x) >= 2]
    oov = [x for x in ascii_alpha if not known(x)]
    #: names are the main false-OOV source in fiction, so a capitalised token
    #: that is not sentence-initial is set aside and counted separately rather
    #: than charged as malformation.
    oov_lower = [x for x in oov if not x[0].isupper()]

    #: A FUSED WORD is the sharpest signal here and needs no proper-noun
    #: handling: an OOV string that splits into two dictionary words.
    fused = 0
    for x in oov:
        s = x.lower()
        if len(s) < 6:
            continue
        for i in range(3, len(s) - 2):
            if s[:i] in DICT and s[i:] in DICT:
                fused += 1
                break

    words = t.split()
    single = 0, 0
    run = best = 0
    for w in words:
        if len(w) == 1 and w.isalpha():
            run += 1
            best = max(best, run)
        else:
            run = 0

    #: verbatim repetition of a 5-word window, which is what "'big time' x3" and
    #: a doubled sentence look like from here.
    lw = [w.lower() for w in words]
    g5 = collections.Counter(tuple(lw[i:i + 5]) for i in range(max(len(lw) - 4, 0)))
    rep5 = (max(g5.values()) - 1) / max(len(lw), 1) if g5 else 0.0

    #: THE THREE THE CODER NOTES NAMED, after the first pass left 57% of
    #: `mangled` scoring clean. Each is taken from a note, not invented:
    #: "CN/EN code-switch" (a000), "names mutate HARPILIA/HARPILER" (a827),
    #: "stray verse numbers '5' and '(...) 6 7'" (a196).

    #: 1. mixed script INSIDE one token. Not a code-switch between sentences,
    #: which is ordinary in this corpus, but a word that is half Han half Latin.
    mixed = 0
    for w in words:
        has_cjk = any("一" <= ch <= "鿿" for ch in w)
        has_lat = any(("a" <= ch <= "z") or ("A" <= ch <= "Z") for ch in w)
        if has_cjk and has_lat:
            mixed += 1

    #: 2. NAME MUTATION: two capitalised out-of-dictionary tokens in the same
    #: passage at edit distance 1. One name spelled two ways.
    def ed1(x, y):
        if abs(len(x) - len(y)) > 1:
            return False
        if len(x) == len(y):
            return sum(p != q for p, q in zip(x, y)) == 1
        a2, b2 = (x, y) if len(x) < len(y) else (y, x)
        i = j = 0
        skipped = False
        while i < len(a2) and j < len(b2):
            if a2[i] != b2[j]:
                if skipped:
                    return False
                skipped = True
                j += 1
                continue
            i += 1
            j += 1
        return True

    caps = sorted({w for w in oov if len(w) >= 5 and w[0].isupper()})
    mut = 0
    for i2 in range(len(caps)):
        for j2 in range(i2 + 1, len(caps)):
            if ed1(caps[i2].lower(), caps[j2].lower()):
                mut += 1

    #: 3. STRAY NUMBERING: a bare integer standing as its own token amid prose.
    #: Enumerated lists and verse numbers both land here, which is intended --
    #: both are paratext intruding into a passage that should be continuous.
    stray = sum(1 for w in words if w.strip(".,()[]").isdigit()
                and len(w.strip(".,()[]")) <= 3)

    d = float(max(len(ascii_alpha), 1))
    return dict(
        mixed_script=mixed / max(len(words), 1),
        name_mutation=float(mut),
        stray_number=stray / max(len(words), 1),
        oov_rate=len(oov_lower) / d,
        oov_rate_all=len(oov) / d,
        fused_rate=fused / d,
        comma_in_word=len(re.findall(r"[A-Za-z],[A-Za-z]", t)) * 1000.0 / n_chars,
        apos_break=len(re.findall(r"[A-Za-z][’'](?:\s|$)", t)) * 1000.0 / n_chars,
        spaced_run=float(best),
        rep5=rep5,
        ascii_share=len(ascii_alpha) / max(len(toks) + t.count(" ") / 2.0, 1.0),
    )


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--misses", action="store_true")
    ap.add_argument("--disagree", action="store_true")
    ap.add_argument("--show", type=int, default=8)
    a = ap.parse_args(argv)

    import numpy as np
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import StratifiedKFold
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import make_pipeline
    from sklearn.metrics import roc_auc_score
    sys.path.insert(0, HERE)
    from passA_errors import load, subtype, PASSA

    ids, texts, y, meta = load()
    y = np.array(y)
    print("%d coder-agreed items, %d junk (%.1f%%)" % (len(y), y.sum(), 100 * y.mean()))
    print("building dictionary...", flush=True)
    F = [feats(t) for t in texts]
    names = sorted(F[0])
    X = np.array([[f[n] for n in names] for f in F])
    print("dictionary: %d words" % len(DICT))

    print()
    print("SINGLE FEATURE AUC  (0.5 = chance; below 0.5 = points the other way)")
    for j, n in enumerate(names):
        print("  %-14s %.3f" % (n, roc_auc_score(y, X[:, j])))

    pipe = make_pipeline(StandardScaler(), LogisticRegression(max_iter=4000,
                                                             class_weight="balanced"))
    oof = np.zeros(len(y))
    for tr, te in StratifiedKFold(5, shuffle=True, random_state=0).split(X, y):
        pipe.fit(X[tr], y[tr])
        oof[te] = pipe.predict_proba(X[te])[:, 1]
    print()
    print("COMBINED, out-of-fold AUC: %.3f" % roc_auc_score(y, oof))
    print("  (char 1-4 n-grams on the same split and label: 0.724)")

    #: THE DECISIVE TEST is not lexical-vs-statistical, it is whether the two
    #: are COMPLEMENTARY. Same folds, same label, three feature sets: char
    #: n-grams alone, lexical alone, and their union stacked. If the union does
    #: not beat the better half, the blind spot was real but empty.
    from sklearn.feature_extraction.text import TfidfVectorizer
    from scipy.sparse import hstack, csr_matrix
    vec = TfidfVectorizer(analyzer="char", ngram_range=(1, 4), min_df=2,
                          sublinear_tf=True, max_features=200000)
    sc = StandardScaler()
    oof_c = np.zeros(len(y))
    oof_u = np.zeros(len(y))
    for tr, te in StratifiedKFold(5, shuffle=True, random_state=0).split(X, y):
        Ztr = vec.fit_transform([texts[i] for i in tr])
        Zte = vec.transform([texts[i] for i in te])
        m1 = LogisticRegression(max_iter=4000, class_weight="balanced").fit(Ztr, y[tr])
        oof_c[te] = m1.predict_proba(Zte)[:, 1]
        Ltr = sc.fit_transform(X[tr]); Lte = sc.transform(X[te])
        m2 = LogisticRegression(max_iter=4000, class_weight="balanced").fit(
            hstack([Ztr, csr_matrix(Ltr)]).tocsr(), y[tr])
        oof_u[te] = m2.predict_proba(hstack([Zte, csr_matrix(Lte)]).tocsr())[:, 1]
    print()
    print("SAME FOLDS, THREE FEATURE SETS")
    print("  char n-grams only : %.3f" % roc_auc_score(y, oof_c))
    print("  lexical only      : %.3f" % roc_auc_score(y, oof))
    print("  UNION             : %.3f" % roc_auc_score(y, oof_u))
    oof = oof_u

    print()
    print("BY SUBTYPE, mean out-of-fold score")
    by = collections.defaultdict(list)
    for i, m in enumerate(meta):
        by[subtype(m) if y[i] else "clean"].append(oof[i])
    for st in ("clean", "mangled", "nonwords", "salad"):
        v = by.get(st, [])
        if v:
            miss = sum(1 for x in v if x < 0.5)
            print("  %-9s n=%4d  mean %.3f  scored<0.5: %d (%.0f%%)"
                  % (st, len(v), float(np.mean(v)), miss, 100 * miss / len(v)))

    #: SCRIPT-STRATIFIED, and this is not a footnote. Every lexical feature above
    #: is computed over ASCII-alphabetic tokens, so on a Chinese passage they
    #: rest on almost nothing. If the detector is much weaker on CJK, the
    #: remaining headroom is a MISSING LEXICON and not a missing statistic.
    def cjk_share(t):
        n = sum(1 for ch in t if not ch.isspace())
        if not n:
            return 0.0
        return sum(1 for ch in t if "一" <= ch <= "鿿") / n

    cs = np.array([cjk_share(t) for t in texts])
    print()
    print("BY SCRIPT  (cjk_share of non-space characters)")
    for lab, sel in (("latin  <0.10", cs < 0.10),
                     ("mixed .10-.50", (cs >= 0.10) & (cs < 0.50)),
                     ("cjk    >=0.50", cs >= 0.50)):
        idx = np.where(sel)[0]
        if len(idx) < 20 or not (0 < y[idx].sum() < len(idx)):
            print("  %-14s n=%4d  (too few to score)" % (lab, len(idx)))
            continue
        print("  %-14s n=%4d  junk %3d (%.0f%%)  AUC %.3f"
              % (lab, len(idx), int(y[idx].sum()), 100 * y[idx].mean(),
                 roc_auc_score(y[idx], oof[idx])))

    print()
    print("WITHIN ARM")
    for arm in ("base", "aligned"):
        sel = [i for i, m in enumerate(meta) if m.get("arm") == arm]
        if sel and 0 < y[sel].sum() < len(sel):
            print("  %-8s AUC %.3f" % (arm, roc_auc_score(y[sel], oof[sel])))

    if a.disagree:
        #: THE LABEL-CEILING TEST, and it is a real test rather than an appeal.
        #: The 66 items excluded because the two coders DISAGREED are the
        #: label's own ambiguous region. A model trained on the agreed items and
        #: applied to them should, if it tracks what the coders track, score
        #: them BETWEEN agreed-clean and agreed-junk. If instead it scores them
        #: like clean items, the disagreement is not what limits it.
        k = json.load(open(os.path.join(PASSA, "passA_key.json")))
        c = json.load(open(os.path.join(PASSA, "passA_codings.json")))
        A, B = c["A"], c["B"]

        def jk(d):
            return bool(d.get("lexical") in ("mangled", "nonwords")
                        or d.get("semantic") == "salad")
        dis = [i for i in sorted(k) if i in A and i in B and jk(A[i]) != jk(B[i])]
        dtext = [k[i].get("text") or "" for i in dis]
        if not dis:
            print("no disagreed items found")
            return 0
        Zt = vec.fit_transform(texts)
        Lt = sc.fit_transform(X)
        mdl = LogisticRegression(max_iter=4000, class_weight="balanced").fit(
            hstack([Zt, csr_matrix(Lt)]).tocsr(), y)
        Zd = vec.transform(dtext)
        Ld = sc.transform(np.array([[feats(t)[n] for n in names] for t in dtext]))
        pd_ = mdl.predict_proba(hstack([Zd, csr_matrix(Ld)]).tocsr())[:, 1]
        print()
        print("LABEL-CEILING TEST -- where do the CODER-DISAGREED items score?")
        print("  agreed CLEAN  n=%4d  mean out-of-fold %.3f" % ((y == 0).sum(), oof[y == 0].mean()))
        print("  DISAGREED     n=%4d  mean in-sample   %.3f  <- should sit BETWEEN" % (len(dis), pd_.mean()))
        print("  agreed JUNK   n=%4d  mean out-of-fold %.3f" % ((y == 1).sum(), oof[y == 1].mean()))
        print()
        print("  NB the disagreed score is IN-SAMPLE for the model but those items")
        print("  were never in its training labels, so it is not leakage of THEIR")
        print("  labels -- there are none. It is the honest quantity available.")
        return 0

    if a.misses:
        print()
        print("=" * 74)
        print("STILL ELUDING -- junk scored clean by the LEXICAL features")
        print("=" * 74)
        for i in [i for i in np.argsort(oof) if y[i] == 1][:a.show]:
            m = meta[i]
            print()
            print("  %s score %.3f %-8s subtype %s" % (ids[i], oof[i], m.get("arm"),
                                                       subtype(m)))
            for who in ("A", "B"):
                n = (m[who].get("note") or "").strip()
                if n:
                    print("  note %s: %s" % (who, n[:130]))
            print("  TEXT: %s" % (m.get("text") or "").replace("\n", " / ")[:340])
    return 0


if __name__ == "__main__":
    sys.exit(main())
