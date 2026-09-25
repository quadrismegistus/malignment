"""Example passages for transgressiveness, arousal and valence, historical and model. (RH, 2026-09-25)

    .venv/bin/python -u arc_norm_examples.py   -> $DATA/arc_norm_examples_scored.parquet, ARC_NORM_EXAMPLES.md

HISTORICAL passages: lltk.passages (scheme p500, ~500 words) of the arc_fiction reps, 1600-2009, a
deterministic sample of up to 2,500 per half-century (ORDER BY cityHash64(_id, seq)). MODEL passages:
the 30-lineage TEMPLATE_ARM population (arc_history_arms v4 sel12: coherent narrative, base and aligned).
Both scored exactly as arc_type_norms.py scores texts: lowercased [a-z]+ tokens, expanded stopwords out,
each form mapped to a lexicon entry (the committed form map, then the same mapper for unseen forms),
token-weighted mean rating. Admitted: historical passages with >= 150 content tokens, model passages with
>= 60, and lexicon coverage >= 60% of content tokens (so OCR wreckage and name lists do not top a scale).

For each scale: the two highest and two lowest historical passages, and the two highest and two lowest
model passages of each arm, each shown as the ~70-word window whose rated words sit furthest from the
scale's mean in the passage's direction, with the rated words that drive it. Extremes illustrate what a
scale registers; they are not typical passages. EXPLORATORY.
"""
import io, os, re, sys, textwrap

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.argv = [sys.argv[0], "v4", "meta", "sel12"]
import arc_interiority as A                             # noqa: E402
import arc_history_arms as H                            # noqa: E402
import arc_type_norms as N                              # noqa: E402

OUT = os.path.join(A.DATA, "arc_norm_examples_scored.parquet")
SCALES = {"k_transgressiveness": "k", "warriner_arousal": "warriner", "warriner_valence": "warriner"}
PER_BIN, WIN = 2500, 70


def passages():
    sql = f"""SELECT p._id AS _id, p.seq AS seq, p.text AS text, t.year AS year, t.title AS title, t.author AS author
      FROM lltk.passages p INNER JOIN (SELECT _id, year, title, author FROM lltk.texts FINAL WHERE _id IN ({A.REPS})) t ON p._id = t._id
      WHERE p._id IN ({A.REPS}) AND p.lang = 'en' AND t.year BETWEEN 1600 AND 2009
      ORDER BY intDiv(t.year, 50), cityHash64(p._id, p.seq) LIMIT {PER_BIN} BY intDiv(t.year, 50)
      FORMAT TSVWithNames"""
    P = pd.read_csv(io.StringIO(A.ch_query(sql, {})), sep="\t", keep_default_na=False, quoting=3)
    #: TSV escapes newlines, tabs, quotes and backslashes; left in, "\nhim" tokenises as "nhim"
    unesc = lambda t: re.sub(r"\\(.)", lambda m: {"n": "\n", "t": "\t", "r": ""}.get(m.group(1), m.group(1)), t)
    for c in ("text", "title", "author"):
        P[c] = P[c].map(unesc)
    #: some stored texts carry a literal backslash-n from their source files, under the TSV layer
    n_lit = int(P.text.str.contains("\\n", regex=False).sum())
    print("passages with a stored literal backslash-n: %d" % n_lit, flush=True)
    P["text"] = P.text.str.replace("\\n", "\n", regex=False)
    assert not P.text.str.contains("\\n", regex=False).any(), "a literal backslash-n survived unescaping"
    return P


def scorer():
    L = N.lexicons()
    Mf = pd.read_parquet(N.MAP)
    fmap = {src: dict(zip(g.form, g.entry)) for src, g in Mf.groupby("source")}
    cores = {src: N.mapper(L[src]) for src in L}
    _, sw, _ = A.lists_expanded()
    cache = {}
    def entry(src, w):
        k = (src, w)
        if k not in cache:
            cache[k] = fmap[src].get(w) or cores[src](w)[0]
        return cache[k]
    def score(txt):
        toks = [w for w in re.findall(r"[a-z]+", (txt or "").lower()) if w not in sw]
        out = {"n_content": len(toks)}
        for s, src in SCALES.items():
            vals = [L[src][e][s] if (e := entry(src, w)) else np.nan for w in toks]
            v = np.array(vals, dtype=float)
            ok = ~np.isnan(v)
            out[s] = float(v[ok].mean()) if ok.any() else np.nan
            out["cov_" + s] = float(ok.mean()) if len(v) else 0.0
        return out
    def rated(txt, s):
        src = SCALES[s]
        words = re.findall(r"[A-Za-z]+|[^A-Za-z]+", txt or "")
        return [(w, (L[src][e][s] if (w.lower() not in sw and (e := entry(src, w.lower()))) else None)) for w in words]
    return score, rated


def window(rated_words, mean, sign):
    """The ~WIN-word window whose rated words deviate most from `mean` in direction `sign`."""
    idx = [i for i, (w, v) in enumerate(rated_words) if re.match(r"[A-Za-z]", w)]
    if len(idx) <= WIN:
        lo, hi = 0, len(rated_words)
    else:
        dev = np.array([sign * (rated_words[i][1] - mean) if rated_words[i][1] is not None else 0.0 for i in idx])
        cs = np.concatenate([[0], np.cumsum(dev)])
        j = int(np.argmax(cs[WIN:] - cs[:-WIN]))
        lo, hi = idx[j], idx[j + WIN - 1] + 1
    seg = "".join(w for w, _ in rated_words[lo:hi])
    drivers = sorted({(w.lower(), v) for w, v in rated_words[lo:hi] if v is not None and sign * (v - mean) > 0},
                     key=lambda x: -sign * (x[1] - mean))[:8]
    return re.sub(r"\s+", " ", seg).strip(), drivers


def main():
    score, rated = scorer()
    if os.path.exists(OUT):
        D = pd.read_parquet(OUT)
    else:
        Ph = passages()
        print("historical passages sampled:", len(Ph), flush=True)
        Ph = pd.concat([Ph.reset_index(drop=True), pd.DataFrame([score(t) for t in Ph.text])], axis=1).assign(kind="history")
        P = pd.read_parquet(H.ARM_OUT)
        S_ = pd.concat([pd.read_parquet(os.path.join(H.TA, "selection.parquet")),
                        pd.read_parquet(os.path.join(H.TA, "selection_2.parquet"))]).set_index("id")
        Pm = P[["id", "model", "arm"]].assign(text=[S_.loc[i, "text"] for i in P.id])
        Pm = pd.concat([Pm.reset_index(drop=True), pd.DataFrame([score(t) for t in Pm.text])], axis=1).assign(kind="model")
        D = pd.concat([Ph, Pm], ignore_index=True)
        D.to_parquet(OUT, index=False)
    L = ["# Example passages: transgressiveness, arousal, valence (EXPLORATORY)", "",
         "Producer `arc_norm_examples.py` (method in its docstring). Scores are token-weighted mean ratings of a "
         "passage's mapped content words (k: 1-7, Warriner: 1-9). Each excerpt is the ~%d-word window that drives the "
         "passage's score; `drivers` are its rated words furthest from the mean in that direction. Extremes, not "
         "typical passages." % WIN, ""]
    for s in SCALES:
        mean = float(D[D.kind == "history"][s].mean())
        L += ["## %s" % s, "", "Historical passage mean %.3f; model passage means: base %.3f, aligned %.3f." % (
            mean, D[(D.kind == "model") & (D.arm == "base")][s].mean(), D[(D.kind == "model") & (D.arm == "raw")][s].mean()), ""]
        hist = D[(D.kind == "history") & (D.n_content >= 150) & (D["cov_" + s] >= 0.6)].dropna(subset=[s])
        mod = D[(D.kind == "model") & (D.n_content >= 60) & (D["cov_" + s] >= 0.6)].dropna(subset=[s])
        blocks = [("Historical, highest", hist.nlargest(2, s), 1), ("Historical, lowest", hist.nsmallest(2, s), -1)]
        for arm, lab in (("base", "Base models"), ("raw", "Aligned models")):
            m = mod[mod.arm == arm]
            blocks += [("%s, highest" % lab, m.nlargest(2, s), 1), ("%s, lowest" % lab, m.nsmallest(2, s), -1)]
        for head, rows, sign in blocks:
            L += ["### %s" % head, ""]
            for r in rows.itertuples():
                seg, drv = window(rated(r.text, s), mean, sign)
                src = ("%s, *%s* (%d)" % (r.author or "anon.", (r.title or "")[:70], r.year)) if r.kind == "history" else r.model
                L += ["- **%.3f** -- %s" % (getattr(r, s), src), "", "  > %s" % seg, "",
                      "  drivers: " + ", ".join("%s %.2f" % (w, v) for w, v in drv), ""]
    open(os.path.join(HERE, "ARC_NORM_EXAMPLES.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L)[:6000])


if __name__ == "__main__":
    main()
