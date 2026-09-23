"""Which hops survive a change of construction, and does any of it beat chance?

    python route_agreement.py            kill -> scream against 200 random pairs

## THE QUESTION (RH, via the drafting seat)

The caption wants to replace "other methods of drawing such a network alter the
routes" with something measured. So: across every construction this folder has
drawn on Llama's base residual, how often does each intermediate WORD recur,
how often does each EDGE, and is any of it more than two arbitrary routes
would share anyway?

## THE TWELVE CONSTRUCTIONS

Three vocabularies -- the 307 above-theta candidates, the 3,359 verb lemmas,
the 10,727 all-POS lemmas -- crossed with four ways of drawing a route:
k-nearest-neighbour shortest path at k=2, 3, 4, and the maximum-spanning-tree
path (the "bottleneck" corridor). All on the same space: the base model's
residual, mean over layers, centred on each vocabulary.

## THE BASELINE IS THE POINT AND IT IS NOT ANALYTIC

"How often would two routes share a word by chance" cannot be computed from
lengths and vocabulary size, because routes are not random walks: they are
shortest paths in a graph whose edges are semantic, so ANY two routes between
related words will share more than a random sequence would. The null has to be
other ROUTES, not other sequences.

So: sample random (source, target) pairs from the words present in all three
vocabularies, draw their routes under the same twelve constructions, and score
them the same way. `kill -> scream` is then read as a percentile of that
distribution. **The null is "an arbitrary pair of these words", which is the
comparison the caption implicitly makes.**

## THE STAGE CLASSIFICATION IS MINE AND IS DECLARED

The four stages below are a hand classification, written before the counts were
read, and it is the weakest link in this file: a reader who disagrees with the
assignment of `damage` or `brag` disagrees with the stage result. Words not in
any list are reported as unclassified rather than forced.
"""
import argparse, collections, itertools, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE) + "/substitution_shape")
sys.path.insert(0, HERE)
import cosines  # noqa: E402
import run as cc  # noqa: E402
import threshold  # noqa: E402
import wide_vocab  # noqa: E402

SPACES = ("llama_resid_mean", "llama_resid_verb", "llama_resid_wide")
KS = (2, 3, 4)

#: declared before the counts were read
STAGES = {
    "bodily injury": """hurt wound hit beat batter bash smash punch slug slap
        stab jab poke claw rip gouge strangle throttle choke drown shoot murder
        butcher gut skin peel thrash pummel damage harm injure maim attack
        fight brawl assault kick smack whip lash bite scratch slash slice
        wring wrench crush pound bang""".split(),
    "verbal injury": """offend insult curse swear cuss malign demean degrade
        discredit disgrace slander taunt mock scold berate nag rant abuse
        accuse blame criticize""".split(),
    "vocal noise": """scream cry shout yell roar shriek howl wail bark yap keen
        lament sob whoop brag boast talk speak say sing laugh weep sigh groan
        moan""".split(),
    "death / collapse": """die perish expire faint despair disappear vomit puke
        collapse drop fall bleed""".split(),
    "destruction": """explode implode burst bust break ruin destroy sabotage
        wreck undermine dismantle shatter""".split(),
}
STAGE_OF = {w: s for s, ws in STAGES.items() for w in ws}


def build(space, prompt):
    words, W, ids = cosines.space(space, prompt)
    W = W[[ids[w] for w in words]]
    pos = {w: i for i, w in enumerate(words)}
    out = {}
    for k in KS:
        adj, _S = cc.graph(words, pos, W, k)
        out[("knn", k)] = adj
    if len(words) > 6000:
        _B, madj, _p = wide_vocab.mst_prim(W, words, "kill")
    else:
        _B, madj, _p = threshold.bottlenecks(W, words, "kill")
    out[("mst", 0)] = {x: {y for y, _v in madj[x]} for x in madj}
    return words, pos, out


def route(adj, pos, words, a, b):
    """shortest path a->b in `adj` (the MST's adjacency gives the tree path)"""
    if a not in pos or b not in pos:
        return None
    s, t = pos[a], pos[b]
    prev, q = {s: None}, collections.deque([s])
    while q:
        x = q.popleft()
        if x == t:
            p = [t]
            while prev[p[-1]] is not None:
                p.append(prev[p[-1]])
            return [words[i] for i in reversed(p)]
        for y in adj.get(x, ()):
            if y not in prev:
                prev[y] = x
                q.append(y)
    return None


def score(routes):
    """-> (word counts, edge counts, mean pairwise Jaccard of interiors)"""
    inter = [set(r[1:-1]) for r in routes]
    edges = [set(zip(r, r[1:])) for r in routes]
    wc = collections.Counter(w for s in inter for w in s)
    ec = collections.Counter(e for s in edges for e in s)
    js = []
    for a, b in itertools.combinations(inter, 2):
        u = a | b
        js.append(len(a & b) / len(u) if u else 1.0)
    return wc, ec, (sum(js) / len(js) if js else 0.0)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prompt", default=cc.FIG2)
    ap.add_argument("--from", dest="src", default="kill")
    ap.add_argument("--to", dest="dst", default="scream")
    ap.add_argument("--nulls", type=int, default=200)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args(argv)

    G, shared = {}, None
    for sp in SPACES:
        words, pos, adjs = build(sp, a.prompt)
        G[sp] = (words, pos, adjs)
        shared = set(words) if shared is None else (shared & set(words))
    shared = sorted(shared)
    print("%d constructions: %d vocabularies x (k=2,3,4 + spanning tree)"
          % (len(SPACES) * (len(KS) + 1), len(SPACES)))
    print("  vocabularies: %s"
          % ", ".join("%s %d" % (s.replace("llama_resid_", ""), len(G[s][0]))
                      for s in SPACES))
    print("  %d words present in all three (the null's sampling frame)"
          % len(shared))

    def routes_for(src, dst):
        out = []
        for sp in SPACES:
            words, pos, adjs = G[sp]
            for key in list(adjs):
                r = route(adjs[key], pos, words, src, dst)
                if r and len(r) > 2:
                    out.append(r)
        return out

    real = routes_for(a.src, a.dst)
    wc, ec, jac = score(real)
    n = len(real)
    print("\n  %r -> %r drawn in %d of %d constructions" % (a.src, a.dst, n,
                                                           len(SPACES) * 4))
    print("\n  INTERMEDIATE WORDS by how many routes contain them")
    for w, c in wc.most_common():
        if c < 2:
            continue
        print("    %2d/%-2d  %-12s %s" % (c, n, w, STAGE_OF.get(w, "(unclassified)")))
    singles = [w for w, c in wc.items() if c == 1]
    print("    %2d words appear in exactly one route" % len(singles))
    print("\n  EDGES by how many routes contain them")
    for e, c in ec.most_common(8):
        if c < 2:
            continue
        print("    %2d/%-2d  %s -> %s" % (c, n, e[0], e[1]))
    if all(c < 2 for c in ec.values()):
        print("    none recurs")

    print("\n  STAGES each route passes through")
    seen_all = None
    for r in real:
        st = []
        for w in r[1:-1]:
            s = STAGE_OF.get(w)
            if s and (not st or st[-1] != s):
                st.append(s)
        seen_all = set(st) if seen_all is None else (seen_all & set(st))
    for r in sorted({tuple(
            [s for i, s in enumerate(
                [STAGE_OF.get(w) for w in rr[1:-1]]) if s and
             (i == 0 or s != [STAGE_OF.get(x) for x in rr[1:-1]][i - 1])])
            for rr in real}):
        print("    %s" % " -> ".join(r))
    print("  stages common to EVERY route: %s"
          % (", ".join(sorted(seen_all)) if seen_all else "NONE"))

    #: **IS A SHARED STAGE ITSELF REMARKABLE?** Every route out of `kill`
    #: starts among words for injuring, because that is what `kill`'s
    #: neighbourhood contains -- so "bodily injury appears in all twelve" may
    #: be forced by the source rather than by the chain. The null has to be
    #: asked the same question: how often does an ARBITRARY pair's routes all
    #: pass through some one stage?
    def common_stage(routes):
        cs = None
        for r in routes:
            st = {STAGE_OF.get(w) for w in r[1:-1]}
            st.discard(None)
            cs = st if cs is None else (cs & st)
        return cs or set()

    rs = random.Random(a.seed)
    cands = [w for w in shared if w not in (a.src, a.dst)]
    nulls = []
    while len(nulls) < a.nulls:
        s, t = rs.sample(cands, 2)
        r = routes_for(s, t)
        if len(r) >= n - 2:
            _wc, _ec, j = score(r)
            nulls.append((j, max(_wc.values()) if _wc else 0,
                          max(_ec.values()) if _ec else 0,
                          len(common_stage(r))))
    jn = sorted(x[0] for x in nulls)
    wn = sorted(x[1] for x in nulls)
    en = sorted(x[2] for x in nulls)

    def pct(v, arr):
        return 100.0 * sum(1 for x in arr if x <= v) / len(arr)

    print("\n  BASELINE: %d random word pairs from the same frame, same "
          "constructions" % len(nulls))
    print("    %-26s %8s %10s %10s" % ("", "kill->scream", "null median", "percentile"))
    print("    %-26s %8.3f %10.3f %9.0fth"
          % ("mean pairwise Jaccard", jac, jn[len(jn) // 2], pct(jac, jn)))
    print("    %-26s %8d %10d %9.0fth"
          % ("most-shared word", max(wc.values()) if wc else 0,
             wn[len(wn) // 2], pct(max(wc.values()) if wc else 0, wn)))
    print("    %-26s %8d %10d %9.0fth"
          % ("most-shared edge", max(ec.values()) if ec else 0,
             en[len(en) // 2], pct(max(ec.values()) if ec else 0, en)))
    sn = [x[3] for x in nulls]
    share = 100.0 * sum(1 for x in sn if x >= 1) / len(sn)
    print("    %-26s %8d %9.0f%% %s"
          % ("stages common to all", len(common_stage(real)), share,
             "of null pairs have >=1"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
