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


#: ---------------------------------------------------------------- PASS C ----
#: The real run, built to survive a session ending mid-way. Three properties,
#: each of which was ABSENT until RH asked "what if I run out of tokens
#: midway... this is all saved and resumable?"
#:
#:   1. the sample is MATERIALISED to parquet, so no rerun re-queries ClickHouse
#:      and no result depends on the roster or the corpus being unchanged later
#:   2. codings land ONE FILE PER SHARD as each finishes, so a kill loses at
#:      most one shard
#:   3. the rubric lives in plans/passC_rubric.md and is read at build time, so
#:      a fresh session cannot silently use a different prompt
#:
#: `resumeFromRunId` is SAME-SESSION ONLY. It is not a resume story across a
#: token exhaustion, which is what this is for.

PASSC = os.path.join(RESULTS, "passC")
PASSC_SAMPLE = os.path.join(PASSC, "sample.parquet")
PASSC_TRIAGE = os.path.join(PASSC, "triage.parquet")
#: The five fields a Pass C coding must carry. A record with fewer came from a
#: different instrument (the Haiku triage returned {id, narrative} alone).
FIELDS_C = frozenset(("narrative", "mode", "drift", "degree", "span"))
RUBRIC_MD = os.path.join(HERE, "plans", "passC_rubric.md")


def passc_key():
    """Every passage Pass C may have coded, from BOTH draws, keyed by id.

    Two draws exist and they use different id spaces:

        sample.parquet   p######   the original random draw, 714/cell.
                                   Shards 00-11 code 535/cell of it.
        triage.parquet   f######   the classifier-ranked draw that superseded
                                   it. L00-L25 code the top-200/cell.

    Reading `sample.parquet` alone is right for the shard-0* codings and wrong
    for the lineage ones, and the worst case is SILENT: `passc_recover()`
    filters journal codings against this set, so an f-id would be dropped as
    "not in the sample" -- discarding recovered work rather than failing.

    They are ALTERNATIVE populations, not addends: one is random within a frozen
    sample, the other is classifier-ranked. This function unions them so nothing
    is lost; it does NOT license pooling them in an analysis.
    """
    import pyarrow.parquet as pq
    out = {}
    for path in (PASSC_SAMPLE, PASSC_TRIAGE):
        if not os.path.exists(path):
            continue
        t = pq.read_table(path).to_pydict()
        for j in range(len(t["id"])):
            out[t["id"][j]] = dict(model=t["model"][j], arm=t["arm"][j],
                                   pair=t["pair"][j], prompt=t["prompt"][j],
                                   text=t["text"][j],
                                   draw=("sample" if path == PASSC_SAMPLE else "triage"))
    return out


def rubric_text():
    """The coder prompt, read from the frozen markdown. Never inlined here."""
    src = open(RUBRIC_MD, encoding="utf-8").read()
    parts = src.split("<<<RUBRIC>>>")
    if len(parts) != 3:
        raise RuntimeError("expected exactly two <<<RUBRIC>>> markers in %s, found %d"
                           % (RUBRIC_MD, len(parts) - 1))
    return parts[1].strip()


def passc_sample(per_cell=714, seed=20260818, lang="en"):
    """Freeze the sample. 29 lineages, both arms, uniform over prompts.

    **ENGLISH ONLY.** Stage 1 is English on all 29 pairs; the zh arm is a
    separate replication on the 8 `cjk_tier` FLUENT pairs and an English-designed
    rubric is a different instrument on Chinese. The first build of this file did
    NOT filter language, so 535 drawn per cell was 271 English per cell and
    delivered ~76 clean where 150 was the target. Caught by RH asking what was
    actually in the parquet.

    `per_cell` is SAMPLED passages, not clean ones: 200 clean at the merged
    form's ~28% narrative yield needs ~714 drawn. The yield is an estimate, so
    the stored sample is what we committed to draw and the clean count lands
    where it lands.

    **OVER-PROVISIONED ON PURPOSE.** 714 is n=200 worth while the declared
    target is n=150. Extending later is then "code more ids from the same frozen
    file, in the same declared order" -- uniform by construction, with no second
    draw to defend and no seed argument to have. Selective extension is the only
    thing that would compromise the design and this makes it impossible by
    accident.

    **Uniform over the 197 prompts**, which serves all three readings at once:
    per-stratum rates, the per-pair Wilcoxon, and prompt as a sign-test unit.

    Population is every lineage with BOTH arms present in f11_l2 -- 29 of them,
    58 models, 100% of the corpus. Not `endpoints()`, which wanted aligned arms
    this corpus does not have and so dropped 7 whole lineages including the only
    three base-vs-DPO contrasts and Mistral->zephyr.
    """
    import random, subprocess, collections
    import pyarrow as pa, pyarrow.parquet as pq
    from malignment import roster
    os.makedirs(PASSC, exist_ok=True)
    have = set(subprocess.run(["clickhouse", "client", "--query",
        "SELECT DISTINCT model FROM malign_logits.gen_sequences WHERE corpus='f11_l2' "
        "FORMAT TabSeparated"], capture_output=True, text=True, timeout=600).stdout.split())
    pairs = []
    for base, arms in roster.lineages().items():
        if base not in have:
            continue
        al = [m for m in arms if m != base and m in have]
        if len(al) == 1:
            pairs.append((base, al[0]))
        elif len(al) > 1:
            raise RuntimeError("lineage %s has %d aligned arms in f11_l2; the "
                               "pairing rule assumes one. Decide explicitly."
                               % (base, len(al)))
    pairs.sort()
    models = [m for p in pairs for m in p]
    print("population: %d lineages, %d models" % (len(pairs), len(models)))

    CJK = _re.compile(r"[\u4e00-\u9fff]")
    rows = collections.defaultdict(list)
    q = ("SELECT model, prompt, sample_idx, text FROM malign_logits.gen_sequences "
         "WHERE corpus='f11_l2' AND model IN (%s) FORMAT JSONEachRow"
         % ",".join(sql_str(m) for m in models))
    out = subprocess.run(["clickhouse", "client", "--query", q],
                         capture_output=True, text=True, timeout=3600)
    n = 0
    for line in out.stdout.split("\n"):
        if not line.strip():
            continue
        r = json.loads(line)
        n += 1
        r["language"] = "zh" if CJK.search(r["prompt"]) else "en"
        if lang and r["language"] != lang:
            continue
        rows[r["model"]].append(r)
    kept = sum(len(v) for v in rows.values())
    print("fetched %s rows (JSONEachRow, so text carries REAL newlines)" % format(n, ","))
    print("  language filter %r -> %s rows eligible (%.0f%%)"
          % (lang, format(kept, ","), 100 * kept / n))
    esc = sum(1 for v in rows.values() for r in v[:50] if "\\n" in r["text"])
    print("  spot check, literal backslash-n in first 50 per model: %d" % esc)

    arm = {}
    for b, a in pairs:
        arm[b] = "base"; arm[a] = "aligned"
    cols = collections.defaultdict(list)
    rng = random.Random(seed)
    for m in models:
        v = sorted(rows[m], key=lambda r: (r["prompt"], r["sample_idx"]))
        take = v if len(v) <= per_cell else rng.sample(v, per_cell)
        for r in sorted(take, key=lambda r: (r["prompt"], r["sample_idx"])):
            cols["model"].append(m)
            cols["arm"].append(arm[m])
            cols["pair"].append([b for b, a in pairs if m in (b, a)][0])
            cols["prompt"].append(r["prompt"])
            cols["language"].append(r["language"])
            cols["sample_idx"].append(int(r["sample_idx"]))
            cols["text"].append(r["text"])
    ids = ["p%06d" % i for i in range(len(cols["model"]))]
    cols["id"] = ids
    t = pa.table({k: pa.array(v) for k, v in cols.items()})
    pq.write_table(t, PASSC_SAMPLE, compression="zstd")
    print("\nwrote %s passages -> %s (%.1f MB)"
          % (format(len(ids), ","), PASSC_SAMPLE, os.path.getsize(PASSC_SAMPLE) / 1e6))
    print("  per cell: %d | cells: %d | arms: %s"
          % (per_cell, len(models), dict(collections.Counter(cols["arm"]))))
    print("  seed %d -- rerunning with the same seed reproduces this file exactly" % seed)


def passc_corpus():
    """EVERY f11_l2 passage for the 29 lineages, to parquet, split by language.

    RH: *"Can we just save all passages to a parquet in case we want to up the
    n= to 200 or more?"* -- yes, and it is a DIFFERENT object from
    `sample.parquet`:

        corpus_en.parquet / corpus_zh.parquet   the frame. everything there is.
        sample.parquet                          the declared draw, seeded,
                                                714/cell, what we committed to
                                                code.

    Keeping them apart matters. Raising n means taking more ids from the frame
    under the same seeded order, which is auditable; it must never mean redrawing
    a sample that happens to be bigger.

    **It lives in `$MALIGNMENT_DATA` (default `~/malignment-data`), NOT in the
    repo.** Same convention as `ingest.py` and `vectors.py`; the README lists it
    as the private rsync target. A manifest with the row count and the sha256
    IS committed, so the repo records exactly which bytes the sample was drawn
    from without carrying them.

    Language is a column, not a file. Stage 1 is English on 29 pairs, stage 2 is
    Chinese on the 8 `cjk_tier` FLUENT pairs, and a column splits that cleanly.
    """
    import subprocess, collections, hashlib
    import pyarrow as pa, pyarrow.parquet as pq
    from malignment import roster
    DATA = os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data"))
    out_dir = os.path.join(DATA, "f11_l2")
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(PASSC, exist_ok=True)
    have = set(subprocess.run(["clickhouse", "client", "--query",
        "SELECT DISTINCT model FROM malign_logits.gen_sequences WHERE corpus='f11_l2' "
        "FORMAT TabSeparated"], capture_output=True, text=True, timeout=600).stdout.split())
    pairs = []
    for base, arms in roster.lineages().items():
        if base not in have:
            continue
        al = [m for m in arms if m != base and m in have]
        if len(al) == 1:
            pairs.append((base, al[0]))
    pairs.sort()
    arm = {}
    for b, a in pairs:
        arm[b] = "base"; arm[a] = "aligned"
    base_of = {m: b for b, a in pairs for m in (b, a)}
    CJK = _re.compile(r"[\u4e00-\u9fff]")
    q = ("SELECT model, prompt, sample_idx, text FROM malign_logits.gen_sequences "
         "WHERE corpus='f11_l2' AND model IN (%s) FORMAT JSONEachRow"
         % ",".join(sql_str(m) for m in arm))
    res = subprocess.run(["clickhouse", "client", "--query", q],
                         capture_output=True, text=True, timeout=3600)
    rows = []
    for line in res.stdout.split("\n"):
        if line.strip():
            rows.append(json.loads(line))
    rows.sort(key=lambda r: (r["model"], r["prompt"], r["sample_idx"]))
    cols = collections.defaultdict(list)
    for j, r in enumerate(rows):
        lang = "zh" if CJK.search(r["prompt"]) else "en"
        cols["id"].append("f%06d" % j)
        cols["model"].append(r["model"]); cols["arm"].append(arm[r["model"]])
        cols["pair"].append(base_of[r["model"]]); cols["language"].append(lang)
        cols["prompt"].append(r["prompt"]); cols["sample_idx"].append(int(r["sample_idx"]))
        cols["text"].append(r["text"])
    t = pa.table({k: pa.array(v) for k, v in cols.items()})
    p = os.path.join(out_dir, "f11_l2_full.parquet")
    pq.write_table(t, p, compression="zstd", compression_level=19)
    h = hashlib.sha256(open(p, "rb").read()).hexdigest()
    mb = os.path.getsize(p) / 1e6
    print("29 lineages, %d models, %s passages" % (len(arm), format(len(rows), ",")))
    print("  language: %s" % dict(collections.Counter(cols["language"])))
    print("  -> %s  (%.1f MB)" % (p, mb))
    print("     sha256 %s" % h)
    man = {"path": p, "rows": len(rows), "sha256": h, "bytes": os.path.getsize(p),
           "columns": list(cols), "pairs": len(pairs), "models": len(arm),
           "language": dict(collections.Counter(cols["language"])),
           "source": "malign_logits.gen_sequences WHERE corpus='f11_l2'",
           "population": "every lineage with base AND exactly one aligned arm present",
           "rebuild": "python run.py --passc-corpus",
           "note": ("Lives OUTSIDE the repo in $MALIGNMENT_DATA. This manifest is "
                    "committed so the repo records which bytes sample.parquet was "
                    "drawn from. Raising n means taking more ids from the frozen "
                    "sample under its seeded order, never redrawing from here.")}
    mp = os.path.join(PASSC, "corpus_manifest.json")
    json.dump(man, open(mp, "w", encoding="utf-8"), indent=1, sort_keys=True)
    print("  manifest -> %s" % mp)


SHARD_TEMPLATE = '''export const meta = {
  name: 'passc-shard-%(shard)02d',
  description: 'Pass C shard %(shard)d of %(nshards)d: two blind coders over %(n)d passages',
  phases: [{ title: 'Code', detail: '2 coders x %(nbatch)d batches, Opus high effort' }],
}

const RUBRIC = %(rubric)s

//: [{file, ids}] -- one small file per batch, ~45 passages and ~30 KB each.
//: NOT one big file (the pass is 33 MB and no agent can read that to find its
//: 45 ids) and NOT inline in this script (the runtime rejects a script over
//: 524,288 bytes, and inlining made these 3.4 MB).
const BATCHES = %(batches)s
const IDS = BATCHES.flatMap(b => b.ids)

const SCHEMA = {
  type: 'object',
  properties: {
    codings: { type: 'array', items: { type: 'object', properties: {
      id:        { type: 'string' },
      narrative: { type: 'boolean' },
      mode:      { type: 'string', enum: ['NONE', 'TOLD', 'SHOWN'] },
      drift:     { type: 'string', enum: ['HOLDS', 'SHIFTS', 'UNMOORED'] },
      degree:    { type: 'integer', minimum: 0, maximum: 3 },
      span:      { type: 'string' },
    }, required: ['id','narrative','mode','drift','degree','span'],
       additionalProperties: false } },
  },
  required: ['codings'], additionalProperties: false,
}

log(`shard %(shard)d: ${IDS.length} passages, ${BATCHES.length} batches, two coders`)

phase('Code')
const jobs = []
for (const coder of ['A', 'B']) {
  BATCHES.forEach((b, bi) => {
    jobs.push(() => agent(
      RUBRIC
        + `\\n\\n## The passages\\n\\nRead ${b.file}. It is a JSON object keyed by passage id; each entry has \\`f\\` (the fragment the model was given) and \\`c\\` (what it wrote). Code EVERY passage in that file -- all ${b.ids.length} of them -- and return every one, keyed by its id. Return nothing else.`,
      { label: `s%(shard)02d:${coder}:b${bi}`, phase: 'Code', schema: SCHEMA, effort: 'high' }
    ).then(r => ({ coder, rows: (r && r.codings) || [] })))
  })
}
const done = (await parallel(jobs)).filter(Boolean)

const asked = new Set(IDS)
const out = { A: {}, B: {} }
let stray = 0
for (const d of done) for (const r of d.rows) {
  if (!asked.has(r.id)) { stray++; continue }   // never accept an id we did not ask for
  out[d.coder][r.id] = { narrative: r.narrative, mode: r.mode, drift: r.drift,
                         degree: r.degree, span: r.span }
}
const missA = IDS.filter(i => !(i in out.A)), missB = IDS.filter(i => !(i in out.B))
if (missA.length || missB.length || stray) log(`INCOMPLETE: A missing ${missA.length}, B missing ${missB.length}, stray ${stray}`)
const both = IDS.filter(i => i in out.A && i in out.B)
log(`shard %(shard)d done: both=${both.length}/${IDS.length}`)
return { _shard: %(shard)d, _requested: IDS.length, _stray: stray,
         _missing_A: missA, _missing_B: missB, A: out.A, B: out.B }
'''


def _passc_coded():
    """Ids coded by BOTH coders, across every saved shard."""
    import collections
    got = collections.defaultdict(set)
    #: `rejected/` counts as HANDLED, not as missing. Codings are parked there
    #: deliberately (L00's Sonnet run: kappa 0.628 on mode, cannot be pooled with
    #: Opus-coded pairs). Without this, `--passc-recover --write` rebuilds them
    #: from the journal straight back into codings/ and silently undoes the
    #: exclusion -- a recovery tool reversing a decision.
    for sub in ("codings", "rejected"):
        d = os.path.join(PASSC, sub)
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if f.endswith(".json") and f != "README.json":
                r = json.load(open(os.path.join(d, f), encoding="utf-8"))
                for c in ("A", "B"):
                    got[c].update(r.get(c, {}))
    #: ANY coder, not both: lineage shards are single-coded by design.
    return (got["A"] | got["B"]) if got else set()


def passc_shards(nshards=6, per_cell=535, batch=45):
    """Generate N disjoint workflow scripts over the ids still to code.

    Shards exist so a killed session loses ONE shard, not the run. They are
    separate top-level Workflow invocations because the concurrency cap is
    min(16, cores-2) PER WORKFLOW -- 10 on this machine -- so six shards give
    60 concurrent agents rather than 10. The cap is set by local cores and the
    work is API calls, which is why it is worth routing around.

    `per_cell` is how many of the frozen 714 to code in this pass; 535 is the
    n=150 target. Ids are taken in the sample's own order, which is
    (model, prompt, sample_idx), so "the first 535" is deterministic and raising
    it later ADDS ids without disturbing any already coded.

    **Shards are cut by LINEAGE, not by row.** A shard that dies then leaves a
    nameable gap -- these pairs are uncoded -- rather than a random hole.
    """
    import collections
    import pyarrow.parquet as pq
    t = pq.read_table(PASSC_SAMPLE).to_pydict()
    bycell = collections.defaultdict(list)
    for i, m in zip(t["id"], t["model"]):
        bycell[m].append(i)
    want = []
    for m in sorted(bycell):
        want.extend(bycell[m][:per_cell])
    done = _passc_coded()
    todo = [i for i in want if i not in done]
    print("frozen sample %s | this pass wants %s (%d/cell) | coded %s | TODO %s"
          % (format(len(t["id"]), ","), format(len(want), ","), per_cell,
             format(len(done & set(want)), ","), format(len(todo), ",")))
    if not todo:
        print("nothing to do")
        return
    pair_of = dict(zip(t["id"], t["pair"]))
    bypair = collections.defaultdict(list)
    for i in todo:
        bypair[pair_of[i]].append(i)
    buckets = [[] for _ in range(nshards)]
    for p in sorted(bypair, key=lambda p: -len(bypair[p])):
        buckets.sort(key=len)
        buckets[0].extend(bypair[p])
    todoset = set(todo)
    pas = {i: {"f": p, "c": x}
           for i, p, x in zip(t["id"], t["prompt"], t["text"]) if i in todoset}
    os.makedirs(os.path.join(PASSC, "scripts"), exist_ok=True)
    bdir = os.path.join(PASSC, "batches")
    os.makedirs(bdir, exist_ok=True)
    plan = {}
    nb = 0
    for k, ids in enumerate(buckets):
        ids = sorted(ids)
        bl = []
        for s0 in range(0, len(ids), batch):
            chunk = ids[s0:s0 + batch]
            bf = os.path.join(bdir, "s%02d-b%03d.json" % (k, s0 // batch))
            json.dump({i: pas[i] for i in chunk}, open(bf, "w", encoding="utf-8"),
                      ensure_ascii=False)
            bl.append({"file": bf, "ids": chunk})
            nb += 1
        src = SHARD_TEMPLATE % {
            "shard": k, "nshards": nshards, "n": len(ids), "batch": batch,
            "nbatch": len(bl),
            "rubric": json.dumps(rubric_text()),
            "batches": json.dumps(bl)}
        f = os.path.join(PASSC, "scripts", "shard-%02d.js" % k)
        open(f, "w", encoding="utf-8").write(src)
        plan[k] = {"script": f, "n": len(ids), "pairs": sorted({pair_of[i] for i in ids})}
        print("  shard %02d  %5d passages  %2d pairs  -> %s"
              % (k, len(ids), len(plan[k]["pairs"]), os.path.basename(f)))
    json.dump(plan, open(os.path.join(PASSC, "plan.json"), "w", encoding="utf-8"),
              indent=1, sort_keys=True)
    tot = sum(len(b) for b in buckets)
    nag = 2 * sum((len(b) + batch - 1) // batch for b in buckets)
    print("\n  %s passages x 2 coders = %s codings | %d agents at %d/batch"
          % (format(tot, ","), format(2 * tot, ","), nag, batch))
    print("  cover check: union of shards == TODO: %s"
          % (sorted(i for b in buckets for i in b) == sorted(todo)))
    print("  disjoint: %s" % (len({i for b in buckets for i in b}) == tot))


def passc_save(src):
    """Persist one shard's result, and CHECK COMPLETENESS HERE.

    The lineage scripts carry batch FILE PATHS and no id lists -- that is what
    took them from 12,708 characters to ~2,600, small enough for the workflow
    approval dialog to display. The consequence is that the script can no longer
    compute `_missing`, so the check moves to save time, where it belongs
    anyway: the ids are the batch files' own keys, so this compares what came
    back against what was actually sent rather than against a list the same
    script wrote.
    """
    raw = json.load(open(src, encoding="utf-8"))
    r = raw.get("result", raw)
    if isinstance(r, str):
        r = json.loads(r)
    k = r.get("_shard")
    if k is None:
        raise RuntimeError("no _shard in %s -- is this a Pass C shard output?" % src)
    os.makedirs(os.path.join(PASSC, "codings"), exist_ok=True)
    p = os.path.join(PASSC, "codings", "shard-%02d.json" % k)
    if os.path.exists(p):
        raise RuntimeError("%s exists; refusing to overwrite a saved shard" % p)

    asked = set()
    for f in (r.get("_files") or []):
        if os.path.exists(f):
            asked.update(json.load(open(f, encoding="utf-8")))
    got = set(r.get("A", {})) | set(r.get("B", {}))
    missing, stray = sorted(asked - got), sorted(got - asked)
    if asked:
        r["_requested"] = len(asked)
        r["_missing"] = missing
        r["_stray"] = stray
    json.dump(r, open(p, "w", encoding="utf-8"), indent=0, sort_keys=True,
              ensure_ascii=False)
    print("shard %02d %s: A=%d B=%d"
          % (k, r.get("_pair", "").split("/")[-1], len(r.get("A", {})), len(r.get("B", {}))))
    if asked:
        print("  sent %d | missing %d | stray %d%s"
              % (len(asked), len(missing), len(stray),
                 ("   e.g. %s" % missing[:3]) if missing else ""))
        if stray:
            print("  *** %d ids returned that were NEVER SENT: %s" % (len(stray), stray[:3]))
    else:
        print("  no _files in the result -- completeness NOT checked")
    print("  -> %s" % p)


def _norm(s):
    """Normalise before declaring a span absent.

    On the test shard 7 of 152 spans failed a literal `in` check and SIX were
    smart quotes, `&amp;` or collapsed whitespace. Reporting those as
    fabrications gives a 4.6% rate where the truth is 0.7%.
    """
    import unicodedata
    s = unicodedata.normalize("NFKC", s)
    for a, b in (("’", "'"), ("‘", "'"), ("“", '"'),
                 ("”", '"'), ("&amp;", "&"), ("&quot;", '"'), ("&#39;", "'")):
        s = s.replace(a, b)
    return _re.sub(r"\s+", " ", s).strip()


def passc_report():
    """Pass C. Wilcoxon on per-pair rate differences; the pair is the unit.

    NOT a sign test. The statistic is a rate difference measured identically in
    every pair, so magnitudes are comparable and discarding them is pure power
    loss. RH: *"why do you keep proposing sign tests and throwing away
    magnitude."* The sign test is reported beside it as a distribution-free
    check, never as the headline.

    PRIMARY is PRESENCE (mode != NONE): the direct form of the scene-kind claim
    and the best powered. At n=150/cell with sigma_het=3pp its Wilcoxon MDE is
    ~3.4pp on a 64% base, against ~4.4pp for the SHOWN-share statistic on a 30%
    base. Told/shown is the refinement that makes a finding interesting, not the
    thing that establishes it.

    sigma_het is estimated by method of moments: Var(observed per-pair deltas)
    minus the mean binomial sampling variance. It is the parameter that decides
    whether raising n buys anything, because n shrinks the sampling half and
    does nothing at all to the other.
    """
    import collections, math, csv, glob, statistics as st
    import pyarrow.parquet as pq
    from scipy import stats
    #: BOTH draws, so lineage-shard codings (f######) resolve as well as the
    #: sample-draw ones (p######). Reports which draw the passages came from,
    #: because the two are alternative populations and pooling needs saying.
    K = passc_key()
    A, B = {}, {}
    for f in sorted(glob.glob(os.path.join(PASSC, "codings", "*.json"))):
        r = json.load(open(f, encoding="utf-8"))
        A.update(r.get("A", {})); B.update(r.get("B", {}))
    ids = sorted(i for i in A if i in B and i in K)
    if not ids:
        print("no codings yet")
        return
    print("PASS C -- %s passages coded by both, %d lineages, %d models\n"
          % (format(len(ids), ","), len({K[i]["pair"] for i in ids}),
             len({K[i]["model"] for i in ids})))

    print("=== AGREEMENT ===")

    def kap(get, lv):
        o = sum(1 for i in ids if get(A[i]) == get(B[i])) / len(ids)
        e = sum((sum(1 for i in ids if get(A[i]) == v) / len(ids)) *
                (sum(1 for i in ids if get(B[i]) == v) / len(ids)) for v in lv)
        return o, ((o - e) / (1 - e) if e < 1 else float("nan"))
    for lbl, get, lv in (
            ("narrative", lambda d: d["narrative"], (True, False)),
            ("mode", lambda d: d["mode"], ("NONE", "TOLD", "SHOWN")),
            ("  presence", lambda d: d["mode"] != "NONE", (True, False)),
            ("drift", lambda d: d["drift"], ("HOLDS", "SHIFTS", "UNMOORED")),
            ("degree", lambda d: d["degree"], (0, 1, 2, 3))):
        o, k = kap(get, lv)
        print("  %-12s raw %5.1f%%  kappa %.3f" % (lbl, 100 * o, k))
    sub = [i for i in ids if A[i]["mode"] != "NONE" and B[i]["mode"] != "NONE"]
    if sub:
        o = sum(1 for i in sub if A[i]["mode"] == B[i]["mode"]) / len(sub)
        p = sum(1 for i in sub for M in (A, B) if M[i]["mode"] == "SHOWN") / (2 * len(sub))
        e = p * p + (1 - p) ** 2
        print("  %-12s raw %5.1f%%  kappa %.3f   (n=%s, TOLD vs SHOWN only)"
              % ("  told/shown", 100 * o, (o - e) / (1 - e), format(len(sub), ",")))

    print("\n=== SPANS ===")
    tot = lit = nrm = absent = 0
    for i in ids:
        for M in (A, B):
            s = M[i]["span"]
            if not s:
                continue
            tot += 1
            if s in K[i]["text"]:
                lit += 1
            elif _norm(s) in _norm(K[i]["text"]):
                nrm += 1
            else:
                absent += 1
    if tot:
        print("  %s spans | literal %.1f%% | recovered by normalising %.1f%% | ABSENT %.2f%%"
              % (format(tot, ","), 100 * lit / tot, 100 * nrm / tot, 100 * absent / tot))

    print("\n=== NARRATIVE YIELD (the filter) ===")
    keep = [i for i in ids if A[i]["narrative"] and B[i]["narrative"]]
    print("  both coders say narrative: %s of %s (%.1f%%)   [assumption was 28%%]"
          % (format(len(keep), ","), format(len(ids), ","), 100 * len(keep) / len(ids)))
    for arm in ("base", "aligned"):
        s2 = [i for i in ids if K[i]["arm"] == arm]
        if s2:
            print("    %-8s %.1f%%" % (arm, 100 * sum(
                1 for i in s2 if A[i]["narrative"] and B[i]["narrative"]) / len(s2)))
    if not keep:
        return
    print("\n  everything below is ON THE NARRATIVE SUBSET ONLY.")

    def rates(sel, f):
        by = collections.defaultdict(lambda: collections.defaultdict(list))
        for i in sel:
            by[K[i]["pair"]][K[i]["arm"]].append(i)
        out = {}
        for p, v in by.items():
            if v["base"] and v["aligned"]:
                out[p] = (sum(1 for i in v["base"] for M in (A, B) if f(M[i])) / (2 * len(v["base"])),
                          sum(1 for i in v["aligned"] for M in (A, B) if f(M[i])) / (2 * len(v["aligned"])),
                          len(v["base"]), len(v["aligned"]))
        return out

    def test(lbl, f, primary=False):
        R = rates(keep, f)
        if len(R) < 3:
            print("  %-26s only %d pairs -- not testable" % (lbl, len(R)))
            return
        d = [a - b for b, a, _, _ in R.values()]
        samp = st.mean(b * (1 - b) / (2 * nb) + a * (1 - a) / (2 * na)
                       for b, a, nb, na in R.values())
        het = max(0.0, st.pvariance(d) - samp) ** 0.5
        try:
            w = stats.wilcoxon(d).pvalue
        except ValueError:
            w = float("nan")
        up = sum(1 for x in d if x > 0); dn = sum(1 for x in d if x < 0)
        sg = stats.binomtest(up, up + dn).pvalue if up + dn else float("nan")
        z = 2.8016 / math.sqrt(len(R)) / math.sqrt(3 / math.pi)
        print("  %-26s%s" % (lbl, "   <-- PRIMARY" if primary else ""))
        print("      %d pairs | base %.1f%% aligned %.1f%% | median delta %+.2fpp"
              % (len(R), 100 * st.mean(b for b, a, _, _ in R.values()),
                 100 * st.mean(a for b, a, _, _ in R.values()), 100 * st.median(d)))
        print("      Wilcoxon p=%.4f | sign %d up %d down p=%.4f" % (w, up, dn, sg))
        print("      sigma_het %.2fpp (sampling %.2fpp) | MDE at this n and spread %.2fpp"
              % (100 * het, 100 * samp ** 0.5, 100 * z * st.pstdev(d)))

    print("\n=== THE ARM TEST, per lineage pair ===")
    test("presence  mode != NONE", lambda d: d["mode"] != "NONE", primary=True)
    test("SHOWN, of all", lambda d: d["mode"] == "SHOWN")
    test("TOLD, of all", lambda d: d["mode"] == "TOLD")
    test("drift HOLDS", lambda d: d["drift"] == "HOLDS")

    print("\n=== F13's TRADE-OFF: mode x drift ===")
    print("  %-10s %8s %8s %8s %8s" % ("drift", "n", "NONE", "TOLD", "SHOWN"))
    for lv in ("HOLDS", "SHIFTS", "UNMOORED"):
        s2 = [i for i in keep if A[i]["drift"] == lv == B[i]["drift"]]
        if not s2:
            continue
        c = collections.Counter(M[i]["mode"] for i in s2 for M in (A, B))
        n = sum(c.values())
        print("  %-10s %8s %7.1f%% %7.1f%% %7.1f%%"
              % (lv, format(len(s2), ","), 100 * c["NONE"] / n,
                 100 * c["TOLD"] / n, 100 * c["SHOWN"] / n))

    print("\n=== STRATA (presence rate, base -> aligned) ===")
    kind = {}
    for r in csv.DictReader(open(os.path.join(RESULTS, "prompt_kind.csv"), encoding="utf-8")):
        if r["unanimous"] == "1":
            kind[r["prompt"]] = r["kind"]
    stage = {}
    try:
        from malignment import roster
        for base, arms in roster.lineages().items():
            for m in arms:
                if m != base:
                    stage[base] = ("DPO" if m.upper().endswith("DPO") else
                                   "zephyr" if "zephyr" in m else "Instruct")
    except Exception:
        pass
    for lbl, keyf in (("prompt kind", lambda i: kind.get(K[i]["prompt"], "?")),
                      ("alignment stage", lambda i: stage.get(K[i]["pair"], "?"))):
        print("  %s:" % lbl)
        for g in sorted({keyf(i) for i in keep}):
            sel = [i for i in keep if keyf(i) == g]
            R = rates(sel, lambda d: d["mode"] != "NONE")
            if not R:
                continue
            d = [a - b for b, a, _, _ in R.values()]
            print("    %-12s %2d pairs %8s passages   %.1f%% -> %.1f%%  (%+.2fpp)"
                  % (g, len(R), format(len(sel), ","),
                     100 * st.mean(b for b, a, _, _ in R.values()),
                     100 * st.mean(a for b, a, _, _ in R.values()), 100 * st.mean(d)))


def filtercal(src=None):
    """Did Haiku's triage match the Opus coders' `narrative` judgement?

    **The number that decides the design is the FALSE-NEGATIVE RATE PER ARM.**
    A false positive is free -- Opus reads one extra passage and codes it out.
    A false negative silently removes a passage from the population, and base
    output is more degenerate than aligned output, so a filter that struggles
    on hard passages drops base ones more often. That would manufacture an arm
    effect in exactly the direction of the hypothesis.

    So the acceptance test is two-sided: recall high enough to keep the
    population, AND recall equal across arms. 90% overall that is 95% aligned
    against 85% base is worse than useless here.
    """
    import glob, collections, math
    import pyarrow.parquet as pq
    from scipy import stats
    P = os.path.join(PASSC, "filtercal", "haiku.json")
    if src:
        raw = json.load(open(src, encoding="utf-8"))
        r = raw.get("result", raw)
        if isinstance(r, str):
            r = json.loads(r)
        json.dump(r, open(P, "w", encoding="utf-8"), indent=0, sort_keys=True)
        print("saved %d judgements | stray %s | missing %s -> %s"
              % (len(r["narrative"]), r.get("_stray"), len(r.get("_missing", [])), P))
    H = json.load(open(P, encoding="utf-8"))["narrative"]
    t = pq.read_table(PASSC_SAMPLE).to_pydict()
    K = {i: (m, a) for i, m, a in zip(t["id"], t["model"], t["arm"])}
    A, B = {}, {}
    for f in sorted(glob.glob(os.path.join(PASSC, "codings", "*.json"))):
        r = json.load(open(f, encoding="utf-8"))
        A.update(r.get("A", {})); B.update(r.get("B", {}))
    ids = sorted(i for i in H if i in A and i in B)
    both = [i for i in ids if A[i]["narrative"] == B[i]["narrative"]]
    split = [i for i in ids if A[i]["narrative"] != B[i]["narrative"]]
    print("HAIKU TRIAGE vs THE OPUS CODERS -- %s passages\n" % format(len(ids), ","))
    print("  Opus coders agree on %s (%.1f%%), split on %d"
          % (format(len(both), ","), 100 * len(both) / len(ids), len(split)))

    def tab(sel, lbl):
        tp = sum(1 for i in sel if A[i]["narrative"] and H[i])
        fn = sum(1 for i in sel if A[i]["narrative"] and not H[i])
        fp = sum(1 for i in sel if not A[i]["narrative"] and H[i])
        tn = sum(1 for i in sel if not A[i]["narrative"] and not H[i])
        rec = tp / (tp + fn) if tp + fn else float("nan")
        pre = tp / (tp + fp) if tp + fp else float("nan")
        print("  %-26s n=%-6s narrative %-5d | RECALL %5.1f%%  precision %5.1f%%"
              % (lbl, format(len(sel), ","), tp + fn, 100 * rec, 100 * pre))
        print("      %-24s haiku keeps %s of %s (%.0f%%) -> Opus would read that many"
              % ("", format(tp + fp, ","), format(len(sel), ","),
                 100 * (tp + fp) / len(sel)))
        return tp, fn, fp, tn, rec

    print("\n=== ON THE %s WHERE BOTH OPUS CODERS AGREE ===" % format(len(both), ","))
    tp, fn, fp, tn, rec = tab(both, "overall")
    print("\n=== THE TEST THAT MATTERS: RECALL BY ARM ===")
    per = {}
    for arm in ("base", "aligned"):
        sel = [i for i in both if K[i][1] == arm]
        per[arm] = tab(sel, arm)
    rb, ra = per["base"][4], per["aligned"][4]
    nb, na = per["base"][0] + per["base"][1], per["aligned"][0] + per["aligned"][1]
    print("\n  recall base %.1f%% vs aligned %.1f%%  -> gap %+.1fpp"
          % (100 * rb, 100 * ra, 100 * (ra - rb)))
    if nb and na:
        tb = stats.fisher_exact([[per["base"][0], per["base"][1]],
                                 [per["aligned"][0], per["aligned"][1]]])[1]
        print("  Fisher exact on the 2x2 of kept/dropped by arm: p=%.4f" % tb)
        print("  %s" % ("ACCEPTABLE -- no detectable differential" if tb > 0.05
                        else "*** DIFFERENTIAL. This filter would manufacture an arm effect. ***"))

    print("\n=== BY MODEL (a cheap filter fails first where the prose is worst) ===")
    print("  %-40s %-8s %6s %8s" % ("model", "arm", "narr", "recall"))
    for m, a in sorted({K[i] for i in both}):
        sel = [i for i in both if K[i] == (m, a)]
        tp2 = sum(1 for i in sel if A[i]["narrative"] and H[i])
        fn2 = sum(1 for i in sel if A[i]["narrative"] and not H[i])
        print("  %-40s %-8s %6d %7s" % (m.split("/")[-1][:40], a, tp2 + fn2,
              ("%.1f%%" % (100 * tp2 / (tp2 + fn2))) if tp2 + fn2 else "-"))

    if split:
        k = sum(1 for i in split if H[i])
        print("\n=== THE %d WHERE THE OPUS CODERS DISAGREED ===" % len(split))
        print("  haiku says narrative on %d of %d (%.0f%%) -- these are the genuinely"
              % (k, len(split), 100 * k / len(split)))
        print("  hard ones; a filter tracking the construct should sit near 50%%.")

    print("\n=== WHAT IT WOULD COST ===")
    keep = (tp + fp) / len(both)
    rem = 27820
    print("  26 pairs remaining = %s passages" % format(rem, ","))
    print("  haiku keeps %.0f%% -> Opus codes %s (single) at ~1,430 tok = %.1fM Opus tokens"
          % (100 * keep, format(int(rem * keep), ","), rem * keep * 1430 / 1e6))
    print("  against %.1fM if Opus double-codes everything, a %.1fx saving"
          % (rem * 2 * 1430 / 1e6, (rem * 2) / (rem * keep)))
    print("  and it loses %.1f%% of the narrative population to false negatives."
          % (100 * (1 - rec)))


def passc_recover(write=False):
    """Rebuild coding files from the workflow JOURNALS in ~/.claude.

    **RH was right and I was wrong.** RESUME.md recorded that a workflow's
    return value lives only in `/private/tmp/.../tasks/*.output` and dies with
    the machine, so a completed-but-unsaved shard had to be recoded. It does
    not:

        ~/.claude/projects/<proj>/<session>/subagents/workflows/<run>/journal.jsonl

    carries one `{"type":"result", ...}` line per agent WITH ITS FULL RETURN
    VALUE. Verified against the Pass C test shard: 90 passages, both codings
    each, byte-identical to the file saved from the task output.

    Two things make recovery work despite what the journal does NOT store:

      - `started` lines carry `label=None`, so the journal cannot say which
        agent was coder A and which was B. It does not need to: both coders get
        an IDENTICAL prompt, so A and B are two independent draws of one
        procedure, not two instruments. Pairing by passage id is sufficient and
        agreement is unaffected by which of the two is called A.
      - a passage is accepted only with EXACTLY two codings. One means an agent
        died mid-shard; three would mean an id was issued twice.

    Journals are keyed by session uuid, so this scans every session directory
    for this project, not only the current one.
    """
    import glob, collections
    #: BOTH draws. Filtering against sample.parquet alone would silently drop
    #: every lineage-shard coding recovered from a journal.
    want = set(passc_key())
    root = os.path.expanduser("~/.claude/projects")
    proj = sorted(glob.glob(os.path.join(root, "*TheoryMachines*lacan*")))
    if not proj:
        print("no project directory under %s" % root)
        return
    pat = os.path.join(proj[0], "*", "subagents", "workflows", "*", "journal.jsonl")
    js = sorted(glob.glob(pat))
    have = _passc_coded()
    found = collections.defaultdict(lambda: collections.defaultdict(list))
    partial = collections.Counter()
    for j in js:
        run = os.path.basename(os.path.dirname(j))
        for line in open(j, encoding="utf-8"):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("type") != "result":
                continue
            res = r.get("result")
            if isinstance(res, str):          # older runs returned free text
                try:
                    res = json.loads(res)
                except ValueError:
                    continue
            if not isinstance(res, dict):
                continue
            #: Journals from OTHER runs live in the same directories -- the Haiku
            #: triage returned {id, narrative} only, and earlier passes had three
            #: or four fields. Take only codings carrying the full Pass C set;
            #: a partial one is a different instrument, not a damaged record.
            for c in (res.get("codings") or []):
                if not isinstance(c, dict):
                    continue
                if c.get("id") not in want:
                    continue
                if not FIELDS_C.issubset(c):
                    partial[run] += 1
                    continue
                found[run][c["id"]].append({k: c[k] for k in FIELDS_C})
    print("scanned %d journal(s) under %s" % (len(js), os.path.basename(proj[0])))
    for run, n in sorted(partial.items()):
        print("  %-20s %d codings skipped: missing %s"
              % (run, n, ", ".join(sorted(FIELDS_C))))
    if not found:
        print("  no Pass C codings in any journal")
        return
    os.makedirs(os.path.join(PASSC, "codings"), exist_ok=True)
    for run in sorted(found):
        by = found[run]
        #: ONE coding is complete for a single-coded run (every lineage shard),
        #: TWO for a double-coded one (shards 00-11). Three means an id was
        #: issued twice and is a defect. An earlier version demanded exactly
        #: two, which would have refused to recover any lineage shard -- the
        #: precise case recovery exists for.
        ok = {i: v for i, v in by.items() if len(v) in (1, 2)}
        bad = {i: len(v) for i, v in by.items() if len(v) > 2}
        single = sum(1 for v in ok.values() if len(v) == 1)
        new = sorted(set(ok) - have)
        print("  %-20s %5d ids | %5d single %5d double | %5d not already saved"
              % (run, len(by), single, len(ok) - single, len(new)))
        if bad:
            print("      *** %d ids with MORE THAN 2 codings -- issued twice: %s"
                  % (len(bad), dict(list(bad.items())[:4])))
        if not new or not write:
            continue
        p = os.path.join(PASSC, "codings", "recovered-%s.json" % run)
        if os.path.exists(p):
            print("      %s exists; skipping" % os.path.basename(p))
            continue
        json.dump({"_shard": -1, "_recovered_from": run, "_requested": len(new),
                   "_coders": 1 if single == len(new) else 2,
                   "A": {i: ok[i][0] for i in new},
                   "B": {i: ok[i][1] for i in new if len(ok[i]) == 2}},
                  open(p, "w", encoding="utf-8"), indent=0, sort_keys=True,
                  ensure_ascii=False)
        print("      -> %s" % os.path.basename(p))
    if not write:
        print("\n  DRY RUN -- add --write to save recovered codings.")


def passc_todo():
    """What is coded, what is not, PER DRAW. The resume check.

    The two draws are ALTERNATIVES, not addends -- one random within a frozen
    sample, one classifier-ranked -- so a single union denominator would imply
    we mean to code all 145,412, which we do not. The live plan is the 26
    lineage shards at top-200 per cell.
    """
    import collections
    K = passc_key()
    want = set(K)
    got = collections.defaultdict(set)
    d = os.path.join(PASSC, "codings")
    if os.path.isdir(d):
        for f in sorted(os.listdir(d)):
            if not f.endswith(".json"):
                continue
            r = json.load(open(os.path.join(d, f), encoding="utf-8"))
            for coder, m in r.items():
                if coder.startswith("_"):
                    continue
                got[coder].update(m)
            print("  %-34s %s" % (f, " ".join("%s:%d" % (c, len(m)) for c, m in sorted(r.items()) if not c.startswith("_"))))
    #: ANY coder saw it vs BOTH did. Not `intersection` over all coders: shards
    #: 00-11 are double-coded and L00-L25 single, so an intersection would
    #: report the single-coded ones as uncoded.
    coded = set().union(*got.values()) if got else set()
    double = (got.get("A", set()) & got.get("B", set()))
    stray = coded - want
    if stray:
        print("\n  *** %d CODED IDS ARE IN NEITHER DRAW *** %s"
              % (len(stray), sorted(stray)[:3]))

    lp = os.path.join(PASSC, "lineage", "plan.json")
    if os.path.exists(lp):
        print("\nLINEAGE PLAN -- the live one, 26 shards at top-200 per cell:")
        plan = json.load(open(lp, encoding="utf-8"))
        allids = set()
        for k in sorted(plan, key=int):
            #: ids come from the BATCH FILES, which are what the agents were
            #: actually handed. Previously parsed out of the script, which broke
            #: silently (0/0 on every shard) the moment the scripts were
            #: shrunk to carry paths instead of id lists.
            ids = []
            for f in plan[k].get("files", []):
                if os.path.exists(f):
                    ids.extend(json.load(open(f, encoding="utf-8")))
            allids.update(ids)
            n = len(set(ids) & coded)
            print("  L%-3s %-32s %4d/%-4d %s"
                  % (k, plan[k]["pair"].split("/")[-1][:32], n, len(ids),
                     "DONE" if ids and n == len(ids) else ""))
        left = sorted(allids - coded)
        print("  --> %s of %s coded. REMAINING %s%s"
              % (format(len(allids & coded), ","), format(len(allids), ","),
                 format(len(left), ","),
                 ("   next id %s" % left[0]) if left else ""))

    ps = {i for i in coded if K.get(i, {}).get("draw") == "sample"}
    print("\nEARLIER DRAW (sample.parquet, random within the frozen sample):")
    print("  %s passages coded, %s of them double-coded" % (format(len(ps), ","),
          format(len({i for i in double if K.get(i, {}).get('draw') == 'sample'}), ",")))
    print("  A DIFFERENT POPULATION from the lineage shards. Do not pool without")
    print("  saying so: one is random within a frozen sample, one is classifier-ranked.")


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
    ap.add_argument("--passc-sample", action="store_true")
    ap.add_argument("--passc-todo", action="store_true")
    ap.add_argument("--passc-corpus", action="store_true")
    ap.add_argument("--shards", type=int)
    ap.add_argument("--passc-save")
    ap.add_argument("--passc-recover", action="store_true")
    ap.add_argument("--passc", action="store_true")
    ap.add_argument("--filtercal", nargs="?", const="", default=None)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--batch", type=int, default=45)
    ap.add_argument("--per-cell", type=int, default=714)
    ap.add_argument("--lang", default="en")
    ap.add_argument("--per-cell-now", type=int, default=535)
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
    elif a.passc_sample:
        passc_sample(per_cell=a.per_cell, lang=a.lang)
    elif a.passc_todo:
        passc_todo()
    elif a.passc_corpus:
        passc_corpus()
    elif a.shards:
        passc_shards(nshards=a.shards, per_cell=a.per_cell_now, batch=a.batch)
    elif a.passc_save:
        passc_save(a.passc_save)
    elif a.passc_recover:
        passc_recover(write=a.write)
    elif a.passc:
        passc_report()
    elif a.filtercal is not None:
        filtercal(a.filtercal or None)
    else:
        ap.print_help()
