"""Per-lineage exhibit: what the model did, beside what the rater said about it.

    python exhibit.py                       every frame in the stash
    python exhibit.py --frame stroking      one frame, by nickname
    python exhibit.py --html out.html       a scannable page instead

## WHY THIS EXISTS

A confidence value and an invented phrase are unreadable without the movement
they were invented for. `--list` gives the phrase and the stash gives the table,
and holding those apart made the result unreadable at exactly the moment it got
interesting -- which is the point at which a reader stops trusting it.

The movement here is the one stored ON THE RECORD, parsed from the prompt the
rater received. It is not re-queried, so the table printed beside a judgment is
the table that judgment was made from, and no insertion into the store can put
those two out of step.
"""
import argparse
import html
import os
import sys

import run


def records(frame=None):
    st = run._stash()
    out = []
    for k in st.keys():
        v = st[k]
        if not v or not v.get("movement"):
            continue
        meta = v.get("meta") or {}
        if frame and meta.get("nickname") != frame:
            continue
        out.append((k, v))
    #: Sorted by the size of the largest single fall, so the lineages that did
    #: the most are first and a reader who stops early has still seen them.
    def worst(x):
        a = x[1]["movement"]["higher_a"]
        return min([m["delta"] for m in a] or [0.0])
    return sorted(out, key=worst)


def rows(mv, n):
    b, a = mv["higher_b"][:n], mv["higher_a"][:n]
    for i in range(max(len(b), len(a))):
        x = b[i] if i < len(b) else None
        y = a[i] if i < len(a) else None
        yield (("%-12s %5.1f->%5.1f %+6.1f" % (x["word"], x["pre"], x["post"], x["delta"])) if x else "",
               ("%-12s %5.1f->%5.1f %+6.1f" % (y["word"], y["pre"], y["post"], y["delta"])) if y else "")


def text(frame=None, n=8):
    recs = records(frame)
    if not recs:
        print("no records with movement%s" % (" for frame %r" % frame if frame else ""),
              file=sys.stderr)
        return
    print("%d lineages | %s" % (len(recs), recs[0][1]["meta"]["frame_prompt"] + " ___"))
    for k, v in recs:
        r, mv, meta = v["result"], v["movement"], v["meta"]
        print("\n" + "=" * 78)
        print("%s   [%s]" % (k["aligned"], r["confidence"]))
        print("  base %s" % k["base"])
        print("  KIND: %s" % r["kind"])
        print("  READING: %s" % r["reading"])
        for rel in r["relations"]:
            print("    * %s -- %s" % (rel["name"], rel["sentence"]))
        print()
        print("  %-34s | %s" % ("HIGHER ALIGNED (B)", "HIGHER BASE (A)"))
        for x, y in rows(mv, n):
            print("  %-34s | %s" % (x, y))
        more = (max(0, len(mv["higher_b"]) - n), max(0, len(mv["higher_a"]) - n))
        if any(more):
            print("  (+%d more B, +%d more A)" % more)


#: PALETTE NOTE, WHICH IS AN ARGUMENT AND NOT A PREFERENCE. The two arms get a
#: TEMPERATURE opposition (burnt ochre for the base checkpoint, deep teal for the
#: aligned one) rather than the red/green a diff would use. Half these lineages
#: move explicit mass down and a third move it up; a palette that codes one arm
#: as loss and the other as gain would assert a direction the data refuses, in
#: the one channel a reader never consciously reads.
CSS = """
:root{
  --paper:#f2f3ef; --ink:#171a17; --rule:#d5d8d0; --mute:#6d716a; --card:#fbfbf8;
  --base:#a1601b; --algn:#175f6d; --accent:#3f4270; --shade:#e7e9e3;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --paper:#101210; --ink:#e7e9e3; --rule:#2c2f2a; --mute:#8d918a; --card:#171a16;
  --base:#d99a52; --algn:#59a7b7; --accent:#a0a2d8; --shade:#1f221d;
}}
:root[data-theme="dark"]{
  --paper:#101210; --ink:#e7e9e3; --rule:#2c2f2a; --mute:#8d918a; --card:#171a16;
  --base:#d99a52; --algn:#59a7b7; --accent:#a0a2d8; --shade:#1f221d;
}
*{box-sizing:border-box}
body{background:var(--paper);color:var(--ink);margin:0;
  font:17px/1.6 "Iowan Old Style","Palatino Linotype",Palatino,"Book Antiqua",Georgia,serif;
  -webkit-font-smoothing:antialiased}
.wrap{max-width:64rem;margin:0 auto;padding:4rem 1.5rem 8rem}
.mono{font-family:ui-monospace,"SF Mono",SFMono-Regular,Menlo,Consolas,monospace;
  font-variant-numeric:tabular-nums}
.eyebrow{font:600 .68rem/1 ui-monospace,Menlo,monospace;letter-spacing:.18em;
  text-transform:uppercase;color:var(--mute)}
h1{font-size:clamp(2.1rem,5vw,3.1rem);line-height:1.04;letter-spacing:-.022em;
  margin:.55rem 0 .9rem;text-wrap:balance;font-weight:600}
.dek{font-size:1.06rem;color:var(--mute);max-width:40rem;margin:0 0 2.6rem}
.dek b{color:var(--ink);font-weight:600}

/* --- summary strip: the finding, before the evidence --- */
.strip{display:grid;grid-template-columns:repeat(auto-fit,minmax(13rem,1fr));gap:1px;
  background:var(--rule);border:1px solid var(--rule);border-radius:3px;margin:0 0 3.4rem}
.cell{background:var(--card);padding:1.1rem 1.15rem}
.cell .n{font:600 1.85rem/1 ui-monospace,Menlo,monospace;letter-spacing:-.02em;
  font-variant-numeric:tabular-nums;display:block;margin:.1rem 0 .35rem}
.cell p{margin:0;font-size:.87rem;color:var(--mute);line-height:1.45}

/* --- frame section --- */
.frame{margin:0 0 4.5rem}
.fh{border-top:2px solid var(--ink);padding-top:.8rem;margin-bottom:.5rem}
.fh h2{font-size:1.5rem;margin:.3rem 0 .5rem;letter-spacing:-.012em;font-weight:600}
.fh .slot{font-family:ui-monospace,Menlo,monospace;font-size:.95rem;
  background:var(--shade);padding:.12rem .38rem;border-radius:2px}
.fh p{margin:.4rem 0 0;color:var(--mute);font-size:.9rem;max-width:44rem}

/* --- one lineage --- */
.e{border-bottom:1px solid var(--rule);padding:1.9rem 0}
.e:last-child{border-bottom:0}
.id{display:flex;flex-wrap:wrap;align-items:baseline;gap:.55rem;margin-bottom:.5rem}
.id .a{font:600 1.06rem/1.2 ui-monospace,Menlo,monospace;letter-spacing:-.015em;color:var(--algn)}
.id .arrow{color:var(--mute);font-size:.85rem}
.id .b{font:.9rem/1.2 ui-monospace,Menlo,monospace;color:var(--base)}
.pill{font:600 .64rem/1 ui-monospace,Menlo,monospace;letter-spacing:.1em;text-transform:uppercase;
  border:1px solid var(--rule);border-radius:99px;padding:.3rem .55rem;color:var(--mute)}
.kind{font-style:italic;font-size:1.08rem;margin:.1rem 0 .55rem;max-width:44rem;text-wrap:balance}
.reading{margin:0 0 .9rem;max-width:44rem;font-size:.97rem}
.rels{margin:0 0 1.15rem;max-width:44rem}
.rel{font-size:.9rem;color:var(--mute);padding-left:.9rem;border-left:2px solid var(--rule);
  margin:.4rem 0;line-height:1.5}
.rel b{color:var(--ink);font-weight:600;font-style:italic}

/* --- the ledger: bars grow away from a centre rule --- */
.ledger{border-top:1px solid var(--rule);padding-top:.7rem;overflow-x:auto}
.lh{display:grid;grid-template-columns:1fr 1fr;gap:0 2.2rem;margin-bottom:.45rem}
.lh span{font:600 .64rem/1 ui-monospace,Menlo,monospace;letter-spacing:.13em;text-transform:uppercase}
.lh .l{text-align:right;color:var(--base)}
.lh .r{color:var(--algn)}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:0 2.2rem;min-width:34rem}
.col{display:flex;flex-direction:column;gap:.14rem}
.row{display:grid;align-items:center;gap:.5rem;font:.79rem/1.35 ui-monospace,Menlo,monospace;
  font-variant-numeric:tabular-nums}
.col.l .row{grid-template-columns:3.2rem 1fr 6.6rem;text-align:right}
.col.r .row{grid-template-columns:6.6rem 1fr 3.2rem}
.bar{height:9px;border-radius:1px;min-width:1px}
.col.l .bar{background:var(--base);justify-self:end}
.col.r .bar{background:var(--algn);justify-self:start}
.wd{color:var(--ink);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.dl{color:var(--mute);font-size:.72rem}
.scale{color:var(--mute);font-size:.72rem;margin-top:.5rem;
  font-family:ui-monospace,Menlo,monospace}
.none{color:var(--mute);font-size:.79rem;font-style:italic;padding:.3rem 0}
footer{border-top:1px solid var(--rule);margin-top:3rem;padding-top:1.3rem;
  color:var(--mute);font-size:.83rem;max-width:44rem}
footer code{font-family:ui-monospace,Menlo,monospace;font-size:.9em;
  background:var(--shade);padding:.06rem .28rem;border-radius:2px}
@media (max-width:44rem){
  .grid,.lh{grid-template-columns:1fr;gap:1.1rem}
  .col.l .row{grid-template-columns:6.6rem 1fr 3.2rem;text-align:left}
  .col.l .bar{justify-self:start}
  .lh .l{text-align:left}
}
"""


FRAMES = [
    ("stroking", "A sexual frame",
     "Fourteen lineages move explicit mass down, six sit flat, ten move it up. "
     "The referent of the gesture is what changes: eleven raters, with no shared "
     "vocabulary, reached for some version of <em>which scene this belongs to</em>."),
    ("union", "An institutional frame",
     "Here the act does not move; its naming does. Raters kept describing a "
     "change of grain or register rather than of content, and one of them named "
     "it outright as <em>which vocabulary an unchanged act is named in</em>."),
]


def _bars(items, side, cap, n):
    e = html.escape
    out = ['<div class="col %s">' % side]
    if not items:
        return '<div class="col %s"><div class=none>nothing rises on this side</div></div>' % side
    for m in items[:n]:
        w = max(1.0, 100.0 * abs(m["delta"]) / cap)
        lab = '<span class=wd>%s</span>' % e(m["word"])
        num = '<span class=dl>%.1f&#8202;&#8594;&#8202;%.1f</span>' % (m["pre"], m["post"])
        bar = '<span class=bar style="width:%.1f%%"></span>' % w
        d = '<span class=dl>%+.1f</span>' % m["delta"]
        if side == "l":
            out.append('<div class=row>%s%s%s %s</div>' % (d, bar, lab, num))
        else:
            out.append('<div class=row>%s %s%s%s</div>' % (num, lab, bar, d))
    out.append('</div>')
    return "".join(out)


def page(frames=None, n=10):
    e = html.escape
    P = ['<title>Sixty Lineages</title>', '<style>%s</style>' % CSS, '<div class=wrap>']
    P.append('<div class=eyebrow>malignment &middot; displacement taxonomy &middot; instrument v3</div>')
    P.append('<h1>Sixty Lineages</h1>')
    P.append('<p class=dek>Two slot frames, run across the thirty declared base&#8202;&#8594;&#8202;aligned '
             'checkpoint pairs that have both arms measured. One blind rater per lineage, '
             'told only that two measurements were taken under conditions <b>A</b> and <b>B</b>. '
             'Every judgment below sits beside the word table it was made from.</p>')

    P.append('<div class=strip>')
    for num, txt in (("23 / 30", "lineages whose next-word distribution NARROWS after alignment. The same count on both frames, p = 0.005 each. This holds with no word list involved."),
                     ("14 / 6 / 10", "on the sexual frame, lineages whose explicit mass falls, holds, rises. The direction is not uniform; the narrowing is."),
                     ("+147 pp", "summed rise on <span class=mono>fire</span> across the institutional frame. <span class=mono>discipline</span> +85, <span class=mono>terminate</span> +69, <span class=mono>retaliate</span> +52."),
                     ("60", "codings, one rater each, claude-opus-5. No rater saw another&#8217;s answer, the checkpoint names, or which arm was which.")):
        P.append('<div class=cell><span class="n mono">%s</span><p>%s</p></div>' % (num, txt))
    P.append('</div>')

    for key, heading, blurb in FRAMES:
        recs = records(key)
        if frames and key not in frames:
            continue
        if not recs:
            continue
        slot = recs[0][1]["meta"]["frame_prompt"] + " ___"
        P.append('<section class=frame><div class=fh><div class=eyebrow>%d lineages</div>'
                 '<h2>%s</h2><div class=slot>%s</div><p>%s</p></div>'
                 % (len(recs), e(heading), e(slot), blurb))
        for k, v in recs:
            r, mv = v["result"], v["movement"]
            #: SCALE IS PER ENTRY AND SAID SO. One lineage puts 66 points on a
            #: single word; a shared axis would flatten the other 59 into
            #: nothing. The bar length is a within-entry comparison and the
            #: largest value is printed so nobody reads it as a between-entry one.
            cap = max([abs(m["delta"]) for m in mv["higher_b"] + mv["higher_a"]] or [1.0])
            P.append('<div class=e><div class=id><span class=a>%s</span>'
                     '<span class=arrow>&#8592; aligned from &#8212; base</span>'
                     '<span class=b>%s</span><span class=pill>%s confidence</span></div>'
                     % (e(k["aligned"].split("/")[-1]), e(k["base"].split("/")[-1]),
                        e(r["confidence"])))
            P.append('<div class=kind>%s</div>' % e(r["kind"]))
            P.append('<p class=reading>%s</p>' % e(r["reading"]))
            if r.get("relations"):
                P.append('<div class=rels>')
                for rel in r["relations"]:
                    P.append('<div class=rel><b>%s</b> &mdash; %s</div>'
                             % (e(rel["name"]), e(rel["sentence"])))
                P.append('</div>')
            P.append('<div class=ledger><div class=lh><span class=l>higher under base</span>'
                     '<span class=r>higher under aligned</span></div><div class=grid>')
            P.append(_bars(mv["higher_a"], "l", cap, n))
            P.append(_bars(mv["higher_b"], "r", cap, n))
            P.append('</div>')
            more = (max(0, len(mv["higher_a"]) - n), max(0, len(mv["higher_b"]) - n))
            note = "bars scaled within this lineage; longest = %.1f points" % cap
            if any(more):
                note += " &middot; %d more falling, %d more rising not shown" % more
            P.append('<div class=scale>%s</div></div></div>' % note)
        P.append('</section>')

    P.append('<footer><p>Percentages are true next-token probabilities over the '
             'measured word field, one decimal, exactly as the rater saw them. A word '
             'appears only if it clears the canonical movement rule; risers are '
             'null-tested and fallers are not, so an empty rising column is a weaker '
             'statement than a full one. Ochre and teal mark the two checkpoints and '
             'carry no valence: on one frame the aligned arm removes explicit terms '
             'and on ten lineages it adds them, so a palette coding one side as loss '
             'would assert what the data refuses.</p>'
             '<p>Produced by <code>exhibit.py</code> from records in '
             '<code>experiments/displacement_taxonomy/results/stash</code>. Each record '
             'stores the prompt verbatim and the movement parsed back out of it, so the '
             'table beside a judgment is the table that judgment was made from.</p>'
             '</footer></div>')
    return "\n".join(P)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--frame")
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--html", metavar="PATH")
    a = ap.parse_args()
    if a.html:
        open(a.html, "w").write(page([a.frame] if a.frame else None, max(a.n, 10)))
        print("wrote %s" % a.html)
    else:
        text(a.frame, a.n)
