"""F21's own annotation task on a sample of the regeneration and all frontier passages.
-> ~/malignment-data/institution_vs_individual/f21task_{regen,frontier}.jsonl, results/f21_task.md

    python -u f21_task_sample.py --run      sample, code (cached), analyse
    python -u f21_task_sample.py            analyse only

WRITTEN AND COMMITTED 2026-09-24 BEFORE ANY PASSAGE WAS CODED WITH THIS TASK. RH's
request: run F21's instrument on the new texts, so that F21's scales and the
referral codes can be compared on the SAME passages.

INSTRUMENT. `largeliterarymodels.tasks.AlignmentAsymmetryTask` unchanged (12
fields: agency, institutional_deference, assertiveness, power_acknowledgment,
strategy_specificity 1-5; apology_present, specific_rights_named,
concrete_action_recommended, homework_assigned, delay_advised; tone; lists), with
F21's input convention (`prepare_alignment_text`): base continuations wrapped as
`[context] prompt [text] continuation`, chat and API responses scored as-is. Model:
`deepseek/deepseek-flash` -- F21 ran on `deepseek-chat`, which the API now
resolves to flash.

SAMPLE. From passages that pass the referral analysis filter (`analyse_regen.keep`)
in lineages with both arms: up to 30 per (lineage, arm, side) cell, seeded
(20260924), about 5,000. Plus all 1,440 frontier API passages (filtered the same
way at analysis). The same passages carry the referral codes, so the two
instruments can be joined.

WHAT IS EXPECTED, stated before the data:

  E1  institutional_deference: the side difference in the base->aligned change is
      NULL at the lineage unit -- F21's own unit result, now on new texts. If it
      is null here while the referral contrasts (P1-P4) are not, a deference scale
      cannot see where a party is SENT.
  E2  specific_rights_named, concrete_action_recommended, strategy_specificity:
      the individual gains MORE than the institution (they should track referral).
  E3  convergent/divergent validity on joined passages: referral to a
      counterparty channel or a public authority should raise strategy_specificity
      and specific_rights_named; it need not move institutional_deference.
  apology_present is reported (F21's fragile 9/1 vs 7/3), with no expectation.

Units: lineage and dispute sign tests on the side-difference-in-change, as in
`analyse_regen.py`; descriptive, no correction. Frontier: endpoint individual-
minus-institution per model.
"""
import collections, json, os, random, sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import analyse_regen as A  # noqa: E402

D = os.path.expanduser("~/malignment-data/institution_vs_individual")
FRONTIER = os.path.join(D, "coded_frontier.jsonl")
OUT_R, OUT_F = os.path.join(D, "f21task_regen.jsonl"), os.path.join(D, "f21task_frontier.jsonl")
PER_CELL = 30
MODEL = "deepseek/deepseek-flash"
SCALES = ["institutional_deference", "agency", "assertiveness", "power_acknowledgment",
          "strategy_specificity"]
FLAGS = ["specific_rights_named", "concrete_action_recommended", "apology_present",
         "homework_assigned", "delay_advised"]


def sample_regen():
    rows = [json.loads(l) for l in open(A.SRC)]
    rows = [r for r in rows if r.get("coded") and A.keep(r["coded"])]
    arms = collections.defaultdict(set)
    for r in rows:
        arms[r["lineage"]].add(r["arm"])
    cells = collections.defaultdict(list)
    for r in rows:
        if arms[r["lineage"]] == {"base", "aligned"}:
            cells[(r["lineage"], r["arm"], r["side"])].append(r)
    rnd = random.Random(20260924)
    out = []
    for k in sorted(cells):
        c = cells[k]
        out += c if len(c) <= PER_CELL else rnd.sample(c, PER_CELL)
    return out


def code(rows, is_base, path):
    from largeliterarymodels.tasks.score_alignment_asymmetry import (AlignmentAsymmetryTask,
                                                                      prepare_alignment_text)
    prompts = [prepare_alignment_text(r["text"], r["prompt"] if is_base(r) else None) for r in rows]
    errors = {}
    res = AlignmentAsymmetryTask().map(prompts, model=MODEL, num_workers=16, errors=errors)
    with open(path, "w") as fh:
        for r, x in zip(rows, res):
            fh.write(json.dumps(dict(r, f21=x.model_dump() if x else None)) + "\n")
    print("%s: coded %d of %d" % (os.path.basename(path), len(rows) - len(errors), len(rows)), flush=True)


def val(r, f):
    v = r["f21"][f]
    return float(v) if not isinstance(v, bool) else float(v)


def side_did(rows, unit, f):
    c = collections.defaultdict(list)
    for r in rows:
        if r.get("f21"):
            c[(r[unit], r["arm"], r["side"])].append(val(r, f))
    out = []
    for u in sorted({k[0] for k in c}):
        v = {(a, s): c.get((u, a, s)) for a in ("base", "aligned") for s in ("individual", "institution")}
        if all(v.values()):
            m = {k: np.mean(x) for k, x in v.items()}
            out.append((m[("aligned", "individual")] - m[("base", "individual")])
                       - (m[("aligned", "institution")] - m[("base", "institution")]))
    return out


def main():
    if "--run" in sys.argv:
        code(sample_regen(), lambda r: r["arm"] == "base", OUT_R)
        fr = [json.loads(l) for l in open(FRONTIER)]
        code(fr, lambda r: False, OUT_F)
    R = [json.loads(l) for l in open(OUT_R)]
    R = [r for r in R if r.get("f21")]
    F = [json.loads(l) for l in open(OUT_F)]
    F = [r for r in F if r.get("f21") and r.get("coded") and A.keep(r["coded"])]
    L = ["# F21's annotation task on the regeneration sample and the frontier", "",
         "Producer `f21_task_sample.py`, committed before coding. %d regeneration passages (up to %d per "
         "lineage x arm x side cell), %d kept frontier passages. Model %s." % (len(R), PER_CELL, len(F), MODEL), ""]
    L += ["## Base -> aligned, individual change minus institution change", "",
          "| field | base ind | base inst | aligned ind | aligned inst | lineages +/- | p | disputes +/- | p | expected |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    exp = {"institutional_deference": "E1 null", "specific_rights_named": "E2 > 0",
           "concrete_action_recommended": "E2 > 0", "strategy_specificity": "E2 > 0"}
    for f in SCALES + FLAGS:
        m = {(a, s): np.mean([val(r, f) for r in R if r["arm"] == a and r["side"] == s])
             for a in ("base", "aligned") for s in ("individual", "institution")}
        lu, ld, lp = A.sign(side_did(R, "lineage", f))
        du, dd, dp = A.sign(side_did(R, "scenario", f))
        L.append("| %s | %.2f | %.2f | %.2f | %.2f | %d/%d | %.3g | %d/%d | %.3g | %s |" % (
            f, m[("base", "individual")], m[("base", "institution")], m[("aligned", "individual")],
            m[("aligned", "institution")], lu, ld, lp, du, dd, dp, exp.get(f, "")))
    L += ["", "## E3: the two instruments on the same passages (regeneration sample)", "",
          "Mean F21 field for passages WITH vs WITHOUT each referral code.", "",
          "| referral code | n with | " + " | ".join(SCALES + ["specific_rights_named"]) + " |",
          "|---|---|" + "---|" * (len(SCALES) + 1)]
    for code_name in ("channel", "outward", "authority", "move_voice_direct", "inward"):
        yes = [r for r in R if A.outcomes(r["coded"])[code_name]]
        no = [r for r in R if not A.outcomes(r["coded"])[code_name]]
        cells = ["%.2f / %.2f" % (np.mean([val(r, f) for r in yes]), np.mean([val(r, f) for r in no]))
                 for f in SCALES + ["specific_rights_named"]]
        L.append("| %s | %d | %s |" % (code_name, len(yes), " | ".join(cells)))
    L += ["", "Cells: with / without.", "", "## Frontier: individual / institution at the endpoint", "",
          "| field | " + " | ".join(m.split("/")[-1] for m in sorted({r["model"] for r in F})) + " |",
          "|---|" + "---|" * len({r["model"] for r in F})]
    for f in SCALES + FLAGS:
        cells = []
        for mdl in sorted({r["model"] for r in F}):
            a = [val(r, f) for r in F if r["model"] == mdl and r["side"] == "individual"]
            b = [val(r, f) for r in F if r["model"] == mdl and r["side"] == "institution"]
            cells.append("%.2f / %.2f" % (np.mean(a), np.mean(b)))
        L.append("| %s | %s |" % (f, " | ".join(cells)))
    open(os.path.join(HERE, "results", "f21_task.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
