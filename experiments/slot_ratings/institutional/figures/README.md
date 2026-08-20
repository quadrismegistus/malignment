# figures/

Produced by `../plot.py`, which draws only this study.

    python experiments/slot_ratings/institutional/plot.py           # all
    python experiments/slot_ratings/institutional/plot.py --list
    python experiments/slot_ratings/institutional/plot.py did_blindness

Every figure reads a saved artifact, re-derives the numbers this study's README
books, and refuses with a named reason if they do not reproduce. Nothing here
queries the store and nothing writes an artifact, so a re-run moves pixels only.
If a figure and the README disagree, the figure is wrong.

    did_blindness           section 13. Both positions move; the difference does not
    per_scenario_signs      section 15. Scenarios that disagree produce a pooled zero

`did_blindness` also writes `did_blindness.vl.json`, the Vega-Lite spec the app
serves. The PNG and the spec come from one dict, so they cannot disagree.

Until 2026-08-20 the institutional figures were drawn by `../../plot.py`
alongside identity and sexual. `per_scenario_signs.png` moved unchanged, and
byte-identical output was the acceptance test for the move.
