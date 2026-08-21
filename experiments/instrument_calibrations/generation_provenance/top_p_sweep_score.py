"""Score the top_p sweep: which way does truncation move drift?

    python .../top_p_sweep_score.py
    python .../top_p_sweep_score.py --k 5

Reads the generations stash, selects each top_p condition by its EXACT key, and
reports both axes against the `top_p=1.0` baseline.

## THE SHAPE OF THE ANSWER MATTERS AS MUCH AS THE SIGN

Four points, not two, because the mechanisms in `top_p_sweep.py` predict
different shapes and a two-point test cannot tell them apart:

    monotone DOWN      truncation lowers step-to-step drift; the argument that
                       our API drift result survives this confound holds
    monotone UP        the ballistic/scaffolding mechanism reaches `mean_drift`
                       and the confound points WITH our effect, not against it
    down then up, or   the two mechanisms trade places at different depths, and
    up then down       no single-signed correction exists at all -- which would
                       be the worst case for us, since a vendor default could
                       sit on either side of the turn

The last is why 0.7 is in the sweep. A reader who sees only 1.0 and 0.9 cannot
distinguish "flat" from "turning".

## SURPRISAL IS THE MANIPULATION CHECK, NOT A RESULT

Nucleus truncation removes tail mass, so it MUST lower reference surprisal. If it
does not, the parameter did not take and nothing else in the table means
anything. It is reported first for that reason.
"""

import argparse, collections, math, os, random, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
sys.path.insert(0, HERE)
from top_p_sweep import TOP_PS, STEM, SEED           # noqa: E402


def boot(a, b, n=2000, seed=20260821):
    rng = random.Random(seed)
    d = sorted(statistics.median(rng.choices(a, k=len(a)))
               - statistics.median(rng.choices(b, k=len(b))) for _ in range(n))
    return d[int(0.025 * n)], d[int(0.975 * n)]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--m", type=int, default=64)
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--stem", default=STEM)
    ap.add_argument("--model")
    a = ap.parse_args(argv)
    from malignment import Checkpoint, score_all
    from malignment.generate import GEN_OUT, DECODER

    models = ([a.model] if a.model else
              [d.replace("__at__", "@").replace("__", "/", 1)
               for d in sorted(os.listdir(GEN_OUT))
               if os.path.isdir(os.path.join(GEN_OUT, d))])

    for mid in models:
        ck = Checkpoint(mid)
        arms = {}
        for tp in TOP_PS:
            want = dict(DECODER); want["top_p"] = tp
            #: EXACT key match on the decoder, so a passage made at another
            #: top_p or another max_new_tokens cannot enter this cell.
            arms[tp] = [p for p in ck.generations(prompt=a.stem, frame="raw")
                        if p.decoder == want and p.seed is not None]
        if not any(arms.values()):
            continue
        print("\n%s | stem %r" % (mid, a.stem[:44]))
        score_all([p for v in arms.values() for p in v], m=a.m)

        rows = {}
        for tp, ps in arms.items():
            if not ps:
                continue
            rows[tp] = {
                "n": len(ps),
                "tok": [p.n_new_tokens for p in ps],
                "sents": [p.n_sents for p in ps],
                "surp": [x for x in (p.surprisal_at(a.m) for p in ps) if x is not None],
                "drift": [x for x in (p.drift for p in ps) if x is not None],
                "drift_k": [x for x in (p.drift_at(a.k) for p in ps) if x is not None],
            }
        base = rows.get(1.0)
        print("  %-7s %5s %8s %9s %12s %12s %12s"
              % ("top_p", "n", "med tok", "med sents", "surp(M=%d)" % a.m,
                 "drift", "drift(k=%d)" % a.k))
        for tp in sorted(rows, reverse=True):
            r = rows[tp]
            med = lambda c: (statistics.median(r[c]) if r[c] else float("nan"))
            print("  %-7s %5d %8.0f %9.1f %6.4f (%3d) %6.4f (%3d) %6.4f (%3d)"
                  % (tp, r["n"], statistics.median(r["tok"]),
                     statistics.median(r["sents"]),
                     med("surp"), len(r["surp"]), med("drift"), len(r["drift"]),
                     med("drift_k"), len(r["drift_k"])))
        if not base:
            print("  (no top_p=1.0 baseline in the stash)")
            continue
        print("  %-7s %s" % ("", "vs top_p=1.0:"))
        for tp in sorted(rows, reverse=True):
            if tp == 1.0:
                continue
            r = rows[tp]
            out = []
            for col in ("surp", "drift", "drift_k"):
                A, B = r[col], base[col]
                if not A or not B:
                    out.append("%s --" % col); continue
                d = statistics.median(A) - statistics.median(B)
                lo, hi = boot(A, B)
                star = "*" if (lo > 0) == (hi > 0) else " "
                out.append("%s %+0.4f [%+0.4f,%+0.4f]%s" % (col, d, lo, hi, star))
            print("  %-7s %s" % (tp, "   ".join(out)))
    print("\n* = the 95%% bootstrap CI excludes zero. Surprisal is the "
          "MANIPULATION CHECK:\nif truncation did not lower it, the parameter "
          "did not take and no other column means anything.")


if __name__ == "__main__":
    main()
