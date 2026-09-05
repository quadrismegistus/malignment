"""Re-ask 197's question with the selector that works.

`malign-logits` `meta/M01_displacement/findings/DISPLACEMENT_EVIDENCE.md` 197
found `no-wildchat` categorically unlike the other three SFT ablations on WHICH
words move -- faller Jaccard against full 0.340 where the others sit at
0.522-0.534 -- and then tested whether that divergence was about transgression by
splitting prompts neutral vs transgressive. It came out FLAT (neutral 0.3656,
transgressive 0.3235), and 197 concluded "a generally unusual training run, not
one that differs where desire is at stake."

THAT SPLIT IS THE WRONG INSTRUMENT. It is a `dose`-LEVEL contrast, and
`malignment/charge.py` documents dose as the wrong selector because the response
saturates: frames rated 5-7 carry the highest dose and show essentially zero
response, so a "transgressive" arm selects INTO the flat region. Headroom runs
+0.38 at frame 2-3 down to -0.05 at frame 6-7 (`readout_share` 208) -- the most
charged prompts have nowhere to displace to. A flat result across that split is
what saturation predicts whether or not the effect exists.

    corr(effect, dose)  -0.091      the level, saturating
    corr(effect, lift)  -0.261      the increment, and -0.311 unsaturated

So this recomputes 197's OWN OUTCOME -- faller Jaccard divergence from full, on
the raw base -> arm edge, no frames anywhere -- against LIFT rather than against
the binary split. If `no-wildchat` diverges from full specifically where charge
is at stake, the divergence should track lift. If 197's conclusion holds up on
the better instrument, it will not.

The mean Jaccard column is the check that this is the same measurement 197 made:
it should land near 0.34 for no-wildchat and 0.52-0.53 for the others.

THREE EDGES. `--edge raw` is `base_raw -> arm_raw`, the original. `--edge framed`
is `base_raw -> arm_framed` on the clean-slot population. `--edge self` is
`arm_raw -> arm_framed` with base == aligned: the frame alone, on weights nobody
touched, which asks whether the training corpus changed what the TEMPLATE moves.

On self-edges the model is its own base and has no lift of its own, so the
family base's lift is used -- the same convention `ladder.py` uses for
intermediate checkpoints, and it is constant across arms so it cannot carry an
arm difference.

    python -m experiments.division_of_labour.data_ablations.jaccard_lift
    python -m experiments.division_of_labour.data_ablations.jaccard_lift --edge framed
    python -m experiments.division_of_labour.data_ablations.jaccard_lift --edge self
"""
import math

from malignment import ch, charge
from malignment.ch import _lit

BASE = "meta-llama/Llama-3.1-8B"
FULL = "allenai/Llama-3.1-Tulu-3-8B-SFT"
ABLATIONS = [
    ("no-math", "allenai/Llama-3.1-Tulu-3-8B-SFT-no-math-data"),
    ("no-persona", "allenai/Llama-3.1-Tulu-3-8B-SFT-no-persona-data"),
    ("no-safety", "allenai/Llama-3.1-Tulu-3-8B-SFT-no-safety-data"),
    ("no-wildchat", "allenai/Llama-3.1-Tulu-3-8B-SFT-no-wildchat-data"),
]


def ols_t(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0:
        return float("nan"), float("nan")
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    a = my - b * mx
    rss = sum((y - (a + b * x)) ** 2 for x, y in zip(xs, ys))
    return b, b / math.sqrt(rss / (n - 2) / sxx)


_MODES = None


def _framed_mode(model):
    """system_mode the clean-slot rule assigns this pair. See framed_population.py."""
    global _MODES
    if _MODES is None:
        from malignment import movement
        _MODES = {(b, a): m for b, a, m in movement.clean_frame_pairs()}
    m = _MODES.get((BASE, model))
    if m is None:
        raise SystemExit("%s is not in the clean-slot framed population" % model)
    return m


def edge_where(model, edge):
    """SQL predicate selecting one edge for one arm.

    NOT `frame_aligned='prefill'` alone for the framed edge: `system_mode`
    records the argument passed, not the treatment received, so the mode has to
    come from `clean_frame_pairs`.
    """
    if edge == "raw":
        return ("base=%s AND aligned=%s AND frame_base='' AND frame_aligned=''"
                % (_lit(BASE), _lit(model)))
    if edge == "framed":
        return ("base=%s AND aligned=%s AND frame_base='' "
                "AND frame_aligned='prefill' AND system_mode_aligned=%s"
                % (_lit(BASE), _lit(model), _lit(_framed_mode(model))))
    if edge == "self":
        return ("base=%s AND aligned=%s AND base=aligned" % (_lit(model), _lit(model)))
    raise SystemExit("unknown edge: %s" % edge)


def fallers(model, edge="raw"):
    """{prompt: frozenset(words that lost mass)} on the requested edge."""
    rows = ch.query(
        "SELECT prompt, groupArray(word) ws FROM movement_v4 WHERE %s "
        "AND cls='faller' GROUP BY prompt" % edge_where(model, edge))
    return {r["prompt"]: frozenset(r["ws"]) for r in rows}


def jac(a, b):
    u = a | b
    return len(a & b) / len(u) if u else None


def main(edge="raw"):
    #: BASE's lift for every edge, self included: on a self-edge the model is its
    #: own base and has no lift entry, and the family base's lift is constant
    #: across arms so it cannot manufacture an arm difference.
    lift = {p: float(v) for (p, b), v in charge.lifts_per_lineage(BASE).items()}
    arms = {"full": fallers(FULL, edge)}
    for name, m in ABLATIONS:
        arms[name] = fallers(m, edge)

    shared = set(arms["full"])
    for name in arms:
        shared &= set(arms[name])
    shared = sorted(p for p in shared if p in lift)

    print("197's OUTCOME, RECOMPUTED AGAINST LIFT   [edge=%s]" % edge)
    print("faller Jaccard vs full.")
    print("n = %d prompts carrying a lift\n" % len(shared))

    print("%-12s %10s %12s %8s   %s"
          % ("arm", "mean J", "d J / lift", "t", "197 reported"))
    ref = {"no-math": 0.528, "no-persona": 0.522, "no-safety": 0.534,
           "no-wildchat": 0.340}
    for name, _m in ABLATIONS:
        js, xs = [], []
        for p in shared:
            v = jac(arms[name][p], arms["full"][p])
            if v is not None:
                js.append(v)
                xs.append(lift[p])
        b, t = ols_t(xs, js)
        print("%-12s %10.4f %12.5f %8.1f   %.3f"
              % (name, sum(js) / len(js), b, t, ref[name]))

    print("\n  mean J is the reproduction check against 197.")
    print("  d J / lift is the new quantity: does the divergence TRACK charge?")

    OTH = ["no-math", "no-persona", "no-safety"]
    xs, ys = [], []
    for p in shared:
        jw = jac(arms["no-wildchat"][p], arms["full"][p])
        jo = [jac(arms[o][p], arms["full"][p]) for o in OTH]
        if jw is None or any(v is None for v in jo):
            continue
        xs.append(lift[p])
        ys.append(jw - sum(jo) / len(jo))
    b, t = ols_t(xs, ys)
    print("\nPAIRED CONTRAST, same prompt: J(no-wildchat) - mean J(other three)")
    print("  n = %d   mean gap = %.4f" % (len(xs), sum(ys) / len(ys)))
    print("  slope vs lift = %+.5f   t = %.1f" % (b, t))

    fr = {q: d["frame"] for q, d in charge.index()["prompts"].items()
          if d.get("frame") is not None}
    print("\n  SPLIT BY SATURATION (readout_share 208: effect peaks frames 2-4,")
    print("  headroom +0.38 at frame 2-3 falling to -0.05 at frame 6-7)")
    for (lo, hi), lab in (((0, 4.999), "frame 2-4.99"), ((5, 9), "frame 5+")):
        sx = [(x, y) for x, y, q in zip(xs, ys, shared)
              if q in fr and lo <= fr[q] <= hi]
        if len(sx) < 30:
            print("  %-12s n=%d, too few" % (lab, len(sx)))
            continue
        bb, tt = ols_t([a for a, _ in sx], [c for _, c in sx])
        print("  %-12s n=%4d  gap %.4f  slope %+.5f  t=%.1f"
              % (lab, len(sx), sum(c for _, c in sx) / len(sx), bb, tt))

    print("\nDENOMINATOR CONTROL -- Jaccard is a ratio, so check the union moves")
    print("%-12s %9s %11s %7s   %9s %11s %7s"
          % ("arm", "mean|U|", "d|U|/lift", "t", "mean|I|", "d|I|/lift", "t"))
    xs2 = [lift[q] for q in shared]
    for name, _m in ABLATIONS:
        U = [len(arms[name][q] | arms["full"][q]) for q in shared]
        I = [len(arms[name][q] & arms["full"][q]) for q in shared]
        bu, tu = ols_t(xs2, U)
        bi, ti = ols_t(xs2, I)
        print("%-12s %9.1f %11.4f %7.1f   %9.1f %11.4f %7.1f"
              % (name, sum(U) / len(U), bu, tu, sum(I) / len(I), bi, ti))
    print("  union flat everywhere => the Jaccard slope is in the NUMERATOR.")


if __name__ == "__main__":
    import sys
    e = "raw"
    if "--edge" in sys.argv:
        e = sys.argv[sys.argv.index("--edge") + 1]
    main(e)
