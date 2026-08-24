"""Do cross-frame relations respect the site/control boundary? Ask without asking.

    python pair_meta.py --doc            # build the grouping document (writes once)
    python pair_meta.py --workflow       # a runner for it, per rater model/effort
    python pair_meta.py --purity         # the measurement, once groupings exist

## WHAT THIS TESTS THAT `compare_pairs.py` COULD NOT

`compare_pairs` measured the SHAPE of each frame's reading -- components,
largest component, reversals -- and returned a null: nothing about shape
separates a frame carrying 15-53% transgressive mass from the same sentence one
word away carrying 2-5%. I then said the CONTENT differs, controls doing
inspection and verification while sites soften violence, and I got that by
reading operation names off a screen. That is an eyeball inference and this is
the instrument that tests it.

## THE OUTCOME IS DERIVED, NEVER ELICITED

The annotator is told nothing about pairs, sites, controls, or transgressive
mass. It receives the same task the frozen 89-component document received: group
these entries by the MOVEMENT they describe, and do not group them merely for
sharing a subject. Role composition is computed afterwards, from the pending
file, over groups the annotator formed for its own reasons.

That matters because the alternative -- asking whether two entries come from
'the same kind of frame' -- supplies the hypothesis in the question.

## AND THE INSTRUMENT PROVES IN ONE DIRECTION ONLY

You cannot blind an annotator to whether `raped` sits in the from-words. The
pairs are one word apart, so role is trivially readable off the material, and a
ROLE-PURE result is therefore ambiguous: it is consistent with the relations
genuinely differing AND with the annotator having sorted by conspicuous content
in spite of being told not to. A ROLE-MIXED result has no such alternative
reading -- an annotator that could trivially separate them and did not is
evidence that the relation crosses the boundary.

Half the outcome space is uninformative. That is stated here rather than
discovered afterwards, because a limitation found after a result is
indistinguishable from an excuse for it.

## THE NULL IS PAIRED, BECAUSE THE DESIGN IS

Components inherit their role from their frame, and a frame contributes several,
so shuffling role labels across COMPONENTS would break the frame clustering and
give a null that is too easy to beat. The randomisation the design licenses is
flipping which arm of each PAIR is called the site -- 2^10 = 1,024 assignments
for ten pairs, enumerated exactly rather than sampled.
"""
import argparse
import collections
import hashlib
import itertools
import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, "/Users/rj416/github/malignment")
import cross_frame as CF  # noqa: E402
import operation_graph as OG  # noqa: E402
import ingest_pending as IP  # noqa: E402

PENDING = os.path.join(HERE, "results", "pending_ingest_controlpairs_20260823.tsv")
DOC = os.path.join(HERE, "results", "inputs", "crossframe_pairs.txt")
IDS = os.path.join(HERE, "results", "crossframe_pairs_components.json")

#: THE TWO PAIRS RUN BEFORE THE EIGHT, which are not in the pending file because
#: they were launched one at a time as an ad hoc batch. Named here rather than
#: recovered by pattern: `dragged`/`helped` and `pinned`/`guided` are pairs by
#: construction in `transgressive_swap`, and nothing in the stash records that.
EXTRA = [("They dragged the driver out of the car and",
          "They helped the driver out of the car and"),
         ("He pinned his roommate to the floor and",
          "He guided his roommate to the floor and")]

#: RUN, READ AND EXCLUDED FROM THE PAIRED TEST. `She was so angry she wanted to`
#: is RH's ad hoc frame and has no control arm, so its components cannot enter a
#: statistic whose randomisation is "flip which arm of this pair is the site".
#: It stays OUT of the document as well: an entry the annotator groups and the
#: analysis then drops is material spent buying nothing, and worse, it would sit
#: in a group and change that group's purity while belonging to no pair.
UNPAIRED = ["She was so angry she wanted to"]


def pairs():
    """`[(site, control)]` -- every complete pair, from the pending file plus EXTRA."""
    rows = IP.pending(PENDING)
    out = [(rows[i]["prompt"], rows[i + 1]["prompt"]) for i in range(0, len(rows) - 1, 2)]
    for i in range(0, len(rows) - 1, 2):
        assert rows[i]["role"] == "SITE" and rows[i + 1]["role"] == "CONTROL", \
            "pending file is not in SITE/CONTROL order at row %d" % i
    out += EXTRA
    seen = [p for pr in out for p in pr]
    assert len(set(seen)) == len(seen), "a prompt appears in two pairs"
    return out


def roles():
    """`{prompt: ('SITE'|'CONTROL', pair_index)}` over the paired frames only."""
    r = {}
    for i, (s, c) in enumerate(pairs()):
        r[s] = ("SITE", i)
        r[c] = ("CONTROL", i)
    return r


def build():
    """Components over the paired frames, ids prefixed `P` so they cannot resolve
    against the frozen 89-component document."""
    R = roles()
    cs = CF.components(only=set(R))
    missing = sorted(set(R) - {c["prompt"] for c in cs})
    #: REFUSE ON A MISSING ARM. A pair with one arm in the document is not a
    #: smaller version of the design, it is an unpaired entry that would enter a
    #: group and move its purity while belonging to no pair -- the same defect
    #: UNPAIRED is excluded for, arrived at by accident instead of by choice.
    assert not missing, "no components for %d frame(s): %s" % (len(missing), missing)
    for i, c in enumerate(cs, 1):
        c["id"] = "P%02d" % i
        c["role"], c["pair"] = R[c["prompt"]]
    return cs


def document():
    cs = build()
    sc = {c["prompt"]: (OG.sidecar(c["prompt"], no_blanks=c.get("no_blanks", False)) or {})
          for c in cs}
    blocks = []
    for c in cs:
        f = lambda ps: "; ".join("%s (%d | %s>%s)" % x for x in ps) or "-"
        names = "\n".join("     [%s]  %s  (%d systems)\n           %s" % (t, nm, k, stx)
                          for t, nm, stx, k in c["names"])
        blocks.append("%s   sentence: %s\n     %d systems\n%s\n     FROM  %s\n     TO    %s"
                      % (c["id"], c["prompt"], c["n_models"], names,
                         f(CF.pooled_words(c["_members"], "a", sc[c["prompt"]])),
                         f(CF.pooled_words(c["_members"], "b", sc[c["prompt"]]))))
    return cs, CF.TASK % (len(cs), "\n\n".join(blocks))


def write_doc(force=False):
    if os.path.exists(DOC) and not force:
        raise SystemExit("%s exists. The document is the record: a later rating is "
                         "comparable only if it read the same bytes. --force to "
                         "replace it, which invalidates every grouping of it." % DOC)
    cs, txt = document()
    os.makedirs(os.path.dirname(DOC), exist_ok=True)
    open(DOC, "w").write(txt)
    #: THE ROLE MAP IS SAVED BESIDE THE DOCUMENT AND NOT RECOMPUTED. Ids are
    #: positional over a sorted population, so a later `build()` on a changed
    #: stash could renumber, and a grouping's ids would then resolve to the wrong
    #: components -- silently, since ids always look valid. This is the same
    #: failure `cross_frame.as_read` exists to prevent for the 89.
    json.dump([{k: c[k] for k in ("id", "prompt", "role", "pair", "n_models")}
               | {"names": [n[1] for n in c["names"]]} for c in cs],
              open(IDS, "w"), indent=1)
    n_site = sum(1 for c in cs if c["role"] == "SITE")
    print("%d components over %d frames (%d pairs), %d chars (~%d tokens)"
          % (len(cs), len({c["prompt"] for c in cs}), len(pairs()),
             len(txt), len(txt) // 4))
    print("  %d from SITE arms, %d from CONTROL arms" % (n_site, len(cs) - n_site))
    print("  md5 %s" % hashlib.md5(txt.encode()).hexdigest())
    print("  document %s\n  id map   %s" % (DOC, IDS))


def workflow(raters=1, model="opus", effort="high"):
    txt = open(DOC).read()
    cs = json.load(open(IDS))
    n_in_doc = sum(1 for l in txt.splitlines() if l.startswith("P") and "sentence:" in l)
    assert n_in_doc == len(cs), \
        "document holds %d components, the id map holds %d" % (n_in_doc, len(cs))
    js = CF.SCRIPT % {"raters": raters, "n": len(cs),
                      "path": json.dumps(os.path.abspath(DOC)),
                      "schema": json.dumps(CF.SCHEMA, indent=2, sort_keys=True),
                      "model": json.dumps(model), "effort": json.dumps(effort)}
    out = os.path.join(HERE, "workflow_pairmeta_%s_%s.js" % (model, effort))
    open(out, "w").write(js)
    for probe in (os.path.abspath(DOC), '"singletons"', model, effort):
        assert probe in js, "generated script missing %r" % probe
    print("%d components, %d chars (~%d tokens), %d rater(s), %s %s"
          % (len(cs), len(txt), len(txt) // 4, raters, model, effort))
    print("  md5 %s  (NOT regenerated)" % hashlib.md5(txt.encode()).hexdigest())
    print("  workflow %s\n\nNOT RUN." % out)
    return out


def purity(groups, role, min_n=2):
    """Mean role purity over groups of at least `min_n` members.

    Purity of a group is the share of its members from whichever arm is more
    common in it, so a group split evenly scores 0.5 and a group drawn from one
    arm scores 1.0. Singletons are excluded because their purity is 1.0 by
    definition and would report the annotator's willingness to leave things
    ungrouped as evidence about roles.
    """
    vs, sizes = [], []
    for g in groups:
        ms = [m for m in g if m in role]
        if len(ms) < min_n:
            continue
        n = collections.Counter(role[m] for m in ms)
        vs.append(max(n.values()) / len(ms))
        sizes.append(len(ms))
    return (statistics.mean(vs) if vs else None), len(vs), sizes


def test(path, min_n=2):
    """Observed purity against the exact paired null: flip each pair's labels."""
    cs = json.load(open(IDS))
    by = {c["id"]: c for c in cs}
    g = json.load(open(path))
    groups = [x["members"] for x in g.get("groups", g if isinstance(g, list) else [])]
    role = {c["id"]: c["role"] for c in cs}
    obs, ng, sizes = purity(groups, role, min_n)
    if obs is None:
        return dict(obs=None, n_groups=0)
    npairs = 1 + max(c["pair"] for c in cs)
    #: EXACT, NOT SAMPLED. 2^10 = 1,024 label assignments, so there is no reason
    #: to approximate and every reason not to: a sampled null at this size
    #: reports a p that moves between runs of the same analysis.
    null = []
    for flips in itertools.product((0, 1), repeat=npairs):
        r = {cid: (c["role"] if not flips[c["pair"]] else
                   ("CONTROL" if c["role"] == "SITE" else "SITE"))
             for cid, c in by.items()}
        v, _, _ = purity(groups, r, min_n)
        if v is not None:
            null.append(v)
    p = sum(1 for x in null if x >= obs) / len(null)
    return dict(obs=obs, n_groups=ng, sizes=sizes, npairs=npairs,
                null_med=statistics.median(null), n_null=len(null), p=p,
                mixed=sum(1 for gg in groups
                          if len({role[m] for m in gg if m in role}) > 1))


PAIR_RATERS = [("opus-high", "crossframe_pairs_101_opus_high.json"),
               ("opus-xhigh", "crossframe_pairs_101_opus_xhigh.json"),
               ("opus-med", "crossframe_pairs_101_opus_medium.json")]

ROLE_COLOUR = {"SITE": "#fa5252", "CONTROL": "#4dabf7"}


def emit_graph(out="pairmeta"):
    """The paired meta-relation network, coloured by ROLE not by domain.

    Reuses `MetaGraph.svelte` from the 89-component metagraph by producing the
    same artifact shape. Nodes carry `group` as the role label and the colour
    map uses SITE=red, CONTROL=blue so mixed groups are visually obvious.
    """
    import json as _json, itertools as _it
    from malignment.chartdata import graph, write
    cs_map = {c["id"]: c for c in _json.load(open(IDS))}
    cs_full = {c["id"]: c for c in build()}
    rs = [(lab, _json.load(open(os.path.join(HERE, "results", f))))
          for lab, f in PAIR_RATERS]
    sc = {}
    nodes, links, seen = [], [], set()
    cap = 10

    def words(model, ws, side, rows):
        key = "rank_a" if side == "a" else "rank_b"
        out = []
        for w in [x.lower() for x in (ws or [])]:
            r = rows.get(w) or rows.get(w.capitalize()) or {}
            out.append({"w": w, "ra": r.get("rank_a"), "rb": r.get("rank_b"),
                        "k": r.get(key)})
        out.sort(key=lambda x: (x["k"] is None, x["k"] or 0))
        return [{"w": x["w"], "ra": x["ra"], "rb": x["rb"]} for x in out[:cap]]

    def leaf(cid):
        if cid in seen or cid not in cs_full:
            return
        seen.add(cid)
        c = cs_full[cid]
        meta = cs_map.get(cid, {})
        if c["prompt"] not in sc:
            sc[c["prompt"]] = OG.sidecar(c["prompt"], no_blanks=c.get("no_blanks", False)) or {}
        rows_by = sc[c["prompt"]]
        rels = []
        for t, o in c["_ops"]:
            mem = []
            for m in sorted(o.get("members") or [], key=lambda m: m["model"]):
                r = rows_by.get(m["model"]) or {}
                mem.append({"model": m["model"],
                            "from": words(m["model"], m.get("a_words"), "a", r),
                            "to": words(m["model"], m.get("b_words"), "b", r)})
            rels.append({"name": o["name"], "reading": t,
                         "statement": o.get("statement") or "",
                         "n": len(o.get("members") or []), "members": mem})
        nodes.append({"id": "%s::%s" % (c["prompt"], cid), "kind": "word", "label": cid,
                      "group": meta.get("role", "?"), "model": c["prompt"], "side": "to",
                      "component": 0, "cid": cid, "sentence": c["prompt"],
                      "n_models": c["n_models"], "stripped": bool(c.get("no_blanks")),
                      "role": meta.get("role"), "pair": meta.get("pair"),
                      "relations": rels})

    for lab, G in rs:
        for g in G["groups"]:
            hid = "META[%s] %s" % (lab, g["name"])
            member_roles = collections.Counter(
                cs_map[m]["role"] for m in g["members"] if m in cs_map)
            nodes.append({"id": hid, "kind": "op", "label": g["name"], "group": None,
                          "rater": lab, "component": 0, "n": len(g["members"]),
                          "statement": g.get("statement", ""), "spans": g.get("spans", ""),
                          "why": g.get("why", ""),
                          "sentences": len({cs_map[m]["prompt"] for m in g["members"] if m in cs_map}),
                          "roles": dict(member_roles),
                          "models": sorted(m for m in g["members"] if m in cs_map)})
            for m in g["members"]:
                leaf(m)
                if m in cs_full:
                    links.append({"source": "%s::%s" % (cs_full[m]["prompt"], m),
                                  "target": hid, "cross": len(member_roles) > 1})
        for cid in G.get("singletons") or []:
            leaf(cid)

    hub_ids = [n["id"] for n in nodes if n["kind"] == "op"]
    mem = {h: set(g) for h, g in
           ((n["id"], n["models"]) for n in nodes if n["kind"] == "op")}
    import networkx as _nx
    Q = _nx.Graph()
    Q.add_nodes_from(hub_ids)
    for a, b in _it.combinations(sorted(hub_ids), 2):
        if a.split("]")[0] != b.split("]")[0] and len(mem[a] & mem[b]) >= CF.K_BRIDGE:
            Q.add_edge(a, b)
    home = {}
    for i, c in enumerate(_nx.connected_components(Q)):
        for h in c:
            home[h] = i
    by_leaf = collections.defaultdict(list)
    for l in links:
        by_leaf[l["source"]].append(l)
    for sid, ls in by_leaf.items():
        cnt = collections.Counter(home.get(l["target"]) for l in ls)
        mine = cnt.most_common(1)[0][0] if cnt else None
        for l in ls:
            l["weak"] = home.get(l["target"]) != mine

    n_site = sum(1 for n in nodes if n["kind"] == "word" and n.get("role") == "SITE")
    n_ctrl = sum(1 for n in nodes if n["kind"] == "word" and n.get("role") == "CONTROL")
    n_mixed = sum(1 for n in nodes if n["kind"] == "op" and n.get("roles", {}).get("SITE") and n.get("roles", {}).get("CONTROL"))
    art = graph(
        title="Matched-pair meta-relations",
        subtitle=("101 components from 10 matched pairs (one word apart), grouped by three "
                  "blind raters told nothing about roles. Leaves coloured by ROLE: "
                  "red = SITE (55), blue = CONTROL (46). A hub whose leaves are "
                  "one colour is role-pure; mixed hubs are the evidence that "
                  "the relation crosses the site/control boundary. "
                  "%d of %d groups are role-mixed."
                  % (n_mixed, len([n for n in nodes if n["kind"] == "op"]))),
        nodes=nodes, links=links,
        groups=[{"key": k, "label": "%s (%d)" % (k, {"SITE": n_site, "CONTROL": n_ctrl}[k]),
                 "colour": v} for k, v in ROLE_COLOUR.items()],
        meta={"chart_hint": "metagraph", "raters": len(rs),
              "components": [{"operations": len([n for n in nodes if n["kind"] == "op"]),
                              "models": len(seen)}]})
    art["chart"] = "metagraph"
    return write(art, os.path.join(HERE, "figures"), out)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--doc", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--workflow", action="store_true")
    ap.add_argument("--raters", type=int, default=1)
    ap.add_argument("--model", default="opus")
    ap.add_argument("--effort", default="high")
    ap.add_argument("--graph", action="store_true",
                    help="write the paired meta-relation network artifact")
    ap.add_argument("--purity", nargs="*", metavar="GROUPING.json")
    ap.add_argument("--min-n", type=int, default=2)
    a = ap.parse_args()
    if a.graph:
        emit_graph()
        return
    if a.doc:
        return write_doc(a.force)
    if a.workflow:
        return workflow(a.raters, a.model, a.effort)
    if a.purity is not None:
        print("ROLE PURITY OF CROSS-FRAME GROUPS, against the exact paired null\n")
        print("  A group's purity is the share of its members from the more common")
        print("  arm. High means relations respect the site/control boundary; at or")
        print("  below the null means they cross it.\n")
        print("  %-30s %7s %8s %8s %7s %7s"
              % ("grouping", "groups", "purity", "null", "mixed", "p"))
        for f in a.purity:
            r = test(f, a.min_n)
            if r["obs"] is None:
                print("  %-30s  -- no group of >= %d --" % (os.path.basename(f), a.min_n))
                continue
            print("  %-30s %7d %8.3f %8.3f %7d %7.3f"
                  % (os.path.basename(f)[:30], r["n_groups"], r["obs"],
                     r["null_med"], r["mixed"], r["p"]))
        print("\n  Null: flip which arm of each pair is the SITE, all %d assignments"
              % (2 ** (1 + max(c["pair"] for c in json.load(open(IDS))))))
        print("  enumerated. A ROLE-MIXED result is clean; a role-PURE one is")
        print("  ambiguous between real difference and the annotator sorting by")
        print("  conspicuous content. See this file's header.")
        return
    ap.error("one of --doc, --workflow, --purity")


if __name__ == "__main__":
    main()
