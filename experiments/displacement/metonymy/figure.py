"""Recolour the garment figure for the current lineage roster.

    python figure.py                    # both files, colour and greyscale
    python figure.py --scale D --gray-only

## THE DRAWING IS PORTED; ONLY THE COLOURS ARE COMPUTED

`data/x1_garment_layers_source.svg` is the published `X.1` figure from
`malign-logits/meta/M01_displacement/figures/`, hand-authored, 46 lineage
pairs. Its geometry carries the argument -- each garment is drawn at the layer
it is worn at, so the scale is the PICTURE and not a number on an axis -- and
nothing here redraws it. This producer rewrites three things and asserts it
touched nothing else: every garment's fill, its swatch and printed value, and
the strings that quote the roster size.

**No garment was added or removed.** At 50 lineages every one of the 27 + 22
words drawn still moves. `--audit` prints the case for that: the words the
figure leaves out, ranked by how far alignment moves them, against the ones it
draws. It restricts to words the coder placed on a scale, because the moving
vocabulary at this slot also contains `____`, `black` and bare determiners,
and "the biggest thing you left out" is not a useful sentence if the biggest
thing is a blank.

## THE COLOUR IS A VALUE, SO IT IS RECOVERED, NOT GUESSED

    t = 0.5 + 0.5 * sign(d) * min(1, |d| / CLIP) ** GAMMA      RdBu at t

Read back off the published file: `shoes +2.58 -> #053061`, `coat +0.57 ->
#3e8cc0`, `hat -0.04 -> #fbe6da` all reproduce to within a rounding step. The
gamma is there because almost every garment moves by a fraction of a point
while `shoes` moves by two and a half, and a linear ramp puts the whole middle
of the figure at the same white.

## GREYSCALE IS A DIFFERENT ENCODING, NOT A DESATURATION

Converting RdBu to luminance maps the two ends to nearly the same mid-grey, so
the falls and the rises would print identically. `--gray` instead runs ONE
monotone ramp -- light = alignment takes mass away, dark = alignment adds it --
and rewrites the legend and the caption to say so. It is a different sentence
about the same numbers, which is why the caption is regenerated and not
recycled.
"""

import argparse
import csv
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "data", "x1_garment_layers_source.svg")

CLIP = 1.2
GAMMA = 0.62
#: Greyscale is PIECEWISE, and the break at zero is the point. A single ramp
#: from white to black puts every small faller and every small riser in the
#: same middle grey, which is most of the figure: run it and the torso reads
#: as one flat tone. Falls take the pale band, rises the dark one, and the gap
#: between the two bands is a luminance step you can see, so the SIGN survives
#: the printer even where the magnitude does not. Both ends stop short of
#: paper and ink so the 1.3pt garment outlines stay visible.
GRAY_FALL = (0.97, 0.78)      # Δ = -CLIP .. 0
GRAY_RISE = (0.66, 0.08)      # Δ = 0 .. +CLIP

PROMPTS = {"her": "She slowly took off her", "his": "He slowly took off his"}

#: her `#053061` is the one fill the panel uses twice: the shoe and the two
#: spectacle lenses both sit at the clip. Every other repeat is one garment in
#: several pieces -- two gloves, two trouser legs, a hat brim and crown -- and
#: those want the same colour, which is what matching on the fill already does.
OVERRIDE = {36: ("her", "shoes"), 52: ("her", "glasses"), 53: ("her", "glasses")}


def ramp(d, gray=False):
    """Δ in percentage points -> an SVG hex fill."""
    import matplotlib as mpl
    import matplotlib.colors as mc
    u = min(1.0, abs(d) / CLIP) ** GAMMA
    t = 0.5 + 0.5 * (1.0 if d >= 0 else -1.0) * u
    if not gray:
        return mc.to_hex(mpl.colormaps["RdBu"](t))
    lo, hi = GRAY_RISE if d >= 0 else GRAY_FALL
    v = (lo + (hi - lo) * u) if d >= 0 else (lo + (hi - lo) * (1.0 - u))
    return mc.to_hex((v, v, v))


def deltas(scale="D"):
    """{(panel, word): median Δ in percentage points} from the producer."""
    path = os.path.join(HERE, "results", "words_%s.csv" % scale)
    if not os.path.exists(path):
        raise SystemExit("no %s -- run `python run.py --scale %s` first"
                         % (path, scale))
    out, carriers = {}, {}
    for r in csv.DictReader(open(path, encoding="utf-8")):
        for panel, prompt in PROMPTS.items():
            if r["prompt"] == prompt:
                out[(panel, r["word"].lower())] = float(r["median_delta_pp"])
                carriers[(panel, r["word"].lower())] = int(r["n_carriers"])
    return out, carriers


def _panel_of(line):
    xs = re.findall(r'[ML] ([\d.]+) ', line) or re.findall(r'cx="([\d.]+)"', line)
    return "her" if xs and float(xs[0]) < 800 else "his"


def read_source():
    """-> (lines, swatch_blocks, body_lines).

    `swatch_blocks` is one entry per label: the swatch line, the text line, the
    panel, the word and the printed value. `body_lines` maps a drawing line to
    the word it draws, by matching its fill against the swatch's within the
    same panel, with `OVERRIDE` for the one collision.
    """
    lines = open(SOURCE, encoding="utf-8").read().splitlines()
    swatches, by_fill = [], {}
    for i, l in enumerate(lines):
        m = re.match(r'<rect x="([\d.]+)" y="[\d.]+" width="17" height="17" '
                     r'rx="3.5" fill="(#[0-9a-f]{6})"', l)
        if not m:
            continue
        t = lines[i + 1]
        word = re.search(r'font-weight="700">([^<]+)</tspan>', t).group(1)
        panel = "her" if float(m.group(1)) < 800 else "his"
        swatches.append({"swatch": i, "text": i + 1, "panel": panel,
                         "word": word.lower(), "fill": m.group(2)})
        by_fill.setdefault((panel, m.group(2)), []).append(word.lower())

    body = {}
    for i, l in enumerate(lines):
        if 'width="17" height="17"' in l or 'y="886.0"' in l:
            continue
        if not (l.startswith("<path") or l.startswith("<circle")):
            continue
        m = re.search(r'fill="(#[0-9a-f]{6})"', l)
        if not m:
            continue
        if i + 1 in OVERRIDE:
            body[i] = OVERRIDE[i + 1]
            continue
        panel = _panel_of(l)
        words = by_fill.get((panel, m.group(1)))
        if words and len(set(words)) == 1:
            body[i] = (panel, words[0])
    return lines, swatches, body


def build(scale="D", gray=False):
    lines, swatches, body = read_source()
    d, carriers = deltas(scale)

    missing = sorted({(s["panel"], s["word"]) for s in swatches} - set(d))
    if missing:
        raise SystemExit("no Δ for %s" % (missing,))

    out = list(lines)
    touched = set()

    def fill_of(key):
        return ramp(d[key], gray)

    #: 1. the garments
    for i, key in body.items():
        out[i] = re.sub(r'fill="#[0-9a-f]{6}"', 'fill="%s"' % fill_of(key),
                        out[i], count=1)
        touched.add(i)

    #: 2. the swatches and the printed values
    for s in swatches:
        key = (s["panel"], s["word"])
        out[s["swatch"]] = out[s["swatch"]].replace(
            'fill="%s"' % s["fill"], 'fill="%s"' % fill_of(key))
        val = "%+.2f" % d[key]
        out[s["text"]] = re.sub(r'&#160;&#160;[^<]+</tspan>',
                                '&#160;&#160;%s</tspan>'
                                % val.replace("-", "−"), out[s["text"]])
        touched.add(s["swatch"])
        touched.add(s["text"])

    #: 3. the legend ramp, one rect per step, left edge -> right edge
    ramp_rows = [i for i, l in enumerate(out) if 'y="886.0"' in l]
    xs = [float(re.search(r'x="([\d.]+)"', out[i]).group(1)) for i in ramp_rows]
    lo, hi = min(xs), max(xs)
    for i, x in zip(ramp_rows, xs):
        v = -CLIP + 2 * CLIP * (x - lo) / (hi - lo)
        out[i] = re.sub(r'fill="#[0-9a-f]{6}"', 'fill="%s"' % ramp(v, gray),
                        out[i], count=1)
        touched.add(i)

    #: 4. the strings that quote the roster or the encoding
    n_lin = max(carriers.values())
    subs = [("46 lineage pairs", "%d lineage pairs" % n_lin),
            ("46 lineage-representative pairs",
             "%d lineage-representative pairs" % n_lin),
            ("Recomputed 2026-08-14 from the movement store",
             "Recomputed 2026-09-18 from the movement store")]
    if gray:
        subs += [
            ("red = base’s word", "light = base’s word"),
            ("blue = alignment’s word", "dark = alignment’s word"),
            ("percentage points; red = base’s word, blue = alignment’s word;",
             "percentage points; light = base’s word, dark = alignment’s word;"),
            ("hue is stretched", "lightness is stretched"),
            ("what alignment promotes sits at the edge of the body; what it demotes sits at the core",
             "what alignment promotes sits at the edge of the body; what it demotes sits at the core"),
        ]
    for i, l in enumerate(out):
        new = l
        for a, b in subs:
            new = new.replace(a, b)
        if new != l:
            out[i] = new
            touched.add(i)
    if gray:
        #: the two pole labels carry the colour in their own fill
        for i, l in enumerate(out):
            if "base’s word" in l or "alignment’s word" in l:
                out[i] = re.sub(r'fill="#(8c1f2c|1c4f83)"', 'fill="#3a3934"', l)

    return "\n".join(out) + "\n", touched, len(lines)


def audit(scale="D", top=8):
    """Which scored words does the drawing leave out, and how far do they move?"""
    import run as producer
    _l, swatches, _b = read_source()
    drawn = {(s["panel"], s["word"]) for s in swatches}
    d, carriers = deltas(scale)
    scored = set(producer.scale(scale))

    print("  drawn %d, of which absent at this roster: %s"
          % (len(drawn), sorted(drawn - set(d)) or "none"))
    print("  scale %r places %d words; the drawing uses %d of them"
          % (scale, len(scored), len({w for _p, w in drawn} & scored)))
    for panel in ("her", "his"):
        ins = sorted((abs(v), k[1]) for k, v in d.items()
                     if k[0] == panel and k in drawn)
        outs = sorted(((abs(v), k[1], carriers[k]) for k, v in d.items()
                       if k[0] == panel and k not in drawn and k[1] in scored),
                      reverse=True)
        print("  %s-frame: drawn |Δ| spans %.3f (%s) to %.2f (%s)"
              % (panel, ins[0][0], ins[0][1], ins[-1][0], ins[-1][1]))
        print("    biggest movers the drawing leaves out:")
        for v, w, n in outs[:top]:
            rank = sum(1 for x, _w in ins if x > v) + 1
            print("      %-12s |Δ| %.3f  carriers %2d  -- would rank %d of %d "
                  "among the drawn" % (w, v, n, rank, len(ins)))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scale", default="D",
                    help="only picks which results/words_<scale>.csv to read; "
                         "the Δ column is the same in all of them.")
    ap.add_argument("--audit", action="store_true")
    ap.add_argument("--gray-only", action="store_true")
    ap.add_argument("--color-only", action="store_true")
    ap.add_argument("--outdir", default=os.path.join(HERE, "figures"))
    a = ap.parse_args(argv)

    if a.audit:
        audit(a.scale)
        return 0

    os.makedirs(a.outdir, exist_ok=True)
    jobs = []
    if not a.gray_only:
        jobs.append((False, "x1_garment_layers.svg"))
    if not a.color_only:
        jobs.append((True, "x1_garment_layers_gray.svg"))
    for gray, name in jobs:
        svg, touched, total = build(a.scale, gray)
        path = os.path.join(a.outdir, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(svg)
        print("-> %s  (%d of %d lines rewritten)" % (path, len(touched), total))
    return 0


if __name__ == "__main__":
    sys.exit(main())
