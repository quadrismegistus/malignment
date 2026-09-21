"""One prompt, fifty lineages, one edge each. -> figures/lineage_graph_*.{png,pdf}

    python -u lineage_graph.py
    python -u lineage_graph.py --prompt "He hated her deeply and wanted to"

**THIS IS THE ANSWER TO "IT IS JUST A CORPUS AVERAGE".** Every other graph in
this folder has the PROMPT as its unit: `run.py` averages the fifty lineages'
probabilities and then picks one faller, so an edge is a property of an
averaged distribution and `substitution_replicated.py` shows the lineages do
not even agree on those pairings (0 of 6,976 drawable pairs survive BH).

Here the unit is the LINEAGE. One prompt is fixed; each of the 50 endpoint
pairs contributes exactly one edge, from its OWN base argmax to its OWN
aligned argmax. Nothing is averaged before the edge is drawn, so an edge of
weight 15 means fifteen separately trained models each made that move.

## WHAT A SELF-LOOP MEANS AND WHY IT IS NOT AN EDGE

A lineage whose top word does not change contributes no movement. Drawing it
as a loop would put it among the arrows and let it be read as a substitution
to itself; it is written into the node label as `(held n)` instead, so the
count is visible and is not in the flow.

## NODE SIZE IS LINEAGE INCIDENCE, NOT DEGREE

A word's type size scales with how many lineages have it as a base argmax or
an aligned argmax -- how much of the roster stands there, before or after.
Sizing by DEGREE would make a word chosen once by fifteen models look smaller
than one chosen once each by three.
"""
import argparse, collections, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, ROOT)

FIG2 = "She was so angry she wanted to"


def is_word(w):
    """Does the token contain a letter? -> bool

    The blank-template completions (`____`, `________`) and bare punctuation
    are real measurements -- they are the genre-collapse signature and they
    belong in `substitution_shape`'s counts -- but they are not words and a
    flow of words should not have them as boxes.

    **A LINEAGE EXCLUDED ON ONE SIDE IS EXCLUDED ON BOTH.** Dropping only the
    offending node would leave its partner's count intact and the two columns
    would stop summing to the same number, which is the one property this
    layout has to keep. The count of dropped lineages is printed and the
    denominator moves with it.
    """
    return any(c.isalpha() for c in w)


def argmaxes(prompt):
    """-> {model: (word, p)} pass 1 only, over every endpoint arm."""
    from malignment import ch, roster
    eps, _ = roster.endpoints()
    models = sorted(set(eps) | set(eps.values()))
    q = ("SELECT model, word, p FROM {db}.twp_words_v4 "
         "WHERE prompt='%s' AND rule_version=4 AND frame='' AND topup=0 "
         "AND model IN (%s)"
         % (prompt.replace("'", "\\'"),
            ", ".join("'%s'" % m.replace("'", "\\'") for m in models)))
    best = {}
    for r in ch.query(q, limit_bytes=None):
        m, w, p = r["model"], r["word"], float(r["p"])
        if m not in best or p > best[m][1]:
            best[m] = (w, p)
    return eps, best


def build(prompt, keep_held=True, words_only=True):
    """-> (edges, held, base_w, aligned_w, n_lineages, n_missing)

    **WITH `keep_held`, A LINEAGE THAT DID NOT MOVE IS AN EDGE.** In the
    two-column layout `kill` on the left and `kill` on the right are DIFFERENT
    NODES -- the word at the base arm and the word at the aligned arm -- so
    `kill -> kill` is an ordinary horizontal edge and not a self-loop. All
    fifty lineages then appear in the flow and the columns sum to 50, which is
    the property a flow diagram has to have and the one-column version could
    not. `kind_flow` draws its same-kind arrows headless for the same reason
    and this follows it.
    """
    eps, best = argmaxes(prompt)
    E, held = collections.Counter(), collections.Counter()
    bw_c, aw_c = collections.Counter(), collections.Counter()
    n = miss = nonword = 0
    for b, a in eps.items():
        if b not in best or a not in best:
            miss += 1
            continue
        bw, aw = best[b][0], best[a][0]
        if words_only and not (is_word(bw) and is_word(aw)):
            nonword += 1
            continue
        n += 1
        bw_c[bw] += 1
        aw_c[aw] += 1
        if bw == aw:
            held[bw] += 1
            if keep_held:
                E[(bw, aw)] += 1
        else:
            E[(bw, aw)] += 1
    return E, held, bw_c, aw_c, n, miss, nonword, len(eps)


def dot(E, held, bw, aw, n):
    from malignment import figure as _fig
    fam, pt = _fig.pub_font(), _fig.PUB_FONT_PT
    inc = collections.Counter()
    for w, k in list(bw.items()) + list(aw.items()):
        inc[w] += k
    hi = max(inc.values())
    mx = max(E.values()) if E else 1
    L = ['digraph lin {', '  splines=true; overlap=prism; overlap_scaling=-4;',
         '  graph [bgcolor="white" sep="+10" K=0.9];',
         '  node [shape=plaintext margin="0.03,0.02"];',
         '  edge [arrowsize=0.5];']
    for w in sorted(inc):
        #: type size runs from the base size to 2.4x it, by how much of the
        #: roster stands on this word at either arm
        size = pt - 1 + 1.4 * pt * (inc[w] / hi)
        #: **A RULE OF UNDERSCORES IS A WORD, NOT A DRAWING ARTEFACT.** `____`
        #: and `________` are real completions -- the blank-template tokens
        #: that are the genre-collapse signature -- and rendered bare they
        #: look like a stray line someone drew. Named explicitly.
        show = ("blank (%d _)" % len(w)) if set(w) == {"_"} else w
        lab = show if not held[w] else "%s\\n(held %d)" % (show, held[w])
        dark = "#000000" if inc[w] >= 0.4 * hi else "#4d4d4d"
        L.append('  "%s" [label="%s" fontname="%s" fontsize=%.1f '
                 'fontcolor="%s"];' % (w, lab, fam, size, dark))
    for (f, t), k in sorted(E.items(), key=lambda kv: -kv[1]):
        L.append('  "%s" -> "%s" [penwidth=%.2f color="%s" '
                 'fontname="%s" fontsize=%.1f fontcolor="#737373"%s];'
                 % (f, t, 0.6 + 4.0 * (k - 1) / max(1, mx - 1),
                    "#1a1a1a" if k >= 3 else "#8c8c8c", fam, pt - 3,
                    ' label="%d"' % k if k >= 2 else ""))
    L.append("}")
    return "\n".join(L)


def dot_flow(E, held, bw, aw, n, prompt, n_roster=None,
             collapse=False):
    """Two columns, base argmax left and aligned argmax right. -> dot source

    The house flow layout (`freudian_hypothesis/kind_flow.py`): `rankdir=LR`,
    one `rank=same` block per column, `size` as a CEILING so the plate shrinks
    to the text block and is never blown up to it.

    **NOTHING IS COLLAPSED.** An earlier version swept the one-lineage flows
    into a counted "other" box to stop thirteen right-hand boxes forcing the
    plate to 2.0 x 5.5 inches. Two reasons it is gone. The point of this plate
    is the real picture at lineage grain, and the singletons ARE the picture --
    the fan is the finding beside the one heavy edge. And the first attempt
    collapsed minor EDGES rather than minor DESTINATIONS, which swept
    `cry -> scream` in with them and made the aligned `scream` box read 28
    where the true aligned argmax marginal is 29. **A column that does not
    show the marginal is not a marginal**, and the fix for a tall plate is a
    tall plate.

    **THE DENOMINATOR IS THE ROSTER, NOT THE DRAWN SET** (RH). Labels read
    `(k/50)` even though 47 lineages are drawn, because 50 is the population
    the reader is being told about and rebasing to 47 would quietly redefine
    it mid-figure. The three excluded lineages are named in the caption file
    instead, where an exclusion belongs.

    **AND A COUNT OF ONE IS NOT PRINTED.** A box reading `(1/50)` and an edge
    reading `1` spend a number to say "this is the smallest thing here", which
    the single thin line already says. Only counts above one are shown, so
    every number on the plate is one a reader would otherwise have to
    estimate.

    **`collapse` STACKS THE ONE-LINEAGE BOXES INTO ONE PER SIDE, NAMED.** Ten
    of the sixteen boxes here hold a single lineage and each costs a row; the
    collapsed version puts their words in one box, one per line. It is not the
    "other (9)" box this file used to have and which was removed: that hid the
    identities behind a count, and the objection to it -- the singletons ARE
    the picture -- does not apply to a box that still shows every word. What
    is lost is which singleton goes with which source, since their edges merge.
    Both versions are written, under different names.

    Vertical order is forced by an invisible chain: `rank=same` fixes the
    column, not the order within it, so without the chain graphviz sorts the
    boxes by whatever the layout finds convenient and the counts read as
    unordered.
    """
    from malignment import figure as _fig
    fam, pt = _fig.pub_font(), _fig.PUB_FONT_PT
    mx = max(E.values())

    def show(w):
        return ("blank (%d _)" % len(w)) if not is_word(w) else w

    singles = {}
    if collapse:
        for side, counts in (("B", bw), ("A", aw)):
            ones = sorted(w for w, k in counts.items() if k == 1)
            #: one box replacing one box is not a collapse, it is a rename
            if len(ones) < 2:
                continue
            singles[side] = ones
        if singles:
            bw, aw = collections.Counter(bw), collections.Counter(aw)
            E2 = collections.Counter()
            for (f, t), v in E.items():
                if "B" in singles and f in singles["B"]:
                    f = "ZZ_ONES"
                if "A" in singles and t in singles["A"]:
                    t = "ZZ_ONES"
                E2[(f, t)] += v
            E = E2
            for side, counts in (("B", bw), ("A", aw)):
                if side not in singles:
                    continue
                for w in singles[side]:
                    del counts[w]
                counts["ZZ_ONES"] = len(singles[side])

    L = ['digraph linflow {', '  rankdir=LR; splines=true; overlap=false;',
         '  size="%g,%g";' % (_fig.PUB_SIZE[0], _fig.PUB_SIZE[0] * 2.6),
         '  bgcolor="white"; nodesep=0.10; ranksep=1.60;',
         '  node [shape=box style="rounded" fontname="%s" fontsize=%g '
         'color="black" fontcolor="black" margin="0.06,0.035" penwidth=0.6];'
         % (fam, pt),
         '  edge [fontname="%s" fontsize=%g color="#4d4d4d" penwidth=0.75 '
         'arrowsize=0.5];' % (fam, pt * 0.8)]
    order = {}
    for side, counts in (("B", bw), ("A", aw)):
        #: **THE STACKED BOX SORTS LAST, NOT BY ITS COUNT** (RH). Its count is
        #: however many singletons happened to exist -- seven here -- so
        #: ranking it with the rest put it third, above `cry (3/50)`, as
        #: though seven lineages had agreed on something. They agreed on
        #: nothing; the box is the residue and belongs at the foot of the
        #: column whatever its size.
        ws = sorted(counts, key=lambda x: (x == "ZZ_ONES", -counts[x], x))
        stack = singles.get(side)
        order[side] = ws
        L.append("  { rank=same;")
        for w in ws:
            k = counts[w]
            if w == "ZZ_ONES":
                #: the words themselves, one per line, and NO count: each is
                #: one lineage and the list is its own tally
                L.append('  "%s_ZZ_ONES" [label="%s"];'
                         % (side, "\\n".join(show(x) for x in stack)))
                continue
            L.append('  "%s_%s" [label="%s%s"];'
                     % (side, w, show(w),
                        "\\n(%d/%d)" % (k, n_roster or n) if k > 1 else ""))
        L.append("  }")
    #: the invisible chain that makes the column read top-to-bottom by count
    for side in ("B", "A"):
        for x, y in zip(order[side], order[side][1:]):
            L.append('  "%s_%s" -> "%s_%s" [style=invis];' % (side, x, side, y))
    #: **AND ONE MORE TO TOP-ALIGN THE COLUMNS** (RH). `dot` centres each rank
    #: against the other, so the five-box left column floated a quarter of the
    #: way down beside the ten-box right one. A heavily weighted invisible edge
    #: between the two FIRST nodes costs the layout length whenever they are
    #: not level, so it pulls the tops together. It is invisible and carries no
    #: flow -- every visible edge is still one lineage's move.
    if order["B"] and order["A"]:
        L.append('  "B_%s" -> "A_%s" [style=invis weight=100];'
                 % (order["B"][0], order["A"][0]))
    for (f, t), k in sorted(E.items(), key=lambda kv: -kv[1]):
        #: **HEADED EVEN WHERE THE WORD IS THE SAME** (RH), reversing an
        #: earlier choice here. The argument for headless was that an arrow
        #: asserts a movement the equality denies. That was wrong about what
        #: the arrow points at: in this layout EVERY edge runs from a base arm
        #: to an aligned arm, and that transition happened for all fifty
        #: lineages whether or not the word changed. A `kill -> kill` lineage
        #: did pass through alignment and came out saying `kill`; the head
        #: marks the arm transition, not a change of word. Dropping the head
        #: also made the two heaviest facts on the plate -- 13 lineages
        #: holding `scream`, 7 holding `kill` -- read as a different KIND of
        #: thing from the 15 that moved, when they are the same measurement.
        #: **THE EDGE LABEL IS A SHARE OF ITS SOURCE** (RH): `(15/28)` reads
        #: "15 of the 28 lineages whose base arm said `kill`". A bare 15 has
        #: to be divided by a box the reader has to look up, and the two
        #: heaviest edges on this plate leave sources of very different size
        #: -- 15 of 28 from `kill` against 13 of 16 from `scream`, which is
        #: the smaller count and the larger share.
        L.append('  "B_%s" -> "A_%s" [penwidth=%.2f color="%s"%s];'
                 % (f, t, 0.5 + 3.6 * (k - 1) / max(1, mx - 1),
                    "#1a1a1a" if k >= 3 else "#8c8c8c",
                    ' label="(%d/%d)"' % (k, bw[f]) if k > 1 else ""))
    L.append("}")
    return "\n".join(L)


def dot_ranked(E, held, bw, aw, n, prompt, n_roster=None):
    """Both columns share one row order, keyed on a word's OVERALL incidence.

    RH. `scream` is 16 in the base column and 29 in the aligned; `kill` is 28
    and 8. Ranked by base count alone `kill` heads the left column and
    `scream` the right, and the eye has to re-find each word in the other
    column. Here a word gets ONE row in both columns, ordered by base plus
    aligned, so `scream` is the top row on both sides and `kill` the second.

    **A WORD EARNS A ROW IF IT CLEARS ONE LINEAGE IN EITHER COLUMN.** `cry` is
    3 in the aligned arm and 1 in the base, so it gets a row; its single base
    lineage falls into the base collapsed box while its aligned box is drawn.
    A row where a column has nothing to show carries an invisible placeholder,
    which holds the slot so the two columns stay level.

    **THE COLLAPSED BOX IS THE LAST ROW IN BOTH COLUMNS, ALWAYS**, whatever it
    holds -- it is the residue rather than a rank, and the same argument that
    keeps it off the count ordering keeps it off this one.

    Rows are held level across the columns by a weighted invisible edge per
    row. `rank=same` fixes which column a box is in and nothing else; without
    the per-row edges the shared ordering would be true of the dot source and
    invisible in the drawing.
    """
    from malignment import figure as _fig
    fam, pt = _fig.pub_font(), _fig.PUB_FONT_PT
    N = n_roster or n

    def show(w):
        return ("blank (%d _)" % len(w)) if not is_word(w) else w

    words = set(bw) | set(aw)
    rows = sorted((w for w in words if max(bw[w], aw[w]) > 1),
                  key=lambda w: (-(bw[w] + aw[w]), w))
    #: **MEMBERSHIP IS PER COLUMN, NOT PER ROW.** A word can earn a row on the
    #: strength of one column and still have a single lineage in the other:
    #: `cry` is 3 aligned and 1 in the base. The first version kept that base
    #: lineage attached to the row -- which meant its edge left an INVISIBLE
    #: placeholder box and appeared in the drawing as a line starting in empty
    #: space. It belongs to that column's collapsed box, as RH specified, and
    #: both the residue list and the edge endpoint have to agree about that.
    resid = {"B": sorted(w for w in bw if bw[w] <= 1),
             "A": sorted(w for w in aw if aw[w] <= 1)}
    E2 = collections.Counter()
    for (f, t), v in E.items():
        E2[(f if bw[f] > 1 else "ZZ_ONES",
            t if aw[t] > 1 else "ZZ_ONES")] += v
    E = E2
    mx = max(E.values())

    L = ['digraph linrank {', '  rankdir=LR; splines=true; overlap=false;',
         '  size="%g,%g";' % (_fig.PUB_SIZE[0], _fig.PUB_SIZE[0] * 2.6),
         '  bgcolor="white"; nodesep=0.10; ranksep=1.60;',
         '  node [shape=box style="rounded" fontname="%s" fontsize=%g '
         'color="black" fontcolor="black" margin="0.06,0.035" penwidth=0.6];'
         % (fam, pt),
         '  edge [fontname="%s" fontsize=%g color="#4d4d4d" penwidth=0.75 '
         'arrowsize=0.5];' % (fam, pt * 0.8)]
    for side, counts in (("B", bw), ("A", aw)):
        L.append("  { rank=same;")
        for w in rows:
            k = counts[w]
            if k > 1:
                #: **SIZE CARRIES THE COUNT HERE BECAUSE POSITION NO LONGER
                #: CAN** (RH). The shared row order is by TOTAL incidence, so
                #: within a column the boxes are not in descending order --
                #: `scream (16/50)` sits above `kill (28/50)` on the base
                #: side. In the unranked layout the column order said how big
                #: a node was; here only the box can.
                #:
                #: Scaled against the ROSTER, not against the column's own
                #: maximum: 29/50 and 28/50 must look alike, and they would
                #: not if each column were normalised to its own top box.
                #: Floored at 6 pt, the house minimum.
                L.append('  "%s_%s" [label="%s\\n(%d/%d)" fontsize=%.1f];'
                         % (side, w, show(w), k, N,
                            max(6.0, pt * (0.80 + 1.30 * k / N))))
            else:
                #: the slot is kept even when this column has nothing in it,
                #: or the rows below would ride up and the alignment would be
                #: a claim the drawing does not keep
                L.append('  "%s_%s" [style=invis label=""];' % (side, w))
        L.append('  "%s_ZZ_ONES" [label="%s"];'
                 % (side, "\\n".join(show(x) for x in resid[side]) or " "))
        L.append("  }")
    seq = rows + ["ZZ_ONES"]
    for side in ("B", "A"):
        for x, y in zip(seq, seq[1:]):
            L.append('  "%s_%s" -> "%s_%s" [style=invis];' % (side, x, side, y))
    for w in seq:
        L.append('  "B_%s" -> "A_%s" [style=invis weight=100];' % (w, w))
    for (f, t), k in sorted(E.items(), key=lambda kv: -kv[1]):
        #: **HEADED EVEN WHERE THE WORD IS THE SAME** (RH), reversing an
        #: earlier choice here. The argument for headless was that an arrow
        #: asserts a movement the equality denies. That was wrong about what
        #: the arrow points at: in this layout EVERY edge runs from a base arm
        #: to an aligned arm, and that transition happened for all fifty
        #: lineages whether or not the word changed. A `kill -> kill` lineage
        #: did pass through alignment and came out saying `kill`; the head
        #: marks the arm transition, not a change of word. Dropping the head
        #: also made the two heaviest facts on the plate -- 13 lineages
        #: holding `scream`, 7 holding `kill` -- read as a different KIND of
        #: thing from the 15 that moved, when they are the same measurement.
        #: **THE EDGE LABEL IS A SHARE OF ITS SOURCE** (RH): `(15/28)` reads
        #: "15 of the 28 lineages whose base arm said `kill`". A bare 15 has
        #: to be divided by a box the reader has to look up, and the two
        #: heaviest edges on this plate leave sources of very different size
        #: -- 15 of 28 from `kill` against 13 of 16 from `scream`, which is
        #: the smaller count and the larger share.
        L.append('  "B_%s" -> "A_%s" [penwidth=%.2f color="%s"%s];'
                 % (f, t, 0.5 + 3.6 * (k - 1) / max(1, mx - 1),
                    "#1a1a1a" if k >= 3 else "#8c8c8c",
                    ' label="(%d/%d)"' % (k, bw[f]) if k > 1 else ""))
    L.append("}")
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prompt", default=FIG2)
    ap.add_argument("--tag", default=None, help="filename tag")
    ap.add_argument("--ranked", action="store_true",
                    help="one shared row per word, ordered by base+aligned "
                         "incidence; implies --collapse-singletons")
    ap.add_argument("--collapse-singletons", action="store_true",
                    help="stack every one-lineage box into one per side, "
                         "listing the words; written under its own name")
    ap.add_argument("--keep-nonwords", action="store_true",
                    help="keep blank-template and punctuation completions")
    ap.add_argument("--free", action="store_true",
                    help="one-column force-directed layout instead of the "
                         "two-column flow; held lineages then cannot be edges")
    a = ap.parse_args(argv)

    E, held, bw, aw, n, miss, nonword, n_roster = build(
        a.prompt, keep_held=not a.free, words_only=not a.keep_nonwords)
    print("PROMPT: %r" % a.prompt)
    print("  %d endpoint lineages drawn%s%s"
          % (n, "; %d missing" % miss if miss else "",
             "; %d dropped for a non-word argmax on one side or the other"
             % nonword if nonword else ""))
    #: **`sum(E)` IS NOT THE CHANGED COUNT ONCE HELD LINEAGES ARE EDGES.**
    #: It became the total, and printed under "CHANGED" it read 47 of 47.
    print("  top word UNCHANGED in %d, CHANGED in %d; %d distinct edges "
          "over %d lineage-edges"
          % (sum(held.values()), n - sum(held.values()), len(E),
             sum(E.values())))
    print("  base argmax:    %s"
          % ", ".join("%s %d" % x for x in bw.most_common(6)))
    print("  aligned argmax: %s"
          % ", ".join("%s %d" % x for x in aw.most_common(6)))
    print("  heaviest edges:")
    for (f, t), k in E.most_common(8):
        print("    %-12s -> %-12s %2d lineages" % (f, t, k))

    tag = a.tag or ("_".join(a.prompt.lower().split()[:5])
                    .replace("'", "").replace(",", ""))
    base = os.path.join(HERE, "figures", "lineage_graph_%s%s"
                        % (tag, "_free" if a.free else
                           "_flow" + ("_ranked" if a.ranked else
                                      "_collapsed" if a.collapse_singletons
                                      else "")))
    os.makedirs(os.path.dirname(base), exist_ok=True)
    src = (dot(E, held, bw, aw, n) if a.free
           else dot_ranked(E, held, bw, aw, n, a.prompt, n_roster) if a.ranked
           else dot_flow(E, held, bw, aw, n, a.prompt, n_roster,
                         a.collapse_singletons))
    open(base + ".dot", "w", encoding="utf-8").write(src + "\n")
    for ext in ("png", "pdf"):
        r = subprocess.run([("neato" if a.free else "dot"), "-T" + ext,
                            "-Gdpi=300",
                            base + ".dot", "-o", base + "." + ext],
                           capture_output=True, text=True)
        if r.returncode:
            raise SystemExit("graphviz failed: %s" % r.stderr[:300])
        print("  wrote %s.%s" % (base, ext))

    cap = [
        "One prompt, one edge per lineage. %r" % a.prompt,
        "",
        "Each of the %d endpoint lineages in `roster.endpoints()` contributes "
        "exactly one edge, from the word its own BASE arm ranks first at the "
        "blank to the word its own ALIGNED arm ranks first. Nothing is "
        "averaged before the edge is drawn, so an edge of weight %d is %d "
        "separately trained models making that move."
        % (n_roster, max(E.values()), max(E.values())),
        "",
        "%d of the %d are drawn. %d are excluded because the first-ranked "
        "word at one arm or the other is not a word -- the blank-template "
        "completions `____` and `________`, which are a real result and are "
        "counted elsewhere in this folder, but are not boxes in a flow of "
        "words. A lineage excluded on one side is excluded on both, so the "
        "two columns still balance against each other -- each sums to %d -- "
        "while the denominator on every label stays %d, the roster. **A "
        "reader who adds the boxes will therefore get %d and not %d**, and "
        "the difference is exactly these %d."
        % (n, n_roster, nonword, n, n_roster, n, n_roster, nonword),
        "",
        "An edge is labelled with its share of its SOURCE box -- (15/28) is "
        "15 of the 28 lineages whose base arm said that word -- so the two "
        "heaviest edges can be compared without looking anything up. Counts "
        "of one are not printed: a box reading (1/%d) and a labelled hairline "
        "spend a number on what the single thin line already "
        "says. Every edge is headed, including the %d that begin and end on "
        "the same word: the arrow marks the passage from the base arm to the "
        "aligned arm, which happened to all %d lineages, and not a change of "
        "word." % (n_roster, sum(held.values()), n),
        "",
        "Pass 1 only (topup=0): the store holds two passes the campaign's "
        "rule forbids merging.",
    ]
    if a.ranked:
        cap[-1:-1] = [
            "",
            "BOTH COLUMNS SHARE ONE ROW ORDER, keyed on a word's total "
            "incidence across the two arms, so a word sits at the same height "
            "on both sides and the eye does not have to re-find it. `scream` "
            "is 16 in the base column and 29 in the aligned, 45 together, so "
            "it is the top row on both; `kill` is 28 and 8, so it is the "
            "second on both -- which is why the left column is NOT in its own "
            "descending order.",
            "",
            "A word earns a row if it clears one lineage in EITHER column. "
            "`cry` is 3 aligned and 1 in the base, so it has a row, its "
            "aligned box is drawn, and its single base lineage sits in the "
            "base collapsed box with the others. Where a column has nothing "
            "to show on a row the slot is held empty rather than closed up.",
            "",
            "BOX SIZE CARRIES THE COUNT IN THIS LAYOUT, because position no "
            "longer can: the shared row order is by total incidence, so "
            "within a column the boxes are not in descending order. Size is "
            "scaled against the roster of %d rather than against each "
            "column's own largest box, so that 29 and 28 look alike -- "
            "normalising per column would have made the base `kill` and the "
            "aligned `scream` the same size as each other and as every other "
            "column maximum, which is the one comparison this layout exists "
            "to make." % (n_roster or n),
        ]
    if a.collapse_singletons or a.ranked:
        cap[-1:-1] = [
            "",
            "THE ONE-LINEAGE BOXES ARE STACKED INTO ONE PER SIDE, listing "
            "every word. Nothing is hidden behind a count and no lineage is "
            "dropped: the words are all there, one per line, and each is one "
            "lineage, so the list is its own tally. What the stacking does "
            "cost is WHICH singleton came from WHICH source -- those edges "
            "merge, so an arrow into the stacked box says only that so many "
            "lineages went somewhere in it. The uncollapsed version, drawn "
            "without a suffix, keeps that routing. The collapsed box is the "
            "LAST row in both columns whatever it holds: it is the residue, "
            "not a rank, and sorting it by its own size would read as "
            "agreement among lineages that agreed on nothing.",
        ]
    cp = base + ".caption.txt"
    open(cp, "w", encoding="utf-8").write("\n".join(cap) + "\n")
    print("  wrote %s" % cp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
