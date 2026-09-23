"""Shortest-path TREE from `kill` to the words the roster's lineages actually moved to.

    python pathways.py                      -> argmax targets, bge, k=2
    python pathways.py --basis faller --k 3
    python pathways.py --min-lineages 2     -> drop the singleton destinations

## THE IDEA (RH)

`run.py` walks from `kill` to ONE word chosen in advance. That picks the
destination, which is most of the answer. This producer takes the destinations
from the measurement instead: on this prompt, at lineage grain, `kill`'s base
arm goes to `scream` in 15 lineages, `cry` in 2, `hurt`/`punch`/`fight`/
`destroy` in 1 each, and stays at `kill` in 7. Those seven words are the query.

## WHY A SHARED NODE IS NOT AN AMBIGUITY

RH raised it: if two paths pass through the same node, do we know which path was
which? From a SINGLE source, yes. The union of shortest paths from one node is a
TREE -- every node has exactly one parent on its route back to `kill` -- so a
shared node means the two destinations genuinely share a prefix of their route,
which is the structure worth seeing rather than a confusion to avoid. Node
weight is then the lineage mass flowing through it, and a waypoint that carries
`scream`'s 15 and `cry`'s 2 is carrying 17.

**THE REAL AMBIGUITY IS TIES, AND IT IS DECLARED RATHER THAN LEFT TO BFS.**
Plain BFS returns whichever equal-length path it happened to reach first, which
is an artefact of vocabulary order. The rule here: minimise hops first, then
among equal-hop paths MAXIMISE the summed cosine of the steps, then take the
alphabetically first path. So the drawn route is the strongest of the shortest,
and it does not move when the word list is reordered.

## WHAT THIS FIGURE IS NOT

Sections 4, 5 and 9 of the README are the standing warning that **a legible
k-NN path is the part to distrust**, and this plate is made entirely of legible
paths. Nothing here shows a model traversing anything: a forward pass does not
walk a graph, and the edges are cosine adjacency in a sentence encoder, not
transitions. What the plate can support is the DISTANCE claim -- that the words
alignment moves to are far from `kill` and reached through the same few
waypoints -- and the waypoints are worth reading only because three independent
measurements agree on the distances (README section 9).

`k` is in the filename because it changes everything: at k=4 the graph is a ball
in which every question has the same answer, at k=2 it discriminates.
"""
import argparse, collections, heapq, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "substitution_shape"))
import cosines  # noqa: E402
import run  # noqa: E402

FIGS = os.path.join(HERE, "figures")


def targets(prompt, basis, src):
    """-> ({word: lineages}, stayed, n_base) from the substitution measurement."""
    import lineage_graph as LG
    E, held, bw, aw, n, miss, nonword, n_roster = LG.build(
        prompt, keep_held=True, words_only=True, basis=basis)
    out = {t: c for (s, t), c in E.items() if s == src}
    return out, out.pop(src, 0), bw.get(src, 0)


def tree(words, W, ids, src, dsts, k, min_cos=None):
    """-> (parent, hops, step) under: fewest hops, then greatest summed cosine.

    Lexicographic Dijkstra on (hops, -sum cos). `heapq` orders the tuple, and
    the third element is the path itself so equal keys break alphabetically.

    **TWO INDICES, AND CONFUSING THEM SILENTLY PRODUCES A FINDING.**
    `cosines.space` returns `W` indexed by TOKEN ID for the llama spaces (it
    hands back the whole embedding matrix) and by POSITION for bge (it builds
    one row per candidate). `run.graph` needs the former to gather rows;
    everything downstream -- `adj`, `S`, `best` -- is the latter, because
    `graph` re-indexes as it gathers. This function took one index and used it
    for both, which was correct for bge and read arbitrary rows of a 128k
    matrix for llama. It produced clean, plausible, entirely fictional plates,
    including a `kill` component of `{kil, kill, le}` that looked like proof
    the unembedding follows spelling. `ids` in, positions out, and the two are
    never the same variable again.
    """
    adj, S = run.graph(words, ids, W, k, min_cos)
    pos = {w: i for i, w in enumerate(words)}
    s = pos[src]
    best = {}
    q = [(0, 0.0, (s,))]
    while q:
        h, negc, path = heapq.heappop(q)
        v = path[-1]
        if v in best:
            continue
        best[v] = (h, -negc, path)
        for u in sorted(adj[v]):
            if u not in best:
                heapq.heappush(q, (h + 1, negc - float(S[v, u]), path + (u,)))
    return best, S


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prompt", default=run.FIG2)
    ap.add_argument("--from", dest="src", default="kill")
    ap.add_argument("--basis", default="argmax", choices=("argmax", "faller", "crossing"))
    ap.add_argument("--space", default="bge",
                    choices=("bge", "llama", "llama_unembed",
                             "llama_resid_mean", "llama_resid23",
                             "llama_resid_wide", "llama_resid_verb"))
    ap.add_argument("--k", type=int, default=2)
    ap.add_argument("--min-lineages", type=int, default=1)
    #: the full above-theta candidate list, fragments and all
    #: drop a candidate that is a strict prefix of another and N times
    #: rarer -- `bur` between `burn`/`burst`/`bury`. See run.candidate_words.
    #: an edge must be among the node's k nearest AND clear this cosine
    ap.add_argument("--min-cos", type=float, default=None)
    ap.add_argument("--clean", action="store_true")
    ap.add_argument("--exclude", default="",
                    help="comma-separated words to remove as possible nodes")
    ap.add_argument("--ranksep", type=float, default=0.08)
    ap.add_argument("--node-height", type=float, default=0.10)
    ap.add_argument("--prefix-ratio", type=float, default=0.0)
    #: residual spaces only: which rung of the ladder to read
    ap.add_argument("--stage", default="base",
                    choices=("base", "sft", "dpo", "rlvr"))
    ap.add_argument("--raw", action="store_true",
                    help="no dictionary/length/case filter: let the path run "
                         "through subwords")
    a = ap.parse_args(argv)

    dsts, stayed, n_base = targets(a.prompt, a.basis, a.src)
    drop = {w: c for w, c in dsts.items() if c < a.min_lineages}
    dsts = {w: c for w, c in dsts.items() if c >= a.min_lineages}
    print("PROMPT %r   basis=%s   from %r" % (a.prompt, a.basis, a.src))
    print("  %d lineages have %r at the base arm; %d keep it"
          % (n_base, a.src, stayed))
    print("  destinations: %s"
          % ", ".join("%s %d" % kv for kv in sorted(dsts.items(), key=lambda x: -x[1])))
    if drop:
        print("  dropped below --min-lineages %d: %s"
              % (a.min_lineages, ", ".join(sorted(drop))))

    words, W, ids = cosines.space(a.space, a.prompt, filtered=not a.raw,
                                  prefix_ratio=a.prefix_ratio,
                                  stage=a.stage)
    #: **A HAND EXCLUSION IS LEGITIMATE ONLY FOR A KIND ERROR, AND MUST BE
    #: VISIBLE.** Removing a word because it is not the sort of thing the
    #: vocabulary is supposed to contain -- a NOUN in a verb vocabulary,
    #: `vandal` or `crime` -- is a correction to the filter. Removing a word
    #: because the route through it reads badly is manufacturing the corridor,
    #: which is what this folder keeps catching itself at. The flag exists for
    #: the first and the excluded words go in the FILENAME so a plate can
    #: never quietly differ from its unpruned twin.
    #:
    #: `vandal` reaches the verb vocabulary only through the 47 above-theta
    #: candidates admitted wholesale to keep `avenge`, `gouge`, `lunge`,
    #: `pummel` and `lynch`, which WordNet has no verb sense for. It is the
    #: cost of that exemption, not a failure of the verb test.
    if a.exclude:
        drop = {w.strip() for w in a.exclude.split(",") if w.strip()}
        missing = drop - set(words)
        if missing:
            print("  --exclude: not in this vocabulary anyway: %s"
                  % ", ".join(sorted(missing)))
        keep = [w for w in words if w not in drop]
        if a.src not in keep:
            raise SystemExit("--exclude removed the source word %r" % a.src)
        print("  --exclude: %d words removed, %d remain"
              % (len(words) - len(keep), len(keep)))
        ids = {w: ids[w] for w in keep}
        words = keep
    #: `ids` gathers rows out of W; `idx` addresses everything graph-side.
    idx = {w: i for i, w in enumerate(words)}
    missing = [w for w in list(dsts) + [a.src] if w not in idx]
    if missing:
        raise SystemExit("not in the %s vocabulary: %s" % (a.space, ", ".join(missing)))
    best, S = tree(words, W, ids, a.src, dsts, a.k, a.min_cos)

    #: mass on a node = lineages of every destination whose route passes it
    mass = collections.Counter()
    paths, unreachable = {}, {}
    for w, c in dsts.items():
        #: **AN UNREACHABLE DESTINATION IS A RESULT, NOT A CRASH.** In bge at
        #: k=2 every candidate is in one component; in llama's spaces the graph
        #: fragments, and a destination in another component means there is no
        #: chain of connections to it AT ALL in that space -- which is the
        #: strongest possible version of the answer and must be reported,
        #: not raised.
        if idx[w] not in best:
            unreachable[w] = c
            continue
        h, tot, path = best[idx[w]]
        paths[w] = [words[i] for i in path]
        for i in path:
            mass[words[i]] += c
    if unreachable:
        print("  NOT REACHABLE from %r in this space at k=%d (separate "
              "component): %s"
              % (a.src, a.k, ", ".join("%s (%d lineages)" % kv
                                       for kv in sorted(unreachable.items(),
                                                        key=lambda x: -x[1]))))
    dsts = {w: c for w, c in dsts.items() if w in paths}
    if not dsts:
        raise SystemExit("no destination is reachable from %r in space=%s at "
                         "k=%d; nothing to draw" % (a.src, a.space, a.k))
    for w in sorted(dsts, key=lambda w: -dsts[w]):
        print("  %-8s %2d lineages  %2d hops  %s"
              % (w, dsts[w], len(paths[w]) - 1, " -> ".join(paths[w])))

    #: **THE WAYPOINTS ARE THE POINT.** A node that is not a destination but
    #: carries mass is a word every route had to pass through.
    way = [(w, m) for w, m in mass.most_common()
           if w not in dsts and w != a.src]
    print("  waypoints by lineage mass: %s"
          % ", ".join("%s %d" % t for t in way) or "  (none)")

    os.makedirs(FIGS, exist_ok=True)
    tag = "%s_%s_%s_k%d%s%s" % (a.src, a.basis, a.space, a.k,
                                "_min%d" % a.min_lineages if a.min_lineages > 1 else "",
                                ("_raw" if a.raw else "")
                                + ("_pfx%g" % a.prefix_ratio if a.prefix_ratio else "")
                                + ("_%s" % a.stage if a.stage != "base" else "")
                                + ("" if a.min_cos is None
                                   else "_mc%02d" % round(a.min_cos * 100))
                                + ("_clean" if a.clean else "")
                                + ("_ex%d" % len(a.exclude.split(","))
                                   if a.exclude else ""))
    base = os.path.join(FIGS, "pathways_" + tag)
    edges = set()
    for w in dsts:
        p = paths[w]
        edges.update(zip(p, p[1:]))

    #: **EVERY PLATE REPORTS ITS OWN ORTHOGRAPHY, because the drawn edges are
    #: far more alliterative than the space is.** Aggregate 3-NN agreement on
    #: a first letter runs 21-26% across bge and llama's two spaces; the edges
    #: a shortest-path tree actually draws run 36-53%, against a 9% chance
    #: baseline. Two causes, and neither is the space: a path SELECTS chaining
    #: edges, and this producer's declared tie-break -- greatest summed cosine
    #: among equal-length paths -- prefers the highest-cosine edges, which are
    #: disproportionately same-letter. So the number belongs on the plate.
    #:
    #: **A ZERO HERE WOULD BE WRONG.** English sound symbolism is real for
    #: exactly this vocabulary: `sl-`, `sm-` and `scr-` are semantically
    #: coherent clusters for violence and noise verbs, so `shriek -> scream`
    #: and `smack -> slap` are alliterative AND semantic. The discriminator is
    #: not the rate but whether spelling is doing work meaning is not, which
    #: is why the offending edges are listed rather than only counted.
    ch1 = [(x, y) for x, y in edges if x[0] == y[0]]
    ch2 = [(x, y) for x, y in edges if x[:2] == y[:2]]
    lc = collections.Counter(w[0] for w in words)
    #: **TWO BASELINES, BECAUSE THEY ARE AN ORDER OF MAGNITUDE APART.** On
    #: this vocabulary chance is 9% for a shared first letter and 1.2% for a
    #: shared two-letter prefix. This block printed the first-letter chance
    #: once, next to both columns, and I read "2-prefix 7% against chance 9%"
    #: as BELOW chance and reported it that way. It is 6x chance.
    l2 = collections.Counter(w[:2] for w in words)
    nn = len(words)
    #: NOT `base` -- that name is the output path a few lines down, and
    #: shadowing it made the writer try to concatenate a float with ".dot".
    c1 = 100.0 * sum(v * (v - 1) for v in lc.values()) / (nn * (nn - 1))
    c2 = 100.0 * sum(v * (v - 1) for v in l2.values()) / (nn * (nn - 1))
    p1 = 100.0 * len(ch1) / len(edges)
    p2 = 100.0 * len(ch2) / len(edges)
    print("  ORTHOGRAPHY of the %d drawn edges: first letter %.0f%% vs chance "
          "%.0f%% (%.1fx); two-letter prefix %.0f%% vs chance %.1f%% (%.1fx)"
          % (len(edges), p1, c1, p1 / c1 if c1 else 0.0,
             p2, c2, p2 / c2 if c2 else 0.0))
    print("      same-letter edges: %s"
          % ", ".join("%s>%s" % e for e in sorted(ch1)))

    #: `--clean` is the same visual language as the bottleneck plate
    #: (`threshold.py`): words and arrows, no boxes, bold destinations, width
    #: carrying cosine, nothing labelled. Kept identical on purpose -- two
    #: plates of the same corridor under different graph constructions can
    #: only be compared if the drawing does not differ as well.
    if a.clean:
        L = ["digraph {",
             '  rankdir=TB; bgcolor="white"; ranksep=%.2f; nodesep=0.14;'
             % a.ranksep,
             '  node [shape=plaintext fontname="Arial" fontsize=9 '
             'height=%.2f width=0.01 margin="0.02,0.005"];' % a.node_height,
             '  edge [arrowsize=0.35 color="#6f757a"];']
    else:
        L = ["digraph {", '  rankdir=LR; bgcolor="white";',
             '  node [shape=box style="rounded,filled" fontname="Arial" '
             'fontsize=10 color="#999999"];',
             '  edge [fontname="Arial" fontsize=8 color="#666666"];']
    mx = max(mass.values())
    for w, m in mass.items():
        if w == a.src:
            lab = "%s\\n%d of %d keep it" % (w, stayed, n_base)
            fill, pen = "#e8e8e8", 2.0
        elif w in dsts:
            lab = "%s\\n%d of %d" % (w, dsts[w], n_base)
            fill, pen = "#cfe0f3", 1.6
        else:
            lab = w
            fill, pen = "#ffffff", 1.0
        if a.clean:
            bold = w == a.src or w in dsts
            L.append('  "%s" [label=<%s%s%s>%s];'
                     % (w, "<B>" if bold else "", w, "</B>" if bold else "",
                        "" if bold else ' fontcolor="#999999"'))
        else:
            L.append('  "%s" [label="%s" fillcolor="%s" penwidth=%.1f '
                     'fontsize=%d];' % (w, lab, fill, pen, 9 + int(5.0 * m / mx)))
    #: **WIDTH CARRIES COSINE IN CLEAN MODE, MASS IN THE OTHER.** The busy
    #: plate sized edges by lineage traffic, which is a fact about the roster;
    #: the clean plate sizes them by the link's cosine, which is a fact about
    #: the space. Two different quantities under one visual channel, so they
    #: must not be mixed on one plate.
    cv = [float(S[idx[x], idx[y]]) for x, y in edges]
    clo, chi = (min(cv), max(cv)) if cv else (0.0, 1.0)
    for x, y in sorted(edges):
        if a.clean:
            t = (float(S[idx[x], idx[y]]) - clo) / (chi - clo) if chi > clo else 0.5
            L.append('  "%s" -> "%s" [penwidth=%.2f];' % (x, y, 0.45 + 1.75 * t))
        else:
            w = mass[y]
            L.append('  "%s" -> "%s" [penwidth=%.2f label="%.2f"];'
                     % (x, y, 0.6 + 3.4 * w / mx, float(S[idx[x], idx[y]])))
    L.append("}")
    open(base + ".dot", "w").write("\n".join(L) + "\n")
    for ext in ("png", "pdf"):
        r = subprocess.run(["dot", "-T" + ext, "-Gdpi=300", base + ".dot",
                            "-o", base + "." + ext], capture_output=True, text=True)
        if r.returncode:
            raise SystemExit("graphviz failed: %s" % r.stderr[:300])
        print("  wrote %s.%s" % (base, ext))
    return 0


if __name__ == "__main__":
    sys.exit(main())
