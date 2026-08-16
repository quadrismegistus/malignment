#!/usr/bin/env python
"""L1/L2/L3 and the descriptive probes. Reads run.py's output; never queries ClickHouse.

    analyse.py            L1 (+ variants), L2, L3, descriptive probes
    analyse.py --words    also the per-word probe (needs results/word_cells.csv)

## THE ONE RULE

**This file may not touch the store.** Everything it knows comes from
`results/cells.csv` and `results/word_cells.csv`. If a test needs a column that
is not there, `run.py` must be changed and re-run, and that shows up as a diff.
An analysis therefore cannot quietly depend on something the measurement never
recorded -- which is exactly how the first L1 came to difference two quantities
computed on different prompt sets without anything in the output saying so.

## WHY THE VARIANTS ARE ALL HERE

`sft_share` decided H3 on a base-level p-value its producer never printed (its
A4). During this experiment's own adversarial pass the corrected L1, its
confidence interval, the explicit-prompt addendum and the OLMo split were each
computed in a shell heredoc and quoted into prose before being moved here.
**Arithmetic that exists only in a transcript is arithmetic nobody can
re-derive.** Every number this experiment reports is printed by this file.
"""
import argparse
import collections
import csv
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

from malignment.wordfield import paired_stats, sign_mde          # noqa: E402

RESULTS = os.path.join(HERE, "results")
CATS = ("sexual", "violent")
MIN_CHAINS = 5
MIN_PROMPTS = 3      # per chain, on whatever prompt set the variant defines


def load():
    """Everything this file knows. No ClickHouse, by rule."""
    cells = {}
    with open(os.path.join(RESULTS, "cells.csv"), encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            cells[(r["base"], r["aligned"], r["prompt_key"], r["category"])] = {
                "js": float(r["js"]), "departed": float(r["departed"]),
                "arrived": float(r["arrived"]), "n_words": int(r["n_words"]),
                "domain": r["prompt_domain"], "explicit": r["explicit"] == "1"}
    with open(os.path.join(RESULTS, "chains.csv"), encoding="utf-8") as fh:
        chains = list(csv.DictReader(fh))
    return cells, chains


def arms(cells, c, cat):
    A = {p: v for (b, al, p, k), v in cells.items()
         if b == c["base"] and al == c["sft"] and k == cat}
    B = {p: v for (b, al, p, k), v in cells.items()
         if b == c["base"] and al == c["pref"] and k == cat}
    return A, B


def chain_rows(cells, chains, variant="corrected", keep=None):
    """One row per chain.

    `corrected` puts BOTH categories on the SAME prompts -- the intersection.
    `original` reproduces the defect the adversarial pass found: each category
    on its own prompt set (195-487 for sexual, 963-1111 for violent), so the
    paired difference contrasted two different prompt populations. Kept runnable
    because a correction whose predecessor cannot be re-run is a claim about a
    number nobody can see.
    """
    out = []
    for c in chains:
        per = {cat: arms(cells, c, cat) for cat in CATS}
        sets = {}
        if variant == "corrected":
            common = set.intersection(*[set(A) & set(B) for A, B in per.values()])
            if keep:
                common = {p for p in common if keep(per["sexual"][0][p])}
            sets = {cat: common for cat in CATS}
        else:
            for cat, (A, B) in per.items():
                s = set(A) & set(B)
                if keep:
                    s = {p for p in s if keep(A[p])}
                sets[cat] = s
        row = {"base": c["base"], "sft": c["sft"], "pref": c["pref"],
               "pref_op": c["pref_op"]}
        ok = True
        for cat in CATS:
            s, (A, B) = sets[cat], per[cat]
            if len(s) < MIN_PROMPTS:
                ok = False
                break
            am = statistics.mean(A[p]["js"] for p in s)
            bm = statistics.mean(B[p]["js"] for p in s)
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
    """18 chains are 16 bases. Chains sharing a base are not independent."""
    per = collections.defaultdict(list)
    for r in rows:
        per[r["base"]].append(r["diff"])
    return {b: statistics.mean(v) for b, v in per.items()}


def report(name, rows, note="", quiet=False):
    if len(rows) < MIN_CHAINS:
        if not quiet:
            print("  %-36s UNDERPOWERED: %d chains (<%d). No p-value."
                  % (name, len(rows), MIN_CHAINS))
        return None
    d = list(by_base(rows).values())
    s = paired_stats(d)
    if not s:
        return None
    s.update({"name": name, "n_chains": len(rows), "note": note})
    if not quiet:
        print("  %-36s n=%-3d mean %+.4f  CI [%+.4f,%+.4f]  %2d/%-2d  sign p=%.4f  t=%.3f  W=%.3f"
              % (name, s["n"], s["mean"], s["ci_lo"], s["ci_hi"], s["pos"], s["n"],
                 s["sign_p"], s["t_p"] if s["t_p"] is not None else -1,
                 s["wilcoxon_p"] if s["wilcoxon_p"] is not None else -1))
    return s


def word_probe(chains):
    """Per WORD: more SFT-displaced than its own chain's transgressive baseline?

    Raw `share_w` across chains would mostly measure the CHAIN -- Amber's whole
    lexicon sits near 0.44 and Olmo-Hybrid's near 1.0 -- so each word is scored
    against its own chain's lexicon-wide share. The poolable question is "is this
    word displaced by SFT more than this model's other transgressive vocabulary".

    **Multiple testing is reported, never corrected away.** ~1,000 words are
    tested; at alpha=.05 roughly 50 clear by chance, so the count that clears is
    compared to that expectation and individual words are named as CANDIDATES.
    """
    path = os.path.join(RESULTS, "word_cells.csv")
    if not os.path.exists(path):
        print("  no results/word_cells.csv -- run: run.py --words")
        return []
    idx, meta = {}, {}
    with open(path, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            idx[(r["base"], r["aligned"], r["word"])] = float(r["js"])
            meta[r["word"]] = (r["category"], r["register"], r["cells"])
    chain_share = {}
    for c in chains:
        a = sum(v for (b, al, w), v in idx.items() if b == c["base"] and al == c["sft"])
        p = sum(v for (b, al, w), v in idx.items() if b == c["base"] and al == c["pref"])
        chain_share[(c["base"], c["pref"])] = (a / p) if p else None
    per_word = collections.defaultdict(list)
    for c in chains:
        cs_ = chain_share[(c["base"], c["pref"])]
        if not cs_:
            continue
        for w in meta:
            a = idx.get((c["base"], c["sft"], w))
            p = idx.get((c["base"], c["pref"], w))
            if a and p and p > 0:
                per_word[w].append((c["base"], a / p - cs_))
    out = []
    for w, vals in per_word.items():
        per_b = collections.defaultdict(list)
        for b, x in vals:
            per_b[b].append(x)
        d = [statistics.mean(v) for v in per_b.values()]
        if len(d) < 8:
            continue
        s = paired_stats(d)
        if not s:
            continue
        cat, reg, cells = meta[w]
        out.append({"word": w, "category": cat, "register": reg, "corpus_cells": cells,
                    "n_lineages": s["n"], "pos": s["pos"],
                    "mean_excess_share": round(s["mean"], 6),
                    "ci_lo": round(s["ci_lo"], 6), "ci_hi": round(s["ci_hi"], 6),
                    "sign_p": round(s["sign_p"], 6)})
    out.sort(key=lambda r: (r["sign_p"], -abs(r["mean_excess_share"])))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--words", action="store_true")
    a = ap.parse_args()
    cells, chains = load()
    print("  cells %d | chains %d over %d bases\n"
          % (len(cells), len(chains), len({c["base"] for c in chains})))

    rows = chain_rows(cells, chains, "corrected")
    orig = chain_rows(cells, chains, "original")
    expl = chain_rows(cells, chains, "corrected", keep=lambda v: v["explicit"])

    print("  L1 AND VARIANTS   unit = LINEAGE; sign test is REGISTERED,")
    print("                    t and Wilcoxon are UNREGISTERED and decide nothing")
    S = {}
    S["corrected"] = report("L1 corrected (both cats, same prompts)", rows, "PRIMARY")
    S["original"] = report("L1 original (defective)", orig, "each cat on its own prompts")
    S["explicit"] = report("addendum: explicit prompts only", expl, "v1 battery stimuli")
    if S["corrected"]:
        d = list(by_base(rows).values())
        S["corrected"]["mde_sign"] = sign_mde(d)
        print("\n  Sign-test MDE at n=%d: %s  -- the registered test cannot see an"
              % (S["corrected"]["n"], S["corrected"]["mde_sign"]))
        print("  effect smaller than that, which is why the CI is the quotable form.")

    print("\n  DESCRIPTIVE -- per chain, ranked. No inference.")
    for r in sorted(rows, key=lambda r: -r["diff"]):
        print("    %-28s %-5s sexual %.3f  violent %.3f  diff %+0.3f  (n=%d)"
              % (r["base"].split("/")[-1][:28], r["pref_op"], r["share_sexual"],
                 r["share_violent"], r["diff"], r["n_prompts_sexual"]))

    print("\n  DESCRIPTIVE -- family split, CHOSEN AFTER SEEING THE RANKING.")
    print("  Not a test: a subgroup found by looking. It is reported because OLMo")
    print("  is where the v1 claim was MADE, so it was always the subgroup that")
    print("  would be inspected -- which makes it a hypothesis for OTHER OLMo")
    print("  checkpoints (Think, the step ladders), not a result on these.")
    for k, sel in (("OLMo family", True), ("everything else", False)):
        sub = [r for r in rows if ("olmo" in r["base"].lower()) is sel]
        S["fam_" + k.split()[0]] = report("  " + k, sub, "POST HOC subgroup")

    byop = collections.defaultdict(list)
    for r in rows:
        byop[r["pref_op"]].append(r["diff"])
    print("\n  DESCRIPTIVE -- by preference op")
    for op, v in sorted(byop.items(), key=lambda x: -len(x[1])):
        print("    %-6s n=%-3d mean %+.4f  %d/%d positive"
              % (op, len(v), statistics.mean(v), sum(1 for x in v if x > 0), len(v)))

    doms = sorted({v["domain"] for v in cells.values() if v["domain"]})
    by_dom = []
    for dv in doms:
        rr = chain_rows(cells, chains, "corrected", keep=lambda v, d=dv: v["domain"] == d)
        s = report("", rr, quiet=True)
        if s:
            by_dom.append({"prompt_domain": dv, "n_chains": len(rr), "n_bases": s["n"],
                           "mean": round(s["mean"], 6), "pos": s["pos"],
                           "ci_lo": round(s["ci_lo"], 6), "ci_hi": round(s["ci_hi"], 6),
                           "sign_p": round(s["sign_p"], 6)})
    by_dom.sort(key=lambda r: -r["mean"])
    print("\n  L2 -- the contrast WITHIN each prompt domain. %d domains tested, so"
          % len(by_dom))
    print("       ~%.1f are expected to clear p<.05 by chance alone." % (0.05 * len(by_dom)))
    for r in by_dom:
        print("    %-16s n=%-3d mean %+8.4f  %2d/%-2d  CI [%+.3f,%+.3f]  p=%.4f"
              % (r["prompt_domain"][:16], r["n_bases"], r["mean"], r["pos"],
                 r["n_bases"], r["ci_lo"], r["ci_hi"], r["sign_p"]))

    l3 = []
    for cat in CATS:
        for tag in ("sft", "pref"):
            dep, arr, n = 0.0, 0.0, 0
            for c in chains:
                vs = [v for (b, al, p, k), v in cells.items()
                      if b == c["base"] and al == c[tag] and k == cat]
                if vs:
                    dep += statistics.mean(v["departed"] for v in vs)
                    arr += statistics.mean(v["arrived"] for v in vs)
                    n += 1
            if n:
                l3.append({"category": cat, "arm": tag, "departed": round(dep / n, 8),
                           "arrived": round(arr / n, 8), "net": round((arr - dep) / n, 8)})
    print("\n  L3 -- mass destination (mean over chains)")
    for r in l3:
        print("    %-8s %-5s departed %.6f  arrived %.6f  net %+.6f"
              % (r["category"], r["arm"], r["departed"], r["arrived"], r["net"]))

    for name, rs in (("by_chain", rows), ("by_chain_original_variant", orig),
                     ("by_chain_explicit", expl), ("by_prompt_domain", by_dom),
                     ("mass_destination", l3)):
        with open(os.path.join(RESULTS, name + ".csv"), "w", newline="",
                  encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rs[0]) if rs else ["empty"])
            w.writeheader()
            w.writerows(rs)
        print("  results/%s.csv  %d rows" % (name, len(rs)))

    if a.words:
        wr = word_probe(chains)
        if wr:
            with open(os.path.join(RESULTS, "by_word.csv"), "w", newline="",
                      encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=list(wr[0]))
                w.writeheader()
                w.writerows(wr)
            clear = [r for r in wr if r["sign_p"] < 0.05]
            print("\n  WORD PROBE -- %d words poolable (>=8 lineages)" % len(wr))
            print("    clearing p<0.05: %d   expected by chance: %.1f"
                  % (len(clear), 0.05 * len(wr)))
            for r in clear[:25]:
                print("      %-16s %-8s %-11s %2d/%-2d excess %+0.4f  p=%.4f"
                      % (r["word"], r["category"], r["register"], r["pos"],
                         r["n_lineages"], r["mean_excess_share"], r["sign_p"]))
            print("  results/by_word.csv  %d rows" % len(wr))

    with open(os.path.join(RESULTS, "summary.json"), "w", encoding="utf-8") as fh:
        json.dump(S, fh, indent=1, default=str)

    if S["corrected"]:
        s = S["corrected"]
        ok = s["sign_p"] < 0.05 and s["mean"] > 0
        print("\n  VERDICT: L1 %s  (base level decides, as registered)"
              % ("SUPPORTED" if ok else "NOT SUPPORTED"))
        if not ok:
            print("  Effect bounded to [%+.4f, %+.4f]. A null is quotable only as a"
                  % (s["ci_lo"], s["ci_hi"]))
            print("  bound, and this one excludes anything larger than ~%.2f."
                  % max(abs(s["ci_lo"]), abs(s["ci_hi"])))
            print('  Stopping rule: "SFT handles sex, DPO handles violence" is WITHDRAWN.')
    return 0


if __name__ == "__main__":
    sys.exit(main())
