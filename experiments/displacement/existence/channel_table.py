"""One readable channel table: significance, words, and charge, in sortable columns.

    python channel_table.py                     # defaults below
    python channel_table.py --p 0.05 --min-prompts 10 --out results/wide.csv

## WHY THIS EXISTS

`adjacency.py --flow` writes two files and neither is readable alone. `--csv`
gives 42,944 channels with no words in them; `--examples` gives 586,528 word
pairs with no significance on them. The join kept being done by hand, and three
CSVs in `results/` are the residue: `flow_channels_with_examples.csv` is 42 rows
because someone cut at p<0.05 AND spec>1, and that rule is written down nowhere.
It was recovered by re-deriving it from the file's own contents.

So the cut travels IN the table, as `p_cut` and `min_prompts_cut` on every row.
Constant columns are the point: a slice of this file pasted into a draft still
says what produced it.

## BOTH SIGNS

Avoided channels outnumber preferred 13 to 1 and the convergence this folder
reports lives on the avoided side. A table keeping only spec>1 shows the
permitted set and silently drops the prohibition, which is the larger half.
`side` is a column; filter on it rather than at write time.

## THE CHARGE COLUMNS ARE SAMPLED, AND THE COLUMN NAMES SAY SO

`flow()` holds the full prompt set per channel (`chan_prompts`) only in memory,
so exact per-channel charge needs a re-run. The examples file carries up to
THREE prompts per word pair, which over many pairs per channel is a usable
sample of the same population -- `n_prompts_sampled` sits beside `n_prompts` so
the two are never confused, and their ratio is the sampling rate.

Word-level charge is weighted by `n_lineages`, the same convention the examples
pass ranks on: a pair thirty models agree about counts for more than one model's
idiosyncratic jump.

## WHAT EACH COLUMN SORTS

    spec           the headline. [P_obs(B|A)/P_obs(B)] / [P_null(B|A)/P_null(B)]
                   1.0 is chance. Row, column and cell-vocabulary effects all
                   cancel; see flow().
    obs_over_exp   the single-normalised version, row effect STILL IN IT. Higher
                   than spec by construction and not the headline.
    up / n         lineages with spec>1, over lineages measured
    n_prompts      distinct prompts. A channel on one scene is a fact about that
                   scene however many lineages replicate it.
    mean_dose      how charged the contributing SCENES are (charge.doses)
    mean_frame     how charged the setup alone is (charge.frame)
    mean_lift      dose - frame: what the candidate words add over the setup
    pct_dose_ge4   share of contributing prompts that are actually charged.
                   Separates "this channel lives at transgressive sites" from
                   "this channel is everywhere".
    faller_charge  mean in-context rating of the words that FELL   (1-7)
    riser_charge   mean in-context rating of the words that ROSE   (1-7)
    charge_drop    faller_charge - riser_charge. How much charge the channel
                   sheds, in rating points. The one order that is neither a
                   frequency order nor an effect-size order.
    faller_kind    modal charge.kinds() of the fallers: VIOLENT, SEXUAL, NONE...
    riser_kind     modal kind of the risers

Sorted by `p` within `side`, because every other default misleads invisibly: by
`n_prompts` the head is the narrative substrate (`called -> left`, 1,863
prompts), by `spec` it is noise (`A1.3+ -> T3-` at 6.93, p=0.845). Everything
else is a column so the reader can re-sort with the trade-off in view.
"""

import argparse
import collections
import csv
import os
import statistics as st
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", ".."))
from malignment import charge  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
CHANNELS = os.path.join(HERE, "results", "flow_allsrc_f500.csv")
#: per-example dumps run 2-148 MB, so they live outside the repo.
DATA = os.path.expanduser("~/malignment-data/existence")
EXAMPLES = os.path.join(DATA, "flow_allsrc_f500_examples.csv")
OUT = os.path.join(HERE, "results", "channel_table.csv")

COLS = ("side", "source", "source_label", "target", "target_label",
        "spec", "obs_over_exp", "p", "up", "n", "n_prompts",
        "mean_dose", "mean_frame", "mean_lift", "pct_dose_ge4",
        "faller_charge", "riser_charge", "charge_drop",
        "faller_kind", "riser_kind",
        "examples", "examples_in_context", "prompts",
        "n_prompts_sampled", "p_cut", "min_prompts_cut")


def _fmt(v, nd=3):
    return "" if v is None else ("%.*f" % (nd, v))


def _modal(counter):
    return counter.most_common(1)[0][0] if counter else ""


def build(channels=CHANNELS, examples=EXAMPLES, out=OUT,
          p_cut=0.001, min_prompts=25, n_examples=3):
    doses = charge.doses()
    lifts = charge.lifts()

    keep = {}
    rows = []
    with open(channels, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if float(r["p"]) >= p_cut or int(r.get("n_prompts") or 0) < min_prompts:
                continue
            r["side"] = "preferred" if float(r["spec"]) > 1 else "avoided"
            rows.append(r)
            keep[(r["source"], r["target"])] = {
                "ex": [], "prompts": set(), "pc": collections.Counter(),
                "fw": [], "rw": [],                       # (rating, weight)
                "fk": collections.Counter(), "rk": collections.Counter()}
    if not rows:
        print("no channel clears p<%g with >=%d prompts" % (p_cut, min_prompts))
        return 1
    print("  %d channels clear p<%g with >=%d distinct prompts"
          % (len(rows), p_cut, min_prompts))

    scene_cache, kind_cache = {}, {}

    def scene_of(pr):
        if pr not in scene_cache:
            scene_cache[pr] = charge.scene(pr) or {}
        return scene_cache[pr]

    def kind_of(pr):
        if pr not in kind_cache:
            kind_cache[pr] = charge.kinds(pr) or {}
        return kind_cache[pr]

    n_ex_rows = 0
    with open(examples, encoding="utf-8") as fh:
        for e in csv.DictReader(fh):
            k = (e["source"], e["target"])
            acc = keep.get(k)
            if acc is None:
                continue
            n_ex_rows += 1
            w = int(e["n_lineages"])
            prs_here = [x.strip() for x in e["prompts"].split(" | ") if x.strip()]
            acc["ex"].append((w, e["faller"], e["riser"],
                              prs_here[0] if prs_here else ""))
            for pr in prs_here:
                if pr not in doses:
                    continue
                acc["prompts"].add(pr)
                acc["pc"][pr] += w
                sc, kd = scene_of(pr), kind_of(pr)
                fr, rr = sc.get(e["faller"]), sc.get(e["riser"])
                if fr is not None:
                    acc["fw"].append((fr, w))
                if rr is not None:
                    acc["rw"].append((rr, w))
                if e["faller"] in kd:
                    acc["fk"][kd[e["faller"]]] += w
                if e["riser"] in kd:
                    acc["rk"][kd[e["riser"]]] += w
    print("  %d example rows matched; %d distinct prompts rated"
          % (n_ex_rows, len(scene_cache)))

    def wmean(pairs):
        tw = sum(w for _, w in pairs)
        return (sum(v * w for v, w in pairs) / tw) if tw else None

    rows.sort(key=lambda r: (r["side"], float(r["p"])))
    n_charge = 0
    with open(out, "w", newline="", encoding="utf-8") as fh:
        wtr = csv.writer(fh)
        wtr.writerow(COLS)
        for r in rows:
            a = keep[(r["source"], r["target"])]
            prs = [p for p in a["prompts"]]
            dv = [doses[p] for p in prs if doses.get(p) is not None]
            lv = [lifts[p] for p in prs if lifts.get(p) is not None]
            fv = [charge.frame(p) for p in prs]
            fv = [x for x in fv if x is not None]
            fc, rc = wmean(a["fw"]), wmean(a["rw"])
            if fc is not None and rc is not None:
                n_charge += 1
            ex = sorted(a["ex"], reverse=True)[:n_examples]
            wtr.writerow((
                r["side"], r["source"], r["source_label"], r["target"],
                r["target_label"], r["spec"], r.get("obs_over_exp", ""), r["p"],
                r["up"], r["n"], r["n_prompts"],
                _fmt(st.mean(dv) if dv else None),
                _fmt(st.mean(fv) if fv else None),
                _fmt(st.mean(lv) if lv else None),
                _fmt((sum(1 for x in dv if x >= 4) / len(dv)) if dv else None),
                _fmt(fc), _fmt(rc),
                _fmt((fc - rc) if (fc is not None and rc is not None) else None),
                _modal(a["fk"]), _modal(a["rk"]),
                "; ".join("%s->%s (%d)" % (f, g, n) for n, f, g, _ in ex),
                "  ||  ".join("%s->%s  <<%s>>" % (f, g, pr)
                              for n, f, g, pr in ex[:3] if pr),
                "  ||  ".join(pr for pr, _ in a["pc"].most_common(n_examples)),
                len(prs), p_cut, min_prompts))

    npref = sum(1 for r in rows if r["side"] == "preferred")
    print("-> %s" % out)
    print("   %d rows: %d preferred, %d avoided" % (len(rows), npref, len(rows) - npref))
    print("   %d of %d carry a charge_drop (both ends rated)" % (n_charge, len(rows)))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--channels", default=CHANNELS)
    ap.add_argument("--examples", default=EXAMPLES)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--p", type=float, default=0.001,
                    help="significance cut. Travels into the table as p_cut.")
    ap.add_argument("--min-prompts", type=int, default=25,
                    help="distinct prompts a channel needs. Travels into the "
                         "table as min_prompts_cut.")
    ap.add_argument("--n-examples", type=int, default=3)
    a = ap.parse_args(argv)
    return build(a.channels, a.examples, a.out, a.p, a.min_prompts, a.n_examples)


if __name__ == "__main__":
    sys.exit(main())
