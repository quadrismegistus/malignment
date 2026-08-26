"""Does wording B say `any_loaded: false` when it should?

The pilot scored three wordings on 60 HAND-TAGGED prompts and B won on the
quantity that matters (mass r 0.894 against 0.602 and 0.642, and 3 off-list words
against A's 269). But `empty` was 0% for all three, which tested nothing: the 255
hand-tagged prompts are all frames an author thought worth tagging, so a rater that
never says "nothing here" scores identically to one that judges correctly.

That matters more than it sounds. On the wider corpus most frames are ordinary. A
rater that cannot return empty MANUFACTURES DOSE EVERYWHERE, and a dose present at
every prompt is not a dose.

`prompts.Prompts.transgressive_pairs()` is the test that exists for free: 1,511
MARKED/UNMARKED prompts differing by ONE TOKEN by construction -- `sedative ->
cinnamon`, `diary -> postcard`. The same scene, the same slot, the same syntax; only
the loaded element swapped. So:

    MARKED    should return words, `any_loaded` true
    UNMARKED  should return empty, or near it

Anything else is a failure the hand-tagged set cannot show. And because the pairs
are matched, a difference between arms cannot be a difference in topic, length or
site -- the confound that wrecked every other contrast in this campaign.

NOTE the fence from `M01_RECONSIDERED.md`: these arms differ by only ~3% of the
available transgressive range, MARKED sitting at the 70th corpus percentile against
UNMARKED's 37th. So this is a WEAK manipulation and a small gap is expected. What
would condemn the instrument is no gap, or a reversed one.
"""
import argparse, base64, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
sys.path.insert(0, HERE)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=40, help="pairs (2 prompts each)")
    ap.add_argument("--cands", type=int, default=200)
    ap.add_argument("--wording", default="B")
    ap.add_argument("--workers", type=int, default=16)
    a = ap.parse_args(argv)

    from malignment import ch, roster, prompts as PR
    from task import task_for, render
    import numpy as np

    P = PR.Prompts()
    pairs = P.transgressive_pairs(language="en")
    #: pair the MARKED text with its partner; keep only pairs where BOTH are in
    #: twp_words_v4, else the arms are not comparable on candidates either
    mv = {r["prompt"] for r in ch.query("SELECT DISTINCT prompt FROM twp_words_v4")}
    seen, both = set(), []
    for p in pairs:
        q = getattr(p, "partner", None)
        qt = getattr(q, "text", None) if q is not None else None
        if not qt or p.text == qt:
            continue
        k = tuple(sorted((p.text, qt)))
        if k in seen:
            continue
        seen.add(k)
        if p.text in mv and qt in mv:
            both.append((p.text, qt))
    random.Random(20260826).shuffle(both)
    both = both[:a.n]
    print("transgressive_swap en pairs: %d | both arms in twp_words_v4: %d | using %d"
          % (len(pairs), len(seen), len(both)))

    m = roster.endpoints(); m = m[0] if isinstance(m, tuple) else m
    inb = ",".join("'" + b.replace("'", "''") + "'" for b in sorted(m))
    texts = [t for pr in both for t in pr]
    CAND, MASS = {}, {}
    for t in texts:
        b64 = base64.b64encode(t.encode()).decode()
        rows = ch.query("SELECT word, sum(p) s FROM twp_words_v4 WHERE base64Encode(prompt)='%s' "
                        "AND model IN (%s) GROUP BY word ORDER BY s DESC LIMIT %d"
                        % (b64, inb, a.cands))
        CAND[t] = [r["word"] for r in rows]
        MASS[t] = {r["word"]: float(r["s"]) for r in rows}

    t_ = task_for(a.wording)
    errs = []
    out = t_.map([render(t, CAND[t]) for t in texts], num_workers=a.workers, errors=errs)
    res = {t: r for t, r in zip(texts, out)}

    def stat(t):
        r = res.get(t)
        if r is None:
            return None
        w = [x for x in (r.words or []) if x in MASS[t]]
        tot = sum(MASS[t].values()) or 1.0
        return (bool(r.any_loaded and w), len(w),
                sum(MASS[t].get(x, 0) for x in w) / tot)
    rows = [(stat(x), stat(y)) for x, y in both]
    rows = [r for r in rows if r[0] and r[1]]
    print("scored pairs: %d | %d errors\n" % (len(rows), len(errs)))
    for lbl, i in (("MARKED  ", 0), ("UNMARKED", 1)):
        v = [r[i] for r in rows]
        print("  %s  any_loaded %3.0f%% | words %5.1f | mass %.4f"
              % (lbl, 100 * np.mean([x[0] for x in v]),
                 float(np.mean([x[1] for x in v])), float(np.mean([x[2] for x in v]))))
    dm = [r[0][2] - r[1][2] for r in rows]
    up = sum(1 for d in dm if d > 0)
    print("\n  MARKED mass > UNMARKED on %d of %d pairs (median gap %+.4f)"
          % (up, len(rows), float(np.median(dm))))
    both_empty = sum(1 for r in rows if not r[0][0] and not r[1][0])
    print("  pairs where BOTH arms came back empty: %d" % both_empty)
    return 0


if __name__ == "__main__":
    sys.exit(main())
