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
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args(argv)
    rs = rows()
    #: ids assigned BEFORE the shuffle, so OP0001 is stable across seeds and two
    #: differently-ordered readings can be joined without re-deriving anything
    random.Random(a.seed).shuffle(rs)
    #: **907, NOT 909, AND THE FILE SAYS SO.** Two operations pool to an empty
    #: side -- the reader named a relation but cited words on one arm only -- so
    #: there is nothing to relate and they are dropped rather than shown as a
    #: one-sided entry. A title carrying the round number would be wrong in the
    #: one place a reader cannot check it.
    L = ["# %d operations, shuffled" % len(rs), "",
         "(Two of the 909 in the stash pool to an empty side and are omitted.)",
         "",
         "Each entry is one relation a reader identified at one sentence, with "
         "the words it was cited on pooled across every model that showed it.",
         "", "`n` is how many models. Order is randomised (seed %d); ids are "
         "assigned before the shuffle and are stable." % a.seed, "",
         "---", ""]
    for r in rs:
        L.append("**%s** · %s · n=%d" % (r["id"], r["name"], r["n"]))
        L.append("")
        L.append("> %s ___" % r["frame"])
        L.append("")
        L.append("    A: %s%s" % (" ".join(r["a"][:CAP]),
                                  " ..." if len(r["a"]) > CAP else ""))
        L.append("    B: %s%s" % (" ".join(r["b"][:CAP]),
                                  " ..." if len(r["b"]) > CAP else ""))
        L.append("")
    txt = "\n".join(L)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    open(a.out, "w").write(txt)
    print("%d operations -> %s" % (len(rs), a.out))
    print("  %s chars, ~%s tokens at 3.6 ch/tok"
          % (format(len(txt), ","), format(int(len(txt) / 3.6), ",")))
    print("  %d rest on one model; %d on two"
          % (sum(1 for r in rs if r["n"] == 1), sum(1 for r in rs if r["n"] == 2)))
    print("  %d distinct frames, %d distinct names"
          % (len({r["frame"] for r in rs}), len({r["name"] for r in rs})))
    return 0


if __name__ == "__main__":
    sys.exit(main())
