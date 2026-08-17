#!/usr/bin/env python
"""run.py — how often the two dN conventions disagree, over all 50 pairs.

    python run.py --scope      # panel, cost, and the axis provenance
    python run.py --run        # the sweep -> results/dn_convention.json

dario measured **16.2%** sign disagreement between `dN` and `dN_renorm` on one
pair ([6375]). I showed that pair is the 9th most aperture-STABLE of 50, so 41
pairs have more room to diverge ([6376]). This is the rate itself.

## THE AXIS IS REUSED, NOT CHOSEN — AND THAT IS THE POINT

`LEXICAL_PAIRS` and `pooled_axis` are IMPORTED from the committed calibration,
never retyped. Two reasons, and the second matters more:

1. Two implementations of one definition is the defect this repo keeps paying
   for — two definitions of "root" in one file printed 47 against 54.
2. **The axis is PRE-SPECIFIED relative to this measurement.** It was committed
   at `cbd0ce5` (00:58), before any aperture or sign-disagreement result existed
   (`9eb760f`, 01:18), and `LEXICAL_PAIRS` is byte-identical across all three
   commits — verified by hashing the block at each. I declined to run this while
   I believed the axis was still open, precisely so I could not pick one after
   seeing that the aperture spread is large. It was never open; I had misread
   which calibration used the tagged items. **Agreeing an axis NOW would be the
   post-hoc choice; inheriting a pre-registered one is not.**

Its licence is its own ceiling, stated rather than re-litigated: pooled, it
reproduces the declared instrument at r = 0.740 against that instrument's own
split-half ceiling of r = 0.828 — about 89% of what tagging buys.

## POOLED vs PER-PAIR IS MOOT HERE, BY DESIGN

dario flagged ([6377] §3) that a 50-pair rate could be pooled over prompts or
averaged over pairs, and that these differ whenever pairs hold unequal prompt
counts — "the kind of choice that is invisible in the output". **Both are
emitted, and whether they coincide is MEASURED, not claimed.**

I nearly claimed they were identical by design. They are nearly identical: the
panel crosses at 1.0000 over its declared membership, but `falcon-mamba-7b-instruct`
holds 475 of 477 prompts, so one pair contributes marginally fewer rows. My first
version made that claim true by raising the coverage threshold until the offending
pair fell out of the sweep — **tidying the population to protect a statement about
the population.** The threshold is now 90%, the pair is in, and
`identical_by_design` reports what is actually the case.

## recurrentgemma IS COMPUTED AND REPORTED SEPARATELY

Its passage generations are 95.15%/79.33% word-repetition loops against a roster
median of 1.14% — a vLLM 0.27.1 Griffin fault, not a model property, and its twp
cells are ordinary. That is exactly the case where dropping it could discard real
signal, so it is neither silently included nor silently excluded: it is in the
per-pair table, out of the headline, and named in both.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CAL = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(CAL))
RESULTS = os.path.join(HERE, "results")
sys.path.insert(0, ROOT)

from malignment import ch                     # noqa: E402
from malignment.slot_axis import Axis         # noqa: E402


def _committed_axis():
    """`LEXICAL_PAIRS` and `pooled_axis` from the calibration that registered them.

    **Loaded BY PATH, not by name.** Every calibration folder holds a `run.py`,
    so `sys.path` + `from run import ...` resolves to whichever one imported
    first — and when this module is itself imported as `run` it resolves to
    ITSELF, which is how the first version failed. A reuse link that depends on
    import order is not reuse; it is a coincidence that has been holding.
    """
    import importlib.util
    p = os.path.join(CAL, "rank_vs_cardinal", "run.py")
    spec = importlib.util.spec_from_file_location("_rank_vs_cardinal_run", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.LEXICAL_PAIRS, mod.pooled_axis


LEXICAL_PAIRS, pooled_axis = _committed_axis()

MIN_MODELS = 400
FLAGGED = {"google/recurrentgemma-9b"}        # see the module docstring
MIN_VOCAB = 8

PANEL = """
WITH enp AS (
  SELECT c.prompt AS prompt FROM twp_cells c
  INNER JOIN (SELECT DISTINCT prompt FROM prompts WHERE language='en') p
    ON c.prompt = p.prompt
  GROUP BY c.prompt HAVING uniqExact(c.model) >= %d
)
""" % MIN_MODELS


def _L(s):
    return "'" + s.replace("\\", "\\\\").replace("'", "\\'") + "'"


def panel():
    prompts = [r["prompt"] for r in ch.query(PANEL + "SELECT prompt FROM enp",
                                             limit_bytes=None)]
    pairs = [(r["base"], r["endpoint"])
             for r in ch.query("SELECT base, endpoint FROM endpoints ORDER BY base")]
    #: **DO NOT DROP A PAIR TO KEEP THE PANEL TIDY.** The first threshold here
    #: was `>= n-1`, which excluded `falcon-mamba-7b-instruct` for holding 475 of
    #: 477 — two cells — and quietly reduced a 50-pair sweep to 49 so that the
    #: prompt counts would be uniform and the pooled/per-pair claim below could
    #: stay clean. That is shaping the population to protect a claim about the
    #: population. The per-prompt loop already skips a prompt an arm lacks, so
    #: the pair costs nothing to keep; what it costs is the tidy claim, which is
    #: now MEASURED (`identical_by_design`) rather than asserted.
    have = {r["model"] for r in ch.query(PANEL + """
        SELECT c.model AS model FROM twp_cells c INNER JOIN enp USING (prompt)
        GROUP BY model HAVING count() >= %d"""
        % int(0.9 * len(prompts)), limit_bytes=None)}
    dropped = [p for p in pairs if p[0] not in have or p[1] not in have]
    for p in dropped:
        print("  DROPPED (under 90%% of the panel): %s -> %s" % p)
    return prompts, [p for p in pairs if p[0] in have and p[1] in have]


def _bare_axis():
    """`split()` touches no instance state when `S` is supplied, so no embedding
    is needed to construct one. Asserted by use, not by reading."""
    return object.__new__(Axis)


def sweep(prompts, pairs, limit=None):
    ax = _bare_axis()
    models = sorted({m for p in pairs for m in p})
    inlist = ",".join(_L(m) for m in models)
    per_pair = {p: {"n": 0, "dis": 0, "rows": []} for p in pairs}
    for i, pr in enumerate(prompts if limit is None else prompts[:limit], 1):
        rows = ch.query(
            "SELECT model, word, p FROM twp_words WHERE prompt=%s AND model IN (%s)"
            % (_L(pr), inlist), limit_bytes=None)
        by = {}
        for r in rows:
            by.setdefault(r["model"], {})[r["word"]] = r["p"]
        #: ONE embedding pass per prompt over the union of every word any pair
        #: needs. Per-pair embedding would re-pay for words shared between pairs,
        #: which on this panel is most of them.
        vocab = sorted({w for m in by for w in by[m]})
        if len(vocab) < MIN_VOCAB:
            continue
        S, _u = pooled_axis(pr, LEXICAL_PAIRS, vocab)
        for b, a in pairs:
            base, post = by.get(b), by.get(a)
            if not base or not post:
                continue
            s = ax.split(base, post, S)
            d = per_pair[(b, a)]
            d["n"] += 1
            d["dis"] += bool(s["sign_disagree"])
            d["rows"].append({"prompt": pr, "dN": s["dN"],
                              "dN_renorm": s["dN_renorm"],
                              "sign_disagree": bool(s["sign_disagree"]),
                              "tb": s["base_scored_mass"], "tp": s["post_scored_mass"]})
        if i % 25 == 0:
            print("  %d/%d prompts" % (i, len(prompts)), flush=True)
    return per_pair


def report(per_pair):
    keep = {k: v for k, v in per_pair.items() if v["n"] and k[0] not in FLAGGED}
    flagged = {k: v for k, v in per_pair.items() if v["n"] and k[0] in FLAGGED}
    allrows = [r for v in keep.values() for r in v["rows"]]
    pooled = 100.0 * sum(r["sign_disagree"] for r in allrows) / max(len(allrows), 1)
    rates = [100.0 * v["dis"] / v["n"] for v in keep.values()]
    avg = sum(rates) / max(len(rates), 1)
    counts = {v["n"] for v in keep.values()}

    #: **THE QUARTILES ARE CUT PER PAIR, THEN AVERAGED. The first version cut
    #: them on the POOLED |dN| and that broke this producer's own governing
    #: ruling.** [6374] rule 3: cross-pair comparison of raw `dN` MAGNITUDE is
    #: not licensed, because `dN` carries a per-pair aperture factor. Sorting all
    #: 23,272 rows by `|dN|` IS that comparison, so the "largest quartile" was
    #: partly a highest-aperture bucket rather than a largest-effect one -- and
    #: that bucket carries the reassuring half of the headline, the number a seat
    #: actually acts on. Caught by dario at [6379], applying my own rule to my
    #: own artifact.
    #:
    #: Both are computed. The pooled pair is retained ONLY so the withdrawn
    #: figure stays checkable rather than disappearing.
    def _quartiles(rows):
        o = sorted(rows, key=lambda r: abs(r["dN"]))
        q = max(len(o) // 4, 1)
        return (100.0 * sum(r["sign_disagree"] for r in o[:q]) / q,
                100.0 * sum(r["sign_disagree"] for r in o[-q:]) / q)

    per = [_quartiles(v["rows"]) for v in keep.values() if len(v["rows"]) >= 8]
    lo = sum(x for x, _ in per) / len(per)
    hi = sum(y for _, y in per) / len(per)
    pooled_lo, pooled_hi = _quartiles(allrows)

    out = {"pooled_pct": pooled, "per_pair_mean_pct": avg,
           "n_pairs": len(keep), "n_prompt_rows": len(allrows),
           "prompt_counts_per_pair": sorted(counts),
           "identical_by_design": len(counts) == 1,
           "smallest_dN_quartile_pct": lo, "largest_dN_quartile_pct": hi,
           "quartiles_cut": "per-pair, then averaged",
           #: Kept so the withdrawn figure remains checkable. NOT to be quoted:
           #: a pooled cut on |dN| is the cross-pair magnitude comparison that
           #: [6374] rule 3 refuses.
           "WITHDRAWN_pooled_cut": {"smallest": pooled_lo, "largest": pooled_hi,
                                    "why": "cross-pair |dN| comparison, [6374] rule 3"},
           "per_pair": {"%s -> %s" % k: 100.0 * v["dis"] / v["n"]
                        for k, v in sorted(keep.items())},
           "flagged_excluded_from_headline": {
               "%s -> %s" % k: 100.0 * v["dis"] / v["n"] for k, v in flagged.items()},
           "axis": {"pairs": LEXICAL_PAIRS, "source": "generic_axis/run.py",
                    "prespecified_at": "cbd0ce5 (00:58), before 9eb760f (01:18)"}}
    print("\n  SIGN DISAGREEMENT between dN and dN_renorm")
    print("    pooled over prompts        %.1f%%" % pooled)
    print("    mean of per-pair rates     %.1f%%" % avg)
    print("    identical by design?       %s (prompt counts %s)"
          % (out["identical_by_design"], sorted(counts)))
    print("    smallest-|dN| quartile     %.1f%%  (cut PER PAIR, then averaged)" % lo)
    print("    largest-|dN|  quartile     %.1f%%" % hi)
    print("    [withdrawn pooled cut      %.1f%% / %.1f%% -- cross-pair |dN|, "
          "[6374] rule 3]" % (pooled_lo, pooled_hi))
    print("    pairs %d, prompt-rows %d" % (len(keep), len(allrows)))
    worst = sorted(out["per_pair"].items(), key=lambda kv: -kv[1])[:6]
    print("\n    worst pairs:")
    for k, v in worst:
        print("      %-56s %.1f%%" % (k.split(" -> ")[1][-56:], v))
    for k, v in out["flagged_excluded_from_headline"].items():
        print("\n    FLAGGED, not in the headline: %s  %.1f%%" % (k.split(" -> ")[1], v))
    os.makedirs(RESULTS, exist_ok=True)
    p = os.path.join(RESULTS, "dn_convention.json")
    json.dump(out, open(p, "w"), indent=1)
    #: **PER-PROMPT ROWS ARE PERSISTED.** The first version wrote aggregates
    #: only, so dario's question about how the quartiles were cut could not be
    #: answered without repeating a 50-minute sweep. An aggregate that cannot be
    #: re-cut is an answer to one question and a refusal of every other.
    import csv
    q = os.path.join(RESULTS, "per_prompt.csv")
    with open(q, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["base", "aligned", "prompt", "dN", "dN_renorm",
                    "sign_disagree", "base_scored_mass", "post_scored_mass"])
        for (b, a), v in sorted(per_pair.items()):
            for r in v["rows"]:
                w.writerow([b, a, r["prompt"], r["dN"], r["dN_renorm"],
                            int(r["sign_disagree"]), r["tb"], r["tp"]])
    print("\n  wrote %s\n  wrote %s" % (p, q))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scope", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--limit", type=int)
    a = ap.parse_args()
    prompts, pairs = panel()
    print("  panel: %d prompts x %d pairs" % (len(prompts), len(pairs)))
    print("  axis:  pooled %d-pair lexical, imported from generic_axis"
          % len(LEXICAL_PAIRS))
    if a.scope or not a.run:
        n = ch.scalar(PANEL + """
            SELECT uniqExact((w.prompt, w.word)) FROM twp_words w
            INNER JOIN enp USING (prompt) WHERE w.model IN (%s)"""
                      % ",".join(_L(m) for m in sorted({m for p in pairs for m in p})),
                      limit_bytes=None)
        print("  distinct (prompt, word) to embed: %s" % format(n, ","))
        print("\n  --run to sweep")
        return 0
    report(sweep(prompts, pairs, a.limit))
    return 0


if __name__ == "__main__":
    sys.exit(main())
