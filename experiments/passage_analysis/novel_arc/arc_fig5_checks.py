"""Three checks the paper seat asked for before Figure 5 (arc_fig5_conc_eval_v3_1700) carries claims. (TheoryMachines,
2026-09-26)

    .venv/bin/python -u arc_fig5_checks.py   -> ARC_FIG5_CHECKS.md

Same populations as the figure: Chadwyck and Chicago novels 1700-2009, >= 2,000 content words; judged no-demonym
national stories, one meta-text per model-condition.
1 PAIRED CONCRETENESS. Per lineage, aligned minus base on abstraction's text score for each condition, and prefilled
  and chat minus aligned-raw: k of n MORE ABSTRACT (gap < 0), two-sided binomial p, median gap.
2 ONE POPULATION. The lineages run in all four conditions: the four lines and their crossing years on that set.
3 EVALUATION AGAINST INNER LIFE. Evaluative share partialled on (a) usas_x's analogue, the full primary-sense USAS X
  list (arc_interiority's `fullx`, expanded for spelling and long-s), (b) the USAS E (emotion) field, every rank-0
  member of E1-E6 expanded the same way, (c) X and E together, (d) X, E and concreteness together. Partial = the
  within-decade (history) or within-condition (models) OLS slope(s), as for concreteness. And (e) the evaluative
  share with every X or E word REMOVED from the evaluative lexicon: a lexical rather than statistical control, since
  love, fear and happy are both evaluative and emotional. All shares per content word (arc_interiority's content
  tokens). EXPLORATORY.
"""
import io, json, os, re, sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.argv = [sys.argv[0], "v3", "1700"]
import arc_fig5_conc_eval as E                               # noqa: E402
V, H, A = E.V, E.H, E.A
from scipy.stats import binomtest                            # noqa: E402

OUT = os.path.join(HERE, "ARC_FIG5_CHECKS.md")
USAS = os.path.join(A.DATA, "usas_fields_members.json")
E_TEXTS = os.path.join(A.DATA, "usas_e_texts_cc.parquet")
INT = os.path.join(A.DATA, "arc_interiority_texts.parquet")
COND, NAME = E.COND, E.NAME


def e_list(sw):
    from wordfreq import zipf_frequency
    d = json.load(open(USAS))["codes"]
    ws = {m["word"].lower() for k, c in d.items() if k.startswith("E") for m in c["members"] if m["rank"] == 0}
    ws = {w for w in ws if w.isalpha()}
    morph = []
    for line in open(A.MORPH, encoding="utf-8", errors="replace"):
        p = line.rstrip("\n").split("\t")
        if len(p) == 2 and p[0].isalpha() and p[1].isalpha():
            morph.append((p[0].lower(), p[1].lower()))
    ex, _, _ = A.expand(ws, morph, zipf_frequency)
    return ex - sw, len(ws)


def history_counts(words, path, col):
    if os.path.exists(path):
        return pd.read_parquet(path)
    sql = f"""SELECT f._id AS _id, sum(f.v) AS {col}
      FROM (SELECT _id, k, v FROM (SELECT _id, freqs FROM lltk.text_freqs FINAL WHERE _id IN ({A.REPS})
              AND _id IN (SELECT _id FROM lltk.texts FINAL WHERE corpus IN ('chadwyck', 'chicago')))
            ARRAY JOIN mapKeys(freqs) AS k, mapValues(freqs) AS v) f
      INNER JOIN w ON f.k = w.form GROUP BY _id FORMAT TSVWithNames"""
    R = pd.read_csv(io.StringIO(A.ch_query(sql, {"w": ("form String", [(w,) for w in sorted(words)])})), sep="\t")
    R.to_parquet(path, index=False)
    return R


def partial(df, y, xs, grp):
    """y minus the within-group OLS fit on xs (centred), -> series"""
    yd = df[y] - df.groupby(grp)[y].transform("mean")
    Xd = np.column_stack([df[x] - df.groupby(grp)[x].transform("mean") for x in xs])
    b = np.linalg.lstsq(Xd, yd.values, rcond=None)[0]
    return df[y] - (np.column_stack([df[x] - df[x].mean() for x in xs]) @ b), b


def paired(Mm, col, a, b, sign):
    """lineages with both conditions: k of n where (a - b) has `sign`, binomial p, median gap"""
    piv = Mm.pivot_table(index="lineage", columns="cond", values=col)[[a, b]].dropna()
    g = piv[a] - piv[b]
    k = int((np.sign(g) == sign).sum())
    return k, len(g), binomtest(k, len(g)).pvalue, float(g.median())


def fall(Th, col):
    cv = H.smooth(H.decades(Th.year, Th[col]))
    return float(np.interp(1765, cv[:, 0], cv[:, 1]) - np.interp(1955, cv[:, 0], cv[:, 1]))


def main():
    _, sw, _ = A.lists_expanded()
    ex, _, _ = A.lists_expanded()
    X = ex["fullx"]
    Ew, n_e = e_list(sw)
    L = V.lexicons()
    lex = L[E.LEX]
    Th = V.history(L).merge(H.concreteness_texts()[["_id", "year", "conc"]], on="_id")
    Th = Th[(Th.lexicon == E.LEX) & Th.year.between(E.START, 2009) & (Th.n_content >= H.MIN_CONTENT)].copy()
    Th["conc"] = Th.conc.astype(float)
    I = pd.read_parquet(INT).rename(columns={"r._id": "_id"})[["_id", "n_content", "n_fullx"]].rename(columns={"n_content": "nc_int"})
    Th = Th.merge(I, on="_id")
    #: the X counts' denominator must be the evaluative share's, or the partial mixes two token definitions
    assert (Th.nc_int == Th.n_content).all(), "content-token counts differ between the two tables"
    Th["usas_x"] = Th.n_fullx / Th.n_content
    Th = Th.merge(history_counts(Ew, E_TEXTS, "n_e"), on="_id", how="left").fillna({"n_e": 0})
    Th["usas_e"] = Th.n_e / Th.n_content
    XE = X | Ew
    lex_d = {w: v for w, v in lex.items() if w not in XE and (v < 4 or v > 6)}
    Td = history_counts(set(lex_d), os.path.join(A.DATA, "eval_disjoint_xe_texts_cc.parquet"), "n_eval_d")
    Th = Th.merge(Td, on="_id", how="left").fillna({"n_eval_d": 0})
    Th["eval_disjoint"] = Th.n_eval_d / Th.n_content
    Th["xe"] = Th.usas_x + Th.usas_e
    assert len(Th) == 9836, len(Th)                       # booked: the figure's 1700+ population

    Mm = V.meta(L)
    Mm = Mm[Mm.lexicon == E.LEX].copy()
    M = pd.read_parquet(os.path.join(A.DATA, "prompt_check_national_judged_meta.parquet"))
    rows = []
    for r in M.itertuples():
        t = [w for w in re.findall(r"[a-z]+", r.text.lower()) if w not in sw]
        n = len(t)
        rows.append(dict(id=r.id, usas_x=sum(w in X for w in t) / n, usas_e=sum(w in Ew for w in t) / n,
                         eval_disjoint=sum(w in lex_d and (lex_d[w] < 4 or lex_d[w] > 6) for w in t) / n,
                         eval_xe_tokens=sum(w in XE and w in lex and (lex[w] < 4 or lex[w] > 6) for w in t) / n))
    Mm = Mm.merge(pd.DataFrame(rows), on="id")
    Mm["xe"] = Mm.usas_x + Mm.usas_e
    Mm = Mm.rename(columns={V.CONC: "conc"})

    R = ["# Figure 5 checks for the paper seat (EXPLORATORY)", "",
         "Producer `arc_fig5_checks.py` (method in its docstring). Figure: figures/arc_fig5_conc_eval_v3_1700.png. History: %s "
         "Chadwyck and Chicago novels, 1700-2009. USAS E list: %d rank-0 members of E1-E6, %s forms after expansion; full X: %s "
         "forms." % (format(len(Th), ","), n_e, format(len(Ew), ","), format(len(X), ",")), ""]

    # 1 paired concreteness
    R += ["## 1. Paired concreteness (abstraction's text score; negative gap = more abstract)", "",
          "| contrast | lineages more abstract | p | median gap |", "|---|---|---|---|"]
    pairs = [("aligned_raw", "base"), ("aligned_prefill", "base"), ("aligned_rettberg", "base"),
             ("aligned_prefill", "aligned_raw"), ("aligned_rettberg", "aligned_raw")]
    lab = {v: NAME[k] for k, v in COND.items()}
    for a, b in pairs:
        k, n, p, g = paired(Mm, "conc", a, b, -1)
        R.append("| %s minus %s | %d/%d | %.4f | %+.4f |" % (lab[a], lab[b], k, n, p, g))

    # 2 common population
    piv = {c: Mm.pivot_table(index="lineage", columns="cond", values=c) for c in ("conc", "eval_rate")}
    common = piv["conc"][list(COND.values())].dropna().index
    R += ["", "## 2. One population: the %d lineages run in all four conditions" % len(common), "",
          "Lines = median over those lineages; crossings on the same smoothed 1700+ history as the figure.", "",
          "| measure | line | all lineages (figure) | crossing | common set | crossing |", "|---|---|---|---|---|---|"]
    for c, hc in (("conc", "conc"), ("eval_rate", "eval_rate")):
        cv = H.smooth(H.decades(Th.year, Th[hc]))
        for k, cd in COND.items():
            v_all, v_com = float(piv[c][cd].median()), float(piv[c].loc[common, cd].median())
            cr = lambda v: ", ".join(str(round(x)) for x, _ in E.crossings(cv, v)) or ("above all" if v > cv[:, 1].max() else "below all")
            R.append("| %s | %s | %.4f | %s | %.4f | %s |" % ("concreteness" if c == "conc" else "evaluative share", NAME[k], v_all, cr(v_all), v_com, cr(v_com)))
    R += ["", "Paired tests on the common set (aligned minus base; concreteness counts MORE ABSTRACT, evaluation counts MORE EVALUATIVE):", "",
          "| measure | condition | k/n | p | median gap |", "|---|---|---|---|---|"]
    Mc = Mm[Mm.lineage.isin(common)]
    for c, sgn in (("conc", -1), ("eval_rate", 1)):
        for k in ("raw", "prefill", "continue"):
            kk, n, p, g = paired(Mc, c, COND[k], "base", sgn)
            R.append("| %s | %s | %d/%d | %.4f | %+.4f |" % ("concreteness" if c == "conc" else "evaluative share", NAME[k], kk, n, p, g))

    # 3 evaluation against inner life
    R += ["", "## 3. Evaluative share against inner-life vocabulary", "",
          "Raw levels (median over lineages / history range):", "",
          "| measure | base | aligned | prefilled | chat | history 1765 | history 1955 |", "|---|---|---|---|---|---|---|"]
    lv, fall_lv = {}, {}
    for c, nm in (("usas_x", "USAS X share"), ("usas_e", "USAS E share"), ("eval_rate", "evaluative share"), ("eval_disjoint", "evaluative share, X and E words removed")):
        med = Mm.pivot_table(index="lineage", columns="cond", values=c).median()
        cv = H.smooth(H.decades(Th.year, Th[c]))
        R.append("| %s | %s | %.4f | %.4f |" % (nm, " | ".join("%.4f" % med[COND[k]] for k in COND), np.interp(1765, cv[:, 0], cv[:, 1]), np.interp(1955, cv[:, 0], cv[:, 1])))
        lv[c], fall_lv[c] = med, (float(np.interp(1765, cv[:, 0], cv[:, 1])), float(np.interp(1955, cv[:, 0], cv[:, 1])))
    ov_m = (Mm.eval_xe_tokens / Mm.eval_rate).median()
    R += ["", "Share of evaluative TOKENS that are also X or E words, model meta-texts (median): %.1f%%." % (100 * ov_m), "",
          "Controls. History: the smoothed 1765-1955 fall, kept share. Models: aligned minus base per lineage, k MORE EVALUATIVE of n, and the median gap kept.", "",
          "| control | history fall kept | aligned (raw) | prefilled | chat |", "|---|---|---|---|---|"]
    f0 = fall(Th, "eval_rate")
    specs = [("none", None), ("concreteness", ["conc"]), ("USAS X", ["usas_x"]), ("USAS E", ["usas_e"]), ("X and E", ["usas_x", "usas_e"]),
             ("X, E and concreteness", ["usas_x", "usas_e", "conc"]), ("lexical: X and E words removed", "disjoint")]
    for nm, xs in specs:
        if xs is None:
            th, mm = Th.eval_rate, Mm.eval_rate
        elif xs == "disjoint":
            th, mm = Th.eval_disjoint, Mm.eval_disjoint
        else:
            th, _ = partial(Th.assign(dec=Th.year // 10), "eval_rate", xs, "dec")
            mm, _ = partial(Mm, "eval_rate", xs, "cond")
        Tq, Mq = Th.assign(q=th), Mm.assign(q=mm)
        cells = []
        for k in ("raw", "prefill", "continue"):
            kk, n, p, g = paired(Mq, "q", COND[k], "base", 1)
            g_raw = paired(Mm, "eval_rate", COND[k], "base", 1)[3]
            cells.append("%d/%d (p %.4f), %d%%" % (kk, n, p, round(100 * g / g_raw)))
        R.append("| %s | %d%% | %s |" % (nm, round(100 * fall(Tq, "q") / f0), " | ".join(cells)))
    R += ["", "Gap kept is against the UNCONTROLLED evaluative gap in every row, including the lexical one, so the rows are comparable.",
          "That makes the lexical row conservative: removing X and E words shrinks the lexicon, so absolute gaps shrink with it. "
          "In RELATIVE terms (from the levels table): history 1765 to 1955, all evaluative words %+.0f%%, X and E removed %+.0f%%; "
          "base to aligned / prefilled / chat, all %s, removed %s." % (
              100 * (fall_lv["eval_rate"][1] / fall_lv["eval_rate"][0] - 1), 100 * (fall_lv["eval_disjoint"][1] / fall_lv["eval_disjoint"][0] - 1),
              " / ".join("%+.0f%%" % (100 * (lv["eval_rate"][COND[k]] / lv["eval_rate"]["base"] - 1)) for k in ("raw", "prefill", "continue")),
              " / ".join("%+.0f%%" % (100 * (lv["eval_disjoint"][COND[k]] / lv["eval_disjoint"]["base"] - 1)) for k in ("raw", "prefill", "continue"))),
          "Statistical partials on E overlap the evaluative lexicon by construction (love, fear), so they remove shared vocabulary "
          "as well as shared variance; the lexical row is the cleaner test of whether inner-life words carry the result."]
    open(OUT, "w").write("\n".join(R) + "\n")
    print("\n".join(R))


if __name__ == "__main__":
    main()
