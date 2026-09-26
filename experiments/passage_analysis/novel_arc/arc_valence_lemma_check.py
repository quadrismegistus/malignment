"""Does the surface-form Warriner lookup's coverage gap move the valence components? (RH, 2026-09-26)

    .venv/bin/python -u arc_valence_lemma_check.py           -> ARC_VALENCE_LEMMA_CHECK.md, figures/arc_valence_lemma_check_v1.*
    .venv/bin/python -u arc_valence_lemma_check.py partial   -> ARC_VALENCE_LEMMA_CHECK_partial.md (RH, 2026-09-26: "Does
        partialing out concreteness affect it"): for each component and lookup, (a) the lineage test with the slope on
        concreteness fitted WITHIN CONDITION over the national meta-texts; (b) placement on the history with the
        history's own text-level slope, arms adjusted with it. Concreteness: Abs-Conc.Median.median, uncorrected.

THE WORRY. The human lookup in abstraction's scorer matches SURFACE forms only, so inflections outside Warriner's
lemma list (killed, screamed, died) go unscored. Model fiction narrates in the past tense more than the history
does (ARC past/present tests), so the gap could bias negative share unevenly between models and novels.

THE TEST. One pipeline, two lookups, so only the mapping differs:
  surface   a token scores only if its form is a Warriner entry (rule `self` of arc_type_norms' map);
  mapped    any rule of arc_type_norms' form map (WordNet lemma, British respelling, MorphAdorner, long-s), so
            killed -> kill; unseen model-text forms through the same mapper.
Tokens: lowercased [a-z]+, arc_interiority's expanded stopwords out (the type-norms policy, not the book's: names
are not removed here, in either version). Components as arc_valence_components.py: neutral 5, band 4-6; positive
and negative share of scored tokens, mean distance from 5 in each bin. History: Chadwyck and Chicago arc_fiction
reps via lltk.text_freqs, 1600-2009, decade medians (>= 3 texts); arms: judged national stories, median over
lineages. EXPLORATORY.
"""
import io, os, re, sys, textwrap

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
PARTIAL = "partial" in sys.argv[1:]                         # read before the argv rewrite below
sys.argv = [sys.argv[0], "v4", "meta", "sel12", "arms4"]
import arc_interiority as A                               # noqa: E402
import arc_type_norms as N                                # noqa: E402
import arc_history_arms as H                              # noqa: E402
from malignment import figure as F                        # noqa: E402

OUT = os.path.join(HERE, "figures", "arc_valence_lemma_check_v1")
TEXTS = os.path.join(A.DATA, "valence_lemma_check_texts_cc.parquet")
COMPS = ["pos_share", "neg_share", "pos_int", "neg_int"]


def comps(pos, neg, tot, spos, sneg):
    return dict(pos_share=pos / tot if tot else np.nan, neg_share=neg / tot if tot else np.nan,
                pos_int=spos / pos if pos else np.nan, neg_int=sneg / neg if neg else np.nan, n_scored=tot)


def history(val, fmap):
    if os.path.exists(TEXTS):
        return pd.read_parquet(TEXTS)
    rows = []
    for mode in ("surface", "mapped"):
        tab = [(f, val[e]) for f, e, how in fmap if (how == "self" or mode == "mapped")]
        sql = f"""SELECT f._id AS _id,
              sum(f.v) AS tot, sumIf(f.v, w.val > 6) AS pos, sumIf(f.v, w.val < 4) AS neg,
              sumIf(f.v * (w.val - 5), w.val > 6) AS spos, sumIf(f.v * (5 - w.val), w.val < 4) AS sneg
          FROM (SELECT _id, k, v FROM (SELECT _id, freqs FROM lltk.text_freqs FINAL WHERE _id IN ({A.REPS})
                  AND _id IN (SELECT _id FROM lltk.texts FINAL WHERE corpus IN ('chadwyck', 'chicago')))
                ARRAY JOIN mapKeys(freqs) AS k, mapValues(freqs) AS v) f
          INNER JOIN w ON f.k = w.form
          GROUP BY _id FORMAT TSVWithNames"""
        R = pd.read_csv(io.StringIO(A.ch_query(sql, {"w": ("form String, val Float64", [(a, repr(b)) for a, b in tab])})), sep="\t")
        for r in R.itertuples():
            rows.append(dict(_id=r._1, mode=mode, **comps(r.pos, r.neg, r.tot, r.spos, r.sneg)))
    D = pd.DataFrame(rows)
    D.to_parquet(TEXTS, index=False)
    return D


def meta(val, fmap):
    lex = N.lexicons()["warriner"]
    core = N.mapper(lex)
    fm = {f: e for f, e, how in fmap}
    _, sw, _ = A.lists_expanded()
    M = pd.read_parquet(os.path.join(A.DATA, "prompt_check_national_judged_meta.parquet"))
    rows, cache = [], {}
    for r in M.itertuples():
        toks = [w for w in re.findall(r"[a-z]+", r.text.lower()) if w not in sw]
        for mode in ("surface", "mapped"):
            pos = neg = tot = spos = sneg = 0
            for w in toks:
                if mode == "surface":
                    e = w if w in val else None
                else:
                    if w not in cache:
                        cache[w] = fm.get(w) or core(w)[0]
                    e = cache[w]
                if not e:
                    continue
                v = val[e]; tot += 1
                if v > 6:
                    pos += 1; spos += v - 5
                elif v < 4:
                    neg += 1; sneg += 5 - v
            rows.append(dict(id=r.id, lineage=r.lineage, cond=r.cond, mode=mode, **comps(pos, neg, tot, spos, sneg)))
    return pd.DataFrame(rows)


def main():
    from scipy.stats import binomtest
    from statsmodels.nonparametric.smoothers_lowess import lowess
    for ext in (".png", ".pdf", ".caption.txt"):
        assert not os.path.exists(OUT + ext), "refusing to overwrite " + OUT + ext
    val = {w: d["warriner_valence"] for w, d in N.lexicons()["warriner"].items()}
    Mf = pd.read_parquet(N.MAP)
    Mf = Mf[Mf.source == "warriner"]
    fmap = list(zip(Mf.form, Mf.entry, Mf.rule))
    Th = history(val, fmap)
    Y = H.concreteness_texts()[["_id", "year"]]
    Th = Th.merge(Y, on="_id")
    Th = Th[Th.year.between(1600, 2009)]
    Mm = meta(val, fmap)
    conds = ["base", "aligned_raw", "aligned_prefill", "aligned_rettberg"]
    lab = {"pos_share": "Positive share", "neg_share": "Negative share", "pos_int": "Positive intensity", "neg_int": "Negative intensity"}
    L = ["# Surface vs lemma-mapped Warriner lookup: valence components (EXPLORATORY)", "",
         "Producer `arc_valence_lemma_check.py` (method in its docstring). Coverage = scored tokens per text relative to "
         "the mapped version's.", ""]
    cov = Th.pivot_table(index="_id", columns="mode", values="n_scored")
    L.append("History: surface scores %.0f%% of the tokens the mapped lookup scores (median over texts). Model meta-texts: %.0f%%." % (
        100 * (cov.surface / cov.mapped).median(),
        100 * (Mm.pivot_table(index="id", columns="mode", values="n_scored").pipe(lambda d: d.surface / d.mapped)).median()))
    L += ["", "| component | lookup | history range (smoothed) | base | aligned raw / prefill / asked | lineages, base -> raw / prefill / asked |",
          "|---|---|---|---|---|---|"]
    pts, cvs, arms, order = [], [], [], []
    for c in COMPS:
        for mode in ("surface", "mapped"):
            name = "%s: %s" % (lab[c], mode)
            order.append(name)
            d = Th[Th["mode"] == mode][["year", c]].dropna()
            h = H.decades(d.year, d[c])
            cv = lowess(h.value.values, h.year.values, frac=0.3, return_sorted=True)
            m = Mm[Mm["mode"] == mode]
            piv = m.pivot_table(index="lineage", columns="cond", values=c)
            med = piv.median()
            agree = []
            for cd in conds[1:]:
                dd = piv[["base", cd]].dropna()
                sgn = np.sign(med[cd] - med["base"])
                k = int((np.sign(dd[cd] - dd["base"]) == sgn).sum())
                agree.append("%s %d/%d (p %.3f)" % ("up" if sgn > 0 else "down", k, len(dd), binomtest(k, len(dd)).pvalue))
            L.append("| %s | %s | %.3f to %.3f | %.3f | %s | %s |" % (lab[c], mode, cv[:, 1].min(), cv[:, 1].max(), med["base"],
                                                                 " / ".join("%.3f" % med[x] for x in conds[1:]), " / ".join(agree)))
            pts += [dict(panel=name, year=y, value=v) for y, v in zip(h.year, h.value)]
            cvs += [dict(panel=name, year=x, value=y) for x, y in cv]
            arms += [dict(panel=name, arm=H.NAME[{"base": "base", "aligned_raw": "raw", "aligned_prefill": "prefill", "aligned_rettberg": "continue"}[k]],
                          value=float(med[k])) for k in conds]
    open(os.path.join(HERE, "ARC_VALENCE_LEMMA_CHECK.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))
    P, C, A_ = pd.DataFrame(pts), pd.DataFrame(cvs), pd.DataFrame(arms)
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
         + labs(x="", y="Share of scored words / mean distance from neutral", linetype="")
         + F.pub_theme(height=8.0)
         + theme(legend_position="bottom", figure_size=(7.5, 8.0), strip_text=element_text(family=F.pub_font(), size=F.PUB_FONT_PT)))
    F.save(p, OUT + ".png")
    open(OUT + ".caption.txt", "w").write("\n".join(textwrap.wrap(
        "SURFACE VS LEMMA-MAPPED WARRINER LOOKUP, valence components: positive and negative share of scored words and each "
        "bin's mean distance from neutral (5; band 4-6). Left: surface forms only; right: forms mapped to Warriner entries "
        "(WordNet lemma, British and old spellings, long-s). Chadwyck and Chicago arc_fiction, decade medians, lowess; "
        "lines: national-story arms, median over lineages.", 100)) + "\n")


def partial():
    from scipy.stats import binomtest, spearmanr
    from statsmodels.nonparametric.smoothers_lowess import lowess
    SH = os.path.expanduser("~/malignment-data/interiority_norms")
    CONC = "Abs-Conc.Median.median"
    Th = pd.read_parquet(TEXTS).merge(H.concreteness_texts()[["_id", "year"]], on="_id")
    Th = Th[Th.year.between(1600, 2009)].merge(pd.read_parquet(os.path.join(SH, "vad_scores_arc_fiction.parquet"))[["_id", CONC]], on="_id")
    val = {w: d["warriner_valence"] for w, d in N.lexicons()["warriner"].items()}
    Mf = pd.read_parquet(N.MAP)
    Mf = Mf[Mf.source == "warriner"]
    Mm = meta(val, list(zip(Mf.form, Mf.entry, Mf.rule)))
    Mm = Mm.merge(pd.read_parquet(os.path.join(A.DATA, "prompt_check_national_judged_meta_scored.parquet"))[["id", CONC]], on="id")
    conds = ["base", "aligned_raw", "aligned_prefill", "aligned_rettberg"]
    L = ["# Valence components with concreteness partialled out (EXPLORATORY)", "",
         "Producer `arc_valence_lemma_check.py partial` (method in its docstring). Lineage cells: lineages moving from base in "
         "the direction of the ADJUSTED medians' difference, sign-test p. Placement: the adjusted arm against the adjusted "
         "history's smoothed range.", "",
         "| component | lookup | rho with concreteness: texts / meta-texts | lineages raw / prefill / asked, unadjusted | the same, within-condition partial | history range adjusted | arms adjusted: base / raw / prefill / asked |",
         "|---|---|---|---|---|---|---|"]
    for c in COMPS:
        for mode in ("surface", "mapped"):
            h = Th[Th["mode"] == mode].dropna(subset=[c, CONC])
            m = Mm[Mm["mode"] == mode].dropna(subset=[c, CONC]).copy()
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
            bh = float(np.polyfit(h[CONC], h[c], 1)[0])
            cm = float(h[CONC].mean())
            adjh = h[c] - bh * (h[CONC] - cm)
            dec = H.decades(h.year, adjh)
            cv = lowess(dec.value.values, dec.year.values, frac=0.3, return_sorted=True)
            lo, hi = cv[:, 1].min(), cv[:, 1].max()
            am = (m[c] - bh * (m[CONC] - cm)).groupby([m.cond, m.lineage]).first().groupby(level=0).median()
            place = lambda v: "%.3f (%s)" % (v, "above all" if v > hi else "below all" if v < lo else "inside")
            L.append("| %s | %s | %+.2f / %+.2f | %s | %s | %.3f to %.3f | %s |" % (
                c, mode, spearmanr(h[c], h[CONC])[0], spearmanr(m[c], m[CONC])[0], lin(m[c]), lin(m[c] - bw * m[CONC]),
                lo, hi, " / ".join(place(am[k]) for k in conds)))
    open(os.path.join(HERE, "ARC_VALENCE_LEMMA_CHECK_partial.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    partial() if PARTIAL else main()
