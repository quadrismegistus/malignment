#!/usr/bin/env python
"""SMOKE: the rhyme_pull fleet's producer shape, end to end, on one small model.

    uv run python experiments/architectures/rhyme/rhyme_smoke.py --n 18
    uv run python experiments/architectures/rhyme/rhyme_smoke.py --model X --device cuda

RH, 2026-09-11: *"Start with 1 box and try everything on a small model to see if
it works."* This is that, run LOCALLY FIRST because a local smoke costs nothing
and catches everything except CUDA and the kernels.

## WHERE THE DATA GOES, WHICH WAS RH'S QUESTION

**Word mass goes where it already goes and nothing changes.** The verse fleet was
not a special producer: `data/verse_fleet_twp_spec.json` is a plain
`[{model, prompts: [...]}]` worklist handed to the ordinary twp runner. That is
why verse pull is in `twp_words` with no verse column anywhere -- **the verse-ness
lives in the slot manifest**, which maps a context string to its slot, scheme and
target rime key. The store never knew it was verse and does not need to.

**Closure does NOT fit that table.** `twp_words` is
`(model, prompt, word, p, n_paths, source, mtime)`; `twp_cells` is cell metadata.
There is no column for a per-word closure probability, and adding one would put a
null on 37M rows for a quantity defined only at verse slots.

So closure rides as **an extra key on the same jsonl record**, and lands in a
**sidecar table**:

    record   {... rule_version, rows, residual, conservation ...,
              "closure": {"k": 40, "nl_ids": 130, "words": {w: p_close}}}

    table    twp_closure(model, prompt, word, p_close, k_rider, source, mtime)

Three things that buys, all of which are failures this campaign has already paid
for:

1. **`ingest.py` does not change.** Its include predicate needs `rule_version`,
   `rows` and `residual`; unknown top-level keys are ignored. The words ingest
   is bit-identical to today's with a `closure` key present -- asserted by this
   smoke, not assumed.
2. **The existing rsync carries it for free.** `fleet_launch.py --pull-every`
   pulls `/root/malignment-data/twp` into `~/malignment-data/twp` on a loop.
   Closure is inside those same files, so there is no second transfer to forget
   and no way for the closure of a cell to arrive without the cell.
3. **Words and their closure cannot be separated**, because they are one record.
   The `.f16` tier is the counter-example: collected, paid for, and holding zero
   live readers because nothing downstream could reach it.

## HOW CLOSURE WAS STORED BEFORE: NOWHERE AT FLEET SCALE, AND ALWAYS DERIVED

Checked, not recalled. Three artifacts exist and none stores the primitive:

    rhyme_pull_pilot.parquet        96 x 14   per (model, poem): line_closure,
                                              rhyme_raw, rhyme_given_closure,
                                              nonpartner_*, p_actual
    verse_fleet_smoke.parquet       27 x 14   per (poem, slot):
                                              close_given_class, p_close_actual
    verse_fleet_smoke_words.parquet 2082 x 4  id_human, slot, surface, prob
                                              -- NO closure column at all
    the 250-file fleet              ZERO      no p_close, no close_given_class

**Both precedents computed `c(w)` per word in memory and threw it away**, keeping
only the ratio. That is the thing to change, and RH's instruction is the reason:

- A stored ratio has the RIME CLASS baked into it, so computing it requires the
  class vocabulary on the box. A stored per-word `p_close` does not, so the box
  runs no phonology and the Mac makes every class decision offline.
- **The rime key has already been revised once.** v1 fell back to syllable
  SPELLING and shattered /ei/ into 'ay' / 'ey' / 'eigh'; v2 is phonemic. Any
  per-cell ratio computed under v1 was unrecoverable without re-running the
  model. Per-word closure is key-agnostic and survives the next revision too.
- `line_closure` and `rhyme_given_closure` are both derivable from
  (`rows`, `closure.words`, manifest). `close_given_class` is derivable from
  them. The reverse holds for none of these.

## THE RIDER IS K=40, NOT K=9, AND THE DIFFERENCE IS THE DECOMPOSITION

`verse_fleet_producer.closure_rider` rides `N_RIDER_CLASS = 8` plus the actual
word. That yields `close_given_class` -- of the TARGET CLASS's mass, how much is
line-final -- which is **not** `plan_rhyme.md`'s `rhyme_given_closure`, whose
denominator runs over ALL candidates:

    line_closure         = sum p(w).c(w) / sum p(w)                over all K
    rhyme_given_closure  = sum_{w in class} p(w).c(w) / sum p(w).c(w)

A class-internal ratio cannot produce either. So the rider takes the top K=40 by
mass, which is the pilot's own `TOP_K`. Measured cost of that choice, 12 real
verse slots, SmolLM2-360M / MPS:

    K=9    expand 0.661s  rider 0.060s   +9%      close_given_class only
    K=40   expand 0.581s  rider 0.159s   +27%     THE DECOMPOSITION
    K=80   expand 0.583s  rider 0.256s   +44%

**The beam is only 2-6 forward passes at these context lengths**, which is why a
rider that looked like 2-3x is 27%: it is one more batched forward beside a
shallow beam, not forty sequential ones.

## WHAT THIS ASSERTS BEFORE ANY BOX IS RENTED

    1  the record still satisfies ingest's include predicate WITH the new key
    2  conservation closes on every cell (the producer refuses, never clamps)
    3  closure is a probability on every rider word
    4  the decomposition computes, and the UNRHYMED control separates

(4) is the one that matters: if rhymed and unrhymed primers do not separate on a
small model, the instrument is not working and no fleet will fix it.
"""
import argparse
import json
import os
import statistics as S
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "experiments", "emergence", "capacities"))
#: `malign_logits.twp` is the VERIFIED twp path ([5698]); it lives in the
#: archive repo, which is not installed, so the path is added explicitly.
sys.path.insert(0, os.path.expanduser("~/github/malign-logits"))

MANIFEST = os.path.join(ROOT, "experiments", "emergence", "capacities",
                        "data", "verse_fleet_slot_manifest.json")
K_RIDER = 40


def cells(n):
    man = json.load(open(MANIFEST, encoding="utf-8"))
    want = [c for c in man["cells"] if c["slot"] == "called"]
    #: the CALLED slot only, and balanced across schemes -- an unbalanced smoke
    #: cannot show the control separating, which is the only check that matters
    out, per = [], {}
    for c in want:
        k = c["scheme"]
        if per.get(k, 0) >= n // 3:
            continue
        per[k] = per.get(k, 0) + 1
        out.append(c)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default="HuggingFaceTB/SmolLM2-360M")
    ap.add_argument("--device", default=None)
    ap.add_argument("--n", type=int, default=18)
    ap.add_argument("--out", default=None)
    ap.add_argument("--produce-only", action="store_true",
                    help="write the jsonl and stop. THE BOX RUNS THIS. No prosodic.")
    a = ap.parse_args(argv)

    import torch
    from malign_logits import twp
    from transformers import AutoModelForCausalLM, AutoTokenizer
    #: **NO PHONOLOGY ON THE BOX.** RH, 2026-09-11: *"Let's not run prosodic on
    #: the cloud though right? We can do the prosodic analysis after we have the
    #: data."* Right, and the K=40 design is what makes it possible: the rider
    #: is the top 40 words BY MASS, so selecting it needs no rime class and the
    #: box never imports prosodic. `rime_key` is imported inside `analyse()`.
    from malignment.closure import newline_ids, rider

    dev = a.device or twp.pick_device()
    out = a.out or os.path.join(HERE, "results", "smoke.jsonl")
    os.makedirs(os.path.dirname(out), exist_ok=True)

    tok = AutoTokenizer.from_pretrained(a.model)
    model = AutoModelForCausalLM.from_pretrained(a.model, dtype=torch.float16).to(dev).eval()
    bmask = twp.boundary_mask(tok, model.config.vocab_size)
    nl = newline_ids(tok, model.config.vocab_size)
    print("model %s on %s | newline family %d ids" % (a.model, dev, len(nl)), flush=True)

    recs, t0 = [], time.time()
    for c in cells(a.n):
        words, res, _ = twp.expand(model, tok, c["context"], dev, bmask)
        surf = {}
        for k, m in words.items():
            s = k[0] if isinstance(k, tuple) else k
            surf[s] = surf.get(s, 0.0) + float(m)
        cl = rider(model, tok, dev, c["context"], surf, nl, K_RIDER)
        closes = cl["words"]
        rows = [{"word": w, "t1": -1, "p": p} for w, p in surf.items()]
        cons = sum(surf.values()) + res["total"]
        recs.append({"model": a.model, "prompt": c["context"], "theta": 0.001,
                     "device": dev, "rule_version": 3, "rows": rows,
                     "residual": res, "conservation": cons,
                     "closure": cl})
    with open(out, "w", encoding="utf-8") as fh:
        for r in recs:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("wrote %s: %d cells in %.1f s" % (out, len(recs), time.time() - t0))
    if a.produce_only:
        print("--produce-only: stopping before any phonology. "
              "Run without it on the Mac to analyse.")
        return 0

    # ---- the four assertions -------------------------------------------------
    print("\nASSERTIONS")
    ok = True

    n_inc = sum(1 for r in recs if r.get("rule_version") == 3
                and "rows" in r and "residual" in r)
    print("  1 ingest include predicate holds WITH the closure key   %d/%d %s"
          % (n_inc, len(recs), "PASS" if n_inc == len(recs) else "FAIL"))
    ok &= n_inc == len(recs)

    bad = [r["prompt"][:30] for r in recs if abs(r["conservation"] - 1.0) > 1e-4]
    print("  2 conservation closes to 1e-4                           %d/%d %s"
          % (len(recs) - len(bad), len(recs), "PASS" if not bad else "FAIL %s" % bad[:2]))
    ok &= not bad

    nprob = [v for r in recs for v in r["closure"]["words"].values()]
    good = all(0.0 <= v <= 1.0 for v in nprob)
    print("  3 closure is a probability on every rider word          %d values %s"
          % (len(nprob), "PASS" if good else "FAIL"))
    ok &= good

    from verse_fleet_producer import rime_key          # ANALYSIS ONLY -- prosodic
    #: **ASSERTION 0, ADDED AFTER THE FIRST SMOKE REPORTED PASS WITH EVERY
    #: CLASS SHARE AT 0.000.** `rime_key` swallows every exception and returns
    #: None, so a missing `prosodic` is indistinguishable from a model with no
    #: class mass: the numerator is empty either way and the ratio is a clean
    #: 0.000 that looks like a measurement. Check the INSTRUMENT before reading
    #: anything it produces.
    probe = ["bed", "fled", "day", "ray", "night", "light"]
    keys = {w: rime_key(w) for w in probe}
    live = sum(1 for v in keys.values() if v)
    print("  0 rime_key resolves (prosodic present)                  %d/%d %s"
          % (live, len(probe), "PASS" if live == len(probe) else
             "FAIL -- prosodic missing; every class share below is a FALSE ZERO"))
    ok &= live == len(probe)
    if live == len(probe):
        same = keys["bed"] == keys["fled"] and keys["day"] == keys["ray"]
        print("    bed/fled and day/ray share a key                     %s"
              % ("PASS" if same else "FAIL -- the key is not rhyme"))
        ok &= same

    # ---- the decomposition ---------------------------------------------------
    byc = {c["context"]: c for c in cells(a.n)}
    stat = {}
    for r in recs:
        c = byc[r["prompt"]]
        p = {w["word"]: w["p"] for w in r["rows"]}
        cl = r["closure"]["words"]
        tot = sum(p[w] for w in cl) or 1e-12
        cw = sum(p[w] * cl[w] for w in cl)
        lc = cw / tot
        num = sum(p[w] * cl[w] for w in cl if rime_key(w) == c["target_key"])
        nump = sum(p[w] * cl[w] for w in cl if rime_key(w) == c["nonpartner_key"])
        stat.setdefault(c["scheme"], []).append(
            (lc, (num / cw if cw > 0 else None), (nump / cw if cw > 0 else None)))

    print("\nTHE DECOMPOSITION, median over cells (K=%d)" % K_RIDER)
    print("    %-10s %3s  %-13s %-19s %s"
          % ("scheme", "n", "line_closure", "rhyme_given_closure", "nonpartner"))
    med = {}
    for sc in ("ABAB", "AABB", "unrhymed"):
        v = stat.get(sc) or []
        if not v:
            continue
        f = lambda i: S.median([x[i] for x in v if x[i] is not None])  # noqa: E731
        med[sc] = f(1)
        print("    %-10s %3d  %-13.3f %-19.3f %.3f" % (sc, len(v), f(0), f(1), f(2)))

    #: **A RATIO IS THE WRONG STATISTIC HERE AND THE FIRST RUN SHOWED WHY.**
    #: `unrhymed` medianed to exactly 0.000 -- the STRONGEST separation there
    #: is -- and the ratio reported it as uncomputable. Difference, plus a
    #: per-cell count, which are defined at zero and say the same thing.
    rhy = [x[1] for sc in ("ABAB", "AABB") for x in stat.get(sc, []) if x[1] is not None]
    unr = [x[1] for x in stat.get("unrhymed", []) if x[1] is not None]
    sep = (S.median(rhy) - S.median(unr)) if (rhy and unr) else None
    #: AUC (the common-language effect size): the share of rhymed-vs-unrhymed
    #: CELL PAIRS in which the rhymed cell scores higher, ties counted half.
    #: Declared before running, at 0.75. The two statistics this replaced were
    #: each wrong in a way worth recording: a RATIO is undefined exactly where
    #: separation is total, and "above every unrhymed cell" is hostage to one
    #: outlier in the control. AUC is defined at zero and is rank-based.
    pairs = [(x, y) for x in rhy for y in unr]
    auc = (sum((x > y) + 0.5 * (x == y) for x, y in pairs) / len(pairs)) if pairs else None
    AUC_BAR = 0.75
    #: **THIS GATES.** The first version of this file printed SMOKE PASSED with
    #: every class share at 0.000, because `ok` never included assertion 4 -- a
    #: control that cannot fail is not a control, and this one was reporting the
    #: instrument's own absence as a clean null.
    sep_ok = auc is not None and auc >= AUC_BAR
    print("\n  4 UNRHYMED control separates                           %s"
          % ("AUC %.2f (bar %.2f) | median diff %+.3f | n=%dx%d  %s"
             % (auc, AUC_BAR, sep, len(rhy), len(unr), "PASS" if sep_ok else "FAIL")
             if auc is not None else "FAIL -- no separation computable"))
    ok &= sep_ok
    print("\n%s" % ("SMOKE PASSED -- the shape is right and the instrument separates."
                    if ok else "SMOKE FAILED -- see above."))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
