"""Is a rise in valence fewer negative words, more positive words, or a change in their intensity? (RH, 2026-09-26)

    ~/github/abslithists/abstraction/.venv/bin/python -u arc_valence_decomp.py   -> ARC_VALENCE_DECOMP.md

THE IDENTITY. Over a group's scored tokens (tokens whose surface form the valence table covers; book-policy
stopwords and names removed, abstraction's tokenize_agnostic on lowercased text), with n the neutral point and
bins NEGATIVE (v < n - h), NEUTRAL (|v - n| <= h), POSITIVE (v > n + h):
    mean - n  =  p * Dpos  -  q * Dneg  +  r * Dneu
p, q, r the bins' token shares; Dpos = mean (v - n) over positive tokens, Dneg = mean (n - v) over negative tokens,
Dneu = mean (v - n) over neutral tokens (signed, small). The change between two groups splits EXACTLY by the
midpoint rule for each product (dXY = dX * mean(Y) + mean(X) * dY):
    more positive words        dp * mean(Dpos)
    fewer negative words      -dq * mean(Dneg)
    positive words stronger    mean(p) * dDpos
    negative words weaker     -mean(q) * dDneg
    neutral band               d(r * Dneu)
The neutral band is what lets "more positive" and "fewer negative" differ: without it p + q = 1.

WORD LEVEL. mean - n = sum_w f_w (v_w - n), f_w the word's share of scored tokens, so the change is exactly
sum_w df_w (v_w - n): each word's contribution, ranked.

VERSIONS. (a) the human Warriner lookup: n = 5, h = 1 (neutral = ratings 4-6); (b) plain vector valence
(VAD-Valence.Warriner.median): n and h where Warriner 5 and a 1-point band fall on the axis (OLS over the
Warriner lemmas; arc_valence_extremity.py uses the same neutral point).

GROUPS. National stories (judged no-demonym, one meta-text per model-condition; prompt_check_national_judged_meta):
per lineage, base against each aligned condition, each component's sign tested over lineages; and all models
pooled per condition for the word ranking. History: arc_fiction reps (abstraction.scores_rep), 1750-1799 against
1850-1899, word counts from lltk.text_freqs pooled over each half-century (long texts weigh more; a description
of the period's fiction as a body of text). EXPLORATORY.
"""
import collections, csv, io, os, sys

import numpy as np
import pandas as pd

ABS = os.path.expanduser("~/github/abslithists/abstraction")
sys.path.insert(0, ABS)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from abstraction.tokenize import get_stopwords_and_names, tokenize_agnostic   # noqa: E402
import arc_interiority as A                                                   # noqa: E402  (ch_query, REPS: stdlib only)

SH = os.path.expanduser("~/malignment-data/interiority_norms")
DATA = os.path.expanduser("~/malignment-data/novel_arc")
PLAIN = "VAD-Valence.Warriner.median"
#: HTML entity residue in lltk.text_freqs (&apos; &quot; ...) tokenises to words the vector vocabulary scores: `apos`
#: topped the first history ranking. Never scored, in any group.
ENTITIES = {"apos", "quot", "amp", "lt", "gt", "nbsp", "mdash", "ndash", "hellip", "rsquo", "lsquo", "rdquo", "ldquo"}
COMP = ["more positive words", "fewer negative words", "positive words stronger", "negative words weaker", "neutral band"]


def warriner():
    sys.path.insert(0, os.path.expanduser("~/github/malignment"))
    from malignment import fields as FD
    W = {}
    for r in csv.DictReader(open(FD.SOURCES["warriner"], encoding="utf-8", errors="replace")):
        try:
            W[r["Word"].lower()] = float(r["V.Mean.Sum"])
        except (KeyError, ValueError, TypeError):
            pass
    return W


def versions():
    """-> {name: (dict word -> value, neutral n, half-band h)}"""
    drop = get_stopwords_and_names()
    W = warriner()
    look = {w: v for w, v in W.items() if w.isalpha() and w not in drop}
    n = pd.read_parquet(os.path.join(SH, "vad_norms.parquet"), columns=[PLAIN])
    n = n[n.index.map(lambda w: isinstance(w, str))]
    n = n[~n.index.duplicated()]
    n = n[~n.index.str.lower().isin(drop)][PLAIN].dropna()
    common = [w for w in W if w in n.index]
    b, a = np.polyfit([W[w] for w in common], n.loc[common].values, 1)
    return {"human lookup": (look, 5.0, 1.0), "plain vector": (n.to_dict(), a + 5.0 * b, b * 1.0)}


def stats(counts, table, n0, h):
    """counts: {word: tokens} -> p, q, r, Dpos, Dneg, Dneu, mean, n_scored"""
    tot = 0; S = collections.defaultdict(float); C = collections.defaultdict(float)
    for w, c in counts.items():
        if w in ENTITIES:
            continue
        v = table.get(w)
        if v is None:
            continue
        d = v - n0
        k = "pos" if d > h else "neg" if d < -h else "neu"
        C[k] += c; S[k] += c * d; tot += c
    if not tot:
        return None
    p, q, r = C["pos"] / tot, C["neg"] / tot, C["neu"] / tot
    Dp = S["pos"] / C["pos"] if C["pos"] else 0.0
    Dq = -S["neg"] / C["neg"] if C["neg"] else 0.0
    Dr = S["neu"] / C["neu"] if C["neu"] else 0.0
    return dict(p=p, q=q, r=r, Dp=Dp, Dq=Dq, Dr=Dr, mean=n0 + p * Dp - q * Dq + r * Dr, n=tot)


def decompose(a, b):
    """exact midpoint split of b.mean - a.mean into COMP"""
    m = lambda k: (a[k] + b[k]) / 2
    return {COMP[0]: (b["p"] - a["p"]) * m("Dp"), COMP[1]: -(b["q"] - a["q"]) * m("Dq"),
            COMP[2]: m("p") * (b["Dp"] - a["Dp"]), COMP[3]: -m("q") * (b["Dq"] - a["Dq"]),
            COMP[4]: b["r"] * b["Dr"] - a["r"] * a["Dr"]}


def word_rank(ca, cb, table, n0, k=15):
    fa = {w: c for w, c in ca.items() if w in table and w not in ENTITIES}
    fb = {w: c for w, c in cb.items() if w in table and w not in ENTITIES}
    ta, tb = sum(fa.values()), sum(fb.values())
    contrib = {w: (fb.get(w, 0) / tb - fa.get(w, 0) / ta) * (table[w] - n0) for w in set(fa) | set(fb)}
    s = pd.Series(contrib).sort_values()
    return s.tail(k)[::-1], s.head(k)


def fmt(dec, total):
    return ", ".join("%s %+.4f (%d%%)" % (k, v, round(100 * v / total)) if total else "%s %+.4f" % (k, v) for k, v in dec.items())


def national(V, L):
    from scipy.stats import binomtest
    M = pd.read_parquet(os.path.join(DATA, "prompt_check_national_judged_meta.parquet"))
    counts = {r.id: collections.Counter(tokenize_agnostic(r.text.lower())) for r in M.itertuples()}
    conds = ["base", "aligned_raw", "aligned_prefill", "aligned_rettberg"]
    lab = {"aligned_raw": "aligned, raw", "aligned_prefill": "aligned, chat, prefilled", "aligned_rettberg": "aligned, chat, asked"}
    L += ["## National stories: base -> aligned", ""]
    for name, (table, n0, h) in V.items():
        L += ["### %s (neutral %.3f, band +-%.3f)" % (name, n0, h), ""]
        st = {(r.lineage, r.cond): stats(counts[r.id], table, n0, h) for r in M.itertuples()}
        pooled = {c: stats(sum((counts[i] for i in M[M.cond == c].id), collections.Counter()), table, n0, h) for c in conds}
        L += ["Pooled over models, bin shares and distances: " + "; ".join(
            "%s p %.3f q %.3f r %.3f D+ %.3f D- %.3f" % (c, s["p"], s["q"], s["r"], s["Dp"], s["Dq"]) for c, s in pooled.items()), "",
              "| base -> | observed rise (pooled) | " + " | ".join(COMP) + " |", "|---|---|" + "---|" * len(COMP)]
        for c in conds[1:]:
            tot = pooled[c]["mean"] - pooled["base"]["mean"]
            dec = decompose(pooled["base"], pooled[c])
            assert abs(sum(dec.values()) - tot) < 1e-9, (sum(dec.values()), tot)
            L.append("| %s | %+.4f | %s |" % (lab[c], tot, " | ".join("%+.4f (%d%%)" % (v, round(100 * v / tot)) for v in dec.values())))
        L += ["", "Per lineage, how many lineages have each component POSITIVE (i.e. pushing valence up; sign test p):", "",
              "| base -> | lineages | observed rise | " + " | ".join(COMP) + " |", "|---|---|---|" + "---|" * len(COMP)]
        for c in conds[1:]:
            lins = [l for l in M.lineage.unique() if (l, "base") in st and (l, c) in st and st[(l, "base")] and st[(l, c)]]
            D = pd.DataFrame([dict(rise=st[(l, c)]["mean"] - st[(l, "base")]["mean"], **decompose(st[(l, "base")], st[(l, c)])) for l in lins])
            cells = []
            for k in ["rise"] + COMP:
                up = int((D[k] > 0).sum())
                cells.append("%d up (p %.3f)" % (up, binomtest(up, len(D)).pvalue))
            L.append("| %s | %d | %s |" % (lab[c], len(D), " | ".join(cells)))
        up, dn = word_rank(sum((counts[i] for i in M[M.cond == "base"].id), collections.Counter()),
                           sum((counts[i] for i in M[M.cond == "aligned_raw"].id), collections.Counter()), table, n0)
        L += ["", "Words driving base -> aligned raw (contribution to the change in mean valence, x1e4):", "",
              "- raising valence: " + ", ".join("%s %+.1f" % (w, 1e4 * v) for w, v in up.items()),
              "- lowering valence: " + ", ".join("%s %+.1f" % (w, 1e4 * v) for w, v in dn.items()), ""]


def history(V, L):
    def counts(lo, hi):
        sql = f"""SELECT k AS word, sum(v) AS n
          FROM (SELECT _id, freqs FROM lltk.text_freqs FINAL WHERE _id IN ({A.REPS})
                AND _id IN (SELECT _id FROM lltk.texts FINAL WHERE year BETWEEN {lo} AND {hi}))
          ARRAY JOIN mapKeys(freqs) AS k, mapValues(freqs) AS v
          WHERE match(k, '^[a-z]+$') GROUP BY word HAVING n >= 3 FORMAT TSVWithNames"""
        T = pd.read_csv(io.StringIO(A.ch_query(sql, {})), sep="\t", keep_default_na=False)
        return collections.Counter(dict(zip(T.word, T.n)))
    c1, c2 = counts(1750, 1799), counts(1850, 1899)
    L += ["## History: arc_fiction 1750-1799 -> 1850-1899 (pooled word counts)", ""]
    for name, (table, n0, h) in V.items():
        a, b = stats(c1, table, n0, h), stats(c2, table, n0, h)
        tot = b["mean"] - a["mean"]
        dec = decompose(a, b)
        assert abs(sum(dec.values()) - tot) < 1e-9
        up, dn = word_rank(c1, c2, table, n0)
        L += ["### %s" % name, "",
              "1750-99: p %.3f q %.3f r %.3f D+ %.3f D- %.3f mean %.4f; 1850-99: p %.3f q %.3f r %.3f D+ %.3f D- %.3f mean %.4f" % (
                  a["p"], a["q"], a["r"], a["Dp"], a["Dq"], a["mean"], b["p"], b["q"], b["r"], b["Dp"], b["Dq"], b["mean"]), "",
              "Change %+.4f = %s" % (tot, fmt(dec, tot)), "",
              "- raising valence (x1e4): " + ", ".join("%s %+.1f" % (w, 1e4 * v) for w, v in up.items()),
              "- lowering valence (x1e4): " + ", ".join("%s %+.1f" % (w, 1e4 * v) for w, v in dn.items()), ""]


def main():
    V = versions()
    L = ["# Decomposing valence: fewer negative words, more positive words, or intensity? (EXPLORATORY)", "",
         "Producer `arc_valence_decomp.py` (method and identity in its docstring). Components sum exactly to the observed "
         "change (asserted). Percentages are shares of the observed change and can exceed 100 or go negative.", ""]
    national(V, L)
    history(V, L)
    open(os.path.join(HERE, "ARC_VALENCE_DECOMP.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
