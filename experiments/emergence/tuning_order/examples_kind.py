"""What does the transgressiveness null LOOK like? Matched NONE and SEXUAL cases.

    python -u examples_kind.py
    python -u examples_kind.py --kind VIOLENT

**DISCOVERED / QUALITATIVE.** Not a test. Q2 and Q3 both returned nulls: charge
does not modulate the departure-before-arrival lag at either grain, and by kind
the lags are NONE +4,865, SEXUAL +5,651, VIOLENT +5,687. This file exists to see
what that sameness actually looks like on the page, by putting a SEXUAL faller
and a NONE faller with nearly identical timing side by side.

Prompts are printed IN FULL. A truncated prompt is not a case.
"""
import argparse, collections, json, os, statistics as S, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
from malignment import ch                                          # noqa: E402
from timing import timings, charge                                 # noqa: E402
from analyse import END                                            # noqa: E402

SHOW = [1000, 2000, 3000, 5000, 8000, 12000, 20000, 30000, 43000]


def masses(pairs):
    inl = ",".join("(%s,%s)" % (ch._lit(p), ch._lit(w)) for p, w in pairs)
    q = ("SELECT prompt, word, step_aligned, p_base, p_aligned "
         "FROM {db}.movement_rungs WHERE kind='base_rooted' "
         "AND (prompt, word) IN (%s)" % inl)
    out, base = collections.defaultdict(dict), {}
    for r in ch.query(q):
        k = (r["prompt"], r["word"])
        out[k][int(r["step_aligned"])] = float(r["p_aligned"])
        base[k] = float(r["p_base"])
    return out, base


def show(tag, p, w, tm, ser, base, risers):
    print("  %s  t_move=%.0f" % (tag, tm))
    print("    PROMPT: %s" % p.replace("\n", "\\n"))
    print("    %-14s %8s %s" % ("word", "base",
                                " ".join("%7d" % s for s in SHOW)))
    s = ser.get((p, w), {})
    print("    %-14s %8.4f %s" % ("F " + w, base.get((p, w), 0.0),
                                  " ".join("%7.4f" % s.get(k, float("nan"))
                                           for k in SHOW)))
    for rw, rtm in risers[:3]:
        s = ser.get((p, rw), {})
        print("    %-14s %8.4f %s   t=%.0f"
              % ("R " + rw, base.get((p, rw), 0.0),
                 " ".join("%7.4f" % s.get(k, float("nan")) for k in SHOW), rtm))
    print()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--kind", default="SEXUAL")
    ap.add_argument("--n", type=int, default=4)
    a = ap.parse_args(argv)

    t = timings()
    ch_ = charge()
    tm = {(p, w): x for p, w, c, x in t}
    risers = collections.defaultdict(list)
    for p, w, c, x in t:
        if c == "riser":
            risers[p].append((w, x))
    for p in risers:
        risers[p].sort(key=lambda z: z[1])

    F = [(p, w, x) for p, w, c, x in t
         if c == "faller" and ch_.get((p, w)) and ch_[(p, w)][0] == a.kind]
    N = [(p, w, x) for p, w, c, x in t
         if c == "faller" and ch_.get((p, w)) and ch_[(p, w)][0] == "NONE"]
    print("%s fallers %d | NONE fallers %d" % (a.kind, len(F), len(N)))
    print("median t_move: %s %.0f | NONE %.0f"
          % (a.kind, S.median([x for _, _, x in F]),
             S.median([x for _, _, x in N])))
    print()

    #: match each charged faller to the NONE faller closest in timing, so the
    #: pair differs in KIND and in almost nothing else
    used, pairs = set(), []
    for p, w, x in sorted(F, key=lambda z: z[2])[::max(1, len(F) // a.n)][:a.n]:
        cand = [c for c in N if (c[0], c[1]) not in used]
        if not cand:
            break
        best = min(cand, key=lambda c: abs(c[2] - x))
        used.add((best[0], best[1]))
        pairs.append(((p, w, x), best))

    want = []
    for (p1, w1, _), (p2, w2, _) in pairs:
        want += [(p1, w1), (p2, w2)]
        want += [(p1, r) for r, _ in risers[p1][:3]]
        want += [(p2, r) for r, _ in risers[p2][:3]]
    ser, base = masses(want)

    for (p1, w1, x1), (p2, w2, x2) in pairs:
        print("=" * 104)
        print("MATCHED ON TIMING: %s t=%.0f against NONE t=%.0f  (gap %.0f steps)"
              % (a.kind, x1, x2, abs(x1 - x2)))
        print("=" * 104)
        show("[%s]" % a.kind, p1, w1, x1, ser, base, risers[p1])
        show("[NONE]  ", p2, w2, x2, ser, base, risers[p2])
    return 0


if __name__ == "__main__":
    sys.exit(main())
