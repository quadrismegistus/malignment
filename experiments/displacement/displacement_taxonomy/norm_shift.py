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

#: **THESE ARE THE MOVEMENT, NOT A NORM, AND THEY SIT IN THE SAME DICT.**
#: `contextual_norms` returns `v6_net`, `v6_rise`, `v6_fall` and the `v6_wide`
#: equivalents beside the twelve actual scales. `net` IS `rise - fall` -- the
#: thing this file is trying to explain. Leaving them in would "predict" the
#: movement with the movement and produce the largest effect in the table.
#: The same leak was found and fixed once already in `annotated_pairs.py`; it
#: recurs because the keys look like every other key.
#: **MATCHED ON SEGMENTS, BECAUSE endswith DID NOT WORK AND I WROTE IT FOR
#: EXACTLY THIS.** The first version tested `k.endswith("_net")`; the key is
#: `v6_net_rate`, which ends in `_rate`. It came through and ranked FIRST in
#: the table at 56 of 56 relations, p=7.5e-11 -- perfect separation, which is
#: what a leak looks like and what a norm never does.
NOT_NORM_SEGMENTS = {"net", "rise", "fall", "ratable", "eligible", "present",
                     "instruments"}


def _is_norm(key):
    return not (NOT_NORM_SEGMENTS & set(key.split("_")))

#: asked for by name; `v6` and the institutional battery cover nearly every
#: relation, the sexual one is scoped to the frames it was built for and is
#: reported at a lower threshold rather than dropped
#: **THESE ARE THE KEYS `contextual_norms` EMITS, NOT THE INSTRUMENT NAMES.**
#: It shortens: `inst.replace("slot_rating_en_", "").replace("_slot_en_", "_")`,
#: so `sexual_slot_en_v2` arrives as `sexual_v2`. Filtering on the instrument
#: name matched nothing and I was one step from reporting that the sexual
#: battery does not cover these frames. It does.
CTX_INSTRUMENTS = ("v6", "slot_institutional_en_v3", "sexual_v2")


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


def charge_sides(frame, base, aligned, weights=None):
    """Contextual task_charge for each side. -> (mean_base, mean_aligned, cov)

    **A DIFFERENT INSTRUMENT FROM `k_charge`, NOT A SECOND READING OF IT.**
    `fields.norms` gives the TYPE-LEVEL lexicon: what the word is worth on its
    own. `charge.scene` gives what `task_charge` rated the COMPLETED SCENE --
    the sentence once that word is in it, averaged over the lineages that rated
    it. On "She was so angry she wanted to" the type-level scale is flat while
    the contextual one puts `kill`/`murder`/`stab`/`shoot` at 6.98-7.00 against
    `scream`/`shout`/`cry` at 1.98-2.54.

    **`lift` ADDS NOTHING TO THE CONTRAST AND IS NOT REPORTED.** lift is
    `scene - dose(frame)` and dose is constant within a frame, so the
    between-side delta is identical for scene and lift. It changes the LEVEL,
    never the difference, and reporting both would look like two results.
    """
    from malignment import charge
    try:
        sc = charge.scene(frame)
    except Exception:
        return None, None, 0.0
    if not sc:
        return None, None, 0.0
    #: weighted the same way `side_norms` is -- a word is repeated by its
    #: agreement count. Without this `--weight` returned the UNWEIGHTED charge
    #: figure unchanged and read as a fourth independent specification when it
    #: was the default one printed twice.
    def vals(ws):
        out = []
        for w in ws:
            if w in sc:
                out.extend([sc[w]] * (max(1, int(weights.get(w, 1)))
                                      if weights else 1))
        return out
    b, a = vals(base), vals(aligned)
    cov = (sum(1 for w in base if w in sc) + sum(1 for w in aligned if w in sc)) \
        / max(1, len(base) + len(aligned))
    if not b or not a:
        return None, None, cov
    return statistics.mean(b), statistics.mean(a), cov


def ctx_sides(frame, base, aligned, weights=None):
    """Contextual norms per scale, both sides. -> {scale: (mb, ma, cov)}

    A rater saw the FRAME, so `scream` after "She wanted to" and `scream` after
    "The kettle began to" are different ratings of the same word -- which is
    the whole reason this is not `fields.norms`.
    """
    from malignment import fields as F
    try:
        cn = {w: F.contextual_norms(frame, w) for w in set(base) | set(aligned)}
    except Exception:
        return {}
    keys = set()
    for d in cn.values():
        keys |= {k for k in d if _is_norm(k)}
    keys = {k for k in keys if k.startswith(CTX_INSTRUMENTS)}
    out = {}
    for k in sorted(keys):
        def vals(ws):
            v = []
            for w in ws:
                d = cn.get(w) or {}
                if k in d and isinstance(d[k], (int, float)):
                    v.extend([d[k]] * (max(1, int(weights.get(w, 1)))
                                       if weights else 1))
            return v
        b, a = vals(base), vals(aligned)
        if not b or not a:
            continue
        nb = sum(1 for w in base if k in (cn.get(w) or {}))
        na = sum(1 for w in aligned if k in (cn.get(w) or {}))
        out[k] = (statistics.mean(b), statistics.mean(a),
                  (nb + na) / max(1, len(base) + len(aligned)))
    return out


def counts_for(frame):
    """{word: agreement count} for one frame. -> dict"""
    import pooled_tables as PT
    got = PT.pooled(frame)
    if not got:
        return {}
    return {w: max(f, r) for w, (f, r, _s) in got[0].items()}


def rows(path, weight=False, min_coverage=0.0, want_ctx=False):
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
        cb, ca, ccov = charge_sides(rec["frame"], base, aligned, wts)
        ctx = ctx_sides(rec["frame"], base, aligned, wts) if want_ctx else {}
        out.append({"ctx": ctx, "charge_base": cb, "charge_aligned": ca, "charge_cov": ccov,
                    "frame": rec["frame"], "name": rec["name"],
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


def report(rs, label="", min_rel=20):
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
    ch = [(r["charge_base"], r["charge_aligned"]) for r in rs
          if r["charge_base"] is not None]
    if len(ch) >= 6:
        d = [a - b for b, a in ch]
        _w, p, n = wilcoxon(d)
        pos = sum(1 for x in d if x > 0)
        star = "  <<<" if p is not None and p < 0.01 else ""
        print("%-26s %8.3f %8.3f %+8.3f %4d/%-4d %9s%s"
              % ("charge.scene (CONTEXTUAL)", statistics.mean(b for b, _a in ch),
                 statistics.mean(a for _b, a in ch), statistics.mean(d),
                 pos, n, ("%.2g" % p) if p is not None else "-", star))
        print("%-26s %d of %d relations; %.0f%% of their words rated"
              % ("", len(ch), len(rs),
                 100 * statistics.mean(r["charge_cov"] for r in rs
                                       if r["charge_base"] is not None)))
    ctxkeys = collections.Counter()
    for r in rs:
        ctxkeys.update(r.get("ctx", {}).keys())
    if ctxkeys:
        print()
        print("CONTEXTUAL -- a rater who saw the frame. delta = ALIGNED - BASE")
        print("%-40s %7s %7s %7s %6s %9s %6s"
              % ("instrument_scale", "base", "aligned", "delta", "n+/n", "p", "wcov"))
        rowsout = []
        for k, nk in ctxkeys.items():
            d = [r["ctx"][k][1] - r["ctx"][k][0] for r in rs if k in r["ctx"]]
            if len(d) < min_rel:
                continue
            _w, p, n = wilcoxon(d)
            if p is None:
                continue
            rowsout.append((p, k, statistics.mean(r["ctx"][k][0] for r in rs if k in r["ctx"]),
                            statistics.mean(r["ctx"][k][1] for r in rs if k in r["ctx"]),
                            statistics.mean(d), sum(1 for x in d if x > 0), n,
                            statistics.mean(r["ctx"][k][2] for r in rs if k in r["ctx"])))
        for p, k, b, a, dm, pos, n, wc in sorted(rowsout):
            star = "  <<<" if p < 0.01 else ""
            print("%-40s %7.3f %7.3f %+7.3f %3d/%-3d %9.2g %5.0f%%%s"
                  % (k, b, a, dm, pos, n, p, 100 * wc, star))
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
    ap.add_argument("--contextual", action="store_true",
                    help="also compare on the slot-rating instruments")
    ap.add_argument("--min-relations", type=int, default=20,
                    help="a contextual scale needs this many relations")
    a = ap.parse_args(argv)
    path = ALLWORDS if a.all_words else CONTENT
    rs = rows(path, a.weight, a.min_coverage, a.contextual)
    if not rs:
        raise SystemExit("no relations")
    report(rs, min_rel=a.min_relations, label="%s%s" % (os.path.basename(path),
                         "  [agreement-weighted]" if a.weight else ""))
    if a.csv:
        import csv
        with open(a.csv, "w", newline="", encoding="utf-8") as fh:
            #: charge is written too: it is the largest effect in the table
            #: and a results file that omits it is not the result.
            cols = ["frame", "name", "confidence", "coverage", "n_base",
                    "n_aligned", "charge_base", "charge_aligned", "charge_cov"]
            w = csv.writer(fh)
            w.writerow(cols + ["base_" + s for s in SCALES]
                       + ["aligned_" + s for s in SCALES])
            for r in rs:
                w.writerow([r[c] for c in cols]
                           + ["%.4f" % r["base"].get(s, float("nan")) for s in SCALES]
                           + ["%.4f" % r["aligned"].get(s, float("nan")) for s in SCALES])
        print("\nwrote %s (%d rows)" % (a.csv, len(rs)))
        #: LONG format, one row per (frame, scale). Wide would be ~80 columns
        #: of mostly-absent contextual scales; long keeps the absence visible
        #: as a missing row rather than as an empty cell that reads as zero.
        if any(r.get("ctx") for r in rs):
            cp = a.csv.replace(".csv", "_contextual.csv")
            with open(cp, "w", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh)
                w.writerow(["frame", "name", "scale", "base", "aligned",
                            "delta", "word_coverage"])
                n = 0
                for r in rs:
                    for k, (b, al, cv) in sorted(r.get("ctx", {}).items()):
                        w.writerow([r["frame"], r["name"], k, "%.4f" % b,
                                    "%.4f" % al, "%.4f" % (al - b), "%.3f" % cv])
                        n += 1
            print("wrote %s (%d rows)" % (cp, n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
