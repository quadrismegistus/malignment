"""A lexicon check with NO LLM in the measurement: USAS semantic fields over the regenerated passages.
-> results/usas_test.md

    python -u usas_test.py

DECLARED 2026-09-24 BEFORE ANY PASSAGE WAS TAGGED. RH's question: is there a check
on the routing that does not go through the LLM coder? USAS (UCREL semantic tagset;
`lexicons/fields/usas_semantic_lexicon_en.txt` via `malignment.fields._usas`) tags
words by field, and two fields map onto two of the four declared predictions:

    GOV_LAW  base code G1.* (government, politics) or G2.* (law and order: courts,
             lawyers, inspectors, police)             ~ P1 outward / P3 authority
    SPEECH   base code Q2.* (speech: talk, discuss, communicate; speech acts:
             complain, ask, explain)                  ~ P2 direct voice

It CANNOT test P4, the counterparty-channel result: a field does not say whose
department, and the counterparty is named in every prompt. Stated here so the
check is not read as covering it.

MEASUREMENT. The passage text only (not the prompt), lower-cased word tokens
([a-z']+). A token is GOV_LAW or SPEECH if any of its lexicon entries' FIRST tag
has that base code (portmanteau tags split on '/', +/- and m/f/n/c modifiers
stripped with fields._USAS_MOD). Rate = field tokens per 1,000 tokens, per passage.
Known losses, accepted: 'HR' and 'Union' are tagged Z3c (proper names); first-sense
lookup (so 'department' reads H2, building).

POPULATION, PRIMARY: every coded regeneration passage in a lineage with both arms,
UNFILTERED -- the coder's form/perspective filter would put the LLM back into the
selection. SECONDARY: form == advice only (uses the coder's form label; reported,
not LLM-free).

CONTRAST, per unit: (aligned - base rate, individual) - (aligned - base rate,
institution). Units: lineages and disputes; floor >= 20 passages per cell per unit.
Two-sided sign tests.

PREDICTIONS, each counted SUPPORTED only if p < 0.05 in the predicted direction on
BOTH units after Holm over the two, in the PRIMARY population:

    U1  GOV_LAW   > 0   the individual gains more government/law vocabulary
    U2  SPEECH    < 0   the institution gains more speech-act vocabulary
"""
import collections, json, os, re, sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import analyse_regen as A  # noqa: E402

FLOOR = 20
TOK = re.compile(r"[a-z']+")
FIELDS = {"GOV_LAW": ("G1", "G2"), "SPEECH": ("Q2",)}
PRED = {"GOV_LAW": 1, "SPEECH": -1}


def lexicon():
    from malignment import fields as F
    lex = F._usas()
    out = {}
    for w, tags in lex.items():
        bases = set()
        for t in tags:
            for part in t.split("/"):
                m = F._USAS_MOD.match(part)
                if m:
                    bases.add(m.group(1))
        out[w] = {name: any(b.startswith(p) for b in bases for p in pre)
                  for name, pre in FIELDS.items()}
    return out


def rates(text, lex):
    toks = TOK.findall((text or "").lower())
    if not toks:
        return None
    return {name: 1000.0 * sum(1 for t in toks if lex.get(t, {}).get(name)) / len(toks)
            for name in FIELDS}


def did(rows, unit, name):
    c = collections.defaultdict(list)
    for r in rows:
        c[(r[unit], r["arm"], r["side"])].append(r["_rates"][name])
    out = []
    for u in sorted({k[0] for k in c}):
        v = {(a, s): c.get((u, a, s), []) for a in ("base", "aligned") for s in ("individual", "institution")}
        if min(len(x) for x in v.values()) < FLOOR:
            continue
        m = {k: np.mean(x) for k, x in v.items()}
        out.append((m[("aligned", "individual")] - m[("base", "individual")])
                   - (m[("aligned", "institution")] - m[("base", "institution")]))
    return out


def main():
    lex = lexicon()
    rows = [json.loads(l) for l in open(A.SRC)]
    rows = [r for r in rows if r["lineage"] not in A.BROKEN_LINEAGES]
    arms = collections.defaultdict(set)
    for r in rows:
        arms[r["lineage"]].add(r["arm"])
    rows = [r for r in rows if arms[r["lineage"]] == {"base", "aligned"}]
    for r in rows:
        r["_rates"] = rates(r["text"], lex)
    rows = [r for r in rows if r["_rates"]]
    covered = np.mean([sum(1 for t in TOK.findall(r["text"].lower()) if t in lex) / max(1, len(TOK.findall(r["text"].lower()))) for r in rows[:3000]])
    L = ["# USAS semantic fields: a check with no LLM in the measurement", "",
         "Producer `usas_test.py`, declared before tagging. Lexicon coverage of tokens (first 3,000 passages): %.1f%%." % (100 * covered), ""]
    for label, sub in (("PRIMARY: all passages, unfiltered", rows),
                       ("SECONDARY: advice only (coder's form label)", [r for r in rows if r.get("coded") and r["coded"]["form"] == "advice"])):
        L += ["## " + label, "",
              "| field | base ind | base inst | aligned ind | aligned inst | lineages +/- | p | disputes +/- | p | predicted | verdict |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
        res = {}
        for name in FIELDS:
            m = {(a, s): np.mean([r["_rates"][name] for r in sub if r["arm"] == a and r["side"] == s])
                 for a in ("base", "aligned") for s in ("individual", "institution")}
            res[name] = (m, A.sign(did(sub, "lineage", name)), A.sign(did(sub, "scenario", name)))
        hl = A.holm([res[n][1][2] for n in FIELDS]); hd = A.holm([res[n][2][2] for n in FIELDS])
        for i, name in enumerate(FIELDS):
            m, (lu, ld, lp), (du, dd, dp) = res[name]
            d = PRED[name]
            ok = (hl[i] < 0.05 and ((lu > ld) if d > 0 else (ld > lu)) and
                  hd[i] < 0.05 and ((du > dd) if d > 0 else (dd > du)))
            verdict = ("SUPPORTED" if ok else "not supported") if label.startswith("PRIMARY") else "(secondary)"
            L.append("| %s | %.2f | %.2f | %.2f | %.2f | %d/%d | %.3g | %d/%d | %.3g | %s | %s (Holm %.3g / %.3g) |" % (
                name, m[("base", "individual")], m[("base", "institution")], m[("aligned", "individual")],
                m[("aligned", "institution")], lu, ld, lp, du, dd, dp, "> 0" if d > 0 else "< 0", verdict, hl[i], hd[i]))
        L += ["", "Rates are field tokens per 1,000 tokens, mean over passages.", ""]
    open(os.path.join(HERE, "results", "usas_test.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
