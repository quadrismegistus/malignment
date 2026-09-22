"""THE Chinese population filter for `twp` cells. Import, do not re-derive.

    from twp_population import measurable, twp_legible, twp_contrast_models

`population.py` filters PASSAGES. This filters CELLS, and the two cannot share a
rule because they are different measurements: a passage is ~100 words of free
generation that a judge can read, a twp cell is one next-word distribution. A
model can put well-formed mass on a single Chinese continuation and still write
incoherent Chinese over a paragraph, so `population.zh_fluent()` is a STRICTER
bar than a twp analysis needs, and using it costs most of the roster.

## THE THREE TIERS, AND WHICH QUESTION EACH ANSWERS

    measurable()            38 of 50 lineages   the cell exists and is Chinese
    twp_legible()           see below           its top mass is Chinese WORDS
    contrast_models()       5 of 50 lineages    the model writes Chinese prose
    (from population.py)

Use `measurable()` where the claim is about the shape of a distribution and the
words need not mean anything -- coverage, conservation, whether a cell is there.
Use `twp_legible()` for displacement direction, faller/riser counts, JS. Use
`population.contrast_models()` for any claim about what the Chinese MEANS.

## WHY THE TIER MATTERS, WITH THE NUMBER THAT FORCED IT

On `她非常生气，她想要` ("She was so angry she wanted to"), contextual `k_zh`
means over the arms, the transgressiveness result INVERTS with the population:

    39 measurable      (tier A)  -0.036   20 up / 19 down     a null
    11 twp-legible     (tier B)  +0.057    8 up /  3 down
     5 passage-fluent  (tier C)  +0.274    5 up /  0 down     unanimous

The 28 lineages in the first row and not the second emit Chinese function words
because their tokenizer covers them, not because they model Chinese. Pooling
them does not add noise to a real effect; it produces the opposite sign.

**TIER B IS A MIDDLE AND NOT A SUBSTITUTE FOR TIER C.** It recovers the SIGN on
the three scales that invert -- transgressiveness +0.057, charge +0.105, valence
-0.011 against tier A's -0.036 / +0.040 / +0.047 -- at a fifth to a third of
tier C's magnitude and without its unanimity. On `concreteness` it agrees with
tier A (-0.140) against tier C (+0.023). So B is the right population for a
claim about direction over a usable n, and C remains the only one for a claim
about what the Chinese means.

## THE STATISTIC

`lex_share(model)` = the share of each cell's TOP-20 mass carried by words that
are (a) at least two characters, (b) CJK, and (c) present in SUBTLEX-CH.
Averaged over every Chinese prompt the model has a cell for.

**Two characters is doing real work.** The failure mode this exists to catch is a
model emitting single characters that are individually valid and jointly
meaningless -- AmberSafe's aligned top-10 on the anger prompt is 知道 告 保 道
向, beaver-7b's is 多多 自 能 学 为 通过. A one-character test passes both.

**NOT the jieba dictionary**, though it is tempting because `fields._zh_words()`
is the very list `twp` segmented with and its digest is part of RULE_VERSION.
That list is maximal by design -- 583,275 entries including 告, 保, 自, 多多 --
so it admits exactly the fragments above. Measured against the judged arms the
three candidates are indistinguishable (spearman 0.796 subtlex / 0.784 jieba /
0.785 either, best Youden J 0.84 for all three), so the choice was made on what
each list IS rather than on a difference in fit.

## CALIBRATION, AGAINST THE JUDGED ARMS

`population.fluency_rates()` covers 48 of the 100 endpoint models. Against the
binary label `judged >= FLUENT_MIN`:

    spearman(lex_share, judged % fluent) = 0.796   over 48 arms

    thr    sens   spec      J
    0.36   1.00   0.76   0.76
    0.40   0.93   0.82   0.75
    0.42   0.93   0.91   0.84      <- LEGIBLE_MIN
    0.44   0.50   0.94   0.44

    leave-one-out accuracy 40/48 = 0.83

**THE CUTOFF SITS ON A CLIFF AND THAT IS THE MAIN CAVEAT.** Seven judged-fluent
arms lie in [0.42, 0.44), so sensitivity falls 0.93 -> 0.50 across two points of
threshold. 0.42 is where Youden's J peaks and it is NOT robust; a re-calibration
on different prompts could reasonably land at 0.40 or 0.36. Pass `threshold=`
rather than treating the default as a property of the world, and if an analysis
turns on which side of the line a lineage falls, report it at two thresholds.

Four arms are misclassified at 0.42, and two of the four are boundary cases of
the LABEL rather than of the measure:

    Falcon3-7B-Instruct       lex 0.393  judged 20%   (label is exactly at the cut)
    neo_7b_instruct_v0.1      lex 0.475  judged 15%   (label just under it)
    MiniCPM5-1B-Base          lex 0.426  judged  0%
    Llama-3.1-8B-Instruct     lex 0.458  judged  0%

The last two are the honest false positives: both place well-formed Chinese
words on a single continuation and neither sustains a paragraph.

## THE CACHE IS REQUIRED, AND ITS ABSENCE RAISES

`lex_share` needs one ClickHouse query per model, so the values live in
`twp_zh_legibility.json` beside this file. A missing cache RAISES rather than
returning an empty mapping, because an empty mapping makes every model fail the
filter and a population of zero is a result. Rebuild with

    python twp_population.py --rebuild

which re-reads the catalogue and the store and rewrites the file with its own
provenance block.
"""

import collections
import json
import os
import re
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "twp_zh_legibility.json")

CJK = re.compile(r"[一-鿿]")

#: Calibrated above. Youden-optimal and, as the docstring says, on a cliff.
LEGIBLE_MIN = 0.42
#: Tier A. `mass` is the measured word mass of the cell; `cjk` the share of that
#: mass on CJK surfaces. Both are properties of the CELL, not of the tokenizer,
#: which is why `cjk_tier` is not used anywhere in this module -- it is a count
#: of characters in the vocabulary, and Llama-3.1-8B is PARTIAL while carrying
#: the highest measured Chinese mass in the roster.
MASS_MIN = 0.35
CJK_MIN = 0.90
#: **A MEAN OVER ONE CELL IS NOT A MODEL PROPERTY**, and without this floor
#: CroissantLLM passes tier B at 0.63/0.69 -- computed over the single Chinese
#: prompt its tokenizer did not mangle, out of 407. The share of the Chinese
#: population a model must actually carry before its mean means anything.
#: The cut is not delicate: cell counts across the roster are 1 (x2), 69 (x3),
#: 227, 311, 406, 407 (x89), so anything in (0.17, 0.55) selects the same 95.
#: Raise it to 1.0 where two models must be compared on identical prompts --
#: the 69-cell models carry only the prompts with no full-width comma, which is
#: a biased subset and not a random one.
MIN_COVERAGE = 0.5
#: The rank the statistic is computed over. Twenty because the failure it must
#: catch is visible in the head of the distribution; a deeper cut drowns it in
#: the tail every model has.
TOPK = 20


class MissingCache(Exception):
    """The legibility cache is not on disk. Not the same as 'no model passes'."""


def _cache():
    if not os.path.exists(CACHE):
        raise MissingCache(
            "%s is absent. Run `python %s --rebuild`. Refusing to return an "
            "empty mapping: every model would then fail every filter here and "
            "the resulting population of zero would look like a measurement."
            % (CACHE, os.path.basename(__file__)))
    with open(CACHE, encoding="utf-8") as fh:
        return json.load(fh)


def lex_share(model=None):
    """{model: share}, or one model's share. Raises if the cache is absent."""
    d = _cache()["models"]
    if model is None:
        return {m: v["lex_share"] for m, v in d.items()}
    r = d.get(model)
    return None if r is None else r["lex_share"]


def cell_stats(model=None):
    """{model: {mass, cjk, n_prompts}} -- the tier-A inputs, as measured."""
    d = _cache()["models"]
    if model is None:
        return {m: {k: v[k] for k in ("mass", "cjk", "n_prompts")}
                for m, v in d.items()}
    return d.get(model)


def coverage(model=None):
    """{model: share of the Chinese prompt population with a cell}."""
    d = _cache()
    n = d["_provenance"]["n_zh_prompts"]
    out = {m: v["n_prompts"] / n for m, v in d["models"].items()}
    return out if model is None else out.get(model)


def measurable(mass_min=MASS_MIN, cjk_min=CJK_MIN, min_coverage=MIN_COVERAGE):
    """TIER A. Models whose Chinese cells exist and are Chinese. -> set

    A model absent from the cache has not been measured and is NOT measurable:
    absence is not a passing grade. Croissant, Teuken and the Tanuki DPO arm are
    present but thin for a different reason again -- their tokenizers refused
    most of the prompts at produce time, recorded per prompt in the runner
    shard's `skipped.jsonl` under `prompt_does_not_survive_encoding` -- and
    `min_coverage` is what stops their surviving handful being averaged into a
    number that looks like every other model's.
    """
    d = _cache()["models"]
    n = _cache()["_provenance"]["n_zh_prompts"]
    return {m for m, v in d.items()
            if v["n_prompts"] / n >= min_coverage
            and v["mass"] >= mass_min and v["cjk"] >= cjk_min}


def twp_legible(threshold=LEGIBLE_MIN, **kw):
    """TIER B. Models whose top mass is Chinese WORDS. -> set

    Tier A is a precondition, not an alternative: a cell with 0.14 of its mass
    measured can still put most of that fraction on dictionary words, and the
    share would then describe a rounding error. SmolLM2-360M is the case --
    lex_share 0.33 over a measured mass of 0.139.
    """
    return {m for m in measurable(**kw) if lex_share(m) >= threshold}


def twp_contrast_models(threshold=LEGIBLE_MIN, **kw):
    """TIER B, BOTH ARMS. -> [(base, aligned)]

    The same argument `population.contrast_models()` makes one instrument up: a
    lineage whose arms differ in COMPETENCE gives an arm contrast that measures
    the competence gap. bloom -> bloomz is the extreme (0.48 -> 0.00, the
    aligned arm answers in English) and it is exactly the lineage that carried
    the largest js_total in the roster.
    """
    from malignment import roster
    eps, unresolved = roster.endpoints()
    if unresolved:
        raise ValueError("%d lineages unresolved: %s -- resolve before taking "
                         "'the endpoints'" % (len(unresolved),
                                              sorted(unresolved)[:3]))
    ok = twp_legible(threshold, **kw)
    return sorted((b, a) for b, a in eps.items() if b in ok and a in ok)


def describe(threshold=LEGIBLE_MIN):
    """What each tier keeps, so a caller can print the population it used."""
    from malignment import roster
    eps, _ = roster.endpoints()
    A, B = measurable(), twp_legible(threshold)
    C = twp_contrast_models(threshold)
    return {
        "lineages": len(eps),
        "measurable_models": len(A),
        "legible_models": len(B),
        "legible_lineages_both_arms": len(C),
        "measurable_lineages_both_arms":
            len([1 for b, a in eps.items() if b in A and a in A]),
        "threshold": threshold,
        "built": _cache()["_provenance"]["built"],
    }


# --------------------------------------------------------------- rebuild

def rebuild(topk=TOPK, verbose=True):
    """Recompute every model's statistic from the catalogue and the store.

    One ClickHouse query per model, top-`topk` rows per cell via a window
    function. Writes the cache with its own provenance so a later reader can
    tell which prompts and which rank cut produced these numbers.
    """
    import datetime
    from malignment import ch, fields, roster
    from malignment.ch import _lit
    from malignment.prompts import Prompts

    zh = sorted({p._row["prompt"] for p in Prompts.all(admitted=None)
                 if p._row.get("language") == "zh"})
    ps = ",".join(_lit(t) for t in zh)
    eps, _ = roster.endpoints()
    models = sorted({m for pair in eps.items() for m in pair})

    seen = {}

    def is_word(w):
        if w not in seen:
            seen[w] = bool(len(w) >= 2 and CJK.search(w)
                           and fields.freq(w, lang="zh") is not None)
        return seen[w]

    out = {}
    for m in models:
        rows = ch.query(
            "SELECT prompt, word, p FROM (SELECT prompt, word, p, row_number() "
            "OVER (PARTITION BY prompt ORDER BY p DESC) rn "
            "FROM {db}.twp_words_v4_best WHERE model=%s AND prompt IN (%s)) "
            "WHERE rn<=%d" % (_lit(m), ps, topk))
        head = collections.defaultdict(lambda: [0.0, 0.0])
        for r in rows:
            head[r["prompt"]][0] += r["p"]
            if is_word(r["word"]):
                head[r["prompt"]][1] += r["p"]
        cells = ch.query(
            "SELECT prompt, total FROM {db}.twp_cells_v4_best "
            "WHERE model=%s AND prompt IN (%s)" % (_lit(m), ps))
        #: `total` is the four-way RESIDUAL, so the measured word mass is its
        #: complement. Taken from the cell rather than summed over the words,
        #: because the words above are truncated at `topk`.
        mass = [1.0 - r["total"] for r in cells]
        allw = ch.query(
            "SELECT word, sum(p) s FROM {db}.twp_words_v4_best "
            "WHERE model=%s AND prompt IN (%s) GROUP BY word" % (_lit(m), ps))
        tot = sum(r["s"] for r in allw) or 1.0
        cjk = sum(r["s"] for r in allw if CJK.search(r["word"])) / tot
        shares = [ok / t for t, ok in head.values() if t > 0]
        out[m] = {
            "lex_share": round(st.mean(shares), 4) if shares else 0.0,
            "mass": round(st.mean(mass), 4) if mass else 0.0,
            "cjk": round(cjk, 4),
            "n_prompts": len(shares),
        }
        if verbose:
            print("%-52s lex=%.3f mass=%.3f cjk=%.2f n=%d"
                  % (m[-52:], out[m]["lex_share"], out[m]["mass"],
                     out[m]["cjk"], out[m]["n_prompts"]), flush=True)

    doc = {
        "_provenance": {
            "what": "Per-model Chinese legibility for twp cells. See "
                    "twp_population.py for the calibration.",
            "built": datetime.date.today().isoformat(),
            "producer": "twp_population.rebuild",
            "topk": topk,
            "n_zh_prompts": len(zh),
            "membership": "len>=2 and CJK and present in SUBTLEX-CH "
                          "(fields.freq(w, lang='zh'))",
            "source_table": "twp_words_v4_best / twp_cells_v4_best",
            "calibrated_against": "population.fluency_rates(), 48 endpoint arms",
        },
        "models": out,
    }
    with open(CACHE, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1, sort_keys=True)
    return doc


def calibrate(threshold=None):
    """Re-run the sweep in the docstring. Returns the table, prints nothing.

    Kept so the numbers above are reproducible rather than remembered, and so a
    future prompt population can be checked against the same criterion instead
    of inheriting a constant whose derivation has been lost.
    """
    sys.path.insert(0, HERE)
    import population as POP
    share = lex_share()
    rates = POP.fluency_rates()
    lab = [(share[m], rates[m] >= POP.FLUENT_MIN, m) for m in share if m in rates]
    rows = []
    for i in range(10, 90):
        t = i / 100.0
        tp = sum(1 for s, y, _ in lab if s >= t and y)
        fp = sum(1 for s, y, _ in lab if s >= t and not y)
        fn = sum(1 for s, y, _ in lab if s < t and y)
        tn = sum(1 for s, y, _ in lab if s < t and not y)
        sens = tp / (tp + fn) if tp + fn else 0.0
        spec = tn / (tn + fp) if tn + fp else 0.0
        rows.append({"threshold": t, "tp": tp, "fp": fp, "fn": fn, "tn": tn,
                     "sens": sens, "spec": spec, "youden": sens + spec - 1})
    if threshold is not None:
        return [r for r in rows if abs(r["threshold"] - threshold) < 1e-9][0]
    return {"n_judged_arms": len(lab), "rows": rows,
            "best": max(rows, key=lambda r: r["youden"])}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--rebuild", action="store_true",
                    help="recompute the cache from the store (one query/model)")
    ap.add_argument("--calibrate", action="store_true",
                    help="print the threshold sweep against the judged arms")
    ap.add_argument("--threshold", type=float, default=LEGIBLE_MIN)
    a = ap.parse_args()
    if a.rebuild:
        rebuild()
    if a.calibrate:
        c = calibrate()
        print("judged arms: %d" % c["n_judged_arms"])
        print("%6s %4s %4s %4s %4s %6s %6s %6s"
              % ("thr", "TP", "FP", "FN", "TN", "sens", "spec", "J"))
        for r in c["rows"]:
            if r["threshold"] * 100 % 2 == 0 and 0.20 <= r["threshold"] <= 0.60:
                print("%6.2f %4d %4d %4d %4d %6.2f %6.2f %6.2f"
                      % (r["threshold"], r["tp"], r["fp"], r["fn"], r["tn"],
                         r["sens"], r["spec"], r["youden"]))
        print("best J=%.2f at %.2f" % (c["best"]["youden"], c["best"]["threshold"]))
    if not (a.rebuild or a.calibrate):
        print(json.dumps(describe(a.threshold), indent=1))
