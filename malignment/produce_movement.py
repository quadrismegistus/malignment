"""twp_words x roster edges -> the movement table. A producer, not an accessor.

    python -m malignment.produce_movement --scan          edges that can be built
    python -m malignment.produce_movement --run [--rule canonical]

## WHY A TABLE AND NOT A FUNCTION CALL

The old repo reached the store cell-at-a-time -- `Cell.pre.probs` -> `word_probs`
-> one payload -- and that access shape is the one ClickHouse is worst at:
measured, 192 ms/cell point-querying against 0.097 ms/cell in bulk. Sixteen
scripts in the archive already query the precomputed `movement` table instead,
which is why `ch_read.py`'s prefetch was brought here and dropped again within
the hour: SQL over a built table does not need it.

RH, 2026-08-15: *"movement.py should be mainly for analysis, it produces the data
for CH movement tables that is then consumed by others via CH queries."*

So `movement.py` keeps the RULES and the arithmetic; this drives them across
every declared edge and writes rows. Analysis is then SQL.

## RUNGS AND TRANSITIVE PAIRS — BOTH, BECAUSE MOVEMENT IS NOT ADDITIVE

RH: *"is it redundant or useful to also produce base -> anything above it no
matter depth?"* Useful, and not redundant, for a reason that is a property of the
metric rather than of the schema: **a word can fall at SFT and rise at DPO**, so
the riser/faller classification of `base -> DPO` is NOT recoverable from
`base -> SFT` plus `SFT -> DPO`. The transitive edge answers *what did the whole
pipeline do*; the rungs answer *which stage did it*. The division-of-labour
result needs both.

It is also the campaign's headline unit. `base_to_superego` is a DEPTH-2 pair on
a three-rung ladder, and the archive's movement table carries it as its own
relation for exactly that reason.

    depth 1   91 pairs    the declared edges
    depth 2   29          e.g. Llama-3.1-8B -> Tulu-3-8B-DPO   (base -> superego)
    depth 3    6          e.g. Llama-3.1-8B -> Tulu-3.1-8B     (base -> RLVR)
                126 total, 122 with both arms in the corpus

`depth` is a column, so a query asks for one-rung or total and says which.

## THE POPULATION IS THE ROSTER, NOT A LIST

One row per (edge, prompt, word). The edges come from `malignment.edges` -- every
DERIVING operation the roster declares -- so a new edge in `roster/models.yaml`
enters the movement table on the next run without anyone maintaining a pair list.
That is the same principle as the ingest taking its sources from the payload
stamp: **the population is derived from a declaration, never retyped beside it.**

`relation` carries the edge's op (sft / dpo / instruct / rlvr / ...), so the
SFT-vs-DPO division-of-labour question -- which stage carries the repression, and
does it vary by family and content -- is a GROUP BY rather than a separate study.
That question is the reason the Freudian slot names came out of the schema.

## THE RESIDUAL IS AN ARM OF THE COMPARISON

`movement()` needs each arm's untruncated remainder or its null is computed over
the scored set alone, and it says so: `diagnostics["exact_null"]` goes False,
which "is a claim about the input, not a property of the data". `twp_cells.total`
holds it, so it is passed. A cell missing its residual is REFUSED rather than
computed with a silently different null.
"""
import argparse
import collections
import sys

from . import ch
from .movement import CANONICAL, LENS, DRAW, movement

RULES = {"canonical": CANONICAL, "lens": LENS, "draw": DRAW}
DERIVING = ("sft", "dpo", "rlvr", "ppo", "kto", "slic", "instruct", "distill")

DDL = """
CREATE TABLE IF NOT EXISTS {db}.movement (
    base String, aligned String, relation LowCardinality(String),
    prompt String, word String,
    p_base Float32, p_aligned Float32, delta Float32,
    cls LowCardinality(String), depth UInt8,
    rule LowCardinality(String), theta Float32
) ENGINE = ReplacingMergeTree
ORDER BY (rule, depth, relation, base, aligned, prompt, word)
"""


def buildable():
    """Every ANCESTOR -> DESCENDANT pair whose both arms have cells, with depth.

    Depth 1 is a declared edge; deeper pairs are transitive. The intersection is
    taken on prompts, never one arm's list: taking either alone silently measures
    a different population, which is how a producer iterating a registry instead
    of the store once dropped 65% of amber's cells.
    """
    par, op = {}, {}
    for r in ch.query("SELECT parent, child, op FROM {db}.edges"):
        if r["op"] in DERIVING:
            par[r["child"]] = r["parent"]
            op[r["child"]] = r["op"]
    have = {r["model"] for r in ch.query("SELECT DISTINCT model FROM {db}.twp_cells")}
    out = []
    for m in par:
        x, d = m, 0
        while x in par:
            x, d = par[x], d + 1
            if x in have and m in have:
                #: `relation` is the op of the LAST rung into the descendant, so a
                #: depth-2 pair through SFT->DPO reads `dpo`. The stage that
                #: produced the endpoint is what a GROUP BY wants; `depth` says
                #: how far back the other arm sits.
                out.append({"base": x, "aligned": m, "relation": op[m], "depth": d})
    return out


def _arm(model):
    """{prompt: ({word: p}, residual_total)} for one model, in ONE query.

    Bulk, not per-cell: the access shape is the variable, not the store.
    """
    words = collections.defaultdict(dict)
    for r in ch.query("SELECT prompt, word, p FROM {db}.twp_words WHERE model='%s'"
                      % model.replace("'", "\\'")):
        words[r["prompt"]][r["word"]] = r["p"]
    resid = {r["prompt"]: r["total"] for r in ch.query(
        "SELECT prompt, total FROM {db}.twp_cells WHERE model='%s'"
        % model.replace("'", "\\'"))}
    return words, resid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scan", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--rule", default="canonical", choices=sorted(RULES))
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    rule = RULES[a.rule]

    edges = buildable()
    import collections as _c
    bydepth = _c.Counter(e["depth"] for e in edges)
    print("  ancestor->descendant pairs with both arms: %d" % len(edges))
    for d in sorted(bydepth):
        print("     depth %d: %d pairs" % (d, bydepth[d]))
    for e in edges[:8]:
        print("     d%d %-30s -%s-> %s" % (e["depth"], e["base"].split("/")[-1][:30],
              e["relation"], e["aligned"].split("/")[-1][:34]))
    if a.scan or not a.run:
        return 0

    ch.execute(DDL)
    if a.limit:
        edges = edges[:a.limit]
    rows = []
    n_cells = n_refused = 0
    for e in edges:
        P, rp = _arm(e["base"])
        Q, rq = _arm(e["aligned"])
        for prompt in set(P) & set(Q):
            #: REFUSED, not computed with a different null. `movement()` says an
            #: absent residual makes `exact_null` False, "a claim about the input,
            #: not a property of the data" -- so a cell without one does not
            #: quietly join a table where every other row had one.
            #: The ingest gate now rejects NaN, but a producer that trusts its
            #: upstream inherits every defect the upstream ever misses.
            if prompt not in rp or prompt not in rq:
                n_refused += 1
                continue
            if rp[prompt] != rp[prompt] or rq[prompt] != rq[prompt]:
                n_refused += 1
                continue
            mv = movement(P[prompt], Q[prompt], rule=rule,
                          residual_pre=rp[prompt], residual_post=rq[prompt])
            n_cells += 1
            fall = set(mv.fallers)
            rise = set(mv.risers)
            for w, d in mv.delta.items():
                if w.startswith("__"):     # the residual key is not a word
                    continue
                rows.append({"base": e["base"], "aligned": e["aligned"],
                             "relation": e["relation"], "prompt": prompt, "word": w,
                             "p_base": float(P[prompt].get(w, 0.0)),
                             "p_aligned": float(Q[prompt].get(w, 0.0)),
                             "delta": float(d),
                             "cls": "faller" if w in fall else
                                    ("riser" if w in rise else "still"),
                             "depth": e["depth"],
                             "rule": rule.name, "theta": rule.theta})
        if len(rows) > 500_000:
            ch.insert("movement", rows); rows = []
            print("     ... %s rows" % format(
                ch.scalar("SELECT count() FROM {db}.movement"), ","))
    if rows:
        ch.insert("movement", rows)
    print("\n  cells computed: %s | refused (no residual): %s"
          % (format(n_cells, ","), format(n_refused, ",")))
    print("  %s.movement: %s rows"
          % (ch.DB, format(ch.scalar("SELECT count() FROM {db}.movement"), ",")))
    for r in ch.query("""SELECT cls, count() c FROM {db}.movement
                         GROUP BY cls ORDER BY c DESC"""):
        print("     %-8s %s" % (r["cls"], format(r["c"], ",")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
