"""How many of the 50 lineages independently pick the same substitution?

    python -u substitution_replicated.py
    python -u substitution_replicated.py --min-lineages 10 --lang en

## WHY THIS EXISTS AND WHAT `run.py` CANNOT DO

`run.py` averages the fifty lineages' probabilities and THEN picks a biggest
faller, so its unit is an averaged distribution and it has no per-lineage
faller at all. Every graph in this folder inherits that: an edge is one
prompt's averaged answer, and a pair supported by fifty models and a pair
supported by one look identical.

**AND NO ARITHMETIC OVER TWO DISTRIBUTIONS CAN ESTABLISH SUBSTITUTION.** A
distribution sums to one, so when one word falls another must rise;
conservation is true by definition. `absorb_1` is a ratio of aggregates rather
than a traced flow, and there is no counterfactual in this corpus. The
strictest within-prompt criterion (`graph.py --basis strict`) excludes every
rival reading available INSIDE a prompt and still cannot give the claim a
direction.

**REPLICATION IS THE EVIDENCE THAT CAN.** If fifty models trained by different
labs on different data independently take mass off `kill` and put it on
`scream` at the same slot, "scream replaces kill here" is a claim about the
alignment operation rather than about one averaged distribution. That is not
proof of a mechanism either -- it is agreement, not causation -- but it is the
strongest thing this corpus holds, and it is a DIFFERENT kind of evidence from
stacking more conditions onto one prompt.

## THE UNIT IS (LINEAGE, PROMPT) AND THE COUNT IS OVER LINEAGES

Per lineage, per prompt: the word that lost the most probability and the word
that gained the most. An edge is then a (faller, riser) pair and its weight is
**how many of the lineages that rated the prompt chose exactly that pair**.
`--min-lineages` is the replication floor.

Ties are dropped rather than broken: if two words lost identically the lineage
has no single biggest faller and voting for either would invent a preference.
"""
import argparse, collections, csv, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, ROOT)


CACHE = os.path.join(HERE, "results", "lineage_picks_%s.json")


def per_lineage(lang="en", rebuild=False):
    """-> {(prompt, faller, riser): set(lineage)} over the raw arm.

    Cached: the fifty ClickHouse scans take about two minutes and the
    significance test below is re-run far more often than the picks change.
    """
    cp = CACHE % lang
    if os.path.exists(cp) and not rebuild:
        d = json.load(open(cp))
        return ({tuple(k.split("\t")): set(v) for k, v in d["vote"].items()},
                set(d["prompts"]))
    v, pr = _scan(lang)
    json.dump({"vote": {"\t".join(k): sorted(s) for k, s in v.items()},
               "prompts": sorted(pr)}, open(cp, "w"))
    return v, pr


def _scan(lang="en"):
    """-> {(prompt, faller, riser): set(lineage)} over the raw arm."""
    from malignment import ch, charge, roster
    eps, _ = roster.endpoints()
    vote = collections.defaultdict(set)
    seen_prompts = set()
    for i, (b, a) in enumerate(sorted(eps.items()), 1):
        rows = ch.query(
            "SELECT prompt, word, (p_aligned - p_base) AS delta "
            "FROM {db}.movement_v4 "
            "WHERE base='%s' AND aligned='%s' AND frame_base='' "
            "AND frame_aligned=''"
            % (b.replace("'", "\\'"), a.replace("'", "\\'")),
            limit_bytes=None)
        by = collections.defaultdict(list)
        for r in rows:
            by[r["prompt"]].append((float(r["delta"]), r["word"]))
        for p, v in by.items():
            if lang != "both" and charge.language(p) != lang:
                continue
            if len(v) < 2:
                continue
            v.sort()
            #: **TIES ARE DROPPED, NOT BROKEN.** Two words losing identically
            #: means this lineage has no single biggest faller; picking one
            #: would manufacture a vote it did not cast.
            if v[0][0] == v[1][0] or v[-1][0] == v[-2][0]:
                continue
            if v[0][0] >= 0 or v[-1][0] <= 0:
                continue
            seen_prompts.add(p)
            vote[(p, v[0][1], v[-1][1])].add(b)
        print("  %2d/%d %-46s %d prompts"
              % (i, len(eps), b.split("/")[-1][:44], len(by)), flush=True)
    return vote, seen_prompts


def _drawable(vote):
    """-> predicate(prompt, faller, riser): could a graph in this folder draw it?

    Testing pairs no drawing would ever show inflates the family for nothing.
    Restricting it is a scope decision and it is made from the filters the
    graphs ALREADY apply -- content POS in the slot, no stopwords -- not from
    looking at which pairs did well.
    """
    import graph as G
    from malignment.pos import get_pos
    SW = G.stopwords_en()
    need = collections.defaultdict(set)
    by = collections.defaultdict(dict)
    for (p, f, t), v in vote.items():
        by[p][(f, t)] = len(v)
    for p, pairs in by.items():
        for (f, t), k in pairs.items():
            if k >= 2:
                need[p].update([f, t])
    tag = {}
    for p, ws in need.items():
        for w, x in get_pos(sorted(ws), p).items():
            tag[(p, w)] = x
    def ok(p, f, t):
        return (f not in SW and t not in SW
                and tag.get((p, f)) in G.CONTENT
                and tag.get((p, t)) in G.CONTENT)
    return ok


def agreement(vote, alpha=0.05, keep=None):
    """Which pairs do the lineages agree on MORE THAN THEIR TASTES PREDICT?

    -> [(prompt, faller, riser, k, n, expected, p, q)] passing BH at `alpha`

    **REPLICATION ALONE IS NOT EVIDENCE OF PAIRING.** If thirty lineages all
    lose `that` and all gain `of`, `that -> of` gets thirty votes without any
    lineage having paired them: the two marginals were already the popular
    choices and the pair is their product. The raw replication table is topped
    by exactly this -- `that -> of` 34, `hands -> hand` 29, `be -> focus` 28.

    So the null is MARGINAL-PRESERVING, the same null `kind_flow` uses. At one
    prompt, over the `n` lineages that made a clean pick, let `a_f` be how many
    chose faller `f` and `b_r` how many chose riser `r`. Under independence a
    lineage draws the pair with probability `(a_f / n) * (b_r / n)`, so the
    observed count is tested against `Binomial(n, p)` in the upper tail. An
    edge survives when the lineages agree on the PAIRING, not on its ends.

    Benjamini-Hochberg over every (prompt, pair) tested, which is the family of
    tests actually performed. `k >= 2` is required to be testable at all: one
    lineage is not agreement.
    """
    from math import comb
    byp = collections.defaultdict(dict)
    for (p, f, t), v in vote.items():
        byp[p][(f, t)] = len(v)
    tests = []
    for p, pairs in byp.items():
        n = sum(pairs.values())
        if n < 3:
            continue
        af, br = collections.Counter(), collections.Counter()
        for (f, t), k in pairs.items():
            af[f] += k
            br[t] += k
        for (f, t), k in pairs.items():
            if k < 2 or (keep and not keep(p, f, t)):
                continue
            q = (af[f] / n) * (br[t] / n)
            if q <= 0 or q >= 1:
                continue
            pv = sum(comb(n, i) * q ** i * (1 - q) ** (n - i)
                     for i in range(k, n + 1))
            tests.append((p, f, t, k, n, n * q, min(1.0, pv)))
    tests.sort(key=lambda r: r[6])
    m = len(tests)
    out, qmin = [], 1.0
    for i in range(m - 1, -1, -1):
        qv = min(qmin, tests[i][6] * m / (i + 1))
        qmin = qv
        if qv < alpha:
            out.append(tests[i] + (qv,))
    out.reverse()
    print("  %d (prompt, pair) tests; %d pass BH at %g" % (m, len(out), alpha))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--min-lineages", type=int, default=5)
    ap.add_argument("--lang", default="en", choices=("en", "zh", "both"))
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--rebuild", action="store_true")
    a = ap.parse_args(argv)

    vote, prompts = per_lineage(a.lang, a.rebuild)
    print("\n%d (prompt, faller, riser) triples over %d prompts"
          % (len(vote), len(prompts)))

    hist = collections.Counter(len(v) for v in vote.values())
    print("\n  lineages agreeing on the SAME pair at the same prompt:")
    tot = sum(hist.values())
    run = 0
    for k in sorted(hist, reverse=True):
        run += hist[k]
        if k >= 2 or k == 1:
            print("    %2d lineages  %5d triples   (%5.1f%% cumulative)"
                  % (k, hist[k], 100.0 * run / tot))
        if k == 1:
            break

    keep = {k: v for k, v in vote.items() if len(v) >= a.min_lineages}
    print("\n  at >= %d lineages: %d triples, %d distinct pairs"
          % (a.min_lineages, len(keep), len({(f, t) for _, f, t in keep})))
    E = collections.Counter()
    for (p, f, t), v in keep.items():
        E[(f, t)] = max(E[(f, t)], len(v))
    print("  most replicated pairs (best lineage count at any one prompt):")
    for (f, t), n in E.most_common(20):
        print("    %-16s -> %-16s %2d lineages" % (f, t, n))

    print("\n  AGREEMENT TEST (marginal-preserving null, BH)")
    print("  family = every (prompt, pair) with k >= 2:")
    sig_all = agreement(vote, a.alpha)
    print("  family = only the pairs a graph could DRAW "
          "(content POS, no stopwords):")
    sig = agreement(vote, a.alpha, _drawable(vote))
    E = collections.Counter()
    for p, f, t, k, n, e, pv, qv in sig:
        E[(f, t)] = max(E[(f, t)], k)
    print("  %d distinct pairs survive" % len(E))
    print("  top, by best lineage count at any one prompt:")
    for (f, t), k in E.most_common(20):
        print("    %-16s -> %-16s %2d lineages" % (f, t, k))
    sp = os.path.join(HERE, "results", "agreed_pairs_%s.json" % a.lang)
    json.dump({"alpha": a.alpha, "lang": a.lang, "null":
               "marginal-preserving binomial over lineages, BH corrected",
               "edges": [{"prompt": p, "faller": f, "riser": t, "k": k,
                          "n_lineages": n, "expected": round(e, 3),
                          "p": pv, "q": qv}
                         for p, f, t, k, n, e, pv, qv in sig]},
              open(sp, "w"), indent=1)
    print("  wrote %s" % sp)

    out = os.path.join(HERE, "results", "replicated_pairs_%s.json" % a.lang)
    json.dump({"min_lineages": a.min_lineages, "lang": a.lang,
               "n_prompts": len(prompts),
               "pairs": [{"prompt": p, "faller": f, "riser": t,
                          "lineages": sorted(v)}
                         for (p, f, t), v in sorted(
                             keep.items(), key=lambda kv: -len(kv[1]))]},
              open(out, "w"), indent=1)
    print("\n  wrote %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
