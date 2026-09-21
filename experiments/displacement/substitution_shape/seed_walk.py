"""Walk the substitution graph OUTWARD from the most charged words.

    python -u seed_walk.py                        # top 10 verbs, raw arm
    python -u seed_walk.py --pos NOUN --top 10
    python -u seed_walk.py --top 20 --arm framed

Seeds are the `--top` words of one part of speech, ranked by their own charge
lift (`lift_words.py` -> `results/words_by_lift.csv`). From each seed the walk
follows ONLY OUTWARD edges, faller -> riser, transitively: where does the
charge go, and where does it end up.

**OUTWARD ONLY IS THE WHOLE POINT.** An undirected walk from `kill` reaches
everything that ever fell to anything `kill` fell to, which is most of the
graph and says nothing. Following the arrow asks a directed question -- what
replaces this, and what replaces that -- so the walk drains toward whatever
alignment treats as a destination rather than spreading over neighbours.

## POS IS MODAL OVER THE WORD'S OWN SLOTS

A word is tagged in each prompt it appears in (`malignment.pos.get_pos`, which
tags `prompt + " " + word` and takes the last token) and the word's POS here is
the most common of those. A type-level tagger is not a substitute: this corpus
is verbs at a blank after a subject, exactly where one reads `kiss`, `strike`
and `punch` as nouns.

## A SEED WITH NO OUT-EDGE IS REPORTED, NOT DROPPED

Several of the most charged words never fall -- `rob` rises once and falls
never -- so they seed nothing. That is a fact about them and it is printed.
"""
import argparse, collections, csv, os, statistics as st, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import graph as G  # noqa: E402


def modal_pos(rows):
    """{word: most common POS over the prompts it appears in}"""
    tag = G.slot_pos(rows)
    acc = collections.defaultdict(collections.Counter)
    for r in rows:
        for k in ("faller", "riser"):
            acc[r[k]][tag[(r["prompt"], r[k])]] += 1
    return {w: c.most_common(1)[0][0] for w, c in acc.items()}


def lifts(min_prompts):
    """{word: lift_med_med} from the CSV, above a prompt-count floor."""
    p = os.path.join(HERE, "results", "words_by_lift.csv")
    if not os.path.exists(p):
        raise SystemExit("run lift_words.py first: %s is missing" % p)
    out = {}
    for r in csv.DictReader(open(p, encoding="utf-8")):
        if int(r["n_prompts"]) >= min_prompts:
            out[r["word"]] = float(r["lift_med_med"])
    return out


def reach(E, seeds):
    """-> (reached nodes, edges among them) following out-edges only."""
    adj = collections.defaultdict(list)
    for (f, t) in E:
        adj[f].append(t)
    seen, stack = set(), list(seeds)
    while stack:
        x = stack.pop()
        if x in seen:
            continue
        seen.add(x)
        stack.extend(adj.get(x, ()))
    return seen, {(f, t): n for (f, t), n in E.items()
                  if f in seen and t in seen}


def components(nodes, E):
    """Weakly connected components of the reached subgraph. -> [set]"""
    par = {x: x for x in nodes}
    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x
    for (f, t) in E:
        a, b = find(f), find(t)
        if a != b:
            par[a] = b
    g = collections.defaultdict(set)
    for x in nodes:
        g[find(x)].add(x)
    return sorted(g.values(), key=len, reverse=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arm", default="raw", choices=("raw", "framed"))
    ap.add_argument("--pos", default="VERB",
                    choices=("VERB", "NOUN", "ADJ", "ANY"))
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--min-prompts", type=int, default=3,
                    help="a seed must be rated in this many prompts")
    ap.add_argument("--edge-pos", default="content",
                    choices=("content", "all"))
    ap.add_argument("--lemma", action="store_true",
                    help="merge surface forms into their slot lemma first")
    ap.add_argument("--draw", action="store_true")
    ap.add_argument("--label-prompts", action="store_true",
                    help="put the prompt that produced each edge on it")
    a = ap.parse_args(argv)

    rows = G.crossings(a.arm)
    E, _ = G.edges(a.arm, a.edge_pos, a.lemma)
    mp = modal_pos(rows)
    lf = lifts(a.min_prompts)
    if a.lemma:
        #: seeds must live in the same namespace as the nodes, so the lift
        #: table and the POS map are folded onto lemmas too -- by the
        #: observation-weighted median, since a lemma's surface forms can sit
        #: at different lifts (`kill` +4.00 and `killed` +2.00 give +2.50).
        m = G.modal_lemma(rows)
        agg, pacc = collections.defaultdict(list), collections.defaultdict(collections.Counter)
        import csv as _csv, os as _os
        for r in _csv.DictReader(open(_os.path.join(HERE, "results",
                                                    "words_by_lift.csv"))):
            w = r["word"]
            if w not in m or int(r["n_prompts"]) < a.min_prompts:
                continue
            agg[m[w]] += [float(r["lift_med_med"])] * int(r["n_prompts"])
            pacc[m[w]][mp.get(w, "?")] += int(r["n_prompts"])
        lf = {k: st.median(v) for k, v in agg.items() if v}
        mp = {k: c.most_common(1)[0][0] for k, c in pacc.items()}

    cand = [(L, w) for w, L in lf.items()
            if w in mp and (a.pos == "ANY" or mp[w] == a.pos)]
    cand.sort(reverse=True)
    seeds = [w for _, w in cand[:a.top]]
    out_deg = collections.Counter(f for (f, _) in E)

    print("%s arm, edges=%s: %d edges over %d nodes"
          % (a.arm, a.edge_pos, len(E), len({x for e in E for x in e})))
    print("\nSEEDS: top %d %s by lift (rated in >= %d prompts)"
          % (a.top, a.pos, a.min_prompts))
    for L, w in cand[:a.top]:
        print("   %-14s lift %+.2f   out-edges %d%s"
              % (w, L, out_deg[w], "   <- seeds nothing" if not out_deg[w] else ""))
    live = [w for w in seeds if out_deg[w]]
    print("   %d of %d seeds have an outward edge" % (len(live), len(seeds)))

    nodes, sub = reach(E, seeds)
    comps = components(nodes, sub)
    print("\nREACHED: %d nodes, %d edges, %d weakly connected component(s)"
          % (len(nodes), len(sub), len(comps)))
    for c in comps:
        s = sorted(w for w in seeds if w in c)
        print("   %4d nodes | seeds: %s" % (len(c), ", ".join(s) or "(none)"))
    #: **WHICH SEEDS SHARE A COMPONENT IS THE QUESTION**, so it is printed
    #: even when the answer is one -- "they all merged" and "they never split"
    #: look identical in a component count alone.
    big = comps[0] if comps else set()
    print("\n   largest component holds %d of %d seeds"
          % (sum(1 for w in seeds if w in big), len(seeds)))
    sink = [w for w in nodes if not out_deg[w]]
    print("   %d of %d reached nodes are sinks (never fall again)"
          % (len(sink), len(nodes)))

    if a.draw:
        src = G.dot(sub, collections.Counter(), a.arm, (0, 0),
                    G.prompt_labels(a.arm, sub) if a.label_prompts
                    else None)
        base = os.path.join(HERE, "figures", "seed_walk_%s_%s_top%d%s"
                            % (a.arm, a.pos.lower(), a.top,
                               ("_lemma" if a.lemma else "")
                               + ("_prompts" if a.label_prompts else "")))
        open(base + ".dot", "w", encoding="utf-8").write(src + "\n")
        for ext in ("png", "pdf"):
            r = subprocess.run(["sfdp", "-T" + ext, "-Gdpi=300",
                                base + ".dot", "-o", base + "." + ext],
                               capture_output=True, text=True)
            if r.returncode:
                raise SystemExit("sfdp failed: %s" % r.stderr[:300])
            print("   wrote %s.%s" % (base, ext))
    return 0


if __name__ == "__main__":
    sys.exit(main())
