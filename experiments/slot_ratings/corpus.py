"""Run the v6 instrument over every frame in pilot3. Resumable.

    python experiments/slot_ratings/corpus.py            # all 303, skipping done
    python experiments/slot_ratings/corpus.py --limit 5  # a slice, to check
    python experiments/slot_ratings/corpus.py --report   # analyse what exists

RESUMABLE BY FILE, NOT BY MEMORY. A frame is done when its
`results/v6/rated_v6_<item_id>.json` exists, so an interrupted run costs nothing
and a rerun is free. The stash underneath is keyed on (prompt, model,
system_prompt, temperature, schema, metadata), so even a deleted output file
re-renders from cache without paying the API again.

Cost measured before launching: 217 tokens and $0.00005 per (prompt, word),
~76 rated words per frame, so 303 frames is ~23,000 calls and about $1.13.
That is why frame selection is not a design decision here.
"""

import argparse, collections, json, os, sys, time
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

from run import population, per_pair, CELLS, CONTENT_POS      # noqa: E402

OUT = os.path.join(HERE, "results", "v6")


def frames():
    """Every item_id in pilot3, with its prompt and domain, biggest first.

    Ordered by pair count so that an interrupted run has done the
    best-powered frames rather than an alphabetical slice of them.
    """
    cells = [json.loads(l) for l in open(CELLS, encoding="utf-8")]
    by = collections.defaultdict(list)
    for c in cells:
        by[c["item_id"]].append(c)
    out = [(i, v[0]["prompt"], v[0].get("domain"), len(v)) for i, v in by.items()]
    return sorted(out, key=lambda r: -r[3])


def one(item_id, prompt, min_elig=3):
    from task import SlotRatingENv6, SCALES_V6, render
    path = os.path.join(OUT, "rated_v6_%s.json" % item_id)
    if os.path.exists(path):
        return None
    prompt, cells, pop = population(item_id=item_id)
    content = [d for d in pop
               if d["pos"] in CONTENT_POS and d["n_eligible"] >= min_elig]
    if len(content) < 10:
        json.dump([], open(path, "w"))          # done, and empty ON PURPOSE
        return dict(item_id=item_id, n=0, skipped="under 10 content words")
    t = SlotRatingENv6()
    errs = {}
    res = t.map([render(prompt, d["word"]) for d in content],
                metadata_list=[{"prompt": prompt, "word": d["word"]} for d in content],
                num_workers=32, errors=errs)
    for d, r in zip(content, res):
        if r is None:
            continue
        d["ratable"], d["reading"] = r.ratable, r.reading
        for s in SCALES_V6:
            d[s] = getattr(r, s)
    json.dump(content, open(path, "w"), indent=1)
    pp, npairs = per_pair(prompt, cells, content)
    json.dump({"prompt": prompt, "item_id": item_id, "n_pairs": npairs,
               "per_pair_rho": pp},
              open(os.path.join(OUT, "perpair_v6_%s.json" % item_id), "w"), indent=1)
    return dict(item_id=item_id, n=len(content), errors=len(errs), pairs=npairs)


def report():
    import glob
    from scipy import stats
    from task import SCALES_V6
    agg = collections.defaultdict(list)
    words = []
    for f in sorted(glob.glob(os.path.join(OUT, "perpair_v6_*.json"))):
        pp = json.load(open(f))["per_pair_rho"]
        for s in SCALES_V6:
            v = pp.get(s) or []
            if len(v) >= 5:
                agg[s].append(st.median(v))
    for f in sorted(glob.glob(os.path.join(OUT, "rated_v6_*.json"))):
        words += [x for x in json.load(open(f)) if x.get("ratable")]
    print("frames analysed: %d   ratable words: %d"
          % (len(glob.glob(os.path.join(OUT, "perpair_v6_*.json"))), len(words)))
    if not words:
        return
    print("\n%-14s %6s %7s | %7s %8s %10s %9s"
          % ("scale", "sd", "%at 1", "frames", "median", "up/down", "wilcoxon"))
    for s in SCALES_V6:
        v = [x[s] for x in words]
        lev = "%6.2f %6.0f%%" % (st.pstdev(v), 100 * sum(1 for y in v if y == 1) / len(v))
        m = agg.get(s) or []
        if len(m) < 5:
            print("%-14s %s | %7d %8s" % (s, lev, len(m), "--"))
            continue
        p = stats.wilcoxon(m).pvalue
        print("%-14s %s | %7d %+8.3f %6d/%-3d %9.2g"
              % (s, lev, len(m), st.median(m),
                 sum(1 for x in m if x > 0), sum(1 for x in m if x < 0), p))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args(argv)
    os.makedirs(OUT, exist_ok=True)
    if a.report:
        return report()
    fs = frames()
    todo = [f for f in fs
            if not os.path.exists(os.path.join(OUT, "rated_v6_%s.json" % f[0]))]
    print("frames: %d total, %d already done, %d to run"
          % (len(fs), len(fs) - len(todo), len(todo)))
    if a.limit:
        todo = todo[:a.limit]
    t0 = time.time()
    for n, (iid, prompt, dom, npairs) in enumerate(todo, 1):
        try:
            r = one(iid, prompt)
        except Exception as e:                      # one bad frame must not end the run
            print("  [%d/%d] %-28s FAILED %s: %s"
                  % (n, len(todo), iid[:28], type(e).__name__, str(e)[:80]))
            continue
        el = time.time() - t0
        print("  [%d/%d] %-28s %-12s %s  (%.0fs elapsed, %.1fs/frame)"
              % (n, len(todo), iid[:28], dom or "?",
                 ("%d words, %d pairs" % (r["n"], r.get("pairs", 0))) if r and r["n"]
                 else (r or {}).get("skipped", "cached"), el, el / n))


if __name__ == "__main__":
    main()
