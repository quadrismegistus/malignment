"""Every measured effect on one scale, so "which moves it more" has an answer.

    python .../synthesis.py

Four things move a model on these two axes, each measured by a different design
in a different file, each reported in its own raw units. Raw units cannot be
compared: 0.02 of drift and 0.8 bits of surprisal are not commensurable, and
"alignment reduces both" says nothing about which it reduces more.

This divides every effect by the PASSAGE-LEVEL standard deviation of its own axis
-- the same sd `quadrants.py` used to z-score the plane, taken from
`results/quadrants.manifest.json` -- so both axes are in units of "how spread out
passages are". Then the two columns can be read against each other.

## WHAT EACH ROW IS, AND WHY THE DESIGNS ARE NOT INTERCHANGEABLE

    alignment   arm_paired.py      aligned - base, PAIRED WITHIN LINEAGE, 22
                                   lineages. Size and lab are held by
                                   construction: both arms are one model.
    size        scale_ladder.py    Falcon3 aligned, 1.7B -> 10.3B. One lab, one
                                   recipe, one data mix, size the only variable.
                                   NOT the 47-model regression, which is
                                   confounded on drift.
    wrapper     run_wrapper.py     continue - raw, 6 aligned models, paired
                                   within (model, prompt). **MEASURED AT M=64**,
                                   not 200, because that pool was generated at
                                   ~100 tokens -- so its surprisal row is on a
                                   shorter prefix and is the least comparable
                                   number in the table.
    API         stem_paired.py     API - aligned, paired within STEM. Not an arm
                                   contrast: these models have no base.

**The four are not four steps of one process.** A model does not go
base -> aligned -> bigger -> wrapped. They are four separate manipulations
measured on overlapping populations, and the table ranks their sizes, not a
sequence.
"""

import argparse, csv, json, math, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
MAN = os.path.join(HERE, "results", "quadrants.manifest.json")

#: (label, d_surprisal, d_drift, note) -- every value from the producer named in
#: the docstring, none recomputed here. A number that moves in one of those
#: files and not here would be a silent divergence, so each is cited.
EFFECTS = [
    ("alignment (aligned - base)", -0.8435, -0.0254,
     "arm_paired.py, 22 lineages, both p<1e-4"),
    ("size (1.7B -> 10.3B)", -0.7677, -0.0070,
     "scale_ladder.py, Falcon3 aligned arm, 6x range"),
    ("chat wrapper (continue - raw)", -0.5103, -0.0375,
     "run_wrapper.py, 6 models, M=64 not 200"),
    ("API - aligned", -0.0852, +0.0085,
     "stem_paired.py, 89 stems"),
]


def main(argv=None):
    ap = argparse.ArgumentParser()
    a = ap.parse_args(argv)
    man = json.load(open(MAN))
    sS, sD = man["sd"]["surprisal"], man["sd"]["drift"]

    print("passage-level sd, the common scale: surprisal %.4f  drift %.4f" % (sS, sD))
    print("(over all %d passages, the reference quadrants.csv used)\n" % man["n"])
    print("%-30s %19s %19s %10s" % ("", "SURPRISAL", "DRIFT", "which"))
    print("%-30s %9s %9s %9s %9s %10s"
          % ("", "raw", "sd", "raw", "sd", "moves more"))
    for lab, ds, dd, note in EFFECTS:
        zs, zd = ds / sS, dd / sD
        #: "which moves more" compares MAGNITUDES on the shared sd scale, and
        #: names the axis only when one is clearly larger -- a 1.2x difference
        #: is not a fact about the world, it is a fact about two sds.
        r = abs(zs) / abs(zd) if zd else float("inf")
        which = ("surprisal %.1fx" % r if r > 1.3 else
                 "drift %.1fx" % (1 / r) if r < 1 / 1.3 else "about equal")
        print("%-30s %+9.4f %+9.3f %+9.4f %+9.3f %10s" % (lab, ds, zs, dd, zd, which))
    print()
    for lab, _, _, note in EFFECTS:
        print("  %-30s %s" % (lab.split(" (")[0], note))

    print("""
READING IT

  ALIGNMENT moves surprisal far more than drift -- about 2x on the shared
  scale. It is primarily a predictability effect with a real but smaller
  trajectory effect beside it.

  SIZE is the most lopsided of the four: a six-fold parameter range moves
  surprisal nearly as far as alignment does and barely touches drift. Size is a
  predictability effect and essentially NOT a drift effect, which is why the
  47-model regression's drift correlation had to be called confounded.

  THE WRAPPER is the only manipulation whose two effects are COMPARABLE --
  0.73 sd of surprisal against 0.86 of drift, drift larger by 1.18x, which is
  inside the band this file calls "about equal" and is not a ranking. Every
  other row is lopsided; this one is not. It carries the M=64 caveat: its
  surprisal is on a shorter prefix, which if anything understates that side.

  THE API CONTRAST is small on surprisal and OPPOSITE IN SIGN on drift. These
  models are not less drifty than aligned models. They are MORE drifty
  (+0.0085, 64/25 stems, p=4.3e-05) while sitting inside the open aligned range
  on surprisal -- five of eleven below its median and six above.
""")


if __name__ == "__main__":
    main()
