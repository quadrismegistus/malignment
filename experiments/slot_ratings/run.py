"""Rate a frame's eligible vocabulary and correlate against CANONICAL movement.

    python experiments/slot_ratings/run.py --prompt "She slowly took off her"
    python experiments/slot_ratings/run.py --item nn_crowdbeganto_2c3f4b48
    python experiments/slot_ratings/run.py --prompt "..." --dry   # population only, no API

## THE POPULATION IS DEFINED BY THE RULE THAT MAKES THE OUTCOME

Not by a coverage threshold. Measured on "She slowly took off her", 2026-08-19,
grouping words by how many of the 8 pairs hold them:

    seen   n   median p_base   % >= min_prob   % with net < 0
    1     66      0.00099            2%              0%
    8     33      0.01984          100%             48%

**CANONICAL gates fallers on `P >= min_prob` (0.003).** A word below that in the
base arm CANNOT be called a faller, so its net is floored at >= 0 BY THE RULE.
Including such words does not add noise, it adds outcomes that were censored
before the rating existed -- and since low coverage tracks low probability, any
`seen >= k` threshold is a probability filter wearing a coverage costume.

So: **a word counts in a pair only where that pair's BASE arm gives it
`p >= min_prob`.** Rises and falls are counted over eligible pairs only, and
`n_eligible` traveIs with every net. A word eligible in 2 pairs and one eligible
in 8 are not on one scale, and `net_rate = net / n_eligible` says so.

This is the asymmetry `movement.py` documents and refuses to patch: risers are
null-tested against renormalisation, fallers are a bare ratio. Nothing here
describes a faller as "beyond renormalisation".

## ONLY CONTENT WORDS ARE ANNOTATED

NOUN, VERB, ADJ, ADV (RH, 2026-08-19), tagged contextually by
`malignment.pos.get_pos` -- at the slot, not by lookup. 44% of one frame's raw
vocabulary was function words, fragments and tokenisation debris, and the
frame-relative scales (`consummation`, `transitivity`) are close to meaningless
on a determiner.

POS also decides where a scale may be READ, not only where it is computed:
`suggestive` is a noun-slot scale on "took off her", and `consummation` needs a
verb slot. Report per POS rather than discovering it as a null.

## WHAT IS NOT CONTROLLED

`n_eligible` correlates with base probability by construction, and probability
correlates with movement. So a rating that tracks frequency will look like a
rating that tracks displacement. The frequency control is NOT implemented here;
until it is, any rho reported is an upper bound.
"""

import argparse, collections, json, os, sys
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
RESULTS = os.path.join(HERE, "results")
CELLS = os.path.join(REPO, "experiments", "displacement", "displacement_axis",
                     "results", "pilot3", "cells.jsonl")
CONTENT_POS = ("NOUN", "VERB", "ADJ", "ADV")


def population(prompt=None, item_id=None):
    """Per-word CANONICAL rise/fall over ELIGIBLE pairs, plus contextual POS."""
    sys.path.insert(0, REPO)
    from malignment import vectors as V
    from malignment.movement import movement, CANONICAL
    from malignment.pos import get_pos

    cells = [json.loads(l) for l in open(CELLS, encoding="utf-8")]
    if item_id:
        mine = [c for c in cells if c["item_id"] == item_id]
    else:
        mine = [c for c in cells if c["prompt"].strip() == prompt.strip()]
    if not mine:
        raise SystemExit("no cells for %r" % (item_id or prompt))
    prompt = mine[0]["prompt"]

    models = sorted({c["base"] for c in mine} | {c["endpoint"] for c in mine})
    #: `_best`, NOT `twp_words_v4`. The raw table carries pass-1 and merged rows
    #: for the same (model, prompt, word) -- 12,300,833 rows over 9,993,876 keys --
    #: and a dict(zip(ws, ps)) keeps whichever came last, arbitrarily. The view does
    #: argMax(p, topup) internally: merged where a topup cell exists, pass 1 where
    #: it does not, one row per key. Impact measured before switching: mean
    #: |pmax-pmin| 1.02e-07 and FOURTEEN keys in the whole table where the choice
    #: flips CANONICAL min_prob -- none of them in these 303 frames. Correctness
    #: fix, not a results fix. (malign, send-peer, 2026-08-19.)
    rows = V.rows("SELECT model, groupArray(word) AS ws, groupArray(p) AS ps "
                  "FROM twp_words_v4_best WHERE prompt={p:String} "
                  "AND model IN {ms:Array(String)} GROUP BY model",
                  p=prompt, ms=models)
    store = {r["model"]: dict(zip(r["ws"], r["ps"])) for r in rows}

    rise = collections.Counter()
    fall = collections.Counter()
    elig = collections.Counter()      # pairs where the BASE arm clears min_prob
    present = collections.Counter()   # pairs where the word appears at all
    for c in mine:
        pb, pa = store.get(c["base"]), store.get(c["endpoint"])
        if not pb or not pa:
            continue
        m = movement(pb, pa, CANONICAL,
                     residual_pre=c.get("residual_base"),
                     residual_post=c.get("residual_endpoint"))
        for w in set(pb) | set(pa):
            present[w] += 1
            if pb.get(w, 0.0) >= CANONICAL.min_prob:
                elig[w] += 1
        rs, fs = set(m.risers), set(m.fallers)
        for w in rs | fs:
            if pb.get(w, 0.0) < CANONICAL.min_prob:
                continue          # not eligible in THIS pair; its net is censored
            if w in rs:
                rise[w] += 1
            if w in fs:
                fall[w] += 1

    words = sorted(w for w in elig if elig[w] > 0)
    pos = get_pos(words, prompt) if words else {}
    out = []
    for w in words:
        out.append(dict(word=w, prompt=prompt, item_id=mine[0]["item_id"],
                        pos=pos.get(w, "X"),
                        rise=rise[w], fall=fall[w], net=rise[w] - fall[w],
                        n_eligible=elig[w], n_present=present[w],
                        net_rate=(rise[w] - fall[w]) / elig[w]))
    return prompt, mine, out


def per_pair(prompt, cells, rated):
    """rho(rating, movement) computed WITHIN each pair, then across pairs.

    **THE UNIT IS THE LINEAGE PAIR** (RH, 2026-08-19). Collapsing rise/fall over
    pairs into one per-word number and correlating across words pools the pairs
    inside the statistic, which is the shape that gave the Pass B pilot the
    opposite sign to its own paired test.

    Within a pair, a word's outcome is the RULE'S verdict, not a raw delta:
    +1 riser, -1 faller, 0 otherwise. Raw `Q - P` would discard the
    renormalisation null that makes a riser a riser.

    Returns {scale: [rho per pair]}. The test across pairs is Wilcoxon on those.
    """
    sys.path.insert(0, REPO)
    from malignment import vectors as V
    from malignment.movement import movement, CANONICAL
    from scipy import stats
    import task as _t
    rat = {d["word"]: d for d in rated if d.get("ratable")}
    if not rat:
        return {}, 0
    _row = next(iter(rat.values()))
    seen, SCALES = set(), []
    for s in (_t.SCALES + _t.SCALES_V2 + _t.SCALES_V3 + _t.SCALES_V4 + _t.SCALES_V5 + _t.SCALES_V6):      # dedup: `suggestive` is in BOTH
        if s in _row and s not in seen:
            seen.add(s); SCALES.append(s)
    models = sorted({c["base"] for c in cells} | {c["endpoint"] for c in cells})
    #: `_best`, NOT `twp_words_v4`. The raw table carries pass-1 and merged rows
    #: for the same (model, prompt, word) -- 12,300,833 rows over 9,993,876 keys --
    #: and a dict(zip(ws, ps)) keeps whichever came last, arbitrarily. The view does
    #: argMax(p, topup) internally: merged where a topup cell exists, pass 1 where
    #: it does not, one row per key. Impact measured before switching: mean
    #: |pmax-pmin| 1.02e-07 and FOURTEEN keys in the whole table where the choice
    #: flips CANONICAL min_prob -- none of them in these 303 frames. Correctness
    #: fix, not a results fix. (malign, send-peer, 2026-08-19.)
    rows = V.rows("SELECT model, groupArray(word) AS ws, groupArray(p) AS ps "
                  "FROM twp_words_v4_best WHERE prompt={p:String} "
                  "AND model IN {ms:Array(String)} GROUP BY model",
                  p=prompt, ms=models)
    store = {r["model"]: dict(zip(r["ws"], r["ps"])) for r in rows}

    out = {s: [] for s in SCALES}
    npairs = 0
    for c in cells:
        pb, pa = store.get(c["base"]), store.get(c["endpoint"])
        if not pb or not pa:
            continue
        m = movement(pb, pa, CANONICAL,
                     residual_pre=c.get("residual_base"),
                     residual_post=c.get("residual_endpoint"))
        rs, fs = set(m.risers), set(m.fallers)
        elig = [w for w in rat if pb.get(w, 0.0) >= CANONICAL.min_prob]
        if len(elig) < 10:
            continue
        mv = [(1 if w in rs else -1 if w in fs else 0) for w in elig]
        if len(set(mv)) < 2:
            continue
        npairs += 1
        for s in SCALES:
            xs = [rat[w][s] for w in elig]
            if len(set(xs)) < 2:
                continue
            r = stats.spearmanr(xs, mv).correlation
            if r == r:
                out[s].append(r)
    return out, npairs


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt")
    ap.add_argument("--item")
    ap.add_argument("--v6", action="store_true",
                    help="THE CORPUS INSTRUMENT: twelve contextual axes.")
    ap.add_argument("--v5", action="store_true",
                    help="WIDE: twelve axes, one per prior campaign finding.")
    ap.add_argument("--v4", action="store_true",
                    help="v3's axes with `directedness` asked about the action's "
                         "normal object rather than a named one, and the FRAGMENT "
                         "made explicit to the rater.")
    ap.add_argument("--v3", action="store_true",
                    help="the crossing act scales (harm, aggression, "
                         "directedness) plus fit. Designed to be read as a GRID, "
                         "not one scale at a time.")
    ap.add_argument("--v2", action="store_true",
                    help="the four-scale v2 instrument (suggestive, fit, "
                         "indirection, expressiveness). A rating is a property "
                         "of the INSTRUMENT VERSION: v1 and v2 numbers are "
                         "comparable on RANKS, never pooled.")
    ap.add_argument("--dry", action="store_true",
                    help="report the population and stop; no API calls")
    ap.add_argument("--min-eligible", type=int, default=3,
                    help="THE RATED POPULATION IS THE ANALYSED POPULATION. "
                         "Eligibility (p_base >= min_prob) fixes censoring; it "
                         "does not fix precision, since a word eligible in one "
                         "pair has net in {-1,0,+1}. Rating below the reporting "
                         "floor buys nothing and was a real defect: 178 words "
                         "rated to analyse 79.")
    a = ap.parse_args(argv)
    if not (a.prompt or a.item):
        raise SystemExit("need --prompt or --item")

    prompt, cells, pop = population(a.prompt, a.item)
    content = [d for d in pop if d["pos"] in CONTENT_POS
               and d["n_eligible"] >= a.min_eligible]
    print("prompt : %s ___" % prompt)
    print("pairs  : %d" % len(cells))
    print("eligible words: %d   content-POS: %d" % (len(pop), len(content)))
    print("  POS mix: %s" % dict(collections.Counter(d["pos"] for d in pop).most_common(6)))
    if content:
        print("  n_eligible: median %d  range %d-%d"
              % (st.median(d["n_eligible"] for d in content),
                 min(d["n_eligible"] for d in content),
                 max(d["n_eligible"] for d in content)))
        print("  net<0: %.0f%%   net>0: %.0f%%   net==0: %.0f%%"
              % tuple(100 * sum(1 for d in content if f(d["net"])) / len(content)
                      for f in (lambda n: n < 0, lambda n: n > 0, lambda n: n == 0)))
    if a.dry:
        return
    if a.v6:
        from task import SlotRatingENv6 as TaskCls, SCALES_V6 as SCALES, render
    elif a.v5:
        from task import SlotRatingENv5 as TaskCls, SCALES_V5 as SCALES, render
    elif a.v4:
        from task import SlotRatingENv4 as TaskCls, SCALES_V4 as SCALES, render
    elif a.v3:
        from task import SlotRatingENv3 as TaskCls, SCALES_V3 as SCALES, render
    elif a.v2:
        from task import SlotRatingENv2 as TaskCls, SCALES_V2 as SCALES, render
    else:
        from task import SlotRatingEN as TaskCls, SCALES, render
    VER = "_v6" if a.v6 else "_v5" if a.v5 else "_v4" if a.v4 else "_v3" if a.v3 else "_v2" if a.v2 else ""
    t = TaskCls()
    errs = {}
    res = t.map([render(prompt, d["word"]) for d in content],
                metadata_list=[{"prompt": prompt, "word": d["word"]} for d in content],
                num_workers=32, errors=errs)
    print("errors: %d" % len(errs))
    for d, r in zip(content, res):
        if r is None:
            continue
        d["ratable"], d["reading"] = r.ratable, r.reading
        for s in SCALES:
            d[s] = getattr(r, s)
    os.makedirs(RESULTS, exist_ok=True)
    slug = cells[0]["item_id"]
    path = os.path.join(RESULTS, "rated%s_%s.json" % (VER, slug))
    json.dump(content, open(path, "w"), indent=1)
    print("-> %s" % path)

    from scipy import stats
    ok = [d for d in content if d.get("ratable")]
    pp, npairs = per_pair(prompt, cells, content)
    print("\nPER-PAIR rho(rating, mover verdict), then across %d pairs" % npairs)
    print("  %-14s %7s %7s %8s %9s" % ("scale", "median", "mean", "up/n", "wilcoxon"))
    for s in SCALES:
        v = pp.get(s) or []
        if len(v) < 5:
            print("  %-14s %7s (only %d pairs)" % (s, "--", len(v)))
            continue
        up = sum(1 for x in v if x > 0)
        try:
            p = stats.wilcoxon(v).pvalue
        except ValueError:
            p = float("nan")
        print("  %-14s %+7.3f %+7.3f %5d/%-3d %9.2g"
              % (s, st.median(v), st.mean(v), up, len(v), p))
    json.dump({"prompt": prompt, "n_pairs": npairs,
               "per_pair_rho": pp}, open(
                   os.path.join(RESULTS, "perpair%s_%s.json" % (VER, slug)), "w"), indent=1)


if __name__ == "__main__":
    main()
