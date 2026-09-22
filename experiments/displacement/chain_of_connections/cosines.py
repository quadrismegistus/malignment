"""Cosine to `kill` directly, instead of hop counts derived from it.

    python cosines.py                  -> both spaces, centred
    python cosines.py --space bge --raw   the uncentred comparison

## WHY THIS EXISTS

`run.py` answers "how many hops", and section 8 of the README is the finding
that the hop count was the wrong instrument: k=4 undirected over 350 nodes has
diameter 7 and 124 words sit at exactly 5 hops, so a difference of 0.26 in
cosine becomes a difference of 2 in a counter. This producer prints the
quantity the graph was built on, so the ordering can be read without the graph.

It is the producer for every number in README section 8.
"""
import argparse, os, statistics as st, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import embed  # noqa: E402
import run  # noqa: E402

#: the words section 8 quotes: the controls, the two poles, and the near ties
PROBE = ["scream", "shout", "yell", "cry", "weep", "shriek", "laugh",
         "dance", "eat", "sit", "sleep", "read", "write",
         "murder", "die", "stab", "shoot", "strangle", "hurt", "punch",
         "fight", "sell", "destroy"]


def space(name, prompt, centre=True):
    """-> (words, unit-normalised matrix, {word: row})"""
    import torch
    cand = run.candidates(prompt)
    ok, _ = run.lexicon("subtlex", 0.0, 2.0, True)
    cand = {w: v for w, v in cand.items() if ok(w.lower())}
    W, tok = embed.matrix(embed.MODEL)
    if name == "bge":
        M, words = embed.bge_in_context(prompt, sorted(cand))
        #: **CENTRING IS THE CHOICE THIS FILE MAKES VISIBLE.** Raw cosines run
        #: 0.69-0.98 because every vector is the same eight-token frame with
        #: one word changed, so raw similarity is mostly the frame. Centred
        #: cosine is similarity of the DEVIATION from the typical candidate,
        #: which is what "what does this word contribute here" means -- and
        #: it is a different quantity, not a cleaned-up version of the same
        #: one. `--raw` prints both so the difference is on the record.
        X = M - M.mean(0) if centre else M
        return sorted(words, key=words.index), \
            torch.nn.functional.normalize(X, dim=1), \
            {w: i for i, w in enumerate(words)}
    ids, _m = embed.words(tok, sorted(cand))
    return sorted(ids), torch.nn.functional.normalize(W.float(), dim=1), ids


def report(name, prompt, src="kill", centre=True):
    words, W, ids = space(name, prompt, centre)
    if src not in ids:
        raise SystemExit("%r is not in the %s vocabulary" % (src, name))
    v = W[ids[src]]
    sims = {w: float(v @ W[ids[w]]) for w in words}
    order = sorted(sims, key=lambda w: -sims[w])
    rank = {w: i for i, w in enumerate(order)}
    rest = [sims[w] for w in words if w != src]
    print("\n=== %s%s === %d words" % (name, "" if centre else " RAW", len(words)))
    print("  NEAREST  %s" % ", ".join("%s %.3f" % (w, sims[w]) for w in order[1:13]))
    print("  FARTHEST %s" % ", ".join("%s %.3f" % (w, sims[w]) for w in order[-12:]))
    print("  spread: max %.3f  median %.3f  min %.3f  sd %.3f"
          % (max(rest), st.median(rest), min(rest), st.pstdev(rest)))
    sd = st.pstdev(rest)
    print("  %-10s %7s %6s   %s" % ("word", "cos", "rank", "gap to scream, in sd"))
    for w in PROBE:
        if w in sims:
            print("  %-10s %7.3f %5d   %+.2f"
                  % (w, sims[w], rank[w], (sims[w] - sims.get("scream", 0)) / sd))
    return sims, rank


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prompt", default=run.FIG2)
    ap.add_argument("--from", dest="src", default="kill")
    ap.add_argument("--space", default="both", choices=("llama", "bge", "both"))
    ap.add_argument("--raw", action="store_true",
                    help="bge only: also print the uncentred ordering")
    a = ap.parse_args(argv)
    print("PROMPT: %r" % a.prompt)
    for nm in (("llama", "bge") if a.space == "both" else (a.space,)):
        report(nm, a.prompt, a.src)
        if a.raw and nm == "bge":
            report(nm, a.prompt, a.src, centre=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
