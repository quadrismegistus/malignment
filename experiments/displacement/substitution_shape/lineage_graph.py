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
    return E, held, bw_c, aw_c, n, miss, nonword


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


def dot_flow(E, held, bw, aw, n, prompt):
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
        ws = sorted(counts, key=lambda x: (-counts[x], x))
        order[side] = ws
        L.append("  { rank=same;")
        for w in ws:
            L.append('  "%s_%s" [label="%s\\n(%d/%d)"];'
                     % (side, w, show(w), counts[w], n))
        L.append("  }")
    #: the invisible chain that makes the column read top-to-bottom by count
    for side in ("B", "A"):
        for x, y in zip(order[side], order[side][1:]):
            L.append('  "%s_%s" -> "%s_%s" [style=invis];' % (side, x, side, y))
    for (f, t), k in sorted(E.items(), key=lambda kv: -kv[1]):
        #: **HEADLESS WHERE THE WORD DID NOT CHANGE.** The arrow would assert
        #: a movement the equality denies; `kind_flow` makes the same choice
        #: for its same-kind edges.
        L.append('  "B_%s" -> "A_%s" [penwidth=%.2f color="%s"%s label="%d"];'
                 % (f, t, 0.5 + 3.6 * (k - 1) / max(1, mx - 1),
                    "#1a1a1a" if k >= 3 else "#8c8c8c",
                    ' arrowhead=none' if f == t else "", k))
    L.append("}")
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prompt", default=FIG2)
    ap.add_argument("--tag", default=None, help="filename tag")
    ap.add_argument("--keep-nonwords", action="store_true",
                    help="keep blank-template and punctuation completions")
    ap.add_argument("--free", action="store_true",
                    help="one-column force-directed layout instead of the "
                         "two-column flow; held lineages then cannot be edges")
    a = ap.parse_args(argv)

    E, held, bw, aw, n, miss, nonword = build(
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
                        % (tag, "_free" if a.free else "_flow"))
    os.makedirs(os.path.dirname(base), exist_ok=True)
    src = (dot(E, held, bw, aw, n) if a.free
           else dot_flow(E, held, bw, aw, n, a.prompt))
    open(base + ".dot", "w", encoding="utf-8").write(src + "\n")
    for ext in ("png", "pdf"):
        r = subprocess.run([("neato" if a.free else "dot"), "-T" + ext,
                            "-Gdpi=300",
                            base + ".dot", "-o", base + "." + ext],
                           capture_output=True, text=True)
        if r.returncode:
            raise SystemExit("graphviz failed: %s" % r.stderr[:300])
        print("  wrote %s.%s" % (base, ext))
    return 0


if __name__ == "__main__":
    sys.exit(main())
