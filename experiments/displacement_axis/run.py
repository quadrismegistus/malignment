#!/usr/bin/env python
"""dN and its decomposition, per (lineage, item), with the words that carried it.

    python experiments/displacement_axis/run.py                 # pilot, declared pairs in v4
    python experiments/displacement_axis/run.py --limit 20      # first 20 items
    python experiments/displacement_axis/run.py --domain identity

## THE QUESTION

Alignment is said to DISPLACE transgressive mass into permitted substitutes --
`kill` drains, `scream` fills. That is a claim about specific words, and `dN`
alone cannot test it, because `dN` is a single signed number over the whole
distribution. This writes the decomposition and the per-word contributions so
the claim can be checked rather than assumed.

## dN IS THE LEAST INFORMATIVE NUMBER IN THE OUTPUT

`Axis.split` returns `suppression` (mass LEAVING, weighted by where it left) and
`substitution` (mass ARRIVING, weighted by where it landed). Their SIGNS
separate cases `dN` conflates. Verified on synthetic distributions
(2026-08-18), moving known mass on `She was so furious she wanted to`:

    kill 0.05->0.01, scream 0.05->0.09   dN -0.0170  supp -0.0087  subs -0.0083
    kill 0.05->0.01, nothing else        dN -0.0087  supp -0.0087  subs  0
    scream 0.05->0.09, nothing else      dN -0.0083  supp  0       subs -0.0083
    scream -> cry, INSIDE the nice pole  dN -0.0001  supp +0.0083  subs -0.0084

**Displacement puts both components NEGATIVE. Churn within one pole puts them
OPPOSITE, with a dN near zero.** A pilot on three items found the second
pattern, not the first, on the item whose `dN` looked strongest -- which is the
`shoes` case `split`'s own docstring warns about, where redistribution inside
one pole nets to nothing while looking like an effect.

So `signature` is written on every row and is the column to read first.

## PAIRS COME FROM `roster.endpoints()`, NOT FROM THE MODEL NAMES IN THE STORE

A first pass paired checkpoints by eye from `twp_words_v4` and produced ten
"lineages" of which two were not declared: `CT-LLM-Base` and `neo_7b` were each
given TWO endpoints, their SFT arm as well as their declared one. `endpoints()`
maps one base to exactly one endpoint by construction, so base->SFT and
base->DPO are two STAGES of one lineage rather than two lineages, and reading
them as peers conflates a stage comparison with a lineage comparison.

`endpoints()` is the declared frame and this asks it. Pairs where either arm is
missing from the corpus are reported as skipped, with the arm named.

## SIGN DISAGREEMENT IS A REFUSAL

`split` emits `dN` and `dN_renorm` under two conventions that can point opposite
ways once the arms' scored masses differ, which they do -- malign measured
aligned `T` above base `T` in 39 of 50 pairs, p = 9.0e-05. Where they disagree
the cell is NOT QUOTABLE on dN and `sign_disagree` says so on the row. Rows are
written anyway; filtering them out here would hide how often it happens.

## WHAT IT WRITES

    results/cells.jsonl      one row per (base, endpoint, item_id)
    results/words.jsonl      one row per (base, endpoint, item_id, word) with
                             p_base, p_aligned, dP, s (axis score), contribution
    results/skipped.jsonl    pairs or items not measured, with the reason

Per-word rows are the point: `contribution = dP(w) * s(w)` sums exactly to `dN`,
so any cell's number can be traced to the words that produced it, and a cell
whose dN rests on one word is visible as such.

## IT RUNS NO CHECKPOINT AND NEEDS NO SERVER

Reads `twp_words_v4` for both arms and imports `slot_axis.Axis` directly.

An earlier draft went through the running server's `/slot/axis` route, out of
habit from the authoring loop. That was wrong twice over: it made a batch job
depend on a server lifecycle (it died mid-smoke-test when the server was
restarted), and it paid an HTTP round trip per cell to reach a module already
importable. `slot_axis`'s own docstring is explicit that it exists to be the
SINGLE implementation -- the archive had three copies that drifted -- so the
module is the thing to call and the route is a convenience wrapper for the app.

bge itself loads on CPU and the vectors are cached, so a re-run costs no
embedding. Nothing here loads a language-model checkpoint.
"""
import argparse
import collections
import json
import os
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")
#: v4 because the slot corpus lives there and nowhere else. The v3 table answers
#: a query for these prompts with 2 rows of 279 -- a well-formed answer from the
#: wrong corpus, which is how this was nearly run against the wrong instrument.
TABLE = "twp_words_v4"


def signature(supp, subs, eps=1e-6):
    """Name the pattern the two components make. -> str

    The whole reason this file exists. See the module docstring for the
    synthetic verification of each case.
    """
    if abs(supp) < eps and abs(subs) < eps:
        return "flat"
    if supp < 0 and subs < 0:
        return "displacement"          # mass leaves naughty AND arrives at nice
    if supp < 0 and abs(subs) < eps:
        return "suppression"           # leaves, nothing arrives
    if abs(supp) < eps and subs < 0:
        return "arrival"               # arrives, nothing left
    if (supp > 0) != (subs > 0):
        return "churn"                 # opposite signs: redistribution in a pole
    return "reverse"                   # both positive: movement toward naughty


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--domain", default=None, help="restrict to one domain")
    ap.add_argument("--limit", type=int, default=None, help="first N items")
    ap.add_argument("--out", default=RESULTS,
                    help="run directory; give each run its OWN (results/pilot1, ...)")
    ap.add_argument("--force", action="store_true",
                    help="overwrite a run directory that already holds a manifest")
    a = ap.parse_args(argv)

    #: **A RUN DIRECTORY IS WRITE-ONCE UNLESS SAID OTHERWISE.** The population is
    #: DISCOVERED (`endpoints()` intersected with the models present in the
    #: store), not declared, so re-running after an ingest silently produces a
    #: different population at the same path under the same name -- and the
    #: files open with mode "w". `pilot1` was measured against a store holding 8
    #: of 50 declared pairs; the SmolLM3 arms the poles were balanced on were
    #: not in it. Nothing in the output would have said so.
    #:
    #: The guard fires on `manifest.json` rather than on the directory being
    #: non-empty, because a half-written run leaves cells.jsonl behind and
    #: should be re-runnable without a flag.
    if os.path.exists(os.path.join(a.out, "manifest.json")) and not a.force:
        print("refusing: %s already holds a manifest.json. Give this run its own\n"
              "          --out (results/<name>), or pass --force to replace it."
              % a.out, file=sys.stderr)
        return 2

    from malignment import roster, vectors as V
    from malignment.slots import read_items, corpora

    ep, unresolved = roster.endpoints()
    items = [d for _, p in corpora() for d in read_items(p) if not d.get("quarantined")]
    if a.domain:
        items = [d for d in items if (d.get("domain") or "") == a.domain]
    if a.limit:
        items = items[:a.limit]
    prompts = sorted({d["prompt"] for d in items})

    rows = V.rows("SELECT prompt, model, groupArray(word) AS ws, groupArray(p) AS ps "
                  "FROM %s WHERE prompt IN {ps:Array(String)} GROUP BY prompt, model"
                  % TABLE, ps=prompts)
    store = collections.defaultdict(dict)
    for r in rows:
        store[r["prompt"]][r["model"]] = dict(zip(r["ws"], r["ps"]))

    #: **THE LEAK BOUND IS NOT OPTIONAL AND `split` SAYS SO OUT LOUD.** Omitting
    #: the residuals returns dN with no bound and emits a warning -- the guard is
    #: active rather than a `None` field, on the reasoning in `_leak`: "a consumer
    #: that ignores a None does so silently".
    #:
    #: `twp_cells.total` IS the residual, verified rather than assumed:
    #: cells.total 0.24342 + summed word mass 0.75658 = 1.000000 exactly, on three
    #: checkpoints. It decomposes as `tail + drop`. The name reads like "total
    #: mass" and means its complement, which is worth one query to check before
    #: passing it into a bound.
    cell_rows = V.rows("SELECT prompt, model, total FROM twp_cells_v4 "
                       "WHERE prompt IN {ps:Array(String)}", ps=prompts)
    residual = collections.defaultdict(dict)
    for r in cell_rows:
        residual[r["prompt"]][r["model"]] = r["total"]

    have = {m for per in store.values() for m in per}
    pairs = [(b, e) for b, e in sorted(ep.items()) if b in have and e in have]
    skipped_pairs = [(b, e, "base absent" if b not in have else "endpoint absent")
                     for b, e in sorted(ep.items()) if not (b in have and e in have)]
    print("items %d | prompts %d | declared pairs %d | measurable pairs %d"
          % (len(items), len(prompts), len(ep), len(pairs)), flush=True)

    os.makedirs(a.out, exist_ok=True)
    fc = open(os.path.join(a.out, "cells.jsonl"), "w", encoding="utf-8")
    fw = open(os.path.join(a.out, "words.jsonl"), "w", encoding="utf-8")
    fs = open(os.path.join(a.out, "skipped.jsonl"), "w", encoding="utf-8")
    for b, e, why in skipped_pairs:
        fs.write(json.dumps({"kind": "pair", "base": b, "endpoint": e, "reason": why}) + "\n")

    from malignment.slot_axis import Axis, separates

    n_cells = 0
    sig = collections.Counter()
    per_pair = collections.Counter()
    per_domain = collections.Counter()
    cells_skipped = collections.Counter()
    items_seen = set()
    prompts_seen = set()
    for d in items:
        per = store.get(d["prompt"]) or {}
        #: **THE AXIS IS BUILT ONCE PER ITEM, NOT ONCE PER CELL.** It depends on
        #: the prompt and the poles and on nothing the checkpoints supply, so
        #: rebuilding it per lineage would re-resolve the same vectors N times.
        ax = Axis(d["prompt"], list(d["naughty"]), list(d["nice"]))
        if not ax.ok:
            fs.write(json.dumps({"kind": "item", "item_id": d["item_id"],
                                 "reason": "degenerate axis"}) + "\n")
            continue
        for b, e in pairs:
            if b not in per or e not in per:
                fs.write(json.dumps({"kind": "cell", "item_id": d["item_id"], "base": b,
                                     "endpoint": e, "reason": "prompt not measured on this arm"}) + "\n")
                cells_skipped["prompt not measured on this arm"] += 1
                continue
            pb, pa = per[b], per[e]
            words = sorted(set(pb) | set(pa))
            probs = {w: (pb.get(w, 0.0) + pa.get(w, 0.0)) / 2 for w in words}
            S = ax.score(words)
            #: **PER-ARM, NOT POOLED.** An earlier draft called `stats()` on the
            #: mean of the two distributions, which is a quantity belonging to
            #: neither checkpoint. N and leverage are properties of one arm.
            stb = ax.stats(pb, S)
            sta = ax.stats(pa, S)
            rp = (residual.get(d["prompt"]) or {})
            sp = ax.split(pb, pa, S,
                          residual_pre=rp.get(b), residual_post=rp.get(e))
            sep_ok, gap, correct, total = separates(S, list(d["naughty"]), list(d["nice"]))
            #: `split.contributions` covers the WHOLE vocabulary. The payload's
            #: separate `scores` field is TAGGED WORDS ONLY -- verified 2026-08-18
            #: by sending 16 words and getting 10 back -- and using it here would
            #: have silently limited the per-word rows to the words already
            #: assumed to matter, which is the opposite of the question.
            contrib = {c["word"]: c for c in (sp.get("contributions") or [])}
            g = signature(sp.get("suppression") or 0.0, sp.get("substitution") or 0.0)
            sig[g] += 1
            fc.write(json.dumps({
                "item_id": d["item_id"], "prompt": d["prompt"],
                "domain": d.get("domain"), "matched_set": d.get("matched_set"),
                "base": b, "endpoint": e,
                "dN": sp.get("dN"), "dN_renorm": sp.get("dN_renorm"),
                "suppression": sp.get("suppression"), "substitution": sp.get("substitution"),
                "sign_disagree": sp.get("sign_disagree"), "signature": g,
                "base_scored_mass": sp.get("base_scored_mass"),
                "post_scored_mass": sp.get("post_scored_mass"),
                #: The aperture travels with the number, per Finding N's
                #: registration: the per-cell bound is a COMPANION COLUMN beside
                #: the primary, not a footnote.
                "leak_worst": sp.get("leak_worst"),
                "leak_matched_floor": sp.get("leak_matched_floor"),
                "residual_base": rp.get(b), "residual_endpoint": rp.get(e),
                "movers": sp.get("movers"),
                #: **ALIGNMENT DOES TWO THINGS AND THEY ARE REPORTED SEPARATELY**
                #: (RH, 2026-08-18). It CONCENTRATES the distribution -- aligned
                #: scored mass exceeds base in 79% of cells here, median dT
                #: +0.0442 -- and it SHIFTS where that mass sits. `dN` multiplies
                #: the two together (T_post*N_post - T_base*N_base), which is why
                #: the same cell can read as displacement or its opposite
                #: depending on convention. Separated, the ambiguity does not
                #: arise: dT is the aperture, dN_renorm is the position.
                #:
                #: The objection to renormalising is that T is post-treatment.
                #: That is right and is not a reason to avoid it -- concentration
                #: is an EFFECT to report, not a nuisance to divide away. Asking
                #: where a distribution concentrates requires normalising out how
                #: much it concentrated.
                "N_base": stb.get("N"), "N_aligned": sta.get("N"),
                "dN_position": (sta.get("N") - stb.get("N"))
                               if (sta.get("N") is not None and stb.get("N") is not None) else None,
                "T_base": sp.get("base_scored_mass"), "T_aligned": sp.get("post_scored_mass"),
                "dT": ((sp.get("post_scored_mass") or 0) - (sp.get("base_scored_mass") or 0)),
                "leverage_base": stb.get("leverage"), "leverage_aligned": sta.get("leverage"),
                "separates": bool(sep_ok), "gap": gap,
                "purity": stb.get("purity"), "flags": stb.get("flags"),
                "n_words": len(words),
            }) + "\n")
            #: Per-word rows. `contribution` sums to `dN` exactly, so a cell
            #: resting on one word is visible rather than inferred.
            for w, c in contrib.items():
                fw.write(json.dumps({
                    "item_id": d["item_id"], "base": b, "endpoint": e, "word": w,
                    "p_base": pb.get(w, 0.0), "p_aligned": pa.get(w, 0.0),
                    "dP": c["dP"], "s": c["s"], "contribution": c["c"],
                    "pole": ("naughty" if w in d["naughty"]
                             else "nice" if w in d["nice"] else None),
                }) + "\n")
            n_cells += 1
            per_pair[(b, e)] += 1
            per_domain[d.get("domain")] += 1
            items_seen.add(d["item_id"])
            prompts_seen.add(d["prompt"])
            if n_cells % 25 == 0:
                print("  %d cells" % n_cells, flush=True)
    for f in (fc, fw, fs):
        f.close()

    #: **THE POPULATION IS RECORDED BY ENUMERATION, NOT BY A COUNT** (RH,
    #: 2026-08-18). "8 of 50 declared pairs" is a fact about the store on one
    #: day and reads as a fact about the design; the next reader compares run
    #: names and gets no signal that the populations differ. So the manifest
    #: names every pair RUN and every pair NOT run with its reason, and the two
    #: sum to the declared frame. Compare `pairs_run`, never the run name.
    #:
    #: `n_cells` per pair is in here because coverage is UNEVEN -- pilot1 ranges
    #: 209 to 290 of 290 items across its eight pairs -- so any corpus-wide
    #: proportion is over an unbalanced panel and the manifest is where that is
    #: visible without reloading the cells.
    import datetime
    manifest = {
        "run": os.path.basename(os.path.normpath(a.out)),
        "measured_on": datetime.date.today().isoformat(),
        "note": ("The population is FROZEN here by enumeration. run.py discovers pairs by "
                 "intersecting roster.endpoints() with the models present in the source "
                 "table, so a later run against a larger store is a different population "
                 "under the same code. Compare pairs_run, not run names."),
        "source_table": TABLE,
        "residual_table": "twp_cells_v4",
        "code_commit": _git_head(),
        "restrictions": {"domain": a.domain, "limit": a.limit},
        "declared_pairs": len(ep),
        "pairs_run": [{"base": b, "endpoint": e, "n_cells": n}
                      for (b, e), n in sorted(per_pair.items())],
        "pairs_not_run": [{"base": b, "endpoint": e, "reason": why}
                          for b, e, why in skipped_pairs],
        "n_cells": n_cells,
        "n_items": len(items_seen),
        "n_prompts": len(prompts_seen),
        "signatures": dict(sig.most_common()),
        "domains": dict(per_domain.most_common()),
        "cells_skipped": dict(cells_skipped.most_common()),
        "files": {"cells.jsonl": "one row per (base, endpoint, item_id)",
                  "skipped.jsonl": "pairs, items and cells NOT measured, with reasons",
                  "words.jsonl": "one row per (cell, word); GITIGNORED, working tree only"},
    }
    with open(os.path.join(a.out, "manifest.json"), "w", encoding="utf-8") as f:
        f.write(json.dumps(manifest, indent=2) + "\n")

    print("\ncells %d" % n_cells)
    for k, v in sig.most_common():
        print("  %-14s %5d  %4.0f%%" % (k, v, 100.0 * v / max(n_cells, 1)))
    print("\npairs run %d of %d declared:" % (len(per_pair), len(ep)))
    for (b, e), n in sorted(per_pair.items()):
        print("  %-38s -> %-38s %4d" % (b, e, n))
    print("\nwrote %s" % a.out)
    return 0


def _git_head():
    """Commit of the working tree, or None. Records WHICH CODE produced a run.

    Best-effort by design: an experiment folder should not fail to write its
    manifest because git is unavailable, and a null here is honest about not
    knowing rather than absent and unremarked.
    """
    import subprocess
    try:
        r = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                           text=True, cwd=os.path.dirname(os.path.abspath(__file__)))
        return r.stdout.strip() or None
    except Exception:
        return None


if __name__ == "__main__":
    sys.exit(main())
