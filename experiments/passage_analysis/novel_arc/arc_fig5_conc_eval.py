"""Figure 5 draft: concrete language on top, evaluative language below, both as SHARES of content words. (RH,
2026-09-26: "combine with concreteness, for a new draft of Fig 5, concreteness on top, evaluative on bottom"; "should
we make Concreteness a share too?")

    .venv/bin/python -u arc_fig5_conc_eval.py         -> figures/arc_fig5_conc_eval_v1.{png,pdf,caption.txt}, ARC_FIG5_CONC_EVAL.md
    .venv/bin/python -u arc_fig5_conc_eval.py 1700    -> figures/arc_fig5_conc_eval_v1_1700.*   (history 1700-2009)
    .venv/bin/python -u arc_fig5_conc_eval.py v2 [1700]   -> figures/arc_fig5_conc_eval_v2[_1700].*: concreteness as the
        NORM SCORE on top (RH, 2026-09-26: "keep Concreteness as a norm"), on the SAME Chadwyck and Chicago texts as the
        evaluative panel ("at least use the same historical corpus in both"), uncorrected like the model lines (the
        two corpora's bias coefficients differ by 0.005)
    .venv/bin/python -u arc_fig5_conc_eval.py ext [1700]  -> figures/arc_fig5_eval_extremity_ref_v1[_1700].*: reference
        plate adding EVALUATIVE EXTREMITY, the norm-average form of the evaluative share on the same cleaned lexicon:
        mean |v - 5| over every scored token, where scored = the kept polar words (as in the share) PLUS the
        neutral-band (4-6) Warriner lemmas and their mapped forms; polar words the rater rejected as ambiguous score
        nothing, as in the share.

CONCRETE SHARE. Abstraction's own word norm, the one its text score averages (`Abs-Conc.Median.median`, the median over
its period norms of the median over the human norms, z-scored), thresholded at its own cutoff (ZCUT = 1.0,
abstraction.config): a word is CONCRETE if z >= 1. Rate = concrete tokens / content tokens, the same content tokens
(lowercased [a-z]+ minus arc_interiority's expanded stopwords) as the evaluative rate, so the two panels share a
denominator. Abstraction's pct_concrete divides by normed tokens instead; with ~2.2M normed forms the two differ little.
EVALUATIVE SHARE. arc_valence_clean_components v2, "+vector" lexicon (positive + negative words per content word).
HISTORY: Chadwyck and Chicago arc_fiction reps, n_content >= 2,000, decade medians (>= 3 texts), lowess 0.3. ARMS:
judged no-demonym national stories, one meta-text per model-condition, median over lineages.
CONTROL (the caption's claim): per lineage, aligned minus base in evaluative share, raw and with concreteness partialled
out by the within-condition slope (arc_valence_clean_components' method), for both concreteness measures (the text
score and this share). EXPLORATORY.
"""
import io, os, re, sys, textwrap

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
_ARGS = sys.argv[1:]                                        # read before the argv rewrite below
sys.argv = [sys.argv[0], "v2"]
import arc_valence_clean_components as V                   # noqa: E402
H, F, A = V.H, V.F, V.A

START = 1700 if "1700" in _ARGS else 1600
MODE = "ext" if "ext" in _ARGS else "v2" if "v2" in _ARGS else "v1"
OUT = os.path.join(HERE, "figures", {"v1": "arc_fig5_conc_eval_v1", "v2": "arc_fig5_conc_eval_v2", "ext": "arc_fig5_eval_extremity_ref_v1"}[MODE]
                   + ("_1700" if START == 1700 else ""))
EXT_TEXTS = os.path.join(A.DATA, "eval_extremity_texts_cc.parquet")
NORMS = "/Users/rj416/github/abslithists/abstraction/data/fields/data.allnorms.pkl.gz"
NORM_COL, ZCUT = "Abs-Conc.Median.median", 1.0
CONC_TEXTS = os.path.join(A.DATA, "conc_share_texts_cc.parquet")
LEX = "+vector"
NAME = {"base": "Base models", "raw": "Aligned models", "prefill": "Aligned (prefilled)", "continue": "Aligned (chat)"}
COND = {"base": "base", "raw": "aligned_raw", "prefill": "aligned_prefill", "continue": "aligned_rettberg"}
X1, XL, XMAX = 2005, 2025, (2190 if START == 1600 else 2165)


def concrete_words(sw):
    d = pd.read_pickle(NORMS)[NORM_COL].dropna()
    d = d[d.index.str.fullmatch(r"[a-z]+") & ~d.index.isin(sw)]
    return set(d[d >= ZCUT].index)


def history_conc(conc):
    if os.path.exists(CONC_TEXTS):
        return pd.read_parquet(CONC_TEXTS)
    sql = f"""SELECT f._id AS _id, sum(f.v) AS n_conc
      FROM (SELECT _id, k, v FROM (SELECT _id, freqs FROM lltk.text_freqs FINAL WHERE _id IN ({A.REPS})
              AND _id IN (SELECT _id FROM lltk.texts FINAL WHERE corpus IN ('chadwyck', 'chicago')))
            ARRAY JOIN mapKeys(freqs) AS k, mapValues(freqs) AS v) f
      INNER JOIN w ON f.k = w.form GROUP BY _id FORMAT TSVWithNames"""
    R = pd.read_csv(io.StringIO(A.ch_query(sql, {"w": ("form String", [(w,) for w in sorted(conc)])})), sep="\t")
    C = pd.read_parquet(H.COUNTS)[["_id", "n_content"]]
    R = R.merge(C, on="_id")
    R["conc_rate"] = R.n_conc / R.n_content
    R.to_parquet(CONC_TEXTS, index=False)
    return R


def extremity_lexicon(L):
    """-> {form: |v - 5|}: the share's kept polar forms plus neutral-band Warriner lemmas and mapped forms, minus every
    form the cleaning rated (a rated form is either kept, and already in, or rejected as ambiguous)."""
    K = pd.read_csv(V.KEEP, keep_default_na=False, na_values=[""])
    Kp = pd.read_csv(V.KEEP_POS, keep_default_na=False, na_values=[""])
    rated = set(K.form) | set(Kp.form)
    val = {w: d["warriner_valence"] for w, d in V.N.lexicons()["warriner"].items()}
    neutral = {w for w, v in val.items() if 4 <= v <= 6}
    ext = {w: abs(v - 5) for w, v in L[LEX].items()}
    Mf = pd.read_parquet(V.N.MAP)
    Mf = Mf[Mf.source == "warriner"]
    for f, e in list(zip(sorted(neutral), sorted(neutral))) + list(zip(Mf.form, Mf.entry)):
        if e in neutral and f not in rated and f not in ext:
            ext[f] = abs(val[e] - 5)
    #: the cleaning rated only polar lemmas; a neutral lemma among the rated would mean the premise above is wrong
    assert not ({w for w in neutral if w in set(K[K.kind == "lemma"].form)}), "neutral lemmas were rated"
    return ext


def history_extremity(ext):
    if os.path.exists(EXT_TEXTS):
        return pd.read_parquet(EXT_TEXTS)
    sql = f"""SELECT f._id AS _id, sum(f.v) AS n_scored, sum(f.v * w.d) AS s_ext
      FROM (SELECT _id, k, v FROM (SELECT _id, freqs FROM lltk.text_freqs FINAL WHERE _id IN ({A.REPS})
              AND _id IN (SELECT _id FROM lltk.texts FINAL WHERE corpus IN ('chadwyck', 'chicago')))
            ARRAY JOIN mapKeys(freqs) AS k, mapValues(freqs) AS v) f
      INNER JOIN w ON f.k = w.form GROUP BY _id FORMAT TSVWithNames"""
    R = pd.read_csv(io.StringIO(A.ch_query(sql, {"w": ("form String, d Float64", [(a, repr(b)) for a, b in ext.items()])})), sep="\t")
    R["ext"] = R.s_ext / R.n_scored
    R.to_parquet(EXT_TEXTS, index=False)
    return R


def meta_extremity(ext, sw):
    M = pd.read_parquet(os.path.join(A.DATA, "prompt_check_national_judged_meta.parquet"))
    rows = []
    for r in M.itertuples():
        d = [ext[w] for w in re.findall(r"[a-z]+", r.text.lower()) if w not in sw and w in ext]
        rows.append(dict(id=r.id, ext=float(np.mean(d)), ext_cover=len(d)))
    return pd.DataFrame(rows)


def meta_conc(conc, sw):
    M = pd.read_parquet(os.path.join(A.DATA, "prompt_check_national_judged_meta.parquet"))
    rows = []
    for r in M.itertuples():
        toks = [w for w in re.findall(r"[a-z]+", r.text.lower()) if w not in sw]
        rows.append(dict(id=r.id, conc_rate=sum(w in conc for w in toks) / len(toks)))
    return pd.DataFrame(rows)


def label_positions(vals, gap):
    order = sorted(vals, key=vals.get)
    groups = [[order[0]]]
    for k in order[1:]:
        if vals[k] - vals[groups[-1][-1]] < gap:
            groups[-1].append(k)
        else:
            groups.append([k])
    pos = {}
    for g in groups:
        c = sum(vals[k] for k in g) / len(g)
        for i, k in enumerate(g):
            pos[k] = c + (i - (len(g) - 1) / 2) * gap
    return pos


def panel(hist, curve, arms, title, ylab, show_x, pct=True):
    from plotnine import (ggplot, aes, geom_point, geom_line, geom_segment, geom_text, geom_vline, labs,
                          scale_x_continuous, scale_y_continuous, scale_linetype_manual, theme, element_text, element_blank)
    fnt = F.pub_font()
    cv = pd.DataFrame(curve, columns=["year", "value"])
    Ad = pd.DataFrame([{"arm": NAME[k], "value": v} for k, v in arms.items()])
    lo = min(cv.value.min(), hist.value.min(), Ad.value.min()); hi = max(cv.value.max(), hist.value.max(), Ad.value.max())
    Ad["ly"] = Ad.arm.map(label_positions({NAME[k]: v for k, v in arms.items()}, 0.075 * (hi - lo)))
    X0 = START
    p = (ggplot()
         + geom_vline(xintercept=[y for y in (1700, 1800, 1900) if y > X0], color="#e9ecef", size=F.PUB_RULE_PT)
         + geom_point(aes("year", "value"), data=hist, color=F.PUB_GRAY, size=0.9)
         + geom_line(aes("year", "value"), data=cv, color=F.PUB_INK, size=F.PUB_LINE_PT)
         + geom_segment(aes(x=X0, xend=X1, y="value", yend="value", linetype="arm"), data=Ad, color=F.PUB_MID, size=F.PUB_RULE_PT * 1.4)
         + geom_segment(aes(x=X1, xend=XL - 3, y="value", yend="ly"), data=Ad, color=F.PUB_MID, size=F.PUB_RULE_PT * 0.8)
         + geom_text(aes(x=XL, y="ly", label="arm"), data=Ad, ha="left", va="center", size=F.PUB_FONT_PT, family=fnt, color=F.PUB_INK)
         + scale_linetype_manual({NAME["base"]: "dotted", NAME["raw"]: "dashed", NAME["prefill"]: "dashdot", NAME["continue"]: "solid"}, guide=None)
         + (scale_y_continuous(labels=lambda v: ["%g%%" % round(100 * x, 6) for x in v]) if pct else scale_y_continuous())
         + scale_x_continuous(limits=(X0 - 5, XMAX), breaks=[y for y in (1600, 1700, 1800, 1900, 2000) if y >= X0], expand=(0, 0))
         + labs(x="", y=ylab, title=title)
         + F.pub_theme(grid="y")
         + theme(axis_title_y=element_text(family=fnt, size=F.PUB_FONT_PT),
                 plot_title=element_text(family=fnt, size=F.PUB_FONT_PT, weight="bold", ha="left")))
    if not show_x:
        p = p + theme(axis_text_x=element_blank())
    return p


def control(Mm, y, x):
    """-> per aligned condition: (k up, n, binomial p, median gap raw, median gap partialled); partial by the
    within-condition slope of y on x across all model meta-texts."""
    from scipy.stats import binomtest
    yd = Mm[y] - Mm.groupby("cond")[y].transform("mean")
    xd = Mm[x] - Mm.groupby("cond")[x].transform("mean")
    b = float(np.polyfit(xd, yd, 1)[0])
    out = {}
    for k in ("raw", "prefill", "continue"):
        res = []
        for yy in (Mm[y], Mm[y] - b * Mm[x]):
            piv = Mm.assign(v=yy).pivot_table(index="lineage", columns="cond", values="v")[["base", COND[k]]].dropna()
            g = piv[COND[k]] - piv["base"]
            res.append((int((g > 0).sum()), len(g), binomtest(int((g > 0).sum()), len(g)).pvalue, float(g.median())))
        out[k] = dict(k=res[1][0], n=res[1][1], p=res[1][2], k_raw=res[0][0], gap_raw=res[0][3], gap_part=res[1][3])
    return b, out


def history_control(Th, x):
    """-> (slope, smoothed fall 1765->1955 raw, partialled): eval_rate partialled on x by the WITHIN-DECADE slope (the
    history's analogue of the within-condition slope; a pooled slope would absorb the very co-movement in question)."""
    dec = Th.year // 10
    yd = Th.eval_rate - Th.groupby(dec).eval_rate.transform("mean")
    xd = Th[x] - Th.groupby(dec)[x].transform("mean")
    b = float(np.polyfit(xd, yd, 1)[0])
    falls = []
    for y in (Th.eval_rate, Th.eval_rate - b * (Th[x] - Th[x].mean())):
        cv = H.smooth(H.decades(Th.year, y))
        falls.append(float(np.interp(1765, cv[:, 0], cv[:, 1]) - np.interp(1955, cv[:, 0], cv[:, 1])))
    return b, falls[0], falls[1]


def main():
    from scipy.stats import pearsonr
    for ext in (".png", ".pdf", ".caption.txt"):
        assert not os.path.exists(OUT + ext), "refusing to overwrite " + OUT + ext
    _, sw, _ = A.lists_expanded()
    conc = concrete_words(sw)
    L = V.lexicons()
    Th = V.history(L).merge(H.concreteness_texts()[["_id", "year", "conc"]], on="_id")
    Th = Th[(Th.lexicon == LEX) & Th.year.between(START, 2009) & (Th.n_content >= H.MIN_CONTENT)]
    Th["conc"] = Th.conc.astype(float)
    Hc = history_conc(conc)
    Th = Th.merge(Hc[["_id", "conc_rate"]], on="_id")
    #: the eval rate's cached n_content and the share's come from the same COUNTS file; a text lost here is a join loss
    assert Th._id.nunique() == len(Th), "duplicate texts after merge"
    Mm = V.meta(L)
    Mm = Mm[Mm.lexicon == LEX].merge(meta_conc(conc, sw), on="id")
    r_hist = pearsonr(Th.conc_rate, Th.conc.astype(float))[0]
    r_meta = pearsonr(Mm.conc_rate, Mm[V.CONC])[0]
    #: the share must track the score it thresholds, or it is a different measure wearing the name
    assert r_hist > 0.7 and r_meta > 0.7, (r_hist, r_meta)
    #: booked (arc_evaluation_share_v2 caption): the evaluative arms are unchanged by this figure
    med_e = Mm.pivot_table(index="lineage", columns="cond", values="eval_rate").median()
    for k, v in {"base": 0.1732, "raw": 0.2212, "prefill": 0.2291, "continue": 0.2327}.items():
        assert abs(med_e[COND[k]] - v) < 5e-5, (k, med_e[COND[k]], v)
    med_c = Mm.pivot_table(index="lineage", columns="cond", values="conc_rate").median()
    arms_c = {k: float(med_c[COND[k]]) for k in COND}
    arms_e = {k: float(med_e[COND[k]]) for k in COND}
    b_score, ctl_score = control(Mm, "eval_rate", V.CONC)
    b_share, ctl_share = control(Mm, "eval_rate", "conc_rate")
    hist_score, hist_share = history_control(Th, "conc"), history_control(Th, "conc_rate")
    n_cond = Mm.groupby("cond").lineage.nunique()
    #: booked (ARC_VALENCE_CLEAN_v2.md, +vector, partialled on the concreteness score): 25/32, 20/23, 17/20
    assert [(ctl_score[k]["k"], ctl_score[k]["n"]) for k in ("raw", "prefill", "continue")] == [(25, 32), (20, 23), (17, 20)], ctl_score

    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["pdf.fonttype"] = 42
    from plotnine.composition import Stack
    he = H.decades(Th.year, Th.eval_rate)
    ev = panel(he, H.smooth(he), arms_e, "Evaluative language in fiction", "Evaluative words\n(per content word)", MODE != "ext")
    if MODE == "v1":
        hc = H.decades(Th.year, Th.conc_rate)
        ps = [panel(hc, H.smooth(hc), arms_c, "Concrete language in fiction", "Concrete words\n(per content word)", False), ev]
    else:
        med_s = Mm.pivot_table(index="lineage", columns="cond", values=V.CONC).median()
        arms_s = {k: float(med_s[COND[k]]) for k in COND}
        #: booked (arc_fig5_conc_valence_extremity_v1 caption): +0.097, -0.125, -0.059, -0.178
        for k, v in {"base": 0.097, "raw": -0.125, "prefill": -0.059, "continue": -0.178}.items():
            assert abs(arms_s[k] - v) < 5e-4, (k, arms_s[k], v)
        hs = H.decades(Th.year, Th.conc)
        ps = [panel(hs, H.smooth(hs), arms_s, "Concrete language in fiction", "Concreteness\n(word norm mean)", False, pct=False), ev]
        arms_c = arms_s
    if MODE == "ext":
        ext = extremity_lexicon(L)
        Tx = Th.merge(history_extremity(ext)[["_id", "ext"]], on="_id")
        assert len(Tx) == len(Th), (len(Tx), len(Th))
        Mx = Mm.merge(meta_extremity(ext, sw), on="id")
        med_x = Mx.pivot_table(index="lineage", columns="cond", values="ext").median()
        arms_x = {k: float(med_x[COND[k]]) for k in COND}
        hx = H.decades(Tx.year, Tx.ext)
        cvx = H.smooth(hx)
        ps.append(panel(hx, cvx, arms_x, "Evaluative extremity in fiction", "Mean distance\nfrom neutral valence", True, pct=False))
        place = {}
        for nm, cv, arms in (("share", H.smooth(he), arms_e), ("extremity", cvx, arms_x)):
            for k, v in arms.items():
                xs = [int(round(y0 + (v - v0) / (v1 - v0) * (y1 - y0))) for (y0, v0), (y1, v1) in zip(cv[:-1], cv[1:]) if (v0 - v) * (v1 - v) < 0]
                place[(nm, k)] = "%.4f (%s)" % (v, "above every decade" if v > cv[:, 1].max() else "below every decade" if v < cv[:, 1].min() else ", ".join(map(str, xs)))
    fig = Stack(ps).draw()
    fig.set_size_inches(F.PUB_SIZE[0], 5.6 if len(ps) == 2 else 8.2)
    fig.savefig(OUT + ".png", dpi=300)
    fig.savefig(OUT + ".pdf")

    #: the caption states the STRICTER control: the text score also counts abstract words, which is where alignment
    #: moves concreteness (ARC_FIG5_CONC_EVAL.md); partialling the one-sided share keeps ~97% and proves little
    c = ctl_score
    head = ("CONCRETE AND EVALUATIVE LANGUAGE IN FICTION, %d-2000. " % START) + ("Per text, as shares of content words. Top: concrete words "
        "(z >= 1 on the median of human concreteness and imageability norms, extended to period vocabulary). Bottom: words " if MODE == "v1" else
        "Top: concreteness, the mean over a text's words of a concreteness norm (z-scored median of human concreteness and "
        "imageability norms, extended to period vocabulary); positive is concrete, negative abstract. Bottom: per text, the share "
        "of content words that are words ")
    cap = textwrap.wrap(head + (
        "of clear positive or negative valence (a cleaned Warriner et al. 2013 lexicon plus rater-confirmed period "
        "vocabulary; above 6 or below 4 on the 1-9 scale). Gray points: decade medians over %s Chadwyck and Chicago novels; "
        "black line: lowess (span 0.3). Lines: model fiction, national stories from a neutral prompt (judged proper stories), "
        "each model-condition as one text, median over the lineages run in that condition (%d base, %d aligned, %d prefilled, "
        "%d chat). Evaluative language's historical fall and its rise under alignment both survive controlling for concreteness (abstraction's text score, partialled out by the slope "
        "within decade or within condition): the fall of evaluative language from the 1760s to the 1950s keeps %d%% of its "
        "size, and aligned exceeds base in %d of %d paired lineages (raw), %d of %d (prefilled) and %d of %d (chat), keeping "
        "%d%%, %d%% and %d%% of the median gap."
        % (format(Th._id.nunique(), ","), *[n_cond[COND[k]] for k in ("base", "raw", "prefill", "continue")],
           round(100 * hist_score[2] / hist_score[1]),
           c["raw"]["k"], c["raw"]["n"], c["prefill"]["k"], c["prefill"]["n"], c["continue"]["k"], c["continue"]["n"],
           *[round(100 * c[k]["gap_part"] / c[k]["gap_raw"]) for k in ("raw", "prefill", "continue")])), 100)
    if MODE == "ext":
        cap += textwrap.wrap("REFERENCE ONLY: third panel, evaluative extremity on the same cleaned lexicon, mean |valence - 5| "
                             "over every scored token including the neutral band (4-6).", 100)
        cap += ["", "  placement (crossing years of the smoothed history):"] + ["    %s %s: %s" % (nm, NAME[k], v) for (nm, k), v in place.items()]
    cap += ["", "  concrete arms: " + ", ".join("%s %.4f" % (NAME[k], v) for k, v in arms_c.items()),
            "  evaluative arms: " + ", ".join("%s %.4f" % (NAME[k], v) for k, v in arms_e.items())]
    open(OUT + ".caption.txt", "w").write("\n".join(cap) + "\n")
    print("\n".join(cap))

    R = ["# Figure 5 draft: concrete and evaluative shares (EXPLORATORY)", "",
         "Producer `arc_fig5_conc_eval.py` (method in its docstring). History %d-2009, %s texts. Concrete forms (z >= %.1f, "
         "stopwords out): %s." % (START, format(Th._id.nunique(), ","), ZCUT, format(len(conc), ",")), "",
         "Concrete share against abstraction's concreteness score: r = %.3f over texts, %.3f over model meta-texts." % (r_hist, r_meta), "",
         "## Evaluative share, aligned minus base, per lineage", "",
         "| control | slope | condition | lineages up, raw | lineages up, partialled | p (partialled) | median gap raw | median gap partialled | kept |",
         "|---|---|---|---|---|---|---|---|---|"]
    tail = ["", "## Evaluative share in the history, smoothed fall 1765 to 1955", "",
            "Partialled by the within-decade slope of text evaluative share on concreteness.", "",
            "| control | slope | fall raw | fall partialled | kept |", "|---|---|---|---|---|"]
    for lab, (b, f0, f1) in (("concreteness score", hist_score), ("concrete share", hist_share)):
        tail.append("| %s | %.4f | %.4f | %.4f | %d%% |" % (lab, b, f0, f1, round(100 * f1 / f0)))
    for lab, b, ctl in (("concreteness score", b_score, ctl_score), ("concrete share", b_share, ctl_share)):
        for k in ("raw", "prefill", "continue"):
            d = ctl[k]
            R.append("| %s | %.4f | %s | %d/%d | %d/%d | %.4f | %.4f | %.4f | %d%% |" % (lab, b, NAME[k], d["k_raw"], d["n"], d["k"], d["n"], d["p"],
                     d["gap_raw"], d["gap_part"], round(100 * d["gap_part"] / d["gap_raw"])))
    R += tail
    if MODE != "v1":
        return
    open(os.path.join(HERE, "ARC_FIG5_CONC_EVAL%s.md" % ("_1700" if START == 1700 else "")), "w").write("\n".join(R) + "\n")
    print("\n".join(R))


if __name__ == "__main__":
    main()
