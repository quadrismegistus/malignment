"""Null-corrected pole mass, per relation. Does alignment move mass marked -> unmarked?

    .venv/bin/python -u pole_null.py --verify     # bulk vs movement.pole_excess
    .venv/bin/python -u pole_null.py

## THE PROBLEM THIS SOLVES

Raw pole mass cannot answer it. Every candidate above 1% gains under alignment
because the aligned arm is more peaked -- measured over 10,970 cells, marked
+0.0208 and unmarked +0.0447. The differential partly cancels that, but
proportional inflation favours whichever pole started larger, and the unmarked
pole does start larger (0.135 against 0.108).

`movement.CANONICAL`'s renormalisation null IS the uniform-concentration model:
`null = P * (R/S)` says every survivor grows by the same factor. So the deviation
from it -- `excess = Q - null` -- is movement beyond general concentration, which
is the question.

    R = 1 - sum(p_aligned) over fallers
    S = sum(p_base) over non-fallers + resid_base
    inflation = R / S
    excess = mass_aligned - sum(p_base * inflation) over the pole

## WHY THIS DOES NOT CALL `movement.pole_excess` IN A LOOP

That function issues two ClickHouse queries per call, and this needs 12,219
splits x 2 poles. Cell-at-a-time is what ClickHouse is worst at -- movement.py
records 192 ms/cell against 0.097 ms/cell in bulk -- so the arithmetic is
mirrored here over bulk pulls, one query per pair. `--verify` checks the mirror
against the function on a sample rather than trusting it.

## THREE THINGS ABOUT `excess` THAT CHANGE HOW IT READS

**IT IS A COUNTERFACTUAL, NOT A PARTITION.** `inflation` is calibrated on
non-fallers, so applying it to a pole containing fallers asks "what would these
words hold if they had scaled like the survivors". Summed over every word in a
cell the nulls exceed 1 -- on the worked cop cell, 1.85 against an aligned mass
of 0.9885. Fine for comparing two poles; meaningless if summed over everything.

**FALLERS ARE NOT NULL-TESTED.** CANONICAL tests risers against the null and
fallers by a bare ratio. `movement.py` is explicit that nothing downstream may
call fallers "beyond renormalisation". A negative pole excess here says the pole
holds less than uniform scaling predicts; it does not certify each member fell
for a lexical reason.

**READ `residual_share`.** The null over a truncated support is approximate. On
the cop cell resid_base is 0.193 and resid_aligned 0.0115, so most of that cell's
inflation is the TAIL DRAINING into named words rather than fallers vacating --
a different mechanism, and the one `decompose`'s `tail_excess` names.
"""

import argparse
import collections
import json
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
sys.path.insert(0, HERE)

from malignment import ch                                          # noqa: E402
from malignment.ch import _lit                                     # noqa: E402
import rank as R                                                   # noqa: E402

OUT = os.path.join(HERE, "results", "rank_en5_multi.jsonl")


def cell_inflation(base, aligned, prompts):
    """{prompt: (inflation, resid_base, {word: (p_base, p_aligned, cls)})}, two queries.

    Mirrors `movement.pole_excess` exactly: residual on BOTH sides of R/S, which
    is `_movement`'s convention, so the two cannot disagree about what inflation
    means on the same cell.
    """
    keep = set(prompts)
    rows = ch.query(
        "SELECT prompt, word, p_base, p_aligned, cls FROM {db}.movement_v4 "
        "WHERE base=%s AND aligned=%s AND frame_base='' AND frame_aligned=''"
        % (_lit(base), _lit(aligned)))
    cells = ch.query(
        "SELECT prompt, resid_base FROM {db}.movement_cells_v4 "
        "WHERE base=%s AND aligned=%s" % (_lit(base), _lit(aligned)))
    resid = {r["prompt"]: float(r["resid_base"]) for r in cells}
    by = collections.defaultdict(dict)
    for r in rows:
        if r["prompt"] in keep:
            by[r["prompt"]][r["word"]] = (float(r["p_base"]), float(r["p_aligned"]),
                                          r["cls"])
    out = {}
    for p, d in by.items():
        rb = resid.get(p, 0.0)
        num = 1.0 - sum(pa for pb, pa, c in d.values() if c == "faller")
        den = sum(pb for pb, pa, c in d.values() if c != "faller") + rb
        out[p] = ((num / den) if den > 0 else 1.0, rb, d)
    return out


def pole(d, inflation, words):
    """(mass_base, mass_aligned, null, excess, n_present, n_fallers)."""
    ws = [w for w in set(words) if w in d]
    mb = sum(d[w][0] for w in ws)
    ma = sum(d[w][1] for w in ws)
    nu = sum(d[w][0] * inflation for w in ws)
    return mb, ma, nu, ma - nu, len(ws), sum(1 for w in ws if d[w][2] == "faller")


def build(limit=None):
    rows = [json.loads(l) for l in open(OUT) if l.strip()]
    by_pair = collections.defaultdict(list)
    for r in rows:
        by_pair[(r["base"], r["aligned"])].append(r)
    recs = []
    for base, aligned in R.PAIRS:
        g = by_pair.get((base, aligned), [])
        if not g:
            continue
        if limit:
            g = g[:limit]
        inf = cell_inflation(base, aligned, [r["prompt"] for r in g])
        for r in g:
            got = inf.get(r["prompt"])
            if not got:
                continue
            fl, rb, d = got
            for s in r.get("splits", []):
                mb, ma, mn, mx, nm, nf = pole(d, fl, s["marked"])
                ub, ua, un, ux, nu_, nfu = pole(d, fl, s["unmarked"])
                if nm == 0 or nu_ == 0:
                    continue
                recs.append(dict(prompt=r["prompt"], base=base, rel=s["relation"],
                                 inflation=fl, resid_base=rb,
                                 m_base=mb, m_aligned=ma, m_null=mn, m_excess=mx,
                                 u_base=ub, u_aligned=ua, u_null=un, u_excess=ux,
                                 n_marked=nm, n_unmarked=nu_, n_fall_marked=nf))
        print("  %-18s %d splits" % (base.split("/")[-1], len(recs)), flush=True)
    return recs


def verify(n=6):
    """The mirror against `movement.pole_excess` itself, on real cells."""
    from malignment import movement as MV
    rows = [json.loads(l) for l in open(OUT) if l.strip()]
    base, aligned = R.PAIRS[0]
    g = [r for r in rows if r["base"] == base and r.get("splits")][:n]
    inf = cell_inflation(base, aligned, [r["prompt"] for r in g])
    bad = 0
    for r in g:
        fl, rb, d = inf[r["prompt"]]
        s = r["splits"][0]
        mine = pole(d, fl, s["marked"])
        theirs = MV.pole_excess(base, aligned, r["prompt"], set(s["marked"]))
        ok = (abs(mine[0] - theirs["mass_base"]) < 1e-6
              and abs(mine[1] - theirs["mass_aligned"]) < 1e-6
              and abs(mine[2] - theirs["null"]) < 1e-6
              and abs(fl - theirs["inflation"]) < 1e-9)
        bad += not ok
        print("  %-5s infl %.4f/%.4f  null %.4f/%.4f  %r"
              % ("OK" if ok else "DIFFER", fl, theirs["inflation"],
                 mine[2], theirs["null"], r["prompt"][:44]))
    print("  %d of %d differ" % (bad, len(g)))
    return bad == 0


def report(recs):
    D = lambda x: x["u_excess"] - x["m_excess"]
    print("\nsplits with both poles present: %d" % len(recs))
    print("median inflation %.3f | median resid_base %.3f"
          % (st.median([x["inflation"] for x in recs]),
             st.median([x["resid_base"] for x in recs])))
    print("\nNULL-CORRECTED POLE EXCESS, mean over splits")
    print("  negative marked excess = the pole holds LESS than uniform scaling predicts")
    print("  %-18s %6s %9s %9s %9s" % ("relation", "n", "marked", "unmarked", "u - m"))
    g = collections.defaultdict(list)
    for x in recs:
        g[x["rel"]].append(x)
    for k, v in sorted(g.items(), key=lambda kv: -st.mean([D(x) for x in kv[1]])):
        print("  %-18s %6d %+9.4f %+9.4f %+9.4f"
              % (k, len(v), st.mean([x["m_excess"] for x in v]),
                 st.mean([x["u_excess"] for x in v]), st.mean([D(x) for x in v])))
    print("  %-18s %6d %+9.4f %+9.4f %+9.4f"
          % ("ALL", len(recs), st.mean([x["m_excess"] for x in recs]),
             st.mean([x["u_excess"] for x in recs]), st.mean([D(x) for x in recs])))
    print("\nBY LINEAGE")
    print("  %-18s %6s %9s %9s %9s %9s" % ("", "n", "marked", "unmarked", "u - m", "infl"))
    for base, _ in R.PAIRS:
        v = [x for x in recs if x["base"] == base]
        if not v:
            continue
        print("  %-18s %6d %+9.4f %+9.4f %+9.4f %9.3f"
              % (base.split("/")[-1], len(v), st.mean([x["m_excess"] for x in v]),
                 st.mean([x["u_excess"] for x in v]), st.mean([D(x) for x in v]),
                 st.median([x["inflation"] for x in v])))
    print("\nBY RELATION x LINEAGE (u - m)")
    print("  %-18s %s" % ("relation", " ".join("%9s" % b.split("/")[-1][:9]
                                               for b, _ in R.PAIRS)))
    for k in sorted(g, key=lambda k: -st.mean([D(x) for x in g[k]])):
        cells = []
        for b, _ in R.PAIRS:
            v = [x for x in g[k] if x["base"] == b]
            cells.append("%+9.4f" % st.mean([D(x) for x in v]) if v else "%9s" % "-")
        print("  %-18s %s" % (k, " ".join(cells)))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--where", action="store_true",
                    help="partition the excess: marked/unmarked/neutral/off/tail")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--out", default=os.path.join(HERE, "results", "pole_null.json"))
    a = ap.parse_args(argv)
    if a.verify:
        return 0 if verify() else 1
    if a.where:
        recs = destinations(a.limit)
        json.dump(recs, open(a.out.replace(".json", "_where.json"), "w"))
        report_destinations(recs)
        return
    recs = build(a.limit)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(recs, open(a.out, "w"))
    report(recs)
    print("\n-> %s" % a.out)




# ---------------------------------------------------------------------------
# WHERE DOES THE MASS GO? The zero-sum accounting.
# ---------------------------------------------------------------------------

def destinations(limit=None):
    """Excess partitioned over five buckets, per cell. Sums to ~0 by construction.

    The pole numbers say the marked pole loses and the unmarked pole sits at its
    null, which leaves the question this answers: where did it go.

    **OVER NON-FALLERS ONLY, AND THAT IS WHAT MAKES IT A PARTITION.** `sum(null)`
    over non-fallers plus the tail equals R, and `sum(Q)` over the same set equals
    R too, so the excesses cancel exactly. Including fallers would answer the
    other question -- how much the marked pole lost -- and would not sum to zero.
    `departed` is reported separately for that.

    The buckets:

        marked / unmarked   the cell's poles, unanimous-reduced
        neutral             candidate words (>=1% in either arm, content, ADV
                            stoplisted) that no split placed in a pole
        off_candidate       words movement_v4 scores that never entered the
                            candidate list -- function words, sub-1% words. NOT a
                            residual: these are named and resolvable.
        tail                the __TAIL__ residual. Mass the instrument cannot see
                            inside at all.
    """
    rows = [json.loads(l) for l in open(OUT) if l.strip()]
    by_pair = collections.defaultdict(list)
    for r in rows:
        by_pair[(r["base"], r["aligned"])].append(r)
    out = []
    for base, aligned in R.PAIRS:
        g = by_pair.get((base, aligned), [])
        if limit:
            g = g[:limit]
        if not g:
            continue
        inf = cell_inflation(base, aligned, [r["prompt"] for r in g])
        cand = R.cells_bulk([r["prompt"] for r in g], base, aligned)
        resid_a = {x["prompt"]: float(x["resid_aligned"]) for x in ch.query(
            "SELECT prompt, resid_aligned FROM {db}.movement_cells_v4 "
            "WHERE base=%s AND aligned=%s" % (_lit(base), _lit(aligned)))}
        for r in g:
            got, c = inf.get(r["prompt"]), cand.get(r["prompt"])
            if not got or not c:
                continue
            fl, rb, d = got
            ra = resid_a.get(r["prompt"], 0.0)
            cw = set(c[0])
            mk, un = set(r["naughty"]) & cw, set(r["nice"]) & cw
            neu = cw - mk - un
            off = set(d) - cw
            nonf = {w for w, (pb, pa, cl) in d.items() if cl != "faller"}
            exc = lambda S: sum(d[w][1] - d[w][0] * fl for w in (S & nonf) if w in d)
            dep = sum(d[w][0] - d[w][1] for w, (pb, pa, cl) in d.items()
                      if cl == "faller")
            out.append(dict(
                prompt=r["prompt"], base=base, inflation=fl,
                marked=exc(mk), unmarked=exc(un), neutral=exc(neu),
                off_candidate=exc(off), tail=ra - rb * fl,
                departed=dep,
                n_fall=sum(1 for _, (pb, pa, cl) in d.items() if cl == "faller")))
        print("  %-18s %d cells" % (base.split("/")[-1], len(out)), flush=True)
    return out


def report_destinations(recs):
    """**CONDITIONED, BECAUSE THE MEAN OVER EVERY CELL ANSWERS NOTHING.** Most
    prompts have no charge and no reason for mass to move anywhere in particular;
    averaging their excess in with the frames that do move reports the corpus's
    composition, not a mechanism. The bands are on `departed` -- how much mass
    actually left the fallers -- which is a property of the cell and not of any
    pole, so it does not select on the quantity being partitioned."""
    B = ("marked", "unmarked", "neutral", "off_candidate", "tail")
    tot = [sum(x[b] for b in B) for x in recs]
    print("\nZERO-SUM CHECK: the five buckets should cancel over non-fallers")
    print("  mean %+.2e | max |sum| %.2e over %d cells" %
          (st.mean(tot), max(abs(t) for t in tot), len(recs)))
    print("\nWHERE THE REDISTRIBUTED MASS GOES, mean excess per cell")
    for b in B:
        v = [x[b] for x in recs]
        print("  %-15s %+.4f   (positive on %d of %d cells)"
              % (b, st.mean(v), sum(1 for x in v if x > 0), len(v)))
    print("  %-15s %+.4f   <- mass that LEFT the fallers, not part of the sum"
          % ("departed", st.mean([x["departed"] for x in recs])))
    print("\nBY HOW MUCH MASS ACTUALLY LEFT THE FALLERS")
    print("  %-16s %6s %8s %9s %9s %13s %8s"
          % ("departed", "n", "marked", "unmarked", "neutral", "off_candidate", "tail"))
    bands = [(0.0, 0.01, "< 0.01"), (0.01, 0.05, "0.01-0.05"),
             (0.05, 0.15, "0.05-0.15"), (0.15, 0.30, "0.15-0.30"),
             (0.30, 9.99, "> 0.30")]
    for lo, hi, lab in bands:
        v = [x for x in recs if lo <= x["departed"] < hi]
        if not v:
            continue
        print("  %-16s %6d %+8.4f %+9.4f %+9.4f %+13.4f %+8.4f"
              % (lab, len(v), *(st.mean([x[b] for x in v]) for b in B)))
    print("\nBY LINEAGE")
    print("  %-18s %8s %9s %9s %13s %8s %9s"
          % ("", "marked", "unmarked", "neutral", "off_candidate", "tail", "departed"))
    for base, _ in R.PAIRS:
        v = [x for x in recs if x["base"] == base]
        if not v:
            continue
        print("  %-18s %+8.4f %+9.4f %+9.4f %+13.4f %+8.4f %+9.4f"
              % (base.split("/")[-1], *(st.mean([x[b] for x in v]) for b in B),
                 st.mean([x["departed"] for x in v])))


if __name__ == "__main__":
    sys.exit(main() or 0)
