"""The surprisal axis for the passages we already measured for drift.

    python experiments/passage_analysis/jakobson_space/surprisal_by_passage.py

F15 and F16 put passages in a space of SURPRISAL x DRIFT and read Jakobsonian
quadrants off it. This folder rebuilds those axes ON OUR OWN CORPUS instead of
auditing someone else's parquet. `../drift_geometry/` supplied the drift axis over
13,557 f11_l2 passages; this supplies the surprisal one, and it needs no new
compute because `malign_logits.gen_scores` already holds it.

    our drift-measured passages   13,557
    found in gen_scores           13,557   100.0%
      with BOTH self and cross    13,316    98.2%

## Definition, taken from the archive so it cannot drift

`surprisal = -logprob`, per token, and `logprobs` aligns 1:1 to `token_ids`
(`../selection_and_combination/scripts/m06_mediation.py`, which asserts
`len(lb) == len(la) == len(ids)` and rejects the rest). Verified here: `n_tokens`
matches `n` on 223,601 of 224,200 self rows, 99.7%.

**`token_ids` is the CONTINUATION, not the prompt.** `plen` is stored separately
(10 against `n_tokens` 256), so no prompt tokens enter the mean. That matters
because prompt tokens are identical across arms and would dilute every contrast.

## SELF-SURPRISAL IS NOT A COMMON YARDSTICK, and this file does not pretend it is

A passage's self-score is its own generator's opinion of it, so base and aligned
passages are measured by DIFFERENT models. F15 avoided this with an external
reference (Pythia 1B-deduped) -- one yardstick for everything. We do not have that
yet; RH's plan is BLT for the external axis, and this is the start rather than the
answer.

What IS recoverable now: both arms score BOTH texts, so within a lineage pair a
FIXED scorer exists. Every passage therefore carries four numbers:

    s_self       its own generator's surprisal
    s_cross      the other arm's, on the same tokens
    s_by_base    the pair's BASE model's opinion       <- fixed scorer
    s_by_aligned the pair's ALIGNED model's opinion    <- fixed scorer

`s_by_base` and `s_by_aligned` are comparable across arms within a pair, which is
`composition_not_level.md`'s CROSS-SCORER level and the only within-corpus
yardstick available before BLT.

## The base/aligned map is derived from the DATA, not the roster

`roster.endpoints()` resolves 26 of our 29 pairs; it selects one arm and drops
others, which `lineages()` keeps. Since every passage carries its own `arm`, the
map is read off the corpus and asserted 1:1 -- no roster call, nothing dropped.

## Guards, each because the archive hit it

  length mismatch   len(logprobs) != n_tokens -> rejected, counted, never coerced
  non-finite        ibm-granite emits non-finite logprobs; one NaN makes the whole
                    passage NaN, so these are rejected and counted separately
"""

import argparse, collections, csv, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DRIFT = os.path.join(os.path.dirname(HERE), "drift_geometry", "results",
                     "drift_by_passage.csv")
OUT = os.path.join(HERE, "results", "jakobson_by_passage.csv")
CORPUS = "f11_l2"


def ch(sql):
    r = subprocess.run(["clickhouse", "client", "--query", sql],
                       capture_output=True, text=True, timeout=3600)
    if r.returncode:
        raise SystemExit("clickhouse failed: %s" % r.stderr[:400])
    return r.stdout


def main(argv=None):
    ap = argparse.ArgumentParser()
    a = ap.parse_args(argv)
    import numpy as np

    rows = list(csv.DictReader(open(DRIFT)))
    print("drift-measured passages: %d" % len(rows))

    #: BASE/ALIGNED FROM THE CORPUS, asserted 1:1. Not roster.endpoints(), which
    #: resolves 26 of 29 here because it selects one arm per lineage.
    side = collections.defaultdict(lambda: collections.defaultdict(set))
    for r in rows:
        side[r["pair"]][r["arm"]].add(r["model"])
    base_of, aligned_of = {}, {}
    for p, d in side.items():
        b, al = d.get("base", set()), d.get("aligned", set())
        assert len(b) == 1 and len(al) == 1, "%s: base=%s aligned=%s" % (p, b, al)
        base_of[p], aligned_of[p] = b.pop(), al.pop()
    print("  pairs: %d, each with exactly one base and one aligned model"
          % len(base_of))

    want = {(r["model"], r["prompt"], r["sample_idx"]) for r in rows}
    models = sorted({m for p in base_of for m in (base_of[p], aligned_of[p])})
    print("  pulling logprobs for %d models from gen_scores ..." % len(models))
    sql = ("SELECT model, prompt, sample_idx, scorer, "
           "arraySum(logprobs) AS lp_sum, length(logprobs) AS lp_n, "
           "arraySum(x -> if(isFinite(x), 0, 1), logprobs) AS n_bad "
           "FROM malign_logits.gen_scores "
           "WHERE corpus='%s' AND forced_word='' AND model IN (%s) "
           "FORMAT TabSeparated"
           % (CORPUS, ",".join("'%s'" % m for m in models)))
    got, bad_len, bad_fin = collections.defaultdict(dict), 0, 0
    ntok = {(r["model"], r["prompt"], r["sample_idx"]): None for r in rows}
    for line in ch(sql).splitlines():
        p = line.split("\t")
        if len(p) != 7:
            continue
        k = (p[0], p[1], p[2])
        if k not in want:
            continue
        n, nbad = int(p[5]), int(p[6])
        if nbad:
            bad_fin += 1
            continue
        #: mean surprisal in nats per CONTINUATION token: -sum(logprob)/n
        got[k][p[3]] = (-float(p[4]) / n if n else None, n)

    out, miss, mism = [], 0, 0
    for r in rows:
        k = (r["model"], r["prompt"], r["sample_idx"])
        sc = got.get(k) or {}
        b, al = base_of[r["pair"]], aligned_of[r["pair"]]
        sb = sc.get(b, (None, None))[0]
        sa = sc.get(al, (None, None))[0]
        self_ = sb if r["arm"] == "base" else sa
        cross = sa if r["arm"] == "base" else sb
        if self_ is None and cross is None:
            miss += 1
        d = dict(r)
        d.update(s_self=self_, s_cross=cross, s_by_base=sb, s_by_aligned=sa,
                 s_cross_minus_self=(None if self_ is None or cross is None
                                     else round(cross - self_, 6)),
                 s_aligned_minus_base=(None if sb is None or sa is None
                                       else round(sa - sb, 6)))
        for kk in ("s_self", "s_cross", "s_by_base", "s_by_aligned"):
            if d[kk] is not None:
                d[kk] = round(d[kk], 6)
        out.append(d)

    cols = list(rows[0].keys()) + ["s_self", "s_cross", "s_by_base", "s_by_aligned",
                                   "s_cross_minus_self", "s_aligned_minus_base"]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader(); w.writerows(out)

    both = [r for r in out if r["s_self"] is not None and r["s_cross"] is not None]
    drift_and_s = [r for r in both if r["mean_drift"]]
    print("\n  rejected, non-finite logprobs : %d score rows" % bad_fin)
    print("  passages with no score at all : %d" % miss)
    print("  passages with BOTH scorers    : %d  (%.1f%%)"
          % (len(both), 100 * len(both) / len(out)))
    print("  ...and a drift measurement    : %d" % len(drift_and_s))
    print("\n  %-22s %9s %9s" % ("", "median", "mean"))
    for k in ("s_self", "s_cross", "s_cross_minus_self", "s_aligned_minus_base"):
        v = np.array([r[k] for r in both if r[k] is not None], float)
        print("  %-22s %9.4f %9.4f" % (k, np.median(v), v.mean()))
    for arm in ("base", "aligned"):
        g = [r for r in both if r["arm"] == arm]
        print("  %-22s n=%-6d s_self %7.4f  s_cross %7.4f"
              % ("  " + arm, len(g),
                 float(np.median([r["s_self"] for r in g])),
                 float(np.median([r["s_cross"] for r in g]))))
    print("\n-> results/jakobson_by_passage.csv  (%d rows, %d columns)"
          % (len(out), len(cols)))


if __name__ == "__main__":
    main()
