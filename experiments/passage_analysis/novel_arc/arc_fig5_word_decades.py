"""Did any decade of the novel use the aligned stories' distinctive evaluative words at the aligned rate? (TheoryMachines,
2026-09-26: "their per-decade rate across the whole history, and the highest decade for each")

    .venv/bin/python -u arc_fig5_word_decades.py   -> ARC_FIG5_WORD_DECADES.md

WORDS: magic, magical, forest, community, explore, stars, glow, discovery -- surface forms, lowercased, as the
evaluative share counts them. HISTORY: the figure's population over the WHOLE span, Chadwyck and Chicago arc_fiction
reps 1600-2009, >= 2,000 content words; per decade, the MEAN over texts of the word's rate per 1,000 content words (the
statistic of ARC_FIG5_EVAL_WORDS, so the aligned numbers compare) and the number of texts. Decades with fewer than 3
texts are dropped, as in the figure. MODELS: base and aligned means over (lineage, condition) pairs, recomputed here from
the meta-texts by arc_fig5_eval_words' definition. "No period" below means no decade of THIS corpus. EXPLORATORY.
"""
import collections, io, os, re, sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import arc_fig5_checks as C                                   # noqa: E402
V, A, E, H = C.V, C.A, C.E, C.H

OUT = os.path.join(HERE, "ARC_FIG5_WORD_DECADES.md")
WORDS = ["magic", "magical", "forest", "community", "explore", "stars", "glow", "discovery"]
#: booked (ARC_FIG5_EVAL_WORDS.md, aligned column): the recomputation must reproduce the list it extends
BOOKED_ALIGNED = {"magic": 1.70, "magical": 0.68, "forest": 2.30, "community": 1.04, "explore": 0.57, "stars": 0.73,
                  "glow": 0.79, "discovery": 0.53}


def main():
    L = V.lexicons()
    Th = V.history(L).merge(H.concreteness_texts()[["_id", "year"]], on="_id")
    Th = Th[(Th.lexicon == E.LEX) & Th.year.between(1600, 2009) & (Th.n_content >= H.MIN_CONTENT)][["_id", "year", "n_content"]]
    sql = f"""SELECT f._id AS _id, f.k AS word, f.v AS n FROM (SELECT _id, k, v FROM (SELECT _id, freqs FROM lltk.text_freqs FINAL
              WHERE _id IN ({A.REPS}) AND _id IN (SELECT _id FROM lltk.texts FINAL WHERE corpus IN ('chadwyck', 'chicago')))
              ARRAY JOIN mapKeys(freqs) AS k, mapValues(freqs) AS v) f INNER JOIN w ON f.k = w.form FORMAT TSVWithNames"""
    R = pd.read_csv(io.StringIO(A.ch_query(sql, {"w": ("form String", [(w,) for w in WORDS])})), sep="\t", keep_default_na=False)
    Wd = R.pivot_table(index="_id", columns="word", values="n", aggfunc="sum").reindex(columns=WORDS).fillna(0)
    T = Th.merge(Wd, left_on="_id", right_index=True, how="left").fillna({w: 0 for w in WORDS})
    for w in WORDS:
        T[w] = 1000 * T[w] / T.n_content
    T["decade"] = T.year // 10 * 10
    D = T.groupby("decade")[WORDS].mean()
    n = T.groupby("decade").size()
    D, n = D[n >= H.MIN_DECADE], n[n >= H.MIN_DECADE]

    _, sw, _ = A.lists_expanded()
    M = pd.read_parquet(os.path.join(A.DATA, "prompt_check_national_judged_meta.parquet"))
    rate = {}
    for r in M.itertuples():
        t = [x for x in re.findall(r"[a-z]+", r.text.lower()) if x not in sw]
        c = collections.Counter(t)
        rate[(r.lineage, r.cond)] = {w: 1000 * c[w] / len(t) for w in WORDS}
    aligned = [c for c in E.COND.values() if c != "base"]
    pairs = [(l, c) for (l, c) in rate if c in aligned and (l, "base") in rate]
    base = {w: np.mean([rate[(l, "base")][w] for l, _ in pairs]) for w in WORDS}
    al = {w: np.mean([rate[p][w] for p in pairs]) for w in WORDS}
    for w, v in BOOKED_ALIGNED.items():
        assert abs(al[w] - v) < 0.006, (w, al[w], v)

    Rr = ["# The aligned stories' distinctive words, decade by decade (EXPLORATORY)", "",
          "Producer `arc_fig5_word_decades.py` (method in its docstring). %s Chadwyck and Chicago novels, 1600-2009, %d decades "
          "with at least %d texts. Per 1,000 content words, mean over texts. \"Aligned\" pools the three aligned conditions (%d "
          "lineage-condition pairs), as in ARC_FIG5_EVAL_WORDS.md." % (format(len(T), ","), len(D), H.MIN_DECADE, len(pairs)), "",
          "## Highest decade against the models", "",
          "| word | highest decade | its rate | texts in it | base models | aligned | aligned / highest decade |", "|---|---|---|---|---|---|---|"]
    for w in WORDS:
        d = int(D[w].idxmax())
        Rr.append("| %s | %ds | %.2f | %d | %.2f | %.2f | %.1fx |" % (w, d, D.loc[d, w], n[d], base[w], al[w], al[w] / D.loc[d, w] if D.loc[d, w] else float("inf")))
    Rr += ["", "## Every decade", "", "| decade | texts | " + " | ".join(WORDS) + " |", "|---|---|" + "---|" * len(WORDS)]
    for d in D.index:
        Rr.append("| %ds | %d | %s |" % (d, n[d], " | ".join("%.2f" % D.loc[d, w] for w in WORDS)))
    Rr += ["", "| base models | | %s |" % " | ".join("%.2f" % base[w] for w in WORDS),
           "| aligned | | %s |" % " | ".join("%.2f" % al[w] for w in WORDS)]
    open(OUT, "w").write("\n".join(Rr) + "\n")
    print("\n".join(Rr))


if __name__ == "__main__":
    main()
