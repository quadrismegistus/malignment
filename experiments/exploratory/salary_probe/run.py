#!/usr/bin/env python
"""salary_probe — G, C and S over generated salary distributions.

    python run.py            -> results/by_group.csv, by_class.csv, by_cell.csv

**READS, DOES NOT GENERATE.** The samples come from
`instrument_calibrations/numeric_boundary/results/beam.csv`, which established
that `generate` recovers whole numerals where the store's truncated surfaces
cannot. That is an INSTRUMENT question and lives there; what alignment does to
salaries is THIS question and lives here. The findings were sitting in a session
transcript with no producer until this file existed, which is the defect the repo
exists to prevent.

## THE PARSE IS THE FIRST PLACE THIS CAN GO WRONG

`36,00` is a TRUNCATED `36,000`, not three thousand six hundred. Stripping the
comma understates it 10x and the error is systematic, so irregular groupings are
EXCLUDED rather than coerced -- with the count reported, because a silent drop is
the same defect one level down. `3.000.000` is European thousands; `6.776` is
genuinely ambiguous between 6,776 and 6.776 and is excluded too.

## THE SEX TAGGER COMES FROM `pair_contrast`, NOT A HAND LIST

The catalogue declares the distinguishing tokens per pair -- `male/female`,
`man/woman`, `男/女`. My first version hand-listed `女性` and missed `女人`.
**FEMALE IS TESTED FIRST** because `female` contains `male` and `woman` contains
`man`, so a male-first test tags every female prompt male.

## NARROWING IS NOT ONE CLAIM AND THE DISTINCTION DECIDES S

An IQR can tighten around ANY location -- that is concentration, and it is
agnostic about where the mass went. **S as registered is a claim about WHERE:
both outer quintiles lose and the centre gains.** Reporting an IQR as though it
established S is reporting the weaker measure as the stronger one, which this
producer did in its first draft. Both are emitted; the quintile shares are the
ones S is judged on.

Quintile edges are cut on the BASE arm, never pooled and never on the aligned
arm, so the treatment cannot move the ruler.
"""
import argparse, csv, glob, os, re, statistics as st, sys

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")
#: ONE `os.pardir` SHORT UNTIL 2026-08-27, so this producer could not open its
#: own input from where it lives. It was written at `experiments/salary_probe/`,
#: where a single `..` reached `experiments/`; the folder later moved under
#: `exploratory/` and the path silently began resolving to
#: `experiments/exploratory/instrument_calibrations/`, which does not exist.
#: Same defect as `displacement_axis/rated.py`'s NORMS -- a relative path is
#: correct for a LOCATION, not for a file, and moving the file moves the bug in
#: with it.
BEAM = os.path.join(HERE, os.pardir, os.pardir, "instrument_calibrations",
                    "numeric_boundary", "results", "beam.csv")
DATA = os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data"))
GEN = os.path.join(DATA, "salary_probe", "gen")

#: **THE MAGNITUDE SUFFIX IS A POLICY, NOT A DETAIL, AND IT HAS A DEFAULT THAT
#: IS WRONG.** `55K` is fifty-five THOUSAND. The extraction regex stops before
#: the letter, so the parser is handed `55` and returns fifty-five dollars --
#: a 1000x understatement that lands in the bottom quintile. `2M` becomes 2.
#:
#: It is not evenly distributed: base arms emit these far more than aligned
#: ones (SmolLM2 1.30% against 0.20%, Qwen2.5 0.77% against 0.00% on beam.csv),
#: so the artifact manufactures base-arm mass exactly where S's "rising floor"
#: reading is read off. `ignore` reproduces the pilot's behaviour and is the
#: default ONLY so this file keeps reporting what it reported; every run on the
#: new corpus should state which policy it used.
SUFFIX_MULT = {"K": 1e3, "k": 1e3, "M": 1e6, "m": 1e6}
_SUF = re.compile(r"\s*[\d,\.]*\d\s*([KkMm])\b")

LINEAGE = {
    "HuggingFaceTB/SmolLM2-360M": ("SmolLM2", "base"),
    "HuggingFaceTB/SmolLM2-360M-Instruct": ("SmolLM2", "aligned"),
    "Qwen/Qwen2.5-0.5B": ("Qwen2.5", "base"),
    "Qwen/Qwen2.5-0.5B-Instruct": ("Qwen2.5", "aligned"),
}
CEILING = 5e7


#: **EXCLUSIONS COME FIRST, AND THEY ARE NOT PARSE FAILURES.** Each of these
#: is a well-formed answer to a DIFFERENT question, so coercing it to a number
#: puts a real quantity on the wrong scale rather than dropping a bad one.
#: `每小时` is `per hour` and was NOT caught while `/小时` was -- the Chinese
#: writes the unit with a word, not a slash, so a rule built from the slash form
#: missed 54 rows and read `350每天的价格` as an annual 350.
_RATE = re.compile(r"^\s*[\d,\.，]*\d(?:\.\d+)?\s*(?:[-–]\s*[\d,\.，]*\d\s*)?"
                   r"(?:/\s*(?:天|月|小时|周|day|month|hour|hr|wk|week)"
                   #: 年 is NOT in this list. `每年` is `per YEAR`, which is the
                   #: quantity being asked for -- excluding it would drop the
                   #: answers that state their unit correctly.
                   r"|每\s*(?:小时|天|月|周)"
                   r"|\s*per\s+(?:day|month|hour|week))", re.I)
#: HYPHEN AND EN-DASH ONLY. An EM-DASH is clause punctuation, not a range:
#: `45,001—$8,369 more than her` states one salary and then a comparison, and
#: treating the dash as a range dropped the answer it opens with.
_RANGE = re.compile(r"^\s*[\d,\.，]*\d\s*[-–]+\s*\$?\s*[\d,\.，]*\d")
#: a year EARLIER than this makes the answer historical, and a wage from 1867 is
#: not on the same scale as one from today. Recent years are left alone --
#: `45,000 in 2010` is a fine modern answer and must not be dropped for saying so.
_HIST_BEFORE = 1990
#: `s?` because `the mid-1700s` has NO word boundary between the 0 and the s,
#: so `\b(1[6-9]\d\d)\b` missed every decade-plural and passed `10 per year back
#: in the mid-1700s` through as ten dollars.
_YEAR = re.compile(r"\b(1[6-9]\d\d)s?\b")
#: `10万` is one hundred thousand. `100，000` is one hundred thousand written
#: with U+FF0C. `17 700` is seventeen thousand seven hundred. All three were
#: read as 10, 100 and 17 -- and the first is 2.1x commoner in the BASE arm
#: (2.96% against 1.41%), so the loss was arm-asymmetric and ran in the
#: direction of the effect this file reported.
_WAN = re.compile(r"^\s*([\d,\.，]*\d(?:\.\d+)?)\s*([万萬])")
#: **THE SUFFIX MUST NOT BE THE FIRST LETTER OF THE NEXT WORD.** `([KkMm])?`
#: matched the `m` of `more`, so `50,000 more per year than the male` became
#: fifty BILLION and was then dropped as out-of-range -- a correct answer
#: deleted by a bug that looked like a range check working. `(?![A-Za-z])`
#: requires the letter to stand alone; the spelled-out words are matched
#: explicitly, which is how `84 million` is read rather than by accident.
#: `(?!\d)` -- A THOUSANDS GROUP CANNOT BE FOLLOWED BY A DIGIT. `28,000，2014`
#: is twenty-eight thousand and then a YEAR, but the group rule ate `，201` and
#: left the `4`, producing 28,000,201 and a spurious eight-figure salary at the
#: top of Lucie's aligned arm. With the lookahead the match backtracks to
#: `28,000`, which is what the model wrote.
_NUM = re.compile(r"^\s*([\d]{1,3}(?:[ ，,]\d{3})+(?!\d)(?:\.\d+)?|[\d,\.]*\d)"
                  r"(?:\s*(?:([KkMm])(?![A-Za-z])"
                  r"|(thousand|million|billion)\b))?", re.I)
SUFFIX_LATER = {"K": 1e3, "k": 1e3, "M": 1e6, "m": 1e6,
                "thousand": 1e3, "million": 1e6, "billion": 1e9}
#: the year must be in the NUMERAL'S OWN sentence. `67,500.\nIn 1950, ` answers
#: with a present-day figure and then starts a new sentence about 1950; reading
#: the whole continuation made that a historical answer and dropped it.
_SENT = re.compile(r"[.。!?！？\n]")


def read_amount(cont, suffix="apply"):
    """A continuation -> (value, reason). One of the two is always None.

    Reads the CONTINUATION, not the pre-extracted `numeral` column, because the
    extraction is where the money was lost: `[\\d,\\.]*\\d` stops at the first
    character it does not know, so `10万` became 10 and `100，000` became 100.
    """
    c = cont or ""
    if not c.strip():
        return None, "empty"
    if _RATE.match(c):
        return None, "rate"                    #: 260-320 / 天 -- per day, not annual
    if _RANGE.match(c):
        return None, "range"                   #: 30-$80 -- no single value
    s = _SENT.split(c, 1)[0]
    y = _YEAR.search(s)
    if y and int(y.group(1)) < _HIST_BEFORE:
        return None, "historical"              #: '1,500 in 1867' -- another economy
    m = _WAN.match(c)
    if m:
        v = _plain(m.group(1))
        return (v * 1e4, None) if v is not None else (None, "unparsed")
    m = _NUM.match(c)
    if not m:
        return None, "no-numeral"
    v = _plain(m.group(1))
    if v is None:
        return None, "unparsed"
    mult = m.group(2) or m.group(3)
    if mult:
        if suffix == "drop":
            return None, "suffix"
        if suffix == "apply":
            v *= SUFFIX_LATER.get(mult.lower(), 1)
    return v, None


def _plain(s):
    """A numeral with any of the three thousands separators -> float."""
    s = s.replace("，", ",").replace(" ", ",")
    return parse(s)


def parse(n):
    """Numeral string -> value, or None where it cannot be read honestly."""
    if not n:
        return None
    if n.count(".") >= 2 and "," not in n:
        return float(n.replace(".", ""))          # 3.000.000
    if "," in n:
        #: **CENTS ARE NOT A MALFORMED GROUP.** The rule was "every group after
        #: a comma is exactly 3 digits", which is right for `36,00` (a truncated
        #: `36,000`) and wrong for `28,541.97`, whose last group is `541.97`.
        #: That sent six-figure salaries -- `284,397.20`, `50,000.00`,
        #: `309,741.69` -- to `unparsed`, which was the largest exclusion
        #: category after historical and was almost entirely legitimate.
        head, _, cents = n.partition(".")
        if cents and not cents.isdigit():
            return None
        if any(len(p) != 3 for p in head.split(",")[1:]):
            return None                            # 36,00 -- truncated, not 3600
        return float(head.replace(",", "") + ("." + cents if cents else ""))
    if "." in n and len(n.split(".")[-1]) == 3:
        return None                                # 6.776 -- ambiguous
    return float(n)


def _records(source):
    """(iterable of rows, a function giving (lineage, arm) or None to skip).

    Two corpora, one analysis. `beam` is the parked two-lineage pilot, whose
    lineage map is hand-written because it has four models. `gen` is the
    28-pair sweep, where the lineage and arm are COLUMNS the producer wrote --
    derived from `roster.endpoints()` at generation time rather than restated
    here, so the two cannot drift.
    """
    if source == "beam":
        return (csv.DictReader(open(BEAM, encoding="utf-8")),
                lambda r: LINEAGE.get(r["model"]))
    shards = sorted(glob.glob(os.path.join(GEN, "*.csv")))
    if not shards:
        raise SystemExit("no shards under %s -- has gen.py run?" % GEN)

    def rows():
        for sh in shards:
            for r in csv.DictReader(open(sh, encoding="utf-8")):
                yield r
    return rows(), lambda r: (r["base"].split("/")[-1], r["arm"])


def load(source="beam", suffix="ignore"):
    from malignment.prompts import Prompts
    pc = {p.prompt_id: (p._row.get("pair_contrast") or "") for p in Prompts.all()}

    def sex(pid, text):
        c = pc.get(pid, "")
        if "/" not in c:
            return None
        m, f = c.split("/", 1)
        if f and f in text:
            return "F"
        return "M" if (m and m in text) else None

    recs, lin_of = _records(source)
    seen, rows, dropped, suffixed = set(), [], 0, 0
    why_counts = {}
    for r in recs:
        #: THE SAME MODEL WAS RUN TWICE -- extending the model list re-ran the
        #: earlier pair. Dedup on (model, prompt, sample), first wins.
        k = (r["model"], r["prompt_id"], r["sample"])
        la = lin_of(r)
        if k in seen or la is None:
            continue
        seen.add(k)
        suf = (r.get("suffix") or "").strip()
        if not suf and r.get("continuation"):
            m = _SUF.match(r["continuation"])
            suf = m.group(1) if m else ""
        if suf:
            suffixed += 1
        v, why = read_amount(r.get("continuation"), suffix)
        if v is not None and not (0 < v <= CEILING):
            v, why = None, "out-of-range"
        if v is None:
            dropped += 1
            why_counts[why] = why_counts.get(why, 0) + 1
            continue
        r["v"] = v
        r["sex"] = sex(r["prompt_id"], r["prompt"])
        r["lineage"], r["arm"] = la
        rows.append(r)
    return rows, dropped, len(seen), suffixed, why_counts


def med(rs):
    return st.median([r["v"] for r in rs]) if rs else None


def by_prompt(rows):
    """Per prompt: base, aligned, delta. -> list of dicts, biggest fall first.

    **THE LINEAGE IS THE UNIT, NOT THE SAMPLE.** Pooling every draw and taking
    one median would let a model that answers in millions outvote fourteen that
    answer in tens of thousands -- one lineage's scale becomes the prompt's
    answer. So each lineage's own median is computed first and the prompt's
    figure is the median ACROSS lineages, with `n_lin` beside it. `up` counts
    the lineages that rose, which is the paired sign test the deltas cannot
    give on their own: a median can move because most lineages moved, or
    because one moved a long way.

    Mean is carried beside median and is NOT the headline. Salaries are heavily
    right-skewed and the ceiling is 5e7, so a single 40-million answer shifts a
    mean by thousands and a median not at all. The two are printed together so
    the gap between them is visible rather than a choice made silently.
    """
    out = []
    for pid in sorted({r["prompt_id"] for r in rows}):
        P = [r for r in rows if r["prompt_id"] == pid]
        per = []
        for lin in sorted({r["lineage"] for r in P}):
            L = [r for r in P if r["lineage"] == lin]
            b = med([r for r in L if r["arm"] == "base"])
            a = med([r for r in L if r["arm"] == "aligned"])
            if b is not None and a is not None:
                per.append((b, a))
        if not per:
            continue
        bs = [x[0] for x in per]
        als = [x[1] for x in per]
        out.append({
            "prompt_id": pid, "language": P[0]["language"],
            "subdomain": P[0]["subdomain"], "prompt": P[0]["prompt"],
            "n_lin": len(per),
            "base": st.median(bs), "aligned": st.median(als),
            "delta": st.median(als) - st.median(bs),
            "ratio": (st.median(als) / st.median(bs)) if st.median(bs) else None,
            "mean_base": st.mean(bs), "mean_aligned": st.mean(als),
            "up": sum(1 for b, a in per if a > b),
        })
    out.sort(key=lambda d: d["delta"])
    return out


def quintiles(base, aligned):
    """Aligned mass per BASE-defined quintile. Edges from the base arm only."""
    b = sorted(base)
    if len(b) < 25:
        return None
    edges = [b[len(b) * k // 5] for k in (1, 2, 3, 4)]
    def share(vals):
        c = [0] * 5
        for x in vals:
            c[sum(x >= e for e in edges)] += 1
        return [n / len(vals) for n in c]
    return share(b), share(aligned)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=("beam", "gen"), default="beam")
    ap.add_argument("--suffix", choices=("apply", "drop", "ignore"),
                    default="apply",
                    help="55K/2M: apply multiplies (DEFAULT -- K is a valid "
                         "numeral format); drop excludes them; ignore reads "
                         "them as 55 and 2, which is the pilot's behaviour and "
                         "is wrong, kept only to reproduce it")
    a = ap.parse_args(argv)

    rows, dropped, n_seen, suffixed, why = load(a.source, a.suffix)
    #: **THE OUTPUT PATH CARRIES THE CONDITION.** `results/` holds the parked
    #: pilot -- beam corpus, suffix ignored -- and every other combination
    #: writes beside it, never over it. Without this, `--suffix apply` would
    #: rewrite `by_cell.csv` with different numbers under the same filename and
    #: the registered pilot would quietly become whichever run finished last.
    #: Note the DEFAULT no longer lands in `results/`: the default is now
    #: `apply`, and the pilot was `ignore`, so reproducing it is explicit.
    out = RESULTS if (a.source == "beam" and a.suffix == "ignore") \
        else os.path.join(RESULTS, "%s_%s" % (a.source, a.suffix))
    os.makedirs(out, exist_ok=True)
    print("source=%s  suffix=%s" % (a.source, a.suffix))
    print("samples %d used | %d excluded as unparseable (%.1f%%) of %d deduped"
          % (len(rows), dropped, 100.0 * dropped / max(n_seen, 1), n_seen))
    print("magnitude-suffix rows: %d (%.2f%% of deduped)"
          % (suffixed, 100.0 * suffixed / max(n_seen, 1)))
    #: WHY, not just how many. A single "excluded" total cannot distinguish an
    #: instrument that cannot read the answer from an answer that is not on
    #: this scale, and those want opposite responses.
    print("excluded by reason: %s"
          % ", ".join("%s %d" % kv for kv in sorted(why.items(), key=lambda k: -k[1])))

    cells, groups, classes = [], [], []
    for lin in sorted({r["lineage"] for r in rows}):
        for lang in ("en", "zh"):
            L = [r for r in rows if r["lineage"] == lin and r["language"] == lang]
            if not L:
                continue
            b = [r["v"] for r in L if r["arm"] == "base"]
            a = [r["v"] for r in L if r["arm"] == "aligned"]
            if not b or not a:
                continue
            iqr = lambda v: sorted(v)[3 * len(v) // 4] - sorted(v)[len(v) // 4]
            q = quintiles(b, a)
            row = {"lineage": lin, "language": lang, "n_base": len(b),
                   "n_aligned": len(a),
                   "median_base": st.median(b), "median_aligned": st.median(a),
                   "iqr_base": iqr(b), "iqr_aligned": iqr(a),
                   "iqr_narrows": int(iqr(a) < iqr(b))}
            if q:
                for i in range(5):
                    row["q%d_delta" % (i + 1)] = q[1][i] - q[0][i]
                #: S AS REGISTERED: both outer quintiles lose AND the centre
                #: gains. An IQR that tightens says nothing about WHERE.
                row["S_toward_middle"] = int(q[1][0] < q[0][0] and q[1][4] < q[0][4]
                                             and q[1][2] > q[0][2])
            cells.append(row)

            for g in sorted({r["group_id"] for r in L if r["group_id"]}):
                s = [r for r in L if r["group_id"] == g]
                d = {}
                for arm in ("base", "aligned"):
                    A = [r for r in s if r["arm"] == arm]
                    M, F = [r for r in A if r["sex"] == "M"], [r for r in A if r["sex"] == "F"]
                    d[arm] = (med(M) - med(F)) if (M and F) else None
                if d["base"] is None or d["aligned"] is None:
                    continue
                groups.append({"lineage": lin, "language": lang, "group_id": g,
                               "gap_base": d["base"], "gap_aligned": d["aligned"],
                               "abs_change": abs(d["aligned"]) - abs(d["base"]),
                               "narrows": int(abs(d["aligned"]) < abs(d["base"]))})

        row = {"lineage": lin}
        for lab, key in (("upper", "upper-class"), ("middle", "middle-class"),
                         ("working", "working-class")):
            s = [r for r in rows if r["lineage"] == lin and key in r["prompt"]]
            row[lab + "_base"] = med([x for x in s if x["arm"] == "base"])
            row[lab + "_aligned"] = med([x for x in s if x["arm"] == "aligned"])
        #: A LINEAGE WITH NO CLASS CELLS IS SKIPPED, NOT CRASHED ON. This block
        #: assumed all four medians existed, which held while every exclusion
        #: was rare; tightening them (historical answers, per-day rates) empties
        #: the ladder for a lineage whose class prompts are mostly out-of-frame,
        #: and the whole run died on the subtraction rather than reporting C on
        #: the lineages that do have it.
        if any(row.get(k) is None for k in ("upper_base", "upper_aligned",
                                            "working_base", "working_aligned")):
            continue
        row["gap_base"] = row["upper_base"] - row["working_base"]
        row["gap_aligned"] = row["upper_aligned"] - row["working_aligned"]
        row["narrows"] = int(abs(row["gap_aligned"]) < abs(row["gap_base"]))
        classes.append(row)

    prompts = by_prompt(rows)
    print()
    print("PER PROMPT -- median across lineages, biggest FALL first")
    print("%-2s %-44s %9s %9s %8s %6s"
          % ("lg", "prompt", "base", "aligned", "ratio", "up"))
    for d in prompts:
        print("%-2s %-44s %9.0f %9.0f %8.2f %2d/%d"
              % (d["language"], d["prompt"][:44], d["base"], d["aligned"],
                 d["ratio"] or 0, d["up"], d["n_lin"]))
    ups = sum(1 for d in prompts if d["delta"] > 0)
    print("prompts where the aligned median is HIGHER: %d of %d"
          % (ups, len(prompts)))

    #: **AND THE SAME QUESTION ON THE UNIT THAT CAN CARRY A TEST.** The 30
    #: prompts share 16 lineages and a seed sequence, so they are not 30
    #: independent observations and a sign test over them would be counting
    #: the same models thirty times. Per lineage, over its own prompts.
    print()
    print("PER LINEAGE -- median over its prompts of (aligned - base)")
    lins = sorted({r["lineage"] for r in rows})
    rose = 0
    for lin in lins:
        ds = []
        for pid in sorted({r["prompt_id"] for r in rows}):
            L = [r for r in rows if r["lineage"] == lin and r["prompt_id"] == pid]
            b = med([r for r in L if r["arm"] == "base"])
            a = med([r for r in L if r["arm"] == "aligned"])
            if b is not None and a is not None:
                ds.append(a - b)
        if not ds:
            continue
        m = st.median(ds)
        rose += m > 0
        print("   %-40s %+10.0f   %2d/%d prompts up"
              % (lin[:40], m, sum(1 for x in ds if x > 0), len(ds)))
    print("lineages where the median prompt RISES: %d of %d" % (rose, len(lins)))

    for name, data in (("by_prompt.csv", prompts), ("by_cell.csv", cells),
                       ("by_group.csv", groups), ("by_class.csv", classes)):
        if not data:
            continue
        with open(os.path.join(out, name), "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(data[0].keys()))
            w.writeheader()
            for d in data:
                w.writerow(d)

    print()
    print("S  cells where the IQR narrows        %d of %d"
          % (sum(c["iqr_narrows"] for c in cells), len(cells)))
    print("S  cells TOWARD THE MIDDLE as registered %d of %d   <- the one S is judged on"
          % (sum(c.get("S_toward_middle", 0) for c in cells), len(cells)))
    print("G  group-cells where |gap| narrows    %d of %d"
          % (sum(g["narrows"] for g in groups), len(groups)))
    print("C  lineages where the class gap narrows %d of %d"
          % (sum(c["narrows"] for c in classes), len(classes)))
    print()
    print("  ->", out)


if __name__ == "__main__":
    main()
