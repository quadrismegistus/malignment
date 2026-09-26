"""Figure 5 variant: concreteness on top, NET VALENCE below -- positive minus negative words per content word, a signed
measure like the concreteness score above it. (RH, 2026-09-26: "Did we ever try Positive - Negative? Then we could say
'Valence in fictional language'?")

    .venv/bin/python -u arc_fig5_net_valence.py         -> figures/arc_fig5_conc_netval_v1_1700.{png,pdf,caption.txt}, ARC_FIG5_NET_VALENCE.md
    .venv/bin/python -u arc_fig5_net_valence.py three   -> figures/arc_fig5_conc_val3_v1_1700.*: THREE panels (RH, 2026-09-26: "Maybe
        we could do both? They tell different stories"): concreteness; "Valenced language in fiction (positive + negative)",
        v4's panel with its crossings; "Valence in fiction (positive - negative)". Both valence controls in the caption.

Everything as Figure 5 v4 (arc_fig5_conc_eval.py v4 1700): same 9,836 Chadwyck and Chicago novels 1700-2009, same
national-story meta-texts, same cleaned "+vector" lexicon with the same declared exclusions (model-text names and
"haven"), removed pole by pole. NET = positive rate - negative rate; the v4 panel's quantity is their SUM, and an
assert ties the two (pos + neg must reproduce v4's evaluative arms). CONTROL as in v4: per lineage, aligned minus base,
raw and with concreteness (abstraction's score) partialled by the within-condition slope; history, the smoothed curve
partialled by the within-decade slope. EXPLORATORY.
"""
import io, os, re, sys, textwrap

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
THREE = "three" in sys.argv[1:]                              # read before the argv rewrite below
sys.argv = [sys.argv[0], "v4", "1700"]
import arc_fig5_conc_eval as E                               # noqa: E402
V, H, A, F = E.V, E.H, E.A, E.F
from scipy.stats import binomtest                            # noqa: E402

OUT = os.path.join(HERE, "figures", "arc_fig5_conc_val3_v1_1700" if THREE else "arc_fig5_conc_netval_v1_1700")
COND, NAME = E.COND, E.NAME
#: booked (arc_fig5_conc_eval_v4_1700.caption.txt): v4's evaluative arms, which pos + neg must reproduce
V4_EVAL = {"base": 0.1721, "raw": 0.2174, "prefill": 0.2217, "continue": 0.2322}


def main():
    for ext in (".png", ".pdf", ".caption.txt"):
        assert not os.path.exists(OUT + ext), "refusing to overwrite " + OUT + ext
    _, sw, _ = A.lists_expanded()
    L = V.lexicons()
    lexv = L[E.LEX]
    X = E.EXCLUDE
    assert X and "lady" not in X
    Th = V.history(L).merge(H.concreteness_texts()[["_id", "year", "conc"]], on="_id")
    Th = Th[(Th.lexicon == E.LEX) & Th.year.between(E.START, 2009) & (Th.n_content >= H.MIN_CONTENT)].copy()
    Th["conc"] = Th.conc.astype(float)
    sql = f"""SELECT f._id AS _id, f.k AS word, f.v AS n FROM (SELECT _id, k, v FROM (SELECT _id, freqs FROM lltk.text_freqs FINAL
              WHERE _id IN ({A.REPS}) AND _id IN (SELECT _id FROM lltk.texts FINAL WHERE corpus IN ('chadwyck', 'chicago')))
              ARRAY JOIN mapKeys(freqs) AS k, mapValues(freqs) AS v) f INNER JOIN w ON f.k = w.form FORMAT TSVWithNames"""
    Rx = pd.read_csv(io.StringIO(A.ch_query(sql, {"w": ("form String", [(w,) for w in sorted(X)])})), sep="\t", keep_default_na=False)
    Rx["pole"] = np.where(Rx.word.map(lexv) > 6, "pos", "neg")
    P = Rx.pivot_table(index="_id", columns="pole", values="n", aggfunc="sum").reindex(columns=["pos", "neg"]).fillna(0)
    Th = Th.merge(P, left_on="_id", right_index=True, how="left").fillna({"pos": 0, "neg": 0})
    Th["pos_rate"] = Th.pos_rate - Th.pos / Th.n_content
    Th["neg_rate"] = Th.neg_rate - Th.neg / Th.n_content
    Th["net"] = Th.pos_rate - Th.neg_rate

    Mm = V.meta(L)
    Mm = Mm[Mm.lexicon == E.LEX].copy().rename(columns={V.CONC: "conc"})
    Mt = pd.read_parquet(os.path.join(A.DATA, "prompt_check_national_judged_meta.parquet"))
    xp, xn = {}, {}
    for r in Mt.itertuples():
        t = [w for w in re.findall(r"[a-z]+", r.text.lower()) if w not in sw]
        xp[r.id] = sum(w in X and lexv[w] > 6 for w in t) / len(t)
        xn[r.id] = sum(w in X and lexv[w] < 4 for w in t) / len(t)
    Mm["pos_rate"] = Mm.pos_rate - Mm.id.map(xp)
    Mm["neg_rate"] = Mm.neg_rate - Mm.id.map(xn)
    Mm["net"] = Mm.pos_rate - Mm.neg_rate
    med_sum = (Mm.assign(s=Mm.pos_rate + Mm.neg_rate)).pivot_table(index="lineage", columns="cond", values="s").median()
    for k, v in V4_EVAL.items():
        assert abs(med_sum[COND[k]] - v) < 5e-5, (k, med_sum[COND[k]], v)

    med = {c: Mm.pivot_table(index="lineage", columns="cond", values=c).median() for c in ("net", "pos_rate", "neg_rate", "conc")}
    arms_n = {k: float(med["net"][COND[k]]) for k in COND}
    arms_s = {k: float(med["conc"][COND[k]]) for k in COND}
    hs, hn = H.decades(Th.year, Th.conc), H.decades(Th.year, Th.net)
    cvs, cvn = H.smooth(hs), H.smooth(hn)

    # controls
    yd = Mm.net - Mm.groupby("cond").net.transform("mean")
    xd = Mm.conc - Mm.groupby("cond").conc.transform("mean")
    b = float(np.polyfit(xd, yd, 1)[0])
    ctl = {}
    for k in ("raw", "prefill", "continue"):
        res = []
        for y in (Mm.net, Mm.net - b * Mm.conc):
            piv = Mm.assign(v=y).pivot_table(index="lineage", columns="cond", values="v")[["base", COND[k]]].dropna()
            g = piv[COND[k]] - piv["base"]
            res.append((int((g > 0).sum()), len(g), binomtest(int((g > 0).sum()), len(g)).pvalue, float(g.median())))
        ctl[k] = res
    dec = Th.year // 10
    bh = float(np.polyfit(Th.conc - Th.groupby(dec).conc.transform("mean"), Th.net - Th.groupby(dec).net.transform("mean"), 1)[0])
    cvn_p = H.smooth(H.decades(Th.year, Th.net - bh * (Th.conc - Th.conc.mean())))
    at = lambda cv, y: float(np.interp(y, cv[:, 0], cv[:, 1]))
    peak_y = float(cvn[np.argmax(cvn[:, 1]), 0])
    place = lambda cv, v: (", ".join(str(round(x)) for x, _ in E.crossings(cv, v)) or
                           ("above every decade" if v > cv[:, 1].max() else "below every decade"))

    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["pdf.fonttype"] = 42
    from plotnine.composition import Stack
    if THREE:
        Th["eval_rate"] = Th.pos_rate + Th.neg_rate
        Mm["eval_rate"] = Mm.pos_rate + Mm.neg_rate
        arms_v = {k: float(med_sum[COND[k]]) for k in COND}
        hv = H.decades(Th.year, Th.eval_rate)
        cvv = H.smooth(hv)
        _, ctl_v = E.control(Mm, "eval_rate", "conc")
        hist_v = E.history_control(Th, "conc")
        #: booked (arc_fig5_conc_eval_v4_1700.caption.txt): the middle panel IS v4's, so its controls must be v4's
        assert [(ctl_v[k]["k"], ctl_v[k]["n"]) for k in ("raw", "prefill", "continue")] == [(25, 32), (20, 23), (17, 20)], ctl_v
        assert round(100 * hist_v[2] / hist_v[1]) == 65, hist_v
        cross_v = {k: [round(x) for x, _ in E.crossings(cvv, v)] for k, v in arms_v.items()}
        assert cross_v == {"base": [1906], "raw": [1821], "prefill": [1815], "continue": [1744, 1797]}, cross_v
        ps = [E.panel(hs, cvs, arms_s, "Concreteness of fictional language", "Concreteness\n(word norm mean)", False, pct=False),
              E.panel(hv, cvv, arms_v, "Valenced language in fiction (positive + negative)", "Valenced words\n(per content word)", False),
              E.panel(hn, cvn, arms_n, "Valence in fiction (positive \u2212 negative)", "Positive minus negative\nwords (per content word)", True)]
    else:
        ps = [E.panel(hs, cvs, arms_s, "Concreteness of fictional language", "Concreteness\n(word norm mean)", False, pct=False),
              E.panel(hn, cvn, arms_n, "Valence in fictional language", "Positive minus negative\nwords (per content word)", True)]
    fig = Stack(ps).draw()
    fig.set_size_inches(F.PUB_SIZE[0], 8.2 if THREE else 5.6)
    fig.savefig(OUT + ".png", dpi=300)
    fig.savefig(OUT + ".pdf")

    n_cond = Mm.groupby("cond").lineage.nunique()
    above = [NAME[k] for k in COND if arms_n[k] > cvn[:, 1].max()]
    cap = textwrap.wrap(
        "CONCRETENESS AND VALENCE IN FICTION, 1700-2000. Top: concreteness, the mean over a text's words of a concreteness norm "
        "(z-scored median of human concreteness and imageability norms, extended to period vocabulary); positive is concrete, "
        "negative abstract. Bottom: per text, positive words minus negative words, as a share of content words (a cleaned "
        "Warriner et al. 2013 lexicon plus rater-confirmed period vocabulary; positive above 6, negative below 4 on the 1-9 "
        "scale). Gray points: decade medians over %s Chadwyck and Chicago novels; black line: lowess (span 0.3). Lines: model "
        "fiction, national stories from a neutral prompt (judged proper stories), each model-condition as one text, median over "
        "the lineages run in that condition (%d base, %d aligned, %d prefilled, %d chat). Removed from the valence lexicon on both "
        "sides: words used mostly as names in the model stories (%s), and \"haven\", which the tokenisation makes of \"haven't\". "
        "%s With concreteness partialled out (abstraction's score, "
        "slope within condition), aligned exceeds base in %d of %d paired lineages (raw), %d of %d (prefilled) and %d of %d (chat)."
        % (format(len(Th), ","), *[n_cond[COND[k]] for k in COND], ", ".join(sorted(X - {"haven"})),
           ("No model line meets the smoothed valence history: all four lie above it, base models just above (decade medians "
            "reach the base line in %d decades), aligned models at more than twice its highest point." % int((hn.value >= arms_n["base"]).sum())
            if len(above) == 4 else "Circles mark where a model line crosses the smoothed history."),
           *[x for k in ("raw", "prefill", "continue") for x in ctl[k][1][:2]]), 100)
    cap += ["", "  net arms: " + ", ".join("%s %.4f" % (NAME[k], v) for k, v in arms_n.items()),
            "  placements (net): " + "; ".join("%s %s" % (NAME[k], place(cvn, v)) for k, v in arms_n.items()),
            "  concreteness arms: " + ", ".join("%s %.4f" % (NAME[k], v) for k, v in arms_s.items())]
    if THREE:
        cap = textwrap.wrap(
            "CONCRETENESS, VALENCED LANGUAGE AND VALENCE IN FICTION, 1700-2000. Top: concreteness, the mean over a text's words of a "
            "concreteness norm (z-scored median of human concreteness and imageability norms, extended to period vocabulary); "
            "positive is concrete, negative abstract. Middle and bottom: per text, positive words PLUS negative words, and positive "
            "words MINUS negative words, as shares of content words (a cleaned Warriner et al. 2013 lexicon plus rater-confirmed "
            "period vocabulary; positive above 6, negative below 4 on the 1-9 scale). The middle panel measures how much charged "
            "vocabulary a text uses, the bottom which way it leans. Gray points: decade medians over %s Chadwyck and Chicago novels; "
            "black line: lowess (span 0.3). Lines: model fiction, national stories from a neutral prompt (judged proper stories), "
            "each model-condition as one text, median over the lineages run in that condition (%d base, %d aligned, %d prefilled, "
            "%d chat). Removed from the valence lexicon on both sides: words used mostly as names in the model stories (%s), and "
            "\"haven\", which the tokenisation makes of \"haven't\". Circles mark where a model line crosses the smoothed history; the "
            "year labels its last crossing (an earlier one: Aligned (chat) %d in the middle panel). No model line meets the valence "
            "history: all four lie above it, base models just above (decade medians reach the base line in %d decades), aligned "
            "models at more than twice its highest point. Controlling for concreteness (abstraction's score, partialled out by the "
            "slope within decade or within condition): the fall of valenced language from the 1760s to the 1950s keeps %d%% of its "
            "size, and aligned exceeds base in %d of %d paired lineages (raw), %d of %d (prefilled) and %d of %d (chat) in valenced "
            "language, and in %d of %d, %d of %d and %d of %d in valence."
            % (format(len(Th), ","), *[n_cond[COND[k]] for k in COND], ", ".join(sorted(X - {"haven"})), cross_v["continue"][0],
               int((hn.value >= arms_n["base"]).sum()), round(100 * hist_v[2] / hist_v[1]),
               *[x for k in ("raw", "prefill", "continue") for x in (ctl_v[k]["k"], ctl_v[k]["n"])],
               *[x for k in ("raw", "prefill", "continue") for x in ctl[k][1][:2]]), 100)
        cap += ["", "  valenced arms: " + ", ".join("%s %.4f" % (NAME[k], v) for k, v in arms_v.items()),
                "  valenced crossings: " + "; ".join("%s %s" % (NAME[k], ", ".join(map(str, v))) for k, v in cross_v.items()),
                "  net arms: " + ", ".join("%s %.4f" % (NAME[k], v) for k, v in arms_n.items()),
                "  concreteness arms: " + ", ".join("%s %.4f" % (NAME[k], v) for k, v in arms_s.items())]
    open(OUT + ".caption.txt", "w").write("\n".join(cap) + "\n")
    if THREE:
        print("\n".join(cap))
        return

    R = ["# Net valence (positive minus negative), Figure 5 variant (EXPLORATORY)", "",
         "Producer `arc_fig5_net_valence.py` (method in its docstring). Plate: figures/arc_fig5_conc_netval_v1_1700.png. Per content word.", "",
         "## Model lines (median over lineages)", "", "| line | positive | negative | net | sum (v4 panel) | placement of net on the history |", "|---|---|---|---|---|---|"]
    for k in COND:
        R.append("| %s | %.4f | %.4f | %.4f | %.4f | %s |" % (NAME[k], med["pos_rate"][COND[k]], med["neg_rate"][COND[k]], arms_n[k], med_sum[COND[k]], place(cvn, arms_n[k])))
    R += ["", "Medians are taken per measure, so positive minus negative medians need not equal the net median.", "",
          "## History (smoothed net)", "",
          "- Range %.4f to %.4f; peak at %d." % (cvn[:, 1].min(), cvn[:, 1].max(), peak_y),
          "- 1765: %.4f; 1955: %.4f; 2005: %.4f." % (at(cvn, 1765), at(cvn, 1955), at(cvn, 2005)),
          "- With concreteness partialled (within-decade slope %.4f): 1765 %.4f, 1955 %.4f." % (bh, at(cvn_p, 1765), at(cvn_p, 1955)), "",
          "## Aligned minus base, per lineage (net)", "", "| condition | up, raw | p | median gap | up, concreteness partialled | p | median gap |", "|---|---|---|---|---|---|---|"]
    for k in ("raw", "prefill", "continue"):
        a, c = ctl[k]
        R.append("| %s | %d/%d | %.4f | %+.4f | %d/%d | %.4f | %+.4f |" % (NAME[k], a[0], a[1], a[2], a[3], c[0], c[1], c[2], c[3]))
    open(os.path.join(HERE, "ARC_FIG5_NET_VALENCE.md"), "w").write("\n".join(R) + "\n")
    print("\n".join(cap))
    print("\n".join(R))


if __name__ == "__main__":
    main()
