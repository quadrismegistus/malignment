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
SLOT = "/Users/rj416/github/malignment/experiments/slot_ratings"
LEX = "/Users/rj416/github/malignment/lexicons/norms"

#: FOUR SOURCES, RUN SEPARATELY. Their scales are not commensurable and their
#: coverage differs by an order of magnitude, so pooling them into one vector
#: would let a well-covered instrument speak for a thin one and would silently
#: score an uncovered component as a zero shift. Each gets its own verdict on
#: the components it actually covers.
#:
#:   v6            12 scales, CONTEXTUAL   34 of 35 frames
#:   sexual v2      9 scales, CONTEXTUAL    8 frames, the ones about bodies
#:   institutional 13 scales, CONTEXTUAL   23 frames
#:   k              5 scales, TYPE-LEVEL   27,242 words, one model's judgments
#:   warriner/brys  4 scales, TYPE-LEVEL   human norms
V6_SCALES = ("harm", "aggression", "directedness", "deliberation", "interiority",
             "superego", "vocalisation", "hedged", "makes_better", "makes_worse",
             "mundanity", "fit")
SEX_SCALES = ("genitality", "explicitness", "exposure", "euphemism", "orality",
              "tactility", "body_distance", "incorporation", "charge")
INST_SCALES = ("agency", "deference", "assertiveness", "procedural", "specificity",
               "delay", "abstraction", "target", "collective", "arousal",
               "vocalisation", "termination", "mediation")
#: ALL SEVEN k SCALES (RH, 2026-08-23). I had dropped `register_level` and
#: `vulgarity` on the file's own `_meta.NOT_ESTABLISHED` -- register_level
#: "usable as a descriptor, not as evidence" at IAA 0.60, vulgarity "a SPARSE
#: INDICATOR: variance on 463 of 27,242 words ... its floor effects are NOT
#: nulls". Those warnings are about reading ONE scale's level. This test reads a
#: DIRECTION across many scales, where a weak or sparse dimension adds noise
#: rather than bias and can only make the test harder to pass. Excluding them
#: was my judgement, not the file's instruction, and it hid how much the result
#: depends on which scales I chose -- so both versions are reported.
K_SCALES = ("vulgarity", "register_level", "transgressiveness", "charge",
            "valence", "bodily_harm", "concreteness")
K_SCALES_ESTABLISHED = ("transgressiveness", "charge", "valence", "bodily_harm",
                        "concreteness")
TYPE_SCALES = ("valence", "arousal", "dominance", "concreteness")
K_BRIDGE = 3
RATERS = ("high", "xhigh", "medium")


def _v6():
    out = collections.defaultdict(dict)
    for f in glob.glob(V6):
        try:
            rows = json.load(open(f))
        except Exception:
            continue
        for r in rows if isinstance(rows, list) else []:
            p, w = r.get("prompt"), r.get("word")
            if p and w:
                v = {s: r[s] for s in V6_SCALES if isinstance(r.get(s), (int, float))}
                if v:
                    out[p][w.lower()] = v
    return dict(out)


def _sexual():
    """From `words_long.csv.gz`, the only place the sexual v2 ratings are flat."""
    import gzip, csv
    out = collections.defaultdict(lambda: collections.defaultdict(dict))
    f = os.path.join(SLOT, "results", "long", "words_long.csv.gz")
    with gzip.open(f, "rt") as fh:
        for r in csv.DictReader(fh):
            if r.get("instrument") != "sexual_slot_en_v2":
                continue
            try:
                out[r["prompt"]][r["word"].lower()][r["scale"]] = float(r["value"])
            except (TypeError, ValueError):
                pass
    return {p: dict(d) for p, d in out.items()}


def _institutional():
    """Per-item `ratings` maps, keyed by prompt. Both arms carry the same words."""
    out = collections.defaultdict(dict)
    for f in glob.glob(os.path.join(SLOT, "institutional", "results", "*", "*.json")):
        try:
            x = json.load(open(f))
        except Exception:
            continue

        def walk(o):
            if isinstance(o, dict):
                p, rr = o.get("prompt"), o.get("ratings")
                if p and isinstance(rr, dict):
                    for w, v in rr.items():
                        if isinstance(v, dict):
                            out[p].setdefault(w.lower(), {}).update(
                                {s: v[s] for s in INST_SCALES
                                 if isinstance(v.get(s), (int, float))})
                for v in o.values():
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
        walk(x)
    return dict(out)


def _typelevel(scales, which):
    """Type-level: one value per word whatever the frame. Same table for every prompt.

    RH's caution stands and is why these are reported apart: a null here says the
    scale cannot see the relation, not that the relation is absent.
    """
    sys.path.insert(0, "/Users/rj416/github/malignment")
    if which == "k":
        #: `{_meta, ratings: {word: [7 POSITIONAL values]}}`, not a per-word dict.
        #: The order lives in `_meta.scales` and must be read from there rather
        #: than assumed -- an assumed order would silently read `charge` off the
        #: `vulgarity` column and every number would be wrong and plausible.
        d = json.load(open(os.path.join(LEX, "k_ratings_en.json")))
        order = d["_meta"]["scales"]
        idx = {s: order.index(s) for s in scales if s in order}
        miss = [s for s in scales if s not in order]
        assert not miss, "k_ratings has no scale(s) %s; it has %s" % (miss, order)
        tbl = {}
        for w, v in (d.get("ratings") or {}).items():
            if isinstance(v, list) and len(v) == len(order):
                tbl[w.lower()] = {s: v[i] for s, i in idx.items()}
    else:
        from malignment import fields as F
        tbl = {w: {s: v[s] for s in scales if isinstance(v.get(s), (int, float))}
               for w, v in F._norms().items()}
    return {"*": tbl}


SOURCES = {
    "v6": (V6_SCALES, _v6, "contextual"),
    "sexual": (SEX_SCALES, _sexual, "contextual"),
    "institutional": (INST_SCALES, _institutional, "contextual"),
    "k": (K_SCALES, lambda: _typelevel(K_SCALES, "k"), "type-level"),
    "k-est": (K_SCALES_ESTABLISHED,
              lambda: _typelevel(K_SCALES_ESTABLISHED, "k"), "type-level"),
    "human": (TYPE_SCALES, lambda: _typelevel(TYPE_SCALES, "human"), "type-level"),
}


def ratings(src="v6"):
    return SOURCES[src][1]()


def lookup(R, prompt, word):
    """Contextual sources key on the frame; type-level sources use one table."""
    return (R.get(prompt) or R.get("*") or {}).get(word)


def shifts(M, R, SC):
    """`{component_id: {scale: TO-mean minus FROM-mean}}`, plus its coverage.

    Unweighted over cited word TYPES. The rater's citation is already a
    selection -- it chose which words to name -- so weighting by mass would
    apply a second selection on top of one whose rule is not recorded.
    """
    out, cov = {}, {}
    for cid, c in M.items():
        rr = R.get(c["prompt"]) or R.get("*") or {}
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
                    for s in SC
                    if any(s in x for x in t) and any(s in x for x in f)}
    return out, cov


def cosine(a, b, SC):
    ks = [s for s in SC if s in a and s in b]
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


def test(src="v6", iters=5000, seed=20260823, M=None, rels=None, quiet=False):
    SC, _, kind = SOURCES[src]
    M = M if M is not None else CF.as_read()
    R = ratings(src)
    S, cov = shifts(M, R, SC)
    rels = rels if rels is not None else relations(M)
    frame = {cid: M[cid]["prompt"] for cid in M}

    def pairs(groups):
        xs = []
        for _, core in groups:
            ms = [c for c in core if c in S]
            for a, b in itertools.combinations(ms, 2):
                if frame[a] == frame[b]:
                    continue
                v = cosine(S[a], S[b], SC)
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
    #: NO PAIRS, NO p. An empty statistic against a null of zeros produced
    #: "p = 0.0005" on a comparison with nothing in it, which is a number that
    #: would be quoted. A source that covers nothing must say so.
    if not obs:
        r = dict(src=src, kind=kind, n_scales=len(SC), n_comp=len(S),
                 n_pairs=0, obs=None, null=None, p95=None, p=None)
        if quiet:
            return r
        print("HELD-OUT TEST (%s): NO cross-frame pairs covered; no test run." % src)
        return r
    m = statistics.mean(obs)
    pv = (sum(1 for x in null if x >= m) + 1.0) / (iters + 1.0)

    if quiet:
        return dict(src=src, kind=kind, n_scales=len(SC), n_comp=len(S),
                    n_pairs=len(obs), obs=m, null=statistics.median(null),
                    p95=sorted(null)[int(.95 * len(null))], p=pv)
    print("HELD-OUT TEST (%s, %s, %d scales)\n" % (src, kind, len(SC)))
    print("  %d relations with a 3-rater core, %d components carrying a shift"
          % (len(rels), len(S)))
    print("  cross-frame pairs inside a relation: %d" % len(obs))
    print("  observed mean cosine  %+.3f" % m)
    print("  null  %+.3f   95th %+.3f" % (statistics.median(null),
                                          sorted(null)[int(.95 * len(null))]))
    print("  p = %.4f   %s" % (pv, "SUPPORTED" if pv < .05 else "not supported"))
    return rels, S, obs, null, pv


def show_shifts(src="v6"):
    SC = SOURCES[src][0]
    M = CF.as_read()
    S, _ = shifts(M, ratings(src), SC)
    rels = relations(M)
    print("PER-RELATION MEAN SHIFT, v6 contextual scales (TO minus FROM)\n")
    hdr = "  %-34s %4s " % ("relation", "n") + " ".join("%5s" % s[:5] for s in SC)
    print(hdr)
    for name, core in sorted(rels, key=lambda r: -len(r[1])):
        ms = [c for c in core if c in S]
        if not ms:
            continue
        row = []
        for s in SC:
            v = [S[c][s] for c in ms if s in S[c]]
            row.append("%+5.2f" % statistics.mean(v) if v else "    -")
        print("  %-34s %4d " % (name[:34], len(ms)) + " ".join(row))


def coverage(src="v6"):
    M = CF.as_read()
    _, cov = shifts(M, ratings(src), SOURCES[src][0])
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
    ap.add_argument("--src", default="v6", choices=sorted(SOURCES))
    ap.add_argument("--all", action="store_true",
                    help="every source, reported separately -- they are not commensurable")
    a = ap.parse_args()
    if a.all:
        M = CF.as_read()
        rels = relations(M)
        print("EVERY RATING SOURCE, RUN SEPARATELY\n")
        print("  %-14s %-11s %6s %6s %6s %8s %8s %9s"
              % ("source", "kind", "scales", "comps", "pairs", "observed", "null95", "p"))
        for k in ("v6", "sexual", "institutional", "k", "k-est", "human"):
            try:
                r = test(k, a.iters, M=M, rels=rels, quiet=True)
            except Exception as e:
                print("  %-14s FAILED %s" % (k, str(e)[:52]))
                continue
            if r["p"] is None:
                print("  %-14s %-11s %6d %6d %6d %8s %8s %9s"
                      % (r["src"], r["kind"], r["n_scales"], r["n_comp"], 0,
                         "-", "-", "no pairs"))
                continue
            print("  %-14s %-11s %6d %6d %6d %+8.3f %+8.3f %9.4f%s"
                  % (r["src"], r["kind"], r["n_scales"], r["n_comp"], r["n_pairs"],
                     r["obs"], r["p95"], r["p"], "  *" if r["p"] < .05 else ""))
    elif a.coverage:
        coverage(a.src)
    elif a.shifts:
        show_shifts(a.src)
    else:
        test(a.src, a.iters)


if __name__ == "__main__":
    main()
