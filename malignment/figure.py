"""THE HOUSE PUBLICATION STYLE, IN ONE PLACE.

Critical Inquiry typesets the figure number, title, legend and notes itself and
forbids a figure repeating them, so a publication render carries only the
figure's OWN labelling: axis titles, tick labels, and whatever key sits inside
the panel. Everything else is the manuscript's.

**THIS MODULE EXISTS BECAUSE THE SECOND PRODUCER WAS ABOUT TO COPY THE FIRST.**
`exploratory/prompt_slopes/plot.py` grew these constants while it was the only
publication figure. A second one wanting the same page geometry had two
options: import them, or paste them. Pasting is how `meta/` ended up with a
median in one folder and a mean in another under one name -- and how a second
model loader drifted from the first until it could measure something the runner
would refuse. The rule this repo keeps relearning: a second copy is the one
without the docstring, and it diverges silently because both halves keep
working.

## THE NUMBERS AND WHERE THEY COME FROM

    PUB_SIZE      4.8 x 3.36 in.  RH MEASURED the text block at 4.8; 4.5 was
                  the received figure and it was wrong. 10:7 aspect kept.
    PUB_FONT_PT   9 pt, ONE size for every piece of text. Rendering at FINAL
                  size is the point: a 10-inch render reduced to the column
                  turns 12 pt into ~5.8 pt, and that is what breaks charts.
    PUB_RULE_PT   0.5 pt, the printed weight. Below this a rule can drop out
                  of the plate entirely.
    PUB_GRAY      #9aa1a7 for de-emphasised series.

Colour is permitted for line charts (the ban is on bar graphs), but some copies
print grayscale, where two mid-saturation hues become two similar grays. So
anything a reader must tell apart needs a second channel -- weight, dash, or a
label at the line end.
"""
import os

PUB_SIZE = (4.8, 3.36)
PUB_FONT_PT = 9
PUB_RULE_PT = 0.5
PUB_LINE_PT = 1.0
#: ── GRAYSCALE BY DEFAULT ────────────────────────────────────────────────
#: **THE HOUSE PALETTE IS VALUE, NOT HUE. RH, 2026-09-16.** Colour is
#: permitted for line charts, but some copies print grayscale and two
#: mid-saturation hues become two similar grays -- the risk we accepted when
#: the dash came off the `kill -> scream` riser, leaving red and blue
#: differing by hue alone. Designing in value removes the risk instead of
#: managing it: the figure a reader sees IS the figure we checked.
#:
#: **SET BY INK PERCENTAGE, NOT BY EYE.** CI's halftone rule: grays between
#: 20% and 80% ink, and at least 20 points apart. The first grayscale pass was
#: picked visually and failed it -- 84.6 / 54.6 / 37.4, so the riser and the
#: flat words sat 17 points apart and would have muddied on a plate.
#: Recomputed to the rule (paper-claude, 2026-09-16), and NEUTRAL: the old
#: values carried a blue cast that a grayscale separation renders as an
#: unintended lightness shift.
#:
#:     PUB_INK    100%  solid black, line art rather than halftone
#:     PUB_MID     55%  45 points below INK
#:     PUB_GRAY    30%  25 points below MID
#:     PUB_FAINT   20%  the floor of the permitted range
PUB_INK = "#000000"       # the figure's subject
PUB_MID = "#737373"       # its counterpart
PUB_GRAY = "#b3b3b3"      # de-emphasised series
PUB_FAINT = "#cccccc"     # background series, at the 20% floor
#: kept so older calls resolve, and MAPPED INTO THE GRAY RAMP rather than left
#: as hues -- a producer that has not been migrated goes gray instead of
#: quietly staying red while the rest of the corpus is not.
PUB_RED = PUB_INK
PUB_BLUE = PUB_MID


def pub_font():
    """One sans-serif, resolved once, with a fallback that actually exists.

    Naming a font matplotlib cannot find is NOT an error: it substitutes DejaVu
    Sans and warns into a stream nobody reads, so the figure ships in a face
    nobody chose and the declaration in the code still reads as true.

    **ARIAL AHEAD OF HELVETICA SINCE 21 Sep 2026** (RH). Helvetica.ttc on this
    machine carries 2,100 glyphs and HAS NO ARROWS -- neither U+2190 nor
    U+2192 -- while Arial.ttf carries 2,830 and has both. Arrows are wanted on
    several plates, Arial is metrically compatible with Helvetica, and at
    figure sizes the two differ only in the terminal cuts on a few letters.

    **THE SECOND SILENT SUBSTITUTION IS THE GLYPH, NOT THE FAMILY.** The
    warning above is about a font that is not found. A font that IS found and
    lacks a character you use fails differently and worse: matplotlib renders
    that one character from another face, the figure looks almost right, and a
    per-Text font audit still reports a single clean family name because the
    fallback happens inside the Text. `missing_glyphs` is the check for it.
    """
    from matplotlib import font_manager
    have = {f.name for f in font_manager.fontManager.ttflist}
    for fam in ("Arial", "Helvetica", "Helvetica Neue", "DejaVu Sans"):
        if fam in have:
            return fam
    return "sans-serif"


def missing_glyphs(text, family=None):
    """Characters of `text` the publication font cannot draw. -> sorted list

    Reads the font's own cmap rather than looking at a render, because a
    render of a missing glyph looks like a slightly different letter and a
    font audit over Text objects cannot see inside one. Whitespace is ignored.

        >>> missing_glyphs("a -> b")     # Arial
        []
    """
    import os
    from matplotlib import font_manager as fm
    fam = family or pub_font()
    try:
        path = fm.findfont(fm.FontProperties(family=fam),
                           fallback_to_default=False)
    except Exception:
        return sorted({c for c in text if not c.isspace()})
    try:
        from fontTools.ttLib import TTFont, TTCollection
        f = (TTCollection(path).fonts[0]
             if os.path.splitext(path)[1].lower() in (".ttc", ".otc")
             else TTFont(path, fontNumber=0))
        cm = set()
        for t in f["cmap"].tables:
            cm |= set(t.cmap.keys())
    except Exception:
        #: **NO SILENT PASS.** If the cmap cannot be read the honest answer is
        #: "unknown", and returning [] would read as "all present".
        raise
    return sorted({c for c in text
                   if not c.isspace() and ord(c) not in cm})


def save(plot, out_path, dpi=300, height=None):
    """Write the PNG and a PDF beside it. -> [paths]

    **PDF, NOT SVG.** matplotlib embeds fonts in PDF and `pdftops -eps`
    converts it losslessly, which is what CI's art guidelines take; SVG goes
    through a rasterizer here and its text handling is less reliable. And a
    vector is what lets one file serve two rules: the submission page asks for
    300 ppi at final size, the art guidelines call 800 dpi the optimum for
    combination line art and grayscale, and a TIFF can be rasterized from the
    PDF at either.

    **FONTS AS TRUETYPE (`pdf.fonttype = 42`).** The default, Type 3, is a
    PostScript subset that does not survive EPS conversion intact and cannot
    be edited by the press. 42 embeds the TrueType outlines.
    """
    import matplotlib
    matplotlib.rcParams["pdf.fonttype"] = 42
    matplotlib.rcParams["ps.fonttype"] = 42
    out = []
    base = out_path[:-4] if out_path.lower().endswith(".png") else out_path
    for ext in (".png", ".pdf"):
        path = base + ext
        if hasattr(plot, "savefig"):          # a matplotlib Figure
            plot.savefig(path, dpi=dpi)
        else:                                 # a plotnine ggplot
            plot.save(path, dpi=dpi, verbose=False)
        out.append(path)
    return out


def pub_theme(height=None, grid="y"):
    """`theme_minimal()` plus the journal's rules. -> a plotnine theme

    The enclosed box is required: "axis lines at the top, bottom, right, and
    left sides of the data, forming a completely enclosed box". `grid` is "y",
    "none" or "both"; gridlines are not forbidden and a faint y grid is what
    makes a level readable without a leader.
    """
    from plotnine import (theme, theme_minimal, element_text, element_rect,
                          element_line, element_blank)
    fnt = pub_font()
    major_y = (element_line(color="#e9ecef", size=PUB_RULE_PT)
               if grid in ("y", "both") else element_blank())
    major_x = (element_line(color="#e9ecef", size=PUB_RULE_PT)
               if grid == "both" else element_blank())
    return (theme_minimal()
            + theme(figure_size=(PUB_SIZE[0], float(height or PUB_SIZE[1])),
                    #: set on `text`, which every other text element inherits
                    #: from -- one family and one size, everywhere
                    text=element_text(family=fnt, size=PUB_FONT_PT),
                    axis_title=element_text(family=fnt, size=PUB_FONT_PT),
                    axis_text=element_text(family=fnt, size=PUB_FONT_PT),
                    panel_border=element_rect(color="black",
                                              size=PUB_RULE_PT, fill=None),
                    axis_ticks=element_line(color="black", size=PUB_RULE_PT),
                    panel_grid_minor=element_blank(),
                    #: **THE STRAY MIDPOINT TICK.** With breaks at 0 and 1 the
                    #: scale still emits a MINOR tick at 0.5, which renders as
                    #: an unlabelled mark between "Base models" and "Aligned
                    #: models" and reads as a third, nameless rung.
                    #: `panel_grid_minor` hides the GRIDLINE, not the tick.
                    axis_ticks_minor_x=element_blank(),
                    axis_ticks_minor_y=element_blank(),
                    panel_grid_major_x=major_x,
                    panel_grid_major_y=major_y))
