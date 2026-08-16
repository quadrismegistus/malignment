"""The base-model population, derived. `roster/models/POPULATION.md` states the rule.

    python -m malignment.population            the list, and the checks
    python -m malignment.population --stamp    write the list into POPULATION.md

## WHY THIS IS A PRODUCER AND NOT A LIST IN A FILE

RH, 2026-08-16: *"I think we should freeze this model population at least for base
models -- a nice round 50 the project's results can reliably work from."*

A frozen list that nobody can regenerate is a number with no provenance; a rule
with no list is unverifiable. **So the file carries both and this asserts they
agree.** The archive's four artifacts -- `model_registry.json`,
`lineage_map_models.json`, `base_aligned_pairs.json`,
`lineage_representative_pairs.txt` -- gave six different answers to "how many
representative pairs" on one afternoon, because each was a list without a rule.

## THE THREE CONDITIONS, AND WHY EACH IS SEPARATE

    root          no incoming DERIVING edge
    corroborated  attested `method: pretrain`, or excluded by `pretrained: false`
    measured      has cells in twp_cells

They fail independently and for different reasons, so the count is reported per
condition rather than as one total. **A root is not necessarily a base**:
`microsoft/phi-4` sat in the base population for weeks because having no parent
edge was taken to mean having no parent, and its card says *"We align the
pretrained model with one round of SFT 4.1, one round of DPO"*.
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOC = os.path.join(ROOT, "roster", "models", "POPULATION.md")


def population():
    """(bases, diagnostics). The rule from POPULATION.md, executed."""
    from . import roster, ch
    d = roster.load()
    nodes = d.get("nodes") or {}
    edges = d.get("edges") or []
    par = {c for p, op, c in edges if op in roster.DERIVING}
    roots = [m for m in nodes if m not in par]
    not_base = [m for m in roots if nodes[m].get("pretrained") is False]
    cand = [m for m in roots if m not in not_base]
    have = {r["model"] for r in ch.query("SELECT DISTINCT model FROM {db}.twp_cells")}
    unmeasured = [m for m in cand if m not in have]
    bases = sorted(m for m in cand if m in have)

    path = os.path.join(ROOT, "roster", "models", "attestations.json")
    att = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            att = (json.load(fh).get("checkpoints") or {})
    #: NOT FRESH RUNS, and the distinction matters for the wording of any claim:
    #: an independent OBSERVATION here is not the same as an independent
    #: pretraining EVENT in the world.
    derived = []
    for m in bases:
        claims = (att.get(m) or {}).get("claims") or []
        meth = next((c.get("value") for c in claims if c.get("field") == "method"), None)
        if meth != "pretrain":
            derived.append((m, meth))
    lin = {}
    for lname, rec in (att.get("__lineages__") or {}).items():
        lin[lname] = rec
    return bases, {"roots": roots, "not_base": not_base,
                   "unmeasured": unmeasured, "no_pretrain_claim": derived}


def _not_fresh():
    """Bases attested as continuations/distillations of checkpoints not held here."""
    path = os.path.join(ROOT, "roster", "models", "attestations.json")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    out = []
    for lname, rec in (doc.get("lineages") or {}).items():
        r = rec.get("root") or {}
        if r.get("independent") == "no":
            out.append((lname, (r.get("derived_from") or "")[:60]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stamp", action="store_true",
                    help="write the derived list into POPULATION.md")
    a = ap.parse_args()
    bases, diag = population()
    from . import roster
    d = roster.load()
    nodes = d.get("nodes") or {}

    print("  BASE-MODEL POPULATION -- rule in roster/models/POPULATION.md\n")
    print("     graph roots                        %3d" % len(diag["roots"]))
    print("     minus roots that are NOT bases     %3d  %s"
          % (len(diag["not_base"]), [m.split("/")[-1][:26] for m in diag["not_base"]]))
    print("     minus bases with no cells          %3d  %s"
          % (len(diag["unmeasured"]), [m.split("/")[-1][:26] for m in diag["unmeasured"]]))
    print("     = BASE MODELS                      %3d" % len(bases))
    nf = _not_fresh()
    nf = [x for x in nf if x[0] in set(bases)]
    print("     of which NOT fresh pretraining     %3d  %s"
          % (len(nf), [m.split("/")[-1][:22] for m, _ in nf]))
    print("     = FRESH PRETRAINING RUNS           %3d" % (len(bases) - len(nf)))
    if diag["no_pretrain_claim"]:
        print("\n  WITHOUT an attested `method: pretrain` (the check roster.py reports):")
        for m, meth in diag["no_pretrain_claim"]:
            print("     %-48s method=%s" % (m, meth))
    print("\n  THE LIST (%d):" % len(bases))
    for i, m in enumerate(bases, 1):
        nick = (nodes.get(m) or {}).get("nickname") or ""
        print("  %3d  %-52s %s" % (i, m, nick))

    if a.stamp:
        with open(DOC, encoding="utf-8") as fh:
            doc = fh.read()
        block = ("\n<!-- GENERATED by `python -m malignment.population --stamp`. "
                 "Do not hand-edit. -->\n\n```\n"
                 + "\n".join("%3d  %s" % (i, m) for i, m in enumerate(bases, 1))
                 + "\n```\n")
        marker = "Re-run it against this file."
        i = doc.index(marker) + len(marker)
        doc = doc[:i] + " **If they disagree, the file is wrong** — the rule is the authority and the list is its receipt.\n" + block
        with open(DOC, "w", encoding="utf-8") as fh:
            fh.write(doc)
        print("\n  stamped %d ids into %s" % (len(bases), os.path.relpath(DOC, ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
