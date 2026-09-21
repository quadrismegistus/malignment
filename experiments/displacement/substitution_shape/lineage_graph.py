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


def build(prompt):
    """-> (edges, held, base_w, aligned_w, n_lineages, n_missing)"""
    eps, best = argmaxes(prompt)
    E, held = collections.Counter(), collections.Counter()
    bw_c, aw_c = collections.Counter(), collections.Counter()
    n = miss = 0
    for b, a in eps.items():
        if b not in best or a not in best:
            miss += 1
            continue
        n += 1
        bw, aw = best[b][0], best[a][0]
        bw_c[bw] += 1
        aw_c[aw] += 1
        if bw == aw:
            held[bw] += 1
        else:
            E[(bw, aw)] += 1
    return E, held, bw_c, aw_c, n, miss


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


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prompt", default=FIG2)
    ap.add_argument("--tag", default=None, help="filename tag")
    a = ap.parse_args(argv)

    E, held, bw, aw, n, miss = build(a.prompt)
    print("PROMPT: %r" % a.prompt)
    print("  %d endpoint lineages with both arms measured%s"
          % (n, "; %d missing" % miss if miss else ""))
    print("  top word UNCHANGED in %d, CHANGED in %d; %d distinct edges"
          % (sum(held.values()), sum(E.values()), len(E)))
    print("  base argmax:    %s"
          % ", ".join("%s %d" % x for x in bw.most_common(6)))
    print("  aligned argmax: %s"
          % ", ".join("%s %d" % x for x in aw.most_common(6)))
    print("  heaviest edges:")
    for (f, t), k in E.most_common(8):
        print("    %-12s -> %-12s %2d lineages" % (f, t, k))

    tag = a.tag or ("_".join(a.prompt.lower().split()[:5])
                    .replace("'", "").replace(",", ""))
    base = os.path.join(HERE, "figures", "lineage_graph_%s" % tag)
    os.makedirs(os.path.dirname(base), exist_ok=True)
    open(base + ".dot", "w", encoding="utf-8").write(dot(E, held, bw, aw, n) + "\n")
    for ext in ("png", "pdf"):
        r = subprocess.run(["neato", "-T" + ext, "-Gdpi=300",
                            base + ".dot", "-o", base + "." + ext],
                           capture_output=True, text=True)
        if r.returncode:
            raise SystemExit("neato failed: %s" % r.stderr[:300])
        print("  wrote %s.%s" % (base, ext))
    return 0


if __name__ == "__main__":
    sys.exit(main())
