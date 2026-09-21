"""Pool every (prompt, lineage) cell, then walk out from one word.

    python -u cell_graph.py                      # from `kill`, en
    python -u cell_graph.py --seed say --min-w 40
    python -u cell_graph.py --depth 2 --min-w 25

**THE UNIT IS THE PROMPT-LINEAGE CELL AND PROMPTS ARE POOLED AGAIN.** The other
graphs in this folder each give up one of those. `run.py` averages the fifty
lineages before picking a faller, so its unit is a prompt. `lineage_graph.py`
fixes one prompt so its unit is a lineage. Here a node is a word that some
model ranked first at some blank, and an edge is one model changing its mind at
one blank: 223,437 cells over 50 endpoint lineages and ~2,400 prompts.

So an edge weight is neither models-that-agree nor prompts-that-agree but
**cells**, and 105 on `kill -> scream` means 105 (prompt, lineage) pairs, which
could be 105 models on one prompt or one model on 105 prompts. It is the
loosest of the three units and it is the only one with enough mass to draw a
neighbourhood several steps deep.

## WHAT IS FILTERED AND WHY, BEFORE ANY OF IT IS DRAWN

    language     English only by default. Pooled, the third-heaviest edge in
                 the corpus is the Chinese 把 -> 将 (115 cells), and a graph
                 mixing scripts is two graphs.
    non-words    a token with no letter -- the blank templates
    stopwords    NLTK's list minus its `n't` fragments, as `graph.py`
    held cells   60% of cells do not change the top word at all; they are
                 counted and reported, never drawn, because a node here is a
                 word and not an arm

Unfiltered the heaviest edges are `have -> be` (736) and `he -> the` (420):
the graph is function words until the stoplist is applied.
"""
import argparse, collections, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import graph as G  # noqa: E402


def cells(lang="en"):
    """-> (Counter[edge], {edge: (lineages, prompts)}, n_cells, n_held, n_prompts)

    **A CELL COUNT ALONE CANNOT BE READ.** 105 cells on `kill -> scream` is
    105 models on one prompt or one model on 105 prompts or anything between,
    and those are different claims. The lineage and prompt counts behind each
    edge are carried alongside so the label can say which.
    """
    from malignment import ch, roster, charge
    eps, _ = roster.endpoints()
    models = sorted(set(eps) | set(eps.values()))
    q = ("SELECT model, prompt, argMax(word, p) AS top "
         "FROM {db}.twp_words_v4 "
         "WHERE rule_version=4 AND frame='' AND topup=0 AND model IN (%s) "
         "GROUP BY model, prompt"
         % ", ".join("'%s'" % m.replace("'", "\\'") for m in models))
    byp = collections.defaultdict(dict)
    for r in ch.query(q, limit_bytes=None):
        byp[r["prompt"]][r["model"]] = r["top"]
    SW = G.stopwords_en()

    def ok(w):
        return any(c.isalpha() for c in w) and w.lower() not in SW

    E, n, held = collections.Counter(), 0, 0
    who = collections.defaultdict(lambda: (set(), set()))
    keep = set()
    for p, d in byp.items():
        if lang != "both" and charge.language(p) != lang:
            continue
        for b, a in eps.items():
            if b not in d or a not in d:
                continue
            if not (ok(d[b]) and ok(d[a])):
                continue
            keep.add(p)
            n += 1
            if d[b] == d[a]:
                held += 1
            else:
                e = (d[b], d[a])
                E[e] += 1
                who[e][0].add(b)
                who[e][1].add(p)
    return E, who, n, held, len(keep)


def walk(E, seed, min_w, depth):
    """-> (edges kept, nodes) outward from `seed` over edges of weight >= min_w."""
    adj = collections.defaultdict(list)
    for (f, t), k in E.items():
        if k >= min_w:
            adj[f].append((t, k))
    seen, frontier, kept, hop = {seed}, [seed], {}, 0
    while frontier and (depth == 0 or hop < depth):
        nxt = []
        for x in frontier:
            for t, k in adj.get(x, ()):
                kept[(x, t)] = k
                if t not in seen:
                    seen.add(t)
                    nxt.append(t)
        frontier, hop = nxt, hop + 1
    return kept, seen


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed", default="kill")
    ap.add_argument("--min-w", type=int, default=20,
                    help="an edge must carry this many prompt-lineage cells")
    ap.add_argument("--depth", type=int, default=3, help="0 = full closure")
    ap.add_argument("--lang", default="en", choices=("en", "zh", "both"))
    a = ap.parse_args(argv)

    E, who, n, held, nps = cells(a.lang)
    print("%d prompt-lineage cells over %d prompts (%s), %d held (%.0f%%)"
          % (n, nps, a.lang, held, 100.0 * held / max(1, n)))
    print("  %d distinct changed edges; heaviest: %s"
          % (len(E), ", ".join("%s->%s %d" % (f, t, k)
                               for (f, t), k in E.most_common(6))))
    kept, nodes = walk(E, a.seed, a.min_w, a.depth)
    print("  from %r at weight >= %d, depth %s: %d nodes, %d edges"
          % (a.seed, a.min_w, a.depth or "full", len(nodes), len(kept)))
    out = sorted(((k, t) for (f, t), k in kept.items() if f == a.seed),
                 reverse=True)
    print("  %s ->:" % a.seed)
    for k, t in out:
        L_, P_ = who[(a.seed, t)]
        print("     %-12s %4d cells  %2d lineages  %3d prompts"
              % (t, k, len(L_), len(P_)))

    from malignment import figure as _fig
    fam, pt = _fig.pub_font(), _fig.PUB_FONT_PT
    inc = collections.Counter()
    for (f, t), k in kept.items():
        inc[f] += k
        inc[t] += k
    mx = max(kept.values())
    hi = max(inc.values())
    L = ['digraph cells {', '  splines=true; overlap=prism; overlap_scaling=-4;',
         '  graph [bgcolor="white" sep="+8" K=0.9];',
         '  node [shape=plaintext margin="0.03,0.02"];',
         '  edge [arrowsize=0.5];']
    for w in sorted(nodes):
        size = pt - 1 + 1.2 * pt * (inc[w] / hi)
        L.append('  "%s" [label="%s" fontname="%s" fontsize=%.1f '
                 'fontcolor="%s"];'
                 % (w, w, fam, size,
                    "#000000" if w == a.seed else
                    ("#1a1a1a" if inc[w] >= 0.35 * hi else "#4d4d4d")))
    for (f, t), k in sorted(kept.items(), key=lambda kv: -kv[1]):
        L.append('  "%s" -> "%s" [penwidth=%.2f color="%s" fontname="%s" '
                 'fontsize=%.1f fontcolor="#737373" label="%s"];'
                 % (f, t, 0.5 + 3.0 * (k - min_w_floor(kept)) /
                    max(1, mx - min_w_floor(kept)),
                    "#1a1a1a" if k >= 0.4 * mx else "#8c8c8c", fam, pt - 3,
                    #: cells, then how many DISTINCT lineages and prompts
                    #: produced them -- the two numbers that say whether the
                    #: cell count is breadth or repetition
                    "%d\\n%dL %dP" % (k, len(who[(f, t)][0]),
                                      len(who[(f, t)][1]))))
    L.append("}")
    base = os.path.join(HERE, "figures", "cell_graph_%s_%s_w%d_d%s"
                        % (a.lang, a.seed, a.min_w, a.depth or "full"))
    os.makedirs(os.path.dirname(base), exist_ok=True)
    open(base + ".dot", "w", encoding="utf-8").write("\n".join(L) + "\n")
    for ext in ("png", "pdf"):
        r = subprocess.run(["sfdp", "-T" + ext, "-Gdpi=300",
                            base + ".dot", "-o", base + "." + ext],
                           capture_output=True, text=True)
        if r.returncode:
            raise SystemExit("sfdp failed: %s" % r.stderr[:300])
        print("  wrote %s.%s" % (base, ext))
    return 0


def min_w_floor(kept):
    return min(kept.values()) if kept else 0


if __name__ == "__main__":
    sys.exit(main())
