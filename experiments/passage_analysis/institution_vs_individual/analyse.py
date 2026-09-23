"""The declared contrast over results/coded.jsonl. -> results/analysis.md

    python -u analyse.py

WRITTEN 2026-09-23 WHILE THE CODING RAN, BEFORE ANY CODED ROW WAS READ. The
contrast is the one in README.md "To agree before running", unchanged.

ARMS. Open families with a base checkpoint (10), base against each family's LAST
stage (rlvr > dpo > sft), the arm `slot_ratings/institutional/f21_prompt_unit.py`
declared. `llama` has no base row and is left out; the four frontier chat models
have no base and are reported separately, as an endpoint contrast.

FORM FILTER. Outcomes are computed on continuation and advice only. The form
distribution itself is reported first, per arm, as its own alignment effect.

OUTCOMES, per generation, counting only referrals the text RECOMMENDS or marks
correct (a listed quiz option is not a referral the text makes):

    any        any third party at all
    outward    a public_authority or collective
    inward     a speaker_side body (own organisation, retained agent)
    channel    a counterparty_side body (the other party's own apparatus)
    authority  any body with authority over the counterparty

and `primary_move` shares. Also `perspective_kept` = False as an outcome.

CONTRAST. For each outcome, per (family, pair): the base->aligned change in the
share on the individual side, minus the same on the institution side. Units: the
12 matched pairs (mean over families) and the 10 families (mean over pairs),
each with a two-sided sign test. The DIRECTION hypothesis is two one-line
predictions, stated here before the data: `outward` rises more on the individual
side (difference > 0); `inward` rises more on the institution side (< 0).
Nothing else here is a prediction.
"""
import collections, json, os

import numpy as np
from scipy.stats import binomtest

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.expanduser("~/malignment-data/institution_vs_individual/coded.jsonl")
OUT = os.path.join(HERE, "results", "analysis.md")

LAST = {"olmo": "rlvr", "olmo-tiny": "rlvr", "tulu": "rlvr", "zephyr": "dpo",
        "amber": "dpo", "pythia": "dpo", "qwen": "dpo", "qwen-tiny": "dpo",
        "smol": "dpo", "deepseek-7b": "dpo"}
KEEP_FORM = {"continuation", "advice"}
TAKEN = {"recommended", "marked_correct"}
OUTCOMES = ["any", "outward", "inward", "channel", "authority", "move_exit",
            "move_voice_direct", "move_third_party", "move_self_help",
            "move_accept", "perspective_flip"]
PRED = {"outward": "> 0", "inward": "< 0"}


def pair_of(key):
    dom, role, n = key.split("_")
    return "%s_%s" % (dom, n)


def outcomes(c):
    refs = [r for r in c["referrals"] if r["stance"] in TAKEN]
    rel = {r["relation"] for r in refs}
    o = {"any": bool(refs),
         "outward": bool(rel & {"public_authority", "collective"}),
         "inward": "speaker_side" in rel,
         "channel": "counterparty_side" in rel,
         "authority": any(r["authority_over_counterparty"] for r in refs),
         "perspective_flip": not c["perspective_kept"]}
    for m in ("exit", "voice_direct", "third_party", "self_help", "accept"):
        o["move_" + m] = c["primary_move"] == m
    return o


def sign(xs):
    up = sum(x > 0 for x in xs); dn = sum(x < 0 for x in xs)
    return up, dn, (binomtest(up, up + dn).pvalue if up + dn else 1.0)


def main():
    rows = [json.loads(l) for l in open(SRC)]
    rows = [r for r in rows if r["coded"]]
    L = ["# institution_vs_individual: the declared contrast", "",
         "Producer `analyse.py`, written before any coded row was read. %d coded rows." % len(rows), ""]

    # ---- form, per arm --------------------------------------------------------
    def arm(r):
        if r["family"] in LAST:
            return "base" if r["layer"] == "base" else ("aligned" if r["layer"] == LAST[r["family"]] else None)
        if r["layer"] == "unknown":
            return "frontier"
        return None
    forms = collections.defaultdict(collections.Counter)
    for r in rows:
        a = arm(r)
        if a:
            forms[a][r["coded"]["form"]] += 1
    L += ["## Form, by arm", "", "| arm | n | " + " | ".join(
        ["continuation", "advice", "quiz_item", "web_boilerplate", "other_language", "degenerate"]) + " |",
          "|---|---|" + "---|" * 6]
    for a in ("base", "aligned", "frontier"):
        n = sum(forms[a].values())
        L.append("| %s | %d | " % (a, n) + " | ".join("%.1f%%" % (100 * forms[a][f] / n) for f in
                 ["continuation", "advice", "quiz_item", "web_boilerplate", "other_language", "degenerate"]) + " |")
    L.append("")
    qb = collections.defaultdict(lambda: [0, 0])
    for r in rows:
        a = arm(r)
        if a in ("base", "aligned"):
            qb[(r["family"], a)][0] += r["coded"]["form"] == "quiz_item"
            qb[(r["family"], a)][1] += 1
    d = [qb[(f, "aligned")][0] / qb[(f, "aligned")][1] - qb[(f, "base")][0] / qb[(f, "base")][1] for f in LAST]
    up, dn, p = sign(d)
    L += ["Quiz share, aligned minus base, by family: %d up / %d down, p=%.3g." % (up, dn, p), ""]

    # ---- the contrast ---------------------------------------------------------
    acc = collections.defaultdict(lambda: collections.defaultdict(list))  # (fam, pair, side, arm) -> outcome -> [0/1]
    for r in rows:
        a = arm(r)
        if a not in ("base", "aligned") or r["coded"]["form"] not in KEEP_FORM:
            continue
        o = outcomes(r["coded"])
        k = (r["family"], pair_of(r["key"]), r["side"], a)
        for name, v in o.items():
            acc[k][name].append(v)
    #: The second entry is POST-HOC, added after the first table was read
    #: (promised to RH before the run finished, 2026-09-23): only the pairs whose
    #: two prompts both end "I should". F21's other six pairs mix endings, and the
    #: site moves `procedural` +0.221 on M03, more than the position contrast. A
    #: ROBUSTNESS CHECK, not part of the declared test.
    for pairs, title in ((sorted({k[1] for k in acc}), "## Base -> aligned, individual side minus institution side"),
                         (["govt_1", "housing_1", "housing_2", "labor_2", "medical_1", "police_1"],
                          "## POST-HOC robustness: the 6 pairs ending \"I should\" on both sides")):
      L += [title, "",
            "Continuation and advice only; referrals counted only if recommended or marked correct. "
            "`diff` = (aligned - base on the individual side) - (aligned - base on the institution side). "
            "Cells missing a side or an arm after the form filter are dropped from that unit.", "",
            "| outcome | base ind | base inst | aligned ind | aligned inst | pairs +/- | p | families +/- | p | predicted |",
            "|---|---|---|---|---|---|---|---|---|---|"]
      for name in OUTCOMES:
          def share(f, pr, side, a):
              v = acc.get((f, pr, side, a), {}).get(name)
              return np.mean(v) if v else None
          cell = {}
          for f in LAST:
              for pr in pairs:
                  s = [share(f, pr, sd, a) for sd in ("individual", "institution") for a in ("base", "aligned")]
                  if None not in s:
                      ib, ia, jb, ja = s
                      cell[(f, pr)] = ((ia - ib) - (ja - jb), ib, ia, jb, ja)
          byp = [np.mean([v[0] for (f, pr), v in cell.items() if pr == q]) for q in pairs
                 if any(pr == q for (_, pr) in cell)]
          byf = [np.mean([v[0] for (f, pr), v in cell.items() if f == fam]) for fam in LAST
                 if any(f == fam for (f, _) in cell)]
          lv = [np.mean([v[i] for v in cell.values()]) for i in (1, 3, 2, 4)]
          pu, pd_, pp = sign(byp); fu, fd, fp = sign(byf)
          L.append("| %s | %.3f | %.3f | %.3f | %.3f | %d/%d | %.3g | %d/%d | %.3g | %s |"
                   % (name, lv[0], lv[1], lv[2], lv[3], pu, pd_, pp, fu, fd, fp, PRED.get(name, "")))
      L.append("")

    # ---- frontier endpoint ----------------------------------------------------
    fr = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in rows:
        if arm(r) != "frontier" or r["coded"]["form"] not in KEEP_FORM:
            continue
        for name, v in outcomes(r["coded"]).items():
            fr[(r["family"], pair_of(r["key"]), r["side"])][name].append(v)
    models = sorted({k[0] for k in fr})
    L += ["## Frontier chat models: individual minus institution (no base arm)", "",
          "| outcome | " + " | ".join(m.split("/")[-1] for m in models) + " | pairs +/- (pooled over models) | p |",
          "|---|" + "---|" * (len(models) + 2)]
    for name in OUTCOMES:
        cells = []
        for m in models:
            ind = [x for (mm, pr, sd), o in fr.items() if mm == m and sd == "individual" for x in o[name]]
            ins = [x for (mm, pr, sd), o in fr.items() if mm == m and sd == "institution" for x in o[name]]
            cells.append("%.2f / %.2f" % (np.mean(ind), np.mean(ins)) if ind and ins else "n/a")
        dp = []
        for q in pairs:
            a = [np.mean(o[name]) for (mm, pr, sd), o in fr.items() if pr == q and sd == "individual"]
            b = [np.mean(o[name]) for (mm, pr, sd), o in fr.items() if pr == q and sd == "institution"]
            if a and b:
                dp.append(np.mean(a) - np.mean(b))
        u, dd, p = sign(dp)
        L.append("| %s | %s | %d/%d | %.3g |" % (name, " | ".join(cells), u, dd, p))
    L += ["", "Cells read individual / institution.", ""]
    ok = sum(r.get("spans_ok", 0) for r in rows); tot = sum(r.get("spans_total", 0) for r in rows)
    L += ["Span verification: %d of %d quoted spans found verbatim in their text (%.1f%%)." % (ok, tot, 100 * ok / max(tot, 1))]
    open(OUT, "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
