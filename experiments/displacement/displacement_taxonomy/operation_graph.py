"""Pool every reading of one prompt into one graph and count its components.

    python operation_graph.py "He started stroking"
    python operation_graph.py "His asylum claim" --png
    python operation_graph.py --all

## The graph

    M##_from_word --> [operation] --> M##_to_word

The OPERATION IS A NODE, not an edge label. That is the whole design: word nodes
are scoped to their model, so two readings share a node only where they put the
SAME model's words on a relation, and the operation hub is what joins them. Built
with the operation as an edge label instead, every model is its own island and
the component count is just the number of models.

## Within one reading the count is trivial; pooling is what makes it a measurement

`crosslineage.ingest` asserts every model appears exactly once across
`operations`, `reversed` and `unassigned`. So inside a single reading no model
can bridge two hubs and COMPONENTS ALWAYS EQUALS THE OPERATION COUNT -- verified
below rather than assumed, because if it ever fails the assert has been bypassed.

Pooled over readings a model appears once per reading under different names, and
the components then say which operations are the same relation renamed. On `He
started stroking his` at 50 lineages, thirteen operations from two conditions and
four raters collapse to two.

## Only `operations` members are used

`reversed` carries `a_words`/`b_words` too and is deliberately EXCLUDED: a
reversal is the same relation run backwards, so admitting it would join hubs
through models that disagree about direction, and the component would then mean
"related somehow" rather than "the same relation". `unassigned` carries no words
at all, so it cannot enter either way.
"""

import argparse
import collections
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def _fingerprint(v):
    """The reading's CONTENT, ignoring provenance -- for spotting duplicates."""
    import hashlib, json
    core = {"operations": v.get("operations"), "reversed": v.get("reversed"),
            "unassigned": v.get("unassigned"), "confidence": v.get("confidence"),
            "survey": v.get("survey")}
    return hashlib.sha256(json.dumps(core, sort_keys=True).encode()).hexdigest()[:12]


def readings(prefix, n_lineages=None):
    """[(tag, reading)] for every DISTINCT stashed reading of a prompt.

    DE-DUPLICATED BY CONTENT, and it matters. 40 of the 87 stashed readings carry
    no `n_lineages` -- they are the pre-provenance era, before `lineages_sha`
    entered the key, and all 40 are byte-identical to a reading that DOES carry
    it. Pooling both copies double-counts every operation in them: the asylum
    prompt reported 7 operations over 4 readings where it has 5 over 3.

    It does not change the component COUNT, because a duplicate connects to its
    original through every model they share -- which is why nothing caught it.
    Prefer the copy with provenance; drop the bare one.
    """
    import crosslineage as X
    st = X._stash()
    ks = [k for k in st if isinstance(k, dict)
          and str(k.get("frame_prompt", "")).lower().startswith(prefix.lower())
          and (n_lineages is None or k.get("n_lineages") == n_lineages)]
    best, drop = {}, 0
    for k in ks:
        f = _fingerprint(st[k])
        if f not in best or (best[f].get("n_lineages") is None and k.get("n_lineages") is not None):
            if f in best:
                drop += 1
            best[f] = k
        else:
            drop += 1
    ks = sorted(best.values(),
                key=lambda k: (k.get("version", ""), k.get("n_lineages") or 0, k.get("rater") or 0))
    if drop:
        print("  (dropped %d duplicate reading(s) with no provenance)" % drop)
    return [("%s.n%s.r%s" % (k.get("version"), k.get("n_lineages"), k.get("rater")), st[k])
            for k in ks], (ks[0]["frame_prompt"] if ks else None)


def build(pairs):
    import networkx as nx
    G = nx.DiGraph()
    for tag, v in pairs:
        for o in v.get("operations") or []:
            op = "OP[%s] %s" % (tag, o["name"])
            G.add_node(op, kind="op", reading=tag, label=o["name"],
                       n=len(o.get("members") or []))
            for m in o.get("members") or []:
                for a in m.get("a_words") or []:
                    G.add_edge("%s::%s" % (m["model"], a.lower()), op)
                for b in m.get("b_words") or []:
                    G.add_edge(op, "%s::%s" % (m["model"], b.lower()))
    return G


def analyse(prefix, n_lineages=None, png=False, report=False, data=False):
    import networkx as nx
    pairs, prompt = readings(prefix, n_lineages)
    if not pairs:
        raise SystemExit("no stashed reading for a prompt starting %r" % prefix)
    print("%r\n  %d reading(s): %s" % (prompt, len(pairs), ", ".join(t for t, _ in pairs)))

    #: THE TRIVIALITY CHECK, stated as an assert rather than a comment. If a
    #: single reading ever splits into more components than it named operations,
    #: a model reached two hubs and the completeness assert did not hold.
    for tag, v in pairs:
        g = build([(tag, v)])
        c = list(nx.connected_components(g.to_undirected()))
        nops = len(v.get("operations") or [])
        assert len(c) == nops, \
            "%s: %d components for %d operations -- a model bridged two hubs" % (tag, len(c), nops)

    G = build(pairs)
    OPS = {n for n in G if G.nodes[n].get("kind") == "op"}
    cc = sorted(nx.connected_components(G.to_undirected()), key=len, reverse=True)
    print("  pooled: %d nodes (%d operations, %d word-nodes), %d edges -> COMPONENTS %d\n"
          % (G.number_of_nodes(), len(OPS), G.number_of_nodes() - len(OPS),
             G.number_of_edges(), len(cc)))
    for i, c in enumerate(cc, 1):
        ops = sorted((n for n in c if n in OPS), key=lambda n: -G.nodes[n]["n"])
        mods = {n.split("::")[0] for n in c if "::" in n}
        by = collections.Counter(G.nodes[n]["reading"] for n in ops)
        print("  component %d: %d operations over %d reading(s), %d models, %d word-nodes"
              % (i, len(ops), len(by), len(mods), len(c) - len(ops)))
        for n in ops:
            print("       %-13s %-40s %d members" % (G.nodes[n]["reading"], G.nodes[n]["label"],
                                                      G.nodes[n]["n"]))
        print()
    if report:
        audit(G, cc, OPS, pairs, prompt)
    if data:
        emit(G, cc, OPS, pairs, prompt, prefix)
    if png:
        render(G, cc, OPS, prompt, prefix)
    return G, cc


def audit(G, cc, OPS, pairs, prompt, width=68):
    """Everything a component rests on, in one place: operations, statements,
    and each model's own FROM and TO words with which operations placed them.

    A component is an assertion that several differently-named operations are one
    relation. That is not checkable from a count, so this prints the evidence:
    if two operations share a component, the models and words that join them are
    on the page and a reader can disagree.
    """
    import collections, textwrap
    #: model -> {op node -> (from words, to words)}, straight off the members.
    per = collections.defaultdict(dict)
    stmt = {}
    for tag, v in pairs:
        for o in v.get("operations") or []:
            op = "OP[%s] %s" % (tag, o["name"])
            stmt[op] = o.get("statement", "")
            for m in o.get("members") or []:
                per[m["model"]][op] = ([w.lower() for w in m.get("a_words") or []],
                                       [w.lower() for w in m.get("b_words") or []])
    W = lambda t, i: textwrap.fill(t, width, initial_indent=i, subsequent_indent=i)

    #: ── THE DENOMINATOR, PRINTED ONCE AT THE TOP ────────────────────────────
    #:
    #: A component's model count is unreadable without it. Only models placed in
    #: `operations` reach the graph at all: `unassigned` carries no words, and
    #: `reversed` is excluded by construction. Measured across the three prompts,
    #: what reaches the graph runs from 18% to 98% of what was SENT, and it is
    #: the RATER that swings it -- insurance sighted r1 placed 46 of 47 and
    #: abstained on none, r2 placed 25 and abstained on 22, on identical tables.
    #:
    #: So "4 models" means one thing against 47 and another against 25, and
    #: nothing else on this page says which.
    print("COVERAGE -- what reached the graph, per reading\n")
    shown = None
    for tag, v in pairs:
        inops = {m["model"] for o in v.get("operations") or [] for m in o.get("members") or []}
        rev, un = len(v.get("reversed") or []), len(v.get("unassigned") or [])
        tot = len(inops) + rev + un
        shown = tot if shown is None else shown
        print("  %-14s placed %3d   reversed %2d   unassigned %2d   of %d shown  (%.0f%% in graph)"
              % (tag, len(inops), rev, un, tot, 100.0 * len(inops) / tot))
    allmods = {n.split("::")[0] for n in G if "::" in n}
    print("  %-14s union over readings: %d of %d (%.0f%%)\n"
          % ("", len(allmods), shown or 0, 100.0 * len(allmods) / (shown or 1)))

    for i, c in enumerate(cc, 1):
        ops = sorted((n for n in c if n in OPS), key=lambda n: -G.nodes[n]["n"])
        mods = sorted({n.split("::")[0] for n in c if "::" in n})
        print("=" * 78)
        print("COMPONENT %d   %d operation(s), %d of the %d models that reached the graph"
              % (i, len(ops), len(mods), len(allmods)))
        print("=" * 78)
        for n in ops:
            print("\n  [%s]  %s  (%d members)"
                  % (G.nodes[n]["reading"], G.nodes[n]["label"], G.nodes[n]["n"]))
            if stmt.get(n):
                print(W(stmt[n], "      "))
        #: THE POOLED VOCABULARY, so a reader sees at a glance what the component
        #: is made of before reading fifty rows of it.
        fw = sorted({w for m in mods for op in per[m] if op in c for w in per[m][op][0]})
        tw = sorted({w for m in mods for op in per[m] if op in c for w in per[m][op][1]})
        print("\n  pooled FROM (%d): %s" % (len(fw), ", ".join(fw)))
        print("  pooled TO   (%d): %s" % (len(tw), ", ".join(tw)))
        print("\n  per model -- FROM -> TO, and which operation(s) placed it\n")
        for m in mods:
            here = {op: v for op, v in per[m].items() if op in c}
            f = sorted({w for v in here.values() for w in v[0]})
            t = sorted({w for v in here.values() for w in v[1]})
            #: CONTINUATION LINES ARE INDENTED PAST THE LABEL. `textwrap` with the
            #: same indent on both put "FROM" at the head of the wrapped line too,
            #: so a long list read as two separate FROM entries on a skim.
            def lab(tag, ws):
                return textwrap.fill(" ".join(ws) or "(none)", width,
                                     initial_indent="        %-6s" % tag,
                                     subsequent_indent="              ")
            print("    %s" % m)
            print(lab("FROM", f))
            print(lab("TO", t))
            print("        in    %s" % "; ".join(
                "%s [%s]" % (G.nodes[op]["label"], G.nodes[op]["reading"]) for op in sorted(here)))
        print()


def render(G, cc, OPS, prompt, prefix):
    import networkx as nx, numpy as np
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    #: EACH COMPONENT LAID OUT ALONE AND NORMALISED TO ITS OWN BOX. One spring
    #: over the whole graph gives a small component a fraction of the area and
    #: pushes it into a corner, so the picture says "minor" about something whose
    #: size is the finding. Sizes are carried by the printed counts instead.
    rng = lambda a: (a.max() - a.min()) or 1.0        # numpy 2 dropped ndarray.ptp
    U, pos, W = G.to_undirected(), {}, 1.0
    for i, c in enumerate(cc):
        p = nx.spring_layout(U.subgraph(c), k=1.6 / np.sqrt(len(c)),
                             seed=20260821, iterations=220)
        xs = np.array([v[0] for v in p.values()]); ys = np.array([v[1] for v in p.values()])
        xs = (xs - xs.min()) / rng(xs); ys = (ys - ys.min()) / rng(ys)
        for (n, _), x, y in zip(p.items(), xs, ys):
            pos[n] = (x * W + i * (W + 0.30), y)
    tags = sorted({G.nodes[n]["reading"] for n in OPS})
    PAL = ["#fa5252", "#e8590c", "#4dabf7", "#b197fc", "#ffd43b", "#51cf66"]
    COL = {t: PAL[i % len(PAL)] for i, t in enumerate(tags)}
    fig, ax = plt.subplots(figsize=(16, 9), facecolor="#0f1015"); ax.set_facecolor("#0f1015")
    nx.draw_networkx_edges(U, pos, ax=ax, edge_color="#5c6472", width=0.22, alpha=0.30)
    for i, c in enumerate(cc):
        w = [n for n in c if n not in OPS]; o = [n for n in c if n in OPS]
        nx.draw_networkx_nodes(U, pos, nodelist=w, ax=ax, node_size=8, linewidths=0, alpha=.85,
                               node_color="#9aa3b0" if i == 0 else "#ffd43b")
        nx.draw_networkx_nodes(U, pos, nodelist=o, ax=ax,
                               node_size=[110 + 24 * G.nodes[n]["n"] for n in o],
                               node_color=[COL[G.nodes[n]["reading"]] for n in o],
                               edgecolors="#0f1015", linewidths=1.6)
        #: LABELS IN A COLUMN BESIDE THE COMPONENT, leader-lined to their hub. On
        #: the nodes they overlap into a smear as soon as two hubs sit close --
        #: which is exactly what happens when two readings agree.
        for j, n in enumerate(sorted(o, key=lambda n: -G.nodes[n]["n"])):
            ax.annotate("%s (%d)" % (G.nodes[n]["label"], G.nodes[n]["n"]), xy=pos[n],
                        xytext=(i * (W + 0.30) + W + 0.02, 0.97 - j * 0.062),
                        fontsize=8.6, color=COL[G.nodes[n]["reading"]], ha="left", va="center",
                        arrowprops=dict(arrowstyle="-", color="#5c6472", lw=.6, alpha=.55,
                                        shrinkA=0, shrinkB=4))
        ax.text(i * (W + 0.30) + W / 2, 1.06,
                "component %d\n%d operations  ·  %d models"
                % (i + 1, len(o), len({n.split("::")[0] for n in c if "::" in n})),
                ha="center", va="bottom", fontsize=12, fontweight="bold",
                color="#c8ccd4" if i == 0 else "#ffd43b")
    ax.legend(handles=[plt.Line2D([], [], marker="o", ls="", ms=9, mfc=COL[t], mec="none", label=t)
                       for t in tags],
              loc="lower center", ncol=min(len(tags), 6), frameon=False,
              labelcolor="#c8ccd4", fontsize=10, bbox_to_anchor=(0.5, -0.04))
    ax.set_title("%s\n%d operations, %d readings, pooled.  M##_word -> [operation] -> M##_word: "
                 "two readings touch only where they put the SAME model's words on a relation."
                 % (prompt, len(OPS), len(tags)),
                 color="#f2f4f8", fontsize=12.5, loc="left", pad=34)
    ax.set_xlim(-0.06, len(cc) * (W + 0.30) + 0.80); ax.set_ylim(-0.10, 1.22)
    ax.axis("off"); plt.subplots_adjust(left=.01, right=.99, top=.82, bottom=.08)
    import re
    slug = re.sub(r"[^a-z0-9]+", "_", prefix.lower())[:34].strip("_")
    out = os.path.join(HERE, "figures", "opgraph_%s.png" % slug)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    plt.savefig(out, dpi=190, facecolor="#0f1015")
    print("  wrote %s" % out)


def emit(G, cc, OPS, pairs, prompt, prefix):
    """Write the pooled graph as a `graph` artifact for the web app.

    Word nodes carry their `model`, so the UI can collapse to model grain
    without a second artifact -- 800 word nodes is a lot for a browser force
    simulation and ~50 model nodes is what a reader can actually judge, but the
    words are what makes a component checkable, so both have to be reachable.
    """
    import json, re, collections
    from malignment.chartdata import graph, write
    comp = {n: i for i, c in enumerate(cc) for n in c}
    stmt, members = {}, collections.defaultdict(dict)
    for tag, v in pairs:
        for o in v.get("operations") or []:
            op = "OP[%s] %s" % (tag, o["name"])
            stmt[op] = o.get("statement", "")
            for m in o.get("members") or []:
                members[op][m["model"]] = ([w.lower() for w in m.get("a_words") or []],
                                           [w.lower() for w in m.get("b_words") or []])
    tags = sorted({G.nodes[n]["reading"] for n in OPS})
    PAL = ["#fa5252", "#e8590c", "#4dabf7", "#b197fc", "#ffd43b", "#51cf66"]
    nodes = []
    for n in G:
        if n in OPS:
            nodes.append({"id": n, "kind": "op", "label": G.nodes[n]["label"],
                          "group": G.nodes[n]["reading"], "component": comp[n],
                          "n": G.nodes[n]["n"], "statement": stmt.get(n, ""),
                          "models": sorted(members.get(n, {}))})
        else:
            model, word = n.split("::", 1)
            side = "from" if any(True for _ in G.successors(n)) else "to"
            nodes.append({"id": n, "kind": "word", "label": word, "model": model,
                          "side": side, "group": None, "component": comp[n]})
    links = [{"source": a, "target": b} for a, b in G.edges()]
    cov = []
    for tag, v in pairs:
        inops = {m["model"] for o in v.get("operations") or [] for m in o.get("members") or []}
        cov.append({"reading": tag, "placed": len(inops),
                    "reversed": len(v.get("reversed") or []),
                    "unassigned": len(v.get("unassigned") or [])})
    art = graph(
        title=prompt,
        subtitle=("%d operations from %d reading(s), pooled. An operation is a NODE: two "
                  "readings touch only where they put the SAME model's words on a relation. "
                  "Only models placed in `operations` are here -- `unassigned` carries no "
                  "words and `reversed` is excluded, so between 18%% and 98%% of what was "
                  "sent reaches this graph depending on the rater."
                  % (len(OPS), len(pairs))),
        nodes=nodes, links=links,
        groups=[{"key": t, "label": t, "colour": PAL[i % len(PAL)]} for i, t in enumerate(tags)],
        meta={"components": [{"operations": sum(1 for x in c if x in OPS),
                              "models": len({x.split("::")[0] for x in c if "::" in x})}
                             for c in cc],
              "coverage": cov, "prompt": prompt})
    slug = re.sub(r"[^a-z0-9]+", "_", prefix.lower())[:34].strip("_")
    return write(art, os.path.join(HERE, "figures"), "opgraph_%s" % slug)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("prefix", nargs="?")
    ap.add_argument("--n-lineages", type=int, default=None)
    ap.add_argument("--png", action="store_true")
    ap.add_argument("--data", action="store_true",
                    help="write a `graph` artifact for the web app")
    ap.add_argument("--report", action="store_true",
                    help="print each component's operations, statements and per-model words")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args(argv)
    if a.all:
        import crosslineage as X
        seen = sorted({k["frame_prompt"] for k in X._stash()
                       if isinstance(k, dict) and k.get("stage") == "crosslineage"})
        for p in seen:
            analyse(p, a.n_lineages, a.png, a.report, a.data); print("-" * 78)
        return
    if not a.prefix:
        raise SystemExit("give a prompt prefix, or --all")
    analyse(a.prefix, a.n_lineages, a.png, a.report, a.data)


if __name__ == "__main__":
    main()
