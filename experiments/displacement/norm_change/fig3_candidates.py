"""Candidate pole words for the 14 Figure 3 scales. -> results/fig3_pole_candidates.md

    python -u fig3_candidates.py

Two rating sources, because the fourteen scales have two kinds of provenance
and the difference has to reach whoever picks:

    LEXICON (8)  `k_*`, `warriner_*`, `brysbaert_*` -- a rating per WORD TYPE,
                 context-free, from `malignment.fields.norms`.
    v6 (6)       a rating per (PROMPT, WORD) from `slot_rating_en_v6`, on disk
                 as 2,236 `rated_v6_*.json` files. A word can be mundane in one
                 frame and not in another, so its value here is the mean over
                 the frames it was rated in, and `n_frames` is reported.

**THE CANDIDATE POOL IS THE MOVERS, NOT THE DICTIONARY.** A word enters only if
`words_long_v4` records it moving -- riser or faller -- on an endpoint lineage,
because a pole label naming a word alignment never touched would illustrate the
scale and not the finding. `n_moves` is how many (prompt, lineage) cells moved
it.

Poles are the scale's own ends, LOW LEFT and HIGH RIGHT, per paper-claude's
spec: no reorientation, so the side of every marker stays a result.
"""
import collections, gzip, json, os, statistics as st, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, ROOT)
V6DIR = os.path.join(ROOT, "experiments", "slot_ratings", "results", "v6")
WORDS = os.path.expanduser("~/malignment-data/norm_change/words_long_v4.csv.gz")
#: the scatter's 18 minus the four `_absz` spread scales, which the caption
#: already concedes are not independent of their parents
DROP = ("_absz",)
POLES = {
    "k_bodily_harm": ("no harm", "bodily harm"),
    "k_transgressiveness": ("unmarked", "transgressive"),
    "k_concreteness": ("abstract", "concrete"),
    "k_register_level": ("low register", "high register"),
    "k_vulgarity": ("not vulgar", "vulgar"),
    "warriner_arousal": ("calm", "aroused"),
    "warriner_valence": ("unpleasant", "pleasant"),
    "warriner_dominance": ("submissive", "dominant"),
    "v6:fit": ("does not fit", "fits the frame"),
    "v6:directedness": ("undirected", "directed"),
    "v6:makes_better": ("does not improve", "makes better"),
    "v6:makes_worse": ("does not worsen", "makes worse"),
    "v6:mundanity": ("charged", "mundane"),
    "v6:vocalisation": ("silent", "vocalized"),
}


def movers(min_moves=3):
    """{word: n cells it moved in}, English endpoint lineages only."""
    from malignment import roster
    eps, _ = roster.endpoints()
    keep = {"%s>%s" % (b, a) for b, a in eps.items()}
    c = collections.Counter()
    with gzip.open(WORDS, "rt") as fh:
        ix = {k: i for i, k in enumerate(fh.readline().rstrip("\n").split("\t"))}
        for line in fh:
            f = line.rstrip("\n").split("\t")
            if f[ix["lang"]] != "en" or f[ix["is_function"]] == "1":
                continue
            if "%s>%s" % (f[ix["base"]], f[ix["aligned"]]) not in keep:
                continue
            c[f[ix["word"]].strip()] += 1
    return {w: n for w, n in c.items() if n >= min_moves and w.isalpha()}


def v6_ratings():
    """{scale: {word: (mean rating, n frames)}} from the rated_v6 files."""
    acc = collections.defaultdict(lambda: collections.defaultdict(list))
    for fn in os.listdir(V6DIR):
        if not fn.startswith("rated_v6_"):
            continue
        for d in json.load(open(os.path.join(V6DIR, fn), encoding="utf-8")):
            if not d.get("ratable"):
                continue
            w = (d.get("word") or "").strip()
            for sc in ("fit", "directedness", "makes_better", "makes_worse",
                       "mundanity", "vocalisation"):
                if isinstance(d.get(sc), (int, float)):
                    acc["v6:" + sc][w].append(float(d[sc]))
    return {sc: {w: (st.mean(v), len(v)) for w, v in by.items()}
            for sc, by in acc.items()}


def main():
    from malignment import fields as F
    mv = movers()
    print("movers with >=3 cells: %d" % len(mv))
    v6 = v6_ratings()
    print("v6 scales rated: %s" % ", ".join("%s %d words" % (k, len(v))
                                            for k, v in sorted(v6.items())))
    lex = {}
    for w in mv:
        try:
            lex[w] = F.norms(w)
        except Exception:
            pass
    print("lexicon ratings for %d of %d movers" % (len(lex), len(mv)))

    L = ["# Figure 3 — candidate pole words", "",
         "Fourteen scales: the scatter's eighteen minus the four `_absz` spread "
         "scales. Poles are the scale's own ends, **low left, high right**, "
         "unreoriented — so the side of every marker on the plate is a result.",
         "",
         "A word enters only if `words_long_v4` records it MOVING on an "
         "endpoint lineage (riser or faller, content words, >= 3 cells): a "
         "pole naming a word alignment never touched would illustrate the "
         "scale and not the finding. `n` is how many cells moved it.",
         "",
         "Lexicon scales carry a context-free rating per word type. The six "
         "`v6:` scales are rated per (prompt, word), so a word's value is the "
         "mean over the frames it was rated in and `f` is how many.", ""]
    for sc, (plo, phi) in POLES.items():
        if sc.startswith("v6:"):
            tab = v6.get(sc, {})
            got = [(w, v[0], v[1]) for w, v in tab.items() if w in mv]
        else:
            got = [(w, d[sc], None) for w, d in lex.items()
                   if isinstance(d.get(sc), (int, float))]
        if len(got) < 20:
            L += ["## %s  <->  %s" % (plo, phi), "",
                  "`%s` — only %d rated movers; not enough to choose from."
                  % (sc, len(got)), ""]
            continue
        got.sort(key=lambda t: t[1])
        #: **A WIDE SLICE RE-SORTED BY FREQUENCY IS NOT A POLE.** Taking the
        #: top 15% by rating and then ranking it by how often the word moved
        #: put `pushed (2.0)` and `saw (2.0)` at the head of "bodily harm"
        #: while `kill (7.0)` came eleventh -- the common words win any
        #: frequency sort, which is the same defect that made the axis figure
        #: repeat `said` and `told`. Cut on the RATING first, hard, then rank.
        #: **AND PERCENTILES FAIL ON A FLOOR-DOMINATED SCALE.** `k_bodily_harm`
        #: rates most words 1.0, so its 90th percentile is also 1.0 and a
        #: `>= q90` filter admitted the whole corpus -- both poles came back
        #: identical, which is the failure mode that looks like working code.
        #: Rank by VALUE and take a fixed number from each end instead, ties
        #: broken by how often the word moved.
        got.sort(key=lambda t: (t[1], -mv[t[0]]))
        POOL = 60
        def fmt(rows):
            return ", ".join(
                "%s (%.1f, n=%d%s)" % (w, r, mv[w],
                                       ", f=%d" % f if f else "")
                for w, r, f in rows)
        lowc = sorted(got[:POOL], key=lambda t: -mv[t[0]])[:14]
        hic = sorted(got[-POOL:], key=lambda t: -mv[t[0]])[:14]
        L += ["## %s  <->  %s" % (plo, phi), "",
              "`%s`, %d rated movers. Ratings run %.2f to %.2f; each pole is "
              "the %d most extreme by rating (%.2f and %.2f at the cut), "
              "ranked within that by how often the word moved."
              % (sc, len(got), got[0][1], got[-1][1], POOL,
                 got[POOL - 1][1], got[-POOL][1]), "",
              "- **%s** (low end) — %s" % (plo, fmt(lowc)),
              "- **%s** (high end) — %s" % (phi, fmt(hic)), ""]
    p = os.path.join(HERE, "results", "fig3_pole_candidates.md")
    open(p, "w", encoding="utf-8").write("\n".join(L) + "\n")
    import shutil
    d = os.path.expanduser("~/Dropbox/Prof/Articles/TheoryMachines/paper/tools")
    shutil.copy(p, d)
    print("wrote %s and to paper/tools/" % p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
