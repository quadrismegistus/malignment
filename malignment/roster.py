"""The roster: checkpoints and the training operations between them.

    python -m malignment.roster            show what would be written
    python -m malignment.roster --write    build malignment.checkpoints + .edges

## NODES AND EDGES, NOT SLOTS

RH, 2026-08-15: *"All we need is info on model checkpoints and their training
edges right? Nodes and edges type data?"* Yes, and it fixes a factual defect as
well as a theoretical one.

The old schema had slots named `base` / `ego` / `superego` / `reinforced_superego`.

**A SCHEMA THAT NAMES A PSYCHIC POSITION HAS ALREADY ANSWERED THE QUESTION.** The
project's best results are about *which stage carries the repression* -- SFT
takes sexual content and DPO takes violence in OLMo; OLMo is ego-dominant at
~90% while Amber splits 50/50; the one reliable Tulu ablation arm is
`no-safety`, which is an SFT ablation. Every one of those says the superego
FUNCTION is distributed and its distribution varies by family and by content. A
column called `superego` makes that unsayable.

**AND `superego` WAS DOING TWO JOBS.** For OLMo it meant a released DPO
checkpoint. For Llama it meant `Llama-3.1-8B-Instruct` -- an aligned endpoint
bundling SFT, preference tuning and whatever else, composition never separately
released. 58 families carried a `superego`; only 29 carried an `ego`. So for 29
of them the "superego" was not a preference stage at all. That is the
heterogeneity behind *"for consistency we've called a pair base->dpo"*: the
consistency was in the label, not in the objects.

The same roster, as edges:

    instruct  35   <- LARGEST class. aligned endpoint, composition UNDECLARED
    sft       29
    dpo       23
    rlvr       6
    distill    2

**The most common aligned checkpoint in the roster is one whose composition we do
not know**, and the old schema called all 35 of them the superego.

## WHAT THIS BUYS

A pair is no longer forced. `Llama-3.1-8B` has six outgoing edges -- Meta's
`instruct`, a `distill`, and five Tulu `sft` arms including four data ablations.
Those are DIFFERENT COMPARISONS, not redundancy, and the graph holds them without
anyone choosing a representative in advance. An analysis picks its edges and says
which. The Freudian reading loses nothing: it moves to the analysis, where it can
be a finding rather than a schema.

## YAML, BECAUSE THE FILE IS HAND-EDITED

JSON cannot hold a comment, and a declaration whose evidence cannot sit beside it
loses the evidence. `roster/roster.yaml` is authored; no script writes it.
"""
import argparse
import collections
import os
import sys

from . import ch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUTHORED = os.path.join(ROOT, "roster", "roster.yaml")

#: Operations that ALIGN. `distill` is a lineage relation, not an alignment step,
#: so it is excluded here rather than at a call site where it would be invisible.
ALIGNING = ("sft", "dpo", "rlvr", "ppo", "kto", "slic", "instruct")

DDL = ["""
CREATE TABLE IF NOT EXISTS {db}.checkpoints (
    model_id String, family Array(String),
    org_type LowCardinality(String), country LowCardinality(String),
    scale LowCardinality(String), open_weight UInt8, open_data UInt8
) ENGINE = ReplacingMergeTree ORDER BY model_id
""", """
CREATE TABLE IF NOT EXISTS {db}.edges (
    parent String, op LowCardinality(String), child String
) ENGINE = ReplacingMergeTree ORDER BY (parent, op, child)
"""]

VIEWS = {
    #: EVERY alignment edge, flagged by whether its parent is a pretrained root.
    #: NOT one per lineage: the Llama root carries Meta's instruct AND five Tulu
    #: sft arms, and those are different comparisons. The roster does not choose.
    "alignment_edges": """
        CREATE OR REPLACE VIEW {db}.alignment_edges AS
        SELECT parent, op, child,
               parent NOT IN (SELECT child FROM {db}.edges) AS from_root
        FROM {db}.edges WHERE op IN %s
    """ % (str(ALIGNING),),
    "roots": """
        CREATE OR REPLACE VIEW {db}.roots AS
        SELECT model_id FROM {db}.checkpoints
        WHERE model_id NOT IN (SELECT child FROM {db}.edges)
    """,
}


def load():
    import yaml
    with open(AUTHORED, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def rows():
    A = load()
    nodes = [{"model_id": m, "family": (d or {}).get("family") or [],
              "org_type": (d or {}).get("org_type", "") or "",
              "country": (d or {}).get("country", "") or "",
              "scale": (d or {}).get("scale", "") or "",
              "open_weight": int(bool((d or {}).get("open_weight"))),
              "open_data": int(bool((d or {}).get("open_data")))}
             for m, d in (A.get("nodes") or {}).items()]
    edges = []
    for e in A.get("edges") or []:
        #: Refuse a malformed edge rather than skipping it. A training relation
        #: silently dropped vanishes from every downstream question.
        if not (isinstance(e, (list, tuple)) and len(e) == 3):
            raise ValueError("malformed edge: %r" % (e,))
        edges.append({"parent": e[0], "op": e[1], "child": e[2]})
    ids = {n["model_id"] for n in nodes}
    dangling = [e for e in edges if e["parent"] not in ids or e["child"] not in ids]
    return nodes, edges, dangling


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    nodes, edges, dangling = rows()
    ops = collections.Counter(e["op"] for e in edges)
    roots = {n["model_id"] for n in nodes} - {e["child"] for e in edges}
    print("  authored: %s" % os.path.relpath(AUTHORED, ROOT))
    print("  %d checkpoints | %d edges | %d roots (no incoming edge)"
          % (len(nodes), len(edges), len(roots)))
    print("  operations: %s" % dict(ops.most_common()))
    if dangling:
        print("  DANGLING EDGES (endpoint not a declared node): %d" % len(dangling))
        for e in dangling[:5]:
            print("     %s -%s-> %s" % (e["parent"], e["op"], e["child"]))
    if not a.write:
        print("\n  --write to build %s.checkpoints and %s.edges" % (ch.DB, ch.DB))
        return 0
    for d in DDL:
        ch.execute(d)
    ch.execute("TRUNCATE TABLE {db}.checkpoints")
    ch.execute("TRUNCATE TABLE {db}.edges")
    ch.insert("checkpoints", nodes)
    ch.insert("edges", edges)
    for name, sql in VIEWS.items():
        try:
            ch.execute(sql)
            print("  view %s.%s" % (ch.DB, name))
        except Exception as e:
            print("  view %s FAILED: %s" % (name, str(e)[:120]))
    print("\n  %s.checkpoints %s | %s.edges %s"
          % (ch.DB, ch.scalar("SELECT count() FROM {db}.checkpoints"),
             ch.DB, ch.scalar("SELECT count() FROM {db}.edges")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
