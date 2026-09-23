"""Run the USAS sense coder over the rated prompts and write the annotation.

    python usas_sense.py --limit 5            # smoke: 5 prompts, prints them
    python usas_sense.py                      # 2,389 prompts
    python usas_sense.py --report             # read back what is on disk

Writes `results/usas_sense.jsonl`, one object per prompt:

    {"prompt": ..., "n_offered": 19, "n_resolved": 17,
     "position": "...", "senses": {"point": {"gloss": ..., "codes": ["Q2.1"]}}}

## RESUMABLE, BECAUSE A PARTIAL RUN IS THE NORMAL CASE

2,389 calls is not one sitting and a killed run must not start over. Prompts
already in the file are skipped on the next invocation, so the file grows and
never rewrites -- and because the unit is the prompt, a half-finished file is
usable rather than merely resumable.

## WHAT IS VALIDATED HERE RATHER THAN TRUSTED

The coder is told to return only codes from the word's own list, so this checks
that it did, per word, and counts the violations instead of silently accepting
them. Three failure modes, each counted separately in the summary:

    off_list    a code the word was never offered (hallucination, or a code
                moved from a neighbouring word)
    missing     a candidate word the coder did not return at all
    abstained   an empty code list, which is LEGITIMATE and not an error --
                downstream it means "use the full undisambiguated set"

A run whose `off_list` is not near zero has not produced an annotation, it has
produced noise wearing sense codes, and the count is printed before any number
derived from it.
"""

import argparse
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", ".."))

OUT = os.path.join(HERE, "results", "usas_sense.jsonl")


def ambiguous(lang="en"):
    """[(prompt, [(word, [(code, name), ...]), ...])] for prompts with any."""
    from malignment import charge, fields
    from adjacency import usas_signed, label
    jobs = []
    for p in charge.prompts(lang):
        items = []
        for w in sorted((charge.scene(p) or {})):
            codes = sorted(usas_signed(w, "fine"))
            if len(codes) > 1:
                items.append((w, [(c, label(c)) for c in codes]))
        if items:
            jobs.append((p, items))
    return jobs


def done(path=OUT, model=None):
    """Prompts already annotated BY THIS MODEL. -> set

    Keyed on (prompt, model), never on prompt alone. A smoke run against
    another provider is a different instrument, and skipping a prompt because
    some other model answered it leaves a hole in the run of record that looks
    like completion. Rows from both models coexist here and are separated at
    aggregation, which is why every row carries its own `model`.

    This is the ONLY cache on this side. `largeliterarymodels` keys its own
    stash on (prompt, model, system prompt, temperature, max_tokens, schema,
    metadata), so a re-run of a prompt this model has already answered costs
    nothing and does not call the API.
    """
    if not os.path.exists(path):
        return set()
    out = set()
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            try:
                r = json.loads(line)
            except Exception:
                continue
            if model is None or r.get("model") == model:
                out.add(r["prompt"])
    return out


def report(path=OUT):
    rows = [json.loads(l) for l in open(path, encoding="utf-8")] if os.path.exists(path) else []
    if not rows:
        print("nothing at %s" % path)
        return 1
    off = sum(r.get("off_list", 0) for r in rows)
    miss = sum(r.get("missing", 0) for r in rows)
    offered = sum(r["n_offered"] for r in rows)
    res = sum(r["n_resolved"] for r in rows)
    abst = sum(r.get("abstained", 0) for r in rows)
    print("  %d prompts, %d words offered" % (len(rows), offered))
    print("  resolved to >=1 code : %d (%.1f%%)" % (res, 100.0 * res / offered))
    print("  abstained (empty)    : %d (%.1f%%)" % (abst, 100.0 * abst / offered))
    print("  MISSING from reply   : %d" % miss)
    print("  OFF-LIST codes       : %d  <- must be ~0" % off)
    n = collections.Counter()
    for r in rows:
        for w, v in r["senses"].items():
            n[len(v["codes"])] += 1
    print("  codes chosen per word: %s" % dict(sorted(n.items())))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--worst", type=int, default=None,
                    help="take the N prompts carrying the MOST ambiguous "
                         "words instead of the first N. The stress test: the "
                         "heaviest item is 69 candidates and a coder that "
                         "silently truncates will do it there first.")
    ap.add_argument("--limit", type=int, default=None,
                    help="only this many prompts. Use it to smoke the coder "
                         "before spending 2,389 calls.")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--model", default=None,
                    help="override the task's model. The model of record is "
                         "the task's own (deepseek-v4-flash, same coder as the "
                         "charge annotation); an override makes a DIFFERENT "
                         "instrument and its rows must not be pooled with it.")
    ap.add_argument("--lang", default="en")
    ap.add_argument("--show", action="store_true",
                    help="print every gloss and choice. Implied by --limit.")
    ap.add_argument("--report", action="store_true",
                    help="summarise what is already on disk and stop")
    a = ap.parse_args(argv)
    if a.report:
        return report(a.out)

    from malignment.tasks.code_usas_sense_v1 import USASSenseTask, render
    from malignment.tasks.code_usas_sense_v1 import USASSenseTask as _T
    jobs = ambiguous(a.lang)
    model = a.model or _T.model
    have = done(a.out, model)
    todo = [(p, it) for p, it in jobs if p not in have]
    if a.worst:
        todo = sorted(todo, key=lambda x: -len(x[1]))[:a.worst]
        print("  --worst %d: heaviest items carry %s candidates"
              % (a.worst, ", ".join(str(len(it)) for _, it in todo)))
    print("  %d prompts carry an ambiguous word; %d already done on %s; %d to do"
          % (len(jobs), len(have), model, len(todo)))
    if a.limit:
        todo = todo[:a.limit]
        print("  --limit %d: running %d" % (a.limit, len(todo)))
    if not todo:
        return report(a.out)

    task = USASSenseTask()
    errs = {}
    if a.model:
        print("  MODEL OVERRIDE: %s (task of record is %s)" % (a.model, task.model))
    res = task.map([render(p, it) for p, it in todo],
                   metadata_list=[{"prompt": p} for p, _ in todo],
                   model=model, num_workers=a.workers, errors=errs)

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    n_ok = 0
    with open(a.out, "a", encoding="utf-8") as fh:
        for (p, items), r in zip(todo, res):
            if r is None:
                continue
            offered = {w: {c for c, _ in cs} for w, cs in items}
            senses, off, abst = {}, 0, 0
            for ws in r.words:
                if ws.word not in offered:
                    off += len(ws.codes)
                    continue
                good = [c for c in ws.codes if c in offered[ws.word]]
                off += len(ws.codes) - len(good)
                senses[ws.word] = {"gloss": ws.gloss, "codes": good}
                if not good:
                    abst += 1
            rec = {"prompt": p, "model": model, "position": r.position,
                   "n_offered": len(items), "n_resolved": sum(1 for v in senses.values() if v["codes"]),
                   "abstained": abst, "missing": len(offered) - len(senses),
                   "off_list": off, "senses": senses}
            fh.write(json.dumps(rec) + "\n")
            n_ok += 1
            if a.show or a.limit:
                print("\n  %s ___" % p)
                print("    position: %s" % r.position)
                for w, v in senses.items():
                    print("    %-12s %-34s -> %s" % (w, v["gloss"][:34],
                                                     ", ".join(v["codes"]) or "(abstained)"))
    print("\n  %d written, %d errors -> %s" % (n_ok, len(errs), a.out))
    if errs:
        print("  first error: %s" % list(errs.items())[0][1])
    print()
    return report(a.out)


if __name__ == "__main__":
    sys.exit(main())
