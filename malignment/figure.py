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
PUB_GRAY = "#9aa1a7"
PUB_RED = "#c92a2a"
PUB_BLUE = "#1c7ed6"


def pub_font():
    """One sans-serif, resolved once, with a fallback that actually exists.

    Naming a font matplotlib cannot find is NOT an error: it substitutes DejaVu
    Sans and warns into a stream nobody reads, so the figure ships in a face
    nobody chose and the declaration in the code still reads as true.
    """
    from matplotlib import font_manager
    have = {f.name for f in font_manager.fontManager.ttflist}
    for fam in ("Helvetica", "Arial", "Helvetica Neue", "DejaVu Sans"):
        if fam in have:
            return fam
    return "sans-serif"


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
                    panel_grid_major_x=major_x,
                    panel_grid_major_y=major_y))
