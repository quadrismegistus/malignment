#!/usr/bin/env python
"""Producer for L1-L3: the division of labour, measured on WORDS not prompts.

    run.py --push     materialise the frozen lexicon as {db}.wf_sexviolence
    run.py            compute L1, L2, L3 and write results/

## WHAT IS HERE AND WHAT IS NOT

Almost nothing is here. The per-word JS term, the same-prompts-on-both-arms
intersection, the base-level collapse and the conservation check against
`movement_cells` all live in `malignment/wordfield.py`, because
`experiments/register_shift/` needs the identical machinery with a different
label column, and every fields.py source (RID, GI, USAS, k-ratings, Warriner,
Brysbaert) needs it again after that. **The question is always the same shape:
label the words, join to movement, aggregate per cell, compare the two arms.**
An earlier draft of this file had it all inline and would have been copied within
the hour -- which is how `produce_movement.DERIVING` became a retyped copy
missing five ops, leaving the Falcon3 upscale and prune edges out of movement
entirely.

What IS here: the registered population, the registered thresholds, and the
verdict. Those are properties of the question, not of the machinery.

## THE UNIT

**Base level decides, and it is computed by this producer from the first run.**
`sft_share` declared exactly this in amendment A2 and did not implement it, so
H3's verdict rested on a p-value computed by hand while the file printed the
friendlier chain-level number. See A4.
"""
import argparse
import collections
import csv
import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def _repo_root(start):
    d = start
    while d != os.path.dirname(d):
        if os.path.isdir(os.path.join(d, "malignment")):
            return d
        d = os.path.dirname(d)
    raise RuntimeError("no malignment/ above %s" % start)


ROOT = _repo_root(HERE)
sys.path.insert(0, ROOT)

from malignment import ch, roster                              # noqa: E402
from malignment.prompts import Prompts                         # noqa: E402
from malignment.wordfield import (WordField, measure, share,    # noqa: E402
                                  paired_test, conservation)

LEXICON = os.path.join(ROOT, "experiments", "sex_violence_lexicon",
                       "results", "lexicon.json")
#: registration rule 4: a result computed against an unrecorded instrument
#: version is not a result. Checked on every run, never assumed.
LEXICON_SHA = "d542e7e2bb86bd00"
FIELD = "sexviolence"
CATS = ("sexual", "violent")
MIN_WORDS_PER_CAT = 20
MIN_CHAINS = 5


def field():
    return WordField.from_lexicon(FIELD, LEXICON, key="category")


def panel():
    """The prompts held by EVERY model in the pairs population.

    Not "all prompts". Prompt sets are fleet-defined and do not nest: the
    universal intersection over all 402 measured models is ONE prompt, over the
    154 in `pairs` it is 2,190. Balancing is not composition-neutral -- it keeps
    100% of taboo and 42% of neutral -- so retention is reported, not assumed.
    """
    n = ch.scalar("""SELECT count(DISTINCT m) FROM (
        SELECT base AS m FROM {db}.pairs UNION DISTINCT SELECT aligned FROM {db}.pairs)""")
    rows = ch.query("""SELECT prompt FROM {db}.twp_words
        WHERE model IN (SELECT base FROM {db}.pairs UNION DISTINCT SELECT aligned FROM {db}.pairs)
        GROUP BY prompt HAVING count(DISTINCT model) = %d""" % n)
    return n, [r["prompt"] for r in rows]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--push", action="store_true", help="materialise the lexicon field")
    a = ap.parse_args()

    f = field()
    if a.push:
        n = f.push()
        print("  pushed %d words to {db}.%s" % (n, f.table))
        return 0
    f.check_sha(LEXICON_SHA)

    cs = roster.chains()
    n_models, prompts = panel()
    print("  panel   %d prompts crossed over %d models" % (len(prompts), n_models))
    print("  chains  %d over %d distinct bases" % (len(cs), len({c["base"] for c in cs})))

    pairs = [(c["base"], c["sft"]) for c in cs] + [(c["base"], c["pref"]) for c in cs]
    con = conservation(pairs[0], prompts)
    if con:
        print("  conservation vs movement_cells: %d prompts, worst |diff| %.2e" % con)
    cells = measure(pairs, f, prompts=prompts)
    print("  cells   %d (base, aligned, prompt, category)" % len(cells))

    rows = share(cells, cs, labels=CATS, min_words=MIN_WORDS_PER_CAT)

    # ---- L2: the same contrast stratified by PROMPT domain -------------------
    dom = {}
    for p in Prompts.all():
        dv = (p._row.get("domain") or "").strip()
        if dv:
            dom.setdefault(p.text, dv)
    by_dom = []
    for c in cs:
        for cat in CATS:
            per = collections.defaultdict(list)
            for (b, al, pr, k), v in cells.items():
                if b != c["base"] or k != cat or pr not in dom:
                    continue
                if al == c["sft"]:
                    per[dom[pr]].append(("sft", pr, v["js"]))
                elif al == c["pref"]:
                    per[dom[pr]].append(("pref", pr, v["js"]))
            for dv, vals in per.items():
                A = {pr: j for tag, pr, j in vals if tag == "sft"}
                B = {pr: j for tag, pr, j in vals if tag == "pref"}
                sh = set(A) & set(B)
                if not sh:
                    continue
                am = statistics.mean(A[p] for p in sh)
                bm = statistics.mean(B[p] for p in sh)
                by_dom.append({"base": c["base"], "pref": c["pref"], "prompt_domain": dv,
                               "word_category": cat, "n_prompts": len(sh),
                               "js_sft": round(am, 8), "js_pref": round(bm, 8),
                               "share": round(am / bm, 6) if bm else ""})

    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    for name, rs in (("by_chain", rows), ("by_chain_domain_category", by_dom)):
        with open(os.path.join(HERE, "results", name + ".csv"), "w", newline="",
                  encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rs[0]) if rs else ["empty"])
            w.writeheader()
            w.writerows(rs)
        print("  results/%s.csv  %d rows" % (name, len(rs)))

    with open(os.path.join(HERE, "population.json"), "w", encoding="utf-8") as fh:
        json.dump({"lexicon_sha": LEXICON_SHA, "field": FIELD,
                   "panel_prompts": len(prompts), "panel_models": n_models,
                   "n_chains": len(rows),
                   "n_distinct_bases": len({r["base"] for r in rows}),
                   "chains": [{k: r[k] for k in ("base", "sft", "pref", "pref_op")}
                              for r in rows],
                   "categories": list(CATS),
                   "min_words_per_category": MIN_WORDS_PER_CAT},
                  fh, indent=1, ensure_ascii=False)

    # ---- L1 -------------------------------------------------------------------
    t = paired_test(rows, CATS[0], CATS[1])
    print("\n  L1  chains qualifying: %d over %d bases"
          % (t["n_chains"], t["n_bases"]) if t else "\n  L1  no qualifying chains")
    if not t or t["n_chains"] < MIN_CHAINS:
        print("      UNDERPOWERED by the registration (needs >=%d). NO p-value quoted."
              % MIN_CHAINS)
        return 0
    print("      CHAIN level  mean %+.4f | %d/%d positive | sign p=%.4f"
          % (t["chain_mean"], t["chain_pos"], t["chain_n"], t["chain_p"]))
    print("      BASE  level  mean %+.4f | %d/%d positive | sign p=%.4f   <- DECIDES"
          % (t["base_mean"], t["base_pos"], t["base_n"], t["base_p"]))
    if t["ties_dropped"]:
        print("      ties dropped (campaign rule, never split): %d" % t["ties_dropped"])
    supported = t["base_p"] < 0.05 and t["base_mean"] > 0
    print("      VERDICT: L1 %s" % ("SUPPORTED" if supported else "NOT SUPPORTED"))
    if not supported:
        print("      Registration stopping rule: a second null WITHDRAWS the claim")
        print('      "SFT handles sex, DPO handles violence". No third instrument.')
    return 0


if __name__ == "__main__":
    sys.exit(main())
