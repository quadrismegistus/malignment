#!/usr/bin/env python3
"""Figure X.1 as the paper prints it: the two CI garment bodies composed into one plate.

    python garment_pair.py                  # 4.8 in, the house width
    python garment_pair.py --width 4.33     # the width the 21 Sep plate was built at
    python garment_pair.py --out-dir DIR    # default figures/

Writes x1_garment_pair_ci.{svg,png,pdf,tif} and .caption.txt. Left body wears
what alignment takes away from "She slowly took off her", right body what it
adds, 15 falls and 5 rises, garments moving under 0.1 pp omitted.

## PROVENANCE: RECOVERED, NOT WRITTEN FRESH

A dario session (log 8690ed90) wrote this as `compose_garment_pair.py` in its
scratchpad on 2026-09-21 and delivered the plate to the paper seat. The script
was never committed; its only surviving copy was an UNTRACKED file in the
read-only archive (`malign-logits/meta/M01_displacement/scripts/`), placed there
the same minute as the last of its edits. Everything from `to_c` down is that
file, unedited except where marked `WIRED`.

## WHAT WIRING IN CHANGED, AND WHY

The recovered script typed its numbers in: 20 labels like ("shoes", "+2.65",
"#141414", ...) and read its two bodies from plates in the paper's folder. A
plate whose numbers are typed in does not notice when the data moves. Now:

- VALUE and GRAY come from `figure.masses("D")` and `figure.two_body_gray`, the
  same calls that shade the garments on the bodies, so a swatch cannot disagree
  with the garment it labels. Only the LAYOUT stays typed in: which edge of the
  garment each leader attaches to, placed by eye.
- BODIES come from `figure.build_two_body(...)` in memory, not from a file on
  disk, so the plate cannot sit on sources older than the producer.
- THE SELECTION IS ASSERTED. The garments labelled here must be exactly the
  garments `figure.py` itself labels on each arm. A garment that crosses the
  0.1 pp line after a re-run fails loudly instead of going unlabelled.
- WIDTH defaults to `malignment.figure.PUB_SIZE[0]` (RH, 2026-09-24: 4.8 in is
  the standard). Type is set in points, so it does not scale with the width.

Checked when wired: at `--width 4.33` the SVG is byte-identical to the plate
delivered on 2026-09-21.
The caption file is not: it said "Panel A"/"Panel B" for a plate with no
panel letters, and now names the left and right bodies (2026-09-24).
"""

import argparse
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
for p in (HERE, REPO):
    if p not in sys.path:
        sys.path.insert(0, p)

import figure as F                                   # noqa: E402  metonymy's producer
from malignment.figure import PUB_SIZE               # noqa: E402

SCALE = "D"
MIN_MOVE = 0.1


def _args():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--width", type=float, default=PUB_SIZE[0],
                    help="physical width in inches (default %g, the house width)" % PUB_SIZE[0])
    ap.add_argument("--out-dir", default=os.path.join(HERE, "figures"))
    return ap.parse_args()


ARGS = _args()
OUT_STEM = os.path.join(ARGS.out_dir, "x1_garment_pair_ci")

FONT = "Arial,Helvetica,sans-serif"
DPI = 300
PHYS_W = ARGS.width
VB_W = 1000.0
PPU = PHYS_W * 72.0 / VB_W   # points per viewBox unit


def pt(n):
    return n / PPU


FS = pt(7.0)             # one size throughout; 7 pt so a reduction to CI's 4.33 in print width stays over the 6 pt floor (RH, 2026-09-24)
PANEL_FS = pt(9.0)
AXIS_FS = pt(7.0)
SWATCH = pt(5.0)

BODY_SCALE = 0.85
BODY_SRC_XMIN, BODY_SRC_XMAX = 231, 580
BODY_SRC_YMIN, BODY_SRC_YMAX = 210, 810
BODY_W = (BODY_SRC_XMAX - BODY_SRC_XMIN) * BODY_SCALE
BODY_H = (BODY_SRC_YMAX - BODY_SRC_YMIN) * BODY_SCALE

GAP = 15.0
TOTAL_BODY = 2 * BODY_W + GAP
MARGIN = (VB_W - TOTAL_BODY) / 2.0

BODY_A_LEFT = MARGIN
BODY_B_LEFT = MARGIN + BODY_W + GAP
TX_A = BODY_A_LEFT - BODY_SCALE * BODY_SRC_XMIN
TX_B = BODY_B_LEFT - BODY_SCALE * BODY_SRC_XMIN

TOP_PAD = 10
PANEL_Y = TOP_PAD + PANEL_FS
BODY_TOP = PANEL_Y + 8
TY = BODY_TOP - BODY_SCALE * BODY_SRC_YMIN
BODY_BOT = BODY_TOP + BODY_H
AXIS_Y = BODY_BOT + 30
VB_H = AXIS_Y + AXIS_FS + 8
PHYS_H = VB_H / VB_W * PHYS_W

MIN_SPACING = FS * 1.08


# --- Label LAYOUT: (word, source_attach_x, source_attach_y) ---
# Placed by eye on the source body. Moved labels use a left-edge (base) or
# right-edge (aligned) attachment. WIRED: value and fill are no longer here.
BASE_LAYOUT = [
    ("clothes",    375, 220),
    ("scarf",      377, 304),
    ("bra",        376, 358),
    ("robe",       359, 398),
    ("shirt",      381, 434),
    ("top",        391, 436),
    ("panties",    383, 498),
    ("dress",      326, 606),
    ("pants",      355, 648),
    ("stockings",  368, 700),
    # Originally right, repointed to left edge of garment shape
    ("clothing",   445, 220),
    ("sweater",    368, 416),
    ("underwear",  397, 510),
    ("skirt",      350, 555),
    ("jeans",      365, 664),
]

ALIGNED_LAYOUT = [
    ("glasses", 468, 248),  # right temple end, avoids hat stack
    ("jacket",  473, 374),
    ("shoes",   488, 802),
    # Originally left, repointed to right edge of garment shape
    ("coat",    486, 352),
    ("gloves",  510, 488),
]


def sources():
    """WIRED: the two CI bodies from figure.py, in memory. -> (base_svg, aligned_svg)"""
    return tuple(F.build_two_body("movement", SCALE, MIN_MOVE, True, True, (arm,))
                 for arm in (0, 1))


def labelled_words(svg):
    """The garments figure.py itself labels on one arm's plate."""
    return {w.lower() for w in re.findall(r'font-weight="700">([^<]+)</tspan>', svg)
            if not re.match(r"[\u2212+\-]?[\d.]+$", w)}


def labels(layout, arm, drawn):
    """WIRED: (word, num, fill, sx, sy) with num and fill from the data.

    `arm` 0 is the base body (falls), 1 the aligned (rises); the shading value
    is the size of the move in that arm's direction, exactly as figure.py
    computes it for the garment itself.
    """
    words = {w for w, _x, _y in layout}
    assert words == drawn, (
        "arm %d: layout labels %s but figure.py labels %s -- a garment crossed "
        "the %.1f pp line or left it; place its leader before drawing"
        % (arm, sorted(words - drawn), sorted(drawn - words), MIN_MOVE))
    m = F.masses(SCALE)
    out = []
    for w, sx, sy in layout:
        d = m[w][2]
        assert (d < 0) if arm == 0 else (d > 0), "%s moved the other way: %+.3f" % (w, d)
        v = max(0.0, -d) if arm == 0 else max(0.0, d)
        num = ("%+.2f" % d).replace("-", "\u2212")
        out.append((w, num, F.two_body_gray(v, "movement"), sx, sy))
    return out


BASE_SVG_TEXT, ALIGNED_SVG_TEXT = sources()
BASE_LABELS = labels(BASE_LAYOUT, 0, labelled_words(BASE_SVG_TEXT))
ALIGNED_LABELS = labels(ALIGNED_LAYOUT, 1, labelled_words(ALIGNED_SVG_TEXT))


def to_c(sx, sy, tx):
    return tx + BODY_SCALE * sx, TY + BODY_SCALE * sy


HAT_STACK_STARTS = ("M 231.9", "M 231.3", "M 250.4", "M 523.8", "M 537.7")


def extract_body(svg_text):
    #: WIRED: takes the SVG text, not a path
    lines = svg_text.splitlines()
    body = []
    for line in lines[3:]:
        if 'stroke="#a8a49b"' in line or line.strip().startswith("</svg"):
            break
        if any(('d="' + p) in line for p in HAT_STACK_STARTS):
            continue
        body.append(line)
    return body


CLOTHING_CLOTHES_GAP = MIN_SPACING * 1.6


def place_labels(labels, tx):
    items = []
    for word, num, fill, sx, sy in labels:
        cx, cy = to_c(sx, sy, tx)
        items.append((word, num, fill, cx, cy))
    items.sort(key=lambda x: x[4])

    placed = []
    prev_y = -999
    prev_word = ""
    for word, num, fill, cx, cy in items:
        gap = MIN_SPACING
        if prev_word == "clothing" and word == "clothes":
            gap = CLOTHING_CLOTHES_GAP
        ly = max(cy, prev_y + gap)
        placed.append((word, num, fill, cx, cy, ly))
        prev_y = ly
        prev_word = word
    return placed


NO_LEADER = {"clothes", "clothing"}
DOT_R = 2.0
DOT_FILL = "#5a5650"


def left_label(word, num, fill, ax, ay, ly):
    sx = MARGIN - SWATCH - 2
    tx = sx - 3
    lx = sx + SWATCH + 2
    parts = [
        '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%.1f" '
        'fill="%s" stroke="#4a4843" stroke-width="0.6"/>'
        % (sx, ly - SWATCH / 2, SWATCH, SWATCH, SWATCH * 0.2, fill),
        '<text x="%.1f" y="%.1f" text-anchor="end" font-size="%.2f" fill="#1d1d20">'
        '<tspan>%s</tspan>'
        '<tspan dx="3" fill="#4a4843">%s</tspan>'
        '</text>' % (tx, ly + FS * 0.33, FS, word, num),
    ]
    if word not in NO_LEADER:
        parts.append(
            '<path d="M %.1f %.1f L %.1f %.1f" '
            'fill="none" stroke="#8a8580" stroke-width="0.5"/>'
            % (lx, ly, ax, ay))
        parts.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s"/>'
                     % (ax, ay, DOT_R, DOT_FILL))
    return "\n".join(parts)


def right_label(word, num, fill, ax, ay, ly):
    sx = VB_W - MARGIN + 2
    tx = sx + SWATCH + 3
    rx = sx - 2
    parts = [
        '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%.1f" '
        'fill="%s" stroke="#4a4843" stroke-width="0.6"/>'
        % (sx, ly - SWATCH / 2, SWATCH, SWATCH, SWATCH * 0.2, fill),
        '<text x="%.1f" y="%.1f" text-anchor="start" font-size="%.2f" fill="#1d1d20">'
        '<tspan>%s</tspan>'
        '<tspan dx="3" fill="#4a4843">%s</tspan>'
        '</text>' % (tx, ly + FS * 0.33, FS, word, num),
    ]
    if word not in NO_LEADER:
        parts.append(
            '<path d="M %.1f %.1f L %.1f %.1f" '
            'fill="none" stroke="#8a8580" stroke-width="0.5"/>'
            % (ax, ay, rx, ly))
        parts.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s"/>'
                     % (ax, ay, DOT_R, DOT_FILL))
    return "\n".join(parts)


def build():
    base_body = extract_body(BASE_SVG_TEXT)       # WIRED
    aligned_body = extract_body(ALIGNED_SVG_TEXT)
    print("  body lines: base %d, aligned %d" % (len(base_body), len(aligned_body)))

    base_placed = place_labels(BASE_LABELS, TX_A)
    aligned_placed = place_labels(ALIGNED_LABELS, TX_B)

    body_a_cx = BODY_A_LEFT + BODY_W / 2
    body_b_cx = BODY_B_LEFT + BODY_W / 2

    o = []
    o.append('<svg xmlns="http://www.w3.org/2000/svg" '
             'viewBox="0 0 %.0f %.0f" width="%.2fin" height="%.3fin" '
             'font-family="%s">'
             % (VB_W, VB_H, PHYS_W, PHYS_H, FONT))
    o.append('<rect width="%.0f" height="%.0f" fill="#ffffff"/>' % (VB_W, VB_H))

    # # Panel letters (disabled)
    # o.append('<text x="%.1f" y="%.1f" font-size="%.1f" '
    #          'font-weight="700" fill="#16161a">A</text>'
    #          % (BODY_A_LEFT, PANEL_Y, PANEL_FS))
    # o.append('<text x="%.1f" y="%.1f" font-size="%.1f" '
    #          'font-weight="700" fill="#16161a">B</text>'
    #          % (BODY_B_LEFT, PANEL_Y, PANEL_FS))

    # Base body
    o.append('<!-- Panel A: base (falls) -->')
    o.append('<g transform="translate(%.2f,%.2f) scale(%.4f)">'
             % (TX_A, TY, BODY_SCALE))
    o.extend(base_body)
    o.append('</g>')

    # Aligned body
    o.append('<!-- Panel B: aligned (rises) -->')
    o.append('<g transform="translate(%.2f,%.2f) scale(%.4f)">'
             % (TX_B, TY, BODY_SCALE))
    o.extend(aligned_body)
    o.append('</g>')

    # # Divider between panels (disabled)
    # mid = BODY_A_LEFT + BODY_W + GAP / 2
    # o.append('<path d="M %.1f %.1f L %.1f %.1f" '
    #          'stroke="#e6e2da" stroke-width="0.8" stroke-dasharray="3 6"/>'
    #          % (mid, BODY_TOP - 5, mid, BODY_BOT + 5))

    # Base labels (left)
    o.append('<!-- Base labels (outboard left) -->')
    for word, num, fill, ax, ay, ly in base_placed:
        o.append(left_label(word, num, fill, ax, ay, ly))

    # Aligned labels (right)
    o.append('<!-- Aligned labels (outboard right) -->')
    for word, num, fill, ax, ay, ly in aligned_placed:
        o.append(right_label(word, num, fill, ax, ay, ly))

    # Axis subtitles
    o.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="%.2f" '
             'font-weight="700" fill="#16161a">'
             'Falls under alignment</text>'
             % (body_a_cx, AXIS_Y, AXIS_FS))
    o.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="%.2f" '
             'font-weight="700" fill="#16161a">'
             'Rises under alignment</text>'
             % (body_b_cx, AXIS_Y, AXIS_FS))

    o.append('</svg>')

    os.makedirs(os.path.dirname(OUT_STEM), exist_ok=True)   # WIRED
    svg_path = OUT_STEM + ".svg"
    with open(svg_path, "w") as f:
        f.write("\n".join(o) + "\n")
    print("-> %s  (%.2f x %.2f in)" % (svg_path, PHYS_W, PHYS_H))
    #: WIRED: printed from the constants, not typed -- it said 6.5/6.0 after they moved
    print("   label font: %.1f pt, axis: %.1f pt" % (FS * PPU, AXIS_FS * PPU))

    # Print label placements for audit
    print("\n  Base label placements:")
    for word, num, fill, ax, ay, ly in base_placed:
        print("    %-12s attach (%.0f, %.0f)  label y=%.0f  offset=%+.0f"
              % (word, ax, ay, ly, ly - ay))
    print("\n  Aligned label placements:")
    for word, num, fill, ax, ay, ly in aligned_placed:
        print("    %-12s attach (%.0f, %.0f)  label y=%.0f  offset=%+.0f"
              % (word, ax, ay, ly, ly - ay))

    return svg_path


def export(svg_path):
    for tool in ("rsvg-convert", "sips"):
        if not shutil.which(tool):
            print("  export needs %s" % tool)
            return []

    stem = os.path.splitext(svg_path)[0]
    w_px = int(round(PHYS_W * DPI))
    out = []

    png = stem + ".png"
    subprocess.run(["rsvg-convert", "-w", str(w_px), "-f", "png",
                    svg_path, "-o", png], check=True)
    subprocess.run(["sips", "-s", "dpiWidth", str(DPI),
                    "-s", "dpiHeight", str(DPI), png],
                   check=True, capture_output=True)
    out.append(png)
    print("-> %s" % png)

    pdf = stem + ".pdf"
    subprocess.run(["rsvg-convert", "-f", "pdf", svg_path, "-o", pdf],
                   check=True)
    out.append(pdf)
    print("-> %s" % pdf)

    tif = stem + ".tif"
    subprocess.run(["sips", "-s", "format", "tiff", png, "--out", tif],
                   check=True, capture_output=True)
    subprocess.run(["sips", "-s", "dpiWidth", str(DPI),
                    "-s", "dpiHeight", str(DPI), tif],
                   check=True, capture_output=True)
    out.append(tif)
    print("-> %s" % tif)

    # Print achieved pixel dimensions
    r = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", png],
                       capture_output=True, text=True)
    wpx = int(re.search(r"pixelWidth: (\d+)", r.stdout).group(1))
    hpx = int(re.search(r"pixelHeight: (\d+)", r.stdout).group(1))
    print("   %d x %d px at %d dpi = %.3f x %.3f in"
          % (wpx, hpx, DPI, wpx / DPI, hpx / DPI))
    return out


def write_caption():
    #: WIRED: the plate has no panel letters (disabled on 21 Sep), so the
    #: caption names the bodies by the subtitles the plate actually carries
    lines = ["Left body, falls under alignment: what alignment takes away"]
    for word, num, _, _, sy in sorted(BASE_LABELS, key=lambda x: x[4]):
        lines.append("  %-12s %s pp" % (word, num))
    lines.append("")
    lines.append("Right body, rises under alignment: what alignment adds")
    for word, num, _, _, sy in sorted(ALIGNED_LABELS, key=lambda x: x[4]):
        lines.append("  %-12s %s pp" % (word, num))
    lines.append("")
    lines.append("Median change in next-token probability (percentage points),")
    lines.append("base to aligned, 50 lineage-representative pairs.")
    lines.append("Prompt: \"She slowly took off her ___\"; scale D; |delta| >= 0.1 pp.")
    lines.append("Darker = larger change. Left body wears what alignment removes;")
    lines.append("right body wears what it adds. A garment blank on one side does")
    lines.append("not move that direction.")

    path = OUT_STEM + ".caption.txt"
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print("-> %s" % path)




if __name__ == "__main__":
    svg = build()
    export(svg)
    write_caption()
