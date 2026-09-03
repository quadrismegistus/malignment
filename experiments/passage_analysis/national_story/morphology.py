"""Run a live-brainstormed function inventory over GPT stories. -> per-function rates.

    python morphology.py --smoke                    3 stories, check it works
    python morphology.py --n 40                     Rettberg's corpus (gpt-4o-mini)
    python morphology.py --n 40 --corpus ours       our own aligned stories
    python morphology.py --n 40 --arms              ours, base vs aligned
    python morphology.py --functions my_list.tsv    the room's inventory

## THE INVENTORY FILE

Tab- or pipe-separated, one function per line, `ID<TAB>gloss`. Blank lines and
`#` comments ignored. Ids must be UPPER_SNAKE.

    SETTING_ESTABLISHED   a place is named and given atmosphere
    ELDER_SPEAKS          an older figure supplies knowledge or a warning

Without `--functions` it uses `FUNCTIONS_SEED` from the task module, which is a
starting point drawn from what the conflict instrument already found recurring
here -- not a proposal about what the answer is.

## WHAT IT PRINTS, AND WHY THE SPAN COLUMN IS THE ONE TO READ

Per function: the share of stories carrying it at least once, the mean number of
occurrences, and its SPAN FAILURE RATE.

**A function with a high span-failure rate is not a rare function, it is one the
annotator is inventing.** That is the single most useful column in the room: it
separates "the corpus does not do this" (fires rarely, spans clean) from "this
category does not survive contact with text" (fires often, spans fail). The first
is a finding about GPT stories; the second is a finding about the proposed
function, and it should be rewritten or dropped.

`--arms` additionally splits by base/aligned on OUR corpus, which Rettberg's
cannot do -- hers is one aligned model with no counterfactual, which is the gap
this whole folder exists to fill.
"""

import argparse
import collections
import csv
import io
import json
import os
import random
import re
import sys

from malignment.paths import repo_root

sys.path.insert(0, repo_root())

DATA = os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data"))
DATA_DIR = os.path.join(DATA, "national_story")
OURS = os.path.join(DATA_DIR, "judged_stories_v2.jsonl")
#: Rettberg & Wigers (2025), 11,800 gpt-4o-mini stories over 236 countries, CC0.
GPT = os.path.expanduser("~/Downloads/dataverse_files/gpt-stories")


#: what a spreadsheet header row looks like, so it can be dropped rather than
#: annotated as a function called "Function".
_HEADERISH = {"function", "functions", "id", "name", "function name", "code",
              "gloss", "description", "definition", "notes", "meaning"}


def _slug(s):
    """'Setting established' -> 'SETTING_ESTABLISHED'.

    **A room writing into a spreadsheet does not write UPPER_SNAKE**, and the
    task's validator refuses anything else so an id survives a round trip
    through a model and a CSV. Normalising here rather than refusing is the
    difference between a live session and a debugging session; the id printed
    back is the normalised one, so nobody is guessing what was run.
    """
    s = re.sub(r"[^0-9A-Za-z]+", "_", (s or "").strip()).strip("_").upper()
    return re.sub(r"_+", "_", s)


def load_functions(path):
    """-> [(ID, gloss)] from a spreadsheet export. Tolerant on purpose.

    Handles what Sheets and Excel actually emit: a header row, CRLF, quoted
    fields, and MORE THAN TWO COLUMNS (a room will add 'proposed by', 'example',
    'keep?'). Column 1 is the id; the gloss is the LONGEST remaining cell on the
    row, because the description is the long one and its position is not stable
    across however the sheet got organised.
    """
    raw = open(path, encoding="utf-8-sig", newline="").read()
    delim = "\t" if "\t" in raw else ("," if raw.count(",") > raw.count("|") else "|")
    out, dropped = [], []
    for row in csv.reader(io.StringIO(raw), delimiter=delim):
        cells = [c.strip() for c in row]
        cells = [c for c in cells if c and not c.startswith("#")]
        if not cells:
            continue
        if len(cells) == 1:
            dropped.append(cells[0])
            continue
        if cells[0].strip().lower() in _HEADERISH:
            continue
        fid = _slug(cells[0])
        gloss = max(cells[1:], key=len)
        if not fid:
            dropped.append(" ".join(cells))
            continue
        out.append((fid, gloss))
    if not out:
        raise SystemExit(
            "no functions parsed from %s -- expected ID<TAB>description per "
            "line. Got %d unusable lines." % (path, len(dropped)))
    if dropped:
        print("note: skipped %d line(s) with no description: %s"
              % (len(dropped), ", ".join(repr(d[:30]) for d in dropped[:4])))
    return out


def load_rettberg(n, seed, only=None):
    """-> [(label, text)] sampled ACROSS countries, not from the first few."""
    if not os.path.isdir(GPT):
        raise SystemExit("Rettberg corpus not at %s -- use --corpus ours" % GPT)
    rows = []
    for d in sorted(os.listdir(GPT)):
        p = os.path.join(GPT, d, "%s_stories.csv" % d)
        if not os.path.exists(p):
            continue
        #: HER COLUMNS ARE CAPITALISED -- `Story`, `Demonym`. A lowercase
        #: `r.get("story")` returns None for every row and the loader reports
        #: "no stories loaded", which reads as a missing corpus rather than a
        #: wrong key. It cost one run to find.
        with open(p, encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                t = (r.get("Story") or "").strip()
                if len(t.split()) < 150:
                    continue
                if only and (r.get("Demonym") or "") not in only:
                    continue
                rows.append((r.get("Demonym") or d, t))
    #: shuffle BEFORE truncating, so a sample is not the alphabetically first
    #: countries -- Rettberg's own directories run AFG, ALB, DZA...
    random.Random(seed).shuffle(rows)
    return rows[:n]


def load_ours(n, seed, arms):
    rows = []
    for line in open(OURS, encoding="utf-8"):
        r = json.loads(line)
        if not r.get("pure_story") or r.get("frame") != "raw":
            continue
        rows.append((r.get("arm", "?"), r["text"]))
    if not arms:
        rows = [x for x in rows if x[0] == "aligned"]
    random.Random(seed).shuffle(rows)
    return rows[:n]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--functions", help="TSV inventory; default is the seed")
    ap.add_argument("--corpus", default="rettberg", choices=("rettberg", "ours"))
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--arms", action="store_true", help="ours: base vs aligned")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--demonyms", help="comma-separated, e.g. Norwegian,Nigerian. "
                                       "Rettberg holds exactly 50 per demonym.")
    ap.add_argument("--smoke", action="store_true", help="3 stories, verbose")
    ap.add_argument("--out", help="write per-story JSONL here")
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args(argv)

    from malignment.tasks.code_gpt_morphology_v1 import (
        build, check_spans, FUNCTIONS_SEED)

    funcs = load_functions(a.functions) if a.functions else FUNCTIONS_SEED
    task = build(funcs)
    n = 3 if a.smoke else a.n
    only = set(x.strip() for x in a.demonyms.split(",")) if a.demonyms else None
    rows = (load_rettberg(n, a.seed, only) if a.corpus == "rettberg"
            else load_ours(n, a.seed, a.arms))
    if not rows:
        raise SystemExit("no stories loaded")

    print("inventory : %d functions, sha %s" % (len(funcs), task.inventory_sha))
    print("corpus    : %s, %d stories" % (a.corpus, len(rows)))
    print("model     : %s" % task.model)
    print()

    hit = collections.Counter()
    occ = collections.Counter()
    by_arm = collections.defaultdict(collections.Counter)
    arm_n = collections.Counter()
    span_ok = span_tot = 0
    span_bad = collections.Counter()
    notes = []
    out_fh = open(a.out, "w", encoding="utf-8") if a.out else None

    #: PARALLEL. Serial at ~1,415 words a story is minutes per dozen, and this
    #: is meant to run while a room waits. `errors` is passed so a None in the
    #: result list is diagnosable rather than positional and opaque.
    errs = {}
    res = task.map([t for _, t in rows], num_workers=a.workers, errors=errs)
    for i, ((label, text), r) in enumerate(zip(rows, res)):
        if r is None:
            print("  [%d/%d] %-10s FAILED: %s"
                  % (i + 1, len(rows), label,
                     (errs.get(i) or {}).get("error", "unknown")))
            continue
        ok, tot, missing = check_spans(text, r)
        span_ok += ok
        span_tot += tot
        for fn, _sp in missing:
            span_bad[fn] += 1
        seen = {f.function for f in r.functions}
        arm_n[label] += 1
        for f in r.functions:
            occ[f.function] += 1
        for f in seen:
            hit[f] += 1
            by_arm[label][f] += 1
        if r.notes:
            notes.append((label, r.notes))
        if out_fh:
            out_fh.write(json.dumps(dict(
                label=label, functions=[f.model_dump() for f in r.functions],
                notes=r.notes, span_ok=ok, span_total=tot)) + "\n")
        if a.smoke:
            print("  --- story %d (%s) ---" % (i + 1, label))
            for f in r.functions:
                mark = "  " if (f.function, f.span) not in missing else "!!"
                print("   %s %-22s %r" % (mark, f.function, f.span[:70]))
            if r.notes:
                print("      NOTES: %s" % r.notes)
            print()
        else:
            print("  [%d/%d] %-10s %2d functions, spans %d/%d"
                  % (i + 1, len(rows), label, len(r.functions), ok, tot))
    if out_fh:
        out_fh.close()

    N = sum(arm_n.values())
    if not N:
        raise SystemExit("every story failed")
    print()
    print("=" * 72)
    print("%-24s %7s %7s %9s" % ("function", "stories", "mean n", "span fail"))
    print("=" * 72)
    for fid, _ in funcs:
        sf = ("%7.0f%%" % (100 * span_bad[fid] / occ[fid])) if occ[fid] else "      -"
        print("%-24s %6.0f%% %7.2f %9s"
              % (fid, 100 * hit[fid] / N, occ[fid] / N, sf))
    print("-" * 72)
    print("%-24s %6s  %d stories, spans %d/%d verbatim (%.1f%%)"
          % ("TOTAL", "", N, span_ok, span_tot,
             100 * span_ok / max(1, span_tot)))

    if (a.arms or a.demonyms) and len(arm_n) > 1:
        print()
        print("BY GROUP (share of stories carrying the function at least once)")
        arms = sorted(arm_n)
        print("%-24s %s" % ("function", "".join("%12s" % x for x in arms)))
        for fid, _ in funcs:
            print("%-24s %s" % (fid, "".join(
                "%11.0f%%" % (100 * by_arm[x][fid] / arm_n[x]) for x in arms)))

    if notes:
        print()
        print("PROPOSED, by the annotator -- moves the inventory has no id for:")
        for label, nt in notes[:15]:
            print("   %-10s %s" % (label, nt[:110]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
