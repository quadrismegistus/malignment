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
import functools
import json
import os
import re
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
#: `rlhf` and `apo` added 2026-08-15 from the card audit. **Both exist so that a
#: card's own word survives into the schema instead of being translated into a
#: neighbouring op by whoever transcribed it.**
#:
#: `beaver-7b-v1.0` and `internlm2-chat-7b` were both booked `dpo`; their cards
#: say "Safe RLHF" and "further trained ... by Online RLHF". Both are almost
#: certainly PPO underneath, and writing `ppo` would have been a fair guess --
#: but it is a guess about the ALGORITHM that neither card makes, and the
#: `algorithm` field in `attestations.json` is where that belongs once someone
#: sources it. An op should carry what the source said.
#:
#: `apo` is Anchored Preference Optimization (SmolLM3-3B). It is a preference
#: method like dpo/kto/slic and aligns, so it goes here rather than beside
#: distill.
#: `distill_align` is DISTILLATION USED AS THE POST-TRAINING, onto the model's
#: OWN base. Added 2026-08-16 because `distill` was carrying two unrelated
#: operations and the conflation was costing two lineages:
#:
#:   distill        DeepSeek-R1-Distill-Llama-8B <- Llama-3.1-8B
#:                  ANOTHER lab's base, retrained on a third model's traces.
#:                  Not alignment. Correctly excluded.
#:   distill_align  Qwen3-8B <- Qwen3-8B-Base, MiniCPM5-1B <- ...-SFT
#:                  the model's OWN base, KL to a teacher, and it IS the
#:                  post-training. Excluding it says these two labs did not
#:                  align their models, which is false.
#:
#: **The sources name the algorithm and neither names this category.** Qwen3
#: (arXiv:2505.09388): "Strong-to-Weak Distillation ... encompassing 5 dense
#: models (Qwen3-0.6B, 1.7B, 4B, 8B, and 14B)", student logits KL'd to
#: Qwen3-32B/235B. MiniCPM5: "we train specialized RL teachers ... and use
#: On-Policy Distillation (OPD)". So the op is named for the STRUCTURE (own base,
#: aligning) and the algorithm stays in `attestations.json`, per the rule above.
#:
#: TWO THINGS THIS OP DOES NOT SAY, both quoted from the attesting agents:
#:   - MiniCPM5's card gives THREE steps -- "SFT, RL, and OPD" -- and only OPD is
#:     edged, because the RL stage was never released as a checkpoint. "A roster
#:     reading method alone will not see the RL stage at all."
#:   - Qwen3-8B's post-training is distillation INSTEAD OF the four-stage
#:     pipeline, not in addition to it. Its "alignment" is KL-to-a-teacher.
#:     `Qwen/Qwen3-8B` declares `base_model: [Qwen/Qwen3-8B-Base]`; the report
#:     never states what the student is initialised from, so the PARENT rests on
#:     the card and the OP rests on the report.
ALIGNING = ("sft", "dpo", "rlvr", "ppo", "kto", "slic", "instruct",
            "rlhf", "apo", "distill_align")
#: `upscale` DERIVES: Falcon3-10B-Base is depth up-scaled FROM 7B with continual
#: pretraining, so it inherits 7B's pretraining and is a DESCENDANT. A derived
#: model is not an independent observation, and `scale` -- a RELATING op -- would
#: have asserted the opposite. `prune` likewise: Falcon3 1B and 3B are pruned and
#: healed FROM larger members on 80 Gigatokens, against 10B's 2 Teratokens. Kept
#: as SEPARATE ops because a 25x difference in post-derivation training is what
#: any independence argument would turn on.
#: `continual` DERIVES and does NOT align: the child is the parent trained on
#: more pretraining data, same size, no preference signal. Added 2026-08-15 for
#: `falcon-mamba-7b -> Falcon3-Mamba-7B-Base` ("Continue Pretrained from
#: Falcon-Mamba-7b, with another 1500 Gigatokens").
#:
#: **It is its own op because the alternatives are each wrong in a way that
#: would move a number.** `pretrain` is not a DERIVING op at all, so the edge
#: would vanish from `movement` rather than appear in it -- an op name that
#: silently deletes an edge is the worst of the three. `sft` would file 1500
#: Gigatokens of web and code under alignment and pollute the SFT-vs-DPO
#: division-of-labour GROUP BY, which is a finding. `upscale`/`prune` assert a
#: size change that did not happen.
#:
#: The same shape sits under `Yi-1.5-9B` (continual pretraining on Yi, +500B on
#: 3.1T) and `OLMoE-1B-7B-0125` (annealed from an 0924 branch); neither parent is
#: in this roster, so they are annotated in `provenance_notes` rather than edged.
DERIVING = ALIGNING + ("distill", "upscale", "prune", "continual")
RELATING = ("scale", "predecessor")

DDL = ["""
CREATE TABLE IF NOT EXISTS {db}.populations (
    kind LowCardinality(String), model String
) ENGINE = MergeTree ORDER BY (kind, model)
""", """
CREATE TABLE IF NOT EXISTS {db}.endpoints (
    base String, endpoint String, resolved_by LowCardinality(String)
) ENGINE = MergeTree ORDER BY base
""", """
CREATE TABLE IF NOT EXISTS {db}.checkpoints (
    model_id String, family Array(String),
    org_type LowCardinality(String), country LowCardinality(String),
    scale LowCardinality(String), open_weight UInt8, open_data UInt8,
    nickname LowCardinality(String), revision LowCardinality(String),
    revision_ladder UInt32, lineage String, depth UInt8, pretrained UInt8,
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
              "reasoning": int(bool((d or {}).get("reasoning"))),
              #: **DEFAULTS TRUE, AND THAT IS THE TRAP.** A node with no incoming
              #: edge is a base unless something says otherwise, so a checkpoint
              #: BECOMES a base when an edit removes its edge. phi-4 sat in the
              #: base->aligned population that way; Teuken-instruct-commercial
              #: would have, the moment its wrong-run edge came out. Carried into
              #: the row so the check and the query read the same field.
              "pretrained": int((d or {}).get("pretrained", True) is not False)}
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


def _report_unasserted_roots(nodes, edges):
    """Every root must be CORROBORATED as a base, not merely lack a parent.

    **A ROOT IS NOT NECESSARILY A BASE**, and the default runs the wrong way: a
    node with no incoming edge is treated as a pretrained base unless something
    says otherwise, so a checkpoint BECOMES a base by an edit that removes its
    edge. That is not hypothetical -- it happened twice:

      microsoft/phi-4    a root all along, attested `instruct_bundle`. Its card:
                         "We align the pretrained model with one round of SFT
                         4.1, one round of DPO". It sat in the base->aligned
                         population until RH asked where phi-4 appears.
      Teuken-7B-instruct-commercial-v0.4
                         BECAME a root the moment its wrong-run edge was removed,
                         and would have defaulted to base.

    So a root must either declare `pretrained: false` or be attested
    `method: pretrain`. Reported on every build rather than raised, because a
    newly added model legitimately has neither until it is audited -- and a check
    that blocks the build gets removed, while one that prints a name gets fixed.
    """
    import json
    import os
    par = {e["child"] for e in edges if e["op"] in DERIVING}
    roots = [n["model_id"] for n in nodes if n["model_id"] not in par]
    path = os.path.join(ROOT, "roster", "models", "attestations.json")
    att = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            att = (json.load(fh).get("checkpoints") or {})
    bad = []
    for m in roots:
        #: READ THE ROW, WHICH NOW CARRIES IT. The first version of this check
        #: read `pretrained` off the built row before `rows()` populated it, so
        #: it was always None and the check flagged all three DECLARED roots --
        #: a checker reporting the opposite of the truth because it read a
        #: different artifact than the one holding the answer.
        if not next((n.get("pretrained", 1) for n in nodes if n["model_id"] == m), 1):
            continue
        claims = (att.get(m) or {}).get("claims") or []
        if next((c.get("value") for c in claims if c.get("field") == "method"), None) == "pretrain":
            continue
        bad.append(m)
    if bad:
        print("  ROOTS NOT CORROBORATED AS BASES: %d -- each will enter the"
              "\n  base->aligned population unasserted. Declare `pretrained: false`"
              "\n  or attest `method: pretrain`:" % len(bad))
        for m in bad:
            print("     %s" % m)
    else:
        print("  roots corroborated as bases: %d/%d" % (len(roots), len(roots)))


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
    _report_unasserted_roots(nodes, edges)
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
    for t in ("checkpoints", "edges", "populations", "endpoints"):
        ch.execute("DROP TABLE IF EXISTS {db}.%s" % t)
    for d in DDL:
        ch.execute(d)
    ch.insert("checkpoints", nodes)
    ch.insert("edges", edges)
    #: THE RULE'S OUTPUT, SO SQL CAN JOIN ON IT. `alignment_edges` says "the
    #: roster does not choose" and that was right when no rule existed. One does
    #: now (`endpoints()`), and a seat writing SQL could not reach it -- which is
    #: how the same question got three incompatible answers. These are TABLES and
    #: not views because the rule lives in Python (it reads attestations and the
    #: family rulings); they are dropped and rebuilt whole, never appended, so
    #: they cannot drift from the rule that makes them.
    ep, unresolved = endpoints()
    if unresolved:
        print("  UNRESOLVED LINEAGES (not written): %s"
              % [b.split("/")[-1] for b in unresolved])
    #: `resolved_by` MUST NAME WHICH ONE DECIDED. Every row said
    #: `roster.endpoints` including the ones a person chose, so the column that
    #: exists to carry provenance was asserting the rule chose where it had
    #: abstained. The chain is re-run unruled to find out -- cheap, and the only
    #: way to tell from outside.
    chain, _ = endpoints(apply_rulings=False)
    ch.insert("endpoints", [
        {"base": b, "endpoint": e,
         "resolved_by": "roster.endpoints" if chain.get(b) == e else "rulings.endpoint"}
        for b, e in sorted(ep.items())])
    ruled_n = sum(1 for b, e in ep.items() if chain.get(b) != e)
    if ruled_n:
        print("  %d endpoint(s) decided by an AUTHORED RULING, not by the chain: %s"
              % (ruled_n, [b.split("/")[-1] for b in ep if chain.get(b) != ep[b]]))
    pop = []
    for kind in POPULATIONS:
        for m in sorted(population(kind)):
            pop.append({"kind": kind, "model": m})
    ch.insert("populations", pop)
    print("  %d endpoints | %d population rows across %d kinds"
          % (len(ep), len(pop), len(POPULATIONS)))
    for name, sql in VIEWS.items():
        try:
            ch.execute(sql)
            print("  view %s.%s" % (ch.DB, name))
        except Exception as e:
            print("  view %s FAILED: %s" % (name, str(e)[:120]))

    #: **THE TWO CHECKS THAT BELONG AT THE MOMENT THE WRONG STATE WOULD BE MADE,
    #: NOT IN A TEST NOBODY RUNS.** There is no CI here. `--write` has just
    #: refreshed `edges`, so this is the first instant at which `pairs` can be
    #: known stale, and it is the instant a seat is most likely to act on it.
    #: **A SILENT PASS IS INDISTINGUISHABLE FROM A CHECK THAT DID NOT RUN**, and
    #: this repo has shipped a `_guard` that existed only in a comment. Both
    #: report their reach on success: `0 conflicts` means nothing without the
    #: `of 7 checkable` beside it.
    probs, checkable = check_attested_topology()
    print("  attested topology: %d checkable, %d conflict(s)" % (checkable, len(probs)))
    for p in probs:
        print("     %s" % p)
    stale = check_derived()
    print("  {db}.pairs: %s".replace("{db}", ch.DB)
          % ("FRESH" if not stale else "%d problem(s)" % len(stale)))
    for p in stale:
        print("     %s" % p)
    if stale:
        print("  ^^ {db}.pairs is DERIVED FROM THE EDGES JUST WRITTEN and no "
              "longer matches them. Anything reading corpus.panel() is on the "
              "old population until produce_movement --run.")
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




#: Preference-optimisation ops. A chain's third rung is one of these.
PREF = ("dpo", "apo", "kto", "slic", "ppo", "rlhf")


def chains():
    """Declared `base -sft-> S -pref-> P` chains, one row each.

    LIVES HERE BECAUSE TWO EXPERIMENTS NEED THE SAME POPULATION.
    `division_of_labour/sft_share` (H1-H3) and `division_of_labour/lexical_domains`
    (L1-L3) must run on an identical chain set or the second cannot be compared
    to the first -- and L1 exists precisely to be compared to H3. Retyping it
    into the second experiment is how `produce_movement.DERIVING` came to be a
    copy missing five ops, which meant the Falcon3 upscale and prune edges had
    NEVER been in movement. One definition, imported twice.

    - pythia-2.8b's four archangel arms are ONE chain: `archangel-dpo` is the
      declared representative in models.yaml. Counting all four would quadruple
      one base's weight across a JS span of 0.0071-0.0081.
    - A root asserted `pretrained: false` is an aligned model with no released
      base (phi-4, Teuken-instruct-commercial) and cannot head a chain.
    """
    d = load()
    nodes, edges = d.get("nodes") or {}, d.get("edges") or []
    fams = d.get("families") or {}
    par = {c: (p, op) for p, op, c in edges if op in DERIVING}
    skip = set()
    for f, meta in fams.items():
        if meta.get("kind") == "method_variant" and not meta.get("representative"):
            for m, v in nodes.items():
                if f in (v.get("family") or []):
                    skip.add(m)
    out = []
    for child, (p, op) in par.items():
        if op not in PREF or child in skip:
            continue
        gp = par.get(p)
        if not gp or gp[1] != "sft":
            continue
        base = gp[0]
        if (nodes.get(base) or {}).get("pretrained") is False:
            continue
        out.append({"base": base, "sft": p, "pref": child, "pref_op": op})
    return out


ATTESTED_PATH = os.path.join(ROOT, "roster", "models", "attestations.json")


def attestations():
    """The ATTESTED file, or {} if it is absent. Loaded once, cheaply cached."""
    global _ATT
    try:
        return _ATT
    except NameError:
        pass
    try:
        with open(ATTESTED_PATH, encoding="utf-8") as fh:
            _ATT = json.load(fh)
    except Exception:                                          # noqa: BLE001
        _ATT = {}
    return _ATT


def endpoints(measured=None, attested=None, apply_rulings=True):
    """{base: endpoint} — one commodity-form endpoint per pretrained base.

    **THE ROSTER DELIBERATELY DOES NOT CHOOSE** (see the `alignment_edges` view:
    "the Llama root carries Meta's instruct AND five Tulu sft arms, and those are
    different comparisons"). This function is an EXPERIMENT'S rule, named and
    shared rather than retyped -- on 2026-08-16 it was written inline in four
    separate shell heredocs with slightly different filters each time, one of
    which matched `"lmo" in base` and so found 4 of 6 OLMo lineages because
    `OLMo-2` and `OLMoE` are capitalised differently.

    The filter chain, in order, each step justified by a case that forced it:

    1. TERMINAL under DERIVING edges, reached only by ALIGNING ops. Excludes
       `distill` (DeepSeek-R1-Distill-Llama), `continual`, `upscale`, `prune` --
       different operations, not alignment.
    2. NOT a declared `kind: ablation`. Four Tulu SFT arms are terminal only
       because nothing was built on them; counting them would weight one
       lineage's SFT five times, and one of them is deliberately safety-ablated.
    3. NOT attested `direction: inverted`. Four exist and each is quoted:
       dolphin x2 ("I have filtered the dataset to remove alignment and bias"),
       zephyr ("removing the in-built alignment of these datasets"), Hermes-3.
       A de-aligning finetune in an "alignment does X" average drags it toward
       zero, and its edge op is `sft` like any other.
    4. If several survive: the one whose family is declared `representative`.
    5. Else the one published by the BASE'S OWN publisher -- the commodity form,
       the version end users receive.
    6. Else return the candidates and let the caller refuse. **An undecided
       lineage is returned, never silently picked**: `unresolved` is the second
       element and a caller that ignores it is choosing by accident.

    `measured` optionally restricts to pairs that exist in the corpus.
    """
    d = load()
    nodes, edges = d.get("nodes") or {}, d.get("edges") or []
    fams = d.get("families") or {}
    par = {c: (p, op) for p, op, c in edges if op in DERIVING}
    kids = {}
    for c, (p, _op) in par.items():
        kids.setdefault(p, []).append(c)

    #: DEFAULTS TO LOADING THE ATTESTED FILE. It used to default to None, which
    #: meant NO attestations, which meant the `inverted` filter silently did not
    #: run -- a default that disables a guard is the guard's worst failure mode,
    #: and it made every caller pass `attestations=json.load(...)` to get correct
    #: behaviour. Pass `attested={}` to mean "explicitly none" (the test does).
    att = attestations() if attested is None else attested
    inverted = set()
    for mid, rec in ((att or {}).get("checkpoints") or {}).items():
        for cl in (rec.get("claims") or []):
            if cl.get("field") == "direction" and cl.get("value") == "inverted":
                inverted.add(mid)

    def kinds(m):
        return {fams.get(f, {}).get("kind")
                for f in (nodes.get(m, {}).get("family") or [])}

    def is_rep(m):
        return any(fams.get(f, {}).get("representative")
                   for f in (nodes.get(m, {}).get("family") or []))

    out, unresolved = {}, {}
    for base, v in nodes.items():
        if base in par or v.get("pretrained") is False:
            continue                                   # not a pretrained root
        cands, stack = [], [(base, [])]
        while stack:
            n, ops = stack.pop()
            ch_ = kids.get(n, [])
            if not ch_ and n != base:
                cands.append((n, ops))
            for c in ch_:
                stack.append((c, ops + [par[c][1]]))
        keep = [e for e, ops in cands
                if set(ops) <= set(ALIGNING)
                and "ablation" not in kinds(e)
                and e not in inverted
                and (measured is None or (base, e) in measured)]
        if not keep:
            continue
        if len(keep) == 1:
            out[base] = keep[0]
            continue
        rep = [e for e in keep if is_rep(e)]
        if len(rep) == 1:
            out[base] = rep[0]
            continue
        same = [e for e in keep if e.split("/")[0] == base.split("/")[0]]
        if len(same) == 1:
            out[base] = same[0]
            continue
        unresolved[base] = sorted(keep)

    #: 7. AN AUTHORED RULING, APPLIED ONLY TO WHAT THE CHAIN LEFT UNRESOLVED.
    #: The order is the whole safety property: a ruling can settle a case the
    #: rules cannot, and can never overturn a case they can. Applied before the
    #: chain it would be an invisible override of a derivable answer.
    #:
    #: Added 2026-08-17 for `stablelm`, whose two arms are both terminal, both
    #: `stabilityai`, and both attested `direction: standard` -- rules 2, 3 and 5
    #: all abstain. Before this existed the only ways to express the choice were
    #: to declare one arm an `ablation` or attest it `inverted`, and BOTH ARE
    #: FALSE OF IT: encoding a ruling as a fact about the model would have put a
    #: wrong claim into the file that every other consumer reads.
    #: The return stays a PAIR. A third element carrying ruling problems would
    #: be a value callers can ignore, which is the exact failure `unresolved`
    #: already documents ("a caller that ignores it is choosing by accident").
    #: So the two kinds of ruling defect go to the two places that cannot be
    #: ignored: a ruling naming a non-candidate RAISES here, and a ruling the
    #: chain no longer needs is reported by `check_authored`.
    #: `apply_rulings=False` returns what the CHAIN ALONE decides. It exists
    #: because the staleness check needs the pre-ruling state and the first
    #: version of that check tried to infer it from the post-ruling result --
    #: it called this function, which had already applied the ruling, and then
    #: reported the ruling as stale for having worked. **A checker cannot read
    #: the state it is checking through the thing it is checking.**
    for b, r in (((d.get("rulings") or {}).get("endpoint") or {})
                 if apply_rulings else {}).items():
        if b.startswith("_"):
            continue
        e = (r or {}).get("endpoint") if isinstance(r, dict) else r
        if b not in unresolved:
            continue                       # stale; `check_authored` reports it
        if e not in unresolved[b]:
            raise ValueError(
                "rulings.endpoint[%r] names %r, which is not one of that base's "
                "candidates %s. A ruling that resolves to nothing would leave the "
                "lineage unresolved while reading as decided."
                % (b, e, unresolved[b]))
        out[b] = e
        del unresolved[b]
    return out, unresolved


#: Quote fragments that mark a claim as naming a DIRECT PARENT rather than a
#: lineage root. Both HF card conventions.
_PARENT_PHRASES = ("inetuned from", "ase model")
_PARENT_FIELDS = ("released_base", "base", "parent", "finetuned_from")
_HF_URL = re.compile(r"huggingface\.co/([\w.\-]+/[\w.\-]+)")


def check_attested_topology(edges=None, att=None):
    """AUTHORED edges vs ATTESTED parent quotes. Returns problems, empty if clean.

    **THE TIER THE ROSTER NEVER READ AGAINST ITSELF.** `attest.unsourced()`
    checks attestations against attestations. Nothing checked them against the
    graph -- which is how `chat -dpo-> zephyr` survived while BOTH arms carried
    a quote naming the base as their parent. The refutation was in the repo,
    quoted, twice, and no code path could see it.

    **IT MUST BE THE PARENT QUOTE, NOT THE `lineage` FIELD.** Comparing attested
    `lineage` to the computed root would NOT have caught stablelm: under the
    fabricated chain zephyr's root was still the base. Only the direct-parent
    claim discriminates, and only because the card says "Finetuned from model"
    and links it.

    `edges` is a parameter so this can be RUN AGAINST A BROKEN ROSTER and shown
    to fire. A checker that can only read the current state cannot be
    demonstrated red, and this repository has shipped three checkers that read
    clean on the case they existed for.

    Reach today is 7 of 160 checkpoints. That ceiling is how many attestations
    carry a parseable "Finetuned from" URL -- **a reason to quote more, not to
    write a cleverer regex.** Silence here is not a clean bill.
    """
    if edges is None:
        edges = load().get("edges") or []
    att = attestations() if att is None else att
    parent = {c: p for p, op, c in edges if op in DERIVING}
    problems, checkable = [], 0
    for m, rec in ((att or {}).get("checkpoints") or {}).items():
        for cl in (rec.get("claims") or []):
            if cl.get("field") not in _PARENT_FIELDS:
                continue
            q = cl.get("quote") or ""
            if not any(p in q for p in _PARENT_PHRASES):
                continue
            named = [x.rstrip(".,)") for x in _HF_URL.findall(q)]
            named = [x for x in named if x != m]
            if not named:
                continue
            checkable += 1
            p = parent.get(m)
            if p is not None and p not in named:
                problems.append(
                    "TOPOLOGY vs ATTESTATION: %s is authored as a child of %s, "
                    "but its own attested quote names %s as the parent -- %.160r"
                    % (m, p, named, q))
    return problems, checkable


def check_derived():
    """`{db}.pairs` vs the roster it is supposed to be derived from.

    **A ROW COUNT DOES NOT DETECT STALENESS.** `pairs` sat a day behind
    `distill_align` at 146 rows where the roster implied 151, and 146 was as
    believable as 151 -- it surfaced only because an unrelated edit moved the
    number by the wrong amount. `endpoints`, `checkpoints` and `edges` rebuild
    from `roster --write`; `pairs` rebuilds only from `produce_movement --run`,
    so a roster edit updates three of four derived tables and silently leaves
    the fourth.

    Returns problems, empty if fresh. Imports `ch` lazily: this module holds a
    no-torch/no-daemon import contract that the test suite asserts.
    """
    from . import ch
    #: `buildable()` IS the producer's own definition, imported rather than
    #: restated. A freshness check that recomputes the target with a second
    #: implementation tests the two implementations against each other and calls
    #: their agreement freshness -- and this repo has already paid for two
    #: definitions of "root" in one file printing 47 against 54.
    from .produce_movement import buildable
    if not ch.exists("pairs"):
        return ["{db}.pairs does not exist"]
    want = {(e["base"], e["aligned"]) for e in buildable()}
    got = {(r["base"], r["aligned"]) for r in
           ch.query("SELECT base, aligned FROM pairs", limit_bytes=None)}
    out = []
    if want - got:
        out.append("STALE {db}.pairs: %d roster pair(s) missing, e.g. %s. "
                   "Rebuild with `produce_movement --run`."
                   % (len(want - got), sorted(want - got)[:3]))
    if got - want:
        out.append("ORPHAN {db}.pairs: %d row(s) the roster no longer declares, "
                   "e.g. %s." % (len(got - want), sorted(got - want)[:3]))
    return out


def check_authored(path=None):
    """Strict re-parse of models.yaml. Returns a list of problems, empty if clean.

    **`yaml.safe_load` SILENTLY KEEPS THE LAST OF A DUPLICATE KEY**, and on
    2026-08-16 that was hiding a real fact: `unavailable['mosaicml/mpt-7b']` had
    TWO `note:` entries, and the one recording that the weights had been
    RECOVERED FROM MIRRORS was the one being dropped. Every program reading the
    roster saw only "The repo is gone." A human reading the file saw both.

    Nothing reported it, because a silently-resolved duplicate is not an error
    to the parser that resolves it -- the file loads, the schema is satisfied,
    and the count of keys is right. It needs a stricter reader to see, which is
    why `ruamel.yaml` is a dependency for a file we otherwise only read.

    Not called from `load()`: that runs on nearly every code path and this is a
    whole-file re-parse. Call it from a test, the CLI, or before writing.
    """
    from ruamel.yaml import YAML
    from ruamel.yaml.constructor import DuplicateKeyError
    y = YAML()
    y.allow_duplicate_keys = False
    problems = []
    try:
        with open(path or AUTHORED, encoding="utf-8") as fh:
            y.load(fh)
    except DuplicateKeyError as e:
        problems.append("DUPLICATE KEY (safe_load would keep the last, silently): %s"
                        % str(e).replace("\n", " ")[:400])
    except Exception as e:                                    # noqa: BLE001
        problems.append("%s: %s" % (type(e).__name__, str(e)[:300]))

    #: A `rulings.endpoint` entry the chain no longer needs. `endpoints()`
    #: cannot report this -- it applies live rulings and returns a pair on
    #: purpose -- so it surfaces here, where authored-file defects belong.
    #: **A ruling that decides nothing still READS as in force**, which is the
    #: shape of a guard killed by a field shift: present, cited, inert.
    try:
        ruled = (load().get("rulings") or {}).get("endpoint") or {}
        if ruled:
            #: THE CHAIN ALONE. Asking the ruled view whether a ruling was
            #: needed gets "no" every time it worked.
            resolved, unres = endpoints(apply_rulings=False)
            for b, r in ruled.items():
                if b.startswith("_"):
                    continue
                if b in unres:
                    continue                            # would have raised
                if b in resolved and resolved[b] == (
                        (r or {}).get("endpoint") if isinstance(r, dict) else r):
                    problems.append(
                        "STALE RULING rulings.endpoint[%r]: the chain now "
                        "resolves this base on its own. The ruling agrees, so "
                        "nothing is wrong today -- but it is deciding nothing "
                        "and should be retired or its `why` re-checked." % b)
                elif b in resolved:
                    problems.append(
                        "CONTRADICTED RULING rulings.endpoint[%r]: the chain "
                        "resolves to %r without it. Rulings are applied only to "
                        "unresolved bases, so this one is INERT while reading as "
                        "decisive." % (b, resolved[b]))
                else:
                    problems.append(
                        "ORPHAN RULING rulings.endpoint[%r]: not a pretrained "
                        "root with terminal aligned arms." % b)
    except Exception as e:                                    # noqa: BLE001
        problems.append("ruling check failed: %s: %s" % (type(e).__name__, str(e)[:200]))
    return problems


#: TRAINING ORDER, with INCOMPARABILITY declared. `ALIGNING` is a set and says
#: nothing about sequence; this says base precedes sft precedes any preference
#: method precedes rlvr, AND that the preference methods are alternatives rather
#: than a sequence -- kto->dpo has no direction, and claiming one would invent an
#: ordering the training never had. Carried from the archive's `step.py`, which
#: is otherwise a WHERE clause: this tuple is the part that was knowledge.
STAGE_ORDER = (
    ("base", "pretrain"),
    ("sft", "distill", "continual"),
    #: `distill_align` sits in the PREFERENCE tier, not beside `distill` in the
    #: sft tier, because it is the LAST post-training stage in both lineages that
    #: use it -- MiniCPM5 runs sft THEN opd, so `sft -> distill_align` must read
    #: forward. It is not claimed to be a preference method; the tier is an
    #: ordering, and this is where the ordering puts it.
    ("dpo", "kto", "ppo", "slic", "orpo", "simpo", "instruct", "rlhf", "apo",
     "distill_align"),
    ("rlvr",),
)


def stage_rank(op):
    """Index in STAGE_ORDER, or None if the op is not a training stage."""
    for i, tier in enumerate(STAGE_ORDER):
        if op in tier:
            return i
    return None


def direction(pre_op, post_op):
    """'forward' | 'reverse' | 'incomparable' | 'unknown'.

    The archive stamped this on every cell rather than refusing a reverse pair,
    because teacher-forcing base->sft and then sft->base is real work here -- so
    a step that raised on reverse order would block the experiment. Detectable
    rather than forbidden. v3 currently holds ZERO reverse pairs, so this has no
    work today; it is here so that a reverse arm cannot be pooled with a forward
    one WITHOUT the mixing being visible.

    `incomparable` is not a failure: two preference methods on the same rung are
    alternatives and their contrast has no direction at all.
    """
    a, b = stage_rank(pre_op), stage_rank(post_op)
    if a is None or b is None:
        return "unknown"
    if a == b:
        return "incomparable"
    return "forward" if a < b else "reverse"


#: EVERY POPULATION A SEAT MIGHT MEAN, in one place with one name each.
#: RH: "what about other cases? (all checkpoints of representative families, all
#: checkpoints, all chains)". Before this they were four different one-off
#: comprehensions in four files, which is how `panel()` and the endpoint rule
#: both came to have three incompatible versions.
POPULATIONS = ("all", "bases", "aligned", "endpoints", "chain_rungs",
               "representative", "unavailable")


def population(kind="endpoints", measured=False):
    """A named set of model ids. `measured=True` keeps only those with cells.

        all             every declared node                          160
        bases           pretrained roots (excludes pretrained:false)  50
        aligned         every child by an ALIGNING op                 99
        endpoints       one commodity-form endpoint per lineage       48
        chain_rungs     every rung of a base->sft->pref chain         52
        representative  members of a family declared representative
        unavailable     declared and deliberately NOT measurable

    **`endpoints` and `chain_rungs` ARE DIFFERENT POPULATIONS AND BOTH ARE
    RIGHT.** An endpoint asks "what does a user receive"; a chain rung asks
    "which stage did it". 48 lineages have an endpoint, 16 have a full chain,
    because most labs never publish the middle.

    `unavailable` is a population too: `gpt-sw3` is declared with
    `kind: access_denied, permanent: true` and kept OUT of `nodes` so it cannot
    inflate a declared population above the measurable one.
    """
    if kind not in POPULATIONS:
        raise ValueError("kind must be one of %s, got %r" % (POPULATIONS, kind))
    d = load()
    nodes = d.get("nodes") or {}
    par = {c: (p, op) for p, op, c in (d.get("edges") or []) if op in DERIVING}
    fams = d.get("families") or {}
    if kind == "all":
        out = set(nodes)
    elif kind == "bases":
        out = {m for m, v in nodes.items()
               if m not in par and v.get("pretrained") is not False}
    elif kind == "aligned":
        out = {m for m, (p, op) in par.items() if op in ALIGNING}
    elif kind == "endpoints":
        out = set(endpoints()[0].values())
    elif kind == "chain_rungs":
        out = {x for c in chains() for x in (c["base"], c["sft"], c["pref"])}
    elif kind == "representative":
        rep = {f for f, m in fams.items() if m.get("representative")}
        out = {m for m, v in nodes.items() if rep & set(v.get("family") or [])}
    else:                                                       # unavailable
        return set(d.get("unavailable") or {})
    if measured:
        from . import ch
        have = {r["model"] for r in
                ch.query("SELECT DISTINCT model FROM {db}.twp_words")}
        out &= have
    return out


if __name__ == "__main__":
    sys.exit(main())



def lineages(ops=ALIGNING, measured=None):
    """{root: [every model reached from it]} -- the SIBLING SET, not the path.

        roster.lineages()["meta-llama/Llama-3.1-8B"]
        -> 11 models: Instruct, Tulu-3 SFT/DPO, the no-safety ablation,
           Hermes, Dolphin, R1-Distill ...

    **`endpoints()` AND `paths()` BOTH COLLAPSE A LINEAGE TO ONE ENDPOINT**, and
    that is right for their questions and wrong for this one. RH's comparisons
    are SIBLING comparisons -- `llama-base` against `llama-instruct`, against
    `tulu-sft`, against `tulu-dpo`, against the no-safety ablation -- four
    children of one root, which `endpoints()` reports as a single row. Nothing in
    the population vocabulary named that set, so the v4 union top-up had to walk
    the edge list by hand, and the first hand-walk was wrong.

    ## WHY THE DEFAULT IS `ALIGNING` AND NOT `DERIVING`

    `models.yaml` states it and nothing enforced it: **`scale` and `predecessor`
    are RELATING, NOT DERIVING.** Walking every edge makes
    `Olmo-3-1025-7B <- predecessor <- OLMo-2-0425-1B` a parent link and reports a
    fifteen-model OLMo lineage that does not exist -- two different pretraining
    runs merged because one succeeds the other. `DERIVING` already excludes
    those, but it still admits `SIZE_OPS` (`upscale`, `prune`), which put
    Falcon3-1B and Falcon3-10B in one group: a SCALE comparison, not an
    alignment one.

    So the default is the set the comparisons actually use. Pass `ops=DERIVING`
    to include distillation and continual pretraining deliberately.

    Every node appears exactly once, including roots with no children -- a
    lineage of one is a fact about the publisher, not an absence.
    """
    d = load()
    par = {c: p for p, op, c in (d.get("edges") or []) if op in ops}

    def root(m):
        seen = set()
        while m in par and m not in seen:
            seen.add(m)
            m = par[m]
        return m

    #: **THE SAME QUERY `population()` USES**, not a private helper. My first
    #: version called `_measured_ids()`, which does not exist -- an untested
    #: keyword argument that raised NameError the moment anyone passed it, and
    #: the three tests I wrote alongside all left it at the default.
    keep = None
    if measured:
        from . import ch
        keep = {r["model"] for r in
                ch.query("SELECT DISTINCT model FROM {db}.twp_words")}
    out = {}
    for m in sorted(d.get("nodes") or {}):
        if keep is not None and m not in keep:
            continue
        out.setdefault(root(m), []).append(m)
    return {r: sorted(v) for r, v in sorted(out.items())}


def paths(measured=None):
    """[{base, endpoint, nodes, ops, n_steps}] -- the FULL path to each lineage's endpoint.

    `endpoints()` returns the two ends and `chains()` returns exactly
    base->sft->pref. Neither answers "what did this lineage actually go
    through", and the answer is not uniform: **a path is 2 nodes for a lab that
    ships one aligned model and 4 for one that publishes every rung.**

        meta-llama/Llama-3.1-8B  -instruct->  Llama-3.1-8B-Instruct      2 nodes
        LLM360/Amber  -sft->  AmberChat  -dpo->  AmberSafe               3 nodes
        allenai/Olmo-3-1025-7B -sft-> -SFT -dpo-> -DPO -rlvr-> Instruct  4 nodes

    **THE LENGTH IS A FACT ABOUT THE PUBLISHER, NOT ABOUT THE PIPELINE.**
    Baichuan2-7B-Chat is one step here and its own paper describes SFT followed
    by RLHF -- the SFT rung was simply never released. So a 2-node path means
    "one released rung", never "one training stage", and any per-stage claim over
    these paths is a claim about the open-science subpopulation.

    `nodes` includes the base; `ops[i]` is the operation from `nodes[i]` to
    `nodes[i+1]`, so `len(ops) == len(nodes) - 1 == n_steps`.
    """
    d = load()
    par = {c: (p, op) for p, op, c in (d.get("edges") or []) if op in DERIVING}
    ep, _unresolved = endpoints(measured=measured)
    out = []
    for base, end in sorted(ep.items()):
        nodes_, ops = [end], []
        cur = end
        while cur in par and cur != base:
            p, op = par[cur]
            ops.insert(0, op)
            nodes_.insert(0, p)
            cur = p
        out.append({"base": base, "endpoint": end, "nodes": nodes_, "ops": ops,
                    "n_steps": len(ops)})
    return out


# ─────────────────────────────────────────────────────────────────────────────
# ENVIRONMENT: what a checkpoint needs, and what to rent to give it.
#
# NINE SOURCES ACROSS TWO REPOS BECAME FOUR FILES, and the point of this section
# is that a caller reads NONE of them. `malign-logits` held the knowledge in
# model_requirements.json, model_load_environments.json, vllm_engine_support.json,
# cloud_profiles.json, weights_audit.csv, twp.py's LOADER_OVERRIDE,
# build_fleet.py's LAUNCH_PROFILE and two prose docs -- and the map between the
# two profile vocabularies existed only as a dict literal on line 78 of a script.
#
# THREE FACT CLASSES, THREE KEYS, AND THEY DO NOT FOLD INTO EACH OTHER:
#
#   REQUIREMENT  per CHECKPOINT              models.yaml  nodes[m].env
#   OUTCOME      per (MODEL x ENVIRONMENT)   observations.json  observations
#   SUPPORT      per (ARCHITECTURE x ENGINE) observations.json  engine_support
#
# The second is why `environment()` never returns "it works". Seven models carry
# both a load_failed and a loads; AmberSafe did both ON ONE BOX, twenty minutes
# apart, either side of `pip install sentencepiece protobuf`. The third is why
# `engine` is an argument and not a field: Aquila is not broken, vLLM DELETED
# AquilaForCausalLM after v0.24.0 and it runs on the 0.22.1 image.
# ─────────────────────────────────────────────────────────────────────────────

ENVIRONMENTS_PATH = os.path.join(ROOT, "roster", "environments.yaml")
OBSERVATIONS_PATH = os.path.join(ROOT, "roster", "models", "observations.json")


@functools.lru_cache(maxsize=1)
def load_environments():
    """The authored vocabulary: `profiles`, `boxes`, `launch` map, `sizing`."""
    import yaml
    with open(ENVIRONMENTS_PATH, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


@functools.lru_cache(maxsize=1)
def observations():
    """OBSERVED: (model x environment) outcomes and (arch x engine) support."""
    with open(OBSERVATIONS_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def _sizing(params_b):
    """(min_vram_gb, gpus) from measured parameters.

    **DERIVED, NEVER TRANSCRIBED.** The archive wrote these per model; across
    159 rows they are a clean step function of `params_b` with no overlaps, so
    160 hand-written copies would have been 160 derived values with no producer
    -- and the first one to go stale would go stale silently.
    """
    #: **UNKNOWN SIZE IS NOT SMALL.** Returning a default here is how a
    #: mis-keyed lookup became a silent downsize: `(params_b or 0)` made every
    #: unmeasured model 24 GB. (None, None) forces the caller to say so.
    if not params_b:
        return None, None
    steps = load_environments()["sizing"]["steps"]
    for s in steps:
        if s["max_params_b"] is None or params_b <= s["max_params_b"]:
            return s["vram_gb"], s["gpus"]
    return steps[-1]["vram_gb"], steps[-1]["gpus"]


def environment(model, engine=None, measured=None):
    """Everything `model` needs, merged: profile floors + its own overrides.

        roster.environment("Zyphra/Zamba2-7B")
        roster.environment("BAAI/Aquila2-7B", engine="0.27.1")

    Returns a dict with `profile`, `box`, `image`, the resolved pins, `why`,
    `min_vram_gb`/`gpus` (derived from measured params), plus:

      `observations`  every (model x environment) row for this model. **A LIST,
                      possibly contradictory, never collapsed to a verdict.**
      `engine`        present only when `engine=` was passed: the
                      (architecture x engine) ruling, with the recovery image.

    THERE IS NO `ok` FIELD AND THAT IS DELIBERATE. The question "will this
    load?" has no answer keyed on the model alone, and a boolean here would be
    read as one. `observations` is what we saw, `blocked` is what was ruled.
    """
    envs = load_environments()
    node = load()["nodes"].get(model)
    if node is None:
        raise KeyError("%s is not in the roster" % model)
    env = dict(node.get("env") or {})
    prof_name = env.get("profile", "default")
    prof = dict(envs["profiles"][prof_name])
    #: A per-model `box:` overrides the profile's default box. The profile
    #: says what SOFTWARE the model needs; the box must also physically hold it,
    #: and those are different questions that the archive answered in one field.
    box_name = env.get("box") or prof.pop("launch")
    prof.pop("launch", None)
    prof.pop("why", None)

    out = dict(prof)
    out.update({k: v for k, v in env.items() if k != "profile"})
    out["profile"] = prof_name
    out["box"] = box_name
    box = envs["boxes"][box_name]
    out["image"] = box.get("image")
    #: THE BOX'S PINS AND THE MODEL'S ARE BOTH REQUIRED, and a set union is
    #: wrong when both name the same package at different versions -- the
    #: model's is the stricter statement and wins. `ssm` pins
    #: transformers==4.57.1 for Zamba2 while the profile floor says >=4.57.
    out["box_pins"] = list(box.get("pins") or [])

    if measured is None:
        measured = _measured_params()
    p = measured.get(model)
    out["params_b"] = p
    #: TWO SIZES, AND THEY ANSWER DIFFERENT QUESTIONS. `box_*` is what the
    #: declared box PROVIDES; `needs_*` is what the measured parameters DEMAND,
    #: and is None when nothing has measured them. Collapsing them into one
    #: number is what let an unmeasured 70B report 24 GB.
    out["box_vram_gb"] = box.get("min_gpu_ram")
    out["box_gpus"] = box.get("num_gpus")
    out["needs_vram_gb"], out["needs_gpus"] = _sizing(p)

    obs = observations()
    out["observations"] = [o for o in obs["observations"]
                           if o["model_id"] == model]

    if engine is not None:
        out["engine"] = _engine_ruling(model, engine, obs)
    return out


@functools.lru_cache(maxsize=1)
def _measured_params():
    """{model: params_b} from measurements.json -- OBSERVED, not authored."""
    try:
        with open(os.path.join(ROOT, "roster", "models",
                               "measurements.json"), encoding="utf-8") as fh:
            m = json.load(fh)
    except FileNotFoundError:
        return {}
    #: THE RUNS ARE NESTED UNDER `sections`. Reading `m["weights"]` returns
    #: None, `_sizing(None)` fell through to the FIRST step, and every one of
    #: 160 checkpoints came back 24 GB / 1 GPU -- including the 70B pair, which
    #: needs 2x80. It planned cleanly and would have OOMed after paying for a
    #: 140 GB download. Nothing failed; the number was just quietly the
    #: smallest one available.
    #:
    #: **EVERY SECTION THAT CARRIES params_b IS READ, NOT A NAMED ONE.** The
    #: safetensors route cannot measure a .bin repo at all -- it recorded 19
    #: models as "no safetensors metadata published" -- so a second pass by a
    #: different route is not an exception, it is the normal shape here. Naming
    #: one section would have meant that pass landing and changing nothing,
    #: which is the quietest possible way to waste a measurement.
    #:
    #: On conflict the LATER `measured_at` wins. A checkpoint's parameters are
    #: true of it AS IT STOOD -- `Aquila2-7B`'s `main` was replaced with a
    #: re-tokenised model once already -- so "most recently observed" is the
    #: only defensible rule, and it needs the stamp the file already requires.
    out, stamp = {}, {}
    for name, sec in (m.get("sections") or {}).items():
        at = sec.get("measured_at") or ""
        for k, v in (sec.get("models") or {}).items():
            p = (v or {}).get("params_b") if isinstance(v, dict) else None
            if not p:
                continue
            if k not in out or at >= stamp[k]:
                out[k], stamp[k] = p, at
    return out


def _engine_ruling(model, engine, obs):
    """(architecture x engine) verdict for `model` under vLLM `engine`.

    Keyed on ARCHITECTURE because that is the fact's shape: `BaichuanForCausalLM`
    was removed after 0.23.0 and every Baichuan goes with it. Returns None when
    the architecture has no ruling, which means UNTESTED, not supported.
    """
    for arch, v in (obs.get("engine_support") or {}).items():
        if not isinstance(v, dict) or model not in (v.get("models") or []):
            continue
        rec = (load_environments().get("engine_recovery") or {})
        r = {"architecture": arch, "status": v.get("status"),
             "recovery_box": rec.get(arch),
             "last_working": v.get("last_working"),
             "recovery": v.get("recovery"), "do_not": v.get("do_not")}
        lw = v.get("last_working")
        if v.get("status") == "removed" and lw:
            r["usable"] = _ver(engine) <= _ver(lw)
        return r
    return None


def _ver(s):
    return tuple(int(x) for x in str(s).split(".") if x.isdigit())


def fleet(models, engine=None):
    """Group `models` into boxes to rent. The plan, not the rental.

        for box in roster.fleet(roster.population("endpoints"))["boxes"]:
            print(box["box"], box["image"], len(box["models"]))

    A row is a REQUIREMENT GROUP, not a machine: the key is (box, image,
    box_pins, transformers, kernels, compute_dtype), so one box shape appears
    once per distinct requirement. `len(...["boxes"])` is therefore a count of
    groups, and `{b["box"] for b in ...}` is the count of machines.

    **GROUPING IS BY REQUIREMENT FIRST AND COUNT SECOND, NEVER THE REVERSE**, and
    that ordering was paid for: on 2026-08-10 a `dense` box pulled 15 GB of
    Zamba2 and died on a kernel it did not have, and four more checkpoints burned
    their downloads on transformers 5.14.1 before `tf457` existed as a name. A
    box that downloads a model it cannot load has paid for the download anyway.

    **IT REFUSES RATHER THAN GUESSES.** A model with no `env:` is returned under
    `unassigned`, never silently placed in `default`. Baichuan2 once fell out of
    every shard when a spec was regenerated, had zero cells anywhere, and no
    completion count showed it -- a model absent from the plan is absent from
    the denominator too, so the fleet reported 100% of a roster that had quietly
    shrunk. Blocked models come back under `blocked` WITH THEIR REASON: a hole
    with a reason beside it is a decision, a hole without one is an accident
    nobody can date.
    """
    nodes = load()["nodes"]
    boxes, blocked, unassigned = {}, [], []
    for m in models:
        node = nodes.get(m)
        if node is None or not node.get("env"):
            unassigned.append(m)
            continue
        e = environment(m, engine=engine)
        if e.get("blocked"):
            blocked.append({"model": m, "blocked": e["blocked"],
                            "why": e.get("why")})
            continue
        key = (e["box"], e["image"], tuple(sorted(set(e["box_pins"]))),
               e.get("transformers"), tuple(e.get("kernels") or ()),
               e.get("compute_dtype"))
        b = boxes.setdefault(key, {
            "box": e["box"], "image": e["image"], "gpus": e["box_gpus"],
            "pins": sorted(set(e["box_pins"])), "transformers": e.get("transformers"),
            "kernels": list(e.get("kernels") or []),
            "compute_dtype": e.get("compute_dtype"),
            "box_vram_gb": e["box_vram_gb"],
            "needs_vram_gb": None, "unmeasured": [], "models": []})
        b["models"].append(m)
        if e["needs_vram_gb"] is None:
            b["unmeasured"].append(m)
        else:
            b["needs_vram_gb"] = max(b["needs_vram_gb"] or 0, e["needs_vram_gb"])
    return {"boxes": sorted(boxes.values(), key=lambda b: -len(b["models"])),
            "blocked": blocked, "unassigned": sorted(unassigned)}


def check_environments():
    """Problems in the env declarations. Empty list if clean.

    **THE COVERAGE GATE IS THE POINT.** "Every checkpoint declares its
    environment" is a claim that decays the moment someone adds a model, and a
    claim that decays silently is worse than none: `build_fleet` would place the
    new model in `default` and a fleet would pay for a download it cannot use.

    A `why` is required on every override AND on every non-default profile. The
    first version of this check asked only whether SOME `why` existed and passed
    Zamba2, whose `kernels` override was 'explained' by a sentence about
    transformers -- a coarse predicate standing in for a fine fact.
    """
    envs = load_environments()
    profiles, boxes = envs["profiles"], envs["boxes"]
    problems = []
    for m, node in sorted(load()["nodes"].items()):
        e = node.get("env")
        if not e:
            problems.append("%s: no env: block" % m)
            continue
        p = e.get("profile")
        if p not in profiles:
            problems.append("%s: profile %r is not declared" % (m, p))
            continue
        if profiles[p]["launch"] not in boxes:
            problems.append("%s: profile %r launches on undeclared box %r"
                            % (m, p, profiles[p]["launch"]))
        overrides = set(e) - {"profile", "why"}
        if (overrides or p != "default") and not (e.get("why") or "").strip():
            problems.append("%s: %s but no why" %
                            (m, "overrides %s" % sorted(overrides)
                             if overrides else "profile %r" % p))
    #: **THE BOX MUST PHYSICALLY HOLD THE MODEL**, and this is the check whose
    #: absence let four 32B checkpoints sit on a 48 GB profile. Compared against
    #: `provides_vram_gb` (the card class) and not `min_gpu_ram` (the search
    #: floor, 47) -- one GB apart and a whole hardware tier apart.
    for m, node in sorted(load()["nodes"].items()):
        e = node.get("env") or {}
        if not e.get("profile"):
            continue
        r = environment(m)
        if r["needs_vram_gb"] is None:
            continue
        box = boxes[r["box"]]
        if r["needs_vram_gb"] > (box.get("provides_vram_gb") or 0):
            problems.append("%s: %.1fB needs %s GB but box %r provides %s"
                            % (m, r["params_b"], r["needs_vram_gb"], r["box"],
                               box.get("provides_vram_gb")))
        if (r["needs_gpus"] or 1) > (box.get("num_gpus") or 1):
            problems.append("%s: needs %s GPUs but box %r has %s"
                            % (m, r["needs_gpus"], r["box"], box.get("num_gpus")))

    #: A profile nothing uses is not an error, but a profile whose BOX cannot
    #: satisfy its kernels is: that is the Zamba2 defect in its general form.
    for name, prof in profiles.items():
        need = set(prof.get("kernels") or ())
        if need and not need <= set(boxes[prof["launch"]].get("pins") or ()):
            problems.append("profile %r needs kernels %s but launches on %r, "
                            "which pins %s" % (name, sorted(need), prof["launch"],
                                               boxes[prof["launch"]].get("pins")))
    return problems
