"""Score the pilot's two arms and compare them. One stem, one model.

    python .../frame_pilot_score.py                       # every model present
    python .../frame_pilot_score.py --model Qwen/...

Reads `results/frame_pilot/*.json`, scores every passage through
`malignment.score` -- which is content-addressed, so a rerun is a lookup and a
passage that appears in two pilots is scored once -- and reports the arm
difference on both axes.

## THE INTERVAL IS OVER PASSAGES AND THAT BOUNDS THE CLAIM

100 draws of ONE stem. The bootstrap below resamples passages, so it estimates
"this model, this stem" and says nothing about models or about stems. Stem is
the largest variance component in this corpus (ICC by stem 0.417-0.433 for the
API models), so a frame effect measured on one scene is a pilot for the
machinery and a first read on magnitude -- not evidence about the frame in
general. `frame_eligibility.py` carries the powered design.

## LENGTH IS REPORTED FIRST, BECAUSE THE FRAME MOVES IT

The smoke run showed the API frame cutting SmolLM2-360M to a median 32 new
tokens against raw's 256: asked to write 200-250 words, a small model answers
briefly and stops. Drift needs sentences, so a frame that shortens the passage
changes the drift axis through length before it changes anything about
trajectory. Any drift difference has to be read against the length difference
sitting beside it, which is why both are in the same table and why `n_sents`
is there too.
"""

import argparse, glob, json, os, random, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
#: the pilot's own decoder, so a draw made at another max_new_tokens is not
#: counted as this run's. Must match frame_pilot.py, which uses the module
#: default.
from malignment.generate import DECODER as DEC                 # noqa: E402
from generate_task import SYSTEM_PROMPT                        # noqa: E402


def _models_with_generations():
    """Every checkpoint with a generations stash on this machine. -> [model_id]

    The stash directory IS the index; nothing keeps a separate manifest of what
    has been generated, so nothing can disagree with it.
    """
    from malignment.generate import GEN_OUT
    if not os.path.isdir(GEN_OUT):
        return []
    return [d.replace("__at__", "@").replace("__", "/", 1)
            for d in sorted(os.listdir(GEN_OUT))
            if os.path.isdir(os.path.join(GEN_OUT, d))]


def boot(a, b, n=2000, seed=20260821):
    """95% CI on median(a) - median(b), resampling passages. -> (lo, hi)"""
    rng = random.Random(seed)
    d = []
    for _ in range(n):
        d.append(statistics.median(rng.choices(a, k=len(a)))
                 - statistics.median(rng.choices(b, k=len(b))))
    d.sort()
    return d[int(0.025 * n)], d[int(0.975 * n)]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--model")
    ap.add_argument("--m", type=int, default=200, help="surprisal prefix, tokens")
    ap.add_argument("--stem", default="She was ugly and misshapen and she wanted to")
    a = ap.parse_args(argv)
    from malignment import Passage, score, score_all

    from malignment import Checkpoint
    models = [a.model] if a.model else _models_with_generations()
    if not models:
        raise SystemExit("no generations cached; run frame_pilot.py first")

    for mid in models:
        ck = Checkpoint(mid)
        #: SELECT THE PILOT'S CONDITION EXACTLY, not "anything not raw".
        #: The stash holds every generation this checkpoint has ever made here,
        #: including smoke tests at other stems and other decoders. Splitting on
        #: `frame != "raw"` swept 7 test draws into the api arm on the first run
        #: -- a population that does not contain only the case.
        arms = {
            "raw": [p for p in ck.generations(prompt=a.stem, frame="raw")
                    if p.decoder == DEC],
            #: **TWO SELECTORS, AND THE REASON IS DATED.** Records written
            #: after 2026-08-21 carry the system prompt IN FULL on the key and
            #: are selected by its text. This pilot's api arm was written
            #: minutes BEFORE that change, under a key that carried only
            #: `system_sha`, so its text is not addressable -- those rows are
            #: selected by `frame="chat_sys"` instead, which is exact HERE
            #: because the pilot ran one system condition per model at this stem
            #: and decoder. It would not be exact in general, and a later run
            #: should use the text selector alone.
            "api": [p for p in ck.generations(prompt=a.stem, system=SYSTEM_PROMPT)
                    if p.decoder == DEC]
                   or [p for p in ck.generations(prompt=a.stem, frame="chat_sys")
                       if p.decoder == DEC],
        }
        if not any(arms.values()):
            continue
        print("\n%s | stem %r" % (mid, a.stem[:46]))
        #: ONE PASS PER INSTRUMENT over every passage in both arms, so the
        #: per-passage properties below are lookups. Scoring by property in a
        #: loop would interleave the two models and load each repeatedly.
        score_all([p for v in arms.values() for p in v], m=a.m)

        rows = {}
        for arm, ps in arms.items():
            rows[arm] = {
                "n": len(ps),
                "new_tokens": [p.n_new_tokens for p in ps],
                "n_sents": [p.n_sents for p in ps],
                #: surprisal at a COMMON PREFIX; a passage too short for it is
                #: None and is dropped from that column only, with the count
                #: shown -- the frame changes length, so differential dropping
                #: is itself part of the result and must be visible.
                "surprisal": [x for x in (p.surprisal_at(a.m) for p in ps)
                              if x is not None],
                "drift": [x for x in (p.drift for p in ps) if x is not None],
            }
        print("  %-12s %8s %10s %10s %12s %12s"
              % ("arm", "n", "med tok", "med sents", "surp(M=%d)" % a.m, "drift"))
        for arm in ("raw", "api"):
            r = rows.get(arm)
            if not r:
                continue
            print("  %-12s %8d %10.0f %10.1f %6.4f (%3d) %6.4f (%3d)"
                  % (arm, r["n"], statistics.median(r["new_tokens"]),
                     statistics.median(r["n_sents"]),
                     statistics.median(r["surprisal"]) if r["surprisal"] else float("nan"),
                     len(r["surprisal"]),
                     statistics.median(r["drift"]) if r["drift"] else float("nan"),
                     len(r["drift"])))
        if "raw" in rows and "api" in rows:
            print("  %-12s" % "api - raw", end="")
            for k in ("surprisal", "drift"):
                A, B = rows["api"][k], rows["raw"][k]
                if not A or not B:
                    print("  %s: no overlap" % k, end=""); continue
                dd = statistics.median(A) - statistics.median(B)
                lo, hi = boot(A, B)
                print("   %s %+0.4f [%+0.4f, %+0.4f]" % (k, dd, lo, hi), end="")
            print()
            #: SAY IT when the prefix drops one arm much harder than the other.
            ra, rr = len(rows["api"]["surprisal"]), len(rows["raw"]["surprisal"])
            if min(ra, rr) < 0.8 * max(ra, rr):
                print("  ** the M=%d prefix retains %d of %d api and %d of %d raw."
                      % (a.m, ra, rows["api"]["n"], rr, rows["raw"]["n"]))
                print("     The surviving passages are LENGTH-SELECTED and the "
                      "surprisal row is\n     a comparison between two "
                      "differently-selected populations.")


if __name__ == "__main__":
    main()
