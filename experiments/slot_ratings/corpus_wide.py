"""The v6 instrument again at n_eligible>=1, for regression power.

    python experiments/slot_ratings/corpus_wide.py --dry
    python experiments/slot_ratings/corpus_wide.py

`corpus.py` rates content-POS words with `n_eligible >= 3`. That gate was set for
a MOVEMENT analysis, where a word appearing in fewer than three pairs has an
unstable rise/fall verdict. In `displacement_axis/variance_decomp.py` the word is
a PREDICTOR, not an outcome, and a rating does not become less valid because the
word is rare -- while the shortage of words does bite: at a median 67 rated words
against 13 parameters, the full 12-scale vector (held-out R2 0.034) does WORSE
than its own best single scale (0.049). That is overfitting, and more words is
the fix.

Dropping to `n_eligible >= 1` takes a frame from ~67 rated words to ~107.

## A SEPARATE OUTPUT DIRECTORY, DELIBERATELY

`results/v6_wide/`, not an extension of `results/v6/`. Every published figure in
this folder was computed on the >=3 set, and adding words changes the
mass-weighted levels -- the same drift the sexual study's store fingerprint
exists to catch. The two sets are kept apart so any analysis states which it
used, and the old numbers stay reproducible.

## THE RE-RATING IS FREE

The stash keys on (prompt, model, system_prompt, temperature, schema, metadata)
and `metadata` here is the same `{"prompt": ..., "word": ...}` corpus.py used, so
the ~67 words per frame already rated come back from cache and only the ~40 new
ones are paid for. Measured before launching: ~12,200 new pairs, about $0.61.

ALL POS was considered and rejected: it adds only 12 more words per frame on top
of this, nearly all function words the instrument declines as unratable.
"""

import argparse, collections, json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

from run import population, CELLS, CONTENT_POS      # noqa: E402

OUT = os.path.join(HERE, "results", "v6_wide")
MIN_ELIG = 1


def frames():
    cells = [json.loads(l) for l in open(CELLS, encoding="utf-8")]
    by = collections.defaultdict(list)
    for c in cells:
        by[c["item_id"]].append(c)
    return sorted([(i, v[0]["prompt"], v[0].get("domain"), len(v))
                   for i, v in by.items()], key=lambda r: -r[3])


def one(item_id, prompt_hint):
    from task import SlotRatingENv6, SCALES_V6, render
    path = os.path.join(OUT, "rated_v6w_%s.json" % item_id)
    if os.path.exists(path):
        return None
    prompt, cells, pop = population(item_id=item_id)
    content = [d for d in pop
               if d["pos"] in CONTENT_POS and d["n_eligible"] >= MIN_ELIG]
    if len(content) < 10:
        json.dump([], open(path, "w"))
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
    return dict(item_id=item_id, n=len(content), errors=len(errs))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args(argv)
    os.makedirs(OUT, exist_ok=True)
    fs = frames()
    todo = [f for f in fs
            if not os.path.exists(os.path.join(OUT, "rated_v6w_%s.json" % f[0]))]
    print("frames: %d total, %d done, %d to run (min_eligible=%d)"
          % (len(fs), len(fs) - len(todo), len(todo), MIN_ELIG))
    if a.dry:
        return
    if a.limit:
        todo = todo[:a.limit]
    t0 = time.time()
    for n, (iid, prompt, dom, npairs) in enumerate(todo, 1):
        try:
            r = one(iid, prompt)
        except Exception as e:
            print("  [%d/%d] %-26s FAILED %s: %s"
                  % (n, len(todo), iid[:26], type(e).__name__, str(e)[:70]))
            continue
        el = time.time() - t0
        print("  [%d/%d] %-26s %-12s %s  (%.0fs, %.1fs/frame)"
              % (n, len(todo), iid[:26], dom or "?",
                 ("%d words" % r["n"]) if r and r["n"] else (r or {}).get("skipped", "cached"),
                 el, el / n))


if __name__ == "__main__":
    main()
