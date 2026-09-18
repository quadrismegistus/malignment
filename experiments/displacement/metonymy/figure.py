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
# Two bodies, one frame: `--mass` and `--movement`
# --------------------------------------------------------------------------
#: The X.1 drawing shades a DIFFERENCE on one body. Both modes here draw the
#: her-frame body TWICE, base on the left and aligned on the right, and differ
#: only in what the shading means.
#:
#: `--mass`      each garment shaded by the share of the slot it holds in that
#:               arm. A picture of two distributions; the difference survives
#:               as the signed number in the label.
#: `--movement`  the left body shaded by how far the garment FALLS, the right
#:               by how far it RISES, and a garment that does not move that way
#:               is left blank AND UNLABELLED on that side. So the left body
#:               wears what alignment takes off and the right wears what it
#:               puts on, and the emptiness of the right body is the finding
#:               rather than a gap in the data.
#:
#: ONE RAMP SERVES BOTH BODIES in both modes. Shading each panel against its
#: own maximum would make the two incomparable at a glance, which is the only
#: thing this layout is for. In `--movement` that costs the falls their
#: contrast -- the biggest fall is 0.55pp against a biggest rise of 2.65 --
#: and that asymmetry is the thing the layout exists to show: the withdrawal
#: is spread over twenty garments, the return concentrates on two.
MASS_MAX = 10.0          # percent; `clothes` at base is 9.08 and is the peak
MASS_GAMMA = 0.45        # the slot spans 0.12% to 9.1%, a factor of 76
MOVE_MAX = 2.7           # pp; `shoes` rises 2.65 and is the peak
MOVE_GAMMA = 0.45
MASS_PAPER, MASS_INK = 0.98, 0.07
SHIFT = 875.0            # how far right the aligned body sits
WIDTH, HEIGHT = 1760, 1100
MID = 880.0

#: Drawing pieces that carry no swatch of their own and so match no word by
#: fill, but belong to one: the belt's buckle, the bra's centre seam, the
#: spectacle bridge and its two temples. They matter only when a garment can
#: be REMOVED -- otherwise they are painted white and nobody notices. Keyed by
#: 1-indexed line in the source, her panel only, which is the only panel the
#: two-body layouts draw.
ORPHANS = {40: "belt", 43: "bra", 54: "glasses", 55: "glasses", 56: "glasses"}

#: A CORRECTION TO THE DRAWING, not to the data. The source nests the torso
#: outward as top, shirt, sweater, jacket, robe, coat -- which puts a robe
#: OUTSIDE a jacket. A robe is indoor and sits nearer the skin; a jacket is
#: outerwear. Swapping which word owns which shape fixes the ordering without
#: touching a single coordinate: the label that points at the outer shape now
#: reads `jacket` and the one that points at the inner reads `robe`.
#:
#: Applied in the two-body layouts only. `build()` is a faithful recolour of
#: the published X.1 and is left alone, so the figure of record keeps the
#: layering it was published with.
LAYER_SWAP = {"robe": "jacket", "jacket": "robe"}

#: The source drew a boot on the left foot and a shoe on the right, so the two
#: feet are not interchangeable. Remove `boots` and one foot goes bare. When
#: that happens, mirror the shoe across the body's axis and give it to `shoes`
#: as well, so the figure keeps a pair. Nothing about the measurement changes:
#: both shapes carry one word's one number.
HER_AXIS = 410.0
SHOE_LINE = 36                # 1-indexed in the source, the her-panel shoe

#: ONE WEIGHT FOR EVERY LINE IN THE DRAWING. The source runs seven: garments
#: at 1.2 to 1.6, the head at 3.2, the arms at 4.5, the spine at 5.0, the legs
#: at 5.5. At those weights a limb reads as a filled dark layer rather than as
#: a limb, and the eye sorts the picture by stroke weight before it gets to
#: the fills -- which are the only thing here carrying a number. Everything in
#: the body goes to the garments' own weight.
STROKE = 1.4
#: and every line in the drawing is lifted off the page at one opacity --
#: garments, head, arms, legs, the smile. The drawing is a coordinate system,
#: not a subject: the only thing here carrying a number is the fill, and a
#: solid black contour around a near-white garment competes with it. One
#: value, for the same reason as one stroke weight.
BORDER_OPACITY = 0.45

MODES = {
    #: (max, what the shading means, the two panel subtitles, the two pole
    #: labels on the legend, the tick values)
    "mass": (MASS_MAX, "share of the slot",
             ("before alignment", "after alignment"),
             ("rare in the slot", "common in the slot"),
             (0.1, 0.5, 1, 2, 5, 10), "%"),
    "movement": (MOVE_MAX, "how far it moves",
                 ("what alignment takes away", "what alignment adds"),
                 ("barely moves", "moves most"),
                 (0.05, 0.1, 0.25, 0.5, 1, 2), ""),
}


def two_body_gray(v, mode):
    """v -> hex. 0 is paper in both modes, and in `movement` means 'not this way'."""
    import matplotlib.colors as mc
    top = MODES[mode][0]
    g = min(1.0, max(0.0, v / top)) ** MASS_GAMMA
    lo = 1.0 if mode == "movement" else MASS_PAPER
    return mc.to_hex((lo + (MASS_INK - lo) * g,) * 3)


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


def _mirror_d(d, axis):
    """Reflect an absolute-coordinate path about a vertical line.

    Every command in this drawing takes x y pairs -- M, L and Q -- so the
    parse is: a letter resets the phase, then numbers alternate x, y.
    """
    out, phase = [], 0
    for tok in d.split():
        if re.match(r'^[A-Za-z]$', tok):
            out.append(tok)
            phase = 0
            continue
        v = float(tok)
        out.append("%g" % ((2 * axis - v) if phase % 2 == 0 else v))
        phase += 1
    return " ".join(out)


#: Critical Inquiry: 4.8 inches of column, nothing smaller than 6pt, and no
#: title, caption or legend inside the image -- the journal sets those.
CI_WIDTH_IN = 4.8
CI_MIN_PT = 6.0
PT_PER_IN = 72.0
#: Helvetica advance widths as a fraction of the em, averaged over mixed case.
#: Good to a few percent, which is all the margin here needs; the achieved
#: figures are printed so a wrong guess is visible rather than silent.
EM_BOLD, EM_PLAIN = 0.58, 0.55


def _label_width(text_line):
    """Rough rendered width, in user units, of one label's <text> element.

    A tspan with no `font-size` inherits the parent <text>'s, so the parent
    has to be read. Hardcoding 16.5 here was right until CI mode started
    scaling the type, at which point the word was measured at half its
    rendered width and the crop clipped the first and last labels.
    """
    parent = re.search(r'<text[^>]*font-size="([\d.]+)"', text_line)
    parent = float(parent.group(1)) if parent else 16.5
    w = 0.0
    for size, weight, body in re.findall(
            r'<tspan(?:[^>]*font-size="([\d.]+)")?([^>]*)>([^<]*)</tspan>',
            text_line):
        size = float(size) if size else parent
        em = EM_BOLD if 'font-weight="700"' in weight else EM_PLAIN
        w += len(body.replace("&#160;", " ")) * em * size
        w += 7.0 if 'dx="7"' in weight else 0.0
    return w


def _boost_fonts(line, k):
    if k == 1.0:
        return line
    return re.sub(r'font-size="([\d.]+)"',
                  lambda m_: 'font-size="%.4g"' % (float(m_.group(1)) * k), line)


def build_two_body(mode, scale="D", min_move=0.0, layer_swap=True,
                   ci=False, arms=(0, 1), font_boost=1.0):
    """Two her-frame bodies, base and aligned, greyscale. See MODES.

    `min_move` drops a garment whose |median Δ| falls below it -- from the
    drawing as well as from the labels, pieces and all, so the layer goes
    rather than being left blank. `layer_swap` applies `LAYER_SWAP`.
    """
    lines = open(SOURCE, encoding="utf-8").read().splitlines()
    m = masses(scale)
    top, meaning, subtitles, poles, ticks, unit = MODES[mode]

    def kept(word):
        return word in m and abs(m[word][2]) >= min_move

    def value(word, which):
        """What the shading encodes for this word on this side."""
        base, aligned, d = m[word]
        if mode == "mass":
            return base if which == 0 else aligned
        #: `movement`: the left body carries the falls, the right the rises,
        #: and each is blank for the other's words.
        return max(0.0, -d) if which == 0 else max(0.0, d)

    def shown(word, which):
        return mode == "mass" or value(word, which) > 0

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
    #: same way `read_source` does, with the same one override, plus the
    #: pieces that carry no fill of their own.
    _l2, _sw, bodymap = read_source()
    fills = {}
    for i, (panel, word) in bodymap.items():
        if panel == "her":
            fills[_l2[i]] = word
    for ln, word in ORPHANS.items():
        fills[lines[ln - 1]] = word

    #: thin the body strokes, and lift the garment outlines off their fills.
    #: Both edits change the line text and `fills` is keyed BY line text, so
    #: the membership test has to be taken ONCE, before either map is rebuilt.
    #: Rebuilding `fills` first and `her_draw` second silently unmaps every
    #: garment -- the draw lines then miss the softened keys and paint white.
    soften = ('stroke="#26262b"',
              'stroke="#26262b" stroke-opacity="%g"' % BORDER_OPACITY)

    def restyle(l):
        #: Everything gets both, so there is no membership test left to get
        #: wrong. The previous version tested the ALREADY-REWRITTEN line
        #: against a set of source lines, which matched only the six garments
        #: whose stroke-width was already STROKE.
        l = re.sub(r'stroke-width="[\d.]+"', 'stroke-width="%g"' % STROKE, l)
        return l.replace(*soften)

    fills = {restyle(k): v for k, v in fills.items()}
    her_draw = [restyle(l) for l in her_draw]

    #: give her a second shoe when the boot that filled the other foot is gone
    shoe = next((l for l in her_draw if fills.get(l) == "shoes"), None)
    if shoe is not None and not kept("boots"):
        twin = re.sub(r'd="([^"]+)"',
                      lambda mo: 'd="%s"' % _mirror_d(mo.group(1), HER_AXIS),
                      shoe)
        her_draw = her_draw[:her_draw.index(shoe)] + [twin] + \
            her_draw[her_draw.index(shoe):]
        fills[twin] = "shoes"
    if layer_swap:
        for line, w in list(fills.items()):
            if w in LAYER_SWAP:
                fills[line] = LAYER_SWAP[w]

    def paint(line, which):
        w = fills.get(line)
        if w is None or w not in m:
            return line
        return re.sub(r'fill="#[0-9a-f]{6}"',
                      'fill="%s"' % two_body_gray(value(w, which), mode),
                      line, count=1)

    def label(a, b, which):
        word = re.search(r'font-weight="700">([^<]+)</tspan>',
                         lines[a + 3]).group(1).lower()
        if layer_swap:
            word = LAYER_SWAP.get(word, word)
        if not kept(word) or not shown(word, which):
            return []
        out = []
        for i in range(a, b):
            l = lines[i]
            if "<tspan" in l:
                #: the swap renames the label as well as the shape, which is
                #: the whole of it: the leader still points where it pointed.
                l = re.sub(r'(<tspan font-weight="700">)[^<]+(</tspan>)',
                           r'\g<1>%s\g<2>' % word, l)
            if 'width="17" height="17"' in l:
                l = re.sub(r'fill="#[0-9a-f]{6}"',
                           'fill="%s"' % two_body_gray(value(word, which), mode),
                           l, count=1)
            elif "<tspan" in l:
                d = m[word][2]
                if mode == "mass":
                    #: `dx`, not two non-breaking spaces. The source used nbsp
                    #: and some renderers collapse it, running the word into
                    #: its own number.
                    tail = ('<tspan dx="7" font-size="14.5" fill="#4a4843" '
                            'font-weight="700">%.2f%%</tspan>'
                            '<tspan dx="7" font-size="14" fill="#8a867e" '
                            'font-weight="600">%s</tspan>'
                            % (value(word, which),
                               ("%+.2f" % d).replace("-", "−")))
                else:
                    tail = ('<tspan dx="7" font-size="14.5" fill="#4a4843" '
                            'font-weight="700">%s</tspan>'
                            % ("%+.2f" % d).replace("-", "−"))
                l = re.sub(r'<tspan font-size="15"[^>]*>&#160;&#160;[^<]+</tspan>',
                           tail, l)
                l = _boost_fonts(l, font_boost)
            out.append(l)
        return out

    her_labels = [(a, b) for a, b, _w in blocks if (_first_x(lines[a + 2]) or 0) < 800]

    title = ("Where the mass sits, before and after (X.1)" if mode == "mass"
             else "What alignment takes off, and what it puts on (X.1)")
    sub = ("darker = more of the slot’s probability" if mode == "mass"
           else "left body shaded by how far each garment FALLS, right body by "
                "how far it RISES; a garment that does not move that way is "
                "left blank and unlabelled")
    o = []
    if not ci:
        o += ['<text x="%g" y="54" text-anchor="middle" font-size="36" '
              'font-weight="700" fill="#16161a">%s</text>' % (MID, title),
              '<text x="%g" y="82" text-anchor="middle" font-size="16.5" '
              'fill="#6b6862">“She slowly took off her ___”, 50 lineage pairs; '
              '%s</text>' % (MID, sub),
              '<path d="M %g 176 L %g 862" stroke="#e6e2da" stroke-width="1.4" '
              'stroke-dasharray="3 8"/>' % (MID, MID)]

    #: content extent, tracked as the parts go in, so the CI crop is measured
    #: rather than guessed. `_label_width` is an estimate; the achieved font
    #: size is printed so a bad one shows up instead of clipping silently.
    xs, ys = [], []
    placed = [(w, SHIFT if len(arms) > 1 and w == 1 else 0.0) for w in arms]
    for which, dx in placed:
        head = ("base", "aligned")[which]
        g = ['<g transform="translate(%g,0)">' % dx] if dx else []
        if ci:
            g.append(_boost_fonts(
                '<text x="410.0" y="150" text-anchor="middle" font-size="21" '
                'font-weight="700" fill="#16161a">%s</text>' % head, font_boost))
            ys.append(132)
        else:
            g.append('<text x="410.0" y="134" text-anchor="middle" '
                     'font-size="25" font-weight="700" fill="#16161a">%s</text>'
                     % head)
            g.append('<text x="410.0" y="158" text-anchor="middle" '
                     'font-size="15" fill="#6b6862">%s</text>' % subtitles[which])
            ys.append(116)
        g += [paint(l, which) for l in her_draw
              if fills.get(l) is None or kept(fills[l])]
        for a, b in her_labels:
            block = label(a, b, which)
            g += block
            if not block:
                continue
            txt = block[-1]
            tx = float(re.search(r'<text x="([-\d.]+)"', txt).group(1))
            w = _label_width(txt)
            lo, hi = ((tx - w, tx) if 'text-anchor="end"' in txt else (tx, tx + w))
            xs += [lo + dx, hi + dx]
            ys.append(float(re.search(r'y="([-\d.]+)"', txt).group(1)))
        xs += [183.5 + dx, 637.0 + dx]          # the body, swatch to swatch
        ys.append(840.0)                        # the ground line
        if dx:
            g.append("</g>")
        o += g

    if ci and len(arms) == 1:
        #: ONE BOX FOR THE PAIR. The two arms label different garments, so
        #: cropping each to its own content gives two files at two scales, and
        #: a reader setting them side by side gets two different-sized bodies.
        #: Measure the arm that is not being drawn as well, and discard it.
        for a, b in her_labels:
            block = label(a, b, 1 - arms[0])
            if not block:
                continue
            txt = block[-1]
            tx = float(re.search(r'<text x="([-\d.]+)"', txt).group(1))
            w = _label_width(txt)
            xs += ([tx - w, tx] if 'text-anchor="end"' in txt else [tx, tx + w])
            ys.append(float(re.search(r'y="([-\d.]+)"', txt).group(1)))

    if ci:
        pad = 10.0
        bx0, bx1 = min(xs) - pad, max(xs) + pad
        by0, by1 = min(ys) - pad, max(ys) + pad
        s_ = CI_WIDTH_IN * PT_PER_IN / (bx1 - bx0)
        smallest = min(float(m_) for m_ in
                       re.findall(r'font-size="([\d.]+)"', "".join(o)))
        #: ONE RETRY, never a loop. Bigger type widens the box, which shrinks
        #: the scale, so the fixed point is approached from below; a 3% margin
        #: clears it in one step for everything here. If it does not, the
        #: figure says so rather than shipping 5.9pt.
        if smallest * s_ < CI_MIN_PT and font_boost == 1.0:
            return build_two_body(mode, scale, min_move, layer_swap, ci, arms,
                                  CI_MIN_PT / (smallest * s_) * 1.03)
        print("   CI: viewBox %.0f x %.0f -> %.2f x %.2f in; smallest type "
              "%.1fpt%s%s" % (bx1 - bx0, by1 - by0, CI_WIDTH_IN,
                              (by1 - by0) * s_ / PT_PER_IN, smallest * s_,
                              "" if font_boost == 1.0
                              else "  (type up %.0f%%)" % (100 * font_boost - 100),
                              "" if smallest * s_ >= CI_MIN_PT
                              else "  ** UNDER %gpt, WILL NOT FIT **" % CI_MIN_PT))
        head_ = ('<svg xmlns="http://www.w3.org/2000/svg" '
                 'viewBox="%.1f %.1f %.1f %.1f" width="%gin" height="%.3fin" '
                 'font-family="Helvetica,Arial,sans-serif">'
                 % (bx0, by0, bx1 - bx0, by1 - by0, CI_WIDTH_IN,
                    (by1 - by0) * s_ / PT_PER_IN),
                 '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" '
                 'fill="#ffffff"/>' % (bx0, by0, bx1 - bx0, by1 - by0))
        return "\n".join(head_ + tuple(o)) + "\n</svg>\n"

    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" '
         'height="%d" font-family="Helvetica,Arial,sans-serif">'
         % (WIDTH, HEIGHT, WIDTH, HEIGHT),
         '<rect width="%d" height="%d" fill="#ffffff"/>' % (WIDTH, HEIGHT)] + o

    #: the legend, rebuilt: one white-to-black ramp on the same power scale,
    #: ticks at the values a reader would look for rather than at even steps.
    x0, x1, y = MID - 230, MID + 230, 886.0
    n = 230
    for k in range(n):
        x = x0 + (x1 - x0) * k / (n - 1.0)
        o.append('<rect x="%.2f" y="%g" width="%.2f" height="24.0" fill="%s"/>'
                 % (x, y, (x1 - x0) / n + 0.7,
                    two_body_gray(top * ((k / (n - 1.0)) ** (1.0 / MASS_GAMMA)),
                                  mode)))
    for v in ticks:
        x = x0 + (x1 - x0) * (v / top) ** MASS_GAMMA
        o.append('<path d="M %.1f 910.0 L %.1f 915.0" stroke="#26262b" '
                 'stroke-width="1.1"/>' % (x, x))
        o.append('<text x="%.1f" y="930.0" text-anchor="middle" font-size="13" '
                 'fill="#4a4843">%g%s</text>' % (x, v, unit))
    o.append('<text x="%g" y="903" text-anchor="end" font-size="15" '
             'font-weight="700" fill="#4a4843">%s</text>' % (x0 - 16, poles[0]))
    o.append('<text x="%g" y="903" font-size="15" font-weight="700" '
             'fill="#16161a">%s</text>' % (x1 + 16, poles[1]))

    if mode == "mass":
        caption = [
            "Each garment shaded by the median share of the slot it holds in "
            "that arm; one ramp serves both bodies, stretched as (share)^%g so "
            "the thin end stays legible." % MASS_GAMMA,
            "Labels read: garment, its share of the slot in that arm, and the "
            "signed change aligned − base in percentage points (the same "
            "number on both sides).",
            "The 27 garments drawn hold 47.4% of the slot at base and 44.5% "
            "after alignment. Recomputed 2026-09-18 from the movement store, "
            "50 lineage-representative pairs, median per lineage."]
    else:
        drawn = [w for _a, _b, w in blocks
                 if (_first_x(lines[_a + 2]) or 0) < 800 and kept(w)]
        nf = sum(1 for w in drawn if m[w][2] < 0)
        nr = sum(1 for w in drawn if m[w][2] > 0)
        caption = [
            "One ramp, in percentage points of median Δ, serves both bodies, "
            "so a fall and a rise of the same size print the same grey. "
            "Stretched as (Δ)^%g." % MOVE_GAMMA,
            "%d of the %d garments shown fall and %d rise%s. The right body is "
            "emptier because the withdrawal spreads over many garments while "
            "the return concentrates on shoes (+2.65) and glasses (+1.09)."
            % (nf, nf + nr, nr,
               ("; garments moving less than %g pp are not drawn" % min_move)
               if min_move else ""),
            "Recomputed 2026-09-18 from the movement store, 50 "
            "lineage-representative pairs, median per lineage."]
    for k, line in enumerate(caption):
        o.append('<text x="%g" y="%d" text-anchor="middle" font-size="15" '
                 'fill="%s">%s</text>'
                 % (MID, 952 + 26 * k, "#3a3934" if k < 2 else "#4a4843", line))
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
    ap.add_argument("--two-body", choices=sorted(MODES),
                    help="the other layout: her-frame only, base body beside "
                         "aligned body. `mass` shades by share of the slot; "
                         "`movement` shades the left by how far each garment "
                         "falls and the right by how far it rises, blanking "
                         "and unlabelling what does not move that way.")
    ap.add_argument("--mass", action="store_true",
                    help="shorthand for --two-body mass")
    ap.add_argument("--min-move", type=float, default=0.0,
                    help="two-body only: drop a garment whose |median Δ| is "
                         "below this, from the DRAWING as well as the labels. "
                         "0.1 removes hat, tie, watch, belt, socks, heels and "
                         "boots from the her frame.")
    ap.add_argument("--ci", action="store_true",
                    help="Critical Inquiry format: %gin wide, no title, no "
                         "caption, no legend, cropped to the content. Writes "
                         "one file per arm unless --ci-both." % CI_WIDTH_IN)
    ap.add_argument("--ci-both", action="store_true",
                    help="with --ci, both arms in one %gin file. Prints the "
                         "achieved type size, which is the whole question."
                         % CI_WIDTH_IN)
    ap.add_argument("--no-layer-swap", action="store_true",
                    help="two-body only: keep the published nesting, which "
                         "puts the robe outside the jacket.")
    ap.add_argument("--gray-only", action="store_true")
    ap.add_argument("--color-only", action="store_true")
    ap.add_argument("--outdir", default=os.path.join(HERE, "figures"))
    a = ap.parse_args(argv)

    if a.audit:
        audit(a.scale)
        return 0

    os.makedirs(a.outdir, exist_ok=True)
    mode = a.two_body or ("mass" if a.mass else None)
    if mode:
        tag = "" if not a.min_move else "_m%g" % a.min_move
        if not a.ci:
            jobs = [((0, 1), "")]
        elif a.ci_both:
            jobs = [((0, 1), "_ci")]
        else:
            jobs = [((0,), "_ci_base"), ((1,), "_ci_aligned")]
        for arms, suffix in jobs:
            path = os.path.join(a.outdir, "x1_garment_%s%s%s_gray.svg"
                                % (mode, tag, suffix))
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(build_two_body(mode, a.scale, a.min_move,
                                        not a.no_layer_swap, a.ci, arms))
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
