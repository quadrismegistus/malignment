"""Where does the mass sit, by CHARGE LEVEL, before and after alignment?

    python -u mass_by_charge.py            # build results/mass_by_charge.json
    python -u mass_by_charge.py --limit 5  # a few lineages, to check the shape

## THE RATING IS AN INTEGER AND THAT IS THE POINT

`charge.scene(prompt)` returns floats, but only because it AVERAGES a word's
rating over the 50 lineages that rated it. `charge.words(prompt, base)` is one
cell's annotation and every value is an integer 1-7 -- swept over 5,372
(word, cell) ratings, zero non-integer, values exactly {1..7}. So banding is not
needed here and must not be invented: seven levels is what was annotated.

**This is the within-cell grain the existence test already uses.** Part 1
regresses delta on scene inside a cell; this sums p inside a cell at each level
instead, which is the same population read as levels rather than as a slope.

## WHAT IS SUMMED, AND THE ONE THING IT IS NOT

For each cell (one prompt x one lineage) and each level k:

    mass_base[k]    = sum of p_base    over that cell's words rated k
    mass_aligned[k] = sum of p_aligned over that cell's words rated k

**NOT normalised within the cell.** A share would answer a different question --
"of the mass twp covered, what fraction sat at level k" -- and the covered mass
itself moves under alignment, so a share folds two changes into one number. The
level IS the quantity: probability that the next word is one rated k.

The unit of inference is the LINEAGE, as everywhere in this folder: mean over
that lineage's cells, then a median and a bootstrap interval across lineages.

## ONLY WORDS THE ANNOTATION AND THE CORPUS BOTH HOLD

A cell's word list is what that base arm offered, so it is not a common
population across lineages -- and `movement_v4` holds rows the annotation never
saw and vice versa. Both counts are reported. A word present in one and absent
from the other is DROPPED, never counted as zero: below theta means smaller than
0.001, and unrated means unrated.
"""
import argparse, collections, json, os, statistics as st, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, ROOT)
OUT = os.path.join(HERE, "results", "mass_by_charge.json")
SCENE_LEVELS = list(range(1, 8))
#: **LIFT'S TAILS ARE POOLED, AND THE POOLING IS MEASURED NOT GUESSED.** Over
#: 1,708,870 word-ratings: lift 0 alone is 76.8% of them and 75.6% of the base
#: mass; -1..+4 covers 99.3%. Below -1 is 0.4% and above +4 is 0.3%, which
#: cannot carry a median across 50 lineages. Pooled into end buckets rather
#: than dropped, so the seven lines still sum to the whole rated mass.
LIFT_LEVELS = [-1, 0, 1, 2, 3, 4]
LIFT_LO, LIFT_HI = -1, 4


def annotation(by):
    """{(prompt, base): {word: level}} read straight from the source jsonl.

    **NOT `charge.words()`, and the reason is `frame`.** That accessor returns
    per-word scene and nothing else, so lift -- which needs the CELL's frame
    rating -- is not reachable through it. The raw record carries both, and
    both are integers: frame is 1-7 (checked over 4,000 cells, zero
    non-integer) and so is scene, so `scene - frame` is an integer per cell and
    no rounding or banding is invented anywhere in this file.
    """
    from malignment import charge
    out = {}
    for src in charge.sources():
        if "_zh" in os.path.basename(src):
            continue                       # English battery only, as Part 1
        for line in open(src, "rb"):
            r = json.loads(line)
            fr = r.get("frame")
            if fr is None:
                continue
            m = {}
            for w in r["words"]:
                k = int(w["scene"])
                if by == "lift":
                    k = max(LIFT_LO, min(LIFT_HI, k - int(fr)))
                m[w["word"]] = k
            out[(r["prompt"], r["base"])] = m
    return out


def build(limit=None, by="scene"):
    from malignment import charge, roster, vectors as V
    levels = SCENE_LEVELS if by == "scene" else LIFT_LEVELS
    ann = annotation(by)
    print("annotation: %d cells, by=%s, levels %s" % (len(ann), by, levels),
          flush=True)
    eps, unresolved = roster.endpoints()
    rated = {p for p, _ in ann}
    pairs = sorted((b, a) for b, a in eps.items())
    if limit:
        pairs = pairs[:int(limit)]
    per_lineage, matched, unmatched, skipped = [], 0, 0, 0
    for i, (b, a) in enumerate(pairs, 1):
        t0 = time.time()
        rows = V.rows(
            "SELECT prompt, word, p_base, p_aligned FROM movement_v4 "
            "WHERE base={b:String} AND aligned={a:String} "
            "AND frame_base='' AND frame_aligned=''", b=b, a=a)
        if not rows:
            skipped += 1
            print("  %2d/%d %-46s NO ROWS" % (i, len(pairs), b.split("/")[-1][:46]),
                  flush=True)
            continue
        by_prompt = collections.defaultdict(list)
        for r in rows:
            if r["prompt"] in rated:
                by_prompt[r["prompt"]].append(r)
        cells = []
        for p, rs in by_prompt.items():
            w = ann.get((p, b))
            if not w:
                continue
            mb = collections.Counter()
            ma = collections.Counter()
            hit = False
            for r in rs:
                rec = w.get(r["word"])
                if rec is None:
                    continue
                k = rec
                mb[k] += float(r["p_base"] or 0.0)
                ma[k] += float(r["p_aligned"] or 0.0)
                hit = True
            if hit:
                cells.append((mb, ma))
        if not cells:
            skipped += 1
            continue
        matched += len(cells)
        rec = {"lineage": "%s>%s" % (b, a), "n_cells": len(cells)}
        for k in levels:
            rec["base_%d" % k] = st.mean([c[0].get(k, 0.0) for c in cells])
            rec["aligned_%d" % k] = st.mean([c[1].get(k, 0.0) for c in cells])
        per_lineage.append(rec)
        print("  %2d/%d %-46s %5d cells  %.1fs"
              % (i, len(pairs), b.split("/")[-1][:46], len(cells),
                 time.time() - t0), flush=True)
    return {"levels": levels, "by": by, "n_lineages": len(per_lineage),
            "n_cells": matched, "skipped_lineages": skipped,
            "built": time.strftime("%Y-%m-%d %H:%M"),
            "per_lineage": per_lineage}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--by", default="scene", choices=["scene", "lift"],
                    help="scene = the word's own charge 1-7. lift = scene minus "
                         "the CELL's frame rating, an integer per cell, clamped "
                         "to -1..+4 which is 99.3%% of rated mass.")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()
    d = build(a.limit, by=a.by)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(d, open(a.out, "w"), indent=1)
    print("\n%d lineages, %d cells -> %s" % (d["n_lineages"], d["n_cells"], a.out))
    print("\n%-8s %14s %14s %9s" % ("level", "base mass", "aligned mass", "change"))
    for k in d["levels"]:
        b = st.median([r["base_%d" % k] for r in d["per_lineage"]])
        al = st.median([r["aligned_%d" % k] for r in d["per_lineage"]])
        print("%-8d %14.5f %14.5f %+9.1f%%"
              % (k, b, al, (100.0 * (al - b) / b) if b else float("nan")))


if __name__ == "__main__":
    main()
