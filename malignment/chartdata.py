"""Figure DATA artifacts: one definition of each chart's schema, and its guards.

    from malignment.chartdata import slopes, write

A producer computes numbers and writes `<figure>.data.json`; a LayerChart
component in the app draws it. RH, 2026-08-21: *python produces the minimal data
LayerChart needs, LayerChart draws.*

## WHY THE SCHEMA LIVES HERE AND NOT IN THE PRODUCER

The first one was a dict literal inside `institutional/plot.py`. That works
exactly once. The second producer copies the shape, the third copies it with a
typo, and the component that reads all three fails on the typo at render time
with nothing useful to say -- the classic shape of a convention that was never
written down.

So each chart type gets a builder here. The FIELD NAMES are then one definition
rather than a habit, and the checks below run for every producer that uses it
instead of for whichever one remembered.

## WHAT IS CHECKED, AND WHY THESE

A missing point does not raise: it draws a line with one end, or no line, and the
panel simply looks calmer than its neighbours. That is the failure this file
exists to catch, and it is why `slopes` requires EVERY panel to carry EVERY
series at EVERY x rather than accepting whatever it is handed.
"""

import json
import os


def slopes(*, title, panels, rows, series, x_order, y_domain, subtitle=None,
           stat_label="diff", note_label=""):
    """A grid of two-point slopegraphs, one panel per key.

        panels    [{key, label, note, did, mark}]   order is drawing order
        rows      [{panel, series, x, y, level}]    y is what is PLOTTED
        series    [{key, colour}]
        x_order   the x categories, in order
        y_domain  [lo, hi] shared by every panel

    `y` and `level` are deliberately separate. Panels are comparable only if each
    is centred on its own midpoint, so `y` is centred and `level` is the value on
    the original scale -- what a tooltip must show, because a centred number read
    as a level is simply wrong.

    `stat_label` names what `panels[].did` MEANS and `note_label` names what
    `panels[].note` means. They are here rather than in the component because the
    component draws any `slopes` artifact from any experiment: a hardcoded
    "indiv - inst" would sit over whatever the next producer put in that field
    and be WRONG WITHOUT BEING BROKEN, which is the expensive direction.
    """
    keys = [p["key"] for p in panels]
    assert len(keys) == len(set(keys)), "duplicate panel keys"
    skeys = [s["key"] for s in series]
    assert len(skeys) == len(set(skeys)), "duplicate series keys"
    assert len(y_domain) == 2 and y_domain[0] < y_domain[1], "y_domain must be [lo, hi]"

    #: EVERY PANEL x SERIES x X, PRESENT EXACTLY ONCE. A gap here is invisible in
    #: the render -- a line with one end, or none -- so it is refused at write
    #: time where it can still name what is missing.
    seen = {}
    for r in rows:
        seen.setdefault((r["panel"], r["series"], r["x"]), 0)
        seen[(r["panel"], r["series"], r["x"])] += 1
    missing = [(p, s, x) for p in keys for s in skeys for x in x_order
               if (p, s, x) not in seen]
    dupes = [k for k, n in seen.items() if n > 1]
    extra = [k for k in seen if k[0] not in keys or k[1] not in skeys or k[2] not in x_order]
    assert not missing, "missing %d point(s), first: %s" % (len(missing), missing[:3])
    assert not dupes, "duplicate point(s), first: %s" % dupes[:3]
    assert not extra, "point(s) outside the declared panels/series/x: %s" % extra[:3]

    #: A point outside the shared domain is CLIPPED silently by the renderer, so
    #: the panel understates a movement it was drawn to show.
    out = [r for r in rows if not (y_domain[0] <= r["y"] <= y_domain[1])]
    assert not out, "%d point(s) outside y_domain %s, first: %s" % (
        len(out), y_domain, out[:2])

    return {"chart": "slopes", "title": title, "subtitle": subtitle,
            "stat_label": stat_label, "note_label": note_label,
            "x_order": list(x_order), "y_domain": list(y_domain),
            "series": series, "panels": panels, "rows": rows}


def write(art, figdir, name):
    """Write `<name>.data.json` into a folder's `figures/`, and say what it holds."""
    os.makedirs(figdir, exist_ok=True)
    js = json.dumps(art, indent=1)
    path = os.path.join(figdir, name + ".data.json")
    with open(path, "w") as fh:
        fh.write(js)
    print("   %-38s %6.0f KB  %s, %d panels, %d rows"
          % (name + ".data.json", len(js) / 1024, art["chart"],
             len(art["panels"]), len(art["rows"])))
    return path
