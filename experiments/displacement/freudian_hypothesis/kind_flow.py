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
                                      "ex": [], "exf": []})
        e["n"] += 1
        e["fate"][af] += 1
        bw = [w.strip() for w in (r.get("_base") or "").split(",") if w.strip()]
        aw = [w.strip() for w in (r.get("_aligned") or "").split(",") if w.strip()]
        if bw and aw:
            #: **THE EXEMPLAR IS THE BEST-ATTESTED WORD, NOT THE MOST CHARGED,
            #: AND CHARGE WAS FIGHTING THE NODE LABEL.** Picking `max(charge)`
            #: from the base group put `asked` on the function-word -> function-
            #: word edge (RH). It is not a function word: it is the most charged
            #: word in a group the coder called FUNCTION, and for such a group
            #: the most charged member is by construction its least typical one.
            #: An exemplar has to exemplify the NODE it sits between.
            #:
            #: List order is agreement rank -- how many of the fifty pairs move
            #: that word the same way -- so the head of each list is the word the
            #: roster is surest about, and it is typical of the group rather than
            #: extreme within it. The original objection to `bw[0]` was that it
            #: collided across edges (`kissed -> whispered` on two of them); that
            #: is now handled where it belongs, by using each pair once.
            #:
            #: Charge is kept only as the TIE-BREAK for which frame's pair to
            #: show on an edge, where a bigger drop is the more telling example.
            sc = charge.scene(r["frame"]) or {}
            bx, ax = bw[0], aw[0]
            e["ex"].append(((bx, ax), sc.get(bx, 0) - sc.get(ax, 0)))
            e["exf"].append(((bx, ax), sc.get(bx, 0) - sc.get(ax, 0), af))
        fates[af] += 1
        used += 1
    #: **THE FILTER IS SIGNIFICANCE, NOT SIZE, AND THE FIRST VERSION HAD IT
    #: BACKWARDS.** Filtering on `n >= min_edge` kept `physical act -> mixed` at
    #: 114 frames -- which is 114 against 106 the other way, p=0.64, not a
    #: direction at all -- and dropped `voice -> mental state` at 11 frames,
    #: which is 11 against 1 and survives BH at q=0.019. A figure drawn on size
    #: shows the big symmetric flows and hides the small one-way ones, which is
    #: the opposite of what it is for, and it disagreed with the asymmetry table
    #: in the same results directory.
    #:
    #: Each off-diagonal pair is tested against its own transpose (two-sided
    #: exact binomial at p=0.5), BH-adjusted over the whole family, and only
    #: q < 0.05 edges are drawn. `MIXED` then thins out on its own rather than
    #: by decree: most of its edges are the symmetric ones.
    from math import comb

    def binom_p(k, n):
        if n == 0:
            return 1.0
        lo = min(k, n - k)
        return min(1.0, 2 * sum(comb(n, i) for i in range(lo + 1)) / (2.0 ** n))

    tested, seen = [], set()
    for (b, a), e in edges.items():
        if b == a or (a, b) in seen:
            continue
        seen.add((b, a))
        m = edges.get((a, b), {"n": 0})["n"]
        if e["n"] + m < min_edge:
            continue
        win = (b, a) if e["n"] >= m else (a, b)
        tested.append((win, max(e["n"], m), min(e["n"], m),
                       binom_p(max(e["n"], m), e["n"] + m)))
    order = sorted(range(len(tested)), key=lambda i: tested[i][3])
    M, q, prev = len(tested), {}, 1.0
    for rank, i in enumerate(reversed(order), 1):
        prev = min(prev, tested[i][3] * M / (M - rank + 1))
        q[tested[i][0]] = prev
    #: **SELF-EDGES ARE DRAWN AND ARE NOT TESTED, AND LEAVING THEM OUT WAS THE
    #: REASON THE FIGURE LOOKED EMPTY.** `X -> X` has no transpose, so the
    #: asymmetry test is undefined for it and the first filtered render dropped
    #: every one -- which is 858 of 1,404 English frames, 61%. They are also the
    #: substantively important case: `thing -> thing` (85, `womb -> apartment`)
    #: and `physical act -> physical act` (62) are the act unchanged with only
    #: its object moving, which is displacement proper.
    #:
    #: So: significant off-diagonal edges, PLUS every self-edge, drawn as its
    #: own class and marked untested in the caption. Nothing claims a direction
    #: for them, because none is claimed.
    #:
    #: `min_edge` is not a size filter and never was: a two-sided binomial at
    #: p=0.5 cannot reach 0.05 below n=6 even at unanimity (5-0 gives 0.0625,
    #: 6-0 gives 0.031). Lowering it only admits pairs that cannot come out
    #: significant.
    keep = {k: v for k, v in edges.items()
            if q.get(k, 1.0) < 0.05 or k[0] == k[1]}
    for k in keep:
        keep[k]["q"] = q.get(k)
        keep[k]["self"] = (k[0] == k[1])
        keep[k]["rev"] = edges.get((k[1], k[0]), {"n": 0})["n"]
    return keep, fates, used, dropped, cut, M


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
    #: **COLUMN-THREE COUNTS ARE OVER THE DRAWN EDGES, NOT THE CORPUS.** They
    #: were the full marginal, so a filtered render showed "feeling arrives 5"
    #: as a node with no incoming edge -- a count for flows the figure had just
    #: excluded. A node whose number does not sum from its own arrows is a
    #: number a reader cannot check.
    drawn_f = collections.Counter()
    for _k, e in edges.items():
        drawn_f.update(e["fate"])
    L.append("  { rank=same;")
    for f, n in drawn_f.most_common():
        L.append("  " + node("F_" + f, FATE.get(f, f), n, f == "NONE"))
    L.append("  }")
    #: **THE LABEL IS ONE WORD PAIR.** It carried the count, the two-way affect
    #: split AND the pair -- three lines an edge, over sixteen edges, at 4.8
    #: inches. The counts are on the nodes and the splits are in the asymmetry
    #: table; what only the figure can give is the words. `→` written as
    #: the literal character: graphviz does not interpret python escapes, and
    #: the first render printed the four characters u2192.
    used_pairs = set()
    for (b, a), e in sorted(edges.items(), key=lambda kv: -kv[1]["n"]):
        top = e["fate"].most_common(1)[0][0]
        #: the exemplar with the LARGEST charge drop on this edge; ties fall to
        #: the alphabetical pair so the same run always names the same words
        #: **A PAIR IS USED ONCE.** `killed -> helped` landed on three edges in
        #: one render, which reads as one frame in three places. Different
        #: frames can share an exemplar; take the next-best instead.
        ex = [x for x in sorted(e["ex"], key=lambda x: (-x[1], x[0]))
              if x[0] not in used_pairs]
        lab = ""
        if ex:
            lab = "%s → %s" % ex[0][0]
            used_pairs.add(ex[0][0])
        #: **WIDTH CARRIES FREQUENCY (RH), AND `channel_graph`'s OBJECTION DOES
        #: NOT TRANSFER.** That file dropped width because `spec` spanned
        #: 0.55-1.28 pt, "a range no reader resolves on the page". Here the
        #: counts run 1 to 645, so on a log scale the thinnest and thickest
        #: differ by a factor a reader sees at once. Its second objection --
        #: "two line-weight encodings in one figure" -- also does not apply:
        #: node borders are uniform here, so weight means one thing.
        #:
        #: Floored at the journal's 0.5 pt, below which a rule can drop out of
        #: the plate entirely, and capped so a 645-frame edge does not swamp the
        #: labels.
        import math
        w = 0.5 + 2.6 * (math.log10(e["n"] + 1) / math.log10(646))
        #: a self-edge is arrowless: nothing changed kind, so there is no
        #: direction to assert and it must not read like one. It keeps its true
        #: width -- the frames are real -- but is drawn gray so the eye reads
        #: the tested edges first.
        extra = ' arrowhead=none color="#737373"' if e.get("self") else ""
        extra += " penwidth=%.2f" % w
        L.append('  "B_%s" -> "A_%s" [label="%s" style=%s%s];'
                 % (b, a, lab, STYLE.get(top, "solid"), extra))
    #: column two to column three carries the MARGINAL only, and is drawn faint
    #: so it reads as a total rather than as a measured flow -- the joint is on
    #: the edge labels above, not here
    #: **COLUMN 2 -> 3 CARRIES A WORD PAIR TOO** (RH). Without one the third
    #: column is four abstractions a reader has to take on trust: the figure
    #: says "feeling kept" and never shows a frame where a feeling was kept.
    #: Each (aligned kind, fate) edge names the pair with the largest charge
    #: drop among the frames that took it -- the same rule as column 1 -> 2, so
    #: the two halves of the figure are exemplified the same way.
    a_fate = collections.defaultdict(collections.Counter)
    a_ex = collections.defaultdict(list)
    for (_b, a), e in edges.items():
        for f, v in e["fate"].items():
            a_fate[a][f] += v
        for pair, drop, fate in e.get("exf", []):
            a_ex[(a, fate)].append((pair, drop))
    for a, c in a_fate.items():
        for f, v in c.items():
            if v >= 8:
                ex = [x for x in sorted(a_ex.get((a, f), []),
                                        key=lambda x: (-x[1], x[0]))
                      if x[0] not in used_pairs]
                lab = "%d" % v
                if ex:
                    lab = "%s → %s" % ex[0][0]
                    used_pairs.add(ex[0][0])
                L.append('  "A_%s" -> "F_%s" [label="%s" color="#b3b3b3" '
                         'fontcolor="#737373" penwidth=0.5 arrowsize=0.4 '
                         'style=%s];' % (a, f, lab, STYLE.get(f, "solid")))
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
    edges, fates, used, dropped, cut, ntest = load(rows, a.lang, a.high_lift, a.min_edge)
    if not edges:
        raise SystemExit("no edges clear --min-edge %d" % a.min_edge)
    tag = "%s%s" % (a.lang, "_highlift" if a.high_lift else "")
    out = a.out or os.path.join(HERE, "results", "kind_flow_%s.dot" % tag)
    note = ("%d frames; %d dropped where the two label orders disagreed; "
            "off-diagonal edges one-way at q&lt;0.05 (BH over %d tested pairs); same-kind edges drawn arrowless and NOT tested%s"
            % (used, dropped, ntest,
               "; top lift tertile only (cut %+.2f)" % cut if cut is not None else ""))
    emit(edges, fates, out, note)
    print("%s: %d frames, %d edges, %d dropped%s"
          % (tag, used, len(edges), dropped,
             ", lift cut %+.2f" % cut if cut is not None else ""))
    print("  " + note)
    outs = [out]
    for fmt in ("pdf", "png"):
        p = out.replace(".dot", "." + fmt)
        #: **REMOVE THE TARGET FIRST.** A failed `dot` run left the PREVIOUS
        #: render in place, so the directory held a current .dot and .pdf beside
        #: a stale .png with an older timestamp and nobody would look. An
        #: artifact that silently does not regenerate is the defect this repo
        #: keeps paying for; absent is a state a reader can see.
        if os.path.exists(p):
            os.remove(p)
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
