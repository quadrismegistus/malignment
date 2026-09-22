"""Does the k-NN graph still hold together at k=2 or 3, and is `scream` still
reachable from `kill` when it does?

    python connectivity.py                  -> both spaces, k = 1..6
    python connectivity.py --space bge --to scream --k-max 8

## WHY

README section 8 is the finding that at k=4 the hop count carries almost no
information: diameter 7, and 35% of the vocabulary sits at exactly `scream`'s
distance. k is the knob that produced that. Lowering it is the direct test --
a sparser graph has to choose which edges are real, and if `scream` leaves
`kill`'s component while a dozen violence verbs stay in it, the neighbourhood
claim is settled without reference to any path.

**REACHABILITY AT LOW k IS THE HONEST VERSION OF THE HOP QUESTION.** "5 hops
against a median of 5" says nothing. "in the same component at k=3 and not at
k=2" says exactly where the word sits.

Note that `graph()` symmetrises, so every node has degree >= k and the graph is
never as sparse as k suggests; k=1 is a forest of mutual-nearest pairs joined
where the 1-NN relation happens to chain.
"""
import argparse, collections, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import cosines  # noqa: E402
import run  # noqa: E402

PROBE = ["scream", "shout", "cry", "shriek", "dance", "eat", "sit", "write",
         "murder", "die", "stab", "strangle", "shoot", "hurt"]


def components(adj, n):
    """-> list of sets, every node in exactly one."""
    seen, out = set(), []
    for s in range(n):
        if s in seen:
            continue
        comp, q = {s}, collections.deque([s])
        seen.add(s)
        while q:
            x = q.popleft()
            for y in adj[x]:
                if y not in seen:
                    seen.add(y)
                    comp.add(y)
                    q.append(y)
        out.append(comp)
    return out


def sweep(name, prompt, src, probe, k_max=6, centre=True):
    words, W, ids = cosines.space(name, prompt, centre)
    idx = {w: i for i, w in enumerate(words)}
    if src not in idx:
        raise SystemExit("%r not in the %s vocabulary" % (src, name))
    print("\n=== %s === %d words" % (name, len(words)))
    print("  %-3s %6s %8s %9s   %s"
          % ("k", "comps", "largest", "kill's", "hops to each probe (- = other component)"))
    for k in range(1, k_max + 1):
        adj, _S = run.graph(words, ids, W, k)
        comps = components(adj, len(words))
        mine = next(c for c in comps if idx[src] in c)
        cells = []
        for w in probe:
            if w not in idx:
                continue
            if idx[w] not in mine:
                cells.append("%s -" % w)
                continue
            p = run.shortest(adj, idx[src], idx[w])
            cells.append("%s %d" % (w, len(p) - 1))
        print("  %-3d %6d %8d %9d   %s"
              % (k, len(comps), max(len(c) for c in comps), len(mine),
                 ", ".join(cells)))
        #: **WHEN THE COMPONENT IS SMALL ENOUGH TO READ, READ IT.** A hop
        #: count says how far; the membership says what the neighbourhood is
        #: made of, and at k=1 that is the whole answer to whether `scream`
        #: belongs to it.
        if len(mine) <= 20:
            print("      %s's component: %s"
                  % (src, ", ".join(sorted(words[i] for i in mine))))
    return words, idx


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prompt", default=run.FIG2)
    ap.add_argument("--from", dest="src", default="kill")
    ap.add_argument("--space", default="both", choices=("llama", "bge", "both"))
    ap.add_argument("--k-max", type=int, default=6)
    ap.add_argument("--raw", action="store_true", help="bge: uncentred too")
    a = ap.parse_args(argv)
    print("PROMPT: %r   from %r" % (a.prompt, a.src))
    for nm in (("llama", "bge") if a.space == "both" else (a.space,)):
        sweep(nm, a.prompt, a.src, PROBE, a.k_max)
        if a.raw and nm == "bge":
            print("  (uncentred)")
            sweep(nm, a.prompt, a.src, PROBE, a.k_max, centre=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
