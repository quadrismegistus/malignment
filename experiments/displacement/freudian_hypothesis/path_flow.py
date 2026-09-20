"""The five tested paths: base kind -> aligned kind -> what happened to the affect.

    python -u path_flow.py                    -> results/path_flow_en.{dot,pdf,png}
    python -u path_flow.py --high-lift
    python -u path_flow.py --also DIR

## WHY A PATH AND NOT TWO HOPS

`kind_flow.py` draws three columns with arrows between 1-2 and between 2-3, and
RH's question exposed what that costs: the 2-3 arrows are MARGINAL OVER THE BASE
KIND, and the base kind is not ignorable. Affect is not conditionally
independent of it given the aligned kind -- p=0.0002 over 5,000 shuffles -- and
the effect is large where it matters:

    aligned = VOCAL_ACT (n=69)        kept   gone  changed   none
      from PHYSICAL_ACT    n=25        64%    12%      0%     16%
      from MIXED           n=31        16%     0%     13%     45%
      from VOCAL_ACT       n=11         0%     9%     18%     73%
      the marginal arrow   n=69        32%     6%      9%     39%

A deed that becomes an utterance keeps its feeling 64% of the time; an utterance
that stays one keeps it 0%. The single arrow reports 32% and is true of neither.

So the unit here is the TRIPLE. One arrow per path, each tested.

## THE TEST, AND WHERE IT DIFFERS FROM `kind_flow`'s

Each (base, aligned, fate) against a null that shuffles the FATE across frames,
holding the edge sizes and the fate marginal, 20,000 draws, BH over the
testable triples. Five survive of twelve testable.

Two differences from the 1->2 test, both because a triple is not a pair:

  - **No transpose.** `X -> Y -> f` has no reverse, so there is no directional
    arm and the `either` rule does not apply here.
  - **One-sided.** An under-represented path is not a path. `kind_flow` tests
    two-sided because a cell BELOW chance is a real finding about a pairing;
    "this route is taken less often than chance" is not a route.

## WHAT IT RESTS ON

253 frames. A triple needs all three fields agreed across both label orders AND
both kinds nameable, and `MIXED`/`FUNCTION` are excluded as elsewhere. That
number belongs in the caption; it is the price of asking a three-way question of
a corpus that abstains on half of it.
"""
import argparse, collections, os, random, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
for p in (ROOT, HERE, os.path.join(HERE, "tasks")):
    if p not in sys.path:
        sys.path.insert(0, p)

from kind_flow import PLAIN, FATE, DROP_KINDS, _width

SEED = 20260920


def paths(path, lang="en", high_lift=False, min_n=6, n_shuffle=20000):
    """-> (significant triples, n_frames, n_testable, cut)"""
    import json
    import re
    from malignment import charge
    cjk = re.compile(r"[一-鿿]")
    rows = [json.loads(l) for l in open(path, encoding="utf-8")]
    rows = [r for r in rows if bool(cjk.search(r["frame"])) == (lang == "zh")]
    cut = None
    if high_lift:
        lift = {}
        for r in rows:
            sc = charge.scene(r["frame"]) or {}
            ws = [w.strip() for w in (r.get("_base") or "").split(",")]
            v = [sc[w] for w in ws if w in sc]
            d, l = charge.dose(r["frame"]), charge.lift(r["frame"])
            if v and isinstance(d, (int, float)) and isinstance(l, (int, float)):
                lift[r["frame"]] = sum(v) / len(v) - (d - l)
        cut = 0.0
        rows = [r for r in rows if lift.get(r["frame"], -9e9) > cut]
    trip, ex = [], collections.defaultdict(list)
    for r in rows:
        ch, af = r["orient"].get("channel"), r["orient"].get("affect")
        if not ch or " -> " not in ch or af is None:
            continue
        b, a = ch.split(" -> ", 1)
        if {b, a} & DROP_KINDS:
            continue
        trip.append((b, a, af))
        bw = [w.strip() for w in (r.get("_base") or "").split(",") if w.strip()]
        aw = [w.strip() for w in (r.get("_aligned") or "").split(",") if w.strip()]
        if bw and aw:
            sc = charge.scene(r["frame"]) or {}
            ex[(b, a, af)].append(((bw[0], aw[0]),
                                   sc.get(bw[0], 0) - sc.get(aw[0], 0)))
    obs = collections.Counter(trip)
    pairs = [(b, a) for b, a, _f in trip]
    fates = [f for _b, _a, f in trip]
    rnd = random.Random(SEED)
    ge = collections.Counter()
    for _ in range(n_shuffle):
        rnd.shuffle(fates)
        c = collections.Counter((b, a, f) for (b, a), f in zip(pairs, fates))
        for k in obs:
            if c[k] >= obs[k]:
                ge[k] += 1
    tested = [k for k in obs if obs[k] >= min_n]
    #: **ONE-SIDED, AND THAT IS THE DIFFERENCE FROM `kind_flow`.** A cell below
    #: chance is a finding about a PAIRING; a route taken less often than
    #: chance is not a route, and there is nothing to draw.
    raw = {k: min(1.0, (ge[k] + 1) / (n_shuffle + 1.0)) for k in tested}
    order = sorted(tested, key=lambda k: raw[k])
    M, q, prev = len(order), {}, 1.0
    for rank, k in enumerate(reversed(order), 1):
        prev = min(prev, raw[k] * M / (M - rank + 1))
        q[k] = prev
    pc, fc, n = collections.Counter(pairs), collections.Counter(fates), len(trip)
    out = {}
    for k in tested:
        if q[k] >= 0.05:
            continue
        e = sorted(ex[k], key=lambda x: (-x[1], x[0]))
        out[k] = {"n": obs[k], "exp": pc[(k[0], k[1])] * fc[k[2]] / n,
                  "q": q[k], "ex": e[0][0] if e else None}
    return out, len(trip), len(tested), cut


def emit(sig, out, note):
    from malignment import figure as _fig
    fam, pt = _fig.pub_font(), _fig.PUB_FONT_PT
    L = ['digraph pathflow {', '  rankdir=LR; splines=true; overlap=false;',
         '  size="%g,%g!"; ratio=compress;' % (_fig.PUB_SIZE[0], _fig.PUB_SIZE[0] * 0.95),
         '  bgcolor="white"; nodesep=0.16; ranksep=1.0;',
         '  node [shape=box style="rounded" fontname="%s" fontsize=%g '
         'color="black" fontcolor="black" margin="0.06,0.035" penwidth=0.6];'
         % (fam, pt),
         '  edge [fontname="%s" fontsize=%g color="#4d4d4d" arrowsize=0.5];'
         % (fam, pt * 0.8)]
    #: **ONE MIDDLE NODE PER PATH, NOT ONE PER KIND.** Sharing a middle node
    #: would put two paths through it and re-create the marginal arrow this
    #: figure exists to avoid: a reader tracing `physical act -> voice` onward
    #: would meet arrows belonging to a different source. The middle column is
    #: therefore labelled by kind but instantiated per path.
    bn = collections.Counter()
    for (b, _a, _f), v in sig.items():
        bn[b] += v["n"]
    fn = collections.Counter()
    for (_b, _a, f), v in sig.items():
        fn[f] += v["n"]
    L.append("  { rank=same;")
    for b, n in bn.most_common():
        L.append('  "B_%s" [label="%s\\n%d"];' % (b, PLAIN.get(b, b), n))
    L.append("  }")
    L.append("  { rank=same;")
    for k, v in sig.items():
        L.append('  "M_%s_%s_%s" [label="%s"];'
                 % (k[0], k[1], k[2], PLAIN.get(k[1], k[1])))
    L.append("  }")
    L.append("  { rank=same;")
    for f, n in fn.most_common():
        L.append('  "F_%s" [label="%s\\n%d"];' % (f, FATE.get(f, f), n))
    L.append("  }")
    for k, v in sorted(sig.items(), key=lambda kv: -kv[1]["n"]):
        mid = "M_%s_%s_%s" % k
        lab = ("%s → %s" % v["ex"]) if v["ex"] else ""
        w = _width(v["n"], top=40.0)
        L.append('  "B_%s" -> "%s" [label="%s" penwidth=%.2f];' % (k[0], mid, lab, w))
        L.append('  "%s" -> "F_%s" [label="%d" penwidth=%.2f];' % (mid, k[2], v["n"], w))
    L.append('  labelloc="b"; labeljust="l";')
    L.append('  label=<<font point-size="%g">%s</font>>;' % (pt * 0.85, note))
    L.append("}")
    open(out, "w", encoding="utf-8").write("\n".join(L) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rows", default=None)
    ap.add_argument("--lang", choices=("en", "zh"), default="en")
    ap.add_argument("--high-lift", action="store_true")
    ap.add_argument("--min-n", type=int, default=6)
    ap.add_argument("--also", default=None)
    a = ap.parse_args(argv)
    rows = a.rows or os.path.join(HERE, "results", "fates_corpus_%s.jsonl" % a.lang)
    sig, nfr, ntest, cut = paths(rows, a.lang, a.high_lift, a.min_n)
    tag = "%s%s" % (a.lang, "_liftpositive" if a.high_lift else "")
    out = os.path.join(HERE, "results", "path_flow_%s.dot" % tag)
    note = ("%d frames carrying all three fields with both kinds nameable; "
            "%d paths testable at n&ge;%d, %d over-represented against a "
            "fate-shuffle at q&lt;0.05 BH (one-sided, 20,000 draws). "
            "MIXED and FUNCTION omitted%s"
            % (nfr, ntest, a.min_n, len(sig),
               "; positive lift only" if cut is not None else ""))
    emit(sig, out, note)
    print("%s: %d frames, %d testable, %d paths drawn" % (tag, nfr, ntest, len(sig)))
    for k, v in sorted(sig.items(), key=lambda kv: -kv[1]["n"]):
        print("   %-44s n=%-3d exp=%4.1f q=%.2g  %s"
              % ("%s -> %s -> %s" % k, v["n"], v["exp"], v["q"],
                 ("%s → %s" % v["ex"]) if v["ex"] else ""))
    outs = [out]
    for fmt in ("pdf", "png"):
        p = out.replace(".dot", "." + fmt)
        if os.path.exists(p):
            os.remove(p)
        r = subprocess.run(["dot", "-T" + fmt]
                           + (["-Gdpi=300"] if fmt == "png" else [])
                           + [out, "-o", p], capture_output=True, text=True)
        if r.returncode or not os.path.exists(p):
            print("  dot -T%s FAILED: %s" % (fmt, r.stderr.strip()[:200]))
        else:
            outs.append(p)
    if a.also:
        import shutil
        os.makedirs(a.also, exist_ok=True)
        for p in outs:
            shutil.copy(p, a.also)
    print("  wrote %s" % ", ".join(os.path.basename(x) for x in outs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
