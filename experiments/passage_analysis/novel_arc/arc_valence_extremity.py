"""Valence EXTREMITY: each word's distance from neutral valence, token-averaged -- emotional charge whatever its
sign. (RH, 2026-09-25: "could we plot abs val of valence")

    ~/github/abslithists/abstraction/.venv/bin/python -u arc_valence_extremity.py
        -> $DATA/valence_extremity_arc.parquet, valence_extremity_meta_{national,f11}.parquet

Runs in the ABSTRACTION venv so the scorer is theirs, unedited: abstraction.scoring.score_ids_ch over lltk
text_freqs for the arc_fiction reps, and vad_score.py's meta path (tokenize_agnostic on lowercased text, token
mean over tokens with a value) for model meta-texts; book-policy stopwords and names removed from the norms,
exactly as vad_score.norms() does.

WHY NOT abs(text valence). A text's mean valence is already positive nearly everywhere, so its absolute value
changes almost nothing. Extremity has to be taken per WORD, before averaging.

NEUTRAL POINT. VAD-Valence.Warriner.median is z-scored over the vocabulary, so its zero is the vocabulary's
mean, not neutrality. Neutral is placed where Warriner's own scale midpoint (5 on 1-9) falls on the vector
axis: an OLS of the vector value on Warriner valence over the Warriner lemmas in the vocabulary, evaluated at
5. Extremity = |vector valence - that point|. The plain valence column is scored alongside as an identity check
against abstraction's vad_scores_arc_fiction. EXPLORATORY.
"""
import csv, os, sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

ABS = os.path.expanduser("~/github/abslithists/abstraction")
sys.path.insert(0, ABS)
sys.path.insert(0, os.path.join(ABS, "scripts"))
from abstraction.tokenize import get_stopwords_and_names, tokenize_agnostic   # noqa: E402

SH = os.path.expanduser("~/malignment-data/interiority_norms")
DATA = os.path.expanduser("~/malignment-data/novel_arc")
WARRINER = os.path.expanduser("~/Dropbox/Prof/Code/norms_sources/BRM-emot-submit.csv")
V = "VAD-Valence.Warriner.median"
X = "VAD-ValenceExtremity.Warriner.median"
_N = None


def warriner_path():
    sys.path.insert(0, os.path.expanduser("~/github/malignment"))
    from malignment import fields as FD
    return FD.SOURCES["warriner"]


def norms():
    global _N
    if _N is None:
        n = pd.read_parquet(os.path.join(SH, "vad_norms.parquet"), columns=[V])
        n = n[n.index.map(lambda w: isinstance(w, str))]
        n = n[~n.index.duplicated()]
        n = n[~n.index.str.lower().isin(get_stopwords_and_names())].dropna()
        W = {}
        for r in csv.DictReader(open(warriner_path(), encoding="utf-8", errors="replace")):
            try:
                W[r["Word"].lower()] = float(r["V.Mean.Sum"])
            except (KeyError, ValueError, TypeError):
                pass
        common = [w for w in W if w in n.index]
        b, a = np.polyfit([W[w] for w in common], n.loc[common, V].values, 1)
        c = a + 5.0 * b
        print("neutral point: Warriner 5 -> vector %+.4f (fit over %d lemmas, slope %.4f)" % (c, len(common), b), flush=True)
        n[X] = (n[V] - c).abs()
        _N = n
    return _N


def _shard(ids):
    from abstraction.scoring import score_ids_ch
    return score_ids_ch(ids, norms())


def arc(j=6):
    out = os.path.join(DATA, "valence_extremity_arc.parquet")
    if os.path.exists(out):
        return
    import vad_score as VS
    reps = VS.ch_df("SELECT _id FROM abstraction.scores_rep WHERE arc_corpus = 'arc_fiction'")
    ids = list(reps._id)
    assert len(ids) == 82080
    norms()
    shards = [ids[i:i + 2000] for i in range(0, len(ids), 2000)]
    with ProcessPoolExecutor(j) as ex:
        parts = []
        for i, df in enumerate(ex.map(_shard, shards), 1):
            parts.append(df)
            print("  shard %d/%d" % (i, len(shards)), flush=True)
    S = pd.concat(parts, ignore_index=True)
    ref = pd.read_parquet(os.path.join(SH, "vad_scores_arc_fiction.parquet"))[["_id", V]].rename(columns={V: "ref"})
    d = S.merge(ref, on="_id").dropna(subset=[V, "ref"])
    print("identity check, valence vs abstraction's arc scores: max|diff| %.2e (n %d)" % ((d[V] - d.ref).abs().max(), len(d)))
    assert (d[V] - d.ref).abs().max() < 1e-4
    S.to_parquet(out, index=False)


def meta(src, name):
    out = os.path.join(DATA, "valence_extremity_meta_%s.parquet" % name)
    if os.path.exists(out):
        return
    T = pd.read_parquet(src)
    N = norms()
    d = {c: N[c].dropna().to_dict() for c in (V, X)}
    rows = []
    for _id, text in zip(T.id, T.text):
        toks = tokenize_agnostic(text.lower())
        r = {"id": _id}
        for c in (V, X):
            v = [d[c][t] for t in toks if t in d[c]]
            r[c] = float(np.mean(v)) if v else np.nan
        rows.append(r)
    S = T.drop(columns=["text"]).merge(pd.DataFrame(rows), on="id")
    S.to_parquet(out, index=False)
    print("-> %s (%d)" % (out, len(S)))


if __name__ == "__main__":
    meta(os.path.join(DATA, "prompt_check_national_judged_meta.parquet"), "national")
    meta(os.path.join(SH, "fig5_meta_texts_arms4.parquet"), "f11")
    arc()
