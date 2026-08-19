"""Does the in-context instrument reproduce X_metonymy's known answer?

    python experiments/slot_ratings/sexual/validate_vs_X.py

X reached rho -0.53 to -0.66 between coder intimacy and net movement at
`She slowly took off her ___` and `He slowly took off his ___`, with four coder
instruments and two model families. That is a KNOWN ANSWER, so it is the check
to run before spending anything at scale: an instrument that cannot reproduce it
is not the instrument, whatever else it does.

SIGN. X's intimacy scale runs low-to-high intimacy and correlates NEGATIVELY
(more intimate, more withdrawal). `body_distance` here is the inverse -- higher
means further from the body -- so it should come out POSITIVE at about the same
magnitude. `zone`, `charge` and `exposure` should be negative.

X also reports the base-probability nuisance is ABSENT at these two frames
(-0.131 and +0.179, both null) while it runs -0.09 to -0.42 at every violence
prompt. That is checked here too, because a scale landing near -0.3 has
explained nothing until it is.
"""

import collections, json, os, sys
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, HERE); sys.path.insert(0, REPO)
OUT = os.path.join(HERE, "results")

SCENES = ["She slowly took off her", "He slowly took off his"]
MIN_PAIRS = 2          #: X pooled at k >= 2, a word must move in >= 2 pairs


def main():
    from malignment import roster, vectors as V
    from scipy import stats
    from task import SexualSlotEN, SCALES_SEX, render
    ep = sorted(roster.endpoints()[0].items())
    rows = V.rows("SELECT prompt, word, cls, avg(p_base) pb, count() n FROM movement "
                  "WHERE prompt IN {ps:Array(String)} "
                  "AND (base, aligned) IN {bs:Array(Tuple(String,String))} "
                  "GROUP BY prompt, word, cls", ps=SCENES, bs=ep)
    mv = collections.defaultdict(lambda: collections.Counter())
    pb = collections.defaultdict(float)
    for r in rows:
        mv[(r["prompt"], r["word"])][r["cls"]] += r["n"]
        pb[(r["prompt"], r["word"])] = max(pb[(r["prompt"], r["word"])], r["pb"])
    net = {k: c["riser"] - c["faller"] for k, c in mv.items()}
    moved = {k: c["riser"] + c["faller"] for k, c in mv.items()}
    jobs = [k for k, m in moved.items() if m >= MIN_PAIRS]
    print("scenes: %d | words moving in >= %d pairs: %d"
          % (len(SCENES), MIN_PAIRS, len(jobs)))
    for s in SCENES:
        print("   %-28s %d words" % (s[:28], sum(1 for p, _ in jobs if p == s)))

    t = SexualSlotEN()
    errs = {}
    res = t.map([render(p, w) for p, w in jobs],
                metadata_list=[{"prompt": p, "word": w} for p, w in jobs],
                num_workers=32, errors=errs)
    R = {}
    for k, r in zip(jobs, res):
        if r is None or not r.ratable:
            continue
        R[k] = dict(reading=r.reading, referent_kind=r.referent_kind,
                    is_modifier=r.is_modifier,
                    **{s: getattr(r, s) for s in SCALES_SEX})
    print("rated %d of %d, errors %d" % (len(R), len(jobs), len(errs)))

    print("\n%-16s %s" % ("", "  ".join("%-22s" % s[:22] for s in SCENES)))
    print("%-16s %s" % ("scale", "  ".join("%9s %11s" % ("rho", "p")
                                           for _ in SCENES)))
    saved = []
    for sc in SCALES_SEX + ["_p_base"]:
        cells = []
        for s in SCENES:
            ks = [k for k in R if k[0] == s and not R[k]["is_modifier"]]
            if len(ks) < 10:
                cells.append((float("nan"), float("nan"), 0)); continue
            x = [pb[k] if sc == "_p_base" else R[k][sc] for k in ks]
            y = [net[k] for k in ks]
            r_ = stats.spearmanr(x, y)
            cells.append((r_.statistic, r_.pvalue, len(ks)))
        print("%-16s %s" % (sc, "  ".join("%+9.3f %11.2g" % (c[0], c[1]) for c in cells)))
        saved.append(dict(scale=sc, **{SCENES[i]: dict(rho=cells[i][0], p=cells[i][1],
                                                       n=cells[i][2])
                                       for i in range(len(SCENES))}))
    print("\n  X's benchmark, coder intimacy vs net movement:  -0.53 to -0.66")
    print("  X's base-probability nuisance at THESE frames:  -0.131 / +0.179, both null")
    print("  (body_distance is inverted against X's intimacy, so expect POSITIVE)")

    #: the referent classes X had to hand-make, now asked for directly
    print("\n  referent_kind at these frames: %s"
          % dict(collections.Counter(v["referent_kind"] for v in R.values())))
    print("  is_modifier: %d of %d"
          % (sum(1 for v in R.values() if v["is_modifier"]), len(R)))

    os.makedirs(OUT, exist_ok=True)
    json.dump(dict(_what="in-context sexual instrument validated against X_metonymy's "
                         "undressing scenes; net = risers minus fallers over 50 pairs",
                   min_pairs=MIN_PAIRS, correlations=saved,
                   words=[dict(prompt=k[0], word=k[1], net=net[k], p_base=pb[k], **R[k])
                          for k in sorted(R)]),
              open(os.path.join(OUT, "validate_vs_X.json"), "w"), indent=1)
    print("\n-> results/validate_vs_X.json")


if __name__ == "__main__":
    main()
