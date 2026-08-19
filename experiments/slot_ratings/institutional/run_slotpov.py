"""The slot corpus's OWN perspective pairs: same event, two sides, one site.

    python experiments/slot_ratings/institutional/run_slotpov.py

## WHY THIS IS THE CLEANEST OF THE THREE POV DESIGNS

`roster/prompts/slots/*.yaml` carries `matched_set`, and six institutional sets
are perspective pairs -- the same event written from each side:

    clear_the_square   protesters / officers      course_removal  she / the college
    hospital_bill      she / the hospital         late_shift      she / the manager
    repairs_bill       she / the landlord         visa_refusal    he / the Home Office

**Both sides end at the identical site**, `so X decided to`. That matters more
than it sounds: measured on M03, changing the grammatical site
(`I should ___` bare infinitive against `...and I ___` finite verb) moves
`procedural` by **+0.221**, which is LARGER than the position contrast the whole
design exists to measure. M03 holds the site fixed by frame specification and
pays for it in heavier syntax; F21 mixes sites (`I should`, `We should`,
`I said`). These pairs hold it fixed by construction and stay short.

    F21    24 prompts   RH-written, mixed sites, direct grievances
    M03   252 prompts   agent-written to a frame spec, site fixed, heavy syntax
    SLOT   12 prompts   perspective pairs, site fixed, short

## MOVEMENT IS COMPUTED HERE, NOT READ

The precomputed `movement` table covers the M03/F21 prompts. These are slot
prompts, so movement comes from `movement.movement()` over `twp_words_v4_best`
with pilot3's cells supplying the pairs and the residuals -- the same path
`run.py` uses. `_best` and not `twp_words_v4`: the raw table holds pass-1 and
merged rows for one (model, prompt, word) and a naive read keeps one at random.

Two arms, never pooled, as in `run_m03.py`: arm A is `p_base >= min_prob` and
can fall; arm B is `p_base < min_prob, p_aligned >= min_prob` and can only rise.
"""

import collections, json, os, sys
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
SLOT = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(SLOT))
sys.path.insert(0, HERE); sys.path.insert(0, REPO)
RESULTS = os.path.join(HERE, "results", "slotpov")
CELLS = os.path.join(REPO, "experiments", "displacement_axis",
                     "results", "pilot3", "cells.jsonl")
MIN_PROB = 0.003
CONTENT_POS = ("NOUN", "VERB", "ADJ", "ADV")

#: which side of each matched set is the individual. Read off the prompts, and
#: stated here rather than inferred by a regex so it is auditable.
INDIV_MARKER = ("the protesters", "so she decided", "so he decided")


def pairs():
    import yaml
    items = []
    for f in ("round3.yaml", "slot-explorer.yaml", "slot-client.yaml"):
        p = os.path.join(REPO, "roster", "prompts", "slots", f)
        if not os.path.exists(p):
            continue
        for it in (yaml.safe_load(open(p, encoding="utf-8")) or []):
            if isinstance(it, dict) and it.get("prompt"):
                items.append(it)
    by = collections.defaultdict(list)
    for i in items:
        ms = i.get("matched_set")
        if ms and ms.endswith("_perspective") and i.get("domain") == "institutional":
            by[ms].append(i)
    out = []
    for ms, v in sorted(by.items()):
        if len(v) != 2:
            continue
        for i in v:
            i["position"] = ("indiv" if any(m in i["prompt"] for m in INDIV_MARKER)
                             else "inst")
        if {i["position"] for i in v} == {"indiv", "inst"}:
            out.append((ms, v))
    return out


def population(prompts, arm="A", min_pairs=3):
    from malignment import vectors as V
    from malignment.movement import movement, CANONICAL
    from malignment.pos import get_pos
    cells = [json.loads(l) for l in open(CELLS, encoding="utf-8")]
    byp = collections.defaultdict(list)
    for c in cells:
        byp[c["prompt"]].append(c)
    out = {}
    for p in prompts:
        mine = byp.get(p) or []
        if not mine:
            out[p] = dict(words=[], verdicts={}); continue
        ms = sorted({c["base"] for c in mine} | {c["endpoint"] for c in mine})
        rows = V.rows("SELECT model, groupArray(word) AS ws, groupArray(p) AS ps "
                      "FROM twp_words_v4_best WHERE prompt={p:String} "
                      "AND model IN {ms:Array(String)} GROUP BY model", p=p, ms=ms)
        store = {r["model"]: dict(zip(r["ws"], r["ps"])) for r in rows}
        vd = {}
        n = collections.Counter()
        for c in mine:
            pb, pa = store.get(c["base"]), store.get(c["endpoint"])
            if not pb or not pa:
                continue
            m = movement(pb, pa, CANONICAL,
                         residual_pre=c.get("residual_base"),
                         residual_post=c.get("residual_endpoint"))
            rs, fs = set(m.risers), set(m.fallers)
            keep = {}
            for w, pv in pb.items():
                ok = (pv >= MIN_PROB) if arm == "A" else (
                    pv < MIN_PROB and pa.get(w, 0.0) >= MIN_PROB)
                if ok:
                    keep[w] = 1 if w in rs else -1 if w in fs else 0
                    n[w] += 1
            for w in pa:                       # arm B words absent from base
                if arm == "B" and w not in keep and pb.get(w, 0.0) < MIN_PROB \
                        and pa[w] >= MIN_PROB:
                    keep[w] = 1 if w in rs else 0
                    n[w] += 1
            vd[(c["base"], c["endpoint"])] = keep
        ws = sorted(w for w, c in n.items() if c >= min_pairs)
        pos = get_pos(ws, p) if ws else {}
        out[p] = dict(words=[w for w in ws if pos.get(w) in CONTENT_POS], verdicts=vd)
    return out


def main():
    import os as _os
    _V3 = _os.environ.get("INST_V3")
    if _V3:
        from task import (InstitutionalSupplementENv3 as InstitutionalSupplementEN,
                          SCALES_INST_V3 as SCALES_INST, render)
    else:
        from task import InstitutionalSupplementEN, SCALES_INST, render
    from scipy import stats
    ps = pairs()
    print("institutional perspective pairs: %d" % len(ps))
    allp = [i["prompt"] for _, v in ps for i in v]
    for arm in ("A", "B"):
        pop = population(allp, arm=arm)
        jobs = [(p, w) for p in allp for w in pop[p]["words"]]
        print("\narm %s: %d words over %d prompts" % (arm, len(jobs), len(allp)))
        if not jobs:
            continue
        task = InstitutionalSupplementEN()
        errs = {}
        res = task.map([render(p, w) for p, w in jobs],
                       metadata_list=[{"prompt": p, "word": w} for p, w in jobs],
                       num_workers=32, errors=errs)
        rat = collections.defaultdict(dict)
        for (p, w), r in zip(jobs, res):
            if r is not None and r.ratable:
                rat[p][w] = {s: getattr(r, s) for s in SCALES_INST}
        print("  errors %d" % len(errs))
        os.makedirs(RESULTS, exist_ok=True)
        json.dump({"arm": arm, "pairs": [(ms, [dict(i, ratings=rat.get(i["prompt"], {}))
                                               for i in v]) for ms, v in ps]},
                  open(os.path.join(RESULTS, "rated_%s_arm%s.json" % (task.name, arm)), "w"), indent=1)
        per = collections.defaultdict(lambda: collections.defaultdict(list))
        for ms, v in ps:
            for i in v:
                p = i["prompt"]
                for pk, vd in pop[p]["verdicts"].items():
                    e = [w for w in rat.get(p, {}) if w in vd]
                    if len(e) < 10:
                        continue
                    mv = [vd[w] for w in e]
                    if len(set(mv)) < 2:
                        continue
                    for s in SCALES_INST:
                        xs = [rat[p][w][s] for w in e]
                        if len(set(xs)) < 2:
                            continue
                        rr = stats.spearmanr(xs, mv).correlation
                        if rr == rr:
                            per[pk][(s, i["position"])].append(rr)
        print("  %-14s %8s %8s %8s %9s %10s"
              % ("scale", "indiv", "inst", "gap", "pairs up", "wilcoxon"))
        for s in SCALES_INST:
            g = [(st.mean(per[pk][(s, "indiv")]), st.mean(per[pk][(s, "inst")]))
                 for pk in per if per[pk][(s, "indiv")] and per[pk][(s, "inst")]]
            if len(g) < 8:
                print("  %-14s (only %d lineages)" % (s, len(g))); continue
            d = [a - b for a, b in g]
            pv = stats.wilcoxon(d).pvalue
            print("  %-14s %+8.3f %+8.3f %+8.3f %6d/%-3d %10.2g%s"
                  % (s, st.mean(a for a, _ in g), st.mean(b for _, b in g), st.mean(d),
                     sum(1 for x in d if x > 0), len(d), pv, "*" if pv < 0.05 else ""))


if __name__ == "__main__":
    main()
