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
    #: Indented while it stays small enough to read in a diff, compact once it
    #: does not. At 1,730 lines x 9 values `indent=1` spends more bytes on
    #: newlines and spaces than on numbers, and this file is fetched by a browser.
    js = json.dumps(art, indent=1)
    if len(js) > 200_000:
        js = json.dumps(art, separators=(",", ":"))
    path = os.path.join(figdir, name + ".data.json")
    with open(path, "w") as fh:
        fh.write(js)
    #: Counted from whatever collections the chart type declares, rather than
    #: from `panels`/`rows`. This printed the slopes shape by name and broke the
    #: first chart type that did not have one -- a writer that only writes the
    #: figure it was written for, which is the leak this module exists to close.
    shape = ", ".join("%d %s" % (len(v), k) for k, v in sorted(art.items())
                      if isinstance(v, list) and k != "x_order")
    print("   %-38s %6.0f KB  %s: %s"
          % (name + ".data.json", len(js) / 1024, art["chart"], shape))
    return path


MARKS = ("", "up", "down", "flat")


def parcoords(*, title, axes, groups, lines, subtitle=None,
              value_label="value", mark_label="", mark_legend=None, meta_order=None,
              table_meta=None, notes=None):
    """Parallel coordinates: one line per case, one axis per measured dimension.

        axes    [{key, label, domain: [lo, hi], note}]   left-to-right order
        groups  [{key, label, colour}]                   what the colour means
        lines   [{key, label, group, values, marks?, missing?, meta?}]

    `values` is an array PARALLEL TO `axes`, not a list of {axis, y} records. At
    1,730 lines x 9 axes the record form spends about four fifths of the file
    repeating nine axis names, and the parallel array cannot disagree with the
    axis order because it has no opinion about it.

    ## THE MARK EXISTS BECAUSE SOME EFFECTS CANNOT BE GEOMETRY

    An axis holds ONE number per line, so a before/after comparison needs two
    lines -- and that only works if the change is large relative to the axis.
    Where it is not, drawing it is worse than useless: the lines coincide, the
    panel reads as "nothing happened", and a reader cannot tell that from an axis
    too coarse to resolve the move. `marks` is an optional parallel array for a
    change the axis cannot show, and `mark_label` names what it means.

    ## A GAP IS DECLARED, NEVER INFERRED

    A `null` in `values` REQUIRES an entry in the line's `missing` map saying
    why. A dimension that does not apply to a case is a real thing to draw, and
    a line that simply stops cannot be told from a producer that dropped a row.
    """
    akeys = [a["key"] for a in axes]
    gkeys = {g["key"] for g in groups}
    lkeys = [l["key"] for l in lines]
    assert len(akeys) == len(set(akeys)), "duplicate axis keys"
    assert len(lkeys) == len(set(lkeys)), "duplicate line keys"
    assert len(gkeys) == len(groups), "duplicate group keys"
    for a in axes:
        assert len(a["domain"]) == 2 and a["domain"][0] < a["domain"][1], \
            "axis %r domain must be [lo, hi]" % a["key"]

    for l in lines:
        assert l["group"] in gkeys, "line %r has undeclared group %r" % (l["key"], l["group"])
        v = l["values"]
        #: EVERY AXIS, EXACTLY ONCE. A short array draws as a shorter line and
        #: reads as a line, which is the failure this refuses.
        assert len(v) == len(axes), \
            "line %r has %d values for %d axes" % (l["key"], len(v), len(axes))
        m = l.get("marks")
        assert m is None or len(m) == len(axes), \
            "line %r has %d marks for %d axes" % (l["key"], len(m or []), len(axes))
        for j, y in enumerate(v):
            if m is not None:
                assert m[j] in MARKS, "line %r axis %r: mark %r not in %s" % (
                    l["key"], akeys[j], m[j], MARKS)
            if y is None:
                assert (l.get("missing") or {}).get(akeys[j]), \
                    "line %r has no value on axis %r and no `missing` reason" % (
                        l["key"], akeys[j])
                continue
            lo, hi = axes[j]["domain"]
            assert lo <= y <= hi, \
                "line %r axis %r: %r outside domain %s (the renderer would CLIP it)" % (
                    l["key"], akeys[j], y, [lo, hi])

    #: EVERY DECLARED COLUMN MUST EXIST ON EVERY LINE. A key that is absent or
    #: misspelled renders as a column of blanks -- a header naming a field the
    #: table does not have, which reads as "these cells have no value" rather
    #: than as a typo. Checked against all lines, not the first: a field present
    #: on some rows and not others is the same defect wearing a disguise.
    for k in table_meta or []:
        bad = [l["key"] for l in lines if k not in (l.get("meta") or {})]
        assert not bad, "table_meta %r missing from %d line(s), first: %s" % (
            k, len(bad), bad[:3])

    return {"chart": "parcoords", "title": title, "subtitle": subtitle,
            "value_label": value_label, "mark_label": mark_label,
            "mark_legend": mark_legend or {}, "meta_order": list(meta_order or []),
            "table_meta": list(table_meta or []), "notes": notes or [],
            "axes": axes, "groups": groups, "lines": lines}


def quadrants(*, title, x, y, cats, models, points, cells, table, subtitle=None,
              detail=None, notes=None, n_total=None, arrows=None, anchors=None):
    """A four-quadrant scatter whose points are addressable, plus its occupancy table.

        x, y     {key, label, note, domain: [lo, hi]}
        cats     [{key, label, colour, kind}]          kind groups the legend
        models   [str]                                 indexed by points.model
        points   {ids: [], x: [], y: [], cat: [], model: []}   PARALLEL ARRAYS
        cells    [{key, label, pooled}]                the quadrants and pooled rates
        table    [{cat, n, pct: {cell: %}, enrich: {cell: x}}]
        detail   {url, scales: {name: {domain, note}}}   how to open one point

    ## WHY PARALLEL ARRAYS AND NOT A LIST OF RECORDS

    14,414 points. As records the field names are repeated 14,414 times and are
    four fifths of the file; as columns they appear once. The cost is that
    nothing structurally prevents the columns from being different lengths, so
    that is the first thing checked.

    ## WHY THE POINTS ARE ADDRESSABLE

    The word and sentence grains behind these points are 3,040,970 and 196,349
    rows and cannot ship. `ids` exists so a component can fetch ONE point's
    detail, and `detail_url` names the route rather than the component knowing
    it -- the same reason `stat_label` lives in the slopes artifact.
    """
    n = len(points["ids"])
    #: WHAT WAS DRAWN AND WHAT WAS COUNTED ARE DIFFERENT NUMBERS when a producer
    #: samples, and the panel has to be able to say both. A figure that prints
    #: only the drawn count while its table is over everything is a windowed
    #: picture beside an unwindowed statistic -- no error anywhere in it.
    assert n_total is None or n_total >= n, \
        "n_total %r is smaller than the %d points drawn" % (n_total, n)
    for k in ("x", "y", "cat", "model"):
        assert len(points[k]) == n, \
            "points.%s has %d entries against %d ids" % (k, len(points[k]), n)
    assert len(set(points["ids"])) == n, "duplicate point ids"

    ckeys = [c["key"] for c in cats]
    assert len(ckeys) == len(set(ckeys)), "duplicate cat keys"
    bad = [i for i in points["cat"] if not 0 <= i < len(cats)]
    assert not bad, "cat index out of range: %s" % bad[:3]
    bad = [i for i in points["model"] if not 0 <= i < len(models)]
    assert not bad, "model index out of range: %s" % bad[:3]

    #: A POINT OUTSIDE THE DECLARED DOMAIN IS CLIPPED SILENTLY, and on a scatter
    #: that reads as a smaller cloud rather than as an error.
    for ax, vals in ((x, points["x"]), (y, points["y"])):
        lo, hi = ax["domain"]
        assert lo < hi, "axis %r domain must be [lo, hi]" % ax["key"]
        out = [v for v in vals if not lo <= v <= hi]
        assert not out, "%d point(s) outside %s domain %s, first: %s" % (
            len(out), ax["key"], ax["domain"], out[:3])

    #: A DETAIL SCALE MUST BE A RANGE, for the same reason an axis must: the
    #: component clamps to it, and a reversed or degenerate domain clamps every
    #: value to one end and paints a uniform field that reads as "nothing varies".
    for k, sc in (detail or {}).get("scales", {}).items():
        assert len(sc["domain"]) == 2 and sc["domain"][0] < sc["domain"][1], \
            "detail scale %r domain must be [lo, hi], got %s" % (k, sc["domain"])
        #: A DIVERGING SCALE'S MIDPOINT MUST BE INSIDE ITS DOMAIN. Outside it,
        #: every value falls on one side of the divergence and the scale paints a
        #: single ramp while still calling itself diverging.
        if "mid" in sc:
            assert sc["domain"][0] < sc["mid"] < sc["domain"][1], \
                "detail scale %r has mid %r outside domain %s" % (k, sc["mid"], sc["domain"])
        assert sc.get("note"), \
            "detail scale %r has no note; a clamped scale that does not say so " \
            "understates its own tail silently" % k

    #: ARROWS AND ANCHORS SHARE THE POINTS' AXES, so they are checked against the
    #: same domains. A vector whose head is off the panel draws as a shorter
    #: vector -- it does not vanish, it UNDERSTATES, which is the direction that
    #: reads as a real result.
    for a in arrows or []:
        for end in ("from", "to"):
            for k, ax in (("x", x), ("y", y)):
                v = a[end][k]
                lo, hi = ax["domain"]
                assert lo <= v <= hi, \
                    "arrow %r %s.%s = %r outside %s domain %s" % (
                        a.get("label"), end, k, v, ax["key"], [lo, hi])
    for an in anchors or []:
        for k, ax in (("x", x), ("y", y)):
            lo, hi = ax["domain"]
            assert lo <= an[k] <= hi, \
                "anchor %r %s = %r outside %s domain %s" % (
                    an.get("label"), k, an[k], ax["key"], [lo, hi])

    cell_keys = [c["key"] for c in cells]
    assert len(cell_keys) == len(set(cell_keys)), "duplicate cell keys"
    for r in table:
        assert r["cat"] in ckeys, "table row for undeclared cat %r" % r["cat"]
        assert sorted(r["pct"]) == sorted(cell_keys), \
            "table row %r covers %s, expected %s" % (r["cat"], sorted(r["pct"]), sorted(cell_keys))
        #: THE ROW MUST BE A PARTITION. These are percentages of a category over
        #: four mutually exclusive quadrants, so anything but 100 means a point
        #: was counted twice or dropped -- and a table that nearly sums is the
        #: version nobody checks.
        tot = sum(r["pct"].values())
        assert abs(tot - 100) < 0.35, \
            "table row %r sums to %.2f%%, not 100 (rounding allows 0.35)" % (r["cat"], tot)

    return {"chart": "quadrants", "title": title, "subtitle": subtitle,
            "x": x, "y": y, "cats": cats, "models": models, "points": points,
            "cells": cells, "table": table, "detail": detail or {},
            "n_total": n_total if n_total is not None else n,
            "arrows": arrows or [], "anchors": anchors or [],
            "notes": notes or []}


def graph(*, title, nodes, links, groups, subtitle=None, notes=None, meta=None):
    """A force-directed graph: nodes with a group, links between node ids.

        nodes   [{id, kind, label, group, ...}]   `kind` drives how it is drawn
        links   [{source, target}]                ids, not indices
        groups  [{key, label, colour}]

    ## IDS, NOT INDICES

    d3-force MUTATES the objects it is given, replacing `source`/`target` with
    node references. A producer emitting indices would be writing something the
    consumer has to keep in sync with array order; ids survive filtering in the
    UI, which is the whole point of shipping a graph rather than a picture.

    ## WHAT IS CHECKED

    Every link endpoint must resolve to a node. A dangling endpoint does not
    raise in d3 -- it silently drops the link, so the graph draws with fewer
    edges than it has and nothing says so.
    """
    ids = {n["id"] for n in nodes}
    assert len(ids) == len(nodes), "duplicate node ids"
    gk = {g["key"] for g in groups}
    assert len(gk) == len(groups), "duplicate group keys"
    bad = [n["id"] for n in nodes if n.get("group") is not None and n["group"] not in gk]
    assert not bad, "node(s) with an undeclared group: %s" % bad[:3]
    dangling = [(l["source"], l["target"]) for l in links
                if l["source"] not in ids or l["target"] not in ids]
    assert not dangling, \
        "%d link(s) with an endpoint that is not a node, first: %s -- d3-force DROPS " \
        "these silently" % (len(dangling), dangling[:3])
    return {"chart": "graph", "title": title, "subtitle": subtitle,
            "nodes": nodes, "links": links, "groups": groups,
            "notes": notes or [], "meta": meta or {}}
