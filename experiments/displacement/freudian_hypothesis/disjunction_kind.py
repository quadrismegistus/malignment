"""The disjunction with the affect axis as KIND, on the validated doer feeling. -> results/disjunction_kind.json, .md

    python -u disjunction_kind.py --write

Declared 2026-09-28 before it ran (paper seat, for RH's Displacement section: "does it survive
on the validated doer probabilities, using existing ratings only?"). `disjunction.py` found the
affect route taken ~3x the substitution route (45/49) -- with AFFECT = `k_charge`, word-level
INTENSITY: a word "keeps the affect" if its charge is at least the departing mass's charge minus
tol. That is keeping the CHARGE, not the feeling's KIND (`kill` anger -> `scream` fear keeps it).
This file keeps everything else identical and swaps that one axis.

    ACT            unchanged: max(k_bodily_harm, k_transgressiveness) against the cell's departing
                   A, tol swept 0.5 / 1.0 / 1.5, charged cells only (departing act >= 4)
    FEELING KEPT   the arriving word's Jev DOER distribution (type_survey.py v2, the reading that
                   passed the second-rater gate) has its top NAMED feeling = X, the departing
                   mass's dominant named feeling (|delta|-weighted mean doer distribution), AND
                   P(none) < 0.5. Words without a Jev rating are dropped from both numerator and
                   availability; their share is reported.
    HEADLINE       per lineage, enrichment(no act, feeling kept) / enrichment(full act, feeling
                   kept), enrichment = share of arriving mass / share of the cell's candidate list;
                   median over lineages, sign test on log ratio -- `disjunction.py`'s own statistic.
"""
import argparse, collections, json, math, os, statistics as st, sys
from math import comb

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
import disjunction as DJ  # noqa: E402

JEV = os.path.expanduser("~/malignment-data/affect_proportionality/type_survey.parquet")
OUT = os.path.join(HERE, "results", "disjunction_kind")
OUT = OUT + os.environ.get("FH_TAG", "")
FEEL = ["anger", "fear", "grief", "desire", "disgust", "shame", "tenderness", "joy", "none"]
NAMED = FEEL[:-1]
Q = ["SUBSTITUTE (full act, feeling kept)", "MILDER ACT (partial act, feeling kept)", "DISPLACED FEELING (no act, feeling kept)",
     "act kept, feeling lost", "NEITHER (content word)", "NEITHER (function word)"]


def compute(tol, min_act, vec):
    ref = collections.defaultdict(lambda: [0.0, 0.0, [0.0] * len(FEEL)])
    n_all = n_rated = 0
    for lin, pr, w, d, a, c, _f in DJ.stream():
        if d < 0:
            r = ref[(lin, pr)]
            r[0] += -d; r[1] += -d * a
            v = vec.get(w)
            if v:
                r[2] = [x + -d * y for x, y in zip(r[2], v)]
    live = {}
    for k, (m, wa, dv) in ref.items():
        if m > 0 and wa / m >= min_act and sum(dv[:-1]) > 0:
            X = max(range(len(NAMED)), key=lambda i: dv[i])
            live[k] = (wa / m, X)
    acc, avail = collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter)
    ex = collections.Counter()
    for lin, pr, w, d, a, c, isfn in DJ.stream():
        key = (lin, pr)
        if key not in live:
            continue
        n_all += 1
        v = vec.get(w)
        if not v:
            continue
        n_rated += 1
        A, X = live[key]
        top = max(range(len(NAMED)), key=lambda i: v[i])
        kept = top == X and v[-1] < 0.5
        act = 2 if a >= A - tol else (1 if a >= DJ.ACT_FLOOR else 0)
        q = (Q[0] if act == 2 else Q[1] if act == 1 else Q[2]) if kept else (Q[3] if act > 0 else (Q[5] if isfn else Q[4]))
        avail[lin][q] += 1
        if d > 0:
            acc[lin][q] += d; ex[(q, w)] += d
    enr = lambda lin, q: (acc[lin][q] / sum(acc[lin].values())) / (avail[lin][q] / sum(avail[lin].values())) if avail[lin][q] and sum(acc[lin].values()) else None
    out = {}
    for q in Q:
        e = [x for x in (enr(l, q) for l in acc) if x is not None]
        out[q] = dict(median_enrichment=st.median(e) if e else None, n=len(e), below_1=sum(x < 1 for x in e),
                      words=[w for (qq, w), _ in ex.most_common() if qq == q][:10])
    head = []
    for lin in acc:
        s, f = enr(lin, Q[0]), enr(lin, Q[2])
        if s and f:
            head.append(f / s)
    nn = len(head); up = sum(x > 1 for x in head); k = min(up, nn - up)
    out["_headline"] = dict(median_ratio=st.median(head) if head else None, above_1=up, n=nn,
                            p_sign=min(1.0, sum(comb(nn, i) for i in range(k + 1)) * 2 / 2 ** nn) if nn else None)
    out["_coverage"] = dict(cells=len(live), candidate_rows=n_all, rated_rows=n_rated)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    import pyarrow.parquet as pq
    vec = {}
    for r in pq.read_table(JEV).to_pylist():
        if r["ok"]:
            v = [r["doer_feeling_p_%s" % f] for f in FEEL]; t = sum(v)
            if t > 0:
                vec[r["word"]] = [x / t for x in v]
    res = {"tol=%.1f" % t: compute(t, 4.0, vec) for t in (0.5, 1.0, 1.5)}
    L = ["# The disjunction with the affect axis as KIND (validated doer feeling)", "",
         "Producer `disjunction_kind.py` (declared in its docstring before it ran). `disjunction.py` with AFFECT = k_charge swapped for 'the arriving word's doer feeling is the departing mass's dominant named feeling'.", "",
         "| tol | cells | rated share of candidate rows | DISPLACED FEELING / SUBSTITUTE enrichment, median | lineages > 1 | p |", "|---|---|---|---|---|---|"]
    for t, r in res.items():
        h, cv = r["_headline"], r["_coverage"]
        L.append("| %s | %d | %.2f | %s | %d / %d | %s |" % (t, cv["cells"], cv["rated_rows"] / max(cv["candidate_rows"], 1),
                 "%.2f" % h["median_ratio"] if h["median_ratio"] else "--", h["above_1"], h["n"], "%.2g" % h["p_sign"] if h["p_sign"] is not None else "--"))
    r = res["tol=1.0"]
    L += ["", "At tol 1.0, per quadrant (median enrichment over lineages; top arriving words):", "", "| quadrant | enrichment | lineages below 1 | words |", "|---|---|---|---|"]
    for q in Q:
        x = r[q]
        L.append("| %s | %s | %d / %d | %s |" % (q, "%.2f" % x["median_enrichment"] if x["median_enrichment"] else "--", x["below_1"], x["n"], ", ".join(x["words"][:8])))
    md = "\n".join(L) + "\n"; print(md)
    if a.write:
        json.dump(res, open(OUT + ".json", "w"), indent=1); open(OUT + ".md", "w").write(md)


if __name__ == "__main__":
    main()
