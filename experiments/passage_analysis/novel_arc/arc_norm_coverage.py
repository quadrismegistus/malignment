"""How much of arc_fiction do the type-based norms cover, decade by decade? (RH, 2026-09-25)

    .venv/bin/python -u arc_norm_coverage.py   -> ARC_NORM_COVERAGE.md, $MALIGNMENT_DATA/novel_arc/arc_norm_coverage_texts.parquet

BEFORE running fields.py's type norms over the history (Warriner valence/arousal/dominance, Brysbaert
concreteness, the k lexicon's LLM-rated scales), the question is whether their coverage holds up in older
fiction or sags with period vocabulary and spelling, which would bias every early decade toward the words
a modern lexicon happens to know.

COVERAGE of a text: its tokens whose form is in a source's word set, over its content tokens (alphabetic,
expanded stopwords out: arc_interiority's denominator). Two versions per source:
  raw       the source's own word forms, lowercased;
  expanded  plus every MorphAdorner variant whose modern form is in the source (shew -> show), plus long-s
            readings of both (arc_interiority.long_s, zipf < 2): the lists' own spelling rule.
Per decade the median over texts (>= 2,000 content tokens, >= 3 texts). Then, per century, the most
frequent content forms NO source covers after expansion: the words an expansion would have to rate.
EXPLORATORY.
"""
import csv, io, json, os, sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, REPO)
import arc_interiority as A                             # noqa: E402
from malignment import fields as FD                     # noqa: E402

OUT = os.path.join(A.DATA, "arc_norm_coverage_texts.parquet")


def sources():
    W = {(r.get("Word") or "").lower() for r in csv.DictReader(open(FD.SOURCES["warriner"], encoding="utf-8", errors="replace"))}
    B = {(r.get("Word") or "").lower() for r in csv.DictReader(open(FD.SOURCES["brysbaert"], encoding="utf-8", errors="replace"), delimiter="\t")}
    _, R, _ = FD._k("en")
    K = {w.lower() for w in R}
    S = {"warriner": W, "brysbaert": B, "k": K}
    return {k: {w for w in v if w.isalpha()} for k, v in S.items()}


def expand_all(words, morph, zipf):
    out = set(words) | {v for v, m in morph if m in words}
    ls = set()
    for w in out:
        ls |= A.long_s(w, zipf)
    return {w for w in out | ls if w.isalpha()}


def main():
    from wordfreq import zipf_frequency
    assert not os.path.exists(OUT), "refusing to overwrite " + OUT
    morph = []
    for line in open(A.MORPH, encoding="utf-8", errors="replace"):
        p = line.rstrip("\n").split("\t")
        if len(p) == 2 and p[0].isalpha() and p[1].isalpha():
            morph.append((p[0].lower(), p[1].lower()))
    S = sources()
    _, sw, _ = A.lists_expanded()
    sets = {}
    for k, v in S.items():
        sets[k + "_raw"] = v - sw
        sets[k + "_exp"] = expand_all(v, morph, zipf_frequency) - sw
    info = {k: len(v) for k, v in sets.items()}
    print(info, flush=True)
    rows = [(w, k) for k, v in sets.items() for w in sorted(v)]
    cols = ",\n".join("sumIf(v, k IN (SELECT word FROM nw WHERE src = '%s')) AS n_%s" % (k, k) for k in sets)
    sql = f"""SELECT _id, {cols}
      FROM (SELECT _id, freqs FROM lltk.text_freqs FINAL WHERE _id IN ({A.REPS}))
      ARRAY JOIN mapKeys(freqs) AS k, mapValues(freqs) AS v
      GROUP BY _id FORMAT TSVWithNames"""
    N = pd.read_csv(io.StringIO(A.ch_query(sql, {"nw": ("word String, src String", rows)})), sep="\t")
    assert len(N) == 82080, len(N)
    D = pd.read_parquet(A.OUT).rename(columns={"r._id": "_id"})[["_id", "year", "corpus", "source", "n_content"]].merge(N, on="_id", validate="1:1")
    D.to_parquet(OUT, index=False)
    D = D[(D.n_content >= A.MIN_CONTENT) & D.year.between(1600, 2009)].copy()
    D["decade"] = D.year // 10 * 10
    for k in sets:
        D["c_" + k] = D["n_" + k] / D.n_content
    C = D.groupby("decade").agg(n=("_id", "size"), **{k: ("c_" + k, "median") for k in sets})
    C = C[C.n >= 3]
    # the most frequent forms no source covers after expansion, per century
    covered = sets["warriner_exp"] | sets["brysbaert_exp"] | sets["k_exp"]
    sql2 = f"""SELECT intDiv(t.year, 100) + 1 AS century, k AS word, sum(v) AS n
      FROM (SELECT _id, freqs FROM lltk.text_freqs FINAL WHERE _id IN ({A.REPS})) f
      INNER JOIN (SELECT _id, year FROM lltk.texts FINAL WHERE _id IN ({A.REPS})) t ON f._id = t._id
      ARRAY JOIN mapKeys(f.freqs) AS k, mapValues(f.freqs) AS v
      WHERE match(k, '^[a-z]+$') AND k NOT IN (SELECT word FROM cw) AND t.year BETWEEN 1600 AND 2009
      GROUP BY century, word ORDER BY century, n DESC LIMIT 60 BY century FORMAT TSVWithNames"""
    U = pd.read_csv(io.StringIO(A.ch_query(sql2, {"cw": ("word String", [(w,) for w in sorted(covered | sw)])})), sep="\t")
    L = ["# Type-norm coverage over arc_fiction (EXPLORATORY)", "",
         "Producer `arc_norm_coverage.py`. Share of a text's content tokens (alphabetic, expanded stopwords out) whose "
         "form a norm source covers; `raw` = the source's own forms, `exp` = plus MorphAdorner variants and long-s "
         "readings. Decade median over texts with >= %d content tokens (%s texts). Set sizes: %s. Warriner's three "
         "scales share one word set; the k lexicon's scales share another." % (
             A.MIN_CONTENT, format(len(D), ","), ", ".join("%s %s" % (k, format(v, ",")) for k, v in info.items())), "",
         "| decade | texts | " + " | ".join(sets) + " |", "|---|---|" + "---|" * len(sets)]
    for dec, r in C.iterrows():
        L.append("| %d | %d | " % (dec, r.n) + " | ".join("%.1f%%" % (100 * r[k]) for k in sets) + " |")
    L += ["", "## Most frequent content forms that no source covers after expansion, per century", ""]
    for cen, g in U.groupby("century"):
        L.append("- C%d: %s" % (cen, ", ".join(g.word.head(60))))
    open(os.path.join(HERE, "ARC_NORM_COVERAGE.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
