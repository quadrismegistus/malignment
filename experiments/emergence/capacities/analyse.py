"""Rhyme pull across the pretraining and SFT ladders. Ported from M05, not re-run.

    python -u analyse.py

READS THE ARCHIVE, WRITES NOTHING THERE. The fleet ran 2026-08-13 under
`meta/M05_emergence/plans/plan_verse_fleet.md` and cost ~$37.50; its parquets sit
in the read-only archive and no findings document was ever written against them.
This recomputes the headline numbers so the README quotes a producer rather than
a hand-copied table.

## THE INSTRUMENT

Instrument 1 of the plan's eight: RHYME PULL against the WITHIN-POEM UNCALLED
NULL. At a called slot -- a line-end whose scheme partner is in the window --
`called_mean` is the mass on the rhyme partner. `null_mean` is the same
rhyme-set's mass at uncalled line-ends and mid-line slots IN THE SAME POEM.
`pull_delta = called - null`.

The null is within-poem by design and NOT a matched control word-set: the plan
cites "the R decoy lesson" for refusing one. A matched set asserts a
comparability it has not earned; the same poem's uncalled slots do not.

## WHAT THE CORPUS SPLIT BUYS

`rhymed` splits the corpus into rhymed poems and free verse. Pull on rhymed
poems is CAPACITY -- the model can find the partner when the form calls for one.
Pull on free verse would be COMPULSION -- reaching for rhyme where the poem does
not ask. Reporting both is what separates a formal competence from a tic.

## WHAT THIS DOES NOT MEASURE

Pull is p(the poem's own partner) under teacher forcing. It is NOT rhyme
production in free generation, and the fleet deliberately deferred generation
("twp first, generation decided later"). RH's *Generative Formalism* reports
~50pp MORE rhyme after instruction-tuning, measured on generated verse. A model
can rhyme more in its own output while tracking a given poet's partner less;
these are different quantities and neither refutes the other.
"""

import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
LOCAL = os.path.join(HERE, "results")
ARCHIVE = os.path.expanduser("~/github/malign-logits/meta/M05_emergence/results")

#: LOCAL FIRST, archive as fallback. The parquets were COPIED here on
#: 2026-08-24 (copy, not move -- the archive is read-only and still holds them),
#: so this folder no longer depends on another checkout being present. The
#: fallback exists so the file still runs from a checkout where the copy has not
#: landed, and it prints which root it used rather than leaving it to be guessed.
RUNGS = os.path.join(LOCAL, "verse_capacity_rungs.parquet")
if not os.path.exists(RUNGS):
    RUNGS = os.path.join(ARCHIVE, "verse_capacity_rungs.parquet")


def main():
    import pandas as pd
    from scipy import stats

    if not os.path.exists(RUNGS):
        print("archive not found: %s" % RUNGS)
        return 1
    r = pd.read_parquet(RUNGS)
    print("reading %s" % ("results/ (local copy)" if RUNGS.startswith(LOCAL)
                          else "the M05 ARCHIVE -- local copy absent"))
    print("%d rung rows, %d checkpoints, ladders %s"
          % (len(r), r.model.nunique(), sorted(r.ladder.unique())))

    print()
    print("1. CAPACITY, NOT COMPULSION -- pull only where the poem rhymes")
    print("   %-8s %-7s %11s %10s %11s %9s" % ("ladder", "rhymed", "called", "null", "pull", "frac>0"))
    g = r.groupby(["ladder", "rhymed"])[["called_mean", "null_mean",
                                         "pull_delta_mean", "frac_positive"]].median()
    for (lad, rh), row in g.iterrows():
        print("   %-8s %-7s %11.4f %10.4f %11.4f %9.2f"
              % (lad, rh, row.called_mean, row.null_mean,
                 row.pull_delta_mean, row.frac_positive))

    print()
    print("2. ERA -- rhymed poems only")
    print("   %-8s %-9s %11s %9s" % ("ladder", "era", "pull", "frac>0"))
    for (lad, era), row in r[r.rhymed].groupby(["ladder", "era"])[
            ["pull_delta_mean", "frac_positive"]].median().iterrows():
        print("   %-8s %-9s %11.4f %9.2f" % (lad, era, row.pull_delta_mean, row.frac_positive))

    #: THE COMPARISON THAT MATTERS, AND THE ONE THAT IS EASY TO GET BACKWARDS.
    #: Group medians across arms compare ladders spanning different developmental
    #: ranges: pretrain's median is dragged down by early rungs where the
    #: capacity does not exist yet, which makes SFT look like it ADDS pull. The
    #: trajectories say the opposite. Report the trend within each arm.
    print()
    print("3. THE TRAJECTORIES -- rhymed, olmo, within arm")
    o = r[(r.ladder == "olmo") & (r.rhymed)]
    for arm in ("pretrain", "Think-SFT"):
        d = (o[o.arm == arm].groupby("model")
             .agg(ordinal=("ordinal", "first"), pull=("pull_delta_mean", "mean"))
             .sort_values("ordinal"))
        if len(d) < 3:
            continue
        rho, p = stats.spearmanr(d.ordinal, d.pull)
        print("   %-10s %2d rungs   %.4f -> %.4f   Spearman %+.3f  p=%.2e"
              % (arm, len(d), d.pull.iloc[0], d.pull.iloc[-1], rho, p))

    print()
    print("4. THE ENDPOINTS -- n=1 each, DESCRIPTIVE ONLY, no DPO ladder exists")
    for m in sorted(o[o.arm == "other"].model.unique()):
        print("   %-40s %.4f" % (m.split("/")[-1], o[o.model == m].pull_delta_mean.mean()))
    print("   (the fleet has 42 pretrain and 43 Think-SFT rungs but exactly ONE")
    print("    DPO checkpoint, so no SFT-vs-DPO comparison is available here.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
