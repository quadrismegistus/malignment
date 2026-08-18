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


def page(frame=None, n=12):
    recs = records(frame)
    e = html.escape
    P = ['<title>Alignment, lineage by lineage</title>', """<style>
:root{--bg:#fbfaf7;--fg:#1a1a1a;--mut:#6b6b6b;--line:#dedbd4;--up:#0a6b3d;--dn:#9b1c1c;--card:#fff}
:root:not([data-theme="light"]){}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#14140f;--fg:#eceae4;--mut:#9a978e;--line:#33322c;--up:#5fd39a;--dn:#f08b8b;--card:#1c1c17}}
:root[data-theme="dark"]{--bg:#14140f;--fg:#eceae4;--mut:#9a978e;--line:#33322c;--up:#5fd39a;--dn:#f08b8b;--card:#1c1c17}
body{background:var(--bg);color:var(--fg);font:16px/1.55 Charter,Georgia,serif;margin:0;padding:2.5rem 1.25rem 6rem}
.w{max-width:60rem;margin:0 auto}
h1{font-size:1.7rem;margin:0 0 .2rem;letter-spacing:-.01em}
.sub{color:var(--mut);margin:0 0 2.2rem;font-size:.95rem}
.c{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:1.1rem 1.25rem;margin:0 0 1.1rem}
.m{font:600 1.02rem/1.3 ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:-.01em}
.b{color:var(--mut);font:.8rem/1.4 ui-monospace,Menlo,monospace;margin:.15rem 0 .7rem}
.k{font-style:italic;margin:.1rem 0 .5rem}
.rd{color:var(--mut);font-size:.93rem;margin:0 0 .7rem}
.rel{font-size:.9rem;margin:.15rem 0;padding-left:1rem;border-left:2px solid var(--line)}
.rel b{font-weight:600;font-style:normal}
.t{display:grid;grid-template-columns:1fr 1fr;gap:0 1.6rem;font:.83rem/1.5 ui-monospace,Menlo,monospace;margin-top:.7rem;overflow-x:auto}
.h{color:var(--mut);font-size:.72rem;letter-spacing:.06em;text-transform:uppercase;border-bottom:1px solid var(--line);padding-bottom:.25rem;margin-bottom:.3rem}
.r{display:flex;justify-content:space-between;gap:.6rem;white-space:nowrap}
.w1{overflow:hidden;text-overflow:ellipsis}
.up{color:var(--up)}.dn{color:var(--dn)}
.pill{display:inline-block;font:.7rem/1 ui-monospace,Menlo,monospace;padding:.28rem .5rem;border:1px solid var(--line);border-radius:99px;color:var(--mut);margin-left:.5rem;vertical-align:.1em}
.more{color:var(--mut);font-size:.78rem;margin-top:.4rem}
</style>"""]
    fr = recs[0][1]["meta"]["frame_prompt"] + " ___" if recs else ""
    P.append('<div class=w><h1>%s</h1>' % e(fr))
    P.append('<p class=sub>%d declared endpoint pairs. Left column rises under the aligned checkpoint, right column under the base. One blind rater per lineage; neither the rater nor the ordering was told which arm is which.</p>' % len(recs))
    for k, v in recs:
        r, mv = v["result"], v["movement"]
        P.append('<div class=c><div class=m>%s<span class=pill>%s</span></div>'
                 % (e(k["aligned"].split("/")[-1]), e(r["confidence"])))
        P.append('<div class=b>%s</div>' % e(k["base"]))
        P.append('<div class=k>%s</div>' % e(r["kind"]))
        P.append('<div class=rd>%s</div>' % e(r["reading"]))
        for rel in r["relations"]:
            P.append('<div class=rel><b>%s</b> &mdash; %s</div>' % (e(rel["name"]), e(rel["sentence"])))
        P.append('<div class=t><div><div class=h>higher aligned</div>')
        for m in mv["higher_b"][:n]:
            P.append('<div class=r><span class=w1>%s</span><span class=up>%+.1f</span></div>' % (e(m["word"]), m["delta"]))
        P.append('</div><div><div class=h>higher base</div>')
        for m in mv["higher_a"][:n]:
            P.append('<div class=r><span class=w1>%s</span><span class=dn>%+.1f</span></div>' % (e(m["word"]), m["delta"]))
        P.append('</div></div>')
        more = (max(0, len(mv["higher_b"]) - n), max(0, len(mv["higher_a"]) - n))
        if any(more):
            P.append('<div class=more>+%d more rising, +%d more falling</div>' % more)
        P.append('</div>')
    P.append('</div>')
    return "\n".join(P)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--frame")
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--html", metavar="PATH")
    a = ap.parse_args()
    if a.html:
        open(a.html, "w").write(page(a.frame, max(a.n, 12)))
        print("wrote %s" % a.html)
    else:
        text(a.frame, a.n)
