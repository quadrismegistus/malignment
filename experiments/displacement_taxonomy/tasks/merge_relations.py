"""Build a vocabulary of displacement operations by folding relations into a register.

A SequentialTask over the stage-1 relations. Each chunk of relations is judged
against the register built so far, and the register is fed forward. This is RH's
snowball: once two things are merged, what the next reader sees is the merged one.

## What a relation is

Stage 1 shows a rater two ranked word lists for one sentence -- the base model's
completions and the aligned model's -- and asks what relation connects them. The
rater invents a name and describes the change. 720 cells (40 prompts x 18 model
lineages) produced 872 two-sided relations at high or medium confidence, a mean
of 1.21 per cell. That thinness is why per-prompt grouping produced constructs
resting on a single reading, and why the unit here is the RELATION rather than
the construct: relations are the primitive and nothing shrinks.

## Why this replaces the accretion it supersedes

The previous design folded per-prompt CONSTRUCTS into a vocabulary one prompt at
a time. It refused 36 merges of 40, and two independent pilots found the reason
was structural rather than a matter of prompting: every decision was
candidate-into-entry or candidate-as-new, so **two existing entries could never
merge with each other**. Redundancy inside the first prompt's own construct set
was frozen in permanently and each later prompt could only add. Both pilots
flagged the same pair (A/H) as under-differentiated and neither could act on it.

`CharacterRegister.apply_same_as` in `extract_social_network.py` is the fix, and
it is why this is modelled on that task: the register can merge two entries that
are already in it, at any chunk, on later evidence. The vocabulary can shrink.

## What the judge is shown, and what it is not

Shown: the register (each cluster's operation statement, its aliases, how many
sentences it spans, a couple of example word lists), and the chunk's relations
with their frames.

NOT shown: which model lineage produced a relation, whether an arm is base or
aligned, and any theory vocabulary. `displacement`, `condensation` and
`foreclosure` are mapped on post-hoc in the analysis, exactly as
`classify_alignment_transformation` does it, so the judge cannot label to the
theory it is being used to test.

## Two things measured elsewhere that determine the design here

**Word overlap is not evidence and is not offered as such.** Across the 171
entry pairs of the first accretion run, the pair known to belong together ranked
60th of 171 at a mean Jaccard of 0.024, while the top pair at 0.500 was a
coincidence of two tiny word sets. Across sentences the tokens are the variable
and the operation is the invariant, so token overlap indexes subject matter,
which is the confound. Example words are labelled as illustration for that
reason.

**Uncertainty defaults to keeping things apart, not to merging.** The accretion
instrument said the opposite -- "if you cannot say what that difference IS ...
they should be merged" -- and a pilot reported it pushing toward merges it could
not defend. `resolve_characters` states the house convention: "When uncertain,
keep clusters separate rather than guessing." A wrongly split pair is visible in
the output as two similar clusters and can be merged later by `same_as`; a
wrongly merged pair has destroyed the evidence that it was ever two.

## Field ordering

Two schema variants, per the bake-off in `classify_alignment_transformation`.
Variant A decides then justifies; variant B states the operation first and then
decides. The accretion schema was A-shaped and its decisions read as post-hoc.
`discriminate.py` holds 20 triads with known answers, which is the gold set the
bake-off runs against. `MergeTask` is reassigned once that is measured.
"""

import json
import re
from copy import deepcopy
from typing import Literal

from pydantic import BaseModel, Field

from largeliterarymodels.task import SequentialTask


# ── Shared types ────────────────────────────────────────────────────────

ConfidenceLevel = Literal['high', 'medium', 'low']

#: Applied post-hoc in analysis; never shown to the judge. Same discipline as
#: THEORY_MAP in classify_alignment_transformation.
THEORY_MAP = {
    'substitution': 'displacement',
    'register': 'condensation',
    'abandonment': 'foreclosure',
}

_OP_DESC = (
    "One sentence saying what KIND of change this is, phrased so it would apply "
    "equally to a sentence about some other subject. Name what sort of thing "
    "differs, not which words differ. This sentence becomes the cluster's "
    "definition and is what the next reader compares against."
)

_CONF_DESC = (
    "'high': the placement is unambiguous. 'medium': reasonably clear but some "
    "judgment involved. 'low': genuinely uncertain, and the cluster should be "
    "treated as provisional."
)


# ── Schema ──────────────────────────────────────────────────────────────

class Placement(BaseModel):
    """Where one relation goes."""
    rid: str = Field(description="The relation's id, copied exactly.")
    operation: str = Field(description=_OP_DESC)
    cluster: str = Field(
        description="The id of the existing cluster this relation performs the "
        "same operation as (e.g. 'K003'), or the word 'new' if no existing "
        "cluster names this operation. When genuinely uncertain, answer 'new' "
        "and mark confidence low: a cluster wrongly kept apart is visible later "
        "and can still be merged, whereas a wrong merge destroys the evidence "
        "that there were ever two things.")
    name: str = Field(
        description="Two to four words naming the operation. If placing into an "
        "existing cluster, the name you would give the cluster now that it "
        "includes this relation, which may be its current name.")
    confidence: ConfidenceLevel = Field(description=_CONF_DESC)


class PlacementReasonFirst(BaseModel):
    """Variant B: state the operation before choosing where it goes."""
    rid: str = Field(description="The relation's id, copied exactly.")
    operation: str = Field(description=_OP_DESC)
    cluster: str = Field(description=Placement.model_fields['cluster'].description)
    name: str = Field(description=Placement.model_fields['name'].description)
    confidence: ConfidenceLevel = Field(description=_CONF_DESC)


class SameAs(BaseModel):
    """Two clusters ALREADY IN THE REGISTER that name one operation.

    The reason this task exists in this shape. The design it replaces could only
    ever grow its vocabulary, so two near-duplicate entries created early stayed
    apart however much later evidence accumulated.
    """
    a: str = Field(description="Cluster id, e.g. 'K002'.")
    b: str = Field(description="The other cluster id.")
    reason: str = Field(
        description="One sentence on why these name the same operation, in terms "
        "that do not depend on the particular words. Only propose this when you "
        "could not state a difference a reader would reliably reproduce.")


class ChunkResult(BaseModel):
    placements: list[Placement] = Field(
        description="One entry for every relation in this chunk, in order.")
    same_as: list[SameAs] = Field(
        default_factory=list,
        description="Pairs of EXISTING clusters that should be merged. Usually "
        "empty. Propose one only when the new relations have shown that two "
        "clusters you were previously shown are the same operation.")
    notes: str = Field(
        default="", description="Anything that did not fit, briefly.")


class ChunkResultReasonFirst(ChunkResult):
    placements: list[PlacementReasonFirst] = Field(
        description="One entry for every relation in this chunk, in order.")


# ── The register ────────────────────────────────────────────────────────

class ConstructRegister:
    """Clusters of relations, with union-find merging.

    Modelled on CharacterRegister in extract_social_network.py. The `merged`
    chain plus `resolve_id` is what lets a cluster id survive being merged away:
    a later chunk may refer to an id that no longer exists, and resolving it is
    cheaper and safer than forbidding it.
    """

    def __init__(self):
        self.clusters = {}   # cid -> dict
        self.merged = {}     # dead cid -> surviving cid
        self._n = 0

    def new(self, operation, name, rid, prompt, confidence):
        self._n += 1
        cid = "K%03d" % self._n
        self.clusters[cid] = {
            "cid": cid, "name": name, "operation": operation,
            "aliases": [], "members": [rid], "prompts": [prompt],
            "confidences": [confidence],
        }
        return cid

    def add_member(self, cid, rid, prompt, name, operation, confidence):
        cid = self.resolve_id(cid)
        c = self.clusters.get(cid)
        if c is None:
            return None
        c["members"].append(rid)
        if prompt not in c["prompts"]:
            c["prompts"].append(prompt)
        c["confidences"].append(confidence)
        #: The placing reader saw BOTH the cluster and the new relation, so its
        #: operation statement is the more general one and supersedes. The old
        #: name is kept as an alias rather than discarded: the spread of names a
        #: cluster has attracted is evidence about it, and three harmonisers
        #: naming one identical partition three ways is why names are not the
        #: unit of comparison here.
        if name and name != c["name"]:
            if c["name"] not in c["aliases"]:
                c["aliases"].append(c["name"])
            c["name"] = name
        if operation:
            c["operation"] = operation
        return cid

    def apply_same_as(self, a, b):
        """Merge two live clusters. Lower id survives, for determinism."""
        a, b = self.resolve_id(a), self.resolve_id(b)
        if a == b or a not in self.clusters or b not in self.clusters:
            return None
        keep, drop = sorted([a, b], key=lambda c: int(c[1:]))[0], \
            sorted([a, b], key=lambda c: int(c[1:]))[1]
        d = self.clusters.pop(drop)
        k = self.clusters[keep]
        k["members"].extend(d["members"])
        k["confidences"].extend(d["confidences"])
        for p in d["prompts"]:
            if p not in k["prompts"]:
                k["prompts"].append(p)
        for n in [d["name"]] + d["aliases"]:
            if n and n != k["name"] and n not in k["aliases"]:
                k["aliases"].append(n)
        self.merged[drop] = keep
        return keep

    def resolve_id(self, cid):
        seen = set()
        while cid in self.merged and cid not in seen:
            seen.add(cid)
            cid = self.merged[cid]
        return cid

    def format_for_prompt(self, rel_index, max_examples=2):
        if not self.clusters:
            return "(empty -- every relation below starts a new cluster)"
        parts = []
        for cid in sorted(self.clusters, key=lambda c: int(c[1:])):
            c = self.clusters[cid]
            p = ["%s  %s" % (cid, c["name"])]
            p.append("   operation: %s" % c["operation"])
            if c["aliases"]:
                p.append("   also named: %s" % "; ".join(c["aliases"][:4]))
            p.append("   %d relation(s) across %d sentence(s)"
                     % (len(c["members"]), len(c["prompts"])))
            #: Illustration, and labelled as such. Across sentences the words are
            #: the variable; see the module docstring for the measurement.
            for rid in c["members"][:max_examples]:
                r = rel_index.get(rid)
                if r:
                    p.append("   e.g.  A: %s" % ", ".join(r["a_words"][:9]))
                    p.append("         B: %s" % ", ".join(r["b_words"][:9]))
            parts.append("\n".join(p))
        return "\n\n".join(parts)

    def all_as_list(self):
        return [deepcopy(self.clusters[c])
                for c in sorted(self.clusters, key=lambda c: int(c[1:]))]


# ── System prompt ───────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are building a vocabulary of the KINDS OF CHANGE that occur between two \
conditions in the completions of a sentence.

Each item you are shown is one observation: for a single sentence, a set of \
words favoured under condition A and a set favoured under condition B, together \
with one person's description of what connects them. Different observations come \
from different sentences and from different sources; each was described by \
someone working alone who invented their own wording.

Your job for each observation is to say WHAT KIND OF CHANGE it is, and whether \
some cluster already in the register names that same kind of change.

WHAT TO COMPARE, AND WHAT TO IGNORE

Across different sentences the words are the variable and the operation is the \
invariant. Word lists will not match even when the operation is identical, and \
matching words are weak evidence rather than strong: two changes involving the \
same words can be different operations, and two involving no shared words at all \
can be the same one. The example words in the register are illustration. The \
operation statement is the thing to compare against.

The test for a placement: if you described both changes without naming any of \
the words, would the same description fit both?

WHEN YOU CANNOT TELL

Answer `new` and mark confidence low. Do not force an observation into the \
nearest cluster to be tidy, and do not keep it apart out of caution when you can \
state the shared operation. These fail in opposite directions and both are \
failures, but they are not equally recoverable: two clusters that should have \
been one stay visible and can be merged later, whereas a wrong merge destroys \
the evidence that there were ever two.

MERGING CLUSTERS THAT ARE ALREADY IN THE REGISTER

If the new observations show you that two clusters already in the register name \
one operation, say so in `same_as`. This is usually empty. Propose it only when \
you could not state a difference between them that another reader would \
reliably reproduce.

DIRECTION MATTERS

A change from explicit to innocuous and a change from innocuous to explicit are \
opposite operations even when they involve identical words. Check which side is \
which before placing an observation. A cluster whose members run in both \
directions is wrong.

Do not speculate about which condition is which, what produced them, or why. \
Describe what changed.
"""


# ── Input formatting ────────────────────────────────────────────────────

def format_relation(r, rid):
    """One observation as the judge sees it. No lineage, no arm labels."""
    return "\n".join([
        "RELATION %s" % rid,
        '   sentence: "%s"' % r["prompt"],
        "   A: %s" % ", ".join(r["a_words"]),
        "   B: %s" % ", ".join(r["b_words"]),
        "   described as: %s" % r["sentence"],
    ])


# ── Tasks ───────────────────────────────────────────────────────────────

class MergeRelationsTask(SequentialTask):
    """Fold relations into a register of operations, chunk by chunk.

    Set `rel_index` (rid -> relation dict) before running; the register needs it
    to render example words for clusters whose members came from earlier chunks.
    """

    name = 'merge_displacement_relations'
    system_prompt = SYSTEM_PROMPT
    schema = ChunkResult
    chunk_size = 10
    max_tokens = 8192
    temperature = 0.2
    retries = 2
    #: Bump when SYSTEM_PROMPT or format_context change materially; it folds into
    #: the per-chunk cache key so a stale generation is not served. A
    #: SequentialTask has no static instrument to hash -- the base class refuses
    #: instrument_sha256() rather than fabricate one -- so this is the version of
    #: record for this task.
    prompt_version = 'v1'

    rel_index = {}

    def build_state(self):
        return {"register": ConstructRegister(), "placements": [], "merges": []}

    def format_context(self, state):
        return ("CURRENT REGISTER OF OPERATIONS:\n\n"
                + state["register"].format_for_prompt(self.rel_index))

    def update_state(self, state, result, chunk_idx, start, end):
        state = deepcopy(state)
        reg = state["register"]
        for p in result.get("placements", []):
            rid = p.get("rid")
            r = self.rel_index.get(rid)
            if r is None:
                #: An id the chunk never carried. Recorded, never invented into a
                #: cluster: a fabricated member would be unauditable downstream.
                state["placements"].append({"rid": rid, "cid": None,
                                            "error": "unknown rid"})
                continue
            tgt = str(p.get("cluster", "new")).strip()
            cid = None
            if tgt.lower() != "new":
                cid = reg.add_member(tgt, rid, r["prompt"], p.get("name"),
                                     p.get("operation"), p.get("confidence"))
            if cid is None:
                cid = reg.new(p.get("operation"), p.get("name") or "unnamed",
                              rid, r["prompt"], p.get("confidence"))
                if tgt.lower() != "new":
                    #: Named a cluster that does not exist. Treated as new and
                    #: flagged, because silently creating it would report a
                    #: judgement the reader did not make.
                    state["placements"].append({"rid": rid, "cid": cid,
                                                "error": "named missing %s" % tgt})
                    continue
            state["placements"].append({"rid": rid, "cid": cid,
                                        "confidence": p.get("confidence"),
                                        "chunk": chunk_idx})
        for m in result.get("same_as", []):
            kept = reg.apply_same_as(m.get("a", ""), m.get("b", ""))
            state["merges"].append({"a": m.get("a"), "b": m.get("b"),
                                    "kept": kept, "reason": m.get("reason"),
                                    "chunk": chunk_idx})
        return state

    def aggregate(self, all_results, state):
        reg = state["register"]
        return {
            "clusters": reg.all_as_list(),
            "placements": state["placements"],
            "merges": state["merges"],
            "n_clusters": len(reg.clusters),
            "n_relations": len(state["placements"]),
            "prompt_version": self.prompt_version,
        }


class MergeRelationsTaskReasonFirst(MergeRelationsTask):
    """Variant B. Identical but for field order within a placement."""
    name = 'merge_displacement_relations_b'
    schema = ChunkResultReasonFirst
    prompt_version = 'v1b'


#: Reassign after the field-ordering bake-off against discriminate.py's 20
#: known-answer triads. Variant A is decide-then-justify, which is the shape the
#: superseded accretion used and whose decisions read as post-hoc.
MergeTask = MergeRelationsTask
