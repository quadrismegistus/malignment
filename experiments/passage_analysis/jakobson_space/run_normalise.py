"""Run the normalisation task over the human pool.

    python .../run_normalise.py --hard          # 12 difficult passages, smoke test
    python .../run_normalise.py                 # the whole pool

Reads `human_pool_raw.jsonl` DIRECTLY. There is no intermediate batch file, which
is the point: the previous design split the pool into 240 batch files, the pool
was then rebuilt, and the batches were never regenerated -- so 148 batches
normalised text that no longer existed in the pool. An intermediate that can go
stale is a defect the pipeline does not need to have.

`Task.map` caches per item, so re-running costs nothing for passages that already
succeeded and retries only what failed or is new.
"""

import argparse, json, os, random, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, REPO)
from experiments.passage_analysis.jakobson_space.normalise_task import (  # noqa: E402
    Normalise, render, straighten)

DATA = os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data"))
ROOT = os.path.join(DATA, "jakobson_space")
POOL = os.path.join(ROOT, "human_pool_raw.jsonl")
OUT = os.path.join(ROOT, "human_passages.jsonl")

#: the shapes that broke earlier rounds, used to pick a smoke-test slice that
#: actually exercises them rather than one that happens to be easy
HARD = [("money", re.compile(r"\$\d")),
        ("suspended", re.compile(r"\w-\s+(and|or|to)\b")),
        ("identifier", re.compile(r"\b\w+_\w+\b")),
        ("compound_num", re.compile(r"\d+[.,]\d+")),
        ("footnote", re.compile(r"(?<!\d)[.,;:!?]\d{1,3}(?=\s|$)")),
        ("latex", re.compile(r"\$[^$]{1,60}\$|\\[a-zA-Z]{2,}")),
        ("typo", re.compile(r"\b(dont|thats|didnt|wasnt|im|cant|teh|alot)\b", re.I)),
        ("ocr_split", re.compile(r"\w-\s+[a-z]{2,}"))]


def pick_hard(rows, per=2, seed=11):
    rng = random.Random(seed)
    out, taken = [], set()
    for name, rx in HARD:
        c = [r for r in rows if rx.search(r["text"]) and r["id"] not in taken]
        rng.shuffle(c)
        for r in c[:per]:
            taken.add(r["id"])
            out.append(dict(r, _why=name))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--hard", action="store_true", help="smoke test on hard cases")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--workers", type=int, default=32)
    ap.add_argument("--force", action="store_true", help="ignore cache")
    ap.add_argument("--seed", type=int, default=20260820)
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args(argv)

    rows = [json.loads(l) for l in open(POOL)]
    #: SHUFFLE, so that a run stopped early is a SAMPLE of the corpus rather than
    #: a prefix of it. The pool is written corpus by corpus, and a first attempt
    #: stopped at 14% had normalised 496 dreams and 14 of everything else --
    #: enough to look like progress and useless for judging whether the pass
    #: works on academic prose or abstracts.
    random.Random(a.seed).shuffle(rows)
    if a.hard:
        rows = pick_hard(rows)
        a.out = os.path.join(ROOT, "human_passages_hard.jsonl")
    if a.limit:
        rows = rows[:a.limit]
    print("passages: %d" % len(rows))

    task = Normalise()
    #: a DICT, keyed by item index. Passing a list made the library's
    #: `errors[i] = ...` raise IndexError on the first failed item, which
    #: surfaced as a traceback after 3,461 of 3,600 had already succeeded.
    errs = {}
    res = task.map([render(r["text"]) for r in rows],
                   metadata_list=[{"id": r["id"], "corpus": r["corpus"]} for r in rows],
                   num_workers=a.workers, errors=errs, verbose=False,
                   force=a.force)

    by_id = {r["id"]: r for r in rows}
    out, n_ok = [], 0
    for r, got in zip(rows, res):
        if got is None:
            continue
        d = dict(by_id[r["id"]])
        d["text_raw"] = d.pop("text")
        #: typography in code, AFTER the model -- see normalise_task.TYPOGRAPHY.
        #: `text_raw` is deliberately left UNstraightened: it is the source of
        #: record, and keeping it so lets the residue check show curly -> 0
        #: rather than comparing the substitution table against itself.
        d["text"] = straighten(getattr(got, "text", "") or "")
        d["changes"] = list(getattr(got, "changes", []) or [])
        if r.get("_why"):
            d["_why"] = r["_why"]
        out.append(d)
        n_ok += 1
    with open(a.out, "w") as fh:
        for d in out:
            fh.write(json.dumps(d) + "\n")
    print("\nreturned %d of %d | errors %d" % (n_ok, len(rows), len(errs)))
    for k in list(errs)[:3]:
        print("  err[%s]: %s" % (k, str(errs[k])[:160]))
    print("-> %s" % a.out)


if __name__ == "__main__":
    main()
