#!/usr/bin/env python
"""TEST A and B. Reads run.py's output; never queries ClickHouse.

Registered design: `registration.md`, frozen 2026-08-16 before any rate existed.

    rate_C(stage)   = mass FALLEN from C / C mass the stage INHERITED
    excess_C(stage) = rate_C(stage) - rate_neutral(stage)      same stage, same lineage

    A   for SEXUAL   excess(SFT)  > excess(PREF)
    B   for VIOLENT  excess(PREF) > excess(SFT)

**A and B are never compared to each other and are never summarised into one
verdict.** The original claim is one sentence with two halves; if A passes and B
fails the sentence is false and something real has still been found, and that
must be sayable. Registration section 5, RH's decision.
"""
import argparse
import collections
import csv
import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def _repo_root(start):
    d = start
    while d != os.path.dirname(d):
        if os.path.isdir(os.path.join(d, "malignment")):
            return d
        d = os.path.dirname(d)
    raise RuntimeError("no malignment/ above %s" % start)


ROOT = _repo_root(HERE)
sys.path.insert(0, ROOT)

from malignment.wordfield import paired_stats, sign_mde       # noqa: E402

RESULTS = os.path.join(HERE, "results")
#: registration section 5: sexual is matched to its own reference, violent to its.
ARMS = {"sexual": "neutral_matched_sexual", "violent": "neutral_matched_violent"}


def load():
    rows = []
    with open(os.path.join(RESULTS, "cells.csv"), encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            rows.append((r["from_model"], r["to_model"], r["prompt_key"],
                         r["prompt_domain"], r["word_set"],
                         float(r["removed"]), float(r["arrived"]),
                         float(r["inherited"]), int(r["n_words"])))
    with open(os.path.join(RESULTS, "chains.csv"), encoding="utf-8") as fh:
        chains = list(csv.DictReader(fh))
    return rows, chains


def rates(rows, chains, per_prompt=False, keep=None):
    """{(base, stage, word_set): rate}. Pooled by default.

    POOLED is the registered primary: a prompt carrying no mass of a set
    contributes to neither numerator nor denominator, so it cannot dilute, and
    the panel choice stops being load-bearing. PER-PROMPT is the registered
    sensitivity check -- it downweights the ~40 prompts holding 82% of sexual
    mass and gives the rest equal say. A check that cannot fail is not a check,
    which is why the alternative is NOT a restriction to those 40.
    """
    edges = {}
    for c in chains:
        edges[(c["base"], c["sft"])] = (c["base"], "SFT")
        edges[(c["sft"], c["pref"])] = (c["base"], "PREF")
    acc = collections.defaultdict(lambda: [0.0, 0.0])          # removed, inherited
    per = collections.defaultdict(list)
    for fr, to, pk, dom, ws, rem, arr, inh, nw in rows:
        e = edges.get((fr, to))
        if not e or (keep and not keep(dom)):
            continue
        k = (e[0], e[1], ws)
        acc[k][0] += rem
        acc[k][1] += inh
        if inh > 0:
            per[k].append(rem / inh)
    if per_prompt:
        return {k: statistics.mean(v) for k, v in per.items() if v}
    return {k: (r / i) for k, (r, i) in acc.items() if i > 0}


def excess(rt, arm, ref):
    """{base: (excess_at_SFT, excess_at_PREF)} for one category."""
    out = {}
    bases = {k[0] for k in rt}
    for b in bases:
        got = {}
        for stage in ("SFT", "PREF"):
            c, n = rt.get((b, stage, arm)), rt.get((b, stage, ref))
            if c is None or n is None:
                got = None
                break
            got[stage] = c - n
        if got:
            out[b] = (got["SFT"], got["PREF"])
    return out


def report(label, diffs, predicted):
    s = paired_stats(list(diffs.values()))
    if not s:
        print("  %-46s no data" % label)
        return None
    s["mde_sign"] = sign_mde(list(diffs.values()))
    ok = (s["ci_lo"] > 0) if predicted == "+" else (s["ci_hi"] < 0)
    print("  %-46s n=%-3d mean %+.4f  CI [%+.4f,%+.4f]  %2d/%-2d  sign p=%.4f  t=%s"
          % (label, s["n"], s["mean"], s["ci_lo"], s["ci_hi"], s["pos"], s["n"],
             s["sign_p"], ("%.3f" % s["t_p"]) if s["t_p"] is not None else "-"))
    s["supported"] = bool(ok)
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-prompt", action="store_true",
                    help="registered sensitivity check: equal weight per prompt")
    a = ap.parse_args()
    rows, chains = load()
    rt = rates(rows, chains, per_prompt=a.per_prompt)
    mode = "PER-PROMPT (sensitivity)" if a.per_prompt else "POOLED (registered primary)"
    print("  %s | %d lineages\n" % (mode, len({k[0] for k in rt})))

    print("  RAW REMOVAL RATES -- fraction of the set's INHERITED mass that fell")
    print("  %-26s %8s %8s" % ("", "SFT", "PREF"))
    for ws in ("sexual", "violent", "neutral",
               "neutral_matched_sexual", "neutral_matched_violent"):
        v = {st: [rt[k] for k in rt if k[1] == st and k[2] == ws] for st in ("SFT", "PREF")}
        if v["SFT"]:
            print("    %-24s %8.4f %8.4f"
                  % (ws, statistics.median(v["SFT"]), statistics.median(v["PREF"])))
    print("  (medians over lineages; matched references are the ones A and B use)")

    S = {}
    print("\n  A -- SEXUAL is an SFT speciality.  Predicts excess(SFT) > excess(PREF)")
    ex = excess(rt, "sexual", ARMS["sexual"])
    S["A"] = report("A: excess_sexual(SFT) - excess_sexual(PREF)",
                    {b: v[0] - v[1] for b, v in ex.items()}, "+")
    print("\n  B -- VIOLENT is a preference-stage speciality.  Predicts excess(PREF) > excess(SFT)")
    ev = excess(rt, "violent", ARMS["violent"])
    S["B"] = report("B: excess_violent(PREF) - excess_violent(SFT)",
                    {b: v[1] - v[0] for b, v in ev.items()}, "+")

    print("\n  UNMATCHED reference, reported so the size of the matching correction is visible")
    exu = excess(rt, "sexual", "neutral")
    evu = excess(rt, "violent", "neutral")
    report("A with unmatched neutral", {b: v[0] - v[1] for b, v in exu.items()}, "+")
    report("B with unmatched neutral", {b: v[1] - v[0] for b, v in evu.items()}, "+")

    for k in ("A", "B"):
        if S[k]:
            print("\n  %s sign-test MDE at n=%d: %s" % (k, S[k]["n"], S[k]["mde_sign"]))

    print("\n  PER LINEAGE (descriptive; the family split is contaminated -- see registration section 2)")
    print("  %-26s %10s %10s %10s %10s" % ("", "sexSFT", "sexPREF", "vioSFT", "vioPREF"))
    for b in sorted(ex, key=lambda b: -(ex[b][0] - ex[b][1])):
        if b in ev:
            print("    %-24s %+10.4f %+10.4f %+10.4f %+10.4f"
                  % (b.split("/")[-1][:24], ex[b][0], ex[b][1], ev[b][0], ev[b][1]))

    out = {"mode": mode, "A": S["A"], "B": S["B"]}
    with open(os.path.join(RESULTS, "summary%s.json" % ("_per_prompt" if a.per_prompt else "")),
              "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, default=str)
    with open(os.path.join(RESULTS, "by_lineage%s.csv" % ("_per_prompt" if a.per_prompt else "")),
              "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["base", "excess_sexual_sft", "excess_sexual_pref",
                    "excess_violent_sft", "excess_violent_pref", "A_diff", "B_diff"])
        for b in sorted(ex):
            if b in ev:
                w.writerow([b, "%.8g" % ex[b][0], "%.8g" % ex[b][1],
                            "%.8g" % ev[b][0], "%.8g" % ev[b][1],
                            "%.8g" % (ex[b][0] - ex[b][1]), "%.8g" % (ev[b][1] - ev[b][0])])

    print("\n  VERDICTS -- reported separately, NEVER summarised into one (registration 5)")
    for k, name in (("A", "SEXUAL is an SFT speciality"),
                    ("B", "VIOLENT is a preference-stage speciality")):
        s = S[k]
        if not s:
            continue
        print("    %s (%s): %s" % (k, name, "SUPPORTED" if s["supported"] else "NOT SUPPORTED"))
        if not s["supported"]:
            print("       bounded to [%+.4f, %+.4f]" % (s["ci_lo"], s["ci_hi"]))
    if S["A"] and S["B"] and not S["A"]["supported"] and not S["B"]["supported"]:
        print("\n    BOTH FAIL. Registration rule 5: the claim is dead. No fourth")
        print("    instrument, no fifth statistic. Not supported at prompt level,")
        print("    at word level, and at removal-rate level.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
