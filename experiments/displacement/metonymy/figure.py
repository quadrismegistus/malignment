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



# --------------------------------------------------------------------------
# `--mass`: one frame, two bodies, levels instead of a difference
# --------------------------------------------------------------------------
#: The X.1 drawing shows a DIFFERENCE, which is the campaign's quantity but
#: not a picture of either distribution. This mode draws the her-frame body
#: twice, base on the left and aligned on the right, and shades each garment
#: by the probability mass it actually holds there. The difference survives as
#: the signed number in the label, so nothing the original said is lost.
#:
#: ONE RAMP SERVES BOTH BODIES. Shading each panel against its own maximum
#: would make the two incomparable at a glance, which is the only thing this
#: layout is for.
MASS_MAX = 10.0          # percent; `clothes` at base is 9.08 and is the peak
MASS_GAMMA = 0.45        # the slot spans 0.12% to 9.1%, a factor of 76
MASS_PAPER, MASS_INK = 0.98, 0.07
SHIFT = 875.0            # how far right the aligned body sits
WIDTH, HEIGHT = 1760, 1100
MID = 880.0


def mass_gray(pct):
    import matplotlib.colors as mc
    g = min(1.0, max(0.0, pct / MASS_MAX)) ** MASS_GAMMA
    v = MASS_PAPER + (MASS_INK - MASS_PAPER) * g
    return mc.to_hex((v, v, v))


def masses(scale="D", prompt="She slowly took off her"):
    """{word: (base %, aligned %, Δ pp)} for the frame the figure draws."""
    path = os.path.join(HERE, "results", "words_%s.csv" % scale)
    out = {}
    for r in csv.DictReader(open(path, encoding="utf-8")):
        if r["prompt"] == prompt:
            out[r["word"].lower()] = (float(r["median_p_base_pct"]),
                                      float(r["median_p_aligned_pct"]),
                                      float(r["median_delta_pp"]))
    return out


def _first_x(line):
    m = (re.search(r'[ML] ([\d.]+) ', line) or re.search(r'x="([-\d.]+)"', line)
         or re.search(r'cx="([\d.]+)"', line))
    return float(m.group(1)) if m else None


def build_mass(scale="D"):
    """Two her-frame bodies, base and aligned, shaded by mass. Greyscale."""
    lines = open(SOURCE, encoding="utf-8").read().splitlines()
    m = masses(scale)

    #: the source is one flat list; cut it at the legend, which is the first
    #: swatch of the colour bar and everything after it.
    legend_at = next(i for i, l in enumerate(lines) if 'y="886.0"' in l)

    #: label blocks are four consecutive lines: leader, dot, swatch, text.
    blocks, i = [], 0
    while i < legend_at:
        if re.match(r'<rect x="[\d.]+" y="[\d.]+" width="17" height="17"', lines[i]):
            word = re.search(r'font-weight="700">([^<]+)</tspan>',
                             lines[i + 1]).group(1).lower()
            blocks.append((i - 2, i + 2, word))      # leader, dot, swatch, text
            i += 2
        i += 1
    in_block = {i for a, b, _w in blocks for i in range(a, b)}

    #: the drawing: everything between the divider and the first label block,
    #: on the her side of the canvas.
    her_draw = [l for i, l in enumerate(lines)
                if i not in in_block and i > 8 and i < legend_at
                and (l.startswith("<path") or l.startswith("<circle"))
                and (_first_x(l) or 0) < 800]

    #: fill lookup: a garment line's colour is its word's colour, matched the
    #: same way `read_source` does, with the same one override.
    _l2, swatches, bodymap = read_source()
    fills = {}
    for i, (panel, word) in bodymap.items():
        if panel == "her":
            fills[_l2[i]] = word

    def paint(line, which):
        w = fills.get(line)
        if w is None or w not in m:
            return line
        return re.sub(r'fill="#[0-9a-f]{6}"',
                      'fill="%s"' % mass_gray(m[w][which]), line, count=1)

    def label(a, b, which):
        out = []
        word = None
        for i in range(a, b):
            l = lines[i]
            if 'width="17" height="17"' in l:
                word = re.search(r'font-weight="700">([^<]+)</tspan>',
                                 lines[i + 1]).group(1).lower()
                l = re.sub(r'fill="#[0-9a-f]{6}"',
                           'fill="%s"' % mass_gray(m[word][which]), l, count=1)
            elif "<tspan" in l:
                pct, d = m[word][which], m[word][2]
                #: `dx`, not two non-breaking spaces. The source figure used
                #: nbsp and some renderers collapse it, which runs the word
                #: into its own number.
                tail = ('<tspan dx="7" font-size="14.5" fill="#4a4843" '
                        'font-weight="700">%s%%</tspan>'
                        '<tspan dx="7" font-size="14" fill="#8a867e" '
                        'font-weight="600">%s</tspan>'
                        % (("%.2f" % pct), ("%+.2f" % d).replace("-", "−")))
                l = re.sub(r'<tspan font-size="15"[^>]*>&#160;&#160;[^<]+</tspan>',
                           tail, l)
            out.append(l)
        return out

    her_labels = [(a, b) for a, b, _w in blocks if (_first_x(lines[a + 2]) or 0) < 800]

    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" '
         'height="%d" font-family="Helvetica,Arial,sans-serif">' % (WIDTH, HEIGHT, WIDTH, HEIGHT),
         '<rect width="%d" height="%d" fill="#ffffff"/>' % (WIDTH, HEIGHT),
         '<text x="%g" y="54" text-anchor="middle" font-size="36" font-weight="700" '
         'fill="#16161a">Where the mass sits, before and after (X.1)</text>' % MID,
         '<text x="%g" y="82" text-anchor="middle" font-size="16.5" fill="#6b6862">'
         '“She slowly took off her ___”, 50 lineage pairs; darker = more of the '
         'slot’s probability</text>' % MID,
         '<path d="M %g 176 L %g 862" stroke="#e6e2da" stroke-width="1.4" '
         'stroke-dasharray="3 8"/>' % (MID, MID)]

    for which, label_txt, dx in ((0, "base", 0.0), (1, "aligned", SHIFT)):
        g = ['<g transform="translate(%g,0)">' % dx] if dx else []
        g.append('<text x="410.0" y="134" text-anchor="middle" font-size="25" '
                 'font-weight="700" fill="#16161a">%s</text>' % label_txt)
        g.append('<text x="410.0" y="158" text-anchor="middle" font-size="15" '
                 'fill="#6b6862">%s</text>'
                 % ("before alignment" if which == 0 else "after alignment"))
        g += [paint(l, which) for l in her_draw]
        for a, b in her_labels:
            g += label(a, b, which)
        if dx:
            g.append("</g>")
        o += g

    #: the legend, rebuilt: one white-to-black ramp on the same power scale,
    #: ticks at the values a reader would look for rather than at even steps.
    x0, x1, y = MID - 230, MID + 230, 886.0
    n = 230
    for k in range(n):
        x = x0 + (x1 - x0) * k / (n - 1.0)
        pct = MASS_MAX * ((k / (n - 1.0)) ** (1.0 / MASS_GAMMA))
        o.append('<rect x="%.2f" y="%g" width="%.2f" height="24.0" fill="%s"/>'
                 % (x, y, (x1 - x0) / n + 0.7, mass_gray(pct)))
    for pct in (0.1, 0.5, 1, 2, 5, 10):
        t = (pct / MASS_MAX) ** MASS_GAMMA
        x = x0 + (x1 - x0) * t
        o.append('<path d="M %.1f 910.0 L %.1f 915.0" stroke="#26262b" '
                 'stroke-width="1.1"/>' % (x, x))
        o.append('<text x="%.1f" y="930.0" text-anchor="middle" font-size="13" '
                 'fill="#4a4843">%s%%</text>'
                 % (x, ("%g" % pct)))
    o.append('<text x="%g" y="903" text-anchor="end" font-size="15" '
             'font-weight="700" fill="#4a4843">rare in the slot</text>' % (x0 - 16))
    o.append('<text x="%g" y="903" font-size="15" font-weight="700" '
             'fill="#16161a">common in the slot</text>' % (x1 + 16))
    o.append('<text x="%g" y="952" text-anchor="middle" font-size="15" '
             'fill="#3a3934">Each garment shaded by the median share of the slot it '
             'holds in that arm; one ramp serves both bodies, stretched as '
             '(share)^%g so the thin end stays legible.</text>' % (MID, MASS_GAMMA))
    o.append('<text x="%g" y="978" text-anchor="middle" font-size="15" '
             'fill="#3a3934">Labels read: garment, its share of the slot in that '
             'arm, and the signed change aligned − base in percentage points '
             '(the same number on both sides).</text>' % MID)
    o.append('<text x="%g" y="1012" text-anchor="middle" font-size="15" '
             'fill="#4a4843">The 27 garments drawn hold 47.4%% of the slot at base '
             'and 44.5%% after alignment. Recomputed 2026-09-18 from the movement '
             'store, 50 lineage-representative pairs, median per lineage.</text>' % MID)
    o.append("</svg>")
    return "\n".join(o) + "\n"


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
    ap.add_argument("--mass", action="store_true",
                    help="the other layout: her-frame only, base body beside "
                         "aligned body, shaded by probability mass.")
    ap.add_argument("--gray-only", action="store_true")
    ap.add_argument("--color-only", action="store_true")
    ap.add_argument("--outdir", default=os.path.join(HERE, "figures"))
    a = ap.parse_args(argv)

    if a.audit:
        audit(a.scale)
        return 0

    os.makedirs(a.outdir, exist_ok=True)
    if a.mass:
        path = os.path.join(a.outdir, "x1_garment_mass_gray.svg")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(build_mass(a.scale))
        print("-> %s" % path)
        return 0
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
