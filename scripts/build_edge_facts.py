#!/usr/bin/env python
"""Facts that belong to an EDGE, not to either model on it.

    python scripts/build_edge_facts.py
    python scripts/build_edge_facts.py --write   -> roster/models/edge_facts.json

## SOME FAILURES ARE INVISIBLE TO EVERY PER-MODEL CHECK

`PKU-Alignment/beaver-7b-v1.0` loads. `huggyllama/llama-7b` loads. Cross-scoring
one against the other dies with a CUDA device-side assert after 85 sites,
because their vocabularies are **32000 and 32001**. Neither model is broken and
no amount of checking either one finds it: the defect is a property of the PAIR.

`observations.json` is keyed on (model x environment) and cannot hold that.
The knowledge existed as six roster pairs flagged `cross_score: false` -- a flag
with no producer, no evidence, and no way to notice the seventh.

## DERIVED FROM THE MEASURED VOCABULARIES, SO IT FINDS PAIRS NOBODY LISTED

`measurements.json` `vocab` carries `vocab_len` for every checkpoint we have
looked at, and the roster declares every parent->child edge. Comparing the two
is the whole method. It covers the pairs somebody remembered AND the ones
nobody did, and it re-derives when either side changes.

**A MISMATCH IS A HAZARD, NOT A VERDICT.** Whether it actually breaks depends on
what the consumer does: a JS divergence over a shared support is fine, while an
index-aligned tensor comparison is not. So the row says the sizes differ, by how
much, and leaves the ruling to the consumer -- which is why the field is
`vocab_delta` and not `broken`.

Also emitted: `byte_notation` disagreement across an edge. v4's
`decoded_boundary` rule bites on byte-level tokenizers and nowhere else, so an
edge whose two arms disagree is one where the instrument itself differs between
the things being compared.
"""
import argparse
import json
import os
import sys
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

OUT = os.path.join(ROOT, "roster", "models", "edge_facts.json")
SOURCES = ["roster/models/models.yaml", "roster/models/measurements.json"]


def _pairs():
    """(parent, op, child) for DIRECT edges AND for root->member pairs.

    **THE MOTIVATING CASE IS NOT A DIRECT EDGE.** `beaver-7b-v1.0` was
    cross-scored against `huggyllama/llama-7b`, which is its lineage ROOT two
    hops up, not its parent. A derivation over direct edges alone reports the
    parent pair as clean and misses the comparison anybody actually ran --
    consumers compare an endpoint against its BASE, so the base pair is the one
    that has to be checked.
    """
    from malignment import roster
    edges = roster.rows()[1]
    seen, out = set(), []
    for e in edges:
        k = (e["parent"], e["child"])
        seen.add(k)
        out.append((e["parent"], e["op"], e["child"], "edge"))
    for root, members in roster.lineages(ops=roster.ALIGNING).items():
        for m in members:
            if m == root or (root, m) in seen:
                continue
            seen.add((root, m))
            out.append((root, "lineage", m, "root"))
    return out


def build():
    meas = json.load(open(os.path.join(ROOT, "roster", "models",
                                       "measurements.json")))["sections"]
    vocab = (meas.get("vocab") or {}).get("models") or {}
    out = []
    for p, op, c, kind in _pairs():
        e = {"parent": p, "op": op, "child": c, "kind": kind}
        vp = (vocab.get(p) or {}).get("vocab_len")
        vc = (vocab.get(c) or {}).get("vocab_len")
        bp = (vocab.get(p) or {}).get("byte_notation")
        bc = (vocab.get(c) or {}).get("byte_notation")
        row = OrderedDict([("parent", p), ("op", op), ("child", c),
                           ("kind", kind),
                           ("vocab_parent", vp), ("vocab_child", vc)])
        if vp is None or vc is None:
            #: **UNMEASURED IS NOT EQUAL.** Defaulting a missing vocab to the
            #: sibling's would silently pass the exact pairs least looked at.
            row["vocab_delta"] = None
            row["vocab_status"] = "unmeasured"
        elif vp == vc:
            row["vocab_delta"] = 0
            row["vocab_status"] = "aligned"
        else:
            row["vocab_delta"] = vc - vp
            row["vocab_status"] = "MISMATCH"
            row["hazard"] = (
                "vocabularies differ by %d (%s vs %s). Safe for anything over a "
                "shared support; UNSAFE for index-aligned tensor comparison -- "
                "beaver-7b vs llama-7b is a CUDA device-side assert after 85 "
                "sites on a delta of 1." % (vc - vp, vp, vc))
        if bp and bc and bp != bc:
            row["byte_notation"] = "%s -> %s" % (bp, bc)
            row["byte_notation_hazard"] = (
                "the arms disagree on tokenizer notation, and v4's "
                "decoded_boundary rule bites on byte-level surfaces only -- so "
                "the INSTRUMENT differs between the two things being compared.")
        out.append(row)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    rows = build()
    import collections
    c = collections.Counter(r["vocab_status"] for r in rows)
    print("edges %d  %s" % (len(rows), dict(c)))
    bn = [r for r in rows if r.get("byte_notation")]
    print("edges whose arms disagree on byte_notation: %d" % len(bn))
    print("\n=== vocab MISMATCH edges ===")
    for r in sorted([x for x in rows if x["vocab_status"] == "MISMATCH"],
                    key=lambda x: -abs(x["vocab_delta"])):
        print("  %-38s -%-8s-> %-30s %s vs %s (%+d)"
              % (r["parent"].split("/")[-1][:38], r["op"],
                 r["child"].split("/")[-1][:30], r["vocab_parent"],
                 r["vocab_child"], r["vocab_delta"]))
    if bn:
        print("\n=== byte_notation disagreements ===")
        for r in bn:
            print("  %-38s -%-8s-> %-28s %s"
                  % (r["parent"].split("/")[-1][:38], r["op"],
                     r["child"].split("/")[-1][:28], r["byte_notation"]))
    un = [r for r in rows if r["vocab_status"] == "unmeasured"]
    if un:
        print("\nunmeasured on one or both arms: %d (NOT assumed aligned)" % len(un))
        for r in un[:5]:
            print("  %s -> %s" % (r["parent"], r["child"]))
    if not a.write:
        print("\nDRY RUN -- pass --write.")
        return 0
    json.dump(OrderedDict([
        ("_about", "Facts belonging to an EDGE rather than to either model. A "
                   "vocab mismatch is invisible to every per-model check: "
                   "beaver-7b and llama-7b both load, and cross-scoring them "
                   "dies on 32000 vs 32001."),
        ("_producer", "scripts/build_edge_facts.py"),
        ("_sources", SOURCES),
        ("_ruling", "A mismatch is a HAZARD, not a verdict. Safe over a shared "
                    "support, unsafe for index-aligned comparison. The consumer "
                    "rules; this file reports the delta."),
        ("n", len(rows)),
        ("edges", rows),
    ]), open(OUT, "w"), indent=1, ensure_ascii=False)
    open(OUT, "a").write("\n")
    print("\nwrote %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
