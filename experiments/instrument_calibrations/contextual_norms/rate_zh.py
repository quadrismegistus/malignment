"""Rate the Chinese tier of the priority manifest with the existing v6 instrument.

    python -u rate_zh.py                  # all tier-1 prompts, resumable
    python -u rate_zh.py --limit 5        # smoke
    python -u rate_zh.py --min-lineages 10

Writes `experiments/slot_ratings/results/v6zh/rated_v6zh_<id>.json`, one file per
prompt, in the record shape `fields._slot_index` reads: a bare list of dicts each
carrying `prompt`, `word`, and numeric scales.

## WHY v6zh AND NOT v6

`_slot_index` takes the instrument name from the directory basename, so these land
as `v6zh` rather than merging into `v6`. They are Chinese content rated with an
ENGLISH instrument -- English scale glosses, English system prompt -- and that is a
different measurement from `v6` on English content until someone shows it is not.
Keeping them separable costs nothing and means no analysis can pool them by
accident; `contextual_norms(prompt, instrument="v6zh")` selects them deliberately.

## THE INSTRUMENT WAS NOT BUILT FOR THIS AND WORKS ANYWAY

An earlier claim in `priority.py` -- that the Chinese arm was blocked because
`SlotRatingENv6` is English-only -- was inferred from the class name and was false.
Smoke test on 5 pairs, 0 errors, sane profiles, discrimination within Chinese
(`死` vs `停` moves aggression 1->5), and the one translation-matched pair agreed
with its English twin on all twelve scales.

**What that established is that the instrument RUNS, not that its output is
comparable across languages.** There is no translation key in the data -- pair_id,
kernel_id and archive_prompt_id all span zero cross-language groups -- so a matched
study needs the correspondence reconstructed first. Absence of systematic offset is
the target, never exact agreement.

## THE `reading` FIELD IS THE AUDIT

The task returns a one-line paraphrase of the completed sentence. On English it is
a nicety; here it is the check that the rater understood the Chinese at all. A
`reading` that mistranslates its own item makes every scale on that row worthless,
and it is visible without a second rater. `--audit` prints a sample.
"""

import argparse, csv, gzip, hashlib, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
SLOT = os.path.abspath(os.path.join(HERE, "..", "..", "slot_ratings"))
sys.path.insert(0, SLOT)
OUT = os.path.join(SLOT, "results", "v6zh")
MANIFEST = os.path.expanduser("~/malignment-data/contextual_norms/priority.csv.gz")


def pid(prompt):
    return "zh_" + hashlib.sha1(prompt.encode("utf-8")).hexdigest()[:12]


def load(tier, min_lineages):
    """-> {prompt: [rows]} for the requested tier, biggest frame first."""
    import collections
    by = collections.defaultdict(list)
    with gzip.open(MANIFEST, "rt", encoding="utf-8") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            if int(r["tier"]) != tier:
                continue
            if int(r["n_lineages"]) < min_lineages:
                continue
            by[r["prompt"]].append(r)
    return sorted(by.items(), key=lambda kv: -len(kv[1]))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier", type=int, default=1)
    ap.add_argument("--min-lineages", type=int, default=5)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=32)
    ap.add_argument("--audit", type=int, default=6, help="readings to print per file")
    a = ap.parse_args(argv)

    from task import SlotRatingENv6, SCALES_V6, render

    frames = load(a.tier, a.min_lineages)
    if a.limit:
        frames = frames[:a.limit]
    todo = [(p, rs) for p, rs in frames
            if not os.path.exists(os.path.join(OUT, "rated_v6zh_%s.json" % pid(p)))]
    print("tier %d: %d prompts, %d pairs | %d prompts already done | %d to run"
          % (a.tier, len(frames), sum(len(r) for _, r in frames),
             len(frames) - len(todo), len(todo)), flush=True)
    os.makedirs(OUT, exist_ok=True)

    t = SlotRatingENv6()
    done_pairs = n_err = 0
    for i, (prompt, rows) in enumerate(todo, 1):
        words = [r["word"] for r in rows]
        errs = {}
        res = t.map([render(prompt, w) for w in words],
                    metadata_list=[{"prompt": prompt, "word": w} for w in words],
                    num_workers=a.workers, errors=errs)
        recs = []
        for r, out in zip(rows, res):
            if out is None:
                n_err += 1
                continue
            d = {"prompt": prompt, "word": r["word"], "item_id": pid(prompt),
                 "lang": "zh", "pos": r.get("pos", ""),
                 "n_lineages": int(r["n_lineages"]),
                 "consistency": float(r["consistency"]),
                 "ratable": out.ratable, "reading": out.reading}
            for s in SCALES_V6:
                d[s] = getattr(out, s)
            recs.append(d)
        path = os.path.join(OUT, "rated_v6zh_%s.json" % pid(prompt))
        #: written whole, never appended -- a partial file that looks complete is
        #: the failure mode the pos tables just demonstrated.
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(recs, fh, ensure_ascii=False, indent=1)
        done_pairs += len(recs)
        rat = sum(1 for d in recs if d.get("ratable"))
        print("[%4d/%-4d] %-26s %4d words | %3d ratable | %d errors | total %d"
              % (i, len(todo), prompt[:26], len(recs), rat, len(errs), done_pairs),
              flush=True)
        if a.audit and i <= 2:
            for d in recs[:a.audit]:
                print("      %-8s harm %s aggr %s mund %s | %s"
                      % (d["word"], d["harm"], d["aggression"], d["mundanity"],
                         (d["reading"] or "")[:70]), flush=True)
    print("\nDONE: %d pairs rated, %d errors -> %s" % (done_pairs, n_err, OUT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
