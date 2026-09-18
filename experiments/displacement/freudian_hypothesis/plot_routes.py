"""The road not taken: where the mass leaves from, and where it refuses to go.

    python -u plot_routes.py --pub          -> figures/routes_pub.png + .pdf

## WHAT THE FIGURE SHOWS, AND THE ONE IT DELIBERATELY DOES NOT

Each word sits at its own (act, affect): `max(k_bodily_harm,
k_transgressiveness)` across, `k_charge` up, both from one rating call. Words are
drawn at the size of the mass they lose or gain across the 1,818 charged cells,
and the two directions get different ink.

The argument is in a REGION THAT IS EMPTY. Top right is high act and high
affect -- `kill`, `murder`, `stab`, `strangle` -- and it is where the departing
mass lives. It is also where a SUBSTITUTE would have to sit: a word that does
what the barred word did, with the same force. Candidates are available there in
every cell. Almost no arriving mass goes there. The upper LEFT, high affect and
no act, is where `scream`, `cry`, `suffer` sit, and that arm is taken three times
as readily.

**NO CENTROID ARROW, THOUGH ONE WAS DRAWN FIRST AND IT OVERCLAIMED.** The
mass-weighted centre of the departing mass is act 6.34 / charge 4.66 and of the
arriving mass act 1.46 / charge 2.16, so an arrow between them falls on BOTH axes
(-4.88, -2.50) and would illustrate "the affect is conserved" by drawing the
affect dropping by half. The conservation result in `departing_arriving.py` is
over all cells; the preference result in `disjunction.py` is a ratio between two
routes. Neither is a claim about this centroid, and a figure that implies it
would be the strongest-looking and least supported thing in the folder.

## OVERPLOTTING

Both scales are integers 1-7, so 49 positions would hold every word. Jitter is
deterministic (hashed on the word) so the figure is stable across runs and a
reader comparing two versions is not misled by points that moved on their own.
"""
import argparse, collections, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
FIGS = os.path.join(HERE, "figures")
MIN_ACT = 4.0


def jitter(word, span=0.30):
    """Deterministic offset in [-span, span], stable across runs."""
    h = hashlib.md5(word.encode()).digest()
    return ((h[0] / 255.0) - 0.5) * 2 * span, ((h[1] / 255.0) - 0.5) * 2 * span


def load(min_cand=80):
    """-> grid rows: one per (act, affect) cell with enrichment and a landmark.

    `min_cand` suppresses cells with too few candidates for a ratio to mean
    anything; 80 over 1,818 cells is about one candidate per 23 cells, and
    without it the corners carry ratios built on a handful of words.
    """
    import disjunction as D
    ref = collections.defaultdict(lambda: [0.0, 0.0, 0.0])
    for lin, pr, _w, d, a, c, _f in D.stream():
        if d < 0:
            r = ref[(lin, pr)]
            r[0] += -d
            r[1] += -d * a
            r[2] += -d * c
    live = {k for k, (m, wa, _wc) in ref.items() if m > 0 and wa / m >= MIN_ACT}
    arr, dep, avail = collections.Counter(), collections.Counter(), collections.Counter()
    #: **THE LANDMARK IS THE HEAVIEST WORD IN EITHER DIRECTION, not the heaviest
    #: ARRIVING one.** A first version labelled each tile with its top arriving
    #: word. At act 7 / affect 6 that is `kill` -- with an arriving mass of 1
    #: against a departing mass of 67. The tile got named for the word whose
    #: whole significance there is that it LEAVES, and the label read as a claim
    #: about arrivals. The word names the POSITION; the two percentages say what
    #: happens at it.
    top = collections.defaultdict(collections.Counter)
    for lin, pr, w, d, a, c, isfn in D.stream():
        #: function words have no act or affect to speak of and would put 10% of
        #: the arriving mass into one corner tile as though it meant something
        if (lin, pr) not in live or isfn:
            continue
        k = (int(a), int(c))
        avail[k] += 1
        top[k][w] += abs(d)
        if d > 0:
            arr[k] += d
        else:
            dep[k] += -d
    A, V, Dm = sum(arr.values()), sum(avail.values()), sum(dep.values())
    rows = []
    for k, n in avail.items():
        if n < min_cand:
            continue
        e = (arr[k] / A) / (n / V) if arr[k] else 0.0
        rows.append({"act": k[0], "affect": k[1],
                     "enrich": e, "log2": math.log2(e) if e > 0 else -4.0,
                     #: log of the DESTINATION share. Raw share is useless as a
                     #: ramp -- one tile holds 47.7% and the rest share the
                     #: remainder, so a linear scale paints 27 tiles the same.
                     "log_in": math.log10(100 * arr[k] / A) if arr[k] else -2.0,
                     "log_out": math.log10(100 * dep[k] / Dm) if dep[k] else -2.0,
                     "depart_share": 100 * dep[k] / Dm,
                     "arrive_share": 100 * arr[k] / A,
                     "word": top[k].most_common(1)[0][0] if top[k] else "",
                     #: OUT then IN, both as a share of their own side's
                     #: total. The ratio is the shading; these two are the
                     #: fact, and they need no explanation of a baseline.
                     #: WORDS, NOT AN ARROW GLYPH. U+2192 is not in the
                     #: publication font and rendered as a tofu box.
                     "label": "%s\nout %.1f%%\nin %.1f%%"
                              % (top[k].most_common(1)[0][0] if top[k] else "",
                                 100 * dep[k] / Dm, 100 * arr[k] / A)})
    return rows, len(live)


def draw(rows, out, shade_by="enrich", top=None, pub=True):
    """A 7x7 field of the measured quantity, with a landmark word per tile.

    **A SCATTER OF THE WORDS WAS DRAWN FIRST AND WITHDRAWN.** It put every word
    at its (act, affect) and shaded the high-act corner, inviting the reader to
    see that corner as EMPTY of arrivals. It is not empty -- under-representation
    is a ratio, and 0.09x of a large availability is still ink on the page. A
    figure whose argument is a blank region is making a claim the measurement
    does not support. This plots the ratio itself.
    """
    import matplotlib
    matplotlib.use("Agg")
    import pandas as pd
    from plotnine import (ggplot, aes, geom_tile, geom_text, labs, theme,
                          scale_fill_identity, scale_color_identity,
                          scale_x_continuous, scale_y_continuous)
    from malignment.figure import PUB_SIZE, pub_theme, save
    f = pd.DataFrame(rows)
    #: **CLAMPED AND STATED.** log2 enrichment runs -5.6 to +2.1; letting the
    #: ramp span that puts every tile but two in the middle third of the ink.
    #: **THREE THINGS THIS COULD SHADE, AND THEY ARE DIFFERENT QUESTIONS.**
    #:   enrich  in / availability -- where mass is STEERED, net of what was on
    #:           offer. `scream` wins. Answers "does alignment prefer this?"
    #:   in      share of arriving mass -- where mass actually ENDS UP. `make`
    #:           wins with 47.7%. Answers "where does it go?"
    #:   out     share of departing mass -- where it comes FROM. `kill` wins.
    #: The paragraph's claim is about destination, so `in` is the literal
    #: answer and `enrich` the interesting one; neither is a substitute for the
    #: other and the filename says which was drawn.
    col = {"enrich": "log2", "in": "log_in", "out": "log_out"}[shade_by]
    lim = (-2.0, 2.0) if shade_by == "enrich" else (-2.0, 1.7)
    f["shade"] = f[col].clip(*lim)
    #: **THE FILL IS COMPUTED HERE, NOT LEFT TO A SCALE.** A first version set
    #: the text colour from a threshold on `shade` and let plotnine interpolate
    #: the fill; the two disagreed and light tiles came out with white text on
    #: them. Interpolating once, in Python, makes the ink a function of the
    #: exact grey that is drawn rather than of a guess about it.
    #: **MORE INK = MORE OF WHATEVER IS SHADED.** RH, reading the first
    #: version: "dark reads as more active". It did the opposite -- `make`, the
    #: destination of 47.7% of the arriving mass, came out nearly white while
    #: `killed`, where almost nothing arrives, was solid black. Ink now runs
    #: WITH the quantity, so a dark tile is a busy one on every mode.
    hi, lo = 0.14, 0.93          # CI halftone band, 86% ink down to 7%
    def grey(v):
        t = (v - lim[0]) / (lim[1] - lim[0])
        return lo + t * (hi - lo)
    f["fill"] = ["#%02x%02x%02x" % ((int(round(grey(v) * 255)),) * 3)
                 for v in f["shade"]]
    f["ink"] = ["#ffffff" if grey(v) < 0.55 else "#000000" for v in f["shade"]]
    p = (ggplot(f, aes("act", "affect"))
         + geom_tile(aes(fill="fill"), color="#ffffff", size=0.8)
         + geom_text(aes(label="label", color="ink"), size=4.8, lineheight=1.05)
         + scale_x_continuous(breaks=range(1, 8), limits=(0.4, 7.6),
                              expand=(0, 0))
         + scale_y_continuous(breaks=range(1, 8), limits=(0.4, 7.6),
                              expand=(0, 0))
         + labs(x="Act  (bodily harm or transgression, rated 1-7)",
                y="Affect  (charge, rated 1-7)")
         + pub_theme(height=4.4, grid=False)
         + theme(legend_position="none"))
    p = p + scale_fill_identity() + scale_color_identity()
    os.makedirs(FIGS, exist_ok=True)
    return save(p, out, height=4.4)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pub", action="store_true", default=True)
    ap.add_argument("--top", type=int, default=22)
    ap.add_argument("--shade", default="enrich",
                    choices=("enrich", "in", "out"),
                    help="what the grey ramp encodes; the filename records it")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    rows, ncell = load()
    print("%d populated tiles over %s charged cells"
          % (len(rows), format(ncell, ",")))
    for r in sorted(rows, key=lambda r: -r["enrich"])[:4]:
        print("   act %d affect %d  %.2fx  %s" % (r["act"], r["affect"],
                                                  r["enrich"], r["word"]))
    for r in sorted(rows, key=lambda r: r["enrich"])[:4]:
        print("   act %d affect %d  %.2fx  %s" % (r["act"], r["affect"],
                                                  r["enrich"], r["word"]))
    out = a.out or os.path.join(
        FIGS, "routes_%s_pub.png" % a.shade)
    print("wrote %s" % ", ".join(draw(rows, out, shade_by=a.shade)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
