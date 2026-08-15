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
    cls LowCardinality(String),
    rule LowCardinality(String), theta Float32
) ENGINE = ReplacingMergeTree
ORDER BY (rule, relation, base, aligned, prompt, word)
"""


def buildable():
    """Edges whose BOTH arms have cells, with the shared-prompt count.

    The intersection, never one arm's list: taking either alone silently measures
    a different population, which is how a producer iterating a registry instead
    of the store once dropped 65% of amber's cells.
    """
    #: **uniqExact, NOT count().** `twp_cells` is a ReplacingMergeTree and rows
    #: are only deduplicated ON MERGE, so a key can sit in several parts. With
    #: `count()` this join reported 9,991 shared prompts for Qwen3-8B-Base ->
    #: Qwen3-8B, against 2,647 DISTINCT prompts in the whole corpus -- a count
    #: exceeding its own universe, which is the only reason it was caught.
    #: Measured at the time: 239,009 rows against 204,062 FINAL, 14.6% unmerged.
    #: The archive carries the same trap and books it as "any twp_words count
    #: without FINAL is an overcount of unknown size".
    return ch.query("""
        SELECT e.parent AS base, e.child AS aligned, e.op AS relation,
               uniqExact(a.prompt) AS prompts
        FROM {db}.edges e
        INNER JOIN (SELECT DISTINCT model, prompt FROM {db}.twp_cells) a
            ON a.model = e.parent
        INNER JOIN (SELECT DISTINCT model, prompt FROM {db}.twp_cells) b
            ON b.model = e.child AND b.prompt = a.prompt
        WHERE e.op IN %s
        GROUP BY base, aligned, relation
        ORDER BY prompts DESC
    """ % (str(DERIVING),))


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
    print("  edges with both arms in the store: %d" % len(edges))
    print("  shared prompts across them: %s"
          % format(sum(e["prompts"] for e in edges), ","))
    for e in edges[:10]:
        print("     %-34s -%s-> %-34s %6d prompts"
              % (e["base"].split("/")[-1][:34], e["relation"],
                 e["aligned"].split("/")[-1][:34], e["prompts"]))
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
            if prompt not in rp or prompt not in rq:
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
