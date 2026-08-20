"""Select the deliverable: 500 verified passages per corpus, cut to 193 words.

    python .../finalise_human.py

Reads `human_passages.jsonl` (600 per corpus, normalised), drops everything the
verifier flags, takes 500, and truncates to the model length. Writes
`human_anchor.jsonl`.

## WHY 600 WERE BUILT FOR A TARGET OF 500

RH, 2026-08-20: the extra 100 is a rejection buffer for passages that come back
unfixable. It was needed. Dropped, of 3,596:

    REWRITTEN 37   NUMBERS 17   LENGTH 20   COMPLETED 4

and the surplus after dropping runs from +65 (literary criticism) to +100, so
every corpus reaches 500 without lowering a threshold to get there.

## WHAT THE REWRITTEN FLAG ACTUALLY CAUGHT, and it is worth stating plainly

Not sloppiness. FABRICATION, and only where the SOURCE was already broken. Three
worst cases, all confirmed by reading:

  * a philosophy passage whose footnote block had crashed into mid-sentence came
    back with an invented continuation -- `III-that we human beings are rational
    beings who are bound to act in accord with CI` -- which appears nowhere in
    the source;
  * a literary-criticism passage carrying two interleaved OCR columns came back
    with invented scholarship about Ghosh's `Sea of Poppies`;
  * a passage quoting MIDDLE ENGLISH verse was modernised wholesale, `Tho my
    mayster spend neuer so faste` -> `Though my master spend never so fast`,
    destroying the quoted primary text.

A cleaner asked to repair damaged text will invent the repair when the damage is
severe enough that no repair is recoverable. The similarity gate catches this
because fabrication moves most of the tokens; nothing else here would.

Both academic corpora carry the damage and the narrative ones do not -- 34
dropped from literary criticism and 14 from philosophy against 0 from dreams and
abstracts -- which is a fact about scanned two-column journals, not about the
cleaner.

## TRUNCATION IS LAST

Normalisation legitimately changes length (`conversa tion` becomes one word,
`water….The` becomes two), so cutting to 193 words after cleaning is what makes
every delivered passage exactly the model's median length. Cutting first would
not.
"""

import argparse, collections, json, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from verify_normalisation import check                       # noqa: E402

DATA = os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data"))
ROOT = os.path.join(DATA, "jakobson_space")
SRC = os.path.join(ROOT, "human_passages.jsonl")
OUT = os.path.join(ROOT, "human_anchor.jsonl")
DROPPED = os.path.join(ROOT, "human_anchor_dropped.jsonl")
TARGET = 193


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--per", type=int, default=500)
    ap.add_argument("--seed", type=int, default=20260820)
    ap.add_argument("--words", type=int, default=TARGET)
    a = ap.parse_args(argv)
    rng = random.Random(a.seed)

    rows = [json.loads(l) for l in open(SRC)]
    keep, drop = collections.defaultdict(list), []
    for r in rows:
        sim, dl, comp, flags = check(r)
        r["sim"] = round(sim, 4)
        if flags:
            r["drop_reason"] = flags
            drop.append(r)
        else:
            keep[r["corpus"]].append(r)

    out, short = [], []
    for corpus in sorted(keep):
        pool = keep[corpus]
        rng.shuffle(pool)
        if len(pool) < a.per:
            short.append((corpus, len(pool)))
        for r in pool[:a.per]:
            w = r["text"].split()
            d = {k: r[k] for k in r if k not in ("text_raw", "drop_reason")}
            #: truncate LAST, so every delivered passage is exactly a.words long
            d["text"] = " ".join(w[:a.words])
            d["n_words"] = min(len(w), a.words)
            out.append(d)

    with open(OUT, "w") as fh:
        for d in out:
            fh.write(json.dumps(d) + "\n")
    with open(DROPPED, "w") as fh:
        for d in drop:
            fh.write(json.dumps(d) + "\n")

    print("%-22s %7s %8s %8s %8s" % ("corpus", "kept", "words", "bytes", "changed"))
    by = collections.defaultdict(list)
    for d in out:
        by[d["corpus"]].append(d)
    import statistics as st
    for k in sorted(by):
        g = by[k]
        print("%-22s %7d %8d %8d %7.1f%%"
              % (k, len(g), int(st.median([x["n_words"] for x in g])),
                 int(st.median([len(x["text"].encode()) for x in g])),
                 100 * sum(1 for x in g if x.get("changes")) / len(g)))
    if short:
        print("\nBELOW QUOTA: %s" % short)
    print("\n%d passages -> %s" % (len(out), OUT))
    print("%d dropped    -> %s" % (len(drop), DROPPED))


if __name__ == "__main__":
    main()
