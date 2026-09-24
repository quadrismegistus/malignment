"""Does the individual/institution gap widen WITHIN a genre, at the lineage unit? -> results/within_genre_test.md

    python -u within_genre_test.py

DECLARED 2026-09-24 BEFORE ANY PER-LINEAGE OR PER-DISPUTE NUMBER WAS COMPUTED, at
the paper seat's request. The POOLED within-genre numbers (`decompose.py`) HAD
been seen: counterparty channel gap +0.26 within advice, +0.09 within
continuation. So this is a check of an observed effect at its proper unit, not an
independent confirmation, and it is reported as such.

POPULATION. Kept passages (continuation or advice, coherent, perspective kept;
`analyse_regen.keep`) in lineages with both arms, coded by `run_regen.py`.

TWO STRATA, each run separately: form == advice; form == continuation.

STATISTIC, per stratum. For each unit u (a lineage, or a dispute), with shares
computed over the passages of that stratum:

    gap_arm(u) = share(individual) - share(institution)
    widening(u) = gap_aligned(u) - gap_base(u)

OUTCOMES. PRIMARY: `channel` (a recommended or marked-correct referral to a
counterparty_side body) -- the sentence the essay leans on. SECONDARY, reported
beside it: `move_voice_direct` (widening expected NEGATIVE: the institution gains
more), `outward`, `authority`.

UNITS AND FLOORS, fixed here, before any count is looked at:

    lineage   enters only if each of its four cells (base/aligned x individual/
              institution) holds at least FLOOR_LINEAGE = 5 passages of the stratum
    dispute   pooled over lineages; enters only if each of its four cells holds at
              least FLOOR_DISPUTE = 10 passages of the stratum

Two-sided sign test over the units that enter; ties dropped. The minimum, median
and maximum base cell n among entering units are reported, and so is how many
units the floor dropped.

DECISION (paper seat's rule): if `channel` widens significantly (p < 0.05, positive
majority) within ADVICE on BOTH units, the within-advice widening is the essay
sentence's evidence. Otherwise the sentence falls back to the declared P4, which
already passed on the pooled arms. The continuation stratum is reported and does
not decide.
"""
import collections, json, os, sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import analyse_regen as A  # noqa: E402

FLOOR_LINEAGE = 5
FLOOR_DISPUTE = 10
OUTCOMES = [("channel", 1, "PRIMARY"), ("move_voice_direct", -1, "secondary"),
            ("outward", 1, "secondary"), ("authority", 1, "secondary")]


def widening(rows, unit, floor, name):
    cells = collections.defaultdict(list)
    for r in rows:
        cells[(r[unit], r["arm"], r["side"])].append(A.outcomes(r["coded"])[name])
    units = sorted({k[0] for k in cells})
    out, dropped, base_ns = {}, 0, []
    for u in units:
        c = {(a, s): cells.get((u, a, s), []) for a in ("base", "aligned") for s in ("individual", "institution")}
        if min(len(v) for v in c.values()) < floor:
            dropped += 1
            continue
        g = lambda a: np.mean(c[(a, "individual")]) - np.mean(c[(a, "institution")])
        out[u] = g("aligned") - g("base")
        base_ns += [len(c[("base", "individual")]), len(c[("base", "institution")])]
    return out, dropped, base_ns


def main():
    rows = [json.loads(l) for l in open(A.SRC)]
    rows = [r for r in rows if r.get("coded") and A.keep(r["coded"])]
    arms = collections.defaultdict(set)
    for r in rows:
        arms[r["lineage"]].add(r["arm"])
    rows = [r for r in rows if arms[r["lineage"]] == {"base", "aligned"}]
    L = ["# Within-genre widening at the lineage and dispute unit", "",
         "Producer `within_genre_test.py`, declared before any per-unit number was computed (pooled numbers "
         "had been seen; see docstring). Floors: >= %d passages per cell per lineage, >= %d per cell per dispute."
         % (FLOOR_LINEAGE, FLOOR_DISPUTE), ""]
    for form in ("advice", "continuation"):
        sub = [r for r in rows if r["coded"]["form"] == form]
        L += ["## Within %s" % form, "",
              "| outcome | role | expected | lineages +/- | p | median widening | dropped by floor | base cell n min/median/max | disputes +/- | p | median widening | dropped |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for name, sign_exp, role in OUTCOMES:
            wl, dl, bn = widening(sub, "lineage", FLOOR_LINEAGE, name)
            wd, dd, _ = widening(sub, "scenario", FLOOR_DISPUTE, name)
            lu, ld, lp = A.sign(list(wl.values()))
            du, dn, dp = A.sign(list(wd.values()))
            L.append("| %s | %s | %s | %d/%d | %.3g | %+.3f | %d | %s | %d/%d | %.3g | %+.3f | %d |" % (
                name, role, "> 0" if sign_exp > 0 else "< 0", lu, ld, lp,
                np.median(list(wl.values())) if wl else float("nan"), dl,
                "%d/%d/%d" % (min(bn), np.median(bn), max(bn)) if bn else "-",
                du, dn, dp, np.median(list(wd.values())) if wd else float("nan"), dd))
        L.append("")
    # the decision
    sub = [r for r in rows if r["coded"]["form"] == "advice"]
    wl, _, _ = widening(sub, "lineage", FLOOR_LINEAGE, "channel")
    wd, _, _ = widening(sub, "scenario", FLOOR_DISPUTE, "channel")
    (lu, ld, lp), (du, dn, dp) = A.sign(list(wl.values())), A.sign(list(wd.values()))
    ok = lp < 0.05 and lu > ld and dp < 0.05 and du > dn
    L += ["## Decision", "",
          "Channel widening within advice: lineages %d/%d (p=%.3g), disputes %d/%d (p=%.3g). %s" % (
              lu, ld, lp, du, dn, dp,
              "**HOLDS on both units: the within-advice widening is the sentence's evidence.**" if ok else
              "**Does NOT hold on both units: the sentence falls back to the declared P4.**")]
    open(os.path.join(HERE, "results", "within_genre_test.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
