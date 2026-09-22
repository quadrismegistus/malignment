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
import argparse, os, sys

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
    return {words[i]: v for i, v in out.items() if i != s}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prompt", default=run.FIG2)
    ap.add_argument("--from", dest="src", default="kill")
    ap.add_argument("--space", default="llama_resid_mean")
    ap.add_argument("--basis", default="faller")
    ap.add_argument("--stage", default="base")
    a = ap.parse_args(argv)
    import numpy as np

    dsts, stayed, nb = pathways.targets(a.prompt, a.basis, a.src)
    words, W, ids = cosines.space(a.space, a.prompt, stage=a.stage)
    pos = {w: i for i, w in enumerate(words)}
    W = W[[ids[w] for w in words]]
    S = (W @ W.T).numpy()
    B = bottlenecks(W, words, a.src)
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
    return 0


if __name__ == "__main__":
    sys.exit(main())
