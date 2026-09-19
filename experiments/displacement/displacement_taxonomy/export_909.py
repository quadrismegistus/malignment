"""The 909 raw operations as one shuffled document, for an independent grouping.

    python -u export_909.py                 -> results/operations_909_shuffled.md
    python -u export_909.py --seed 7        a different shuffle, same content

## WHAT THIS IS FOR

`cross_frame.py` groups the 89 per-frame COMPONENTS, three raters each, and the
ten meta-relations are connected components of the resulting hub graph. This
exports the layer BELOW that aggregation so the same question can be put to a
reader in one pass, and the two partitions scored against each other.

## IT CARRIES WORDS, WHICH `cross_frame.py` DELIBERATELY WITHHELD

RH asked for name + prompt + `a_words -> b_words`, and that is the opposite of
the blind document's rule. `cross_frame.py`:

    Words would leak the frame, and worse, they would supply an easier grouping
    than the real one: give a rater `cock -> beard` beside `dick -> chin` and it
    can sort by domain without ever considering the relation. Domain similarity
    is exactly the confound, because the question is which relations SURVIVE a
    change of domain.

So a grouping made from this file is answering a DIFFERENT question from the one
the ten answer, and the two are not interchangeable. A reader given the words can
sort by domain -- sexual, violent, institutional -- and land a clean-looking
partition that says nothing about relations at all. **That is the first thing to
check in whatever comes back**: if the clusters are domains, the file did the
sorting, not the reader. Keeping the statement out (as asked) removes the one
field written to describe a transformation rather than a scene, which makes the
domain shortcut easier still.

Both facts are stated here rather than in the output, because the output is
going to a reader who should not be told what to find.

## THE UNION, NOT THE MEMBERS

An operation holds one member per lineage, 8,661 rows in all, and the same
relation is asserted of every one of them. The words shown are the UNION across
members, so each entry is one relation with everything it was cited on. Member
count is printed because an operation resting on one lineage is a different kind
of evidence from one resting on forty, and 166 of the 909 rest on one.

## SHUFFLED, SEEDED

Order is randomised so a reader cannot group by adjacency -- operations arrive
from the stash grouped by frame, and consecutive entries would otherwise share a
prompt. The seed is recorded in the file so the shuffle is reproducible and two
readings can be compared row for row.
"""
import argparse, collections, json, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
STASH = os.path.join(HERE, "results", "crosslineage_stash",
                     "jsonl.hashstash.raw", "data.jsonl")
OUT = os.path.join(HERE, "results", "operations_909_shuffled.md")
#: enough to show the movement, short enough that one entry stays readable
CAP = 14


def components(min_ops=2):
    """Corroborated components: one per (frame, version), >= `min_ops` readings.

    ## WHY THIS IS A DIFFERENT UNIT FROM `rows()`

    `rows()` exports the 907 raw operations -- one reader's account at one
    sentence. Most of them are near-duplicates of each other, because a frame
    was read 2 to 16 times, and both agents spent most of their groups merging
    those: 158 of gpt6's 200 and 62 of opus5's 107 sat inside a single frame.
    That work is DEDUPLICATION and the corpus can do it without an agent.

    A COMPONENT is the merge already made, on roster evidence rather than prose:
    two operations join when they cite at least two of the same models
    (`operation_graph.op_components`, k=2). `cross_frame.py:203` states the case
    -- handing raw operations to a grouping pass asks it "to rediscover across
    frames a merge already made WITHIN each frame on roster evidence, and to redo
    it on prose, which is the weaker evidence of the two."

    ## AND WHY ONLY THE CORROBORATED ONES

    211 of 431 components hold a single operation: nobody else saw it, and it
    passes through the merge untouched. Those are not components in any useful
    sense, and including them would hand an agent the same deduplication problem
    in a new costume. **220 of 431 survive.**

    ## THE (frame, version) KEY IS NOT OPTIONAL

    Stripped and unstripped readings of one sentence CANNOT pool: dropping blank
    tokens redistributes mass and moves every rank below a blank, so a stripped
    table is a different measurement of the same surface. Grouping on frame alone
    would merge two measurements and the words would silently disagree.
    """
    import operation_graph as OG
    g = collections.defaultdict(list)
    for i, line in enumerate(open(STASH, encoding="utf-8")):
        r = json.loads(line)
        g[(r["__key__"]["frame_prompt"], r["__key__"].get("version"))].append(
            ("r%03d" % i, r))
    out, dropped = [], 0
    for (frame, ver), pairs in sorted(g.items()):
        G = OG.build(pairs)
        OPS = {x for x in G if G.nodes[x].get("kind") == "op"}
        if not OPS:
            continue
        info = {}
        for tag, r in pairs:
            for o in (r.get("operations") or []):
                info["OP[%s] %s" % (tag, o["name"])] = o
        comps, _c, _m = OG.op_components(G, OPS, 2)
        for c in comps:
            if len(c) < min_ops:
                dropped += 1
                continue
            names, a, b = [], [], []
            for node in sorted(c):
                o = info.get(node)
                if not o:
                    continue
                if o["name"] not in names:
                    names.append(o["name"])
                for m in (o.get("members") or []):
                    for w in (m.get("a_words") or []):
                        if w not in a:
                            a.append(w)
                    for w in (m.get("b_words") or []):
                        if w not in b:
                            b.append(w)
            if names and a and b:
                out.append({"id": "CP%03d" % (len(out) + 1), "frame": frame,
                            "ver": ver, "name": " / ".join(names),
                            "names": names, "n": len(c), "a": a, "b": b})
    print("%d corroborated components (>=%d readings); %d single-reading "
          "components dropped" % (len(out), min_ops, dropped), file=sys.stderr)
    return out


def rows():
    out = []
    for i, line in enumerate(open(STASH, encoding="utf-8")):
        r = json.loads(line)
        frame = r["__key__"]["frame_prompt"]
        for j, o in enumerate(r.get("operations") or []):
            ms = o.get("members") or []
            a, b = [], []
            for m in ms:
                for w in (m.get("a_words") or []):
                    if w not in a:
                        a.append(w)
                for w in (m.get("b_words") or []):
                    if w not in b:
                        b.append(w)
            if not a or not b:
                continue
            out.append({"id": "OP%04d" % (len(out) + 1),
                        "src": "r%03d.o%d" % (i, j), "frame": frame,
                        "name": o.get("name", ""), "n": len(ms),
                        "a": a, "b": b})
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed", type=int, default=20260919)
    ap.add_argument("--components", action="store_true",
                    help="export corroborated COMPONENTS, not raw operations")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    rs = components() if a.components else rows()
    #: ids assigned BEFORE the shuffle, so OP0001 is stable across seeds and two
    #: differently-ordered readings can be joined without re-deriving anything
    out_path = a.out or (os.path.join(HERE, "results",
        "components_corroborated_shuffled.md") if a.components else OUT)
    random.Random(a.seed).shuffle(rs)
    #: **907, NOT 909, AND THE FILE SAYS SO.** Two operations pool to an empty
    #: side -- the reader named a relation but cited words on one arm only -- so
    #: there is nothing to relate and they are dropped rather than shown as a
    #: one-sided entry. A title carrying the round number would be wrong in the
    #: one place a reader cannot check it.
    #: **907, NOT 909, AND THE FILE SAYS SO.** Two operations pool to an empty
    #: side -- the reader named a relation but cited words on one arm only -- so
    #: there is nothing to relate and they are dropped rather than shown as a
    #: one-sided entry. A title carrying the round number would be wrong in the
    #: one place a reader cannot check it.
    #:
    #: **THE INSTRUCTION IS ADAPTED FROM `cross_frame.py:140-170`, NOT WRITTEN
    #: FRESH.** That one has been used by three raters on the layer above and
    #: already carries the two clauses that matter: separate a shared SUBJECT
    #: from a shared MOVEMENT, and prefer many small groups because a wrong merge
    #: destroys more than a missed one. Rewriting it would have changed the
    #: instrument and the population at once.
    #:
    #: **DIRECTION IS WITHHELD.** A is the base arm throughout and B the aligned
    #: one, and the reader is told neither -- `PROTOCOL_naming.md`: "Name the
    #: relation, not the instances. A construct pinned to a direction is pinned
    #: to a fact about which lineages we happen to have." Which side rose is
    #: recoverable from the key afterwards and must not be annotatable.
    head = (["# %d corroborated transformations" % len(rs), "",
             "Below are annotations of how word probabilities moved in language "
             "models trained under two conditions, A and B. Each entry is one "
             "transformation that TWO OR MORE readers independently identified "
             "at the same sentence, having each read it without sight of the "
             "others. Where an entry carries several names separated by `/`, "
             "those are the different names they gave the one transformation, "
             "and all of their words are pooled below it.",
             "",
             "The A words are the ones more likely under one condition and the "
             "B words more likely under the other.",
             ""]
            if a.components else
            ["# %d annotated relations" % len(rs), "",
             "(Two of the 909 in the source pool to an empty side and are "
             "omitted.)", "",
             "Below are annotations of how word probabilities moved in language "
             "models trained under two conditions, A and B. Each entry is one "
             "reader's account of a single transformation seen at a single "
             "sentence: a short name for it, the sentence, and the words it was "
             "cited on. The A words are the ones more likely under one condition "
             "and the B words more likely under the other.",
             ""])
    L = head + [
         "**You are not told which condition is which.** The relation you name "
         "must read the same either way round: say what separates the two "
         "groups, never which direction anything moved.",
         "",
         "## Your job",
         "",
         "Say which of these entries describe THE SAME transformation.",
         "",
         "Group them. A group is a set of entries naming one underlying "
         "transformation, however differently they word it and whatever "
         "material the reader was looking at. Two entries belong together only "
         "if the MOVEMENT is the same. They do NOT belong together merely "
         "because their words come from a similar subject area: entries drawn "
         "from the same subject matter will look alike, and separating a shared "
         "SUBJECT from a shared MOVEMENT is most of the work here. A "
         "transformation appearing in several subject areas is more interesting "
         "than one confined to a single area, so look for those in particular.",
         "",
         "For each group give:",
         "",
         "    name        a short label for the transformation itself",
         "    statement   one or two sentences stating the movement in general",
         "                terms, in your own words, at a level that covers every",
         "                member",
         "    members     the ids in it",
         "    spans       whether its members are drawn from one subject area or",
         "                several, and which",
         "    why         what makes these one transformation and not several",
         "",
         "Then list, as `singletons`, the ids you could not place with anything.",
         "",
         "Every id must appear exactly once, in a group or in singletons. Be "
         "willing to return many small groups: a wrong merge destroys more than "
         "a missed one.",
         "",
         "Order is randomised (seed %d); ids are stable across seeds." % a.seed,
         "",
         "## Entries", "", "---", ""]
    for r in rs:
        #: `n` dropped on RH's instruction. It is how many models showed the
        #: operation, and a reader shown it can weight a 40-model entry over a
        #: 1-model one -- which is evidence about PREVALENCE, not about what the
        #: relation IS, and would import the aggregation this file exists to
        #: bypass. It stays recoverable from the stash by id.
        L.append("**%s** · %s" % (r["id"], r["name"]))
        L.append("")
        L.append("> %s ___" % r["frame"])
        L.append("")
        L.append("    A: %s%s" % (" ".join(r["a"][:CAP]),
                                  " ..." if len(r["a"]) > CAP else ""))
        L.append("    B: %s%s" % (" ".join(r["b"][:CAP]),
                                  " ..." if len(r["b"]) > CAP else ""))
        L.append("")
    txt = "\n".join(L)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    open(out_path, "w").write(txt)
    print("%d entries -> %s" % (len(rs), out_path))
    print("  %s chars, ~%s tokens at 3.6 ch/tok"
          % (format(len(txt), ","), format(int(len(txt) / 3.6), ",")))
    print("  %d rest on one model; %d on two"
          % (sum(1 for r in rs if r["n"] == 1), sum(1 for r in rs if r["n"] == 2)))
    print("  %d distinct frames, %d distinct names"
          % (len({r["frame"] for r in rs}), len({r["name"] for r in rs})))
    return 0


if __name__ == "__main__":
    sys.exit(main())
