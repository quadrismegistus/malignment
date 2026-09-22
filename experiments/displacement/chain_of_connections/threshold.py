"""Edges by COSINE CUTOFF instead of k nearest, so that path length is metric.

    python threshold.py                     bottlenecks + a threshold sweep
    python threshold.py --space bge

## WHY (RH)

A k-NN graph gives every node degree >= k, so an edge means "relatively
nearest", not "actually similar". In a sparse region it manufactures edges
between things that are not close. §12.5 is the consequence: at k=2 the control
`eat` and the substitute `scream` land on the SAME eight hops from `kill` while
their cosines are 1.5 sd apart, so length carried no information.

Under a cutoff an edge means the similarity cleared a bar. Dense regions stay
connected, sparse ones genuinely disconnect, and length is metric again.

## THE THRESHOLD-FREE FORM: THE BOTTLENECK

Choosing a cutoff is choosing an answer, so this reports the quantity that does
not need one. The BOTTLENECK from `kill` to a word is

    max over all paths of ( min cosine along the path )

i.e. the highest cutoff at which the two are still connected -- the weakest
link on the best available route. It is the widest-path / minimax-path problem
and Kruskal gives every target's answer in one pass: sort all pairs by
descending cosine, union them, and record the cosine at which each target first
joins `kill`'s component. That edge is the bottleneck.

**A BOTTLENECK IS A COSINE, SO IT IS COMPARABLE TO THE DIRECT COSINE**, which
is what makes it answer the question a hop count could not: if `kill -> scream`
bottlenecks far below `kill -> eat`, then `scream` is genuinely harder to reach
and the chain's difficulty is a number rather than an artefact of k.
"""
import argparse, collections, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE) + "/substitution_shape")
sys.path.insert(0, HERE)
import cosines  # noqa: E402
import pathways  # noqa: E402
import run  # noqa: E402

#: the same four carried through every table in this folder
CONTROLS = ["eat", "dance", "sit", "write"]


class DSU:
    def __init__(self, n):
        self.p = list(range(n))

    def find(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        self.p[ra] = rb
        return True


def bottlenecks(W, words, src):
    """-> {word: (bottleneck cosine, hops)} = min edge on the MST path.

    **THE FIRST VERSION OF THIS WAS WRONG AND ITS NUMBERS LOOKED FINE.** It
    walked edges in descending order and recorded a bottleneck for the two
    ENDPOINTS whenever one of them was in `src`'s component. But a union merges
    a whole component: every node in it joins `src` at that cosine, not just
    the endpoint. The rest were picked up by some later, LOWER edge, so every
    non-endpoint bottleneck was an underestimate -- and the table printed
    plausible values throughout.

    The correct statement is the standard one: build the MAXIMUM spanning tree,
    and the bottleneck from `src` to `x` is the MINIMUM edge on the unique tree
    path between them. Kruskal gives the tree; one BFS gives every answer.
    """
    import collections
    import numpy as np
    n = len(words)
    S = (W @ W.T).numpy()
    iu = np.triu_indices(n, 1)
    order = np.argsort(-S[iu])
    ri, ci, vv = iu[0][order], iu[1][order], S[iu][order]
    d = DSU(n)
    adj = collections.defaultdict(list)
    kept = 0
    for a, b, v in zip(ri, ci, vv):
        if d.union(int(a), int(b)):
            adj[int(a)].append((int(b), float(v)))
            adj[int(b)].append((int(a), float(v)))
            kept += 1
            if kept == n - 1:
                break
    pos = {w: i for i, w in enumerate(words)}
    s = pos[src]
    out = {s: (float("inf"), 0)}
    q = collections.deque([s])
    while q:
        x = q.popleft()
        bx, hx = out[x]
        for y, v in adj[x]:
            if y not in out:
                out[y] = (min(bx, v), hx + 1)
                q.append(y)
    return {words[i]: v for i, v in out.items() if i != s}, adj, pos


def plot(words, adj, pos, src, dsts, B, S, base, controls, clean=False,
         height=6.5):
    """The MST corridor: the union of minimax paths, with the weak links shown.

    **THIS IS NOT THE k-NN PLATE AND MUST NOT BE READ AS ONE.** Its edges are
    maximum-spanning-tree edges, so a path here is the route whose WEAKEST link
    is as strong as possible -- not the fewest hops. It is longer than the k-NN
    plate on purpose: the k-NN plate optimises step count, which §12.5 showed
    carries no information, and this optimises the bottleneck, which does.

    The weakest edge on each route is drawn heavy and labelled, because that
    single number IS the result for that word.
    """
    parent = {pos[src]: None}
    q = collections.deque([pos[src]])
    while q:
        x = q.popleft()
        for y, _v in adj[x]:
            if y not in parent:
                parent[y] = x
                q.append(y)
    want = list(dsts) + [c for c in controls if c in pos]
    edges, keep = {}, set()
    bott = {}
    for w in want:
        if w not in pos:
            continue
        path, x = [], pos[w]
        while x is not None:
            path.append(x)
            x = parent[x]
        path.reverse()
        keep.update(path)
        lo = min(float(S[a, b]) for a, b in zip(path, path[1:])) if len(path) > 1 else 1.0
        bott[w] = lo
        for a, b in zip(path, path[1:]):
            edges[(a, b)] = float(S[a, b])
    #: TB, not LR: these corridors are 16-22 hops and the LR render came
    #: out 11,652 px wide and unreadable. A long chain is long in one
    #: dimension whichever way it is laid out; tall scrolls better than wide.
    if clean:
        #: **PUBLICATION FORM (RH): source at the BOTTOM, arrows UPWARD.**
        #: `rankdir=BT` puts `kill` at the bottom and the far end of the
        #: corridor at the top, so the plate reads as ascent out of the
        #: violence cluster. Labels are the word alone and edges carry no
        #: numbers: the lineage counts and bottleneck values belong in the
        #: table, and on a 6.5 in plate they are unreadable anyway. What
        #: SURVIVES the stripping is the encoding that needs no legend --
        #: width still tracks cosine, so the corridor visibly narrows at its
        #: weakest link, and that link is still red.
        #:
        #: Sized to fit rather than scaled to fit: a `size` cap would shrink
        #: the type along with the drawing. 17 ranks at 0.22 in a node plus
        #: 0.14 in of ranksep lands just under the 6.5 in ceiling.
        L = ["digraph {",
             '  rankdir=TB; bgcolor="white"; ranksep=%.2f; nodesep=0.14;'
             % max(0.08, min(0.20, (height - 0.3) / 40.0)),
             #: **NO BOXES (RH).** `plaintext` removes the frame and fill, so
             #: the plate is words and arrows and nothing else. Emphasis moves
             #: from a coloured box to a BOLD word, which is the same
             #: distinction carried by type rather than by furniture -- and it
             #: survives being printed in one colour, which a blue fill does
             #: not.
             '  node [shape=plaintext fontname="Arial" fontsize=9 '
             'height=0.18 margin="0.02,0.01"];',
             #: arrowheads and widths were scaled for a plate with boxes and
             #: labels; without them they dominate the short gaps between words
             '  edge [arrowsize=0.35 color="#9aa0a6"];']
    else:
        L = ["digraph {", '  rankdir=TB; bgcolor="white"; ranksep=0.30;',
         '  node [shape=box style="rounded,filled" fontname="Arial" '
         'fontsize=10 color="#999999" fillcolor="#ffffff"];',
         '  edge [fontname="Arial" fontsize=8 color="#888888"];']
    mx = max(dsts.values()) if dsts else 1
    for i in sorted(keep):
        w = words[i]
        if clean:
            #: bold marks the source and the destinations; everything else is
            #: a way station and set in the regular face
            bold = w == src or w in dsts or w in controls
            L.append('  "%s" [label=<%s%s%s>];'
                     % (w, "<B>" if bold else "", w, "</B>" if bold else ""))
            continue
        if w == src:
            lab, fill, pen = w, "#d8d8d8", 1.6
        elif w in dsts:
            lab = "%s\\n%d of %d\\nbottleneck %.3f" % (
                w, dsts[w], sum(dsts.values()), bott[w])
            fill, pen = "#cfe0f3", 1.6
        elif w in controls:
            lab = "%s\\nCONTROL\\nbottleneck %.3f" % (w, bott[w])
            fill, pen = "#f3e0cf", 1.6
        else:
            lab, fill, pen = w, "#ffffff", 1.0
        L.append('  "%s" [label="%s" fillcolor="%s" penwidth=%.1f];' % (w, lab, fill, pen))
    #: an edge is WEAK if it is the minimum on some drawn route: that is the
    #: quantity the plate exists to show, so it is the only thing emphasised
    weak = set()
    for w in want:
        if w not in pos:
            continue
        path, x = [], pos[w]
        while x is not None:
            path.append(x)
            x = parent[x]
        path.reverse()
        if len(path) > 1:
            e = min(zip(path, path[1:]), key=lambda ab: float(S[ab[0], ab[1]]))
            weak.add(e)
    #: **THICKNESS TRACKS COSINE, so a bottleneck LOOKS like one** (RH). With
    #: width proportional to the similarity of the link, the weakest edge on a
    #: route is literally the narrowest point of the corridor, and the red
    #: marking only names what the geometry already shows. Scaled over the
    #: drawn range rather than 0-1, because these cosines occupy 0.3-0.8 and a
    #: 0-1 scale would flatten every difference that matters.
    vs = list(edges.values())
    lo, hi = min(vs), max(vs)
    def width(v):
        t = (v - lo) / (hi - lo) if hi > lo else 0.5
        #: the boxed plate could carry 0.5-5.5 pt strokes; between bare words
        #: at 9 pt a 5 pt arrow reads as the subject rather than the relation
        return (0.3 + 1.6 * t) if clean else (0.5 + 5.0 * t)
    for (a, b), v in sorted(edges.items()):
        hot = (a, b) in weak
        lab = "" if clean else ' label="%.2f"%s' % (
            v, ' fontcolor="#b23a3a"' if hot else "")
        L.append('  "%s" -> "%s" [%spenwidth=%.2f color="%s"];'
                 % (words[a], words[b], lab.strip() + " " if lab else "",
                    width(v), "#b23a3a" if hot else "#9aa0a6"))
    L.append("}")
    open(base + ".dot", "w").write("\n".join(L) + "\n")
    for ext in ("png", "pdf"):
        r = subprocess.run(["dot", "-T" + ext, "-Gdpi=300", base + ".dot",
                            "-o", base + "." + ext], capture_output=True, text=True)
        if r.returncode:
            raise SystemExit("graphviz failed: %s" % r.stderr[:300])
        print("  wrote %s.%s" % (base, ext))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prompt", default=run.FIG2)
    ap.add_argument("--from", dest="src", default="kill")
    ap.add_argument("--space", default="llama_resid_mean")
    ap.add_argument("--basis", default="faller")
    ap.add_argument("--stage", default="base")
    ap.add_argument("--plot", action="store_true")
    #: the controls earn their place in the TABLE (they are the comparison);
    #: on the plate they add two long corridors that are not the subject
    ap.add_argument("--no-controls", dest="controls", action="store_false")
    #: publication form: source at the bottom, arrows up, words only
    ap.add_argument("--clean", action="store_true")
    ap.add_argument("--height", type=float, default=6.5, help="inches")
    a = ap.parse_args(argv)
    import numpy as np

    dsts, stayed, nb = pathways.targets(a.prompt, a.basis, a.src)
    words, W, ids = cosines.space(a.space, a.prompt, stage=a.stage)
    pos = {w: i for i, w in enumerate(words)}
    W = W[[ids[w] for w in words]]
    S = (W @ W.T).numpy()
    B, mstadj, mstpos = bottlenecks(W, words, a.src)
    print("PROMPT %r  space=%s stage=%s  %d candidates"
          % (a.prompt, a.space, a.stage, len(words)))
    print("\n  BOTTLENECK = highest cosine cutoff at which %r is still "
          "connected to the word" % a.src)
    print("  %-10s %9s %9s %7s %6s   %s"
          % ("word", "direct", "bottleneck", "hops", "lin", "kind"))
    rows = [(w, "destination", dsts[w]) for w in dsts] + \
           [(w, "CONTROL", 0) for w in CONTROLS if w in pos]
    for w, kind, c in sorted(rows, key=lambda t: -B.get(t[0], (-9, 0))[0]):
        if w not in B:
            print("  %-10s  unreachable" % w)
            continue
        bn, hp = B[w]
        print("  %-10s %9.3f %9.3f %7s %6s   %s"
              % (w, S[pos[a.src], pos[w]], bn, hp, c or "-", kind))

    print("\n  THRESHOLD SWEEP: components, and %r's distance to %r"
          % (a.src, "scream"))
    print("  %-7s %8s %9s %9s   %s"
          % ("cutoff", "edges", "comps", "src comp", "hops to scream / eat"))
    import collections
    for t in (0.6, 0.5, 0.45, 0.4, 0.35, 0.3, 0.25, 0.2):
        adj = collections.defaultdict(set)
        ii, jj = np.where(np.triu(S, 1) >= t)
        for x, y in zip(ii, jj):
            adj[int(x)].add(int(y))
            adj[int(y)].add(int(x))
        seen, comps = set(), 0
        sizes = {}
        for st in range(len(words)):
            if st in seen:
                continue
            comps += 1
            comp, q = {st}, collections.deque([st])
            seen.add(st)
            while q:
                x = q.popleft()
                for y in adj[x]:
                    if y not in seen:
                        seen.add(y)
                        comp.add(y)
                        q.append(y)
            for x in comp:
                sizes[x] = len(comp)
        d = {pos[a.src]: 0}
        q = collections.deque([pos[a.src]])
        while q:
            x = q.popleft()
            for y in adj[x]:
                if y not in d:
                    d[y] = d[x] + 1
                    q.append(y)
        def h(w):
            return d.get(pos[w], "-") if w in pos else "?"
        print("  %-7.2f %8d %9d %9d   scream %-4s eat %-4s"
              % (t, sum(len(v) for v in adj.values()) // 2, comps,
                 sizes[pos[a.src]], h("scream"), h("eat")))
    if a.plot:
        figs = os.path.join(HERE, "figures")
        os.makedirs(figs, exist_ok=True)
        tag = "bottleneck_%s_%s_%s%s" % (a.src, a.basis, a.space,
                                         "" if a.stage == "base" else "_" + a.stage)
        plot(words, mstadj, mstpos, a.src, dsts, B, S,
             os.path.join(figs, tag + ("" if a.controls else "_nocontrols")
                          + ("_clean" if a.clean else "")),
             CONTROLS if a.controls else [], a.clean, a.height)
    return 0


if __name__ == "__main__":
    sys.exit(main())
