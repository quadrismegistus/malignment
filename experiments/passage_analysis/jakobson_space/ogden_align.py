"""Align Ogden Basic English against its original, paragraph by paragraph.

    python .../ogden_align.py                    # report the alignment
    python .../ogden_align.py --csv out.csv      # and write the pairs

## WHY ALIGNMENT AND NOT INDEXING

`malign-logits/data/texts/{basic,original}/` holds three stories rendered into
Ogden's 850-word Basic English beside their originals, plus Joyce in `original`
only -- Finnegans Wake has no Basic rendering, and that absence is the point it
was collected to make.

Paragraph COUNTS do not match: 46/49 (hemingway), 185/179 (mansfield), 7/11
(andersen). Pairing by index would work for the first two and silently mispair
the third, whose Basic version merges paragraphs so heavily that its line 1 is
already describing a different moment than the original's.

So the pairing is computed, not assumed, by monotone alignment -- the same shape
as Needleman-Wunsch, over paragraphs instead of residues.

## THE ALGORITHM, AND WHY MONOTONE IS THE WHOLE CONSTRAINT

Both texts tell one story in one order. That is a strong prior and it is what
makes this tractable: an alignment may MERGE (several original paragraphs to one
Basic) or SPLIT, but it may never cross. So the search is a shortest path over a
grid, and crossing pairings are not merely penalised, they are unreachable.

Score between two paragraphs is a bag-of-words Jaccard on lowercased alphabetic
tokens. Deliberately crude: a Basic rendering REPLACES the rare words, which are
exactly the ones a tf-idf scheme would weight most, so an "informative-word"
similarity would systematically score true pairs LOWER the more Basic-ish they
are. Function words and the surviving nouns carry the alignment, and the
substitutions this file exists to find are the tokens the metric ignores.

    match       consume one paragraph on each side       score = jaccard
    merge       consume one on the LONGER side only      score = GAP
    (both directions available, so a merge and a split are the same move)

`GAP` is negative, so the path prefers matching to skipping unless the match is
worse than the gap cost. It is a free parameter and is reported, because an
alignment whose gap penalty is not stated is an alignment nobody can reproduce.

## POOLING: n:m PARAGRAPHS -> ONE PAIRED PASSAGE

Paragraphs are short -- median 24 words basic against 21 original, and 101 of
228 under twenty -- because two of the three texts are dialogue-heavy. That is
long enough for a paired surprisal difference and too short for drift, which
needs sentences to take steps between.

So `--group-words N` walks the aligned pairs IN ORDER and closes a group when
BOTH sides have reached N words. Both sides always close on the same pair
boundary, so an n:m paragraph run becomes one paired passage and the
correspondence survives pooling -- the group is a contiguous run of pairs, never
a re-pairing.

Two rules the pooling must not break, and does not:

  * **Groups never cross a text.** A passage half Mansfield and half Hemingway
    would have a drift step at the seam that belongs to neither.
  * **The tail is dropped, not padded.** A final run that never reaches N on
    both sides is discarded and counted; keeping it would put one short passage
    per text into a comparison whose whole point is a common length floor.

Both sides reach the floor before the group closes, so the Basic side runs
LONGER than the original by construction -- which is the Ogden effect itself
(an 850-word vocabulary needs more words), not an artifact of the pooling. The
word counts travel on every row so the asymmetry is visible rather than assumed.

## THE ALIGNMENT IS CHECKED, NOT TRUSTED

Three things are printed and any of them can condemn the result:

    the per-pair Jaccard distribution -- a true pairing of a text with its own
      paraphrase should sit high; a floor near zero means the path matched noise
    the merge/split count -- andersen SHOULD show many, the other two few
    the endpoints -- first-to-first and last-to-last, which are the two pairs
      whose correctness can be read by eye

A pair below `--min-jaccard` is dropped and counted rather than carried, because
the downstream question is what Basic English does to a passage, and a mispaired
passage answers a different question with the same number.
"""

import argparse, csv, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEXTS = "/Users/rj416/github/malign-logits/data/texts"
GAP = -0.15
WORD = re.compile(r"[a-z']+")


def paras(path):
    return [l.strip() for l in open(path, encoding="utf-8", errors="replace")
            if l.strip()]


def bag(s):
    return set(WORD.findall(s.lower()))


def jaccard(a, b):
    A, B = bag(a), bag(b)
    if not A or not B:
        return 0.0
    return len(A & B) / len(A | B)


def align(A, B, gap=GAP):
    """Monotone alignment of two paragraph lists. -> [(i or None, j or None)]

    Needleman-Wunsch with an affine-free constant gap. `i` indexes A (basic),
    `j` indexes B (original); a None on either side is a merge, i.e. a
    paragraph on the other side with no counterpart of its own.
    """
    n, m = len(A), len(B)
    #: dynamic-programming table; +1 for the empty prefixes
    D = [[0.0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        D[i][0] = D[i - 1][0] + gap
    for j in range(1, m + 1):
        D[0][j] = D[0][j - 1] + gap
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            D[i][j] = max(D[i - 1][j - 1] + jaccard(A[i - 1], B[j - 1]),
                          D[i - 1][j] + gap,
                          D[i][j - 1] + gap)
    #: traceback, preferring the diagonal on ties so a genuine match is not
    #: rewritten as two gaps of equal total score
    out, i, j = [], n, m
    while i > 0 or j > 0:
        if i > 0 and j > 0 and \
           abs(D[i][j] - (D[i - 1][j - 1] + jaccard(A[i - 1], B[j - 1]))) < 1e-12:
            out.append((i - 1, j - 1)); i, j = i - 1, j - 1
        elif i > 0 and abs(D[i][j] - (D[i - 1][j] + gap)) < 1e-12:
            out.append((i - 1, None)); i -= 1
        else:
            out.append((None, j - 1)); j -= 1
    return out[::-1]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv")
    ap.add_argument("--gap", type=float, default=GAP)
    ap.add_argument("--min-jaccard", type=float, default=0.15)
    ap.add_argument("--group-words", type=int, default=0,
                    help="pool consecutive pairs until BOTH sides reach N "
                         "words; 0 = one row per paragraph pair")
    a = ap.parse_args(argv)

    rows, tot = [], {"pairs": 0, "dropped": 0, "merges": 0}
    print("gap penalty %.2f | min jaccard %.2f | similarity = bag-of-words "
          "jaccard\n" % (a.gap, a.min_jaccard))
    for fn in sorted(os.listdir(os.path.join(TEXTS, "basic"))):
        A = paras(os.path.join(TEXTS, "basic", fn))
        B = paras(os.path.join(TEXTS, "original", fn))
        al = align(A, B, a.gap)
        m = [(i, j) for i, j in al if i is not None and j is not None]
        js = sorted(jaccard(A[i], B[j]) for i, j in m)
        merges = len(al) - len(m)
        keep = [(i, j) for i, j in m if jaccard(A[i], B[j]) >= a.min_jaccard]
        name = fn.replace(".txt", "")
        print("%s  basic %d paras / original %d" % (name, len(A), len(B)))
        print("   matched %d, merges/splits %d, kept %d at >= %.2f (dropped %d)"
              % (len(m), merges, len(keep), a.min_jaccard, len(m) - len(keep)))
        if js:
            print("   jaccard  min %.2f  p25 %.2f  median %.2f  p75 %.2f  max %.2f"
                  % (js[0], js[len(js)//4], js[len(js)//2], js[3*len(js)//4], js[-1]))
        #: THE TWO PAIRS ANYONE CAN CHECK BY EYE
        if m:
            i, j = m[0]
            print("   first pair  B: %s" % A[i][:58])
            print("               O: %s" % B[j][:58])
            i, j = m[-1]
            print("   last pair   B: %s" % A[i][:58])
            print("               O: %s" % B[j][:58])
        tot["pairs"] += len(keep); tot["dropped"] += len(m) - len(keep)
        tot["merges"] += merges
        if not a.group_words:
            for i, j in keep:
                rows.append(dict(text=name, basic_idx=i, orig_idx=j,
                                 jaccard=round(jaccard(A[i], B[j]), 4),
                                 basic_words=len(A[i].split()),
                                 orig_words=len(B[j].split()),
                                 basic=A[i], original=B[j]))
        else:
            #: contiguous runs of PAIRS, closed when both sides reach the floor
            buf, n_drop = [], 0
            for i, j in keep:
                buf.append((i, j))
                bw = sum(len(A[x].split()) for x, _ in buf)
                ow = sum(len(B[y].split()) for _, y in buf)
                if bw >= a.group_words and ow >= a.group_words:
                    rows.append(dict(
                        text=name, basic_idx="%d-%d" % (buf[0][0], buf[-1][0]),
                        orig_idx="%d-%d" % (buf[0][1], buf[-1][1]),
                        n_paras=len(buf), jaccard="",
                        basic_words=bw, orig_words=ow,
                        basic=" ".join(A[x] for x, _ in buf),
                        original=" ".join(B[y] for _, y in buf)))
                    buf = []
            if buf:
                #: SAID, not padded -- see the docstring.
                n_drop = len(buf)
                print("   tail of %d pairs never reached %d words on both "
                      "sides; dropped" % (n_drop, a.group_words))
        print()

    print("TOTAL  %d usable pairs, %d dropped below threshold, %d merges/splits"
          % (tot["pairs"], tot["dropped"], tot["merges"]))
    #: Joyce is in `original` alone, deliberately -- state it so its absence
    #: reads as the design it is rather than as a missing file.
    extra = set(os.listdir(os.path.join(TEXTS, "original"))) - \
        set(os.listdir(os.path.join(TEXTS, "basic")))
    if extra:
        print("original-only, by design (no Basic rendering exists): %s"
              % ", ".join(sorted(x.replace(".txt", "") for x in extra)))
    if a.csv:
        with open(a.csv, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader(); w.writerows(rows)
        print("-> %s" % a.csv)


if __name__ == "__main__":
    main()
