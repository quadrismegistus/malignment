"""Contiguity measured on its own axis: how often two words complete the SAME frames.

    python cocompletion.py                 -> kill's partners by PMI, vs cosine
    python cocompletion.py --unit cell     -> same model AND same prompt
    python cocompletion.py --arms base     -> base arms only

## THE QUESTION (TheoryMachines, the paper seat)

Sections 8-10 found that `scream` is far from `kill` in every embedding tried,
and read that as: the two are related by the FRAME rather than by meaning --
contiguity rather than similarity, Jakobson's combination axis rather than his
selection axis, which is what makes the displacement metonymic. That reading was
inferred from the FAILURE of a similarity measure, which is weak evidence: a
null on one axis is not a positive result on the other.

His proposal, and it is the right one: measure contiguity directly. If `kill`
and `scream` are frame-mates, they should **co-occur as completions of the same
prompts across the corpus** even though they are far apart in the embedding. So
rank `kill`'s partners by co-completion and see where `scream` lands.

    cosine rank of `scream` among the 307 candidates   262 of 307  (far)
    co-completion rank                                 this file

## WHY PMI AND NOT A RAW COUNT

Raw co-occurrence ranks by frequency: `go` and `get` complete nearly every
prompt in the corpus and would top any list. PMI divides out each word's own
rate, which is the standard collocation measure and the right register for a
claim about the combination axis.

    PMI(a,b) = log2 [ P(a,b) / (P(a) P(b)) ]     P over the 4,600 prompts

**A HIGH PMI ON A TINY COUNT IS NOISE**, so `--min-co` sets a floor and the
count is printed beside every score. Words that co-occur 3 times out of 4,600
can reach PMI 7 and mean nothing.

## THE UNIT IS A CHOICE AND BOTH ARE REPORTED

`prompt` asks whether the two words complete the same FRAME anywhere in the
roster -- model-agnostic, which is what "frame-mate" means. `cell` asks whether
one model's single distribution gave both words mass at once, which is stronger
and closer to "in the same paradigm at the same moment". They can disagree and
the disagreement is informative, so neither is hardcoded.
"""
import argparse, collections, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "substitution_shape"))
sys.path.insert(0, HERE)
import run  # noqa: E402


def sets(words, unit="prompt", arms="all"):
    """-> ({word: frozenset of unit ids}, N units in the corpus)."""
    from malignment import ch, roster
    eps, _ = roster.endpoints()
    models = sorted(set(eps)) if arms == "base" else \
        sorted(set(eps) | set(eps.values()))
    mlist = ", ".join("'%s'" % m.replace("'", "\\'") for m in models)
    key = "prompt" if unit == "prompt" else "concat(model, '\\t', prompt)"
    wl = ", ".join("'%s'" % w.replace("'", "\\'") for w in sorted(words))
    base = ("FROM {db}.twp_words_v4 WHERE rule_version=4 AND frame='' "
            "AND topup=0 AND model IN (%s)" % mlist)
    n = int(next(iter(ch.query(
        "SELECT uniqExact(%s) AS n %s" % (key, base), limit_bytes=None)))["n"])
    out = collections.defaultdict(set)
    q = ("SELECT word, %s AS u %s AND word IN (%s) GROUP BY word, u"
         % (key, base, wl))
    for r in ch.query(q, limit_bytes=None):
        out[r["word"]].add(r["u"])
    return {w: frozenset(s) for w, s in out.items()}, n


def pmi(S, N, src, words, min_co=5):
    """-> {word: (pmi, co, p_given_src)} for every word meeting `min_co`."""
    a = S.get(src, frozenset())
    out = {}
    for w in words:
        if w == src:
            continue
        b = S.get(w, frozenset())
        co = len(a & b)
        if co < min_co or not b:
            continue
        out[w] = (math.log2((co * N) / (len(a) * len(b))), co, co / len(a))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prompt", default=run.FIG2)
    ap.add_argument("--from", dest="src", default="kill")
    ap.add_argument("--unit", default="prompt", choices=("prompt", "cell"))
    ap.add_argument("--arms", default="all", choices=("all", "base"))
    ap.add_argument("--min-co", type=int, default=5)
    ap.add_argument("--basis", default="argmax", choices=("argmax", "faller", "crossing"))
    a = ap.parse_args(argv)

    import cosines
    cand, _why = run.candidate_words(a.prompt)
    words = sorted(cand)
    print("PROMPT %r   unit=%s arms=%s min-co=%d" % (a.prompt, a.unit, a.arms, a.min_co))
    S, N = sets(set(words) | {a.src}, a.unit, a.arms)
    print("  %d %ss in the corpus; %r clears theta on %d of them"
          % (N, a.unit, a.src, len(S.get(a.src, ()))))
    P = pmi(S, N, a.src, words, a.min_co)
    print("  %d of %d candidates meet min-co %d" % (len(P), len(words), a.min_co))

    _w, W, ids = cosines.space("bge", a.prompt)
    v = W[ids[a.src]]
    cos = {w: float(v @ W[ids[w]]) for w in _w}
    crank = {w: i for i, w in enumerate(sorted(cos, key=lambda x: -cos[x]))}
    prank = {w: i for i, w in enumerate(sorted(P, key=lambda x: -P[x][0]))}

    print("\n  TOP 15 BY CO-COMPLETION PMI (cosine rank in the last column)")
    for w in sorted(P, key=lambda x: -P[x][0])[:15]:
        pm, co, cond = P[w]
        print("    %-10s pmi %5.2f  co %5d  P(w|%s) %.2f   cos %+.3f rank %3d"
              % (w, pm, co, a.src, cond, cos[w], crank[w]))

    import lineage_graph as LG
    E, held, bw, aw, n, miss, nw, nr = LG.build(a.prompt, True, True, a.basis)
    dst = {t: c for (s, t), c in E.items() if s == a.src and t != a.src}
    print("\n  THE DESTINATIONS (basis=%s): the two axes side by side" % a.basis)
    print("    %-10s %8s  %18s  %18s" % ("word", "lineages", "COSINE (similarity)",
                                         "CO-COMPLETION (contiguity)"))
    for w, c in sorted(dst.items(), key=lambda x: -x[1]):
        cr = "%+.3f  rank %3d" % (cos[w], crank[w]) if w in crank else "not in vocab"
        pr = ("pmi %5.2f  rank %3d" % (P[w][0], prank[w])) if w in P else \
             "below min-co %d" % a.min_co
        print("    %-10s %8d  %18s  %18s" % (w, c, cr, pr))

    #: **THE HEADLINE IS THE DISAGREEMENT.** If the two rankings agreed, one of
    #: them would be redundant and the metonymy claim would have no axis of its
    #: own. Spearman over the words scored by both.
    both = [w for w in P if w in crank]
    if len(both) > 5:
        import statistics as st
        xs = [crank[w] for w in both]
        ys = [prank[w] for w in both]
        mx, my = st.mean(xs), st.mean(ys)
        num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        den = math.sqrt(sum((x - mx) ** 2 for x in xs)
                        * sum((y - my) ** 2 for y in ys))
        print("\n  rank correlation between the two axes over %d words: %+.3f"
              % (len(both), num / den if den else float("nan")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
