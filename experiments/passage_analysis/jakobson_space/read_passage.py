"""Render one passage with both decompositions marked on it.

    python .../read_passage.py --id mode-9a6eb2cd09ec16
    python .../read_passage.py --quadrant '(-surp +drift)' --category API -n 3
    python .../read_passage.py --id ... --top 8

For each passage: the sentences in order with their displacement from the
opening sentence, and the words that carried the most and least surprisal.

## WHAT THE TWO MARKINGS MEAN, BECAUSE THEY ARE NOT THE SAME KIND OF THING

    words       deepseek's surprisal at that word, in bits. A HIGH number means
                deepseek did not expect this word here -- a selection deepseek
                would not have made. It is a property of the WORD IN ITS
                LEFT CONTEXT, so the same word scores differently twice over.
    sentences   cosine displacement from the FIRST sentence, in bge space. A
                high number means the passage has moved away from where it
                opened. `+` is the step from the previous sentence.

Surprisal is per-word and local; drift is per-sentence and cumulative. A passage
can be full of unexpected words while never leaving its opening topic, and that
combination is exactly the `(+surp -drift)` quadrant.

Both are shown per sentence, so the question "do the surprising words sit in the
sentences that move?" can be read off one passage rather than inferred from two
correlations. The per-sentence bits come from assigning each word to the sentence
whose CHARACTER SPAN contains it -- the word producer and the sentence producer
share the text and nothing else, so position is the only honest join.

## THE FIRST WORD HAS NO SCORE AND IS MARKED, NOT DROPPED

`word_bits()` cannot score the first token -- nothing precedes it -- so its word
is flagged `partial` and excluded from the extremes. Including it would rank a
word by a number that was never computed.

## `--quadrant` SAMPLES, AND SAMPLING IS A DESIGN

With `--quadrant`, passages are drawn at the 85th percentile of distance from the
plane's origin, NOT from the extreme tips. The tips of a two-axis plane are
degenerate cases -- the most surprising passage in the corpus is usually
malformed rather than interesting -- and quoting them as illustrations of a
quadrant is an illustration sampled on its effect size. `--seed` is fixed so the
same call returns the same passages.
"""

import argparse, collections, csv, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data"))
EXPLODED = os.path.join(DATA, "jakobson_space", "exploded")
QUAD = os.path.join(HERE, "results", "quadrants.csv")

PCT = 0.85


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", action="append", default=[])
    ap.add_argument("--quadrant")
    ap.add_argument("--category")
    ap.add_argument("-n", type=int, default=2, help="passages to draw")
    ap.add_argument("--top", type=int, default=6, help="extreme words to show")
    ap.add_argument("--seed", type=int, default=20260821)
    a = ap.parse_args(argv)
    import pyarrow.parquet as pq

    csv.field_size_limit(10 ** 7)
    rows = {r["id"]: r for r in csv.DictReader(open(QUAD, newline=""))}

    want = list(a.id)
    if a.quadrant:
        pool = [r for r in rows.values() if r["quadrant"] == a.quadrant
                and (not a.category or r["category"] == a.category)]
        if not pool:
            raise SystemExit("no passages in %r%s" % (a.quadrant,
                             " for %s" % a.category if a.category else ""))
        #: distance from the origin ON THE QUADRANT'S OWN AXES, so p85 means
        #: "well inside this quadrant" rather than "far along whichever axis
        #: happens to have the larger spread".
        pool.sort(key=lambda r: (float(r["z_surprisal"]) ** 2
                                 + float(r["z_drift_residual"]) ** 2) ** 0.5)
        lo, hi = int(PCT * len(pool)), min(int(PCT * len(pool)) + 40, len(pool))
        band = pool[lo:hi] or pool[-a.n:]
        want += [r["id"] for r in random.Random(a.seed).sample(
            band, min(a.n, len(band)))]
        print("drew %d of %d %s passages%s, from the p%d band (n=%d)\n"
              % (min(a.n, len(band)), len(pool), a.quadrant,
                 " in %s" % a.category if a.category else "", PCT * 100, len(band)))

    W = collections.defaultdict(list)
    t = pq.read_table(os.path.join(EXPLODED, "words.parquet"))
    d = {c: t.column(c).to_pylist() for c in t.column_names}
    keep = set(want)
    for i, pid in enumerate(d["id"]):
        if pid in keep:
            W[pid].append((d["word_index"][i], d["word"][i], d["bits"][i],
                           d["partial"][i]))
    S = collections.defaultdict(list)
    t = pq.read_table(os.path.join(EXPLODED, "sentences.parquet"))
    d = {c: t.column(c).to_pylist() for c in t.column_names}
    for i, pid in enumerate(d["id"]):
        if pid in keep:
            S[pid].append((d["sent_index"][i], d["sentence"][i], d["step"][i],
                           d["dist_from_first"][i], d["is_furthest"][i]))

    for pid in want:
        r = rows.get(pid)
        if not r:
            print("%s -- not in quadrants.csv\n" % pid); continue
        who = r["model"] or r["category"]
        print("=" * 78)
        print("%s   %s   %s" % (pid, who, r["quadrant"]))
        print("  surprisal %.3f bits/token (z %+.2f)   drift %.4f (z %+.2f, "
              "residual z %+.2f)" % (float(r["surprisal"]), float(r["z_surprisal"]),
                                     float(r["drift"]), float(r["z_drift"]),
                                     float(r["z_drift_residual"])))
        if r["prompt"]:
            print("  stem: %r" % r["prompt"])

        ws = sorted(W.get(pid, []))
        scored = [w for w in ws if not w[3]]
        if scored:
            by = sorted(scored, key=lambda w: -w[2])
            print("\n  MOST surprising words (bits, deepseek did not expect these):")
            print("    " + "  ".join("%s %.1f" % (w[1], w[2]) for w in by[:a.top]))
            #: the bottom of the list is closed-class words at 0.0 bits, and a
            #: row of seven zeroes shows that badly. The SHARE says the same
            #: thing quantitatively and imports no stoplist -- no decision about
            #: which words count as machinery is made here.
            tot = sum(w[2] for w in scored)
            top_share = sum(w[2] for w in by[:10]) / tot if tot else 0
            n_flat = sum(1 for w in scored if w[2] < 0.5)
            print("  concentration: the top 10 words carry %.0f%% of the "
                  "passage's %.0f bits;" % (100 * top_share, tot))
            print("                 %d of %d words (%.0f%%) cost under 0.5 bits"
                  % (n_flat, len(scored), 100 * n_flat / len(scored)))
            n_part = sum(1 for w in ws if w[3])
            if n_part:
                print("  (%d word%s unscored: no left context)"
                      % (n_part, "" if n_part == 1 else "s"))

        ss = sorted(S.get(pid, []))
        if ss:
            #: per-sentence mean bits, so the two grains are readable together.
            #: The join is by CHARACTER POSITION -- words are walked in order and
            #: assigned to the sentence whose span contains them -- because the
            #: two producers agree on the text and on nothing else. A word
            #: straddling a boundary goes to the sentence it starts in.
            spans, at = [], 0
            for _, sent, _, _, _ in ss:
                j = r["text"].find(sent, at)
                j = at if j < 0 else j
                spans.append((j, j + len(sent))); at = j + len(sent)
            bits = collections.defaultdict(list)
            pos = 0
            for _, word, b, part in sorted(W.get(pid, [])):
                k = r["text"].find(word, pos)
                if k < 0:
                    continue
                pos = k + len(word)
                if not part:
                    for si, (s0, s1) in enumerate(spans):
                        if s0 <= k < s1:
                            bits[si].append(b); break
            print("\n  SENTENCES  (+step from previous | displacement from the "
                  "first | mean bits/word)")
            for i, sent, step, d0, far in ss:
                mark = "  <-- FURTHEST" if far else ""
                sp = "     " if step is None else "%+.3f" % step
                bb = ("%5.2f" % (sum(bits[i]) / len(bits[i]))) if bits.get(i) else "   . "
                print("   %2d %s | %.3f | %s%s  %s" % (i, sp, d0, bb, mark,
                      (sent[:76] + ("..." if len(sent) > 76 else "")).replace("\n", " ")))
        print()


if __name__ == "__main__":
    main()
