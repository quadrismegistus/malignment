"""Six annotators' categories over the 220 components, as a bipartite network.

    python -u annotator_graph.py            the clusters at k=3
    python -u annotator_graph.py --sweep    the threshold sweep
    python -u annotator_graph.py --cluster 2   one cluster, every category in it
    python -u annotator_graph.py --emit     -> figures/annotator_metagraph.data.json

## A SECOND METAGRAPH, NOT A REPLACEMENT

`cross_frame.emit_graph()` writes `figures/metagraph.data.json`: 89 components
grouped by ONE blind reader, hubs coloured by the domain their leaves came from.
This writes `figures/annotator_metagraph.data.json` from the same `chartdata`
helpers and the same `chart="metagraph"` renderer, over a different population:
220 corroborated components grouped by SIX annotators -- Opus and Fable at three
effort levels each. Both artifacts stay; the UI gains a second view rather than
losing the first. `pair_meta.py` already reuses `MetaGraph.svelte` this way.

## WHY BIPARTITE, AND WHY IT COLLAPSES WITHOUT A THRESHOLD

Nodes are CATEGORIES (one per annotator per group, carrying the annotator) and
OPERATIONS (the CP components, carrying frame and names). An edge is membership.

Taken plainly the graph has 4 connected components and one of them holds 210 of
the 220 operations: six annotators each partition the whole corpus, so their
categories chain through shared members until everything fuses. That is the same
collapse `K_BRIDGE` exists to prevent one layer up.

So the object of interest is the PROJECTION: two categories from DIFFERENT
annotators are joined when they share at least `k` operations, and a cluster is
a connected component of that. At k=3 -- the taxonomy's own threshold -- this
gives 20 clusters, 16 of them carrying all six annotators, covering 205 of 220
operations.

## WHAT THE COMPARISON IS WORTH

The raters' hub graph at k=3 covers 70 of 86 components (19% unplaced); this
covers 205 of 220 (7%). And 16 clusters carry all six annotators, where the ten
needed three raters plus one merge nobody recorded. That is a stronger
corroboration standard, on a corpus two and a half times larger.

It is NOT six independent witnesses. Three of the six are one model at three
effort levels and three are another, and the pairwise ARI matrix shows effort
moves a partition about as far as changing model does. Read "6/6 annotators" as
"both families at every effort", not as six votes.
"""
import argparse, collections, itertools, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
AG = os.path.join(HERE, "results", "agent_groupings")
REMAP = os.path.join(AG, "cp_id_shipped_to_canonical.json")
K = 3

RUNS = {"opus high": "opus-agent", "opus xhigh": "opus-xhigh",
        "opus max": "opus-max", "fable high": "fable-high",
        "fable xhigh": "fable-xhigh", "fable max": "fable-max"}
#: one hue per family, lightening with effort, so the picture reads as two
#: families before it reads as six runs
COLOUR = {"opus high": "#1864ab", "opus xhigh": "#4dabf7", "opus max": "#a5d8ff",
          "fable high": "#a61e4d", "fable xhigh": "#e64980", "fable max": "#faa2c1"}


def load():
    """-> (categories {id: (annotator, ops, name, group)}, components {id: rec})"""
    import yaml
    import export_909 as E
    remap = json.load(open(REMAP))
    comps = {c["id"]: c for c in E.components()}
    cat = {}
    for run, f in RUNS.items():
        d = yaml.safe_load(open(os.path.join(AG, "%s_components_groups.yaml" % f)))
        for g in d["groups"]:
            #: **THE AGENT YAMLs CARRY THE SHIPPED NUMBERING.** 78 of 220 CP ids
            #: moved when `op_components` was made deterministic; every id is
            #: translated here rather than at the call site, so no consumer can
            #: forget to.
            cat["%s :: %s" % (run, g["name"])] = {
                "annotator": run, "name": g["name"],
                "ops": set(remap.get(m, m) for m in g["members"]),
                "statement": g.get("statement", ""),
                "spans": g.get("spans", ""), "why": g.get("why", "")}
    return cat, comps


def clusters(cat, k=K):
    """Connected components of the category projection at threshold k. -> [set]"""
    import networkx as nx
    Q = nx.Graph()
    Q.add_nodes_from(cat)
    for a, b in itertools.combinations(sorted(cat), 2):
        #: DIFFERENT ANNOTATORS ONLY. Two categories from one run are two things
        #: that run chose to keep apart, and joining them here would undo its
        #: judgement with its own evidence.
        if cat[a]["annotator"] != cat[b]["annotator"] \
                and len(cat[a]["ops"] & cat[b]["ops"]) >= k:
            Q.add_edge(a, b)
    out = [sorted(c) for c in nx.connected_components(Q) if len(c) >= 2]
    return sorted(out, key=lambda c: (-len(set().union(*[cat[x]["ops"] for x in c])), c))


def domains():
    """CP id -> domain, for colouring the leaves as the first metagraph does."""
    import csv
    dom = {}
    for r in csv.DictReader(open(os.path.join(HERE, "results", "word_groups.csv"))):
        dom[r["prompt"]] = r["domain"]
    for x in json.load(open(os.path.join(HERE, "results", "crossframe_ops.json"))):
        dom.setdefault(x["prompt"], x.get("domain"))
    return dom


def emit(out="annotator_metagraph", k=K):
    """Write the artifact beside the first metagraph, not over it."""
    from malignment.chartdata import graph, write
    cat, comps = load()
    dom = domains()
    cl = clusters(cat, k)
    home = {}
    for i, c in enumerate(cl):
        for x in c:
            home[x] = i
    nodes, links, seen = [], [], set()
    for cid, c in comps.items():
        d = dom.get(c["frame"])
        nodes.append({"id": "%s::%s" % (c["frame"], cid), "kind": "leaf",
                      "label": cid, "group": d, "rater": None,
                      "component": None, "n": c["n"],
                      "statement": " / ".join(c["names"]),
                      "spans": c["frame"], "why": "",
                      "sentences": 1, "domains": {d: 1} if d else {},
                      "models": []})
        seen.add("%s::%s" % (c["frame"], cid))
    for key, v in cat.items():
        hid = "CAT[%s] %s" % (v["annotator"], v["name"])
        nodes.append({"id": hid, "kind": "op", "label": v["name"],
                      "group": None, "rater": v["annotator"],
                      "component": home.get(key), "n": len(v["ops"]),
                      "statement": v["statement"], "spans": v["spans"],
                      "why": v["why"], "sentences": len({comps[o]["frame"]
                                                         for o in v["ops"]
                                                         if o in comps}),
                      "domains": dict(collections.Counter(
                          dom.get(comps[o]["frame"]) for o in v["ops"]
                          if o in comps and dom.get(comps[o]["frame"]))),
                      "models": sorted(v["ops"])})
        for o in v["ops"]:
            if o not in comps:
                continue
            lid = "%s::%s" % (comps[o]["frame"], o)
            #: `graph()` asserts every endpoint resolves -- a dangling link does
            #: not raise in d3, it silently drops and the picture draws with
            #: fewer edges than it has
            if lid in seen:
                links.append({"source": lid, "target": hid,
                              "cross": len(set(
                                  dom.get(comps[x]["frame"])
                                  for x in v["ops"] if x in comps)) > 1,
                              "weak": home.get(key) is None})
    six = sum(1 for c in cl if len({cat[x]["annotator"] for x in c}) == 6)
    cov = len(set().union(*[cat[x]["ops"] for c in cl for x in c]))
    dc = collections.Counter(d for d in (dom.get(c["frame"])
                                         for c in comps.values()) if d)
    art = graph(
        title="Six annotators over the corroborated components",
        subtitle=("%d categories from six annotators -- Opus and Fable at three "
                  "effort levels each -- over %d corroborated components from "
                  "%d sentences. A leaf is a component, coloured by the domain "
                  "it came from; a hub is one annotator's category, coloured by "
                  "which annotator named it. Joining two categories from "
                  "different annotators that share at least %d components gives "
                  "%d clusters, %d of them carrying all six, covering %d of the "
                  "%d components. Unclustered categories are drawn attached but "
                  "weak, because a corpus with unplaceable categories should not "
                  "look tidier than it is."
                  % (len(cat), len(comps),
                     len({c["frame"] for c in comps.values()}), k,
                     len(cl), six, cov, len(comps))),
        nodes=nodes, links=links,
        groups=([{"key": kk, "label": "%s (%d)" % (kk, dc[kk]),
                  "colour": v} for kk, v in
                 (("sexual", "#fa5252"), ("violence", "#e8590c"),
                  ("institutional", "#4dabf7"), ("identity", "#51cf66"))
                 if kk in dc]
                + [{"key": a, "label": a, "colour": COLOUR[a]} for a in RUNS]),
        meta={"chart_hint": "metagraph", "raters": len(RUNS), "k_bridge": k,
              "components": [{"operations": len(cl), "models": len(comps)}]})
    art["chart"] = "metagraph"
    return write(art, os.path.join(HERE, "figures"), out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--k", type=int, default=K)
    ap.add_argument("--sweep", action="store_true")
    ap.add_argument("--cluster", type=int, default=None)
    ap.add_argument("--emit", action="store_true")
    a = ap.parse_args(argv)
    cat, comps = load()
    if a.emit:
        print("wrote %s" % emit(k=a.k))
        return 0
    if a.sweep:
        print("  %s %9s %9s %12s %13s %12s" %
              ("k", "clusters", ">=2 cats", "all 6", "largest(ops)", "ops covered"))
        for k in range(1, 8):
            cl = clusters(cat, k)
            six = sum(1 for c in cl if len({cat[x]["annotator"] for x in c}) == 6)
            cov = set().union(*[cat[x]["ops"] for c in cl for x in c]) if cl else set()
            big = max((len(set().union(*[cat[x]["ops"] for x in c])) for c in cl),
                      default=0)
            print("  %d %9d %9d %12d %13d %9d/%d"
                  % (k, len(cl), len(cl), six, big, len(cov), len(comps)))
        return 0
    cl = clusters(cat, a.k)
    if a.cluster is not None:
        c = cl[a.cluster - 1]
        ops = set().union(*[cat[x]["ops"] for x in c])
        print("cluster %d: %d operations, %d sentences, %d categories\n"
              % (a.cluster, len(ops),
                 len({comps[o]["frame"] for o in ops if o in comps}), len(c)))
        for x in sorted(c, key=lambda x: cat[x]["annotator"]):
            print("  %-12s %s" % (cat[x]["annotator"], cat[x]["name"]))
            if cat[x]["statement"]:
                print("       %s" % cat[x]["statement"][:96])
        return 0
    six = sum(1 for c in cl if len({cat[x]["annotator"] for x in c}) == 6)
    print("%d categories, %d components, k=%d -> %d clusters (%d with all six)\n"
          % (len(cat), len(comps), a.k, len(cl), six))
    for i, c in enumerate(cl, 1):
        ops = set().union(*[cat[x]["ops"] for x in c])
        ann = sorted({cat[x]["annotator"] for x in c})
        print("  %2d. %3d ops %3d sentences %d/6 annotators %2d cats   %s"
              % (i, len(ops),
                 len({comps[o]["frame"] for o in ops if o in comps}),
                 len(ann), len(c),
                 collections.Counter(cat[x]["name"] for x in c).most_common(1)[0][0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
