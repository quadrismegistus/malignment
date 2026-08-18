#!/usr/bin/env python
"""Which of our generation prompts OPEN a scene, and which CLOSE the field?

    python run.py --save <workflow-output.json>   persist the coding
    python run.py --report                        the partition, joined to metadata

## WHY THIS EXISTS

Every scene-kind question -- does alignment change WHAT KIND of situation the
model produces -- needs prompts that leave the event to be invented. A prompt
that names the act ("He clubbed the seal pup on the ice and") measures how a
model elaborates a determined situation, which is a different question.

**The partition was ASSERTED from four examples before it was measured.** This
replaces that with 482 blind judgments, two coders, agreement 0.909.

## THE CODERS WERE TOLD SUBJECT MATTER IS IRRELEVANT

The obvious failure is coding "clubbed the seal pup" CLOSED because it is
violent rather than because it fixes the event. The scheme states that a prompt
can be disturbing and OPEN or bland and CLOSED, and that length is not the
criterion. Whether that held is checkable here: openness should NOT track
`pair_role`, which marks the transgressive member of a minimal pair.
"""
import argparse, collections, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")
CODINGS = os.path.join(RESULTS, "codings.json")


def save(src):
    d = json.load(open(src, encoding="utf-8"))
    r = d.get("result", d)
    if isinstance(r, str):
        r = json.loads(r)
    json.dump({"coder_A": r["A"], "coder_B": r["B"], "agreed": r["agreed"],
               "both_coded": r["both_coded"], "raw_agreement": r["raw_agreement"],
               "run_id": "wf_1468cab2-4b6"},
              open(CODINGS, "w", encoding="utf-8"), indent=0, sort_keys=True)
    print("saved %d/%d codings -> %s" % (len(r["A"]), len(r["B"]), CODINGS))


def meta():
    """prompt -> (source, family, domain, pair_role) from the catalogue."""
    q = ("SELECT prompt, source, domain, pair_role, slot FROM malign_logits.prompt_catalogue "
         "WHERE status='ACTIVE' FORMAT TabSeparated")
    out = subprocess.run(["clickhouse", "client", "--query", q],
                         capture_output=True, text=True, timeout=600)
    m = {}
    for line in out.stdout.splitlines():
        f = line.split("\t")
        if len(f) >= 5:
            m[f[0].replace("\\'", "'")] = {"source": f[1], "domain": f[2],
                                           "pair_role": f[3], "slot": f[4]}
    return m


def report():
    from scipy import stats
    C = json.load(open(CODINGS, encoding="utf-8"))
    A, B = C["coder_A"], C["coder_B"]
    key = json.load(open(os.path.join(RESULTS, "key.json"), encoding="utf-8"))
    M = meta()
    both = [i for i in A if i in B]
    print("coded %d by both | agreement %.4f (declared %s)"
          % (len(both), C["agreed"] / len(both), C["raw_agreement"]))

    #: PRIMARY is the AGREED subset. A prompt the two coders split on is not a
    #: prompt whose openness we know, and the whole use of this partition is to
    #: select a population -- so a contested item must not silently enter it.
    agreed = {i: A[i]["openness"] for i in both if A[i]["openness"] == B[i]["openness"]}
    print("agreed on %d of %d; %d contested and EXCLUDED from the partition\n"
          % (len(agreed), len(both), len(both) - len(agreed)))

    c = collections.Counter(agreed.values())
    for k in ("OPEN", "PARTIAL", "CLOSED"):
        print("  %-8s %4d  (%.0f%% of agreed)" % (k, c[k], 100 * c[k] / len(agreed)))

    print("\n=== BY SOURCE: was the partition I asserted correct? ===")
    by = collections.defaultdict(collections.Counter)
    unmatched = 0
    for i, v in agreed.items():
        s = M.get(key[i], {}).get("source")
        if not s:
            unmatched += 1; continue
        by[s][v] += 1
    print("  %-24s %6s %8s %8s %8s" % ("source", "n", "OPEN", "PARTIAL", "CLOSED"))
    for s, cc in sorted(by.items(), key=lambda x: -sum(x[1].values())):
        n = sum(cc.values())
        if n < 5:
            continue
        print("  %-24s %6d %7.0f%% %7.0f%% %7.0f%%"
              % (s, n, 100 * cc["OPEN"] / n, 100 * cc["PARTIAL"] / n, 100 * cc["CLOSED"] / n))
    if unmatched:
        print("  (%d agreed prompts did not join the catalogue)" % unmatched)

    print("\n=== THE CHECK: does openness track TRANSGRESSIVENESS? It should not. ===")
    tab = collections.Counter()
    for i, v in agreed.items():
        pr = M.get(key[i], {}).get("pair_role")
        if pr in ("MARKED", "UNMARKED"):
            tab[(pr, v)] += 1
    for pr in ("MARKED", "UNMARKED"):
        n = sum(tab[(pr, k)] for k in ("OPEN", "PARTIAL", "CLOSED"))
        if n:
            print("  %-10s n=%-4d OPEN %.0f%%  PARTIAL %.0f%%  CLOSED %.0f%%"
                  % (pr, n, 100 * tab[(pr, "OPEN")] / n,
                     100 * tab[(pr, "PARTIAL")] / n, 100 * tab[(pr, "CLOSED")] / n))
    if all(sum(tab[(p, k)] for k in ("OPEN", "PARTIAL", "CLOSED")) for p in ("MARKED", "UNMARKED")):
        t = [[tab[("MARKED", "OPEN")], tab[("MARKED", "CLOSED")]],
             [tab[("UNMARKED", "OPEN")], tab[("UNMARKED", "CLOSED")]]]
        if min(map(min, t)) >= 0 and sum(map(sum, t)) > 20:
            print("  Fisher, OPEN vs CLOSED by MARKED/UNMARKED: p=%.3g" % stats.fisher_exact(t)[1])
            print("  (a LOW p means coders let subject matter drive the code)")

    with open(os.path.join(RESULTS, "openness.csv"), "w", encoding="utf-8") as fh:
        fh.write("id,openness,agreed,source,domain,pair_role,prompt\n")
        for i in sorted(A):
            v = A[i]["openness"]; ag = int(i in agreed)
            mm = M.get(key[i], {})
            p = '"%s"' % key[i].replace('"', '""')
            fh.write("%s,%s,%d,%s,%s,%s,%s\n" % (i, v, ag, mm.get("source", ""),
                                                 mm.get("domain", ""), mm.get("pair_role", ""), p))
    print("\n  -> %s" % os.path.join(RESULTS, "openness.csv"))


def round2(src=None):
    """Slot corpus + third-coder adjudication of the contested 44.

    THE ANCHORS ARE THE POINT. A coder shown only contested items sees an
    unrepresentative run of hard cases and drifts to PARTIAL. 30 items where A
    and B already agreed were shuffled in indistinguishably, so C's agreement
    with them CALIBRATES it. If C misses the settled cases, C is a third opinion
    and the ties stay open."""
    import collections
    from scipy import stats
    p = os.path.join(RESULTS, "round2.json")
    if src:
        d = json.load(open(src, encoding="utf-8"))
        r = d.get("result", d)
        if isinstance(r, str):
            r = json.loads(r)
        json.dump(r, open(p, "w", encoding="utf-8"), indent=0, sort_keys=True)
        print("saved -> %s" % p)
    R = json.load(open(p, encoding="utf-8"))
    A, B, C = R["A"], R["B"], R["C"]
    SK = json.load(open(os.path.join(RESULTS, "slots_key.json"), encoding="utf-8"))
    AK = json.load(open(os.path.join(RESULTS, "adjudicate_key.json"), encoding="utf-8"))

    both = [i for i in A if i in B]
    ag = {i: A[i]["openness"] for i in both if A[i]["openness"] == B[i]["openness"]}
    print("=== SLOT CORPUS: %d prompts, agreement %s ===" % (len(both), R["slots_agreement"]))
    print("agreed %d, contested %d EXCLUDED\n" % (len(ag), len(both) - len(ag)))
    c = collections.Counter(ag.values())
    for k in ("OPEN", "PARTIAL", "CLOSED"):
        print("  %-8s %4d  (%.0f%%)" % (k, c[k], 100 * c[k] / len(ag)))
    print("\n  %-20s %6s %8s %8s %8s" % ("source", "n", "OPEN", "PARTIAL", "CLOSED"))
    by = collections.defaultdict(collections.Counter)
    for i, v in ag.items():
        by[SK[i]["source"]][v] += 1
    for s_, cc in sorted(by.items(), key=lambda x: -sum(x[1].values())):
        n = sum(cc.values())
        print("  %-20s %6d %7.0f%% %7.0f%% %7.0f%%"
              % (s_, n, 100 * cc["OPEN"] / n, 100 * cc["PARTIAL"] / n, 100 * cc["CLOSED"] / n))

    print("\n=== ADJUDICATION: is the third coder calibrated? ===")
    anc = [i for i in C if not AK[i]["is_contested"]]
    hit = sum(1 for i in anc if C[i]["openness"] == AK[i]["A"])
    t = stats.binomtest(hit, len(anc), 1 / 3)
    print("  ANCHORS  C matches the A/B consensus on %d of %d = %.0f%%  (chance 33%%, p=%.3g)"
          % (hit, len(anc), 100 * hit / len(anc), t.pvalue))
    ok = hit / len(anc) >= 0.70
    print("  -> %s" % ("CALIBRATED. C's verdicts on the contested items count."
                       if ok else "NOT CALIBRATED. C is a third opinion; ties stay open."))

    con = [i for i in C if AK[i]["is_contested"]]
    sideA = sum(1 for i in con if C[i]["openness"] == AK[i]["A"])
    sideB = sum(1 for i in con if C[i]["openness"] == AK[i]["B"])
    neither = len(con) - sideA - sideB
    print("\n  CONTESTED %d: C sides with A on %d, with B on %d, with NEITHER on %d"
          % (len(con), sideA, sideB, neither))
    if ok:
        res = collections.Counter(C[i]["openness"] for i in con if C[i]["openness"] in
                                  (AK[i]["A"], AK[i]["B"]))
        print("  resolved %d of %d: %s" % (sideA + sideB, len(con), dict(res)))
        print("  %d unresolved (C picked the third option) and stay excluded" % neither)


def final(src=None):
    """Fold both adjudications into one partition and RE-TEST the leakage check.

    The MARKED/UNMARKED check was run BEFORE any adjudication and its p=0.067 has
    been sitting in the container's table since. 34 items have entered the
    partition and more are entering now; a caveat quoted against a corpus that has
    changed is a stale number wearing a fence."""
    import collections
    from scipy import stats
    p = os.path.join(RESULTS, "round3.json")
    if src:
        d = json.load(open(src, encoding="utf-8"))
        r = d.get("result", d)
        if isinstance(r, str):
            r = json.loads(r)
        json.dump(r, open(p, "w", encoding="utf-8"), indent=0, sort_keys=True)
    C3 = json.load(open(p, encoding="utf-8"))["C"]
    K3 = json.load(open(os.path.join(RESULTS, "adjudicate_slots_key.json"), encoding="utf-8"))

    anc = [i for i in C3 if not K3[i]["is_contested"]]
    hit = sum(1 for i in anc if C3[i]["openness"] == K3[i]["A"])
    t = stats.binomtest(hit, len(anc), 1 / 3)
    print("=== SLOT ADJUDICATION ===")
    print("  ANCHORS  %d of %d = %.0f%%  (chance 33%%, p=%.3g)"
          % (hit, len(anc), 100 * hit / len(anc), t.pvalue))
    ok3 = hit / len(anc) >= 0.70
    print("  -> %s" % ("CALIBRATED" if ok3 else "NOT CALIBRATED; slot ties stay open"))
    con = [i for i in C3 if K3[i]["is_contested"]]
    sA = sum(1 for i in con if C3[i]["openness"] == K3[i]["A"])
    sB = sum(1 for i in con if C3[i]["openness"] == K3[i]["B"])
    print("  CONTESTED %d: sides with A %d, with B %d, NEITHER %d -> resolved %d"
          % (len(con), sA, sB, len(con) - sA - sB, sA + sB))

    #: ---- the consolidated partition, both populations
    C1 = json.load(open(CODINGS, encoding="utf-8"))
    A1, B1 = C1["coder_A"], C1["coder_B"]
    K1 = json.load(open(os.path.join(RESULTS, "adjudicate_key.json"), encoding="utf-8"))
    C2 = json.load(open(os.path.join(RESULTS, "round2.json"), encoding="utf-8"))
    A2, B2 = C2["A"], C2["B"]
    key = json.load(open(os.path.join(RESULTS, "key.json"), encoding="utf-8"))
    SK = json.load(open(os.path.join(RESULTS, "slots_key.json"), encoding="utf-8"))

    part = {}
    for i in A1:
        if i in B1 and A1[i]["openness"] == B1[i]["openness"]:
            part[key[i]] = A1[i]["openness"]
    for a, v in K1.items():
        if v["is_contested"]:
            c = json.load(open(os.path.join(RESULTS, "round2.json"), encoding="utf-8"))["C"][a]["openness"]
            if c in (v["A"], v["B"]):
                part[key[v["orig_id"]]] = c
    for i in A2:
        if i in B2 and A2[i]["openness"] == B2[i]["openness"]:
            part[SK[i]["prompt"]] = A2[i]["openness"]
    if ok3:
        for a, v in K3.items():
            if v["is_contested"] and C3[a]["openness"] in (v["A"], v["B"]):
                part[SK[v["orig_id"]]["prompt"]] = C3[a]["openness"]

    c = collections.Counter(part.values())
    print("\n=== FINAL PARTITION, both populations, all adjudications ===")
    print("  %d prompts resolved of 679 coded" % len(part))
    for k in ("OPEN", "PARTIAL", "CLOSED"):
        print("  %-8s %4d  (%.0f%%)" % (k, c[k], 100 * c[k] / len(part)))

    print("\n=== RE-TEST: does openness track transgressiveness? (was p=0.0667) ===")
    M = meta()
    tab = collections.Counter()
    for pr_text, v in part.items():
        pr = M.get(pr_text, {}).get("pair_role")
        if pr in ("MARKED", "UNMARKED"):
            tab[(pr, v)] += 1
    for pr in ("MARKED", "UNMARKED"):
        n = sum(tab[(pr, k)] for k in ("OPEN", "PARTIAL", "CLOSED"))
        print("  %-10s n=%-4d OPEN %.0f%%  PARTIAL %.0f%%  CLOSED %.0f%%"
              % (pr, n, 100 * tab[(pr, "OPEN")] / n, 100 * tab[(pr, "PARTIAL")] / n,
                 100 * tab[(pr, "CLOSED")] / n))
    tt = [[tab[("MARKED", "OPEN")], tab[("MARKED", "CLOSED")]],
          [tab[("UNMARKED", "OPEN")], tab[("UNMARKED", "CLOSED")]]]
    pv = stats.fisher_exact(tt)[1]
    print("  Fisher, OPEN vs CLOSED: p=%.4g  ->  %s"
          % (pv, "still borderline/leaking" if pv < 0.15 else "no detectable leakage"))
    json.dump(part, open(os.path.join(RESULTS, "partition.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=0)
    print("\n  -> %s" % os.path.join(RESULTS, "partition.json"))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--save")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--round2", nargs="?", const=True)
    ap.add_argument("--final", nargs="?", const=True)
    a = ap.parse_args()
    if a.save:
        save(a.save)
    elif a.report:
        report()
    elif a.round2:
        round2(None if a.round2 is True else a.round2)
    elif a.final:
        final(None if a.final is True else a.final)
    else:
        ap.print_help()
