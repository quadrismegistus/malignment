"""Smell test for negative share: which words make up the negative mass, and what negative passages look like, across
history and in the models. (RH, 2026-09-26: "examples of negative passages across history and in the models")

    .venv/bin/python -u arc_negative_examples.py   -> ARC_NEGATIVE_EXAMPLES.md

Scoring is arc_valence_lemma_check.py's MAPPED Warriner lookup: lowercased [a-z]+ tokens, expanded stopwords out,
forms mapped to Warriner entries (arc_type_norms' map, the same mapper for unseen forms); a scored token is NEGATIVE
if its valence is below 4 (neutral band 4-6).
GROUPS. History: lltk.passages (p500) of Chadwyck and Chicago arc_fiction reps, a deterministic sample of up to 1,500
per century (cityHash64 order), 1700s, 1800s, 1900s. Models: the judged no-demonym national stories (whole pure
stories or spliced before degeneration; arc_prompt_check.splice), endpoint lineages, each story's first 500 words,
for base, aligned raw and aligned chat-asked.
PER GROUP: (1) the negative words carrying the most negative tokens, as shares of the group's negative tokens; (2)
two passages at the group's 90th percentile of negative share and one at its median, each excerpted as the ~60-word
window densest in negative words, negative words [bracketed] with their rating. EXPLORATORY.
"""
import io, json, os, re, sys, collections

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, REPO)
import arc_interiority as A                                # noqa: E402
import arc_type_norms as N                                 # noqa: E402

WIN, PER = 60, 1500
#: words the smell test found carrying negative mass without negative meaning in context (RH's smell test,
#: 2026-09-26): old (3.2; "old man"), means/meant lemmatised to `mean` (2.4, as in cruel), cried (the period speech
#: tag), and ordinary nouns and verbs. Recounted without them as a robustness check; not a new lexicon.
SUSPECT = {"old", "mean", "means", "meant", "cried", "late", "distance", "weight", "cut", "court"}


def scorer():
    lex = N.lexicons()["warriner"]
    val = {w: d["warriner_valence"] for w, d in lex.items()}
    Mf = pd.read_parquet(N.MAP)
    fm = dict(zip(Mf[Mf.source == "warriner"].form, Mf[Mf.source == "warriner"].entry))
    core = N.mapper(lex)
    _, sw, _ = A.lists_expanded()
    cache = {}

    def entry(w):
        if w not in cache:
            cache[w] = fm.get(w) or core(w)[0]
        return cache[w]

    def score(text):
        toks = [w for w in re.findall(r"[a-z]+", (text or "").lower()) if w not in sw]
        sc = [(w, val[e]) for w in toks if (e := entry(w))]
        neg = [(w, v) for w, v in sc if v < 4]
        sc2 = [(w, v) for w, v in sc if w not in SUSPECT]
        neg2 = [(w, v) for w, v in sc2 if v < 4]
        return dict(n_scored=len(sc), neg_share=len(neg) / len(sc) if sc else np.nan, neg=neg,
                    neg_share_clean=len(neg2) / len(sc2) if sc2 else np.nan)

    def marked(text):
        """-> (excerpt with [negative] words marked, list of negatives in it)"""
        parts = re.findall(r"[A-Za-z]+|[^A-Za-z]+", text or "")
        words = [i for i, p in enumerate(parts) if p[0].isalpha()]
        isneg = []
        for i in words:
            w = parts[i].lower()
            e = None if w in sw else entry(w)
            isneg.append(e is not None and val[e] < 4)
        if len(words) > WIN:
            cs = np.concatenate([[0], np.cumsum(isneg)])
            j = int(np.argmax(cs[WIN:] - cs[:-WIN]))
        else:
            j = 0
        lo, hi = words[j], words[min(j + WIN, len(words)) - 1] + 1
        out = []
        for k in range(lo, hi):
            p = parts[k]
            if p[0].isalpha() and isneg[words.index(k)]:
                out.append("[%s %.1f]" % (p, val[entry(p.lower())]))
            else:
                out.append(p)
        return re.sub(r"\s+", " ", "".join(out)).strip()
    return score, marked


def history_passages():
    sql = f"""SELECT p._id AS _id, p.seq AS seq, p.text AS text, t.year AS year, t.title AS title, t.author AS author
      FROM lltk.passages p INNER JOIN (SELECT _id, year, title, author FROM lltk.texts FINAL
            WHERE _id IN ({A.REPS}) AND corpus IN ('chadwyck', 'chicago')) t ON p._id = t._id
      WHERE p.lang = 'en' AND t.year BETWEEN 1700 AND 1999
      ORDER BY intDiv(t.year, 100), cityHash64(p._id, p.seq) LIMIT {PER} BY intDiv(t.year, 100)
      FORMAT TSVWithNames"""
    P = pd.read_csv(io.StringIO(A.ch_query(sql, {})), sep="\t", keep_default_na=False, quoting=3)
    unesc = lambda t: re.sub(r"\\(.)", lambda m: {"n": "\n", "t": "\t", "r": ""}.get(m.group(1), m.group(1)), t)
    for c in ("text", "title", "author"):
        P[c] = P[c].map(unesc)
    P["text"] = P.text.str.replace("\\n", "\n", regex=False)
    P["group"] = "novels " + (P.year // 100 * 100).astype(str) + "s"
    P["source"] = [("%s, %s (%d)" % (a or "anon.", (t or "")[:60], y)) for a, t, y in zip(P.author, P.title, P.year)]
    return P[["group", "source", "text"]]


def model_passages():
    import arc_prompt_check as PC
    from malignment import roster
    EPS = roster.endpoints()[0]
    rows = []
    for line in open(os.path.expanduser("~/malignment-data/national_story/judged_stories_v2.jsonl"), encoding="utf-8"):
        r = json.loads(line)
        if r["demonym"] != "none":
            continue
        lin, arm, fr, m = r["lineage"], r["arm"], r["frame"], r["model"]
        ok = (arm == "base" and m == lin and fr == "raw") or (arm == "aligned" and m == EPS.get(lin) and fr in ("raw", "rettberg"))
        if not ok:
            continue
        t, _ = PC.splice(r)
        if not t:
            continue
        g = {"raw": "models: base", "rettberg": "models: aligned, chat, asked"}[fr] if arm == "base" or fr == "rettberg" else "models: aligned, raw"
        if arm == "base":
            g = "models: base"
        rows.append(dict(group=g, source=m, text=" ".join(t.split()[:500])))
    return pd.DataFrame(rows)


def main():
    score, marked = scorer()
    P = pd.concat([history_passages(), model_passages()], ignore_index=True)
    S = pd.DataFrame([score(t) for t in P.text])
    P = pd.concat([P, S], axis=1)
    P = P[P.n_scored >= 60]
    order = ["novels 1700s", "novels 1800s", "novels 1900s", "models: base", "models: aligned, raw", "models: aligned, chat, asked"]
    L = ["# Negative share: words and passages, history and models (EXPLORATORY)", "",
         "Producer `arc_negative_examples.py` (method in its docstring). Negative = mapped Warriner valence below 4. Passages "
         "with at least 60 scored words.", "",
         "| group | passages | median negative share | 90th percentile | median, suspect words removed |", "|---|---|---|---|---|"]
    for g in order:
        s = P[P.group == g]
        L.append("| %s | %d | %.3f | %.3f | %.3f |" % (g, len(s), s.neg_share.median(), s.neg_share.quantile(0.9), s.neg_share_clean.median()))
    L += ["", "Suspect words (removed from both numerator and denominator in the last column): " + ", ".join(sorted(SUSPECT))]
    for g in order:
        G = P[P.group == g]
        cnt = collections.Counter(w for negs in G.neg for w, _ in negs)
        tot = sum(cnt.values())
        L += ["", "## %s" % g, "", "Negative words carrying the most negative tokens (share of the group's negative tokens): " +
              ", ".join("%s %.1f%%" % (w, 100 * c / tot) for w, c in cnt.most_common(30)), ""]
        q90, q50 = G.neg_share.quantile(0.9), G.neg_share.median()
        picks = [("90th percentile", r) for r in G.iloc[(G.neg_share - q90).abs().argsort()[:2]].itertuples()] + \
                [("median", r) for r in G.iloc[(G.neg_share - q50).abs().argsort()[:1]].itertuples()]
        for lab, r in picks:
            L += ["- **%s**, negative share %.3f -- %s" % (lab, r.neg_share, r.source), "", "  > %s" % marked(r.text), ""]
    open(os.path.join(HERE, "ARC_NEGATIVE_EXAMPLES.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
