"""Produce `roster/models/attestations.json` -- the ATTESTED side of the roster.

    python -m malignment.attest --ingest <workflow-journal.jsonl> [...]
    python -m malignment.attest --report

## THE THIRD TRUST CLASS, AND WHY IT IS A SEPARATE FILE

    roster/models/models.yaml          AUTHORED   RH's rulings, hand-edited
    roster/models/measurements.json    OBSERVED   scripts reading files / the API
    roster/models/attestations.json    ATTESTED   an agent reading a card, quoted

These are three different things to believe and they fail differently. An
observation is wrong when the measurement is wrong. An attestation is wrong when
the SOURCE is wrong, or when the reader misread it, or -- the failure no schema
prevents -- when the quote was never on the page.

Writing them into one file would make the authored file unfalsifiable: a ruling
and a scraped sentence would become indistinguishable a month later, and there
would be no way to ask *which authored claims rest on an attestation that has
since been corrected*. So promotion from attested to authored stays a deliberate
act with a citation behind it.

## ONE QUOTE PER CLAIM, WHICH IS A LESSON NOT A PREFERENCE

The first pass gave each CHECKPOINT one `evidence` field while asking the reader
for four separate claims. It put the overflow in `notes`, and the audit read as a
fabrication: `dolphin-2.6-mistral-7b-dpo` came back `direction: inverted` beside
a quote about `ultrafeedback-binarized-preferences-cleaned`, a perfectly standard
preference set. The sentence that actually established the inversion -- *"I have
filtered the dataset to remove alignment and bias ... It will be highly compliant
to any requests, even unethical ones"* -- was three fields away in the notes.

Nothing was lost. It was UNAUDITABLE, which is the same thing one review later.
So a claim here is `{field, value, quote, url}` and the gate below is a
computation rather than something a reader has to eyeball.

## WHAT THE GATE CAN AND CANNOT SEE

It can see: a non-default value asserted with no quote. Measured on the 45-lineage
run, 2 of 905 claims -- both `unknown (no dataset named)`, a descriptive value
where the schema wanted a bare `unknown`. A formatting slip, caught.

It CANNOT see a fabricated quote, and no schema can. That is what spot-checking
against live pages is for, and it is not optional. On this corpus 4 of 4 sampled
quotes verified verbatim -- including Amber's `an7B` typo and OLMoE's exact
`step1200000-tokens5033B` string, which is the signature of a real read.

**One of those checks initially looked like a miss and was my error, worth
recording because the failure mode is symmetrical.** The Gemma-2 distillation
quote is not on the model card; I fetched the card, did not find it, and had a
fabrication on my hands for about a minute. The agent had cited
`arxiv.org/abs/2408.00118`, the technical report, where the sentence appears
verbatim. **Check the URL the claim cites, not the URL you expect it to cite** --
otherwise the audit invents the defect it was built to detect.

## INDEPENDENT PRETRAINING RUN != INDEPENDENT OBSERVATION

`root.independent` is a property of the MODEL: was it pretrained from scratch.
Whether a lineage inflates n is a property of the model AND THE POPULATION: does
its parent also sit in this roster.

The 45-lineage run returned four non-independent roots and they split evenly:

    phi-4-reasoning        <- phi-4                 parent IS in the roster -> n falls
    Falcon3-Mamba-7B-Base  <- falcon-mamba-7b       parent IS in the roster -> n falls
    Yi-1.5-9B              <- an unreleased Yi ckpt parent NOT here -> n unchanged
    gemma-2-9b             <- an unnamed Google teacher (distilled, not next-token
                              prediction) -> parent NOT here -> n unchanged

Yi-1.5 and gemma-2 are still each one observation of one pretraining process.
They are not fresh runs, and that is worth recording -- it constrains any future
roster that adds a Yi or a Gemma teacher -- but deleting them would discard real
data to fix a duplication that does not exist in this population.
"""
import argparse
import glob
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ATTESTED = os.path.join(ROOT, "roster", "models", "attestations.json")

DEFAULT_VALUES = ("unknown", "na", "")


def _blank():
    return {"schema": 1, "runs": [], "checkpoints": {}, "lineages": {},
            "not_found": {}}


def load():
    if not os.path.exists(ATTESTED):
        return _blank()
    with open(ATTESTED, encoding="utf-8") as fh:
        return json.load(fh)


def _results(path):
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if '"result"' not in line:
                continue
            try:
                r = json.loads(line).get("result")
            except ValueError:
                continue
            if isinstance(r, dict) and r.get("checkpoints"):
                out.append(r)
    return out


def _lineage_key(rec, declared):
    """The lineage id, recovered from the CHECKPOINT SET rather than the label.

    Readers put an essay in `lineage` often enough that the field cannot be a
    key: one returned 400 words of argument where a model id was asked for. The
    checkpoint set is unambiguous and the reader did not choose it -- we did.
    """
    ids = {c.get("model_id") for c in rec.get("checkpoints") or []}
    best, score = None, 0
    for lin, members in declared.items():
        n = len(ids & set(members))
        if n > score:
            best, score = lin, n
    return best


def _declared():
    from . import roster
    d = roster.load()
    par = {}
    for p, op, c in (d.get("edges") or []):
        if op in set(roster.DERIVING):
            par[c] = p

    def rt(m):
        seen = set()
        while m in par and m not in seen:
            seen.add(m)
            m = par[m]
        return m
    groups = {}
    for m in (d.get("nodes") or {}):
        groups.setdefault(rt(m), []).append(m)
    return groups


def ingest(paths):
    doc = load()
    declared = _declared()
    n_rec = n_claim = 0
    for path in paths:
        recs = _results(path)
        if not recs:
            print("  %s: no results" % os.path.basename(path))
            continue
        run = os.path.basename(os.path.dirname(path)) or os.path.basename(path)
        for rec in recs:
            lin = _lineage_key(rec, declared)
            n_rec += 1
            if lin:
                doc["lineages"][lin] = {
                    "root": rec.get("root") or {},
                    "lab": rec.get("lab") or {},
                    #: The reader's own prose, kept as a SUMMARY and never as a
                    #: key. It is often the most useful thing in the record and
                    #: the least structured.
                    "summary": rec.get("lineage") or "",
                    "run": run,
                }
            for nf in (rec.get("not_found") or []):
                doc["not_found"][nf[:120]] = {"detail": nf, "run": run}
            for c in rec.get("checkpoints") or []:
                mid = c.get("model_id")
                if not mid:
                    continue
                claims = []
                for cl in (c.get("claims") or []):
                    claims.append({"field": cl.get("field"),
                                   "value": cl.get("value"),
                                   "quote": cl.get("quote") or "",
                                   "url": cl.get("url") or ""})
                    n_claim += 1
                doc["checkpoints"][mid] = {
                    "lineage": lin, "url": c.get("url") or "",
                    "confidence": c.get("confidence") or "",
                    "notes": c.get("notes") or "",
                    "claims": claims, "run": run,
                }
        doc["runs"].append({"run": run, "path": path, "n_lineages": len(recs),
                            "ingested_at": time.strftime("%Y-%m-%dT%H:%M:%S")})
        print("  %s: %d lineages" % (run, len(recs)))
    with open(ATTESTED, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, ensure_ascii=False)
    print("\n  %d lineage records, %d claims -> %s"
          % (n_rec, n_claim, os.path.relpath(ATTESTED, ROOT)))
    return doc


def unsourced(doc, split=False):
    """Non-default values asserted with no quote. The computable half of trust.

    `split=True` separates TWO THINGS THIS USED TO CONFLATE, and the difference
    is the whole point of the gate. A claim with a URL and no quote has been
    sourced to a page and not to a sentence; a claim with NEITHER has been
    asserted. On 2026-08-16 an ingest took this count from 3 to 461, and 458 of
    the new ones were dataset NAMES -- where the evidence unit is the page that
    lists them, not a sentence about each. Reporting those as "unsourced"
    alongside a bare assertion would make the gate's number stop meaning
    anything, and quietly exempting the field would make it stop biting. So it
    counts both and says which.
    """
    no_quote, no_evidence = [], []
    for mid, c in doc["checkpoints"].items():
        for cl in c["claims"]:
            v = (cl.get("value") or "").strip()
            if not v or v in DEFAULT_VALUES or (cl.get("quote") or "").strip():
                continue
            (no_quote if (cl.get("url") or "").strip() else no_evidence).append(
                (mid, cl.get("field"), v))
    if split:
        return {"url_no_quote": no_quote, "no_evidence": no_evidence}
    return no_quote + no_evidence


def report(doc):
    cps, lins = doc["checkpoints"], doc["lineages"]
    n_claims = sum(len(c["claims"]) for c in cps.values())
    print("  %d lineages | %d checkpoints | %d claims" % (len(lins), len(cps), n_claims))
    uns = unsourced(doc)
    #: SPLIT, because "461 unsourced" and "2 asserted" are different facts and
    #: the first number stops meaning anything if they are pooled. A dataset NAME
    #: is evidenced by the page that lists it, not by a sentence about each one.
    sp = unsourced(doc, split=True)
    print("  sourced to a page but not a sentence: %d (%.1f%%)"
          % (len(sp["url_no_quote"]), 100.0 * len(sp["url_no_quote"]) / max(1, n_claims)))
    print("  NO EVIDENCE AT ALL: %d (%.2f%%)"
          % (len(sp["no_evidence"]), 100.0 * len(sp["no_evidence"]) / max(1, n_claims)))
    for mid, f, v in sp["no_evidence"][:6]:
        print("     %-46s %-14s %s" % (mid.split("/")[-1][:46], f, v[:44]))

    conf = {}
    for c in cps.values():
        conf[c["confidence"]] = conf.get(c["confidence"], 0) + 1
    print("  confidence: %s" % conf)

    #: The distinction that decides n, printed rather than left to a reader.
    print("\n  ROOTS ATTESTED NOT-INDEPENDENT:")
    declared = _declared()
    for lin, rec in sorted(lins.items()):
        r = rec.get("root") or {}
        if r.get("independent") != "no":
            continue
        frm = (r.get("derived_from") or "")
        in_roster = any(k in frm for k in declared) or any(
            m in frm for ms in declared.values() for m in ms)
        print("  - %-44s parent in roster: %s" % (lin[:44], "YES -> n falls" if in_roster else "no -> n unchanged"))
        print("      from : %s" % frm[:96])
    print("\n  not_found / gated: %d" % len(doc["not_found"]))
    return 0


def promote(doc):
    """PROPOSE edits to models.yaml. Never apply them.

    An attestation is evidence, not a decision. This prints what the cards say
    that the authored roster does not, each with the quote a reader would need to
    rule on it -- and stops. The archive is full of derived things stored beside
    their source and left to drift; the fix is not to automate the promotion, it
    is to make the promotion cheap to judge and impossible to do by accident.
    """
    from . import roster
    d = roster.load()
    declared_nodes = set(d.get("nodes") or {})
    edge_op = {}
    for p, op, c in (d.get("edges") or []):
        edge_op[c] = (p, op)

    # THREE BUCKETS, BECAUSE "PROPOSED" MUST MEAN "NOT ALREADY THERE".
    # This block used to print every attested non-independent root as a proposed
    # NEW edge without diffing against models.yaml -- so `phi-4 -sft-> phi-4-
    # reasoning` and `falcon-mamba-7b -continual-> Falcon3-Mamba-7B-Base`, both
    # long declared, were reported as findings and read as "n falls by 2". A
    # check that does not compare against the artifact it checks is not a check.
    new_edges, confirmed, conflicts = [], [], []
    for lin, rec in sorted(doc["lineages"].items()):
        r = rec.get("root") or {}
        if r.get("independent") != "no":
            continue
        frm = r.get("derived_from") or ""
        hit = [m for m in declared_nodes if m and m in frm]
        if not hit:
            continue
        parent = max(hit, key=len)
        cur = edge_op.get(lin)
        if cur is None:
            new_edges.append((lin, parent, r))
        elif cur[0] == parent:
            confirmed.append((lin, parent, cur[1]))
        else:
            conflicts.append((lin, parent, cur, r))

    print("  == PROPOSED NEW EDGES (a root the cards say is derived, parent in roster,")
    print("     AND no edge already declared)")
    for lin, parent, r in new_edges:
        print("\n  %s" % lin)
        print("     parent : %s" % parent)
        print("     quote  : %s" % (r.get("quote") or "")[:170].replace("\n", " "))
        print("     source : %s" % (r.get("url") or ""))
    if not new_edges:
        print("     (none)")

    if conflicts:
        print("\n  == PARENT DISAGREEMENTS (roster declares a DIFFERENT parent)")
        for lin, parent, cur, r in conflicts:
            print("  %-44s roster: %s (%s)  |  card: %s"
                  % (lin.split("/")[-1][:44], cur[0].split("/")[-1], cur[1],
                     parent.split("/")[-1]))

    if confirmed:
        print("\n  == ALREADY DECLARED, card agrees (no action): %d" % len(confirmed))
        for lin, parent, op in confirmed:
            print("     %-42s <-%s- %s" % (lin.split("/")[-1][:42], op,
                                           parent.split("/")[-1]))

    # STALENESS. An attestation describes the roster AS IT WAS when the agent
    # read the card. `SmolLM3-3B-checkpoints` was flagged as a disagreement by a
    # run ingested at 20:48 against edges declared at 21:47 the SAME EVENING --
    # a claim about a state that stopped existing an hour later.
    import subprocess
    newest = max((r.get("ingested_at") or "") for r in (doc.get("runs") or [{}]))
    try:
        mtime = subprocess.run(["git", "log", "-1", "--format=%aI", "--",
                                "roster/models/models.yaml"], capture_output=True,
                               text=True, cwd=os.path.dirname(os.path.dirname(
                                   os.path.abspath(__file__)))).stdout.strip()
    except Exception:                                        # noqa: BLE001
        mtime = ""
    if mtime and newest and mtime[:19] > newest[:19]:
        print("\n  !! models.yaml last changed %s; newest attestation %s."
              % (mtime[:19], newest[:19]))
        print("     Disagreements below may describe a roster state that no longer exists.")

    print("\n  == METHOD DISAGREEMENTS (roster edge op vs the card's own words)")
    n = 0
    #: Families of names for the same operation. A disagreement inside a family
    #: is a vocabulary difference; across families it is a claim about training.
    SAME = [{"instruct", "instruct_bundle"}, {"rlhf", "ppo", "rlvr", "grpo"},
            {"pretrain"}, {"distill"}, {"prune"}, {"upscale"}]

    def fam(x):
        for s in SAME:
            if x in s:
                return frozenset(s)
        return frozenset([x])
    for mid, c in sorted(doc["checkpoints"].items()):
        #: ALL method claims, not the first. A card and its paper are two
        #: sources and a checkpoint routinely carries both -- `neo_7b_instruct`
        #: has `method=instruct` (a one-line row in a card that is BYTE-IDENTICAL
        #: to its sibling's) and `method=dpo` (the paper, which names Iterative
        #: DPO with a reward model and a preference dataset). `next()` took the
        #: card and reported a disagreement the attestation itself resolved,
        #: against a roster ruling that had already been made, reversed, and
        #: remade on exactly this evidence. **If ANY claim agrees, there is no
        #: disagreement**; the roster needs only one source to be right.
        methods = [cl for cl in c["claims"] if cl.get("field") == "method"]
        if not methods or mid not in edge_op:
            continue
        parent0, op0 = edge_op[mid]
        if any(fam((cl.get("value") or "").strip().split()[0] if (cl.get("value") or "").strip() else "")
               == fam(op0) for cl in methods):
            continue
        got = methods[0]
        v = (got.get("value") or "").strip()
        parent, op = edge_op[mid]
        #: **A RELATING EDGE MAKES NO CLAIM ABOUT HOW THE CHILD WAS PRODUCED.**
        #: `scale` says two checkpoints are the same recipe at different sizes;
        #: `predecessor` says one generation came before another. Comparing
        #: either against a method turns every scale edge into a false
        #: disagreement -- Qwen2.5-7B "roster says scale, card says pretrain" is
        #: two compatible facts, and reporting it would bury the real ones.
        if op in roster.RELATING:
            continue
        if not v or v in DEFAULT_VALUES or fam(v) == fam(op):
            continue
        n += 1
        print("\n  %s" % mid)
        print("     roster says : %s  (from %s)" % (op, parent))
        print("     card says   : %s" % v)
        print("     quote       : %s" % (got.get("quote") or "")[:150].replace("\n", " "))
    if not n:
        print("     (none)")

    print("\n  == NOT INDEPENDENT, BUT PARENT NOT IN THIS ROSTER (annotate, do not delete)")
    for lin, rec in sorted(doc["lineages"].items()):
        r = rec.get("root") or {}
        if r.get("independent") != "no":
            continue
        if any(m and m in (r.get("derived_from") or "") for m in declared_nodes):
            continue
        print("  - %-42s <- %s" % (lin[:42], (r.get("derived_from") or "")[:70]))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ingest", nargs="*", default=None,
                    help="workflow journal.jsonl paths (globs ok)")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--promote", action="store_true",
                    help="print proposed models.yaml edits; applies nothing")
    a = ap.parse_args()
    if a.promote:
        return promote(load())
    if a.ingest is not None:
        paths = []
        for p in a.ingest:
            paths.extend(sorted(glob.glob(p)) or [p])
        doc = ingest(paths)
        print()
        return report(doc)
    return report(load())




def merge_claims(records, run, url_field="url"):
    """Add per-CHECKPOINT claims WITHOUT destroying what is already attested.

    **`ingest()` ASSIGNS `doc["checkpoints"][mid] = {...}` AND SO REPLACES THE
    WHOLE ENTRY.** That is right for the lineage-shaped run it was written for,
    where one pass produces every claim about a checkpoint. It is wrong for a
    TARGETED pass: ingesting a direction-only run through it would have dropped
    `method`, `datasets`, `train_tokens`, `license`, `released_base`,
    `reasoning` and `algorithm` for every checkpoint it touched, silently,
    because nothing counts claims before and after.

    **AND A REPEATED FIELD IS KEPT, NOT OVERWRITTEN.** `neo_7b_instruct_v0.1`
    carries `method=instruct` (a card row) and `method=dpo` (the paper), and the
    disagreement check has to see both -- reading only the first reported a
    conflict the attestation itself resolved. Two sources disagreeing is a fact
    about the sources; collapsing them is a decision, and not this function's.

    `records` are flat dicts with a `model` key. Returns (n_checkpoints,
    n_added, n_new_checkpoints).
    """
    doc = load()
    n_add = n_new = 0
    for rec in records:
        mid = rec.get("model")
        if not mid:
            continue
        entry = doc["checkpoints"].get(mid)
        if entry is None:
            entry = {"lineage": "", "url": rec.get(url_field) or "",
                     "confidence": "", "notes": "", "claims": [], "run": run}
            doc["checkpoints"][mid] = entry
            n_new += 1
        for cl in rec.get("_claims", []):
            entry["claims"].append({"field": cl["field"], "value": cl["value"],
                                    "quote": cl.get("quote") or "",
                                    "url": cl.get("url") or "", "run": run})
            n_add += 1
        if rec.get("note"):
            entry["notes"] = ((entry.get("notes") or "")
                              + ("\n\n[%s] " % run) + rec["note"]).strip()
    doc["runs"].append({"run": run, "path": "merge_claims",
                        "n_lineages": len(records),
                        "ingested_at": time.strftime("%Y-%m-%dT%H:%M:%S")})
    with open(ATTESTED, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, ensure_ascii=False)
    return len(records), n_add, n_new


if __name__ == "__main__":
    sys.exit(main())
