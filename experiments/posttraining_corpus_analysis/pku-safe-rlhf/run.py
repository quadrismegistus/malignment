#!/usr/bin/env python
"""PKU-SafeRLHF — is "safer" declining or milder wording? Registered `1f35b01`+`94526aa`.

    python run.py --check      the required false-positive sample, no fitting
    python run.py              the registered test

**FINDING A vs FINDING B, not hypothesis vs null.** RH: the milder hypothesis, if
right, is also a result. A = safety supervision teaches DECLINING; B = it teaches
REGISTER. Same arithmetic either way.

## THE REFUSAL PROXY IS M02's AND NOT MINE

`exit_markers.py` declared these before this question existed, and its header
bars the alternative: *the Y-pilot provenance rule bars lexicons harvested from
one arm's outputs, not declared structural patterns.* A marker set extracted from
Y's coded spans would be exactly that, so it is not used.

**REFUSAL and E-ASSIST stay separate and are never pooled** — M02's rule, and it
is H1's distinction: declining versus disclaiming.

## K RATINGS ON RANKS, NEVER LEVELS

The instrument's own `level_vs_rank` note: charge and concreteness shift in LEVEL
between versions while holding ORDER at r 0.88. So every dimension is converted
to a percentile rank over the lexicon before any averaging.

`transgressiveness` (IAA 0.828) and `bodily_harm` (IAA 0.879) are PRIMARY.
`register_level` (IAA 0.597, NOT ESTABLISHED) and `vulgarity` (sparse, variance
on 463 of 27,242 words) are computed and REPORTED, never used as evidence.
"""
import argparse, csv, glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")
CACHE = "~/.cache/huggingface/datasets/PKU-Alignment___pku-safe_rlhf"
SEED = 20260817
TOKEN = re.compile(r"[a-z']+")
#: The splitter that produced `results/coding/sentences.jsonl`. It is a constant
#: rather than a local because the coding ids are `pair_who_SENTENCEINDEX`, so
#: changing it silently renumbers every id. `coded()` asserts the regenerated
#: ids still cover the codings.
SENT = re.compile(r"(?<=[.!?])\s+")

#: VERBATIM from meta/M02_frame_exit/scripts/exit_markers.py. Copied rather than
#: imported because that repo is the read-only archive; the source is named so
#: the two can be diffed.
REFUSAL = re.compile(r"i (?:cannot|can't|won't|will not) (?:write|continue|create|"
                     r"generate|produce|engage|describe)|i(?:'m| am) sorry,? but|"
                     r"i apologi[sz]e,? but|cannot fulfill|against my (?:guidelines|"
                     r"principles|programming)", re.I)
E_ASSIST = re.compile(r"you are an? (?:ai|helpful|language)|as an ai|"
                      r"i(?:'m| am) an ai|i cannot (?:assist|help|provide)|"
                      r"it(?:'s| is) important to (?:approach|note|remember)|"
                      r"raises (?:some )?(?:significant )?concerns", re.I)

K_PRIMARY = ("transgressiveness", "bodily_harm")
K_REPORTED = ("register_level", "vulgarity", "charge", "valence", "concreteness")


def load(split):
    import pyarrow as pa, pyarrow.ipc as ipc
    f = sorted(glob.glob(os.path.expanduser(CACHE) + "/**/*%s*.arrow" % split,
                         recursive=True))
    if not f:
        raise SystemExit("no %s arrow under %s" % (split, CACHE))
    with pa.memory_map(f[0]) as s:
        return ipc.open_stream(s).read_all().to_pydict()


def both_unsafe(d):
    return [i for i in range(len(d["prompt"]))
            if not d["is_response_0_safe"][i] and not d["is_response_1_safe"][i]]


def check(d, n=50):
    """REQUIRED BEFORE ANY FIT. M02 established by sampling that their REFUSAL
    pattern fired on in-scene dialogue apology. PKU is assistant prose so that
    mode should not apply -- and `should not apply` is what M02 declined to
    assume, which is the whole point of this function."""
    import random
    rng = random.Random(SEED)
    for name, pat in (("REFUSAL", REFUSAL), ("E-ASSIST", E_ASSIST)):
        hits = []
        for i in both_unsafe(d):
            for c in ("response_0", "response_1"):
                m = pat.search(d[c][i])
                if m:
                    a = max(0, m.start() - 40)
                    hits.append(d[c][i][a:m.end() + 60].replace("\n", " "))
        rng.shuffle(hits)
        print("\n===== %s: %d hits in both-unsafe. %d sampled =====" % (name, len(hits), n))
        for h in hits[:n]:
            print("   ...%s..." % h.strip()[:120])


def k_ranks():
    """Each K dimension as a percentile rank over the lexicon. Never a level."""
    from malignment import fields
    import numpy as np
    #: `_k` returns (scales, ratings, meta) -- a TUPLE. The first version of
    #: this subscripted it as a dict and never fired, because the registered
    #: test it belongs to never ran. A latent bug in an unexercised path.
    dims, raw, _meta = fields._k("en")
    dims = list(dims)
    words, vals = [], []
    for w, v in raw.items():
        if isinstance(v, (list, tuple)) and len(v) == len(dims):
            words.append(w); vals.append(v)
    V = np.asarray(vals, dtype=float)
    if not len(V):
        raise SystemExit("no usable K rows")
    R = np.argsort(np.argsort(V, axis=0), axis=0) / max(len(V) - 1, 1)
    return dims, {w: R[i] for i, w in enumerate(words)}


def features(d, idx, dims, ranks):
    """Per pair: refusal counts, e-assist counts, K rank deltas, length, words."""
    import numpy as np
    A, B, meta = [], [], []
    for i in idx:
        A.append(d["response_0"][i]); B.append(d["response_1"][i])
        meta.append((d["better_response_id"][i], d["safer_response_id"][i]))

    def marks(texts):
        return np.asarray([[len(REFUSAL.findall(t)), len(E_ASSIST.findall(t))]
                           for t in texts], dtype=float)

    def kvec(texts):
        out = np.zeros((len(texts), len(dims))); cov = np.zeros(len(texts))
        for j, t in enumerate(texts):
            ws = [w for w in TOKEN.findall(t.lower()) if w in ranks]
            cov[j] = len(ws) / max(len(TOKEN.findall(t.lower())), 1)
            if ws:
                out[j] = np.mean([ranks[w] for w in ws], axis=0)
        return out, cov

    mA, mB = marks(A), marks(B)
    kA, covA = kvec(A); kB, covB = kvec(B)
    lA = np.asarray([[len(TOKEN.findall(t.lower()))] for t in A], dtype=float)
    lB = np.asarray([[len(TOKEN.findall(t.lower()))] for t in B], dtype=float)
    return {"refusal": mA[:, :1] - mB[:, :1], "eassist": mA[:, 1:] - mB[:, 1:],
            "marks": mA - mB, "k": kA - kB, "len": lA - lB,
            "coverage": float((covA.mean() + covB.mean()) / 2),
            "texts": (A, B), "meta": meta}


def randomise(n, seed):
    import numpy as np
    rng = np.random.default_rng(seed)
    y = rng.integers(0, 2, n)
    return y, np.where(y == 1, 1.0, -1.0)


def auc(Xtr, ytr, Xte, yte):
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    import numpy as np
    if Xtr.shape[1] == 0 or len(set(ytr)) < 2:
        return float("nan"), None
    m = LogisticRegression(max_iter=3000, solver="liblinear")
    m.fit(Xtr, ytr)
    return roc_auc_score(yte, m.decision_function(Xte)), m


def disclaim(tr, te):
    """A3's replacement: where exactly ONE response disclaims, does it win?

    CONDITIONAL BY CONSTRUCTION. The unconditional question died with the
    variance: REFUSAL differs on 0.02% of pairs and E-ASSIST on 1.68%, so a
    classifier would report an absent feature as a refuted hypothesis.
    """
    from scipy import stats
    os.makedirs(RESULTS, exist_ok=True)
    rows = []
    for split, d in (("train", tr), ("test", te)):
        strata = {"BOTH-UNSAFE": both_unsafe(d),
                  "MIXED": [i for i in range(len(d["prompt"]))
                            if d["is_response_0_safe"][i] != d["is_response_1_safe"][i]]}
        for sname, idx in strata.items():
            for pname, pat in (("E-ASSIST", E_ASSIST), ("REFUSAL", REFUSAL)):
                sel = []
                for i in idx:
                    a = len(pat.findall(d["response_0"][i]))
                    b = len(pat.findall(d["response_1"][i]))
                    if (a > 0) != (b > 0):
                        sel.append((i, 0 if a > b else 1))
                if not sel:
                    continue
                for label, col in (("safer", "safer_response_id"),
                                   ("better", "better_response_id")):
                    win = sum(1 for i, who in sel if d[col][i] == who)
                    n = len(sel)
                    p = stats.binomtest(win, n, 0.5).pvalue
                    lo, hi = stats.binomtest(win, n, 0.5).proportion_ci()
                    rows.append({"split": split, "stratum": sname, "marker": pname,
                                 "label": label, "n": n, "wins": win,
                                 "rate": round(win / n, 4), "p": "%.3g" % p,
                                 "ci_lo": round(lo, 4), "ci_hi": round(hi, 4),
                                 "powered": "yes" if n >= 100 else "NO"})
                    print("%-6s %-12s %-9s %-7s n=%-5d disclaiming wins %5.1f%%  "
                          "CI [%.3f, %.3f]  p=%-9.3g %s"
                          % (split, sname, pname, label, n, 100 * win / n, lo, hi, p,
                             "" if n >= 100 else "<- UNPOWERED, not a null"))
    with open(os.path.join(RESULTS, "disclaimer_sign_test.csv"), "w", newline="",
              encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader()
        for r in rows: w.writerow(r)
    print("\n  ->", RESULTS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--disclaim", action="store_true")
    ap.add_argument("--length", action="store_true")
    ap.add_argument("--coded", action="store_true")
    a = ap.parse_args()
    tr, te = load("train"), load("test")
    if a.coded:
        coded(tr)
        return
    if a.check:
        check(tr)
        return
    if a.disclaim:
        disclaim(tr, te)
        return
    if a.length:
        lengthcheck(tr)
        return

    import numpy as np, scipy.sparse as sp
    dims, ranks = k_ranks()
    print("K lexicon: %d words, dims %s" % (len(ranks), dims), file=sys.stderr)
    itr, ite = both_unsafe(tr), both_unsafe(te)
    print("both-unsafe: train %d test %d" % (len(itr), len(ite)), file=sys.stderr)
    Ftr, Fte = features(tr, itr, dims, ranks), features(te, ite, dims, ranks)
    print("K coverage: train %.3f test %.3f" % (Ftr["coverage"], Fte["coverage"]),
          file=sys.stderr)

    ytr, str_ = randomise(len(itr), SEED)
    yte, ste = randomise(len(ite), SEED + 1)
    kprim = [dims.index(x) for x in K_PRIMARY]

    rows = []
    for label, col in (("safer", 1), ("better", 0)):
        #: The label is WHICH RESPONSE the column names; after sign flipping, y
        #: is whether the FIRST-PRESENTED response is the named one.
        ltr = np.asarray([m[col] for m in Ftr["meta"]])
        lte = np.asarray([m[col] for m in Fte["meta"]])
        Ytr = np.where(str_ > 0, 1 - ltr, ltr)
        Yte = np.where(ste > 0, 1 - lte, lte)
        sets = {
            "REFUSAL":  (Ftr["refusal"] * str_[:, None], Fte["refusal"] * ste[:, None]),
            "E-ASSIST": (Ftr["eassist"] * str_[:, None], Fte["eassist"] * ste[:, None]),
            "MARKS":    (Ftr["marks"] * str_[:, None], Fte["marks"] * ste[:, None]),
            "K-PRIMARY": (Ftr["k"][:, kprim] * str_[:, None], Fte["k"][:, kprim] * ste[:, None]),
            "K-ALL":    (Ftr["k"] * str_[:, None], Fte["k"] * ste[:, None]),
            "LENGTH":   (Ftr["len"] * str_[:, None], Fte["len"] * ste[:, None]),
        }
        keep_tr = np.abs(Ftr["len"][:, 0]) <= 5
        keep_te = np.abs(Fte["len"][:, 0]) <= 5
        for name, (Xtr, Xte) in sets.items():
            full, m = auc(Xtr, Ytr, Xte, Yte)
            match = (auc(Xtr[keep_tr], Ytr[keep_tr], Xte[keep_te], Yte[keep_te])[0]
                     if keep_tr.sum() > 200 and keep_te.sum() > 50 else float("nan"))
            rows.append({"label": label, "features": name, "auc": round(full, 4),
                         "auc_lenmatched": round(match, 4),
                         "n_train": int(Xtr.shape[0]), "n_matched_train": int(keep_tr.sum()),
                         "coef": None if m is None else
                                 " ".join("%.3f" % c for c in m.coef_[0][:8])})
            print("%-7s %-10s AUC %.4f | len-matched %.4f | coef %s"
                  % (label, name, full, match,
                     "" if m is None else " ".join("%+.2f" % c for c in m.coef_[0][:6])))

    os.makedirs(RESULTS, exist_ok=True)
    with open(os.path.join(RESULTS, "by_featureset.csv"), "w", newline="",
              encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader()
        for r in rows: w.writerow(r)

    g = lambda l, f: next(r["auc_lenmatched"] for r in rows
                          if r["label"] == l and r["features"] == f)
    dA = g("safer", "MARKS") - g("safer", "K-PRIMARY")
    print()
    print("FINDING A (declining) minus FINDING B (register): %+.4f  [threshold 0.05]" % dA)
    print("  -> %s" % ("A: safety supervision teaches DECLINING" if dA >= 0.05 else
                       "B: safety supervision teaches REGISTER" if dA <= -0.05 else
                       "UNDECIDED, |difference| < 0.05"))
    d3 = g("better", "MARKS") - g("safer", "MARKS")
    print("H3  better minus safer on MARKS: %+.4f  [threshold 0.03]" % d3)
    print("  ->", RESULTS)




def lengthcheck(tr):
    """Does the disclaimer effect survive length? A disclaimer ADDS a sentence,
    so 68.4% may be 'longer wins' wearing a costume -- and CONCISENESS is one of
    the four declared helpfulness criteria, so if longer wins on `better` the
    annotation contradicts its own rubric."""
    from scipy import stats
    import numpy as np
    idx = both_unsafe(tr)
    sel = []
    for i in idx:
        a = len(E_ASSIST.findall(tr["response_0"][i]))
        b = len(E_ASSIST.findall(tr["response_1"][i]))
        if (a > 0) != (b > 0):
            who = 0 if a > b else 1
            la = len(TOKEN.findall(tr["response_0"][i].lower()))
            lb = len(TOKEN.findall(tr["response_1"][i].lower()))
            sel.append((i, who, (la - lb) if who == 0 else (lb - la)))
    d = np.asarray([s[2] for s in sel], dtype=float)
    print("n=%d | disclaiming response is LONGER by median %+.0f words "
          "(longer in %.1f%% of pairs)"
          % (len(sel), np.median(d), 100 * (d > 0).mean()))
    print()
    print("%-26s %6s %8s   %-22s %s" % ("condition", "n", "wins", "95% CI", "p"))
    def row(name, keep, col):
        s = [x for x, k in zip(sel, keep) if k]
        if len(s) < 30:
            print("%-26s %6d   UNPOWERED, not a null" % (name, len(s))); return
        w = sum(1 for i, who, _ in s if tr[col][i] == who)
        r = stats.binomtest(w, len(s), 0.5)
        lo, hi = r.proportion_ci()
        print("%-26s %6d %7.1f%%   [%.3f, %.3f]   %-9.3g" %
              (name, len(s), 100*w/len(s), lo, hi, r.pvalue))
    for col, lab in (("safer_response_id", "SAFER"), ("better_response_id", "BETTER")):
        print("-- %s" % lab)
        row("  all", np.ones(len(sel), bool), col)
        row("  |len diff| <= 20 words", np.abs(d) <= 20, col)
        row("  |len diff| <= 10 words", np.abs(d) <= 10, col)
        row("  disclaimer is SHORTER", d < 0, col)
        print()
    #: THE DECISIVE ONE. If length alone predicts as well, the disclaimer is a
    #: proxy for it.
    w = sum(1 for i, who, dd in sel if (tr["safer_response_id"][i] == who) == (dd > 0))
    print("length ALONE agrees with the safer verdict on %.1f%% of the %d pairs"
          % (100*w/len(sel), len(sel)))


def disclaimer_sentences(tr):
    """The 553 sentences that carry a disclaimer marker, in the 550 pairs where
    exactly one response disclaims. Regenerated here rather than read back, so
    the ids in `codings.json` are checked against the corpus every run."""
    idx, out = both_unsafe(tr), []
    for i in idx:
        a = len(E_ASSIST.findall(tr["response_0"][i]))
        b = len(E_ASSIST.findall(tr["response_1"][i]))
        if (a > 0) != (b > 0):
            who = 0 if a > b else 1
            for j, s in enumerate(SENT.split(tr["response_%d" % who][i])):
                if E_ASSIST.search(s):
                    out.append(("%d_%d_%d" % (i, who, j), s,
                                tr["safer_response_id"][i] == who,
                                tr["better_response_id"][i] == who))
    return out


def coded(tr):
    """What KIND of disclaimer wins? Six declared categories, coded blind by two
    agents that never saw the outcome (`results/coding/workflow.js`).

    THE PRIMARY CODER IS B BECAUSE B IS THE ONLY COMPLETE PASS, not because of
    anything in the result. Coder A's batch 2 (lines 187-279) was refused by the
    API, so A has 460 of 553. Choosing the complete pass is forced; choosing the
    one with the nicer table would not be."""
    from scipy import stats
    import collections
    p = os.path.join(RESULTS, "coding", "codings.json")
    C = json.load(open(p, encoding="utf-8"))
    A, B = C["coder_A"], C["coder_B"]
    sents = disclaimer_sentences(tr)
    outcome = {i: (safer, better) for i, _, safer, better in sents}
    missing = [i for i in B if i not in outcome]
    print("sentences regenerated %d | coder B %d | coder A %d | ids not in corpus %d"
          % (len(sents), len(B), len(A), len(missing)))
    assert not missing, "coded ids absent from the corpus: %s" % missing[:5]

    both = [i for i in A if i in B]
    ag = [i for i in both if A[i] == B[i]]
    print("AGREEMENT  %d/%d = %.4f  (declared: %s)"
          % (len(ag), len(both), len(ag) / len(both), C["raw_agreement"]))
    dis = collections.Counter(tuple(sorted((A[i], B[i]))) for i in both if A[i] != B[i])
    print("  disagreements: %s"
          % ", ".join("%s/%s x%d" % (k[0], k[1], n) for k, n in dis.most_common(5)))

    def table(cat, label, col):
        print("\n-- %s | %s (n=%d)" % (label, col, len(cat)))
        print("   %-12s %6s %8s   %-18s %s" % ("category", "n", "wins", "95% CI", "p"))
        for c, _ in collections.Counter(cat.values()).most_common():
            ids = [i for i, v in cat.items() if v == c]
            if len(ids) < 30:
                print("   %-12s %6d   UNPOWERED, not a null" % (c, len(ids))); continue
            k = 0 if col == "safer" else 1
            w = sum(1 for i in ids if outcome[i][k])
            r = stats.binomtest(w, len(ids), 0.5); lo, hi = r.proportion_ci()
            print("   %-12s %6d %7.1f%%   [%.3f, %.3f]   %-9.3g%s"
                  % (c, len(ids), 100 * w / len(ids), lo, hi, r.pvalue,
                     " *" if r.pvalue < 0.05 else ""))

    for col in ("safer", "better"):
        table(B, "PRIMARY: coder B, complete", col)
    table({i: A[i] for i in ag}, "SENSITIVITY: both coders agreed", "safer")

    rows = [{"id": i, "sentence": s, "coder_B": B.get(i), "coder_A": A.get(i),
             "agree": (A.get(i) == B.get(i)) if i in A else None,
             "safer": int(sa), "better": int(be)} for i, s, sa, be in sents]
    with open(os.path.join(RESULTS, "coding", "coded.csv"), "w", newline="",
              encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader()
        for r in rows: w.writerow(r)
    print("\n  ->", os.path.join(RESULTS, "coding", "coded.csv"))


if __name__ == "__main__":
    main()
