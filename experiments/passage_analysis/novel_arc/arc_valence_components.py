"""The valence decomposition drawn as history with model arms: share of positive words, share of negative words, and
each bin's intensity. (RH, 2026-09-26: "plot the decomposition (pos and neg) as we plot others, history + ref lines")

    ~/github/abslithists/abstraction/.venv/bin/python -u arc_valence_components.py --score
        -> $DATA/valence_components_arc_cc.parquet, valence_components_meta_national.parquet
    .venv/bin/python -u arc_valence_components.py --plot   -> figures/arc_valence_components_cc_v1.{png,pdf,caption.txt}

The components of arc_valence_decomp.py, per text: with neutral n and half-band h (human Warriner lookup: n = 5,
h = 1; plain vector valence: where Warriner 5 and a 1-point band fall on the axis),
    positive share    p  = share of scored tokens with v > n + h
    negative share    q  = share with v < n - h
    positive intensity D+ = mean (v - n) over positive tokens
    negative intensity D- = mean (n - v) over negative tokens
Scored with abstraction's own scorer (score_ids_ch over lltk.text_freqs for texts; tokenize_agnostic token mean for
model meta-texts), passing indicator and distance columns: a column's mean over the tokens that carry a value is
exactly p, q, D+ or D- (distance columns are NaN outside their bin). Book-policy stopwords and names removed; HTML
entity tokens removed (bpo's unescaped entities, abstraction's finding).
HISTORY: arc_fiction reps from Chadwyck and Chicago only (Figure 5's corpora), 1600-2009, decade medians (>= 3
texts), lowess 0.3; not bias-corrected. ARMS: the judged no-demonym national stories, one meta-text per
model-condition, median over lineages. EXPLORATORY.
"""
import os, sys, textwrap

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.expanduser("~/malignment-data/novel_arc")
ARC = os.path.join(DATA, "valence_components_arc_cc.parquet")
META = os.path.join(DATA, "valence_components_meta_national.parquet")
OUT = os.path.join(HERE, "figures", "arc_valence_components_cc_v1")
ENTITIES = {"apos", "quot", "amp", "lt", "gt", "nbsp", "mdash", "ndash", "hellip", "rsquo", "lsquo", "rdquo", "ldquo"}
COMPS = [("pos_share", "Positive share"), ("neg_share", "Negative share"), ("pos_int", "Positive intensity"), ("neg_int", "Negative intensity")]


def table():
    sys.path.insert(0, HERE)
    import arc_valence_decomp as VD
    V = VD.versions()
    cols = {}
    for name, (tab, n0, h) in V.items():
        key = "lookup" if name.startswith("human") else "plain"
        s = pd.Series(tab)
        s = s[~s.index.isin(ENTITIES)]
        d = s - n0
        pos, neg = d > h, d < -h
        cols["%s.pos_share" % key] = pos.astype(float)
        cols["%s.neg_share" % key] = neg.astype(float)
        cols["%s.pos_int" % key] = d.where(pos)
        cols["%s.neg_int" % key] = (-d).where(neg)
    return pd.DataFrame(cols)


_T = None


def get_T():
    """built lazily, once per process: spawned workers do not inherit the parent's globals"""
    global _T
    if _T is None:
        _T = table()
    return _T


def _shard(ids):
    sys.path.insert(0, os.path.expanduser("~/github/abslithists/abstraction"))
    from abstraction.scoring import score_ids_ch
    return score_ids_ch(ids, get_T())


def score(j=6):
    sys.path.insert(0, os.path.expanduser("~/github/abslithists/abstraction"))
    sys.path.insert(0, os.path.join(os.path.expanduser("~/github/abslithists/abstraction"), "scripts"))
    from concurrent.futures import ProcessPoolExecutor
    from abstraction.tokenize import tokenize_agnostic
    import vad_score as VS
    T_ = get_T()
    if not os.path.exists(META):
        M = pd.read_parquet(os.path.join(DATA, "prompt_check_national_judged_meta.parquet"))
        d = {c: T_[c].dropna().to_dict() for c in T_.columns}
        rows = []
        for _id, text in zip(M.id, M.text):
            toks = tokenize_agnostic(text.lower())
            r = {"id": _id}
            for c in T_.columns:
                v = [d[c][t] for t in toks if t in d[c]]
                r[c] = float(np.mean(v)) if v else np.nan
            rows.append(r)
        M.drop(columns=["text"]).merge(pd.DataFrame(rows), on="id").to_parquet(META, index=False)
        print("-> %s" % META, flush=True)
    if not os.path.exists(ARC):
        ids = list(VS.ch_df("SELECT r._id AS _id FROM abstraction.scores_rep r WHERE r.arc_corpus = 'arc_fiction' AND r._id IN "
                            "(SELECT _id FROM lltk.texts FINAL WHERE corpus IN ('chadwyck', 'chicago'))")._id)
        print("Chadwyck + Chicago reps: %d" % len(ids), flush=True)
        shards = [ids[i:i + 1000] for i in range(0, len(ids), 1000)]
        with ProcessPoolExecutor(j) as ex:
            S = pd.concat(list(ex.map(_shard, shards)), ignore_index=True)
        S.to_parquet(ARC, index=False)
        print("-> %s (%d)" % (ARC, len(S)))


def plot():
    sys.argv = [sys.argv[0], "v4", "meta", "sel12", "arms4"]
    sys.path.insert(0, HERE)
    import arc_history_arms as H
    from malignment import figure as F
    from statsmodels.nonparametric.smoothers_lowess import lowess
    for ext in (".png", ".pdf", ".caption.txt"):
        assert not os.path.exists(OUT + ext), "refusing to overwrite " + OUT + ext
    T = H.concreteness_texts()[["_id", "year", "corpus"]].merge(pd.read_parquet(ARC), on="_id", validate="1:1")
    T = T[T.corpus.isin(["chadwyck", "chicago"]) & T.year.between(1600, 2009)]
    M = pd.read_parquet(META)
    arms_lab = {"base": "Base models", "aligned_raw": "Aligned models", "aligned_prefill": "Aligned, chat, prefilled",
                "aligned_rettberg": "Aligned, chat, asked"}
    pts, cvs, arms, order = [], [], [], []
    for comp, clab in COMPS:
        for key, klab in (("lookup", "human lookup"), ("plain", "plain vector")):
            c = "%s.%s" % (key, comp)
            name = "%s: %s" % (clab, klab)
            order.append(name)
            d = T[["year", c]].dropna()
            h = H.decades(d.year, d[c])
            pts += [dict(panel=name, year=y, value=v) for y, v in zip(h.year, h.value)]
            cvs += [dict(panel=name, year=x, value=y) for x, y in lowess(h.value.values, h.year.values, frac=0.3, return_sorted=True)]
            arms += [dict(panel=name, arm=arms_lab[k], value=float(M[M.cond == k][c].median())) for k in arms_lab]
    P, C, A = pd.DataFrame(pts), pd.DataFrame(cvs), pd.DataFrame(arms)
    for df in (P, C, A):
        df["panel"] = pd.Categorical(df.panel, categories=order)
    A["arm"] = pd.Categorical(A.arm, categories=list(arms_lab.values()))
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["pdf.fonttype"] = 42
    from plotnine import (ggplot, aes, geom_point, geom_line, geom_hline, facet_wrap, labs, scale_linetype_manual,
                          scale_x_continuous, theme, element_text)
    p = (ggplot()
         + geom_point(aes("year", "value"), data=P, color=F.PUB_GRAY, size=0.6)
         + geom_line(aes("year", "value"), data=C, color=F.PUB_INK, size=F.PUB_LINE_PT)
         + geom_hline(aes(yintercept="value", linetype="arm"), data=A, color=F.PUB_MID, size=F.PUB_RULE_PT * 1.2)
         + scale_linetype_manual(dict(zip(arms_lab.values(), ["dotted", "dashed", "dashdot", "solid"])))
         + facet_wrap("~panel", ncol=2, scales="free_y")
         + scale_x_continuous(breaks=[1600, 1700, 1800, 1900, 2000])
         + labs(x="", y="Share of scored words / mean distance from neutral", linetype="")
         + F.pub_theme(height=8.0)
         + theme(legend_position="bottom", figure_size=(7.5, 8.0), strip_text=element_text(family=F.pub_font(), size=F.PUB_FONT_PT)))
    F.save(p, OUT + ".png")
    cap = textwrap.wrap("VALENCE DECOMPOSED, 1600-2000: the share of positive and of negative words among a text's valence-"
                        "rated words, and each bin's mean distance from neutral (human Warriner lookup, neutral 5, band 4-6; "
                        "plain vector valence, the same band mapped onto the axis). Gray points: decade medians over %s "
                        "Chadwyck and Chicago arc_fiction texts; black line: lowess (span 0.3); HTML entity tokens and "
                        "book-policy stopwords and names removed; not bias-corrected. Lines: national-story arms (judged "
                        "no-demonym stories), median over lineages." % format(len(T), ","), 100)
    open(OUT + ".caption.txt", "w").write("\n".join(cap) + "\n")
    print("\n".join(cap))
    for name in order:
        a = A[A.panel == name].set_index("arm").value
        h = P[P.panel == name]
        print("  %-38s history %.3f..%.3f | %s" % (name, h.value.min(), h.value.max(), " ".join("%s %.3f" % (k.split()[0] if k != "Aligned, chat, asked" else "asked", v) for k, v in a.items())))


if __name__ == "__main__":
    if "--score" in sys.argv:
        score()
    elif "--plot" in sys.argv:
        plot()
    else:
        print(__doc__)
