"""The substitution network: every biggest-faller -> biggest-riser crossing.

    python -u graph.py                 # raw arm
    python -u graph.py --arm framed
    python -u graph.py --min-degree 1  # everything, including the leaves

`run.py` classifies each prompt's biggest faller and biggest riser and calls the
pair CROSSED when the two lines swap -- the shape `kill -> scream` names. This
draws every such pair at once, as a directed graph, one edge per (faller, riser)
with its width the number of prompts that took it.

## DEGREE > 1, AND WHAT THAT HIDES

**The full graph is a fan, not a network.** 589 crossings give 475 DISTINCT
pairs, 0.81 per crossing, so nearly every substitution happens once and never
again. Drawing all 475 would be 456 nodes of which most are leaves hanging off
a handful of common verbs, and the picture would say "there is no stable
substitution lexicon" -- which a number says better.

`--min-degree 2` keeps the nodes that appear in more than one pair. That is 152
of 456 nodes and 215 of 475 edges, and it is the part of the graph where a word
is doing something more than once. **The 260 dropped edges are not noise and
the caption says so**: they are the majority, and their existence is the main
finding about this graph.

Degree is taken ONCE on the full graph, not iterated to a k-core. Iterating
would peel the graph down to its densest centre and quietly answer a different
question; a single pass answers the one asked.

## DIRECTION IS ARITHMETIC, NOT JUDGEMENT

The faller lost probability base -> aligned and the riser gained it, both
measured. Neither is required to be the argmax and usually neither is -- on 51%
of crossings the top word does not change at all.
"""
import argparse, collections, csv, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, ROOT)


#: kept by `--pos content`. spaCy's open classes minus ADV, and ADV is the
#: whole argument: 102 of its 142 tokens here are `then` (36), `now` (25),
#: `only` (12), `there` (8), `just` (6), `forth` (6), `so`, `far`, `back` --
#: deictic and discourse particles that say where the sentence is standing
#: rather than what happens at the slot. **THE COST IS REAL AND IS ABOUT
#: TWELVE TOKENS**: `carefully`, `quickly`, `quietly`, `urgently`, `tightly`,
#: `accidentally` are manner adverbs and they go too. Named here rather than
#: buried, because a POS cut always throws away something it did not mean to.
CONTENT = {"VERB", "NOUN", "ADJ", "PROPN"}


def crossings(arm="raw"):
    """-> the CROSSED rows of one arm, with prompt, faller, riser."""
    p = os.path.join(HERE, "results", "by_prompt_%s.csv" % arm)
    with open(p, encoding="utf-8") as fh:
        return [r for r in csv.DictReader(fh)
                if r["crossing"] == "CROSSED" and r["faller"] and r["riser"]]


def slot_pos(rows):
    """-> {(prompt, word): POS}, tagged IN THE SLOT, not as a type.

    `malignment.pos.get_pos` tags `prompt + " " + word` and takes the last
    token, which is the position the model was predicting. **An out-of-context
    lookup is not a substitute**: its own docstring records 41.2% verbs inside
    an out-of-context "noun" band, and this corpus is mostly verbs at a blank
    after a subject -- exactly where a type-level tagger reads `kiss`, `strike`
    and `punch` as nouns.

    Stash-backed, so the second run costs no spaCy calls.
    """
    from malignment.pos import get_pos
    byp = collections.defaultdict(set)
    for r in rows:
        byp[r["prompt"]].update([r["faller"], r["riser"]])
    tag = {}
    for p, ws in byp.items():
        for w, t in get_pos(sorted(ws), p).items():
            tag[(p, w)] = t
    return tag


def edges(arm="raw", pos="content"):
    """-> (Counter[(faller, riser)], how many crossings the POS cut removed)"""
    rows = crossings(arm)
    if pos == "all":
        return collections.Counter((r["faller"], r["riser"]) for r in rows), 0
    tag = slot_pos(rows)
    keep = [r for r in rows
            if tag[(r["prompt"], r["faller"])] in CONTENT
            and tag[(r["prompt"], r["riser"])] in CONTENT]
    return (collections.Counter((r["faller"], r["riser"]) for r in keep),
            len(rows) - len(keep))


def induced(w, min_degree=2, min_weight=3):
    """-> (kept edges, node degree map, how much was dropped)

    **DEGREE ALONE DROPS `kill -> scream`, AND THAT IS DISQUALIFYING.** Degree
    counts DISTINCT PARTNERS, so a word that is only ever the substitute for
    one other word has degree 1 however many prompts took the pair. `scream`
    rises from `kill` and from nothing else: degree 1, dropped. So is
    `said -> only`, which at 12 prompts is the HEAVIEST EDGE IN THE GRAPH.

        said  -> only    12 prompts   only  degree 1
        kill  -> scream   7           scream degree 1
        went  -> made     4           made   degree 1
        marry -> spend    3           spend  degree 1

    A filter that removes the example the figure is named after is measuring
    the wrong thing. An edge is therefore kept if BOTH endpoints are busy
    (degree >= `min_degree`) OR the edge itself is heavy (>= `min_weight`
    prompts) -- connectedness or weight, either qualifies. `--min-weight 0`
    turns the second clause off and gives the pure degree filter.
    """
    deg = collections.Counter()
    for (f, t) in w:
        deg[f] += 1
        deg[t] += 1
    busy = {x for x, d in deg.items() if d >= min_degree}
    E = {(f, t): n for (f, t), n in w.items()
         if (f in busy and t in busy) or (min_weight and n >= min_weight)}
    return E, deg, (len(w) - len(E), len(deg) - len({x for e in E for x in e}))


def dot(E, deg, arm, drop):
    from malignment import figure as _fig
    fam, pt = _fig.pub_font(), _fig.PUB_FONT_PT
    mx = max(E.values())
    #: **NOT `dot`.** This graph has cycles (a word falls on one prompt and
    #: rises on another), and a hierarchical layout answers a cyclic graph by
    #: stretching it: `dot -Grankdir=LR` returned 2217 x 12263 px, a ribbon
    #: forty times taller than wide and unreadable at any print size. A
    #: force-directed engine is the right tool for a graph with no levels.
    L = ['digraph subs {', '  splines=true; overlap=prism; overlap_scaling=-4;',
         '  graph [bgcolor="white" sep="+6" K=0.7 repulsiveforce=1.2];',
         '  node [shape=plaintext fontname="%s" fontsize=%g '
         'margin="0.02,0.01"];' % (fam, pt - 2),
         '  edge [fontname="%s" fontsize=%g arrowsize=0.45];' % (fam, pt - 3)]
    #: a node that only ever falls, only ever rises, or does both. The third
    #: class is the one worth seeing: a word alignment moves INTO on one prompt
    #: and OUT OF on another, which a bipartite drawing would make invisible.
    fell = {f for f, _ in E}
    rose = {t for _, t in E}
    for x in sorted(fell | rose):
        both = x in fell and x in rose
        col = "#000000" if both else ("#404040" if x in fell else "#737373")
        L.append('  "%s" [label="%s" fontcolor="%s"%s];'
                 % (x, x, col, ' fontname="%s-Bold"' % fam if both else ""))
    for (f, t), n in sorted(E.items(), key=lambda kv: -kv[1]):
        L.append('  "%s" -> "%s" [penwidth=%.2f color="%s"];'
                 % (f, t, 0.5 + 2.2 * (n - 1) / max(1, mx - 1),
                    "#1a1a1a" if n >= 3 else "#8c8c8c"))
    L.append("}")
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arm", default="raw", choices=("raw", "framed"))
    ap.add_argument("--pos", default="content", choices=("content", "all"),
                    help="content: keep a crossing only when BOTH words are "
                         "VERB/NOUN/ADJ/PROPN in the slot")
    ap.add_argument("--min-degree", type=int, default=1)
    ap.add_argument("--min-weight", type=int, default=3,
                    help="keep an edge this heavy whatever its endpoints' "
                         "degree; 0 for the pure degree filter")
    ap.add_argument("--engine", default="sfdp",
                    choices=("dot", "neato", "sfdp", "fdp"))
    a = ap.parse_args(argv)

    w, cut = edges(a.arm, a.pos)
    E, deg, (de, dn) = induced(w, a.min_degree, a.min_weight)
    nodes = {x for e in E for x in e}
    print("%s arm, pos=%s: %d crossings -> %d distinct pairs%s"
          % (a.arm, a.pos, sum(w.values()), len(w),
             "; the POS cut dropped %d crossings" % cut if cut else ""))
    print("  degree >= %d keeps %d edges and %d nodes; dropped %d edges, %d nodes"
          % (a.min_degree, len(E), len(nodes), de, dn))
    rep = sorted(((n, f, t) for (f, t), n in E.items()), reverse=True)[:8]
    print("  heaviest: " + ", ".join("%s->%s %d" % (f, t, n) for n, f, t in rep))

    src = dot(E, deg, a.arm, (de, dn))
    #: **EVERY FILTER THAT CHANGES THE PICTURE CHANGES THE NAME.** Four
    #: combinations of --pos and --min-degree were written to one filename
    #: earlier in this session and each silently replaced the last; the same
    #: defect cost a figure in `fig3_osgood` the same afternoon.
    base = os.path.join(HERE, "figures", "substitution_graph_%s%s%s"
                        % (a.arm, "" if a.pos == "content" else "_allpos",
                           "" if a.min_degree <= 1 else "_deg%d" % a.min_degree))
    os.makedirs(os.path.dirname(base), exist_ok=True)
    open(base + ".dot", "w", encoding="utf-8").write(src + "\n")
    for ext in ("png", "pdf"):
        r = subprocess.run([a.engine, "-T" + ext, "-Gdpi=300",
                            base + ".dot", "-o", base + "." + ext],
                           capture_output=True, text=True)
        if r.returncode:
            raise SystemExit("%s failed: %s" % (a.engine, r.stderr[:400]))
        print("  wrote %s.%s" % (base, ext))
    return 0


if __name__ == "__main__":
    sys.exit(main())
