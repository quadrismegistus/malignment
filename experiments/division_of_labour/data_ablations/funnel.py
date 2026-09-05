"""Which SFT corpus installs the funnel toward SPEECH?

`existence/field_matrix.py` establishes that freed mass leaves the faller's own
USAS field and routes to a small destination set -- linguistic acts is in the top
5 for 17 of 18 source domains -- and that under lift the funnel narrows toward
speech (37/11 lineages) and away from social action (11/36).

`semantics.py` reports the MARGINAL field composition per ablation arm, which is
a different quantity: "the speech share of riser mass rose" does not say that a
given faller's mass went to speech. This runs the CONDITIONAL version per arm.

THE BASELINE IS THE WHOLE QUESTION, as in `field_matrix.py`. Against a global
base rate the diagonal dominates and that is prompt composition, not routing.
The denominator here is the base distribution's own mass over that cell's
candidates, so the ratio asks whether mass went to a domain MORE than that
prompt's own vocabulary made likely.

THE UNIT IS THE PROMPT. Each arm is one checkpoint, so there is no lineage
replication; arms are compared paired within prompt, never as two means.

    python -m experiments.division_of_labour.data_ablations.funnel
"""
import collections
import math

from malignment import ch, charge, fields
from .jaccard_lift import edge_where, BASE, FULL, ABLATIONS

NAMES = {"Q": "linguistic acts", "X": "psychological", "S": "social",
         "B": "the body", "E": "emotion", "M": "movement"}
_U = {}


def dom(w):
    if w not in _U:
        try:
            _U[w] = frozenset(c[0] for c in (fields.usas(w, names=False) or ()) if c)
        except Exception:
            _U[w] = frozenset()
    return _U[w]


def sign_test(ds):
    up = sum(1 for d in ds if d > 0)
    dn = sum(1 for d in ds if d < 0)
    t = up + dn
    if not t:
        return up, dn, 1.0
    k = min(up, dn)
    return up, dn, min(1.0, 2 * sum(math.comb(t, i) for i in range(k + 1)) / 2 ** t)


def enrich(model, edge, targets=("Q", "X", "S")):
    """{prompt: {target: enrichment}} -- riser share over availability share."""
    rows = ch.query(
        "SELECT prompt, word, p_base, (p_aligned-p_base) AS delta, cls "
        "FROM movement_v4 WHERE %s" % edge_where(model, edge), limit_bytes=None)
    cells = collections.defaultdict(list)
    for r in rows:
        cells[r["prompt"]].append(r)
    out = {}
    for q, wr in cells.items():
        ri = [(r["word"], float(r["delta"])) for r in wr if r["cls"] == "riser"]
        rt = sum(d for _, d in ri)
        if rt <= 0:
            continue
        av = collections.Counter()
        at = 0.0
        for r in wr:
            pb = float(r["p_base"])
            T = dom(r["word"])
            if not T:
                continue
            at += pb
            for t in T:
                av[t] += pb / len(T)
        if at <= 0:
            continue
        obs = collections.Counter()
        for w, d in ri:
            T = dom(w)
            if not T:
                continue
            for t in T:
                obs[t] += (d / rt) / len(T)
        rec = {}
        for t in targets:
            a = av[t] / at
            if a > 0.005:
                rec[t] = obs[t] / a
        if rec:
            out[q] = rec
    return out


def main(edge="raw"):
    lift = {p: float(v) for (p, b), v in charge.lifts_per_lineage(BASE).items()}
    arms = {"full": enrich(FULL, edge)}
    for name, m in ABLATIONS:
        arms[name] = enrich(m, edge)
    shared = set(arms["full"])
    for v in arms.values():
        shared &= set(v)
    shared = sorted(shared)

    print("WHICH ABLATION CHANGES THE FUNNEL?   [edge=%s]" % edge)
    print("enrichment = riser mass share of a domain / that domain's share of")
    print("the base distribution IN THE SAME CELL. unit = the prompt.")
    print("n = %d prompts covered by all five arms\n" % len(shared))

    for tgt in ("Q", "X", "S"):
        ps = [p for p in shared if tgt in arms["full"][p]
              and all(tgt in arms[n][p] for n, _ in ABLATIONS)]
        if len(ps) < 30:
            print("%s %-18s  n=%d, too few" % (tgt, NAMES[tgt], len(ps)))
            continue
        base = sum(arms["full"][p][tgt] for p in ps) / len(ps)
        print("%s %-18s  full mix enrichment %.3f   over %d prompts"
              % (tgt, NAMES[tgt], base, len(ps)))
        for name, _m in ABLATIONS:
            ds = [arms[name][p][tgt] - arms["full"][p][tgt] for p in ps]
            up, dn, pv = sign_test(ds)
            star = "*" if pv < 0.01 else (":" if pv < 0.05 else " ")
            print("    %-14s %+8.4f %9s  p=%.5f%s"
                  % (name, sum(ds) / len(ds), "%d/%d" % (up, dn), pv, star))
        print()

    print("DOSED. The same contrast inside lift bands, target Q only.")
    print("%-14s %10s %10s %10s" % ("removed", "L-lo", "L-mid", "L-hi"))
    bands = {"L-lo": [], "L-mid": [], "L-hi": []}
    for p in shared:
        v = lift.get(p)
        if v is None:
            continue
        bands["L-lo" if v < 0.5 else ("L-mid" if v < 1.2 else "L-hi")].append(p)
    for name, _m in ABLATIONS:
        line = "%-14s" % name
        for b in ("L-lo", "L-mid", "L-hi"):
            ps = [p for p in bands[b]
                  if "Q" in arms["full"][p] and "Q" in arms[name][p]]
            if len(ps) < 30:
                line += "%10s" % ("n=%d" % len(ps))
                continue
            ds = [arms[name][p]["Q"] - arms["full"][p]["Q"] for p in ps]
            up, dn, pv = sign_test(ds)
            star = "*" if pv < 0.01 else (":" if pv < 0.05 else "")
            line += "%9.3f%s" % (sum(ds) / len(ds), star)
        print(line)
    print("\n  * p<0.01  : p<0.05   sign test over prompts, paired by prompt id")
    print("  positive = the ABLATED arm funnels to that domain MORE than full")


if __name__ == "__main__":
    import sys
    e = "raw"
    if "--edge" in sys.argv:
        e = sys.argv[sys.argv.index("--edge") + 1]
    main(e)
