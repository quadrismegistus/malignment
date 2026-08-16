
"""DOL — which stage carries the displacement, and does it depend on content?

    python experiments/division_of_labour/run.py            the registered run
    python experiments/division_of_labour/run.py --pilot    marked incomplete

Registration: `registration.md`, frozen 2026-08-16 before this file was written.
Reads it rather than restating it — the hypotheses live there, and a producer
that paraphrases its own registration is a second copy that can drift.

## WHAT THIS WRITES

    results/by_chain.csv          one row per chain          H1, H2
    results/by_chain_domain.csv   one row per chain x domain H3
    population.json               the exact ids used

**The grain is the row, never the mean.** Both files carry the per-chain values
so the summary can be re-derived and a disagreement can surface; `RESULTS.md`
states why, and this repository has twice found a defect only because the rows
underneath a summary existed to inspect.
"""
import argparse
import collections
import csv
import json
import os
import statistics
import sys
from math import comb, sqrt

HERE = os.path.dirname(os.path.abspath(__file__))


def _repo_root(start):
    """Walk up until `malignment/` is found, rather than counting directories.

    The first version did `dirname(dirname(HERE))` -- correct at
    experiments/<q>/, and broken the moment this moved to
    experiments/<subject>/<q>/. **A hardcoded depth encodes the layout in every
    file that uses it**, so the layout cannot change without breaking them all,
    which is a good way to make a layout permanent by accident.
    """
    d = start
    while d != os.path.dirname(d):
        if os.path.isdir(os.path.join(d, "malignment")):
            return d
        d = os.path.dirname(d)
    raise RuntimeError("no malignment/ package above %s" % start)


sys.path.insert(0, _repo_root(HERE))

from malignment import roster, ch                     # noqa: E402
from malignment.prompts import Prompts                # noqa: E402

#: THE CHAIN POPULATION LIVES IN malignment/roster.py, NOT HERE.
#: `lexical_domains` (L1-L3) must run on an identical chain set for its result to
#: be comparable to H3's -- which is its entire purpose. A retyped copy is how
#: `produce_movement.DERIVING` came to be missing five ops. Imported, never
#: duplicated.
from malignment.roster import chains, PREF                # noqa: E402,F401

#: FIXED IN THE REGISTRATION. `taboo` is NOT merged into `sexual`.
H3_DOMAINS = ("sexual", "violence")
MIN_PROMPTS_PER_DOMAIN = 20
MIN_CHAINS_FOR_H3 = 5


def _cells(pairs):
    """{(base, aligned): {prompt: js_total}} for the pairs we need, in one query."""
    want = {p for pr in pairs for p in pr}
    q = "','".join(m.replace("'", "\\'") for m in sorted(want))
    out = collections.defaultdict(dict)
    for r in ch.query("""SELECT base, aligned, prompt, js_total FROM {db}.movement_cells
                         WHERE base IN ('%s') AND aligned IN ('%s')""" % (q, q)):
        out[(r["base"], r["aligned"])][r["prompt"]] = r["js_total"]
    return out


def _sign_p(pos, n):
    if not n:
        return 1.0
    return min(1.0, 2 * sum(comb(n, k) for k in range(pos, n + 1)) / 2 ** n)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true",
                    help="the measurement queue has not drained; mark output INCOMPLETE")
    a = ap.parse_args()

    live = Prompts.all()
    dom = {}
    for p in live:
        dv = (p._row.get("domain") or "").strip()
        if dv:
            dom.setdefault(p.text, dv)
    cs = chains()
    cells = _cells([(c["base"], c["sft"]) for c in cs] + [(c["base"], c["pref"]) for c in cs])

    by_chain, by_dom = [], []
    for c in cs:
        A = cells.get((c["base"], c["sft"]) , {})
        B = cells.get((c["base"], c["pref"]), {})
        shared = set(A) & set(B)
        if not shared:
            continue
        #: THE SAME PROMPTS ON BOTH ARMS. Taking each arm's own mean would compare
        #: two populations -- the error that dropped 65% of amber's cells once.
        a_mean = statistics.mean(A[p] for p in shared)
        b_mean = statistics.mean(B[p] for p in shared)
        by_chain.append({"base": c["base"], "sft": c["sft"], "pref": c["pref"],
                         "pref_op": c["pref_op"], "n_prompts": len(shared),
                         "js_base_sft": round(a_mean, 6),
                         "js_base_pref": round(b_mean, 6),
                         "share": round(a_mean / b_mean, 6) if b_mean else ""})
        per = collections.defaultdict(list)
        for p in shared:
            dv = dom.get(p)
            if dv:
                per[dv].append((A[p], B[p]))
        for dv, vals in sorted(per.items()):
            am = statistics.mean(x for x, _ in vals)
            bm = statistics.mean(y for _, y in vals)
            by_dom.append({"base": c["base"], "pref": c["pref"], "domain": dv,
                           "n_prompts": len(vals),
                           "js_base_sft": round(am, 6), "js_base_pref": round(bm, 6),
                           "share": round(am / bm, 6) if bm else ""})

    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    for name, rows in (("by_chain", by_chain), ("by_chain_domain", by_dom)):
        path = os.path.join(HERE, "results", name + ".csv")
        with open(path, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]) if rows else ["empty"])
            w.writeheader()
            w.writerows(rows)
        print("  results/%s.csv  %d rows" % (name, len(rows)))

    pop = {"status": "PILOT — measurement queue not drained" if a.pilot else "registered run",
           "rule_version": 3, "dict_sha": __import__("malignment.twp", fromlist=["x"]).dict_sha(),
           "n_chains": len(by_chain), "n_distinct_bases": len({r["base"] for r in by_chain}),
           "chains": [{k: r[k] for k in ("base", "sft", "pref", "pref_op")} for r in by_chain],
           "prompts_live": len(live), "prompt_texts_unique": len({p.text for p in live}),
           "prompts_struck_excluded": len(Prompts.struck()),
           "domains_present": sorted({r["domain"] for r in by_dom})}
    with open(os.path.join(HERE, "population.json"), "w", encoding="utf-8") as fh:
        json.dump(pop, fh, indent=1, ensure_ascii=False)
    print("  population.json  %d chains, %d distinct bases"
          % (pop["n_chains"], pop["n_distinct_bases"]))

    # ---- the registered tests, reported but not interpreted here -------------
    sh = [r["share"] for r in by_chain if r["share"] != ""]
    if sh:
        pos = sum(1 for v in sh if v > 0.50)
        print("\n  H1  median share %.3f | %d/%d above 0.50 | sign p=%.4f"
              % (statistics.median(sh), pos, len(sh), _sign_p(pos, len(sh))))
        over = [r for r in by_chain if r["share"] != "" and r["share"] > 1.0]
        print("      shares > 1.0 (endpoint CLOSER to base than the sft rung): %d %s"
              % (len(over), [r["pref"].split("/")[-1][:24] for r in over]))
    olmo = [r for r in by_chain if r["base"] == "allenai/Olmo-3-1025-7B"]
    for r in olmo:
        print("  H2  %-34s share %.3f  (registered threshold 0.85)"
              % (r["pref"].split("/")[-1][:34], r["share"]))

    idx = collections.defaultdict(dict)
    for r in by_dom:
        idx[(r["base"], r["pref"])][r["domain"]] = r
    paired = []
    for k, v in idx.items():
        s, w = v.get(H3_DOMAINS[0]), v.get(H3_DOMAINS[1])
        if (s and w and s["n_prompts"] >= MIN_PROMPTS_PER_DOMAIN
                and w["n_prompts"] >= MIN_PROMPTS_PER_DOMAIN
                and s["share"] != "" and w["share"] != ""):
            paired.append((k, s["share"] - w["share"]))
    print("\n  H3  chains with >=%d live prompts in BOTH %s and %s: %d"
          % (MIN_PROMPTS_PER_DOMAIN, *H3_DOMAINS, len(paired)))
    if len(paired) < MIN_CHAINS_FOR_H3:
        print("      UNDERPOWERED by the registration (needs >=%d). NOT INTERPRETED."
              % MIN_CHAINS_FOR_H3)
    else:
        d = [x for _, x in paired]
        pos = sum(1 for x in d if x > 0)
        print("      CHAIN level  mean %+.4f | %d/%d positive | sign p=%.4f"
              % (statistics.mean(d), pos, len(d), _sign_p(pos, len(d))))

        # A2 DECLARES THIS TEST DECISIVE, AND UNTIL 2026-08-16 THE PRODUCER DID
        # NOT COMPUTE IT. The verdict "H3 NOT SUPPORTED" rested on p=0.077 -- a
        # number produced by hand, outside this file, reproducible only by
        # someone who already knew to collapse bases the way A2 describes. It was
        # RIGHT: recomputed here it is 0.0768. But a hypothesis whose verdict
        # comes from arithmetic the producer does not perform cannot be
        # re-derived by running the experiment, and the friendlier chain-level
        # number is the one the producer DID print. Chains sharing a base are not
        # independent -- 18 chains are 16 bases.
        per_base = collections.defaultdict(list)
        for (b, _p), x in paired:
            per_base[b].append(x)
        db = [statistics.mean(v) for v in per_base.values()]
        bpos = sum(1 for x in db if x > 0)
        bp = _sign_p(bpos, len(db))
        print("      BASE  level  mean %+.4f | %d/%d positive | sign p=%.4f   <- DECIDES (A2)"
              % (statistics.mean(db), bpos, len(db), bp))
        print("      VERDICT: H3 %s"
              % ("SUPPORTED" if bp < 0.05 and statistics.mean(db) > 0 else "NOT SUPPORTED"))
        print("      registration fixes the DIRECTION: positive supports, negative is a"
              "\n      SURPRISE to be reported as such, not as confirmation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
