"""Rate F21's OWN 24 institutional prompts with the slot instrument.

    python experiments/slot_ratings/run_f21.py

## WHY THESE PROMPTS AND NOT ONLY M03's

M03's speaker kernel is F21 REWRITTEN to a frame specification -- each scenario
carries an `f21_anchor` (m03_N1 is "worker_3 / mgmt_3 (safety complaints)"), so
its 252 prompts are paraphrases built to a grammar. F21's 24 are the originals
its tagger actually scored.

Running both separates two things that would otherwise be confounded: whether a
position gap is a property of the SCENARIOS or of M03's frame specification. If
it appears on both, it is the phenomenon. If only on the rewrites, it is the
frame.

    F21     24 prompts, 12 symmetric pairs, roles labelled in the prompts table
            (worker/mgmt, tenant/landlord, citizen/agency, patient/doctor,
             citizen/officer, citizen/party)
    M03     252 prompts, 18 scenarios x 14 cells, crossing position x person x modal

Coverage checked before writing this: all 24 are in `movement` with all 50
`roster.endpoints()` pairs; arm A holds a median 134 words per prompt and arm B
150.

## THE COMPARISON IS TO F21's UNIT, NOT ITS NUMBERS

F21 scored ~21,000 GENERATIONS on 12 passage-level dimensions. This scores WORDS
in the slot. A position gap here is the same claim measured on a different
object, never a reproduction of +5.3pp -- and F21's own rider records that those
four numbers do not reproduce from its surviving tagged data anyway.

The individual/institutional assignment comes from the prompts table's
`subdomain`, which is the corpus's own labelling and not mine:

    INDIVIDUAL   citizen, worker, tenant, patient
    INSTITUTION  agency, mgmt, landlord, doctor, officer, party
"""

import collections, json, os, sys
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
SLOT = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(SLOT))
sys.path.insert(0, HERE); sys.path.insert(0, REPO)
RESULTS = os.path.join(HERE, "results", "m03")
MIN_PROB = 0.003
CONTENT_POS = ("NOUN", "VERB", "ADJ", "ADV")
INDIV = ("citizen", "worker", "tenant", "patient")
INST = ("agency", "mgmt", "landlord", "doctor", "officer", "party")


def prompts():
    from malignment import vectors as V
    rows = V.rows("SELECT prompt_id, subdomain, prompt FROM prompts "
                  "WHERE source='INSTITUTIONAL' ORDER BY subdomain, prompt_id")
    for r in rows:
        r["position"] = ("indiv" if r["subdomain"] in INDIV else
                         "inst" if r["subdomain"] in INST else "?")
    return rows


def population(ps, arm="A", min_pairs=3):
    from malignment import roster, vectors as V
    from malignment.pos import get_pos
    ep = sorted(roster.endpoints()[0].items())
    gate = ("p_base >= {mp:Float64}" if arm == "A" else
            "p_base < {mp:Float64} AND p_aligned >= {mp:Float64}")
    rows = V.rows("SELECT prompt, word, base, aligned, cls FROM movement "
                  "WHERE prompt IN {ps:Array(String)} "
                  "AND (base, aligned) IN {bs:Array(Tuple(String,String))} AND " + gate,
                  ps=sorted(ps), bs=ep, mp=MIN_PROB)
    by = collections.defaultdict(lambda: collections.defaultdict(dict))
    n = collections.defaultdict(collections.Counter)
    for r in rows:
        by[r["prompt"]][(r["base"], r["aligned"])][r["word"]] = (
            1 if r["cls"] == "riser" else -1 if r["cls"] == "faller" else 0)
        n[r["prompt"]][r["word"]] += 1
    out = {}
    for p in ps:
        ws = sorted(w for w, c in n[p].items() if c >= min_pairs)
        pos = get_pos(ws, p) if ws else {}
        out[p] = dict(words=[w for w in ws if pos.get(w) in CONTENT_POS],
                      verdicts=by[p])
    return out


def main():
    from task import InstitutionalSupplementEN, SCALES_INST, render
    from scipy import stats
    rows = prompts()
    ps = [r["prompt"] for r in rows]
    print("F21 prompts: %d (%d indiv, %d inst)"
          % (len(rows), sum(r["position"] == "indiv" for r in rows),
             sum(r["position"] == "inst" for r in rows)))
    pops = {a: population(ps, arm=a) for a in ("A", "B")}
    for a in "AB":
        print("  arm %s: %d words total" % (a, sum(len(pops[a][p]["words"]) for p in ps)))

    task = InstitutionalSupplementEN()
    os.makedirs(RESULTS, exist_ok=True)
    for arm in ("A", "B"):
        jobs = [(p, w) for p in ps for w in pops[arm][p]["words"]]
        errs = {}
        res = task.map([render(p, w) for p, w in jobs],
                       metadata_list=[{"prompt": p, "word": w} for p, w in jobs],
                       num_workers=32, errors=errs)
        rat = collections.defaultdict(dict)
        for (p, w), r in zip(jobs, res):
            if r is not None and r.ratable:
                rat[p][w] = {s: getattr(r, s) for s in SCALES_INST}
        print("\narm %s: %d words rated, errors %d" % (arm, len(jobs), len(errs)))
        json.dump({"arm": arm, "instrument": task.name,
                   "prompts": [dict(r, ratings=rat.get(r["prompt"], {})) for r in rows]},
                  open(os.path.join(RESULTS, "rated_f21_arm%s.json" % arm), "w"), indent=1)

        # per PAIR: mean rho over indiv prompts minus mean over inst prompts
        per = collections.defaultdict(lambda: collections.defaultdict(list))
        for r in rows:
            p = r["prompt"]
            for pk, vd in pops[arm][p]["verdicts"].items():
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
                        per[pk][(s, r["position"])].append(rr)
        print("  POSITION GAP, pair as unit")
        print("    %-14s %8s %8s %8s %9s %10s" % ("scale", "indiv", "inst", "gap", "pairs up", "wilcoxon"))
        for s in SCALES_INST:
            g = []
            for pk, d in per.items():
                iv, it = d.get((s, "indiv")), d.get((s, "inst"))
                if iv and it and len(iv) >= 2 and len(it) >= 2:
                    g.append((st.mean(iv), st.mean(it)))
            if len(g) < 8:
                print("    %-14s (only %d pairs)" % (s, len(g))); continue
            d_ = [a - b for a, b in g]
            pv = stats.wilcoxon(d_).pvalue
            print("    %-14s %+8.3f %+8.3f %+8.3f %6d/%-3d %10.2g%s"
                  % (s, st.mean(a for a, _ in g), st.mean(b for _, b in g), st.mean(d_),
                     sum(1 for x in d_ if x > 0), len(d_), pv, "*" if pv < 0.05 else ""))


if __name__ == "__main__":
    main()
