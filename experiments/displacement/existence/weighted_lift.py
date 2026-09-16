"""Mass-weighted mean CHARGE of the next word, per arm. -> results/weighted_*.json

    python -u weighted_lift.py --by lift      # scene - frame, UNCLAMPED
    python -u weighted_lift.py --by scene     # raw scene 1-7

Per cell, `sum(p * k) / sum(p)`: the charge of whatever the model is about to
say, weighted by how likely it is to say it. Then the mean over that lineages
cells, then a median over the 50 endpoint lineages.

**THE TWO ARMS DIFFER BY THE SAME AMOUNT UNDER EITHER `--by`**, to 4e-16: the
frame rating is constant within a cell, so `mean(scene - frame) = mean(scene) -
frame` and the constant cancels in `aligned - base`. Subtracting the frame moves
the LEVEL and cannot move the CHANGE -- so the choice is presentational, and it
is a trap: lift makes the same movement read as -9.8%% where dose reads -0.79%%,
purely by putting a smaller number underneath. Quote the level with the
percentage or neither.

**LIFT IS UNCLAMPED HERE**, unlike the seven-line figures, which pool below -1
and above +4 because those bands cannot carry a median. A mean has no such
problem and clamping would pull in exactly the tails where alignment acts.
"""
import argparse, collections, json, os, statistics as st, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(HERE))))

_ap = argparse.ArgumentParser(description=__doc__.splitlines()[0],
                              formatter_class=argparse.RawDescriptionHelpFormatter)
_ap.add_argument("--by", default="lift", choices=["lift", "scene"],
                 help="lift = scene minus the CELL's frame rating; scene = raw "
                      "1-7. The two give the SAME aligned-base movement to "
                      "4e-16 -- the frame is constant within a cell and cancels "
                      "in the difference -- so this changes the level only.")
_ap.add_argument("--out", default=None)
_A = _ap.parse_args()
BY = _A.by
from malignment import charge, roster, vectors as V

def annotation():
    out = {}
    for src in charge.sources():
        if "_zh" in os.path.basename(src):
            continue
        for line in open(src, "rb"):
            r = json.loads(line)
            fr = r.get("frame")
            if fr is None:
                continue
            #: UNCLAMPED. Clamping -1..+4 was right for seven discrete lines and
            #: is wrong for a MEAN: it pulls the tails toward the centre, and the
            #: tails are exactly where alignment is doing something.
            out[(r["prompt"], r["base"])] = {
                w["word"]: (int(w["scene"]) - int(fr) if BY == "lift"
                            else int(w["scene"])) for w in r["words"]}
    return out

ann = annotation()
eps, _ = roster.endpoints()
rows = []
for i, (b, a) in enumerate(sorted(eps.items()), 1):
    got = V.rows("SELECT prompt, word, p_base, p_aligned FROM movement_v4 "
                 "WHERE base={b:String} AND aligned={a:String} "
                 "AND frame_base='' AND frame_aligned=''", b=b, a=a)
    if not got:
        continue
    byp = collections.defaultdict(list)
    for r in got:
        byp[r["prompt"]].append(r)
    cb, ca = [], []
    for p, rs in byp.items():
        w = ann.get((p, b))
        if not w:
            continue
        nb = db = na = da = 0.0
        for r in rs:
            L = w.get(r["word"])
            if L is None:
                continue
            pb = float(r["p_base"] or 0.0); pa = float(r["p_aligned"] or 0.0)
            nb += pb * L; db += pb
            na += pa * L; da += pa
        if db > 0 and da > 0:
            cb.append(nb / db); ca.append(na / da)
    if cb:
        rows.append({"lineage": "%s>%s" % (b, a), "n_cells": len(cb),
                     "base": st.mean(cb), "aligned": st.mean(ca)})
        print("  %2d %-44s %5d cells  base %+.4f  aligned %+.4f"
              % (i, b.split("/")[-1][:44], len(cb), rows[-1]["base"],
                 rows[-1]["aligned"]), flush=True)
out = {"built": time.strftime("%Y-%m-%d %H:%M"), "n_lineages": len(rows),
       "n_cells": sum(r["n_cells"] for r in rows), "per_lineage": rows}
_out = _A.out or os.path.join(HERE, "results", "weighted_%s.json" % BY)
os.makedirs(os.path.dirname(_out), exist_ok=True)
json.dump(out, open(_out, "w"), indent=1)
print("-> %s" % _out)
d = [r["aligned"] - r["base"] for r in rows]
print("\nlineages %d, cells %d" % (len(rows), out["n_cells"]))
print("median mass-weighted lift   base %+.5f   aligned %+.5f"
      % (st.median([r["base"] for r in rows]), st.median([r["aligned"] for r in rows])))
print("paired within-lineage delta median %+.5f   down in %d/%d lineages"
      % (st.median(d), sum(1 for x in d if x < 0), len(d)))
