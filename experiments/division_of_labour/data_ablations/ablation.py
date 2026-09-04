"""WHICH SFT DATA installs responsiveness to the chat frame?

Tulu-3 ships four leave-one-out SFT checkpoints beside the full-mix one: same
base (Llama-3.1-8B), same recipe, one training source removed. That is the
cleanest design available in this campaign for asking what a training corpus
installs, because every alternative explanation is held fixed by construction.

    full mix          allenai/Llama-3.1-Tulu-3-8B-SFT
    minus math        ...-SFT-no-math-data
    minus persona     ...-SFT-no-persona-data
    minus safety      ...-SFT-no-safety-data
    minus wildchat    ...-SFT-no-wildchat-data      (real logged user chat)

The contrast is paired within prompt -- all five checkpoints answer the same
840 prompts -- so `full - ablated` is a per-prompt difference, not two means
compared across populations.

TWO OUTCOMES, and the second is the point of the file:

  FRAME    n_tot on the SELF-EDGE. Same weights, bare prompt against framed
           prompt. How much the scene of address revises.

  CONTROL  n_tot on the RAW alignment edge, base -> this checkpoint, no frame
           on either side. How much this checkpoint moves off its base at all.

An ablation that raises BOTH is simply a more movable model and says nothing
about the frame. Only a split between the columns is evidence that a data source
installs frame responsiveness specifically. The control is restricted to the
self-edge's own prompts so the two columns describe one population.

A third column carries the discrimination quantity from ladder.py -- the
dose slope of fall-rise -- because the marginal and dose-conditional answers
came apart along the ladder and there is no reason to assume they agree here.

MASS is the fourth column and it exists to kill one artifact. n_tot counts
words over a threshold (theta=0.001, fixed and identical across these five
checkpoints), so a checkpoint with flatter distributions piles more words near
that threshold and every count inflates for a reason that has nothing to do
with frames. Mass is sum|delta|/2 over ALL candidate words including `still`
ones -- the total variation the frame displaces, with no threshold in it.

    python -m experiments.displacement.rate_and_magnitude.ablation
"""
import math

from malignment import ch, charge
from malignment.ch import _lit

BASE = "meta-llama/Llama-3.1-8B"
FULL = "allenai/Llama-3.1-Tulu-3-8B-SFT"
ABLATIONS = [
    ("no-math", "allenai/Llama-3.1-Tulu-3-8B-SFT-no-math-data"),
    ("no-persona", "allenai/Llama-3.1-Tulu-3-8B-SFT-no-persona-data"),
    ("no-safety", "allenai/Llama-3.1-Tulu-3-8B-SFT-no-safety-data"),
    ("no-wildchat", "allenai/Llama-3.1-Tulu-3-8B-SFT-no-wildchat-data"),
]


def ols_t(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    a = my - b * mx
    rss = sum((y - (a + b * x)) ** 2 for x, y in zip(xs, ys))
    return b, b / math.sqrt(rss / (n - 2) / sxx)


def paired_t(d):
    n = len(d)
    m = sum(d) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in d) / (n - 1))
    if sd == 0:
        return m, float("nan")
    return m, m / (sd / math.sqrt(n))


def _counts(where):
    rows = ch.query(
        "SELECT prompt, countIf(cls='faller') nf, countIf(cls='riser') nr, "
        "sum(abs(delta))/2 tv, count() nw "
        "FROM movement_v4 WHERE %s GROUP BY prompt" % where)
    return {r["prompt"]: (float(r["nf"]), float(r["nr"]), float(r["tv"]),
                          float(r["nw"])) for r in rows}


def self_counts(model):
    return _counts("base=%s AND aligned=%s AND base=aligned"
                   % (_lit(model), _lit(model)))


def raw_counts(model):
    return _counts("base=%s AND aligned=%s AND frame_base='' AND frame_aligned=''"
                   % (_lit(BASE), _lit(model)))


def main():
    lift = {p: float(v) for (p, b), v in charge.lifts_per_lineage(BASE).items()}
    sf, rw = {}, {}
    for name, m in [("full", FULL)] + ABLATIONS:
        sf[name], rw[name] = self_counts(m), raw_counts(m)

    # one population for every column: prompts the self-edge and the raw edge
    # both cover, for every checkpoint being compared.
    shared = set(sf["full"]) & set(rw["full"])
    for name, _m in ABLATIONS:
        shared &= set(sf[name]) & set(rw[name])
    shared = sorted(shared)
    dosed = [p for p in shared if p in lift]
    print("TULU-3 SFT ABLATIONS: what installs frame responsiveness?")
    print("paired within prompt, full mix MINUS the leave-one-out checkpoint.")
    print("n = %d prompts (%d with a lift)\n" % (len(shared), len(dosed)))

    print("LEVELS")
    print("%-12s %8s %8s %8s %8s %8s"
          % ("checkpoint", "frame", "control", "dose", "mass", "n_cand"))
    for name, _m in [("full", FULL)] + ABLATIONS:
        n = len(shared)
        f = sum(sf[name][p][0] + sf[name][p][1] for p in shared) / n
        c = sum(rw[name][p][0] + rw[name][p][1] for p in shared) / n
        mass = sum(sf[name][p][2] for p in shared) / n
        cand = sum(sf[name][p][3] for p in shared) / n
        b, _t = ols_t([lift[p] for p in dosed],
                      [sf[name][p][0] - sf[name][p][1] for p in dosed])
        print("%-12s %8.2f %8.2f %8.3f %8.4f %8.1f" % (name, f, c, b, mass, cand))

    print("\nPAIRED CONTRASTS  (positive = REMOVING the data RAISED it)")
    print("%-12s %8s %6s %9s %6s %8s %6s %9s %6s" % (
        "removed", "d frame", "t", "d control", "t", "d dose", "t", "d mass", "t"))
    for name, _m in ABLATIONS:
        def tot(d, p):
            return d[name][p][0] + d[name][p][1] - d["full"][p][0] - d["full"][p][1]
        mf, tf = paired_t([tot(sf, p) for p in shared])
        mc, tc = paired_t([tot(rw, p) for p in shared])
        mm, tm = paired_t([sf[name][p][2] - sf["full"][p][2] for p in shared])
        xs = [lift[p] for p in dosed]
        bd, td = ols_t(xs, [(sf[name][p][0] - sf[name][p][1])
                            - (sf["full"][p][0] - sf["full"][p][1]) for p in dosed])
        print("%-12s %8.3f %6.1f %9.3f %6.1f %8.3f %6.1f %9.4f %6.1f"
              % (name, mf, tf, mc, tc, bd, td, mm, tm))
    print("\n    a source that installs FRAME responsiveness moves the frame")
    print("    column and leaves the control alone. one that moves both is a")
    print("    generally more movable checkpoint and is not about the frame.")
    print("    mass must agree with frame, or the count is a threshold artifact.")


if __name__ == "__main__":
    main()
