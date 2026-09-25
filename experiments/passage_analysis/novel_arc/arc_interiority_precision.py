"""The arc_fiction interiority curves redrawn with the precision-kept lists. (RH, 2026-09-25)

    .venv/bin/python -u arc_interiority_precision.py --count    -> $MALIGNMENT_DATA/novel_arc/arc_interiority_texts_precision.parquet
    .venv/bin/python -u arc_interiority_precision.py --report   -> ARC_INTERIORITY_PRECISION.md, figures/arc_interiority_precision_decades.*
    add --vetted to either: lists from interiority_vetting.py's conservative hand vetting; outputs suffixed _vetted

BEFORE is arc_interiority.py: clean X (1,526) and the period candidates (2,161) with every MorphAdorner
variant and long-s reading added mechanically. The candidates' tokens were dominated by would, like, say,
looked, and RH asked for a precision-first re-rating that also judged the variants (interiority_precision.py).

AFTER, per list:
  - base words the precision consensus keeps (RH's hand removals already excluded there);
  - MorphAdorner variants the consensus keeps AS FORMS, and only when a word they spell is itself kept on
    that list (a variant of `waiting` does not outlive `waiting`);
  - minus any kept variant that is a common modern word (wordfreq zipf >= 3): the rater was told to judge
    the form as written, and this is the executable backstop for `red` as a spelling of `read`;
  - plus long-s OCR readings of every kept form, rule unchanged (zipf < 2);
  - minus stopwords, with arc_interiority's expanded stopword list, so the denominator is identical.
Denominator, text set, floors and decade medians are arc_interiority's; the BEFORE numerators are read
from its committed parquet and joined by _id, so the two sides differ only in the lists. EXPLORATORY.
"""
import io, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import arc_interiority as A                                   # noqa: E402

VETTED = "--vetted" in sys.argv
SUF = "_vetted" if VETTED else ""
KEEP_CSV = os.path.join(A.SHARED, "precision_keep_v2%s.csv" % SUF)
KEEP_COL = "keep_vetted" if VETTED else "keep"
OUT = os.path.join(A.DATA, "arc_interiority_texts_precision%s.parquet" % SUF)
AFTER = "vetted" if VETTED else "precision"
NEW = ("cleanx_p", "cand_p", "comb_p")
LABEL = {"cleanx": "Clean X, before", "cleanx_p": "Clean X, " + AFTER,
         "comb": "Clean X + candidates, before", "comb_p": "Clean X + candidates, " + AFTER,
         "cand": "Candidates, before", "cand_p": "Candidates, " + AFTER}
MODERN_ZIPF = 3.0


def lists_precision():
    import pandas as pd
    from wordfreq import zipf_frequency
    K = pd.read_csv(KEEP_CSV)
    assert len(K) == 15099, len(K)       # 15,101 rated forms less bright and would, rated only as anchors
    base = K[K.spelling_of.isna()]
    kept = {s: set(base[(base.source == s) & base[KEEP_COL]].form) for s in ("cleanx", "cand")}
    assert not (kept["cleanx"] | kept["cand"]) & A_RH_REMOVED(), "an RH removal survived consensus"
    info, ex = {}, {}
    var = K[K.spelling_of.notna() & K[KEEP_COL]]
    modern = {v for v in var.form if zipf_frequency(v, "en") >= MODERN_ZIPF}
    _, sw, _ = A.lists_expanded()
    for s in ("cleanx", "cand"):
        mv = {r.form for r in var.itertuples() if set(r.spelling_of.split(", ")) & kept[s]}
        out = kept[s] | (mv - modern)
        ls = set()
        for w in out:
            ls |= A.long_s(w, zipf_frequency)
        out = {w for w in out | ls if w.isalpha()}
        clash = out & sw
        ex[s + "_p"] = out - clash
        info[s + "_p"] = dict(base_kept=len(kept[s]), base_rated=int((base.source == s).sum()),
                              variants_kept=len(mv - modern), variants_dropped_modern=sorted(mv & modern),
                              long_s=len(ls - kept[s] - mv), expanded=len(ex[s + "_p"]), dropped_as_stopword=len(clash))
    ex["comb_p"] = ex["cleanx_p"] | ex["cand_p"]
    info["comb_p"] = dict(expanded=len(ex["comb_p"]))
    return ex, sw, info


def A_RH_REMOVED():
    import interiority_precision as P
    return P.RH_REMOVED


def count():
    import pandas as pd
    assert not os.path.exists(OUT), "refusing to overwrite " + OUT
    ex, sw, info = lists_precision()
    print(json.dumps(info, indent=1))
    lw = [(w, k) for k in ("cleanx_p", "cand_p") for w in sorted(ex[k])]
    sql = f"""
      SELECT _id,
        sumIf(v, k IN (SELECT word FROM lw WHERE list = 'cleanx_p')) AS n_cleanx_p,
        sumIf(v, k IN (SELECT word FROM lw WHERE list = 'cand_p')) AS n_cand_p,
        sumIf(v, k IN (SELECT word FROM lw)) AS n_comb_p
      FROM (SELECT _id, freqs FROM lltk.text_freqs FINAL WHERE _id IN ({A.REPS}))
      ARRAY JOIN mapKeys(freqs) AS k, mapValues(freqs) AS v
      GROUP BY _id
      FORMAT TSVWithNames"""
    N = pd.read_csv(io.StringIO(A.ch_query(sql, {"lw": ("word String, list String", lw)})), sep="\t")
    #: a short read under load has happened before; the population is booked
    assert len(N) == 82080, len(N)
    #: arc_interiority's parquet carries the join alias as its column name
    D = pd.read_parquet(A.OUT).rename(columns={"r._id": "_id"}).merge(N, on="_id", how="inner", validate="1:1")
    assert len(D) == 82080, len(D)
    assert (D.n_cleanx_p <= D.n_content).all() and (D.n_comb_p <= D.n_content).all()
    D.to_parquet(OUT, index=False)
    json.dump(info, open(OUT.replace(".parquet", "_lists.json"), "w"), indent=1)
    print("-> %s (%d texts)" % (OUT, len(D)))


def report():
    import pandas as pd
    import matplotlib
    matplotlib.use("Agg")
    from plotnine import (ggplot, aes, geom_line, facet_wrap, labs, scale_color_manual,
                          scale_linetype_manual, theme, element_text, guides, guide_legend)
    from scipy.stats import spearmanr
    from malignment import figure as F
    D = pd.read_parquet(OUT)
    info = json.load(open(OUT.replace(".parquet", "_lists.json")))
    D = D[(D.n_content >= A.MIN_CONTENT) & D.year.between(1600, 2009)].copy()
    keys = ("cleanx", "cand", "comb") + NEW
    for k in keys:
        D[k] = D["n_" + k] / D.n_content
    D["decade"] = (D.year // 10) * 10
    rows = []
    for (src, dec), g in D.groupby(["source", "decade"]):
        if len(g) >= A.MIN_TEXTS and src != "unclassified":
            rows.append(dict(source=src, decade=dec, n=len(g), **{k: float(g[k].median()) for k in keys}))
    C = pd.DataFrame(rows)
    shown = ["cleanx", "cleanx_p", "comb", "comb_p"]
    long = []
    for src, g in C.groupby("source"):
        for k in shown:
            long += [dict(source=src, decade=r.decade, list=LABEL[k], pct=100 * getattr(r, k)) for r in g.itertuples()]
    Lg = pd.DataFrame(long)
    order = [LABEL[k] for k in shown]
    Lg["list"] = pd.Categorical(Lg.list, categories=order)
    Lg["source"] = pd.Categorical(Lg.source, categories=["transcribed", "ocr", "modern/other"])
    p = (ggplot(Lg, aes("decade", "pct", color="list", linetype="list"))
         + geom_line(size=0.7)
         + facet_wrap("~source", ncol=1, scales="free_y")
         + guides(color=guide_legend(nrow=2), linetype=guide_legend(nrow=2))
         + scale_color_manual({order[0]: F.PUB_INK, order[1]: F.PUB_INK, order[2]: F.PUB_MID, order[3]: F.PUB_MID})
         + scale_linetype_manual({order[0]: "dashed", order[1]: "solid", order[2]: "dashed", order[3]: "solid"})
         + labs(x="", y="Decade median, % of content tokens", color="", linetype="")
         + F.pub_theme(height=6.0) + theme(legend_position="bottom", figure_size=(F.PUB_SIZE[0], 6.0),
                                           strip_text=element_text(family=F.pub_font(), size=F.PUB_FONT_PT)))
    fig = os.path.join(HERE, "figures", "arc_interiority_precision_decades" + SUF)
    for ext in (".png", ".pdf"):
        assert not os.path.exists(fig + ext), "refusing to overwrite " + fig + ext
    F.save(p, fig + ".png")
    #: token mass of the new lists: what now carries the curve
    ex, _, _ = lists_precision()
    mass = {}
    for k in ("cleanx_p", "cand_p"):
        sql = f"""
          SELECT k AS word, sum(v) AS n
          FROM (SELECT _id, freqs FROM lltk.text_freqs FINAL WHERE _id IN ({A.REPS}))
          ARRAY JOIN mapKeys(freqs) AS k, mapValues(freqs) AS v
          WHERE k IN (SELECT word FROM cw)
          GROUP BY word ORDER BY n DESC
          FORMAT TSVWithNames"""
        T = pd.read_csv(io.StringIO(A.ch_query(sql, {"cw": ("word String", [(w,) for w in sorted(ex[k])])})), sep="\t")
        T.to_csv(os.path.join(A.SHARED, "arc_token_mass_%s%s.csv" % (k, SUF)), index=False)
        mass[k] = T
    L = ["# Interiority curves over arc_fiction, before and after the %s lists (EXPLORATORY)" % AFTER, "",
         "Producer `arc_interiority_precision.py`. Same %d arc_fiction reps, denominator, floors (at least %d content "
         "tokens, %d texts per decade and source group) as ARC_INTERIORITY.md; %d texts enter. BEFORE numerators from "
         "arc_interiority's parquet; AFTER lists from %s (see the docstring for the rule). Plate: "
         "figures/arc_interiority_precision_decades%s.png (levels, not indexed)." % (
             82080, A.MIN_CONTENT, A.MIN_TEXTS, len(D), os.path.basename(KEEP_CSV) + (" (keep_vetted)" if VETTED else ""), SUF), "",
         "## Lists", ""]
    for k, v in info.items():
        L.append("- %s: %s" % (LABEL.get(k, k), ", ".join("%s %s" % (a, b if not isinstance(b, list) else
                                                                     (", ".join(b) if b else "none")) for a, b in v.items())))
    L += ["", "## Does the re-rating change the history? Decade-series agreement, before vs after", "",
          "| source | decades | rho(clean X) | rho(candidates) | rho(clean X + candidates) | rho(clean X after, comb after) |",
          "|---|---|---|---|---|---|"]
    for src, g in C.groupby("source"):
        L.append("| %s | %d | %+.3f | %+.3f | %+.3f | %+.3f |" % (
            src, len(g), spearmanr(g.cleanx, g.cleanx_p)[0], spearmanr(g.cand, g.cand_p)[0],
            spearmanr(g.comb, g.comb_p)[0], spearmanr(g.cleanx_p, g.comb_p)[0]))
    L += ["", "## Decade medians (percent of content tokens)", "",
          "| source | decade | texts | clean X before | clean X after | cand before | cand after | comb before | comb after |",
          "|---|---|---|---|---|---|---|---|---|"]
    for r in C.sort_values(["source", "decade"]).itertuples():
        L.append("| %s | %d | %d | %.2f | %.2f | %.2f | %.2f | %.2f | %.2f |" % (
            r.source, r.decade, r.n, 100 * r.cleanx, 100 * r.cleanx_p, 100 * r.cand, 100 * r.cand_p, 100 * r.comb, 100 * r.comb_p))
    L += ["", "## Token mass after: share of each list's tokens carried by its most frequent forms (all texts)", ""]
    for k, T in mass.items():
        cum = T.n.cumsum() / T.n.sum()
        L.append("- %s: top 10 %.0f%%, top 25 %.0f%% of %d forms with any tokens. Top 25: %s" % (
            LABEL[k], 100 * cum.iloc[9], 100 * cum.iloc[24], len(T),
            ", ".join("%s %.1f%%" % (w, 100 * n / T.n.sum()) for w, n in zip(T.word.head(25), T.n.head(25)))))
    open(os.path.join(HERE, "ARC_INTERIORITY_PRECISION%s.md" % SUF.upper()), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    a = sys.argv
    if "--count" in a:
        count()
    elif "--report" in a:
        report()
    else:
        print(__doc__)
