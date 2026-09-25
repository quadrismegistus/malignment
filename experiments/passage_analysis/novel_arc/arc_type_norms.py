"""Every type-based norm in fields.py over arc_fiction, with TEMPLATE_ARM meta-text arms. (RH, 2026-09-25)

    .venv/bin/python -u arc_type_norms.py --map        -> $DATA/arc_norm_formmap.parquet  (form -> lexicon word, per source)
    .venv/bin/python -u arc_type_norms.py --count      -> $DATA/arc_type_norms_texts.parquet
    .venv/bin/python -u arc_type_norms.py --arms       -> $DATA/arc_type_norms_meta.parquet
    .venv/bin/python -u arc_type_norms.py --plot       -> figures/arc_type_norms_{human,k}.{png,pdf,caption.txt}, ARC_TYPE_NORMS.md

SCALES. Human norms: Warriner valence, arousal, dominance (1-9); Brysbaert concreteness (1-5). The k lexicon
(fields._k): seven scales rated 1-7 by ONE model (deepseek-v4-flash) out of context -- NOT human norms, and
its own metadata says two are not established (register_level) or sparse (vulgarity). They go on a separate
plate so the two kinds of object are never read as one.

THE MAP (ARC_NORM_COVERAGE.md found what no lexicon covers is inflection, British spelling, old spelling
and long-s OCR, not missing vocabulary). Every alphabetic form in arc_fiction's text_freqs with >= 20 tokens
is mapped to a lexicon entry, per source, by the first rule that lands on one:
  1 the form itself;
  2 its MorphAdorner modern spelling (shew -> show), then rules 1, 3, 4 on that -- unless the form is itself a
    common modern word (zipf >= 3; MorphAdorner maps mary -> marry and wo -> woe);
  3 British -> American respellings, only when the respelled form is in the lexicon: -our -> -or,
    -ise/-ised/-ising -> -ize.., -yse -> -yze, -re -> -er, -ence -> -ense, judgement -> judgment, doubled l;
  4 WordNet's lemma (noun, then verb, then adjective) when that lemma is in the lexicon (desires -> desire);
  5 long-s: a form with no mapping, rare as modern English (wordfreq zipf < 2), whose non-final f's read as s
    (up to three positions) map by rules 1-4 (fhe -> she is a stopword; moft -> most).
Stopwords (arc_interiority's expanded list) never score. A text's value on a scale: the token-weighted mean
of its mapped forms' lexicon values; coverage = mapped tokens / content tokens.

HISTORY and ARMS as the cognitive/emotional plates: decade median over texts (>= 2,000 content tokens,
1600-2009), lowess 0.3; TEMPLATE_ARM 30 lineages (sel12), each model's coherent narrative passages as one
meta-text scored by the same map, median over lineages. EXPLORATORY.
"""
import csv, io, itertools, json, os, re, sys, textwrap

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, REPO)
import arc_interiority as A                                # noqa: E402
from malignment import fields as FD                        # noqa: E402

DATA = A.DATA
MAP = os.path.join(DATA, "arc_norm_formmap.parquet")
TEXTS = os.path.join(DATA, "arc_type_norms_texts.parquet")
META = os.path.join(DATA, "arc_type_norms_meta.parquet")
MIN_FORM = 20
HUMAN = ["warriner_valence", "warriner_arousal", "warriner_dominance", "brysbaert_concreteness"]


def lexicons():
    """-> {source: {word: {scale: value}}}, scales named source_scale."""
    W, B = {}, {}
    for r in csv.DictReader(open(FD.SOURCES["warriner"], encoding="utf-8", errors="replace")):
        w = (r.get("Word") or "").lower()
        try:
            W[w] = {"warriner_valence": float(r["V.Mean.Sum"]), "warriner_arousal": float(r["A.Mean.Sum"]),
                    "warriner_dominance": float(r["D.Mean.Sum"])}
        except (KeyError, ValueError, TypeError):
            pass
    for r in csv.DictReader(open(FD.SOURCES["brysbaert"], encoding="utf-8", errors="replace"), delimiter="\t"):
        w = (r.get("Word") or "").lower()
        try:
            B[w] = {"brysbaert_concreteness": float(r["Conc.M"])}
        except (KeyError, ValueError, TypeError):
            pass
    sc, R, _ = FD._k("en")
    K = {w.lower(): {"k_" + s: float(v) for s, v in zip(sc, vals)} for w, vals in R.items() if vals}
    return {k: {w: v for w, v in d.items() if w.isalpha()} for k, d in {"warriner": W, "brysbaert": B, "k": K}.items()}


BRIT = [(r"our$", "or"), (r"ours$", "ors"), (r"oured$", "ored"), (r"ise$", "ize"), (r"ised$", "ized"), (r"ising$", "izing"),
        (r"isation$", "ization"), (r"yse$", "yze"), (r"ysed$", "yzed"), (r"re$", "er"), (r"res$", "ers"),
        (r"ence$", "ense"), (r"judgement", "judgment"), (r"lled$", "led"), (r"lling$", "ling"), (r"ller$", "ler")]


def mapper(lex):
    from nltk.corpus import wordnet as wn
    wn.ensure_loaded()
    def core(f):
        if f in lex:
            return f, "self"
        for pat, rep in BRIT:
            g = re.sub(pat, rep, f)
            if g != f and g in lex:
                return g, "british"
        for pos in ("n", "v", "a"):
            m = wn.morphy(f, pos)
            if m and m != f and m in lex:
                return m, "lemma"
            if m:
                for pat, rep in BRIT:
                    g = re.sub(pat, rep, m)
                    if g != m and g in lex:
                        return g, "lemma+british"
        return None, None
    return core


def build_map():
    from wordfreq import zipf_frequency
    assert not os.path.exists(MAP), "refusing to overwrite " + MAP
    sql = f"""SELECT k AS word, sum(v) AS n FROM (SELECT _id, freqs FROM lltk.text_freqs FINAL WHERE _id IN ({A.REPS}))
      ARRAY JOIN mapKeys(freqs) AS k, mapValues(freqs) AS v WHERE match(k, '^[a-z]+$') GROUP BY word HAVING n >= {MIN_FORM}
      FORMAT TSVWithNames"""
    V = pd.read_csv(io.StringIO(A.ch_query(sql, {})), sep="\t", keep_default_na=False)
    print("forms with >= %d tokens: %d" % (MIN_FORM, len(V)), flush=True)
    morph = {}
    for line in open(A.MORPH, encoding="utf-8", errors="replace"):
        p = line.rstrip("\n").split("\t")
        if len(p) == 2 and p[0].isalpha() and p[1].isalpha():
            morph.setdefault(p[0].lower(), p[1].lower())
    _, sw, _ = A.lists_expanded()
    L = lexicons()
    rows = []
    for src, lex in L.items():
        core = mapper(lex)
        def full(f):
            t, how = core(f)
            if t:
                return t, how
            #: a common modern word is not an old spelling (MorphAdorner lists mary -> marry, wo -> woe): the
            #: word lists' own filter, zipf >= 3
            if f in morph and zipf_frequency(f, "en") < 3.0:
                t, how = core(morph[f])
                if t:
                    return t, "morph+" + how
            return None, None
        for f in V.word:
            if f in sw:
                continue
            t, how = full(f)
            if not t and "f" in f[:-1] and zipf_frequency(f, "en") < 2.0:
                pos = [i for i, ch in enumerate(f[:-1]) if ch == "f"][:3]
                for r in range(1, len(pos) + 1):
                    for c in itertools.combinations(pos, r):
                        g = "".join("s" if i in c else ch for i, ch in enumerate(f))
                        if g in sw:
                            break
                        t, how = full(g)
                        if t:
                            how = "long_s+" + how
                            break
                    if t or g in sw:
                        break
            if t:
                rows.append((src, f, t, how))
        print("  %s: %d forms mapped" % (src, sum(1 for r in rows if r[0] == src)), flush=True)
    M = pd.DataFrame(rows, columns=["source", "form", "entry", "rule"])
    M.to_parquet(MAP, index=False)
    print(M.groupby(["source", "rule"]).size().unstack(fill_value=0).to_string())


def value_table():
    """-> long (form, scale, value) over the map."""
    L = lexicons()
    M = pd.read_parquet(MAP)
    out = []
    for src, g in M.groupby("source"):
        lex = L[src]
        for f, e in zip(g.form, g.entry):
            for s, v in lex[e].items():
                out.append((f, s, v))
    return pd.DataFrame(out, columns=["form", "scale", "value"])


def count():
    assert not os.path.exists(TEXTS), "refusing to overwrite " + TEXTS
    Vt = value_table()
    print("value rows:", len(Vt), flush=True)
    sql = f"""SELECT f._id AS _id, nw.scale AS scale, sum(f.v * nw.value) AS s, sum(f.v) AS n
      FROM (SELECT _id, k, v FROM (SELECT _id, freqs FROM lltk.text_freqs FINAL WHERE _id IN ({A.REPS}))
            ARRAY JOIN mapKeys(freqs) AS k, mapValues(freqs) AS v) f
      INNER JOIN nw ON f.k = nw.form
      GROUP BY _id, scale FORMAT TSVWithNames"""
    R = pd.read_csv(io.StringIO(A.ch_query(sql, {"nw": ("form String, scale String, value Float64",
                                                       [(a, b, repr(c)) for a, b, c in Vt.itertuples(index=False)])})), sep="\t")
    R["mean"] = R.s / R.n
    W = R.pivot_table(index="_id", columns="scale", values="mean")
    Nn = R.pivot_table(index="_id", columns="scale", values="n").add_prefix("n_")
    D = pd.read_parquet(A.OUT).rename(columns={"r._id": "_id"})[["_id", "year", "corpus", "source", "n_content"]]
    D = D.merge(W.join(Nn).reset_index(), on="_id", how="left", validate="1:1")
    assert len(D) == 82080
    D.to_parquet(TEXTS, index=False)
    print("-> %s" % TEXTS)


def arms():
    """Meta-text per model from arc_history_arms' sel12 passages, scored with the same map."""
    assert not os.path.exists(META), "refusing to overwrite " + META
    sys.argv = [sys.argv[0], "v4", "meta", "sel12"]
    import arc_history_arms as H
    P = pd.read_parquet(H.ARM_OUT)                      # the 30-lineage coherent-narrative population
    TA = H.TA
    S_ = pd.concat([pd.read_parquet(os.path.join(TA, "selection.parquet")),
                    pd.read_parquet(os.path.join(TA, "selection_2.parquet"))]).set_index("id")
    L = lexicons()
    Mf = pd.read_parquet(MAP)
    fmap = {src: dict(zip(g.form, g.entry)) for src, g in Mf.groupby("source")}
    cores = {src: mapper(L[src]) for src in L}
    _, sw, _ = A.lists_expanded()
    rows = []
    for (base, arm, model), g in P.groupby(["base", "arm", "model"]):
        txt = "\n\n".join(S_.loc[i, "text"] or "" for i in g.id).lower()
        toks = [w for w in re.findall(r"[a-z]+", txt) if w not in sw]
        row = dict(base=base, arm=arm, model=model, n_content=len(toks))
        for src, lex in L.items():
            acc, n = {}, 0
            for w in toks:
                e = fmap[src].get(w) or cores[src](w)[0]
                if e:
                    n += 1
                    for s, v in lex[e].items():
                        acc[s] = acc.get(s, 0.0) + v
            for s, v in acc.items():
                row[s] = v / n
            row["cov_" + src] = n / len(toks)
        rows.append(row)
    pd.DataFrame(rows).to_parquet(META, index=False)
    print("-> %s (%d models)" % (META, len(rows)))


def plot():
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["pdf.fonttype"] = 42
    from plotnine import (ggplot, aes, geom_point, geom_line, geom_hline, geom_vline, facet_wrap, labs,
                          scale_linetype_manual, scale_x_continuous, theme, element_text)
    from statsmodels.nonparametric.smoothers_lowess import lowess
    from malignment import figure as F
    T = pd.read_parquet(TEXTS)
    T = T[(T.n_content >= A.MIN_CONTENT) & T.year.between(1600, 2009)]
    assert len(T) == 75974, len(T)
    Mm = pd.read_parquet(META)
    scales = [c for c in T.columns if c.startswith(("warriner_", "brysbaert_", "k_")) and not c.startswith("n_")]
    L_ = ["# Type-based norms over arc_fiction, with TEMPLATE_ARM meta-text arms (EXPLORATORY)", "",
          "Producer `arc_type_norms.py` (method in its docstring). %s texts; %d lineages. Coverage after the map, "
          "decade medians, and each scale's decade range with the arms." % (format(len(T), ","), Mm.base.nunique()), ""]
    Mf = pd.read_parquet(MAP)
    L_ += ["Mapped forms by rule: " + "; ".join("%s: %s" % (src, ", ".join("%s %d" % (r, n) for r, n in g.rule.value_counts().items()))
                                              for src, g in Mf.groupby("source")), ""]
    for group, names, fname in (("human norms", [s for s in scales if s in HUMAN], "human"),
                                ("k lexicon (one model's ratings, not human norms)", [s for s in scales if s.startswith("k_")], "k")):
        H_, C_, Ar = [], [], []
        for s in names:
            d = T[[s, "year"]].dropna()
            for yr in range(1600, 2010, 10):
                t = d[(d.year >= yr) & (d.year < yr + 10)]
                if len(t) >= 3:
                    H_.append(dict(scale=s, year=yr + 5, value=float(t[s].median()), n=len(t)))
        H_ = pd.DataFrame(H_)
        for s, g in H_.groupby("scale"):
            cv = lowess(g.value.values, g.year.values, frac=0.3, return_sorted=True)
            C_ += [dict(scale=s, year=x, value=y) for x, y in cv]
            for a, lab in (("base", "Base models"), ("raw", "Aligned models")):
                Ar.append(dict(scale=s, arm=lab, value=float(Mm[Mm.arm == a][s].median())))
        C_, Ar = pd.DataFrame(C_), pd.DataFrame(Ar)
        lab = {s: s.replace("warriner_", "Warriner ").replace("brysbaert_", "Brysbaert ").replace("k_", "k: ").replace("_", " ") for s in names}
        for df in (H_, C_, Ar):
            df["scale"] = pd.Categorical(df.scale.map(lab), categories=[lab[s] for s in names])
        nrow = (len(names) + 1) // 2
        p = (ggplot()
             + geom_vline(xintercept=[1700, 1800, 1900], color="#e9ecef", size=F.PUB_RULE_PT)
             + geom_point(aes("year", "value"), data=H_, color=F.PUB_GRAY, size=0.6)
             + geom_line(aes("year", "value"), data=C_, color=F.PUB_INK, size=F.PUB_LINE_PT)
             + geom_hline(aes(yintercept="value", linetype="arm"), data=Ar, color=F.PUB_MID, size=F.PUB_RULE_PT * 1.4)
             + scale_linetype_manual({"Base models": "dotted", "Aligned models": "dashed"})
             + facet_wrap("~scale", ncol=2, scales="free_y")
             + scale_x_continuous(breaks=[1600, 1700, 1800, 1900, 2000])
             + labs(x="", y="Token-weighted mean rating", linetype="")
             + F.pub_theme(height=1.7 * nrow + 0.8)
             + theme(legend_position="bottom", figure_size=(F.PUB_SIZE[0], 1.7 * nrow + 0.8),
                     strip_text=element_text(family=F.pub_font(), size=F.PUB_FONT_PT)))
        out = os.path.join(HERE, "figures", "arc_type_norms_" + fname)
        for ext in (".png", ".pdf", ".caption.txt"):
            assert not os.path.exists(out + ext), "refusing to overwrite " + out + ext
        F.save(p, out + ".png")
        cap = textwrap.wrap(("TYPE-BASED NORMS IN FICTION, 1600-2000: %s. Per text the token-weighted mean rating of its "
                             "content words that the lexicon covers after mapping inflections, British and old spellings "
                             "and long-s OCR to lexicon entries; gray points: decade medians over %s arc_fiction texts; "
                             "black line: lowess (span 0.3). Model arms: TEMPLATE_ARM, %d lineages, each model's coherent "
                             "narrative passages as one meta-text scored the same way; the median over lineages."
                             % (group, format(len(T), ","), Mm.base.nunique())) + (
            " The k scales are one model's out-of-context ratings (deepseek-v4-flash), not human norms; register level "
            "is not established as a scale and vulgarity is a sparse indicator (fields.k_warnings)." if fname == "k" else ""), 100)
        open(out + ".caption.txt", "w").write("\n".join(cap) + "\n")
        L_ += ["## %s" % group, "", "| scale | decade min | decade max | base | aligned | aligned - base |", "|---|---|---|---|---|---|"]
        for s in names:
            h = H_[H_.scale == lab[s]]
            b, a = Ar[(Ar.scale == lab[s]) & (Ar.arm == "Base models")].value.iloc[0], Ar[(Ar.scale == lab[s]) & (Ar.arm == "Aligned models")].value.iloc[0]
            L_.append("| %s | %.3f | %.3f | %.3f | %.3f | %+.3f |" % (s, h.value.min(), h.value.max(), b, a, a - b))
        L_.append("")
    cov = T.assign(dec=T.year // 10 * 10)
    L_ += ["## Coverage after the map (share of content tokens scored), decade medians at 1650, 1750, 1850, 1950", ""]
    for src in ("warriner", "brysbaert", "k"):
        ncol = "n_" + {"warriner": "warriner_valence", "brysbaert": "brysbaert_concreteness", "k": "k_valence"}[src]
        c = (cov[ncol] / cov.n_content).groupby(cov.dec).median()
        L_.append("- %s: %s; model meta-texts median %.1f%%" % (src, ", ".join("%d %.1f%%" % (d, 100 * c.get(d, np.nan)) for d in (1650, 1750, 1850, 1950)),
                                                               100 * Mm["cov_" + src].median()))
    open(os.path.join(HERE, "ARC_TYPE_NORMS.md"), "w").write("\n".join(L_) + "\n")
    print("\n".join(L_))


if __name__ == "__main__":
    a = sys.argv
    {"--map": build_map, "--count": count, "--arms": arms, "--plot": plot}.get(next((x for x in a if x.startswith("--")), ""), lambda: print(__doc__))()
