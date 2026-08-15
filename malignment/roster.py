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
import json
import os
import sys

from . import ch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUTHORED = os.path.join(ROOT, "roster", "models", "models.yaml")
#: OBSERVED, not declared: one stamped file, a section per pass. The archive
#: kept these in six artifacts that each defined "the set of models" and
#: drifted apart.
OBSERVED = os.path.join(ROOT, "roster", "models", "measurements.json")

#: TWO KINDS OF EDGE, and conflating them silently moved a population count.
#:
#: DERIVING  the child was PRODUCED from the parent by training. An incoming
#:           deriving edge is what makes a checkpoint not-pretrained.
#: RELATING  two independently-produced checkpoints stand in a relation. Neither
#:           was made from the other.
#:
#: When `scale` edges were added on 2026-08-15 the `roots` view -- defined as
#: "no incoming edge" -- fell from 54 to 47, because `Olmo-3-1125-32B` acquired
#: an incoming `scale` edge and stopped counting as pretrained. It is pretrained.
#: **A view keyed on "any edge" breaks the moment a new edge type means something
#: different**, and it breaks by changing a number rather than by failing.
ALIGNING = ("sft", "dpo", "rlvr", "ppo", "kto", "slic", "instruct")
#: `upscale` DERIVES: Falcon3-10B-Base is depth up-scaled FROM 7B with continual
#: pretraining, so it inherits 7B's pretraining and is a DESCENDANT. A derived
#: model is not an independent observation, and `scale` -- a RELATING op -- would
#: have asserted the opposite. `prune` likewise: Falcon3 1B and 3B are pruned and
#: healed FROM larger members on 80 Gigatokens, against 10B's 2 Teratokens. Kept
#: as SEPARATE ops because a 25x difference in post-derivation training is what
#: any independence argument would turn on.
DERIVING = ALIGNING + ("distill", "upscale", "prune")
RELATING = ("scale", "predecessor")

DDL = ["""
CREATE TABLE IF NOT EXISTS {db}.checkpoints (
    model_id String, family Array(String),
    org_type LowCardinality(String), country LowCardinality(String),
    scale LowCardinality(String), open_weight UInt8, open_data UInt8,
    nickname LowCardinality(String), revision LowCardinality(String),
    revision_ladder UInt32, lineage String, depth UInt8,
    params_b Float32, scale_group String, is_representative UInt8,
    vocab_size UInt32, vocab_len UInt32, n_added_tokens UInt32,
    reasoning UInt8
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
               parent NOT IN (SELECT child FROM {db}.edges WHERE op IN %s) AS from_root
        FROM {db}.edges WHERE op IN %s
    """ % (str(DERIVING), str(ALIGNING)),
    #: MEASURED, not declared. `revision_ladder` on a node says a trajectory
    #: EXISTS and how long; this says which rungs we have run. Availability
    #: dwarfs coverage -- 1,487 revisions published for Olmo-3-1025-7B, 43
    #: measured -- and conflating the two is how "we have the ladder" comes to
    #: mean two different things in one sentence.
    "measured_revisions": """
        CREATE OR REPLACE VIEW {db}.measured_revisions AS
        SELECT splitByChar('@', model)[1] AS repo,
               if(position(model, '@') > 0, splitByChar('@', model)[2], '') AS revision,
               count() AS cells
        FROM {db}.twp_cells GROUP BY repo, revision
    """,
    #: Two checkpoints sharing a pretrained root. Was `same_base_as`, 84 declared
    #: edges; here it is a join and yields 175 pairs.
    "same_base": """
        CREATE OR REPLACE VIEW {db}.same_base AS
        SELECT a.model_id AS a, b.model_id AS b, a.lineage AS lineage
        FROM {db}.checkpoints a INNER JOIN {db}.checkpoints b USING (lineage)
        WHERE a.model_id < b.model_id
    """,
    "roots": """
        CREATE OR REPLACE VIEW {db}.roots AS
        SELECT model_id FROM {db}.checkpoints
        WHERE model_id NOT IN (SELECT child FROM {db}.edges WHERE op IN %s)
    """ % (str(DERIVING),),
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
              "open_data": int(bool((d or {}).get("open_data"))),
              "nickname": (d or {}).get("nickname", "") or "",
              "revision": str((d or {}).get("revision", "") or ""),
              "revision_ladder": int((d or {}).get("revision_ladder") or 0),
              "reasoning": int(bool((d or {}).get("reasoning")))}
             for m, d in (A.get("nodes") or {}).items()]
    edges = []
    for e in A.get("edges") or []:
        #: Refuse a malformed edge rather than skipping it. A training relation
        #: silently dropped vanishes from every downstream question.
        if not (isinstance(e, (list, tuple)) and len(e) == 3):
            raise ValueError("malformed edge: %r" % (e,))
        edges.append({"parent": e[0], "op": e[1], "child": e[2]})
    #: LINEAGE IS DERIVED BY WALKING DERIVING EDGES TO A ROOT, at build time,
    #: because the whole table is rebuilt from the authored file and so cannot
    #: drift from it. **This replaces `same_base_as`**, which the archive declared
    #: as 84 hand-maintained edges: all 84 are derivable from this graph, and the
    #: graph yields 175 such pairs. A derivable relation that is ALSO maintained
    #: by hand drifts toward incompleteness -- it had less than half.
    par = {e["child"]: e["parent"] for e in edges if e["op"] in DERIVING}
    for n in nodes:
        m, d, seen = n["model_id"], 0, set()
        while m in par and m not in seen:
            seen.add(m); m = par[m]; d += 1
        n["lineage"], n["depth"] = m, d
    #: PARAMS_B IS MEASURED, NOT DECLARED, so it is joined here from
    #: `data/weights_audit.csv` (safetensors header counts) rather than written
    #: into the authored YAML. 156 of 159 in the archive's audit; a model absent
    #: from it gets 0 and is excluded from the size pick rather than guessed at.
    obs = {}
    if os.path.exists(OBSERVED):
        with open(OBSERVED, encoding="utf-8") as fh:
            obs = json.load(fh).get("sections") or {}
    pb = {k: v.get("params_b", 0.0)
          for k, v in (obs.get("weights", {}).get("models") or {}).items()}
    tok = obs.get("tokenizer", {}).get("models") or {}
    lad = obs.get("revision_ladders", {}).get("models") or {}
    for n in nodes:
        m = n["model_id"]
        n["params_b"] = pb.get(m, 0.0)
        t = tok.get(m) or {}
        n["vocab_size"] = int(t.get("vocab_size") or 0)
        n["vocab_len"] = int(t.get("vocab_len") or 0)
        n["n_added_tokens"] = int(t.get("n_added_tokens") or 0)
        #: OBSERVED WINS over the authored `revision_ladder`. A ladder length is
        #: something the HF API reports, never something anyone declares -- and
        #: the authored value was itself imported from this survey.
        n["revision_ladder"] = int(lad.get(m) or n.get("revision_ladder") or 0)

    #: SCALE GROUP: lineages linked by `scale` or `predecessor` edges — the same
    #: recipe at several sizes. THE LEVEL ABOVE LINEAGE, and the one RH means by
    #: "representative": *"a representative is what picks olmo7b instead of 1b or
    #: 8b"*. 54 lineages collapse to 47 groups; five hold more than one
    #: (OLMo 1B/7B/32B, Falcon3 1B/3B/7B, Llama 8B/70B, Qwen2.5 0.5B/7B,
    #: Falcon-H1 1.5B/7B).
    #:
    #: **A `family` is a different axis and must not be confused with either.**
    #: `olmo`, `olmo-32b` and `olmo-tiny` are three families inside ONE scale
    #: group, and a family can span lineages while a lineage cannot span groups.
    par = {}

    def _find(x):
        par.setdefault(x, x)
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x

    lin_of = {n["model_id"]: n["lineage"] for n in nodes}
    for n in nodes:
        _find(n["lineage"])
    for e in edges:
        if e["op"] in RELATING:
            a, b = lin_of.get(e["parent"]), lin_of.get(e["child"])
            if a and b:
                ra, rb = _find(a), _find(b)
                if ra != rb:
                    par[ra] = rb
    #: THE PICK IS THE LINEAGE NEAREST 8B, RH's rule. Deterministic, stated, and
    #: independent of any outcome -- a representative chosen by a measured
    #: quantity cannot be chosen to favour a result.
    TARGET = 8.0
    #: **THE FLAG IS PER CHECKPOINT, NOT PER LINEAGE**, and the difference is the
    #: whole point of the size pick. Marking the lineage let every member inherit
    #: it: the Falcon3 lineage is ONE pretraining run and still contributed FOUR
    #: alignment pairs (1B, 3B, 7B, 10B each -instruct-> its own arm), so a
    #: representative-filtered analysis counted one run four times. Being one
    #: lineage does not dedupe by size; something has to choose the size.
    #:
    #: A checkpoint is representative iff it sits on the SIZE-CHOSEN branch:
    #:   - the base-side node of its lineage nearest 8B (root, or reached from the
    #:     root by prune / upscale / scale -- the ops that change SIZE), or
    #:   - anything reached from that node by ALIGNING ops.
    #: So Falcon3 yields 7B-Base -> 7B-Instruct and nothing else, while 1B/3B/10B
    #: stay in the roster, visible, with is_representative = 0.
    SIZE_OPS = ("prune", "upscale", "scale", "predecessor")
    kids = collections.defaultdict(list)
    for e in edges:
        kids[e["parent"]].append((e["op"], e["child"]))
    pb = {n["model_id"]: n["params_b"] for n in nodes}
    lin_of2 = {n["model_id"]: n["lineage"] for n in nodes}

    def _size_side(root):
        """Root plus everything reachable from it by SIZE ops -- the candidates."""
        seen, stack = {root}, [root]
        while stack:
            m = stack.pop()
            for op, c in kids.get(m, ()):
                if op in SIZE_OPS and c not in seen:
                    seen.add(c); stack.append(c)
        return seen

    def _aligned_from(m):
        """Everything derived from m EXCEPT by a size op, at any depth.

        NOT just ALIGNING. Following aligning ops alone dropped
        `DeepSeek-R1-Distill-Qwen-7B` and `-Llama-8B`, which reach their base by
        `distill` -- so two reasoning distils were excluded by a mechanism built
        for SIZES, having nothing to do with size. **A rule that excludes should
        exclude for its own reason**; anything derived from the picked checkpoint
        by a non-size operation is a different model and counts.
        """
        seen, stack = set(), [m]
        while stack:
            x = stack.pop()
            for op, c in kids.get(x, ()):
                if op in DERIVING and op not in SIZE_OPS and c not in seen:
                    seen.add(c); stack.append(c)
        return seen

    #: **THE PICK RUNS OVER THE LINEAGE, NOT THE SCALE GROUP** -- changed
    #: 2026-08-15 on RH's reasoning and a measurement.
    #:
    #: RH: *"if 2 models behave differently then we are not statistically inflating
    #: n."* Independence is a property of the OUTCOME, not the provenance. Measured,
    #: per-prompt js_total correlation between comparable edges:
    #:
    #:     Falcon3 7B vs 10B (DERIVED)   0.626      excess over floor +0.307
    #:     Falcon-H1 7B vs 1.5B          0.440                        +0.121
    #:     Olmo-3 7B vs 32B              0.425                        +0.106
    #:     Qwen2.5 7B vs 0.5B            0.152                        -0.167
    #:     BETWEEN-FAMILY FLOOR          0.319   (Olmo-7B vs Qwen-7B)
    #:
    #: Two UNRELATED labs correlate at 0.319 because prompts differ. Sibling sizes
    #: clear that by ~0.11 and Qwen's pair sits BELOW it, so they carry nearly as
    #: much independent information as different families do. Only the DERIVED pair
    #: is genuinely redundant -- the one that shares weights.
    #:
    #: So a lineage (one pretraining run) still yields ONE size, and sibling
    #: lineages each count. Falcon3's 1B/3B/10B stay excluded because they ARE that
    #: run; Olmo-32B, Llama-70B, Qwen-0.5B and Falcon-H1-1.5B come back.
    #:
    #: **AND LAB IMBALANCE IS A DIFFERENT PROBLEM.** Finding U's caveat -- "AI2 is 6
    #: of the 16" -- is about WEIGHTING (bias), not independence (variance).
    #: Deleting models fixes a bias problem by discarding variance you have. Weight
    #: by design, or report with and without the dominant lab, or use a random
    #: effect for lab; do not delete.
    rep = set()
    for root in {n["lineage"] for n in nodes}:
        cand = [m for m in _size_side(root) if lin_of2.get(m) == root]
        sized = [(m, pb.get(m, 0.0)) for m in cand if pb.get(m)]
        over = (load().get("rulings") or {}).get("representative") or {}
        pick = over.get(root) or (
            min(sized, key=lambda x: abs(x[1] - TARGET))[0] if sized else root)
        rep.add(pick)
        rep |= _aligned_from(pick)

    for n in nodes:
        n["scale_group"] = _find(n["lineage"])
        n["is_representative"] = int(n["model_id"] in rep)

    ids = {n["model_id"] for n in nodes}
    dangling = [e for e in edges if e["parent"] not in ids or e["child"] not in ids]
    return nodes, edges, dangling


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    nodes, edges, dangling = rows()
    ops = collections.Counter(e["op"] for e in edges)
    #: THE SAME PREDICATE AS THE VIEW. This line read `{e["child"] for e in edges}`
    #: and printed 47 while `{db}.roots` returned 54 -- two definitions of "root"
    #: in one file, which is the defect this whole repo exists to stop.
    roots = ({n["model_id"] for n in nodes}
             - {e["child"] for e in edges if e["op"] in DERIVING})
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
    #: `CREATE TABLE IF NOT EXISTS` IS A SILENT NO-OP ON A SCHEMA CHANGE. On
    #: 2026-08-15 three columns were added to the DDL, the statement ran clean
    #: against the existing table, the insert dropped the unknown columns, and
    #: the first query for one of them raised UNKNOWN_IDENTIFIER -- after the
    #: commit. The DDL reported success and changed nothing.
    #:
    #: This table is DERIVED from an authored file and costs a second to rebuild,
    #: so it is dropped rather than reconciled. Anything that cannot be dropped
    #: needs a migration, not an IF NOT EXISTS.
    for t in ("checkpoints", "edges"):
        ch.execute("DROP TABLE IF EXISTS {db}.%s" % t)
    for d in DDL:
        ch.execute(d)
    ch.insert("checkpoints", nodes)
    ch.insert("edges", edges)
    for name, sql in VIEWS.items():
        try:
            ch.execute(sql)
            print("  view %s.%s" % (ch.DB, name))
        except Exception as e:
            print("  view %s FAILED: %s" % (name, str(e)[:120]))
    #: THE CHECK THE DDL COULD NOT DO: every column named in the row dicts must
    #: exist on the table. A column silently dropped by an insert is a field that
    #: reads as absent forever after.
    cols = {c["name"] for c in ch.query(
        "SELECT name FROM system.columns WHERE database='%s' AND table='checkpoints'" % ch.DB)}
    want = set(nodes[0]) if nodes else set()
    if want - cols:
        raise SystemExit("  SCHEMA MISMATCH: table lacks %s" % sorted(want - cols))
    print("\n  %s.checkpoints %s | %s.edges %s"
          % (ch.DB, ch.scalar("SELECT count() FROM {db}.checkpoints"),
             ch.DB, ch.scalar("SELECT count() FROM {db}.edges")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
