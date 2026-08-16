#!/usr/bin/env python
"""generation_check.py — the sequence-level half, which twp cannot see.

    python generation_check.py --validate     # the detector against known cases
    python generation_check.py --run          # sweep -> results/generation_check.json
    python generation_check.py                # report from the written results

`run.py` measures ONE position. Everything it reports was blind to the only
fluency failure this project had actually observed with its own eyes — mpt's
repetition loop — because **repetition is a sequence property and no
single-position distribution can carry it**. This is the producer that looks at
the text.

## SOURCE — the ARCHIVE database, read-only

Generations live in `malign_logits.gen_sequences` (the archive repo's database),
not in `malignment`. `ch._guard` refuses a statement naming a foreign database,
which is correct and is not worked around here: `ch.DB` is REPOINTED at the
archive for the read. Pointing the configured database somewhere is a
configuration; naming another database inside a statement is the thing the guard
exists to stop.

## THE THREE DETECTORS

    loop    a whitespace token repeated 3+ times consecutively
    short   n_tokens <= 12, against a corpus mean of 222
    quiz    the text contains 'Does it follow' / 'choices' / '____'

**`loop` REPLACED A DETECTOR THAT FAILED, AND THAT IS WHY --validate EXISTS.**
The first version tested whether a 20-character window recurred later in the
string. It maxed out at 3.6% across the roster and returned *0.8%* for
recurrentgemma-9b-it, whose true rate is 79%. A checker that reads clean on the
one case it was built for is worse than no checker, so this one is run against a
known positive AND known negatives before it is trusted:

    google/recurrentgemma-9b        expect ~95%   (independent regex: 94.2%)
    google/recurrentgemma-9b-it     expect ~79%   (independent regex: 83.8%)
    RedPajama-INCITE-7B-Chat        expect  <1%   (eyeballed: fluent prose)
    beaver-7b-v1.0 / AmberSafe      expect  <1%   (eyeballed: fluent prose)
    bloom-7b1                       expect  <1%   (eyeballed: fluent prose)

The SQL detector and a Python backreference regex are two independent
implementations; `--validate` prints both, and they must agree.

## WHY IT SWEEPS THE WHOLE ROSTER INSTEAD OF THE SUSPECTS

The suspects came from `run.py`'s outlier columns. Checking only those would
have confirmed my own shortlist and found nothing else — a check that inherits
its selection from the thing it is checking. Sweeping all 76 is what surfaced
recurrentgemma, which sits at the roster MEDIAN on every twp column.
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
RESULTS = os.path.join(HERE, "results")
OUT = os.path.join(RESULTS, "generation_check.json")
sys.path.insert(0, REPO)
from malignment import ch  # noqa: E402

ARCHIVE = "malign_logits"
#: The home database, captured before anything repoints `ch.DB`. Every read
#: below names which of the two it wants. Leaving it ambient cost a run:
#: `--run` calls `validate()` first, which repoints to the archive, and the
#: following `SELECT ... FROM endpoints` then went looking for a malignment
#: table inside the archive. **A repointed global is a parameter, so pass it.**
HOME = ch.DB
CORPUS = "passage"

#: re2 has no backreferences, so the loop test is expressed over the split array
#: rather than as a regex. Equivalent to r'\b(\w+)\b(?:\s+\1\b){2,}'.
LOOP = ("arrayExists(i -> (arr[i] != '') AND (arr[i] = arr[i+1]) AND (arr[i] = arr[i+2]), "
        "range(1, length(arr)-1))")
QUIZ = ("position(text,'Does it follow')>0 OR position(text,'choices')>0 "
        "OR position(text,'____')>0")
PY_LOOP = re.compile(r"\b(\w+)\b(?:\s+\1\b){2,}", re.I)

VALIDATE = [("google/recurrentgemma-9b", "positive", 90.0, 100.0),
            ("google/recurrentgemma-9b-it", "positive", 70.0, 90.0),
            ("togethercomputer/RedPajama-INCITE-7B-Chat", "negative", 0.0, 2.0),
            ("PKU-Alignment/beaver-7b-v1.0", "negative", 0.0, 2.0),
            ("LLM360/AmberSafe", "negative", 0.0, 2.0),
            ("bigscience/bloom-7b1", "negative", 0.0, 2.0)]


def _ours():
    ch.DB = HOME
    eps = ch.query("SELECT base, endpoint FROM endpoints")
    pair = {}
    for e in eps:
        pair[e["base"]] = e["endpoint"]
        pair[e["endpoint"]] = e["base"]
    return sorted(set(pair)), pair


def _loop_rate(model):
    r = ch.query("SELECT 100*countIf(%s)/count() AS loop, count() AS n FROM "
                 "(SELECT splitByRegexp('\\\\s+', text) AS arr FROM gen_sequences "
                 "WHERE model='%s' AND corpus='%s')" % (LOOP, model, CORPUS),
                 limit_bytes=None)
    return (r[0]["loop"], r[0]["n"]) if r and r[0]["n"] else (None, 0)


def validate():
    ch.DB = ARCHIVE
    print("  %-46s %8s %8s %10s" % ("model", "sql", "regex", "verdict"))
    ok = True
    for m, kind, lo, hi in VALIDATE:
        sql, n = _loop_rate(m)
        if not n:
            print("  %-46s   NO ROWS -- cannot validate" % m[-46:])
            ok = False
            continue
        #: The independent implementation. Text is capped and sampled because
        #: shipping full passages for 40k rows overflows the client buffer --
        #: which it did, and `ch.query` RAISED on the truncated line rather than
        #: dropping it. That raise is the module working.
        #: `substringUTF8`, not `substring`. The byte-based one cut a multibyte
        #: character in half and the client died on `UnicodeDecodeError` before
        #: any row was read -- a truncation rule that is not the data's own
        #: encoding is the format-decides-the-population defect in miniature.
        rs = ch.query("SELECT substringUTF8(text,1,600) AS t FROM gen_sequences "
                      "WHERE model='%s' AND corpus='%s' "
                      "ORDER BY cityHash64(prompt, sample_idx) LIMIT 400"
                      % (m, CORPUS), limit_bytes=None)
        py = 100.0 * sum(bool(PY_LOOP.search(r["t"]) or "") for r in rs) / len(rs)
        good = lo <= sql <= hi and abs(sql - py) < 15
        ok = ok and good
        print("  %-46s %7.2f%% %7.2f%% %10s"
              % (m[-46:], sql, py, "ok" if good else "FAIL(%s)" % kind))
    print("\n  %s" % ("detector validated" if ok else
                      "DETECTOR NOT VALIDATED -- do not sweep with it"))
    return 0 if ok else 1


def run():
    models, _ = _ours()
    ch.DB = ARCHIVE
    out = {}
    for i, m in enumerate(models, 1):
        loop, n = _loop_rate(m)
        if not n:
            continue
        r = ch.query("""SELECT avg(n_tokens) AS mean_tok, median(n_tokens) AS med_tok,
            100*countIf(n_tokens<=12)/count() AS short, 100*countIf(%s)/count() AS quiz
            FROM gen_sequences WHERE model='%s' AND corpus='%s'"""
                     % (QUIZ, m, CORPUS), limit_bytes=None)[0]
        r.update(loop=loop, n=n, model=m)
        out[m] = r
        print("  [%3d/%d] %-46s loop %6.2f%%" % (i, len(models), m[-46:], loop))
    os.makedirs(RESULTS, exist_ok=True)
    json.dump({"corpus": CORPUS, "archive_db": ARCHIVE, "n_models": len(out),
               "models": out}, open(OUT, "w"), indent=1)
    print("\n  wrote %s (%d models)" % (OUT, len(out)))
    return 0


def report(n=14):
    if not os.path.exists(OUT):
        raise SystemExit("no %s -- run with --run first" % OUT)
    doc = json.load(open(OUT))
    d = doc["models"]
    _, pair = _ours()
    rows = sorted(d.values(), key=lambda r: -r["loop"])
    print("  corpus=%s   %d of our models have generations\n" % (doc["corpus"], len(d)))
    print("  %-44s %8s %9s %7s %7s %7s"
          % ("model", "loop%", "partner", "mean", "short%", "quiz%"))
    print("  " + "-" * 88)
    for r in rows[:n]:
        p = pair.get(r["model"])
        print("  %-44s %7.2f%% %9s %7.1f %7.2f %7.2f"
              % (r["model"][-44:], r["loop"],
                 ("%.2f%%" % d[p]["loop"]) if p in d else "-",
                 r["mean_tok"], r["short"], r["quiz"]))
    for key, lab in (("short", "SHORTEST / MOST TRUNCATED"), ("quiz", "QUIZ FORMAT")):
        print("\n  %s" % lab)
        for r in sorted(d.values(), key=lambda r: -r[key])[:5]:
            print("      %-44s %s %6.2f%%  mean_tok %.1f"
                  % (r["model"][-44:], key, r[key], r["mean_tok"]))
    for k in ("loop", "short", "quiz"):
        v = sorted(r[k] for r in d.values())
        print("  %-6s median %6.2f%%  p90 %6.2f%%  max %6.2f%%"
              % (k, v[len(v) // 2], v[int(.9 * len(v))], v[-1]))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--n", type=int, default=14)
    a = ap.parse_args()
    if a.validate:
        return validate()
    if a.run:
        #: The sweep is gated on the validation. A detector that has not been
        #: shown to fire on a known positive produces a table of zeros that
        #: reads exactly like a clean roster.
        if validate():
            return 1
        print()
        return run()
    return report(a.n)


if __name__ == "__main__":
    sys.exit(main())
