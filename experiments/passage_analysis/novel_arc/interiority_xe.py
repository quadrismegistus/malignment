"""Interiority as USAS X + E, counted once per word with a POS-matched entry. (RH, 2026-09-25)

    ~/github/lltk/.venv/bin/python -u interiority_xe.py --benchmark
        -> INTERIORITY_XE_BENCHMARK.md, and per-passage scores beside the coder data
    ~/github/lltk/.venv/bin/python -u interiority_xe.py --lists
        -> INTERIORITY_LISTS_BENCHMARK.md: word LISTS from the LLM consensus ratings against the coder
    ~/github/lltk/.venv/bin/python -u interiority_xe.py --history --corpus chadwyck --workers 8
        -> $MALIGNMENT_DATA/novel_arc/interiority_{corpus}_n200.parquet
    ~/github/lltk/.venv/bin/python -u interiority_xe.py --models
        -> $MALIGNMENT_DATA/novel_arc/interiority_model_placement.parquet

WHY. Figure 5's interiority panel is `usas_x`. Against the blind interiority coder (interiority_in_passages)
it beats every seeded word2vec norm the abstraction seat built, and adding emotion (USAS E) beats it on
every criterion but narrative-only (USAS_X_CODER_BENCHMARK.md; the seat's eval under its own controls).

THE COUNTING RULE (agreed with the abstraction seat). `usas_x` as measure_lltk counts it takes the primary
tag of EVERY part-of-speech entry a word has in the USAS lexicon and counts each, so `thought` (verb,
adjective and noun entries) scores up to three X tags per token and a share can pass 1. Here, per content
word (measure_lltk.Scorer's tokens, modernisation, lemma and type-level POS):
  1. the lexicon entry matching the word's tagged POS, surface form first, then lemma;
  2. only when no entry matches the POS, the first entry of the surface form, then of the lemma;
  3. that entry's PRIMARY tag (both halves of a compound like X9.2+/A12+);
  4. the word counts ONCE for a family if the tag is in it: x (X*), e (E*), xe (X* or E*).
Shares are over content words, as usas_x's are.

The history pass also scores two seeded norms from the abstraction seat (interiority_norms.parquet,
B_ALL.median emotion-vs-exterior, C_ALL.median cognition+emotion-vs-exterior) as a passage MEAN over
lower-cased tokens minus NLTK stopwords -- the seat's scoring rule -- for the diagnostic plate.

CONTROLS. The history pass recomputes measure_lltk's own `usas_x` in the same pass and requires it to equal
the stored value for the same (text_id, seq), so the passages are the published ones. The benchmark asserts
the seat's passage count (13,564).
"""
import collections, glob, json, os, re, sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
for p in (HERE, REPO):
    if p not in sys.path:
        sys.path.insert(0, p)
DATA = os.path.join(os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data")), "novel_arc")
SHARED = os.path.expanduser("~/malignment-data/interiority_norms")
BASE = re.compile(r"^([A-Z])")
FAMILIES = {"x": ("X",), "e": ("E",), "xe": ("X", "E")}
NORM_COLS = ("B_ALL.median", "C_ALL.median")


def usas_entries():
    """(word, pos) -> primary tag, and word -> first entry's primary tag, from the raw English lexicon."""
    from malignment import fields as F
    by_pos, first = {}, {}
    for line in open(F.SOURCES["usas"], encoding="utf-8", errors="replace"):
        p = line.rstrip("\n").split("\t")
        if len(p) < 3 or p[0] == "lemma" or not p[2].strip():
            continue
        w, pos, prim = p[0].lower(), p[1], p[2].split()[0]
        by_pos.setdefault((w, pos), prim)
        first.setdefault(w, prim)
    return by_pos, first


class XE:
    """Per passage: n_content and the x / e / xe shares under the POS-matched, once-per-word rule."""

    def __init__(self, scorer=None):
        from measure_lltk import Scorer
        self.S = scorer or Scorer()
        self.by_pos, self.first = usas_entries()

    def primary(self, w, lem, pos):
        for key in ((w, pos), (lem, pos)):
            if key in self.by_pos:
                return self.by_pos[key]
        return self.first.get(w) or self.first.get(lem)

    def score(self, txt, base=None):
        from measure_lltk import TOK
        S = self.S
        v = base if base is not None else S.score(txt)       # fills the lemma/POS caches
        if not v:
            return None
        raw = [w.lower() for w in TOK.findall(txt)]
        mod = [S._modernise(w) for w in raw]
        content = [(w, S._lem.get(w, w), S._pos.get(w)) for w in mod]
        content = [c for c in content if c[2] in ("NOUN", "VERB", "ADJ", "ADV")]
        n = len(content)
        hits = collections.Counter()
        for w, lem, pos in content:
            tag = self.primary(w, lem, pos)
            if not tag:
                continue
            heads = {m.group(1) for m in (BASE.match(part) for part in tag.split("/")) if m}
            for fam, letters in FAMILIES.items():
                if heads & set(letters):
                    hits[fam] += 1
        out = {"n_content": n, "usas_x_old": v.get("usas_x"), "rh_absconc_median": v.get("rh_absconc_median")}
        for fam in FAMILIES:
            out["int_" + fam] = hits[fam] / n if n else None
        return out


def word_lists():
    """The lists under test (RH, 2026-09-25), from interiority_candidates.py's consensus ratings.
    A word is ON a list if its consensus interior >= 2 and its consensus kind is a mental one."""
    import pandas as pd
    mental = ("cognition", "emotion", "volition", "perception", "attention")
    x = pd.read_csv(os.path.join(SHARED, "usasx_consensus_v1.csv"))
    c = pd.read_csv(os.path.join(SHARED, "candidate_consensus_v1.csv"))
    clean_x = set(x.word[(x.interior >= 2) & x.kind.isin(mental)])
    cand = set(c.word[(c.interior >= 2) & c.kind.isin(mental)])
    full_x = set(x.word)
    assert (len(clean_x), len(cand), len(full_x)) == (1526, 2161, 3225), (len(clean_x), len(cand), len(full_x))
    assert not clean_x & cand                    # candidates are non-X by construction
    return {"full X list (3,225)": full_x, "clean X (1,526)": clean_x, "new candidates (2,161)": cand,
            "clean X + candidates (3,687)": clean_x | cand}


def list_shares(X, txt, lists):
    """Share of content words whose surface form or lemma is on each list, each word counted once."""
    from measure_lltk import TOK
    S = X.S
    v = S.score(txt)
    if not v:
        return None
    raw = [w.lower() for w in TOK.findall(txt)]
    mod = [S._modernise(w) for w in raw]
    content = [(w, S._lem.get(w, w)) for w in mod if S._pos.get(w) in ("NOUN", "VERB", "ADJ", "ADV")]
    n = len(content)
    out = {"n_content": n, "usas_x_old": v.get("usas_x"), "rh_absconc_median": v.get("rh_absconc_median")}
    for name, L_ in lists.items():
        out[name] = sum(1 for w, l in content if w in L_ or l in L_) / n if n else None
    return out


def benchmark_lists():
    import pandas as pd
    from scipy.stats import spearmanr
    import usas_x_coder_benchmark as B
    P = B.passages()
    assert len(P) == 13564, len(P)
    lists = word_lists()
    X = XE()
    rows = []
    for i, (pid, r) in enumerate(P.iterrows()):
        rows.append(dict(id=pid, **(list_shares(X, r.text or "", lists) or {})))
        if (i + 1) % 3000 == 0:
            print("  %d scored" % (i + 1), flush=True)
    D = pd.DataFrame(rows).set_index("id").join(P[["degree", "narrative", "prompt"]])
    ok = D[(D.n_content >= B.MIN_CONTENT) & D.rh_absconc_median.notna()]
    c, y, nar = ok.rh_absconc_median, ok.degree, ok.narrative.astype(bool)
    assert abs(spearmanr(ok.usas_x_old, y)[0] - 0.368) < 0.0005          # the earlier benchmark, unchanged
    L = ["# Interiority word lists from the LLM consensus ratings, against the blind coder (EXPLORATORY)", "",
         "Producer `interiority_xe.py --lists`. The abstraction seat's %d coded English passages, %d with at least "
         "%d content words (%d narrative); coder degree 0-3, mean over coders A and B; control the plate's "
         "concreteness. Each list: share of content words whose surface form or lemma is on the list, each word "
         "counted once. Lists from interiority_candidates.py's consensus ratings (interior >= 2 and a mental kind; "
         "INTERIORITY_TIEBREAK.md): CLEAN X is the USAS X words that pass; NEW CANDIDATES are period-model "
         "neighbours of X from outside X that pass. The FULL X LIST is every X word under the same rule, so "
         "clean X against it isolates the cleaning from the counting rule. The coder is an LLM and so is the "
         "rater that made these lists: agreement here is not independent validation." % (
             len(P), len(ok), B.MIN_CONTENT, int(nar.sum())), "",
         "| measure | raw | partial (concreteness) | partial within prompt | partial narrative | rho with concreteness | median share |",
         "|---|---|---|---|---|---|---|"]
    for col in ["usas_x_old"] + list(lists):
        x = ok[col]
        lab = "usas_x (panel now)" if col == "usas_x_old" else col
        L.append("| %s | %+.3f | %+.3f | %+.3f | %+.3f | %+.3f | %.3f |" % (
            lab, spearmanr(x, y)[0], B.partial(x, y, c)[0], B.partial(x, y, c, groups=ok.prompt)[0],
            B.partial(x[nar], y[nar], c[nar])[0], spearmanr(x, c)[0], float(x.median())))
    L += ["", "Sampling error of each coefficient is about 0.009 overall and 0.013 in the narrative subset; gaps "
          "smaller than ~0.03 between measures on the same passages are not differences without a dependent-"
          "correlation test."]
    open(os.path.join(HERE, "INTERIORITY_LISTS_BENCHMARK.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


# ─────────────────────────────────────────────────────────────── the coder benchmark
def benchmark():
    import pandas as pd
    from scipy.stats import spearmanr
    import usas_x_coder_benchmark as B
    P = B.passages()
    assert len(P) == 13564, len(P)
    X = XE()
    rows = []
    for i, (pid, r) in enumerate(P.iterrows()):
        v = X.score(r.text or "") or {}
        rows.append(dict(id=pid, **v))
        if (i + 1) % 3000 == 0:
            print("  %d scored" % (i + 1), flush=True)
    D = pd.DataFrame(rows).set_index("id").join(P[["degree", "narrative", "prompt"]])
    D.reset_index().to_parquet(os.path.join(SHARED, "interiority_xe_passages_dario.parquet"), index=False)
    ok = D[(D.n_content >= B.MIN_CONTENT) & D.rh_absconc_median.notna()]
    c, y, nar = ok.rh_absconc_median, ok.degree, ok.narrative.astype(bool)
    #: the earlier benchmark's usas_x must come back unchanged from this pass
    assert abs(spearmanr(ok.usas_x_old, y)[0] - 0.368) < 0.0005, spearmanr(ok.usas_x_old, y)[0]
    L = ["# Interiority as X + E, POS-matched and once per word, against the blind coder (EXPLORATORY)", "",
         "Producer `interiority_xe.py --benchmark`. The abstraction seat's %d coded English passages, %d with at "
         "least %d content words (%d narrative); coder degree 0-3, mean over coders A and B; control the plate's "
         "concreteness (`rh_absconc_median`). Rule: the USAS entry matching the word's tagged POS (surface, then "
         "lemma; any entry only if none matches), its primary tag, counted once per word per family." % (
             len(P), len(ok), B.MIN_CONTENT, int(nar.sum())), "",
         "| measure | raw | partial (concreteness) | partial within prompt | partial narrative | rho with concreteness | share > 1 |",
         "|---|---|---|---|---|---|---|"]
    for col, lab in (("usas_x_old", "usas_x (panel now: every POS entry, counted per tag)"), ("int_x", "X"),
                     ("int_e", "E"), ("int_xe", "X + E")):
        x = ok[col]
        L.append("| %s | %+.3f | %+.3f | %+.3f | %+.3f | %+.3f | %d |" % (
            lab, spearmanr(x, y)[0], B.partial(x, y, c)[0], B.partial(x, y, c, groups=ok.prompt)[0],
            B.partial(x[nar], y[nar], c[nar])[0], spearmanr(x, c)[0], int((x > 1).sum())))
    L += ["", "The panel should cite the X + E row for the rule it uses. EXPLORATORY."]
    open(os.path.join(HERE, "INTERIORITY_XE_BENCHMARK.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


# ─────────────────────────────────────────────────────────────── the history pass
def _norm_dicts():
    import pyarrow.parquet as pq
    t = pq.read_table(os.path.join(SHARED, "interiority_norms.parquet"), columns=["word"] + list(NORM_COLS))
    words = t.column("word").to_pylist()
    return {c: {w: v for w, v in zip(words, t.column(c).to_pylist()) if v is not None and v == v} for c in NORM_COLS}


def _norm_means(txt, D, sw):
    from measure_lltk import TOK
    toks = [w.lower() for w in TOK.findall(txt)]
    toks = [w for w in toks if w not in sw]
    out = {}
    for c, d in D.items():
        v = [d[w] for w in toks if w in d]
        out["norm_" + c.split(".")[0]] = float(np.mean(v)) if v else None
    out["n_norm"] = sum(1 for w in toks if w in D[NORM_COLS[0]])
    return out


def hist_text(job):
    """(text_id, year, n, corpus) -> [row], exactly measure_lltk.one_text's passages and seq."""
    global _X, _D, _SW
    tid, year, n, corpus = job
    try:
        X = _X
    except NameError:
        from nltk.corpus import stopwords
        X = _X = XE()
        _D = _norm_dicts()
        _SW = set(stopwords.words("english"))
    import lltk
    C = lltk.Corpus(corpus)
    rows = []
    try:
        tx = C.text(tid)
        for seq, p in enumerate(tx.passages(n=n).texts()):
            v = X.score(p.txt)
            if v is None:
                continue
            v.update(_norm_means(p.txt, _D, _SW))
            v.update(text_id=tid, year=year, seq=seq)
            rows.append(v)
    except Exception as e:
        rows.append({"text_id": tid, "year": year, "seq": -1, "error": "%s: %s" % (type(e).__name__, str(e)[:120])})
    return rows


def history(corpus, workers=1, limit=None, n=200):
    import time
    import pandas as pd
    from measure_lltk import texts_with_years
    t0 = time.time()
    jobs = [(tid, y, n, corpus) for tid, y in texts_with_years(corpus)]
    if limit:
        jobs = jobs[:limit]
    print("%d dated %s texts" % (len(jobs), corpus), flush=True)
    if workers > 1:
        import multiprocessing as mp
        pool = mp.get_context("spawn").Pool(workers)          # spawn, as measure_lltk (Metal + fork)
        it = pool.imap_unordered(hist_text, jobs, chunksize=1)
    else:
        pool, it = None, (hist_text(j) for j in jobs)
    rows, done = [], 0
    for part in it:
        rows.extend(part)
        done += 1
        if done % 50 == 0 or done == len(jobs):
            el = time.time() - t0
            print("  [%d/%d] %s passages  %.0f/s  %.1f min" % (done, len(jobs), "{:,}".format(len(rows)),
                                                             len(rows) / max(el, 1e-9), el / 60), flush=True)
    if pool:
        pool.close(); pool.join()
    bad = [r for r in rows if r.get("seq") == -1]
    D = pd.DataFrame([r for r in rows if r.get("seq") != -1])
    #: CONTROL: the stored table's usas_x for the same (text_id, seq) must come back exactly
    ref = pd.read_parquet(os.path.join(DATA, "%s_n%d.parquet" % (corpus, n)), columns=["text_id", "seq", "usas_x"])
    if limit:
        ref = ref[ref.text_id.isin(set(D.text_id))]
    m = D.merge(ref, on=["text_id", "seq"], how="outer", indicator=True)
    assert (m._merge == "both").all(), m._merge.value_counts().to_dict()
    both = m.dropna(subset=["usas_x", "usas_x_old"])
    assert np.allclose(both.usas_x, both.usas_x_old, atol=1e-12), "usas_x differs on %d passages" % int(
        (~np.isclose(both.usas_x, both.usas_x_old, atol=1e-12)).sum())
    print("  CONTROL: %d passages, keys and usas_x identical to %s_n%d.parquet" % (len(D), corpus, n))
    out = os.path.join(DATA, "interiority_%s_n%d%s.parquet" % (corpus, n, "_limit%d" % limit if limit else ""))
    D.to_parquet(out, index=False)
    print("-> %s  (%.1f min)%s" % (out, (time.time() - t0) / 60, ("  %d TEXTS FAILED" % len(bad)) if bad else ""))


if __name__ == "__main__":
    if "--history" in sys.argv:
        a = sys.argv
        history(a[a.index("--corpus") + 1], int(a[a.index("--workers") + 1]) if "--workers" in a else 1,
                int(a[a.index("--limit") + 1]) if "--limit" in a else None)
    elif "--benchmark" in sys.argv:
        benchmark()
    elif "--lists" in sys.argv:
        benchmark_lists()
    else:
        print(__doc__)
