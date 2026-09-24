"""The declared neutral battery: word-level and paired tests on ten neutral body-part
prompts. -> results/body_neutral.md, results/body_neutral_rated.json

    python -u body_neutral.py --rate     rate what the tests need, then test
    python -u body_neutral.py            test from what is rated

Declaration, prompts and readings: `data/neutral_battery.md` (committed 19720533
before any cell was measured). Measured locally by `scripts/queue_v4.py
--prompts-json data/neutral_battery.json` on the endpoint checkpoints except the
Llama-3.1-70B pair.

WHERE THE DELTAS COME FROM. These prompts are outside `Prompts.all()`, and
`produce_movement` is incremental by PAIR, so `movement_v4` will not hold them.
They are read straight from the jsonl STASH, not ClickHouse, so this analysis
needs no ingest (a scoped ingest of this host's stash would also pull 125 files
belonging to other runs). Record choice mirrors ingest + `produce_movement`: raw
frame, rule_version 4, the record winning on (topup, prompt_cache, written_at),
rows folded to surfaces by summing p. Per endpoint pair, every word either arm
holds, p_aligned - p_base, a word absent from one arm counted at 0 there -- the
one difference from `movement_v4` where pass 2 (topup) has not run: there an
absent word gets its sub-theta lower bound. The header of the output counts
cells by pass.

TESTS, identical to `body.py` (word-level: Spearman of body_distance against the
median per-lineage delta, >= 10 carriers) and `body_paired.py` (largest valid
faller against largest valid riser per lineage, ties dropped). Ruler: the
sexual_slot_en_v2 task, ratable, not a modifier, body_distance > 0.
"""
import collections, json, os, statistics as st, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "experiments", "slot_ratings", "sexual"))
import body_paired as BP  # noqa: E402

PROMPTS = json.load(open(os.path.join(HERE, "data", "neutral_battery.json")))
PSET = set(PROMPTS)
STASH = os.path.expanduser(os.environ.get("MALIGNMENT_TWP_OUT", "~/malignment-data/twp"))
RATED = os.path.join(HERE, "results", "body_neutral_rated.json")
MIN_CARRIERS = 10
MIN_WORDS = 10


def _stash_cells(model):
    """{prompt: {word: p}} for the battery prompts, read from the model's jsonl stash.

    The same record choice the ingest + `produce_movement` make: raw frame,
    rule_version 4, a record with `rows`; per prompt the record winning on
    (topup, prompt_cache, written_at); rows FOLDED to the surface by summing p
    over first-token paths, as `ingest` does before `twp_words_v4` exists.
    """
    import glob
    best = {}
    for f in glob.glob(os.path.join(STASH, model.replace("/", "__"), "*", "jsonl.hashstash.raw", "data.jsonl")):
        for line in open(f, encoding="utf-8"):
            if '"rule_version": 4' not in line:
                continue
            try:
                r = json.loads(line)
            except ValueError:
                continue
            p = r.get("prompt")
            if p not in PSET or not r.get("rows") or r.get("frame") not in (None, ""):
                continue
            k = (int(bool(r.get("topup"))), int(bool(r.get("prompt_cache"))), r.get("__written_at__", 0))
            if p not in best or k > best[p][0]:
                best[p] = (k, r)
    out = {}
    for p, (k, r) in best.items():
        fold = collections.defaultdict(float)
        for w in r["rows"]:
            fold[w["word"]] += float(w["p"])
        out[p] = (dict(fold), k[0])
    return out


def cells():
    """{prompt: {(base, aligned): [(word, delta)]}}, and the count of cells by pass."""
    from malignment import roster
    eps, _ = roster.endpoints()
    S = {m: _stash_cells(m) for pair in eps.items() for m in pair}
    tops = collections.Counter(v[1] for s in S.values() for v in s.values())
    out = collections.defaultdict(dict)
    for b, a in eps.items():
        for p in PROMPTS:
            if p in S[b] and p in S[a]:
                wb, wa = S[b][p][0], S[a][p][0]
                out[p][(b, a)] = [(w, wa.get(w, 0.0) - wb.get(w, 0.0)) for w in set(wb) | set(wa)]
    return out, tops


def ratings():
    R = BP.ratings()
    if os.path.exists(RATED):
        for r in json.load(open(RATED))["rows"]:
            R.setdefault((r["prompt"], r["word"]), r)
    return R


def rate(jobs, R):
    from task import SexualSlotEN, SCALES_SEX, render
    jobs = sorted(set(jobs))
    t = SexualSlotEN()
    errs = {}
    res = t.map([render(p, w) for p, w in jobs],
                metadata_list=[{"prompt": p, "word": w} for p, w in jobs],
                num_workers=16, errors=errs)
    old = json.load(open(RATED))["rows"] if os.path.exists(RATED) else []
    for (p, w), r in zip(jobs, res):
        if r is None:
            continue
        rec = dict(prompt=p, word=w, ratable=bool(r.ratable), reading=r.reading,
                   referent_kind=r.referent_kind, zone_kind=r.zone_kind, is_modifier=bool(r.is_modifier))
        if r.ratable:
            rec.update({s: getattr(r, s) for s in SCALES_SEX})
        old.append(rec)
        R[(p, w)] = rec
    json.dump(dict(_what="sexual_slot_en_v2 over the declared neutral battery; NOT filed under slot_ratings/",
                   rows=old), open(RATED, "w"), indent=1)
    print("  rated %d, errors %d" % (len(jobs) - len(errs), len(errs)), flush=True)


def sorted_sides(ws):
    return (sorted([x for x in ws if x[1] < 0], key=lambda x: x[1]),
            sorted([x for x in ws if x[1] > 0], key=lambda x: -x[1]))


def main():
    from scipy.stats import binomtest, spearmanr
    C, tops = cells()
    R = ratings()
    if "--rate" in sys.argv:
        need = set()
        for p, cs in C.items():
            car = collections.Counter(w for ws in cs.values() for w, _d in ws)
            need |= {(p, w) for w, n in car.items() if n >= MIN_CARRIERS and (p, w) not in R}
        if need:
            print("word-level: %d words to rate" % len(need), flush=True)
            rate(need, R)
        for rnd in range(6):
            need = set()
            for p, cs in C.items():
                for ws in cs.values():
                    for lst in sorted_sides(ws):
                        need |= {(p, w) for w in BP.walk(lst, R, p)[1]}
            print("paired walk round %d: %d unrated" % (rnd + 1, len(need)), flush=True)
            if not need:
                break
            rate(need, R)
    L = ["# The neutral body-part battery", "",
         "Producer `body_neutral.py`; prompts and readings declared in `data/neutral_battery.md` before "
         "measurement. Deltas from the jsonl stash (raw frame, movement_v4's record choice); cells by pass: %s "
         "(1 = pass 2 topup). Ruler sexual_slot_en_v2 body_distance." % dict(tops), "",
         "| prompt | lineages | word-level n | rho | p | paired hits | misses | ties |", "|---|---|---|---|---|---|---|---|"]
    rhos, pos_pair = [], 0
    for p in PROMPTS:
        cs = C.get(p, {})
        d = collections.defaultdict(list)
        for ws in cs.values():
            for w, x in ws:
                d[w].append(100.0 * x)
        med = {w: st.median(v) for w, v in d.items() if len(v) >= MIN_CARRIERS and BP.valid(R.get((p, w)))}
        if len(med) >= MIN_WORDS:
            rho, pv = spearmanr([R[(p, w)]["body_distance"] for w in med], list(med.values()))
            rhos.append(rho)
            wl = "%d | %+.3f | %.2g" % (len(med), rho, pv)
        else:
            wl = "%d | -- | --" % len(med)
        h = m = t = 0
        for ws in cs.values():
            fl, rs = sorted_sides(ws)
            f, _ = BP.walk(fl, R, p)
            r, _ = BP.walk(rs, R, p)
            if f and r:
                a, b = R[(p, r)]["body_distance"], R[(p, f)]["body_distance"]
                h += a > b; m += a < b; t += a == b
        pos_pair += h > m
        L.append("| %s | %d | %s | %d | %d | %d |" % (p, len(cs), wl, h, m, t))
    pos = sum(r > 0 for r in rhos)
    L += ["", "| test | prompts in the predicted-outward direction | sign p | median rho |", "|---|---|---|---|",
          "| word-level | %d of %d | %.2g | %s |" % (pos, len(rhos), binomtest(pos, len(rhos)).pvalue if rhos else float("nan"),
                                                  "%+.3f" % st.median(rhos) if rhos else "--"),
          "| paired | %d of %d | %.2g | -- |" % (pos_pair, len(PROMPTS), binomtest(pos_pair, len(PROMPTS)).pvalue),
          "", "Declared readings: >= 8 of 10 on both = a general outward move; neither reaching 8 and median rho "
          "well below the sexual +0.36 = the ordering tracks the scene's charge; between = reported, no gradient claim."]
    open(os.path.join(HERE, "results", "body_neutral.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
