"""The org / lab / country census of the 50 endpoint bases. -> docs/model_census.md

    python -u scripts/model_census.py            print the census
    python -u scripts/model_census.py --write    regenerate docs/model_census.md
    python -u scripts/model_census.py --check    fail if the mapping is stale

## WHY THIS FILE EXISTS AT ALL

**The country of a model has been worked out by hand at least four times and has
never survived**, because each answer went into a transcript or a docket post and
not into a file. RH, 2026-09-08: *"we've asked agents to identify country like 3
times so far, do we need to do it again."*

The reason it never finished is a GRAIN MISMATCH. `roster/models/models.yaml`
carries `country` on the NODE — 160 entries to fill by hand, 43 ever filled —
when the fact is a property of the ORG, of which there are 46 (34 with bases).
A 160-row chore nobody completes; a 46-row one that can be checked for
completeness. `--check` is that completeness gate, so an unfilled org now fails
loudly instead of sitting at 27% for a month.

## THE MAPPING IS AUTHORED, AND THREE ENTRIES ARE RULINGS NOT LOOKUPS

Country is a lookup for 31 of 34 orgs. Three are judgement calls, and they are
RH's, made 2026-09-08:

    LLM360      ["US", "AE"]      Petuum (Pittsburgh) and MBZUAI (Abu Dhabi)
                                  jointly. Multiple countries permitted.
    RWKV        ["none"]          a community project with no national home.
                                  `none` is a VALUE, not a missing field.
    bigscience  ["FR", "none"]    a multinational workshop, HF-led, trained on
                                  French public infrastructure (Jean Zay).
                                  France by compute, stateless by membership.

**`none` is not null.** An org with no country recorded is a defect this file
refuses; an org whose country is `none` is a decided fact about a stateless
producer. Anything counting countries must exclude `none` or say that it did not.

## TWO ORGS ARE MIRRORS, WHICH IS WHY "34 LABS" WAS WRONG

    huggyllama   re-upload of Meta's LLaMA-1 weights
    gl198976     mirror of MosaicML's MPT; the mosaicml repo is gone

Meta is separately present as `meta-llama`, so it collapses; MosaicML is a real
lab that appears ONLY under a personal account. **34 HuggingFace orgs, 33 labs.**

`provenance_notes.org_renames` in models.yaml records `THUDM -> zai-org`, so org
strings are not stable identities over time either; this file keys on the org as
the roster names it TODAY.

## WHAT THIS FILE DOES NOT SETTLE

**Architecture.** `model_type` from the configs gives **17 distinct** over the 50
bases (llama 19, gpt_neox 3, qwen2 2, qwen3 2, then singletons), with 11
unreadable without `trust_remote_code`. Any coarser count — dense / MoE /
SSM-hybrid / RNN would be four — is a taxonomy nobody has authored, and it is not
invented here.
"""
import argparse, collections, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, ROOT)
DOC = os.path.join(ROOT, "docs", "model_census.md")

#: **THE MAPPING LIVES IN `roster/models/models.yaml` UNDER `orgs:`, NOT HERE.**
#: An earlier draft of this file carried its own copy, which would have been a
#: second authored source for one fact -- the defect that produced the problem
#: it exists to fix. This reads the roster.
ORGS_PATH = os.path.join(ROOT, "roster", "models", "models.yaml")


def orgs_block():
    """-> {org: (lab, [country])} from the roster's authored `orgs:` block."""
    import yaml
    d = yaml.safe_load(open(ORGS_PATH))
    if "orgs" not in d:
        raise SystemExit("roster has no `orgs:` block -- see %s" % ORGS_PATH)
    return {o: (v.get("lab", "unknown"), list(v.get("country", ["unknown"])))
            for o, v in d["orgs"].items()}


MIRRORS = {
    "huggyllama": "re-upload of Meta's LLaMA-1 weights",
    "gl198976":   "mirror of MosaicML's MPT; the mosaicml repo is gone",
}


def census():
    from malignment import roster
    ORGS = orgs_block()
    eps, unresolved = roster.endpoints()
    bases = sorted(eps)
    orgs = sorted({b.split("/")[0] for b in bases})
    #: a base-bearing org that is absent OR `unknown` is the defect this gate
    #: exists for; an aligned-only org may be unknown, nothing rests on it
    missing = [o for o in orgs
               if o not in ORGS or "unknown" in ORGS[o][1]]
    labs = sorted({ORGS[o][0] for o in orgs if o in ORGS})
    cc = collections.Counter()
    for o in orgs:
        for c in ORGS.get(o, ("", []))[1]:
            cc[c] += 1
    real = sorted(c for c in cc if c != "none")
    return dict(bases=bases, orgs=orgs, missing=missing, labs=labs,
                countries=real, counter=cc, unresolved=unresolved, ORGS=ORGS)


def render(z):
    ORGS = z["ORGS"]
    L = []
    a = L.append
    a("# The model census — 50 families, 34 orgs, %d labs, %d countries"
      % (len(z["labs"]), len(z["countries"])))
    a("")
    a("**Generated by `scripts/model_census.py`. Do not hand-edit — the mapping")
    a("lives in that file and this is its output.** The org→country mapping is")
    a("AUTHORED; three entries are RH's rulings rather than lookups (LLM360,")
    a("RWKV, bigscience) and the producer's docstring states them.")
    a("")
    a("## THE NUMBERS, AS DERIVED")
    a("")
    a("    model families (endpoint bases)   %d" % len(z["bases"]))
    a("    HuggingFace orgs                  %d" % len(z["orgs"]))
    a("    LABS                              %d   two orgs are mirrors" % len(z["labs"]))
    a("    countries                         %d   plus `none` on %d orgs"
      % (len(z["countries"]), z["counter"]["none"]))
    a("")
    a("**Write 33 labs, not 34.** `huggyllama` re-uploads Meta's LLaMA-1 and Meta")
    a("is separately present as `meta-llama`; `gl198976` mirrors MosaicML's MPT,")
    a("whose own repo is gone. 34 is the count of org strings.")
    a("")
    a("**Write 10 countries, not 11**, unless `none` is being counted as an")
    a("eleventh value — which it is not, it is a decided fact about two stateless")
    a("producers (RWKV, and BigScience's membership half).")
    a("")
    a("## BY COUNTRY")
    a("")
    a("    %-6s %3s  %s" % ("code", "n", "orgs"))
    for c, n in sorted(z["counter"].items(), key=lambda x: (-x[1], x[0])):
        who = ", ".join(o for o in z["orgs"] if c in ORGS[o][1])
        a("    %-6s %3d  %s" % (c, n, who))
    a("")
    a("`LLM360` appears under both US and AE, and `bigscience` under both FR and")
    a("`none`, so the column sums to more than 34 by design.")
    a("")
    a("## THE FULL MAPPING")
    a("")
    a("    %-24s %-34s %s" % ("org", "lab", "country"))
    for o in z["orgs"]:
        lab, cs = ORGS[o]
        note = "   <- MIRROR" if o in MIRRORS else ""
        a("    %-24s %-34s %s%s" % (o, lab, ",".join(cs), note))
    a("")
    a("## WHAT THIS DOES NOT SETTLE")
    a("")
    a("**Architecture.** `model_type` over the 50 bases gives **17 distinct**")
    a("(llama 19, gpt_neox 3, qwen2 2, qwen3 2, then singletons), and 11 configs")
    a("need `trust_remote_code` to read at all. A four-way taxonomy — dense / MoE")
    a("/ SSM-hybrid / RNN — is defensible but nobody has authored it, so **do not")
    a("write \"four architectures\" until it exists**; it is not derivable today.")
    a("")
    a("## WHY THIS FILE EXISTS")
    a("")
    a("The country of a model had been worked out by hand at least four times and")
    a("never survived, because each answer went into a transcript rather than a")
    a("file. `models.yaml` carries `country` at NODE grain — 160 to fill, 43 ever")
    a("filled — when the fact belongs to the ORG. `--check` is the completeness")
    a("gate that node-grain never had.")
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    z = census()
    if z["missing"]:
        print("STALE: %d org(s) in the roster with no mapping: %s"
              % (len(z["missing"]), ", ".join(z["missing"])), file=sys.stderr)
        print("  a base-bearing org must have a lab and a non-`unknown` country",
              file=sys.stderr)
        if a.check:
            return 1
    elif a.check:
        print("ok: all %d orgs mapped, %d labs, %d countries"
              % (len(z["orgs"]), len(z["labs"]), len(z["countries"])))
        return 0
    out = render(z)
    if a.write:
        os.makedirs(os.path.dirname(DOC), exist_ok=True)
        open(DOC, "w").write(out)
        print("wrote %s" % DOC)
    else:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
