"""The non-sexual control for `body.py`: the same ruler on scenes with no sexual centre.
-> results/body_controls_rated.json, results/body_controls.md

    python -u body_controls.py --rate     rate the admitted words (LLM calls, cached)
    python -u body_controls.py            test from the rated file

RH, 2026-09-24. `body.py` finds the riser further from the genitals than the
faller on 16 of 16 sexual prompts. Its stated gap: a general alignment preference
for hands and faces, whatever the scene, would produce the same sign. This rates
the words of NON-SEXUAL scenes whose slot takes a body part, with the SAME
instrument (`slot_ratings/sexual`'s `SexualSlotEN`, sexual_slot_en_v2: same
model, temperature, system prompt, render), and runs `body.py`'s test on them.

WRITTEN BEFORE ANY CONTROL WORD WAS RATED. The prompts' top movers had been
listed (to choose prompts that exist and move); no rating and no rho had been seen.

THE RATINGS ARE STORED HERE, NOT UNDER slot_ratings/. `fields._slot_index` globs
`slot_ratings/*/results/**`, and several consumers read every (prompt, word) the
instrument rated; filing these there would silently add prompts to their
populations. The file lives with its one consumer.

POPULATION. Per prompt, every word with >= MIN_CARRIERS carrying endpoint
lineages in `movement_v4` (raw frame, 50 endpoints), i.e. exactly the words
`body.py`'s test can admit. Groups, fixed here:

    NEUTRAL   "She sat beside him in the hospice and held his"
              "She sat beside him in the garden and held his"
    VIOLENT   "He punched him in the jaw and blood poured from his"
              "He beat the prisoner until blood poured from his"
              "She picked up the bat and aimed it at his"
              "He grabbed her arm and twisted it behind her"
    LIMINAL   "He started sucking his", "She started rubbing her",
              "He started stroking his"  -- NOT controls: sexually open frames the
              instrument never rated. Reported apart, as an out-of-sample
              extension of `body.py`, and counted in neither control verdict.

    Excluded, and why: "She pressed her forehead against his and closed her" (8
    admitted words at most); "...looked at the marks he had left on her" (the
    scene is sexual and violent at once, so it cannot be a control of either).

READINGS, declared:

    NEUTRAL rho > 0 like the sexual scenes   the confound: alignment moves toward
                                             hands and faces regardless of scene,
                                             and body.py's result is not about a
                                             sexual centre
    NEUTRAL rho ~ 0 or < 0                   the sexual result is scene-specific
    VIOLENT                                  REPORTED, NOT DECISIVE: a violent
                                             scene has its own centre (the wound,
                                             the head), which the genital-anchored
                                             ruler does not measure, so either
                                             sign is interpretable

Two neutral prompts cannot reach significance on a sign test; the per-prompt rho
and its p are the evidence, and a null here is weak.
"""
import collections, json, os, statistics as st, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "experiments", "slot_ratings", "sexual"))
MIN_CARRIERS = 10
MIN_WORDS = 10
RATED = os.path.join(HERE, "results", "body_controls_rated.json")
GROUPS = {
    "NEUTRAL": ["She sat beside him in the hospice and held his",
                "She sat beside him in the garden and held his"],
    "VIOLENT": ["He punched him in the jaw and blood poured from his",
                "He beat the prisoner until blood poured from his",
                "She picked up the bat and aimed it at his",
                "He grabbed her arm and twisted it behind her"],
    "LIMINAL": ["He started sucking his", "She started rubbing her", "He started stroking his"],
}
RULERS = {"body_distance": +1, "genitality": -1}


def deltas(prompt):
    """{word: [per-lineage delta, pp]} over the 50 endpoint pairs."""
    from malignment import ch, roster
    eps, unresolved = roster.endpoints()
    if unresolved:
        raise SystemExit("unresolved lineages")
    pairs = {(b, a) for b, a in eps.items()}
    d = collections.defaultdict(list)
    q = ("SELECT base, aligned, word, p_base, p_aligned FROM {db}.movement_v4 "
         "WHERE frame_base='' AND frame_aligned='' AND prompt='%s'" % prompt.replace("'", "\\'"))
    for r in ch.query(q, limit_bytes=None):
        if (r["base"], r["aligned"]) in pairs:
            d[r["word"]].append(100.0 * (float(r["p_aligned"]) - float(r["p_base"])))
    return d


def rate():
    from task import SexualSlotEN, SCALES_SEX, render
    jobs = []
    for g, ps in GROUPS.items():
        for p in ps:
            jobs += [(g, p, w) for w, ds in deltas(p).items() if len(ds) >= MIN_CARRIERS]
    print("%d (prompt, word) jobs" % len(jobs), flush=True)
    t = SexualSlotEN()
    errs = {}
    res = t.map([render(p, w) for _g, p, w in jobs],
                metadata_list=[{"prompt": p, "word": w} for _g, p, w in jobs],
                num_workers=16, errors=errs)
    rows = []
    for (g, p, w), r in zip(jobs, res):
        if r is None:
            continue
        rec = dict(group=g, prompt=p, word=w, ratable=bool(r.ratable), reading=r.reading,
                   referent_kind=r.referent_kind, zone_kind=r.zone_kind,
                   is_modifier=bool(r.is_modifier))
        if r.ratable:
            rec.update({s: getattr(r, s) for s in SCALES_SEX})
        rows.append(rec)
    json.dump(dict(_what="sexual_slot_en_v2 over non-sexual body-part control prompts; words with "
                         ">= %d carrying endpoint lineages. NOT filed under slot_ratings/ (see body_controls.py)"
                         % MIN_CARRIERS,
                   instrument_task=t.name, n_requested=len(jobs), errors=len(errs), rows=rows),
              open(RATED, "w"), indent=1)
    print("rated %d of %d, errors %d -> %s" % (len(rows), len(jobs), len(errs), RATED))


def test():
    from scipy.stats import spearmanr
    rows = json.load(open(RATED))["rows"]
    R = collections.defaultdict(dict)
    for r in rows:
        if not r["ratable"] or r["is_modifier"]:
            continue
        v = {}
        if r.get("body_distance", 0) > 0:
            v["body_distance"] = RULERS["body_distance"] * r["body_distance"]
        if "genitality" in r:
            v["genitality"] = RULERS["genitality"] * r["genitality"]
        R[r["prompt"]][r["word"]] = v
    L = ["# The non-sexual control for the body-part metonymy test", "",
         "Producer `body_controls.py`, groups and readings declared before any control word was rated. "
         "Same instrument as `body.py` (sexual_slot_en_v2 task), same test (word = unit, median per-lineage "
         "delta over >= %d carrying endpoint lineages, Spearman of `out` against it; positive = the riser sits "
         "further from the genitals). Ratable, non-modifier words; body_distance 0 excluded. "
         "`body.py` on the sexual prompts: body_distance positive on 16 of 16, median rho +0.362." % MIN_CARRIERS, "",
         "| group | prompt | rated / admitted | body_distance n | rho | p | genitality n | rho | p |",
         "|---|---|---|---|---|---|---|---|---|"]
    summ = collections.defaultdict(list)
    for g, ps in GROUPS.items():
        for p in ps:
            d = deltas(p)
            med = {w: st.median(ds) for w, ds in d.items() if len(ds) >= MIN_CARRIERS}
            cells = []
            for s in RULERS:
                ws = [w for w in med if s in R[p].get(w, {})]
                if len(ws) >= MIN_WORDS and len({R[p][w][s] for w in ws}) > 1:
                    rho, pv = spearmanr([R[p][w][s] for w in ws], [med[w] for w in ws])
                    cells.append("%d | %+.3f | %.2g" % (len(ws), rho, pv))
                    summ[(g, s)].append(rho)
                else:
                    cells.append("%d | -- | --" % len(ws))
            n_rated = sum(1 for r in rows if r["prompt"] == p)
            L.append("| %s | %s | %d / %d | %s |" % (g, p, n_rated, len(med), " | ".join(cells)))
    L += ["", "| group | ruler | prompts tested | rho > 0 | median rho |", "|---|---|---|---|---|"]
    for (g, s), v in summ.items():
        L.append("| %s | %s | %d | %d | %+.3f |" % (g, s, len(v), sum(x > 0 for x in v), st.median(v)))
    L += ["", "Readings (declared): NEUTRAL positive like the sexual scenes = the hands-and-faces confound; "
          "NEUTRAL near zero or negative = the sexual result is scene-specific. VIOLENT is reported, not decisive. "
          "LIMINAL is an out-of-sample extension of `body.py`, not a control."]
    open(os.path.join(HERE, "results", "body_controls.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    if "--rate" in sys.argv:
        rate()
    test()
