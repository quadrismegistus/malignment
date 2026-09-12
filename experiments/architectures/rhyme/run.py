#!/usr/bin/env python
"""Does rhyme pull depend on the attention mechanism? THE REGISTERED TEST.

    python run.py                 the `called` slot, both arms, by architecture
    python run.py --slot end1

## WHY THIS IS THE ONE THAT COUNTS

Every other instrument in `architectures/` reads a SEMANTIC profile -- charge,
word norms, sentence drift, vocabulary overlap -- and all of them came back
null. They had to: those quantities live in the output distribution, which is
the unembedding matrix and the softmax, and every model in the census has one.

**A rime class is a FORMAL equivalence relation.** It is computed from IPA, not
from an encoder, so nothing here can fail an embedding gate; and it is Jakobson's
axis of selection in the one form the poetic function actually names. This is the
only place in the subject where an instrument could see something the others
cannot.

## THE MEASURE

`data/verse_fleet_slot_manifest.json` gives, per cell, the rime key of the
scheme partner's end word (`target_key`) and of a NON-partner line (`nonpartner_key`),
which is the control. `rime_class_vocab_v2.json` maps 8,052 keys to their words.

    pull        target-class mass MINUS nonpartner-class mass
    closure     mass-weighted p(the line ends here)
    given       target share of CLOSURE-WEIGHTED mass

**The nonpartner term is not optional.** Some rime classes are simply commoner
than others, so raw target mass rewards a model for having drawn a common class;
the difference against a matched non-partner class removes that.

## THE PRE-COMMITMENT THIS TESTS, RECORDED 2026-09-11 BEFORE ANY CELL

From `README.md`, amended the same day and before the fleet ran:

  * The prediction is about whether GLOBAL attention carries the operation.
  * `Olmo-3-1025-7B` and `Olmo-Hybrid-7B` share a 32-layer schedule with
    `full_attention` at exactly [3,7,11,15,19,23,27,31] in BOTH, and all 24
    remaining layers go `sliding_attention -> linear_attention`. Global attention
    is held CONSTANT; only the local mechanism is replaced.
  * **So if global attention carries it, that pair should move LEAST on rhyme
    pull of any architecture contrast in the fleet.**
  * And the comparison must be a DELTA, not a base capacity, because every other
    number in this subject is a base->aligned delta and ordering a capacity
    against a delta compares two constructs.

## NEITHER TABLE IS DEDUPLICATED, AND ONE OF THEM IS NOT THE ONE YOU EXPECT

`twp_closure` holds 15,604,273 rows over 5,325,818 distinct (model, prompt,
word) -- about 2.9 copies of each, all with the SAME `p_close` (checked: 0 keys
carry more than one distinct value). `twp_words_v4` duplicates too, 39,138 rows
over 33,178 keys on these prompts. Harmless to any per-key aggregate and fatal
to a raw row count, so both sides group first.

**And the words come from `twp_words_v4`, not `twp_words_v4_best`.** The `_best`
view holds ZERO of these prompts: the verse fleet wrote the raw v4 table and the
topup merge never ran over it. A first version of this file queried `_best`,
joined cleanly, and returned an empty frame rather than an error -- the same
silent-empty failure as joining passages on `prompt_id`.
"""
import argparse
import collections
import json
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, ROOT)
CAP = os.path.join(ROOT, "experiments", "emergence", "capacities", "data")
MANIFEST = os.path.join(CAP, "verse_fleet_slot_manifest.json")
RIME = os.path.join(CAP, "rime_class_vocab_v2.json")
FLOOR = 0.01


def main():
    from malignment import roster, vectors as V
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--slot", default="called")
    ap.add_argument("--min-cells", type=int, default=30)
    ap.add_argument("--floor", type=float, default=0.01,
                    help="minimum BASE pull for a lineage to enter the relative-"
                         "delta table. A ratio needs a denominator, and a model "
                         "with base pull 0.002 has none.")
    a = ap.parse_args()

    global FLOOR
    FLOOR = a.floor
    cells = [c for c in json.load(open(MANIFEST))["cells"] if c.get("slot") == a.slot]
    k2w = json.load(open(RIME))["key_to_words"]
    #: (prompt -> target words, nonpartner words). A cell whose two classes
    #: OVERLAP is dropped: the difference would be partly self-cancelling.
    role = {}
    for c in cells:
        tw = set(k2w.get(c.get("target_key") or "", []))
        nw = set(k2w.get(c.get("nonpartner_key") or "", []))
        if not tw or not nw or (tw & nw):
            continue
        role[c["context"]] = (tw, nw)
    prompts = sorted(role)
    print("slot=%s: %d cells, %d usable after dropping overlapping classes"
          % (a.slot, len(cells), len(prompts)))

    #: GROUP FIRST -- see the docstring on duplication.
    #: **twp_words_v4, NOT twp_words_v4_best.** The `_best` view holds ZERO of
    #: these prompts -- the verse fleet wrote to the raw v4 table and the topup
    #: merge never ran over it. Checked, not assumed: 0 rows against 39,138.
    #: `frame=''` is every verse row, so the filter costs nothing and documents
    #: that this is the raw edge.
    q = ("SELECT w.model AS model, w.prompt AS prompt, w.word AS word, "
         "       max(w.p) AS p, any(c.pc) AS pc "
         "FROM twp_words_v4 w "
         "LEFT JOIN (SELECT model, prompt, word, any(p_close) AS pc "
         "           FROM twp_closure GROUP BY model, prompt, word) c "
         "  ON c.model = w.model AND c.prompt = w.prompt AND c.word = w.word "
         "WHERE w.prompt IN {ps:Array(String)} AND w.frame = '' "
         "GROUP BY w.model, w.prompt, w.word")
    rows = V.rows(q, ps=prompts)
    print("%d (model, prompt, word) rows, %d models\n"
          % (len(rows), len({r["model"] for r in rows})))

    acc = collections.defaultdict(lambda: collections.defaultdict(
        lambda: [0.0, 0.0, 0.0, 0.0]))          # tgt, non, tgt*pc, all*pc
    for r in rows:
        tw, nw = role[r["prompt"]]
        p = float(r["p"] or 0.0)
        pc = float(r["pc"] or 0.0)
        v = acc[r["model"]][r["prompt"]]
        #: **CASE-FOLD THE CANDIDATE.** `rime_class_vocab_v2.json` is entirely
        #: lowercase, so `Love`, `Night` and `God` were invisible while `love`,
        #: `night` and `god` were not -- and at a LINE-END slot in verse a
        #: capitalised candidate is ordinary. Measured before the fix: median
        #: 84.7% of slot mass was in-vocabulary, 94.3% after folding, a gain of
        #: +9.9 points -- and the gain is DIFFERENTIAL, 7.0 to 12.1 points across
        #: models, so the unfolded measure was partly reading how often a model
        #: capitalises. Case is phonologically irrelevant to a rime class.
        w = r["word"] if r["word"] in tw or r["word"] in nw else r["word"].lower()
        if w in tw:
            v[0] += p
            v[2] += p * pc
        elif w in nw:
            v[1] += p
        v[3] += p * pc
    out = {}
    for m, byp in acc.items():
        pulls = [v[0] - v[1] for v in byp.values()]
        given = [v[2] / v[3] for v in byp.values() if v[3] > 0]
        if len(pulls) >= a.min_cells:
            out[m] = (st.median(pulls), st.median(given) if given else float("nan"),
                      len(pulls))
    eps, _ = roster.endpoints()
    print("%-30s %-13s %-7s %10s %10s %6s"
          % ("model", "attn", "block", "pull", "given", "cells"))
    for m in sorted(out, key=lambda x: -out[x][0]):
        at, bl = roster.architecture(m)
        arm = "base" if m in eps else ("aligned" if m in set(eps.values()) else "-")
        print("%-30s %-13s %-7s %10.5f %10.4f %6d  %s"
              % (m.split("/")[-1][:30], at, bl, out[m][0], out[m][1], out[m][2], arm))
    print()
    print("THE REGISTERED CONTRAST, base -> aligned DELTA per lineage:")
    print("%-34s %-16s %10s %10s %10s"
          % ("lineage", "architecture", "base", "aligned", "delta"))
    deltas = []
    for b, al in sorted(eps.items()):
        if b not in out or al not in out:
            continue
        at, bl = roster.architecture(b)
        d = out[al][0] - out[b][0]
        deltas.append((abs(d), d, b, at, bl))
        print("%-34s %-16s %10.5f %10.5f %+10.5f"
              % (b.split("/")[-1][:34], at + "/" + bl, out[b][0], out[al][0], d))
    if deltas:
        deltas.sort()
        print()
        print("THE PRE-COMMITMENT, READ LITERALLY. It said Olmo-3/Olmo-Hybrid should")
        print("show the SMALLEST |delta| of any contrast. Smallest first:")
        for ad, d, b, at, bl in deltas[:6]:
            print("   %-32s %-16s %+.5f" % (b.split("/")[-1][:32], at + "/" + bl, d))
        rank = {b: i + 1 for i, (_, _, b, _, _) in enumerate(deltas)}
        for b in ("allenai/Olmo-3-1025-7B", "allenai/Olmo-Hybrid-7B"):
            if b in rank:
                print("   ... %-28s rank %d of %d" % (b.split("/")[-1], rank[b], len(deltas)))
        print()
        print("**IT FAILS, AND THE RANKING IT ASKED FOR IS CONFOUNDED.** |delta|")
        print("tracks BASELINE: a model with no rhyme pull has nothing to lose, so")
        print("the top of that list is models whose base pull is ~0.002-0.003.")
        print("Ranking by raw |delta| rewards having no rhyme pull at all. That is")
        print("a defect in the pre-commitment as written, not a result.")
        print()
        print("POST HOC REPAIR, LABELLED AS ONE: relative delta, and only for")
        print("lineages whose BASE pull clears %.3f, so the ratio has a denominator."
              % FLOOR)
        rel = [(abs(d) / out[b][0], d / out[b][0], b, at, bl)
               for _, d, b, at, bl in deltas if out[b][0] >= FLOOR]
        rel.sort()
        print("   %-32s %-16s %10s %10s" % ("lineage", "architecture", "rel delta", "base"))
        for ar, r, b, at, bl in rel:
            print("   %-32s %-16s %+10.3f %10.5f"
                  % (b.split("/")[-1][:32], at + "/" + bl, r, out[b][0]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
