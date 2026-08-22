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


def op_components(G, OPS, k=2):
    """Components over OPERATIONS, joined only where they share >= k models.

    ## WHY CONNECTIVITY OVER WORD NODES WAS THE WRONG CRITERION (RH, 2026-08-22)

    The word graph joins two operations if they share ONE model, and RH spotted
    the consequence in the render: `explicit-to-decorous displacement` and
    `neutral-field reordering` hang together on `deepseek-llm-7b-chat` alone.
    Remove that one model and stroking's component 1 splits.

    Worse, it explains a result I had already misread. Insurance's transgressive
    cluster "merges when you add readings" -- but it is attached to the main blob
    by exactly two single-model bridges, `Olmo-3.1-32B-Instruct` and
    `Olmo-3-7B-Instruct`, which are THE MODELS THE CLUSTER IS ABOUT. A rater who
    also places them in `Auxiliary Action Displacement` lists their ordinary
    from-words there, and the finding ends up joined to everything else by its own
    subjects.

    So a shared model is not evidence that two operations are one relation. k=2
    is the default because it is the smallest threshold that means anything: two
    readings assert the same relation only if they agree about at least two
    models. k=1 reproduces the old behaviour and is what nobody chose.
    """
    import itertools, networkx as nx
    mods = {o: {n.split("::")[0] for n in G.to_undirected().neighbors(o)} for o in OPS}
    Q = nx.Graph()
    Q.add_nodes_from(OPS)
    for a, b in itertools.combinations(sorted(OPS), 2):
        sh = mods[a] & mods[b]
        if len(sh) >= k:
            Q.add_edge(a, b, shared=len(sh))
    comps = sorted(nx.connected_components(Q), key=len, reverse=True)
    #: the pairs k EXCLUDED, so the threshold's cost is visible rather than
    #: implied -- these are the joins that would have existed at k=1.
    cut = [(a, b, len(mods[a] & mods[b])) for a, b in itertools.combinations(sorted(OPS), 2)
           if 0 < len(mods[a] & mods[b]) < k]
    return comps, cut, mods


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


def analyse(prefix, n_lineages=None, png=False, report=False, data=False, k=2):
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
        #: A k=1 PROPERTY, so it is checked at k=1 whatever k the caller asked
        #: for: the completeness assert guarantees each model sits in exactly
        #: one operation, so a single reading cannot bridge two hubs by sharing
        #: a model. At k>=2 a single reading has no operation edges at all and
        #: this would be vacuous.
        assert len(c) == nops, \
            "%s: %d components for %d operations -- a model bridged two hubs" % (tag, len(c), nops)

    G = build(pairs)
    OPS = {n for n in G if G.nodes[n].get("kind") == "op"}
    ocs, cut, mods = op_components(G, OPS, k)
    at1, _, _ = op_components(G, OPS, 1)
    #: components are over OPERATIONS; word nodes are carried along by whichever
    #: operations placed them, and a model in two components appears in both --
    #: which is a fact about the readings, not a bug to resolve away.
    cc = []
    for oc in ocs:
        c = set(oc)
        for o in oc:
            c |= set(G.to_undirected().neighbors(o))
        cc.append(c)
    print("  pooled: %d nodes (%d operations, %d word-nodes), %d edges"
          % (G.number_of_nodes(), len(OPS), G.number_of_nodes() - len(OPS), G.number_of_edges()))
    print("  COMPONENTS at k=%d: %d      (at k=1 it would be %d)\n" % (k, len(cc), len(at1)))
    if cut:
        print("  operation pairs k=%d EXCLUDES (they share fewer than %d models):" % (k, k))
        for a, b, n in sorted(cut, key=lambda x: -x[2])[:8]:
            print("     %-32s + %-32s  %d shared"
                  % (G.nodes[a]["label"][:32], G.nodes[b]["label"][:32], n))
        print()
    for i, c in enumerate(cc, 1):
        ops = sorted((n for n in c if n in OPS), key=lambda n: -G.nodes[n]["n"])
        #: NOT `mods` -- that name holds op -> models for the whole graph and is
        #: passed to emit() below. Shadowing it here handed emit a set of model
        #: names from the last component and every cross-link came out False.
        cmods = {n.split("::")[0] for n in c if "::" in n}
        by = collections.Counter(G.nodes[n]["reading"] for n in ops)
        print("  component %d: %d operations over %d reading(s), %d models, %d word-nodes"
              % (i, len(ops), len(by), len(cmods), len(c) - len(ops)))
        for n in ops:
            print("       %-13s %-40s %d members" % (G.nodes[n]["reading"], G.nodes[n]["label"],
                                                      G.nodes[n]["n"]))
        print()
    if report:
        audit(G, cc, OPS, pairs, prompt)
    if data:
        emit(G, cc, OPS, pairs, prompt, prefix, k, len(at1), ocs, mods)
    if png:
        render(G, cc, OPS, prompt, prefix)
    return G, cc


def sidecar(prompt):
    """`{model: {word: row}}` from the `.tables.json` the rater actually read.

    ## WHY THIS EXISTS (RH, 2026-08-22)

    `audit` printed each model's words with `sorted()`, which is alphabetical, so
    `bastards` at rank 3 carrying 7.2% and `birds` at rank 60 carrying 0.02% were
    adjacent and indistinguishable. Every trace of magnitude and prominence was
    destroyed by the display, and a reader could not tell a headline term from a
    tail one. The ranks were never lost -- `tables()` writes them to the sidecar
    for exactly this reason -- they were simply thrown away at print time.

    ## MATCHED ON CONTENT, NOT ON NAME

    The file is found by reading each candidate's `prompt` field rather than by
    reconstructing a slug, because the slug is a truncation of the prompt to 34
    characters and two prompts can share one. Globbing then matching on content
    is the safe form of a glob: the name is a hint and the field is the check.
    Exactly one file must match, and it is an error if none or several do.
    """
    import glob, json
    hits = []
    for f in sorted(glob.glob(os.path.join(HERE, "results", "xling_*.tables.json"))):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        if d.get("prompt") == prompt:
            hits.append((f, d))
    if not hits:
        return None
    #: A PROMPT USUALLY HAS TWO SIDECARS, blind and sighted, and their `prompt`
    #: fields are identical because blinding relabels the MODELS and never the
    #: sentence. Requiring exactly one match silently returned None for every
    #: prompt run both ways -- the insurance frame audited as NO SIDECAR when its
    #: file was on disk the whole time. The tables are computed from twp and are
    #: written under real model names either way, so the copies must agree; take
    #: the first and refuse if they do not.
    idx = [{m: {r["word"]: r for r in (t.get("rows") or [])}
            for m, t in (d.get("tables") or {}).items()} for _, d in hits]
    for other in idx[1:]:
        assert set(other) == set(idx[0]) and all(
            set(other[m]) == set(idx[0][m]) for m in other), \
            "sidecars for one prompt disagree: %s" % [f for f, _ in hits]
    #: CASE-FOLDED, and this is not cosmetic. Table words keep their corpus
    #: casing while raters are asked for words and cite them lowercased, so a
    #: raw-key lookup marks every PROPER NOUN absent. That produced a false
    #: fabrication finding: `Jews` and `Nazis` are in the tables, and because
    #: proper nouns are exactly the capitalised tokens, the bug's false positives
    #: were guaranteed to be charged group terms and read as a pattern.
    out = {}
    for m, rows in idx[0].items():
        fold = {}
        for w, r in rows.items():
            fold.setdefault(w.lower(), r)
        fold.update(rows)
        out[m] = fold
    return out


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
    SC = sidecar(prompt)
    if SC is None:
        print("  (no .tables.json matched this prompt; words print unranked)\n")

    def ranked(model, ws, side):
        """Cited words newest-first by PROMINENCE ON THEIR OWN SIDE, with rank and mass.

        A word the rater cited but the table does not contain is printed as `?`
        rather than dropped. That is a rater citing something it was not shown,
        which is a data-integrity event and has to be visible; silently omitting
        it would make the exhibit agree with the reading by deleting the
        disagreement.
        """
        rows = (SC or {}).get(model) or {}
        ws = [w if w in rows else w.lower() for w in ws]
        rk, pk = ("rank_a", "p_a") if side == "A" else ("rank_b", "p_b")
        ok = [(rows[w][rk], rows[w][pk], rows[w].get("rank_b" if side == "A" else "rank_a"), w)
              for w in ws if w in rows and rows[w].get(rk) is not None]
        miss = sorted(w for w in ws if w not in rows)
        #: RANK ONLY. Rank and per-cent together put four numbers on every word and
        #: the line stopped reading as language. Rank carries prominence on its
        #: own; the mass is in the sidecar and in the artifact for anything that
        #: needs magnitude rather than order.
        out = ["%s (%d->%s)" % (w, r, ("%d" % o) if o is not None else "-")
               for r, p, o, w in sorted(ok)]
        return out + ["%s (?)" % w for w in miss]

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
                return textwrap.fill("; ".join(ws) or "(none)", width + 26,
                                     initial_indent="        %-6s" % tag,
                                     subsequent_indent="              ")
            print("    %s" % m)
            print(lab("FROM", ranked(m, f, "A") if SC else sorted(f)))
            print(lab("TO", ranked(m, t, "B") if SC else sorted(t)))
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


def emit(G, cc, OPS, pairs, prompt, prefix, k=2, n_at1=None, ocs=None, mods=None):
    """Write the pooled graph as a `graph` artifact for the web app.

    Word nodes carry their `model`, so the UI can collapse to model grain
    without a second artifact -- 800 word nodes is a lot for a browser force
    simulation and ~50 model nodes is what a reader can actually judge, but the
    words are what makes a component checkable, so both have to be reachable.
    """
    import json, re, collections
    from malignment.chartdata import graph, write
    #: `mods` maps operation -> models and `ocs` is op_components' component list.
    #: Both were shadowed in analyse()'s report loop once, which turned every
    #: cross flag False and reported it as a clean run. Cheap to state, and it is
    #: the only thing standing between a wrong picture and a plausible one.
    assert isinstance(ocs, list) and isinstance(mods, dict) and all(
        isinstance(v, set) for v in mods.values()), \
        "emit() needs op_components' (ocs, mods); got %s / %s" % (type(ocs), type(mods))
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
    #: RANKS TRAVEL WITH THE ARTIFACT. Without them the web panel can only sort
    #: alphabetically, which is the same defect audit() had: `bastards` at rank 3
    #: carrying 7.2% printed beside `birds` at rank 60 carrying 0.02% and nothing
    #: told them apart. The consumer cannot recover this -- the sidecar is not
    #: served -- so it is emitted here or the display cannot be fixed at all.
    SC = sidecar(prompt) or {}
    def rk(model, word):
        r = (SC.get(model) or {}).get(word) or (SC.get(model) or {}).get(word.lower())
        if not r:
            return None
        return {"ra": r.get("rank_a"), "rb": r.get("rank_b"),
                "pa": round(r.get("p_a") or 0.0, 6), "pb": round(r.get("p_b") or 0.0, 6)}
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
            nodes.append(dict({"id": n, "kind": "word", "label": word, "model": model,
                               "side": side, "group": None, "component": comp[n]},
                              **(rk(model, word) or {})))
    #: A LINK THAT CROSSES A COMPONENT BOUNDARY IS MARKED, NOT DROPPED. These are
    #: exactly the single-model bridges k=2 refuses to count -- the whole reason
    #: for the threshold -- so hiding them would make the picture agree with the
    #: number by concealing the thing the number is about. Marked instead: the UI
    #: keeps them out of the LINK FORCE, so components separate, and still draws
    #: them faintly, so a reader can see where two clusters touch and by how
    #: little. Without this the count said 4 and the image said 1.
    ocomp = {}
    for i, oc in enumerate(ocs):
        for o in oc:
            ocomp[o] = i
    #: A word node has no component of its own; it takes the one of the operation
    #: at the other end. So a link is CROSSING only when the model that word
    #: belongs to touches operations in more than one component -- it is that
    #: model that is the bridge. The lowest-numbered component it touches is
    #: treated as its home, and every link it has into any other one is marked.
    home = {}
    for o in OPS:
        for m in mods[o]:
            home[m] = min(home.get(m, ocomp[o]), ocomp[o])
    links = []
    for a, b in G.edges():
        op = a if a in OPS else b
        model = (b if a in OPS else a).split("::")[0]
        links.append({"source": a, "target": b,
                      "cross": ocomp[op] != home.get(model, ocomp[op])})
    #: THE INVARIANT THAT FAILED. If k split a component that k=1 held together,
    #: some model bridges two components by construction, so there is at least
    #: one crossing link. Zero crossings with fewer components at k=1 is not a
    #: quiet graph, it is a broken flag.
    n_cross = sum(1 for l in links if l["cross"])
    assert n_at1 is None or len(ocs) == n_at1 or n_cross > 0, \
        "k=%d gives %d components against %d at k=1, yet no link crosses a boundary" \
        % (k, len(ocs), n_at1)
    #: REVERSALS ARE CARRIED, NOT DROPPED. A reversed model is one the rater says
    #: runs the operation BACKWARDS, so it must not be a member -- it would put
    #: the opposite movement inside the cluster the operation names -- but it is
    #: a judgement ABOUT that operation and belongs on the panel beside it. The
    #: UI draws it as a red dashed line from the model to the operation.
    #:
    #: Measured over the three 47-50 lineage prompts: a reversed model is NEVER
    #: also placed in the same reading, so this cannot double-count a model, and
    #: reversals attach almost exclusively to a reading's largest operation --
    #: which is what "reversed" means here, the dominant relation run backwards.
    revs = []
    for tag, v in pairs:
        names = {o["name"] for o in v.get("operations") or []}
        for r in v.get("reversed") or []:
            #: A reversal cites an operation name from its OWN reading. If the
            #: name does not resolve, the rater named something they never
            #: defined and the red line would point at nothing. Refuse: a line
            #: to a missing hub is the silent-drop failure with a colour on it.
            assert r["operation"] in names, \
                "%s: reversed model %r cites operation %r, which that reading does not define" \
                % (tag, r["model"], r["operation"])
            #: ORDERED BY PROMINENCE ON THEIR OWN SIDE and carrying the numbers,
            #: so even a consumer that only joins the list prints something
            #: meaningful. A word with no table row keeps its place at the end
            #: rather than vanishing.
            def ranked(ws, side):
                out = []
                for w in [x.lower() for x in ws or []]:
                    d = rk(r["model"], w) or {}
                    out.append({"w": w, "r": d.get("ra" if side == "a" else "rb"),
                                "o": d.get("rb" if side == "a" else "ra"),
                                "p": d.get("pa" if side == "a" else "pb")})
                return sorted(out, key=lambda x: (x["r"] is None, x["r"] or 0))
            ra_, rb_ = ranked(r.get("a_words"), "a"), ranked(r.get("b_words"), "b")
            revs.append({"model": r["model"], "op": "OP[%s] %s" % (tag, r["operation"]),
                         "reading": tag, "a": ra_, "b": rb_,
                         "a_words": [x["w"] for x in ra_],
                         "b_words": [x["w"] for x in rb_],
                         "how_you_know": r.get("how_you_know") or ""})
    nid = {n["id"] for n in nodes}
    miss = sorted({r["op"] for r in revs} - nid)
    assert not miss, "reversal(s) pointing at a node that is not in the graph: %s" % miss[:3]
    cov = []
    for tag, v in pairs:
        inops = {m["model"] for o in v.get("operations") or [] for m in o.get("members") or []}
        cov.append({"reading": tag, "placed": len(inops),
                    "reversed": len(v.get("reversed") or []),
                    "unassigned": len(v.get("unassigned") or [])})
    #: THE COVERAGE TABLE AND THE RED LINES COUNT THE SAME THING. `cov` has always
    #: printed a `reversed` column; now something is drawn from the same field, and
    #: a panel showing 13 lines beside a table saying 5 is the mismatch no reader
    #: would suspect, because both would be internally consistent.
    assert len(revs) == sum(c["reversed"] for c in cov), \
        "%d reversal(s) to draw against %d in the coverage table" \
        % (len(revs), sum(c["reversed"] for c in cov))
    art = graph(
        title=prompt,
        #: THE THRESHOLD IS DECLARED. Components here are over OPERATIONS, joined
        #: only where they share >= k models. At k=1 -- sharing a SINGLE model --
        #: every prompt collapses further, and on insurance the transgressive
        #: pair is swallowed by the main blob through the very two models it is
        #: about. A reader who does not know k cannot read the component count.
        subtitle=("%d operations from %d reading(s), pooled. An operation is a NODE, and two "
                  "operations are in one component only if they share at least k=%d models "
                  "(at k=1 there would be %s). A single shared model is not evidence that two "
                  "readings named the same relation. Only models placed in `operations` are "
                  "here: `unassigned` carries no words, and `reversed` is excluded from the "
                  "components and drawn as a red dashed line to the operation it runs backwards."
                  % (len(OPS), len(pairs), k,
                     "%d component(s)" % n_at1 if n_at1 is not None else "fewer")),
        nodes=nodes, links=links,
        groups=[{"key": t, "label": t, "colour": PAL[i % len(PAL)]} for i, t in enumerate(tags)],
        meta={"components": [{"operations": sum(1 for x in c if x in OPS),
                              "models": len({x.split("::")[0] for x in c if "::" in x})}
                             for c in cc],
              "coverage": cov, "prompt": prompt, "k": k, "components_at_k1": n_at1,
              "reversals": revs, "ranked": bool(SC)})
    slug = re.sub(r"[^a-z0-9]+", "_", prefix.lower())[:34].strip("_")
    return write(art, os.path.join(HERE, "figures"), "opgraph_%s" % slug)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("prefix", nargs="?")
    ap.add_argument("--n-lineages", type=int, default=None)
    ap.add_argument("--png", action="store_true")
    ap.add_argument("-k", type=int, default=2,
                    help="models two operations must share to be joined (default 2; "
                         "1 reproduces the old shared-a-single-model behaviour)")
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
            analyse(p, a.n_lineages, a.png, a.report, a.data, a.k); print("-" * 78)
        return
    if not a.prefix:
        raise SystemExit("give a prompt prefix, or --all")
    analyse(a.prefix, a.n_lineages, a.png, a.report, a.data, a.k)


if __name__ == "__main__":
    main()
