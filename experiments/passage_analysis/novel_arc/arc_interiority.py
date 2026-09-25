"""Interiority word lists over the book's arc_fiction set, from lltk.text_freqs. (RH, 2026-09-25)

    .venv/bin/python -u arc_interiority.py --count [--limit N]   -> $MALIGNMENT_DATA/novel_arc/arc_interiority_texts.parquet
    .venv/bin/python -u arc_interiority.py --report              -> ARC_INTERIORITY.md, figures/arc_interiority_decades.*

QUESTION. Figure 5's interiority panel is USAS X. The LLM-rated "clean X" (1,526 X words with consensus
interior >= 2 and a mental kind) edges it against the blind coder on modern prose; the period-model
candidates (2,161 non-X neighbours that passed the same rating) add nothing there
(INTERIORITY_LISTS_BENCHMARK.md). They were proposed from period models, so the question left is whether
they change the HISTORICAL curve. This measures every list over the texts behind the book's arc figures.

TEXT SET (the abstraction seat): abstraction.scores_rep where arc_corpus = 'arc_fiction' -- 82,080 deduped
reps (oldest member of each match group, English), every one with a lltk.text_freqs row; year from
lltk.texts FINAL. Read over ClickHouse HTTP as the read-only lltk user (readonly=1: writes refused).

WHAT text_freqs HOLDS: lowercased raw surface tokens, no lemma, no POS, NO spelling modernisation, no
long-s correction (fuch, moft, promife appear as-is). So:
  - membership is by SURFACE FORM: a list word matches only as spelled (its inflections are separate
    words, present only where the lexicon or the candidate pool listed them);
  - the denominator is alphabetic tokens minus stopwords, so these shares are comparable across the
    history, NOT on usas_x's scale on model prose;
  - SPELLING. Each list (and the stopword list) is expanded with (a) MorphAdorner variants whose modern
    form is on it (spelling_variants_from_morphadorner.txt: shew, vertue, chuse) and (b) long-s OCR
    variants of each word: every non-final s read as f, in all combinations up to three positions, kept
    only if the variant is not itself a common modern word (wordfreq zipf < 2), so `same` never becomes
    `fame`. Without this, shares rise across 1700-1820 for orthographic reasons alone.
  - CONTROL for what the expansion misses: curves by SOURCE TYPE -- transcribed (chadwyck, earlyprint,
    eebo_tcp, ecco_tcp, evans_tcp, clmet, litlab) against OCR (hathi_englit, gale_amfic, blbooks, bpo,
    internet_archive), with modern/other (coha, chicago, markmark, gildedage, long_arc_prestige, tedjdh)
    beside them. A spelling artefact lives in the OCR group.

LISTS: full X (every primary-sense USAS X word, the usas_x analogue, 3,225), clean X (1,526), candidates
(2,161), clean X + candidates. EXPLORATORY.
"""
import io, itertools, json, os, sys, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE); sys.path.insert(0, REPO)
DATA = os.path.join(os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data")), "novel_arc")
SHARED = os.path.expanduser("~/malignment-data/interiority_norms")
MORPH = "/Volumes/diderot/DH/data/data_abslithist/fields/spelling_variants_from_morphadorner.txt"
OUT = os.path.join(DATA, "arc_interiority_texts.parquet")
CH = "http://localhost:8123/"
SOURCE = {**{c: "transcribed" for c in ("chadwyck", "earlyprint", "eebo_tcp", "ecco_tcp", "evans_tcp", "clmet", "litlab")},
          **{c: "ocr" for c in ("hathi_englit", "gale_amfic", "blbooks", "bpo", "internet_archive")},
          **{c: "modern/other" for c in ("coha", "chicago", "markmark", "gildedage", "long_arc_prestige", "tedjdh")}}
LISTS = ("fullx", "cleanx", "cand", "comb")
LABEL = {"fullx": "Full USAS X", "cleanx": "Clean X", "cand": "Period candidates", "comb": "Clean X + candidates"}


def base_lists():
    import pandas as pd
    import interiority_xe as IX
    L = IX.word_lists()
    return {"fullx": L["full X list (3,225)"], "cleanx": L["clean X (1,526)"], "cand": L["new candidates (2,161)"]}


def long_s(w, zipf):
    """Long-s OCR readings of w: non-final s -> f, all combinations over up to three positions."""
    pos = [i for i, ch in enumerate(w[:-1]) if ch == "s"]
    out = set()
    if not pos:
        return out
    combos = (itertools.chain.from_iterable(itertools.combinations(pos, r) for r in range(1, len(pos) + 1))
              if len(pos) <= 3 else [tuple(pos)])
    for c in combos:
        v = "".join("f" if i in c else ch for i, ch in enumerate(w))
        if zipf(v, "en") < 2.0:
            out.add(v)
    return out


def expand(words, morph, zipf):
    """words + MorphAdorner variants mapping onto them + long-s variants of both. -> (set, n_morph, n_longs)"""
    out = set(words)
    mv = {v for v, m in morph if m in words}
    out |= mv
    ls = set()
    for w in list(out):
        ls |= long_s(w, zipf)
    out |= ls
    return {w for w in out if w.isalpha()}, len(mv - set(words)), len(ls - out.intersection(words))


def lists_expanded():
    from nltk.corpus import stopwords
    from wordfreq import zipf_frequency
    morph = []
    for line in open(MORPH, encoding="utf-8", errors="replace"):
        p = line.rstrip("\n").split("\t")
        if len(p) == 2 and p[0].isalpha() and p[1].isalpha():
            morph.append((p[0].lower(), p[1].lower()))
    B = base_lists()
    ex, info = {}, {}
    for k, ws in B.items():
        ex[k], nm, nl = expand(ws, morph, zipf_frequency)
        info[k] = dict(base=len(ws), expanded=len(ex[k]), morph_variants=nm, long_s_variants=nl)
    ex["comb"] = ex["cleanx"] | ex["cand"]
    info["comb"] = dict(base=len(B["cleanx"] | B["cand"]), expanded=len(ex["comb"]))
    sw, _, _ = expand(set(stopwords.words("english")), morph, zipf_frequency)
    info["stopwords"] = dict(base=len(stopwords.words("english")), expanded=len(sw))
    #: a list word that is also a stopword (after expansion) would count in the numerator but not the
    #: denominator; drop it from the lists, and say how many
    for k in LISTS:
        clash = ex[k] & sw
        info[k]["dropped_as_stopword"] = len(clash)
        ex[k] -= clash
    return ex, sw, info


def ch_query(sql, externals):
    """POST a query with external tables (read-only user). -> TSV text"""
    boundary = "----arcinteriority"
    body = io.BytesIO()
    params = {"user": "lltk", "password": "lltk", "readonly": "1"}
    for name, (structure, rows) in externals.items():
        params[name + "_structure"] = structure
        params[name + "_format"] = "TSV"
        body.write(("--%s\r\nContent-Disposition: form-data; name=\"%s\"; filename=\"%s\"\r\n\r\n"
                    % (boundary, name, name)).encode())
        body.write("\n".join("\t".join(r) for r in rows).encode() + b"\n\r\n")
    body.write(("--%s\r\nContent-Disposition: form-data; name=\"query\"\r\n\r\n%s\r\n--%s--\r\n"
                % (boundary, sql, boundary)).encode())
    req = urllib.request.Request(CH + "?" + urllib.parse.urlencode(params), data=body.getvalue(),
                                 headers={"Content-Type": "multipart/form-data; boundary=" + boundary})
    with urllib.request.urlopen(req, timeout=3600) as r:
        return r.read().decode()


REPS = "SELECT _id FROM abstraction.scores_rep WHERE arc_corpus = 'arc_fiction'"


def count(limit=None):
    import pandas as pd
    ex, sw, info = lists_expanded()
    print(json.dumps(info, indent=1))
    lw = [(w, k) for k in ("fullx", "cleanx", "cand") for w in sorted(ex[k])]
    ids = REPS + (" ORDER BY _id LIMIT %d" % limit if limit else "")
    sql = f"""
      SELECT r._id, t.year, t.corpus, a.n_content, a.n_fullx, a.n_cleanx, a.n_cand, a.n_comb
      FROM ({ids}) r
      INNER JOIN (SELECT _id, year, corpus FROM lltk.texts FINAL WHERE _id IN ({ids})) t ON r._id = t._id
      INNER JOIN (
        SELECT _id,
          sumIf(v, match(k, '^[a-z]+$') AND k NOT IN (SELECT word FROM sw)) AS n_content,
          sumIf(v, k IN (SELECT word FROM lw WHERE list = 'fullx')) AS n_fullx,
          sumIf(v, k IN (SELECT word FROM lw WHERE list = 'cleanx')) AS n_cleanx,
          sumIf(v, k IN (SELECT word FROM lw WHERE list = 'cand')) AS n_cand,
          sumIf(v, k IN (SELECT word FROM lw WHERE list IN ('cleanx', 'cand'))) AS n_comb
        FROM (SELECT _id, freqs FROM lltk.text_freqs FINAL WHERE _id IN ({ids}))
        ARRAY JOIN mapKeys(freqs) AS k, mapValues(freqs) AS v
        GROUP BY _id) a ON r._id = a._id
      FORMAT TSVWithNames"""
    txt = ch_query(sql, {"lw": ("word String, list String", lw), "sw": ("word String", [(w,) for w in sorted(sw)])})
    D = pd.read_csv(io.StringIO(txt), sep="\t")
    D["source"] = D.corpus.map(SOURCE).fillna("unclassified")
    if not limit:
        assert len(D) == 82080, len(D)
        D.to_parquet(OUT, index=False)
        json.dump(info, open(OUT.replace(".parquet", "_lists.json"), "w"), indent=1)
        print("-> %s (%d texts)" % (OUT, len(D)))
    else:
        print(D.head(10).to_string()); print(len(D), "texts; sources", D.source.value_counts().to_dict())
    return D


MIN_CONTENT, MIN_TEXTS = 2000, 5


def top_candidates(key="cand"):
    """A list's words carrying the most tokens, by century and source group (the spelling check)."""
    import pandas as pd
    ex, sw, info = lists_expanded()
    rows = [(w,) for w in sorted(ex[key])]
    sql = f"""
      SELECT intDiv(t.year, 100) + 1 AS century, t.corpus, k AS word, sum(v) AS n
      FROM (SELECT _id, freqs FROM lltk.text_freqs FINAL WHERE _id IN ({REPS})) f
      INNER JOIN (SELECT _id, year, corpus FROM lltk.texts FINAL WHERE _id IN ({REPS})) t ON f._id = t._id
      ARRAY JOIN mapKeys(f.freqs) AS k, mapValues(f.freqs) AS v
      WHERE k IN (SELECT word FROM cw)
      GROUP BY century, t.corpus, word
      FORMAT TSVWithNames"""
    T = pd.read_csv(io.StringIO(ch_query(sql, {"cw": ("word String", rows)})), sep="\t")
    T["source"] = T.corpus.map(SOURCE).fillna("unclassified")
    return T.groupby(["century", "source", "word"]).n.sum().reset_index()


def report():
    import numpy as np
    import pandas as pd
    import matplotlib
    matplotlib.use("Agg")
    from plotnine import (ggplot, aes, geom_line, geom_point, facet_wrap, labs, scale_color_manual,
                          scale_linetype_manual, theme, element_text, guides, guide_legend)
    from scipy.stats import spearmanr
    from malignment import figure as F
    D = pd.read_parquet(OUT)
    info = json.load(open(OUT.replace(".parquet", "_lists.json")))
    D = D[(D.n_content >= MIN_CONTENT) & D.year.between(1600, 2009)].copy()
    for k in LISTS:
        D[k] = D["n_" + k] / D.n_content
    D["decade"] = (D.year // 10) * 10
    rows = []
    for (src, dec), g in D.groupby(["source", "decade"]):
        if len(g) >= MIN_TEXTS:
            rows.append(dict(source=src, decade=dec, n=len(g), **{k: float(g[k].median()) for k in LISTS}))
    C = pd.DataFrame(rows)
    C = C[C.source != "unclassified"]
    #: shapes, not levels: each list's decade medians over its own mean within the source group
    long = []
    for src, g in C.groupby("source"):
        for k in LISTS:
            long += [dict(source=src, decade=r.decade, list=LABEL[k], index=getattr(r, k) / g[k].mean())
                     for r in g.itertuples()]
    Lg = pd.DataFrame(long)
    order = [LABEL[k] for k in LISTS]
    Lg["list"] = pd.Categorical(Lg.list, categories=order)
    Lg["source"] = pd.Categorical(Lg.source, categories=["transcribed", "ocr", "modern/other"])
    p = (ggplot(Lg, aes("decade", "index", color="list", linetype="list"))
         + geom_line(size=0.7) + geom_point(size=0.8)
         + facet_wrap("~source", ncol=1)
         + guides(color=guide_legend(nrow=2), linetype=guide_legend(nrow=2))   # one row ran off the canvas
         + scale_color_manual({order[0]: F.PUB_GRAY, order[1]: F.PUB_INK, order[2]: F.PUB_MID, order[3]: F.PUB_INK})
         + scale_linetype_manual({order[0]: "solid", order[1]: "solid", order[2]: "dotted", order[3]: "dashed"})
         + labs(x="", y="Decade median share / its mean over decades", color="", linetype="")
         + F.pub_theme(height=6.0) + theme(legend_position="bottom", figure_size=(F.PUB_SIZE[0], 6.0),
                                           strip_text=element_text(family=F.pub_font(), size=F.PUB_FONT_PT)))
    fig = os.path.join(HERE, "figures", "arc_interiority_decades")
    for ext in (".png", ".pdf"):
        assert not os.path.exists(fig + ext), "refusing to overwrite " + fig + ext
    F.save(p, fig + ".png")
    T = top_candidates()
    L = ["# Interiority word lists over the arc_fiction set (EXPLORATORY)", "",
         "Producer `arc_interiority.py`. %d arc_fiction reps (abstraction.scores_rep), share of alphabetic "
         "non-stopword tokens (lltk.text_freqs, surface forms) on each list; texts with at least %d such tokens "
         "(%d texts); decade median over texts, decades with at least %d texts per source group. Lists and their "
         "spelling expansion (MorphAdorner variants plus long-s OCR variants not common as modern words): %s. "
         "Plate: figures/arc_interiority_decades.png (each list indexed to its own mean, to compare shapes)." % (
             82080, MIN_CONTENT, len(D), MIN_TEXTS, "; ".join("%s %d -> %d" % (LABEL.get(k, k), v["base"], v["expanded"])
                                                            for k, v in info.items() if k in LABEL)), "",
         "## Do the period candidates change the history? Decade-series agreement with clean X", "",
         "| source | decades | span | rho(clean X, clean X + candidates) | rho(clean X, candidates) | rho(clean X, full X) |",
         "|---|---|---|---|---|---|"]
    for src, g in C.groupby("source"):
        L.append("| %s | %d | %d-%d | %+.3f | %+.3f | %+.3f |" % (
            src, len(g), g.decade.min(), g.decade.max(), spearmanr(g.cleanx, g.comb)[0],
            spearmanr(g.cleanx, g.cand)[0], spearmanr(g.cleanx, g.fullx)[0]))
    L += ["", "## Decade medians (percent of content tokens)", "",
          "| source | decade | texts | full X | clean X | candidates | clean X + candidates |", "|---|---|---|---|---|---|---|"]
    for r in C.sort_values(["source", "decade"]).itertuples():
        L.append("| %s | %d | %d | %.2f | %.2f | %.2f | %.2f |" % (r.source, r.decade, r.n, 100 * r.fullx,
                                                                 100 * r.cleanx, 100 * r.cand, 100 * r.comb))
    L += ["", "## Candidate words carrying the most tokens, by century and source (the spelling check)", ""]
    for (cen, src), g in T.groupby(["century", "source"]):
        if src == "unclassified":
            continue
        g = g.sort_values("n", ascending=False)
        tot = g.n.sum()
        L.append("- C%d %s: %s" % (cen, src, ", ".join("%s %.1f%%" % (w, 100 * n / tot) for w, n in zip(g.word.head(15), g.n.head(15)))))
    #: CONCENTRATION: surface-form counting cannot tell `like` the verb from `like` the preposition, or
    #: `would` the volition from the modal; if a few such words carry most of a list's tokens, the list's
    #: curve is theirs
    L += ["", "## Token-mass concentration: share of a list's tokens carried by its most frequent words (all texts)", ""]
    for key, TT in (("cleanx", top_candidates("cleanx")), ("cand", T)):
        tot = TT.groupby("word").n.sum().sort_values(ascending=False)
        cum = tot.cumsum() / tot.sum()
        L.append("- %s: top 10 %.0f%%, top 25 %.0f%%, top 50 %.0f%%, top 100 %.0f%% of %d words with any tokens. "
                 "Top 25: %s" % (LABEL[key], 100 * cum.iloc[9], 100 * cum.iloc[24], 100 * cum.iloc[49], 100 * cum.iloc[99],
                                 len(tot), ", ".join("%s %.1f%%" % (w, 100 * n / tot.sum()) for w, n in tot.head(25).items())))
        tot.reset_index().rename(columns={"n": "tokens"}).to_csv(
            os.path.join(SHARED, "arc_token_mass_%s.csv" % key), index=False)
    open(os.path.join(HERE, "ARC_INTERIORITY.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L[:20]))


if __name__ == "__main__":
    a = sys.argv
    if "--report" in a:
        report()
    elif "--count" in a:
        count(int(a[a.index("--limit") + 1]) if "--limit" in a else None)
    else:
        print(__doc__)
