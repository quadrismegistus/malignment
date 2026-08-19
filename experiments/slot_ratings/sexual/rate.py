"""Rate every moving word in the 8 sexual gender pairs with sexual_slot_en_v2.

    python experiments/slot_ratings/sexual/rate.py            # k>=1, all 8 pairs
    python experiments/slot_ratings/sexual/rate.py --dry

Population: words moving (riser or faller) in AT LEAST ONE of the 33 lineage
pairs, at every one of the 16 prompts. 2,599 (prompt, word) cells, covering 96.7%
of base+aligned mass at the median prompt and 93.1% at the worst. k>=1 rather
than X's k>=2 because the extra 1,033 words cost $0.05 and remove any question
about whether the rated set is selected on movement -- which matters if the
analysis is a mass-weighted level rather than X's word-level correlation.

Movement is computed with `movement.movement()` over `twp_words_v4_best`: these
are slot frames and have ZERO rows in the `movement` table (checked), so that
path does not exist for them.

Resumable by file. Writes results/rated_gender_pairs_v2.json.
"""

import argparse, collections, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, HERE); sys.path.insert(0, REPO)
OUT = os.path.join(HERE, "results")
MIN_PAIRS = 1


def population():
    from malignment import roster, vectors as V
    from malignment.movement import movement, CANONICAL
    from gender_pairs import PAIRS, DROP
    keep = {t: v for t, v in PAIRS.items() if v[0] not in DROP}
    ep = sorted(roster.endpoints()[0].items())
    ms = sorted({x for p in ep for x in p})
    q = V.rows("SELECT prompt, model, groupArray(word) AS ws, groupArray(p) AS ps "
               "FROM twp_words_v4_best WHERE prompt IN {ts:Array(String)} "
               "AND model IN {ms:Array(String)} GROUP BY prompt, model",
               ts=sorted(keep), ms=ms)
    store = collections.defaultdict(dict)
    for r in q:
        store[r["prompt"]][r["model"]] = dict(zip(r["ws"], r["ps"]))
    mv = collections.defaultdict(collections.Counter)
    npairs = collections.Counter()
    for t in sorted(keep):
        for b, a in ep:
            pb, pa = store[t].get(b), store[t].get(a)
            if not pb or not pa:
                continue
            npairs[t] += 1
            m = movement(pb, pa, CANONICAL)
            for w in m.risers:
                mv[(t, w)]["r"] += 1
            for w in m.fallers:
                mv[(t, w)]["f"] += 1
    jobs = sorted(k for k, c in mv.items() if c["r"] + c["f"] >= MIN_PAIRS)
    return keep, jobs, mv, npairs


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args(argv)
    keep, jobs, mv, npairs = population()
    print("8 pairs, %d prompts, %d lineage pairs each"
          % (len(keep), sorted(set(npairs.values()))[0]))
    print("words moving in >= %d pairs: %d   cost ~$%.3f"
          % (MIN_PAIRS, len(jobs), 0.00005 * len(jobs)))
    per = collections.Counter(keep[t][0] for t, _ in jobs)
    print("  per set: %s" % dict(sorted(per.items())))
    if a.dry:
        return
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "rated_gender_pairs_v2.json")
    from task import SexualSlotEN, SCALES_SEX, render
    t = SexualSlotEN()
    errs = {}
    res = t.map([render(p, w) for p, w in jobs],
                metadata_list=[{"prompt": p, "word": w} for p, w in jobs],
                num_workers=32, errors=errs)
    rows = []
    for (p, w), r in zip(jobs, res):
        if r is None:
            continue
        rec = dict(prompt=p, word=w, pair=keep[p][0], gender=keep[p][1],
                   role=keep[p][2], ratable=bool(r.ratable),
                   rise=mv[(p, w)]["r"], fall=mv[(p, w)]["f"],
                   net=mv[(p, w)]["r"] - mv[(p, w)]["f"],
                   reading=r.reading, referent_kind=r.referent_kind,
                   zone_kind=r.zone_kind, is_modifier=bool(r.is_modifier))
        if r.ratable:
            rec.update({s: getattr(r, s) for s in SCALES_SEX})
        rows.append(rec)
    ok = sum(1 for r in rows if r["ratable"])
    print("\nrated %d of %d requested, ratable %d, errors %d"
          % (len(rows), len(jobs), ok, len(errs)))
    print("  zone_kind: %s" % dict(collections.Counter(
        r["zone_kind"] for r in rows if r["ratable"])))
    print("  referent_kind: %s" % dict(collections.Counter(
        r["referent_kind"] for r in rows if r["ratable"])))
    print("  is_modifier: %d" % sum(1 for r in rows if r["ratable"] and r["is_modifier"]))
    json.dump(dict(_what="sexual_slot_en_v2 over the 8 sexual gender matched pairs; "
                         "words moving in >=1 of 33 lineage pairs",
                   instrument=t.name, min_pairs=MIN_PAIRS, n_requested=len(jobs),
                   errors=len(errs), rows=rows), open(path, "w"), indent=1)
    print("-> %s" % path)


if __name__ == "__main__":
    main()
