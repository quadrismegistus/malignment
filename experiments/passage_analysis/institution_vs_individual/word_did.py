"""Which WORDS carry base-vs-aligned x individual-vs-institution? -> results/word_did.md

    python -u word_did.py

EXPLORATORY, NOT DECLARED (RH, 2026-09-24: "simple word counts?"). No LLM in the
measurement or the selection: every regeneration passage in a lineage with both
arms, passage text only, lower-cased [a-z']+ tokens.

Per word, the share of passages CONTAINING it (document frequency, so a long
list does not count five times). Per lineage:

    did = (aligned - base, individual) - (aligned - base, institution)

Two-sided sign test over lineages, Benjamini-Hochberg over every word tested.
Words tested: those in >= 300 passages overall. A surviving word is also checked
by dispute (18). Positive = the word gains MORE (or loses less) on the
individual's side; negative = on the institution's.
"""
import collections, json, os, re, sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import analyse_regen as A  # noqa: E402

TOK = re.compile(r"[a-z']+")
MIN_DOCS = 300


def bh(ps, q=0.05):
    o = sorted(range(len(ps)), key=lambda i: ps[i])
    k = max([r for r, i in enumerate(o, 1) if ps[i] <= q * r / len(ps)], default=0)
    keep = set(o[:k])
    return [i in keep for i in range(len(ps))]


def compute():
    """Everything the table is built from. -> dict

    For `plot.py` (dario, 2026-09-24): import this rather than recompute it.

        n_passages, vocab, min_docs     the population and the tested words
        n_lineages, n_disputes          units with all four (arm x side) cells
        words   {word: {lineage_up, lineage_down, lineage_p, dispute_up,
                        dispute_down, dispute_p, median_did, bh_lineage}}
                median_did is over LINEAGES; bh_lineage is BH over every tested
                word's lineage p
        share   {(arm, side): {word: share of that cell's passages containing it}}
    """
    rows = [json.loads(l) for l in open(A.SRC)]
    rows = [r for r in rows if r["lineage"] not in A.BROKEN_LINEAGES]
    arms = collections.defaultdict(set)
    for r in rows:
        arms[r["lineage"]].add(r["arm"])
    rows = [r for r in rows if arms[r["lineage"]] == {"base", "aligned"}]
    docs = [set(TOK.findall((r["text"] or "").lower())) for r in rows]
    df = collections.Counter(w for d in docs for w in d)
    vocab = sorted(w for w, n in df.items() if n >= MIN_DOCS)
    idx = {w: i for i, w in enumerate(vocab)}
    # counts per (unit, arm, side): passages, and per-word containing counts
    def tally(unit):
        n = collections.Counter(); c = collections.defaultdict(lambda: np.zeros(len(vocab)))
        for r, d in zip(rows, docs):
            k = (r[unit], r["arm"], r["side"])
            n[k] += 1
            for w in d:
                if w in idx:
                    c[k][idx[w]] += 1
        units = sorted({k[0] for k in n})
        out = []
        for u in units:
            ks = [(u, a, s) for a in ("base", "aligned") for s in ("individual", "institution")]
            if min(n[k] for k in ks) == 0:
                continue
            f = {k: c[k] / n[k] for k in ks}
            out.append((f[(u, "aligned", "individual")] - f[(u, "base", "individual")])
                       - (f[(u, "aligned", "institution")] - f[(u, "base", "institution")]))
        return np.array(out)
    L_ = tally("lineage"); D_ = tally("scenario")
    res = []
    for w, i in idx.items():
        lu, ld, lp = A.sign(list(L_[:, i])); du, dd, dp = A.sign(list(D_[:, i]))
        res.append((w, lu, ld, lp, du, dd, dp, float(np.median(L_[:, i]))))
    sig = bh([r[3] for r in res])
    share = {}
    for a in ("base", "aligned"):
        for s in ("individual", "institution"):
            sub = [d for r, d in zip(rows, docs) if r["arm"] == a and r["side"] == s]
            share[(a, s)] = {w: sum(1 for d in sub if w in d) / len(sub) for w in vocab}
    words = {w: dict(lineage_up=lu, lineage_down=ld, lineage_p=lp, dispute_up=du, dispute_down=dd,
                     dispute_p=dp, median_did=med, bh_lineage=s)
             for (w, lu, ld, lp, du, dd, dp, med), s in zip(res, sig)}
    return dict(n_passages=len(rows), vocab=vocab, min_docs=MIN_DOCS, n_lineages=int(L_.shape[0]),
                n_disputes=int(D_.shape[0]), words=words, share=share)


def main():
    C = compute()
    words, share = C["words"], C["share"]
    keep = [(w, v) for w, v in words.items() if v["bh_lineage"]]
    both = [(w, v) for w, v in keep if v["dispute_p"] < 0.05]
    L = ["# Word-level base/aligned x individual/institution (EXPLORATORY)", "",
         "Producer `word_did.py`. %d passages, %d words tested (in >= %d passages), %d survive BH over "
         "lineages, %d of those also p<0.05 by dispute. Cells: share of passages containing the word." % (
             C["n_passages"], len(C["vocab"]), C["min_docs"], len(keep), len(both)), ""]
    for sign_, title in ((1, "Gains MORE on the individual's side"), (-1, "Gains MORE on the institution's side")):
        sel = sorted([(w, v) for w, v in both if np.sign(v["median_did"]) == sign_],
                     key=lambda wv: -abs(wv[1]["median_did"]))[:40]
        L += ["## " + title, "", "| word | base ind | base inst | aligned ind | aligned inst | median did | lineages +/- | disputes +/- |",
              "|---|---|---|---|---|---|---|---|"]
        for w, v in sel:
            L.append("| %s | %.3f | %.3f | %.3f | %.3f | %+.3f | %d/%d | %d/%d |" % (
                w, share[("base", "individual")][w], share[("base", "institution")][w],
                share[("aligned", "individual")][w], share[("aligned", "institution")][w], v["median_did"],
                v["lineage_up"], v["lineage_down"], v["dispute_up"], v["dispute_down"]))
        L.append("")
    open(os.path.join(HERE, "results", "word_did.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
