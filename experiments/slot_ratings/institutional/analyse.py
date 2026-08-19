"""Every table in the README, computed here and SAVED. Nothing is eyeballed.

    python experiments/slot_ratings/institutional/analyse.py

Writes `results/tables/*.json` -- one file per table, each carrying its own
`_what`, the unit, and the n. Plotting reads these, never the raw ratings.

THE UNIT IS THE LINEAGE in every test. `roster.endpoints()` is a dict keyed by
base model, so its 50 entries are 50 distinct pretrained models and no two share
a base: the "pair" and the "lineage" are the same object here.

ARM A and ARM B ARE NEVER POOLED. Arm A's outcome is signed (+1 riser / -1
faller / 0 still) and its statistic is a rank correlation. Arm B's outcome is
binary by construction -- a word below min_prob cannot be called a faller -- and
its statistic is a two-group mean, because a lineage holds a median of 3 such
words and a correlation cannot work on that.
"""

import collections, json, glob, os, sys
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "results", "tables")
import run_m03, run_f21, run_slotpov
from task import SCALES_INST
from scipy import stats


def _save(name, what, rows, **meta):
    os.makedirs(OUT, exist_ok=True)
    json.dump(dict(_what=what, _unit="lineage", **meta, rows=rows),
              open(os.path.join(OUT, name + ".json"), "w"), indent=1)
    print("  -> results/tables/%s.json (%d rows)" % (name, len(rows)))


def rows_m03(arm):
    for f in sorted(glob.glob(os.path.join(
            HERE, "results/m03/rated_slot_institutional_en_v2_m03_*_arm%s.json" % arm))):
        d = json.load(open(f))
        for c in d["cells"]:
            if c["ratings"] and not c["cell"].endswith("absent"):
                yield (c["prompt"], c["ratings"],
                       "indiv" if c["cell"].startswith("indiv") else "inst",
                       d["scenario"])


def rows_f21(arm):
    d = json.load(open(os.path.join(HERE, "results/m03/rated_f21_arm%s.json" % arm)))
    for r in d["prompts"]:
        if r["ratings"]:
            yield r["prompt"], r["ratings"], r["position"], r.get("subdomain")


def rows_slot(arm):
    d = json.load(open(os.path.join(HERE, "results/slotpov/rated_arm%s.json" % arm)))
    for ms, v in d["pairs"]:
        for i in v:
            if i["ratings"]:
                yield i["prompt"], i["ratings"], i["position"], ms


CORPORA = {"F21": (rows_f21, run_f21.population),
           "M03": (rows_m03, run_m03.population),
           "SLOT": (rows_slot, run_slotpov.population)}


def per_lineage_armA(rows, popper):
    """lineage -> (scale, position) -> [rho]"""
    rows = list(rows)
    pop = popper([p for p, _, _, _ in rows], arm="A")
    out = collections.defaultdict(lambda: collections.defaultdict(list))
    for pr, rat, pos, _ in rows:
        for pk, vd in pop[pr]["verdicts"].items():
            e = [w for w in rat if w in vd]
            if len(e) < 10:
                continue
            mv = [vd[w] for w in e]
            if len(set(mv)) < 2:
                continue
            for s in SCALES_INST:
                xs = [rat[w][s] for w in e]
                if len(set(xs)) < 2:
                    continue
                r = stats.spearmanr(xs, mv).correlation
                if r == r:
                    out[pk][(s, pos)].append(r)
    return out


def per_lineage_armB(rows, popper):
    """lineage -> (scale, position) -> (riser ratings, still ratings)"""
    rows = list(rows)
    pop = popper([p for p, _, _, _ in rows], arm="B")
    out = collections.defaultdict(lambda: collections.defaultdict(lambda: ([], [])))
    for pr, rat, pos, _ in rows:
        for pk, vd in pop[pr]["verdicts"].items():
            ris = [w for w in rat if vd.get(w) == 1]
            sti = [w for w in rat if vd.get(w) == 0]
            if len(ris) < 2 or len(sti) < 2:
                continue
            for s in SCALES_INST:
                a, b = out[pk][(s, pos)]
                a.extend(rat[w][s] for w in ris)
                b.extend(rat[w][s] for w in sti)
    return out


def table(per, arm, corpus):
    """main effect and position gap, from one per_lineage_* structure."""
    main, gap = [], []
    for s in SCALES_INST:
        if arm == "A":
            allv = [st.mean(v) for pk in per
                    for k, v in per[pk].items() if k[0] == s and v]
            byl = {}
            for pk in per:
                v = [x for k, vv in per[pk].items() if k[0] == s for x in vv]
                if v:
                    byl[pk] = st.mean(v)
            g = [(st.mean(per[pk][(s, "indiv")]), st.mean(per[pk][(s, "inst")]))
                 for pk in per if per[pk][(s, "indiv")] and per[pk][(s, "inst")]]
        else:
            byl = {}
            for pk in per:
                R = [x for k, (a, b) in per[pk].items() if k[0] == s for x in a]
                S = [x for k, (a, b) in per[pk].items() if k[0] == s for x in b]
                if len(R) >= 5 and len(S) >= 5:
                    byl[pk] = st.mean(R) - st.mean(S)
            g = []
            for pk in per:
                ai, bi = per[pk].get((s, "indiv"), ([], []))
                at, bt = per[pk].get((s, "inst"), ([], []))
                if len(ai) >= 5 and len(bi) >= 5 and len(at) >= 5 and len(bt) >= 5:
                    g.append((st.mean(ai) - st.mean(bi), st.mean(at) - st.mean(bt)))
        v = list(byl.values())
        if len(v) >= 8:
            main.append(dict(corpus=corpus, arm=arm, scale=s, stat=st.mean(v),
                             n=len(v), up=sum(1 for x in v if x > 0),
                             p=stats.wilcoxon(v).pvalue))
        if len(g) >= 8:
            d = [a - b for a, b in g]
            gap.append(dict(corpus=corpus, arm=arm, scale=s,
                            indiv=st.mean(a for a, _ in g), inst=st.mean(b for _, b in g),
                            gap=st.mean(d), n=len(d), up=sum(1 for x in d if x > 0),
                            p=stats.wilcoxon(d).pvalue))
    return main, gap


def main():
    allmain, allgap = [], []
    for corpus, (getter, popper) in CORPORA.items():
        for arm in ("A", "B"):
            try:
                per = (per_lineage_armA if arm == "A" else per_lineage_armB)(
                    getter(arm), popper)
            except FileNotFoundError:
                continue
            m, g = table(per, arm, corpus)
            allmain += m; allgap += g
            print("%s arm %s: %d main, %d gap" % (corpus, arm, len(m), len(g)))
    _save("main_effect",
          "rho(rating, mover verdict) per lineage (arm A) or mean(riser)-mean(still) "
          "per lineage (arm B), Wilcoxon across lineages", allmain)
    _save("position_gap",
          "indiv minus inst on the same statistic. NEGATIVE means the scale moved MORE "
          "in the institution's slot, not that anything fell for the individual", allgap)
    print("\nARM B POSITION GAP -- does it change the indiv/inst picture?")
    print("  %-6s %-14s %8s %8s %8s %8s %10s"
          % ("corpus", "scale", "indiv", "inst", "gap", "up/n", "wilcoxon"))
    for r in allgap:
        if r["arm"] != "B":
            continue
        print("  %-6s %-14s %+8.3f %+8.3f %+8.3f %4d/%-3d %10.2g%s"
              % (r["corpus"], r["scale"], r["indiv"], r["inst"], r["gap"],
                 r["up"], r["n"], r["p"], "*" if r["p"] < 0.05 else ""))




# ---------------------------------------------------------------------------
# WORD-LEVEL, BENEATH THE CATEGORIES
# ---------------------------------------------------------------------------
# The scales are a hypothesis about what the words have in common and they can be
# wrong about it: `file` and `contact` both score procedural 5-7, but one is a
# formal instrument and the other is a phone call. So the vocabulary is also
# aggregated raw -- which words rise, which fall, in how many lineages -- with no
# scale involved. RH, 2026-08-19.

def word_tables():
    out = []
    for corpus, (getter, popper) in CORPORA.items():
        rows = list(getter("A"))
        if not rows:
            continue
        pop = popper([p for p, _, _, _ in rows], arm="A")
        agg = collections.defaultdict(lambda: collections.Counter())
        rate = {}
        for pr, rat, pos, grp in rows:
            for pk, vd in pop[pr]["verdicts"].items():
                for w, v in vd.items():
                    if w not in rat:
                        continue
                    a = agg[(w, pos)]
                    a["seen"] += 1
                    a["rise" if v == 1 else "fall" if v == -1 else "still"] += 1
                    rate[w] = rat[w]
        for (w, pos), c in agg.items():
            if c["seen"] < 20:
                continue
            out.append(dict(corpus=corpus, word=w, position=pos, seen=c["seen"],
                            rise=c["rise"], fall=c["fall"],
                            net=(c["rise"] - c["fall"]) / c["seen"],
                            **{k: rate[w][k] for k in SCALES_INST}))
    _save("words_armA", "per (corpus, word, position): rise/fall counts over "
          "(prompt x lineage) cells, with the word's mean ratings. NO scale is used "
          "to build this -- it is the raw vocabulary", out, min_seen=20)
    # arm B: what arrives
    outB = []
    for corpus, (getter, popper) in CORPORA.items():
        try:
            rows = list(getter("B"))
        except FileNotFoundError:
            continue
        if not rows:
            continue
        pop = popper([p for p, _, _, _ in rows], arm="B")
        agg = collections.defaultdict(lambda: collections.Counter()); rate = {}
        for pr, rat, pos, grp in rows:
            for pk, vd in pop[pr]["verdicts"].items():
                for w, v in vd.items():
                    if w not in rat:
                        continue
                    a = agg[(w, pos)]; a["seen"] += 1; a["arrive"] += (v == 1)
                    rate[w] = rat[w]
        for (w, pos), c in agg.items():
            if c["seen"] < 10:
                continue
            outB.append(dict(corpus=corpus, word=w, position=pos, seen=c["seen"],
                             arrive=c["arrive"], rate=c["arrive"] / c["seen"],
                             **{k: rate[w][k] for k in SCALES_INST}))
    _save("words_armB", "per (corpus, word, position): how often a word ARRIVING from "
          "below min_prob cleared the renormalisation null", outB, min_seen=10)
    return out, outB


if __name__ == "__main__":
    main()
    word_tables()
