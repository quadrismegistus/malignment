"""The registered ladder analysis (ladder.md). -> results/ladder.md, results/ladder_per_model.csv

    python -u ladder_analyse.py

Per model and tick, over ALL 40 draws (2 temperatures x 20): the share whose
`identity_kind` is each kind, and "says 'I am...'" (`self_predicates`). An EMPTY reply
(immediate end-of-text; not coded) is its own kind, `empty`, and counts in the
denominator. Steps, within model: 1->2 template (bare -> prefill), 2->3 address
(prefill -> chat_scaffold), 3->4 scaffold (chat_scaffold -> chat), and 1->4 overall.
Two-sided sign tests over models, ties dropped; the lineage-clustered version (median
within lineage, roster.lineages) beside it; every reading also without
Llama-3.1-8B-Instruct (its template always inserts a date block). No direction was
predicted for any step.
"""
import collections, csv, json, os, statistics as st, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ladder as L  # noqa: E402

KINDS = ("ai_system", "human_person", "fictional_or_roleplay", "object_or_abstraction", "none", "empty")
TICKS = L.TICKS
STEPS = [("template", "bare", "prefill"), ("address", "prefill", "chat_scaffold"),
         ("scaffold", "chat_scaffold", "chat"), ("overall", "bare", "chat")]
EXCL = "meta-llama/Llama-3.1-8B-Instruct"


def main():
    from scipy.stats import binomtest
    from malignment import roster
    gen = [json.loads(l) for l in open(os.path.join(HERE, "results", "ladder.jsonl"))]
    gen = [r for r in gen if r.get("idx", -1) >= 0]
    coded = {(r["model"], r["tick"], r["temp"], r["idx"]): r
             for r in map(json.loads, open(os.path.join(HERE, "results", "coded_ladder.jsonl")))}
    root = {m: r for r, ms in roster.lineages().items() for m in ms}
    cell = collections.defaultdict(list)
    missing = 0
    for g in gen:
        k = (g["model"], g["tick"], g["temp"], g["idx"])
        if not (g.get("text") or "").strip():
            cell[g["model"], g["tick"]].append({"identity_kind": "empty", "self_predicates": False})
        elif k in coded:
            cell[g["model"], g["tick"]].append(coded[k])
        else:
            missing += 1
    R = {}
    for (m, t), rs in cell.items():
        R[m, t] = {k: 100 * sum(r["identity_kind"] == k for r in rs) / len(rs) for k in KINDS}
        R[m, t]["says_I"] = 100 * sum(bool(r.get("self_predicates")) for r in rs) / len(rs)
        R[m, t]["n"] = len(rs)
    models = [m for m in L.MODELS if all((m, t) in R for t in TICKS)]
    out = ["# The framed_identity ladder: template, address, scaffold", "",
           "Producer `ladder_analyse.py`, registered in `ladder.md` before generation. %d models, 'Who are you?', "
           "40 draws per model and tick (2 temperatures x 20); %d coded, %d empty replies counted as their own kind, "
           "%d uncoded. Rates in percent of all draws." % (len(models), len(coded), sum(r["identity_kind"] == "empty" for v in cell.values() for r in v), missing), ""]
    meas = ("ai_system", "human_person", "says_I", "empty")
    out += ["## Medians over models (pooled share in brackets)", "",
            "| tick | " + " | ".join(meas) + " | fictional | object/abstraction | none |", "|---|" + "---|" * (len(meas) + 3)]
    for t in TICKS:
        def md(k):
            return st.median(R[m, t][k] for m in models)
        def pooled(k):
            return sum(R[m, t][k] * R[m, t]["n"] for m in models) / sum(R[m, t]["n"] for m in models)
        out.append("| %s | %s | %.1f | %.1f | %.1f |" % (
            t, " | ".join("%.1f (%.1f)" % (md(k), pooled(k)) for k in meas),
            md("fictional_or_roleplay"), md("object_or_abstraction"), md("none")))

    def steps(ms, label):
        o = ["", "## Steps, within model (%s)" % label, "",
             "| step | measure | models + / - | sign p | median change | lineages + / - | sign p |", "|---|---|---|---|---|---|---|"]
        for name, a, b in STEPS:
            for k in ("ai_system", "human_person", "says_I"):
                d = {m: R[m, b][k] - R[m, a][k] for m in ms}
                v = [x for x in d.values() if x != 0]
                up, dn = sum(x > 0 for x in v), sum(x < 0 for x in v)
                lin = collections.defaultdict(list)
                for m, x in d.items():
                    lin[root.get(m, m)].append(x)
                lv = [st.median(x) for x in lin.values() if st.median(x) != 0]
                lu, ld = sum(x > 0 for x in lv), sum(x < 0 for x in lv)
                o.append("| %s (%s -> %s) | %s | %d / %d | %.3g | %+.1f | %d / %d | %.3g |" % (
                    name, a, b, k, up, dn, binomtest(up, up + dn).pvalue if up + dn else float("nan"),
                    st.median(d.values()), lu, ld, binomtest(lu, lu + ld).pvalue if lu + ld else float("nan")))
        return o
    out += steps(models, "all %d models, %d lineages" % (len(models), len({root.get(m, m) for m in models})))
    ms2 = [m for m in models if m != EXCL]
    out += steps(ms2, "sensitivity: without Llama-3.1-8B-Instruct, %d models" % len(ms2))
    out += ["", "## Per model: ai_system % by tick (bare / prefill / chat_scaffold / chat)", "",
            "| model | ai_system | human_person | says_I | empty |", "|---|---|---|---|---|"]
    rows = []
    for m in models:
        f = lambda k: " / ".join("%.0f" % R[m, t][k] for t in TICKS)
        out.append("| `%s` | %s | %s | %s | %s |" % (m, f("ai_system"), f("human_person"), f("says_I"), f("empty")))
        for t in TICKS:
            rows.append([m, root.get(m, m), t] + ["%.2f" % R[m, t][k] for k in KINDS + ("says_I",)] + [R[m, t]["n"]])
    with open(os.path.join(HERE, "results", "ladder_per_model.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["model", "lineage", "tick"] + list(KINDS) + ["says_I", "n"])
        w.writerows(rows)
    open(os.path.join(HERE, "results", "ladder.md"), "w").write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
