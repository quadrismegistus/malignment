"""The permitted channel network as a layered graph, with the layer statistic that justifies the layout.

    python channel_graph.py                          # defaults: charge>=4, all reachable edges
    python channel_graph.py --spec-min 1.3           # prune for legibility
    dot -Tpdf results/channel_graph.dot -o results/channel_graph.pdf

## WHY THE LAYOUT IS A MEASUREMENT AND NOT A PICTURE

A force-directed drawing of 287 edges is a hairball and every arrangement of it
is a choice nobody can check. This lays nodes out by BFS depth from a SEED SET
defined by a threshold that already exists in this folder: `run.py`'s dose bands
call 4-5 "strong", so `--charge-min 4` is a stated cut rather than an aesthetic
one, and everything downstream is derived rather than arranged.

The layout then earns its axis, because the layer means are the finding:

    depth 0   the seeds themselves          charge 4.92
    depth 1   one permitted substitution    charge 2.67
    depth 2                                 charge 2.59
    depth 3+  nine nodes total              noise

**The whole descent happens at the first move.** Displacement is not a ladder of
progressively milder substitutes; it is one jump off the charged field into a
flat network of ordinary vocabulary.

## WHAT THE DRAWING IS HONEST ABOUT, AND WHAT IT IS NOT

Honest at the level of LAYERS. Not at the level of ARROWS: preferred edges run
downhill in charge 69.5% of the time against a 68.0% +- 1.6 shuffle of which
target attaches to which source, so a single arrow is 0.9 sd from chance and
must not be read as a measured drop. The per-layer means are printed into the
graph and into stdout so the caption can cite the run that drew it.

Both numbers are emitted by `--stats` on every run, because the folder's
recurring defect is a figure whose caption carries a number no producer printed.

## CHARGE PER FIELD

`charge.scene(prompt)` rates a word IN CONTEXT, so a field's charge is the mean
over every (prompt, word) observation whose word carries that field at fine
grain, with a word's mass NOT divided across its senses -- this is a property of
the field's vocabulary, not of moved mass, so `_spread`'s division does not
apply. Cached to `results/field_charge.json`; delete it to rebuild.
"""

import argparse
import collections
import csv
import json
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)

TABLE = os.path.join(HERE, "results", "channel_table.csv")
CACHE = os.path.join(HERE, "results", "field_charge%s.json")
OUT = os.path.join(HERE, "results", "channel_graph.dot")

#: USAS top-level domains. `label()` resolves the FULL code, so a bare letter
#: from --grain letter comes back as the letter itself and the node reads "Q /
#: Q". Same map as field_matrix.py, kept in sync by hand -- it is 21 entries
#: and it has not changed since USAS did.
LETTERS = {"A": "general/abstract", "B": "the body", "C": "arts",
           "E": "emotion", "F": "food", "G": "govt", "H": "architecture",
           "I": "money", "K": "entertainment", "L": "life & living",
           "M": "movement", "N": "numbers", "O": "substances",
           "P": "education", "Q": "linguistic acts", "S": "social",
           "T": "time", "W": "world", "X": "psychological", "Y": "science",
           "Z": "grammar/names"}


def letter_name(code):
    """`E-` -> "emotion [-]". Empty when the code is not a bare signed letter."""
    base, mod = code[:1], code[1:]
    if base not in LETTERS or mod.strip("+-"):
        return ""
    return "%s [%s]" % (LETTERS[base], mod) if mod else LETTERS[base]


def field_charge(grain="fine", rebuild=False, use_senses=False,
                 drop_fragments=False, abstain="fallback", pos_keep=None):
    """{field: [mean_charge, n_observations, mean_lift]} over rated words.

    Keyed by GRAIN and cached separately: a letter-grain run pools `L1-` and
    `L2` into `L`, so its charges are a different quantity from the fine ones
    and the two must never share a file.
    """
    #: the cache key carries the CODING, not just the grain. A field's charge
    #: is the mean rating of the words carrying it, so disambiguation changes
    #: which words those are and therefore the number. Node colours computed
    #: under one coding beside edges computed under another would be a figure
    #: whose two halves describe different tables.
    #: POS belongs in the key for the same reason the coding does: restricting
    #: the flow to verbs and then colouring nodes by a charge computed over all
    #: parts of speech would describe two different populations in one figure.
    cache = CACHE % (("" if grain == "fine" else "_" + grain)
                     + ("_senses" if use_senses else "")
                     + ("_" + "".join(pos_keep).lower() if pos_keep else ""))
    if os.path.exists(cache) and not rebuild:
        return json.load(open(cache))
    from malignment import charge
    from adjacency import senses_of
    lifts = charge.lifts()
    acc, lac = collections.defaultdict(list), collections.defaultdict(list)
    prompts = charge.prompts("en")
    tagger = None
    if pos_keep:
        from malignment import pos as _P
        tagger = _P
    for p in prompts:
        lf = lifts.get(p)
        sc = charge.scene(p) or {}
        tags = {}
        if pos_keep and sc:
            try:
                tags = tagger.get_pos(sorted(sc), p, lang="en")
            except Exception:
                tags = {}
        for w, r in sc.items():
            if pos_keep and tags.get(w) not in pos_keep:
                continue
            for f in senses_of(w, grain, p, use_senses, abstain, drop_fragments):
                acc[f].append(r)
                if lf is not None:
                    lac[f].append(lf)
    out = {f: [st.mean(v), len(v),
               (st.mean(lac[f]) if lac.get(f) else None)] for f, v in acc.items()}
    json.dump(out, open(cache, "w"))
    print("  built %s-grain field charge over %d prompts, %d fields -> %s"
          % (grain, len(prompts), len(out), cache))
    return out


def node_words(rows, n=4):
    """{field: [example words]} from the table's own `examples` column.

    A field's words are the fallers observed LEAVING it plus the risers
    observed ARRIVING in it, since both are words USAS filed under that code.
    Weighted by the lineage counts the examples column already carries, so a
    pair thirty models agree on outranks one model's idiosyncratic jump -- the
    same convention `--examples` ranks by, not a second one invented here.

    Read off the table rather than recomputed, so the words in a node are the
    words in the row a reader can look up.
    """
    acc = collections.defaultdict(collections.Counter)
    for r in rows:
        for part in (r.get("examples") or "").split(";"):
            part = part.strip()
            if "->" not in part or "(" not in part:
                continue
            pair, _, cnt = part.rpartition("(")
            try:
                w = int(cnt.rstrip(") "))
            except ValueError:
                continue
            fall, _, rise = pair.strip().partition("->")
            acc[r["source"]][fall.strip()] += w
            acc[r["target"]][rise.strip()] += w
    return {f: [w for w, _ in c.most_common(n)] for f, c in acc.items()}


def centrality(rows, how="pagerank"):
    """{field: score} on the PREFERRED digraph, edges weighted by spec.

    `degree` counts channels and says nothing about direction, so a field that
    only ever gives and one that only ever receives score alike. These do not:

      pagerank     where a walker following preferred channels ENDS UP.
                   Destination-ness under the graph's own flow.
      authority    HITS: pointed to by fields that themselves point widely.
      indegree     arrivals only, weighted. The blunt version of the same idea.
      betweenness  how often a field lies ON a shortest path. Waystation-ness,
                   which is a DIFFERENT question from destination-ness -- a
                   pure sink scores zero here and top on pagerank.

    Weighted by `spec - 1` (floored at 0.01), not by spec: an edge at chance
    should contribute nothing, and spec is a ratio against 1, not against 0.
    """
    import networkx as nx
    g = nx.DiGraph()
    for r in rows:
        w = max(0.01, float(r["spec"]) - 1.0)
        g.add_edge(r["source"], r["target"], weight=w)
    if how == "pagerank":
        return nx.pagerank(g, weight="weight")
    if how == "authority":
        return nx.hits(g, max_iter=500)[1]
    if how == "betweenness":
        return nx.betweenness_centrality(g, weight=None)
    if how == "indegree":
        return {n: sum(d["weight"] for _, _, d in g.in_edges(n, data=True))
                for n in g}
    return {n: g.degree(n) for n in g}


def _hex(c, mono=False):
    """Charge 1-7 to a fill. Blue-to-red normally; a grey ramp under `mono`.

    **THE GREY RAMP IS NOT A DESATURATED COPY OF THE COLOUR ONE.** The
    blue-red scale is diverging and carries its meaning in hue, so converting
    it to luminance sends both ends to a similar mid-grey and the hottest and
    coolest fields become indistinguishable -- which is what a reader of a
    black-and-white print sees. The mono ramp is monotonic in lightness
    instead: light is cool, dark is hot, and it survives photocopying.
    """
    t = max(0.0, min(1.0, (c - 1.5) / 4.0))
    if mono:
        #: 253 down to 170: the coolest fields land nearly white and the
        #: hottest at a light mid-grey. **The ramp is chosen so BLACK TYPE
        #: clears WCAG AA on every node, not so the range looks wide.** At the
        #: darkest fill here black text sits at about 7.8:1, well past the 4.5:1
        #: floor; the earlier ramp bottomed at #484848, where black type is
        #: 2.6:1 and the label is doing worse than the box it sits in. 83 levels
        #: still separate the ends on a greyscale print, and the node OUTLINE
        #: and the words carry the identity anyway -- a fill is the weakest
        #: channel in the figure and should not be the one asked to do the most.
        v = int(253 - 83 * t)
        return "#%02x%02x%02x" % (v, v, v)
    r, g, b = int(60 + 195 * t), int(110 + 60 * (1 - abs(2 * t - 1))), int(200 - 160 * t)
    return "#%02x%02x%02x" % (r, g, b)


def build(table=TABLE, out=OUT, charge_min=4.0, spec_min=1.0, max_depth=None,
          rebuild=False, edge_labels=False, grain="fine", label_spec=1.5,
          seed="charge", use_senses=False, size_by=None, words=0, hide=(),
          pos_keep=None, pub=False, pub_width=4.8, pub_font_pt=None,
          edge_ratio=0.78):
    ch = field_charge(grain=grain, rebuild=rebuild, use_senses=use_senses,
                      drop_fragments=use_senses,
                      abstain="drop" if use_senses else "fallback",
                      pos_keep=pos_keep)
    rows = [r for r in csv.DictReader(open(table, encoding="utf-8"))
            if r["side"] == "preferred"]
    #: A DISPLAY FILTER, APPLIED HERE AND NOWHERE ELSE. `--drop-generic` in
    #: adjacency.py drops fields inside the cell loop, which changes every
    #: channel's `spec` through the column normalisation and therefore reports
    #: a different population. Dropping rows at draw time changes no number: a
    #: hidden field's channels are still in the table the reader can look up.
    #: Z is the case this exists for -- `he->killed`, `she->smiled`,
    #: `that->it`, a pronoun falling while a verb rises in the same cell, which
    #: is a syntactic reflex rather than a substitution.
    if hide:
        n0 = len(rows)
        rows = [r for r in rows
                if not any(r["source"].startswith(h) or r["target"].startswith(h)
                           for h in hide)]
        print("  hiding %s: %d of %d preferred channels not drawn"
              % ("/".join(hide), n0 - len(rows), n0))
    if not rows:
        print("no preferred channels in %s" % table)
        return 1
    p_cut = rows[0].get("p_cut", "?")
    mp_cut = rows[0].get("min_prompts_cut", "?")

    cent = centrality(rows, size_by) if size_by else {}
    if cent and seed != "sources":
        print("  --size-by %s computed but NOT applied: layered mode draws every "
              "node the same size (see the note in build())." % size_by)
    nw = node_words(rows, words) if words else {}
    out_e, lab, top = collections.defaultdict(list), {}, {}
    for r in rows:
        out_e[r["source"]].append(r)
        lab[r["source"]] = r["source_label"]
        lab[r["target"]] = r["target_label"]
        top.setdefault((r["source"], r["target"]), r["examples"].split(";")[0].strip())

    if seed == "sources":
        #: every node with no in-edge, so the layering is topological and the
        #: whole preferred graph is drawn rather than the part downstream of a
        #: charge threshold. Layers are then position in the graph, NOT
        #: distance from transgression, and the layer charges mean something
        #: different -- see the module docstring.
        has_in = {r["target"] for r in rows}
        seeds = sorted(f for f in out_e if f not in has_in)
    else:
        seeds = sorted(f for f in out_e if ch.get(f) and ch[f][0] >= charge_min)
    if not seeds:
        print("no seed found (seed=%s, charge_min=%.1f)" % (seed, charge_min))
        return 1

    depth, edges, q = {s: 0 for s in seeds}, [], [(s, 0) for s in seeds]
    while q:
        n, d = q.pop(0)
        if max_depth is not None and d >= max_depth:
            continue
        for r in out_e.get(n, []):
            t = r["target"]
            if float(r["spec"]) < spec_min:
                continue
            edges.append((n, t, float(r["spec"]), r["charge_drop"]))
            if t not in depth:
                depth[t] = d + 1
                q.append((t, d + 1))

    if seed == "sources":
        stray = sorted({r["source"] for r in rows if float(r["spec"]) >= spec_min}
                       | {r["target"] for r in rows if float(r["spec"]) >= spec_min}
                       - set(depth))
        for n in stray:
            depth[n] = max(depth.values(), default=0) + 1
        if stray:
            print("  %d node(s) unreachable from any pure source, placed last: %s"
                  % (len(stray), ", ".join(stray)))
        #: AND THEIR EDGES. BFS only emits edges it traverses, so an edge whose
        #: SOURCE is a stray was silently absent: at spec>=1.1 that dropped
        #: `A- -> T+` and `A- -> G-`, and `G-` then rendered as an isolated
        #: island it is not. In `sources` mode the figure claims to be the whole
        #: preferred graph, so it has to carry every qualifying edge, not every
        #: edge the walk happened to reach.
        have = {(a, b) for a, b, _, _ in edges}
        for r in rows:
            k = (r["source"], r["target"])
            if float(r["spec"]) >= spec_min and k not in have:
                edges.append((k[0], k[1], float(r["spec"]), r["charge_drop"]))
                have.add(k)
    layers = collections.defaultdict(list)
    for n, d in depth.items():
        layers[d].append(n)

    print()
    print("  seeds: charge >= %.1f with out-edges -> %s" % (charge_min, ", ".join(seeds)))
    print("  reachable: %d nodes, %d edges (spec >= %.2f) from %d preferred channels"
          % (len(depth), len(edges), spec_min, len(rows)))
    print()
    print("  %-8s %5s  %-12s %-12s" % ("depth", "n", "mean charge", "mean lift"))
    stats = []
    for d in sorted(layers):
        g = [n for n in layers[d] if n in ch]
        mc = st.mean(ch[n][0] for n in g) if g else float("nan")
        ml = [ch[n][2] for n in g if ch[n][2] is not None]
        print("  %-8d %5d  %-12.3f %+.3f" % (d, len(layers[d]), mc,
                                             st.mean(ml) if ml else float("nan")))
        stats.append((d, len(layers[d]), mc))

    dd = [ch[a][0] - ch[b][0] for a, b, _, _ in edges if ch.get(a) and ch.get(b)]
    downhill = 100.0 * sum(1 for x in dd if x > 0) / len(dd) if dd else float("nan")
    print()
    print("  %-10s %5s  %-9s %s" % ("step", "edges", "downhill", "mean drop"))
    by_step = collections.defaultdict(list)
    for a, b, _, _ in edges:
        if ch.get(a) and ch.get(b):
            by_step[depth[a]].append(ch[a][0] - ch[b][0])
    steps = []
    for d in sorted(by_step):
        v = by_step[d]
        pc = 100.0 * sum(1 for x in v if x > 0) / len(v)
        print("  %-10s %5d  %8.1f%% %+9.3f" % ("%d -> %d" % (d, d + 1), len(v), pc, st.mean(v)))
        steps.append((d, len(v), pc, st.mean(v)))
    print()
    print("  all edges: %.1f%% downhill (mean %+0.3f), against a ~68%% shuffle of"
          % (downhill, st.mean(dd) if dd else float("nan")))
    print("  which target attaches to which source. The layout is honest per")
    print("  LAYER, not per ARROW -- see the module docstring.")

    pin = (seed != "sources")
    with open(out, "w", encoding="utf-8") as fh:
        w = fh.write
        w("// permitted channels, layered by BFS depth from charge >= %.1f\n" % charge_min)
        w("// source: %s  (p < %s, >= %s distinct prompts)\n" % (os.path.basename(table), p_cut, mp_cut))
        w("// layer means: %s\n" % "; ".join("d%d n=%d charge %.2f" % s for s in stats))
        w("// %.1f%% of drawn edges run downhill; shuffle gives ~68%%\n" % downhill)
        w("// per step: %s\n" % "; ".join("%d->%d n=%d %.0f%% downhill %+.2f"
                                          % (d, d + 1, n, pc, m) for d, n, pc, m in steps))
        w("digraph channels {\n")
        if pub:
            #: SIZED FOR A `--pub-width` COLUMN AT 300dpi, A LAYOUT CHOICE AND
            #: NOT A RENDER FLAG. Laying out at screen size and scaling down
            #: divides every font by the same factor and a 9pt label becomes
            #: unreadable at 4.7pt. Setting the target width here lets graphviz
            #: place nodes for the space that exists, so the type stays at a
            #: size that prints.
            w('  rankdir=LR; splines=true; overlap=false; bgcolor="white";\n')
            #: `pack` because a DISCONNECTED component is laid out in its own
            #: band and the bands are separated by the height of the tallest:
            #: the GOVT -> SOCIAL -> PSYCHOLOGICAL[-] chain sat alone above two
            #: inches of white. Packing places components side by side instead.
            #: `ratio` is left unset -- it stretches to fill the box and that
            #: pulls ranks apart rather than tightening them.
            #: THE `!` MATTERS. Without it `size` is a cap and graphviz only
            #: scales DOWN, so a drawing whose natural width is 4.69in comes out
            #: at 4.69 when 4.8 was asked for -- silently short of the column,
            #: which is the kind of near-miss nobody checks. `!` scales to the
            #: box exactly, up or down, and scales the type with it.
            w('  size="%.2f,%.2f!"; ranksep=0.28; nodesep=0.08;\n'
              % (pub_width, pub_width * 1.6))

            #: font family and size come from `malignment.figure`, the house
            #: style the plotnine figures already use, so a diagram and a plot
            #: on facing pages are the same face at the same size. `pub_font`
            #: resolves rather than declares -- naming a font matplotlib cannot
            #: find is not an error, it substitutes and warns into a stream
            #: nobody reads.
            from malignment import figure as _fig
            #: DEFAULT is the house size; `--pub-font` overrides it. A dense
            #: diagram is not a plot: at house 9pt this graph lays out 6.79in
            #: wide and `size=!` then scales everything to 0.707, so 9pt PRINTS
            #: at 6.4 and the declaration lies. Declaring the smaller size and
            #: printing it honestly beats declaring the house size and shipping
            #: something else -- the house rule is about what a reader sees.
            fam = _fig.pub_font()
            pt = pub_font_pt or _fig.PUB_FONT_PT
            #: NO FILL. CI's halftone rule wants 20-80% ink with levels >=20
            #: points apart; the charge ramp ran 33% down to 7% with neighbours
            #: one or two points apart, so most of it sat under the floor and
            #: adjacent layers merged after screening. Nobody reads a mean
            #: charge off a grey anyway. Charge moves to BORDER WIDTH, which
            #: draws the cliff directly: four heavy boxes on the left, fourteen
            #: light and equal to their right.
            w('  node [shape=box style="rounded" fontname="%s" fontsize=%g '
              'color="black" fontcolor="black" margin="0.05,0.03"];\n'
              % (fam, pt))
            #: EDGES UNIFORM. Width previously carried `spec` over 0.55-1.28pt,
            #: a range no reader resolves on the page, and two line-weight
            #: encodings in one figure make a heavy node with heavy arrows read
            #: as "big" and nothing else. One weight variable; `spec` lives in
            #: the selection threshold the caption states.
            w('  edge [fontname="%s" fontsize=%g color="#4d4d4d" penwidth=0.75 '
              'arrowsize=0.5];\n' % (fam, pt * edge_ratio))
        else:
            w('  rankdir=LR; splines=true; overlap=false; bgcolor="white";\n')
            w('  node [shape=box style="rounded,filled" fontname="Helvetica" '
              'fontsize=9 penwidth=0.6 color="#666666"];\n')
            w('  edge [fontname="Helvetica" fontsize=7 color="#88888899" '
              'arrowsize=0.6];\n')
        #: `rank=same` pins each BFS layer to a column, which is the point when
        #: depth MEANS something (distance from a charged seed). Seeded from
        #: pure sources it does not: BFS shortest-path over many sources
        #: degenerates into 28 ranks of one node. There, let dot compute its own
        #: layering, which for a near-DAG is the standard Sugiyama pass.
        for d in sorted(layers):
            g = [n for n in layers[d] if n in ch]
            mc = st.mean(ch[n][0] for n in g) if g else float("nan")
            w('\n  // depth %d: %d nodes, mean charge %.2f\n' % (d, len(layers[d]), mc))
            if pin:
                w("  { rank=same;\n")
            for n in sorted(layers[d], key=lambda x: -(ch.get(x, [0])[0])):
                c = ch.get(n, [2.5])[0]
                fc = "#ffffff" if c < 4.2 else "#ffffff"
                nm = (letter_name(n) or lab.get(n, ""))[:28].replace('"', "'")
                #: with example words the CODE and the CHARGE both come out of
                #: the label: the code is an index into a table nobody reads
                #: aloud, and the charge is already the fill colour, so
                #: printing it twice spends the space the words need.
                if words:
                    #: NAME uppercased and the words on ONE line: two short
                    #: lines read as a unit where a stack of five reads as a
                    #: list, and a force layout has to place the whole box.
                    head = (nm or n).upper()
                    body = "  ".join(nw.get(n, [])[:words])
                    if pub:
                        #: THREE TYPE LEVELS, ONE FAMILY AND ONE SIZE. The
                        #: figure has three kinds of text doing three jobs and
                        #: they were identical: field NAME, its example words,
                        #: and the word pair on an edge. Bold the name, leave
                        #: the words regular, italicise the edges. Weight and
                        #: slope separate them without a second family and
                        #: without going under the 6pt floor, which is the
                        #: only other lever and the one that breaks print.
                        esc = lambda t: (t.replace("&", "&amp;")
                                          .replace("<", "&lt;").replace(">", "&gt;"))
                        lb = ("<<b>%s</b>%s>"
                              % (esc(head),
                                 ("<br/>%s" % esc(body)) if body else ""))
                    else:
                        lb = "%s\\n%s" % (head, body) if body else head
                else:
                    head = n if nm in ("", n) else "%s\\n%s" % (n, nm)
                    lb = "%s\\n%.2f" % (head, c)
                size = ""
                if pub:
                    #: 0.5 + 1.5*(charge-2.5)/3, clamped. Depth 0 lands near
                    #: 1.7-2.0pt and depths 1-2 near 0.5-0.6, so the one-step
                    #: cliff is the first thing the eye reads.
                    bw = max(0.5, min(2.0, 0.5 + 1.5 * (c - 2.5) / 3.0))
                    size = " penwidth=%.2f" % bw
                #: LAYERED MODE DRAWS EVERY NODE THE SAME SIZE. A column already
                #: encodes position, so scaling inside it adds a second visual
                #: variable competing with the one the layout exists to show --
                #: and a wide box in a rank pushes its neighbours out of line,
                #: which reads as structure and is not. Centrality stays a
                #: column in the table and sizes the FORCE layouts, where
                #: nothing else encodes it.
                if cent and not pin and not pub:
                    lo, hi = min(cent.values()), max(cent.values())
                    t = 0.0 if hi <= lo else (cent.get(n, lo) - lo) / (hi - lo)
                    size = (' width=%.2f height=%.2f fontsize=%.1f'
                            % (1.0 + 2.2 * t, 0.5 + 0.9 * t, 8.0 + 6.0 * t))
                fmt = ('    "%s" [label=%s fillcolor="%s" fontcolor="%s"%s];\n'
                       if (pub and words) else
                       '    "%s" [label="%s" fillcolor="%s" fontcolor="%s"%s];\n')
                w(fmt % (n, lb, _hex(c, pub),
                     ("#111111" if pub else
                      ("#ffffff" if c >= 4.2 else "#111111")),
                     size))
            if pin:
                w("  }\n")
        w("\n")
        #: **WITHIN-RANK EDGES ARE EMITTED FIRST, AND THAT IS THE FIX FOR THE
        #: LABELS.** Graphviz paints in file order, so a dashed edge listed
        #: after a labelled one lands ON TOP of that label's white ground and
        #: reads through the type. Listed first, the label boxes mask it
        #: wherever they cross. The greys were never the problem: at 20% ink a
        #: thin dash is a row of faint dots after an 80 lpi screen, so lightening
        #: them would have traded one defect for a worse one.
        #:
        #: **AND RECIPROCAL PAIRS MERGE INTO ONE `dir=both` EDGE.** The long
        #: curves are what cross the source-side labels, because graphviz swings
        #: them out around the middle node; two arcs saying A<->B become one
        #: saying the same thing, halving the crossings. The three short
        #: verticals between stacked nodes were never in anyone's way.
        uniq = sorted(set((a, b, sp, cd) for a, b, sp, cd in edges))
        lat = {(a, b) for a, b, _, _ in uniq if pin and depth.get(a) == depth.get(b)}
        recip = {(a, b) for a, b in lat if (b, a) in lat and a < b}
        skip = {(b, a) for a, b in recip}
        order = ([e for e in uniq if (e[0], e[1]) in lat]
                 + [e for e in uniq if (e[0], e[1]) not in lat])
        for a, b, sp, cd in order:
            if (a, b) in skip:
                continue
            pw = 0.4 + 1.8 * max(0.0, min(1.0, (sp - 1.0) / 1.2))
            #: WITHIN-RANK EDGES GO UNLABELLED. An edge between two nodes in the
            #: same column has to route around the column, and graphviz places
            #: those labels on top of each other: three edges into MOVEMENT
            #: rendered as an unreadable smear around "word->walked". The edge
            #: is still drawn; only its caption is dropped, and the pair is in
            #: the table's `examples` column.
            #: WITHIN-RANK EDGES ARE DRAWN DASHED AND WITH constraint=false.
            #: They are not noise and they are not forward motion: at depth 1 of
            #: the verb graph all five run among M, Q and X+ -- movement, speech
            #: and mental state -- two of them RECIPROCAL, on ~2,000 prompts
            #: each at 43-47 lineages. That triangle IS the flat network the
            #: one-step result asserts, so dropping it would draw a clean
            #: cascade the data does not contain. `constraint=false` keeps them
            #: from distorting the ranks they sit inside; dashed says lateral.
            same_rank = (a, b) in lat
            #: and TRANSLUCENT. Graphviz takes #RRGGBBAA and composites at
            #: render time, so this survives into the JPEG even though JPEG
            #: carries no alpha of its own. The lateral circuit should read as
            #: present but recessive: it is the flat network, not the cascade,
            #: and at full weight it competes with the arrows that are forward
            #: motion.
            #: the dash already encodes the class, so the grey was doing no
            #: work the dash does not -- and alpha is not a halftone. 50% grey
            #: clears CI's floor; the label's white ground is what keeps a
            #: dashed line out of the type.
            lateral = ""
            if same_rank:
                lateral = (' style=dashed constraint=false color="%s"'
                           % ("#808080" if pub else "#88888855"))
                if (a, b) in recip:
                    lateral += " dir=both"
                if pub:
                    #: ROUTE ON THE RIGHT OF THE COLUMN. Left to its own
                    #: devices graphviz swings a within-rank curve out to the
                    #: LEFT around the middle node, straight through the
                    #: source-side labels -- `kill -> scream`, `hit -> said`,
                    #: the exhibits. Forcing both ends to the east port puts it
                    #: on the destination side, where the labels have white
                    #: grounds and the dashes are emitted first, so the
                    #: crossings are masked instead of merely thinner.
                    lateral += " tailport=e headport=e"
            show = edge_labels and sp >= label_spec and not same_rank
            if show and pub:
                #: HTML-LIKE LABEL ON A WHITE GROUND. A plain label sits ON the
                #: line and the dashes read through the type; a one-cell table
                #: with bgcolor masks whatever runs beneath, which is what let
                #: the dashes darken to 50% grey without clogging the labels.
                #: no space around the arrow, and no replication count. The
                #: count is a third of every label's width and the figure is
                #: width-bound, so dropping it is what buys type size. It moves
                #: to the caption as a range.
                txt = (top.get((a, b), "").split("(")[0].strip()
                       .replace("&", "&amp;").replace("<", "&lt;")
                       .replace(">", "&gt;").replace("-&gt;", "&#8594;"))
                lbl = (' label=<<table border="0" cellborder="0" cellpadding="0"'
                       ' bgcolor="white"><tr><td><i>%s</i></td></tr></table>>' % txt)
            elif show:
                lbl = ' label="%s"' % top.get((a, b), "").replace('"', "'")
            else:
                lbl = ""
            w('  "%s" -> "%s" [%s%s%s];\n'
              % (a, b, "" if pub else "penwidth=%.2f" % pw, lateral, lbl))
        w("}\n")
    if pub:
        #: **THE DECLARED POINT SIZE IS NOT THE PRINTED ONE** and nothing said
        #: so until a figure nearly shipped at 6.4pt under a 9pt declaration.
        #: `size=...!` scales the whole drawing to the target width, type
        #: included, so a layout whose natural width is 6.79in prints every
        #: font at 0.707x. Measured here by laying the same graph out with no
        #: size cap and comparing, because the scale factor is not recoverable
        #: from the .dot.
        import re as _re, subprocess as _sp, struct as _st, tempfile as _tf
        try:
            body = _re.sub(r'\s*size="[^"]*";', '', open(out).read())
            with _tf.NamedTemporaryFile("w", suffix=".dot", delete=False) as fh2:
                fh2.write(body); nat_dot = fh2.name
            png = nat_dot + ".png"
            _sp.run(["dot", "-Tpng", "-Gdpi=72", nat_dot, "-o", png],
                    capture_output=True, check=True)
            raw = open(png, "rb").read()
            nw, _nh = _st.unpack(">II", raw[16:24])
            sc = min(1.0, pub_width / (nw / 72.0))
            from malignment import figure as _fig2
            dpt = pub_font_pt or _fig2.PUB_FONT_PT
            print("  PRINTED type: %.1fpt node / %.1fpt edge (declared %g/%g, "
                  "natural width %.2f in, scale %.3f)"
                  % (dpt * sc, dpt * edge_ratio * sc, dpt,
                     dpt * edge_ratio, nw / 72.0, sc))
            print("  house size is %gpt (malignment.figure.PUB_FONT_PT); this "
                  "figure prints at %.1fpt." % (_fig2.PUB_FONT_PT, dpt * sc))
        except Exception as e:
            print("  (could not measure printed type: %s)" % e)
    print()
    print("-> %s" % out)
    print("   dot -Tpdf %s -o %s" % (out, out.replace(".dot", ".pdf")))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--table", default=TABLE)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--charge-min", type=float, default=4.0,
                    help="seed set: fields whose vocabulary averages this "
                         "charge. 4.0 is run.py's 'strong' dose band.")
    ap.add_argument("--spec-min", type=float, default=1.0,
                    help="drop edges below this specificity before tracing")
    ap.add_argument("--max-depth", type=int, default=None)
    ap.add_argument("--rebuild-charge", action="store_true")
    ap.add_argument("--pub", action="store_true",
                    help="publication geometry: a grey charge ramp that is "
                         "monotonic in LIGHTNESS so it survives black and "
                         "white, 4.5in target width, tighter ranks, and type "
                         "sized for print rather than scaled down from screen.")
    ap.add_argument("--pub-width", type=float, default=4.8,
                    help="target width in INCHES for --pub. The height cap is "
                         "1.6x this; graphviz uses both as a bounding box and "
                         "only scales down, so the rendered figure is at most "
                         "this wide and usually exactly this wide.")
    ap.add_argument("--pub-font", type=float, default=None,
                    help="declared node point size under --pub; edge labels "
                         "get 0.78x. Defaults to malignment.figure."
                         "PUB_FONT_PT. The producer reports what actually "
                         "PRINTS after size scaling, which is the number that "
                         "matters and is not the declared one.")
    ap.add_argument("--pub-edge-ratio", type=float, default=0.78,
                    help="edge label size as a fraction of the node size. "
                         "Raising it costs NODE size rather than adding "
                         "width, because the layout is already at the width "
                         "budget and everything then scales together: 0.78 "
                         "prints 6.0/4.7, 0.93 prints 5.8/5.4, 1.0 prints "
                         "5.6/5.6.")
    ap.add_argument("--pos", default=None,
                    help="restrict FIELD CHARGE to candidates with this "
                         "contextual tag, e.g. VERB. Match it to how --table "
                         "was produced: node colour and edge come from "
                         "different populations otherwise.")
    ap.add_argument("--hide", default=None,
                    help="comma-separated field prefixes to leave OUT OF THE "
                         "DRAWING, e.g. Z for grammar/names. A display filter: "
                         "it changes no number, unlike adjacency.py's "
                         "--drop-generic which drops inside the cell loop and "
                         "moves every spec.")
    ap.add_argument("--size-by", default=None,
                    choices=("degree", "indegree", "pagerank", "authority",
                             "betweenness"),
                    help="scale node size by a centrality on the preferred "
                         "digraph, edges weighted by spec-1. pagerank and "
                         "authority measure DESTINATION-ness; betweenness "
                         "measures WAYSTATION-ness and scores a pure sink "
                         "zero. They answer different questions.")
    ap.add_argument("--words", type=int, default=0,
                    help="print this many example words in each node instead "
                         "of the USAS code and the charge number. The charge "
                         "stays as the fill colour.")
    ap.add_argument("--senses", action="store_true",
                    help="compute field charge on the DISAMBIGUATED coding "
                         "(senses, fragments dropped, abstentions honoured), "
                         "cached separately. Match this to how --table was "
                         "produced or the nodes and the edges describe "
                         "different tables.")
    ap.add_argument("--grain", default="fine", choices=("fine", "letter"),
                    help="must MATCH the grain of --table. Field charge is "
                         "cached per grain because a letter pools codes and "
                         "its charges are a different quantity.")
    ap.add_argument("--seed", default="charge", choices=("charge", "sources"),
                    help="'charge' seeds on fields at or above --charge-min, "
                         "so depth means distance from transgression. "
                         "'sources' seeds on every node with no in-edge, so "
                         "the WHOLE preferred graph is drawn and depth means "
                         "position in it. The two layer statistics are "
                         "different quantities.")
    ap.add_argument("--label-spec", type=float, default=1.5,
                    help="only label edges at or above this spec. Coarse-grain "
                         "specs run 1.1-1.3, so the fine default draws nothing.")
    ap.add_argument("--edge-labels", action="store_true",
                    help="write the top word pair on strong edges. OFF by "
                         "default: graphviz's fixLabelOrder asserts and aborts "
                         "when edge labels meet rank=same groups, so the "
                         "labelled variant may not render at all.")
    a = ap.parse_args(argv)
    return build(a.table, a.out, a.charge_min, a.spec_min, a.max_depth,
                 a.rebuild_charge, a.edge_labels, a.grain, a.label_spec,
                 a.seed, a.senses, a.size_by, a.words,
                 tuple(x.strip() for x in a.hide.split(",")) if a.hide else (),
                 tuple(x.strip().upper() for x in a.pos.split(",")) if a.pos else None,
                 a.pub, a.pub_width, a.pub_font, a.pub_edge_ratio)


if __name__ == "__main__":
    sys.exit(main())
