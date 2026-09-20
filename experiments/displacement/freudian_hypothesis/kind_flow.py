"""Three columns: base kind -> aligned kind -> what happened to the affect.

    python -u kind_flow.py                       -> results/kind_flow.{dot,pdf,png}
    python -u kind_flow.py --high-lift           only frames whose base words LIFT
    python -u kind_flow.py --lang zh
    python -u kind_flow.py --also DIR            second copy of the renders

## WHY GRAPHVIZ AND NOT AN ALLUVIAL

paper-claude specified an alluvial: three columns, ribbons shaded by affect fate,
width the frame count. RH asked whether a dot could carry the same data, and it
can carry MORE, because this repo has already measured the alluvial's two
encodings against the plate. `existence/channel_graph.py`, on the same page
geometry:

    NO FILL. CI's halftone rule wants 20-80% ink with levels >=20 points apart;
    the charge ramp ran 33% down to 7% with neighbours one or two points apart,
    so most of it sat under the floor and adjacent layers merged after screening.

    EDGES UNIFORM. Width previously carried `spec` over 0.55-1.28pt, a range no
    reader resolves on the page, and two line-weight encodings in one figure make
    a heavy node with heavy arrows read as "big" and nothing else.

A ribbon IS fill and its width IS the quantity. Both encodings are the ones that
folder abandoned for cause. And a ribbon cannot be labelled: a band is a curved
region, so `kill -> scream` either rides the curve or sits at an end, and at 4.8
inches with twenty ribbons there is nowhere to put it. The exemplar labels were
paper-claude's own first requirement.

**WHAT THE ALLUVIAL WOULD DO BETTER, STATED RATHER THAN DISMISSED:** it makes a
reader follow one flow left to right, and a graph asks them to trace arrows. For
"where the deed goes, then what happens to the feeling" that is a real loss.

## THE THREE-WAY JOINT LIVES ON THE EDGE LABEL, NOT IN COLUMN THREE

Each frame is (base kind, aligned kind, affect fate). An edge from column 2 to
column 3 would aggregate over base kinds and lose which deed fed which fate --
the thing the figure is for. So the affect split is printed ON the base->aligned
edge ("kept 21 / gone 3") and column three carries the marginal. Nothing is
averaged away; the joint is where a reader is already looking.

## WHAT IS EXCLUDED, AND `MIXED` IS NOT

Frames whose `channel` or `affect` was WITHHELD -- the two label orders
disagreed -- are dropped and counted in the caption. `MIXED` is KEPT as a node:
it is 769 of 1,695 agreed English frames, and paper-claude's spec drops it.
Dropping it would discard two-thirds of the corpus and draw the legible minority
as though it were the finding. It is drawn faint and the caption says what it is.
"""
import argparse, collections, os, statistics, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
for p in (ROOT, HERE, os.path.join(HERE, "tasks")):
    if p not in sys.path:
        sys.path.insert(0, p)

#: the coder's values, in a reader's words. CI's reader knows "voice"; nobody
#: outside this repo knows VOCAL_ACT.
PLAIN = {"PHYSICAL_ACT": "physical act", "VOCAL_ACT": "voice",
         "MENTAL_STATE": "mental state", "PROCEDURE": "procedure",
         "DESCRIPTION": "description", "THING": "thing",
         "FUNCTION": "function word", "MIXED": "mixed"}
FATE = {"KEPT": "feeling kept", "RECOLORED": "feeling changed",
        "GONE": "feeling gone", "INTRODUCED": "feeling arrives",
        "NONE": "no feeling either side"}
#: solid / dashed / dotted, not three grays: a SECOND CHANNEL, which
#: `malignment.figure` requires of anything a reader must tell apart, and which
#: survives the halftone screen that merged the grays.
STYLE = {"GONE": "solid", "KEPT": "dashed", "RECOLORED": "dashed",
         "NONE": "dotted", "INTRODUCED": "dotted"}


def load(path, lang="en", high_lift=False, min_edge=6):
    """-> (edges, fates, n_used, n_dropped, cut)"""
    import json
    import re
    from malignment import charge
    cjk = re.compile(r"[一-鿿]")
    rows = [json.loads(l) for l in open(path, encoding="utf-8")]
    rows = [r for r in rows if bool(cjk.search(r["frame"])) == (lang == "zh")]
    cut = None
    if high_lift:
        #: LIFT, not the scene level: `charge.lift`'s own docstring says "THIS
        #: IS THE DOSE ANY DISPLACEMENT WORK WANTS, NOT dose()". Top tertile of
        #: the base words' scene rating minus the frame's own.
        lift = {}
        for r in rows:
            sc = charge.scene(r["frame"]) or {}
            ws = [w.strip() for w in (r.get("_base") or "").split(",")]
            v = [sc[w] for w in ws if w in sc]
            d, l = charge.dose(r["frame"]), charge.lift(r["frame"])
            if v and isinstance(d, (int, float)) and isinstance(l, (int, float)):
                lift[r["frame"]] = sum(v) / len(v) - (d - l)
        vals = sorted(lift.values())
        cut = vals[int(len(vals) * 2 / 3)] if vals else 0
        rows = [r for r in rows if lift.get(r["frame"], -9e9) > cut]
    edges, fates, used, dropped = {}, collections.Counter(), 0, 0
    for r in rows:
        ch, af = r["orient"].get("channel"), r["orient"].get("affect")
        if not ch or " -> " not in ch or af is None:
            dropped += 1
            continue
        b, a = ch.split(" -> ", 1)
        e = edges.setdefault((b, a), {"n": 0, "fate": collections.Counter(),
                                      "ex": []})
        e["n"] += 1
        e["fate"][af] += 1
        bw = [w.strip() for w in (r.get("_base") or "").split(",") if w.strip()]
        aw = [w.strip() for w in (r.get("_aligned") or "").split(",") if w.strip()]
        if bw and aw:
            #: **THE EXEMPLAR IS THE MOST CHARGED BASE WORD AGAINST THE LEAST
            #: CHARGED ALIGNED ONE, NOT THE FIRST OF EACH.** `bw[0]` gave
            #: `kissed -> whispered` on BOTH the physical-act-to-mixed and the
            #: physical-act-to-voice edge: list order is agreement rank, and the
            #: head of two different lists can be the same ordinary word. An
            #: exemplar that does not exemplify is worse than none, because a
            #: reader takes it as the edge's content.
            sc = charge.scene(r["frame"]) or {}
            bx = max(bw, key=lambda w: sc.get(w, -1))
            ax = min(aw, key=lambda w: sc.get(w, 9))
            e["ex"].append(((bx, ax), sc.get(bx, 0) - sc.get(ax, 0)))
        fates[af] += 1
        used += 1
    edges = {k: v for k, v in edges.items() if v["n"] >= min_edge}
    return edges, fates, used, dropped, cut


def emit(edges, fates, out, title_note, pub=True):
    from malignment import figure as _fig
    fam, pt = _fig.pub_font(), _fig.PUB_FONT_PT
    bases = sorted({b for b, _a in edges})
    aligns = sorted({a for _b, a in edges})
    #: **`size` AND `ratio=compress` PIN THE PAGE WIDTH.** The first render came
    #: out 6.3 inches against CI's measured text block of 4.8, and a figure
    #: reduced to the column afterwards turns 9 pt into about 6.9 -- which is
    #: the exact failure `malignment.figure` exists to prevent ("rendering at
    #: FINAL size is the point"). `size` is a maximum, so a sparse graph stays
    #: smaller rather than being stretched.
    L = ['digraph kindflow {', '  rankdir=LR; splines=true; overlap=false;',
         '  size="%g,%g!"; ratio=compress;' % (_fig.PUB_SIZE[0], _fig.PUB_SIZE[0] * 1.15),
         '  bgcolor="white"; nodesep=0.14; ranksep=0.95;',
         '  node [shape=box style="rounded" fontname="%s" fontsize=%g '
         'color="black" fontcolor="black" margin="0.06,0.035" penwidth=0.6];'
         % (fam, pt),
         '  edge [fontname="%s" fontsize=%g color="#4d4d4d" penwidth=0.75 '
         'arrowsize=0.5];' % (fam, pt * 0.8)]
    bn = collections.Counter()
    an = collections.Counter()
    for (b, a), e in edges.items():
        bn[b] += e["n"]
        an[a] += e["n"]

    def node(nid, label, n, faint=False):
        return ('  "%s" [label="%s\\n%d"%s];'
                % (nid, label, n, ' penwidth=0.35 color="#8c8c8c" '
                                  'fontcolor="#595959"' if faint else ""))
    L.append("  { rank=same;")
    for b in sorted(bases, key=lambda x: -bn[x]):
        L.append("  " + node("B_" + b, PLAIN.get(b, b), bn[b], b == "MIXED"))
    L.append("  }")
    L.append("  { rank=same;")
    for a in sorted(aligns, key=lambda x: -an[x]):
        L.append("  " + node("A_" + a, PLAIN.get(a, a), an[a], a == "MIXED"))
    L.append("  }")
    L.append("  { rank=same;")
    for f, n in fates.most_common():
        L.append("  " + node("F_" + f, FATE.get(f, f), n, f == "NONE"))
    L.append("  }")
    for (b, a), e in sorted(edges.items(), key=lambda kv: -kv[1]["n"]):
        top = e["fate"].most_common(1)[0][0]
        #: the exemplar with the LARGEST charge drop on this edge, which is the
        #: one that shows what the edge is; ties fall to the alphabetical pair
        #: so the same run always names the same words
        ex = sorted(e["ex"], key=lambda x: (-x[1], x[0]))
        #: the three-way joint, printed where the reader is already looking
        split = " / ".join("%s %d" % (k.lower(), v)
                           for k, v in e["fate"].most_common(2))
        lab = "%d\\n%s" % (e["n"], split)
        if ex and e["n"] >= 10:
            #: **THE LITERAL CHARACTER, NOT AN ESCAPE.** `\\u2192` in the dot
            #: source is not interpreted by graphviz and printed as the four
            #: characters u2192 in the first render.
            lab += "\\n%s → %s" % ex[0][0]
        L.append('  "B_%s" -> "A_%s" [label="%s" style=%s];'
                 % (b, a, lab, STYLE.get(top, "solid")))
    #: column two to column three carries the MARGINAL only, and is drawn faint
    #: so it reads as a total rather than as a measured flow -- the joint is on
    #: the edge labels above, not here
    a_fate = collections.defaultdict(collections.Counter)
    for (_b, a), e in edges.items():
        for f, v in e["fate"].items():
            a_fate[a][f] += v
    for a, c in a_fate.items():
        for f, v in c.items():
            if v >= 8:
                L.append('  "A_%s" -> "F_%s" [label="%d" color="#b3b3b3" '
                         'penwidth=0.5 arrowsize=0.4 style=%s];'
                         % (a, f, v, STYLE.get(f, "solid")))
    L.append('  labelloc="b"; labeljust="l";')
    L.append('  label=<<font point-size="%g">%s</font>>;' % (pt * 0.85, title_note))
    L.append("}")
    open(out, "w", encoding="utf-8").write("\n".join(L) + "\n")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rows", default=None)
    ap.add_argument("--lang", choices=("en", "zh"), default="en")
    ap.add_argument("--high-lift", action="store_true")
    ap.add_argument("--min-edge", type=int, default=6)
    ap.add_argument("--out", default=None)
    ap.add_argument("--also", default=None, help="directory for a second copy")
    a = ap.parse_args(argv)
    rows = a.rows or os.path.join(HERE, "results", "fates_corpus_%s.jsonl" % a.lang)
    edges, fates, used, dropped, cut = load(rows, a.lang, a.high_lift, a.min_edge)
    if not edges:
        raise SystemExit("no edges clear --min-edge %d" % a.min_edge)
    tag = "%s%s" % (a.lang, "_highlift" if a.high_lift else "")
    out = a.out or os.path.join(HERE, "results", "kind_flow_%s.dot" % tag)
    note = ("%d frames; %d dropped where the two label orders disagreed; "
            "edges with fewer than %d frames omitted%s"
            % (used, dropped, a.min_edge,
               "; top lift tertile only (cut %+.2f)" % cut if cut is not None else ""))
    emit(edges, fates, out, note)
    print("%s: %d frames, %d edges, %d dropped%s"
          % (tag, used, len(edges), dropped,
             ", lift cut %+.2f" % cut if cut is not None else ""))
    print("  " + note)
    outs = [out]
    for fmt in ("pdf", "png"):
        p = out.replace(".dot", "." + fmt)
        cmd = ["dot", "-T" + fmt] + (["-Gdpi=300"] if fmt == "png" else []) + [out, "-o", p]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode:
            print("  dot -T%s FAILED: %s" % (fmt, r.stderr.strip()[:200]))
        else:
            outs.append(p)
            print("  wrote %s" % p)
    if a.also:
        import shutil
        os.makedirs(a.also, exist_ok=True)
        for p in outs:
            shutil.copy(p, a.also)
        print("  copied %d files to %s" % (len(outs), a.also))
    return 0


if __name__ == "__main__":
    sys.exit(main())
