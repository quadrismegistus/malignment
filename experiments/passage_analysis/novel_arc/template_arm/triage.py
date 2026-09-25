"""passC's narrative triage classifier, recovered verbatim, as a committed producer.

    python triage.py --check      # retrain, re-score triage.parquet's rows, compare
    python triage.py --score IN.parquet OUT.parquet

PROVENANCE. `interiority_in_passages/results/passC/triage.parquet` (18 Aug 2026) ranked
the passages Figure 5 codes, and its producer was never committed: the lacan seat ran it
inline (transcript agents-lacan/cdbe9c9e..., 2026-08-18T17:00:47Z, "Train the triage
classifier and score the corpus"). The feature code, model and training set below are
copied from that call unchanged: logistic regression (C=0.5, balanced) on char_wb 2-4
TF-IDF (5,000 features, min_df 3, sublinear) plus 23 surface features, trained on the
passC sample passages where coders A and B agreed on `narrative`. Recovered 2026-09-25
so the template arm is ranked by the SAME instrument, not a lookalike.
"""
import argparse, collections, glob, json, os, re, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PASSC = os.path.abspath(os.path.join(HERE, "..", "..", "interiority_in_passages", "results", "passC"))

MSV = re.compile(r"\b(knew|thought|felt|wanted|hoped|realis|realiz|wondered|remember|believ|decid|imagin|afraid|scared|angry|sad|happy|loved?|hated?|desire|fear|worried|ashamed|guilt|mind|heart)", re.I)
PRON = re.compile(r"\b(he|she|his|her|him|they|them|i|me|my)\b", re.I); PAST = re.compile(r"\b\w+ed\b")
URL = re.compile(r"https?://|www\.|\.com|\.org")
WEB = re.compile(r"(posted|comments?|reply|share|tags?:|categor|copyright|©|read more|click here|download|subscribe)", re.I)
QA = re.compile(r"\b(Q\s*:|A\s*:|Answer|Question|Options?:|Step \d)", re.I)
MD = re.compile(r"(^|\n)\s*(#{1,6}\s|\*\s|-\s|\d+\.\s|\|)")


def feats(xs):
    out = []
    for x in xs:
        w = x.split(); nw = max(len(w), 1); nc = max(len(x), 1)
        sents = [s for s in re.split(r'[.!?]+', x) if s.strip()]
        tok = [t for t in re.findall(r"[a-z']+", x.lower())]; cnt = collections.Counter(tok)
        out.append([len(x), nw, len(sents), nw / max(len(sents), 1), sum(len(t) for t in w) / nw,
                    sum(c.isdigit() for c in x) / nc, sum(c.isupper() for c in x) / nc, sum(c in '.,;:' for c in x) / nc,
                    x.count('"') / nw, x.count('?') / nw, x.count('!') / nw, x.count('\n') / nw, x.count('\n\n') / nw,
                    sum(ord(c) > 127 for c in x) / nc, len(MSV.findall(x)) / nw, len(PRON.findall(x)) / nw,
                    len(PAST.findall(x)) / nw, len(URL.findall(x)), len(WEB.findall(x)), len(QA.findall(x)),
                    len(MD.findall(x)), (cnt.most_common(1)[0][1] / max(len(tok), 1)) if tok else 0,
                    len(set(tok)) / max(len(tok), 1)])
    return np.array(out)


def train():
    import pyarrow.parquet as pq
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline, make_union
    from sklearn.preprocessing import StandardScaler, FunctionTransformer
    S = pq.read_table(os.path.join(PASSC, "sample.parquet")).to_pydict()
    K = {i: x for i, x in zip(S["id"], S["text"])}
    A, B = {}, {}
    for f in sorted(glob.glob(os.path.join(PASSC, "codings", "*.json"))):
        r = json.load(open(f, encoding="utf-8")); A.update(r.get("A", {})); B.update(r.get("B", {}))
    tr = [i for i in A if i in B and i in K and A[i]["narrative"] == B[i]["narrative"]]
    y = np.array([1 if A[i]["narrative"] else 0 for i in tr])
    m = make_pipeline(make_union(make_pipeline(FunctionTransformer(feats), StandardScaler()),
                                 TfidfVectorizer(analyzer='char_wb', ngram_range=(2, 4), max_features=5000, min_df=3, sublinear_tf=True)),
                      LogisticRegression(max_iter=3000, class_weight='balanced', C=0.5))
    m.fit([K[i] for i in tr], y)
    print("trained on %d passages (%d narrative)" % (len(tr), y.sum()), flush=True)
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--score", nargs=2, metavar=("IN", "OUT"))
    a = ap.parse_args()
    import pyarrow as pa, pyarrow.parquet as pq
    m = train()
    if a.check:
        T = pq.read_table(os.path.join(PASSC, "triage.parquet"), columns=["id", "text", "score"]).to_pydict()
        rng = np.random.default_rng(0); ix = rng.choice(len(T["id"]), 3000, replace=False)
        new = m.predict_proba([T["text"][j] for j in ix])[:, 1]; old = np.array([T["score"][j] for j in ix])
        print("re-scored 3,000 triage rows: max |diff| %.2e, r %.6f" % (np.abs(new - old).max(), np.corrcoef(new, old)[0, 1]))
    if a.score:
        t = pq.read_table(a.score[0])
        sc = m.predict_proba(t.column("text").to_pylist())[:, 1]
        pq.write_table(t.append_column("score", pa.array(sc)), a.score[1], compression="zstd")
        print("scored %d -> %s" % (len(sc), a.score[1]))


if __name__ == "__main__":
    main()
