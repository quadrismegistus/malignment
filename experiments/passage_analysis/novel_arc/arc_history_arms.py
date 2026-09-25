"""Concreteness, cognitive and emotional language over arc_fiction, with TEMPLATE_ARM model arms. (RH, 2026-09-25)

    .venv/bin/python -u arc_history_arms.py --no-arms   -> figures/arc_history_three_preview.{png,pdf,caption.txt}
    .venv/bin/python -u arc_history_arms.py --write-lists  -> $MALIGNMENT_DATA/novel_arc/arc_vetted_lists_expanded.json
    ~/github/lltk/.venv/bin/python -u arc_history_arms.py --arms   (measure_lltk needs lltk)
                                                        -> $MALIGNMENT_DATA/novel_arc/arc_history_arm_passages.parquet
                                                          figures/arc_history_three_arms.{png,pdf,caption.txt}
    add v2 to any of these (and run --count v2 after --write-lists v2): the lists PARTITIONED BY RATED KIND
    across the X and E work, not by the list a word came from (RH, 2026-09-25: emotion words carry the trend;
    E through the X procedure). Outputs suffixed _v2.

V2 LISTS. Base words: X's vetted keeps (precision_keep_v2_vetted.csv, keep_vetted) and E's
(precision_e_keep_v2_vetted.csv, keep_vetted), disjoint by construction (E never re-rated an X-rated form).
COGNITIVE = rated kind cognition, attention or perception; EMOTIONAL = emotion. VOLITION (want-less:
wish, hope, desire, intend...) sits in neither until RH places it; speech and other in neither. RH's
interiority removals (happy, fear, love, loved...) stand: they are X keep_vetted False. Variants: a
MorphAdorner variant the rater kept enters a list when a word it spells is on that list, less common
modern words (zipf >= 3); long-s readings of every form (zipf < 2); the expanded stopwords out --
arc_interiority_precision.py's rules, unchanged.

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
#: v3 (RH, 2026-09-25): v2 with fear, happy and loved restored to the emotion list ("I only removed love
#: because it can sign letters, you can call someone love"; love stays out) and volition added to cognitive
#: v4 (RH, 2026-09-25): v3 without loved -- a common adjective and epithet ("loved ones"), and on its own it
#: moved the base arm most of the way from v2 to v3
V4 = "v4" in sys.argv[1:]
V3 = "v3" in sys.argv[1:] or V4
V2 = "v2" in sys.argv[1:] or V3
#: past (RH, 2026-09-25): v4 restricted to PAST verb forms, to test whether the post-1800 shift in cognitive
#: vocabulary is narrated mental acts (she realized, he wondered). See is_past(): regular -ed forms WordNet
#: lemmatises to another verb, and WordNet's irregular verb forms; past tense and past participle cannot be
#: told apart for regular verbs, so both count, and irregular participles (known, forgotten) count too.
PAST = "past" in sys.argv[1:]
assert not PAST or V4, "past is a v4 option"
VER = ("v4_past" if PAST else "v4") if V4 else "v3" if V3 else "v2"
SUF = "_" + VER if V2 else ""
RESTORE = ({"fear", "happy"} if V4 else {"fear", "happy", "loved"}) if V3 else set()
COUNTS = os.path.join(DATA, "arc_cogemo_texts_%s.parquet" % VER if V2 else "arc_interiority_texts_precision_vetted.parquet")
COG_COL, EMO_COL = ("n_cog", "n_emo") if V2 else ("n_cleanx_p", "n_cand_p")
COG_KINDS, EMO_KINDS = {"cognition", "attention", "perception"} | ({"volition"} if V3 else set()), {"emotion"}
CONC = os.path.join(DATA, "arc_concreteness_texts.parquet")
ARM_OUT = os.path.join(DATA, "arc_history_arm_passages%s.parquet" % SUF)
LISTS = os.path.join(DATA, "arc_cogemo_lists_%s.json" % VER if V2 else "arc_vetted_lists_expanded.json")
BIAS = "/Volumes/diderot/DH/data/data_abslithist/scores/corpus_bias_coefficients.json"
MIN_CONTENT, MIN_DECADE, MIN_ARM = 2000, 3, 10
#: RH dropped RWKV (TEMPLATE_ARM.md amendment 3, malignment 4bd3f90b: its bf16 output is 88-90% repeated-word
#: loops). Its raw cells are coded and in selection.parquet, so the exclusion is stated, not left to the floor.
DROPPED = {"RWKV/rwkv-4-7b-pile"}
ARMS_ON = "--arms" in sys.argv
OUT = os.path.join(HERE, "figures", "arc_history_three_" + ("arms" if ARMS_ON else "preview") + SUF)
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
            "cog": (decades(T.year, T[COG_COL] / T.n_content), len(T)),
            "emo": (decades(T.year, T[EMO_COL] / T.n_content), len(T))}


def arm_passages():
    """-> per narrative passage of the registered primary: model, base, arm, conc, cog, emo.
    selection.text, not passages.parquet's: continue replies there have a leading assistant preamble
    stripped (malign; flag `stripped`). Only selection.parquet's 161 cells; the leftovers (internlm2-chat
    continue, rwkv-raven prefill/continue) arrive as selection_2.parquet, and until then those two lineages
    drop out under the all-four-arms rule."""
    if os.path.exists(ARM_OUT):
        return pd.read_parquet(ARM_OUT)
    from measure_lltk import Scorer
    S_ = pd.read_parquet(os.path.join(TA, "selection.parquet"))
    Cd = pd.read_parquet(os.path.join(TA, "codings.parquet"))
    #: malign asked for the COMPLETE coding; a half-coded cell would enter as a thin cell, not an error
    assert S_.id.isin(Cd.id).all(), "coding incomplete: %d of %d selected passages uncoded" % (
        (~S_.id.isin(Cd.id)).sum(), len(S_))
    P = S_.merge(Cd[["id", "narrative"]], on="id", how="inner", validate="1:1")
    #: the key is checked against the SELECTION: all 400 RWKV passages are coded non-narrative, so after the
    #: narrative filter there is nothing left to exclude and the exclusion would be untestable
    assert DROPPED <= set(P.base), ("a dropped lineage is not in the selection; check its key", DROPPED - set(P.base))
    P = P[~P.base.isin(DROPPED)]
    P = P[(P.narrative == True) & (P.n_words >= 40)]                    # noqa: E712
    n = P.groupby(["base", "arm"]).size().unstack(fill_value=0)
    keep = n.index[(n.reindex(columns=["base", "raw", "prefill", "continue"], fill_value=0) >= MIN_ARM).all(axis=1)]
    P = P[P.base.isin(keep) & P.arm.isin(["base", "raw"])]
    #: the expanded lists come from write_lists() (wordfreq lives in the malignment venv, lltk in its own)
    Lj = json.load(open(LISTS))
    cog, emo, sw = set(Lj["cog"]), set(Lj["emo"]), set(Lj["stopwords"])
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


def arm_values(D, col, pooled=False):
    """Per model the median over passages (Figure 5), or with pooled=True the model's POOLED rate -- its list
    tokens over its content tokens across all its passages, the analogue of a whole-text share -- then the
    median over lineages. Pooled is used where a list is too sparse for a passage median: past-form emotion
    words are absent from most ~100-word passages, and every model's median is 0."""
    if pooled:
        d = D.dropna(subset=[col]).assign(hits=lambda x: x[col] * x.n_content)
        g = d.groupby(["base", "arm"])
        per = (g.hits.sum() / g.n_content.sum()).unstack()
    else:
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
            arms[k], nl = arm_values(D, k, pooled=PAST and k != "conc")
            if k != "conc":
                print("  %s arms: median-of-passages %s, pooled %s" % (k, {a: round(100 * v, 3) for a, v in arm_values(D, k)[0].items()},
                                                                      {a: round(100 * v, 3) for a, v in arm_values(D, k, True)[0].items()}))
        info = (" Arms: TEMPLATE_ARM (41 lineages, one vLLM engine, Figure 5's 100 English stems), %d lineages with at "
                "least %d coherent narrative passages in all four arms (coder claude-opus-5, stricter about coherence "
                "than Figure 5's); base %s and aligned (no template) %s passages." % (
            nl, MIN_ARM, format(int((D.arm == "base").sum()), ","), format(int((D.arm == "raw").sum()), ",")))
    spec = (("conc", "Concreteness in fiction", "Concreteness\n(word norm mean)", False),
            ("cog", "Cognitive verbs in fiction, past forms" if PAST else "Cognitive language in fiction",
             "Cognitive words\n(share of words)", True),
            ("emo", "Emotional verbs in fiction, past forms" if PAST else "Emotional language in fiction",
             "Emotional words\n(share of words)", True))
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
        "%s such tokens (%s texts). " % (MIN_DECADE, format(H["conc"][1], ","), format(MIN_CONTENT, ","), format(H["cog"][1], ",")) + (
        V2_CAPTION() if V2 else
        "Cognitive: the USAS X words an LLM rater kept under a precision-first rule, "
        "hand-vetted (872 base words; 68% cognition by token mass). Emotional: period-model neighbours of X rated "
        "and vetted the same way (1,077 base words; 67% emotion).") + (
        info + (" Model arms for the two word-list panels: per model the POOLED rate over its coherent narrative "
                "passages (list tokens over content tokens; past forms are too sparse for a passage median, which is 0 "
                "for every model's emotional forms), then the median over lineages; concreteness as below." if PAST else "") +
        " Model arms: per model the median over its coherent narrative passages, then the median over lineages; "
        "passage values, not text values, so medians compare and spreads do not. Model concreteness is not "
        "bias-corrected (clean digital text)." if ARMS_ON else ""))
    L += ["", "  arms: " + json.dumps({k: {a: round(v, 4) for a, v in d.items()} for k, d in arms.items()})] if ARMS_ON else []
    open(OUT + ".caption.txt", "w").write("\n".join(L) + "\n")
    print("\n".join(L))
    for k, (h, n) in H.items():
        print(k, "decades %d, texts %d, range %.4f..%.4f" % (len(h), n, h.value.min(), h.value.max()))


def V2_CAPTION():
    info = json.load(open(LISTS))["info"]
    return ("Word lists from USAS X (cognition) and USAS E (emotion), each with its period-model neighbours, rated "
            "by an LLM under a precision-first rule (keep a word only if every common sense is mental) and hand-vetted; "
            "split by the rated kind of each word, not by field. " + (
            ("Cognitive: cognition, attention, perception and volition words (%s base words). Emotional: emotion words "
             "(%s), with %s restored after an interiority vetting removed them." + (
                 " PAST FORMS ONLY: past-tense and past-participle verb forms by WordNet (regular -ed forms and irregular "
                 "inflections; the two cannot be separated for regular verbs), with their old spellings; many of the "
                 "emotional ones are participial adjectives (pleased, surprised, frightened)." if PAST else "")) % (
                format(info["cog_base"], ","), format(info["emo_base"], ","),
                "fear and happy" if V4 else "fear, happy and loved") if V3 else
            "Cognitive: cognition, attention and perception words "
            "(%s base words). Emotional: emotion words (%s). Volition words (%s) are in neither panel."
            % (format(info["cog_base"], ","), format(info["emo_base"], ","), format(info["volition_base"], ","))))


def is_past(w):
    """A past verb form by WordNet: an irregular inflection in its verb exception list, or an -ed form it
    lemmatises to a different verb. -ing and -s forms are never past."""
    from nltk.corpus import wordnet as wn
    wn.ensure_loaded()
    if w.endswith("ing") or (w.endswith("s") and not w.endswith("ss")):
        return False
    ex = wn._exception_map["v"].get(w)
    if ex and ex[0] != w:
        return True
    if w.endswith("ed"):
        m = wn.morphy(w, "v")
        return m is not None and m != w
    return False


def v2_lists():
    """-> {cog, emo, stopwords, info}: the kind partition, expanded by arc_interiority_precision's rules."""
    from wordfreq import zipf_frequency
    import arc_interiority as A
    SH = os.path.expanduser("~/malignment-data/interiority_norms")
    X = pd.read_csv(os.path.join(SH, "precision_keep_v2_vetted.csv"))
    E = pd.read_csv(os.path.join(SH, "precision_e_keep_v2_vetted.csv"))
    assert (len(X), len(E)) == (15099, 17635), (len(X), len(E))
    assert not set(X.form) & set(E.form), "an E form was re-rated"
    B = pd.concat([X[X.spelling_of.isna() & X.keep_vetted][["form", "kind"]],
                   E[E.spelling_of.isna() & E.keep_vetted][["form", "kind"]]])
    base = {"cog": set(B.form[B.kind.isin(COG_KINDS)]), "emo": set(B.form[B.kind.isin(EMO_KINDS)])}
    #: dreaded and regretted are E seeds AND the keep-anchors, so neither consensus file carries them (items
    #: excluded anchors; the anchor rows are dropped). Rated keep, kind emotion, in every calibrated batch.
    anchors = {"dreaded", "regretted"}
    assert not anchors & (set(X.form) | set(E.form))
    base["emo"] |= anchors
    #: v3 restorations: RH's interiority removals that the rater kept as emotion
    Xi = X.set_index("form")
    for w in RESTORE:
        assert Xi.loc[w, "keep_llm"] and Xi.loc[w, "rh_removed"] and Xi.loc[w, "kind"] == "emotion", w
    base["emo"] |= RESTORE
    if PAST:
        n0 = {k: len(v) for k, v in base.items()}
        base = {k: {w for w in v if is_past(w)} for k, v in base.items()}
        #: booked on 2026-09-25: 187 of 1,411 cognitive and 173 of 1,121 emotional base words are past forms
        assert {k: len(v) for k, v in base.items()} == {"cog": 187, "emo": 173}, ({k: len(v) for k, v in base.items()}, n0)
    V = pd.concat([X[X.spelling_of.notna() & X.keep], E[E.spelling_of.notna() & E.keep]])
    _, sw, _ = A.lists_expanded()
    out, info = {}, {"cog_base": len(base["cog"]), "emo_base": len(base["emo"]), "emo_anchor_seeds_added": sorted(anchors),
                     "volition_base": int((B.kind == "volition").sum()), "other_base": int((~B.kind.isin(COG_KINDS | EMO_KINDS | {"volition"})).sum())}
    for k in ("cog", "emo"):
        mv = {r.form for r in V.itertuples() if set(r.spelling_of.split(", ")) & base[k]}
        modern = {v for v in mv if zipf_frequency(v, "en") >= 3.0}
        forms = base[k] | (mv - modern)
        ls = set()
        for w in forms:
            ls |= A.long_s(w, zipf_frequency)
        forms = {w for w in forms | ls if w.isalpha()} - sw
        out[k] = sorted(forms)
        info.update({k + "_variants": len(mv - modern), k + "_dropped_modern": sorted(modern), k + "_expanded": len(forms)})
    #: a long-s reading can arise from a word on each list (penfive: pensive, cognition, and a sibling on the
    #: emotion side); a form either list could claim goes in neither, and is counted
    both = set(out["cog"]) & set(out["emo"])
    assert len(both) <= 5, sorted(both)
    out = {k: sorted(set(v) - both) for k, v in out.items()}
    info["in_both_dropped"] = sorted(both)
    return {"cog": out["cog"], "emo": out["emo"], "stopwords": sorted(sw), "info": info}


def count_v2():
    """Per text over arc_fiction: n_cog, n_emo under the v2 lists, joined to arc_interiority's denominator."""
    import io
    import arc_interiority as A
    assert not os.path.exists(COUNTS), "refusing to overwrite " + COUNTS
    Lj = json.load(open(LISTS))
    lw = [(w, "cog") for w in Lj["cog"]] + [(w, "emo") for w in Lj["emo"]]
    sql = f"""
      SELECT _id,
        sumIf(v, k IN (SELECT word FROM lw WHERE list = 'cog')) AS n_cog,
        sumIf(v, k IN (SELECT word FROM lw WHERE list = 'emo')) AS n_emo
      FROM (SELECT _id, freqs FROM lltk.text_freqs FINAL WHERE _id IN ({A.REPS}))
      ARRAY JOIN mapKeys(freqs) AS k, mapValues(freqs) AS v
      GROUP BY _id
      FORMAT TSVWithNames"""
    N = pd.read_csv(io.StringIO(A.ch_query(sql, {"lw": ("word String, list String", lw)})), sep="\t")
    assert len(N) == 82080, len(N)
    D = pd.read_parquet(A.OUT).rename(columns={"r._id": "_id"})[["_id", "year", "corpus", "source", "n_content"]]
    D = D.merge(N, on="_id", how="inner", validate="1:1")
    assert len(D) == 82080 and (D.n_cog + D.n_emo <= D.n_content).all()
    D.to_parquet(COUNTS, index=False)
    print("-> %s" % COUNTS)


def write_lists():
    """The expanded vetted lists exactly as the history counted them, for the arms' passage count."""
    assert not os.path.exists(LISTS), "refusing to overwrite " + LISTS
    if V2:
        Lj = v2_lists()
        json.dump(Lj, open(LISTS, "w"))
        print(json.dumps(Lj["info"], indent=1)[:1500])
        print("-> %s" % LISTS)
        return
    sys.argv = [sys.argv[0], "--vetted"]             # the list module reads its mode at import
    import arc_interiority_precision as AP
    assert AP.VETTED
    ex, sw, info = AP.lists_precision()
    assert (len(ex["cleanx_p"]), len(ex["cand_p"])) == (4216, 6117), (len(ex["cleanx_p"]), len(ex["cand_p"]))  # ARC_INTERIORITY_PRECISION_VETTED.md
    json.dump({"cog": sorted(ex["cleanx_p"]), "emo": sorted(ex["cand_p"]), "stopwords": sorted(sw)}, open(LISTS, "w"))
    print("-> %s" % LISTS)


if __name__ == "__main__":
    if "--write-lists" in sys.argv:
        write_lists()
    elif "--count" in sys.argv:
        count_v2()
    else:
        main()
