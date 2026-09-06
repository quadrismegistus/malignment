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
CELLS = os.path.join(REPO, "experiments", "displacement", "displacement_axis",
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


def population(prompts, arm="A", min_pairs=3, pilot=False, edge="raw"):
    """Words and per-pair verdicts for each prompt.

    ## THE PANEL CAME FROM A PILOT CELL LIST AND NOW COMES FROM THE ROSTER

    This read `CELLS` -- `displacement_axis/results/pilot3/cells.jsonl` -- for
    both the model list AND the residuals, so the panel was **21 endpoint pairs**
    wherever the pilot happened to run. `displacement_axis`'s own README calls
    that a DATA SHORTFALL, not a design: *"EVERY NUMBER BELOW IS pilot3, WHICH
    RAN 21 OF THE 50 ENDPOINT PAIRS."* The same shortfall reached
    `slot_ratings/identity` (fixed 2026-09-05) and `slot_ratings/sexual`.

    The residuals were the obstacle -- `movement()` needs total mass and
    `twp_words_v4_best` carries only the scored set -- and **`movement_v4` removes
    it**, because its rows were classified when the null had the full
    distribution. So the risers and fallers are READ, not recomputed, and the
    panel is `roster.endpoints()`.

    `pilot=True` reproduces the published 21-pair numbers.

    ## THE THREE EDGES

    `edge` selects which contrast the verdicts describe, via
    `movement.endpoint_edges`:

        raw     base_raw    -> aligned_raw       50 pairs
        framed  base_raw    -> aligned_framed    45, alignment AND deployment
        self    aligned_raw -> aligned_framed    45, the frame ALONE

    **The base side is raw on all three**, so the gate reads a different table
    per side and `store` is keyed by `(model, frame)` rather than by model: on a
    self-edge one model is BOTH sides and a model-keyed store would silently
    serve the raw distribution to both.

    A framed side reads `twp_words_v4` at `frame='prefill'`, NOT the `_best`
    view, which is raw-only. `_best` merges topup cells, so in general a framed
    side could carry fewer words for reasons unrelated to the frame -- but for
    THESE 12 prompts it does not: `_best` and `twp_words_v4` at `frame=''` are
    identical in all 540 cells (2026-09-06), so the shrink IS the frame.

        median words per cell    raw 129    framed 81    (530/540 smaller)

    **That shrink lands on the two arms differently.** Arm A gates on the BASE
    side, which is raw on all three edges, so its population is comparable
    across them. Arm B gates on the ALIGNED side -- words absent from base and
    present in aligned -- so it is gated on the concentrated distribution and
    its population is NOT the same object across edges. Read an arm B change
    across edges as confounded with vocabulary size unless that is checked.

    `min_pairs` is applied to whichever population is asked for and the two
    framed edges are 45, not 50: do not compare a count here against a raw count
    without saying which edge produced it.
    """
    from malignment import movement as Mv, roster, vectors as V
    from malignment.movement import movement, CANONICAL
    from malignment.pos import get_pos
    cells = [json.loads(l) for l in open(CELLS, encoding="utf-8")]
    byp = collections.defaultdict(list)
    for c in cells:
        byp[c["prompt"]].append(c)

    #: risers/fallers per (prompt, base, aligned), read once for every prompt
    mv = collections.defaultdict(lambda: (set(), set()))
    #: the frame each SIDE is read at. Base is raw on every edge.
    fa = '' if edge == "raw" else 'prefill'
    if not pilot:
        edges = [(b, a) for b, a, _ in Mv.endpoint_edges(edge)]
        #: the roster restriction and the clean-slot rule both live in the
        #: predicate, so no python-side `eps.get(base) != aligned` filter here.
        #: `V.rows` not `ch.query`: it binds parameters, and a prompt here can
        #: carry an apostrophe. See `vectors.rows`'s own warning about TSV
        #: escaping and hand-built literals.
        for r in V.rows(
                "SELECT prompt, base, aligned, cls, groupArray(word) ws "
                "FROM movement_v4 WHERE prompt IN {ps:Array(String)} "
                "AND rule='canonical' AND cls IN ('riser','faller') AND %s "
                "GROUP BY prompt, base, aligned, cls"
                % Mv.endpoint_edge_where(edge),
                ps=list(prompts)):
            k = (r["prompt"], r["base"], r["aligned"])
            rs, fs = mv[k]
            (rs if r["cls"] == "riser" else fs).update(r["ws"])
            mv[k] = (rs, fs)

    out = {}
    for p in prompts:
        mine = byp.get(p) or []
        if pilot:
            if not mine:
                out[p] = dict(words=[], verdicts={}); continue
        else:
            mine = [dict(base=b, endpoint=e) for b, e in edges
                    if (p, b, e) in mv]
            if not mine:
                out[p] = dict(words=[], verdicts={}); continue
        store = {}
        for side, fr in (("base", ''), ("endpoint", fa)):
            ms = sorted({c[side] for c in mine})
            if fr == '':
                rows = V.rows(
                    "SELECT model, groupArray(word) AS ws, groupArray(p) AS ps "
                    "FROM twp_words_v4_best WHERE prompt={p:String} "
                    "AND model IN {ms:Array(String)} GROUP BY model", p=p, ms=ms)
            else:
                rows = V.rows(
                    "SELECT model, groupArray(word) AS ws, groupArray(p) AS ps "
                    "FROM twp_words_v4 WHERE prompt={p:String} "
                    "AND model IN {ms:Array(String)} AND frame={fr:String} "
                    "GROUP BY model", p=p, ms=ms, fr=fr)
            for r in rows:
                store[(r["model"], fr)] = dict(zip(r["ws"], r["ps"]))
        vd = {}
        n = collections.Counter()
        for c in mine:
            pb, pa = store.get((c["base"], '')), store.get((c["endpoint"], fa))
            if not pb or not pa:
                continue
            if pilot:
                m = movement(pb, pa, CANONICAL,
                             residual_pre=c.get("residual_base"),
                             residual_post=c.get("residual_endpoint"))
                rs, fs = set(m.risers), set(m.fallers)
            else:
                rs, fs = mv[(p, c["base"], c["endpoint"])]
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


def main(argv=None):
    #: `--dry` EXISTS BECAUSE ITS ABSENCE COST AN ARTIFACT (2026-09-06).
    #: This file had NO argument parsing at all, so `run_slotpov.py --dry` was
    #: neither honoured nor rejected -- it ran for real and overwrote both
    #: `rated_slot_institutional_en_v2_arm{A,B}.json`, which had to be restored
    #: from git. `run_slotdomain.py` in the same folder DOES take `--dry` and
    #: shares this module's `population()`, which is exactly why the flag was
    #: assumed to work here. An unimplemented flag is indistinguishable from an
    #: implemented one until you check the file mtime.
    import argparse
    ap = argparse.ArgumentParser(description="institutional instrument over the "
                                             "6 POV-paired slot frames")
    ap.add_argument("--dry", action="store_true",
                    help="report the job size and WRITE NOTHING")
    ap.add_argument("--pilot", action="store_true",
                    help="use the pilot3 cell list (reproduces the published "
                         "21-pair numbers) instead of roster.endpoints()")
    #: THE EDGE IS IN THE FILENAME. `movers.jsonl` was overwritten by a run on a
    #: different panel on 2026-09-06 because the output path did not name it,
    #: and a rated file whose edge is not in its name is indistinguishable from
    #: the raw one it sits beside.
    ap.add_argument("--edge", default="raw", choices=("raw", "framed", "self"),
                    help="raw: base->aligned unframed (50 pairs). "
                         "framed: base_raw->aligned_framed (45). "
                         "self: aligned_raw->aligned_framed, the frame alone (45)")
    a = ap.parse_args(argv)
    sfx = "" if a.edge == "raw" else "_" + a.edge
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
        pop = population(allp, arm=arm, pilot=a.pilot, edge=a.edge)
        jobs = [(p, w) for p in allp for w in pop[p]["words"]]
        pairs_seen = len({k for p in allp for k in pop[p]["verdicts"]})
        print("\narm %s: %d words over %d prompts, %d %s edges%s"
              % (arm, len(jobs), len(allp), pairs_seen, a.edge,
                 "   [PILOT]" if a.pilot else ""))
        if a.dry or not jobs:
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
                  open(os.path.join(RESULTS, "rated_%s_arm%s%s.json"
                                    % (task.name, arm, sfx)), "w"), indent=1)
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
