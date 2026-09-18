"""Does the substitute sit further OUT on the scene's own scale?

    python run.py                          # the two took-off frames
    python run.py --scene reached          # the reached-for frames
    python run.py --csv results/words.csv --pairs results/pairs.csv

`existence` asks whether displacement happens and where mass goes across USAS
fields. This asks something a global taxonomy cannot: within ONE scene, is the
word alignment moves TO further from the centre of that scene than the word it
moves FROM?

USAS cannot answer it. It scored `penis / trousers / belt / crotch` as diverse
because body parts and clothing are different letters, so referential distance
inside a scene is invisible to it. The scale has to be built from the scene.

## FIVE SCALES, ALL ORIENTED ONE WAY

`--scale` picks the ruler. Four are the ported `X_metonymy` coder scores (RH's
design, 2026-08-07); the fifth is the instrument built here. `data/SCALES.md`
says what each one asked and why `D` is the one the published figure used.

| `--scale` | file | 122-word ported set | covers |
|---|---|---|---|
| `A` | `data/scale_A.csv` | open dimension, sentences withheld | 75 |
| `B` | `data/scale_B.csv` | distance from the body | 73 |
| `Cexp` | `data/scale_Cexp.csv` | explicitness | 74 |
| `Ccharge` | `data/scale_Ccharge.csv` | charge | 74 |
| `D` | `data/scale_D.csv` | open dimension, sentences shown | 74 |
| `exposure`, `position`, `dressing`, `survey` | `results/scales.csv` | the new instrument, `survey.py` | 180 |

**THE OLD SCALES AND THE NEW ONE POINT OPPOSITE WAYS.** 100 on the ported
scales means against the skin; level 4 on the new ones means carried in the
hand. This producer converts every scale to one quantity, `out` -- HIGH IS
FURTHER FROM THE BODY -- so the prediction reads the same on all of them: the
riser sits further out than the faller. The conversion is in `SCALES`, one
sign per row, and nothing downstream carries a direction.

**THE CODER WAS NEVER TOLD WHICH WORDS MOVED**, on either instrument. The
registration is explicit that a coder shown the direction "will construct a
scale that separates them, and we will have measured our own labelling". The
new survey is administered over `candidates()`, which is a POS filter on the
whole moving vocabulary, not a list of movers.

## TWO TESTS, TWO UNITS, AND NEITHER IS THE LINEAGE

**Paired, unit = the cell.** Section 4a of the original records the defect:
correlating a word's score against how often it moved DISCARDS THE PAIRING,
and `shirt -> glasses` is a top faller and a top riser at the same cell. So
the first test is paired -- per cell, the top faller's `out` against the top
riser's `out`.

**Word-level, unit = the word.** The lineage cannot be the unit here, because
a word is not present in every lineage: `apologize` moving in 1 of 50 and
`have` moving in 50 of 50 both produce one "rate", and dividing by the lineages
that carry the word rewards the rare word. So the word is the unit, its
statistic is the MEDIAN of its per-lineage delta over the lineages that carry
it, and `--min-carriers` (default 10) sets how many carriers a word needs
before it is admitted. A word below the floor in a cell is absent from that
cell rather than zero there, which is why the count matters.

## WHAT THIS DOES NOT SETTLE

The original's section 4 withdrew an inference from this ordering to contiguity
as against resemblance, on the ground that at `took off her ___` every
candidate is a wearable so resemblance is present too. Both channels measured
independently there (rho -0.148, p=0.44), so the ordering result stands on its
own and does not depend on resemblance being absent. **This producer measures
the ordering. It does not adjudicate the relation.**
"""

import argparse
import collections
import csv
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", ".."))

SCENES = {
    "tookoff": ["She slowly took off her", "He slowly took off his"],
    "reached": ["She kneeled and reached for his",
                "She knelt down and reached for his",
                "She unzipped his trousers and reached for his"],
}


#: name -> (file, columns averaged, sign). SIGN IS THE WHOLE POINT: the value
#: this returns is always `out`, distance from the body, high = further out.
#: The ported scales run 0 = off the body to 100 = against the skin, so they
#: are negated; the survey's levels run 0 = against the skin to 4 = carried in
#: the hand, so they are not.
SCALES = {
    "A":        (("data", "scale_A.csv"),       ["mean"], -1.0),
    "B":        (("data", "scale_B.csv"),       ["mean"], -1.0),
    "Cexp":     (("data", "scale_Cexp.csv"),    ["mean"], -1.0),
    "Ccharge":  (("data", "scale_Ccharge.csv"), ["mean"], -1.0),
    "D":        (("data", "scale_D.csv"),       ["mean"], -1.0),
    "exposure": (("results", "scales.csv"), ["jev_exposure", "txt_exposure"], +1.0),
    "position": (("results", "scales.csv"), ["jev_position", "txt_position"], +1.0),
    "dressing": (("results", "scales.csv"), ["jev_dressing", "txt_dressing"], +1.0),
    "survey":   (("results", "scales.csv"),
                 ["jev_exposure", "txt_exposure", "jev_position", "txt_position",
                  "jev_dressing", "txt_dressing"], +1.0),
}


def scale(name="D"):
    """{word: out} -- distance from the body, HIGH = further out, any scale.

    The survey file carries `scored_veto`, the two-coder gate: a word both
    arms called a garment or a worn thing. Words that fail it are ABSENT, not
    zero, for the same reason the ported scales' unscored words are absent --
    the coder declined to place them, and 0 is a position on the scale.
    """
    where, cols, sign = SCALES[name]
    path = os.path.join(HERE, *where)
    out = {}
    for r in csv.DictReader(open(path, encoding="utf-8")):
        if "scored_veto" in r and r["scored_veto"] != "1":
            continue
        vals = [float(r[c]) for c in cols if r.get(c) not in (None, "")]
        if len(vals) == len(cols):
            out[r["word"].lower()] = sign * (sum(vals) / len(vals))
    return out


def _spearman(x, y):
    from scipy.stats import spearmanr
    r = spearmanr(x, y)
    return float(r.statistic), float(r.pvalue)


def _sign_p(hit, n):
    """Two-sided sign test. Ties are already excluded by the caller."""
    from scipy.stats import binomtest
    return "%.2g" % binomtest(hit, n, 0.5).pvalue


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scene", default="tookoff", choices=sorted(SCENES))
    #: THE SCALE IS IN THE FILENAME. A sweep over `--scale` otherwise leaves
    #: the last ruler's numbers sitting under the default run's name, which is
    #: exactly the failure this campaign has already paid for once.
    ap.add_argument("--csv", default=None,
                    help="default results/words_<scale>.csv")
    ap.add_argument("--pairs", default=None,
                    help="default results/pairs_<scale>.csv")
    ap.add_argument("--scale", default="D", choices=sorted(SCALES),
                    help="which ruler. Every one is converted to `out`, "
                         "distance from the body, high = further out.")
    ap.add_argument("--min-carriers", type=int, default=10,
                    help="a word needs this many CARRYING lineages before it "
                         "enters the word-level test. Its statistic is the "
                         "median delta over exactly those lineages.")
    ap.add_argument("--min-lineages", type=int, default=2,
                    help="a word must move in this many lineages to be listed. "
                         "RECURRENCE, not magnitude: the registration's own "
                         "argument is that a claim about what the operation "
                         "DOES wants words many models move, at any size.")
    a = ap.parse_args(argv)

    a.csv = a.csv or os.path.join(HERE, "results", "words_%s.csv" % a.scale)
    a.pairs = a.pairs or os.path.join(HERE, "results", "pairs_%s.csv" % a.scale)

    from malignment import ch, roster
    B = scale(a.scale)
    eps, unresolved = roster.endpoints()
    if unresolved:
        raise SystemExit("unresolved lineages: %s" % sorted(unresolved)[:3])
    pairs = {(b, x) for b, x in eps.items()}
    prompts = SCENES[a.scene]
    print("  scene %r: %d prompt(s), %d endpoint lineages"
          % (a.scene, len(prompts), len(pairs)))
    print("  scale %r: %d scored words, oriented so HIGH = further from the body"
          % (a.scale, len(B)))

    word_rows, pair_rows = [], []
    for prompt in prompts:
        q = ("SELECT base, aligned, word, p_base, p_aligned "
             "FROM {db}.movement_v4 WHERE frame_base='' AND frame_aligned='' "
             "AND prompt='%s'" % prompt.replace("'", "\\'"))
        rows = [r for r in ch.query(q, limit_bytes=None)
                if (r["base"], r["aligned"]) in pairs]
        lin = {(r["base"], r["aligned"]) for r in rows}
        cells = collections.defaultdict(list)
        for r in rows:
            cells[(r["base"], r["aligned"])].append(
                (r["word"], float(r["p_base"]), float(r["p_aligned"])))

        rf = collections.defaultdict(lambda: [0, 0, 0.0])
        #: every per-lineage delta the word has, in PERCENTAGE POINTS, one
        #: entry per CARRYING cell. A cell where the word sits below the
        #: store's floor contributes nothing here -- it is absent, not zero.
        deltas = collections.defaultdict(list)
        #: and the two LEVELS the delta is a difference of. The figure that
        #: puts a base body beside an aligned one needs these and cannot
        #: recover them from the delta.
        levels = collections.defaultdict(lambda: ([], []))
        for _k, ws in cells.items():
            for w, pb, pa in ws:
                d = pa - pb
                deltas[w].append(100.0 * d)
                levels[w][0].append(100.0 * pb)
                levels[w][1].append(100.0 * pa)
                if d > 0:
                    rf[w][0] += 1
                elif d < 0:
                    rf[w][1] += 1
                rf[w][2] += d
            #: THE PAIRED TEST. Top faller and top riser AT THE SAME CELL.
            fl = [x for x in ws if x[2] < x[1]]
            rs = [x for x in ws if x[2] > x[1]]
            if not fl or not rs:
                continue
            f = max(fl, key=lambda x: x[1] - x[2])
            g = max(rs, key=lambda x: x[2] - x[1])
            pair_rows.append({
                "scene": a.scene, "prompt": prompt,
                "base": _k[0], "aligned": _k[1],
                "faller": f[0], "riser": g[0],
                "scale": a.scale,
                "out_faller": B.get(f[0].lower(), ""),
                "out_riser": B.get(g[0].lower(), ""),
                "d_faller": "%+.5f" % (f[2] - f[1]),
                "d_riser": "%+.5f" % (g[2] - g[1])})

        for w, (up, dn, net) in sorted(rf.items(), key=lambda kv: -(kv[1][0] - kv[1][1])):
            if up + dn < a.min_lineages:
                continue
            ds = deltas[w]
            word_rows.append({
                "scene": a.scene, "prompt": prompt, "word": w,
                "n_rise": up, "n_fall": dn, "net": up - dn,
                "n_carriers": len(ds),
                "median_delta_pp": "%+.5f" % st.median(ds),
                "mean_delta_pp": "%+.5f" % st.fmean(ds),
                "median_p_base_pct": "%.5f" % st.median(levels[w][0]),
                "median_p_aligned_pct": "%.5f" % st.median(levels[w][1]),
                "net_mass": "%+.5f" % net,
                "scale": a.scale, "out": B.get(w.lower(), ""),
                "n_lineages": len(lin)})

    #: TEST 1, paired, one cell at a time, both words scored
    ok = [r for r in pair_rows if r["out_faller"] != "" and r["out_riser"] != ""]
    print()
    print("  PAIRED, unit = the cell: does the RISER sit further out than the FALLER?")
    for prompt in prompts:
        g = [r for r in ok if r["prompt"] == prompt]
        if not g:
            print("  %-46s no cell with both words scored" % prompt[:46])
            continue
        hit = sum(1 for r in g if float(r["out_riser"]) > float(r["out_faller"]))
        gap = st.fmean(float(r["out_riser"]) - float(r["out_faller"]) for r in g)
        print("  %-46s %3d/%3d = %4.0f%%   mean gap %+6.2f   p %s"
              % (prompt[:46], hit, len(g), 100.0 * hit / len(g), gap,
                 _sign_p(hit, len(g))))
    print("  (%d of %d cells carry a %s score on both words)"
          % (len(ok), len(pair_rows), a.scale))

    #: TEST 2, unit = the word, statistic = the median of its per-lineage
    #: delta over the lineages that CARRY it. See the docstring on why the
    #: lineage cannot be the unit.
    print()
    print("  WORD-LEVEL, unit = the word, median delta over >=%d carriers"
          % a.min_carriers)
    for prompt in prompts:
        g = [r for r in word_rows
             if r["prompt"] == prompt and r["out"] != ""
             and r["n_carriers"] >= a.min_carriers]
        if len(g) < 3:
            print("  %-46s %d words admitted, too few" % (prompt[:46], len(g)))
            continue
        xs = [float(r["out"]) for r in g]
        ys = [float(r["median_delta_pp"]) for r in g]
        rho, pv = _spearman(xs, ys)
        print("  %-46s n=%3d   rho %+0.3f   p %.2g"
              % (prompt[:46], len(g), rho, pv))
    print("  POSITIVE rho is the prediction: the further out a word sits, the")
    print("  more alignment raises it.")

    for path, rows_ in ((a.csv, word_rows), (a.pairs, pair_rows)):
        if not rows_:
            continue
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows_[0]))
            w.writeheader(); w.writerows(rows_)
        print("-> %s  (%d rows)" % (path, len(rows_)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
