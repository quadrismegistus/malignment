"""WHEN does a word move? All fallers and all risers, no pairing.

    python -u timing.py

**DISCOVERED ARM.** Not in `REGISTRATION.md`. RH, 2026-09-06: *"isn't this just
the top riser/faller still? How do we scale this up? Do we need word-pairs?
Are we measuring within prompts as we should be? Can we do something more
aggregative: the average timestep at which fallers peak vs risers peak, by kind,
within prompt, aggregated to all prompts by kind, generally as well as dosed by
lift?"* All four criticisms are correct and this file answers them.

## WHAT WAS WRONG WITH Q1/Q3/f04_spirit

They used ONE faller and ONE riser per prompt -- about 1,000 word-instances out
of tens of thousands -- selected by |delta| or by scene. **The pairing was never
required by the question.** "Does the faller move before the riser" is a
comparison of two DISTRIBUTIONS of timings; it does not need a faller matched to
a particular riser, and matching them threw away most of the data and imported a
selection rule that turned out to favour function words.

## THE STATISTIC: CENTRE OF MASS OF MOVEMENT

From the `increment` edges (rung n -> n+1), which the earlier arms never touched:

    t_move(w) = SUM_n  step_n * |d_n|  /  SUM_n |d_n|

where `d_n` is the per-step change. It is the mass-weighted average step at which
the word actually moved.

**Why this and not AUC.** AUC needed a signed total in the denominator, so it
broke on words that overshoot and revert, and -- found the hard way -- it read
the 29.5% of fallers that AMPLIFY before falling as *late* rather than as early
and non-monotonic. `t_move` weights by |movement| wherever it happens, so an
amplification at step 1000 counts as movement at step 1000, which is what it is.

**Why not argmax.** `peak` in the ask is one step and is noisy; the centre of
mass uses the whole trajectory. `--peak` reports argmax as a check.

## THE UNIT IS STILL THE PROMPT

Words within a prompt are not independent -- they compete for the same mass. So
timings are averaged WITHIN a prompt first (mean over its fallers, mean over its
risers), the per-prompt lag is `mean_riser - mean_faller`, and the prompt is the
replicate. This is what "within prompts as we should be" requires, and it is
preserved rather than abandoned when the pairing goes.
"""
import argparse, collections, math, os, statistics as S, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
from malignment import ch                                          # noqa: E402
from analyse import binom, ci, END                                 # noqa: E402
import json                                                        # noqa: E402

ANN = os.path.join(HERE, "results", "charge_olmo_thinksft_v3.jsonl")
MIN_MOVE = 0.003          #: CANONICAL's delta; below it a "timing" is noise


def timings(peak=False):
    """-> [(prompt, word, cls, t_move)] for every faller and riser."""
    agg = ("argMax(step_aligned, abs(delta))" if peak else
           "sum(step_aligned * abs(delta)) / sum(abs(delta))")
    q = ("""
    WITH cls AS (
      SELECT prompt, word, cls FROM {db}.movement_rungs
      WHERE kind='base_rooted' AND step_aligned=%d AND cls IN ('faller','riser')
        AND prompt IN (SELECT DISTINCT prompt FROM {db}.prompts WHERE prompt != '')
    )
    SELECT i.prompt AS prompt, i.word AS word, cls.cls AS cls,
           %s AS t_move, sum(abs(i.delta)) AS tv
    FROM {db}.movement_rungs AS i INNER JOIN cls
      ON i.prompt = cls.prompt AND i.word = cls.word
    WHERE i.kind='increment'
    GROUP BY prompt, word, cls
    HAVING tv >= %f
    """ % (END, agg, MIN_MOVE))
    return [(r["prompt"], r["word"], r["cls"], float(r["t_move"]))
            for r in ch.query(q)]


def charge():
    """-> {(prompt, word): (kind, scene - frame)}."""
    out = {}
    with open(ANN) as fh:
        for line in fh:
            r = json.loads(line)
            for w in r["words"]:
                out[(r["prompt"], w["word"])] = (w["kind"], w["scene"] - r["frame"])
    return out


def report(label, lags):
    if len(lags) < 5:
        print("  %-30s n=%-4d (too few)" % (label, len(lags)))
        return
    up = sum(1 for v in lags if v > 0)
    lo, hi = ci(lags)
    print("  %-30s n=%-4d median %+8.0f steps  %3d/%-3d  p=%.5f  CI [%+.0f, %+.0f]"
          % (label, len(lags), S.median(lags), up, len(lags) - up,
             binom(min(up, len(lags) - up), len(lags)), lo, hi))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--peak", action="store_true",
                    help="argmax |delta| instead of the centre of mass")
    a = ap.parse_args(argv)

    t = timings(a.peak)
    ch_ = charge()
    print("DISCOVERED ARM -- not registered.  statistic: %s"
          % ("argmax |delta| (peak)" if a.peak else "centre of mass of |movement|"))
    print("word-instances with movement >= %.3f: %d  (Q1 used ~1,010)"
          % (MIN_MOVE, len(t)))
    nf = sum(1 for x in t if x[2] == "faller")
    print("  fallers %d | risers %d | prompts %d"
          % (nf, len(t) - nf, len({x[0] for x in t})))
    print()

    #: within prompt first -- words in a prompt compete for the same mass
    byp = collections.defaultdict(lambda: {"faller": [], "riser": []})
    for p, w, c, tm in t:
        byp[p][c].append(tm)
    lag = [S.mean(d["riser"]) - S.mean(d["faller"])
           for d in byp.values() if d["faller"] and d["riser"]]
    print("GENERAL: per-prompt mean(riser t_move) - mean(faller t_move)")
    print("  positive = fallers move EARLIER than risers")
    report("all prompts", lag)
    print()

    print("BY THE FALLER's KIND (the faller side only, risers unrestricted)")
    bk = collections.defaultdict(lambda: collections.defaultdict(
        lambda: {"faller": [], "riser": []}))
    for p, w, c, tm in t:
        if c == "faller":
            k = ch_.get((p, w))
            if k:
                bk[k[0]][p]["faller"].append(tm)
        else:
            for k in bk:
                bk[k][p]["riser"].append(tm)
    #: risers added to every kind's prompt bucket above, so each kind compares
    #: ITS fallers against the SAME prompt's full riser set
    for k in sorted(bk, key=lambda z: -len(bk[z])):
        lg = [S.mean(d["riser"]) - S.mean(d["faller"])
              for d in bk[k].values() if d["faller"] and d["riser"]]
        report(k, lg)
    print()

    print("DOSED BY LIFT (scene - frame) of the faller")
    bl = collections.defaultdict(lambda: collections.defaultdict(
        lambda: {"faller": [], "riser": []}))
    for p, w, c, tm in t:
        if c == "faller":
            k = ch_.get((p, w))
            if k:
                bl[min(k[1], 3)][p]["faller"].append(tm)
        else:
            for k in bl:
                bl[k][p]["riser"].append(tm)
    for k in sorted(bl):
        lg = [S.mean(d["riser"]) - S.mean(d["faller"])
              for d in bl[k].values() if d["faller"] and d["riser"]]
        report("lift %s" % (">=+3" if k == 3 else "%+d" % k), lg)
    print()
    print("  raw timings: faller median %.0f | riser median %.0f steps"
          % (S.median([x[3] for x in t if x[2] == "faller"]),
             S.median([x[3] for x in t if x[2] == "riser"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
