"""Valence components on the CLEANED lexicon: negative and positive words per content word, and their intensity,
history with national-story arms. (RH, 2026-09-26, after valence_lexicon_clean.py)

    .venv/bin/python -u arc_valence_clean_components.py   -> ARC_VALENCE_CLEAN.md, figures/arc_valence_clean_v1.{png,pdf,caption.txt}

LEXICON (valence_clean_keep_v1.csv). A form scores when:
  - it is a KEPT polar Warriner lemma (value: Warriner's rating); or
  - arc_type_norms' map sends it to a kept lemma, and, if the form itself was rated, the form was kept too; or
  - (+vector version only) it is a KEPT vector negative-pole candidate, direction confirmed by the rater (value: the
    rater's 1-9 valence; must be < 4).
Neutral-band Warriner words (4-6) never score: per content word they are simply not counted.
MEASURES per text: negative rate = negative tokens / content tokens; positive rate likewise; negative intensity = mean
(5 - v) over negative tokens; positive intensity = mean (v - 5) over positive tokens. Content tokens = lowercased
alphabetic tokens minus arc_interiority's expanded stopwords (the history's own n_content). Per CONTENT word, so adding
vector negatives cannot move the denominator (RH: positive words are not needed for negative share).
HISTORY: Chadwyck and Chicago arc_fiction reps via lltk.text_freqs, 1600-2009, n_content >= 2,000, decade medians
(>= 3 texts), lowess 0.3. ARMS: judged no-demonym national stories, one meta-text per model-condition, median over
lineages; lineage sign tests unpartialled and with the within-condition concreteness partial. EXPLORATORY.
"""
import io, os, re, sys, textwrap

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.argv = [sys.argv[0], "v4", "meta", "sel12", "arms4"]
import arc_interiority as A                              # noqa: E402
import arc_type_norms as N                               # noqa: E402
import arc_history_arms as H                             # noqa: E402
from malignment import figure as F                       # noqa: E402

SH = os.path.expanduser("~/malignment-data/interiority_norms")
KEEP = os.path.join(SH, "valence_clean_keep_v1.csv")
TEXTS = os.path.join(A.DATA, "valence_clean_texts_cc.parquet")
OUT = os.path.join(HERE, "figures", "arc_valence_clean_v1")
COMPS = [("neg_rate", "Negative words per content word"), ("neg_int", "Negative intensity"),
         ("pos_rate", "Positive words per content word"), ("pos_int", "Positive intensity")]
CONC = "Abs-Conc.Median.median"


def lexicons():
    """-> {'human': {form: v}, '+vector': {form: v}}"""
    K = pd.read_csv(KEEP, keep_default_na=False, na_values=[""])
    K = K.set_index("form")
    val = {w: d["warriner_valence"] for w, d in N.lexicons()["warriner"].items()}
    kept_lem = {w for w, r in K[K.kind == "lemma"].iterrows() if r.keep}
    rated_form = {w: bool(r.keep) for w, r in K[K.kind == "form"].iterrows()}
    human = {w: val[w] for w in kept_lem}
    Mf = pd.read_parquet(N.MAP)
    for f, e in zip(*[Mf[Mf.source == "warriner"][c] for c in ("form", "entry")]):
        if e in kept_lem and rated_form.get(f, True) and f not in human:
            human[f] = val[e]
    vec = dict(human)
    for w, r in K[(K.kind == "vector") & K.keep.astype(bool)].iterrows():
        if pd.notna(r.llm_valence) and float(r.llm_valence) < 4:
            vec[w] = float(r.llm_valence)
    return {"human": human, "+vector": vec}


def stats(counts, n_content, lex):
    neg = pos = sneg = spos = 0.0
    for w, c in counts:
        v = lex.get(w)
        if v is None:
            continue
        if v < 4:
            neg += c; sneg += c * (5 - v)
        elif v > 6:
            pos += c; spos += c * (v - 5)
    return dict(neg_rate=neg / n_content, pos_rate=pos / n_content,
                neg_int=sneg / neg if neg else np.nan, pos_int=spos / pos if pos else np.nan)


def history(L):
    if os.path.exists(TEXTS):
        return pd.read_parquet(TEXTS)
    rows = []
    C = pd.read_parquet(H.COUNTS)[["_id", "n_content"]]
    for name, lex in L.items():
        sql = f"""SELECT f._id AS _id, sumIf(f.v, w.val < 4) AS neg, sumIf(f.v, w.val > 6) AS pos,
              sumIf(f.v * (5 - w.val), w.val < 4) AS sneg, sumIf(f.v * (w.val - 5), w.val > 6) AS spos
          FROM (SELECT _id, k, v FROM (SELECT _id, freqs FROM lltk.text_freqs FINAL WHERE _id IN ({A.REPS})
                  AND _id IN (SELECT _id FROM lltk.texts FINAL WHERE corpus IN ('chadwyck', 'chicago')))
                ARRAY JOIN mapKeys(freqs) AS k, mapValues(freqs) AS v) f
          INNER JOIN w ON f.k = w.form GROUP BY _id FORMAT TSVWithNames"""
        R = pd.read_csv(io.StringIO(A.ch_query(sql, {"w": ("form String, val Float64", [(a, repr(b)) for a, b in lex.items()])})), sep="\t")
        R = R.merge(C, on="_id")
        for r in R.itertuples():
            rows.append(dict(_id=r._1, lexicon=name, n_content=r.n_content, neg_rate=r.neg / r.n_content, pos_rate=r.pos / r.n_content,
                             neg_int=r.sneg / r.neg if r.neg else np.nan, pos_int=r.spos / r.pos if r.pos else np.nan))
    D = pd.DataFrame(rows)
    D.to_parquet(TEXTS, index=False)
    return D


def meta(L):
    _, sw, _ = A.lists_expanded()
    M = pd.read_parquet(os.path.join(A.DATA, "prompt_check_national_judged_meta.parquet"))
    conc = pd.read_parquet(os.path.join(A.DATA, "prompt_check_national_judged_meta_scored.parquet"))[["id", CONC]]
    rows = []
    for r in M.itertuples():
        toks = [w for w in re.findall(r"[a-z]+", r.text.lower()) if w not in sw]
        cnt = pd.Series(toks).value_counts()
        for name, lex in L.items():
            rows.append(dict(id=r.id, lineage=r.lineage, cond=r.cond, lexicon=name, **stats(cnt.items(), len(toks), lex)))
    return pd.DataFrame(rows).merge(conc, on="id")


def main():
    from scipy.stats import binomtest
    from statsmodels.nonparametric.smoothers_lowess import lowess
    for ext in (".png", ".pdf", ".caption.txt"):
        assert not os.path.exists(OUT + ext), "refusing to overwrite " + OUT + ext
    L = lexicons()
    Th = history(L).merge(H.concreteness_texts()[["_id", "year"]], on="_id")
    Th = Th[Th.year.between(1600, 2009) & (Th.n_content >= H.MIN_CONTENT)]
    Mm = meta(L)
    conds = ["base", "aligned_raw", "aligned_prefill", "aligned_rettberg"]
    arm = {"base": "base", "aligned_raw": "raw", "aligned_prefill": "prefill", "aligned_rettberg": "continue"}
    R = ["# Valence components on the cleaned lexicon (EXPLORATORY)", "",
         "Producer `arc_valence_clean_components.py` (method in its docstring). Lexicon sizes (scoring forms): " +
         ", ".join("%s %s" % (k, format(len(v), ",")) for k, v in L.items()) + ". History: %s Chadwyck and Chicago texts." % format(Th._id.nunique(), ","), "",
         "| component | lexicon | history range | base | aligned raw / prefill / asked | lineages unpartialled | lineages, within-condition concreteness partial |",
         "|---|---|---|---|---|---|---|"]
    pts, cvs, arms_, order = [], [], [], []
    for c, clab in COMPS:
        for name in L:
            h = Th[Th.lexicon == name][["year", c]].dropna()
            dec = H.decades(h.year, h[c])
            cv = lowess(dec.value.values, dec.year.values, frac=0.3, return_sorted=True)
            lo, hi = cv[:, 1].min(), cv[:, 1].max()
            m = Mm[Mm.lexicon == name].dropna(subset=[c, CONC])

            def lin(y):
                piv = m.assign(y=y).pivot_table(index="lineage", columns="cond", values="y")
                med = piv.median()
                out = []
                for cd in conds[1:]:
                    dd = piv[["base", cd]].dropna()
                    sgn = np.sign(med[cd] - med["base"])
                    k = int((np.sign(dd[cd] - dd["base"]) == sgn).sum())
                    out.append("%s %d/%d (p %.3f)" % ("up" if sgn > 0 else "down", k, len(dd), binomtest(k, len(dd)).pvalue))
                return " / ".join(out)
            yd = m[c] - m.groupby("cond")[c].transform("mean")
            xd = m[CONC] - m.groupby("cond")[CONC].transform("mean")
            bw = float(np.polyfit(xd, yd, 1)[0])
            med = m.pivot_table(index="lineage", columns="cond", values=c).median()
            place = lambda v: "%.4f (%s)" % (v, "above all" if v > hi else "below all" if v < lo else "inside")
            R.append("| %s | %s | %.4f to %.4f | %s | %s | %s | %s |" % (clab, name, lo, hi, place(med["base"]),
                     " / ".join(place(med[k]) for k in conds[1:]), lin(m[c]), lin(m[c] - bw * m[CONC])))
            pname = "%s: %s" % (clab, name)
            order.append(pname)
            pts += [dict(panel=pname, year=y, value=v) for y, v in zip(dec.year, dec.value)]
            cvs += [dict(panel=pname, year=x, value=y) for x, y in cv]
            arms_ += [dict(panel=pname, arm=H.NAME[arm[k]], value=float(med[k])) for k in conds]
    open(os.path.join(HERE, "ARC_VALENCE_CLEAN.md"), "w").write("\n".join(R) + "\n")
    print("\n".join(R))
    P, C, A_ = pd.DataFrame(pts), pd.DataFrame(cvs), pd.DataFrame(arms_)
    for df in (P, C, A_):
        df["panel"] = pd.Categorical(df.panel, categories=order)
    A_["arm"] = pd.Categorical(A_.arm, categories=[H.NAME[k] for k in ("base", "raw", "prefill", "continue")])
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["pdf.fonttype"] = 42
    from plotnine import (ggplot, aes, geom_point, geom_line, geom_hline, facet_wrap, labs, scale_linetype_manual,
                          scale_x_continuous, theme, element_text)
    p = (ggplot()
         + geom_point(aes("year", "value"), data=P, color=F.PUB_GRAY, size=0.6)
         + geom_line(aes("year", "value"), data=C, color=F.PUB_INK, size=F.PUB_LINE_PT)
         + geom_hline(aes(yintercept="value", linetype="arm"), data=A_, color=F.PUB_MID, size=F.PUB_RULE_PT * 1.2)
         + scale_linetype_manual({H.NAME["base"]: "dotted", H.NAME["raw"]: "dashed", H.NAME["prefill"]: "dashdot", H.NAME["continue"]: "solid"})
         + facet_wrap("~panel", ncol=2, scales="free_y")
         + scale_x_continuous(breaks=[1600, 1700, 1800, 1900, 2000])
         + labs(x="", y="Rate per content word / mean distance from neutral", linetype="")
         + F.pub_theme(height=8.0)
         + theme(legend_position="bottom", figure_size=(7.5, 8.0), strip_text=element_text(family=F.pub_font(), size=F.PUB_FONT_PT)))
    F.save(p, OUT + ".png")
    open(OUT + ".caption.txt", "w").write("\n".join(textwrap.wrap(
        "VALENCE COMPONENTS ON THE CLEANED LEXICON: negative and positive words per content word and their mean distance "
        "from neutral (5), 1600-2000. Left: kept Warriner lemmas and their kept forms; right: plus the vector negative-pole "
        "candidates the rater confirmed (their 1-9 rating as value). Chadwyck and Chicago arc_fiction, decade medians, "
        "lowess; lines: national-story arms, median over lineages.", 100)) + "\n")


if __name__ == "__main__":
    main()
