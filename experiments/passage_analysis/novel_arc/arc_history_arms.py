"""Concreteness, cognitive and emotional language over arc_fiction, with TEMPLATE_ARM model arms. (RH, 2026-09-25)

    .venv/bin/python -u arc_history_arms.py --no-arms   -> figures/arc_history_three_preview.{png,pdf,caption.txt}
    .venv/bin/python -u arc_history_arms.py --arms      -> $MALIGNMENT_DATA/novel_arc/arc_history_arm_passages.parquet
                                                          figures/arc_history_three_arms.{png,pdf,caption.txt}

HISTORY, all three panels over the book's arc_fiction set (abstraction.scores_rep, arc_corpus =
'arc_fiction', 82,080 reps, each rep's own score), drawn as Figure 5 draws its history: per decade the
median over texts, decades with fewer than 3 texts dropped, gray points, black lowess at span 0.3.
  1. CONCRETENESS: `Abs-Conc.Median.median` (abstraction seat: the book's column, up = concrete),
     with the book v5's corpus-bias correction: each text's corpus coefficient from
     corpus_bias_coefficients.json subtracted, a corpus absent from the file uncorrected
     (abstraction.corpus_correction.correct_scores_df's rule: map(coefficients).fillna(0); applied here
     directly because that package needs gensim, which this venv lacks). Texts 1600-2009.
  2. COGNITIVE: vetted clean X (arc_interiority_precision.py --vetted), share of alphabetic non-stopword
     tokens, texts with >= 2,000 such tokens.
  3. EMOTIONAL: the vetted period candidates alone, same rule. By token mass 67% emotion words.

ARMS (malign, 2026-09-25): the TEMPLATE_ARM run (TEMPLATE_ARM.md), NOT model_placement.parquet:
41 lineages (roster.population("framed_empty")), one vLLM engine for every arm, the same 100 English
f11_l2 stems. Passages = coding/selection.parquet joined to coding/codings.parquet on id, narrative ==
True, n_words >= 40. base = the lineage's base model, aligned = arm "raw" (aligned model, no template;
Figure 5's aligned). Registered primary: lineages with >= 10 narrative passages in ALL FOUR arms; per
model the median over its passages, then the median over lineages.
  - concreteness per passage: measure_lltk.Scorer's rh_absconc_median, on scores_rep's scale (abstraction
    rescored 13,468 passages both ways: Pearson 0.999, mean difference -0.000). Model prose is clean text,
    closest to a transcribed source, so it is not bias-corrected.
  - cognitive and emotional per passage: the history's own rule on the passage text (lowercased [a-z]+
    tokens, the expanded stopwords out, the expanded vetted list in).
Grain: arms are passage values (~80-200 words), points are whole-text values; decade medians and arm
medians are comparable, spreads are not.
"""
import json, os, re, sys, textwrap

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, REPO)
from malignment import figure as F                              # noqa: E402

DATA = os.path.join(os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data")), "novel_arc")
TA = os.path.join(os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data")), "template_arm", "coding")
COUNTS = os.path.join(DATA, "arc_interiority_texts_precision_vetted.parquet")
CONC = os.path.join(DATA, "arc_concreteness_texts.parquet")
ARM_OUT = os.path.join(DATA, "arc_history_arm_passages.parquet")
BIAS = "/Volumes/diderot/DH/data/data_abslithist/scores/corpus_bias_coefficients.json"
MIN_CONTENT, MIN_DECADE, MIN_ARM = 2000, 3, 10
ARMS_ON = "--arms" in sys.argv
OUT = os.path.join(HERE, "figures", "arc_history_three_" + ("arms" if ARMS_ON else "preview"))
NAME = {"base": "Base models", "raw": "Aligned models"}
LINETYPE = {"Base models": "dotted", "Aligned models": "dashed"}      # Figure 5 v5+
X0, X1, XLAB, XMAX = 1600, 2005, 2011, 2150


def concreteness_texts():
    """-> per text: _id, year, corpus, conc (raw), conc_corr. Read once, written, then re-read."""
    if os.path.exists(CONC):
        return pd.read_parquet(CONC)
    import io
    import arc_interiority as A
    sql = f"""
      SELECT r._id AS _id, t.year AS year, t.corpus AS corpus, r.`Abs-Conc.Median.median` AS conc
      FROM (SELECT _id, `Abs-Conc.Median.median` FROM abstraction.scores_rep WHERE arc_corpus = 'arc_fiction') r
      INNER JOIN (SELECT _id, year, corpus FROM lltk.texts FINAL WHERE _id IN ({A.REPS})) t ON r._id = t._id
      FORMAT TSVWithNames"""
    #: ClickHouse writes NULL as \N in TSV
    T = pd.read_csv(io.StringIO(A.ch_query(sql, {})), sep="\t", na_values=["\\N"], keep_default_na=False)
    #: the population is booked; a short read under load has happened before
    assert len(T) == 82080, len(T)
    T["conc"] = T.conc.astype(float)
    print("concreteness: %d texts, %d without a score, %d without a year" % (len(T), T.conc.isna().sum(), T.year.isna().sum()))
    coef = json.load(open(BIAS))["coefficients"]
    T["conc_corr"] = T.conc - T.corpus.map(coef).fillna(0.0)
    T.to_parquet(CONC, index=False)
    return T


def decades(years, values):
    d = pd.DataFrame({"year": years, "v": values}).dropna()
    rows = []
    for yr in range(1600, 2010, 10):
        t = d[(d.year >= yr) & (d.year < yr + 10)]
        if len(t) >= MIN_DECADE:
            rows.append({"year": yr + 5, "value": float(t.v.median()), "n": len(t)})
    return pd.DataFrame(rows)


def smooth(h):
    from statsmodels.nonparametric.smoothers_lowess import lowess
    return lowess(h.value.values, h.year.values, frac=0.3, return_sorted=True)


def history():
    C = concreteness_texts()
    #: a count in the caption is a claim about what was DRAWN: long_arc_prestige's 356 reps carry no score
    C = C[C.year.between(1600, 2009) & C.conc_corr.notna()]
    assert len(C) == 81555, len(C)
    T = pd.read_parquet(COUNTS)
    assert len(T) == 82080, len(T)
    T = T[(T.n_content >= MIN_CONTENT) & T.year.between(1600, 2009)]
    assert len(T) == 75974, len(T)                   # ARC_INTERIORITY_PRECISION_VETTED.md
    return {"conc": (decades(C.year, C.conc_corr), len(C)),
            "cog": (decades(T.year, T.n_cleanx_p / T.n_content), len(T)),
            "emo": (decades(T.year, T.n_cand_p / T.n_content), len(T))}


def arm_passages():
    """-> per narrative passage of the registered primary: model, base, arm, conc, cog, emo."""
    if os.path.exists(ARM_OUT):
        return pd.read_parquet(ARM_OUT)
    import arc_interiority_precision as AP
    from measure_lltk import Scorer
    S_ = pd.read_parquet(os.path.join(TA, "selection.parquet"))
    Cd = pd.read_parquet(os.path.join(TA, "codings.parquet"))
    #: malign asked for the COMPLETE coding; a half-coded cell would enter as a thin cell, not an error
    assert S_.id.isin(Cd.id).all(), "coding incomplete: %d of %d selected passages uncoded" % (
        (~S_.id.isin(Cd.id)).sum(), len(S_))
    P = S_.merge(Cd[["id", "narrative"]], on="id", how="inner", validate="1:1")
    P = P[(P.narrative == True) & (P.n_words >= 40)]                    # noqa: E712
    n = P.groupby(["base", "arm"]).size().unstack(fill_value=0)
    keep = n.index[(n.reindex(columns=["base", "raw", "prefill", "continue"], fill_value=0) >= MIN_ARM).all(axis=1)]
    P = P[P.base.isin(keep) & P.arm.isin(["base", "raw"])]
    old = sys.argv
    sys.argv = [old[0], "--vetted"]                  # the list module reads its mode at import
    import importlib
    AP = importlib.reload(AP)
    sys.argv = old
    ex, sw, _ = AP.lists_precision()
    cog, emo = ex["cleanx_p"], ex["cand_p"]
    Sc = Scorer()
    rows = []
    for r in P.itertuples():
        toks = re.findall(r"[a-z]+", (r.text or "").lower())
        content = [w for w in toks if w not in sw]
        v = Sc.score(r.text or "") or {}
        rows.append(dict(id=r.id, model=r.model, base=r.base, arm=r.arm, n_content=len(content),
                         cog=sum(w in cog for w in content) / len(content) if content else np.nan,
                         emo=sum(w in emo for w in content) / len(content) if content else np.nan,
                         conc=v.get("rh_absconc_median")))
    D = pd.DataFrame(rows)
    D.to_parquet(ARM_OUT, index=False)
    json.dump({"lineages": sorted(keep), "n_lineages": len(keep)}, open(ARM_OUT.replace(".parquet", "_lineages.json"), "w"), indent=1)
    return D


def arm_values(D, col):
    per = D.groupby(["base", "arm"])[col].median().unstack()
    return {a: float(per[a].median()) for a in ("base", "raw")}, len(per)


def panel(h, curve, arms, title, ylab, show_x, pct):
    from plotnine import (ggplot, aes, geom_point, geom_line, geom_vline, geom_segment, geom_text, labs,
                          scale_x_continuous, scale_y_continuous, scale_linetype_manual, theme, element_text)
    fnt = F.pub_font()
    cv = pd.DataFrame(curve, columns=["year", "value"])
    p = (ggplot()
         + geom_vline(xintercept=[1700, 1800, 1900], color="#e9ecef", size=F.PUB_RULE_PT)
         + geom_point(aes("year", "value"), data=h, color=F.PUB_GRAY, size=0.9)
         + geom_line(aes("year", "value"), data=cv, color=F.PUB_INK, size=F.PUB_LINE_PT))
    xmax = XMAX if arms else 2010
    if arms:
        A = pd.DataFrame([{"arm": NAME[a], "value": v} for a, v in arms.items()])
        lo, hi = float(min(cv.value.min(), h.value.min(), A.value.min())), float(max(cv.value.max(), h.value.max(), A.value.max()))
        o = A.sort_values("value").reset_index(drop=True)
        o["ly"] = o.value
        for i in range(1, len(o)):
            o.loc[i, "ly"] = max(o.loc[i, "ly"], o.loc[i - 1, "ly"] + 0.11 * (hi - lo))
        p = (p + geom_segment(aes(x=X0, xend=X1, y="value", yend="value", linetype="arm"), data=A,
                              color=F.PUB_MID, size=F.PUB_RULE_PT * 1.4)
             + geom_text(aes(x=XLAB, y="ly", label="arm"), data=o, ha="left", va="center",
                         size=F.PUB_FONT_PT, family=fnt, color=F.PUB_INK)
             + scale_linetype_manual(LINETYPE, guide=None))
    return (p
            + (scale_y_continuous(labels=lambda v: ["%g%%" % round(100 * x, 6) for x in v]) if pct else scale_y_continuous())
            + scale_x_continuous(limits=(X0 - 5, xmax), breaks=list(range(1600, 2001, 50)), expand=(0, 0),
                                 labels=(lambda v: ["%d" % x for x in v]) if show_x else (lambda v: [""] * len(v)))
            + labs(x="", y=ylab, title=title)
            + F.pub_theme(grid="y")
            + theme(axis_title_y=element_text(family=fnt, size=F.PUB_FONT_PT),
                    plot_title=element_text(family=fnt, size=F.PUB_FONT_PT, weight="bold", ha="left")))


def main():
    for ext in (".png", ".pdf", ".caption.txt"):
        assert not os.path.exists(OUT + ext), "refusing to overwrite " + OUT + ext
    F.check_halftones({"history": F.PUB_INK, "points": F.PUB_GRAY, "arms": F.PUB_MID})
    H = history()
    arms, info = {}, ""
    if ARMS_ON:
        D = arm_passages()
        for k in ("conc", "cog", "emo"):
            arms[k], nl = arm_values(D, k)
        info = " Arms: TEMPLATE_ARM, %d lineages with at least %d narrative passages in all four arms; base %s and aligned (raw) %s passages." % (
            nl, MIN_ARM, format(int((D.arm == "base").sum()), ","), format(int((D.arm == "raw").sum()), ","))
    spec = (("conc", "Concreteness in fiction", "Concreteness\n(word norm mean)", False),
            ("cog", "Cognitive language in fiction", "Cognitive words\n(share of words)", True),
            ("emo", "Emotional language in fiction", "Emotional words\n(share of words)", True))
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["pdf.fonttype"] = 42
    from plotnine.composition import Stack
    ps = [panel(H[k][0], smooth(H[k][0]), arms.get(k), t, yl, i == 2, pct) for i, (k, t, yl, pct) in enumerate(spec)]
    fig = Stack(ps).draw()
    fig.set_size_inches(F.PUB_SIZE[0], 6.0)
    fig.savefig(OUT + ".png", dpi=300)
    fig.savefig(OUT + ".pdf")
    wrap = lambda s: textwrap.wrap(s, 100)
    L = wrap("CONCRETENESS, COGNITIVE AND EMOTIONAL LANGUAGE IN FICTION, 1600-2000, drawn as Figure 5 draws its "
             "history" + (", with base and aligned model arms." if ARMS_ON else " (preview, no model arms).")) + [""] + wrap(
        "Gray points: per decade, the median over texts; black line: their lowess smooth (span 0.3); decades under "
        "%d texts dropped. Texts: the book's arc_fiction set (abstraction.scores_rep, deduplicated), every source "
        "pooled. Top: concreteness, the book's Abs-Conc.Median.median, corrected for corpus bias as in the book "
        "(v5) (%s texts). Middle and bottom: share of a text's alphabetic non-stopword tokens on a word list "
        "(lltk.text_freqs surface forms, with MorphAdorner and long-s variants of kept words), texts with at least "
        "%s such tokens (%s texts). Cognitive: the USAS X words an LLM rater kept under a precision-first rule, "
        "hand-vetted (872 base words; 68%% cognition by token mass). Emotional: period-model neighbours of X rated "
        "and vetted the same way (1,077 base words; 67%% emotion)." % (
            MIN_DECADE, format(H["conc"][1], ","), format(MIN_CONTENT, ","), format(H["cog"][1], ",")) + (
        info + " Model arms: per model the median over its narrative passages, then the median over lineages; "
        "passage values, not text values, so medians compare and spreads do not. Model concreteness is not "
        "bias-corrected (clean digital text)." if ARMS_ON else ""))
    L += ["", "  arms: " + json.dumps({k: {a: round(v, 4) for a, v in d.items()} for k, d in arms.items()})] if ARMS_ON else []
    open(OUT + ".caption.txt", "w").write("\n".join(L) + "\n")
    print("\n".join(L))
    for k, (h, n) in H.items():
        print(k, "decades %d, texts %d, range %.4f..%.4f" % (len(h), n, h.value.min(), h.value.max()))


if __name__ == "__main__":
    main()
