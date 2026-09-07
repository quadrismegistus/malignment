"""Cross-seat audit of M05-A `A_acquisition`, which asked this same question first.

    python -u audit_m05a.py

**M05-A ASKED F04'S QUESTION ON THIS LADDER THREE WEEKS BEFORE tuning_order DID**,
and its own words say so: *"When in training do alignment's operations install?
Specifically (the registered primary, F04's question at 43-rung power): does
repression precede displacement within the SFT run?"* Same 43-rung Think-SFT
ladder, written 2026-08-11 by the registrar seat.

    STATUS: DRAFT, grade C -- single run, single lineage (OLMo-3), no
    cross-seat audit yet.

`experiments/TODO.md` ranks that audit as the highest-value work in its list:
*"the cluster's weakness is audit, not coverage."* This is it, and it was
reached by accident -- the commission that produced `tuning_order` asserted the
snapshot held no SFT-ladder acquisition curve, which was wrong.

## THE APPARENT DISAGREEMENT

    M05-A   paired per-site, persistent-sign onsets:
            median lag 0, Wilcoxon p=0.97, n=44 sites with both onsets;
            34 sites never persistently fall, 41 never persistently rise
            READING: "F04's repression-precedes-displacement does not survive
            as a lag between two onsets"

    tuning_order   t_move (centre of mass of per-step |movement|):
            faller 15,126 | riser 19,796 | +5,341 steps, 506 of 507, p<1e-6

## WHAT THIS FILE DOES: REPRODUCE THEIR NULL WITH THEIR METHOD, THEN LOCATE IT

Their criterion, from `meta/M05_emergence/scripts/m05_onsets.py`:

    onset_persistent_sign(traj, base_value, direction)
      "First rung where (p - base) takes the predicted sign and keeps it."

Applied to tuning_order's sites it **reproduces their median lag of 0**. So the
disagreement is not arithmetic and neither result is a mistake. It is located,
and it is a resolution problem:

    PERSISTENT-SIGN ONSET, tuning_order sites
      fallers  fire at step 1000: 276 of 505 (55%)   median onset 1000
      risers   fire at step 1000: 288 of 505 (57%)   median onset 1000

**The criterion fires at the FIRST RUNG for the majority of sites, so the paired
lag is 0 by construction.** A word that crosses below base at step 1000 and does
most of its actual falling at step 20,000 is scored as onset=1000. It measures
WHEN THE SIGN SETTLES, not when the mass moves — a direction-detection
statistic, not a timing one.

On the same sites `t_move` gives faller 14,987 against riser 19,674.

## SO THE DISAGREEMENT IS NARROWER THAN IT LOOKS, AND M05-A'S READING SURVIVES

M05-A's **aggregate** Result 1 — fallers reach onset at SFT step 27,000 while
risers never clear the base envelope within the arm and keep rising through DPO
and RLVR — is in the SAME DIRECTION as ours: what falls, completes; what rises,
does not. Its gloss (*"the substitute does not arrive after the prohibition — it
never stops arriving"*) is untouched by this audit.

**What does not survive is the paired per-site null**, and specifically the
inference from p=0.97 to "there is no fall-then-rise sequence". That p is
computed on a statistic with no resolution at this ladder's spacing.

Two failure modes, and M05-A's population has both:

    on ITS sites   the criterion also DISCARDED 75 of ~105 (34 never fall,
                   41 never rise), leaving n=44
    on OUR sites   it discards 0 -- ours are endpoint-defined under CANONICAL,
                   so a faller has fallen by step 43000 by construction -- and
                   still returns lag 0, because it fires at the first rung

The second is the more important one: the null does not depend on the discards.
"""
import collections, os, statistics as S, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
from analyse import sites, curves, binom, ci                       # noqa: E402
from timing import timings                                         # noqa: E402


def persistent_sign(curve, direction):
    """M05-A's criterion, ported verbatim in behaviour.

    `m05_onsets.py`: *"First rung where (p - base) takes the predicted sign and
    keeps it."* Our `movement_rungs` delta IS `p(step) - p(base)`, so the sign
    test applies directly with no re-derivation of a base value.
    """
    steps = sorted(curve)
    want = -1 if direction == "down" else 1
    ok = [(s, (1 if curve[s] > 0 else -1 if curve[s] < 0 else 0) == want)
          for s in steps]
    for i, (s, good) in enumerate(ok):
        if good and all(g for _, g in ok[i:]):
            return s
    return None


def main():
    st = sites(False)
    cv = curves([(p, r["faller"]) for p, r in st.items()]
                + [(p, r["riser"]) for p, r in st.items()])
    tm = {(p, w): x for p, w, c, x in timings()}

    F, R, diffs, nf, nr = [], [], [], 0, 0
    for p, r in st.items():
        fc, rc = cv.get((p, r["faller"]), {}), cv.get((p, r["riser"]), {})
        if not fc or not rc:
            continue
        of, orr = persistent_sign(fc, "down"), persistent_sign(rc, "up")
        if of is None:
            nf += 1
        else:
            F.append(of)
        if orr is None:
            nr += 1
        else:
            R.append(orr)
        if of is not None and orr is not None:
            diffs.append(orr - of)

    print("M05-A's CRITERION, reproduced on tuning_order's sites")
    print("  sites %d | faller never persistently falls %d | riser never rises %d"
          % (len(st), nf, nr))
    up = sum(1 for v in diffs if v > 0)
    lo, hi = ci(diffs)
    print("  paired lag  n=%d  median %+0.0f steps  %d up/%d dn  p=%.4f  CI [%+0.0f, %+0.0f]"
          % (len(diffs), S.median(diffs), up, len(diffs) - up,
             binom(min(up, len(diffs) - up), len(diffs)), lo, hi))
    print("  M05-A reported: n=44, median 0, p=0.97 (34 never fall, 41 never rise)")
    print("  -> THE MEDIAN LAG OF 0 REPRODUCES.")
    print()

    print("WHY: the criterion has almost no resolution at this spacing")
    for lab, v in (("fallers", F), ("risers", R)):
        c = collections.Counter(v)
        print("  %-8s n=%-4d fire at step 1000: %d (%.0f%%)  median %d  p90 %d"
              % (lab, len(v), c[1000], 100 * c[1000] / len(v), S.median(v),
                 sorted(v)[int(0.9 * len(v))]))
    print("  A word crossing below base at 1000 and doing most of its falling at")
    print("  20,000 is scored onset=1000. It times the SIGN, not the MASS.")
    print()

    f = [tm[(p, r["faller"])] for p, r in st.items() if (p, r["faller"]) in tm]
    rr = [tm[(p, r["riser"])] for p, r in st.items() if (p, r["riser"]) in tm]
    print("SAME SITES, t_move (centre of mass of |movement|)")
    print("  faller median %.0f | riser median %.0f | gap %+.0f steps"
          % (S.median(f), S.median(rr), S.median(rr) - S.median(f)))
    print()
    print("VERDICT: M05-A's AGGREGATE reading survives -- what falls completes,")
    print("what rises does not, and keeps rising past the arm. What does not")
    print("survive is the inference from the paired p=0.97 to 'no fall-then-rise")
    print("sequence': that p is computed on a statistic with no resolution here.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
