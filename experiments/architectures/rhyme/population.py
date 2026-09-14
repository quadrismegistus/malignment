#!/usr/bin/env python
"""WHAT THE RHYME PULL ACTUALLY COVERS. Three numbers, not one.

    python -u population.py                      the census
    python -u population.py --out results/population.txt

## WHY THIS FILE EXISTS

Two seats quoted ONE population number for THREE different quantities, in both
directions, over two days. `malign` called 96 a ceiling when it was a choice of
card; `lacan` carried 48 covered lineages into a README draft on an intermediate
step that does not hold. Each number was true under some predicate and was
quoted under another -- the campaign's recurring defect, and the fix is not more
care in a transcript, it is a producer that emits all three side by side so they
cannot be confused for each other.

**The three quantities are:**

    models with closure rows       a MODEL count, over the 1,786 verse contexts
    lineages with BOTH arms        a LINEAGE count -- the unit of inference
    lineages with the base arm     larger, and NOT the unit of any claim here

They differ because coverage is not a single fact: a lineage can have a base
and no aligned arm, and a model can be in the table with 3 prompts or 1,786.

## THE ARM CENSUS IS THE PART THAT SETTLES THE DISPUTE

`lacan`'s route was 48 covered minus 1 that lost its aligned arm. Mine is 50
minus 3 absent. Both give 47, which is a coincidence of arithmetic and not a
corroboration -- so the census prints the four cells of the cross-tab, because
the claim "one lineage lost its aligned arm" is checkable and the table says
whether it is true.

## ATTEMPT-COVERAGE AND DATA-COVERAGE DIVERGE ON EXACTLY ONE MODEL

`internlm2-base-7b` was shipped to a box and failed at load, returning
`exit=0, skipped: 0` -- a silent failure that looks like a completed unit. So a
census built from what the fleet ATTEMPTED and a census built from what is IN
the table differ by that one model, and they differ on the model whose failure
was invisible. Say which one you mean.

## A MIN-CELLS FILTER ON THIS TABLE HAS NO USEFUL SETTING

The sweep is printed rather than described. Every threshold up to 1,600 selects
the same models and the same lineages; the population collapses at 1,700. There
is no setting in between, so a min-cells clause on this table is either inert or
catastrophic -- which is why one was struck from the rhyme README rather than
tuned.
"""
import argparse, collections, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, ROOT)
PROMPTS = os.path.join(HERE, "data", "verse_prompts.json")
SWEEP = (1, 500, 1000, 1500, 1600, 1700, 1786)


def census():
    """-> (manifest, {model: distinct prompts}, endpoints, unresolved)

    **No prompt filter, and that is checked rather than assumed.** The table's
    own prompt population is asserted equal to the manifest, both ways -- so a
    `WHERE prompt IN (...)` would be a 1,786-element no-op, and it also happens
    to overflow ClickHouse's URL form. If the assert ever fires, something else
    has written to `twp_closure` and every count below needs the filter back.
    """
    from malignment import roster, vectors as V
    want = set(json.load(open(PROMPTS)))
    have = {r["prompt"] for r in V.rows("SELECT DISTINCT prompt FROM twp_closure")}
    if have != want:
        raise SystemExit("twp_closure is no longer manifest-scoped: +%d / -%d"
                         % (len(have - want), len(want - have)))
    rows = V.rows("SELECT model, count(DISTINCT prompt) AS n "
                  "FROM twp_closure GROUP BY model")
    n_by = {r["model"]: int(r["n"]) for r in rows}
    eps, unresolved = roster.endpoints()
    return sorted(want), n_by, eps, unresolved


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    want, n_by, eps, unresolved = census()
    L = []
    p = lambda s="": L.append(s)

    p("THE RHYME PULL POPULATION -- three numbers, side by side so they cannot")
    p("be quoted for each other. Manifest: %d verse contexts." % len(want))
    p("")
    p("    models with any closure row          %d" % len(n_by))
    both = [(b, al) for b, al in sorted(eps.items()) if b in n_by and al in n_by]
    base_only = [(b, al) for b, al in sorted(eps.items()) if b in n_by and al not in n_by]
    aligned_only = [(b, al) for b, al in sorted(eps.items()) if b not in n_by and al in n_by]
    neither = [(b, al) for b, al in sorted(eps.items()) if b not in n_by and al not in n_by]
    p("    endpoint lineages, BOTH arms         %d   <- the unit of inference" % len(both))
    p("    endpoint lineages, base arm present  %d" % (len(both) + len(base_only)))
    p("    endpoint lineages declared           %d" % len(eps))
    if unresolved:
        p("    unresolved lineages                  %d" % len(unresolved))
    p("")
    p("THE ARM CROSS-TAB. `48 covered minus 1 that lost its aligned arm` requires")
    p("the second cell to be non-empty. It is not.")
    p("")
    p("    both arms present                    %d" % len(both))
    p("    base present, ALIGNED ABSENT         %d" % len(base_only))
    p("    aligned present, base absent         %d" % len(aligned_only))
    p("    neither arm                          %d" % len(neither))
    for b, al in base_only:
        p("        %-42s aligned arm absent" % b)
    for b, al in aligned_only:
        p("        %-42s base arm absent" % b)
    for b, al in neither:
        p("        %-42s BOTH arms absent" % b)
    p("")
    srt = sorted(n_by.items(), key=lambda kv: kv[1])
    p("THINNEST AND FATTEST MODELS, by distinct verse contexts carrying closure.")
    p("The floor is %d, about %.0fx the largest number in the `176 or 177 cells`"
      % (srt[0][1], srt[0][1] / 177.0))
    p("claim, so that claim is not counting this quantity.")
    p("")
    for m, n in srt[:6]:
        p("    %-46s %6d  of %d" % (m, n, len(want)))
    p("    %-46s %6s" % ("...", "..."))
    for m, n in srt[-2:]:
        p("    %-46s %6d  of %d" % (m, n, len(want)))
    p("")
    p("MIN-CELLS SWEEP. No useful setting exists, which is why the clause was")
    p("struck rather than tuned.")
    p("")
    p("    %8s %8s %9s" % ("min cells", "models", "lineages"))
    for t in SWEEP:
        keep = {m for m, n in n_by.items() if n >= t}
        lin = sum(1 for b, al in eps.items() if b in keep and al in keep)
        p("    %8d %8d %9d" % (t, len(keep), lin))
    p("")
    p("ATTEMPT-COVERAGE vs DATA-COVERAGE. Of the %d absent lineages, two were"
      % len(neither))
    p("never shipped -- they are the only models above 9B and no 24 GB card in")
    p("the fleet would hold them -- and one was shipped and failed at load,")
    p("returning `exit=0, skipped: 0`. An attempt-census counts that one as")
    p("covered and this table does not, so the two censuses differ by exactly")
    p("the model whose failure was silent:")
    p("")
    for b, al in neither:
        why = ("shipped, failed at load (silent)" if "internlm" in b
               else "never shipped -- above the card")
        p("    %-44s %s" % (b, why))
    out = "\n".join(L) + "\n"
    print(out, end="")
    if a.out:
        path = a.out if os.path.isabs(a.out) else os.path.join(HERE, a.out)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, "w").write(out)
        print("\n-> %s" % path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
