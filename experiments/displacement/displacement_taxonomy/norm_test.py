"""Do the cross-frame relations agree in CONTEXTUAL rating space? A held-out test.

    python norm_test.py                 # the test
    python norm_test.py --coverage      # what fraction of cited words are rated
    python norm_test.py --shifts        # per-relation shift table, no test

## WHAT IS BEING TESTED, AND WHY IT IS NOT CIRCULAR

Three blind raters grouped 89 per-frame components into cross-frame relations
using STATEMENTS AND WORDS. They never saw a rating. So asking whether the
components inside one relation move alike in rating space is a check on the
grouping by evidence the grouping never touched -- the same discipline as the
reversal check, and the reason grouping ON these scales was refused (RH): a
criterion you group by cannot then be the result you report.

## WHY CONTEXTUAL RATINGS AND NOT TYPE NORMS

Warriner and Brysbaert give a word ONE value whatever sentence it is in, so a
null there says only that concreteness cannot see the relation -- it disproves
nothing (RH, 2026-08-23). `slot_ratings` v6 rates each (prompt, word) pair IN
ITS FRAME, on twelve scales written for this phenomenon:

    harm  aggression  directedness  deliberation  interiority  superego
    vocalisation  hedged  makes_better  makes_worse  mundanity  fit

`vocalisation` is literally what `Blow becomes utterance` claims, and
`superego`, `hedged` and `deliberation` name what the procedure relations
claim. A null across these is informative about the taxonomy rather than about
the instrument, which is what makes the test worth running.

## THE STATISTIC

Per component, the shift on each scale is the mean rating of its cited TO words
minus the mean of its cited FROM words, over words that carry a rating in that
frame. Two components AGREE to the extent their 12-vectors point the same way,
measured by cosine, because what a relation claims is a DIRECTION of movement
and not a magnitude -- two frames can move the same way by different amounts.

    observed = mean cosine over pairs of components INSIDE one relation
    null     = the same, over relations reassembled at random with sizes held

Same-frame pairs are excluded from both. Components of one relation that come
from the same sentence share a vocabulary and would agree for a reason that has
nothing to do with the relation; that is the confound that made the earlier
reverser check collapse when the four identity prompts were counted as four
frames rather than one template.

## WHAT A RESULT MEANS

A positive result says the grouping predicts movement in a space the raters
never saw. A null says these twelve scales do not separate relations that three
raters called distinct -- which bears on the taxonomy, but is still a statement
about twelve scales and should be reported as one.
"""
import argparse
import collections
import glob
import itertools
import json
import math
import os
import random
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cross_frame as CF  # noqa: E402

V6 = "/Users/rj416/github/malignment/experiments/slot_ratings/results/v6full/*.json"
#: `ratable` is a gate the rater set, not a scale; `rise`/`fall`/`net` are
#: movement columns from a different measurement and must not enter the vector.
SCALES = ("harm", "aggression", "directedness", "deliberation", "interiority",
          "superego", "vocalisation", "hedged", "makes_better", "makes_worse",
          "mundanity", "fit")
K_BRIDGE = 3
RATERS = ("high", "xhigh", "medium")


def ratings():
    """`{prompt: {word: {scale: value}}}` from the v6 contextual run."""
    out = collections.defaultdict(dict)
    for f in glob.glob(V6):
        try:
            rows = json.load(open(f))
        except Exception:
            continue
        for r in rows if isinstance(rows, list) else []:
            p, w = r.get("prompt"), r.get("word")
            if not p or not w:
                continue
            vals = {s: r[s] for s in SCALES if isinstance(r.get(s), (int, float))}
            if vals:
                out[p][w.lower()] = vals
    return dict(out)


def shifts(M, R):
    """`{component_id: {scale: TO-mean minus FROM-mean}}`, plus its coverage.

    Unweighted over cited word TYPES. The rater's citation is already a
    selection -- it chose which words to name -- so weighting by mass would
    apply a second selection on top of one whose rule is not recorded.
    """
    out, cov = {}, {}
    for cid, c in M.items():
        rr = R.get(c["prompt"], {})
        fw, tw = set(), set()
        for _, o in c["_ops"]:
            for m in o.get("members") or []:
                fw |= {w.lower() for w in (m.get("a_words") or [])}
                tw |= {w.lower() for w in (m.get("b_words") or [])}
        f = [rr[w] for w in fw if w in rr]
        t = [rr[w] for w in tw if w in rr]
        cov[cid] = (len(f), len(fw), len(t), len(tw))
        if len(f) < 4 or len(t) < 4:
            continue
        out[cid] = {s: statistics.mean(x[s] for x in t if s in x)
                    - statistics.mean(x[s] for x in f if s in x)
                    for s in SCALES
                    if any(s in x for x in t) and any(s in x for x in f)}
    return out, cov


def cosine(a, b):
    ks = [s for s in SCALES if s in a and s in b]
    if not ks:
        return None
    na = math.sqrt(sum(a[s] ** 2 for s in ks))
    nb = math.sqrt(sum(b[s] ** 2 for s in ks))
    if na == 0 or nb == 0:
        return None
    return sum(a[s] * b[s] for s in ks) / (na * nb)


def relations(M):
    """Meta-relations at k>=3: `[(name, {component ids})]`, three raters present."""
    import networkx as nx
    G = {}
    for lab in RATERS:
        p = os.path.join(HERE, "results", "crossframe_groups_89_opus_%s.json" % lab)
        for g in json.load(open(p))["groups"]:
            G["%s:%s" % (lab, g["name"])] = set(g["members"])
    Q = nx.Graph()
    Q.add_nodes_from(G)
    for a, b in itertools.combinations(sorted(G), 2):
        if a.split(":")[0] != b.split(":")[0] and len(G[a] & G[b]) >= K_BRIDGE:
            Q.add_edge(a, b)
    out = []
    for c in nx.connected_components(Q):
        if len({x.split(":")[0] for x in c}) < len(RATERS):
            continue
        core = set.intersection(*[G[x] for x in c])
        if len(core) >= 2:
            out.append((sorted(x.split(":", 1)[1] for x in c)[0], core))
    return out


def test(iters=5000, seed=20260823):
    M = CF.as_read()
    R = ratings()
    S, cov = shifts(M, R)
    rels = relations(M)
    frame = {cid: M[cid]["prompt"] for cid in M}

    def pairs(groups):
        xs = []
        for _, core in groups:
            ms = [c for c in core if c in S]
            for a, b in itertools.combinations(ms, 2):
                if frame[a] == frame[b]:
                    continue
                v = cosine(S[a], S[b])
                if v is not None:
                    xs.append(v)
        return xs

    obs = pairs(rels)
    sizes = [len([c for c in core if c in S]) for _, core in rels]
    pool = sorted(S)
    rng = random.Random(seed)
    null = []
    for _ in range(iters):
        p = pool[:]
        rng.shuffle(p)
        k, fake = 0, []
        for n in sizes:
            fake.append(("x", set(p[k:k + n])))
            k += n
        xs = pairs(fake)
        null.append(statistics.mean(xs) if xs else 0.0)
    m = statistics.mean(obs) if obs else float("nan")
    pv = (sum(1 for x in null if x >= m) + 1.0) / (iters + 1.0)

    print("HELD-OUT TEST: do a relation's components move alike in v6 space?\n")
    print("  %d relations with a 3-rater core, %d components carrying a shift"
          % (len(rels), len(S)))
    nocov = [c for c in M if c not in S]
    print("  %d components dropped for coverage (<4 rated words a side)" % len(nocov))
    bad = sorted({frame[c] for c in nocov})
    for p in bad[:3]:
        print("      %s" % p[:66])
    print("\n  cross-frame pairs inside a relation: %d" % len(obs))
    print("  observed mean cosine  %+.3f" % m)
    print("  null (relations reassembled at random, sizes held)  %+.3f"
          % statistics.median(null))
    print("  95th percentile of null %+.3f" % sorted(null)[int(.95 * len(null))])
    print("  p = %.4f   %s" % (pv, "SUPPORTED" if pv < .05 else "NOT SUPPORTED"))
    return rels, S, obs, null, pv


def show_shifts():
    M = CF.as_read()
    S, _ = shifts(M, ratings())
    rels = relations(M)
    print("PER-RELATION MEAN SHIFT, v6 contextual scales (TO minus FROM)\n")
    hdr = "  %-34s %4s " % ("relation", "n") + " ".join("%5s" % s[:5] for s in SCALES)
    print(hdr)
    for name, core in sorted(rels, key=lambda r: -len(r[1])):
        ms = [c for c in core if c in S]
        if not ms:
            continue
        row = []
        for s in SCALES:
            v = [S[c][s] for c in ms if s in S[c]]
            row.append("%+5.2f" % statistics.mean(v) if v else "    -")
        print("  %-34s %4d " % (name[:34], len(ms)) + " ".join(row))


def coverage():
    M = CF.as_read()
    R = ratings()
    _, cov = shifts(M, R)
    f = sum(c[0] for c in cov.values())
    ft = sum(c[1] for c in cov.values())
    t = sum(c[2] for c in cov.values())
    tt = sum(c[3] for c in cov.values())
    print("v6 contextual coverage of cited word TYPES")
    print("  FROM %d of %d (%.0f%%)   TO %d of %d (%.0f%%)"
          % (f, ft, 100 * f / ft, t, tt, 100 * t / tt))
    print("  components with <4 rated words on a side: %d of %d"
          % (sum(1 for c in cov.values() if c[0] < 4 or c[2] < 4), len(cov)))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--coverage", action="store_true")
    ap.add_argument("--shifts", action="store_true")
    ap.add_argument("--iters", type=int, default=5000)
    a = ap.parse_args()
    if a.coverage:
        coverage()
    elif a.shifts:
        show_shifts()
    else:
        test(a.iters)


if __name__ == "__main__":
    main()
