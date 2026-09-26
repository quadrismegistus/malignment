"""Which evaluative words carry the novels' evaluative PEAK (1765-1795) against the 1950s, in the format of
arc_fig5_eval_words.py; and how far lowercasing lets names and personified abstractions score as words. (TheoryMachines,
2026-09-26: "which words carry the novels' evaluative peak, around 1765 to 1795, against the 1950s")

    .venv/bin/python -u arc_fig5_history_words.py   -> ARC_FIG5_HISTORY_WORDS.md

WINDOWS: the figure's population (Chadwyck and Chicago arc_fiction reps, >= 2,000 content words), years 1765-1795
(PEAK) and 1945-1975 (the 1950s, widened to thirty years to match). The peak window holds 31 novels, all Chadwyck; the
1950s window 1,771, all Chicago, so the contrast is also a contrast of corpora.
WORDS: the figure's "+vector" lexicon, polar only, minus USAS X and E forms (arc_fig5_checks' lists), as in
arc_fig5_eval_words. Rates per 1,000 content words from lltk.text_freqs (lowercased surface tokens), MEAN over texts,
so contributions (peak mean - 1950s mean) sum to the difference in mean evaluative share. TEXTS WITH: how many texts
in each window contain the word, the concentration check (one novel's heroine can carry a word).
CASE: text_freqs has none, so capitalisation is read from lltk.passages (p500) -- every passage of the 31 peak texts.
lltk.passages holds NO Chicago texts (checked 2026-09-26: chadwyck 232,522 passages, chicago 0), so the 1950s window
has no case information at all; its column is dropped and the absence stated, not printed as dashes. MID-CAP = occurrences capitalised after a lowercase word or
comma (not sentence-initial) over all occurrences. A capitalised mid-sentence word is a name, a personification, or,
in the eighteenth century, a typographic habit of capitalising nouns: the column cannot tell them apart, and it is
given only so the reader can see where the question arises. COMPARISON: the aligned list's top words
(ARC_FIG5_EVAL_WORDS.md) with their rates in both windows. EXPLORATORY.
"""
import collections, io, os, re, sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import arc_fig5_checks as C                                   # noqa: E402
V, A, E, H = C.V, C.A, C.E, C.H

OUT = os.path.join(HERE, "ARC_FIG5_HISTORY_WORDS.md")
WIN = {"peak": (1765, 1795), "1950s": (1945, 1975)}
CACHE = os.path.join(A.DATA, "history_words_windows.parquet")
PSG_1950 = 4000
TOP, FALL = 30, 10
ALIGNED_TOP = ["heart", "forest", "life", "journey", "magic", "lily", "beauty", "community", "sun", "warm", "help", "magical",
               "trees", "glow", "spirit", "guardian", "family", "stars", "grateful", "mysterious", "discovery", "explore"]
PERSON = ["hope", "grace", "honour", "honor", "virtue", "fortune", "providence", "heaven", "nature", "fate", "love", "joy",
          "faith", "charity", "prudence", "patience", "mercy", "vice", "folly", "reason"]


def window_texts():
    L = V.lexicons()
    Th = V.history(L).merge(H.concreteness_texts()[["_id", "year", "corpus"]], on="_id")
    Th = Th[(Th.lexicon == E.LEX) & (Th.n_content >= H.MIN_CONTENT)]
    out = {}
    for k, (a, b) in WIN.items():
        out[k] = Th[Th.year.between(a, b)][["_id", "year", "corpus", "n_content", "eval_rate"]]
    return out, L


def counts(ids, forms):
    if os.path.exists(CACHE):
        return pd.read_parquet(CACHE)
    idl = ",".join("'%s'" % i.replace("'", "\\'") for i in ids)
    sql = f"""SELECT f._id AS _id, f.k AS word, f.v AS n
      FROM (SELECT _id, k, v FROM (SELECT _id, freqs FROM lltk.text_freqs FINAL WHERE _id IN ({idl}))
            ARRAY JOIN mapKeys(freqs) AS k, mapValues(freqs) AS v) f
      INNER JOIN w ON f.k = w.form FORMAT TSVWithNames"""
    R = pd.read_csv(io.StringIO(A.ch_query(sql, {"w": ("form String", [(w,) for w in sorted(forms)])})), sep="\t",
                    keep_default_na=False, quoting=3)
    R.to_parquet(CACHE, index=False)
    return R


def passages(ids, limit):
    idl = ",".join("'%s'" % i.replace("'", "\\'") for i in ids)
    lim = "ORDER BY cityHash64(_id, seq) LIMIT %d" % limit if limit else ""
    sql = f"SELECT text FROM lltk.passages WHERE _id IN ({idl}) {lim} FORMAT TSVWithNames"
    P = pd.read_csv(io.StringIO(A.ch_query(sql, {})), sep="\t", keep_default_na=False, quoting=3)
    unesc = lambda t: re.sub(r"\\(.)", lambda m: {"n": "\n", "t": "\t", "r": ""}.get(m.group(1), m.group(1)), t)
    return [unesc(t) for t in P.text]


def midcap(texts, words):
    cap, alln = collections.Counter(), collections.Counter()
    ws = set(words)
    for t in texts:
        for m in re.finditer(r"(?<=[a-z,;] )([A-Z][a-z]+)\b", t):
            w = m.group(1).lower()
            if w in ws:
                cap[w] += 1
        for m in re.finditer(r"\b([A-Za-z]+)\b", t):
            w = m.group(1).lower()
            if w in ws:
                alln[w] += 1
    return {w: (cap[w], alln[w]) for w in ws}


def main():
    W, L = window_texts()
    assert len(W["peak"]) == 31 and set(W["peak"].corpus) == {"chadwyck"}, W["peak"].corpus.value_counts()
    assert set(W["1950s"].corpus) == {"chicago"}, W["1950s"].corpus.value_counts()
    ex, sw, _ = A.lists_expanded()
    Ew, _ = C.e_list(sw)
    XE = ex["fullx"] | Ew
    lex_all = {w: v for w, v in L[E.LEX].items() if v < 4 or v > 6}
    lex_d = {w: v for w, v in lex_all.items() if w not in XE}
    T = pd.concat([W[k].assign(win=k) for k in WIN])
    R0 = counts(list(T._id), set(lex_all) | set(ALIGNED_TOP) | set(PERSON))
    R0 = R0.merge(T[["_id", "win", "n_content"]], on="_id")
    R0["rate"] = R0.n / R0.n_content
    n_t = T.groupby("win")._id.nunique()
    #: mean over texts, zeros included: sum of rates / number of texts in the window
    mean_rate = R0.groupby(["win", "word"]).rate.sum().unstack(0).fillna(0) / n_t
    has = R0[R0.n > 0].groupby(["win", "word"])._id.nunique().unstack(0).fillna(0).astype(int)
    #: the lexicon rates must add up to the figure's own evaluative share, or this is a different measure
    tot = R0[R0.word.isin(lex_all)].groupby("_id").rate.sum()
    chk = T.set_index("_id").eval_rate
    assert np.allclose(tot.reindex(chk.index).fillna(0), chk, atol=1e-9), "window rates do not reproduce eval_rate"
    ml = mean_rate.reindex(list(lex_all)).fillna(0)
    gap_all = float((ml["peak"] - ml["1950s"]).sum())
    D = pd.DataFrame({"word": list(lex_d)})
    D["valence"] = D.word.map(lex_d)
    D["pole"] = np.where(D.valence > 6, "positive", "negative")
    mr = mean_rate.reindex(D.word).fillna(0)
    D["peak"], D["fifties"] = mr["peak"].values, mr["1950s"].values
    D["contrib"] = D.peak - D.fifties
    hs = has.reindex(D.word).fillna(0)
    D["has_peak"], D["has_50s"] = hs["peak"].values.astype(int), hs["1950s"].values.astype(int)
    gap_d = D.contrib.sum()
    top_words = set()
    for pole in ("positive", "negative"):
        P = D[D.pole == pole].sort_values("contrib", ascending=False)
        top_words |= set(P.head(TOP).word) | set(P.tail(FALL).word)
    peak_txt = passages(list(W["peak"]._id), None)
    #: booked absence: if Chicago passages ever land, this fires and the 1950s column should come back
    assert len(passages(list(W["1950s"]._id), PSG_1950)) == 0, "Chicago passages now exist: restore the 1950s mid-cap column"
    mc_p = midcap(peak_txt, top_words | set(ALIGNED_TOP) | set(PERSON))
    pct = lambda d, w: "%d%% of %d" % (round(100 * d[w][0] / d[w][1]), d[w][1]) if d[w][1] else "-"

    R = ["# Evaluative words at the novels' peak (1765-1795) against the 1950s (EXPLORATORY)", "",
         "Producer `arc_fig5_history_words.py` (method in its docstring). Peak: %d novels, all Chadwyck; 1950s window (1945-1975): %s "
         "novels, all Chicago. **The contrast is also a contrast of corpora, and the peak rests on 31 texts.** Rates per 1,000 "
         "content words, mean over texts; contributions sum to the difference in mean evaluative share. Mid-cap from %s peak "
         "passages (all); none for the 1950s, because lltk.passages holds no Chicago texts." % (n_t["peak"], format(n_t["1950s"], ","), format(len(peak_txt), ",")), "",
         "- Mean evaluative share: peak %.1f, 1950s %.1f per 1,000 (difference %+.1f)." % (1000 * T[T.win == "peak"].eval_rate.mean(), 1000 * T[T.win == "1950s"].eval_rate.mean(), 1000 * gap_all),
         "- Of which words outside USAS X and E: %+.1f (%.0f%%)." % (1000 * gap_d, 100 * gap_d / gap_all)]
    for pole in ("positive", "negative"):
        R.append("- %s pole, outside X and E: net %+.1f per 1,000." % (pole.capitalize(), 1000 * D[D.pole == pole].contrib.sum()))
    for pole in ("positive", "negative"):
        P = D[D.pole == pole].sort_values("contrib", ascending=False)
        top = P.head(TOP)
        R += ["", "## %s pole: top %d by contribution (more at the peak)" % (pole.capitalize(), TOP), "",
              "These carry %+.1f per 1,000, %.0f%% of the gap outside X and E." % (1000 * top.contrib.sum(), 100 * top.contrib.sum() / gap_d), "",
              "| word | valence | peak | 1950s | contribution | peak texts with (of %d) | 1950s texts with (of %s) | mid-cap, peak |" % (n_t["peak"], format(n_t["1950s"], ",")),
              "|---|---|---|---|---|---|---|---|"]
        R += ["| %s | %.1f | %.2f | %.2f | %+.3f | %d | %d | %s |" % (r.word, r.valence, 1000 * r.peak, 1000 * r.fifties, 1000 * r.contrib, r.has_peak, r.has_50s, pct(mc_p, r.word)) for r in top.itertuples()]
        low = P.tail(FALL).iloc[::-1]
        R += ["", "Largest %d rises into the 1950s on this pole:" % FALL, "",
              "| word | valence | peak | 1950s | contribution | peak texts with | 1950s texts with |", "|---|---|---|---|---|---|---|"]
        R += ["| %s | %.1f | %.2f | %.2f | %+.3f | %d | %d |" % (r.word, r.valence, 1000 * r.peak, 1000 * r.fifties, 1000 * r.contrib, r.has_peak, r.has_50s) for r in low.itertuples()]
    Mr = mean_rate.reindex(ALIGNED_TOP + PERSON).fillna(0)
    Hs = has.reindex(ALIGNED_TOP + PERSON).fillna(0).astype(int)
    for title, ws in (("The aligned list's top words in the two windows", ALIGNED_TOP), ("Candidate names and personified abstractions", PERSON)):
        R += ["", "## " + title, "", "| word | in figure lexicon | USAS X/E | peak | 1950s | peak texts with | mid-cap, peak |", "|---|---|---|---|---|---|---|"]
        R += ["| %s | %s | %s | %.2f | %.2f | %d | %s |" % (w, "%.1f" % lex_all[w] if w in lex_all else "no", "yes" if w in XE else "no",
                                                    1000 * Mr.loc[w, "peak"], 1000 * Mr.loc[w, "1950s"], Hs.loc[w, "peak"], pct(mc_p, w)) for w in ws]
    R += ["", "Mid-cap cannot separate a name, a personification and the eighteenth-century habit of capitalising nouns; it marks where the question arises."]
    open(OUT, "w").write("\n".join(R) + "\n")
    print("\n".join(R))


if __name__ == "__main__":
    main()
