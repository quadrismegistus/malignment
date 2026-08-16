#!/usr/bin/env python
"""Producer for L1-L3 and the descriptive probes: division of labour on WORDS.

    run.py --push       materialise the frozen lexicon as {db}.wf_sexviolence
    run.py [--words]    MEASURE. Writes results/cells.csv (+ word_cells.csv).
    analyse.py          TEST. Reads those files; never touches ClickHouse.

## WHY MEASUREMENT AND ANALYSIS ARE SEPARATE FILES

The measurement is a 54M-row join that takes minutes; the tests are instant. On
2026-08-16 the L1 analysis was revised three times in one session -- a prompt-set
defect, an explicit-prompt subset, a family split -- and each revision re-ran the
join to recompute numbers that had not changed.

The rule that makes the split real rather than cosmetic: **analyse.py may not
query ClickHouse.** If a test needs a column, the measurement must be re-run and
that appears as a diff. An analysis therefore cannot quietly depend on something
the measurement never recorded. It is the rule `plot.py` already follows.

This does not multiply producers: run.py is still the only producer of
measurement, and analysis variants are flags on analyse.py.

Every number this experiment reports is produced HERE. Nothing is computed in a
shell heredoc and quoted into prose. `sft_share` decided H3 on a p-value its own
producer never printed (see its A4), and during this experiment's own second
pass the corrected L1, the confidence interval, the explicit-prompt addendum and
the OLMo split were all likewise computed outside the file before being moved
in. **Arithmetic that only exists in a transcript is arithmetic nobody can
re-derive**, and a transcript is not an artifact.

## L1 IS COMPUTED ON THE INTERSECTION, AND THE DEFECTIVE FORM IS KEPT

The first run took, for each category, the prompts where that category appears
on both arms -- 195-487 prompts for `sexual` and 963-1111 for `violent`. The
paired difference then contrasted two quantities measured on 3-5x different
prompt populations, while SFT share is known to vary strongly by prompt domain.
`--variant original` reproduces it, because a correction whose predecessor
cannot be re-run is a claim about a number nobody can see.
"""
import argparse
import collections
import csv
import hashlib
import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def _repo_root(start):
    d = start
    while d != os.path.dirname(d):
        if os.path.isdir(os.path.join(d, "malignment")):
            return d
        d = os.path.dirname(d)
    raise RuntimeError("no malignment/ above %s" % start)


ROOT = _repo_root(HERE)
sys.path.insert(0, ROOT)

from malignment import ch, roster                                   # noqa: E402
from malignment.prompts import Prompts                              # noqa: E402
from malignment.wordfield import (WordField, measure, conservation,  # noqa: E402
                                  paired_stats, sign_mde, JS_TERM)

LEXICON = os.path.join(ROOT, "experiments", "sex_violence_lexicon",
                       "results", "lexicon.json")
LEXICON_SHA = "d542e7e2bb86bd00"
FIELD = "sexviolence"
CATS = ("sexual", "violent")
MIN_PROMPTS = 20          # A1: per chain, on the contrast's own prompt set
MIN_CHAINS = 5
RESULTS = os.path.join(HERE, "results")


def field():
    return WordField.from_lexicon(FIELD, LEXICON, key="category")


def panel():
    """Prompts held by EVERY model in the pairs population AND declared live.

    THE STATUS GATE IS APPLIED HERE, NOT ASSUMED. Building the panel from
    `twp_words` alone takes whatever was measured, which is not the declared
    population: it admitted `f11_reason_BOTH`, whose status is
    `MIXED: ACTIVE/DISPUTED` and which `Prompts.all()` excludes. One prompt of
    1,760 -- but the defect is that the panel was defined by measurement history
    rather than by the declaration, and a seat struck that prompt for a reason.

    Not "all prompts" either: prompt sets are fleet-defined and do not nest, so
    the universal intersection over all 402 measured models is ONE prompt; over
    the 154 in `pairs` it is 2,190.
    """
    live = {p.text for p in Prompts.all()}
    n = ch.scalar("""SELECT count(DISTINCT m) FROM (
        SELECT base AS m FROM {db}.pairs UNION DISTINCT SELECT aligned FROM {db}.pairs)""")
    rows = ch.query("""SELECT prompt FROM {db}.twp_words
        WHERE model IN (SELECT base FROM {db}.pairs UNION DISTINCT SELECT aligned FROM {db}.pairs)
        GROUP BY prompt HAVING count(DISTINCT model) = %d""" % n)
    crossed = [r["prompt"] for r in rows]
    kept = [p for p in crossed if p in live]
    if len(kept) != len(crossed):
        print("  panel: %d crossed, %d dropped by the status gate"
              % (len(crossed), len(crossed) - len(kept)))
    return n, kept


def explicit_prompts():
    """The v1 battery's explicit stimuli -- the prompts the ORIGINAL claim was made on.

    English only: the `_zh` variants exist but the lexicon is English and cannot
    read them, so including them would score Chinese prompts as having no
    sexual or violent vocabulary, which is an instrument gap, not a measurement.
    """
    return {r["prompt"] for r in ch.query("""SELECT prompt FROM {db}.prompts
        WHERE admitted AND upper(status) IN ('ACTIVE','')
          AND prompt_id LIKE '%explicit%' AND prompt_id NOT LIKE '%_zh'""")}


def arms(cells, c, cat):
    A = {p: v["js"] for (b, al, p, k), v in cells.items()
         if b == c["base"] and al == c["sft"] and k == cat}
    B = {p: v["js"] for (b, al, p, k), v in cells.items()
         if b == c["base"] and al == c["pref"] and k == cat}
    return A, B


def chain_rows(cells, cs, variant="corrected", restrict=None):
    """One row per chain. `corrected` puts BOTH categories on the same prompts.

    `original` reproduces the defect: each category on its own prompt set. Kept
    runnable so the correction is checkable rather than asserted.
    """
    out = []
    for c in cs:
        per = {cat: arms(cells, c, cat) for cat in CATS}
        if variant == "corrected":
            common = set.intersection(*[set(A) & set(B) for A, B in per.values()])
            if restrict is not None:
                common &= restrict
            sets = {cat: common for cat in CATS}
        else:
            sets = {cat: (set(A) & set(B)) if restrict is None
                    else (set(A) & set(B) & restrict) for cat, (A, B) in per.items()}
        row = {"base": c["base"], "sft": c["sft"], "pref": c["pref"],
               "pref_op": c["pref_op"]}
        ok = True
        for cat in CATS:
            s = sets[cat]
            A, B = per[cat]
            if len(s) < 3:
                ok = False
                break
            am = statistics.mean(A[p] for p in s)
            bm = statistics.mean(B[p] for p in s)
            if not bm:
                ok = False
                break
            row["n_prompts_" + cat] = len(s)
            row["js_sft_" + cat] = round(am, 8)
            row["js_pref_" + cat] = round(bm, 8)
            row["share_" + cat] = round(am / bm, 6)
        if ok:
            row["diff"] = round(row["share_sexual"] - row["share_violent"], 6)
            out.append(row)
    return out


def by_base(rows):
    """Collapse chains to their base. 18 chains are 16 bases; they are not independent."""
    per = collections.defaultdict(list)
    for r in rows:
        per[r["base"]].append(r["diff"])
    return {b: statistics.mean(v) for b, v in per.items()}


def report(name, rows, note=""):
    if len(rows) < MIN_CHAINS:
        print("  %-34s UNDERPOWERED: %d chains (<%d). No p-value." % (name, len(rows), MIN_CHAINS))
        return None
    d = list(by_base(rows).values())
    s = paired_stats(d)
    if not s:
        return None
    s["name"], s["n_chains"], s["note"] = name, len(rows), note
    s["mde_sign"] = sign_mde(d)
    print("  %-34s n=%-3d mean %+.4f  CI [%+.4f, %+.4f]  %d/%d  sign p=%.4f  t=%.3f  W=%.3f"
          % (name, s["n"], s["mean"], s["ci_lo"], s["ci_hi"], s["pos"], s["n"],
             s["sign_p"], s["t_p"] or -1, s["wilcoxon_p"] or -1))
    return s


def word_probe(cs, prompts, lex):
    """Per WORD: is it consistently more SFT-displaced than its chain's baseline?

    `share_w` for one chain is js_w(base->sft)/js_w(base->endpoint) summed over
    the panel. Comparing raw `share_w` across chains would mostly measure the
    chain (Amber's whole lexicon sits near 0.44, Olmo-Hybrid's near 1.0), so
    each word is scored against ITS OWN CHAIN's lexicon-wide share. The question
    is then "is this word displaced by SFT more than this model's other
    transgressive vocabulary", which is the question that can be pooled.

    **Multiple testing is unavoidable here and is reported, not corrected away.**
    ~1,000 words are tested; at alpha=0.05 roughly 50 clear by chance, so the
    count of clearing words is compared against that expectation and individual
    words are named only as candidates.
    """
    ms = "','".join(m.replace("'", "\\'") for c in cs
                    for m in (c["base"], c["sft"], c["pref"]))
    rows = ch.query("""
        SELECT m.base AS base, m.aligned AS aligned, m.word AS word,
               sum(%s) AS js, count() AS n_prompts
        FROM {db}.movement m
        INNER JOIN {db}.wf_%s l ON l.word = m.word
        WHERE m.base IN ('%s') AND m.aligned IN ('%s')
          AND m.prompt IN (SELECT prompt FROM {db}.wf_panel)
        GROUP BY base, aligned, word""" % (JS_TERM % {"a": "m"}, FIELD, ms, ms))
    idx = {(r["base"], r["aligned"], r["word"]): r["js"] for r in rows}
    chain_share = {}
    for c in cs:
        a = sum(v for (b, al, w), v in idx.items() if b == c["base"] and al == c["sft"])
        p = sum(v for (b, al, w), v in idx.items() if b == c["base"] and al == c["pref"])
        chain_share[(c["base"], c["pref"])] = (a / p) if p else None
    per_word = collections.defaultdict(list)
    for c in cs:
        cshare = chain_share[(c["base"], c["pref"])]
        if not cshare:
            continue
        for w in lex:
            a = idx.get((c["base"], c["sft"], w))
            p = idx.get((c["base"], c["pref"], w))
            if a and p and p > 0:
                per_word[w].append((c["base"], a / p - cshare))
    out = []
    for w, vals in per_word.items():
        per_b = collections.defaultdict(list)
        for b, x in vals:
            per_b[b].append(x)
        d = [statistics.mean(v) for v in per_b.values()]
        if len(d) < 8:                       # needs most lineages to be poolable
            continue
        s = paired_stats(d)
        if not s:
            continue
        out.append({"word": w, "category": lex[w]["category"],
                    "register": lex[w].get("register", ""), "cells": lex[w]["cells"],
                    "n_lineages": s["n"], "pos": s["pos"],
                    "mean_excess_share": round(s["mean"], 6),
                    "ci_lo": round(s["ci_lo"], 6), "ci_hi": round(s["ci_hi"], 6),
                    "sign_p": round(s["sign_p"], 6)})
    out.sort(key=lambda r: r["sign_p"])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--push", action="store_true")
    ap.add_argument("--words", action="store_true",
                    help="also write the per-word grain (bigger, slower)")
    a = ap.parse_args()

    f = field()
    if a.push:
        print("  pushed %d words to {db}.%s" % (f.push(), f.table))
        return 0
    f.check_sha(LEXICON_SHA)

    cs = roster.chains()
    n_models, prompts = panel()
    print("  panel   %d prompts crossed over %d models" % (len(prompts), n_models))
    print("  chains  %d over %d distinct bases" % (len(cs), len({c["base"] for c in cs})))
    con = conservation((cs[0]["base"], cs[0]["sft"]), prompts)
    if con:
        print("  conservation vs movement_cells: %d prompts, worst |diff| %.2e" % con)

    cells = measure([(c["base"], c["sft"]) for c in cs]
                    + [(c["base"], c["pref"]) for c in cs], f, prompts=prompts)

    os.makedirs(RESULTS, exist_ok=True)
    dom = {}
    for p in Prompts.all():
        dv = (p._row.get("domain") or "").strip()
        if dv:
            dom.setdefault(p.text, dv)
    expl = explicit_prompts()

    # THE FINEST GRAIN MEASURED. analyse.py reads this and nothing else, so an
    # analysis cannot depend on a column the measurement did not record.
    path = os.path.join(RESULTS, "cells.csv")
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        # PROMPT IDENTITY AS A HASH, FOR SIZE. An earlier version of this
        # comment claimed the text could not be published because the repo is
        # public -- that is WRONG: `roster/prompts/` is tracked, 39 files, the
        # battery verbatim, deliberately, because a stimulus nobody can read is
        # not reproducible. The real reason is bulk: 67,655 rows x prompt text
        # is ~14MB against ~5MB. Join on `prompt_key`, look the text up in
        # roster/prompts when you need it.
        w.writerow(["base", "aligned", "prompt_key", "prompt_domain", "explicit",
                    "category", "js", "departed", "arrived", "n_words"])
        for (b, al, pr, cat), v in cells.items():
            w.writerow([b, al, hashlib.sha1(pr.encode()).hexdigest()[:16],
                        dom.get(pr, ""), int(pr in expl), cat,
                        "%.10g" % v["js"], "%.10g" % v["departed"],
                        "%.10g" % v["arrived"], v["n_words"]])
    print("  results/cells.csv  %d rows" % len(cells))

    # THE KEY MAP. cells.csv joins on `prompt_key`, so without this the key is
    # an orphan hash: no prompt_id, no subdomain, no language, nothing to label
    # a point with. A join key you do not ship is a column nobody can use.
    # The text is included -- roster/prompts/ is already tracked and public,
    # because a stimulus nobody can read is not reproducible.
    seen = {}
    for r in ch.query("""SELECT prompt_id, prompt, domain, subdomain, language
        FROM {db}.prompts WHERE admitted AND upper(status) IN ('ACTIVE','')"""):
        seen.setdefault(r["prompt"], r)
    with open(os.path.join(RESULTS, "prompts.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["prompt_key", "prompt_id", "domain", "subdomain", "language",
                    "explicit", "in_panel", "prompt"])
        panel_set = set(prompts)
        for text, r in seen.items():
            w.writerow([hashlib.sha1(text.encode()).hexdigest()[:16], r["prompt_id"],
                        r["domain"], r["subdomain"], r["language"],
                        int(text in expl), int(text in panel_set), text])
    print("  results/prompts.csv  %d rows" % len(seen))

    # FAMILY on the chain table, so nobody has to string-match a model id. The
    # OLMo subgroup was first computed with `"lmo" in base`, which is
    # case-sensitive and silently found 4 of 6 (OLMo-2 and OLMoE do not match).
    nodes = roster.load().get("nodes") or {}
    with open(os.path.join(RESULTS, "chains.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["base", "sft", "pref", "pref_op",
                                           "family", "vendor"])
        w.writeheader()
        for c in cs:
            fams = (nodes.get(c["base"]) or {}).get("family") or []
            w.writerow({**{k: c[k] for k in ("base", "sft", "pref", "pref_op")},
                        "family": ";".join(fams),
                        "vendor": c["base"].split("/")[0]})
    print("  results/chains.csv  %d rows" % len(cs))

    if a.words:
        ms = "','".join(m.replace("'", "\\'") for c in cs
                        for m in (c["base"], c["sft"], c["pref"]))
        rows = ch.query("""
            SELECT m.base AS base, m.aligned AS aligned, m.word AS word,
                   sum(%s) AS js, count() AS n_prompts
            FROM {db}.movement m
            INNER JOIN {db}.wf_%s l ON l.word = m.word
            WHERE m.base IN ('%s') AND m.aligned IN ('%s')
              AND m.prompt IN (SELECT prompt FROM {db}.wf_panel)
            GROUP BY base, aligned, word""" % (JS_TERM % {"a": "m"}, FIELD, ms, ms))
        lex = json.load(open(LEXICON))
        with open(os.path.join(RESULTS, "word_cells.csv"), "w", newline="",
                  encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["base", "aligned", "word", "category", "register", "cells", "js", "n_prompts"])
            for r in rows:
                d = lex.get(r["word"], {})
                w.writerow([r["base"], r["aligned"], r["word"], d.get("category", ""),
                            d.get("register", ""), d.get("cells", ""),
                            "%.10g" % r["js"], r["n_prompts"]])
        print("  results/word_cells.csv  %d rows" % len(rows))

    with open(os.path.join(HERE, "population.json"), "w", encoding="utf-8") as fh:
        json.dump({"lexicon_sha": LEXICON_SHA, "field": FIELD,
                   "panel_prompts": len(prompts), "panel_models": n_models,
                   "n_chains": len(cs),
                   "n_distinct_bases": len({c["base"] for c in cs}),
                   "chains": [{k: c[k] for k in ("base", "sft", "pref", "pref_op")}
                              for c in cs],
                   "categories": list(CATS)}, fh, indent=1, ensure_ascii=False)
    print("\n  MEASUREMENT ONLY. Run analyse.py for L1/L2/L3 and the probes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
