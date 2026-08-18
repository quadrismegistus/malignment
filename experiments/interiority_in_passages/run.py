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
    else:
        ap.print_help()
