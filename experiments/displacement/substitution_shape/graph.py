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

#: NLTK's `n't` remnants, which are tokenizer debris and not stopwords of
#: English. **TWO OF THEM ARE REAL WORDS AND ONE IS IN THIS GRAPH**: `won`
#: is in NLTK's list only because "won't" splits to `wo` + `n't` in some
#: tokenizers, and `won` the past of `win` is a node here with its own edges.
#: `don` likewise. Removing the whole set from the stoplist costs nothing --
#: `couldn` and `didn` are not words either way and carry one edge between
#: them -- and it stops the filter deleting a verb for a spelling coincidence.
_FRAGMENTS = {"ain", "aren", "couldn", "didn", "doesn", "don", "hadn", "hasn",
              "haven", "isn", "ll", "mightn", "mustn", "needn", "re", "shan",
              "shouldn", "ve", "wasn", "weren", "won", "wouldn"}


def stopwords_en():
    """NLTK's English stoplist, minus its contraction fragments. -> set

    198 entries in, 176 out. What it removes from this graph is mostly `have`
    and its forms, which under the deployment frame is the single largest hub:
    `have -> need` (10 prompts), `-> contact` (6), `-> consider` (6),
    `-> escalate` (5). **THAT IS A QUARTER OF THE FRAMED ARM AND IT IS NOT
    NOISE** -- it is "have them stop" becoming "contact them", a construction
    change rather than a lexical substitution. Dropping it is defensible and
    it is a DECISION, so it is named here and reversible with `--keep-stop`.
    """
    from nltk.corpus import stopwords
    return set(stopwords.words("english")) - _FRAGMENTS


def crossings(arm="raw", basis="crossing"):
    """-> rows of one arm carrying `faller` and `riser` under the chosen basis.

    **TWO DIFFERENT QUESTIONS, NOT TWO VIEWS OF ONE.**

        crossing   the biggest faller and the biggest riser, on the prompts
                   where the two lines SWAP. Neither need be the top word and
                   usually neither is. 589 prompts raw.
        argmax     the base arm's top word and the aligned arm's top word, on
                   the prompts where the top word CHANGED. 570 prompts raw.
        strict     every condition this corpus can impose at once: the lines
                   swap, the faller IS the base argmax, the riser IS the
                   aligned argmax, and the single top riser absorbs at least
                   half the mass the prompt lost. 89 prompts raw, 70 pairs.

    **AND `strict` STILL DOES NOT ESTABLISH SUBSTITUTION.** A distribution sums
    to one, so when one word falls another must rise; conservation is true by
    definition and no arithmetic over these two distributions can distinguish
    "y replaced x" from "x fell and y rose". `absorb_1` is a ratio of
    aggregates, not a traced flow, and there is no counterfactual anywhere in
    this corpus. What `strict` buys is that every rival reading available
    WITHIN a prompt has been excluded; what it cannot buy is the direction of
    a causal claim. The evidence that would is REPLICATION ACROSS LINEAGES --
    the same pair chosen independently by many models -- which this file
    cannot see, because `run.py` averages the fifty lineages before it picks
    a faller. See `substitution_replicated.py`.

    Nearly the same count and NOT the same population: `run.py` records that
    51% of crossings happen with the top word unchanged, so the two overlap
    far less than their sizes suggest. Both are real and neither contains the
    other -- the crossing asks what moved most, the argmax asks what the model
    would actually say.

    **AND THE ARGMAX BASIS IS NOT A SUBSTITUTION CLAIM.** Of its 570 raw
    prompts only 62 are classified `MOVED_SUBSTITUTION`; 313 are
    `MOVED_PROMOTION`, where the new top word was already present and merely
    rose past the old one. An edge here means "the top word changed from x to
    y", which is weaker than "y replaced x".
    """
    p = os.path.join(HERE, "results", "by_prompt_%s.csv" % arm)
    with open(p, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if basis in ("crossing", "strict"):
        out = [r for r in rows
               if r["crossing"] == "CROSSED" and r["faller"] and r["riser"]]
        if basis == "strict":
            def yes(r, k):
                return str(r.get(k, "")).lower() in ("true", "1")
            def num(r, k):
                try:
                    return float(r[k])
                except (TypeError, ValueError):
                    return 0.0
            out = [r for r in out
                   if yes(r, "faller_is_base_argmax")
                   and yes(r, "riser_is_aligned_argmax")
                   and num(r, "absorb_1") >= 0.5]
        return out
    out = []
    for r in rows:
        b, a = r["base_top"], r["aligned_top"]
        if b and a and b != a:
            q = dict(r)
            q["faller"], q["riser"] = b, a
            out.append(q)
    return out


def slot_lemma(rows):
    """-> {(prompt, word): lemma}, lemmatised IN THE SLOT.

    Only the words that actually appear as a faller or riser are lemmatised,
    not every rated candidate: that is ~6,400 (prompt, word) pairs instead of
    ~115,000, and the rest are never drawn. Stash-backed, so reruns are free.
    """
    from malignment.pos import get_lemma
    byp = collections.defaultdict(set)
    for r in rows:
        byp[r["prompt"]].update([r["faller"], r["riser"]])
    out = {}
    for p, ws in byp.items():
        for w, l in get_lemma(sorted(ws), p).items():
            out[(p, w)] = l
    return out


def modal_lemma(rows):
    """-> {surface: lemma}, the most common slot lemma across its own prompts.

    **A SURFACE FORM GETS ONE LEMMA FOR THE WHOLE GRAPH**, because a node is
    one node. Taking the per-slot lemma edge by edge would let `saw` be `see`
    on one arrow and `saw` on another, which is correct about the language and
    incoherent as a drawing. The modal choice is recorded rather than assumed;
    disagreements are reported by `lemma_report`.
    """
    L = slot_lemma(rows)
    acc = collections.defaultdict(collections.Counter)
    for (p, w), l in L.items():
        acc[w][l] += 1
    return {w: c.most_common(1)[0][0] for w, c in acc.items()}


def lemma_report(rows):
    """Surfaces whose slot lemma is not constant, and the merges performed."""
    L = slot_lemma(rows)
    acc = collections.defaultdict(collections.Counter)
    for (p, w), l in L.items():
        acc[w][l] += 1
    split = {w: dict(c) for w, c in acc.items() if len(c) > 1}
    m = modal_lemma(rows)
    groups = collections.defaultdict(set)
    for w, l in m.items():
        groups[l].add(w)
    merges = {l: sorted(v) for l, v in groups.items() if len(v) > 1}
    return split, merges


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


def edges(arm="raw", pos="content", lemma=False, stop=True,
          basis="crossing"):
    """-> (Counter[(faller, riser)], how many crossings the POS cut removed)

    With `lemma`, both ends are replaced by their modal slot lemma BEFORE the
    edge is counted, so `kill`/`killed`, `stab`/`stabbed` and `punch`/`punched`
    become one node and their edges add rather than sitting in separate
    components. **A SELF-LOOP IS DROPPED**: `killed -> kill` is an inflection
    change, not a substitution, and drawing it as an edge would assert a
    movement the lemma has just declared absent.
    """
    rows = crossings(arm, basis)
    if pos != "all":
        #: "verb" is narrower than "content" and is its own choice rather than
        #: a filter applied afterwards: a crossing survives only if BOTH ends
        #: are verbs IN THEIR SLOTS. Dropping non-verb NODES after the fact
        #: would leave the edges that passed through them, which asserts a
        #: substitution between two verbs that never substituted for one
        #: another.
        keep = {"verb": {"VERB"}}.get(pos, CONTENT)
        tag = slot_pos(rows)
        rows = [r for r in rows
                if tag[(r["prompt"], r["faller"])] in keep
                and tag[(r["prompt"], r["riser"])] in keep]
    if stop:
        #: **CHECKED ON THE SURFACE AND ON THE LEMMA.** `had` and `having` are
        #: in the list and `have` is their lemma, but the reverse also happens
        #: -- a surface the list misses whose lemma it holds -- so a crossing
        #: dies if EITHER form of EITHER end is a stopword. Applied here, in
        #: the one place edges are built, so nothing downstream can walk a
        #: node this filter removed.
        SW = stopwords_en()
        lm = modal_lemma(crossings(arm, basis))
        def stopish(w):
            return w in SW or lm.get(w, w) in SW
        rows = [r for r in rows
                if not stopish(r["faller"]) and not stopish(r["riser"])]
    cut = len(crossings(arm, basis)) - len(rows)
    if not lemma:
        return collections.Counter((r["faller"], r["riser"]) for r in rows), cut
    m = modal_lemma(crossings(arm, basis))
    E = collections.Counter()
    for r in rows:
        f, t = m.get(r["faller"], r["faller"]), m.get(r["riser"], r["riser"])
        if f != t:
            E[(f, t)] += 1
    return E, cut


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


def prompt_labels(arm, E, wrap=30, basis="crossing"):
    """{(faller, riser): label} -- the prompt that produced the edge.

    **89% OF CONTENT EDGES HAVE EXACTLY ONE PROMPT**, so for most of the graph
    the prompt is not a summary of the edge, it IS the edge. Those are labelled
    in full. An edge carried by several prompts gets the shortest, marked with
    how many more there are -- picking one and saying nothing would make a
    seven-prompt edge look like a one-prompt edge.
    """
    import textwrap
    byedge = collections.defaultdict(list)
    for r in crossings(arm, basis):
        k = (r["faller"], r["riser"])
        if k in E:
            byedge[k].append(r["prompt"])
    out = {}
    for k, v in byedge.items():
        v = sorted(v, key=len)
        txt = "\\n".join(textwrap.wrap(v[0], wrap)[:3])
        if len(v) > 1:
            txt += "\\n(+%d more)" % (len(v) - 1)
        out[k] = txt.replace('"', "'")
    return out


def dot(E, deg, arm, drop, labels=None):
    from malignment import figure as _fig
    fam, pt = _fig.pub_font(), _fig.PUB_FONT_PT
    mx = max(E.values())
    #: **NOT `dot`.** This graph has cycles (a word falls on one prompt and
    #: rises on another), and a hierarchical layout answers a cyclic graph by
    #: stretching it: `dot -Grankdir=LR` returned 2217 x 12263 px, a ribbon
    #: forty times taller than wide and unreadable at any print size. A
    #: force-directed engine is the right tool for a graph with no levels.
    #: **A LABELLED EDGE NEEDS ROOM THE NODE DID NOT.** With prompts on the
    #: edges the drawing is no longer words joined by lines, it is words joined
    #: by paragraphs, and the spacing that suited bare arrows collides in any
    #: dense neighbourhood -- `kill` alone has fourteen labelled edges. So the
    #: separation and the spring length scale with whether labels are on.
    lab_on = bool(labels)
    L = ['digraph subs {',
         '  splines=true; overlap=prism; overlap_scaling=%d;' % (-6 if lab_on else -4),
         '  graph [bgcolor="white" sep="%s" K=%.1f repulsiveforce=%.1f];'
         % ("+12" if lab_on else "+6", 1.3 if lab_on else 0.7,
            1.5 if lab_on else 1.2),
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
        lab = ''
        if labels and (f, t) in labels:
            #: the prompt sits ON the edge, in the lighter grey and two points
            #: down, so the words stay the figure and the frames are the gloss
            lab = (' label="%s" fontcolor="#8c8c8c" labelfloat=false'
                   % labels[(f, t)])
        L.append('  "%s" -> "%s" [penwidth=%.2f color="%s"%s];'
                 % (f, t, 0.5 + 2.2 * (n - 1) / max(1, mx - 1),
                    "#1a1a1a" if n >= 3 else "#8c8c8c", lab))
    L.append("}")
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arm", default="raw", choices=("raw", "framed"))
    ap.add_argument("--pos", default="content",
                    choices=("content", "verb", "all"),
                    help="content: keep a crossing only when BOTH words are "
                         "VERB/NOUN/ADJ/PROPN in the slot")
    ap.add_argument("--min-degree", type=int, default=1)
    ap.add_argument("--min-weight", type=int, default=3,
                    help="keep an edge this heavy whatever its endpoints' "
                         "degree; 0 for the pure degree filter")
    ap.add_argument("--basis", default="crossing",
                    choices=("crossing", "argmax", "strict"),
                    help="crossing: biggest faller -> biggest riser where the "
                         "lines swap. argmax: base top word -> aligned top "
                         "word where the top word changed.")
    ap.add_argument("--keep-stop", action="store_true",
                    help="do NOT drop NLTK stopwords (they are dropped by "
                         "default, which removes the framed `have` hub)")
    ap.add_argument("--lemma", action="store_true",
                    help="merge surface forms into their slot lemma")
    ap.add_argument("--label-prompts", action="store_true",
                    help="put the prompt that produced each edge on it")
    ap.add_argument("--engine", default="sfdp",
                    choices=("dot", "neato", "sfdp", "fdp"))
    a = ap.parse_args(argv)

    w, cut = edges(a.arm, a.pos, a.lemma, not a.keep_stop, a.basis)
    E, deg, (de, dn) = induced(w, a.min_degree, a.min_weight)
    nodes = {x for e in E for x in e}
    print("%s arm, pos=%s: %d crossings -> %d distinct pairs%s"
          % (a.arm, a.pos, sum(w.values()), len(w),
             "; the POS cut dropped %d crossings" % cut if cut else ""))
    print("  degree >= %d keeps %d edges and %d nodes; dropped %d edges, %d nodes"
          % (a.min_degree, len(E), len(nodes), de, dn))
    rep = sorted(((n, f, t) for (f, t), n in E.items()), reverse=True)[:8]
    print("  heaviest: " + ", ".join("%s->%s %d" % (f, t, n) for n, f, t in rep))

    src = dot(E, deg, a.arm, (de, dn),
              prompt_labels(a.arm, E, basis=a.basis)
              if a.label_prompts else None)
    #: **EVERY FILTER THAT CHANGES THE PICTURE CHANGES THE NAME.** Four
    #: combinations of --pos and --min-degree were written to one filename
    #: earlier in this session and each silently replaced the last; the same
    #: defect cost a figure in `fig3_osgood` the same afternoon.
    base = os.path.join(HERE, "figures", "substitution_graph_%s%s%s"
                        % (a.arm + ("" if a.basis == "crossing"
                                    else "_" + a.basis),
                           "" if a.pos == "content" else "_allpos",
                           ("_stop" if a.keep_stop else "")
                           + ("_lemma" if a.lemma else "")
                           + ("" if a.min_degree <= 1 else "_deg%d" % a.min_degree)))
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
