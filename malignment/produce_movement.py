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
from . import corpus
from .movement import CANONICAL, LENS, DRAW, RESIDUAL_KEY, movement

#: **THE RULE VERSION SELECTS THE SOURCE TABLES AND THE DESTINATION.** v4 cells
#: live in twp_*_v4 and their movement lands in `movement_v4`, never mixed into
#: `movement` -- which has no rule_version column and could not tell them apart
#: row by row.
_RV = {"v": 3}
MOVEMENT_TABLE = {3: "movement", 4: "movement_v4"}

RULES = {"canonical": CANONICAL, "lens": LENS, "draw": DRAW}

#: **IMPORTED, NOT RETYPED.** This module's own docstring says "the population is
#: derived from a declaration, never retyped beside it" -- and then this line was
#: a hand-copied tuple that had drifted from `roster.DERIVING` by FIVE ops:
#: apo, continual, rlhf, and -- long before any of those existed -- `upscale` and
#: `prune`. So Falcon3-10B-Base's upscale edge and Falcon3-1B/3B's prune edges
#: were never in `movement` at all, and nothing reported their absence: a missing
#: edge is indistinguishable from an unmeasured one in a table built by iterating
#: the declaration you happen to hold.
#:
#: Found when two corrected edges (beaver, internlm2 -> `rlhf`) vanished from a
#: rebuild that otherwise looked clean. The duplicate constant is the bug; the
#: drift is only how it showed.
from .roster import DERIVING

#: **`relation` AND `depth` ARE NOT IN THIS TABLE, AND THAT IS THE POINT.**
#:
#: They are properties of the EDGE GRAPH, not of the measurement. The row
#: (base, aligned, prompt, word) -> p_base, p_aligned, delta, cls does not change
#: when an op is relabelled -- only the label does. Storing them here made every
#: `models.yaml` edit cost a full 52.9M-row, 25-minute recompute to change a
#: string, and `relation` sat in the ORDER BY, so a ReplacingMergeTree could not
#: even replace them: a re-run APPENDED `rlhf` rows beside stale `dpo` rows and
#: double-counted the corrected edges under both labels.
#:
#: This is the failure `views.py` already names -- "a stored rollup can disagree
#: with its source ... every one is a derived thing stored beside its source and
#: left to drift" -- and `relation` in `movement` was exactly that, missed
#: because it looks like a column rather than like a rollup.
#:
#: They now live in `{db}.pairs` (143 rows, rebuilt in milliseconds from the
#: roster) and the views JOIN it. A models.yaml relabel is now free.
DDL = """
CREATE TABLE IF NOT EXISTS {db}.%(tbl)s (
    base String, aligned String,
    prompt String, word String,
    p_base Float32, p_aligned Float32, delta Float32,
    cls LowCardinality(String),
    rule LowCardinality(String), theta Float32
) ENGINE = ReplacingMergeTree
ORDER BY (rule, base, aligned, prompt, word)
"""

DDL_V4 = """
CREATE TABLE IF NOT EXISTS {db}.movement_v4 (
    base String, aligned String,
    prompt String, word String,
    p_base Float32, p_aligned Float32, delta Float32,
    cls LowCardinality(String),
    rule LowCardinality(String), theta Float32,
    frame_base LowCardinality(String),
    frame_aligned LowCardinality(String),
    system_mode_base LowCardinality(String),
    system_mode_aligned LowCardinality(String)
) ENGINE = ReplacingMergeTree
ORDER BY (rule, frame_base, frame_aligned, base, aligned, prompt, word)
"""

#: **THE VALID FRAME COMBINATIONS AND WHY framed->raw IS REFUSED.**
#:
#: A framed base with a raw aligned is nonsensical: the base is measured inside
#: a deployment template while the aligned is measured on a bare string. The
#: delta would be (what the base produces in conversation) minus (what the
#: aligned produces as a raw continuation), which answers no coherent question
#: about alignment or deployment.
#:
#:     raw->raw        the existing contrast: both arms on bare strings
#:     raw->framed     deployed displacement: bare base, templated aligned
#:     framed->framed  within-frame: both arms templated (ladder tier)
#:     framed->raw     REFUSED: nonsensical direction
#:
#: Checked in the producer at row construction time, not at query time, because
#: a schema that permits a nonsensical row eventually holds one (lacan, [6560]).
VALID_FRAME_COMBOS = {
    ("", ""),               # raw -> raw
    ("", "prefill"),        # raw -> framed
    ("prefill", "prefill"), # framed -> framed
}

#: The graph, at the grain the views need it. Derived from `edges` every run, so
#: it cannot drift from the roster: it has no independent existence to drift into.
PAIRS_DDL = """
CREATE OR REPLACE TABLE {db}.pairs (
    base String, aligned String,
    relation LowCardinality(String), depth UInt8
) ENGINE = MergeTree ORDER BY (base, aligned)
"""


def _token_surface_models():
    """Models whose words are tokens not words — refused from movement."""
    bad = [r["model"] for r in ch.query(
        (r"""SELECT model FROM {db}.%s GROUP BY model"""
         % corpus.TABLES[_RV["v"]][0]) + r"""
            HAVING countIf(startsWith(word, '▁') OR startsWith(word, 'Ġ')
                           OR match(word, '^<0x[0-9A-Fa-f]{2}>$')) > 0""")]
    if bad:
        print("  REFUSING %d model(s): word surfaces are TOKENS, not words." % len(bad))
        for m in bad:
            print("     %s  -- re-measure; do not strip the marker" % m)
    return set(bad)


def buildable():
    """Every ANCESTOR -> DESCENDANT pair whose both arms have cells, with depth.

    Depth 1 is a declared edge; deeper pairs are transitive. The intersection is
    taken on prompts, never one arm's list: taking either alone silently measures
    a different population, which is how a producer iterating a registry instead
    of the store once dropped 65% of amber's cells.

    At v4, returns BOTH raw->raw pairs (frame_base='', frame_aligned='') AND
    cross-frame pairs (frame_base='', frame_aligned='prefill') where the base
    has raw cells and the aligned has framed cells.
    """
    par, op = {}, {}
    for r in ch.query("SELECT parent, child, op FROM {db}.edges"):
        if r["op"] in DERIVING:
            par[r["child"]] = r["parent"]
            op[r["child"]] = r["op"]
    _c = corpus.TABLES[_RV["v"]][1]
    have = {r["model"] for r in ch.query(
        "SELECT DISTINCT model FROM {db}.%s" % _c)}
    bad = _token_surface_models()
    have -= bad

    out = []
    for m in par:
        x, d = m, 0
        while x in par:
            x, d = par[x], d + 1
            if x in have and m in have:
                out.append({"base": x, "aligned": m, "relation": op[m],
                            "depth": d, "frame_base": "", "frame_aligned": ""})
    if _RV["v"] == 4:
        have_framed = {r["model"] for r in ch.query(
            "SELECT DISTINCT model FROM {db}.twp_cells_v4 "
            "WHERE frame='prefill'")}
        have_framed -= bad
        n_cross = 0
        for m in par:
            x, d = m, 0
            while x in par:
                x, d = par[x], d + 1
                if x in have and m in have_framed:
                    out.append({"base": x, "aligned": m, "relation": op[m],
                                "depth": d,
                                "frame_base": "", "frame_aligned": "prefill"})
                    n_cross += 1
        print("  cross-frame pairs (raw->framed): %d" % n_cross)
    return out


def graph():
    """Every declared ancestor -> descendant pair, WITHOUT the measured filter.

    **`pairs` IS THE EDGE GRAPH AND MUST NOT BE RULE-VERSION SCOPED.** It was
    populated from `buildable()`, which keeps only pairs whose both arms have
    cells AT THE CURRENT RULE VERSION -- and `pairs` is a single shared table
    that every run rewrites with CREATE OR REPLACE.

    So the first `--rule-version 4` run cut it from 151 rows to 132, and because
    `movement_cells` INNER JOINs it, the V3 rollup silently dropped from 400,267
    cells to 350,431. The 19 lost pairs are exactly the models not yet measured
    at v4 -- the Falcon3 ladder, DeepSeek-R1-Distill-Llama-8B, phi-4, Pharia --
    so building one version quietly narrowed the other version's published view,
    with nothing in either table recording it.

    The graph is a property of the ROSTER, not of the corpus. A pair belongs in
    it whether or not anyone has measured its arms; what is measured is decided
    by which rows exist in `movement`/`movement_v4`, and the JOIN then yields
    exactly the intersection without either side needing to know the other's
    population. Same shape as the module docstring's rule: derive from the
    declaration, never from whatever the store happens to hold today.
    """
    par, op = {}, {}
    for r in ch.query("SELECT parent, child, op FROM {db}.edges"):
        if r["op"] in DERIVING:
            par[r["child"]], op[r["child"]] = r["parent"], r["op"]
    out = []
    for m in par:
        x, d = m, 0
        while x in par:
            x, d = par[x], d + 1
            out.append({"base": x, "aligned": m, "relation": op[m], "depth": d})
    return out


def _arm(model, frame=""):
    """{prompt: ({word: p}, residual_total)} for one model at one frame.

    Bulk, not per-cell: the access shape is the variable, not the store.

    `frame=""` is the raw (untemplated) surface — every cell before 2026-08-22.
    `frame="prefill"` is the framed (chat-template) surface.

    ## AT v4 THIS PREFERS THE MERGED (TOPUP) CELL, AND THAT IS THE POINT

    Pass 2 measures the words a model's LINEAGE cleared and it did not -- words
    every consumer would otherwise impute as zero, which is most of the reason
    topup was built. So `movement` over merged cells is the intended product and
    not a variant of it. RH, 2026-08-19: *"not comparable is fine, movement with
    topup was part of motivation for topup."*

    **The v3 and v4 movement numbers are therefore NOT COMPARABLE**, and not only
    because the boundary rule changed: `departed` and `arrived` are computed over
    a LARGER SUPPORT at v4, since the merged cell carries sub-theta words the
    pass-1 cell never had. Two tables, deliberately, with no path between them.

    A merged cell already contains pass 1's rows -- `topup` writes expand's rows
    plus the scored ones with `tail` decremented -- so preferring it is a choice
    of ONE row per (model, prompt), never a union of two. Where no topup cell
    exists the pass-1 cell is used, so coverage is never reduced by asking.

    ## FRAMED CELLS HAVE NO TOPUP, AND THAT IS CORRECT

    Topup is a pass-2 operation keyed on the LINEAGE UNION — which words a
    model's siblings cleared but it did not. It exists for the raw arm because
    the raw corpus is the one where displacement comparisons omit sub-theta
    words. The framed arm has no topup by design: it is pass 1 only, and the
    cross-frame delta compares the raw arm's merged words against the framed
    arm's pass-1 words. That is an asymmetry of coverage, not an error — the
    raw arm is as complete as it can be, and the framed arm is as complete as
    its own measurement.
    """
    esc = model.replace("'", "\\'")
    fesc = frame.replace("'", "\\'")
    if _RV["v"] == 3:
        wq = "SELECT prompt, word, p FROM {db}.twp_words WHERE model='%s'" % esc
        cq = "SELECT prompt, total FROM {db}.twp_cells WHERE model='%s'" % esc
    else:
        #: argMax over the tuple picks the merged cell where one exists and the
        #: pass-1 cell where it does not -- one row per prompt either way.
        #:
        #: **THE ORDERING MUST MATCH `twp_*_v4_best` EXACTLY, AND `topup` ALONE
        #: DOES NOT.** 3,790 cell keys and 495,624 word keys carry two rows at the
        #: SAME topup, differing on `prompt_cache`, so `argMax(p, topup)` hits a
        #: tie and breaks it arbitrarily. Two consequences, and the second is
        #: worse than the first: the choice is not reproducible across a merge,
        #: and `movement_v4` could select a DIFFERENT row than the `_best` views
        #: hand every other consumer -- two canonical answers for one cell, with
        #: nothing in either table saying they disagree.
        #:
        #: (topup, prompt_cache, mtime) leaves 0 tied keys in either table.
        #: prompt_cache=1 wins because it is 80.2% of the corpus and four cells
        #: in five have no replicate at all. Same tuple, same order, same reason
        #: as `views.py` -- if one of these changes the other has to.
        wq = ("SELECT prompt, word, argMax(p, (topup, prompt_cache, mtime)) AS p "
              "FROM {db}.twp_words_v4 WHERE model='%s' AND frame='%s' "
              "GROUP BY prompt, word" % (esc, fesc))
        #: **NOT `total`. `total` IS STALE ON A TOPUP CELL.** Measured corpus-wide
        #: 2026-08-21: `total` == tail+drop+open+mojibake on 434,391 of 434,391
        #: pass-1 cells and on 984,857 of 984,857 v3 cells -- and on only 35,402
        #: of 385,855 topup cells. The topup writer decrements `tail` when it adds
        #: sub-theta words and does not recompute `total`, so a merged cell's
        #: `total` is the PASS-1 residual: mean 0.0148 too high, max 0.115.
        #:
        #: Passing it as the residual is what broke the ledger --
        #: `arrived - departed + mass_still + resid_delta` failed on 294,854 of
        #: 392,285 v4 cells (75%) while v3 was 0 of 400,267. The words came from
        #: the merged cell and the residual from the pass-1 one, so the two arms
        #: of the same identity were measured over different supports.
        #:
        #: `conservation` (words+tail+drop+open+mojibake) is 1.0 on BOTH passes,
        #: 0 violations in 820,246 cells, so the components are trustworthy and
        #: only their `total` summary is not. Deriving the residual from them is
        #: therefore exact rather than a repair.
        cq = ("SELECT prompt, argMax(tail + drop + open + mojibake, "
              "(topup, prompt_cache, mtime)) AS total "
              "FROM {db}.twp_cells_v4 WHERE model='%s' AND frame='%s' "
              "GROUP BY prompt" % (esc, fesc))
    words = collections.defaultdict(dict)
    for r in ch.query(wq):
        words[r["prompt"]][r["word"]] = r["p"]
    resid = {r["prompt"]: r["total"] for r in ch.query(cq)}
    return words, resid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scan", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--rule", default="canonical", choices=sorted(RULES))
    ap.add_argument("--rule-version", type=int, default=3, choices=[3, 4],
                    help="4 reads twp_*_v4 (merged topup cells) and writes "
                         "movement_v4. The two tables are NOT comparable and are "
                         "kept separate for that reason.")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--all", action="store_true",
                    help="recompute every pair, not just missing ones")
    a = ap.parse_args()
    _RV["v"] = a.rule_version
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

    ch.execute((DDL_V4 if _RV["v"] == 4 else DDL) % {"tbl": MOVEMENT_TABLE[_RV["v"]]})
    #: THE GRAPH, REWRITTEN EVERY RUN AND FREE. CREATE OR REPLACE, so it cannot
    #: hold a pair the roster no longer declares.
    ch.execute(PAIRS_DDL)
    #: **THE FULL GRAPH, NOT `edges`.** `edges` is this run's buildable subset and
    #: is rule-version scoped; `pairs` is shared by the v3 and v4 views, so
    #: writing the subset here makes one version's build narrow the other
    #: version's rollup. See graph().
    _g = graph()
    ch.insert("pairs", [{"base": e["base"], "aligned": e["aligned"],
                         "relation": e["relation"], "depth": e["depth"]}
                        for e in _g])
    print("  %s.pairs: %d rows, the whole declared graph "
          "(relation + depth live HERE, not in movement); %d buildable at v%d"
          % (ch.DB, len(_g), len(edges), _RV["v"]))
    if a.limit:
        edges = edges[:a.limit]

    #: INCREMENTAL BY DEFAULT. A models.yaml edit that ADDS an edge should cost
    #: the new pairs, not all 143. `--all` forces the full recompute; anything
    #: that changes the ARITHMETIC (a new --rule, a movement.py fix) needs it and
    #: nothing else does.
    if not a.all:
        #: **THE DESTINATION TABLE, NOT `movement`.** This read was hardcoded to
        #: `{db}.movement` while the INSERTS below correctly used
        #: MOVEMENT_TABLE[_RV["v"]]. So `--rule-version 4` found all 132 pairs
        #: "already present" in the V3 table, computed nothing, and left
        #: `movement_v4` created and EMPTY -- while printing a plausible
        #: incremental summary. The campaign's own rule-version trap, in the
        #: producer that names it in its module docstring.
        if _RV["v"] == 4:
            have = {(r["base"], r["aligned"], r.get("frame_base", ""),
                     r.get("frame_aligned", "")) for r in ch.query(
                "SELECT DISTINCT base, aligned, frame_base, frame_aligned "
                "FROM {db}.%s WHERE rule='%s'"
                % (MOVEMENT_TABLE[_RV["v"]], rule.name))}
            skip = [e for e in edges if (e["base"], e["aligned"],
                    e.get("frame_base", ""), e.get("frame_aligned", "")) in have]
            edges = [e for e in edges if (e["base"], e["aligned"],
                     e.get("frame_base", ""), e.get("frame_aligned", "")) not in have]
        else:
            have = {(r["base"], r["aligned"]) for r in ch.query(
                "SELECT DISTINCT base, aligned FROM {db}.%s WHERE rule='%s'"
                % (MOVEMENT_TABLE[_RV["v"]], rule.name))}
            skip = [e for e in edges if (e["base"], e["aligned"]) in have]
            edges = [e for e in edges if (e["base"], e["aligned"]) not in have]
        print("  incremental: %d pairs already present, %d to compute"
              " (--all to force)" % (len(skip), len(edges)))
    _system_mode_cache = {}
    if _RV["v"] == 4:
        for r in ch.query(
                "SELECT model, any(system_mode) AS sm FROM {db}.twp_cells_v4 "
                "WHERE frame='prefill' GROUP BY model"):
            _system_mode_cache[r["model"]] = r["sm"]

    rows = []
    n_cells = n_refused = 0
    for e in edges:
        fb = e.get("frame_base", "")
        fa = e.get("frame_aligned", "")
        if (fb, fa) not in VALID_FRAME_COMBOS:
            print("  REFUSING %s -> %s: frame combo (%r, %r) is not valid"
                  % (e["base"].split("/")[-1], e["aligned"].split("/")[-1], fb, fa))
            continue
        P, rp = _arm(e["base"], frame=fb)
        Q, rq = _arm(e["aligned"], frame=fa)
        sm_base = ""
        sm_aligned = ""
        if _RV["v"] == 4 and fa:
            sm_aligned = _system_mode_cache.get(e["aligned"], "")
        if _RV["v"] == 4 and fb:
            sm_base = _system_mode_cache.get(e["base"], "")
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
                #: **EXACT MATCH, NOT A PREFIX.** This read `w.startswith("__")`
                #: to skip the residual key `__TAIL__`, and silently deleted
                #: `____`, `______`, `__________` -- the blank-fill template
                #: tokens that ARE the OLMo genre-collapse finding ("intermediate
                #: layers dominated by template tokens (`____`, `kms`); explains
                #: genre collapse"). 16 words per cell carrying 0.606 of the
                #: aligned distribution, on the cell where `kill` 0.098 -> 0 and
                #: `Options` 0 -> 0.097.
                #:
                #: Caught by a ledger that would not close: arrived - departed +
                #: still + resid came to -0.698 where it must be 0. A reserved
                #: key is a VALUE, and testing a value with a prefix is the same
                #: text-for-structure substitution that cost this project four
                #: other results today.
                if w == RESIDUAL_KEY:
                    continue
                row = {"base": e["base"], "aligned": e["aligned"],
                       "prompt": prompt, "word": w,
                       "p_base": float(P[prompt].get(w, 0.0)),
                       "p_aligned": float(Q[prompt].get(w, 0.0)),
                       "delta": float(d),
                       "cls": "faller" if w in fall else
                              ("riser" if w in rise else "still"),
                       "rule": rule.name, "theta": rule.theta}
                if _RV["v"] == 4:
                    row.update({"frame_base": fb, "frame_aligned": fa,
                                "system_mode_base": sm_base,
                                "system_mode_aligned": sm_aligned})
                rows.append(row)
        if len(rows) > 500_000:
            ch.insert(MOVEMENT_TABLE[_RV["v"]], rows); rows = []
            print("     ... %s rows" % format(
                ch.scalar("SELECT count() FROM {db}.%s" % MOVEMENT_TABLE[_RV["v"]]), ","))
    if rows:
        ch.insert(MOVEMENT_TABLE[_RV["v"]], rows)
    #: Every read here was hardcoded to `{db}.movement` while the inserts above
    #: went to MOVEMENT_TABLE. A v4 run therefore wrote v4 rows and then reported
    #: the v3 table's counts as its result -- the writes were right and every
    #: number printed was about another table.
    _tbl = MOVEMENT_TABLE[_RV["v"]]
    print("\n  cells computed: %s | refused (no residual): %s"
          % (format(n_cells, ","), format(n_refused, ",")))
    print("  %s.%s: %s rows"
          % (ch.DB, _tbl, format(ch.scalar("SELECT count() FROM {db}.%s" % _tbl), ",")))
    for r in ch.query("""SELECT cls, count() c FROM {db}.%s
                         GROUP BY cls ORDER BY c DESC""" % _tbl):
        print("     %-8s %s" % (r["cls"], format(r["c"], ",")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
