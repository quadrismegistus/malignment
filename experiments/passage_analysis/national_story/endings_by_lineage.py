"""How national stories end, base against aligned, counted by lineage.

    python endings_by_lineage.py            -> results/endings_by_lineage.md

Added 2026-09-24 by the paper seat (TheoryMachines) beside this folder's own
producers, to give the Critical Inquiry draft's Form section a committed source
for two sentences: in aligned stories the opposition endures less often and
the story more often ends by handing something down.

SOURCE. `conflict.sqlite` (export_db.py), table `stories`: the judged corpus
(`judge_pure_story` only; see conflict.py), each story coded once by
`code_story_conflict_v1` (deepseek-v4-flash) for, among other fields,
`opponent_fate` (endures, prevails, dissolved, absent, dropped, withdraws,
defeated, converted) and `ending` (open, none, loss, departure, stays,
reconciliation, restoration, bequest). Raw frame only: no chat template on
either arm.

METHOD. Unit = lineage. Per lineage and arm, the share of stories carrying each
value. A lineage enters if each arm has at least MIN_STORIES stories. For each
value: lineages where the aligned share is higher / lower (ties dropped), the
median aligned-minus-base difference, and a two-sided sign test over lineages.
Descriptive and post hoc: the values were read off the coded store, not
declared; no correction across the 16 values.
"""
import collections
import os
import sqlite3
import statistics as st
import sys

from scipy.stats import binomtest

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "conflict.sqlite")
OUT = os.path.join(HERE, "results", "endings_by_lineage.md")
MIN_STORIES = 10
FIELDS = {"opponent_fate": ["endures", "prevails", "dissolved", "absent", "dropped",
                            "withdraws", "defeated", "converted"],
          "ending": ["open", "none", "loss", "departure", "stays",
                     "reconciliation", "restoration", "bequest"]}


def main():
    db = sqlite3.connect(DB)
    rows = db.execute("SELECT lineage, arm, opponent_fate, ending FROM stories "
                      "WHERE frame = 'raw'").fetchall()
    agg = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    for lin, arm, fate, end in rows:
        c = agg[lin][arm]
        c["n"] += 1
        c["opponent_fate=" + str(fate)] += 1
        c["ending=" + str(end)] += 1
    lins = [l for l, a in agg.items()
            if a["base"]["n"] >= MIN_STORIES and a["aligned"]["n"] >= MIN_STORIES]
    nb = sum(agg[l]["base"]["n"] for l in lins)
    na = sum(agg[l]["aligned"]["n"] for l in lins)
    L = ["# How national stories end, base against aligned, by lineage", "",
         "Producer `endings_by_lineage.py` (paper seat, 2026-09-24). Raw frame, judged pure stories, "
         "coded by `code_story_conflict_v1`. %d lineages with at least %d stories in each arm "
         "(%d base stories, %d aligned). Descriptive and post hoc; no correction across values."
         % (len(lins), MIN_STORIES, nb, na), ""]
    for field, values in FIELDS.items():
        L += ["## %s" % field, "",
              "| value | pooled base | pooled aligned | aligned higher | aligned lower | median diff | sign p |",
              "|---|---|---|---|---|---|---|"]
        for v in values:
            key = "%s=%s" % (field, v)
            up = dn = 0
            diffs = []
            for l in lins:
                pb = agg[l]["base"][key] / agg[l]["base"]["n"]
                pa = agg[l]["aligned"][key] / agg[l]["aligned"]["n"]
                diffs.append(pa - pb)
                up += pa > pb
                dn += pa < pb
            pooled_b = sum(agg[l]["base"][key] for l in lins) / nb
            pooled_a = sum(agg[l]["aligned"][key] for l in lins) / na
            p = binomtest(up, up + dn).pvalue if up + dn else float("nan")
            L.append("| %s | %.3f | %.3f | %d | %d | %+.3f | %.2g |"
                     % (v, pooled_b, pooled_a, up, dn, st.median(diffs), p))
        L.append("")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w").write("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    sys.exit(main())
