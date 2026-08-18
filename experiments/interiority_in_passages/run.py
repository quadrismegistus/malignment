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


PASSA = os.path.join(RESULTS, "passA_codings.json")


def passa_save(src):
    """Lift the two coders' returns out of the workflow output."""
    raw = open(src, encoding="utf-8").read()
    d = json.loads(raw)
    r = d.get("result", d)
    if isinstance(r, str):
        r = json.loads(r)
    json.dump({"A": r["A"], "B": r["B"], "agreement": r.get("agreement"),
               "coded": r.get("coded"), "batches_ok": r.get("batches_ok")},
              open(PASSA, "w", encoding="utf-8"), indent=0, sort_keys=True,
              ensure_ascii=False)
    print("saved %d/%d codings -> %s" % (len(r["A"]), len(r["B"]), PASSA))


FIELDS = ("lexical", "semantic", "repetition", "frame")
#: The value each field takes when NOTHING is wrong. Used only to compute the
#: chance-agreement baseline honestly: these are skewed distributions and a raw
#: agreement rate on a skewed field is not comparable across fields.
LEVELS = {"lexical":    ("clean", "mangled", "nonwords"),
          "semantic":   ("means", "stalls", "salad"),
          "repetition": ("none", "phrase", "block"),
          "frame":      ("none", "furniture", "task", "assistant")}


def _kappa(A, B, ids, f):
    """Cohen's kappa. Raw agreement on a skewed field flatters the instrument."""
    lv = LEVELS[f]
    obs = sum(1 for i in ids if A[i][f] == B[i][f]) / len(ids)
    exp = sum((sum(1 for i in ids if A[i][f] == v) / len(ids)) *
              (sum(1 for i in ids if B[i][f] == v) / len(ids)) for v in lv)
    return obs, exp, (obs - exp) / (1 - exp) if exp < 1 else float("nan")


def passa_report():
    import collections
    R = json.load(open(PASSA, encoding="utf-8"))
    K = json.load(open(os.path.join(RESULTS, "passA_key.json"), encoding="utf-8"))
    A, B = R["A"], R["B"]
    ids = sorted(i for i in A if i in B and i in K)
    print("PASS A PILOT -- %d passages, two blind coders, arms unlabelled\n" % len(ids))

    print("=== AGREEMENT ===")
    print("  %-11s %8s %8s %8s   %s" % ("field", "raw", "chance", "kappa", "reading"))
    for f in FIELDS:
        obs, exp, k = _kappa(A, B, ids, f)
        rd = ("substantial" if k >= .6 else "moderate" if k >= .4 else
              "fair" if k >= .2 else "POOR")
        print("  %-11s %7.1f%% %7.1f%% %8.3f   %s" % (f, 100*obs, 100*exp, k, rd))
    allfour = sum(1 for i in ids if all(A[i][f] == B[i][f] for f in FIELDS))
    print("\n  all four fields agree: %d/%d (%.1f%%)" % (allfour, len(ids), 100*allfour/len(ids)))

    print("\n=== BASE RATES BY ARM (coder-averaged; a field is 'flagged' when not the clean level) ===")
    print("  %-11s %10s %10s %9s" % ("field", "base", "aligned", "delta"))
    for f in FIELDS:
        row = []
        for arm in ("base", "aligned"):
            sub = [i for i in ids if K[i]["arm"] == arm]
            hits = sum(1 for i in sub for M in (A, B) if M[i][f] != LEVELS[f][0])
            row.append(100 * hits / (2 * len(sub)))
        print("  %-11s %9.1f%% %9.1f%% %+8.1f" % (f, row[0], row[1], row[1] - row[0]))

    print("\n=== FULL DISTRIBUTIONS (coder A | coder B), by arm ===")
    for f in FIELDS:
        print("  %s" % f)
        for arm in ("base", "aligned"):
            sub = [i for i in ids if K[i]["arm"] == arm]
            ca = collections.Counter(A[i][f] for i in sub)
            cb = collections.Counter(B[i][f] for i in sub)
            print("    %-8s %s" % (arm, "  ".join(
                "%s %d|%d" % (v, ca[v], cb[v]) for v in LEVELS[f])))

    print("\n=== CODED `frame` vs THE M02 REGEX BATTERY ===")
    print("  The battery is the archive's instrument. Where the coders see an")
    print("  irruption the regexes miss, the regexes are the thing that is wrong.")
    import pyarrow.parquet as pq
    t = pq.read_table(os.path.join(RESULTS, "frame_exit.parquet")).to_pydict()
    reg = {}
    for j in range(len(t["model"])):
        reg[(t["model"][j], t["prompt"][j], t["sample_idx"][j])] = (
            t["any_exit"][j], t["REFUSAL"][j],
            [n for n, _ in EXIT_TYPES if t[n][j]])
    miss = 0
    cells = collections.Counter()
    unmatched = 0
    for i in ids:
        k = (K[i]["model"], K[i]["prompt"], K[i]["sample_idx"])
        if k not in reg:
            unmatched += 1
            continue
        any_exit, refusal, types = reg[k]
        for M, tag in ((A, "A"), (B, "B")):
            coded = M[i]["frame"] != "none"
            cells[(coded, bool(any_exit))] += 1
    print("\n  joined on (model, prompt, sample_idx); %d of %d unmatched"
          % (unmatched, len(ids)))
    n = sum(cells.values())
    print("  %-24s %8s %8s" % ("", "regex +", "regex -"))
    for c in (True, False):
        print("  %-24s %8d %8d" % ("coder %s" % ("+" if c else "-"),
                                   cells[(c, True)], cells[(c, False)]))
    tp, fn = cells[(True, True)], cells[(True, False)]
    fp, tn = cells[(False, True)], cells[(False, False)]
    print("\n  coder-positive rate  %.1f%%   regex-positive rate  %.1f%%"
          % (100*(tp+fn)/n, 100*(tp+fp)/n))
    if tp + fn:
        print("  regex RECALL against the coders: %.1f%% (%d of %d coded irruptions caught)"
              % (100*tp/(tp+fn), tp, tp+fn))
    if tp + fp:
        print("  regex PRECISION against the coders: %.1f%%" % (100*tp/(tp+fp)))
    obs = (tp + tn) / n
    print("  raw agreement %.1f%%" % (100*obs))

    print("\n  coded `frame` level x what the battery fired on:")
    by = collections.defaultdict(collections.Counter)
    for i in ids:
        k = (K[i]["model"], K[i]["prompt"], K[i]["sample_idx"])
        if k not in reg:
            continue
        _, _, types = reg[k]
        for M in (A, B):
            by[M[i]["frame"]][",".join(types) or "(none fired)"] += 1
    for lvl in LEVELS["frame"]:
        tot = sum(by[lvl].values())
        top = ", ".join("%s %d" % (t, c) for t, c in by[lvl].most_common(4))
        print("    %-10s n=%-5d %s" % (lvl, tot, top))

    with open(os.path.join(RESULTS, "passA_pilot.csv"), "w", encoding="utf-8") as fh:
        fh.write("id,model,arm,%s\n" % ",".join(
            "%s_%s" % (f, c) for f in FIELDS for c in "AB"))
        for i in ids:
            fh.write("%s,%s,%s,%s\n" % (i, K[i]["model"], K[i]["arm"], ",".join(
                M[i][f] for f in FIELDS for M in (A, B))))
    print("\n  -> %s" % os.path.join(RESULTS, "passA_pilot.csv"))


def sql_str(s):
    """A ClickHouse string LITERAL. Three ways this went wrong in one session.

    `json.dumps(s)`                  escapes non-ASCII to \\uXXXX, so a Chinese
                                     prompt matched nothing and returned 0 rows.
    `json.dumps(s, ensure_ascii=0)`  emits DOUBLE quotes, which ClickHouse reads
                                     as an IDENTIFIER: "Unknown expression or
                                     function identifier `lomahony/...`".
    single quotes, unescaped         breaks on any apostrophe in a prompt.
    """
    return "'" + s.replace("\\", "\\\\").replace("'", "\\'") + "'"


def fetch_clean(rows, nchars=1200):
    """Passage text with REAL newlines. Use this, never TabSeparated.

    **THE DEFECT THIS EXISTS TO PREVENT.** The Pass A sample was extracted with
    `FORMAT TabSeparated`, which escapes newlines and quotes. Every one of those
    880 passages reached its coders carrying literal `\\n` (82.4%) and `\\'`
    (31.4%) as visible characters, and NOT ONE had a real newline. The source is
    clean -- 190,473 of 228,520 f11_l2 rows contain a genuine char(10) -- so the
    damage was entirely in the extraction.

    It was symmetric (base 83.4% carrying escapes against aligned 81.4%, 6.15
    against 6.72 per passage), so the Pass A arm contrasts stand and that pass
    was not re-run. Pass B is a judgement about narrative form, where paragraph
    structure is part of what is being read, so it gets this instead.

    `rows` is a list of dicts with model / prompt / sample_idx.
    """
    import subprocess
    out = []
    for v in rows:
        q = ("SELECT text FROM malign_logits.gen_sequences WHERE corpus='f11_l2' "
             "AND model=%s AND prompt=%s AND sample_idx=%d FORMAT JSONEachRow"
             % (sql_str(v["model"]), sql_str(v["prompt"]), int(v["sample_idx"])))
        r = subprocess.run(["clickhouse", "client", "--query", q],
                           capture_output=True, text=True, timeout=120)
        got = [json.loads(l) for l in r.stdout.strip().split("\n") if l.strip()]
        if len(got) != 1:
            raise RuntimeError("%d rows for %s / %s / %s -- %s"
                               % (len(got), v["model"], v["prompt"][:30],
                                  v["sample_idx"], r.stderr[:200]))
        out.append(got[0]["text"][:nchars])
    return out


def calib(n=20, seed=20260818):
    """Draw the Pass B calibration set: n at RANDOM from the Pass B population.

    RH: *"maybe we just get 20 random?"* -- right, because hand-picking hard
    cases calibrates the instrument on MY theory of what is hard, and the
    resulting agreement is a number about the selection. Random within the
    population the instrument will actually run on gives an honest IAA estimate.

    The population is the Pass A survivors with ENGLISH prompts, since stage 1
    is English on all 22 pairs and the zh arm is a separate 8-pair replication.

    `a009` is appended as a NAMED PROBE for the stacked-telling question
    (beaver-7b, aligned, coherent, eight state reports and nothing rendered).
    It is reported apart and never counted in the agreement figure.
    """
    import random, collections
    K = json.load(open(os.path.join(RESULTS, "passA_key.json"), encoding="utf-8"))
    R = json.load(open(PASSA, encoding="utf-8"))
    A, B = R["A"], R["B"]
    zh = lambda s: any("一" <= c <= "鿿" for c in s)
    pool = [i for i in sorted(K)
            if A[i]["lexical"] == "clean" == B[i]["lexical"]
            and A[i]["semantic"] == "means" == B[i]["semantic"]
            and A[i]["frame"] in ("none", "furniture")
            and B[i]["frame"] in ("none", "furniture")
            and not zh(K[i]["prompt"])]
    print("Pass B population in the pilot, English prompts: %d" % len(pool))
    random.seed(seed)
    pick = sorted(random.sample(pool, n))
    print("drawn %d, seed %d | %s"
          % (n, seed, dict(collections.Counter(K[i]["arm"] for i in pick))))
    ids = pick + ["a009"]
    texts = fetch_clean([K[i] for i in ids])
    out = {}
    for j, (i, txt) in enumerate(zip(ids, texts)):
        key = ("q%03d" % j) if i != "a009" else "PROBE"
        out[key] = {"fragment": K[i]["prompt"], "continuation": txt,
                    "_src": i, "_model": K[i]["model"], "_arm": K[i]["arm"]}
    esc = sum(1 for v in out.values() if "\\n" in v["continuation"])
    nl = sum(1 for v in out.values() if "\n" in v["continuation"])
    print("extracted %d | still-escaped %d | real newlines in %d" % (len(out), esc, nl))
    p = os.path.join(RESULTS, "calib20.json")
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("-> %s\n" % p)
    for k in sorted(out):
        v = out[k]
        print("  %-6s %-3s %-26s %s" % (k, v["_arm"][:3], v["_model"].split("/")[-1][:26],
                                        " ".join(v["continuation"][:88].split())))


def passb_build():
    """The Pass B pilot set: the ENGLISH Pass A survivors, re-fetched clean.

    **Not a fresh draw.** Pass B only ever runs on survivors, Pass A is already
    done on these exact passages, and everything joins on one key with no
    second extraction. RH, on the alternative of a fresh 880: batch size does
    not shorten wall clock -- it is total-work-over-concurrency -- so the way
    to a short pilot is fewer codings, not bigger batches.

    English only: stage 1 is English on all 22 pairs; the zh arm is a separate
    8-pair replication and an English-designed rubric is a different instrument
    on Chinese.

    NOT balanced by construction, unlike the Pass A draw. Balance buys nothing
    here -- each arm's rate is computed within arm -- and discarding aligned
    passages to match base would throw away precision for symmetry's sake.
    """
    import collections
    K = json.load(open(os.path.join(RESULTS, "passA_key.json"), encoding="utf-8"))
    R = json.load(open(PASSA, encoding="utf-8"))
    A, B = R["A"], R["B"]
    zh = lambda s: any("一" <= c <= "鿿" for c in s)
    keep = [i for i in sorted(K)
            if A[i]["lexical"] == "clean" == B[i]["lexical"]
            and A[i]["semantic"] == "means" == B[i]["semantic"]
            and A[i]["frame"] in ("none", "furniture")
            and B[i]["frame"] in ("none", "furniture")
            and not zh(K[i]["prompt"])]
    print("Pass A survivors: %d | English: %d" % (
        sum(1 for i in K if A[i]["lexical"] == "clean" == B[i]["lexical"]
            and A[i]["semantic"] == "means" == B[i]["semantic"]
            and A[i]["frame"] in ("none", "furniture")
            and B[i]["frame"] in ("none", "furniture")), len(keep)))
    print("  arms: %s" % dict(collections.Counter(K[i]["arm"] for i in keep)))
    print("  models: %d of 44" % len(set(K[i]["model"] for i in keep)))
    texts = fetch_clean([K[i] for i in keep])
    out = {}
    for j, (i, txt) in enumerate(zip(keep, texts)):
        out["b%03d" % j] = {"fragment": K[i]["prompt"], "continuation": txt,
                            "_src": i, "_model": K[i]["model"], "_arm": K[i]["arm"],
                            "_sample_idx": K[i]["sample_idx"]}
    esc = sum(1 for v in out.values() if "\\n" in v["continuation"])
    print("  extracted %d | still-escaped %d | real newlines in %d"
          % (len(out), esc, sum(1 for v in out.values() if "\n" in v["continuation"])))
    p = os.path.join(RESULTS, "passB_pilot.json")
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  -> %s" % p)
    return out


PASSB = os.path.join(RESULTS, "passB_codings.json")


def passb_save(src):
    raw = json.load(open(src, encoding="utf-8"))
    r = raw.get("result", raw)
    if isinstance(r, str):
        r = json.loads(r)
    json.dump({"A": r["A"], "B": r["B"], "agree": r.get("agree")},
              open(PASSB, "w", encoding="utf-8"), indent=0, sort_keys=True,
              ensure_ascii=False)
    print("saved %d/%d -> %s" % (len(r["A"]), len(r["B"]), PASSB))


def passb_report():
    """Pass B pilot. 190 English Pass A survivors, two blind coders.

    **THE UNIT IS WRONG FOR A TEST AND SAID SO.** 190 passages over 41 models is
    ~2.3 per model per arm, so the per-pair sign test here is a preview of shape,
    not a result. Passage-level rates are quoted because they are what this n
    supports; the real run's unit is the 22 lineage pairs.
    """
    import csv, itertools, collections, statistics as st, yaml
    R = json.load(open(PASSB, encoding="utf-8"))
    K = json.load(open(os.path.join(RESULTS, "passB_pilot.json"), encoding="utf-8"))
    A, B = R["A"], R["B"]
    ids = sorted(i for i in A if i in B and i in K)
    MODE = ("NONE", "TOLD", "SHOWN")
    DRIFT = ("HOLDS", "SHIFTS", "UNMOORED")

    def kappa(f, lv):
        obs = sum(1 for i in ids if A[i][f] == B[i][f]) / len(ids)
        exp = sum((sum(1 for i in ids if A[i][f] == v) / len(ids)) *
                  (sum(1 for i in ids if B[i][f] == v) / len(ids)) for v in lv)
        return obs, exp, (obs - exp) / (1 - exp)

    print("PASS B PILOT -- %d passages, two blind coders, arms unlabelled\n" % len(ids))
    print("=== AGREEMENT ===")
    for f, lv in (("mode", MODE), ("drift", DRIFT), ("degree", (0, 1, 2, 3))):
        o, e, k = kappa(f, lv)
        print("  %-8s raw %5.1f%%  chance %5.1f%%  kappa %.3f" % (f, 100*o, 100*e, k))
    w1 = sum(1 for i in ids if abs(A[i]["degree"] - B[i]["degree"]) <= 1) / len(ids)
    print("  degree within 1 point: %.1f%%" % (100*w1))
    print("\n  where mode disagrees, what are the pairs?")
    c = collections.Counter(tuple(sorted((A[i]["mode"], B[i]["mode"])))
                            for i in ids if A[i]["mode"] != B[i]["mode"])
    for k2, v in c.most_common():
        print("    %-16s %d" % ("/".join(k2), v))

    print("\n=== BY ARM (coder-averaged; %d base, %d aligned passages) ==="
          % (sum(1 for i in ids if K[i]["_arm"] == "base"),
             sum(1 for i in ids if K[i]["_arm"] == "aligned")))
    print("  %-22s %10s %10s %9s" % ("", "base", "aligned", "delta"))
    for lbl, pred in (("mode NONE", lambda M, i: M[i]["mode"] == "NONE"),
                      ("mode TOLD", lambda M, i: M[i]["mode"] == "TOLD"),
                      ("mode SHOWN", lambda M, i: M[i]["mode"] == "SHOWN"),
                      ("any interiority", lambda M, i: M[i]["mode"] != "NONE"),
                      ("SHOWN | interior", None)):
        row = []
        for arm in ("base", "aligned"):
            sub = [i for i in ids if K[i]["_arm"] == arm]
            if lbl == "SHOWN | interior":
                num = sum(1 for i in sub for M in (A, B) if M[i]["mode"] == "SHOWN")
                den = sum(1 for i in sub for M in (A, B) if M[i]["mode"] != "NONE")
                row.append(100 * num / den if den else float("nan"))
            else:
                row.append(100 * sum(1 for i in sub for M in (A, B) if pred(M, i))
                           / (2 * len(sub)))
        print("  %-22s %9.1f%% %9.1f%% %+8.1f" % (lbl, row[0], row[1], row[1] - row[0]))
    for arm in ("base", "aligned"):
        sub = [i for i in ids if K[i]["_arm"] == arm]
        print("  mean degree, %-8s %.3f" % (arm, st.mean(M[i]["degree"] for i in sub for M in (A, B))))
    print("  %-22s %10s %10s %9s" % ("drift", "base", "aligned", "delta"))
    for lv in DRIFT:
        row = [100 * sum(1 for i in ids if K[i]["_arm"] == arm and A[i]["drift"] == lv)
               / max(sum(1 for i in ids if K[i]["_arm"] == arm), 1) for arm in ("base", "aligned")]
        print("  %-22s %9.1f%% %9.1f%% %+8.1f" % ("  " + lv, row[0], row[1], row[1] - row[0]))

    print("\n=== F13's TRADE-OFF AT PASSAGE SCALE: mode x drift ===")
    print("  Does interiority arrive with the scene intact, or where it stops?")
    print("  %-10s %5s %8s %8s %8s   %s" % ("drift", "n", "NONE", "TOLD", "SHOWN", "mean deg"))
    for lv in DRIFT:
        sub = [i for i in ids if A[i]["drift"] == lv == B[i]["drift"]]
        if not sub:
            continue
        cc = collections.Counter(M[i]["mode"] for i in sub for M in (A, B))
        n = sum(cc.values())
        print("  %-10s %5d %7.1f%% %7.1f%% %7.1f%%   %.2f"
              % (lv, len(sub), 100*cc["NONE"]/n, 100*cc["TOLD"]/n, 100*cc["SHOWN"]/n,
                 st.mean(M[i]["degree"] for i in sub for M in (A, B))))
    print("\n  and the same split WITHIN each arm (SHOWN share among interior):")
    for arm in ("base", "aligned"):
        out = []
        for lv in DRIFT:
            sub = [i for i in ids if K[i]["_arm"] == arm and A[i]["drift"] == lv == B[i]["drift"]]
            num = sum(1 for i in sub for M in (A, B) if M[i]["mode"] == "SHOWN")
            den = sum(1 for i in sub for M in (A, B) if M[i]["mode"] != "NONE")
            out.append("%s %s" % (lv[:4], ("%.0f%% (%d)" % (100*num/den, den)) if den else "-"))
        print("    %-8s %s" % (arm, "   ".join(out)))

    print("\n=== BY PROMPT KIND (the echo check) ===")
    kind = {}
    for r in csv.DictReader(open(os.path.join(RESULTS, "prompt_kind.csv"), encoding="utf-8")):
        if r["unanimous"] == "1":
            kind[r["prompt"]] = r["kind"]
    print("  %-10s %5s %10s %10s %9s" % ("kind", "n", "base int%", "algn int%", "delta"))
    for kk in ("EXTERIOR", "INTERIOR", "NEITHER"):
        sub = [i for i in ids if kind.get(K[i]["fragment"]) == kk]
        if not sub:
            continue
        row = []
        for arm in ("base", "aligned"):
            s2 = [i for i in sub if K[i]["_arm"] == arm]
            row.append(100 * sum(1 for i in s2 for M in (A, B) if M[i]["mode"] != "NONE")
                       / (2 * len(s2)) if s2 else float("nan"))
        print("  %-10s %5d %9.1f%% %9.1f%% %+8.1f" % (kk, len(sub), row[0], row[1], row[1] - row[0]))

    print("\n=== BY QUINTUPLET ROLE ===")
    SRC = os.path.join(os.path.dirname(os.path.dirname(HERE)),
                       "roster", "prompts", "flat", "quintuplets.yaml")
    role = {q["prompt"]: q["group_role"] for q in yaml.safe_load(open(SRC, encoding="utf-8"))["prompts"]}
    print("  %-14s %5s %10s %10s %9s" % ("role", "n", "base int%", "algn int%", "delta"))
    for rr in ("POLE_A", "POLE_B", "BOTH", "CONTROL_A", "CONTROL_B"):
        sub = [i for i in ids if role.get(K[i]["fragment"]) == rr]
        if not sub:
            continue
        row = []
        for arm in ("base", "aligned"):
            s2 = [i for i in sub if K[i]["_arm"] == arm]
            row.append(100 * sum(1 for i in s2 for M in (A, B) if M[i]["mode"] != "NONE")
                       / (2 * len(s2)) if s2 else float("nan"))
        print("  %-14s %5d %9.1f%% %9.1f%% %+8.1f" % (rr, len(sub), row[0], row[1], row[1] - row[0]))

    print("\n=== PER-PAIR PREVIEW -- SHAPE ONLY, NOT A TEST ===")
    from malignment import roster
    ep = roster.endpoints()[0]
    rev = {}
    for b, a in ep.items():
        rev[b] = b; rev[a] = b
    per = collections.defaultdict(lambda: collections.defaultdict(list))
    for i in ids:
        base = rev.get(K[i]["_model"])
        if base:
            per[base][K[i]["_arm"]].append(st.mean(M[i]["degree"] for M in (A, B)))
    ok = [(p, st.mean(v["base"]), st.mean(v["aligned"]))
          for p, v in per.items() if v["base"] and v["aligned"]]
    up = sum(1 for _, b, a in ok if a > b)
    dn = sum(1 for _, b, a in ok if a < b)
    print("  pairs with BOTH arms present: %d of 22" % len(ok))
    print("  aligned mean degree higher in %d, lower in %d, tied %d"
          % (up, dn, len(ok) - up - dn))
    print("  median passages per arm in those pairs: %.1f"
          % st.median([len(v["base"]) + len(v["aligned"]) for p, v in per.items()
                       if v["base"] and v["aligned"]]))
    print("  -> at this n a sign test is not worth computing; the real run is 22 pairs")

    with open(os.path.join(RESULTS, "passB_pilot.csv"), "w", encoding="utf-8") as fh:
        fh.write("id,model,arm,mode_A,mode_B,degree_A,degree_B,drift_A,drift_B,span_A\n")
        for i in ids:
            fh.write('%s,%s,%s,%s,%s,%d,%d,%s,%s,"%s"\n'
                     % (i, K[i]["_model"], K[i]["_arm"], A[i]["mode"], B[i]["mode"],
                        A[i]["degree"], B[i]["degree"], A[i]["drift"], B[i]["drift"],
                        A[i]["span"].replace('"', '""')))
    print("\n  -> %s" % os.path.join(RESULTS, "passB_pilot.csv"))


def combined_build(n=60, seed=20260819):
    """Smoke set for a MERGED Pass A+B form: random over ALL 880, not survivors.

    RH: *"do we need all the Pass A questions? can't we just ask 'is this
    narrative throughout, no interruptions?'"* -- testable, but only against
    passages that FAIL. The 190 Pass B passages are all survivors, so they
    cannot test a filter; this draws from the whole Pass A sample, where the
    survival rate is ~32%.

    Text is re-fetched CLEAN, which means the comparison against Pass A's
    composite decision carries one known confound: Pass A read escaped text
    (literal \\n in 82.4%), and escapes push `lexical` toward `mangled`. So
    Pass A's filter is conservative, and disagreements in the direction of the
    merged form keeping MORE passages are expected rather than alarming.
    """
    import random, collections
    K = json.load(open(os.path.join(RESULTS, "passA_key.json"), encoding="utf-8"))
    R = json.load(open(PASSA, encoding="utf-8"))
    A, B = R["A"], R["B"]
    zh = lambda s: any("一" <= c <= "鿿" for c in s)
    pool = [i for i in sorted(K) if not zh(K[i]["prompt"])]
    random.seed(seed)
    pick = sorted(random.sample(pool, n))

    def readable(i):
        return (A[i]["lexical"] == "clean" == B[i]["lexical"]
                and A[i]["semantic"] == "means" == B[i]["semantic"])

    #: LENIENT was the Pass B pilot's filter and it was WRONG. It admitted
    #: `frame=furniture` -- web paratext, comment widgets, bylines, post dates --
    #: on my judgement that a heading above a scene is still a scene. RH:
    #: *"I thought we agreed to give Pass B only entirely clean narrative text."*
    #: 21% of the Pass B set carried furniture, base-heavy (27% of base against
    #: 16% of aligned), and removing it cut the drift arm-difference from +17.4pp
    #: to +5.4pp. The call is recorded here rather than left in a docstring
    #: because it changed a reported number.
    def survives(i):
        return readable(i) and A[i]["frame"] == "none" == B[i]["frame"]

    def survives_lenient(i):
        return (readable(i) and A[i]["frame"] in ("none", "furniture")
                and B[i]["frame"] in ("none", "furniture"))
    print("English Pass A passages: %d | drawn %d (seed %d)" % (len(pool), n, seed))
    print("  STRICT (frame=none)      keeps %d, drops %d"
          % (sum(1 for i in pick if survives(i)), sum(1 for i in pick if not survives(i))))
    print("  lenient (+furniture)     keeps %d  <- the Pass B pilot's filter, superseded"
          % sum(1 for i in pick if survives_lenient(i)))
    print("  arms: %s" % dict(collections.Counter(K[i]["arm"] for i in pick)))
    texts = fetch_clean([K[i] for i in pick])
    out = {}
    for j, (i, txt) in enumerate(zip(pick, texts)):
        out["c%03d" % j] = {"fragment": K[i]["prompt"], "continuation": txt,
                            "_src": i, "_model": K[i]["model"], "_arm": K[i]["arm"],
                            "_passA_keep": survives(i),
                            "_passA": {"lexical": A[i]["lexical"], "semantic": A[i]["semantic"],
                                       "frame": A[i]["frame"]}}
    p = os.path.join(RESULTS, "combined_smoke.json")
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  extracted %d clean -> %s" % (len(out), p))


def combined_report():
    """Does one narrative question reproduce Pass A's three-field filter?"""
    import itertools, collections, statistics as st
    R = json.load(open(os.path.join(RESULTS, "combined_codings.json"), encoding="utf-8"))
    K = json.load(open(os.path.join(RESULTS, "combined_smoke.json"), encoding="utf-8"))
    A, B = R["A"], R["B"]
    ids = sorted(i for i in A if i in B and i in K)
    print("MERGED FORM SMOKE -- %d passages, two blind coders\n" % len(ids))

    def kappa(f, lv):
        obs = sum(1 for i in ids if A[i][f] == B[i][f]) / len(ids)
        exp = sum((sum(1 for i in ids if A[i][f] == v) / len(ids)) *
                  (sum(1 for i in ids if B[i][f] == v) / len(ids)) for v in lv)
        return obs, exp, (obs - exp) / (1 - exp) if exp < 1 else float("nan")

    print("=== AGREEMENT, six fields in one form ===")
    print("  (Pass B alone, n=190, gave mode 0.893 drift 0.865 degree 0.837)")
    for f, lv in (("narrative", (True, False)), ("why", ("", "UNREADABLE", "NOT_A_STORY", "INTERRUPTED")),
                  ("mode", ("NONE", "TOLD", "SHOWN")),
                  ("drift", ("HOLDS", "SHIFTS", "UNMOORED")), ("degree", (0, 1, 2, 3))):
        if f not in A[ids[0]]:
            continue
        o, e, k = kappa(f, lv)
        print("  %-10s raw %5.1f%%  chance %5.1f%%  kappa %.3f" % (f, 100*o, 100*e, k))

    print("\n=== DOES ONE QUESTION REPRODUCE THE THREE-FIELD FILTER? ===")
    cells = collections.Counter()
    for i in ids:
        for M in (A, B):
            cells[(bool(M[i]["narrative"]), bool(K[i]["_passA_keep"]))] += 1
    n = sum(cells.values())
    print("  %-22s %12s %12s" % ("", "Pass A KEEP", "Pass A DROP"))
    for v in (True, False):
        print("  %-22s %12d %12d" % ("merged " + ("YES" if v else "NO "),
                                     cells[(v, True)], cells[(v, False)]))
    agree = (cells[(True, True)] + cells[(False, False)]) / n
    print("\n  agreement %.1f%%" % (100*agree))
    print("  merged keeps %.1f%% | Pass A keeps %.1f%%"
          % (100*(cells[(True, True)] + cells[(True, False)])/n,
             100*(cells[(True, True)] + cells[(False, True)])/n))

    print("\n  WHERE THEY DIFFER, what did Pass A see?")
    for mv, pv, lbl in ((True, False, "merged YES, Pass A DROP"),
                        (False, True, "merged NO,  Pass A KEEP")):
        sub = [(i, M) for i in ids for M in (A, B)
               if bool(M[i]["narrative"]) == mv and bool(K[i]["_passA_keep"]) == pv]
        if not sub:
            continue
        c = collections.Counter()
        for i, M in sub:
            pa = K[i]["_passA"]
            c[(pa["lexical"], pa["semantic"], pa["frame"])] += 1
        print("    %s (%d):" % (lbl, len(sub)))
        for k2, v in c.most_common(5):
            print("      lexical=%-8s semantic=%-6s frame=%-9s  %d" % (k2 + (v,)))

    print("\n=== `why` AGAINST PASS A's REASON ===")
    x = collections.defaultdict(collections.Counter)
    for i in ids:
        for M in (A, B):
            if M[i]["narrative"]:
                continue
            pa = K[i]["_passA"]
            reason = ("UNREADABLE" if pa["lexical"] != "clean" or pa["semantic"] != "means"
                      else "FRAME" if pa["frame"] in ("task", "assistant") else "(Pass A kept it)")
            x[M[i].get("why", "")][reason] += 1
    for w in sorted(x):
        print("  merged why=%-12s -> %s" % (w, dict(x[w])))


def roles():
    """Quintuplet role per prompt, from the DECLARED field. Not reconstructed.

    `gen_sequences` has `role` and `pair` columns and BOTH ARE EMPTY for
    f11_l2 -- one distinct value ('') over all 228,520 rows. Checked, not
    assumed. But the roles are authored in
    `roster/prompts/flat/quintuplets.yaml` (200 prompts, 44 groups), so this
    reads them rather than inferring them from prompt text.

        POLE_A / POLE_B     He was beautiful / disgusting and she wanted to
        BOTH                He was beautiful and disgusting and she wanted to
        CONTROL_A / _B      He was beautiful and radiant and she wanted to

    **Joined on prompt TEXT, never prompt_id** (RH's standing rule).

    Two facts the file states and this must not flatten:
      - only 34 of 44 groups have CONTROLS; the other 10 are triplets.
      - status is CARRIED, NOT FILTERED ([5084].2, "a shape filter is not a
        membership filter"): 41 groups ACTIVE, 2 MIXED ACTIVE/DISPUTED, 1
        RETIRED. The population choice is an open construct ruling, so both
        the full and the ACTIVE-only counts are printed and neither is
        silently adopted here.
    """
    import csv, collections, yaml
    import pyarrow.parquet as pq
    SRC = os.path.join(os.path.dirname(os.path.dirname(HERE)),
                       "roster", "prompts", "flat", "quintuplets.yaml")
    Q = yaml.safe_load(open(SRC, encoding="utf-8"))["prompts"]
    role = {q["prompt"]: q["group_role"] for q in Q}
    group = {q["prompt"]: q["group_id"] for q in Q}
    status = {q["prompt"]: q.get("status", "") for q in Q}
    print("declared source: %s" % SRC)
    print("  %d prompts, %d groups, roles %s"
          % (len(Q), len(set(group.values())),
             dict(collections.Counter(role.values()))))

    kind = {}
    for r in csv.DictReader(open(os.path.join(RESULTS, "prompt_kind.csv"), encoding="utf-8")):
        if r["unanimous"] == "1":
            kind[r["prompt"]] = r["kind"]

    t = pq.read_table(os.path.join(RESULTS, "frame_exit.parquet")).to_pydict()
    pr = sorted(set(t["prompt"]))
    hit = [p for p in pr if p in role]
    print("\n%d corpus prompts; %d join the declared file BY TEXT, %d do not"
          % (len(pr), len(hit), len(pr) - len(hit)))
    c = collections.Counter(role.get(p, "(not declared)") for p in pr)
    print("  " + "  ".join("%s %d" % kv for kv in c.most_common()))
    gs = collections.Counter(status.get(p) for p in hit)
    print("  status of the joining prompts: %s" % dict(gs))
    ng = collections.Counter()
    for p in hit:
        ng[group[p]] += 1
    print("  groups represented: %d ; complete 5-member groups in-corpus: %d ; "
          "3-member: %d" % (len(ng), sum(1 for v in ng.values() if v == 5),
                            sum(1 for v in ng.values() if v == 3)))
    if len(pr) - len(hit):
        print("  NOT DECLARED (first 5): %s"
              % [p[:44] for p in pr if p not in role][:5])

    print("\n=== Q1. IS ROLE BALANCED ACROSS ARMS? ===")
    print("  It is balanced BY CONSTRUCTION: every model sees every prompt")
    print("  exactly 20 times, so no prompt property can confound the arm")
    print("  contrast. Asserted rather than assumed:")
    cell = collections.Counter()
    for j in range(len(t["model"])):
        cell[(t["arm"][j], role.get(t["prompt"][j], "(not declared)"))] += 1
    for r in sorted(set(role.get(p, "(not declared)") for p in pr)):
        b, a = cell[("base", r)], cell[("aligned", r)]
        print("    %-14s base %7d  aligned %7d  %s" % (r, b, a, "EQUAL" if b == a else "*** UNEQUAL ***"))

    print("\n=== Q2. DOES ROLE CLUSTER IN A PROMPT-KIND STRATUM? ===")
    print("  If it did, a between-stratum difference could really be a role difference.")
    x = collections.defaultdict(collections.Counter)
    for p in pr:
        if p in kind and p in role:
            x[role[p]][kind[p]] += 1
    print("  %-14s %9s %9s %9s %7s" % ("role", "EXTERIOR", "INTERIOR", "NEITHER", "n"))
    for r in sorted(x):
        n = sum(x[r].values())
        print("  %-14s %8d%% %8d%% %8d%% %7d"
              % (r, round(100*x[r]["EXTERIOR"]/n), round(100*x[r]["INTERIOR"]/n),
                 round(100*x[r]["NEITHER"]/n), n))
    print("  %-14s %8d%% %8d%% %8d%% %7d"
          % ("ALL", round(100*sum(v["EXTERIOR"] for v in x.values())/sum(sum(v.values()) for v in x.values())),
             round(100*sum(v["INTERIOR"] for v in x.values())/sum(sum(v.values()) for v in x.values())),
             round(100*sum(v["NEITHER"] for v in x.values())/sum(sum(v.values()) for v in x.values())),
             sum(sum(v.values()) for v in x.values())))

    print("\n=== Q3. THE REAL HAZARD: DOES THE COHERENCE FILTER RETAIN BY ROLE x ARM? ===")
    print("  The filter is POST-TREATMENT. If contradiction prompts break base")
    print("  models harder, filtering leaves the two arms with different role")
    print("  compositions, and a composition difference is not an arm effect.")
    try:
        R = json.load(open(PASSA, encoding="utf-8"))
        PK = json.load(open(os.path.join(RESULTS, "passA_key.json"), encoding="utf-8"))
    except IOError:
        print("  (pilot codings not present)")
        return
    A, B = R["A"], R["B"]

    def ok(i, M):
        return (M[i]["semantic"] == "means" and M[i]["lexical"] == "clean"
                and M[i]["frame"] in ("none", "furniture"))
    keep = collections.defaultdict(lambda: [0, 0])
    for i in sorted(PK):
        r = role.get(PK[i]["prompt"], "(not declared)")
        k = (PK[i]["arm"], r)
        keep[k][1] += 1
        if ok(i, A) and ok(i, B):
            keep[k][0] += 1
    print("  %-14s %18s %18s %10s" % ("role", "base kept", "aligned kept", "gap"))
    for r in sorted(set(k[1] for k in keep)):
        b, a = keep[("base", r)], keep[("aligned", r)]
        if not b[1] or not a[1]:
            continue
        yb, ya = 100*b[0]/b[1], 100*a[0]/a[1]
        print("  %-14s %8.1f%% (%3d/%3d) %8.1f%% (%3d/%3d) %+9.1f"
              % (r, yb, b[0], b[1], ya, a[0], a[1], ya - yb))
    print("\n  A CONSTANT gap across roles means the filter is role-neutral and")
    print("  composition is preserved. A gap that varies by role is the thing to")
    print("  correct for, by filtering within (prompt, arm) or reweighting.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--roles", action="store_true")
    ap.add_argument("--calib", action="store_true")
    ap.add_argument("--passb-build", action="store_true")
    ap.add_argument("--passb-save")
    ap.add_argument("--passb", action="store_true")
    ap.add_argument("--combined-build", action="store_true")
    ap.add_argument("--combined", action="store_true")
    ap.add_argument("--save")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--exits", action="store_true")
    ap.add_argument("--passa-save")
    ap.add_argument("--passa", action="store_true")
    a = ap.parse_args()
    if a.save:
        save(a.save)
    elif a.report:
        report()
    elif a.exits:
        exits()
    elif a.passa_save:
        passa_save(a.passa_save)
    elif a.passa:
        passa_report()
    elif a.roles:
        roles()
    elif a.calib:
        calib()
    elif a.passb_build:
        passb_build()
    elif a.passb_save:
        passb_save(a.passb_save)
    elif a.passb:
        passb_report()
    elif a.combined_build:
        combined_build()
    elif a.combined:
        combined_report()
    else:
        ap.print_help()
