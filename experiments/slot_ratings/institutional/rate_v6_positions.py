"""Rate F21 and M03 prompts with the GENERAL v6 instrument.

    python experiments/slot_ratings/institutional/rate_v6_positions.py --corpus f21
    python experiments/slot_ratings/institutional/rate_v6_positions.py --corpus m03 --dry

v6 ran on the 303 pilot3 slot frames. F21 and M03 are different prompt sets, so
v6 covers 0 of 24 F21 prompts and 0 of 252 M03 prompts, while slotpov's 12 are
slot frames and are already at 100%. Without this pass a "both instruments"
table can only be built for one of the three corpora.

**THE WORD POPULATION IS THE ONE v3 USED**, taken from each corpus's own
producer (`run_f21.population`, `run_m03.population`), so the two instruments
rate the SAME (prompt, word) pairs and a difference between them is a difference
in the instrument rather than in what it was shown. Both arms are rated, since
the mass-weighted level measure has no eligibility gate and merges them.

Resumable by file: a corpus is done when its output exists.
"""

import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SLOT = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(SLOT))
sys.path.insert(0, HERE); sys.path.insert(0, SLOT); sys.path.insert(0, REPO)
OUT = os.path.join(HERE, "results", "v6")


def jobs_f21():
    from run_f21 import prompts, population
    ps = [r["prompt"] for r in prompts()]
    out = []
    for arm in ("A", "B"):
        pop = population(ps, arm=arm)
        for p in ps:
            for w in pop[p]["words"]:
                out.append((p, w))
    return out


def jobs_m03():
    from run_m03 import kernel, population
    ps = sorted({c["prompt"] for c in kernel()})
    out = []
    for arm in ("A", "B"):
        pop = population(ps, arm=arm)
        for p in ps:
            for w in pop[p]["words"]:
                out.append((p, w))
    return out


CORPORA = {"f21": jobs_f21, "m03": jobs_m03}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True, choices=sorted(CORPORA))
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args(argv)
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "rated_%s_v6.json" % a.corpus)
    if os.path.exists(path) and not a.dry:
        print("exists, nothing to do: %s" % path)
        return
    pairs = sorted(set(CORPORA[a.corpus]()))
    print("%s: %d distinct (prompt, word) to rate over %d prompts"
          % (a.corpus, len(pairs), len({p for p, _ in pairs})))
    print("  estimated cost at $0.00005/call: $%.2f" % (0.00005 * len(pairs)))
    if a.dry:
        return
    #: `institutional/task.py` shadows `slot_ratings/task.py` on sys.path, and
    #: v6 lives in the parent. Load it by file so the name cannot resolve to the
    #: institutional instrument by accident.
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "slot_ratings_task", os.path.join(SLOT, "task.py"))
    m = importlib.util.module_from_spec(spec)
    sys.modules["slot_ratings_task"] = m
    spec.loader.exec_module(m)
    SlotRatingENv6, SCALES_V6, render = m.SlotRatingENv6, m.SCALES_V6, m.render
    t = SlotRatingENv6()
    errs = {}
    res = t.map([render(p, w) for p, w in pairs],
                metadata_list=[{"prompt": p, "word": w} for p, w in pairs],
                num_workers=32, errors=errs)
    rows = []
    for (p, w), r in zip(pairs, res):
        if r is None or not getattr(r, "ratable", False):
            continue
        rows.append(dict(prompt=p, word=w, ratable=True,
                         **{s: getattr(r, s) for s in SCALES_V6}))
    json.dump(dict(corpus=a.corpus, instrument=t.name, n_requested=len(pairs),
                   errors=len(errs), prompts=rows), open(path, "w"), indent=1)
    print("rated %d of %d, errors %d -> %s" % (len(rows), len(pairs), len(errs), path))


if __name__ == "__main__":
    main()
