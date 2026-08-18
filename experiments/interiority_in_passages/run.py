#!/usr/bin/env python
"""Is interiority already implied by the l2 prompts, before any model writes?

    python run.py --save <workflow-output.json>
    python run.py --report

## WHY THIS RUNS FIRST

The question downstream is whether ALIGNMENT shifts passages toward interior
content. That is only askable if the PROMPT does not already supply it. RH's
prior, and mine, was that these prompts are exterior -- "He was beautiful and she
wanted to" names an appearance, not a state of mind.

**Checked before building on it, because the prior was wrong.**

## THE ACQUIESCENCE GUARD, AND WHY IT WAS NEEDED

RH: *"agents sometimes don't like saying false to everything."* A yes/no on
"does this imply interiority" would drift positive. Four countermeasures:

  1. EXTERIOR is a POSITIVE category, so declining INTERIOR means choosing
     something, not refusing.
  2. The scheme states EXTERIOR and NEITHER are ordinary answers.
  3. The `wanted to / chose to / decided to` hinge -- present in nearly every
     prompt and itself intention-flavoured -- is excluded by instruction.
  4. **The corpus supplies its own discrimination test**: families split into
     appearance (beautiful/ugly), circumstance (captive/free, rich/poor) and
     genuine mental state (love/hate, fear, rational/irrational). Coders who
     separate those are reading; coders who return INTERIOR throughout are not.
"""
import argparse, collections, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")
CODINGS = os.path.join(RESULTS, "codings.json")


def save(src):
    d = json.load(open(src, encoding="utf-8"))
    r = d.get("result", d)
    if isinstance(r, str):
        r = json.loads(r)
    json.dump(r, open(CODINGS, "w", encoding="utf-8"), indent=0, sort_keys=True)
    print("saved -> %s" % CODINGS)


def report():
    R = json.load(open(CODINGS, encoding="utf-8"))
    K = json.load(open(os.path.join(RESULTS, "key.json"), encoding="utf-8"))
    A, B, C = R["A"], R["B"], R["C"]
    ids = [i for i in A if i in B and i in C]
    unan = {i: A[i]["kind"] for i in ids
            if A[i]["kind"] == B[i]["kind"] == C[i]["kind"]}
    print("212 prompts, three coders | unanimous on %d (%.0f%%)"
          % (len(unan), 100 * len(unan) / len(ids)))
    print("\nper-coder distribution -- stable across coders is the first acquiescence check:")
    for c, M in (("A", A), ("B", B), ("C", C)):
        cc = collections.Counter(M[i]["kind"] for i in ids)
        print("  %s  EXTERIOR %3d  INTERIOR %3d  NEITHER %3d"
              % (c, cc["EXTERIOR"], cc["INTERIOR"], cc["NEITHER"]))

    cc = collections.Counter(unan.values())
    print("\nUNANIMOUS partition (n=%d):" % len(unan))
    for k in ("EXTERIOR", "INTERIOR", "NEITHER"):
        print("  %-9s %3d  (%.0f%%)" % (k, cc[k], 100 * cc[k] / len(unan)))

    print("\n=== DISCRIMINATION: does the coding track the family? ===")
    by = collections.defaultdict(collections.Counter)
    for i, v in unan.items():
        by[K[i]["family"] or "(none)"][v] += 1
    fams = sorted(by.items(), key=lambda x: (-x[1]["INTERIOR"] / max(sum(x[1].values()), 1),
                                             -sum(x[1].values())))
    print("  %-26s %5s %5s %5s %5s" % ("family", "n", "INT", "EXT", "NEI"))
    for f, c in fams:
        n = sum(c.values())
        if n < 3:
            continue
        print("  %-26s %5d %5d %5d %5d" % (f[:26], n, c["INTERIOR"], c["EXTERIOR"], c["NEITHER"]))
    pure_i = [f for f, c in by.items() if sum(c.values()) >= 3 and c["INTERIOR"] == sum(c.values())]
    pure_e = [f for f, c in by.items() if sum(c.values()) >= 3 and c["EXTERIOR"] == sum(c.values())]
    print("\n  families unanimously INTERIOR throughout: %d" % len(pure_i))
    print("  families unanimously EXTERIOR throughout: %d" % len(pure_e))
    print("  -> %s" % ("DISCRIMINATES. Not acquiescence." if pure_i and pure_e else
                       "NO DISCRIMINATION -- treat the coding as suspect."))

    print("\n=== BY LANGUAGE ===")
    for lang in ("en", "zh"):
        sub = [v for i, v in unan.items() if K[i]["language"].strip() == lang]
        if not sub:
            continue
        c = collections.Counter(sub)
        print("  %-4s n=%-4d INTERIOR %.0f%%  EXTERIOR %.0f%%  NEITHER %.0f%%"
              % (lang, len(sub), 100 * c["INTERIOR"] / len(sub),
                 100 * c["EXTERIOR"] / len(sub), 100 * c["NEITHER"] / len(sub)))

    with open(os.path.join(RESULTS, "prompt_kind.csv"), "w", encoding="utf-8") as fh:
        fh.write("id,kind,unanimous,family,language,prompt\n")
        for i in sorted(A):
            k = unan.get(i, "")
            fh.write('%s,%s,%d,%s,%s,"%s"\n'
                     % (i, k or A[i]["kind"], int(i in unan), K[i]["family"],
                        K[i]["language"].strip(), K[i]["prompt"].replace('"', '""')))
    print("\n  -> %s" % os.path.join(RESULTS, "prompt_kind.csv"))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--save")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    if a.save:
        save(a.save)
    elif a.report:
        report()
    else:
        ap.print_help()
