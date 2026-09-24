"""The four contrasts dispute by dispute, grouped by domain. -> results/by_dispute.md

    python -u by_dispute.py

EXPLORATORY (RH, 2026-09-24: "do any of the results apply more or less to
particular subdomains?"). One to four disputes per domain, so domains are
described, not tested. Per dispute: the mean over lineages of the per-lineage
difference-in-differences (individual change minus institution change), with the
count of lineages each way; and F = the three frontier models' endpoint gap
(individual minus institution), DeepSeek excluded as self-coded.
"""
import collections, json, os, sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import analyse_regen as A  # noqa: E402

FRONTIER = os.path.expanduser("~/malignment-data/institution_vs_individual/coded_frontier.jsonl")
DOM = {"housing": ["housing_repairs", "housing_rent", "housing_deposit"],
       "labor": ["labor_credit", "labor_safety", "labor_layoff", "labor_benefits_cut"],
       "medical": ["medical_bill", "medical_referral"], "police": ["police_search"],
       "state": ["benefits_denial", "civic_highway", "immigration_visa"],
       "consumer": ["consumer_charge", "banking_fee", "utilities_bill", "insurance_denial"],
       "education": ["education_removal"]}
O = ["channel", "outward", "authority", "move_voice_direct"]


def main():
    rows = [json.loads(l) for l in open(A.SRC)]
    rows = [r for r in rows if r.get("coded") and A.keep(r["coded"])]
    arms = collections.defaultdict(set)
    for r in rows:
        arms[r["lineage"]].add(r["arm"])
    rows = [r for r in rows if arms[r["lineage"]] == {"base", "aligned"}]
    fr = [json.loads(l) for l in open(FRONTIER)]
    fr = [r for r in fr if r.get("coded") and A.keep(r["coded"]) and "deepseek" not in r["model"]]
    L = ["# The four contrasts by dispute (EXPLORATORY)", "",
         "Cells: mean per-lineage DiD (lineages +/-); F = frontier endpoint gap, individual minus institution.", "",
         "| domain | dispute | " + " | ".join(O) + " |", "|---|---|" + "---|" * len(O)]
    for d, ss in DOM.items():
        for s in ss:
            cells = []
            for n in O:
                c = collections.defaultdict(list)
                for r in rows:
                    if r["scenario"] == s:
                        c[(r["lineage"], r["arm"], r["side"])].append(A.outcomes(r["coded"])[n])
                dd = []
                for l in {k[0] for k in c}:
                    v = [c.get((l, a, sd)) for a in ("base", "aligned") for sd in ("individual", "institution")]
                    if all(v):
                        bi, bs, ai, as_ = (np.mean(x) for x in v)
                        dd.append((ai - bi) - (as_ - bs))
                fi = [A.outcomes(r["coded"])[n] for r in fr if r["scenario"] == s and r["side"] == "individual"]
                fs = [A.outcomes(r["coded"])[n] for r in fr if r["scenario"] == s and r["side"] == "institution"]
                cells.append("%+.2f (%d/%d) F%+.2f" % (np.mean(dd), sum(x > 0 for x in dd), sum(x < 0 for x in dd),
                                                        np.mean(fi) - np.mean(fs)))
            L.append("| %s | %s | %s |" % (d, s, " | ".join(cells)))
    open(os.path.join(HERE, "results", "by_dispute.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
