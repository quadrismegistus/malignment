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


#: VERBATIM from meta/M02_frame_exit/scripts/exit_markers.py, TYPES block.
#: Copied rather than imported because that repo is the read-only archive; the
#: source is named so the two can be diffed. Seven types, REFUSAL declared a
#: priori and REPORTED APART FROM EXIT ALWAYS (M02's rule, not a preference).
import re as _re
EXIT_TYPES = [
    ("E-QUIZ",    _re.compile(r"_{3,}|\([A-D]\)\s|\b[A-D]\.\s+\w|possible answers|"
                              r"multiple choice|fill in the blank|choose the correct", _re.I)),
    ("E-QA",      _re.compile(r"\bQ\s*:|\bA\s*:|\bquestion\s*:|\banswer\s*:|答案", _re.I)),
    ("E-TASK",    _re.compile(r"\btranslate\b|\brewrite\b|\bsummari[sz]e\b|your task is|"
                              r"\bexercise\b|\bcomplete the\b|\bconvert the\b", _re.I)),
    ("E-ASSIST",  _re.compile(r"you are an? (?:ai|helpful|language)|as an ai|"
                              r"i(?:'m| am) an ai|i cannot (?:assist|help|provide)|"
                              r"it(?:'s| is) important to (?:approach|note|remember)|"
                              r"raises (?:some )?(?:significant )?concerns", _re.I)),
    ("E-MENTION", _re.compile(r"words like|the (?:word|term|phrase) [\"'“]|"
                              r"\bmeans\b.{0,20}\bdefinition|refer(?:s|ring) to in the", _re.I)),
    ("E-META",    _re.compile(r"content warning|trigger warning|this (?:excerpt|passage|text) is|"
                              r"\bgenre\b|editor(?:'s|ial) note|\bexcerpt from\b", _re.I)),
    ("REFUSAL",   _re.compile(r"i (?:cannot|can't|won't|will not) (?:write|continue|create|"
                              r"generate|produce|engage|describe)|i(?:'m| am) sorry,? but|"
                              r"i apologi[sz]e,? but|cannot fulfill|against my (?:guidelines|"
                              r"principles|programming)", _re.I)),
]


def exits():
    """Per-passage frame-exit flags over f11_l2, keyed so they can be joined.

    LONG FORM, per RESULTS.md: one row per (model, prompt, sample_idx). Rates are
    a view computed at read time, never the stored record.

    **REFUSAL is excluded from `any_exit`.** M02 declares it a priori and reports
    it apart from exit always; folding it in would silently change what `any_exit`
    means relative to every M02 number."""
    import subprocess, collections
    import pyarrow as pa, pyarrow.parquet as pq
    from malignment import roster
    ep = roster.endpoints()[0]
    chm = set(subprocess.run(["clickhouse", "client", "--query",
        "SELECT DISTINCT model FROM malign_logits.gen_sequences WHERE corpus='f11_l2' "
        "FORMAT TabSeparated"], capture_output=True, text=True, timeout=600).stdout.splitlines())
    arm = {}
    for b, a in ep.items():
        if b in chm and a in chm:
            arm[b] = "base"; arm[a] = "aligned"
    print("22 endpoint pairs -> %d models" % len(arm))
    q = ("SELECT model, prompt, sample_idx, n_tokens, text FROM malign_logits.gen_sequences "
         "WHERE corpus='f11_l2' AND model IN (%s) FORMAT TabSeparated"
         % ",".join("'%s'" % m for m in arm))
    out = subprocess.run(["clickhouse", "client", "--query", q],
                         capture_output=True, text=True, timeout=1800)
    cols = collections.defaultdict(list)
    n = 0
    for line in out.stdout.split("\n"):
        f = line.split("\t")
        if len(f) < 5:
            continue
        m, pr, si, nt, txt = f[0], f[1], f[2], f[3], "\t".join(f[4:])
        n += 1
        cols["model"].append(m); cols["arm"].append(arm[m])
        cols["prompt"].append(pr); cols["sample_idx"].append(int(si))
        cols["n_tokens"].append(int(nt))
        any_exit = False
        for name, pat in EXIT_TYPES:
            h = bool(pat.search(txt))
            cols[name].append(h)
            if h and name != "REFUSAL":
                any_exit = True
        cols["any_exit"].append(any_exit)
    t = pa.table({k: pa.array(v) for k, v in cols.items()})
    p = os.path.join(RESULTS, "frame_exit.parquet")
    pq.write_table(t, p, compression="zstd")
    print("wrote %d rows -> %s (%.1f MB)" % (n, p, os.path.getsize(p) / 1e6))
    print("\n  %-10s %10s %10s %9s" % ("type", "base", "aligned", "delta"))
    for name, _ in EXIT_TYPES + [("any_exit", None)]:
        nb = sum(1 for i, a in enumerate(cols["arm"]) if a == "base")
        na = len(cols["arm"]) - nb
        hb = sum(1 for i, a in enumerate(cols["arm"]) if a == "base" and cols[name][i])
        ha = sum(1 for i, a in enumerate(cols["arm"]) if a == "aligned" and cols[name][i])
        print("  %-10s %9.2f%% %9.2f%% %+8.2f" % (name, 100*hb/nb, 100*ha/na, 100*ha/na - 100*hb/nb))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--save")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--exits", action="store_true")
    a = ap.parse_args()
    if a.save:
        save(a.save)
    elif a.report:
        report()
    elif a.exits:
        exits()
    else:
        ap.print_help()
