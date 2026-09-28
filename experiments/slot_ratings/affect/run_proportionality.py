"""Rate the charged prompts' frames and movers with the affect task. -> results/affect_proportionality.parquet

    python run_proportionality.py --plan          count, spend nothing
    python run_proportionality.py --limit 500     the pilot
    python run_proportionality.py                 everything (resumable: the Task stash caches every call)

For `freudian_hypothesis/proportionality.py`'s contextual arm (declared there). ITEMS, by a
rule fixed before any rating:

    PROMPTS   the English prompts where any of the 50 endpoint lineages moves mass OFF a
              barred word (act >= 4, as proportionality.py): 1,873 at the time of writing
    FRAMES    each such prompt with no candidate word (target must echo `frame`)
    WORDS     per prompt, pooled over lineages: the barred departing words carrying 80% of
              the prompt's barred mass, plus the arriving words carrying 80% of its
              arriving mass (most-moved first). The same coverage rule proportionality.py
              gates on, so the rated set is chosen by what moved, never by what it rates.

Rater: `task.py` unchanged (deepseek/deepseek-v4-flash, resolved server-side to
`deepseek-flash`, temperature 0). The resolved id is the model of record.
"""
import argparse, collections, csv, gzip, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE); sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "experiments", "displacement", "freudian_hypothesis"))
SRC = os.path.expanduser("~/malignment-data/norm_change/words_long_v4.csv.gz")
OUT = os.path.join(os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data")), "affect_proportionality")
MIN_ACT, COVER = 4.0, 0.80
FIELDS = ["target", "ratable", "whose", "intensity", "feeling", "affect_move", "anxiety", "scene_intensity", "discharge", "reading"]


def items():
    from departing_arriving import norms
    from malignment import roster
    F, _ = norms()
    pairs = {(b, a) for b, a in roster.endpoints()[0].items()}
    kc = {}

    def act(w):
        if w not in kc:
            k = F.k(w) or {}
            kc[w] = max(float(k.get("bodily_harm", 0) or 0), float(k.get("transgressiveness", 0) or 0)) if k else None
        return kc[w]
    bar = collections.defaultdict(collections.Counter); arr = collections.defaultdict(collections.Counter)
    with gzip.open(SRC, "rt") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            if r["lang"] != "en" or (r["base"], r["aligned"]) not in pairs:
                continue
            d = float(r["delta"]); a = act(r["word"])
            if d < 0 and a is not None and a >= MIN_ACT:
                bar[r["prompt"]][r["word"]] += -d
            elif d > 0:
                arr[r["prompt"]][r["word"]] += d

    def cover(cnt):
        tot, acc, out = sum(cnt.values()), 0.0, []
        for w, m in cnt.most_common():
            out.append(w); acc += m
            if acc >= COVER * tot:
                break
        return out
    out = []
    for p in sorted(bar):
        out.append((p, None))
        for w in dict.fromkeys(cover(bar[p]) + cover(arr[p])):
            out.append((p, w))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--chunk", type=int, default=2000)
    ap.add_argument("--workers", type=int, default=16)
    a = ap.parse_args()
    its = items()
    print("%d prompts, %d calls (%d frames, %d words)" % (sum(1 for _, w in its if w is None), len(its),
          sum(1 for _, w in its if w is None), sum(1 for _, w in its if w)), flush=True)
    if a.plan:
        return
    if a.limit:
        import random
        its = random.Random(20260928).sample(its, a.limit)
    import task as T
    import pyarrow as pa, pyarrow.parquet as pq
    t = T.task()
    rows, t0 = [], time.time()
    for c0 in range(0, len(its), a.chunk):
        ch = its[c0:c0 + a.chunk]
        res = t.map([T.render(p, w) for p, w in ch], num_workers=a.workers)
        for (p, w), r in zip(ch, res):
            d = dict(prompt=p, word=w, ok=r is not None)
            if r is not None:
                d.update({f: getattr(r, f) for f in FIELDS})
                d["echo_ok"] = r.target == ("completion" if w else "frame")
            rows.append(d)
        print("  %d / %d  (%.1f min)" % (len(rows), len(its), (time.time() - t0) / 60), flush=True)
    os.makedirs(OUT, exist_ok=True)
    fn = os.path.join(OUT, "pilot.parquet" if a.limit else "affect_proportionality.parquet")
    pq.write_table(pa.Table.from_pylist(rows), fn, compression="zstd")
    ok = sum(r["ok"] for r in rows); echo = sum(r.get("echo_ok", False) for r in rows)
    print("wrote %s | %d rows, %d returned, %d echo ok" % (fn, len(rows), ok, echo))


if __name__ == "__main__":
    main()
