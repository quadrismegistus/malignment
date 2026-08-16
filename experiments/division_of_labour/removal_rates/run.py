#!/usr/bin/env python
"""MEASURE removal rates per stage. Writes results/cells.csv; runs no test.

    run.py --push   materialise the word sets as {db}.wf_removal
    run.py          measure; writes results/cells.csv + sets.csv + chains.csv
    analyse.py      test A and B. Reads those files; never queries ClickHouse.

Registered design: `registration.md`, frozen 2026-08-16 before any rate existed.

## THE STAGES ARE THE REAL EDGES

`base -> sft` and `sft -> pref`, both measured for all 18 chains. `lexical_domains`
compared `base->sft` against `base->endpoint` and so never touched the preference
step at all -- it asked "SFT or DPO?" without measuring DPO.

## THE FIVE WORD SETS, AND WHY A WORD IS IN TWO OF THEM

    sexual    lexicon `sexual` + `both`
    violent   lexicon `violent` + `both`
    neutral   3,812 words rated `neither` by >=2 of 3 blind raters
    neutral_matched_sexual   frequency-matched subset of neutral
    neutral_matched_violent  frequency-matched subset of neutral

`rape` is in BOTH `sexual` and `violent`. In a difference that would be
double-counting; in two INDEPENDENT tests it is the true statement that rape is
sexual content and is violent content. Registration section 5: this is only
sound because A and B are never compared, which is RH's design decision.

Matching exists because the lexicon's `cells` field was wrong (a case collision
booked `rape` at 4 against a true 3,130), and once corrected the reference is
frequency-comparable to `violent` (50 vs 52 median) but NOT to `sexual` (30).
"""
import argparse
import collections
import csv
import hashlib
import json
import os
import random
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

from malignment import ch, corpus, roster                         # noqa: E402
from malignment.prompts import Prompts                    # noqa: E402
from malignment.wordfield import WordField, measure       # noqa: E402

LEXDIR = os.path.join(ROOT, "experiments", "sex_violence_lexicon", "results")
LEXICON_SHA = "d542e7e2bb86bd00"
FIELD = "removal"
RESULTS = os.path.join(HERE, "results")
SEED = 20260816
MATCH_TOL = 0.25          # registration section 4: +-25% on corpus cell count


def true_cells():
    """Case-SUMMED corpus counts. The lexicon's own `cells` was case-clobbered."""
    return {r["w"]: int(r["n"]) for r in ch.query(
        "SELECT lower(word) AS w, count() AS n FROM {db}.twp_words "
        "WHERE match(word, '^[A-Za-z]+$') GROUP BY w")}


def neutral_words():
    """Words >=2 of 3 blind raters called `neither`, excluding admitted lexicon words.

    POSITIVELY RATED NEUTRAL, not merely absent from the lexicon -- absence and
    rated-neutral are different claims, and only one of them is a measurement.
    """
    lex = json.load(open(os.path.join(LEXDIR, "lexicon.json")))
    votes = collections.defaultdict(collections.Counter)
    for fn in os.listdir(os.path.join(LEXDIR, "rated")):
        for r in json.load(open(os.path.join(LEXDIR, "rated", fn))):
            votes[r["word"]][r["category"]] += 1
    return lex, [w for w, c in votes.items()
                 if c.most_common(1)[0][0] == "neither" and c["neither"] >= 2
                 and w not in lex]


def matched(target_words, pool, cells, rng):
    """For each target word, neutral words within +-MATCH_TOL on corpus frequency.

    Sampled WITHOUT replacement so no neutral word is counted twice; a target
    with no match in tolerance contributes nothing and is counted, not silently
    dropped.
    """
    by_cells = sorted((cells.get(w, 0), w) for w in pool)
    used, out, unmatched = set(), [], 0
    for w in target_words:
        n = cells.get(w, 0)
        lo, hi = n * (1 - MATCH_TOL), n * (1 + MATCH_TOL)
        cands = [x for c, x in by_cells if lo <= c <= hi and x not in used]
        if not cands:
            unmatched += 1
            continue
        pick = rng.choice(cands)
        used.add(pick)
        out.append(pick)
    return out, unmatched


def build_sets():
    lex, neu = neutral_words()
    cells = true_cells()
    rng = random.Random(SEED)
    sexual = sorted(w for w, d in lex.items() if d["category"] in ("sexual", "both"))
    violent = sorted(w for w, d in lex.items() if d["category"] in ("violent", "both"))
    ms, us = matched(sexual, neu, cells, rng)
    mv, uv = matched(violent, neu, cells, rng)
    sets = {"sexual": sexual, "violent": violent, "neutral": sorted(neu),
            "neutral_matched_sexual": sorted(ms),
            "neutral_matched_violent": sorted(mv)}
    meta = {"unmatched_sexual": us, "unmatched_violent": uv, "cells": cells}
    return sets, meta, lex


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--push", action="store_true")
    a = ap.parse_args()

    sets, meta, lex = build_sets()
    f = WordField.from_sets(FIELD, sets, sha=LEXICON_SHA, source="sex_violence_lexicon")
    if a.push:
        print("  pushed %d (word, set) rows to {db}.%s" % (f.push(), f.table))
        for k, v in sets.items():
            print("     %-24s %5d words" % (k, len(v)))
        print("  unmatched: sexual %d, violent %d"
              % (meta["unmatched_sexual"], meta["unmatched_violent"]))
        return 0
    f.check_sha(LEXICON_SHA)

    cs = roster.chains()
    n_models, prompts = corpus.panel(verbose=True)
    print("  panel   %d prompts crossed over %d models" % (len(prompts), n_models))
    print("  chains  %d over %d lineages" % (len(cs), len({c["base"] for c in cs})))

    # BOTH REAL STAGES.
    pairs = [(c["base"], c["sft"]) for c in cs] + [(c["sft"], c["pref"]) for c in cs]
    cells = measure(pairs, f, prompts=prompts)
    print("  cells   %d (from, to, prompt, set)" % len(cells))

    dom = corpus.domains(prompts)

    os.makedirs(RESULTS, exist_ok=True)
    with open(os.path.join(RESULTS, "cells.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["from_model", "to_model", "prompt_key", "prompt_domain", "word_set",
                    "removed", "arrived", "inherited", "n_words"])
        for (fr, to, pr, setname), v in cells.items():
            w.writerow([fr, to, hashlib.sha1(pr.encode()).hexdigest()[:16],
                        dom.get(pr, ""), setname,
                        "%.10g" % v["departed"], "%.10g" % v["arrived"],
                        "%.10g" % v["inherited"], v["n_words"]])
    print("  results/cells.csv  %d rows" % len(cells))

    with open(os.path.join(RESULTS, "chains.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["base", "sft", "pref", "pref_op", "vendor"])
        w.writeheader()
        for c in cs:
            w.writerow({**{k: c[k] for k in ("base", "sft", "pref", "pref_op")},
                        "vendor": c["base"].split("/")[0]})

    # PROMPT KEY MAP. cells.csv joins on prompt_key; without this the key is an
    # orphan hash and no exemplar can be named. roster/prompts/ is public, so the
    # text ships too.
    seen = {}
    for r in ch.query("""SELECT prompt_id, prompt, domain, subdomain, language
        FROM {db}.prompts WHERE admitted AND upper(status) IN ('ACTIVE','')"""):
        seen.setdefault(r["prompt"], r)
    panel_set = set(prompts)
    with open(os.path.join(RESULTS, "prompts.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["prompt_key", "prompt_id", "domain", "subdomain", "language",
                    "in_panel", "prompt"])
        for text, r in seen.items():
            w.writerow([hashlib.sha1(text.encode()).hexdigest()[:16], r["prompt_id"],
                        r["domain"], r["subdomain"], r["language"],
                        int(text in panel_set), text])
    print("  results/prompts.csv  %d rows" % len(seen))

    # PER-WORD GRAIN, so exemplars can be named. Aggregated over the panel: the
    # per-prompt-per-word grain would be ~5M rows for no gain, since a word-level
    # exemplar is a statement about the word across the panel.
    ms = "','".join(m.replace("'", "\\'") for c in cs
                    for m in (c["base"], c["sft"], c["pref"]))
    wrows = ch.query("""
        SELECT m.base AS fr, m.aligned AS to, m.word AS word, l.label AS word_set,
               sum(if(m.delta < 0, -m.delta, 0)) AS removed,
               sum(m.p_base) AS inherited, count() AS n_prompts
        FROM {db}.movement m INNER JOIN {db}.wf_%s l ON l.word = m.word
        WHERE m.base IN ('%s') AND m.aligned IN ('%s')
          AND m.prompt IN (SELECT prompt FROM {db}.wf_panel)
        GROUP BY fr, to, word, word_set""" % (FIELD, ms, ms))
    with open(os.path.join(RESULTS, "word_cells.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["from_model", "to_model", "word", "word_set", "removed",
                    "inherited", "n_prompts"])
        for r in wrows:
            w.writerow([r["fr"], r["to"], r["word"], r["word_set"],
                        "%.10g" % r["removed"], "%.10g" % r["inherited"], r["n_prompts"]])
    print("  results/word_cells.csv  %d rows" % len(wrows))

    with open(os.path.join(RESULTS, "sets.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["word_set", "word", "corpus_cells"])
        for k, ws in sets.items():
            for word in ws:
                w.writerow([k, word, meta["cells"].get(word, 0)])
    print("  results/sets.csv, results/chains.csv")

    with open(os.path.join(HERE, "population.json"), "w", encoding="utf-8") as fh:
        json.dump({"lexicon_sha": LEXICON_SHA, "seed": SEED, "match_tol": MATCH_TOL,
                   "panel_prompts": len(prompts), "panel_models": n_models,
                   "n_chains": len(cs), "n_lineages": len({c["base"] for c in cs}),
                   "set_sizes": {k: len(v) for k, v in sets.items()},
                   "unmatched_sexual": meta["unmatched_sexual"],
                   "unmatched_violent": meta["unmatched_violent"],
                   "chains": [{k: c[k] for k in ("base", "sft", "pref", "pref_op")}
                              for c in cs]}, fh, indent=1, ensure_ascii=False)
    print("\n  MEASUREMENT ONLY. Run analyse.py for A and B.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
