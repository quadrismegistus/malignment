"""The declared test on the 256-token regeneration. -> results/analysis_regen.md

    python -u analyse_regen.py

WRITTEN 2026-09-23 WHILE THE FLEET WAS GENERATING, BEFORE ANY REGENERATED
PASSAGE WAS READ OR CODED. Everything below is fixed by the pass-1 v2 result
(results/analysis_v2.md), which is where the predictions come from.

POPULATION. `coded_regen.jsonl` (run_regen.py): 18 disputes x both sides, all
"I should", n=10 per model per prompt, 256 tokens; base arm raw, aligned arm
chat (the frame is part of the contrast and is stated, not hidden). A lineage
enters only with BOTH arms coded.

FILTER, the pass-1 v2 rule unchanged: form continuation or advice, coherent,
perspective_kept. user_request, quiz_item, boilerplate, other language and
degenerate are excluded and their shares reported per arm.

OUTCOMES, the pass-1 definitions unchanged (referrals counted only when
recommended or marked correct): outward, inward, channel, authority, any, and
the primary-move shares.

CONTRAST. Per (lineage, scenario): (aligned - base share on the individual side)
- (aligned - base on the institution side). Units: the 18 scenarios (mean over
lineages) and the lineages (mean over scenarios), each a two-sided sign test.

FOUR PREDICTIONS, from pass 1 v2, stated before the data:

    P1  outward            diff > 0   individual sent to authority/collective more
    P2  move_voice_direct  diff < 0   institution gets direct voice more
    P3  authority          diff > 0   individual sent to bodies with power over the counterparty
    P4  channel            diff > 0   individual sent into the counterparty's own apparatus

A prediction is SUPPORTED if its sign test is p < 0.05 in the predicted direction
on BOTH units, after Holm correction over the four on each unit. `inward` and the
other moves are reported, not tested. The aligned-arm individual-minus-institution
level (the frontier comparison) is reported descriptively.
"""
import collections, json, os

import numpy as np
from scipy.stats import binomtest

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.expanduser("~/malignment-data/institution_vs_individual/coded_regen.jsonl")
#: LINEAGES WHOSE PASSAGES ARE NOISE IN EVERY CELL (2026-09-24, found by the dario
#: seat). internlm2: 1,080 of 1,080 passages (base raw, aligned chat, aligned raw)
#: coded degenerate/incoherent -- word salad under vLLM 0.22.1 even with the
#: sentencepiece 0.2.1 / no-tiktoken environment, which fixed the tokenizer LOAD and
#: not the output. The `keep` filter already drops every one of them, so the coded
#: analyses are unchanged; producers that count UNFILTERED passages must drop the
#: lineage here or they count 720 noise passages as a 43rd lineage.
BROKEN_LINEAGES = {"internlm/internlm2-base-7b"}
OUT = os.path.join(HERE, "results", "analysis_regen.md")
KEEP_FORM = {"continuation", "advice"}
TAKEN = {"recommended", "marked_correct"}
FORMS = ["continuation", "advice", "user_request", "quiz_item", "web_boilerplate",
         "other_language", "degenerate"]
PRED = {"outward": 1, "move_voice_direct": -1, "authority": 1, "channel": 1}
OUTCOMES = ["outward", "move_voice_direct", "authority", "channel", "any", "inward",
            "move_third_party", "move_exit", "move_self_help", "move_accept"]


def outcomes(c):
    refs = [r for r in c["referrals"] if r["stance"] in TAKEN]
    rel = {r["relation"] for r in refs}
    o = {"any": bool(refs), "outward": bool(rel & {"public_authority", "collective"}),
         "inward": "speaker_side" in rel, "channel": "counterparty_side" in rel,
         "authority": any(r["authority_over_counterparty"] for r in refs)}
    for m in ("exit", "voice_direct", "third_party", "self_help", "accept"):
        o["move_" + m] = c["primary_move"] == m
    return o


def keep(c):
    return c["form"] in KEEP_FORM and c["coherent"] and c["perspective_kept"]


def sign(xs):
    up = sum(x > 0 for x in xs); dn = sum(x < 0 for x in xs)
    return up, dn, (binomtest(up, up + dn).pvalue if up + dn else 1.0)


def holm(ps):
    o = sorted(range(len(ps)), key=lambda i: ps[i]); out = [None] * len(ps); run = 0
    for r, i in enumerate(o):
        run = max(run, min(1.0, (len(ps) - r) * ps[i])); out[i] = run
    return out


def main():
    rows = [json.loads(l) for l in open(SRC)]
    rows = [r for r in rows if r.get("coded")]
    arms = collections.defaultdict(set)
    for r in rows:
        arms[r["lineage"]].add(r["arm"])
    lineages = sorted(l for l, a in arms.items() if a == {"base", "aligned"})
    rows = [r for r in rows if r["lineage"] in lineages]
    L = ["# institution_vs_individual: the regeneration, declared test", "",
         "Producer `analyse_regen.py`, written before any regenerated passage was read. "
         "%d coded passages over %d lineages with both arms." % (len(rows), len(lineages)), ""]

    fm = collections.defaultdict(collections.Counter)
    for r in rows:
        fm[r["arm"]][r["coded"]["form"]] += 1
    L += ["## Form, by arm", "", "| arm | n | " + " | ".join(FORMS) + " |", "|---|---|" + "---|" * len(FORMS)]
    for a in ("base", "aligned"):
        n = sum(fm[a].values())
        L.append("| %s | %d | " % (a, n) + " | ".join("%.1f%%" % (100 * fm[a][f] / n) for f in FORMS) + " |")
    ex = collections.defaultdict(lambda: [0, 0, 0])
    for r in rows:
        if r["coded"]["form"] in KEEP_FORM:
            e = ex[(r["arm"], r["side"])]; e[0] += 1
            e[1] += not r["coded"]["coherent"]; e[2] += not r["coded"]["perspective_kept"]
    L += ["", "Excluded among continuation/advice (incoherent / perspective switched):", ""]
    for k in sorted(ex):
        e = ex[k]; L.append("- %s %s: %.1f%% / %.1f%% of %d" % (k[0], k[1], 100 * e[1] / e[0], 100 * e[2] / e[0], e[0]))
    L.append("")

    acc = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in rows:
        if keep(r["coded"]):
            for n, v in outcomes(r["coded"]).items():
                acc[(r["lineage"], r["scenario"], r["side"], r["arm"])][n].append(v)
    scen = sorted({k[1] for k in acc})
    res = {}
    for name in OUTCOMES:
        cell = {}
        for l in lineages:
            for s in scen:
                v = [acc.get((l, s, sd, a), {}).get(name) for sd in ("individual", "institution") for a in ("base", "aligned")]
                if all(v):
                    ib, ia, jb, ja = (np.mean(x) for x in v)
                    cell[(l, s)] = ((ia - ib) - (ja - jb), ib, ia, jb, ja)
        bys = [np.mean([v[0] for (l, s), v in cell.items() if s == q]) for q in scen if any(s == q for _, s in cell)]
        byl = [np.mean([v[0] for (l, s), v in cell.items() if l == q]) for q in lineages if any(l == q for l, _ in cell)]
        lv = [np.mean([v[i] for v in cell.values()]) for i in (1, 2, 3, 4)] if cell else [np.nan] * 4
        res[name] = (lv, sign(bys), sign(byl), len(bys), len(byl))
    ps_s = holm([res[n][1][2] for n in PRED]); ps_l = holm([res[n][2][2] for n in PRED])
    L += ["## Base -> aligned, individual side minus institution side", "",
          "| outcome | ind base -> aligned | inst base -> aligned | scenarios +/- | p | lineages +/- | p | predicted | verdict |",
          "|---|---|---|---|---|---|---|---|---|"]
    for i, name in enumerate(OUTCOMES):
        lv, (su, sd, sp), (lu, ld, lp), ns, nl = res[name]
        verdict = ""
        if name in PRED:
            j = list(PRED).index(name); d = PRED[name]
            ok_s = ps_s[j] < 0.05 and ((su > sd) if d > 0 else (sd > su))
            ok_l = ps_l[j] < 0.05 and ((lu > ld) if d > 0 else (ld > lu))
            verdict = "SUPPORTED" if ok_s and ok_l else ("one unit only" if ok_s or ok_l else "not supported")
            verdict += " (Holm p %.3g / %.3g)" % (ps_s[j], ps_l[j])
        L.append("| %s | %.3f -> %.3f | %.3f -> %.3f | %d/%d | %.3g | %d/%d | %.3g | %s | %s |"
                 % (name, lv[0], lv[1], lv[2], lv[3], su, sd, sp, lu, ld, lp,
                    {1: "> 0", -1: "< 0"}.get(PRED.get(name), ""), verdict))
    L += ["", "Units: %d scenarios, %d lineages." % (res["outward"][3], res["outward"][4]), ""]

    ok = sum(r.get("spans_ok", 0) for r in rows); tot = sum(r.get("spans_total", 0) for r in rows)
    L += ["Span verification: %d of %d quoted spans verbatim (%.1f%%)." % (ok, tot, 100 * ok / max(tot, 1))]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
