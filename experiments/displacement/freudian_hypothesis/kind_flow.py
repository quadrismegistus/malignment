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
#: **KINDS EXCLUDED FROM THE FIGURE (RH).**
#:
#:   MIXED     the coder's ABSTENTION -- no single kind covers two thirds of
#:             the group's words. `mixed -> voice` says the reader could not
#:             name the base side, not that a kind moved.
#:   FUNCTION  the residue of what task 1 tried to remove. **AND IT IS NOT THE
#:             SAME SET**, which is why it survived: `--content-only` drops
#:             CLOSED-CLASS words by spaCy POS, while the coder's FUNCTION is a
#:             judgement that a group of content-POS words behaves as
#:             connective -- `never, probably`, `started, took`, `never, pay,
#:             know, also, only, get`. All of those passed the POS filter.
#:             190 of 2,244 frames have a FUNCTION side.
#:
#: **WHAT GOES WITH IT, STATED RATHER THAN QUIETLY LOST:** `voice -> function
#: word` at 17 against 2.4 expected (q=0.00022) is one of the strongest cells
#: in the positive-lift figure, and it is the third link of the chain the
#: asymmetry test found -- deed to utterance to connective. It survives in the
#: permutation table and in `fates_corpus_en.md`; only the figure declines it.
#: **`MIXED` IS BACK (RH, on paper-claude's point).** Omitting it removed the
#: proceduralization story: `MIXED -> procedure` is 75 against `physical act ->
#: procedure` 6, and `MIXED -> mental state` 95. The police pattern is rare in
#: KIND terms at corpus scale precisely because institutional base lists are
#: grab-bags the coder cannot give one kind -- that is a finding about the
#: corpus, not a reason to hide the cell. It is drawn faint, and the caption
#: says it is an abstention rather than a kind.
DROP_KINDS = {"FUNCTION"}

#: **THE THIRD COLUMN DROPS `NONE`, AND IT WAS A SINK.** `affect = "NONE"` is the
#: coder saying neither side carries a feeling -- 1,043 of 1,404 agreed English
#: frames, three quarters of the corpus. Drawn as a fate node it takes the widest
#: arrow out of nearly every edge and flattens the four outcomes the column
#: exists to show into a stripe at the bottom of the plate (paper-claude).
#:
#: **IT IS NOT A NULL RESULT AND IT IS NOT HIDDEN.** That most displacement
#: happens on frames with no affect on either side is the Freudian hypothesis's
#: own denominator, and it is the first number in every dose table in
#: `fates_corpus_en.md`. The caption states how many frames it covers. What the
#: column now shows is the conditional: GIVEN a feeling somewhere in the pair,
#: where did it go.
DROP_FATES = {"NONE"}

#: **EXEMPLARS PICKED BY HAND (paper-claude), KEYED BY EDGE.** The automatic rule
#: -- head of each agreement-ranked list, largest charge drop breaking ties --
#: picks a pair that is typical of its GROUP, which is not the same as a pair
#: that shows the EDGE. `mixed -> mental state` is a real cell of 95 frames and
#: its automatic exemplar is whatever word the roster happened to agree on.
#:
#: These were chosen from `fates_corpus_en.jsonl` by a reader who had the sheet,
#: one per edge, each from a frame coded on that edge with both words in that
#: frame's own lists. **ALL THIRTEEN WERE CHECKED BACK AGAINST THE ROWS** before
#: being wired: edge match, frame exists, `_base` contains the left word,
#: `_aligned` the right. A hand-picked label that does not resolve to a frame is
#: a fabricated example, and the check is cheap.
#:
#: Any edge not listed keeps the automatic rule.
EXEMPLARS = {
    ("PHYSICAL_ACT", "VOCAL_ACT"): ("kill", "scream"),
    ("PHYSICAL_ACT", "MENTAL_STATE"): ("die", "suffer"),
    ("PHYSICAL_ACT", "PHYSICAL_ACT"): ("stabbed", "pointed"),
    ("VOCAL_ACT", "MENTAL_STATE"): ("say", "understand"),
    ("VOCAL_ACT", "VOCAL_ACT"): ("ordered", "asked"),
    ("VOCAL_ACT", "PROCEDURE"): ("mention", "file"),
    ("THING", "THING"): ("mouth", "room"),
    ("PROCEDURE", "PROCEDURE"): ("charge", "dismiss"),
    ("MENTAL_STATE", "MENTAL_STATE"): ("obliged", "uneasy"),
    ("DESCRIPTION", "DESCRIPTION"): ("naked", "still"),
    ("MIXED", "PROCEDURE"): ("throw", "terminate"),
    ("MIXED", "MENTAL_STATE"): ("safe", "uneasy"),
    ("MIXED", "PHYSICAL_ACT"): ("beat", "held"),
}

#: **LINE STYLE IS RETIRED (RH).** It carried the edge's MODAL affect fate --
#: solid gone, dashed kept/recoloured, dotted none/introduced -- which was
#: defensible before column three existed and is not now. Three faults at once:
#: it repeats what the third column states exactly; two fates shared each
#: style, so dotted meant NONE *or* INTRODUCED, opposite readings of one mark;
#: and a mode threw away the split, drawing `physical act -> voice` at 16 kept
#: against 3 gone identically to a bare majority. All edges are solid. Width
#: carries frequency and the arrowhead carries tested-vs-self; the affect story
#: is told once, in the column built for it.


def load(path, lang="en", high_lift=False, min_edge=6, test="transpose",
         lift_cut="third"):
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
        #: **THREE CUTS, AND `positive` IS THE ONLY STATED ONE.** A tertile is a
        #: rank -- it moves if the corpus changes and it means nothing outside
        #: this file. `lift > 0` is a boundary with a reading: the base words
        #: are more charged than the sentence they complete, so there is
        #: something for alignment to displace. 587 of 2,225 English frames
        #: have lift <= 0, which is the saturated regime `charge.lift`'s
        #: docstring describes -- a setup already rated 6.4 whose candidates are
        #: no more transgressive than itself.
        vals = sorted(lift.values())
        if lift_cut == "positive":
            cut = 0.0
        elif lift_cut == "half":
            cut = vals[len(vals) // 2] if vals else 0
        else:
            cut = vals[int(len(vals) * 2 / 3)] if vals else 0
        rows = [r for r in rows if lift.get(r["frame"], -9e9) > cut]
    rows_for_test = rows
    edges, fates, used, dropped = {}, collections.Counter(), 0, 0
    for r in rows:
        #: **EACH COLUMN PAIR USES THE FRAMES ITS OWN FIELDS AGREED ON.**
        #: Requiring BOTH a channel and an affect fate cost 291 English frames
        #: that had a perfectly good channel and were dropped because a
        #: DIFFERENT field was contested -- 1,404 drawn where 1,695 were
        #: available for columns one and two.
        #:
        #: And the two absences are not the same thing. `affect = "NONE"` is a
        #: VALUE, the coder saying neither side carries a feeling (1,374
        #: frames). `affect = None` is the field WITHHELD because the two label
        #: orders disagreed. Treating the second like the first is how a
        #: disagreement becomes a finding.
        ch, af = r["orient"].get("channel"), r["orient"].get("affect")
        if not ch or " -> " not in ch:
            dropped += 1
            continue
        b, a = ch.split(" -> ", 1)
        e = edges.setdefault((b, a), {"n": 0, "fate": collections.Counter(),
                                      "ex": [], "exf": []})
        e["n"] += 1
        if af is not None:
            e["fate"][af] += 1
            e["n_af"] = e.get("n_af", 0) + 1
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
            if af is not None:
                e["exf"].append(((bx, ax), sc.get(bx, 0) - sc.get(ax, 0), af))
        if af is not None:
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
    #: **BOTH TESTS ALWAYS, THEN CHOOSE.** They answer different questions and
    #: a cell can pass one and fail the other -- `voice -> mental state` is
    #: 11 against 1 in the transpose (q=0.019, DIRECTED) and 11 against 8.2
    #: expected in the permutation (q=0.46, not over-represented). Computing
    #: only the selected one meant the figure could not say WHICH kind of
    #: evidence an edge had.
    from tasks.fates import kind_permutation
    drawn_rows = [r for r in rows_for_test
                  if r["orient"].get("channel")
                  and " -> " in (r["orient"].get("channel") or "")]
    pq = kind_permutation(drawn_rows, n_shuffle=20000, min_n=min_edge)
    for k, v in edges.items():
        v["q_perm"] = pq[k][2] if k in pq else None
        v["exp"] = pq[k][1] if k in pq else None
        v["over"] = (pq[k][0] > pq[k][1]) if k in pq else None
        v["q_dir"] = q.get(k)
        v["self"] = (k[0] == k[1])
        v["rev"] = edges.get((k[1], k[0]), {"n": 0})["n"]
        v.setdefault("n_af", 0)
        #: what KIND of evidence this edge has, which the arrowhead encodes
        sig_p = v["q_perm"] is not None and v["q_perm"] < 0.05 and v["over"]
        sig_d = v["q_dir"] is not None and v["q_dir"] < 0.05
        v["evidence"] = ("both" if sig_p and sig_d else
                         "over" if sig_p else "directed" if sig_d else None)

    if test == "either":
        keep = {k: v for k, v in edges.items()
                if v["evidence"] and not (set(k) & DROP_KINDS)}
        return keep, fates, used, dropped, cut, len(pq)

    if test == "permutation":
        #: **THE OTHER TEST, AND IT CAN SEE THE SELF-EDGES.** Each cell against
        #: a shuffle that holds BOTH marginals and destroys only the
        #: association, so `X -> X` is testable -- and on the full corpus every
        #: self-edge comes out far over chance (`thing -> thing` 103 against
        #: 7.9 expected). Nothing here is drawn untested.
        #:
        #: It asks a different question, not a better one: "given how often X
        #: is a base kind and Y an aligned kind at all, is X -> Y
        #: over-represented" rather than "of the frames that moved between them,
        #: did more go one way". A cell can pass one and fail the other, and
        #: `physical act -> mental state` does both -- one-way at q=0.02 AND
        #: under-represented at q=0.0024.
        #:
        #: **AND IT CONDITIONS ON A MARGINAL ALIGNMENT PRODUCED.** The aligned
        #: column's distribution is partly the thing under test, so holding it
        #: fixed removes the overall shift and reports only the residual. That
        #: is conservative, and it is why both versions of the figure exist.
        #: **THE TEST MUST SEE THE FIGURE'S POPULATION.** `kind_permutation`
        #: counts every frame with a CHANNEL; the figure draws only frames with
        #: a channel AND an affect fate. So `procedure -> procedure` was tested
        #: on 6+ frames and drawn with n=5 -- a q computed on a population the
        #: node count does not describe, and a reader checking the number
        #: against the figure would find it missing. Pass the drawn rows.
        from tasks.fates import kind_permutation
        drawn_rows = [r for r in rows_for_test
                      if r["orient"].get("channel")
                      and " -> " in (r["orient"].get("channel") or "")]
        pq = kind_permutation(drawn_rows, n_shuffle=20000, min_n=min_edge)
        #: **`MIXED` OUT AND BELOW-CHANCE OUT (RH).** Both were kept on
        #: arguments that were right about the DATA and wrong about the FIGURE.
        #:
        #: `MIXED` is a coder's abstention -- no single kind covers two thirds
        #: of a group's words -- so a `mixed -> voice` edge says the reader
        #: could not name the base side, not that a kind moved. As a node it
        #: dominates the layout while asserting nothing, and its exclusion is a
        #: caption line rather than a lost result: the marginals in
        #: `fates_corpus_en.md` carry it.
        #:
        #: A below-chance cell is a real finding and a bad arrow. An arrow means
        #: "this happens"; an open-headed arrow meaning "this happens LESS than
        #: chance" asks a reader to hold two opposite readings of one mark, and
        #: at 4.8 inches they will read the mark. They stay in the permutation
        #: table, where a sign is a column and not a glyph.
        keep = {k: v for k, v in edges.items()
                if k in pq and pq[k][2] < 0.05
                and pq[k][0] > pq[k][1]
                and not (set(k) & DROP_KINDS)}
        #: a drawn edge may have no fate counter at all if every one of its
        #: frames had the affect withheld; it still belongs in columns 1-2
        for _k, _v in keep.items():
            _v.setdefault("n_af", 0)
        for k in keep:
            keep[k]["q"] = pq[k][2]
            keep[k]["exp"] = pq[k][1]
            keep[k]["over"] = pq[k][0] > pq[k][1]
            keep[k]["self"] = (k[0] == k[1])
            keep[k]["rev"] = edges.get((k[1], k[0]), {"n": 0})["n"]
        return keep, fates, used, dropped, cut, len(pq)
    keep = {k: v for k, v in edges.items()
            if q.get(k, 1.0) < 0.05 or k[0] == k[1]}
    for k in keep:
        keep[k]["q"] = q.get(k)
        keep[k]["self"] = (k[0] == k[1])
        keep[k]["over"] = None
        keep[k]["rev"] = edges.get((k[1], k[0]), {"n": 0})["n"]
    return keep, fates, used, dropped, cut, M


#: **ONE WIDTH SCALE FOR THE WHOLE FIGURE.** Column 1->2 carried frequency in
#: its line weight while column 2->3 was hardcoded at 0.5 pt, so a thick edge
#: meant "many frames" on the left of the figure and nothing on the right. One
#: mark with two meanings is the defect that also killed the line-style
#: encoding. Log-scaled because the counts run 1 to 645; floored at the
#: journal's 0.5 pt, below which a rule can drop out of the plate.
def _width(n, top=646.0):
    #: **SQRT, NOT LOG.** On the log scale `description -> description` at 11
    #: drew at 1.50 pt and `thing -> thing` at 103 at 2.37 -- 9.4 times the
    #: count in 1.6 times the width, which a reader reads as "about the same"
    #: (paper-claude). Sqrt is the standard area-perception scale and gives
    #: 1.00 against 2.55 for the same pair. Floored at the journal's 0.5 pt,
    #: below which a rule can drop out of the plate.
    import math
    return 0.5 + 3.0 * math.sqrt(min(n, top) / top)


def _fate_flows(edges, triples):
    """-> (every fate over the drawn edges, the non-NONE flows, which of those
    get an arrow, how many frames are in the ones that do not).

    Hoisted out of `emit` because the fate NODES need the selection that the
    fate ARROWS make, and they are written to the dot file first -- the node
    was printing a total the arrows below it did not sum to.
    """
    drawn_f, allflow = collections.Counter(), collections.Counter()
    if triples is None:
        return drawn_f, allflow, set(), 0
    for _k, e in edges.items():
        drawn_f.update(e["fate"])
    for (b, a), e in edges.items():
        for f, v in e["fate"].items():
            if f not in DROP_FATES:
                allflow[(b, a, f)] += v
    sig = {k for k in triples if (k[0], k[1]) in edges}
    keepf, tail = set(), 0
    for (b, a), e in edges.items():
        fa = collections.Counter({f: v for f, v in e["fate"].items()
                                  if f not in DROP_FATES})
        top = fa.most_common(1)
        if top:
            keepf.add((b, a, top[0][0]))
        for f, v in fa.items():
            if (b, a, f) in sig:
                keepf.add((b, a, f))
            elif not top or f != top[0][0]:
                tail += v
    return drawn_f, allflow, keepf, tail


def emit(edges, fates, out, title_note, pub=True, triples=None):
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
    #: **THE CAPTION WAS SETTING THE FIGURE'S WIDTH, AND THAT IS WHY THE TYPE
    #: WAS UNDER 4 POINTS.** The graph lays out at 6.0 by 5.2 inches; the
    #: caption was one unwrapped line and graphviz made the drawing 29 INCHES
    #: wide to hold it, so `size!` then scaled the whole plate down by a factor
    #: of six and left the left two thirds empty -- paper-claude measured the
    #: PNG at 1442 by 388 with an empty left third, which is this and nothing
    #: else. `ratio=compress` could not help: the aspect ratio it was compressing
    #: was already the caption's.
    #:
    #: So the caption wraps (graphviz has no auto-wrap; the breaks are inserted)
    #: and `size` loses its `!`. A bare `size` is a CEILING -- shrink to fit,
    #: never stretch -- so the plate is now 4.8 inches wide with 7 pt type, and
    #: a future render that lays out smaller will stay at 9 pt rather than being
    #: blown up to the margin.
    L = ['digraph kindflow {', '  rankdir=LR; splines=true; overlap=false;',
         '  size="%g,%g";' % (_fig.PUB_SIZE[0], _fig.PUB_SIZE[0] * 1.15),
         '  bgcolor="white"; nodesep=0.14; ranksep=0.50;',
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
    #: **THE COUNT SUMS FROM THE ARROWS THAT REACH IT.** When the 2->3 arrows
    #: became tested triples, the node counts stayed marginal, so `feeling kept
    #: 70` sat at the end of a single arrow labelled 16 and `feeling arrives 6`
    #: had no arrow at all. Third time this figure has had a node whose number a
    #: reader could not check against its own edges; the fix is the same each
    #: time, which is why it is now written down: a column's counts come from
    #: whatever the figure actually draws into it.
    #: **AND WHEN IT CANNOT SUM, IT SAYS SO ON THE NODE.** There are 29 non-NONE
    #: flows and eleven of them are a single frame; drawing all of them puts the
    #: right half back where RH stopped it. So the selection stays, and the node
    #: carries BOTH numbers -- "155 (132 drawn)" -- because the alternative is
    #: the choice this figure has already got wrong twice in both directions:
    #: print the marginal and a reader adding the arrows finds it short, print
    #: the drawn sum and the figure quietly understates the conditional that is
    #: the whole point of the column.
    drawn_f, allflow, keepf, tail = _fate_flows(edges, triples)
    n_none = drawn_f.pop("NONE", 0)
    shown_f = collections.Counter()
    for (_b, _a, f), n in allflow.items():
        if (_b, _a, f) in keepf:
            shown_f[f] += n
    #: **A FATE NODE WITH NO ARROW IS NOT DRAWN.** `feeling arrives 7 (0 drawn)`
    #: stood alone in the top corner of the positive-lift render: it is never
    #: any edge's largest fate and never clears the triple test, so the
    #: selection leaves it with nothing pointing at it. This is the SAME defect
    #: the paragraph above records ("a count for flows the figure had just
    #: excluded") reappearing through a new route, which is why the rule is
    #: enforced here rather than trusted: a node exists if an arrow reaches it.
    #: Its frames join the omitted tail in the caption.
    col3 = 0
    L.append("  { rank=same;")
    for f, n in drawn_f.most_common():
        lab = FATE.get(f, f)
        if not shown_f[f]:
            tail += n
            continue
        col3 += n
        if shown_f[f] != n:
            L.append('  "F_%s" [label="%s\\n%d (%d drawn)"];' % (f, lab, n, shown_f[f]))
        else:
            L.append("  " + node("F_" + f, lab, n))
    L.append("  }")
    #: **THE LABEL IS ONE WORD PAIR.** It carried the count, the two-way affect
    #: split AND the pair -- three lines an edge, over sixteen edges, at 4.8
    #: inches. The counts are on the nodes and the splits are in the asymmetry
    #: table; what only the figure can give is the words. `→` written as
    #: the literal character: graphviz does not interpret python escapes, and
    #: the first render printed the four characters u2192.
    used_pairs = set()
    for (b, a), e in sorted(edges.items(), key=lambda kv: -kv[1]["n"]):
        #: the exemplar with the LARGEST charge drop on this edge; ties fall to
        #: the alphabetical pair so the same run always names the same words
        #: **A PAIR IS USED ONCE.** `killed -> helped` landed on three edges in
        #: one render, which reads as one frame in three places. Different
        #: frames can share an exemplar; take the next-best instead.
        lab = ""
        if (b, a) in EXEMPLARS:
            lab = "%s → %s" % EXEMPLARS[(b, a)]
            used_pairs.add(EXEMPLARS[(b, a)])
        else:
            ex = [x for x in sorted(e["ex"], key=lambda x: (-x[1], x[0]))
                  if x[0] not in used_pairs]
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
        w = _width(e["n"])
        #: a self-edge is arrowless: nothing changed kind, so there is no
        #: direction to assert and it must not read like one. It keeps its true
        #: width -- the frames are real -- but is drawn gray so the eye reads
        #: the tested edges first.
        #: **UNDER-REPRESENTED CELLS ARE DRAWN, AND MARKED.** The permutation
        #: test finds some cells significantly BELOW chance -- `physical act ->
        #: mixed` at 114 against 137 expected. Drawing them like the others
        #: would put "significant" on an arrow that means the opposite, so they
        #: are open-headed and their label carries the sign.
        #: **THE ARROWHEAD SAYS WHAT KIND OF EVIDENCE THE EDGE HAS.**
        #:   none    a self-edge: nothing changed kind, no direction asserted
        #:   normal  over-represented against the shuffle (and one-way, if the
        #:           transpose could test it at all)
        #:   vee     one-way ONLY -- directed but no more frequent than the
        #:           marginals predict. `voice -> mental state` is this: 11
        #:           against 1, and 11 against 8.2 expected.
        ev = e.get("evidence")
        if e.get("self"):
            extra = ' arrowhead=none color="#737373"'
        elif ev == "directed":
            extra = ' arrowhead=vee color="#737373"'
        else:
            extra = ""
        #: **THE BELOW-CHANCE MARKER IS GONE AND IT WAS COLLIDING.** It set a
        #: second `arrowhead=` on the same edge, so in `either` mode
        #: `physical act -> mental state` -- one-way AND significantly rarer
        #: than chance -- got both `vee` and `odot`, and graphviz takes the
        #: last. Two encodings on one mark, which is the fault this figure has
        #: already had twice.
        #:
        #: The arrowhead now says one thing: what KIND of evidence the edge
        #: has. That a directed edge is also below chance is a fact for the
        #: permutation table, where a sign is a column. RH removed below-chance
        #: edges from the permutation figure; in `either` mode such an edge can
        #: still be drawn on its directional evidence, and is.
        extra += " penwidth=%.2f" % w
        L.append('  "B_%s" -> "A_%s" [label="%s"%s];' % (b, a, lab, extra))
    #: column two to column three carries the MARGINAL only, and is drawn faint
    #: so it reads as a total rather than as a measured flow -- the joint is on
    #: the edge labels above, not here
    #: **COLUMN 2 -> 3 CARRIES A WORD PAIR TOO** (RH). Without one the third
    #: column is four abstractions a reader has to take on trust: the figure
    #: says "feeling kept" and never shows a frame where a feeling was kept.
    #: Each (aligned kind, fate) edge names the pair with the largest charge
    #: drop among the frames that took it -- the same rule as column 1 -> 2, so
    #: the two halves of the figure are exemplified the same way.
    #: **COLUMN 2 -> 3 IS TESTED TOO, AND PER SOURCE (RH).** It used to draw
    #: every fate a drawn edge produced, untested and MARGINAL over the base
    #: kind. Both were wrong.
    #:
    #: Untested: 1->2 had to clear BH while 2->3 cleared nothing, so one picture
    #: held two kinds of arrow drawn alike. Marginal: affect is NOT
    #: conditionally independent of the base kind given the aligned kind
    #: (p=0.0002 over 5,000 shuffles), and the effect is large -- a deed that
    #: becomes an utterance keeps its feeling 64% of the time, an utterance that
    #: stays one keeps it 0%, and the single arrow reported 32%, true of
    #: neither.
    #:
    #: An onward arrow now exists only where the TRIPLE (base, aligned, fate) is
    #: over-represented against a fate-shuffle -- one-sided, BH over the
    #: testable triples, from `path_flow.paths` so there is one implementation
    #: of that test -- and only for a pair that already earned a 1->2 edge.
    #:
    #: It is LABELLED BY ITS SOURCE only where the middle node has more than one
    #: onward arrow to the same fate, which is where an unlabelled arrow would
    #: be ambiguous. RH: with so few, the label is usually unnecessary.
    #: **EVERY FLOW IS DRAWN; SIGNIFICANCE IS THE HEAD, NOT THE EXISTENCE**
    #: (paper-claude). Drawing only the significant onward link made the figure
    #: assert the opposite of its own data: `thing -> thing` runs none 40, kept
    #: 27, gone 14, and only GONE is over-represented -- so the reader saw one
    #: arrow to "feeling gone" and concluded that moving the object loses the
    #: feeling, when it is the THIRD outcome and the feeling is kept twice as
    #: often. Significance says a flow is larger than chance predicts; it does
    #: not say the flow is what usually happens, and an arrow that exists only
    #: when significant conflates the two.
    #:
    #: So: an arrow for every fate a drawn edge produced, width by count, and a
    #: filled head only where the triple clears the test. A hollow head is a
    #: real flow that is not over-represented.
    if triples is not None:
        sig = {k for k in triples if (k[0], k[1]) in edges}
        src_count = collections.Counter(k[1:] for k in keepf)
        #: **EVERY FLOW THAT MATTERS, NOT EVERY FLOW.** Drawing all of them gave
        #: 30 onward arrows, about twenty of them n=1 or 2, and the right half
        #: became unreadable at 4.8 inches -- paper-claude's principle
        #: (significance is not prevalence) taken past the point where the
        #: figure can carry it.
        #:
        #: Per 1->2 edge: the fates that together cover 90% of its frames, PLUS
        #: any that clears the triple test however small. So the dominant flow
        #: is always shown -- which is the fix -- and a significant-but-minor
        #: one is never hidden. What is dropped is the tail, and the caption
        #: says how much of it.
        #: **THE DOMINANT FATE PER EDGE, PLUS ANY SIGNIFICANT ONE.** A 90%
        #: coverage rule gave 22 onward arrows and, with MIXED restored, would
        #: give well over thirty -- unreadable at 4.8 inches (RH). One arrow per
        #: edge is the minimum that still answers paper-claude's objection: the
        #: flow a reader would infer from the figure is the flow that actually
        #: dominates, and a significant-but-minor one is added rather than
        #: substituted. Everything else is tail, counted in the caption.
        for (b, a, f), n in sorted(allflow.items(), key=lambda kv: -kv[1]):
            if (b, a, f) not in keepf:
                continue
            tv = triples.get((b, a, f)) or {"n": n, "ex": None}
            #: **A WORD PAIR, NOT A COUNT (RH).** The onward arrows carried
            #: bare numbers while every 1->2 arrow carried words, so half the
            #: figure showed what a movement looks like and half asked the
            #: reader to take it on arithmetic. The count is already on the node
            #: the arrow reaches.
            #:
            #: The pair is the triple's own exemplar, from `path_flow`, chosen
            #: by the same rule as everywhere else -- best-attested word on each
            #: side, largest charge drop breaking ties -- so an onward arrow
            #: shows a frame that actually took THAT path rather than one that
            #: merely ended at the same fate.
            #: **EVERY ONWARD ARROW CARRIES A PAIR, NOT SOME OF THEM.** The
            #: third column mixed `kill → scream` with bare `40` and `7
            #: (voice)`, so one mark meant two things again -- the defect this
            #: figure has now had with fill, with line style and with width
            #: (paper-claude). His fix was counts everywhere; RH's standing
            #: instruction on this column is word pairs, so it is pairs
            #: everywhere. The counts are on the node each arrow reaches.
            #:
            #: A significant triple keeps `path_flow`'s own exemplar -- a frame
            #: that took THAT path. The rest fall back to the frame on this edge
            #: with that fate and the largest charge drop, which is the same
            #: rule column one uses, and `used_pairs` keeps one pair to one
            #: arrow across the whole figure.
            ex = tv.get("ex")
            if not ex or tuple(ex) in used_pairs:
                cand = sorted((x for x in edges[(b, a)]["exf"]
                               if x[2] == f and x[0] not in used_pairs),
                              key=lambda x: (-x[1], x[0]))
                ex = cand[0][0] if cand else ex
            if ex:
                used_pairs.add(tuple(ex))
            issig = (b, a, f) in sig
            lab = ("%s → %s" % tuple(ex)) if ex else "%d" % n
            if src_count[(a, f)] > 1:
                lab = "%s  (%s)" % (lab, PLAIN.get(b, b))
            head = "normal" if issig else "onormal"
            L.append('  "A_%s" -> "F_%s" [label="%s" color="#737373" '
                     'fontcolor="#737373" penwidth=%.2f arrowsize=0.4 '
                     'arrowhead=%s];' % (a, f, lab, _width(n), head))
    if triples is not None:
        title_note += ("; every arrow is labelled with one word pair from a "
                       "frame that took it and every count is on a node. "
                       "Column three is the %d frames the coder found a "
                       "feeling in: %d more had none on either side and are "
                       "not drawn. Onward arrows are each edge's largest fate "
                       "plus any over-represented one, %d frames in smaller "
                       "flows omitted"
                       % (col3, n_none, tail))
    L.append('  labelloc="b"; labeljust="l";')
    #: wrapped narrower than the graph lays out, so the caption never drives the
    #: plate width again; `align="left"` because the default centres each line
    import textwrap
    wrapped = '<br align="left"/>'.join(textwrap.wrap(title_note, 95)) + \
              '<br align="left"/>'
    L.append('  label=<<font point-size="%g">%s</font>>;' % (pt * 0.85, wrapped))
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
    ap.add_argument("--lift-cut", choices=("third", "half", "positive"),
                    default="third",
                    help="with --high-lift: top third (a rank), top half, or "
                         "any POSITIVE lift (a stated boundary -- the base "
                         "words are more charged than their setup)")
    ap.add_argument("--test", choices=("transpose", "permutation", "either"),
                    default="transpose",
                    help="transpose: X->Y against Y->X, cannot test a self-edge. "
                         "permutation: each cell against a marginal-preserving "
                         "shuffle, tests everything, conditions on a marginal "
                         "alignment produced")
    ap.add_argument("--out", default=None)
    ap.add_argument("--also", default=None, help="directory for a second copy")
    a = ap.parse_args(argv)
    rows = a.rows or os.path.join(HERE, "results", "fates_corpus_%s.jsonl" % a.lang)
    edges, fates, used, dropped, cut, ntest = load(rows, a.lang, a.high_lift,
                                                   a.min_edge, a.test, a.lift_cut)
    if not edges:
        raise SystemExit("no edges clear --min-edge %d" % a.min_edge)
    #: **THE TEST GOES IN THE FILENAME TOO, AND LEAVING IT OUT PUT THE WRONG
    #: FIGURE IN THE PAPER.** The tag carried the language, the lift cut and a
    #: `_perm` suffix, so `--test either` and `--test transpose` both wrote
    #: `kind_flow_en`. A loop that ran the three variants in sequence ended on
    #: `transpose`, which overwrote the `either` render, and that was what got
    #: copied to Dropbox and committed -- a figure with MIXED, FUNCTION and
    #: untested marginal arrows, captioned as the current one. Caught by RH
    #: looking at the Dropbox copy.
    #:
    #: The rule this file already states for the lift variants ("a default name
    #: shared by four runs is how a level-mode figure ends up captioned as a
    #: delta-mode one") applied to the test dimension and was not extended to
    #: it. Every dimension that changes the figure is now in the path.
    tag = "%s%s_%s" % (a.lang,
                       ("_lift" + a.lift_cut) if a.high_lift else "",
                       a.test)
    out = a.out or os.path.join(HERE, "results", "kind_flow_%s.dot" % tag)
    note = ("%d frames; %d dropped where the two label orders disagreed; "
            "%s%s"
            % (used, dropped,
               ("every cell against a marginal-preserving shuffle, q&lt;0.05 BH "
                "over %d cells; cells below chance and all MIXED cells omitted" % ntest)
               if a.test == "permutation" else
               ("edges significant on EITHER test: over-represented against a "
                "marginal-preserving shuffle (solid head) or one-way against "
                "its own transpose (open head); same-kind edges headless and "
                "testable only by the shuffle. `mixed` is the coder's "
                "ABSTENTION -- no one kind covers two thirds of that group's "
                "words -- not a kind; FUNCTION omitted" )
               if a.test == "either" else
               ("off-diagonal edges one-way at q&lt;0.05, BH over %d tested "
                "pairs; same-kind edges arrowless and NOT tested" % ntest),
               ("; lift above %+.2f only (%s)" % (cut, {"positive": "any positive lift",
                "half": "top half", "third": "top third"}[a.lift_cut]))
               if cut is not None else ""))
    #: the triple test runs only for `either`, which is the hybrid RH asked
    #: for: 1->2 on the looser rule (directed OR over-represented), 2->3 on the
    #: strict one (the path itself over-represented). The other two modes keep
    #: their old untested marginal arrows and say so in their captions.
    trip = None
    if a.test == "either":
        from path_flow import paths as _paths
        trip, _nf, _nt, _c = _paths(rows, a.lang, a.high_lift, a.min_edge)
    emit(edges, fates, out, note, triples=trip)
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
