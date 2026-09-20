"""Do the two sides of a named relation differ on the norms, base -> aligned?

    python -u norm_shift.py                        the content run
    python -u norm_shift.py --all-words
    python -u norm_shift.py --weight               weight a word by its agreement count
    python -u norm_shift.py --csv results/norm_shift.csv

## WHAT THIS IS FOR, AND WHY IT COULD NOT BE DONE BEFORE

`pooled_relations` gives, per frame, the words a BLIND reader says carry the
relation -- and only those. Every previous norm comparison in this campaign ran
either over whole arms (mass-weighted, every cell) or over annotated pairs
(coder-linked). This is a third population: the words a reader picked out as
the ones that separate the columns.

**THE RATER NEVER KNEW THE DIRECTION AND WE ALWAYS DO.** The columns are
relabelled per frame; `blind_for` fixes which column is the faller block, and a
faller is a word that lost probability from base to aligned -- so the faller
column is the BASE-favoured one. Every row here is oriented base -> aligned
from that, computed after the reading, never shown to the reader. This is the
whole reason the A/B blind is worth keeping.

## THE SELECTION EFFECT IS THE MAIN BOUND AND IT IS NOT SMALL

The rater is instructed to find the CLEAREST relation and to drop any word that
would force a hedge. So these word lists are chosen for separability, and a
norm gap between them is partly a measurement of what a reader found salient.
Coverage per relation runs from 10 of 24 words to 23 of 23; a 10/24 relation and
a 23/23 relation are not the same kind of claim and `--min-coverage` exists to
say so. Nothing here estimates what alignment does to the arm; it estimates
what separates the words a reader used.

## LEXICON COVERAGE IS REPORTED BECAUSE THE SIDES CAN DIFFER IN IT

`fields.norms` returns `warriner_coverage`, `brysbaert_coverage` and
`k_coverage`. If the base side is rarer or more transgressive than the aligned
side it can be less covered, and then the two means are over different
populations rather than over the same one at two values. A gap on an axis whose
coverage also moves is not quotable.

## THE UNIT IS THE FRAME, AND THE TEST IS PAIRED

One relation per frame, one delta per frame, Wilcoxon signed-rank plus the sign
count over frames. Words are not the unit: they are nested in frames, shared
across the template families (six `Three ___ came into the room` frames, two
`cop pinned her/him`), and a per-word test would count those as independent.

## NOT A TEST OF THE QUOTA OF AFFECT, AND MUST NOT BE QUOTED AS ONE

The campaign's affect result is CONSERVED at arm grain (`inst:arousal` -0.037,
p=0.67) and FALLS at pair grain (-0.637, p=4e-11). This is a THIRD population,
so it can corroborate or complicate; it cannot referee that seventeen-fold gap,
and a third number in the same sentence as those two invites exactly that.
"""
import argparse, collections, json, math, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
for p in (ROOT, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

CONTENT = os.path.join(HERE, "results", "pooled_relations_flash_content.jsonl")
ALLWORDS = os.path.join(HERE, "results", "pooled_relations_flash.jsonl")

#: the scales worth reading across; the `_coverage` fields are reported beside
#: them rather than tested, and `n_tokens`/`n_content` are counts not scales
SCALES = ["warriner_valence", "warriner_arousal", "warriner_dominance",
          "brysbaert_concreteness", "k_charge", "k_transgressiveness",
          "k_vulgarity", "k_register_level", "k_bodily_harm", "k_concreteness",
          "k_valence"]
COVER = ["warriner_coverage", "brysbaert_coverage", "k_coverage"]


def side_norms(words, weights=None):
    """Mean norms over a word list. -> dict or None

    `fields.norms` takes text and averages over its content words, which is the
    unweighted reading. For the weighted reading a word is repeated by its
    agreement count, so a word 39 lineages agree on outweighs one at 15 -- the
    same weighting the table asks the reader to apply.
    """
    from malignment import fields as F
    if not words:
        return None
    if weights:
        toks = []
        for w in words:
            toks.extend([w] * max(1, int(weights.get(w, 1))))
    else:
        toks = list(words)
    try:
        return F.norms(" ".join(toks))
    except Exception:
        return None


def counts_for(frame):
    """{word: agreement count} for one frame. -> dict"""
    import pooled_tables as PT
    got = PT.pooled(frame)
    if not got:
        return {}
    return {w: max(f, r) for w, (f, r, _s) in got[0].items()}


def rows(path, weight=False, min_coverage=0.0):
    out = []
    for line in open(path, encoding="utf-8"):
        rec = json.loads(line)
        if rec["n_shown"] and rec["n_covered"] / rec["n_shown"] < min_coverage:
            continue
        #: ORIENTATION. `a_is_faller` means GROUP A is the faller block; a
        #: faller lost probability from base to aligned, so that column is the
        #: BASE-favoured one. Getting this backwards flips every sign below and
        #: nothing downstream would look wrong.
        if rec["a_is_faller"]:
            base, aligned = rec["words_a"], rec["words_b"]
        else:
            base, aligned = rec["words_b"], rec["words_a"]
        wts = counts_for(rec["frame"]) if weight else None
        nb, na = side_norms(base, wts), side_norms(aligned, wts)
        if not nb or not na:
            continue
        out.append({"frame": rec["frame"], "name": rec["name"],
                    "confidence": rec["confidence"],
                    "n_base": len(base), "n_aligned": len(aligned),
                    "coverage": rec["n_covered"] / max(1, rec["n_shown"]),
                    "base": nb, "aligned": na})
    return out


def wilcoxon(d):
    """Signed-rank p, two-sided, normal approximation. -> (W, p, n)"""
    d = [x for x in d if x != 0]
    n = len(d)
    if n < 6:
        return None, None, n
    order = sorted(range(n), key=lambda i: abs(d[i]))
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and abs(d[order[j + 1]]) == abs(d[order[i]]):
            j += 1
        avg = (i + j) / 2.0 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    wp = sum(r for r, x in zip(ranks, d) if x > 0)
    mu = n * (n + 1) / 4.0
    sd = math.sqrt(n * (n + 1) * (2 * n + 1) / 24.0)
    z = (wp - mu) / sd if sd else 0.0
    p = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
    return wp, p, n


def report(rs, label):
    print("=" * 74)
    print("%s   %d relations, frame as the unit, delta = ALIGNED - BASE" % (label, len(rs)))
    print("=" * 74)
    print("%-26s %8s %8s %8s %7s %9s" % ("scale", "base", "aligned", "delta", "n+/n", "p"))
    for s in SCALES:
        d = [r["aligned"].get(s, float("nan")) - r["base"].get(s, float("nan"))
             for r in rs]
        d = [x for x in d if x == x]
        if len(d) < 6:
            continue
        b = statistics.mean([r["base"][s] for r in rs if s in r["base"]])
        a = statistics.mean([r["aligned"][s] for r in rs if s in r["aligned"]])
        _w, p, n = wilcoxon(d)
        pos = sum(1 for x in d if x > 0)
        star = "  <<<" if p is not None and p < 0.01 else ""
        print("%-26s %8.3f %8.3f %+8.3f %4d/%-4d %9s%s"
              % (s, b, a, statistics.mean(d), pos, n,
                 ("%.2g" % p) if p is not None else "-", star))
    print()
    print("%-26s %8s %8s %8s" % ("(lexicon coverage)", "base", "aligned", "delta"))
    for c in COVER:
        b = statistics.mean([r["base"][c] for r in rs if c in r["base"]])
        a = statistics.mean([r["aligned"][c] for r in rs if c in r["aligned"]])
        flag = "   <- SIDES DIFFER, means are over different populations" \
            if abs(a - b) > 0.05 else ""
        print("%-26s %8.3f %8.3f %+8.3f%s" % (c, b, a, a - b, flag))
    print()
    print("words per side: base %.1f, aligned %.1f; coverage of frame %.0f%% median"
          % (statistics.mean(r["n_base"] for r in rs),
             statistics.mean(r["n_aligned"] for r in rs),
             100 * statistics.median(r["coverage"] for r in rs)))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--all-words", action="store_true")
    ap.add_argument("--weight", action="store_true",
                    help="weight each word by how many lineages agree on it")
    ap.add_argument("--min-coverage", type=float, default=0.0)
    ap.add_argument("--csv", default=None)
    a = ap.parse_args(argv)
    path = ALLWORDS if a.all_words else CONTENT
    rs = rows(path, a.weight, a.min_coverage)
    if not rs:
        raise SystemExit("no relations")
    report(rs, "%s%s" % (os.path.basename(path),
                         "  [agreement-weighted]" if a.weight else ""))
    if a.csv:
        import csv
        with open(a.csv, "w", newline="", encoding="utf-8") as fh:
            cols = ["frame", "name", "confidence", "coverage", "n_base", "n_aligned"]
            w = csv.writer(fh)
            w.writerow(cols + ["base_" + s for s in SCALES]
                       + ["aligned_" + s for s in SCALES])
            for r in rs:
                w.writerow([r[c] for c in cols]
                           + ["%.4f" % r["base"].get(s, float("nan")) for s in SCALES]
                           + ["%.4f" % r["aligned"].get(s, float("nan")) for s in SCALES])
        print("\nwrote %s (%d rows)" % (a.csv, len(rs)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
