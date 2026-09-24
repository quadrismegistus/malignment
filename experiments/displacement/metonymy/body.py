"""The word-level metonymy test on the body-part scenes, on an existing contextual ruler.
-> results/body_words.csv, results/body.md

    python -u body.py

RH, 2026-09-24: does the garment result (the riser sits further out) hold where the
slot takes a BODY PART? The ruler is not built here. `slot_ratings/sexual` rates
every (prompt, word) IN CONTEXT with instrument `sexual_slot_en_v2`, and two of its
scales are the ruler:

    body_distance  0 = not applicable (action, state, manner; EXCLUDED), then
                   1 = the genitals ... 7 = off the body.   out = +body_distance
    genitality     1 = no relation ... 7 = names the genitals. out = -genitality

A word enters only if its rating is `ratable` and not `is_modifier` (as
`slot_ratings/sexual` drops modifiers) and, for body_distance, not 0.

THE TEST IS `run.py`'s WORD-LEVEL TEST, UNCHANGED: unit = the word, statistic =
the median of its per-lineage delta (percentage points) over the endpoint
lineages that carry it, admitted at >= MIN_CARRIERS carriers; Spearman of `out`
against that median, per prompt. Positive rho is the prediction.

THE PROMPT SET IS A RULE, NOT A LIST: every English prompt the instrument rated
whose slot is a possessive (ends in " his" or " her"). A prompt is TESTED if >= 10
words are admitted, reported otherwise. The took-off frames qualify by the rule
and have 8 rated words; they are served by `run.py` on scale D.

AGGREGATION. Gender-swapped prompts share a scene and most of a vocabulary, so a
sign test over prompts overcounts. Both are reported: over prompts, and over
SCENES (a scene's rho = the mean of its prompts' rhos; the scene key removes
She/He, his/her, him/her).

WHAT WAS SEEN FIRST, stated because it bounds what this is. A quick uncommitted
pass on 14 hand-picked body-part prompts (same statistic, same ruler) had been
looked at before this file was written: body_distance positive on 12 of 14. The
rule above was written after that, so this is the committed version of an effect
already glimpsed, not an independent test. EXPLORATORY, like the rest of this folder.

NO NON-SEXUAL CONTROL. The instrument's population holds no non-sexual scene
whose slot takes a body part ("held his" in a hospice, "blood poured from his"),
so a general alignment preference for hands and faces is NOT excluded here.
"""
import collections, csv, os, re, statistics as st, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", ".."))
INSTRUMENT = "sexual_slot_en_v2"
MIN_CARRIERS = 10
MIN_WORDS = 10
RULERS = {"body_distance": +1, "genitality": -1}
PRON = re.compile(r"\b(She|He|she|he|his|her|him|himself|herself)\b")


def ruler(idx):
    """{prompt: {word: {scale: out}}} for every rated, ratable, non-modifier word."""
    out = collections.defaultdict(dict)
    for (pr, w), by in idx.items():
        g = by.get(INSTRUMENT)
        if not g or not g.get("ratable") or g.get("is_modifier"):
            continue
        v = {}
        bd = g.get("body_distance")
        if isinstance(bd, (int, float)) and bd > 0:
            v["body_distance"] = RULERS["body_distance"] * bd
        gn = g.get("genitality")
        if isinstance(gn, (int, float)):
            v["genitality"] = RULERS["genitality"] * gn
        if v:
            out[pr][w] = v
    return out


def main():
    from scipy.stats import binomtest, spearmanr
    from malignment import ch, fields as F, roster
    R = ruler(F._slot_index())
    prompts = sorted(p for p in R if re.search(r" (his|her)$", p) and p.isascii())
    eps, unresolved = roster.endpoints()
    if unresolved:
        raise SystemExit("unresolved lineages")
    pairs = {(b, a) for b, a in eps.items()}
    rows, res = [], []
    for p in prompts:
        q = ("SELECT base, aligned, word, p_base, p_aligned FROM {db}.movement_v4 "
             "WHERE frame_base='' AND frame_aligned='' AND prompt='%s'" % p.replace("'", "\\'"))
        d = collections.defaultdict(list)
        lin = set()
        for r in ch.query(q, limit_bytes=None):
            if (r["base"], r["aligned"]) in pairs:
                lin.add((r["base"], r["aligned"]))
                d[r["word"]].append(100.0 * (float(r["p_aligned"]) - float(r["p_base"])))
        for w, ds in d.items():
            if len(ds) < MIN_CARRIERS or w not in R[p]:
                continue
            rows.append({"prompt": p, "word": w, "n_carriers": len(ds),
                         "median_delta_pp": "%+.5f" % st.median(ds),
                         **{"out_" + s: R[p][w].get(s, "") for s in RULERS}})
        for s in RULERS:
            g = [r for r in rows if r["prompt"] == p and r["out_" + s] != ""]
            if len(g) >= MIN_WORDS:
                rho, pv = spearmanr([r["out_" + s] for r in g], [float(r["median_delta_pp"]) for r in g])
            else:
                rho, pv = float("nan"), float("nan")
            res.append({"prompt": p, "scale": s, "n": len(g), "rho": rho, "p": pv, "lineages": len(lin)})
    with open(os.path.join(HERE, "results", "body_words.csv"), "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(rows[0]))
        wr.writeheader(); wr.writerows(rows)

    L = ["# The word-level metonymy test on the body-part scenes", "",
         "Producer `body.py`. Ruler: `%s` (slot_ratings/sexual), rated in context; `out` = +body_distance, "
         "-genitality, HIGH = further from the genitals. Word = unit, median per-lineage delta over >= %d "
         "carrying endpoint lineages (movement_v4, raw frame, 50 endpoints). Prompts by rule: every English "
         "rated prompt ending in \" his\"/\" her\"; tested at >= %d admitted words. Positive rho = prediction. "
         "Exploratory; an uncommitted 14-prompt glimpse preceded it (see docstring). No non-sexual control."
         % (INSTRUMENT, MIN_CARRIERS, MIN_WORDS), "",
         "| prompt | lineages | body_distance n | rho | p | genitality n | rho | p |", "|---|---|---|---|---|---|---|---|"]
    by = collections.defaultdict(dict)
    for r in res:
        by[r["prompt"]][r["scale"]] = r
    fmt = lambda r: ("%d | %+.3f | %.2g" % (r["n"], r["rho"], r["p"])) if r["rho"] == r["rho"] else "%d | -- | --" % r["n"]
    for p in prompts:
        L.append("| %s | %d | %s | %s |" % (p, by[p]["body_distance"]["lineages"],
                                            fmt(by[p]["body_distance"]), fmt(by[p]["genitality"])))
    L += ["", "## Aggregate", "", "| scale | unit | tested | rho > 0 | p (two-sided sign) | median rho |", "|---|---|---|---|---|---|"]
    for s in RULERS:
        t = [r for r in res if r["scale"] == s and r["rho"] == r["rho"]]
        scenes = collections.defaultdict(list)
        for r in t:
            scenes[PRON.sub("_", r["prompt"])].append(r["rho"])
        for unit, vals in (("prompt", [r["rho"] for r in t]), ("scene", [st.fmean(v) for v in scenes.values()])):
            pos = sum(v > 0 for v in vals)
            L.append("| %s | %s | %d | %d | %.2g | %+.3f |" % (
                s, unit, len(vals), pos, binomtest(pos, len(vals)).pvalue if vals else float("nan"),
                st.median(vals) if vals else float("nan")))
    open(os.path.join(HERE, "results", "body.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    sys.exit(main())
